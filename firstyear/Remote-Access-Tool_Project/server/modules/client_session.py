import utility

from . import session_manager as sm


class ClientSession:
    def __init__(self, *, conn: socket.socket, sid: int, manager: sm.SessionManager):
        self._conn = conn
        self._sid = sid
        self._manager = manager
        self._instructions = {"screenshot": self._screenshot}

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
        self._send_command("screenshot")
        try:
            file_size = int(self._conn.recv(512).decode())
        except (ValueError, TypeError):
            # TODO: Error handling
            return

    def _download(self) -> None:
        """Download a file from the client"""
        pass

    def execute(self, command: str, *args):
        """Fetch the relative function of the given command and execute it with the given arguments

        Args:
            command (str): [description]
        """
        func = self._instructions.get(command)
        if func is not None:
            func(*args)

    # socket interaction ----------------------------------------------------

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
            # TODO: Download status indicator
            if data.tell() >= file_size:
                break
        if len(data) == file_size:
            with open(
                os.path.join(save_dir, file_name or f"{self.sid}_{time.time()}.png"),
                "wb",
            ) as file:
                file.write(data.getvalue())
                # TODO: OUTPUT CONFIRMATION

    def _send_command(self, command: str, *args) -> None:
        """Send a command packet to the client

        Args:
            command (str): command string to send over the socket connection
        """
        self._conn.send(json.dumps({"command": command, "args": args}).encode())

    def _send_file(self) -> None:
        """Send a file to the client"""
        pass

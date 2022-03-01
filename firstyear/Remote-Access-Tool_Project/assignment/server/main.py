# import modules

import shlex
import socket
import threading

import settings
import utility
from modules.manager import Manager


def connection_listener(*, host: str = "127.0.0.1", port: int = 3000) -> None:
    """Listens for connections from clients and passes them through to the manager for further processing

    Args:
        host (str, optional): Host address to listen for connections on. Defaults to "127.0.0.1".
        port (int, optional): Port to be paired with the host address for listening to connections. Defaults to 3000.

    Raises:
        OSError: If the socket cannot be created due to a clash with prexisting network usage
    """
    global manager

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError as exception:
            raise OSError(
                f"Unable to bind to {host}:{port}; "
                "This may be because the specified host address is invalid, "
                "or the specified port number is already in use."
            ) from exception
        else:
            sock.listen()

        while True:
            conn, _ = sock.accept()
            print(
                utility.padstr(
                    "Connection from {}:{}".format(*conn.getpeername()), bottom=0
                )
            )
            manager.add_client(conn)


# Help Menu / Command List --------------------------------------------------


def command_list() -> str:
    """Displays a list of all available commands and their descriptions."""
    global manager

    commands = {
        "help": {"description": "Displays this help message"},
        "exit": {"description": "Shutdown the server and exit"},
    } | manager.get_commands()
    arg_str = (", ".join(x.get("arguments", [])) for x in commands.values())
    arg_pad = max(len(max(arg_str, key=len)), 9) + 5
    cmd_pad = max(len(max(*commands.keys(), key=len)), 7) + 5
    heading = "COMMAND".ljust(cmd_pad) + "ARGUMENTS".ljust(arg_pad) + "DESCRIPTION"
    content = "\n".join(
        (
            cmd.ljust(cmd_pad)
            + ", ".join(info.get("arguments", ["-"])).ljust(arg_pad)
            + info.get("description", "-")
        )
        for cmd, info in commands.items()
    )
    print(utility.padstr(heading + "\n\n" + content))


# Main Startup and Processing -----------------------------------------------


if __name__ == "__main__":
    manager = Manager()

    # start the connection listener thread
    threading.Thread(
        target=connection_listener,
        kwargs={"host": settings.HOST, "port": settings.PORT},
        daemon=True,
    ).start()

    # server-side user interface
    while True:
        try:
            cmd, *args = shlex.split(input("$ "), posix=False)
        except ValueError:
            continue

        if cmd == "exit":
            break  # close the server
        elif cmd == "help":
            command_list()  # display the list of commands and their descriptions/arguments
        else:
            manager.handle_command(cmd, *args)  # handle command in manager

    input(
        utility.padstr("Press any key to exit...", top=2, bottom=0)
    )  # wait for enter key to close

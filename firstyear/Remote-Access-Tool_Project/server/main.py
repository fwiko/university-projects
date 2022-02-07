"""Remote Access Tool server

This is the main server script for the Remote Access Tool.
Providing the command line interfaceand linking to all other functionality.
"""

import shlex
import utility


class ServerInterface:
    """Provides an interface for the server to interact with, control, and manage connected
    clients"""

    def __init__(self):
        self._active = False

    def start(self) -> None:
        """Start the user interface. This method should be called from the main thread."""
        self._active = True
        while self._active:
            try:
                command, *arguments = shlex.split(input("Server> "))
            except ValueError:
                # Catch upon an error involving the shlex module (unclosed quotations)
                continue
            if command == "exit":
                self._active = False
            elif command == "help":
                self._help_menu()
            else:
                manager.handle_command(command.lower(), *arguments)

    def _help_menu(self) -> None:
        """Displays a list of all available commands and their descriptions."""
        commands = {
            "help": {"description": "Prints this help message"},
            "exit": {"description": "Shutdown the server and exit the program"},
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
        print(utility.padded(heading + "\n\n" + content))


if __name__ == "__main__":
    import modules.manager as mgr

    manager = mgr.Manager()

    ServerInterface().start()
    print("Server is shutting down...")

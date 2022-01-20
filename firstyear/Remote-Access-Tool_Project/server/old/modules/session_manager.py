from __future__ import annotations

import socket
import threading

import utility

from . import client_session as cs


class SessionManager:
    def __init__(self, *, host: str = "127.0.0.1", port: int = 5001) -> None:
        self._host = host
        self._port = port
        self._nextsid = 1
        self._sessions = []

    # getters ---------------------------------------------------------------

    def get_session(self, sid: int) -> cs.ClientSession:
        """Returns the session object for the given sid

        Args:
            sid (int): Session identification number of the session to be returned
        Returns:
            [type]: Session object relative to the given sid or None if no session is found
        """
        return next((s for s in self._sessions if s.sid == sid), None)

    def get_sessions(self) -> list[cs.ClientSession]:
        """Returns a list of all active sessions recognised by the session manager

        Returns:
            list: list of all active session objects
        """
        return self._sessions

    # session interaction ---------------------------------------------------

    def execute_on_session(self, command: int, sid: int, *args) -> None:
        try:
            session = self.get_session(int(sid))
        except ValueError:
            utility.Response.err("Session ID must be an integer")
        else:
            if session is not None:
                session.execute(command, *args)
            else:
                utility.Response.err(f"Session with ID {sid} not found")

    # session management -----------------------------------------------------

    def _add_session(self, conn: socket.socket) -> None:
        self._sessions.append(
            cs.ClientSession(conn=conn, sid=self._nextsid, manager=self)
        )
        self._nextsid += 1

    def _remove_session(self, sid: int):
        self._sessions.remove(self.get_session(sid))

    # connection management --------------------------------------------------

    def _handle_connection(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        utility.Response.out("Connection from {}:{}".format(*addr))
        self._add_session(conn)

    def connection_listener(self) -> None:
        """Listener for incoming socket connections"""

        def listen():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind((self._host, self._port))
                except OSError as exception:
                    raise OSError(
                        f"Unable to bind to {self._host}:{self._port}; "
                        "This may be because the specified host address is invalid, "
                        "or the specified port number is already in use."
                    ) from exception
                s.listen()
                while True:
                    conn, addr = s.accept()
                    threading.Thread(
                        target=self._handle_connection, args=(conn, addr)
                    ).start()

        threading.Thread(target=listen, daemon=True).start()

    # session signals -------------------------------------------------------

    def disconnected(self, session: cs.ClientSession) -> None:
        ...

import json
import socket
import threading
from collections import namedtuple

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Logger, Server, Game, State

class Client:
    """Client class - used for handling of connected clients"""
    __alive = False

    def __init__(self, server: 'Server', conn, addr, uid) -> None:
        self.logger = Logger(f"Client-{uid}")
        self.__conn = conn
        self.__addr = addr
        self.__server = server
        self.__settings = namedtuple('ClientData', ['state', 'username', 'uid', 'commands', 'game'])(State.IN_MENU,
                                                                                                    f'Client-{uid}',
                                                                                                    uid, {}, None)

    def listen(self):
        """Start listening to client - listen for data sent from client and handle it"""
        self.__alive = True
        while self.__alive:
            try:
                data = self.__conn.recv(1024).decode('utf-8')
                if not data: break
                self.logger.info(f"Received data from {self.__addr}: {data}")
                decoded = json.loads(data)

            except WindowsError:
                self.logger.error(f"Connection/Socket error on {self.__addr}")
                self.__alive = False

            except json.decoder.JSONDecodeError:
                self.logger.error(f"Invalid JSON data received from {self.__addr}")
                continue

            if not decoded.get("header", None) or not decoded.get("data", None):
                continue

            # checking a users state
            client_state = self.__settings.get("state", None)

            if decoded["header"] == "command":
                self.__handle_command(decoded["data"].get("command"))
            elif client_state == State.IN_GAME and decoded["header"] == "answer":
                self.__handle_answer(decoded["data"].get("answer"))

        __server.client_disconnected(self)

    # SETTER METHODS

    def set_state(self, state: 'State') -> None:
        """Set the state of the client"""
        self.__settings.state = state
        # self.send("state", {"state": 'State'})
        self.logger.info(f"State changed to {state}")

    def set_username(self, username: str) -> None:
        """Set the username of the client"""
        self.__settings.username = username
        self.logger.info(f"Username changed to {username}")

    def set_game(self, game: 'Game') -> None:
        """Set the game of the client"""
        self.__settings.game = game
        self.logger.info(f"Game changed to {self.__settings.game}")

    # GETTER METHODS

    def get_address(self) -> str:
        """Get the address of the client"""
        return self.__addr

    def get_state(self) -> str:
        """Get the state of the client"""
        return self.__settings.state

    def get_settings(self) -> dict:
        """Get the settings of the client"""
        return self.__settings

    def get_uid(self) -> int:
        """Get the uid of the client"""
        return self.__settings.uid

    def get_username(self) -> str:
        """Get the username of the client"""
        return self.__settings.username

    def get_game(self) -> 'Game':
        """Get the game of the client"""
        return self.__settings.game

    def __get_handlers(self) -> dict:
        """Get the handlers of the client"""
        return {
            "host": self.__host_game,
            "join": self.__join_game,
            "leave": self.__leave_game,
            "games": self.__get_games,
            "start": self.__start_game
        }

    # COMMAND HANDLERS

    def __host_game(self) -> None:
        """Handle the host game command"""
        new_game = Game(self)
        self.__server.add_game(new_game)
        self.set_state(State.IN_LOBBY)
        self.set_game(game)

    def __join_game(self, game_code: str) -> None:
        """Handle the join game command"""
        game = self.__server.get_game_from_code(game_code.upper())
        if not game: return

        self.set_game(game)
        game.add_client(self)
        self.set_state(State.IN_LOBBY)

    def __leave_game(self) -> None:
        """Handle the leave game command"""
        if self.get_state() not in (State.IN_GAME, State.IN_LOBBY) or not self.get_game():
            return

        self.__settings.game.client_leave(self)
        self.set_game(None)
        self.set_state(State.IN_MENU)

    def __get_games(self) -> None:
        """Handle the get games command"""
        self.send("games", {"game_list": [{"code": 'Game'.get_code(), "players": len(game.get_players())} for game in
                                        self.__server.get_games()]})

    def __start_game(self) -> None:
        """Handle the start game command"""
        if self.get_state() != State.IN_LOBBY or not self.get_game():
            return

        self.get_game().start()

    # SERVER INTERACTION METHODS

    def __handle_command(self, command: str) -> None:
        """Handle a command sent from the client"""
        parsed_data = (re.sub(' +', ' ', command.strip())).lower().split(" ")
        cmd = parsed_data[0]
        args = parsed_data[1:]

        handler = self.__get_handlers().get(cmd, None)
        if handler:
            handler(*args)

    def __handle_answer(self, answer: str) -> None:
        """Handle an answer sent from the client"""
        if self.get_state() != State.IN_GAME or not self.get_game():
            return

        parsed_answer = (re.sub(' +', ' ', answer.strip())).lower()
        self.get_game().submit_answer(self, parsed_answer)

    # CLIENT INTERACTION METHODS

    def close_connection(self):
        """Close the connection of the client"""
        self.__alive = False
        self.__conn.close()
        self.logger.debug(f"Connection closed on {self.__addr}")

    def send(self, header: str, data: dict) -> None:
        """Send data packets to the client"""
        packet = json.dumps({"header": header, "data": data})
        self.__conn.send(packet.encode('utf-8'))

        self.logger.debug(f"Sent data to {self.__addr}: {packet}")

from . import Logger, Server, Game, State

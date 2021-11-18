from __future__ import annotations

import re
import json
import socket

import classes.game as game
import classes.manager as manager
import settings

from modules import State, Logger

class Client:
    def __init__(self, manager: manager.Manager, uid: int, conn: socket.socket, addr):
        self.username = f"Client-{uid}"
        self.logger = Logger(self.username)
        self.__uid = uid
        self.__conn = conn
        self.__addr = addr
        self.__manager = manager
        self.game = None
        self.state = State.IN_MENU
        
        
    def __repr__(self):
        return f"{self.__class__.__name__}-{self.uid}"
    
    # properties (attribute getters and setters)
    
    @property
    def uid(self) -> int:
        return self.__uid
    
    @property
    def conn(self) -> socket.socket:
        return self.__conn
    
    @property
    def addr(self) -> tuple:
        return self.__addr
    
    @property
    def username(self):
        return self._username

    @property
    def state(self):
        return self._state
    
    @property
    def game(self):
        return self._game

    @username.setter
    def username(self, username: str):
        if 3 <= len(username) <= 16:
            self._username = username
        else:
            self.logger.error(f"Attempted to set invalid username \"{username}\"")
            
    @state.setter
    def state(self, state: State):
        if isinstance(state, State):
            self._state = state
            self.send("state", {"state": state.value})
        else:
            self.logger.error(f"Attempted to set invalid state \"{state}\"")
            
    @game.setter
    def game(self, g: game.Game or None):
        if g is None or isinstance(g, game.Game):
            self._game = g
            if g:
                self.send("game_code", {"game_code": g.settings.code})
        else:
            self.logger.error(f"Attempted to set invalid game \"{g}\"")
            
    # command handler methods
    
    def __host_command(self) -> None:
        if self.game:
            return
        g = game.Game(self.__manager, self)
        self.game = g
        self.__manager.add_game(g)
        self.state = State.IN_GAME
    
    def __join_command(self, game_code: str) -> None:
        g = self.__manager.get_game_from_code(game_code)
        if not g or g.is_active(): return
        self.game = g
        g.add_client(self)
        self.state = State.IN_GAME
        
    def __leave_command(self) -> None:
        if self.state not in (State.IN_GAME, State.IN_LOBBY) or not self.game:
            return
        self.game.client_leave(self)
        self.game = None
        self.state = State.IN_MENU
    
    def __games_command(self) -> None:
        game_list = [{"code": g.settings.code, "player_count": len(g.settings.players)} for g in self.__manager.get_games() if not g.is_active()]
        self.send("game_list", {"game_list": game_list})
    
    def __start_command(self) -> None:
        if self.state != State.IN_LOBBY or not self.game or self != self.game.owner:
            return
        self.game.start_quiz()
        
    def __username_command(self, username: str) -> None:
        if self.state != State.IN_MENU:
            return
        self.username = username
    
    def _get_handlers(self) -> dict:
        return {
            "host": self.__host_command,
            "join": self.__join_command,
            "leave": self.__leave_command,
            "games": self.__games_command,
            "start": self.__start_command
        }
    
    # command and answer processing methods
    
    def __process_command(self, command: str) -> None:
        sanitised_command: list[str] = (re.sub(' +', ' ', command.strip())).lower().split(" ")
        cmd: str = sanitised_command[0]
        args: list[str] = sanitised_command[1:]
        handler = self._get_handlers().get(cmd)
        if handler:
            self.logger.debug(f"Handling command: {command}{' '+' '.join(args) if args else ''}")
            handler(*args)
        else:
            self.logger.debug(f"Unknown command: {command}{' '+' '.join(args) if args else ''}")
        
    def __process_answer(self, answer: str) -> None:
        sanitised_answer: str = (re.sub(' +', ' ', answer.strip())).lower()
        self.game.handle_answer(self, sanitised_answer)
    
    # client interaction methods
    
    def send(self, header: str, data: dict) -> None:
        self.logger.debug(f"Sending data: {data}")
        self.conn.send(json.dumps({"header": header, "data": data}).encode("utf-8"))
    
    # data receiver methods
    
    def listen(self) -> None:
        self.send("client_info", {"uid": self.uid})
        self.send("help_menu", settings.HELP_MENU)
        self._alive = True
        while self._alive:
            try:
                data = self.conn.recv(1024).decode("utf-8")
                if not data:
                    break
                decoded: dict = json.loads(data)
                self.logger.debug(f"Received data: {decoded}")
                
            except WindowsError as error:
                self.logger.error(error)
                self._alive = False
                continue
            
            except json.decoder.JSONDecodeError as error:
                self.logger.error(error)
                continue
            
            if not decoded.get("header", None) or not decoded.get("data", None):
                continue
            
            if decoded.get("header") == "command":
                self.logger.debug(f"Handling command: {decoded.get('data')}")
                self.__process_command(decoded.get("data").get("command"))
            elif decoded.get("header") == "answer" and self.state == State.IN_GAME and self.game:
                self.logger.debug(f"Handling answer: {decoded.get('data')}")

        self.__manager.client_exit(self)
        
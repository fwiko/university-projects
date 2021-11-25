from __future__ import annotations

import re
import json
import time
import socket

import classes.game as game
import classes.manager as manager
import settings

from utility import State, Logger

class Client:
    def __init__(self, manager: manager.Manager, uid: int, conn: socket.socket, addr: tuple):
        self.__uid = uid
        self.__conn = conn
        self.__addr = addr
        self.__manager = manager
        self.username = f"Client-{uid}"
        self.logger = Logger(self.username)
        self.game = None
        self.state = State.IN_MENU

    # properties (attribute getters and setters)
    
    @property
    def uid(self) -> int:
        """property method to fetch the uid value of the client"""
        return self.__uid
    
    @property
    def conn(self) -> socket.socket:
        """property method to fetch the socket connection of the client"""
        return self.__conn
    
    @property
    def addr(self) -> tuple:
        """property method to fetch the address information of the client (ip and port)"""
        return self.__addr
    
    @property
    def username(self) -> str:
        """property method to fetch the username value of the client"""
        return self._username

    @property
    def state(self) -> State:
        """property method to fetch the state value of the client"""
        return self._state
    
    @property
    def game(self) -> game.Game or None:
        """property method to fetch the game value of the client"""
        return self._game

    @username.setter
    def username(self, username: str):
        """property setter method to set the username value of the client"""
        # check whether the specified username argument is between 3 and 16 characters in length
        if 3 <= len(username) <= 16:
            # if it is, set the username value of the client to the specified username argument
            self._username = username
        else:
            # if it isn't, log an error message and do not set the username value of the client
            self.logger.error(f"Attempted to set invalid username \"{username}\"")
            
    @state.setter
    def state(self, state: State):
        """property setter method to set the state value of the client"""
        # check whether the specified state argument is a valid state
        if isinstance(state, State):
            # if it is, set the state value of the client to the specified state argument
            self._state = state
            # send a state packet to the connected client with the new state value
            self.send("state", {"state": state.value})
        else:
            # if it isn't, log an error message and do not set the state value of the client
            self.logger.error(f"Attempted to set invalid state \"{state}\"")
            
    @game.setter
    def game(self, g: game.Game or None):
        """property setter method to set the game value of the client"""
        # check whether the specified game argument is a valid game or is None
        if g is None or isinstance(g, game.Game):
            # if it is, set the game value of the client to the specified game argument
            self._game = g
            # if the specified game argument is an instance of the game class (not None)
            if g:
                # send the new game code to the local client
                self.send("game_code", {"game_code": g.settings.code})
        # if the specified game argument is not a valid game or is not None
        else:
            # log an error message and do not set the game value of the client
            self.logger.error(f"Attempted to set invalid game \"{g}\"")
            
    # command handler methods
    
    def __host_command(self) -> None:
        """method used to handle the host command once sent to the server"""
        # if the client is already in a game, do not allow them to host a new game
        if self.game:
            return
        # if the client is not in a game, create a new game with the client as the owner
        g = game.Game(self.__manager, self)
        # set the clients game value to the newly created game
        self.game = g
        # add the newly created game to the server manager
        self.__manager.add_game(g)
        # set the clients state to IN_LOBBY
        self.state = State.IN_LOBBY
        # wait a tenth of a second (safety)
        time.sleep(0.1)
        # alert the client that a game has been created
        self.send("alert", {"message": f"Game created with code {self.game.settings.code}"})
    
    def __join_command(self, *args) -> None:
        """method used to handle the join command once received by the server"""
        # if no game code was specified, do not allow the client to join a game
        if len(args) < 1:
            return
        # if the client is already in a game, do not allow them to join another game
        if self.game or self.state != State.IN_MENU:
            return
        # if the client is not in a game, try to find the game with the specified game code
        g = self.__manager.get_game_from_code(args[0].upper())
        # if the game was not found or is already mid game
        if not g or g.is_active():
            # alert the client of the error
            self.send("alert", {"message": f"Game code \"{args[0].upper()}\" not found or game is already active"})
            # log the error
            self.logger.error(f"Game code \"{args[0].upper()}\" not found or game is already active")
            return
        # if the game was found and is not active, add the client to the game
        self.game = g
        g.add_client(self)
        # set the clients state to IN_LOBBY
        self.state = State.IN_LOBBY
        # alert the client that they have joined the game
        self.send("alert", {"message": f"Joined game with code {self.game.settings.code}"})
        
    def __leave_command(self) -> None:
        """method used to handle the leave command once received by the server"""
        # if the client is not in a game, cancel the handlers operation
        if self.state not in (State.IN_GAME, State.IN_LOBBY) or not self.game:
            return
        # if the client is in a game, trigger that games leave handler passing in the client
        self.game.client_leave(self)
        # set the client class' game value to None
        self.game = None
        # set the clients state to IN_MENU
        self.state = State.IN_MENU
        # Alert the client that they have left the game
        self.send("alert", {"message": f"Left game {self.game.settings.code}"})
    
    def __games_command(self) -> None:
        """method used to handle the games command once received by the server"""
        game_list = [{"code": g.settings.code, "player_count": len(g.settings.players)} for g in self.__manager.get_games() if not g.is_active()]
        self.send("game_list", {"game_list": game_list})
    
    def __start_command(self) -> None:
        if self.state != State.IN_LOBBY or not self.game or self != self.game.settings.owner:
            return
        self.game.start_quiz()
        
    def __username_command(self, *args) -> None:
        if self.state not in (State.IN_MENU, State.IN_LOBBY):
            return
        self.username = " ".join(args)
        self.send("alert", {"message": f"Username set to {self.username}"})
    
    def _get_handler(self, cmd: str) -> dict:
        return {
            "host": self.__host_command,
            "join": self.__join_command,
            "leave": self.__leave_command,
            "games": self.__games_command,
            "start": self.__start_command,
            "username": self.__username_command
        }.get(cmd)
    
    # command and answer processing methods
    
    def __process_command(self, command: str) -> None:
        sanitised_command: list[str] = (re.sub(' +', ' ', command.strip())).lower().split(" ")
        cmd: str = sanitised_command[0]
        args: list[str] = sanitised_command[1:]
        handler = self._get_handler(cmd)
        if handler:
            self.logger.debug(f"Handling command: {cmd}{' '+' '.join(args) if args else ''}")
            try:
                handler(*args)
            except TypeError:
                handler()
        else:
            self.logger.debug(f"Unknown command: {cmd}{' '+' '.join(args) if args else ''}")
        
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
        self._alive = True
        while self._alive:
            try:
                data = self.conn.recv(1024).decode("utf-8")
                if not data:
                    break
                decoded: dict = json.loads(data)
                self.logger.debug(f"Received data: {decoded}")
                
            except OSError as error:
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
                self.__process_answer(decoded.get("data").get("answer"))

        self.__manager.client_exit(self)
        
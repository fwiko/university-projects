from __future__ import annotations

# importing python packages
import re
import json
import time
import socket

# importing custom classes/files
import classes.game as game
import classes.manager as manager
import settings
from utility import State, Logger

class Client:
    def __init__(self, manager: manager.Manager, uid: int, conn: socket.socket, addr: tuple):
        """initialize the client object

        Args:
            manager (manager.Manager): server manager, controller of clients and games
            uid (int): unique identifier of the client object
            conn (socket.socket): socket the client is connected on
            addr (tuple): address information of the client
        """
        self.__uid = uid
        self.__conn = conn
        self.__addr = addr
        self.__manager = manager
        self.logger = Logger(f"Client-{uid}")
        self.username = f"Client-{uid}"
        self.game = None
        self.state = State.IN_MENU

    # properties (attribute getters and setters)
    
    @property
    def uid(self) -> int:
        """property method to fetch the uid value of the client

        Returns:
            int: uid of the client object
        """
        return self.__uid
    
    @property
    def conn(self) -> socket.socket:
        """property method to fetch the socket connection of the client

        Returns:
            socket.socket: socket connection of the client object
        """
        return self.__conn
    
    @property
    def addr(self) -> tuple:
        """property method to fetch the address information of the client (ip and port)

        Returns:
            tuple: address information of the client objects socket connection
        """
        return self.__addr
    
    @property
    def username(self) -> str:
        """property method to fetch the username value of the client

        Returns:
            str: username attribute of the client object
        """
        return self._username

    @property
    def state(self) -> State:
        """property method to fetch the state value of the client

        Returns:
            State: state value of the client object
        """
        return self._state
    
    @property
    def game(self) -> game.Game or None:
        """property method to fetch the game value of the client

        Returns:
            game.Game or None: game object of the client object or None
        """
        return self._game

    @username.setter
    def username(self, username: str):
        """property setter method to set the username value of the client

        Args:
            username (str): username value to set the client object's username attribute to
        """
        # check whether the specified username argument is between 3 and 16 characters in length
        if 3 <= len(username) <= 16:
            # if it is, set the username value of the client to the specified username argument
            self._username = username
            self.logger.info(f"Username set to \"{username}\"")
        else:
            # if it isn't, log an error message and do not set the username value of the client
            self.logger.error(f"Attempted to set invalid username \"{username}\"")
            
    @state.setter
    def state(self, state: State):
        """property setter method to set the state value of the client

        Args:
            state (State): state value to set the client object's state attribute to
        """
        # check whether the specified state argument is a valid state
        if isinstance(state, State):
            # if it is, set the state value of the client to the specified state argument
            self._state = state
            # send a state packet to the connected client with the new state value
            self.send("state", {"state": state.value})
            self.logger.info(f"State set to {state.value}")
        else:
            # if it isn't, log an error message and do not set the state value of the client
            self.logger.error(f"Attempted to set invalid state \"{state}\"")
            
    @game.setter
    def game(self, g: game.Game or None):
        """property setter method to set the game value of the client[summary]

        Args:
            g (game.Game or None): game object to set the client object's game attribute to
        """
        # check whether the specified game argument is a valid game or is None
        if g is None or isinstance(g, game.Game):
            # if it is, set the game value of the client to the specified game argument
            self._game = g
            # if the specified game argument is an instance of the game class (not None)
            if g:
                # send the new game code to the local client
                self.send("game_code", {"game_code": g.settings.code})
            self.logger.info(f"Game set to {g.settings.code if g else None}")
        # if the specified game argument is not a valid game or is not None
        else:
            # log an error message and do not set the game value of the client
            self.logger.error(f"Attempted to set invalid game \"{g}\"")
            
    # command handler methods
    
    def __host_command(self) -> None:
        """method used to handle the host command once received by the server"""
        # if the client is already in a game, do not allow them to host a new game
        if self.game:
            self.send("alert", {"message": f"You are already in a game/lobby and cannot currently host another."})
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
        game_code = self.game.settings.code
        self.game = None
        # set the clients state to IN_MENU
        self.state = State.IN_MENU
        # Alert the client that they have left the game
        self.send("alert", {"message": f"Left game {game_code}"})
        self.logger.info(f"Left game {game_code}")
    
    def __games_command(self) -> None:
        """method used to handle the games command once received by the server"""
        # a list comprehension to create a list of dictionaries containing the game code and player count of all idle lobbies
        game_list = [{"code": g.settings.code, "player_count": len(g.settings.players)} for g in self.__manager.get_games() if not g.is_active()]
        # send the generated list back to the client who executed the command
        self.send("game_list", {"game_list": game_list})
    
    def __start_command(self) -> None:
        """method used to handle the start command once received by the server"""
        # if the client instances state is not IN_LOBBY, or they are not the owner of the lobby they are in
        if self.state != State.IN_LOBBY or not self.game or self != self.game.settings.owner:
            # return, cancelling the start command
            return
        # otherwise, start a quiz with the current players in the game/lobby
        self.game.start_quiz()
        
    def __username_command(self, *args) -> None:
        """method used to handle the username command once received by the server"""
        # if the clients state is not IN_MENU, or IN_LOBBY
        if self.state not in (State.IN_MENU, State.IN_LOBBY):#
            # return, cancelling the username command
            return
        # otherwise, set the clients username to the specified username
        self.username = " ".join(args)
        self.send("alert", {"message": f"Username set to {self.username}"})
    
    def _get_handler(self, cmd: str) -> dict:
        """method used to fetch a command handler method based on the command that was sent to the server"""
        return {
            "host": self.__host_command,
            "join": self.__join_command,
            "leave": self.__leave_command,
            "games": self.__games_command,
            "start": self.__start_command,
            "username": self.__username_command
            # fetch a class method based on the passed in 'cmd' argument, otherwise return None
        }.get(cmd)
    
    # command and answer processing methods
    
    def __process_command(self, command: str) -> None:
        """method used to process a command sent to the server

        Args:
            command (str): command string sent to the server from the client
        """
        # sanitise the command string - remove any extra spaces and split the string up into a list of single words
        sanitised_command: list[str] = (re.sub(' +', ' ', command.strip())).lower().split(" ")
        # set the first element of the sanitised command list to the 'cmd' variable
        cmd: str = sanitised_command[0]
        # set all elements after the first index (index 0) to the 'args' variable
        args: list[str] = sanitised_command[1:]
        # fetch the command handler method based on the 'cmd' variable
        handler = self._get_handler(cmd)
        # if there is a handler based on the sent command
        if handler:
            self.logger.debug(f"Handling command: {cmd}{' '+' '.join(args) if args else ''}")
            try:
                # try to call the handler method passing in the list of arguments 'args'
                handler(*args)
            # if the handler doesn't accept arguments, an exception will be thrown
            except TypeError:
                # in that case, call the handler without arguments
                handler()
        # if the command is not recognised, log an unknown command message
        else:
            self.logger.error(f"Unknown command: {cmd}{' '+' '.join(args) if args else ''}")
        
    def __process_answer(self, answer: str) -> None:
        """method used to process answers sent by the client when answering questions in a quiz

        Args:
            answer (str): answer string sent to the server from the client
        """
        # sanitise the answer - remove all extra spaces/white space in the string
        sanitised_answer: str = (re.sub(' +', ' ', answer.strip())).lower()
        # pass the sanitised answer to the game instance's answer handler
        # to check whether it is correct and update the leaderboard
        self.game.handle_answer(self, sanitised_answer)
    
    # client interaction methods
    
    def send(self, header: str, data: dict) -> None:
        """method used to to send data back to local clients which are connected to the server

        Args:
            header (str): header of the data to be sent to the client object
            data (dict): data to be sent to the client object
        """
        self.logger.debug(f"Sending data: {data}")
        # send a JSON string of the data encoded in UTF-8 to the client socket of the client instance
        self.conn.send(json.dumps({"header": header, "data": data}).encode("utf-8"))
    
    # data receiver methods
    
    def listen(self) -> None:
        """method used to start the client listener which will listen for data (commands and answers)
        sent from clients that are connected to the server"""
        # send data to the client instances socket including the UID value of the client instance
        self.send("client_info", {"uid": self.uid})
        # while the client is still alive (i.e. not disconnected from the server)
        while True:
            try:
                # attempt to receive data from the client socket
                data = self.conn.recv(1024).decode("utf-8")
                # if the data is empty (usually because of a critical error or client disconnect)
                if not data:
                    # break, exiting the client listener
                    break
                # otherwise attempt to decode the data into a dictionary object
                decoded: dict = json.loads(data)
                # log the received data
                self.logger.debug(f"Received data: {decoded}")
                
            # if there is an OSError (usually because of a critical error or client disconnect)
            except OSError as error:
                # log the error
                self.logger.error(error)
                # exit the client listener
                break
            # if there is a JSONDecodeError (the data sent by the client is not a valid JSON string)
            except json.decoder.JSONDecodeError as error:
                # log the error
                self.logger.error(error)
                # reset to the top of the data fetch loop
                continue
            # if the decoded dictionary is not correctly formatted
            if not decoded.get("header", None) or not decoded.get("data", None):
                # reset to the top of the data fetch loop
                continue
            # if the header of the decoded data indicates that a command has been sent
            if decoded.get("header") == "command":
                # log the received data/command
                self.logger.debug(f"Handling command: {decoded.get('data')}")
                # pass the data into the client instances command processor method
                self.__process_command(decoded.get("data").get("command"))
            # if the header of the decoded data indicaties that an answer has been sent
            elif decoded.get("header") == "answer" and self.state == State.IN_GAME and self.game:
                # log the received data/answer
                self.logger.debug(f"Handling answer: {decoded.get('data')}")
                # pass the data into the client instances answer processor method
                self.__process_answer(decoded.get("data").get("answer"))
                
        # when the client listener exits, notify the server manager that the client has disconnected
        self.__manager.client_exit(self)

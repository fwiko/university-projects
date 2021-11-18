from __future__ import annotations

import json
import socket
import threading
from dataclasses import dataclass

from modules import State, Helpers, Logger

class Game:
    """Game class - storing information and management of active quiz games/lobbies"""
    __current_game = None
    
    def __init__(self, owner: Client, server: Server):
        self.__server: Server = server
        self.__settings = GameData(Helpers.generate_code(5), owner, [owner])
        self.logger: Logger = Logger(f"Game-{self.__settings.code}")
        
        self.logger.info(f"Game created by {owner.get_username()}")
        
    # SETTER/MODIFICATION METHODS
    
    def add_client(self, client: Client) -> None:
        """Add a client to the list of clients in the game"""
        # add the specified client to the list of players in the game
        self.__settings.players.append(client)
        self.logger.debug(f"Client with identifier #{client.get_uid()} added to Game ({self.get_code()})")
        
    def remove_client(self, client: Client) -> None:
        """Remove a client from the list of clients in the game"""
        # remove the specified client from the list of players in the game
        self.__settings.players.remove(client)
        self.logger.debug(f"Client with identifier #{client.get_uid()} removed from Game ({self.get_code()})")
    
    def close_game(self) -> None:
        """function called to completely close a game"""
        # Setting the games status to False (in-active)
        self.__settings.active: bool = False
        # Removing the game from the servers list of active games
        self.__server.remove_game(self)
        # Loop through all players in the game and set their game to None
        for player in self.__settings.players:
            player.set_game(None)
        # Change the state of all players in the game to inMenu therefore allowing them to join another game
        self.state_change(State.IN_MENU)
        self.logger.info(f"Game ({self.get_code()}) has been closed ")
        
    # CLIENT INTERACTION
        
    def send_data(self, header: str, data: dict, client: Client = None) -> None:
        """Send data to all clients or a specified client in the game"""
        # checking whether the a client parameter has been specified
        if not client:
            # if not, loop through all clients in the game and send the data to them
            for c in self.__settings.players:
                c.send(header, data)
        else:
            # if a client parameter has been specified, send the data to that client in particular
            client.send(header, data)
            
    def alert(self, message: str, client: Client = None) -> None:
        """Alert all clients or a specified client in the game with a message"""
        # send an 'alert' data packet to all clients or a specified client with data specified in the 'message' parameter
        self.send_data("alert", message, client) 
        
    def state_change(self, state: 'State', client: Client = None) -> None:
        """Change the state of clients in the game"""
        # checking whether a client parameter has been specified
        if not client:
            # if not, loop through all clients in the game and change their state
            for c in self.__settings.players:
                c.set_state(state)
        else:
            # if a client parameter has been specified, change the state of that client in particular
            client.set_state(state)
            
    def ask_question(self, question: str) -> None:
        """ask a question to all clients in the game"""
        # send a 'question' data packet to all clients in the game specifying the question within the 'question' parameter
        self.send_data("question", {"question": "What is your name?"})
    
    # QUIZ RELATED
    
    def __question_sequence(self) -> None:
        """function to run the question sequence - going through all questions in chosen topic and asking them"""
        pass
    
    # GAME INTERACTION
    
    def submit_answer(self, client: Client, answer: str) -> None:
        """handle the submission of answers to questions by the client"""
        # adding the client who submitted an answer to the submitted list of the current question (so they can't submit again)
        self.__current_game.current_question.submitted.append(client)
        self.logger.info(f"Client {client.get_username()} submitted answer {answer}")
        # checking whether the client has already submitted an answer or not
        if not self.__current_game or client in self.__current_game.get("current_question").get("submitted"):
            # if they have, return and do not handle the answer
            self.logger.debug(f"Client {client.get_username()} tried to submit again after submitting or is not currently in a game")
            return
        # checking whether the answer is correct
        if answer in self.__current_game.get("current_question").get("answer"):
            # if the answer is correct, increment the client's score by 1
            self.__current_game.scores[client.get_uid()] += 1
            self.logger.debug(f"Client {client.get_username()} answered question \"{__current_game.get('current_question')}\" correctly")

    def start(self) -> None:
        """start the quiz game"""
        # if there is already an active game and this function has somehow been called return (cancel the start operation)
        if self.__current_game:
            return
        # initialise a fresh (empty) game data object
        # creating empty leaderboard dictionary with the client's uid as the key and the score as the value
        scores_table: dict = {key: value for (key, value) in [(p.get_uid(), 0) for p in self.__settings.get("players")]}
        # creating a new game data object with the settings of the game and scores

        self.__current_game = QuizData(False, scores_table, [], {})
        # setting the state of all users to inGame
        self.state_change(State.IN_GAME)
        # setting the game to active
        self.__current_game.active = True
        # starting the quiz game, starting as a seperate thread (coroutine) to allow further interaction with the backend game if necessary
        threading.Thread(target=self.__start_quiz).start()
        
    def end(self) -> None:
        """end the quiz game"""
        # if there is not an active game, return (cancel the end operation)
        if not self.__current_game:
            return
        # setting the game object to None
        self.__current_game = None
        # setting the state of all users to inLobby
        self.state_change(State.IN_LOBBY)
        self.logger.info(f"Quiz in Game {self.get_code()} has ended, resetting data..")
        
    # EVENT HANDLING
    
    def client_leave(self, client: Client) -> None:
        """handle a client leaving the game"""
        # if the client that called this event is in the current game
        if client in self.__settings.players:
            # remove the client from the game
            self.remove_client(client)
            self.logger.info(f"Client {client.get_username()} has left Game {self.get_code()}")


class Client:
    """Client class - used for handling of connected clients"""
    __alive: bool = False

    def __init__(self, server: Server, conn, addr, uid: int) -> None:
        self.logger = Logger(f"Client-{uid}")
        self.__conn = conn
        print(type(self.__conn))
        self.__addr = addr
        print(type(self.__addr))
        self.__server: Server = server
        self.__settings = namedtuple(
            'ClientData',
            ['state', 'username', 'uid', 'commands', 'game'])
        (State.IN_MENU, f'Client-{uid}', uid, {}, None)

    def listen(self):
        """Start listening to client - listen for data sent from client and handle it"""
        # setting the alive status of the client to True meaning it is currently connected
        self.__alive: bool = True
        # while the client is alive, listen for data sent from the client
        while self.__alive:
            # try to receive adequate data from the client
            try:
                # receive and decode data sent from the client
                data: str = self.__conn.recv(1024).decode('utf-8')
                # if data is empty, it means the client has disconnected or that there has been an error so close the connection
                if not data: break
                # load the data into json format - all data sent from clients should be in json format
                decoded = json.loads(data)
                self.logger.info(f"Received data from {self.__addr}: {decoded}")

            # if the client has disconnected (through a connection/socket error), set the alive status of the client to False and break the loop
            except WindowsError:
                self.logger.debug(f"Connection/Socket error on {self.__addr}")
                self.__alive = False

            # if there is an error decoding the data, log it and continue (reset to the top of) the loop
            except json.decoder.JSONDecodeError:
                self.logger.error(f"Invalid JSON data received from {self.__addr}")
                continue

            # if the data received doesn't have a header or doesn't contain any data, continue (reset to the top of) the loop
            if not decoded.get("header", None) or not decoded.get("data", None):
                continue

            # if the data received has a header and contains data, handle the data
            # if the header is 'command' handle the data as a command
            if decoded["header"] == "command":
                self.__handle_command(decoded["data"].get("command"))
            # if the header is 'answer' and the user is inGame handle the data as an answer
            elif self.__settings.get("state", None) == State.IN_GAME and decoded["header"] == "answer":
                self.__handle_answer(decoded["data"].get("answer"))

        # if the client is not alive and the while loop has been broken out of, remove the client from the server
        __server.client_disconnected(self)

    # SETTER METHODS

    def set_state(self, state: 'State') -> None:
        """Set the state of the client"""
        self.__settings.state = state
        self.send("state", {"state": 'State'})
        self.logger.info(f"State set to {state}")

    def set_username(self, username: str) -> None:
        """Set the username of the client"""
        self.__settings.username = username
        self.logger.info(f"Username set to {username}")

    def set_game(self, game: 'Game') -> None:
        """Set the game of the client"""
        self.__settings.game = game
        self.logger.info(f"Game set to {self.__settings.game}")

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
        """Get the handler functions of the client"""
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
        # creation of a new game object with the client as the owner/creator
        new_game: Game = Game(self)
        # add the game to the server's list of known/active games
        self.__server.add_game(new_game)
        # set the state of the client to inLobby
        self.set_state(State.IN_LOBBY)
        # set the game of the client to the new game that was created
        self.set_game(game)

    def __join_game(self, game_code: str) -> None:
        """Handle the join game command"""
        # fetching the game with the given game code from the server
        game = self.__server.get_game_from_code(game_code.upper())
        # if there is not a game with the given code, return
        if not game: return
        # set the game of the client to the game fetched from the code
        self.set_game(game)
        # add the client to the game that was fetched from the code
        game.add_client(self)
        # set the state of the client to inLobby
        self.set_state(State.IN_LOBBY)

    def __leave_game(self) -> None:
        """Handle the leave game command"""
        # if the client is not in a game, return (they can't leave a game if they aren't in one)
        if self.get_state() not in (State.IN_GAME, State.IN_LOBBY) or not self.get_game():
            return
        # trigger the client_leave event of the game the client is in indicating the client wants to leave
        self.__settings.game.client_leave(self)
        # setting the game of the client to None as they are no longer in a game
        self.set_game(None)
        # setting the state of the client to a inMenu
        self.set_state(State.IN_MENU)

    def __get_games(self) -> None:
        """Handle the get games command"""
        # send a dictionary of all joinable games and the player count of those games to the client
        self.send("games", {"game_list": [{"code": 'Game'.get_code(), "players": len(game.get_players())} for game in
                                        self.__server.get_games()]})

    def __start_game(self) -> None:
        """Handle the start game command"""
        # if the client is not in a lobby or is not the owner of the lobby/game return
        if self.get_state() != State.IN_LOBBY or not self.get_game() or client != self.get_game().get_owner():
            return
        # start the game that the client is in and is the owner of, therefore beginning the quizzing process
        self.get_game().start()

    # SERVER INTERACTION METHODS

    def __handle_command(self, command: str) -> None:
        """Handle a command sent from the client"""
        # split the passed in command string into a list, without repeating spaces and with no empty strings
        parsed_data: list = (re.sub(' +', ' ', command.strip())).lower().split(" ")
        # setting the first element of the list as the command variable
        cmd: str = parsed_data[0]
        # setting the remaining second to last elements of the list as the arguments variable (if there are any)
        args: list = parsed_data[1:]
        # get the handler relative to the command that was passed in (if one exists)
        handler = self.__get_handlers().get(cmd, None)
        # if the handler for the input command does exist
        if handler:
            # call the fetched handler function and pass in the arguments (if there are any)
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

"""

Server class used for maangement of games and connected clients

"""

class Server:
    __running = False
    __games = []
    __clients = []
    __data = namedtuple('ServerData', ['games', 'clients', 'nuid'])([], [], 1)
    
    def __init__(self, host: str, port: int) -> None:
        self.__host = host
        self.__port = port
        self.logger = Logger("Server")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def start(self) -> None:
        """Start the server - wait for and handle connections from clients"""
        
        # Opening the socket for listening
        with self.socket as sock:
            sock.bind((self.__host, self.__port))
            sock.listen(5)
            self.logger.info(f"Listening on {self.__host}:{self.__port}")
        
            # Begin listening for and handling connections
            self.__running = True
            while self.__running:
                # Accepting a new connection fron a Client socket
                conn, addr = sock.accept()
                # Creation of new object using the Client class
                new_client = Client(self, conn, addr, self.__data.nuid)
                # Incrementing the next unique ID
                self.__data.nuid += 1
                # Starting the client listener
                threading.Thread(target=new_client.listen).start()
                # Adding Client objects to list of known/active clients
                self.__add_client(new_client)
                self.logger.info("Connection from {}:{}".format(*addr))

        self.logger.info("Server stopped")     

    def stop(self) -> None:
        """Stop the server - setting the __running value stopping process of listening for connections"""
        self.__running = False
        
    # SETTER/MODIFICATION METHODS
    
    def add_game(self, game: 'Game') -> None:
        """Add a game to the list of known games"""
        self.__data.games.append(game)
        
        self.logger.info(f"Game with identifier {game.get_code()} added")
    
    def remove_game(self, game: 'Game') -> None:
        """Remove a game from the list of known games"""
        self.__data.games.remove(game)
        
        self.logger.info(f"Game with identifier {game.get_code()} removed")
        
    def add_client(self, client: Client) -> None:
        """Add a client to the list of known clients"""
        self.__data.clients.append(client)
        
        self.logger.info(f"Client with identifier {client.get_uid()} added")
    
    def remove_client(self, client: Client) -> None:
        """Remove a client from the list of known clients"""
        self.__data.clients.remove(client)
        
        self.logger.info(f"Client with identifier {client.get_uid()} removed")
    
    # GETTER METHODS
    
    def get_games(self) -> list:
        """Return the list of known games"""
        return self.__data.games
    
    def get_clients(self) -> list:
        """Return the list of known clients"""
        return self.__data.clients
    
    def get_game_from_code(self, code: str) -> 'Game':
        """Return the game with the given code"""
        return next((x for x in self.get_games() if x.get_code() == code), None)
    
    def get_client_from_id(self, uid: int) -> Client:
        """Return the client with the given ID"""
        return next((x for x in self.get_clients() if x.get_uid() == uid), None)
    
    # EVENTS
    
    def client_disconnected(self) -> None:
        """function called by a client object when it disconnects or stops responding"""
        self.remove_client(client)
        client_game = client.get_game()
        if client_game:
            client_game.client_leave(client)
            
        self.logger.info("Disconnect from {}:{}".format(*client.get_address()))

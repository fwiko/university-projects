import json
import socket
import threading
from collections import namedtuple

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Logger, Server, Game, State, Helpers, Client

class Game:
    """Game class - storing information and management of active quiz games/lobbies"""
    QuestionData = namedtuple('QuestionData', ['question', 'answer', 'submitted'])
    GameData = namedtuple('GameData', ['active', 'scores', 'current_question', 'questions'])
    __current_game = None
    
    def __init__(self, owner: Client, server: 'Server'):
        self.__server = server
        self.__settings = namedtuple('GameData', ['code', 'owner', 'players'])(Helpers.generate_code(5), owner, [owner])
        self.logger = Logger(f"Game-{self.__settings.code}")
        self.logger.info(f"Game created with code {self.__settings.code} by {owner.get_username()}")
        
    # SETTER/MODIFICATION METHODS
    
    def add_client(self, client: Client) -> None:
        """Add a client to the list of clients in the game"""
        self.__settings.players.append(client)
        
        self.logger.debug(f"Client with identifier #{client.get_uid()} added to Game {self.get_code()}")
        
    def remove_client(self, client: Client) -> None:
        """Remove a client from the list of clients in the game"""
        self.__settings.players.remove(client)
        
        self.logger.debug(f"Client with identifier #{client.get_uid()} removed from Game {self.get_code()}")
    
    def close_game(self) -> None:
        """function called to completely close a game"""
        self.__active = False
        self.__server.remove_game(self)
        
        for player in self.__settings.players:
            player.set_game(None)
            
        self.state_change(State.IN_MENU)
        
        self.logger.info(f"Game ({self.get_code()}) has been closed closed")
        
    # CLIENT INTERACTION
        
    def send_data(self, header: str, data: dict, client: Client = None) -> None:
        """Send data to all clients or a specified client in the game"""
        if not client:
            for c in self.__settings.players:
                c.send(header, data)
        else:
            client.send(header, data)
            
    def alert(self, message: str, client: Client = None) -> None:
        """Alert all clients or a specified client in the game"""
        self.send_data("alert", message, client)
        
    def state_change(self, state: 'State', client: Client = None) -> None:
        """Change the state of clients in the game"""
        if not client:
            for c in self.__settings.players:
                c.set_state(state)
        else:
            client.set_state(state)
            
    def ask_question() -> None:
        """ask a question to all clients in the game"""
        self.send_data("question", {"question": "What is your name?"})
    
    # QUIZ RELATED
    
    def __question_sequence(self) -> None:
        """function to run the question sequence - going through all questions in chosen topic and asking them"""
        pass
    
    # GAME INTERACTION
    
    def submit_answer(self, client: Client, answer: str) -> None:
        """handle the submission of answers to questions by the client"""
        self.logger.debug(f"Client {client.get_username()} submitted answer {answer}")
        if not self.__current_game or client in self.__current_game.get("current_question").get("submitted"):
            self.logger.debug(f"Client {client.get_username()} tried to submit again after submitting or is not currently in a game")
            return
    
        if answer in self.__current_game.get("current_question").get("answer"):
            self.logger.debug(f"Client {client.get_username()} answered question \"{__current_game.get('current_question')}\" correctly")

    def start(self) -> None:
        """start the quiz game"""
        if self.__current_game:
            return
        
        scores_table = {key: value for (key, value) in [(p.get_uid(), 0) for p in self.__settings.get("players")]}
        self.__current_game = GameData(False, scores_table, QuestionData("", "", []), Helpers.get_questions()) 
        
        self.state_change(State.IN_GAME)
        self.__current_game.active = True
        
        threading.Thread(target=self.__start_quiz).start()
        
    def end(self) -> None:
        """end the quiz game"""
        if not self.__current_game:
            return
        
        self.__current_game = None
        self.state_change(State.IN_LOBBY)
        
        self.logger.info(f"Quiz in Game {self.get_code()} has ended, resetting data..")
        
    # EVENT HANDLING
    
    def client_leave(self, client: Client) -> None:
        """handle a client leaving the game"""
        if client in self.__settings.players:
            self.remove_client(client)
            self.logger.info(f"Client {client.get_username()} has left Game {self.get_code()}")

from . import Logger, Server, Game, State, Helpers, Client

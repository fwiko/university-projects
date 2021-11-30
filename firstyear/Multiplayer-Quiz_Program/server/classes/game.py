from __future__ import annotations

# importing python packages
import time
import json
import threading
from dataclasses import dataclass

# importing custom classes/files
import classes.client as client
import classes.manager as manager
from utility import Logger, State, Helpers

@dataclass
class QuizData:
    """data class used to store quiz data"""
    scores: dict[int, int]
    questions: list[dict]
    current_question: dict[str, str]
    
@dataclass
class GameData:
    """data class used to store game/game lobby data"""
    code: str
    owner: client.Client
    players: list[client.Client]
    active: bool = False

class Game:
    __current_quiz: QuizData or None = None
    def __init__(self, manager: manager.Manager, creator: client.Client):
        """ititializes the game object

        Args:
            manager (manager.Manager): the manager object of the game server which will be used to manage the game
            creator (client.Client): the client object which created the game
        """
        self.__manager = manager
        self.settings = GameData(Helpers.generate_code(5), creator, [creator])
        self.logger = Logger(f"{self.__class__.__name__}-{self.settings.code}")
        self.logger.info("Game has been created")
        
    @property
    def settings(self) -> GameData:
        """getter method for the game objects settings attribute

        Returns:
            GameData: the game objects settings attribute (an object of the GameData dataclass)
        """
        return self.__settings
    
    @settings.setter
    def settings(self, settings: GameData):
        """setter method to set the game objects settings attribute

        Args:
            settings (GameData): value to set the objects settings property/attribute to
        """
        # checking whether the passed in settings value is a GameData object
        if isinstance(settings, GameData):
            # if it is, set the objects settings property to the passed in value
            self.__settings = settings
            self.logger.info(f"Game settings have been updated: {settings.__dict__}")
        else:
            # if not, log an error and do nothing
            self.logger.error(f"Attempted to set invalid settings \"{settings}\"")
            
    # information/getter methods
    
    def is_active(self) -> bool:
        """method to check if the game is active (currently in a quiz)

        Returns:
            bool: the active state of the game True if active, False if not
        """
        return self.settings.active
            
    # management methods
    
    def add_client(self, client_object: client.Client) -> None:
        """method to add a client to the game

        Args:
            client_object (client.Client): an object of the client class which will be added to game objects list of players
        """
        # checking whether the passed in client object is a in the game objects list of players
        if client in self.settings.players:
            # if it is, do nothing
            return
        # if not, add the client to the game objects list of players
        self.settings.players.append(client_object)
        self.alert(f"{client_object.username} has joined the game!", [client_object])
        self.logger.info(f"Added client {client_object.username}")
    
    def remove_client(self, client: client.Client) -> None:
        """method to remove a client from the game

        Args:
            client (client.Client): an object of the client class which will be removed from the game objects list of players
        """
        # checking whether the passed in client object is not in the game objects list of players
        if client not in self.settings.players:
            # if not, do nothing
            return
        # if it is, remove the client from the game objects list of players
        self.settings.players.remove(client)
        self.alert(f"{client.username} has left the game.")
        self.logger.info(f"Removed client {client.username}")
    
    def close_game(self) -> None:
        """method to close the game and remove it from the manager"""
        # calling the game_close method within the game server manager object,
        # removing the game object from the list of active games
        self.__manager.game_close(self)
        # change the state of all players in the game to IN_MENU
        self.state_change(State.IN_MENU)
        # alert all players in the game that the game has been closed
        self.alert(f"Game {self.settings.code} has been closed")
        # set the game of all players to None
        for client in self.settings.players:
            client.game = None
        self.logger.info("Game has been closed")
        
    # client interaction methods
    
    def _send_data(self, header: str, data: dict[str: str]) -> None:
        """method to send data to all clients in the game

        Args:
            header (str): header value of data "packet" to be sent
            data (dict): actual data to be sent
        """
        # for each player in the game objects list of players
        for c in self.settings.players:
            # send the data to the player
            c.send(header, data)
    
    def alert(self, message: str, blacklist: list[client.Client] = None) -> None:
        """method to send a message to all clients in the game with an exception of those in the blacklist

        Args:
            message (str): message value to be sent to all clients in the game
            blacklist (list[client.Client]): list of clients not to send an alert to
        """
        # if the blacklist value is not specified
        if not blacklist:
            # set the blacklist to an empty list (must do this instead of setting default value to a mutable value)
            blacklist = []
        # get a list of all clients in the game objects list of players except for those in the blacklist
        allowed_players = [c for c in self.settings.players if c not in blacklist]
        # for each client in the allowed players list
        for c in allowed_players:
            # send the alert message to the client
            c.send("alert", {"message": message})
        
    def question(self, question: str) -> None:
        """method to send a question to all clients in the game object

        Args:
            question (str): question value to be sent to all clients
        """
        self._send_data("question", {"question": question})
        
    def state_change(self, state: State) -> None:
        """method to change the state of all clients in the game object

        Args:
            state (State): state to change to
        """
        # for each client in the game objects list of players
        for client in self.settings.players:
            # set the client objects state to the passed in state
            client.state = state
            
    # quiz handling methods
    
    def start_quiz(self) -> None:
        """method to start a quiz within the current game object"""
        # set the game objects active state to True
        self.settings.active = True
        # change the state of all players in the game to IN_GAME
        self.state_change(State.IN_GAME)
        # get a set of questions
        chosen_question_set = Helpers.get_questions()
        # generate an empty leaderboard/scores table dictionary
        scores_table = {p.uid: {"score": 0, "username": p.username} for p in self.settings.players}
        # create a new QuizData object and set the game objects current_quiz attribute to it
        self.__current_quiz = QuizData(scores_table, chosen_question_set, None)
        # start the quiz sequence as a new thread
        threading.Thread(target=self._quiz_sequence).start()
        self.logger.info("Quiz has started")
    
    def end_quiz(self) -> None:
        """method to end the quiz within the current game object"""
        # if the game object doesn't have a currently running quiz
        if not self.__current_quiz:
            # do nothing, cancel
            return
        # send the sorted leaderboard to all players in the game
        self._send_data("quiz_stats", dict(sorted(self.__current_quiz.scores.items(), key=lambda x: x[1]["score"], reverse=True)))
        # set the current quiz to None within the game object
        self.__current_quiz = None
        # change the active state of the game to False
        self.settings.active = False
        # change the state of all players in the game to IN_LOBBY
        self.state_change(State.IN_LOBBY)
        self.logger.info("Quiz has ended")
        
    def handle_answer(self, game_client: client.Client, answer: str) -> None:
        """method to handle an answer from a client within the current game object when a quiz is running

        Args:
            game_client (client.Client): the client object which sent the answer
            answer (str): the answer sent by the client
        """
        self.logger.info(f"{game_client.username} submitted answer '{answer}'")
        # if the game object doesn't have a currently running quiz
        if not self.__current_quiz or not self.__current_quiz.current_question:
            # do nothing, cancel
            return
        # if the client who submitted the answer has not already submitted an answer
        if game_client not in self.__current_quiz.current_question.get("submitted"):
            # add the client to the submitted list of the current question
            self.__current_quiz.current_question["submitted"].append(game_client)
            # if the answer is correct
            if answer in self.__current_quiz.current_question.get("answer"):
                # increment the clients score
                self.__current_quiz.scores[game_client.uid]["score"] += 1
    
    def _quiz_sequence(self) -> None:
        """method to run the quiz sequence within the current game object (asks questions until all questions have been asked)"""
        # alert all clients that the quiz will be starting in 5 seconds
        self.alert("Quiz starting in 5 seconds!")
        # wait 5 seconds
        time.sleep(5)
        # if the quiz has been cancelled, game closed, etc..
        if not self.__current_quiz:
            # cancel the quiz sequence
            return
        # for each question in the chosen set of questions
        for num, (q, a) in enumerate(self.__current_quiz.questions):
            # set the current question to the question relative to the current question index
            self.__current_quiz.current_question = {
                "question": q,
                "answer": a,
                "submitted": []
            }
            # ast all players in the current game the question
            self.question(f"Question {num + 1}: {q}")
            # while not all clients have answered the question
            while len(self.__current_quiz.current_question.get("submitted")) != len(self.settings.players):
                # wait two tenths of a second
                time.sleep(.2)
                # if the quiz has been closed/cancelled or game closed
                if not self.__current_quiz:
                    # cancel the quiz sequence
                    return
        # after all questions have been asked and answered, end the quiz
        self.end_quiz()
    
    # event handlers
    
    def client_leave(self, client: client.Client) -> None:
        """method to handle a client leaving the game

        Args:
            client (client.Client): client object which has left the game
        """
        # if the client is not in the game object list of players
        if client not in self.settings.players:
            # do nothing, cancel
            return
        # otherwise remove the client from the game objects list of players
        self.remove_client(client)
        if client == self.settings.owner:
            self.close_game()

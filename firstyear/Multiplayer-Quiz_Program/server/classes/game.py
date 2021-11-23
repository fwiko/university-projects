from __future__ import annotations

import time
import json
import threading

from dataclasses import dataclass

import classes.client as client
import classes.manager as manager
from modules import Logger, State, Helpers

@dataclass
class QuizData:
    scores: dict[int, int]
    questions: list[dict]
    current_question: dict[str, str]
    
@dataclass
class GameData:
    code: str
    owner: client.Client
    players: list[client.Client]
    active: bool = False

class Game:
    __current_quiz: QuizData or None = None
    def __init__(self, manager: manager.Manager, creator: client.Client):
        self.__manager = manager
        self.settings = GameData(Helpers.generate_code(5), creator, [creator])
        self.logger = Logger(f"{self.__class__.__name__}-{self.settings.code}")
        self.logger.info("Game has been created")
        
    def __repr__(self):
        return f"{self.__class__.__name__}-{self.settings.code}"
        
    @property
    def settings(self):
        return self.__settings
    
    @settings.setter
    def settings(self, settings: GameData):
        if isinstance(settings, GameData):
            self.__settings = settings
        else:
            self.logger.error(f"Attempted to set invalid settings \"{settings}\"")
            
    # information/getter methods
    
    def is_active(self) -> bool:
        return self.settings.active
            
    # management methods
    
    def add_client(self, client_object: client.Client) -> None:
        if client in self.settings.players:
            return
        self.settings.players.append(client_object)
        self.alert(f"{client_object.username} has joined the game!", [client_object])
        self.logger.debug(f"Added client {client_object.username}")
    
    def remove_client(self, client: client.Client) -> None:
        if client not in self.settings.players:
            return
        self.settings.players.remove(client)
        self.alert(f"{client.username} has left the game.")
        self.logger.debug(f"Removed client {client.username}")
    
    def close_game(self) -> None:
        self.__manager.game_close(self)
        self.__current_quiz = None
        self.state_change(State.IN_MENU)
        for client in self.settings.players:
            client.game = None
            
        self.logger.info("Game has been closed")
        
    # client interaction methods
    
    def _send_data(self, header: str, data: dict[str: str]) -> None:
        for c in self.settings.players:
            c.send(header, data)
    
    def alert(self, message: str, blacklist: list[client.Client] = []) -> None:
        allowed_players = [c for c in self.settings.players if c not in blacklist]
        for c in allowed_players:
            c.send("alert", {"message": message})
        
    def question(self, question: str) -> None:
        self._send_data("question", {"question": question})
        
    def state_change(self, state: State) -> None:
        for client in self.settings.players:
            client.state = state
            
    # quiz handling methods
    
    def start_quiz(self) -> None:
        self.settings.active = True
        self.state_change(State.IN_GAME)
        chosen_question_set = Helpers.get_questions()
        print(chosen_question_set)
        scores_table = {p.uid: {"score": 0, "username": p.username} for p in self.settings.players}
        self.__current_quiz = QuizData(scores_table, chosen_question_set, None)
        threading.Thread(target=self._quiz_sequence).start()
    
    def end_quiz(self) -> None:
        if not self.__current_quiz:
            return
        self._send_data("quiz_stats", dict(sorted(self.__current_quiz.scores.items(), key=lambda x: x[1]["score"], reverse=True)))
        self.__current_quiz = None
        self.settings.active = False
        self.state_change(State.IN_LOBBY)
        self.logger.info("Quiz has ended")
        
    def handle_answer(self, game_client: client.Client, answer: str) -> None:
        self.logger.info(f"{game_client.username} submitted answer '{answer}'")
        if not self.__current_quiz or not self.__current_quiz.current_question:
            return
        if game_client not in self.__current_quiz.current_question.get("submitted"):
            self.__current_quiz.current_question["submitted"].append(game_client)
            if answer in self.__current_quiz.current_question.get("answer"):
                self.__current_quiz.scores[game_client.uid]["score"] += 1
    
    def _quiz_sequence(self) -> None:
        self.alert("Quiz starting in 5 seconds!")
        time.sleep(5)
        if not self.__current_quiz:
            return
        for q, a in self.__current_quiz.questions.items():
            self.__current_quiz.current_question = {
                "question": q,
                "answer": a,
                "submitted": []
            }
            self.question(q)
            
            while len(self.__current_quiz.current_question.get("submitted")) != len(self.settings.players):
                time.sleep(.2)
                if not self.__current_quiz:
                    return
                
        self.end_quiz()
    
    # event handlers
    
    def client_leave(self, client: client.Client) -> None:
        if client not in self.settings.players:
            return
        self.remove_client(client)
        if client == self.settings.owner:
            self.close_game()
        
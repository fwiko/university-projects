from quizgame import Client
from dataclasses import dataclass


@dataclass
class QuizData:
    active: bool
    scores: dict
    questions: list
    current_question: dict
    
@dataclass
class GameData:
    code: int
    owner: Client
    players: list
    
@dataclass
class ClientData:
    id: int
    name: str
    score: int
    game: int
    active: bool
    ready: bool
    socket: int
    

import random
import string
from enum import Enum

class State(Enum):
    """Enum for the state of the client"""
    IN_MENU = "inMenu"
    IN_LOBBY = "inLobby"
    IN_GAME = "inGame"

class Helpers:
    
    @staticmethod
    def generate_code(length: int) -> str:
        """return a random string of specified length"""
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))
    
    @staticmethod
    def get_questions() -> dict:
        """return a dictionary including questions and answers to the chosen topic"""
        with open("data/questions_database.json", "r") as f:
            try:
                loaded_data = json.load(f)
            except json.decoder.JSONDecodeError:
                return {}
            
            return random.choice(loaded_data.get("_questions", []))
        
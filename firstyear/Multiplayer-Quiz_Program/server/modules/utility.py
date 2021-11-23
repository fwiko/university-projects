import os
import json
import random
import string
import settings
import datetime
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
        with open(os.path.join(settings.QUESTION_PATH, "questions.json"), "r") as f:
            try:
                loaded_data = json.load(f)
            except json.decoder.JSONDecodeError:
                return {}
            
            return random.choice(loaded_data.get("_questions", []))
        
class Logger:
    def __init__(self, logger_name: str):
        self.logger_name = logger_name
    
    @staticmethod
    def get_time():
        """returns the current timestamp"""
        return datetime.datetime.now()
    
    def __log(self, prefix: str, message: str):
        """prints a final log"""
        log_file = os.path.normpath(os.path.join(os.path.dirname(__file__)+ os.sep + os.pardir + os.sep + settings.LOG_PATH + os.sep + "server.log"))
        log_string = f"{self.get_time().strftime('%d-%m-%Y %H:%M:%S')} - {self.logger_name}:{prefix} - {message}"
        with open(log_file, "a+") as log:
            log.write(log_string + "\n")
        print(log_string)
    
    def error(self, message: str):
        """logs an error log"""
        self.__log("ERROR", message)
    
    def info(self, message: str):
        """logs an info log"""
        self.__log("INFO", message)
        
    def debug(self, message: str):
        """logs a debug log"""
        if settings.DEBUG:
            self.__log("DEBUG", message)

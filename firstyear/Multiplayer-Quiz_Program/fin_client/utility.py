import os
import settings

from enum import Enum
import datetime

import pyfiglet
import time


def cls():
    os.system('cls' if os.name=='nt' else 'clear')
    time.sleep(0.1)
    print(pyfiglet.figlet_format("Quiz Game", font = "rectangles"))


class State(Enum):
    """Enum for the state of the client"""
    IN_MENU = "inMenu"
    IN_LOBBY = "inLobby"
    IN_GAME = "inGame"


class Logger:
    
    @staticmethod
    def get_time():
        """returns the current timestamp"""
        return datetime.datetime.now()
    
    def __log(self, prefix: str, message: str):
        """prints a final log"""
        log_file = os.path.normpath(os.path.join(os.path.dirname(__file__) + os.sep + settings.LOG_PATH + os.sep + "server.log"))
        log_string = f"{self.get_time().strftime('%d-%m-%Y %H:%M:%S')} - {self.__class__.__name__}:{prefix} - {message}"
        with open(log_file, "a+") as log:
            log.write(log_string + "\n")
        
    def error(self, message: str):
        """logs an error log"""
        self.__log("ERROR", message)
    
    def info(self, message: str):
        """logs an info log"""
        self.__log("INFO", message)
        
    def debug(self, message: str):
        """logs a debug log"""
        self.__log("DEBUG", message)

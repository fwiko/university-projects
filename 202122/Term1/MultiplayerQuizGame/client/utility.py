# import python packages
import datetime
import os
import time
from enum import Enum

# import third party packages
import pyfiglet

import settings


def clear_screen():
    """clear the CLI screen"""
    # if the operating system is windows execute the 'cls' command
    # if the operating system is unix based execute the 'clear' command
    os.system("cls" if os.name == "nt" else "clear")
    # wait a tenth of a second
    time.sleep(0.1)
    # output the 'title'/header text
    print(pyfiglet.figlet_format("Quiz Game", font="rectangles", width=80))


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
        """prints a final log

        Args:
            prefix (str): prefix for the log e.g. ERROR, INFO, DEBUG
            message (str): message for the log e.g. "This is an error message"
        """
        # get the directory path to store the logs
        log_path = os.path.normpath(
            os.path.join(
                os.path.dirname(__file__) + os.sep + settings.LOG_PATH + os.sep
            )
        )
        # create the directory if it doesn't exist
        if not os.path.exists(log_path):
            print("Creating log directory")
            os.makedirs(log_path)
        # get the whole log path including the file
        log_file = os.path.join(log_path, "client.log")
        # generate the log message
        log_string = f"{self.get_time().strftime('%d-%m-%Y %H:%M:%S')} - {self.__class__.__name__}:{prefix} - {message}"
        # save the log message to the file
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

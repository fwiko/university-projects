
# import python packages
import os
import json
import random
import string
import settings
import datetime
from enum import Enum


def normalise_path(*path) -> str:
    """normalises a path"""
    return os.path.normpath(os.path.join(*path))


class State(Enum):
    """Enum for the state of the client - prevents state attributes being set to invalid values"""
    IN_MENU = "inMenu"
    IN_LOBBY = "inLobby"
    IN_GAME = "inGame"
    

class Helpers:
    
    @staticmethod
    def generate_code(length: int) -> str:
        """return a random string of specified length"""
        # combine a specified length of random uppercase letters and numbers into a string and return that string
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))
    
    @staticmethod
    def get_questions() -> dict or None:
        """return a dictionary including questions and answers to the chosen topic"""
        # find the directory that the questions database should be stored in
        questions_path = normalise_path(os.path.dirname(__file__), settings.QUESTION_PATH)
        # if the questions database file does not exist
        if not os.path.exists(questions_path):
            # return None - no questions to be found - this is a fatal error
            return None
        # if the questions database file does exist - open it - read it
        with open(os.path.join(questions_path, "questions.json"), "r") as f:
            try:
                # attempt to load the data stored in the questions file as a dictionary object
                loaded_data = json.load(f)
            except json.decoder.JSONDecodeError:
                # if the data could not be loaded - return None - this is a fatal error
                return None
            else:
                # if the data could be loaded - return a random set of questions from the database
                question_set = random.choice(loaded_data.get("_questions", []))
                try:
                    final_set = {"topic": question_set["topic"], "questions": random.sample(question_set["questions"].items(), settings.QUESTIONS_PER_QUIZ)}
                except ValueError:
                    final_set = question_set
                return final_set

class Logger:
    """Logger used throughout the server files to debug and log errors"""
    def __init__(self, logger_name: str):
        # setting the name of the logger depending on the class that created a logger instance
        self.logger_name = logger_name
    
    @staticmethod
    def get_time():
        """returns the current timestamp"""
        return datetime.datetime.now()

    def __log(self, prefix: str, message: str):
        """prints a final log"""
        # call the normalise path function and assign the returned value to a variable
        # this prevents errors when running the server file from an external location or script
        # connects the directory of the utiliy file to the log file directory
        log_path = normalise_path(os.path.dirname(__file__), settings.LOG_PATH) 
        # if the log directory does not exist
        if not os.path.exists(log_path):
            # create the log directory
            os.makedirs(log_path)
        # create the prefix/header of the log combining the current timestamp with the name of the logger instance and the passed in log message
        log_string = f"{self.get_time().strftime('%d-%m-%Y %H:%M:%S')} - {self.logger_name}:{prefix} - {message}"
        # open the log file in append mode
        with open(os.path.join(log_path, "server.log"), "a+") as log:
            # write the log string to the log file
            log.write(log_string + "\n")
        # print the log string to the console
        print(log_string)
    
    def error(self, message: str):
        """called upon an error - prefixes log with ERROR"""
        self.__log("ERROR", message)
    
    def info(self, message: str):
        """called for simple information logs - prefixes log with INFO"""
        self.__log("INFO", message)
        
    def debug(self, message: str):
        """called upon logs used for debugging - prefixes log with DEBUG - can be toggled on or off"""
        if settings.DEBUG:
            self.__log("DEBUG", message)

import datetime

class Logger:
    
    def __init__(self, logger_name: str):
        self.logger_name = logger_name
    
    @staticmethod
    def get_time():
        """returns the current timestamp"""
        return datetime.datetime.now()
    
    def __log(self, prefix: str, message: str):
        """prints a final log"""
        print(f"{self.get_time().strftime('%d-%m-%Y %H:%M:%S')} - {self.logger_name}:{prefix} - {message}")
    
    def error(self, message: str):
        """logs an error log"""
        self.__log("ERROR", message)
    
    def info(self, message: str):
        """logs an info log"""
        self.__log("INFO", message)
        
    def debug(self, message: str):
        """logs a debug log"""
        self.__log("DEBUG", message)

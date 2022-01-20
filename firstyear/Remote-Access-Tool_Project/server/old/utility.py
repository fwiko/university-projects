import argparse
import datetime
import os


# def parse_args(input_string: str) -> tuple[any, any]:
#     """
#     Parses the input string into a command paired with a list of optional arguments.
#     :param input_string: The input string to parse.
#     :return: The list of arguments.
#     """
#     command, *args = input_string.split()
#     return command, args
#

class Response:
    @staticmethod
    def err(message: str) -> None:
        print(f"\n[-] {message}\n")
        
    @staticmethod
    def out(message: str) -> None:
        print(f"\n[+] {message}\n")


def data_dir() -> str:
    """
    Returns the data directory.
    :return: The data directory.
    """
    return os.path.join(os.path.dirname(__file__), 'data')


def log_dir() -> str:
    """
    Returns the log directory.
    :return: The log directory.
    """
    return os.path.join(data_dir(), 'logs')


def screenshot_dir() -> str:
    """
    Returns the screenshot directory.
    :return: The screenshot directory.
    """
    path = os.path.join(data_dir(), 'screenshots')
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def download_dir() -> str:
    """
    Returns the download directory.
    :return: The download directory.
    """
    path = os.path.join(data_dir(), 'downloads')
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def upload_args(arg_string: str) -> tuple[str, str]:
    """
    Parses the upload arguments.
    :param arg_string: The argument string to parse.
    :return: The file path and remote path.
    """
    parser = argparse.ArgumentParser(description='Upload a file to the client.')
    parser.add_argument("s", help="ID of the session to upload to.")
    parser.add_argument("-f", "--file", help="The file to upload.", nargs='+')
    parser.add_argument("-d", "--directory", help="The location to upload to.", nargs='+')
    
    return parser.parse_args(arg_string)

print(upload_args(input(">").split(" ")))
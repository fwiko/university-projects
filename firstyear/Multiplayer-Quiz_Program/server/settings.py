

# listener settings
HOST = "0.0.0.0"
PORT = 5050

# logging settings
DEBUG = True
LOG_PATH = "data/logs/"

# question settings
QUESTION_PATH = "data/"

# client data settings

HELP_MENU = {
    "host": {"desc": "Host a game"},
    "join": {"desc": "Join a game", "args": ["game_id"]},
    "leave": {"desc": "Leave a game"},
    "games": {"desc": "List available games"},
    "start": {"desc": "Start a quiz"},
    "username": {"desc": "Set username", "args": ["username"]},
    "help": {"desc": "Show help menu"},
}
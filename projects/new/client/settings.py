# server addresses

HOST = "127.0.0.1"
PORT = 5050

# help commands

HELP_COMMANDS = {
    "host": {"desc": "Host a game"},
    "join": {"desc": "Join a game", "args": ["game_id"]},
    "leave": {"desc": "Leave a game"},
    "games": {"desc": "List available games"},
    "start": {"desc": "Start a quiz"},
    "username": {"desc": "Set username", "args": ["username"]},
    "help": {"desc": "Show help menu"},
}
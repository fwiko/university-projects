import os

# server addresses

HOST = "vps.ssh"
PORT = 5050

# logging settings
LOG_PATH = "data\\logs\\"

# help commands

COMMANDS = {
    "host": {"description": "Host a game"},
    "join": {"description": "Join a game", "args": ["<game_id>"]},
    "leave": {"description": "Leave a game"},
    "games": {"description": "List available games"},
    "start": {"description": "Start a quiz"},
    "username": {"description": "Set username", "args": ["<username>"]},
    "help": {"description": "Show help menu"},
}

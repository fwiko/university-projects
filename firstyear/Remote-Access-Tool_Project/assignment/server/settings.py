import os

HOST = "127.0.0.1"
PORT = 1337

FILE_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "files")

EXECUTE_BLACKLIST = ["cmd", "powershell", "bash", "sh", "nano", "vi", "vim", "emacs"]

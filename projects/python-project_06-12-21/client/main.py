import re
import time
import json
import socket
import threading

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 5050


if __name__ == '__main__':
    session = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    session.connect((SERVER_ADDRESS, SERVER_PORT))
    session.send(json.dumps({"action": "login", "username": "fwiko"}).encode('utf-8'))
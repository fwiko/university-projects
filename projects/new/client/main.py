import re
import time
import json
import socket
import threading

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 5050

class Session():
    def __init__(self, host: str, port: int):
        self.alive = True
        self._host = host
        self._port = port
    
    def start(self):
        """initiate the connection with the quiz server"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self._host, self._port))
            threading.Thread(target=self._receiver, args=[sock]).start()
            
    
    def _receiver(self, sock: socket.socket):
        """receive data sent from the quiz server
        function will run in a thread (coroutine) alongside the rest of the client"""
        while True:
            try:
                data = sock.recv(1024).decode('utf-8')
                if not data: break
                print(data)
            except Exception as e:
                print(e)
                break
        self.alive = False
        print("Connection closed")
    
    def _send(self):
        pass
    

if __name__ == '__main__':
    session = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    session.connect((SERVER_ADDRESS, SERVER_PORT))
    while True:
        message = input("> ")
        if message == "exit":
            break
        try:
            session.send(json.dumps({"header": "command", "data": {"command": message}}).encode('utf-8'))
        except Exception as e:
            print(e)
            input("Press enter to continue...")
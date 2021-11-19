import re
import time
import json
import socket
import threading

import settings

class Session():
    def __init__(self, host: str, port: int):
        self.alive = True
        self._host = host
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # server connection  

    def start(self):
        """initiate the connection with the quiz server"""
        with self._socket as sock:
            sock.connect((self._host, self._port))
            threading.Thread(target=self._receiver, args=[sock]).start()
    
    # receiving data from the server
    
    def _receiver(self, sock: socket.socket):
        """receive data sent from the quiz server
        function will run in a thread (coroutine) alongside the rest of the client"""
        while self.alive:
            try:
                data = sock.recv(1024).decode('utf-8')
                if not data: break
                print(data)
            except Exception as e:
                print(e)
                break
        self.alive = False
        print("Connection closed")
        
    # sending data to the server
    
    def _send(self, header: str, data: str):
        self._socket.send(json.dumps({header: header, "data": {header: data}}).encode('utf-8'))
        
    def _command(self, command: str):
        """handles user input"""
        self._send("command", command)
        
    def _answer(self, answer: str):
        self._send("answer", answer)
        
    # handling user input
    
    def _handlers(self):
        """handles user input"""
        return {
            "host": self._command(*args),
            "join": self._command(*args)
        }
    
    def input(self, input: str):
        """input and send it to the quiz server"""
        print(input.upper())
    

if __name__ == '__main__':
    session = Session(settings.HOST, settings.PORT)
    while True:
        message = input("> ")
        if message == "exit":
            break
        try:
            session.input(message)
        except Exception as e:
            print(e)
            input("Press enter to continue...")
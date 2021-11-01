import sys
import json
import socket
import threading

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 5555


class Session:
    __CLIENT_DATA = {}
    alive = False
    
    def __init__(self, address, port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = address
        self.port = port
    
    def connect(self):
        self.client_socket.connect((self.address, self.port))
        thread = threading.Thread(target=self.receiver)
        thread.start()
        self.alive = True
        
    def receiver(self):
        while True:
            try:
                data = self.client_socket.recv(1024)
                if len(data) < 1: break
            except:
                break
        print("Connection closed")
        self.alive = False

if __name__ == '__main__':
    s = Session(SERVER_ADDRESS, SERVER_PORT)
    s.connect()
    while s.alive:
        s.client_socket.send(input(":> ").encode())
        
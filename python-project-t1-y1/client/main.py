import json
import socket

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 5555


class Session:
    __CLIENT_DATA = {}
    def __init__(self, address, port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = address
        self.port = port
    
    
    
    def connect(self):
        self.client_socket.connect((self.address, self.port))
        self.__CLIENT_DATA = json.loads(self.client_socket.recv(1024).decode())
        print(self.__CLIENT_DATA["options"])



if __name__ == '__main__':
    s = Session(SERVER_ADDRESS, SERVER_PORT)
    s.connect()
    while True:
        s.client_socket.send(input(":> ").encode())
        
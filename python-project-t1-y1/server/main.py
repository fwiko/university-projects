import re
import json
import socket
import threading



class Game:
    pass


class Player:
    __alive = True
    def __init__(self, pid, client):
        self.__pid = pid
        self.__client = client

    def listen(self):
        while self.__alive:
            try:
                data = self.__client.recv(1024)
                if data:
                    SERVER.message(f"CLIENT-{self.__pid}", data.decode())
                    parsed_command = re.sub(' +', ' ', data.decode()).strip().split(" ")
                    print(parsed_command)
            except socket.error:
                SERVER.message("Disconnect", f"Session #{self.__pid} closed")
                self.kill()
                
    def send(self, data):
        self.__client.send(json.dumps(data).encode())

    def kill(self):
        self.__alive = False

class ConnectionHandler:
    _running = False
    def __init__(self, host, port):
        self._host = host
        self._port = port
        
        
    def _gateway(self, con_socket: socket.socket):
        self._running = True
        SERVER.message("ConnectionHandler", "Listening on {}:{}".format(*con_socket.getsockname()))
        
        while self._running:
            (client, client_address) = con_socket.accept()
            SERVER.message("ConnectionHandler", "Connection from {}:{}".format(*client.getpeername()))
            SERVER.add_client(client)
            
    
    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self._host, self._port))
        s.listen()
        
        gateway = threading.Thread(target=self._gateway, args=[s])
        gateway.start()

        

class Server:
    __games = []
    __clients = []
    __next_id = 1
    
    __CLIENT_DATA = {
        "options": {
            "host": {
                "desc": "host own game"
                },
            "join": {
                "desc": "join a game",
                "params": "<game_code>"
                },
            "leave": {
                "desc": "leave current game"
            },
            "exit": {
                "desc": "exit program"
            }
            },
        "instructions":"AAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    }
    
    def __init__(self, host, port):
        self.__connection_handler = ConnectionHandler(host, port)
    
    @staticmethod
    def message(prefix, message):
        print(f"[{prefix}] {message}")

    def handle_instruction(self):
        pass

    # add player/client connection
    def add_client(self, client):
        p = Player(self.__next_id, client)
        self.__clients.append(p) 
        self.__next_id += 1
        threading.Thread(target=p.listen).start()
        p.send(self.__CLIENT_DATA)
        
    # start the connection handler 
    def start(self):
        self.__connection_handler.start()


def main():
    global SERVER
    SERVER = Server("0.0.0.0", 5555)
    SERVER.start()
    


if __name__ == "__main__":
    main()
import re
import json
import string
import socket
import threading

HOST = "0.0.0.0"
PORT = 5555

CLIENT_COMMANDS = {
    "games": { "desc": "list available games"},
    "host": { "desc": "host own game" },
    "join": {
        "desc": "join a game",
        "params": "<game_code>"
        },
    "leave": { "desc": "leave current game" },
    "exit": { "desc": "exit program" }
    }

def generate_code():
    return "".join([random.choice(string.ascii_uppercase) for _ in range(5)])


class Client:
    __alive = False
    __state = "inMenu"
    
    def __init__(self, conn, addr, uid):
        self.__conn = conn
        self.addr = addr
        self.uid = uid
        self.__config = {
            "game": None,
            "username": f"CLIENT-{uid}"
        }
    
    def listen(self):
        self.__alive = True
        self.__conn.settimeout(300)
        while self.__alive:
            try:
                data = self.__conn.recv(1024)
                if len(data) < 1: break
                console_output(f"CLIENT-{self.uid}", data.decode())
            except:
                break
        SERVER.disconnected(self)
        
    def send(self, header, data):
        packet = {
            "header": header,
            "data": data
        }
        self.__conn.send(json.dumps(packet).encode())
        
    def __command(self, command):
        parsed_command = (re.sub(' +', ' ', command.strip())).lower().split(" ")
        if self.__state == "inMenu":
            command = parsed_command[0]
            args = parsed_command[1:]
            if command == "host":
                new_game = Game(self)
                SERVER.add_game(new_game)
        elif self.__state == "inGame":
            pass
        
    def get_state(self):
        return self.__state
    
    def set_state(self, state):
        self.__state = state
    
    def close_connection(self):
        self.__alive = False
        self.__conn.close()
    
        

class Game:
    def __init__(self, owner: Client):
        self.__config = {
            "code": generate_code(),
            "owner": owner,
            "players": [],
            "questions": {}
        }

class Server:
    __running = False
    __clients = []
    __games = {}
    __next_uid = 1
    

    
    # Handles client connections
    # Gets relevant data and creates a client object based on the Client class
    def __handle_connection(self, conn, addr):
        console_output("server", "Connection from {}:{}".format(*addr))
        new_client = Client(conn, addr, self.__next_uid)
        self.__next_uid += 1
        thread = threading.Thread(target=new_client.listen)
        thread.start()
        self.__clients.append(new_client)
        new_client.send("commands", CLIENT_COMMANDS)
        new_client.send("state", {"state": new_client.get_state()})

    # Client disconnection signal
    # Called when a client has stopped responding - lost connection
    def disconnected(self, client):
        console_output("server", "Disconnect from {}:{}".format(*client.addr))
        self.__clients.remove(client)
    
    # Main listener
    # Listening for connections from clients then passing to the handler
    def listen(self):
        self.__running = True
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((HOST, PORT))
            console_output("server", f"Listening on {HOST}:{PORT}")
            while self.__running:
                sock.listen()
                conn, addr = sock.accept()
                self.__handle_connection(conn, addr)

    # Handle instructions sent to server
    def instruction(self, instruction, args):
        if instruction == "stop":
            self.__stop()
        if instruction == "kill":
            client = next((x for x in self.__clients if x.uid == args[0]), None)
            if client:
                client.kill()

    # Return list of clients connected to the server
    def get_clients(self):
        return self.__clients
            
    # stop everything - close server..
    def __stop(self):
        self.__running = False
    
# server-side terminal output function
def console_output(prefix, message):
    print(f"[{prefix.upper()}] > {message.capitalize()}")

if __name__ == "__main__":
    SERVER = Server()
    # main server thread - listening for connections - handling games etc..
    server_thread = threading.Thread(target=SERVER.listen)
    server_thread.start()

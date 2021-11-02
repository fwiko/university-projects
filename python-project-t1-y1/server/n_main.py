import re
import json
import string
import socket
import random
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
        
    # client command processor
    # commands sent by client connections are processed here
    def __process_command(self, command):
        # formatting the command, removing spaces, seperating command and passed in arguments
        parsed_command = (re.sub(' +', ' ', command.strip())).lower().split(" ")
        
        # checking what state the user is in
        # user is in-menu
        if self.__state == "inMenu":
            command = parsed_command[0]
            args = parsed_command[1:]
            
            # if the command sent by the user is "host"
            if command == "host":
                # create/host a new quiz game
                new_game = Game(self)
                SERVER.add_game(new_game)
                self.set_state("inGame")
                self.__config["game"] = new_game
                new_game.alert(f"Game created with code {new_game.get_code()}")
                
            # if the command sent by the user is "join"
            elif command == "join":
                # join an available game 
                pass
        
            elif command == "games":
                # display list of available games
                pass
                
        #user is in-game
        elif self.__state == "inGame":
            pass
    
    def listen(self):
        self.__alive = True
        self.__conn.settimeout(300)
        while self.__alive:
            try:
                data = self.__conn.recv(1024)
                if len(data) < 1: break
                
                data = json.loads(data.decode())
                
                console_output(f"CLIENT-{self.uid}", data)
                
                if not data.get("header", None) or not data.get("data", None) or not data["data"].get("command"): continue
                if data["header"] == "command":
                    self.__process_command(data["data"]["command"])
                    
            except Exception as e:
                print(e)
                break
        SERVER.disconnected(self)
        
    def send(self, header, data):
        packet = {
            "header": header,
            "data": data
        }
        self.__conn.send(json.dumps(packet).encode())
        
    def get_state(self):
        return self.__state
    
    def set_state(self, state):
        self.__state = state
        self.send("state", {"state": state})
        console_output("server", f"Set state of CLIENT-{self.uid} to \"{state}\"")
        
    def set_username(self, username):
        self.__config["username"] = username
        console_output("server", f"Set username of CLIENT-{self.uid} to \"{username}\"")
    
    def close_connection(self):
        self.__alive = False
        self.__conn.close()
        
class Game:
    def __init__(self, owner: Client):
        self.__config = {
            "code": generate_code(),
            "owner": owner,
            "players": [owner],
            "questions": {}
        }
        console_output("GAME", f"New game created by CLIENT-{owner.uid}")
        
    def get_code(self):
        return self.__config.get("code")

    def alert(self, message):
        for client in self.__config.get("players"):
            client.send("alert", {"message": message})
            

class Server:
    __running = False
    __clients = []
    __games = []
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
        
        
        
    #   relative to game management   #
    
    def add_game(self, game):
        self.__games.append(game)
    
# server-side terminal output function
def console_output(prefix, message):
    print(f"[{prefix.upper()}] > {message}")

if __name__ == "__main__":
    SERVER = Server()
    # main server thread - listening for connections - handling games etc..
    server_thread = threading.Thread(target=SERVER.listen)
    server_thread.start()

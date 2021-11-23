import re
import time
import json
import socket
import threading

import settings
from utility import Logger, State

class Session():
    _state: State = None
    _game_code: str = None
    _username: str = None
    _uid: int = None
    _logger: Logger = Logger("Client")
    
    def __init__(self, host: str, port: int):
        self.alive = True
        self._host = host
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    @property
    def state(self):
        return self._state
    
    @property
    def game_code(self):
        return self._game_code
    
    @property
    def username(self):
        return self._username
    
    @property
    def uid(self):
        return self._uid
    
    @state.setter
    def state(self, state: str):
        try:
            self._state = State(state)
        except ValueError:
            self._logger.error(f"Invalid state: {state}")
        else:
            self._logger.info(f"State changed to {state}")
    
    @game_code.setter
    def game_code(self, code: str):
        if len(code) == 5:
            self._game_code = code
            self._logger.info(f"Game code set to {code}")
        else:
            self._logger.error(f"Invalid game code: {code}")
            
    @username.setter
    def username(self, username: str):
        self.username = username
            
    @uid.setter
    def uid(self, uid: int):
        self._uid = uid
        self._logger.info(f"UID set to {uid}")
    
    # client side helper methods
    
    def get_prefix(self):
        if self.state in (State.IN_GAME, State.IN_LOBBY):
            location_fix = f"[{self.state.value[2:]}-{self.game_code}]"
        else:
            location_fix = f"[{self.state.value[2:]}]"
        username_fix = f"[{self.username}]" if self.username else "Client"
        return f"{username_fix} @ {location_fix}"
    
    # handler getters
    
    def _get_handler(self, command: str):
        """handles user input"""
        if command in ("host", "join", "leave", "start", "games"):
            return self._command
        elif command == "help":
            return self._help_menu
        
    def _get_rec_handler(self, header: str):
        """returns a function that handles received data of a certain header"""
        return {
            "state": self._handle_state,
            "game_code": self._handle_game_code,
            "alert": self._handle_alert,
            "question": self._handle_question,
            "client_info": self._handle_client_info,
            "game_list": self._handle_game_list,
            "quiz_stats": self._handle_game_stats
        }.get(header)
    
    
    # command handlers
    
    def _help_menu(self, **kwargs):
        print(settings.HELP_COMMANDS)
        
    def _command(self, **kwargs):
        """handles user input"""
        cmd = kwargs.get("command")
        args = kwargs.get("args")
        self._send("command", f"{cmd}{' ' + ' '.join(args) if args else ''}")
    
    # received data handlers
    
    def _handle_state(self, data: dict):
        self.state = data.get("state")
        
    def _handle_game_code(self, data: str):
        self._game_code = data.get("game_code")
    
    def _handle_alert(self, data: str):
        print(f"\n\n > {data.get('message')}\n"+f"\n {self.get_prefix()} > ", end="")
        
    def _handle_question(self, data: str):
        print(f"\n\n > {data.get('question')}\n"+f"\n {self.get_prefix()} > ", end="")
    
    def _handle_client_info(self, data: str):
        self.uid = int(data.get("uid"))
    
    def _handle_game_list(self, data: str):
        game_list = "\n".join([f" {g.get('code')} | {g.get('player_count')}" for g in data.get("game_list")])
        output_string = f"\n ------------------\n\n Available Games\n\n{game_list}\n\n ------------------" if game_list \
            else "\n ------------------\n\n No games available\n\n ------------------"
        print(output_string)
    
    def _handle_game_stats(self, data: dict):
        print(data)
        leaderboard = "\n".join([f" #{i+1}. {p.get('username')} | {p.get('score')} points" for i, p in enumerate(data.values())])
        output_string = f"\n -----------------\n\n Final Leaderboard\n\n ------------------\n\n{leaderboard}\n\n ------------------"
        print(output_string)

    # server connection  

    def start(self):
        """initiate the connection with the quiz server"""
        try:
            self._socket.connect((self._host, self._port))
        except ConnectionRefusedError:
            self.stop()
            self._logger.error(e)
        else:
            self._logger.info("Connected to server")
        self.listener_thread = threading.Thread(target=self._receiver).start()
        
    def stop(self):
        self.alive = False
        self._socket.close()
        self._logger.info("Session stopped")
        
    # receiving data from the server
    
    def _handle_received(self, recieved: dict):
        """handles received data from the quiz server"""
        header = recieved.get("header")
        data = recieved.get("data")
        if not header or not data:
            self._logger.error(f"Invalid data received: {recieved}")
            return
    
        handler = self._get_rec_handler(header)
        if handler:
            handler(data)
        else:
            print(header)
    
    def _receiver(self):
        """receive data sent from the quiz server
        function will run in a thread (coroutine) alongside the rest of the client"""
        while self.alive:
            try:
                data = self._socket.recv(1024).decode("utf-8")
                if not data:
                    break
                decoded: dict = json.loads(data)
                self._logger.debug(f"Received data: {decoded}")
                
            except WindowsError as error:
                self._logger.error(error)
                self.alive = False
                continue
            
            except json.decoder.JSONDecodeError as error:
                print(data)
                self._logger.error(error)
                continue
            
            if not decoded.get("header", None) or not decoded.get("data", None):
                continue
            
            self._handle_received(decoded)
            
        self.alive = False
        print("Connection closed")
        

        
    # sending data to the server
    
    def _send(self, header: str, data: str):
        self._socket.send(json.dumps({"header": header, "data": {header: data}}).encode('utf-8'))
        
    def _command(self, **kwargs):
        """handles user input"""
        cmd = kwargs.get("command")
        args = kwargs.get("args")
        self._send("command", f"{cmd}{' ' + ' '.join(args) if args else ''}")
        
    def _answer(self, answer: str):
        self._send("answer", answer)
        
    # additional command handlers
    
    def _help_menu(self, **kwargs):
        print(settings.HELP_COMMANDS)
        
    # handling user input
    

    
    def input(self, input: str):
        """input and send it to the quiz server"""
        sanitised_input: list[str] = (re.sub(' +', ' ', input.strip())).lower().split(" ")
        cmd = sanitised_input[0]
        args = sanitised_input[1:]
        handler = self._get_handler(cmd)
        if handler:
            handler(command=cmd, args=args)
        else:
            self._answer(input)
    

if __name__ == '__main__':
    session = Session(settings.HOST, settings.PORT)
    session.start()
    while not session.state:
        time.sleep(.1)
    while session.alive:
        message = input(f"\n {session.get_prefix()} > ")
        if len(message) < 1:
            continue
        if message == "exit":
            session.stop()
            break
        try:
            session.input(message)
        except Exception as e:
            print(e)
            input("Press enter to continue...")
        time.sleep(1)
import re
import time
import json
import socket
import threading

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 5555
DEBUG = True


def console_out(prefix, message):
    """send the passed in message to console with the specified prefix"""
    print(f"[{prefix}] {message}")


def debug(data):
    """function used for debugging"""
    if DEBUG:
        print(data)


class GameSession:
    __state = None
    __alive = False
    __data = {"client": {"uid": None, "username": None}, "commands": {}, "game_code": None}

    def __init__(self, address, port):
        self.__client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__address = address
        self.__port = port

    # CLIENT -> SERVER METHODS

    def connect(self):
        """called to make a connection to the game server"""
        self.__client_socket.connect((self.__address, self.__port))
        self.__alive = True
        threading.Thread(target=self.receiver).start()

    def disconnect(self):
        """called to disconnect from the game server"""
        self.__client_socket.shutdown(2)
        self.__client_socket.close()
        self.__alive = False

    def send(self, header: str, data: dict):
        """called when sending data/commands from the client to the server"""
        self.__client_socket.send(json.dumps({"header": header, "data": data}).encode())

    # SERVER -> CLIENT METHODS

    def receiver(self):
        """used to listen for/receive packets/data from the game server"""
        while self.__alive:
            try:
                data = self.__client_socket.recv(1024)
                if len(data) < 1:
                    break
                self.__process_data(json.loads(data.decode()))
            except Exception as error:
                console_out(self.__class__.__name__, f"Data processing error; {error}")
                self.__alive = False

        console_out(self.__class__.__name__, "Connection closed")

    @staticmethod
    def __alerted(data: dict) -> None:
        """function called when an alert packet is sent from the server"""

        debug(f"Alerted; {data}")

    @staticmethod
    def __game_list(data: dict) -> None:
        """function called when a list of available games is sent from the server"""

        debug(f"Available Games; {data}")

    @staticmethod
    def __game_stats(data: dict) -> None:
        """function called when a list of stats is sent when a game ends"""

        debug(f"Game Stats; {data}")

    # GETTER METHODS

    def get_prefix(self):
        """returns a prefix string for the user input cli"""
        c = "CLIENT-"
        state_fixes = {
            "inMenu": "Home Menu",
            "inLobby": f"{self.__data['game_code']} (lobby)",
            "inGame": f"{self.__data['game_code']} (game)"}
        return f"{self.__data.get('client').get('username') or c+str(self.__data.get('uid'))} "\
               f"@ {state_fixes.get(self.get_state())}"

    def get_state(self):
        """returns the current state of the client"""
        return self.__state

    def get_status(self) -> bool:
        """returns a bool value of the sessions state true = alive, false = dead"""
        return self.__alive

    def __get_handlers(self):
        """returns handle function dictionary"""
        return {
            "state": self.__set_state,
            "commands": self.__set_commands,
            "question": self.__ask_question,
            "alert": self.__alerted,
            "client_info": self.__update_client_info,
            "game_code": self.__update_game_info,
            "game_list": self.__game_list,
            "game_stats": self.__game_stats
        }

    def get_commands(self):
        """called to return a dictionary of all available commands and related information"""
        return self.__data.get("commands", {})

    # SETTER METHODS

    def __set_state(self, data: dict) -> None:
        """called to set the state of the client"""
        self.__state = data.get("state")

        debug(f"State change; {data}")

    def __set_game_code(self, data: str) -> None:
        """called to set the code of the game locally"""
        self.__data["game_code"] = data

        debug(f"Game code set; {data}")

    def __set_commands(self, data: dict) -> None:
        """called upon connection to the server to handle list of available commands"""
        self.__data["commands"] = data.get("commands", {})

        debug(f"Commands set; {data or {}}")

    def __update_client_info(self, data: dict) -> None:
        """called to update the info of the client (username/uid)"""
        self.__data["client"]["uid"] = data.get("uid")
        self.__data["client"]["username"] = data.get("username")

        debug(f"Username set; {data.get('username')}")
        debug(f"UID set; {data.get('uid')}")

    def __update_game_info(self, data) -> None:
        self.__data["game_code"] = data

        debug(f"Game code set; {data}")

    # QUIZ RELATED

    @staticmethod
    def __ask_question(data: dict):
        """function called when a question is sent to the client"""

        debug(f"Question asked; {data}")

    # DATA HANDLING

    def __process_data(self, packet):
        """process/handle data packets received by the client"""
        header = packet.get("header", None)
        data = packet.get("data", None)

        if not header or not data:
            return

        handlers = self.__get_handlers()
        handler = handlers.get(header, None)
        if handler:
            handler(data)

    def command(self, data: list[any]) -> None:
        """function called externally based on user input and state of self for commands"""
        if data[0] not in self.__data.get("commands").keys():
            return
        self.send("command", {"command": " ".join(data)})

        debug(f"Command sent; {data}")

    def answer(self, data: str) -> None:
        """function called externally based on user input and state of self for quiz answers"""
        if len(data) <= 0:
            return
        self.send("answer", {"answer": data})

        debug(f"Answer submitted; {data}")


def main():
    while session.get_status():
        user_input = (re.sub(' +', ' ', input(f"{session.get_prefix()} $ ").strip())).lower().split(" ")
        debug(f"User input; {user_input}")
        if session.get_state() in ("inMenu", "inLobby"):
            session.command(user_input)
        elif session.get_state() == "inGame" and not (user_input[0] in ("exit", "leave") and len(user_input) == 1):
            session.answer(" ".join(user_input))
        elif user_input[0] in ("exit", "leave") and len(user_input) == 1:
            session.command(user_input)


if __name__ == '__main__':
    session = GameSession(SERVER_ADDRESS, SERVER_PORT)
    session.connect()
    while not session.get_commands():
        continue

    print("\n".join([
        f"{command}{' ' + data.get('params') + ' ' if data.get('params') else ' '}| {data.get('desc')}"
        for command, data in session.get_commands().items()
    ]))

    main()

import json
import random
import re
import time
import socket
import string
import threading

VALID_STATES = ("inMenu", "inGame", "inLobby")
CLIENT_COMMANDS = {"games": {"desc": "list available games", "states": ["inMenu"]},
                   "host": {"desc": "host own game", "states": ["inMenu"]},
                   "join": {"desc": "join a game", "states": ["inMenu"], "params": "<game_code>"},
                   "leave": {"desc": "leave current game", "states": ["inGame", "inLobby"]},
                   "exit": {"desc": "exit program", "states": ["inMenu", "inGame", "inLobby"]},
                   "start": {"desc": "start the current game", "states": ["inLobby"]}
                   }


def console_out(prefix, message):
    """send the passed in message to console with the specified prefix"""
    print(f"[{prefix}] {message}")


def generate_code():
    """return a random 5 character long string"""
    return "".join([random.choice(string.ascii_uppercase) for _ in range(5)])


def get_topic():
    """choose a random topic from the ones available and return the respective questions"""
    with open("server/questions.json", "r") as questions:
        q = json.load(questions)
        topic = random.choice(list(q.keys()))
        return {"topic": topic, "questions": q.get(topic)}


class Client:
    __alive = False

    def __init__(self, conn, addr, uid):
        self.__conn = conn
        self.__addr = addr
        self.__uid = uid
        self.__settings = {"state": "inMenu", "username": f"CLIENT-{uid}", "commands": CLIENT_COMMANDS, "game": None}

    def listen(self):
        """start listening for data sent from the client"""
        self.__alive = True
        while self.__alive:
            try:
                data = self.__conn.recv(1024)
                if len(data) < 1:
                    break

                decoded = json.loads(data.decode())
                console_out(f"{self.__class__.__name__}-{self.__uid}", decoded)

                if not decoded.get("header", None) or not decoded.get("data", None):
                    continue

                # checking a users state
                client_state = self.__settings.get("state", None)
                if client_state == "inMenu" and decoded["header"] == "command":
                    self.__handle_command(decoded["data"])
                elif client_state == "inGame" and decoded["header"] == "command":
                    self.__handle_command(decoded["data"])
                elif client_state == "inLobby" and decoded["header"] == "command":
                    self.__handle_command(decoded["data"])
                elif decoded["header"] == "answer" and self.get_state() == "inGame":
                    self.__handle_answer(decoded["data"].get("answer"))

            except WindowsError:
                self.__alive = False

        SERVER.disconnected(self)

    # GETTER METHODS

    def get_address(self):
        """return the addressing information of the client object"""
        return self.__addr

    def get_state(self):
        """return the current state of the client object"""
        return self.__settings.get("state", None)

    def get_settings(self):
        """return the current settings configuration of the client object"""
        return self.__settings

    def get_uid(self):
        """return the uid of the specified client"""
        return self.__uid

    def get_username(self):
        """return the current username of the specified client"""
        return self.__settings.get("username", f"CLIENT-{self.__uid}")

    def get_game(self):
        """return the game object of the game the client is in if they are in a game"""
        return self.__settings.get("game", None)

    # SETTER METHODS

    def set_state(self, state):
        """set the state of current user object to specified"""
        self.__settings["state"] = state if state in VALID_STATES else self.__settings.get("state", None)
        self.send("state", {"state": self.get_state()})

        console_out(f"{self.__class__.__name__}-{self.__uid}", f"State set to \"{state}\"")

    def set_username(self, username: str) -> None:
        """set the username of the client object to one specified"""
        self.__settings["username"] = username

        console_out(f"{self.__class__.__name__}-{self.__uid}", f"Display name set to \"{username}\"")

    def set_game(self, game):
        """set the game object that the client is in"""
        self.__settings["game"] = game
        self.send("game_code", game.get_code() if game else None)

        console_out(f"{self.__class__.__name__}-{self.__uid}", f"Game set to \"{game.get_code() if game else None}\"")

    # CLIENT -> SERVER

    def __handle_command(self, command):
        """handling commands sent from the client to the server"""
        parsed_data = (re.sub(' +', ' ', command["command"].strip())).lower().split(" ")
        cmd = parsed_data[0]
        args = parsed_data[1:]

        if cmd == "host":
            # create/host a new quiz game instance
            new_game = Game(self)
            SERVER.add_game(new_game)
            self.set_state("inLobby")
            self.set_game(new_game)
            new_game.alert(f"GAME CREATED with CODE: {new_game.get_code()}, " +
                           f"currently entertaining {len(new_game.get_players())}/10 PLAYERS", self)

        elif cmd == "join":
            # join an available/active game
            if not len(args) > 0 or self.get_state() in ("inGame", "inLobby"):
                return

            available_games = SERVER.get_games()
            chosen_game = next((x for x in available_games if x.get_code() == args[0].upper()), None)
            if chosen_game:
                self.set_game(chosen_game)
                chosen_game.add_player(self)
                self.set_state("inLobby")

        elif cmd == "leave":
            # leave the current game/lobby
            if self.__settings.get("state") in ("inGame", "inLobby"):
                try:
                    game = self.__settings["game"]
                except KeyError:
                    return
                else:
                    # noinspection PyUnresolvedReferences
                    game.client_leave(self)
                    self.set_game(None)
                    self.set_state("inMenu")

        elif cmd == "games":
            # display a list of available/active games
            available_games = SERVER.get_games()
            formatted_games = "\n".join(f"{g.get_code()} | {len(g.get_players())}/10 players" for g in available_games)
            self.send("game_list", formatted_games)

        elif cmd == "start":
            # start the quiz game if the executing player is the game owner
            current_game = self.__settings.get("game", None)
            if not current_game or self != current_game.get_owner():
                return
            current_game.start()

    def __handle_answer(self, answer):
        """handling answers sent from the client when in an active game"""
        if answer:
            pass
        parsed_answer = (re.sub(' +', ' ', answer.strip())).lower()
        self.__settings.get("game").submit_answer(self, parsed_answer)

    # SERVER -> CLIENT

    def close_connection(self):
        """close the connection of the client object to the server"""
        self.__alive = False
        self.__conn.close()

    def send(self, header, data):
        """send data packets to the client"""
        packet = {"header": header, "data": data}
        self.__conn.send(json.dumps(packet).encode())


class Game:
    __active = False
    __current_game = None

    def __init__(self, owner: Client):
        self.__settings = {
            "code": generate_code(),
            "owner": owner,
            "players": [owner],
        }
        console_out(self.__class__.__name__,
                    f"Game with code \"{self.__settings.get('code')}\" created by {owner.get_username()}")

    # GETTER METHODS

    def get_code(self) -> str:
        """returns the randomly generated 'join' code or 'identifier' of the specified game object"""
        return self.__settings.get("code")

    def get_players(self) -> list[Client]:
        """returns a list of all players in the relative game"""
        return self.__settings.get("players")

    def get_owner(self) -> Client:
        """returns the Client object of the game creator/host/owner"""
        return self.__settings.get("owner")

    # SETTER/MANAGEMENT METHODS

    def add_player(self, client: Client) -> None:
        """add a player/client to the relative game instance"""
        self.__settings["players"].append(client)
        self.alert(f"{client.get_username()} has joined the game..")

        console_out(self.__class__.__name__, f"{client.get_username()} has joined game ({self.get_code()})")

    def __remove_player(self, client: Client):
        """remove a player/client from the relative game instance"""
        if client in self.__settings.get("players"):
            self.__settings["players"].remove(client)

            console_out(self.__class__.__name__, f"{client.get_username()} has left game ({self.get_code()})")

    def close_game(self):
        """function called to completely close a game"""
        self.state_change("inMenu")
        self.__active = False
        SERVER.remove_game(self)

        for player in self.__settings.get("players"):
            player.set_game(None)

        console_out(self.__class__.__name__, f"Game ({self.get_code()}) has been closed..")

    # SERVER/GAME -> CLIENT

    def alert(self, message: str, player: Client = None) -> None:
        """sends the specified message to all/a specific player/s/client/s in the game"""
        if not player:
            for client in self.__settings.get("players"):
                client.send("alert", {"message": message})
        else:
            player.send("alert", {"message": message})

    def send_data(self, header: str,  data: dict, player: Client = None) -> None:
        """send a specified data packet to each player or a specific player in the game"""
        if not player:
            for client in self.__settings.get("players"):
                client.send(header, data)
        else:
            player.send(header, data)

    def state_change(self, state: str, player: Client = None) -> None:
        """changes the state of all clients in the current game instance if one is not specified"""
        if not player:
            for p in self.__settings.get("players", []):
                p.set_state(state)
        else:
            player.set_state(state)

    def ask_question(self, question, answer):
        """ask a question to all clients in the current game instance"""

        for p in self.__settings.get("players", []):
            p.send("question", {"question": question, "answer": answer})

        console_out(f"Game-{self.get_code()}", f"Asking question \"{question}\"")

    # CLIENT -> GAME

    def submit_answer(self, client: Client, answer: str):
        """handle the user submitting an answer to the game/question asked"""
        if not self.__current_game or client in self.__current_game["current_question"]["submitted"]:
            return

        if answer in self.__current_game.get("current_question").get("answer") \
                and client not in self.__current_game.get("current_question").get("submitted"):

            if self.__current_game["scores"].get(client.get_uid()):
                self.__current_game["scores"][client.get_uid()] += 1
            else:
                self.__current_game["scores"][client.get_uid()] = 1

            console_out(f"Game-{self.get_code()}",
                        f"{client.get_username()} guessed question "
                        f"\"{self.__current_game.get('current_question').get('question')}\" correctly")

        self.__current_game["current_question"]["submitted"].append(client)

    # QUIZ RELATED

    def question_sequence(self):
        """start the process of asking questions and collecting answers from users"""
        self.alert("Quiz starting in 5 seconds..")
        time.sleep(2)

        for question, answer in self.__current_game["quiz_info"]["questions"].items():
            self.__current_game["current_question"]["question"] = question
            self.__current_game["current_question"]["answer"] = answer
            self.__current_game["current_question"]["submitted"].clear()
            self.__current_game["current_question"]["start_time"] = time.time()
            self.ask_question(question, answer)

            while len(self.__current_game["current_question"]["submitted"]) != len(self.get_players()):
                time.sleep(1)

        final_scores = [{
                "uid": p.get_uid(),
                "username": p.get_username(),
                "score": self.__current_game.get('scores').get(p.get_uid())
            } for p in self.__settings.get("players")]

        self.send_data("game_stats", {"scores": final_scores})
        self.end()

    def start(self):
        """starts the quiz game asking all involved players the questions.."""
        chosen_topic = get_topic()
        self.__current_game = {
            "quiz_info": chosen_topic,
            "scores": {key: value for (key, value) in [(p.get_uid(), 0) for p in self.__settings.get("players")]},
            "current_question": {
                "question": None,
                "answer": None,
                "submitted": [],
                "start_time": 0.0
            }
        }

        self.state_change("inGame")
        self.__active = True
        threading.Thread(target=self.question_sequence).start()

    def end(self):
        """function called when a quiz has finished to reset all respective values/variables"""
        self.__active = False
        self.__current_game = None
        self.state_change("inLobby")

        console_out(self.__class__.__name__, "QUIZ COMPLETE, RESETTING GAME...")

    # EVENTS

    def client_leave(self, client: Client):
        """message sent to the game if a client is to disconnect from the server or leave the game"""
        self.__remove_player(client)

        console_out(self.__class__.__name__, f"{client.get_username()} has left game ({self.get_code()})")


class GameServer:
    __running = False
    __nuid = 1
    __data = {"clients": [], "games": []}

    def __init__(self, host: str, port: int) -> None:
        self.__host = host
        self.__port = port

    def start(self) -> None:
        """start listening for and handling client connections"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.__host, self.__port))
            console_out(self.__class__.__name__, f"Listening on {self.__host}:{self.__port}")
            sock.listen()
            self.__running = True
            while self.__running:
                conn, addr = sock.accept()
                # creation of new client
                new_client = Client(conn, addr, self.__nuid)
                self.__nuid += 1
                # starting the client listener
                threading.Thread(target=new_client.listen).start()
                # adding client to server
                self.__add_client(new_client)
                console_out(self.__class__.__name__, "Connection from {}:{}".format(*addr))

    def stop(self) -> None:
        """set the __running value to False thus breaking the server listener loop"""
        self.__running = False

    # GETTER METHODS

    def get_clients(self) -> list[any]:
        """returns a list of all connected clients"""
        return self.__data.get("clients", [])

    def get_games(self) -> list[any]:
        """returns a list of all running quiz games"""
        return self.__data.get("games", [])

    def get_player(self, uid: int):
        """return a player object relative to the passed in uid value"""
        return next((x for x in self.__data.get("clients") if x.get_uid() == uid), None)

    # CLIENT/GAME > SERVER MANAGEMENT METHODS

    def add_game(self, game: Game):
        """add a game object to the servers list of active games"""
        self.__data["games"].append(game)

    def __add_client(self, client):
        """adding a client object to the servers known clients and sending initialisation data to client"""
        self.__data["clients"].append(client)
        client.send("commands", {"commands": client.get_settings()["commands"]})
        time.sleep(.5)
        client.send("state", {"state": client.get_settings()["state"]})
        time.sleep(.5)
        client.send("client_info", {"uid": client.get_uid(), "username": client.get_username()})

    def remove_game(self, game: Game):
        """remove a game object from the servers list of active games"""
        self.__data["games"].remove(game)

    def __remove_client(self, client):
        """remove a client object from the servers list of known clients"""
        self.__data["clients"].remove(client)

    # CLIENT HANDLING METHODS

    # signal sent to server if a client disconnects
    def disconnected(self, client):
        """handles a disconnect signal sent from a client indicating that it has lost connection"""
        console_out(self.__class__.__name__, "Disconnect from {}:{}".format(*client.get_address()))
        self.__remove_client(client)
        client_game = client.get_game()
        if client_game:
            client_game.client_leave(client)


if __name__ == "__main__":
    SERVER = GameServer("0.0.0.0", 5555)
    SERVER.start()


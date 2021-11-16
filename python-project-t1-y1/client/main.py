import re
import time
import json
import socket
import threading

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 5555


def console_out(prefix, message):
    """send the passed in message to console with the specified prefix"""
    print(f"[{prefix}] {message}")


class Session:
    alive = False
    __state = None
    commands = {}

    def __init__(self, address, port):
        self.__client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = address
        self.port = port

    def get_prefix(self):
        location = ""
        if self.__state == "inMenu":
            location = "Menu"
        elif self.__state == "inGame":
            location = "Game"
        elif self.__state == "inLobby":
            location = "Lobby"

        return f"{location}"

    def connect(self):
        self.__client_socket.connect((self.address, self.port))
        thread = threading.Thread(target=self.receiver)
        thread.start()
        self.alive = True

    def disconnect(self):
        self.__client_socket.shutdown(2)
        self.__client_socket.close()
        self.alive = False

    def send(self, header, data):
        self.__client_socket.send(json.dumps({"header": header, "data": data}).encode())

    def receiver(self):
        while True:
            try:
                data = self.__client_socket.recv(1024)

                if len(data) < 1:
                    break

                self.__process_data(json.loads(data.decode()))
            except Exception as e:
                print(e)
                break
        print("Connection closed")
        self.alive = False

    def __process_data(self, packet):
        header = packet.get("header", None)
        data = packet.get("data", None)
        if not header or not data: return
        if header == "state":
            self.__state = data.get("state", None)
            print(self.get_state())
        elif header == "commands":
            self.commands = data["commands"]
        elif header == "alert":
            console_output(header, data.get("message", None))
        elif header == "question":
            console_output(header, data.get("question", None))
        elif header == "quiz_scores":
            console_output(header, "\n".join(f"{uid} {info['score']}" for uid, info in data.get("final_scores")))

    def get_state(self):
        return self.__state


if __name__ == '__main__':
    session = Session(SERVER_ADDRESS, SERVER_PORT)
    session.connect()
    time.sleep(2)
    print("\n".join([f"{key} | {value['desc']}" for key, value in session.commands.items()]))
    try:
        print(session.get_state())
        while session.alive:
            user_input = (re.sub(' +', ' ', input(f"{session.get_prefix()} $ ").strip())).lower().split(" ")
            if user_input[0] == "exit":
                session.disconnect()
            elif user_input[0] in session.commands.keys():
                if user_input[0] == "host" and session.get_state() == "inMenu":
                    session.send("command", {"command": "host"})
                elif user_input[0] == "join" and session.get_state() == "inMenu":
                    session.send("command", {"command": " ".join(user_input)})
                elif user_input[0] == "leave" and session.get_state() in ("inGame", "inLobby"):
                    session.send("command", {"command": "leave"})
                elif user_input[0] == "start" and session.get_state() == "inLobby":
                    session.send("command", {"command": "start"})
            elif session.get_state() == "inGame":
                session.send("answer", {"answer": " ".join(user_input)})

    except Exception as e:
        print("DISCONNECTED", e)
        session.disconnect()

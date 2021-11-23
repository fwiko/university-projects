import re
import sys
import time
import json
import socket
import threading
import settings
import pyfiglet
from colorama import Fore, Style
from dataclasses import dataclass
from utility import *


@dataclass()
class SessionData:
    state: State
    game_code: str or None
    username: str or None
    uid: int or None
    alive: bool = True


class Session:
    logger = Logger()
    settings = SessionData(State.IN_MENU, None, None, None)

    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # client side helpers ------------------------------------------------------

    def prefix(self):
        if self.settings.state in (State.IN_LOBBY, State.IN_GAME):
            location = f"{self.settings.state.value[2:]}-{self.settings.game_code}"
        else:
            location = self.settings.state.value[2:]
        return f"{Fore.GREEN}{self.settings.username or 'Client'}{Fore.RESET} $ {location}"

    # handler processing ---------------------------------------------------------

    def _get_respective_handler(self, command: str):
        if command in ("host", "join", "leave", "start", "games"): 
            return self._command
        elif command == "help":
            return self._help
        elif command == "username":
            return self._username

    def _get_received_handler(self, header: str):
        """return a method within the session class based on the 'header' argument value"""
        return {
            # if the input is 'state' return _handle_state_change method
            "state": self._handle_state_change,
            # if the input is 'game_code' return _handle_game_code_change method
            "game_code": self._handle_game_code_change,
            # if the input is 'alert' return _handle_alert method
            "alert": self._handle_alert,
            # if the input is 'question' return _handle_question method
            "question": self._handle_question,
            # if the input is 'client_info' return _handle_client_info method
            "client_info": self._handle_client_info,
            # if the input is 'game_list' return _handle_game_list method
            "game_list": self._handle_game_list,
            # if the input is 'quiz_stats' return _handle_game_stats method
            "quiz_stats": self._handle_game_stats
        }.get(header) # get and return the relative value based on the header argument from the attached dictionary

    # command handlers --------------------------------------------------------

    @staticmethod
    def _help(**kwargs):
        """fetch and display the help menu in a readable format"""
        # create a list of tuples that contain the full length command and its description
        parsed_commands = [
            # tuple generation
            # formatted as ("<command name> <command arguments>", "<command description>")
            (f"{key}{' ' if value.get('args') else ''}{''.join(arg for arg in value.get('args', []))}",
            value.get('description'))
            # for each command specified in the settings
            for key, value in settings.COMMANDS.items()
            ]
        # finding the maximum length of a command string in the list above
        # calculated from len(command_name) + len(command_arguments)
        max_len = max(map(len, [x[0] for x in parsed_commands]))+1
        # finally print the help menu into the CLI
        print("\n".join(' ' * (max_len - len(x[0])) + x[0] + ' | ' + x[1] for x in parsed_commands) + "\n")

    def _command(self, **kwargs):
        """called when the user enters a command that must be sent to the server for processing
        (all commands except for the help command)"""
        cmd = kwargs.get("command")
        args = kwargs.get("args")
        self._send("command", f"{cmd}{' ' + ' '.join(args) if args else ''}")
        
    def _username(self, **kwargs):
        if not kwargs.get("args"):
            print(f"{Fore.RED}Missing <username> argument{Fore.RESET}\n")
            return
        self.settings.username = kwargs.get("args")[0]
        self._send("command", f"username {self.settings.username}")

    # received data handlers ---------------------------------------------------

    def _handle_state_change(self, data: dict) -> None:
        try:
            state = State(data.get("state"))
        except KeyError:
            self.logger.error(f"Invalid state: {data}")
        else:
            self.settings.state = State(state)

    def _handle_game_code_change(self, data: dict) -> None:
        self.settings.game_code = data.get("game_code")

    @staticmethod
    def _handle_alert(data: dict) -> None:
        print(f"{Fore.RED}{data.get('message')}{Style.RESET_ALL}\n")

    @staticmethod
    def _handle_question(data: dict) -> None:
        clear_screen()
        print(f"{Fore.YELLOW}{data.get('question')}{Style.RESET_ALL}\n")

    def _handle_client_info(self, data: dict) -> None:
        self.uid = int(data.get("uid"))

    @staticmethod
    def _handle_game_list(data: dict) -> None:
        game_list = "\n".join([f"{g.get('code')} | {Fore.GREEN if g.get('player_count') < 10 else Fore.RED}"
                            f"{g.get('player_count')}/10{Fore.RESET} players"
                            for g in data.get("game_list")])
        output_string = f"Available Games\n\n──────────────────\n\n{game_list}\n\n──────────────────\n" if game_list \
            else f"──────────────────\n\n{Fore.RED}No games available{Fore.RESET}\n\n──────────────────\n"
        print(output_string)

    @staticmethod
    def _handle_game_stats(data: dict) -> None:
        """organise and display quiz game statistics sent from the server in a tabular format"""
        leaderboard = "\n".join(
            [f"#{i + 1}. {Fore.LIGHTBLUE_EX}{p.get('username')}{Fore.RESET} | {p.get('score')} points" for i, p in
            enumerate(data.values())])
        output_string = f"{Fore.GREEN}Final Leaderboard{Fore.RESET}\n\n──────────────────\n\n{leaderboard}\n\n" \
                        f"──────────────────\n "
        print(output_string)

    # connection management -----------------------------------------------------

    def start(self):
        try:
            self._socket.connect((self._host, self._port))
        except ConnectionRefusedError:
            self.stop()
        else:
            self.logger.info("Connected to server")
        threading.Thread(target=self._receiver).start()

    def stop(self):
        self.settings.alive = False
        self._socket.close()
        self.logger.info("Session stopped")

    # send/receive -------------------------------------------------------------

    def _handle_received(self, received: dict):
        """handles received data from the quiz server"""
        header = received.get("header")
        data = received.get("data")
        if not header or not data:
            self.logger.error(f"Invalid data received: {received}")
            return
        handler = self._get_received_handler(header)
        if handler:
            handler(data)
        else:
            print(header)

    def _receiver(self):
        """receive data sent from the quiz server
        function will run in a thread (coroutine) alongside the rest of the client"""
        while self.settings.alive:
            try:
                data = self._socket.recv(1024).decode("utf-8")
                if not data:
                    break
                decoded: dict = json.loads(data)
                self.logger.debug(f"Received data: {decoded}")

            except WindowsError as error:
                self.logger.error(error)
                self.settings.alive = False
                continue

            except json.decoder.JSONDecodeError as error:
                self.logger.error(str(error))
                continue

            if not decoded.get("header", None) or not decoded.get("data", None):
                continue

            self._handle_received(decoded)

        self.settings.alive = False
        clear_screen()
        print(f"\n{Fore.RED}Connection closed{Fore.RESET}\n")

    def _send(self, header: str, data: str):
        self._socket.send(json.dumps({"header": header, "data": {header: data}}).encode('utf-8'))

    def _answer(self, answer: str):
        self._send("answer", answer)

    # client message --------------------------------------------------------------

    def input(self, message: str):
        """message and send it to the quiz server"""
        sanitised_input: list[str] = (re.sub(' +', ' ', message.strip())).lower().split(" ")
        cmd = sanitised_input[0]
        args = sanitised_input[1:]
        handler = self._get_respective_handler(cmd)
        if handler:
            handler(command=cmd, args=args)
        elif self.settings.state == State.IN_GAME:
            self._answer(message)
        else:
            print(f"{Fore.RED}Invalid input, please try again.{Fore.RESET}\n")


def main():
    """Main function"""
    clear_screen()
    session = Session(settings.HOST, settings.PORT)
    session.start()
    if not session.settings.alive:
        input("Press enter to exit...")
        return
    session._help()
    while True:
        user_input = input(f"{session.prefix()} > " if session.settings.state != State.IN_GAME else "")
        clear_screen()
        if len(user_input) < 1:
            continue
        if user_input == "exit":
            session.stop()
            break
        try:
            session.input(user_input)
        except Exception as e:
            print(e)
            input("Press enter to continue...")
        time.sleep(0.5)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
    input("\nPress enter to exit...")


# import python packages
import re
import time
import json
import socket
import threading
import settings
from dataclasses import dataclass

# import third party packages
from colorama import Fore, Style

# import custom packages/files
from utility import *


@dataclass()
class SessionData:
    """dataclass for storing session/local client data"""
    state: State
    game_code: str or None
    username: str or None
    uid: int or None
    alive: bool = True


class Session:
    # creation of logger object
    logger = Logger()
    # creation of SessionData object for storage of config
    settings = SessionData(State.IN_MENU, None, None, None)

    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # client side helpers ------------------------------------------------------

    def prefix(self):
        """method to return the prefix for the input prompt

        Returns:
            str: formatted prefix string which will be used in the input prompt
        """
        if self.settings.state in (State.IN_LOBBY, State.IN_GAME):
            location = f"{self.settings.state.value[2:]}-{self.settings.game_code}"
        else:
            location = self.settings.state.value[2:]
        return f"{Fore.GREEN}{self.settings.username or 'Client'}{Fore.RESET} $ {location}"

    # handler processing ---------------------------------------------------------

    def _get_respective_handler(self, command: str):
        """method used to get the respective handler method for the input by the user

        Args:
            command (str): executed command by the user

        Returns:
            function: the respective handler method for the input by the user
        """
        if command in ("host", "join", "leave", "start", "games"): 
            return self._command
        elif command == "help":
            return self._help
        elif command == "username":
            return self._username

    def _get_received_handler(self, header: str):
        """return a method within the session class based on the 'header' argument value

        Args:
            header (str): header of the received data

        Returns:
            function: the respective handler method for the received data
        """
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
    def _help():
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
        """called when the user enters the username command - set the username locally - then send it to the server"""
        # if the kwargs value 'args' is empty or None, return as the username is not specified
        if not kwargs.get("args"):
            # error message response to the client
            print(f"{Fore.RED}Missing <username> argument{Fore.RESET}\n")
            return
        # if the kwargs value 'args' is not empty or None, fetch the username value by concatenating the args
        uname = ' '.join(kwargs.get("args"))
        # if the final username value is between 3 and 16 characters long, set it locally and send it to the server
        if 3 <= len(uname) <= 16:
            # set the username locally
            self.settings.username = uname
            # send the username to the server
            self._send("command", f"username {self.settings.username}")
        # if the final username value is not between 3 and 16 characters long, return as the username is invalid
        else:
            print(f"{Fore.RED}Entered username is too {'short' if len(uname) < 3 else 'long'}{Style.RESET_ALL}\n")

    # received data handlers ---------------------------------------------------

    def _handle_state_change(self, data: dict) -> None:
        """handles incoming data with a 'state' header - used to set the state of the client locally (inMenu, inGame, inLobby)

        Args:
            data (dict): received state packet from the server
        """
        try:
            # try to fetch the Enum value from the State enum class
            state = State(data.get("state"))
        except KeyError:
            # if the Enum value is not found, log an error message
            self.logger.error(f"Invalid state: {data}")
        else:
            # if the Enum value is found, set the state of the client locally
            self.settings.state = State(state)

    def _handle_game_code_change(self, data: dict) -> None:
        """handles incoming data with the 'game_code' header - used to set the game code value locally for use in the input prefix

        Args:
            data (dict): received game code packet from the server
        """
        # set the local game_code value to the value of the 'game_code' key in the received data
        self.settings.game_code = data.get("game_code")

    @staticmethod
    def _handle_alert(data: dict) -> None:
        """handles incoming data with the 'alert' header

        Args:
            data (dict): alert data packet from the server
        """
        # simply prints the alert message to the CLI - colouring the text in red with the colorama module
        print(f"{Fore.RED}{data.get('message')}{Style.RESET_ALL}\n")

    @staticmethod
    def _handle_question(data: dict) -> None:
        """handles incoming data with the 'question' header

        Args:
            data (dict): received question packet from the server
        """
        # clear the CLI
        clear_screen()
        # print the question to the CLI - colouring the text in yellow with the colorama module
        print(f"{Fore.YELLOW}{data.get('question')}{Style.RESET_ALL}\n")

    def _handle_client_info(self, data: dict) -> None:
        """handles incoming data with the 'client_info' header - used to set the local UID value of the client

        Args:
            data (dict): received client info packet from the server
        """
        # set the local uid value to the value of the 'uid' key in the received data
        self.uid = int(data.get("uid"))

    @staticmethod
    def _handle_game_list(data: dict) -> None:
        """handles incoming data with the 'game_list' header - used to display the list of games in the lobby
        
        Args:
            data (dict): received game list packet from the server
        """
        # use a list comprehension to create a list of formatted strings based on game data
        # formatted as "<game code> | <player count>"
        # this list is then 'joined' into a single string with a newline character between each item
        game_list = "\n".join([f"{g.get('code')} | {Fore.GREEN if g.get('player_count') < 10 else Fore.RED}"
                            f"{g.get('player_count')}{Fore.RESET} players"
                            for g in data.get("game_list")])
        # if the list is not empty, print the list with the header "Available Games"
        # Otherwise print "No games available" under that header

        output_string = f"Available Games\n\n──────────────────\n\n{game_list}\n\n──────────────────\n" if game_list \
            else f"──────────────────\n\n{Fore.RED}No games available{Fore.RESET}\n\n──────────────────\n"  
        
        """
        Example output:
        
        Available Games

        ──────────────────

        CFJPE | 1 players
        JPTXQ | 9 players

        ──────────────────
        """
        
        print(output_string)

    @staticmethod
    def _handle_game_stats(data: dict) -> None:
        """organise and display quiz game statistics sent from the server in a tabular format
        
        Args:
            data (dict): dictionary of game statistics/leaderboard
        """
        # use a list comprehension to create a list of formatted strings based on the final statistics
        # formatted as "<position> | <username> | <score>"
        # this list is then 'joined' into a single string with a newline character between each item
        leaderboard = "\n".join(
            [f"#{i + 1}. {Fore.LIGHTBLUE_EX}{p.get('username')}{Fore.RESET} | {p.get('score')} points" for i, p in
            enumerate(data.values())])
        # print a beautified leaderboard table with a "Final Leaderboard" header and line dividers
        output_string = f"{Fore.GREEN}Final Leaderboard{Fore.RESET}\n\n──────────────────\n\n{leaderboard}\n\n" \
                        f"──────────────────\n "
        """
        Example output:
        
        Final Leaderboard

        ──────────────────

        #1. Client-1 | 3 points
        #2. Client-2 | 1 points

        ──────────────────
        """                
        print(output_string)

    # connection management -----------------------------------------------------

    def start(self):
        """initialises the connection to the server"""
        try:
            # attempt to connect to the server
            self._socket.connect((self._host, self._port))
        except ConnectionRefusedError:
            # if the connection is refused, stop and exit the program
            self.stop()
        else:
            # if the connection is successful, start the connection loop and log the connection
            self.logger.info("Connected to server")
            # receiver thread for receiving data from the server with the '_receiver' method
            t = threading.Thread(target=self._receiver)
            t.daemon = True
            t.start()

    def stop(self):
        """stops the connection or attempted connection to the server"""
        # setting the alive value to False will stop the input
        self.settings.alive = False
        # close the socket connection
        self._socket.close()
        # log the disconnection
        self.logger.info("Session stopped")

    # send/receive -------------------------------------------------------------

    def _handle_received(self, received: dict):
        """handles received data from the quiz server

        Args:
            received (dict): received data from the server
        """
        # if the received data has a 'header' key, fetch the 'header' data
        header = received.get("header")
        # if the received data has a 'data' key, fetch the 'data' data
        data = received.get("data")
        # if either the 'header' or 'data' data is not found, log an error message and return
        if not header or not data:
            self.logger.error(f"Invalid data received: {received}")
            return
        # otherwise, fetch the data handler based on the 'header' value
        handler = self._get_received_handler(header)
        if handler:
            # if the handler is found, call the handler with the 'data' data
            handler(data)
        else:
            # if the handler is not found, log an error message
            self.logger.error(f"No handler for header: {header}")

    def _receiver(self):
        """receive data sent from the quiz server
        function will run in a thread (coroutine) alongside the rest of the client"""
        # while the client is alive, keep receiving data from the server
        while self.settings.alive:
            try:
                # attempt to receive data from the server
                data = self._socket.recv(1024).decode("utf-8")
                # if the data is empty (indication of an error or disconnect) stop the loop (exiting the thread)
                if not data:
                    break
                # otherwise, decode the received data and load it into a dictionary
                decoded: dict = json.loads(data)
                # log a debug message with the decoded data
                self.logger.debug(f"Received data: {decoded}")

            except OSError as error:
                # if an OSError is raised (usually due to a disconnection), log an error message and stop the loop
                self.logger.error(error)
                break

            except json.decoder.JSONDecodeError as error:
                # if a JSONDecodeError is raised (usually due to an invalid JSON string), log an error message
                self.logger.error(str(error))

            if not decoded.get("header", None) or not decoded.get("data", None):
                # if the received data is not valid, continue (reset to the top of the loop to try again disregarding the current data)
                continue

            # otherwise, handle the received data as intended (if all checks pass)
            self._handle_received(decoded)

        # when the above loop is broken out of (due to an error or disconnection)
        # set the alive value to false (stopping loops and threads such as the input)
        self.settings.alive = False
        # clear the CLI
        clear_screen()
        

    def _send(self, header: str, data: str):
        """called to send a data packet to the server (commands)

        Args:
            header (str): header of data to be sent
            data (str): data to be sent
        """
        # send a JSON string to the server - data is passed in as two parameters
        # combined into a dictionary object and encoded as a string then into bytes
        # data sent over the socket connection to the server with self._socket.send()
        self._socket.send(json.dumps({"header": header, "data": {header: data}}).encode('utf-8'))

    def _answer(self, answer: str):
        """used to send answer data to the server (easier than specifying values) will call the above _send function

        Args:
            answer (str): answer string to sent to server
        """
        # calls the _send function with the 'answer' header and the answer data
        self._send("answer", answer)

    # client message --------------------------------------------------------------

    def input(self, message: str):
        """message and send it to the quiz server

        Args:
            message (str): raw input given by the user
        """
        sanitised_input: list[str] = (re.sub(' +', ' ', message.strip())).lower().split(" ")
        cmd = sanitised_input[0]
        args = sanitised_input[1:]
        handler = self._get_respective_handler(cmd)
        if handler:
            try:
                handler(command=cmd, args=args)
            except TypeError:
                handler()
        elif self.settings.state == State.IN_GAME:
            self._answer(message)
        else:
            print(f"{Fore.RED}Invalid input, please try again.{Fore.RESET}\n")


def main():
    """main function for the client"""
    # clear the CLI
    clear_screen()
    # create a new session object
    session = Session(settings.HOST, settings.PORT)
    # connect to the server through the session object
    session.start()
    # if the session fais to connect to the server, cancel
    if not session.settings.alive:
        return
    # display the help menu in the CLI
    session._help()
    # while the connection is alive (client is still connected to the server)
    while session.settings.alive:
        # accept input from the user
        user_input = input(f"{session.prefix()} > " if session.settings.state != State.IN_GAME else "")
        # clear the CLI
        clear_screen()
        # if the length of the input is below 1, reset the loop (accept different input)
        if len(user_input) < 1:
            continue
        # otherwise
        # if the input is 'exit', stop the connection and exit the program
        if user_input == "exit":
            session.stop()
            break
        # otherwise
        # pass the input into the session object
        session.input(user_input)
        # wait half a second
        time.sleep(0.5)
    

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        input(error)
    time.sleep(0.5)
    print(f"\n{Fore.RED}Connection closed{Fore.RESET}\n")
    input("\nPress enter to exit...")

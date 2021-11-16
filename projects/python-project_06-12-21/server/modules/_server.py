import socket
import threading
from collections import namedtuple

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Logger, Client, Game

class Server:
    """Server class - used for management of games and connected clients"""
    __running = False
    __games = []
    __clients = []
    __data = namedtuple('ServerData', ['games', 'clients', 'nuid'])([], [], 1)
    
    def __init__(self, host: str, port: int) -> None:
        self.__host = host
        self.__port = port
        self.logger = Logger("Server")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM).bind((host, port))
        
    def start(self) -> None:
        """Start the server - wait for and handle connections from clients"""
        
        # Opening the socket for listening
        self.socket.listen(5)
        self.logger.info(f"Listening on {self.__host}:{self.__port}")
        
        # Begin listening for and handling connections
        self.__running = True
        while self.__running:
            # Accepting a new connection fron a Client socket
            conn, addr = sock.accept()
            # Creation of new object using the Client class
            new_client = Client(self, conn, addr, self.__data.nuid)
            # Incrementing the next unique ID
            self.__data.nuid += 1
            # Starting the client listener
            threading.Thread(target=new_client.listen).start()
            # Adding Client objects to list of known/active clients
            self.__add_client(new_client)
            self.logger.info("Connection from {}:{}".format(*addr))

        self.logger.info("Server stopped")     

    def stop(self) -> None:
        """Stop the server - setting the __running value stopping process of listening for connections"""
        self.__running = False
        
    # SETTER/MODIFICATION METHODS
    
    def add_game(self, game: 'Game') -> None:
        """Add a game to the list of known games"""
        self.__data.games.append(game)
        
        self.logger.info(f"Game with identifier {game.get_code()} added")
    
    def remove_game(self, game: 'Game') -> None:
        """Remove a game from the list of known games"""
        self.__data.games.remove(game)
        
        self.logger.info(f"Game with identifier {game.get_code()} removed")
        
    def add_client(self, client: Client) -> None:
        """Add a client to the list of known clients"""
        self.__data.clients.append(client)
        
        self.logger.info(f"Client with identifier {client.get_uid()} added")
    
    def remove_client(self, client: Client) -> None:
        """Remove a client from the list of known clients"""
        self.__data.clients.remove(client)
        
        self.logger.info(f"Client with identifier {client.get_uid()} removed")
    
    # GETTER METHODS
    
    def get_games(self) -> list:
        """Return the list of known games"""
        return self.__data.games
    
    def get_clients(self) -> list:
        """Return the list of known clients"""
        return self.__data.clients
    
    def get_game_from_code(self, code: str) -> 'Game':
        """Return the game with the given code"""
        return next((x for x in self.get_games() if x.get_code() == code), None)
    
    def get_client_from_id(self, uid: int) -> Client:
        """Return the client with the given ID"""
        return next((x for x in self.get_clients() if x.get_uid() == uid), None)
    
    # EVENTS
    
    def client_disconnected(self) -> None:
        """function called by a client object when it disconnects or stops responding"""
        self.remove_client(client)
        client_game = client.get_game()
        if client_game:
            client_game.client_leave(client)
            
        self.logger.info("Disconnect from {}:{}".format(*client.get_address()))


from . import Logger, Client, Game
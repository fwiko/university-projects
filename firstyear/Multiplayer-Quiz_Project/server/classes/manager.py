from __future__ import annotations

# importing python packages
import threading

# importing custom classes/files
import classes.game as game
import classes.client as client
from utility import Logger


class Manager:
    _next_uid: int = 1
    games: list[game.Game] = []
    clients: list[client.Client] = []

    def __init__(self):
        self.logger = Logger(self.__class__.__name__)

    # setters

    def add_client(self, conn: socket.socket, addr: tuple) -> None:
        """method to add a client to the manager

        Args:
            conn (socket.socket): the socket object of the new client connection
            addr (tuple): a tuple containing address information of the connection
        """
        # create a new client object using the Client class
        c = client.Client(self, self._next_uid, conn, addr)
        # increment the next_uid attribute of the manager (this is used to assign a unique id to each client)
        self._next_uid += 1
        # add the client to the managers list of active/connected clients
        self.clients.append(c)
        # start the new clients listener thread (this will handle all incoming communcation from the client)
        threading.Thread(target=c.listen).start()
        self.logger.debug("Added client {}:{}".format(*c.addr))

    def remove_client(self, client: client.Client) -> None:
        """method to remove a client from the manager

        Args:
            client (client.Client): the client object to be removed
        """
        # if the client is in the manager objects list of clients
        if client in self.clients:
            # remove the client object from the list
            self.clients.remove(client)
            self.logger.debug("Removed client {}:{}".format(*client.addr))

    def add_game(self, game: game.Game) -> None:
        """method to add a game to the manager

        Args:
            game (game.Game): game object to be added
        """
        # add the passed in game object to the managers list of active games/game lobbies
        self.games.append(game)
        self.logger.debug(f"Added game {game.settings.code}")

    def remove_game(self, game: game.Game) -> None:
        """method to remove a game from the manager

        Args:
            game (game.Game): game object to be removed
        """
        # if the passed in game object is in the managers list of games
        if game in self.games:
            # remove the game object from the list
            self.games.remove(game)
            self.logger.debug(f"Removed game {game.settings.code}")

    # getters

    def get_games(self) -> list[game.Game]:
        """method to get a list of all games in the manager

        Returns:
            list[game.Game]: list of game objects within the manager storage
        """
        return self.games

    def get_clients(self) -> list[client.Client]:
        """method to get a list of all clients in the manager

        Returns:
            list[client.Client]: list of client objects within the manager storage
        """
        return self.clients

    def get_game_from_code(self, game_code: str) -> game.Game or None:
        """method to get a game object from the manager based on the game code

        Args:
            game_code (str): the join code of the game that the game will be recognised by

        Returns:
            game.Game or None: either the game object if one was found or None if no game was found
        """
        # return the first game object in the manager list of games that has the same code as the passed in game code
        # if one is found, if one cannot be found return None
        return next(
            (game for game in self.games if game.settings.code == game_code), None
        )

    def get_client_from_uid(self, client_uid: int) -> client.Client or None:
        """method to get a client object from the manager based on the client uid

        Args:
            client_uid (int): unique identification number of the client object

        Returns:
            client.Client or None: either the retreived client object if one was found or None
        """
        return next(
            (client for client in self.clients if client.uid == client_uid), None
        )

    # manager interaction

    def client_exit(self, client: client.Client) -> None:
        """method to handle the exit/disconnection of a client

        Args:
            client (client.Client): client object that has exited/disconnected
        """
        self.logger.info("Client disconnect: {}:{}".format(*client.addr))
        # remove the passed in client from the managers list of clients
        self.remove_client(client)
        # if clients game attribute exists
        if client.game is not None:
            # trigger the client leave event within the game to remove the client from the game
            client.game.client_leave(client)

    def game_close(self, g: game.Game) -> None:
        """method to handle the closure of a game/game lobby

        Args:
            g (game.Game): game object that has closed/is closing
        """
        # remove the passed in game object from the managers list of games
        self.remove_game(g)

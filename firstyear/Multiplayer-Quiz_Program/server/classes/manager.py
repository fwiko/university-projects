from __future__ import annotations

import threading

import classes.game as game
import classes.client as client

from modules import Logger

class Manager:
    _next_uid: int = 1
    games: list[game.Game] = []
    clients: list[client.Client] = []
    def __init__(self):
        self.logger = Logger(self.__class__.__name__)
        
    # setters
        
    def add_client(self, conn: socket.socket, addr: tuple) -> None:
        c = client.Client(self, self._next_uid, conn, addr)
        self._next_uid += 1
        self.clients.append(c)
        threading.Thread(target=c.listen).start()
        self.logger.debug("Added client {}:{}".format(*c.addr))
        
    def remove_client(self, client: client.Client) -> None:
        if client in self.clients:
            self.clients.remove(client)
            self.logger.debug("Removed client {}:{}".format(*client.addr))

    def add_game(self, game: game.Game) -> None:
        self.games.append(game)
        self.logger.debug(f"Added game {game.settings.code}")

    def remove_game(self, game: game.Game) -> None:
        if game in self.games:
            self.games.remove(game)
            self.logger.debug(f"Removed game {game.settings.code}")
    
    # getters
    
    def get_games(self) -> list[game.Game]:
        return self.games
    
    def get_clients(self) -> list[client.Client]:
        return self.clients
    
    def get_game_from_code(self, game_code: str) -> game.Game or None:
        return next((game for game in self.games if game.settings.code == game_code), None)
    
    def get_client_from_uid(self, client_uid: int) -> client.Client or None:
        return next((client for client in self.clients if client.uid == client_uid), None)
    
    # manager interaction
    
    def client_exit(self, client: client.Client) -> None:
        self.logger.info("Client disconnect: {}:{}".format(*client.addr))
        self.remove_client(client)
        if client.game is not None:
            client.game.client_leave(client)
        
    def game_close(self, g: game.Game) -> None:
        self.remove_game(g)

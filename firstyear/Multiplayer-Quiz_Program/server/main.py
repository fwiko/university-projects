from __future__ import annotations

import os
import sys
import json
import socket
import settings
import threading

from utility import Logger
from classes import manager


def connection_listener(m: manager.Manager) -> None:
    # create a socket object
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # bind the socket to the address and port specified in the settings file
        sock.bind((settings.HOST, settings.PORT))
        # listen for incoming connections
        sock.listen()
        logger.info(f"Listening on {settings.HOST}:{settings.PORT}")
        # while the server is running
        while True:
            # accept connections from clients
            conn, addr = sock.accept()
            logger.info("Client connect: {}:{}".format(*addr))
            # pass the connection into the manager class to handle the client from here on
            m.add_client(conn, addr)
            
            
def main() -> None:
    # create a manager class instance
    m = manager.Manager()
    # create a thread to listen for incoming connections with the connection_listener function
    threading.Thread(target=connection_listener, args=[m]).start()

# if this file is run directly
if __name__ == "__main__":
    # create a logger object
    logger = Logger("Listener")
    # run the main function
    main()

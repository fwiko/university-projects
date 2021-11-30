from __future__ import annotations

# importing python packages
import socket
import settings

# importing custom classes/files
from utility import Logger
from classes import manager


def connection_listener(m: manager.Manager) -> None:
    """the main connection listener, will wait for incoming connections from clients and send them to be processed

    Args:
        m (manager.Manager): the manager object for the server
    """
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
            logger.info("Connection from client at {}:{}".format(*addr))
            # pass the connection into the manager class to handle the client from here on
            m.add_client(conn, addr)
            

# if this file is run directly
if __name__ == "__main__":
    # create a logger object
    logger = Logger("Listener")
    # run the listner function while passing in a new manager object
    connection_listener(manager.Manager())

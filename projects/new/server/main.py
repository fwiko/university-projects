from __future__ import annotations

import os
import sys
import json
import socket
import settings
import threading

from modules import Logger
from classes import manager


def connection_listener(m: manager.Manager) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((settings.HOST, settings.PORT))
        sock.listen()
        logger.info(f"Listening on {settings.HOST}:{settings.PORT}")
        running = True
        while running:
            conn, addr = sock.accept()
            logger.info("Client connect: {}:{}".format(*addr))
            m.add_client(conn, addr)
            
            
def main() -> None:
    m = manager.Manager()
    threading.Thread(target=connection_listener, args=[m]).start()


if __name__ == "__main__":
    logger = Logger("Listener")
    main()

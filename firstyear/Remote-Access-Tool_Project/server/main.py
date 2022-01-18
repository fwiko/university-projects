import socket
import threading
import time

# import utility
# import settings
import modules.session_manager as sm




if __name__ == "__main__":
    manager = sm.SessionManager()
    manager.connection_listener()
    while True:
        pass
    
    
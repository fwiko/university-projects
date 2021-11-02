import re
import sys
import time
import json
import socket
import threading

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 5555


class Session:
    alive = False
    __state = None
    commands = {}
    
    def __init__(self, address, port):
        self.__client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = address
        self.port = port
    
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
        self.__client_socket.send(json.dumps({"header":header, "data":data}).encode())
    
    def receiver(self):
        while True:
            try:
                data = self.__client_socket.recv(1024)
                if len(data) < 1: break
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
        elif header == "commands":
            self.commands = data
        elif header == "alert":
            console_output(header, data.get("message", None))
            

# client-side terminal output function
def console_output(prefix, message):
    print(f"[{prefix.upper()}] > {message}")

if __name__ == '__main__':
    session = Session(SERVER_ADDRESS, SERVER_PORT)
    session.connect()
    time.sleep(.5)
    print("\n".join([f"{key} | {value['desc']}" for key, value in session.commands.items()]))
    try:
        while session.alive:
            user_input = (re.sub(' +', ' ', input("$ ").strip())).lower().split(" ")
            if user_input[0] == "exit":
                session.disconnect()
            elif user_input[0] in session.commands.keys():
                if user_input[0] == "host":
                    session.send("command", {"command":"host"})
    except Exception as e:
        print("DISCONNECTED", e)
        session.disconnect()

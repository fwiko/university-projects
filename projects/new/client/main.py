import re
import time
import json
import socket
import threading

import settings

class Session():
    def __init__(self, host: str, port: int):
        self.alive = True
        self._host = host
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # server connection  

    def start(self):
        """initiate the connection with the quiz server"""
        self._socket.connect((self._host, self._port))
        self.listener_thread = threading.Thread(target=self._receiver).start()
        
    def stop(self):
        self.alive = False
        self._socket.close()
    
    # receiving data from the server
    
    def _handle_received(self, data: str):
        """handles received data from the quiz server"""
        pass
    
    def _receiver(self):
        """receive data sent from the quiz server
        function will run in a thread (coroutine) alongside the rest of the client"""
        while self.alive:
            try:
                data = self._socket.recv(1024).decode('utf-8')
                if not data: break
                print(data)
            except Exception as e:
                print(e)
                break
        self.alive = False
        print("Connection closed")
        
    # received data handling
    
    
    
    # sending data to the server
    
    def _send(self, header: str, data: str):
        self._socket.send(json.dumps({"header": header, "data": {header: data}}).encode('utf-8'))
        
    def _command(self, **kwargs):
        """handles user input"""
        cmd = kwargs.get("command")
        args = kwargs.get("args")
        self._send("command", f"{cmd}{' ' + ' '.join(args) if args else ''}")
        
    def _answer(self, answer: str):
        self._send("answer", answer)
        
    # additional handlers
    
    def _help_menu(self):
        print(settings.HELP_MENU)
        
    # handling user input
    
    def _get_handler(self, command: str):
        """handles user input"""
        if command in ("host", "join", "leave", "start", "games"):
            return self._command
        elif command in ("help"):
            return self._help_menu
    
    def input(self, input: str):
        """input and send it to the quiz server"""
        sanitised_input: list[str] = (re.sub(' +', ' ', input.strip())).lower().split(" ")
        cmd = sanitised_input[0]
        args = sanitised_input[1:]
        handler = self._get_handler(cmd)
        if handler:
            handler(command=cmd, args=args)
    

if __name__ == '__main__':
    session = Session(settings.HOST, settings.PORT)
    session.start()
    while True:
        message = input("> ")
        if message == "exit":
            break
        try:
            session.input(message)
        except Exception as e:
            print(e)
            input("Press enter to continue...")
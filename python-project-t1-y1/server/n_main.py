import re
import socket
import threading

HOST = "0.0.0.0"
PORT = 5555


class Client:
    __alive = False
    __state = "menu"
    
    def __init__(self, conn, addr, uid):
        self.conn = conn
        self.addr = addr
        self.uid = uid
    
    def listen(self):
        self.__alive = True
        self.conn.settimeout(300)
        while self.__alive:
            try:
                data = self.conn.recv(1024)
                parsed_data = data.decode()
                print(parsed_data)
            except:
                break
        SERVER.died(self)
        
    def __client_command(self, command):
        if self.__state == "inMenu":
            pass
        elif self.__state == "inGame":
            pass
    
    def kill(self):
        self.__alive = False
        self.conn.close()
    
        

class Server:
    __running = False
    __clients = []
    __games = []
    __next_uid = 1
    
    # handles client connections - gets relevant data and creates a client object based on the Client class
    def __handle_connection(self, conn, addr):
        console_output("server", "Connection from {}:{}".format(*conn.getpeername()))
        new_client = Client(conn, addr, self.__next_uid)
        self.__next_uid += 1
        thread = threading.Thread(target=new_client.listen)
        thread.start()
        self.__clients.append(new_client)
    
    # main listener - listening for client connections and passing them to the handler
    def listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((HOST, PORT))
            self.__running = True
            while self.__running:
                
                sock.listen()
                conn, addr = sock.accept()
                self.__handle_connection(conn, addr)
                
    # signal to the server that a client has stopped responding - lost connection
    def died(self, client):
        console_output("server", "Disconnect from {}:{}".format(*client.addr))
        self.__clients.remove(client)
    
    # handle instructions sent to server from server-side command line
    def instruction(self, instruction, args):
        if instruction == "stop":
            self.__stop()
        if instruction == "kill":
            client = next((x for x in self.__clients if x.uid == args[0]), None)
            if client:
                client.kill()

    # return list of clients connected to the server
    def get_clients(self):
        return self.__clients
            
    # stop everything - close server..
    def __stop(self):
        self.__running = False
    
# handle commands executed within the server-side terminal
def handle_command(command, args):
    if command == "clients":
        formatted_clients =  "\n".join(["{} | {}:{}".format(x.uid, *x.conn.getpeername()) for x in SERVER.get_clients()]) or "\nNo connections\n"
        print(f"\n{formatted_clients}\n")
    if command == "kill":
        if len(args) < 1 or not args[0].isnumeric():
            return
        SERVER.instruction("kill", [int(args[0])])

# server-side terminal output function
def console_output(prefix, message):
    print(f"\n[{prefix.upper()}] > {message.capitalize()}\n")

if __name__ == "__main__":
    SERVER = Server()
    # main server thread - listening for connections - handling games etc..
    server_thread = threading.Thread(target=SERVER.listen)
    server_thread.start()
    
    # server CLI - if for whatever reason something needs to be controlled on the server side
    while True:
        server_cmd = (re.sub(' +', ' ', input("SERVER :> ").strip())).lower().split(" ")
        if server_cmd[0] == "exit":
            SERVER.instruction("stop")
            break
        handle_command(server_cmd[0], server_cmd[1:])

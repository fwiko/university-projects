import PIL


HOST_ADDRESS = "127.0.0.1"
HOST_PORT = 1337


class Client:
    def __init__(self, host: str, port: int):
        self._addr = host, port

    def start(self):
        pass

    def _connect(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            while True:
                try:
                    sock.connect(self._addr)
                    while True:
                        data = sock.recv(1024)
                        if not data:
                            break
                        self._handle_data(data.decode("utf-8"))
                except OSError:
                    pass


if __name__ == "__main__":
    pass

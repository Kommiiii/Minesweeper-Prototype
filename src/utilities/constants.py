import os
import sys
import json

WHITE = (255, 255, 255)


def get_resource_path(relative_path: str) -> str:
    """Safe file handling that ALWAYS finds the Minesweeper root folder."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(current_dir)
        base_path = os.path.dirname(src_dir)

    return os.path.join(base_path, relative_path)

def get_save_path(filename: str) -> str:
    """Ensures save data stays next to the .exe permanently."""
    if getattr(sys, 'frozen', False):
        # If running as a compiled .exe, save next to the executable
        base_path = os.path.dirname(sys.executable)
    else:
        # If running in IDE, save in the project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(os.path.dirname(current_dir))

    return os.path.join(base_path, filename)

class GameConfig:
    _instance = None
    CONFIG_FILE = "settings.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GameConfig, cls).__new__(cls)
            cls._instance.load()
        return cls._instance

    def load(self):
        self.settings = {
            "width": 1080,
            "height": 720,
            "fullscreen": False,
            "custom_rows": 10,
            "custom_cols": 10,
            "custom_mines": 15
        }
        path = get_save_path(self.CONFIG_FILE)
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.settings.update(json.load(f))

    def save(self):
        path = get_save_path(self.CONFIG_FILE)
        with open(path, 'w') as f:
            json.dump(self.settings, f, indent=4)
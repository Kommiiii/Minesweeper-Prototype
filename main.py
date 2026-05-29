import sys
import pygame
from src.utilities.constants import GameConfig
from src.core.game_engine import Engine
from src.interface.menu_screens import AppRouter
from src.utilities.asset_loader import AssetManager
from src.core.audio_manager import AudioManager


def main():
    AudioManager.init_audio()

    pygame.init()

    config = GameConfig()

    engine = Engine(config)

    AssetManager.load_assets()

    app_router = AppRouter(config)

    engine.run(app_router)

    config.save()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
import pygame
import os
from src.utilities.constants import get_resource_path

class AssetManager:
    tiles = {}
    _scaled_cache = {}

    @classmethod
    def get_tile_scaled(cls, name, size):
        cache_key = (name, size)
        if cache_key not in cls._scaled_cache:
            tile = cls.get_tile(name)
            cls._scaled_cache[cache_key] = pygame.transform.scale(tile, (size, size))
        return cls._scaled_cache[cache_key]

    @classmethod
    def load_assets(cls):
        # Now looking in the "assets" folder for your tiles!
        image_path = get_resource_path(os.path.join("assets", "minesweeper_tiles.png"))
        if not os.path.exists(image_path):
            print(f"Error: Could not find tileset at: {image_path}")
            return

        try:
            sheet = pygame.image.load(image_path).convert_alpha()
        except pygame.error as e:
            print(f"Error loading image: {e}")
            return

        w, h = sheet.get_size()
        tile_size = 16
        cols = w // tile_size

        keys = [
            '1', '2', '3', '4', '5', '6', '7', '8',
            'empty', 'unrevealed', 'mine', 'flag',
            'smile', 'sad', 'ooh', 'menu',
            'question', 'hint'
        ]

        for i, key in enumerate(keys):
            x = (i % cols) * tile_size
            y = (i // cols) * tile_size
            if x + tile_size <= w and y + tile_size <= h:
                cls.tiles[key] = sheet.subsurface((x, y, tile_size, tile_size))

        # Now looking in the "assets" folder for your custom logo!
        logo_path = get_resource_path(os.path.join("assets", "minesweeper_logo.png"))
        if os.path.exists(logo_path):
            try:
                cls.tiles['logo'] = pygame.image.load(logo_path).convert_alpha()
            except pygame.error:
                cls.tiles['logo'] = None

    @classmethod
    def get_tile(cls, name):
        if name not in cls.tiles:
            return pygame.Surface((32, 32))
        return cls.tiles.get(name)
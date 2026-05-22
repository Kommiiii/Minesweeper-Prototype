import pygame
from src.board import Board
from src.ui import Button, draw_text_screen
import os

WHITE = (255, 255, 255)


class AssetManager:
    tiles = {}
    _scaled_cache = {}

    @classmethod
    def get_tile_scaled(cls, name, size):
        """Returns a tile scaled to `size x size`, cached to avoid per-frame scaling."""
        cache_key = (name, size)
        if cache_key not in cls._scaled_cache:
            tile = cls.get_tile(name)
            cls._scaled_cache[cache_key] = pygame.transform.scale(tile, (size, size))
        return cls._scaled_cache[cache_key]

    @classmethod
    def load_assets(cls):
        image_path = os.path.join("sprite", "minesweeper_tiles.png")
        if not os.path.exists(image_path):
            print(f"Error: Could not find tileset at: {image_path}")
            return

        try:
            sheet = pygame.image.load(image_path).convert_alpha()
        except pygame.error as e:
            print(f"Error loading image: {e}")
            return

        # --- DEBUG: Print dimensions to verify tile_size ---
        w, h = sheet.get_size()
        print(f"Tileset loaded! Dimensions: {w}x{h}")

        tile_size = 16  # confirmed 16x16
        cols = w // tile_size  # will be 4

        keys = [
            '1', '2', '3', '4',
            '5', '6', '7', '8',
            'empty', 'unrevealed', 'mine', 'flag',
            'smile', 'sad', 'ooh', 'menu'
        ]

        for i, key in enumerate(keys):
            x = (i % cols) * tile_size
            y = (i // cols) * tile_size

            # --- SAFETY CHECK ---
            # Only slice if the full tile fits within the image boundaries
            if x + tile_size <= w and y + tile_size <= h:
                cls.tiles[key] = sheet.subsurface((x, y, tile_size, tile_size))
            else:
                print(f"Warning: Skipping tile '{key}' (Position {x},{y} is out of bounds)")

    @classmethod
    def get_tile(cls, name):
        # Return the tile, or a default empty surface if it's missing (prevents crashes)
        if name not in cls.tiles:
            return pygame.Surface((32, 32))
        return cls.tiles.get(name)


def create_board(rows, cols, mines, screen_width, screen_height):
    max_w = screen_width - 40
    max_h = screen_height - 110  # Reduced to account for the fixed UI header
    cell_size = max(15, min(50, min(max_w // cols, max_h // rows)))

    board = Board(rows, cols, mines, cell_size)
    board_w = cols * cell_size
    board_h = rows * cell_size
    offset_x = (screen_width - board_w) // 2

    # Force the board to always draw below the 80px header
    offset_y = max(90, (screen_height - board_h) // 2 + 20)
    board.update_rects(offset_x, offset_y)

    AssetManager._scaled_cache.clear()

    return board


class MinesweeperApp:
    def __init__(self):
        # Display Settings
        self.width, self.height = 1280, 800
        self.is_fullscreen = False
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Minesweeper")

        AssetManager.load_assets()

        # Fonts
        self.title_font = pygame.font.SysFont(None, 64)
        self.subtitle_font = pygame.font.SysFont(None, 32)
        self.ui_font = pygame.font.SysFont(None, 40)
        self.stat_font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 20)

        # Game State Variables
        self.clock = pygame.time.Clock()
        self.state = "MENU"
        self.previous_state = "MENU"
        self.running = True

        # Input Tracking
        self.mouse_pos = (0, 0)
        self.mouse_clicked = False
        self.click_handled = False
        self.valid_game_click = False
        self.is_mouse_down = False  # <-- NEW: Tracks physical mouse down state

        # Board Data
        self.game_board = None
        self.cur_r, self.cur_c, self.cur_m = 9, 9, 10
        self.cust_r, self.cust_c, self.cust_m = 10, 10, 15
        self.elapsed_time = 0.0
        self.ui_y = 0

        # Persistent Game UI
        self.in_game_menu_btn = Button("", self.small_font, 0, 0, 40, 40)
        self.face_btn = Button("", self.subtitle_font, 0, 0, 40, 40)  # <-- REVERTED to empty square

    def run(self):
        """The main execution loop."""
        while self.running:
            dt = self.clock.tick(60)
            self.mouse_pos = pygame.mouse.get_pos()
            self.mouse_clicked = False

            self._update_layout()
            self._handle_events()

            if self.state == "GAME" and self.game_board and not self.game_board.game_over and not self.game_board.is_won:
                self.elapsed_time += dt / 1000.0

            self._render()

    def _update_layout(self):
        """Dynamically anchors UI if the board exists."""
        if self.game_board:
            # Anchor the face button strictly to the center of the screen
            self.face_btn.rect.center = (self.width // 2, 40)

            # Anchor the pause menu safely to the top right corner
            self.in_game_menu_btn.rect.topleft = (self.width - 60, 20)

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouse_clicked = True
                    if self.state == "GAME" and self.game_board:
                        self.valid_game_click = True
                        self.is_mouse_down = True  # <-- Trigger the 'Ooh' face

                elif event.button == 3 and self.state == "GAME" and self.game_board:
                    self.game_board.toggle_flag(*self.mouse_pos)

                elif event.button == 2 and self.state == "GAME" and self.game_board:
                    self.game_board.handle_chord(*self.mouse_pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.is_mouse_down = False  # <-- Revert the face back to normal
                    if self.state == "GAME" and self.game_board and self.valid_game_click:
                        if not self.face_btn.is_clicked(self.mouse_pos) and not self.in_game_menu_btn.is_clicked(
                                self.mouse_pos):
                            self.game_board.handle_click(*self.mouse_pos)

                    self.valid_game_click = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "PAUSE" if self.state == "GAME" else "GAME" if self.state == "PAUSE" else self.state

        if not pygame.mouse.get_pressed()[0]:
            self.click_handled = False

    def _render(self):
        """Routes drawing logic based on the current state."""
        self.screen.fill((30, 30, 32))

        if self.state == "MENU":
            self._draw_menu()
        elif self.state == "DIFFICULTY":
            self._draw_difficulty()
        elif self.state == "CUSTOM_SETUP":
            self._draw_custom_setup()
        elif self.state == "SETTINGS":
            self._draw_settings()
        elif self.state == "CREDITS":
            self._draw_credits()
        elif self.state == "PAUSE":
            self._draw_pause()
        elif self.state == "GAME":
            self._draw_game()

        pygame.display.flip()

    # --- INDIVIDUAL STATE RENDERERS ---

    def _draw_menu(self):
        draw_text_screen(self.screen, "MINESWEEPER", self.title_font, self.width, self.height)

        b1 = Button("Standard Mode", self.subtitle_font, self.width // 2, 250, 50)
        b2 = Button("Settings", self.subtitle_font, self.width // 2, 320, 50)
        b3 = Button("Credits", self.subtitle_font, self.width // 2, 390, 50)
        b4 = Button("Exit", self.subtitle_font, self.width // 2, 460, 50, hover_color=(200, 100, 100))

        for b in [b1, b2, b3, b4]: b.draw(self.screen, self.mouse_pos)

        if self.mouse_clicked and not self.click_handled:
            if b1.is_clicked(self.mouse_pos):
                self.state = "DIFFICULTY"
            elif b2.is_clicked(self.mouse_pos):
                self.previous_state, self.state = "MENU", "SETTINGS"
            elif b3.is_clicked(self.mouse_pos):
                self.state = "CREDITS"
            elif b4.is_clicked(self.mouse_pos):
                self.running = False
            self.click_handled = True

    def _draw_difficulty(self):
        draw_text_screen(self.screen, "Select Difficulty", self.title_font, self.width, self.height)

        # Calculate dynamic Y spacing based on current screen height
        center_y = self.height // 2

        d1 = Button("Beginner (9x9, 10)", self.subtitle_font, self.width // 2, center_y - 140, 50,
                    hover_color=(150, 200, 150))
        d2 = Button("Intermediate (16x16, 40)", self.subtitle_font, self.width // 2, center_y - 70, 50,
                    hover_color=(200, 200, 150))
        d3 = Button("Expert (30x16, 99)", self.subtitle_font, self.width // 2, center_y, 50,
                    hover_color=(200, 150, 150))
        d4 = Button("Custom", self.subtitle_font, self.width // 2, center_y + 70, 50)
        back = Button("Back", self.subtitle_font, self.width // 2, center_y + 140, 50)

        for b in [d1, d2, d3, d4, back]: b.draw(self.screen, self.mouse_pos)

        if self.mouse_clicked and not self.click_handled:
            if d1.is_clicked(self.mouse_pos):
                self.cur_r, self.cur_c, self.cur_m = 9, 9, 10
            elif d2.is_clicked(self.mouse_pos):
                self.cur_r, self.cur_c, self.cur_m = 16, 16, 40
            elif d3.is_clicked(self.mouse_pos):
                self.cur_r, self.cur_c, self.cur_m = 16, 30, 99
            elif d4.is_clicked(self.mouse_pos):
                self.state = "CUSTOM_SETUP"; self.click_handled = True; return
            elif back.is_clicked(self.mouse_pos):
                self.state = "MENU"; self.click_handled = True; return
            else:
                return  # Avoid triggering game creation on background clicks

            self.game_board = create_board(self.cur_r, self.cur_c, self.cur_m, self.width, self.height)
            self.elapsed_time, self.state, self.click_handled = 0.0, "GAME", True

    def _draw_custom_setup(self):
        draw_text_screen(self.screen, "Custom Setup", self.title_font, self.width, self.height)
        cx = self.width // 2

        btns = {
            "r-": Button("-", self.subtitle_font, cx - 100, 220, 40, min_width=50),
            "r+": Button("+", self.subtitle_font, cx + 100, 220, 40, min_width=50),
            "c-": Button("-", self.subtitle_font, cx - 100, 280, 40, min_width=50),
            "c+": Button("+", self.subtitle_font, cx + 100, 280, 40, min_width=50),
            "m-": Button("-", self.subtitle_font, cx - 100, 340, 40, min_width=50),
            "m+": Button("+", self.subtitle_font, cx + 100, 340, 40, min_width=50),
            "start": Button("Start", self.subtitle_font, cx, 420, 50, hover_color=(150, 200, 150)),
            "back": Button("Back", self.subtitle_font, cx, self.height - 100, 50)
        }

        for btn in btns.values(): btn.draw(self.screen, self.mouse_pos)
        self.screen.blit(self.subtitle_font.render(f"Rows: {self.cust_r}", True, WHITE), (cx - 40, 230))
        self.screen.blit(self.subtitle_font.render(f"Cols: {self.cust_c}", True, WHITE), (cx - 40, 290))
        self.screen.blit(self.subtitle_font.render(f"Mines: {self.cust_m}", True, WHITE), (cx - 40, 350))

        if self.mouse_clicked and not self.click_handled:
            if btns["r-"].is_clicked(self.mouse_pos):
                self.cust_r = max(5, self.cust_r - 1)
            elif btns["r+"].is_clicked(self.mouse_pos):
                self.cust_r = min(30, self.cust_r + 1)
            elif btns["c-"].is_clicked(self.mouse_pos):
                self.cust_c = max(5, self.cust_c - 1)
            elif btns["c+"].is_clicked(self.mouse_pos):
                self.cust_c = min(50, self.cust_c + 1)
            elif btns["m-"].is_clicked(self.mouse_pos):
                self.cust_m = max(1, self.cust_m - 1)
            elif btns["m+"].is_clicked(self.mouse_pos):
                self.cust_m = min((self.cust_r * self.cust_c) - 1, self.cust_m + 1)
            elif btns["back"].is_clicked(self.mouse_pos):
                self.state = "DIFFICULTY"
            elif btns["start"].is_clicked(self.mouse_pos):
                self.cur_r, self.cur_c, self.cur_m = self.cust_r, self.cust_c, self.cust_m
                self.game_board = create_board(self.cur_r, self.cur_c, self.cur_m, self.width, self.height)
                self.elapsed_time, self.state = 0.0, "GAME"
            self.click_handled = True

    def _draw_settings(self):
        draw_text_screen(self.screen, "Settings", self.title_font, self.width, self.height)
        fs_text = "Windowed" if not self.is_fullscreen else "Fullscreen"

        s1 = Button(fs_text, self.subtitle_font, self.width // 2, 250, 50)
        s2 = Button("960 x 600", self.subtitle_font, self.width // 2, 320, 50)
        s3 = Button("1280 x 800", self.subtitle_font, self.width // 2, 390, 50)
        back = Button("Close", self.subtitle_font, self.width // 2, self.height - 100, 50)

        for b in [s1, s2, s3, back]: b.draw(self.screen, self.mouse_pos)

        if self.mouse_clicked and not self.click_handled:
            update_board = False
            if s1.is_clicked(self.mouse_pos):
                self.is_fullscreen = not self.is_fullscreen
                self.screen = pygame.display.set_mode((self.width, self.height),
                                                      pygame.FULLSCREEN if self.is_fullscreen else 0)
            elif s2.is_clicked(self.mouse_pos):
                self.width, self.height, update_board = 960, 600, True
            elif s3.is_clicked(self.mouse_pos):
                self.width, self.height, update_board = 1280, 800, True
            elif back.is_clicked(self.mouse_pos):
                self.state = self.previous_state

            if update_board:
                self.screen = pygame.display.set_mode((self.width, self.height),
                                                      pygame.FULLSCREEN if self.is_fullscreen else 0)
                if self.game_board: self.game_board = create_board(self.cur_r, self.cur_c, self.cur_m, self.width,
                                                                   self.height)
            self.click_handled = True

    def _draw_credits(self):
        draw_text_screen(self.screen, "Credits", self.title_font, self.width, self.height)

        # Anchor point for where the text starts
        start_y = 250
        spacing = 100

        # The list of credits to display
        credits_info = [
            ("Developer", "Kyle Dungo"),
            ("Sprite Reference (OpenGameArt.org)", "FrostC"),
            ("Game Mechanics Inspired By", "Minesweeper Online")
        ]

        # Loop through and draw each credit beautifully centered
        for i, (role, name) in enumerate(credits_info):
            # Draw the Role/Title in a softer gray
            role_surf = self.subtitle_font.render(role, True, (180, 180, 180))
            role_rect = role_surf.get_rect(center=(self.width // 2, start_y + (i * spacing)))
            self.screen.blit(role_surf, role_rect)

            # Draw the Name in bold white
            name_surf = self.ui_font.render(name, True, WHITE)
            name_rect = name_surf.get_rect(center=(self.width // 2, start_y + (i * spacing) + 35))
            self.screen.blit(name_surf, name_rect)

        # Draw the Back button at the bottom
        back = Button("Back", self.subtitle_font, self.width // 2, self.height - 100, 50)
        back.draw(self.screen, self.mouse_pos)

        # Handle going back to the menu
        if self.mouse_clicked and not self.click_handled and back.is_clicked(self.mouse_pos):
            self.state, self.click_handled = "MENU", True

    def _draw_pause(self):
        self.game_board.draw(self.screen)
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        draw_text_screen(self.screen, "GAME PAUSED", self.title_font, self.width, self.height)

        p1 = Button("Continue", self.subtitle_font, self.width // 2, 250, 50, hover_color=(100, 150, 100))
        p2 = Button("Settings", self.subtitle_font, self.width // 2, 320, 50)
        p3 = Button("Return to Title", self.subtitle_font, self.width // 2, 390, 50, hover_color=(150, 50, 50))

        for b in [p1, p2, p3]: b.draw(self.screen, self.mouse_pos)

        if self.mouse_clicked and not self.click_handled:
            if p1.is_clicked(self.mouse_pos):
                self.state = "GAME"
            elif p2.is_clicked(self.mouse_pos):
                self.previous_state, self.state = "PAUSE", "SETTINGS"
            elif p3.is_clicked(self.mouse_pos):
                self.state = "MENU"
            self.click_handled = True

    def _draw_game(self):
        self.game_board.draw(self.screen)

        # --- NEW: Draw a dedicated UI Header background ---
        pygame.draw.rect(self.screen, (45, 45, 48), (0, 0, self.width, 80))
        pygame.draw.line(self.screen, (25, 25, 27), (0, 80), (self.width, 80), 3)

        # Top UI Text fixed to screen bounds, completely avoiding overlaps!
        self.screen.blit(self.ui_font.render(f"Time: {int(self.elapsed_time)}", True, WHITE), (30, 25))

        flags_left = self.game_board.mines - self.game_board.flags_placed
        counter_text = self.ui_font.render(f"Flags: {flags_left}", True, WHITE)
        # Positioned safely 200px away from the right edge, nowhere near the menu button
        self.screen.blit(counter_text, (self.width - 200, 25))

        # --- APPLY NEW SPRITES HERE BEFORE DRAWING ---
        # 1. Apply the static menu icon (scaled from 16x16 to 32x32 to fit the 40px button)
        self.in_game_menu_btn.image = AssetManager.get_tile_scaled('menu', 32)

        # 2. Decide which face to show based on game state and mouse state
        if self.game_board.game_over:
            face_img = 'sad'
        elif self.is_mouse_down and self.valid_game_click and not self.face_btn.is_clicked(self.mouse_pos):
            face_img = 'ooh'
        else:
            face_img = 'smile'

        # Apply the chosen face image
        self.face_btn.image = AssetManager.get_tile_scaled(face_img, 32)

        # Draw the buttons onto the screen
        self.face_btn.draw(self.screen, self.mouse_pos)
        self.in_game_menu_btn.draw(self.screen, self.mouse_pos)

        # Handle button clicks
        if self.mouse_clicked and not self.click_handled:
            if self.face_btn.is_clicked(self.mouse_pos):
                self.game_board = create_board(self.cur_r, self.cur_c, self.cur_m, self.width, self.height)
                self.elapsed_time = 0.0
            elif self.in_game_menu_btn.is_clicked(self.mouse_pos):
                self.state = "PAUSE"
            self.click_handled = True

        # Game Over / Win Panel
        if self.game_board.is_won or self.game_board.game_over:
            board_right = self.game_board.grid[0][-1].rect.right
            panel_w, panel_h = 260, 160

            if self.width - board_right > panel_w + 40:
                panel_x, panel_y = board_right + 20, self.game_board.grid[0][0].rect.y
            else:
                panel_x, panel_y = (self.width - panel_w) // 2, (self.height - panel_h) // 2
                overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                self.screen.blit(overlay, (0, 0))

            bg_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
            pygame.draw.rect(self.screen, (42, 42, 45), bg_rect)
            pygame.draw.rect(self.screen, (80, 80, 85), bg_rect, 2)

            title_txt = "YOU WIN!" if self.game_board.is_won else "GAME OVER"
            title_col = (100, 255, 100) if self.game_board.is_won else (255, 100, 100)
            title_surf = self.ui_font.render(title_txt, True, title_col)
            self.screen.blit(title_surf, (panel_x + panel_w // 2 - title_surf.get_width() // 2, panel_y + 15))

            self.screen.blit(self.stat_font.render(f"Time: {self.elapsed_time:.3f} sec", True, (220, 220, 220)),
                             (panel_x + 20, panel_y + 60))
            self.screen.blit(self.stat_font.render(f"3BV: {self.game_board.board_3bv}", True, (220, 220, 220)),
                             (panel_x + 20, panel_y + 90))
            bvs_val = (self.game_board.board_3bv / self.elapsed_time) if self.elapsed_time > 0 else 0
            self.screen.blit(self.stat_font.render(f"3BV/s: {bvs_val:.4f}", True, (220, 220, 220)),
                             (panel_x + 20, panel_y + 120))
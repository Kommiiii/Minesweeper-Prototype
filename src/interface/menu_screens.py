import pygame
import os
import random
from src.core.board_manager import Board
from src.interface.ui_components import Button, draw_text_screen
from src.utilities.asset_loader import AssetManager
from src.utilities.score_manager import ScoreManager
from src.utilities.constants import WHITE, get_resource_path
from src.core.audio_manager import AudioManager


def _load_fonts():
    font_path = get_resource_path(os.path.join("assets", "PressStart2P-Regular.ttf"))

    if os.path.exists(font_path):
        return {
            'title': pygame.font.Font(font_path, 36),
            'subtitle': pygame.font.Font(font_path, 16),
            'tab': pygame.font.Font(font_path, 13),
            'ui': pygame.font.Font(font_path, 20),
            'stat': pygame.font.Font(font_path, 11),
            'small': pygame.font.Font(font_path, 10),
        }
    else:
        print("Press Start 2P font not found — using system font fallback.")
        print("Download PressStart2P-Regular.ttf and place it in assets/ for a retro look!")
        return {
            'title': pygame.font.SysFont(None, 64),
            'subtitle': pygame.font.SysFont(None, 32),
            'tab': pygame.font.SysFont(None, 28),
            'ui': pygame.font.SysFont(None, 40),
            'stat': pygame.font.SysFont(None, 24),
            'small': pygame.font.SysFont(None, 20),
        }


def create_board(rows, cols, mines, screen_width, screen_height, max_hints):
    max_w = screen_width - 40
    max_h = screen_height - 110
    cell_size = max(15, min(50, min(max_w // cols, max_h // rows)))

    board = Board(rows, cols, mines, cell_size, max_hints)
    board_w = cols * cell_size
    board_h = rows * cell_size
    offset_x = (screen_width - board_w) // 2
    offset_y = max(90, (screen_height - board_h) // 2 + 20)

    board.update_rects(offset_x, offset_y)
    AssetManager._scaled_cache.clear()
    return board


class FloatingTile:
    def __init__(self, screen_width, screen_height):
        self.x = random.randint(0, screen_width)
        self.y = random.randint(0, screen_height)
        self.speed = random.uniform(15, 35)
        self.size = random.choice([24, 32, 48, 64])
        self.img_key = random.choice(['unrevealed', 'mine', 'flag', '1', '2'])
        self.alpha = random.randint(10, 40)

    def update(self, dt, screen_width, screen_height):
        self.y -= self.speed * dt
        if self.y + self.size < 0:
            self.y = screen_height + self.size
            self.x = random.randint(0, screen_width)

    def draw(self, surface):
        img = AssetManager.get_tile_scaled(self.img_key, self.size)
        if img:
            temp = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            temp.blit(img, (0, 0))
            temp.set_alpha(self.alpha)
            surface.blit(temp, (self.x, self.y))


class AppRouter:
    def __init__(self, config):
        self.config = config
        self.width, self.height = 1080, 720
        self.score_mgr = ScoreManager()
        self.score_filter = "Beginner"

        fonts = _load_fonts()
        self.title_font = fonts['title']
        self.subtitle_font = fonts['subtitle']
        self.tab_font = fonts['tab']
        self.ui_font = fonts['ui']
        self.stat_font = fonts['stat']
        self.small_font = fonts['small']

        self.state = "MENU"
        self.previous_state = "MENU"

        self.mouse_pos = (0, 0)
        self.mouse_clicked = False
        self.click_handled = False
        self.valid_game_click = False
        self.is_mouse_down = False

        self.game_board = None
        self.cur_r, self.cur_c, self.cur_m = 9, 9, 10
        self.cur_hints = 3
        self.cust_r, self.cust_c, self.cust_m = 10, 10, 15
        self.elapsed_time = 0.0

        self.hint_btn = Button("", self.ui_font, 0, 0, 40, min_width=40)
        self.face_btn = Button("", self.subtitle_font, 0, 0, 40, min_width=40)
        self.in_game_menu_btn = Button("", self.small_font, 0, 0, 40, min_width=40)

        self.particles = [FloatingTile(self.width, self.height) for _ in range(30)]

    def update(self, dt, events, mouse_pos):
        self.mouse_pos = mouse_pos
        self.mouse_clicked = False

        if self.state in ["MENU", "DIFFICULTY", "CUSTOM_SETUP", "SCORES", "CREDITS"]:
            for p in self.particles:
                p.update(dt, self.width, self.height)

        if self.game_board:
            self.hint_btn.rect.center = (self.width // 2 - 60, 40)
            self.hint_btn.shadow_rect.center = (self.width // 2 - 60, 44)
            self.face_btn.rect.center = (self.width // 2, 40)
            self.face_btn.shadow_rect.center = (self.width // 2, 44)
            self.in_game_menu_btn.rect.center = (self.width // 2 + 60, 40)
            self.in_game_menu_btn.shadow_rect.center = (self.width // 2 + 60, 44)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouse_clicked = True
                    if self.state == "GAME" and self.game_board:
                        self.valid_game_click = True
                        self.is_mouse_down = True
                elif event.button == 3 and self.state == "GAME" and self.game_board:
                    self.game_board.toggle_flag(*self.mouse_pos)
                elif event.button == 2 and self.state == "GAME" and self.game_board:
                    self.game_board.handle_chord(*self.mouse_pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.is_mouse_down = False
                    if self.state == "GAME" and self.game_board and self.valid_game_click:
                        if not self.face_btn.rect.collidepoint(self.mouse_pos) and \
                                not self.in_game_menu_btn.rect.collidepoint(self.mouse_pos) and \
                                not self.hint_btn.rect.collidepoint(self.mouse_pos):
                            self.game_board.handle_click(*self.mouse_pos)
                    self.valid_game_click = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "PAUSE" if self.state == "GAME" else "GAME" if self.state == "PAUSE" else self.state

        if not pygame.mouse.get_pressed()[0]:
            self.click_handled = False

        if self.state == "GAME" and self.game_board and not self.game_board.game_over and not self.game_board.is_won:
            self.elapsed_time += dt

    def render(self, surface):
        if self.state == "MENU":
            self._draw_menu(surface)
        elif self.state == "DIFFICULTY":
            self._draw_difficulty(surface)
        elif self.state == "CUSTOM_SETUP":
            self._draw_custom_setup(surface)
        elif self.state == "SCORES":
            self._draw_scores(surface)
        elif self.state == "CREDITS":
            self._draw_credits(surface)
        elif self.state == "PAUSE":
            self._draw_pause(surface)
        elif self.state == "GAME":
            self._draw_game(surface)

    def _draw_background(self, surface):
        for p in self.particles:
            p.draw(surface)

    def _draw_menu(self, surface):
        self._draw_background(surface)
        cx, cy = self.width // 2, self.height // 2

        logo = AssetManager.tiles.get('logo')
        if logo:
            scale = 600 / logo.get_width()
            scaled_h = int(logo.get_height() * scale)
            scaled_logo = pygame.transform.smoothscale(logo, (600, scaled_h))
            logo_rect = scaled_logo.get_rect(center=(cx, cy - 180))
            surface.blit(scaled_logo, logo_rect)
        else:
            draw_text_screen(surface, "MINESWEEPER", self.title_font, self.width, self.height)

        b1 = Button("Standard Mode", self.subtitle_font, cx, cy - 20, 50, min_width=300)
        b2 = Button("High Scores", self.subtitle_font, cx, cy + 50, 50, min_width=300)
        b3 = Button("Credits", self.subtitle_font, cx, cy + 120, 50, min_width=300)
        b4 = Button("Exit", self.subtitle_font, cx, cy + 190, 50, min_width=300, hover_color=(200, 100, 100))

        for b in [b1, b2, b3, b4]:
            b.is_hovered = b.rect.collidepoint(self.mouse_pos)
            b.draw(surface)

        if self.mouse_clicked and not self.click_handled:
            if any(b.rect.collidepoint(self.mouse_pos) for b in [b1, b2, b3, b4]):
                AudioManager.play('click')

            if b1.rect.collidepoint(self.mouse_pos):
                self.state = "DIFFICULTY"
            elif b2.rect.collidepoint(self.mouse_pos):
                self.state = "SCORES"
            elif b3.rect.collidepoint(self.mouse_pos):
                self.state = "CREDITS"
            elif b4.rect.collidepoint(self.mouse_pos):
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            self.click_handled = True

    def _draw_difficulty(self, surface):
        self._draw_background(surface)
        draw_text_screen(surface, "Select Difficulty", self.title_font, self.width, self.height)
        cx, cy = self.width // 2, self.height // 2

        d1 = Button("Beginner (9x9, 10)", self.subtitle_font, cx, cy - 110, 50, min_width=380)
        d2 = Button("Intermediate (16x16, 40)", self.subtitle_font, cx, cy - 40, 50, min_width=380)
        d3 = Button("Expert (30x16, 99)", self.subtitle_font, cx, cy + 30, 50, min_width=380)
        d4 = Button("Custom", self.subtitle_font, cx, cy + 100, 50, min_width=380)
        back = Button("Back", self.subtitle_font, cx, cy + 190, 50, min_width=380, default_color=(60, 50, 75))

        for b in [d1, d2, d3, d4, back]:
            b.is_hovered = b.rect.collidepoint(self.mouse_pos)
            b.draw(surface)

        if self.mouse_clicked and not self.click_handled:
            if any(b.rect.collidepoint(self.mouse_pos) for b in [d1, d2, d3, d4, back]):
                AudioManager.play('click')

            if d1.rect.collidepoint(self.mouse_pos):
                self.cur_r, self.cur_c, self.cur_m, self.cur_hints = 9, 9, 10, 1
            elif d2.rect.collidepoint(self.mouse_pos):
                self.cur_r, self.cur_c, self.cur_m, self.cur_hints = 16, 16, 40, 3
            elif d3.rect.collidepoint(self.mouse_pos):
                self.cur_r, self.cur_c, self.cur_m, self.cur_hints = 16, 30, 99, 5
            elif d4.rect.collidepoint(self.mouse_pos):
                self.state = "CUSTOM_SETUP"
                self.click_handled = True
                return
            elif back.rect.collidepoint(self.mouse_pos):
                self.state = "MENU"
                self.click_handled = True
                return
            else:
                return

            self.game_board = create_board(self.cur_r, self.cur_c, self.cur_m, self.width, self.height, self.cur_hints)
            self.elapsed_time, self.state, self.click_handled = 0.0, "GAME", True

    def _draw_custom_setup(self, surface):
        self._draw_background(surface)
        draw_text_screen(surface, "Custom Setup", self.title_font, self.width, self.height)
        cx, cy = self.width // 2, self.height // 2

        btns = {
            "r-": Button("-", self.subtitle_font, cx - 120, cy - 100, 40, min_width=50),
            "r+": Button("+", self.subtitle_font, cx + 120, cy - 100, 40, min_width=50),
            "c-": Button("-", self.subtitle_font, cx - 120, cy - 40, 40, min_width=50),
            "c+": Button("+", self.subtitle_font, cx + 120, cy - 40, 40, min_width=50),
            "m-": Button("-", self.subtitle_font, cx - 120, cy + 20, 40, min_width=50),
            "m+": Button("+", self.subtitle_font, cx + 120, cy + 20, 40, min_width=50),
            "start": Button("Start", self.subtitle_font, cx, cy + 110, 50, min_width=300),
            "back": Button("Back", self.subtitle_font, cx, cy + 180, 50, min_width=300, default_color=(60, 50, 75))
        }

        for btn in btns.values():
            btn.is_hovered = btn.rect.collidepoint(self.mouse_pos)
            btn.draw(surface)

        surface.blit(self.subtitle_font.render(f"Rows: {self.cust_r}", True, WHITE), (cx - 50, cy - 90))
        surface.blit(self.subtitle_font.render(f"Cols: {self.cust_c}", True, WHITE), (cx - 50, cy - 30))
        surface.blit(self.subtitle_font.render(f"Mines: {self.cust_m}", True, WHITE), (cx - 55, cy + 30))

        if self.mouse_clicked and not self.click_handled:
            if any(b.rect.collidepoint(self.mouse_pos) for b in btns.values()):
                AudioManager.play('click')

            if btns["r-"].rect.collidepoint(self.mouse_pos):
                self.cust_r = max(5, self.cust_r - 1)
            elif btns["r+"].rect.collidepoint(self.mouse_pos):
                self.cust_r = min(30, self.cust_r + 1)
            elif btns["c-"].rect.collidepoint(self.mouse_pos):
                self.cust_c = max(5, self.cust_c - 1)
            elif btns["c+"].rect.collidepoint(self.mouse_pos):
                self.cust_c = min(50, self.cust_c + 1)
            elif btns["m-"].rect.collidepoint(self.mouse_pos):
                self.cust_m = max(1, self.cust_m - 1)
            elif btns["m+"].rect.collidepoint(self.mouse_pos):
                self.cust_m = min((self.cust_r * self.cust_c) - 1, self.cust_m + 1)
            elif btns["back"].rect.collidepoint(self.mouse_pos):
                self.state = "DIFFICULTY"
            elif btns["start"].rect.collidepoint(self.mouse_pos):
                self.cur_r, self.cur_c, self.cur_m = self.cust_r, self.cust_c, self.cust_m
                self.cur_hints = 3
                self.game_board = create_board(self.cur_r, self.cur_c, self.cur_m, self.width, self.height,
                                               self.cur_hints)
                self.elapsed_time, self.state = 0.0, "GAME"
            self.click_handled = True

    def _draw_scores(self, surface):
        self._draw_background(surface)
        draw_text_screen(surface, "High Scores", self.title_font, self.width, self.height)
        cx, cy = self.width // 2, self.height // 2

        f1 = Button("Beginner", self.tab_font, cx - 285, cy - 130, 40, min_width=170)
        f2 = Button("Intermediate", self.tab_font, cx - 95, cy - 130, 40, min_width=170)
        f3 = Button("Expert", self.tab_font, cx + 95, cy - 130, 40, min_width=170)
        f4 = Button("Custom", self.tab_font, cx + 285, cy - 130, 40, min_width=170)

        for b, name in zip([f1, f2, f3, f4], ["Beginner", "Intermediate", "Expert", "Custom"]):
            b.default_color = (169, 161, 217) if self.score_filter == name else (80, 70, 95)
            b.text_color = (20, 15, 25) if self.score_filter == name else WHITE
            b.is_hovered = b.rect.collidepoint(self.mouse_pos)
            b.draw(surface)
            if self.mouse_clicked and not self.click_handled and b.rect.collidepoint(self.mouse_pos):
                AudioManager.play('click')
                self.score_filter = name
                self.click_handled = True

        start_y = cy - 60
        scores = self.score_mgr.scores.get(self.score_filter, [])
        if not scores:
            txt = self.subtitle_font.render("No scores yet!", True, WHITE)
            surface.blit(txt, txt.get_rect(center=(cx, start_y + 50)))
        else:
            header = self.stat_font.render("Rank       Time (s)       3BV/s", True, (169, 161, 217))
            surface.blit(header, header.get_rect(center=(cx, start_y)))
            for i, sc in enumerate(scores):
                row = self.subtitle_font.render(f"{i + 1}.         {sc['time']:.3f}         {sc['bvs']:.4f}", True,
                                                WHITE)
                surface.blit(row, row.get_rect(center=(cx, start_y + 40 + (i * 35))))

        back = Button("Back", self.subtitle_font, cx, cy + 220, 50, min_width=300, default_color=(60, 50, 75))
        back.is_hovered = back.rect.collidepoint(self.mouse_pos)
        back.draw(surface)
        if self.mouse_clicked and not self.click_handled and back.rect.collidepoint(self.mouse_pos):
            AudioManager.play('click')
            self.state, self.click_handled = "MENU", True

    def _draw_credits(self, surface):
        self._draw_background(surface)
        draw_text_screen(surface, "Credits", self.title_font, self.width, self.height)
        cx, cy = self.width // 2, self.height // 2
        start_y, spacing = cy - 100, 100

        credits_info = [
            ("Developer", "Kyle Dungo"),
            ("Sprite Reference (OpenGameArt.org)", "FrostC"),
            ("Game Mechanics Inspired By", "Minesweeper Online")
        ]
        for i, (role, name) in enumerate(credits_info):
            role_surf = self.subtitle_font.render(role, True, (169, 161, 217))
            surface.blit(role_surf, role_surf.get_rect(center=(cx, start_y + (i * spacing))))
            name_surf = self.ui_font.render(name, True, WHITE)
            surface.blit(name_surf, name_surf.get_rect(center=(cx, start_y + (i * spacing) + 35)))

        back = Button("Back", self.subtitle_font, cx, cy + 220, 50, min_width=300, default_color=(60, 50, 75))
        back.is_hovered = back.rect.collidepoint(self.mouse_pos)
        back.draw(surface)

        if self.mouse_clicked and not self.click_handled and back.rect.collidepoint(self.mouse_pos):
            AudioManager.play('click')
            self.state, self.click_handled = "MENU", True

    def _draw_pause(self, surface):
        self.game_board.draw(surface)
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((20, 15, 25, 180))
        surface.blit(overlay, (0, 0))
        draw_text_screen(surface, "GAME PAUSED", self.title_font, self.width, self.height)

        cx, cy = self.width // 2, self.height // 2
        p1 = Button("Continue", self.subtitle_font, cx, cy - 50, 50, min_width=300)
        p3 = Button("Return to Title", self.subtitle_font, cx, cy + 30, 50, min_width=300, default_color=(60, 50, 75))

        for b in [p1, p3]:
            b.is_hovered = b.rect.collidepoint(self.mouse_pos)
            b.draw(surface)

        if self.mouse_clicked and not self.click_handled:
            if p1.rect.collidepoint(self.mouse_pos):
                AudioManager.play('click')
                self.state = "GAME"
            elif p3.rect.collidepoint(self.mouse_pos):
                AudioManager.play('click')
                self.state = "MENU"
            self.click_handled = True

    def _draw_game(self, surface):
        self.game_board.draw(surface)

        pygame.draw.rect(surface, (25, 20, 35), (0, 0, self.width, 80))
        pygame.draw.line(surface, (169, 161, 217), (0, 80), (self.width, 80), 4)

        surface.blit(self.ui_font.render(f"Time: {int(self.elapsed_time)}", True, WHITE), (30, 25))

        flags_left = self.game_board.mines - self.game_board.flags_placed
        counter_text = self.ui_font.render(f"Flags: {flags_left}", True, WHITE)
        surface.blit(counter_text, (self.width - 200, 25))

        self.hint_btn.image = AssetManager.get_tile_scaled('hint', 32)
        self.in_game_menu_btn.image = AssetManager.get_tile_scaled('menu', 32)

        if self.game_board.game_over:
            face_img = 'sad'
        elif self.is_mouse_down and self.valid_game_click and not self.face_btn.rect.collidepoint(self.mouse_pos):
            face_img = 'ooh'
        else:
            face_img = 'smile'

        self.face_btn.image = AssetManager.get_tile_scaled(face_img, 32)

        for b in [self.hint_btn, self.face_btn, self.in_game_menu_btn]:
            b.is_hovered = b.rect.collidepoint(self.mouse_pos)
            b.draw(surface)

        if self.game_board.hints_remaining > 0:
            hint_txt = self.small_font.render(str(self.game_board.hints_remaining), True, (255, 255, 100))
            surface.blit(hint_txt, (self.hint_btn.rect.right - 12, self.hint_btn.rect.bottom - 15))

        if self.mouse_clicked and not self.click_handled:
            if self.face_btn.rect.collidepoint(self.mouse_pos):
                AudioManager.play('click')
                self.game_board = create_board(self.cur_r, self.cur_c, self.cur_m, self.width, self.height,
                                               self.cur_hints)
                self.elapsed_time = 0.0
            elif self.in_game_menu_btn.rect.collidepoint(self.mouse_pos):
                AudioManager.play('click')
                self.state = "PAUSE"
            elif self.hint_btn.rect.collidepoint(self.mouse_pos):
                AudioManager.play('click')
                self.game_board.provide_hint()
            self.click_handled = True

        if self.game_board.is_won or self.game_board.game_over:
            if self.game_board.is_won and not getattr(self.game_board, 'score_saved', False):
                diff_str = "Custom"
                if self.cur_r == 9 and self.cur_c == 9 and self.cur_m == 10:
                    diff_str = "Beginner"
                elif self.cur_r == 16 and self.cur_c == 16 and self.cur_m == 40:
                    diff_str = "Intermediate"
                elif self.cur_r == 16 and self.cur_c == 30 and self.cur_m == 99:
                    diff_str = "Expert"

                bvs = (self.game_board.board_3bv / self.elapsed_time) if self.elapsed_time > 0 else 0
                self.score_mgr.add_score(diff_str, self.elapsed_time, bvs)
                self.game_board.score_saved = True

            board_right = self.game_board.grid[0][-1].rect.right
            panel_w, panel_h = 260, 160

            if self.width - board_right > panel_w + 40:
                panel_x, panel_y = board_right + 20, self.game_board.grid[0][0].rect.y
            else:
                panel_x, panel_y = (self.width - panel_w) // 2, (self.height - panel_h) // 2
                overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                surface.blit(overlay, (0, 0))

            bg_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
            pygame.draw.rect(surface, (35, 30, 45), bg_rect, border_radius=10)
            pygame.draw.rect(surface, (169, 161, 217), bg_rect, 3, border_radius=10)

            title_txt = "YOU WIN!" if self.game_board.is_won else "GAME OVER"
            title_col = (100, 255, 100) if self.game_board.is_won else (255, 100, 100)
            title_surf = self.ui_font.render(title_txt, True, title_col)
            surface.blit(title_surf, (panel_x + panel_w // 2 - title_surf.get_width() // 2, panel_y + 15))

            surface.blit(self.stat_font.render(f"Time: {self.elapsed_time:.3f} sec", True, (220, 220, 220)),
                         (panel_x + 20, panel_y + 60))
            surface.blit(self.stat_font.render(f"3BV: {self.game_board.board_3bv}", True, (220, 220, 220)),
                         (panel_x + 20, panel_y + 90))
            bvs_val = (self.game_board.board_3bv / self.elapsed_time) if self.elapsed_time > 0 else 0
            surface.blit(self.stat_font.render(f"3BV/s: {bvs_val:.4f}", True, (220, 220, 220)),
                         (panel_x + 20, panel_y + 120))
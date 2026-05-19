# main.py
import pygame
import sys
from settings import ROWS, COLS, CELL_SIZE
from src.board import Board


def draw_game_over(screen, width, height, title_font, subtitle_font):
    # Prepare text surfaces
    title = title_font.render("GAME OVER", True, (200, 0, 0))
    subtitle = subtitle_font.render("Press 'R' to Restart", True, (0, 0, 0))

    # Calculate centering math
    title_rect = title.get_rect(center=(width // 2, height // 2 - 20))
    subtitle_rect = subtitle.get_rect(center=(width // 2, height // 2 + 30))

    # Draw background box for readability
    bg_rect = pygame.Rect(0, 0, width, 100)
    bg_rect.center = (width // 2, height // 2 + 5)
    pygame.draw.rect(screen, (220, 220, 220), bg_rect)
    pygame.draw.rect(screen, (0, 0, 0), bg_rect, 3)

    # Blit text to screen
    screen.blit(title, title_rect)
    screen.blit(subtitle, subtitle_rect)


def main():
    # --- Initialization ---
    pygame.init()
    screen_width = COLS * CELL_SIZE
    screen_height = ROWS * CELL_SIZE
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Minesweeper")

    # --- Game Setup ---
    game_board = Board()
    game_board.debug_console_view()
    title_font = pygame.font.SysFont(None, 64)
    subtitle_font = pygame.font.SysFont(None, 32)
    clock = pygame.time.Clock()

    # --- Main Loop ---
    running = True
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if event.button == 1:  # Left Click
                    game_board.handle_click(x, y)
                elif event.button == 3:  # Right Click
                    game_board.toggle_flag(x, y)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Restart Key
                    game_board = Board()

        # 2. Drawing
        screen.fill((200, 200, 200))
        game_board.draw(screen)

        # Trigger UI overlay if a mine was hit
        if game_board.game_over:
            draw_game_over(screen, screen_width, screen_height, title_font, subtitle_font)

        # 3. Update Display
        pygame.display.flip()
        clock.tick(60)

    # --- Cleanup ---
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
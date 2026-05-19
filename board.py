# src/board.py
import random
import pygame
from src.cell import Cell
from settings import ROWS, COLS, MINES, CELL_SIZE


class Board:
    def __init__(self):
        self.grid = self.create_grid()
        self.place_mines()
        self.calculate_numbers()
        self.font = pygame.font.SysFont(None, 36)
        self.game_over = False

    # --- SETUP METHODS ---
    @staticmethod
    def create_grid():
        # Generates the 2D list of generic Cell objects
        return [[Cell(row, col) for col in range(COLS)] for row in range(ROWS)]

    def place_mines(self):
        # Randomly assigns mines to cells until the target count is reached
        mines_placed = 0
        while mines_placed < MINES:
            row = random.randint(0, ROWS - 1)
            col = random.randint(0, COLS - 1)
            cell = self.grid[row][col]

            if not cell.is_mine:
                cell.is_mine = True
                mines_placed += 1

    def calculate_numbers(self):
        # Counts neighboring mines for all non-mine cells
        for row in range(ROWS):
            for col in range(COLS):
                cell = self.grid[row][col]
                if cell.is_mine:
                    continue

                count = 0
                # Check the 3x3 grid around the current cell
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue

                        r, c = row + dr, col + dc
                        # Ensure we don't check outside the board boundaries
                        if 0 <= r < ROWS and 0 <= c < COLS:
                            if self.grid[r][c].is_mine:
                                count += 1
                cell.neighbor_mines = count

    def debug_console_view(self):
        # Prints a retro terminal representation of the hidden board layout
        print("\n--- MINESWEEPER TERMINAL DEBUG ---")
        for row in self.grid:
            row_display = []
            for cell in row:
                if cell.is_mine:
                    row_display.append("[ * ]")
                else:
                    row_display.append("[   ]")
            print("".join(row_display))
        print("----------------------------------\n")

    # --- GAME LOGIC ---
    def handle_click(self, x, y):
        if self.game_over:
            return

        # Convert pixels to grid coordinates
        col = x // CELL_SIZE
        row = y // CELL_SIZE
        self.reveal_cell(row, col)

    def toggle_flag(self, x, y):
        if self.game_over:
            return

        col = x // CELL_SIZE
        row = y // CELL_SIZE
        if 0 <= row < ROWS and 0 <= col < COLS:
            cell = self.grid[row][col]
            if not cell.is_revealed:
                cell.is_flagged = not cell.is_flagged

    def reveal_cell(self, row, col):
        # Stop checking if out of bounds, already revealed, or protected by a flag
        if not (0 <= row < ROWS and 0 <= col < COLS):
            return

        cell = self.grid[row][col]
        if cell.is_revealed or cell.is_flagged:
            return

        cell.is_revealed = True

        # Hitting a mine triggers the game over state
        if cell.is_mine:
            self.game_over = True
            self.reveal_all_mines()
            return

        # Flood Fill: Automatically open neighbors if this cell touches zero mines
        if cell.neighbor_mines == 0:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    self.reveal_cell(row + dr, col + dc)

    def reveal_all_mines(self):
        for row in self.grid:
            for cell in row:
                if cell.is_mine:
                    cell.is_revealed = True

    # --- DRAWING ---
    def draw(self, screen):
        for row in self.grid:
            for cell in row:
                x = cell.col * CELL_SIZE
                y = cell.row * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

                if cell.is_revealed:
                    pygame.draw.rect(screen, (220, 220, 220), rect)  # Revealed background

                    if cell.is_mine:
                        pygame.draw.rect(screen, (255, 0, 0), rect)  # Mine
                    elif cell.neighbor_mines > 0:
                        # Draw number text
                        text = self.font.render(str(cell.neighbor_mines), True, (0, 0, 0))
                        text_rect = text.get_rect(center=rect.center)
                        screen.blit(text, text_rect)
                else:
                    pygame.draw.rect(screen, (150, 150, 150), rect)  # Hidden background

                    if cell.is_flagged:
                        # Draw flag indicator
                        pygame.draw.circle(screen, (255, 50, 50), rect.center, CELL_SIZE // 4)

                        # Draw grid borders
                pygame.draw.rect(screen, (100, 100, 100), rect, 2)
import random
import pygame
from src.cell import Cell


class Board:
    def __init__(self, rows, cols, mines, cell_size):
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.cell_size = cell_size

        self.grid = self.create_grid()
        self.board_3bv = 0
        self.first_click = True

        self.game_over = False
        self.is_won = False

        self.font = pygame.font.SysFont(None, int(self.cell_size * 0.8))
        self.number_surfaces = {}
        colors = [(0, 0, 255), (0, 128, 0), (255, 0, 0), (0, 0, 128),
                  (128, 0, 0), (0, 128, 128), (0, 0, 0), (128, 128, 128)]

        for i in range(1, 9):
            self.number_surfaces[i] = self.font.render(str(i), True, colors[i - 1])

    @property
    def flags_placed(self):
        return sum(1 for row in self.grid for cell in row if cell.is_flagged)

    def create_grid(self):
        return [[Cell(row, col) for col in range(self.cols)] for row in range(self.rows)]

    def update_rects(self, offset_x, offset_y):
        for row in self.grid:
            for cell in row:
                x = (cell.col * self.cell_size) + offset_x
                y = (cell.row * self.cell_size) + offset_y
                cell.rect = pygame.Rect(x, y, self.cell_size, self.cell_size)

    def place_mines(self, safe_row, safe_col):
        mines_placed = 0
        safe_zone = [(r, c) for r in range(safe_row - 1, safe_row + 2)
                     for c in range(safe_col - 1, safe_col + 2)
                     if 0 <= r < self.rows and 0 <= c < self.cols]

        if (self.rows * self.cols) - len(safe_zone) < self.mines:
            safe_zone = [(safe_row, safe_col)]

        while mines_placed < self.mines:
            row, col = random.randint(0, self.rows - 1), random.randint(0, self.cols - 1)
            cell = self.grid[row][col]
            if not cell.is_mine and (row, col) not in safe_zone:
                cell.is_mine = True
                mines_placed += 1

        self.debug_print()

    def debug_print(self):
        """Prints the current mine layout to the terminal for debugging."""
        print("\n--- Mine Distribution (Debug) ---")
        for r in range(self.rows):
            row_str = ""
            for c in range(self.cols):
                if self.grid[r][c].is_mine:
                    row_str += "[X] "
                else:
                    row_str += "[ ] "
            print(row_str)
        print("---------------------------------\n")

    def calculate_numbers(self):
        for row in range(self.rows):
            for col in range(self.cols):
                cell = self.grid[row][col]
                if cell.is_mine:
                    continue

                count = sum(1 for dr in [-1, 0, 1] for dc in [-1, 0, 1]
                            if (dr != 0 or dc != 0) and
                            0 <= row + dr < self.rows and 0 <= col + dc < self.cols and
                            self.grid[row + dr][col + dc].is_mine)
                cell.neighbor_mines = count

    def calculate_3bv(self):
        visited = set()
        score_3bv = 0

        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                if not cell.is_mine and cell.neighbor_mines == 0 and (r, c) not in visited:
                    score_3bv += 1
                    queue = [(r, c)]
                    visited.add((r, c))
                    while queue:
                        curr_r, curr_c = queue.pop(0)
                        for dr in [-1, 0, 1]:
                            for dc in [-1, 0, 1]:
                                nr, nc = curr_r + dr, curr_c + dc
                                if 0 <= nr < self.rows and 0 <= nc < self.cols and (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    if self.grid[nr][nc].neighbor_mines == 0:
                                        queue.append((nr, nc))

        for r in range(self.rows):
            for c in range(self.cols):
                if not self.grid[r][c].is_mine and (r, c) not in visited:
                    score_3bv += 1

        return score_3bv

    def check_win(self):
        for row in self.grid:
            for cell in row:
                if not cell.is_mine and not cell.is_revealed:
                    return False
        self.is_won = True
        return True

    def handle_click(self, x, y):
        if self.game_over or self.is_won: return
        for row in self.grid:
            for cell in row:
                if cell.rect and cell.rect.collidepoint(x, y):
                    if cell.is_flagged: return

                    if self.first_click:
                        self.place_mines(cell.row, cell.col)
                        self.calculate_numbers()
                        self.board_3bv = self.calculate_3bv()
                        self.first_click = False

                    self.reveal_cell(cell.row, cell.col)
                    return

    def handle_chord(self, x, y):
        if self.game_over or self.is_won: return
        for row in self.grid:
            for cell in row:
                if cell.rect and cell.rect.collidepoint(x, y):
                    if cell.is_revealed and cell.neighbor_mines > 0:
                        flags_around = 0
                        neighbors = []
                        for dr in [-1, 0, 1]:
                            for dc in [-1, 0, 1]:
                                if dr == 0 and dc == 0: continue
                                r, c = cell.row + dr, cell.col + dc
                                if 0 <= r < self.rows and 0 <= c < self.cols:
                                    n_cell = self.grid[r][c]
                                    neighbors.append(n_cell)
                                    if n_cell.is_flagged:
                                        flags_around += 1

                        if flags_around == cell.neighbor_mines:
                            for n in neighbors:
                                if not n.is_revealed and not n.is_flagged:
                                    self.reveal_cell(n.row, n.col)
                    return

    def toggle_flag(self, x, y):
        if self.game_over or self.is_won: return
        for row in self.grid:
            for cell in row:
                if cell.rect and cell.rect.collidepoint(x, y):
                    if not cell.is_revealed:
                        if not cell.is_flagged and not cell.is_question:
                            cell.is_flagged = True
                        elif cell.is_flagged:
                            cell.is_flagged = False
                            cell.is_question = True
                        elif cell.is_question:
                            cell.is_question = False
                    return

    def reveal_cell(self, row, col):
        if not (0 <= row < self.rows and 0 <= col < self.cols): return

        cell = self.grid[row][col]
        if cell.is_revealed or cell.is_flagged: return

        cell.is_revealed = True

        if cell.is_mine:
            self.game_over = True
            self.reveal_all_mines()
            return

        if cell.neighbor_mines == 0:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    self.reveal_cell(row + dr, col + dc)

        self.check_win()

    def reveal_all_mines(self):
        for row in self.grid:
            for cell in row:
                if cell.is_mine:
                    cell.is_revealed = True

    def draw(self, screen):
        from src.app import AssetManager  # Import the manager locally

        for row in self.grid:
            for cell in row:
                if not cell.rect: continue

                if cell.is_revealed:
                    if cell.is_mine:
                        # Draw mine tile
                        screen.blit(AssetManager.get_tile_scaled('mine', self.cell_size), cell.rect)
                    elif cell.neighbor_mines > 0:
                        # Draw number tile
                        surf = AssetManager.get_tile_scaled(str(cell.neighbor_mines), self.cell_size)
                        screen.blit(surf, cell.rect)
                    else:
                        # Draw empty revealed tile
                        screen.blit(AssetManager.get_tile_scaled('empty', self.cell_size), cell.rect)
                else:
                    # Draw unrevealed tile
                    screen.blit(AssetManager.get_tile_scaled('unrevealed', self.cell_size), cell.rect)

                    if cell.is_flagged:
                        screen.blit(AssetManager.get_tile_scaled('flag', self.cell_size), cell.rect)
                    elif cell.is_question:
                        q_surf = self.font.render("?", True, (0, 0, 0))  # defined here
                        q_rect = q_surf.get_rect(center=cell.rect.center)  # ← must be inside elif
                        screen.blit(q_surf, q_rect)  # ← must be inside elif

                pygame.draw.rect(screen, (70, 70, 73), cell.rect, 1)
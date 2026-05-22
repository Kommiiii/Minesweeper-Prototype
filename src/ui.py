import pygame

class Button:
    def __init__(self, text, font, center_x, y, height, min_width=250,
                 default_color=(200, 200, 200), hover_color=(150, 150, 150), text_color=(0, 0, 0),
                 image=None): # <-- NEW: Accepts an image
        self.text = text
        self.font = font
        self.default_color = default_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.image = image  # <-- Store the image

        if text:
            text_w, _ = font.size(text)
            self.width = max(min_width, text_w + 40)
        else:
            self.width = min_width

        self.rect = pygame.Rect(center_x - self.width // 2, y, self.width, height)

    def draw(self, screen, mouse_pos):
        is_hovered = self.rect.collidepoint(mouse_pos)
        color = self.hover_color if is_hovered else self.default_color

        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)

        # --- NEW: Draw the image if it exists ---
        if self.image:
            img_rect = self.image.get_rect(center=self.rect.center)
            screen.blit(self.image, img_rect)
        elif self.text:
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            screen.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

def draw_text_screen(screen, title, font, width, height):
    title_surf = font.render(title, True, (255, 255, 255))
    rect = title_surf.get_rect(center=(width // 2, height // 8))
    screen.blit(title_surf, rect)
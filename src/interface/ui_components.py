import pygame


class Button:
    def __init__(self, text, font, center_x, y, height, min_width=250,
                 default_color=(80, 70, 95), hover_color=(130, 120, 150), text_color=(255, 255, 255),
                 image=None, action=None):
        self.text = text
        self.font = font
        self.default_color = default_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.image = image
        self.action = action
        self.is_hovered = False

        if text:
            text_w, _ = font.size(text)
            self.width = max(min_width, text_w + 40)
        else:
            self.width = min_width

        self.rect = pygame.Rect(center_x - self.width // 2, y, self.width, height)

        # Create a secondary rect for the drop shadow
        self.shadow_rect = self.rect.copy()
        self.shadow_rect.y += 4

    def handle_event(self, event, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.action:
                self.action()

    def draw(self, screen):
        # 1. Draw Drop Shadow
        pygame.draw.rect(screen, (20, 15, 25), self.shadow_rect, border_radius=8)

        # 2. Draw Main Button Body
        color = self.hover_color if self.is_hovered else self.default_color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)

        # 3. Draw a crisp inner highlight border
        border_col = (169, 161, 217) if self.is_hovered else (50, 40, 65)
        pygame.draw.rect(screen, border_col, self.rect, 2, border_radius=8)

        # 4. Render Contents
        if self.image:
            img_rect = self.image.get_rect(center=self.rect.center)
            screen.blit(self.image, img_rect)
        elif self.text:
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            screen.blit(text_surf, text_rect)


def draw_text_screen(screen, title, font, width, height):
    # Add a drop shadow to our main text headers too!
    shadow_surf = font.render(title, True, (20, 15, 25))
    shadow_rect = shadow_surf.get_rect(center=(width // 2, height // 8 + 4))
    screen.blit(shadow_surf, shadow_rect)

    title_surf = font.render(title, True, (255, 255, 255))
    rect = title_surf.get_rect(center=(width // 2, height // 8))
    screen.blit(title_surf, rect)
import pygame


class Engine:
    def __init__(self, config):
        self.config = config
        self.width = self.config.settings.get("width", 1080)
        self.height = self.config.settings.get("height", 720)

        # Create a fixed-size window (Removed the pygame.RESIZABLE flag)
        flags = pygame.FULLSCREEN if self.config.settings.get("fullscreen") else 0
        self.window = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption("Dungo's Minesweeper")

        from core.audio_manager import AudioManager
        AudioManager.init_audio()

        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0.0

    def run(self, state_machine):
        """Strict decoupling of loop components, now rendering directly to the window."""
        while self.running:
            self.dt = self.clock.tick(60) / 1000.0
            events = pygame.event.get()

            # Since the window size is fixed 1:1, we can pass raw mouse coordinates directly
            mouse_pos = pygame.mouse.get_pos()

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            # 1. Update Game State
            state_machine.update(self.dt, events, mouse_pos)

            # 2. Render directly to the OS window (using the deep purple background)
            self.window.fill((35, 30, 45))
            state_machine.render(self.window)

            # 3. Swap buffers
            pygame.display.flip()
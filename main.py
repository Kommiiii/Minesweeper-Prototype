import pygame
import sys
from src.app import MinesweeperApp

def main():

    pygame.init()
    app = MinesweeperApp()
    app.run()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
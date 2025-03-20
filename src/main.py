#!/usr/bin/env python3

import os
import sys
import pygame
from game import Game

def main():
    # Initialize pygame
    pygame.init()
    pygame.mixer.init()
    
    # Create game instance and run
    game = Game()
    game.run()
    
    # Clean exit
    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    # Ensure we're running from the right directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()

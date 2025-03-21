#!/usr/bin/env python3
"""
Direct runner script for the enemy bounds test with a custom sprite sheet.
This completely bypasses unittest's command-line parsing.

Usage:
    python tests/run_bounds_test.py path/to/spritesheet.png
"""

import os
import sys
import pygame

# Set up the path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Import the test environment setup
from tests.helpers import setup_test_environment
setup_test_environment()

# Import the Enemy class
try:
    from src.sprites.enemy import Enemy, EnemyType, Direction
except ImportError:
    # If that fails, try a direct relative import
    from sprites.enemy import Enemy, EnemyType, Direction

def run_test(sprite_sheet_path):
    """Run bounds test with the given sprite sheet."""
    print(f"Running enemy bounds test with sprite sheet: {sprite_sheet_path}")
    
    # Initialize pygame
    pygame.init()
    
    # Create a display surface for testing
    screen = pygame.Surface((800, 600))
    
    # Create a test display to avoid "No video mode has been set" error
    pygame.display.set_mode((100, 100))
    
    # Cell size (standard for testing)
    cell_size = 32
    
    # Create an enemy instance for testing
    enemy = Enemy(5, 5, EnemyType.BASIC, cell_size)
    
    try:
        # Load the sprite sheet
        if os.path.exists(sprite_sheet_path):
            try:
                sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
                print(f"Successfully loaded sprite sheet: {sprite_sheet_path}")
                sheet_width, sheet_height = sprite_sheet.get_size()
                print(f"Sprite sheet dimensions: {sheet_width}x{sheet_height}")
            except pygame.error as e:
                print(f"Failed to load sprite sheet: {e}")
                pygame.quit()
                return False
        else:
            print(f"Sprite sheet not found: {sprite_sheet_path}")
            pygame.quit()
            return False
            
        # Let's extract some frames and check their bounds
        frame_width = sheet_width // 4
        frame_height = sheet_height // 4
        
        print("\nTesting frame bounds:")
        print("=====================")
        
        directions = ["NORTH", "EAST", "SOUTH", "WEST"]
        
        # Test a few frames from each direction
        for row in range(4):
            direction = directions[row]
            for col in range(4):
                # Extract frame
                frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                frame.blit(sprite_sheet, (0, 0), 
                         (col * frame_width, row * frame_height, frame_width, frame_height))
                
                # Calculate bounds
                bounds = enemy._calculate_tight_bounds(frame)
                
                # Print bounds
                print(f"{direction}_{col} bounds: ({bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]})")
                
                # Calculate dimensions
                width = bounds[2] - bounds[0]
                height = bounds[3] - bounds[1]
                print(f"{direction}_{col} size: {width}x{height}")
        
        print("\nTest completed successfully!")
        
    finally:
        # Clean up
        pygame.quit()
    
    return True

if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) != 2:
        print("Usage: python tests/run_bounds_test.py path/to/spritesheet.png")
        sys.exit(1)
        
    sprite_sheet_path = sys.argv[1]
    
    if run_test(sprite_sheet_path):
        print("Test completed successfully.")
    else:
        print("Test failed.")
        sys.exit(1)
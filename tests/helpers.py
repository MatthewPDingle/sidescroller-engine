"""Test helpers for the sidescroller engine tests."""
import os
import sys
import pygame

def setup_test_environment():
    """
    Set up the test environment:
    1. Add the project root to Python's sys.path
    2. Initialize pygame
    """
    # Get the absolute path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Add it to sys.path if it's not already there
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Also explicitly add src to the path
    src_path = os.path.join(project_root, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # Initialize pygame display (required for some pygame operations)
    os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Use dummy video driver
    pygame.display.init()
    pygame.display.set_mode((100, 100))
    
    # Initialize pygame if it's not already initialized
    if not pygame.get_init():
        pygame.init()
    
    return True
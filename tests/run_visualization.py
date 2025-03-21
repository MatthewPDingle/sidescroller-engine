#!/usr/bin/env python3
"""
Direct runner script for enemy bounds visualization with a custom sprite sheet.
This completely bypasses unittest's command-line parsing.

Usage:
    python tests/run_visualization.py path/to/spritesheet.png
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

def run_visualization(sprite_sheet_path):
    """Generate visualizations of sprite frames with their bounding boxes."""
    print(f"Running bounds visualization with sprite sheet: {sprite_sheet_path}")
    
    # Initialize pygame
    pygame.init()
    
    try:
        # Create a display surface for testing
        screen = pygame.Surface((800, 600))
        
        # Create a test display to avoid "No video mode has been set" error
        pygame.display.set_mode((100, 100))
        
        # Cell size (standard for testing)
        cell_size = 32
        
        # Create an enemy instance for testing
        enemy = Enemy(5, 5, EnemyType.BASIC, cell_size)
        
        # Output directory for visualizations
        output_dir = os.path.join(project_root, 'tests', 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Load the sprite sheet
        if os.path.exists(sprite_sheet_path):
            try:
                sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
                print(f"Successfully loaded sprite sheet: {sprite_sheet_path}")
            except pygame.error as e:
                print(f"Failed to load sprite sheet: {e}")
                return False
        else:
            print(f"Sprite sheet not found: {sprite_sheet_path}")
            return False
        
        # Create visualization of the entire sprite sheet with grid lines
        sheet_width, sheet_height = sprite_sheet.get_size()
        frame_width = sheet_width // 4
        frame_height = sheet_height // 4
        
        print(f"Sprite sheet dimensions: {sheet_width}x{sheet_height}")
        print(f"Frame dimensions: {frame_width}x{frame_height}")
        
        # Create a new surface with an extra 20px on each side for labels
        visualization = pygame.Surface((sheet_width + 40, sheet_height + 40), pygame.SRCALPHA)
        visualization.fill((50, 50, 50, 255))  # Dark gray background
        
        # Draw sprite sheet with grid
        visualization.blit(sprite_sheet, (20, 20))
        
        # Draw grid lines
        for i in range(5):
            # Vertical grid lines
            pygame.draw.line(visualization, (255, 255, 255, 255), 
                          (20 + i * frame_width, 20), 
                          (20 + i * frame_width, 20 + sheet_height), 2)
            # Horizontal grid lines
            pygame.draw.line(visualization, (255, 255, 255, 255), 
                          (20, 20 + i * frame_height), 
                          (20 + sheet_width, 20 + i * frame_height), 2)
        
        # Save sheet visualization
        sheet_viz_path = os.path.join(output_dir, 'sprite_sheet_grid.png')
        pygame.image.save(visualization, sheet_viz_path)
        print(f"Saved sprite sheet visualization to {sheet_viz_path}")
        
        # Now create individual frame visualizations with bounding boxes
        directions = ["NORTH", "EAST", "SOUTH", "WEST"]
        
        # Create a 4x4 grid of frame visualizations
        frames_viz = pygame.Surface((frame_width * 4 + 8, frame_height * 4 + 8), pygame.SRCALPHA)
        frames_viz.fill((50, 50, 50, 255))  # Dark gray background
        
        for row in range(4):
            for col in range(4):
                # Extract frame
                frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                frame.blit(sprite_sheet, (0, 0), 
                         (col * frame_width, row * frame_height, frame_width, frame_height))
                
                # Calculate bounds
                bounds = enemy._calculate_tight_bounds(frame)
                
                # Create a visualization of this frame with bounding box
                frame_viz = pygame.Surface((frame_width + 2, frame_height + 2), pygame.SRCALPHA)
                frame_viz.fill((20, 20, 20, 255))  # Darker background
                
                # Draw frame
                frame_viz.blit(frame, (1, 1))
                
                # Draw bounding box (orange)
                pygame.draw.rect(frame_viz, (255, 165, 0, 255), 
                              (1 + bounds[0], 1 + bounds[1], 
                               bounds[2] - bounds[0], bounds[3] - bounds[1]), 
                              1)  # 1px width for the outline
                
                # Add to grid
                frames_viz.blit(frame_viz, (2 + col * frame_width, 2 + row * frame_height))
                
                # Add frame info text below - save to a separate image instead
                dir_name = directions[row]
                frame_info = f"{dir_name}_{col} bounds: ({bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]})"
                print(frame_info)
                
                # Save individual frame with bounds
                individual_frame_path = os.path.join(output_dir, f'frame_{dir_name}_{col}.png')
                pygame.image.save(frame_viz, individual_frame_path)
        
        # Save visualizations of all frames with bounds
        frames_viz_path = os.path.join(output_dir, 'frames_with_bounds.png')
        pygame.image.save(frames_viz, frames_viz_path)
        print(f"Saved frames visualization to {frames_viz_path}")
        
        # Create a comparison visualization showing all frames with different colors for direction
        # and with bounding boxes
        comparison = pygame.Surface((frame_width * 4 + 20, frame_height * 4 + 20), pygame.SRCALPHA)
        comparison.fill((50, 50, 50, 255))  # Dark gray background
        
        # Direction colors
        direction_colors = [
            (0, 255, 0, 128),    # NORTH: Green
            (255, 0, 0, 128),    # EAST: Red
            (0, 0, 255, 128),    # SOUTH: Blue
            (255, 255, 0, 128)   # WEST: Yellow
        ]
        
        for row in range(4):
            direction = row
            for col in range(4):
                # Extract frame
                frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                frame.blit(sprite_sheet, (0, 0), 
                         (col * frame_width, row * frame_height, frame_width, frame_height))
                
                # Calculate bounds
                bounds = enemy._calculate_tight_bounds(frame)
                
                # Create a visualization with colored overlay for direction
                frame_viz = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                frame_viz.blit(frame, (0, 0))
                
                # Create semi-transparent overlay for direction
                overlay = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                overlay.fill(direction_colors[direction])
                frame_viz.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                # Draw bounding box (orange)
                pygame.draw.rect(frame_viz, (255, 165, 0, 255), 
                              (bounds[0], bounds[1], 
                               bounds[2] - bounds[0], bounds[3] - bounds[1]), 
                              1)  # 1px width for the outline
                
                # Add frame number text
                font = pygame.font.SysFont(None, 24)
                text = font.render(f"{col}", True, (255, 255, 255))
                frame_viz.blit(text, (5, 5))
                
                # Add to grid
                comparison.blit(frame_viz, (10 + col * frame_width, 10 + row * frame_height))
        
        # Save comparison visualization
        comparison_path = os.path.join(output_dir, 'direction_comparison.png')
        pygame.image.save(comparison, comparison_path)
        print(f"Saved direction comparison to {comparison_path}")
        
        # Include a legend
        legend = pygame.Surface((300, 150), pygame.SRCALPHA)
        legend.fill((50, 50, 50, 255))
        
        font = pygame.font.SysFont(None, 24)
        legend.blit(font.render("Legend:", True, (255, 255, 255)), (10, 10))
        
        y_pos = 40
        for i, dir_name in enumerate(directions):
            pygame.draw.rect(legend, direction_colors[i], (10, y_pos, 20, 20))
            legend.blit(font.render(dir_name, True, (255, 255, 255)), (40, y_pos))
            y_pos += 30
        
        # Draw orange box for bounds
        pygame.draw.rect(legend, (255, 165, 0, 255), (10, y_pos, 20, 20), 1)
        legend.blit(font.render("Bounding Box", True, (255, 255, 255)), (40, y_pos))
        
        # Save legend
        legend_path = os.path.join(output_dir, 'legend.png')
        pygame.image.save(legend, legend_path)
        print(f"Saved legend to {legend_path}")
        
        print(f"\nVisualization completed successfully!")
        print(f"Output files saved to: {output_dir}")
        
        return True
        
    except Exception as e:
        print(f"Error in visualization: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        pygame.quit()

if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) != 2:
        print("Usage: python tests/run_visualization.py path/to/spritesheet.png")
        sys.exit(1)
        
    sprite_sheet_path = sys.argv[1]
    
    if run_visualization(sprite_sheet_path):
        print("Visualization completed successfully.")
    else:
        print("Visualization failed.")
        sys.exit(1)
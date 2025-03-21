import os
import sys
import unittest
import pygame
from enum import Enum, auto

# Set up the path before importing anything else
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import and set up the test environment
from tests.helpers import setup_test_environment
setup_test_environment()

# Import from the src package using try/except to handle different import contexts
try:
    from src.sprites.enemy import Enemy, EnemyType, Direction
except ImportError:
    # If that fails, try a direct relative import
    from sprites.enemy import Enemy, EnemyType, Direction

class TestEnemyBoundsVisualization(unittest.TestCase):
    def setUp(self):
        """Initialize test environment with default sprite sheet."""
        # Initialize pygame
        pygame.init()
        
        # Create a display surface for testing (required for pygame)
        self.screen = pygame.Surface((800, 600))
        
        # Cell size (standard for testing)
        self.cell_size = 32
        
        # Create an enemy instance for testing
        self.enemy = Enemy(5, 5, EnemyType.BASIC, self.cell_size)
        
        # Create a test display to avoid "No video mode has been set" error
        pygame.display.set_mode((100, 100))
        
        # Output directory for visualizations
        self.output_dir = os.path.join(project_root, 'tests', 'output')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Default sprite sheet path (will be updated by test_with_sprite_sheet)
        self.sprite_sheet_path = None
    
    def test_visualize_sprite_bounds(self):
        """Generate visualizations of sprite frames with their bounding boxes"""
        # Get the actual sprite sheet from the enemy
        sprite_sheet = None
        
        # If a custom path was provided via test_with_sprite_sheet, use it
        if self.sprite_sheet_path and os.path.exists(self.sprite_sheet_path):
            sprite_sheet_path = self.sprite_sheet_path
        else:
            # Use default sprite sheet path
            sprite_sheet_path = os.path.join(project_root, 'resources', 'graphics', 'armadillo_warrior_ss.png')
        
        try:
            sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
            print(f"Loaded sprite sheet: {sprite_sheet_path}")
        except (pygame.error, FileNotFoundError):
            print(f"Could not load sprite sheet from {sprite_sheet_path}, creating a test version")
            
            # Create a test sprite sheet
            sheet_width = 256  # 64px * 4 columns
            sheet_height = 256  # 64px * 4 rows
            
            # Create a surface for our test sprite sheet
            sprite_sheet = pygame.Surface((sheet_width, sheet_height), pygame.SRCALPHA)
            
            # Create 16 distinct frames with non-transparent pixels
            frame_width = sheet_width // 4
            frame_height = sheet_height // 4
            
            for row in range(4):
                for col in range(4):
                    # Calculate frame position
                    x = col * frame_width
                    y = row * frame_height
                    
                    # Create a frame with all transparent pixels
                    frame_surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                    frame_surface.fill((0, 0, 0, 0))  # Fully transparent
                    
                    # Draw different shapes based on direction
                    if row == 1:  # EAST direction
                        # Draw a wide rectangle for east-facing frames
                        rect_width = frame_width * 0.8  # 80% of width
                        rect_x = frame_width * 0.15
                        pygame.draw.rect(frame_surface, (255, 0, 0, 255), 
                                       (rect_x, frame_height * 0.1, rect_width, frame_height * 0.8))
                    elif row == 3:  # WEST direction
                        # Draw a narrower rectangle for west-facing frames
                        rect_width = frame_width * 0.6  # 60% of width - DIFFERENT width than EAST
                        rect_x = frame_width * 0.2
                        pygame.draw.rect(frame_surface, (0, 0, 255, 255), 
                                       (rect_x, frame_height * 0.1, rect_width, frame_height * 0.8))
                    else:
                        # Other directions (row 0 and 2)
                        # Draw a circle with a different radius for each direction
                        radius = frame_width // 3 if row == 0 else frame_width // 5
                        pygame.draw.circle(frame_surface, (0, 255, 0, 255), 
                                         (frame_width // 2, frame_height // 2), 
                                         radius)
                    
                    # For each column, slightly vary the width/position to make frames different
                    if col > 0:
                        # Add an additional marker that changes with each frame
                        marker_x = 10 + (col * 5)
                        marker_y = 10 + (col * 5)
                        pygame.draw.rect(frame_surface, (255, 255, 0, 255),
                                       (marker_x, marker_y, 10, 10))
                    
                    # Blit the frame to the sprite sheet
                    sprite_sheet.blit(frame_surface, (x, y))

        # Create visualization of the entire sprite sheet with grid lines
        sheet_width, sheet_height = sprite_sheet.get_size()
        frame_width = sheet_width // 4
        frame_height = sheet_height // 4
        
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
        sheet_viz_path = os.path.join(self.output_dir, 'sprite_sheet_grid.png')
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
                bounds = self.enemy._calculate_tight_bounds(frame)
                
                # Create a visualization of this frame with bounding box
                frame_viz = pygame.Surface((frame_width + 2, frame_height + 2), pygame.SRCALPHA)
                frame_viz.fill((20, 20, 20, 255))  # Darker background
                
                # Draw frame
                frame_viz.blit(frame, (1, 1))
                
                # Draw bounding box (orange)
                pygame.draw.rect(frame_viz, (255, 165, 0, 255), 
                              (1 + bounds[0], 1 + bounds[1], 
                               bounds[2] - bounds[0], bounds[3] - bounds[1]), 
                              2)  # 2px width for the outline
                
                # Add to grid
                frames_viz.blit(frame_viz, (2 + col * frame_width, 2 + row * frame_height))
                
                # Add frame info text below - save to a separate image instead
                dir_name = directions[row]
                frame_info = f"{dir_name}_{col} bounds: ({bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]})"
                print(frame_info)
                
                # Save individual frame with bounds
                individual_frame_path = os.path.join(self.output_dir, f'frame_{dir_name}_{col}.png')
                pygame.image.save(frame_viz, individual_frame_path)
        
        # Save visualizations of all frames with bounds
        frames_viz_path = os.path.join(self.output_dir, 'frames_with_bounds.png')
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
                bounds = self.enemy._calculate_tight_bounds(frame)
                
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
        comparison_path = os.path.join(self.output_dir, 'direction_comparison.png')
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
        pygame.draw.rect(legend, (255, 165, 0, 255), (10, y_pos, 20, 20), 2)
        legend.blit(font.render("Bounding Box", True, (255, 255, 255)), (40, y_pos))
        
        # Save legend
        legend_path = os.path.join(self.output_dir, 'legend.png')
        pygame.image.save(legend, legend_path)
        print(f"Saved legend to {legend_path}")
    
    def tearDown(self):
        pygame.quit()

# Create a separate function to run the test with a custom sprite sheet
def test_with_sprite_sheet(sprite_sheet_path):
    """Run the test with a specific sprite sheet."""
    # Create the test case
    test = TestEnemyBoundsVisualization('test_visualize_sprite_bounds')
    
    # Set up the test with the custom path
    test.setUp()
    test.sprite_sheet_path = sprite_sheet_path
    
    # Run the test method
    test.test_visualize_sprite_bounds()
    
    # Clean up
    test.tearDown()
    
    print(f"Testing completed with sprite sheet: {sprite_sheet_path}")
    print(f"Output files saved to: {os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), 'tests', 'output')}")

# Run tests when executed directly
if __name__ == '__main__':
    import sys
    
    # If a sprite sheet path is provided, run with it
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        test_with_sprite_sheet(sys.argv[1])
    else:
        unittest.main()
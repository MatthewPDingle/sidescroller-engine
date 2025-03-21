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

class TestEnemyBounds(unittest.TestCase):
    def setUp(self, sprite_sheet_path=None):
        """
        Initialize test environment with optional custom sprite sheet.
        
        Args:
            sprite_sheet_path: Optional path to a sprite sheet. If None, creates a test sprite sheet.
        """
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
        
        # If sprite_sheet_path is provided, try to load it
        if sprite_sheet_path and os.path.exists(sprite_sheet_path):
            try:
                self.sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
                print(f"Loaded sprite sheet from: {sprite_sheet_path}")
            except pygame.error as e:
                print(f"Failed to load sprite sheet from {sprite_sheet_path}: {e}")
                # Fall back to creating a test sprite sheet
                self._create_test_sprite_sheet()
        else:
            # Create a test sprite sheet
            self._create_test_sprite_sheet()
    
    def _create_test_sprite_sheet(self):
        """Create a synthetic test sprite sheet with predictable patterns"""
        # Standard enemy sprite sheet is 4x4 grid
        sheet_width = 256  # 64px * 4 columns
        sheet_height = 256  # 64px * 4 rows
        
        # Create a surface for our test sprite sheet
        self.sprite_sheet = pygame.Surface((sheet_width, sheet_height), pygame.SRCALPHA)
        
        # Create 16 distinct frames with non-transparent pixels in different positions
        # This will simulate different enemy poses with different bounding boxes
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
                
                # Draw different shapes based on direction to mimic direction-specific bounds
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
                self.sprite_sheet.blit(frame_surface, (x, y))
        
        print("Created test sprite sheet successfully")

    def test_frame_bounds_calculation(self):
        """Test that tight bounds are calculated correctly for all frames"""
        # Since we created our own test sprite sheet, we'll use it directly
        # instead of relying on the pre-calculated enemy.frame_bounds
        
        frame_width = 64  # Same as in our test sprite sheet setup
        frame_height = 64
        
        # Test bounds for east and west directions specifically
        directions = [Direction.EAST, Direction.WEST]
        
        for direction in directions:
            for frame_idx in range(4):  # Test all 4 frames in each direction
                # Extract the frame from our test sprite sheet
                frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                row = direction.value
                col = frame_idx
                frame.blit(self.sprite_sheet, (0, 0), (
                    col * frame_width, 
                    row * frame_height, 
                    frame_width, 
                    frame_height
                ))
                
                # Calculate bounds directly using the enemy's method
                bounds = self.enemy._calculate_tight_bounds(frame)
                
                # Verify basic properties of the bounds
                self.assertIsNotNone(bounds, f"Bounds should not be None for direction {direction.name}, frame {frame_idx}")
                self.assertEqual(len(bounds), 4, f"Bounds should be a 4-tuple for direction {direction.name}, frame {frame_idx}")
                
                # Bounds should be within frame dimensions
                self.assertGreaterEqual(bounds[0], 0, "Min X should be >= 0")
                self.assertGreaterEqual(bounds[1], 0, "Min Y should be >= 0")
                self.assertLessEqual(bounds[2], frame_width, f"Max X should be <= {frame_width}")
                self.assertLessEqual(bounds[3], frame_height, f"Max Y should be <= {frame_height}")
                
                # Bounds should be valid (max > min)
                self.assertLess(bounds[0], bounds[2], "Min X should be < Max X")
                self.assertLess(bounds[1], bounds[3], "Min Y should be < Max Y")
                
                # For our test sprite sheet, check that bounds are valid
                # These are just basic sanity checks for any reasonable bounds
                if direction == Direction.EAST:  # Row 1
                    # East-facing frames - make sure they're within reasonable bounds
                    self.assertGreaterEqual(bounds[0], 0, 
                                          f"East-facing frame should have min_x >= 0, got {bounds[0]}")
                    self.assertLess(bounds[0], bounds[2], 
                                   f"East-facing frame bounds should have min_x < max_x")
                elif direction == Direction.WEST:  # Row 3
                    # West-facing frames - make sure they're within reasonable bounds
                    self.assertLessEqual(bounds[2], frame_width, 
                                       f"West-facing frame should have max_x <= {frame_width}, got {bounds[2]}")
                    self.assertLess(bounds[0], bounds[2], 
                                   f"West-facing frame bounds should have min_x < max_x")
                
                # Print bounds for debugging
                print(f"Direction: {direction.name}, Frame: {frame_idx}, Bounds: {bounds}")
                
    def test_bounds_difference_between_directions(self):
        """Test that east and west facing frames have different bounds"""
        # Since we're using our custom sprite sheet, we calculate bounds directly
        frame_width = 64
        frame_height = 64
        
        for frame_idx in range(4):
            # Get east-facing frame and calculate bounds
            east_frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            east_frame.blit(self.sprite_sheet, (0, 0), (
                frame_idx * frame_width, 
                Direction.EAST.value * frame_height, 
                frame_width, 
                frame_height
            ))
            east_bounds = self.enemy._calculate_tight_bounds(east_frame)
            
            # Get west-facing frame and calculate bounds
            west_frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            west_frame.blit(self.sprite_sheet, (0, 0), (
                frame_idx * frame_width, 
                Direction.WEST.value * frame_height, 
                frame_width, 
                frame_height
            ))
            west_bounds = self.enemy._calculate_tight_bounds(west_frame)
            
            # Verify the bounds are different (horizontally flipped character)
            # In our test sprite sheet, east and west frames have different shapes
            self.assertNotEqual(east_bounds[0], west_bounds[0], 
                              f"Frame {frame_idx} min_x should differ between EAST and WEST directions")
            
            # Print the difference for debugging
            east_width = east_bounds[2] - east_bounds[0]
            west_width = west_bounds[2] - west_bounds[0]
            print(f"Frame {frame_idx} - East bounds: {east_bounds}, West bounds: {west_bounds}")
            print(f"Frame {frame_idx} - East width: {east_width}, West width: {west_width}")
    
    def test_frame_bounds_consistency(self):
        """Test that bounds calculation is consistent for the same frame"""
        frame_width = 64
        frame_height = 64
        
        for direction in [Direction.EAST, Direction.WEST]:
            for frame_idx in range(4):
                # Create a simple test frame with a predictable shape
                frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                frame.fill((0, 0, 0, 0))  # Fully transparent
                
                # Draw a simple shape that will have consistent bounds
                if direction == Direction.EAST:
                    pygame.draw.rect(frame, (255, 0, 0, 255), (20, 10, 30, 40))
                else:  # WEST
                    pygame.draw.rect(frame, (0, 0, 255, 255), (10, 15, 30, 35))
                
                # Calculate bounds twice on the same frame
                bounds1 = self.enemy._calculate_tight_bounds(frame)
                bounds2 = self.enemy._calculate_tight_bounds(frame)
                
                # They should be exactly the same
                self.assertEqual(bounds1, bounds2, 
                              f"Bounds calculation should be consistent for {direction.name}, frame {frame_idx}")
                
                # Basic sanity check on bounds values
                if direction == Direction.EAST:
                    # Should be approximately the rectangle we drew (minus buffer)
                    self.assertGreaterEqual(bounds1[0], 18)  # x min (20-buffer)
                    self.assertLessEqual(bounds1[2], 52)     # x max (50+buffer)
                else:  # WEST
                    # Should be approximately the rectangle we drew (minus buffer)
                    self.assertGreaterEqual(bounds1[0], 8)   # x min (10-buffer)
                    self.assertLessEqual(bounds1[2], 42)     # x max (40+buffer)
                    
                print(f"Consistent bounds for {direction.name}, frame {frame_idx}: {bounds1}")

    def test_collision_rect_updates_with_frame(self):
        """Test that the collision rect is properly updated when the frame changes"""
        # Use our custom test sprite sheet with different size shapes for EAST vs WEST frames
        frame_width = 64
        frame_height = 64
        
        # Create mock frames and bounds based on our test sprite sheet
        all_frames = {}
        all_bounds = {}
        
        # We'll artificially create bounds with different widths for each direction
        # to ensure the test can verify that rect dimensions change
        
        # For each direction, extract frames and create bounds
        directions = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        for direction in directions:
            direction_frames = []
            direction_bounds = []
            
            for frame_idx in range(4):
                # Extract frame from our test sprite sheet
                frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                frame.blit(self.sprite_sheet, (0, 0), (
                    frame_idx * frame_width, 
                    direction.value * frame_height, 
                    frame_width, 
                    frame_height
                ))
                
                # Create different bounds for each direction to ensure they're distinct
                if direction == Direction.EAST:
                    bounds = (10, 5, 58, 59)  # 48x54 size
                elif direction == Direction.WEST:
                    bounds = (15, 10, 45, 58)  # 30x48 size - DIFFERENT from EAST
                elif direction == Direction.NORTH:
                    bounds = (20, 20, 50, 50)  # 30x30 size
                else:  # SOUTH
                    bounds = (5, 15, 40, 55)   # 35x40 size
                
                # Add an offset based on frame_idx to make each frame's bounds different
                frame_offset = frame_idx * 2
                adjusted_bounds = (
                    bounds[0] + frame_offset,
                    bounds[1],
                    bounds[2] - frame_offset,
                    bounds[3]
                )
                
                direction_frames.append(frame)
                direction_bounds.append(adjusted_bounds)
                
                print(f"Created bounds for {direction.name} frame {frame_idx}: {adjusted_bounds}")
            
            all_frames[direction.value] = direction_frames
            all_bounds[direction.value] = direction_bounds
        
        # Replace the enemy's frames and bounds with our test versions
        self.enemy.frames = all_frames
        self.enemy.frame_bounds = all_bounds
        
        # Force rect to a known size to start with
        self.enemy.rect = pygame.Rect(0, 0, 20, 30)
        initial_rect = self.enemy.rect.copy()
        
        # Set initial direction and frame
        self.enemy.direction = Direction.EAST
        self.enemy.current_frame = 0
        
        # Now update collision bounds for the initial frame
        print("Before update - rect:", self.enemy.rect)
        self.enemy.update_collision_bounds_for_frame()
        print("After update - rect:", self.enemy.rect)
        
        # The rect dimensions should have changed to match East direction frame 0
        east_bounds = all_bounds[Direction.EAST.value][0]
        expected_width = east_bounds[2] - east_bounds[0]
        expected_height = east_bounds[3] - east_bounds[1]
        
        print(f"Initial rect: {initial_rect}")
        print(f"Updated rect: {self.enemy.rect}")
        print(f"Expected width: {expected_width}, Actual width: {self.enemy.rect.width}")
        
        # The rect should have changed after updating to EAST direction
        self.assertEqual(self.enemy.rect.width, expected_width,
                       "Collision rect width should be updated to match EAST frame bounds")
        
        # Test that the rect updates when changing direction
        self.enemy.direction = Direction.WEST
        east_rect = self.enemy.rect.copy()
        self.enemy.update_collision_bounds_for_frame()
        
        # The dimensions should now match West direction frame 0
        west_bounds = all_bounds[Direction.WEST.value][0]
        expected_west_width = west_bounds[2] - west_bounds[0]
        
        print(f"East rect: {east_rect}, West rect: {self.enemy.rect}")
        print(f"Expected west width: {expected_west_width}, Actual: {self.enemy.rect.width}")
        
        # The rect should have changed after updating to WEST direction
        self.assertEqual(self.enemy.rect.width, expected_west_width,
                       "Collision rect width should be updated to match WEST frame bounds")
                       
        # The EAST and WEST widths should be different (we've designed the test this way)
        self.assertNotEqual(expected_width, expected_west_width,
                         "EAST and WEST bounds should have different widths in this test")
    
    def tearDown(self):
        pygame.quit()

def run_tests(sprite_sheet_path=None):
    """Run the enemy bounds tests with an optional custom sprite sheet."""
    # Create a test suite that allows passing the sprite_sheet_path to setUp
    suite = unittest.TestSuite()
    
    # Add each test method to the suite with custom initialization
    test_cases = [
        'test_frame_bounds_calculation',
        'test_bounds_difference_between_directions',
        'test_frame_bounds_consistency',
        'test_collision_rect_updates_with_frame'
    ]
    
    for test_case in test_cases:
        test = TestEnemyBounds(test_case)
        if sprite_sheet_path:
            test.setUp(sprite_sheet_path)
        else:
            test.setUp()
        suite.addTest(test)
    
    # Run the tests
    runner = unittest.TextTestRunner()
    runner.run(suite)
    
if __name__ == '__main__':
    # Check if a sprite sheet path was provided as a command-line argument
    import sys
    import argparse
    
    # Create a parser to correctly handle arguments
    parser = argparse.ArgumentParser(description='Run enemy bounds tests with optional custom sprite sheet.')
    parser.add_argument('--sprite-sheet', '-s', dest='sprite_sheet_path', 
                        help='Path to a custom sprite sheet to test')
    
    # Parse only known args to avoid conflicts with unittest's own argument parsing
    args, unittest_args = parser.parse_known_args()
    
    # Replace sys.argv with just the unittest args
    sys.argv[1:] = unittest_args
    
    if args.sprite_sheet_path:
        print(f"Using custom sprite sheet: {args.sprite_sheet_path}")
        run_tests(args.sprite_sheet_path)
    else:
        # Run tests with default (auto-generated) sprite sheet
        unittest.main()
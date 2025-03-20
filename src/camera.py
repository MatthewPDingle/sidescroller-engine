import pygame
from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT

class Camera:
    def __init__(self, level_width, level_height):
        # Camera dimensions (same as screen)
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        
        # Level dimensions in pixels
        self.level_width = level_width
        self.level_height = level_height
        
        # Camera position
        self.x = 0
        self.y = 0
        
        # Parallax scroll rates
        self.fg_scroll_rate = 1.0
        self.bg_scroll_rate = 0.4
        
        # Track if screen has been resized
        self.screen_resized = False
    
    def update(self, target_x, target_y):
        """Update camera position to follow target"""
        # Center target in camera view
        target_camera_x = target_x - (self.width // 2)
        
        # Ensure camera boundary respects level width
        max_camera_x = max(0, self.level_width - self.width)
        
        # Special handling if screen is wider than level
        if self.width >= self.level_width:
            # If screen is wider than level, keep camera at 0
            self.x = 0
        else:
            # Normal case - restrict camera to level boundaries
            self.x = max(0, min(target_camera_x, max_camera_x))
        
        # Vertical position currently fixed
        self.y = 0
    
    def apply(self, x, y):
        """Convert world coordinates to screen coordinates"""
        return x - self.x, y - self.y
    
    def apply_rect(self, rect):
        """Convert world rect to screen rect"""
        new_rect = pygame.Rect(rect)
        new_rect.x -= self.x
        new_rect.y -= self.y
        return new_rect
    
    def apply_parallax_bg(self, bg_x, bg_y, bg_width):
        """Apply parallax effect to background"""
        # Calculate background position with parallax scroll rate
        # We use a negative because we want the background to move in the opposite direction
        # of the camera movement (the camera moves right, the background moves left)
        parallax_x = -(self.x * self.bg_scroll_rate)
        
        # Ensure smooth transition as camera begins to move
        # This avoids any potential jumps in the background position
        
        return parallax_x, bg_y

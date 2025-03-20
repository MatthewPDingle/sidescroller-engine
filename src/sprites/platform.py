import pygame
import os

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, cell_size):
        super().__init__()
        
        # Store original dimensions in cells
        self.cell_x = x
        self.cell_y = y
        self.cell_width = width
        self.cell_height = height
        self.cell_size = cell_size
        
        # Convert to pixels
        pixel_x = x * cell_size
        pixel_y = y * cell_size
        pixel_width = width * cell_size
        pixel_height = height * cell_size
        
        # Get platform image path from level if available, or use default
        platform_path = None
        try:
            # Custom platform texture from the level data
            from level import Level
            if hasattr(Level, 'current_instance') and Level.current_instance and \
               'assets' in Level.current_instance.level_data and \
               'platform_image' in Level.current_instance.level_data['assets']:
                platform_path = Level.current_instance.level_data['assets']['platform_image']
        except (ImportError, AttributeError):
            pass
        
        # If no specific path or not found, use the default
        if not platform_path:
            platform_path = os.path.join('resources', 'graphics', 'platform.png')
        
        try:
            # Try to load platform texture
            self.image = pygame.image.load(platform_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (pixel_width, pixel_height))
        except (pygame.error, FileNotFoundError) as e:
            # Create fallback image - visible rectangle for platforms
            self.image = pygame.Surface((pixel_width, pixel_height))
            self.image.fill((150, 75, 0))  # Brown color
            
            # Add some visual detail 
            pygame.draw.rect(self.image, (180, 100, 20), 
                            pygame.Rect(2, 2, pixel_width-4, pixel_height-4))
        
        # Create rect
        self.rect = self.image.get_rect()
        self.rect.x = pixel_x
        self.rect.y = pixel_y

class GroundBlock(pygame.sprite.Sprite):
    def __init__(self, x, y, width, cell_size):
        super().__init__()
        
        # Store original dimensions in cells
        self.cell_x = x
        self.cell_y = y
        self.cell_width = width
        self.cell_size = cell_size
        
        # Convert to pixels
        pixel_x = x * cell_size
        pixel_y = y * cell_size
        pixel_width = width * cell_size
        pixel_height = cell_size  # Ground blocks are 1 cell tall
        
        # Create ground block surface
        self.image = pygame.Surface((pixel_width, pixel_height), pygame.SRCALPHA)
        
        # By default, ground is transparent (invisible)
        self.image.fill((0, 0, 0, 0))
        
        # Store the debug version (visible) of the ground block separately
        self.debug_image = pygame.Surface((pixel_width, pixel_height), pygame.SRCALPHA)
        pygame.draw.rect(self.debug_image, (0, 255, 0, 100), pygame.Rect(0, 0, pixel_width, pixel_height))
        
        # Add border for clarity
        pygame.draw.rect(self.debug_image, (0, 200, 0, 180), pygame.Rect(0, 0, pixel_width, pixel_height), 2)
        
        # Create rect
        self.rect = self.image.get_rect()
        self.rect.x = pixel_x
        self.rect.y = pixel_y

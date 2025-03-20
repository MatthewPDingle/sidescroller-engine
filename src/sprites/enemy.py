import pygame
import os
from enum import Enum, auto
from utils.constants import GRAVITY, TERMINAL_VELOCITY

class EnemyType(Enum):
    BASIC = auto()
    FLYING = auto()
    JUMPING = auto()

class Direction(Enum):
    NORTH = 0  # Up
    EAST = 1   # Right
    SOUTH = 2  # Down
    WEST = 3   # Left
    
    @staticmethod
    def from_movement(dx, dy):
        """Convert movement to direction"""
        if dx > 0:
            return Direction.EAST
        elif dx < 0:
            return Direction.WEST
        elif dy < 0:  # Negative y is up in pygame
            return Direction.NORTH
        elif dy > 0:
            return Direction.SOUTH
        else:
            return None  # No movement

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type, cell_size):
        super().__init__()
        self.cell_size = cell_size
        self.enemy_type = enemy_type
        
        # Convert from cell to pixel coordinates
        self.cell_x = x
        self.cell_y = y
        pixel_x = x * cell_size
        pixel_y = y * cell_size
        
        # Default values
        self.speed = 2
        self.direction = Direction.EAST  # Start facing right
        self.patrol_distance = 4 * cell_size  # 4 cells
        self.start_x = pixel_x
        
        # Physics properties - all enemies have gravity except flying type
        self.velocity_x = self.speed  # Initialize velocity
        self.velocity_y = 0
        self.on_ground = False
        
        # Always use armadillo_warrior_ss.png for all enemy types
        sprite_sheet_path = os.path.join('resources', 'graphics', 'armadillo_warrior_ss.png')
        
        try:
            sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
        except pygame.error:
            # Fallback sprite if even the armadillo sprite is missing
            print(f"Error: Could not load enemy sprite from {sprite_sheet_path}")
            sprite_sheet = pygame.Surface((64, 64))
            sprite_sheet.fill((255, 0, 0))  # Red for missing texture
        
        # Calculate frame size
        sheet_width, sheet_height = sprite_sheet.get_size()
        self.frame_width = sheet_width // 4
        self.frame_height = sheet_height // 4
        
        # Extract animation frames for all directions
        self.frames = self._create_animation_frames(sprite_sheet)
        
        # Precalculate tight bounds for each frame to avoid doing this every update
        self.frame_bounds = self._precalculate_frame_bounds()
        
        # Animation variables
        self.current_frame = 0
        self.animation_speed = 0.15
        self.animation_time = 0
        
        # Create initial image for sizing
        self.image = self.frames[self.direction.value][0]
        
        # Setup the rectangles with careful centering:
        
        # Step 1: Create visual rect (purple box) - exactly matches sprite dimensions
        self.visual_rect = pygame.Rect(0, 0, self.frame_width, self.frame_height)
        # Position it exactly at the intended position
        self.visual_rect.midbottom = (pixel_x, pixel_y)
        
        # Step 2: Calculate a tighter collision rect (orange box) based on non-transparent pixels
        # This will provide better collision detection by matching the visible sprite shape
        collision_width = int(self.frame_width * 0.7)  # Default to 70% if pixel analysis fails
        collision_height = int(self.frame_height * 0.9)  # Default to 90% if pixel analysis fails
        
        # Use precalculated bounds for the initial frame
        self.tight_bounds = self.frame_bounds[self.direction.value][0]
        
        # Create collision rect using the calculated bounds
        self.rect = pygame.Rect(0, 0, 
                               self.tight_bounds[2] - self.tight_bounds[0], 
                               self.tight_bounds[3] - self.tight_bounds[1])
        
        # Critically important: position the collision rect precisely relative to the visual rect
        self.rect.centerx = self.visual_rect.centerx  # Exact horizontal centering
        self.rect.bottom = self.visual_rect.bottom  # Align bottom with visual rect
        
        # Step 3: Create foot rect (cyan box) - small rect at bottom center of collision rect
        foot_width = int(self.rect.width * 0.6)  # 60% of collision width
        self.foot_rect = pygame.Rect(0, 0, foot_width, 6)  # 6 pixels high
        self.foot_rect.centerx = self.rect.centerx  # Center horizontally with collision rect
        self.foot_rect.bottom = self.rect.bottom    # Align with bottom of collision rect
        
        # Double-check alignment
        self.update_foot_rect()  # Ensure proper initial positioning
        
        # Set behavior based on enemy type
        if enemy_type == EnemyType.BASIC:
            # Patrol back and forth
            self._update = self._update_patrol
        elif enemy_type == EnemyType.FLYING:
            # Fly up and down - no gravity for flying enemies
            self._update = self._update_flying
            self.flight_height = 2 * cell_size
            self.start_y = pixel_y
            self.flight_direction = 1
            # Flying enemies don't need gravity
            self.on_ground = True  # Always consider flying enemies on ground
        elif enemy_type == EnemyType.JUMPING:
            # Jump periodically
            self._update = self._update_jumping
            self.jump_timer = 0
            self.jump_interval = 2.0  # seconds
            self.jump_strength = -10
            self.on_ground = False  # Will be set after first gravity check
    
    def _create_animation_frames(self, sprite_sheet):
        """Create animation frames from sprite sheet"""
        # Create a dictionary to hold frames for each direction
        all_frames = {}
        
        # Extract frames for each direction (4x4 grid)
        for row, direction in enumerate([Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]):
            direction_frames = []
            
            for col in range(4):
                # Extract frame from sprite sheet
                frame = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
                frame.blit(sprite_sheet, (0, 0), (
                    col * self.frame_width, 
                    row * self.frame_height, 
                    self.frame_width, 
                    self.frame_height
                ))
                direction_frames.append(frame)
            
            all_frames[direction.value] = direction_frames
        
        return all_frames
        
    def _precalculate_frame_bounds(self):
        """Precalculate the tight bounds for all animation frames."""
        bounds = {}
        
        # For each direction
        for direction in Direction:
            if direction.value not in self.frames:
                continue
                
            direction_bounds = []
            # For each frame in this direction
            for frame in self.frames[direction.value]:
                # Calculate bounds for this frame
                frame_bounds = self._calculate_tight_bounds(frame)
                direction_bounds.append(frame_bounds)
            
            bounds[direction.value] = direction_bounds
            
        return bounds
    
    def _calculate_tight_bounds(self, surface):
        """Calculate tight bounds around non-transparent pixels in a surface.
        Returns a tuple of (min_x, min_y, max_x, max_y)."""
        # Get surface dimensions
        width, height = surface.get_size()
        
        # Initialize bounds to extreme values
        min_x = width
        min_y = height
        max_x = 0
        max_y = 0
        
        # Alpha threshold for considering a pixel "solid"
        # Values below this are considered transparent
        alpha_threshold = 25
        
        # Scan the surface for non-transparent pixels
        for y in range(height):
            for x in range(width):
                # Get the color at this pixel
                color = surface.get_at((x, y))
                
                # Check if this pixel is visible (alpha > threshold)
                if color[3] > alpha_threshold:  # Alpha is the 4th component (index 3)
                    # Update bounds
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x + 1)  # +1 to get correct width
                    max_y = max(max_y, y + 1)  # +1 to get correct height
        
        # If no non-transparent pixels found, return default bounds
        if min_x > max_x or min_y > max_y:
            return (0, 0, width, height)
            
        # Add a small buffer (padding) for better collision
        buffer = 2
        min_x = max(0, min_x - buffer)
        min_y = max(0, min_y - buffer)
        max_x = min(width, max_x + buffer)
        max_y = min(height, max_y + buffer)
        
        return (min_x, min_y, max_x, max_y)
    
    def update_visual_rect(self):
        """Update the visual rectangle to match current sprite"""
        # Center visual rect on collision rect
        self.visual_rect.centerx = self.rect.centerx
        self.visual_rect.bottom = self.rect.bottom
    
    def update_foot_rect(self):
        """Update the foot rectangle position to match the enemy's position"""
        self.foot_rect.width = self.rect.width // 2
        self.foot_rect.height = 8
        self.foot_rect.centerx = self.rect.centerx
        self.foot_rect.bottom = self.rect.bottom
        
    def update_collision_bounds_for_frame(self):
        """Update collision rectangle based on the current frame's non-transparent pixels"""
        # Use the precalculated bounds for the current frame and direction
        new_bounds = self.frame_bounds[self.direction.value][self.current_frame]
        
        # Store the current position
        old_centerx = self.rect.centerx
        old_bottom = self.rect.bottom
        
        # Update collision rect with new dimensions
        self.rect.width = new_bounds[2] - new_bounds[0] 
        self.rect.height = new_bounds[3] - new_bounds[1]
        
        # Restore position
        self.rect.centerx = old_centerx
        self.rect.bottom = old_bottom
    
    def update(self, dt, platforms, ground_blocks):
        """Update enemy based on its type"""
        # Store original position for collision
        old_x = self.rect.x
        old_y = self.rect.y
        
        # Apply gravity if not flying type and not on ground
        if self.enemy_type != EnemyType.FLYING and not self.on_ground:
            self.velocity_y += GRAVITY
            if self.velocity_y > TERMINAL_VELOCITY:
                self.velocity_y = TERMINAL_VELOCITY
            
            # Apply vertical velocity 
            self.rect.y += int(self.velocity_y)
            self.update_foot_rect()  # Update foot rect after vertical position change
            
            # Reset ground state to check actual collision
            self.on_ground = False
            
            # Check ground collisions
            self.check_ground_collisions(platforms, ground_blocks)
        
        # Call the appropriate behavior update method based on enemy type
        self._update(dt, platforms, ground_blocks)
        
        # Update visual rect and foot rect positions to match collision rect
        self.update_visual_rect()
        self.update_foot_rect()
        
        # Update animation
        self.animation_time += dt
        if self.animation_time >= self.animation_speed:
            self.current_frame = (self.current_frame + 1) % 4
            self.animation_time = 0
            
            # Use the correct set of frames based on direction
            self.image = self.frames[self.direction.value][self.current_frame]
            
            # Update collision rectangle based on the current frame's non-transparent pixels
            self.update_collision_bounds_for_frame()
    
    def check_ground_collisions(self, platforms, ground_blocks):
        """Check if enemy is on ground"""
        # Check platform collisions for landing
        for platform in platforms:
            if self.rect.colliderect(platform.rect) and self.velocity_y > 0:
                self.rect.bottom = platform.rect.top
                self.on_ground = True
                self.velocity_y = 0
                return
        
        # Check ground block collisions for landing
        for block in ground_blocks:
            if self.rect.colliderect(block.rect) and self.velocity_y > 0:
                self.rect.bottom = block.rect.top
                self.on_ground = True
                self.velocity_y = 0
                return
    
    def check_edge(self, platforms, ground_blocks):
        """Check if there's ground ahead in the direction of movement"""
        # Create a temporary sensor rect extending downward from the front edge
        edge_sensor = pygame.Rect(0, 0, 10, 20)
        
        # Position the sensor based on direction
        if self.direction == Direction.EAST:
            edge_sensor.midtop = (self.rect.right, self.rect.bottom)
        else:  # Direction.WEST
            edge_sensor.midtop = (self.rect.left, self.rect.bottom)
        
        # Check if the sensor collides with any platform or ground
        for platform in platforms:
            if edge_sensor.colliderect(platform.rect):
                return True  # There's ground ahead
        
        for block in ground_blocks:
            if edge_sensor.colliderect(block.rect):
                return True  # There's ground ahead
        
        return False  # No ground ahead - there's an edge
    
    def _update_patrol(self, dt, platforms, ground_blocks):
        """Update logic for patrolling enemies"""
        # Only move horizontally if on ground (unless flying)
        if self.on_ground or self.enemy_type == EnemyType.FLYING:
            # Check if there's ground ahead before moving
            if not self.check_edge(platforms, ground_blocks) and self.enemy_type != EnemyType.FLYING:
                # No ground ahead - reverse direction to avoid falling
                if self.direction == Direction.EAST:
                    self.direction = Direction.WEST
                else:
                    self.direction = Direction.EAST
            
            # Set velocity based on direction
            self.velocity_x = self.speed if self.direction == Direction.EAST else -self.speed
            
            # Move horizontally
            self.rect.x += self.velocity_x
            self.update_foot_rect()  # Update foot rect after horizontal position change
            
            # Check if we've reached the patrol limit
            old_direction = self.direction
            if self.direction == Direction.EAST and self.rect.centerx > self.start_x + self.patrol_distance:
                self.direction = Direction.WEST
            elif self.direction == Direction.WEST and self.rect.centerx < self.start_x - self.patrol_distance:
                self.direction = Direction.EAST
                
            # If direction changed, immediately update collision bounds for the new direction
            if old_direction != self.direction:
                # Update the sprite image for the new direction
                self.image = self.frames[self.direction.value][self.current_frame]
                
                # Update collision bounds for the new direction's frame
                self.update_collision_bounds_for_frame()
            
            # Check for horizontal collisions
            for platform in platforms:
                if self.rect.colliderect(platform.rect):
                    # Save old direction
                    old_direction = self.direction
                    # Reverse direction
                    self.direction = Direction.WEST if self.direction == Direction.EAST else Direction.EAST
                    # Reset position to avoid getting stuck
                    if self.direction == Direction.EAST:
                        self.rect.left = platform.rect.right
                    else:
                        self.rect.right = platform.rect.left
                    
                    # If direction changed, immediately update collision bounds for the new direction
                    if old_direction != self.direction:
                        # Update the sprite image for the new direction
                        self.image = self.frames[self.direction.value][self.current_frame]
                        
                        # Update collision bounds for the new direction's frame
                        self.update_collision_bounds_for_frame()
                    
                    self.update_foot_rect()  # Update foot rect after collision repositioning
                    break
            
            for block in ground_blocks:
                if self.rect.colliderect(block.rect):
                    # Save old direction
                    old_direction = self.direction
                    # Reverse direction
                    self.direction = Direction.WEST if self.direction == Direction.EAST else Direction.EAST
                    # Reset position to avoid getting stuck
                    if self.direction == Direction.EAST:
                        self.rect.left = block.rect.right
                    else:
                        self.rect.right = block.rect.left
                    
                    # If direction changed, immediately update collision bounds for the new direction
                    if old_direction != self.direction:
                        # Update the sprite image for the new direction
                        self.image = self.frames[self.direction.value][self.current_frame]
                        
                        # Update collision bounds for the new direction's frame
                        self.update_collision_bounds_for_frame()
                    
                    self.update_foot_rect()  # Update foot rect after collision repositioning
                    break
    
    def _update_flying(self, dt, platforms, ground_blocks):
        """Update logic for flying enemies"""
        # Move up and down
        self.rect.y += self.speed * self.flight_direction
        self.update_foot_rect()  # Update foot rect after vertical movement
        
        # Check if we've reached the flight limit
        if self.flight_direction > 0 and self.rect.bottom > self.start_y:
            self.flight_direction = -1
        elif self.flight_direction < 0 and self.rect.bottom < self.start_y - self.flight_height:
            self.flight_direction = 1
        
        # Move horizontally based on direction
        self.velocity_x = self.speed if self.direction == Direction.EAST else -self.speed
        self.rect.x += self.velocity_x
        self.update_foot_rect()  # Update foot rect after horizontal movement
        
        # Check if we've reached the patrol limit
        old_direction = self.direction
        if self.direction == Direction.EAST and self.rect.centerx > self.start_x + self.patrol_distance:
            self.direction = Direction.WEST
        elif self.direction == Direction.WEST and self.rect.centerx < self.start_x - self.patrol_distance:
            self.direction = Direction.EAST
            
        # If direction changed, immediately update collision bounds for the new direction
        if old_direction != self.direction:
            # Update the sprite image for the new direction
            self.image = self.frames[self.direction.value][self.current_frame]
            
            # Update collision bounds for the new direction's frame
            self.update_collision_bounds_for_frame()
    
    def _update_jumping(self, dt, platforms, ground_blocks):
        """Update logic for jumping enemies"""
        # Jump timer logic - jump is now handled in the main update
        if self.on_ground:
            self.jump_timer += dt
            if self.jump_timer >= self.jump_interval:
                self.velocity_y = self.jump_strength
                self.on_ground = False
                self.jump_timer = 0
                self.update_foot_rect()  # Update foot rect after jump
        
        # Patrol horizontally if on ground
        if self.on_ground:
            # Check if there's ground ahead before moving
            if not self.check_edge(platforms, ground_blocks):
                # No ground ahead - reverse direction
                old_direction = self.direction
                self.direction = Direction.WEST if self.direction == Direction.EAST else Direction.EAST
                
                # If direction changed, immediately update collision bounds for the new direction
                if old_direction != self.direction:
                    # Update the sprite image for the new direction
                    self.image = self.frames[self.direction.value][self.current_frame]
                    
                    # Update collision bounds for the new direction's frame
                    self.update_collision_bounds_for_frame()
            
            # Set velocity based on direction
            self.velocity_x = self.speed if self.direction == Direction.EAST else -self.speed
            
            # Move horizontally
            self.rect.x += self.velocity_x
            self.update_foot_rect()  # Update foot rect after horizontal movement
            
            # Check if we've reached the patrol limit
            old_direction = self.direction
            if self.direction == Direction.EAST and self.rect.centerx > self.start_x + self.patrol_distance:
                self.direction = Direction.WEST
            elif self.direction == Direction.WEST and self.rect.centerx < self.start_x - self.patrol_distance:
                self.direction = Direction.EAST
                
            # If direction changed, immediately update collision bounds for the new direction
            if old_direction != self.direction:
                # Update the sprite image for the new direction
                self.image = self.frames[self.direction.value][self.current_frame]
                
                # Update collision bounds for the new direction's frame
                self.update_collision_bounds_for_frame()
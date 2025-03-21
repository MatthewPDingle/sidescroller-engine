import pygame
import pygame.mixer
import os
from enum import Enum, auto
from utils.constants import GRAVITY, PLAYER_SPEED, JUMP_STRENGTH, TERMINAL_VELOCITY

class Direction(Enum):
    NORTH = auto()
    EAST = auto()
    SOUTH = auto()
    WEST = auto()
    
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

class AnimationState(Enum):
    IDLE = auto()
    WALKING = auto()
    JUMPING = auto()

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, cell_size):
        super().__init__()
        self.cell_size = cell_size
        
        # Load sprite sheet
        try:
            sprite_sheet = pygame.image.load(os.path.join('resources', 'graphics', 'characters', 'scientist_ss.png')).convert_alpha()
        except pygame.error:
            # Create fallback surface
            sprite_sheet = pygame.Surface((64, 64))
            sprite_sheet.fill((255, 0, 255))  # Magenta for missing texture
        
        # Calculate frame size
        sheet_width, sheet_height = sprite_sheet.get_size()
        self.frame_width = sheet_width // 4
        self.frame_height = sheet_height // 4
        
        # Create animation frames
        self.frames = {}
        self._create_animation_frames(sprite_sheet)
        
        # Initialize state
        self.direction = Direction.EAST
        self.animation_state = AnimationState.IDLE
        self.animation_frame = 0
        self.animation_speed = 0.15  # Frames per update
        self.animation_time = 0
        
        # Set up physics
        self.rect = pygame.Rect(0, 0, self.frame_width // 2, self.frame_height)  # Half width rect for better collision
        self.rect.centerx = x
        self.rect.bottom = y  # Bottom-aligned for platforms
        
        # Create visual rect for debug display (full sprite size)
        self.visual_rect = pygame.Rect(0, 0, self.frame_width, self.frame_height)
        self.update_visual_rect()
        
        # Create foot rect for more precise ground detection
        self.foot_rect = pygame.Rect(0, 0, self.rect.width // 2, 10)
        self.update_foot_rect()
        
        self.velocity_x = 0
        self.velocity_y = 0
        self.on_ground = False
        
        # Ground check stability
        self.ground_buffer = 0  # Frames to remain "on ground" after leaving ground
        self.ground_buffer_max = 5  # Max frames to buffer ground state
        
        # Jump control
        self.jump_cooldown = 0
        self.can_jump = True
        self.jumping = False
        self.jump_released = True  # To prevent holding the jump key
        
        # Update image
        self.update_image()
    
    def _create_animation_frames(self, sprite_sheet):
        """Create animation frames from sprite sheet"""
        # Initialize direction frames
        for direction in Direction:
            self.frames[direction] = []
        
        # Extract frames for each direction (4x4 grid)
        for row, direction in enumerate([Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]):
            for col in range(4):
                # Extract frame from sprite sheet
                frame = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
                frame.blit(sprite_sheet, (0, 0), (
                    col * self.frame_width, 
                    row * self.frame_height, 
                    self.frame_width, 
                    self.frame_height
                ))
                
                self.frames[direction].append(frame)
    
    def update_image(self):
        """Update the current image based on state"""
        if self.animation_state == AnimationState.IDLE:
            # Use 4th frame (index 3) for idle
            self.image = self.frames[self.direction][3]
        else:
            # Use current animation frame for other states
            frame_index = int(self.animation_frame) % 4
            self.image = self.frames[self.direction][frame_index]
        
        # Get current sprite dimensions
        img_width = self.image.get_width()
        img_height = self.image.get_height()
        
        # Store current position before updating rect dimensions
        old_centerx = self.rect.centerx
        old_bottom = self.rect.bottom
        
        # Update collision rect (narrower than the sprite for better collision)
        # Center it horizontally on the sprite
        self.rect.width = img_width // 2  # Half width for better collisions
        self.rect.height = img_height
        self.rect.centerx = old_centerx
        self.rect.bottom = old_bottom
        
        # Update foot rect position
        self.update_foot_rect()
        
        # Set visual rect to exactly match the sprite image dimensions
        self.visual_rect.width = img_width
        self.visual_rect.height = img_height
        self.visual_rect.centerx = old_centerx
        self.visual_rect.bottom = old_bottom
        
    def update_visual_rect(self):
        """Update the visual rectangle to match the full sprite dimensions"""
        self.visual_rect.width = self.frame_width
        self.visual_rect.height = self.frame_height
        # Center the visual rect on the collision rect
        self.visual_rect.centerx = self.rect.centerx
        self.visual_rect.bottom = self.rect.bottom
    
    def update_foot_rect(self):
        """Update the foot rectangle position to match the player's position"""
        self.foot_rect.width = self.rect.width // 2
        self.foot_rect.height = 10
        self.foot_rect.centerx = self.rect.centerx
        self.foot_rect.bottom = self.rect.bottom
    
    def update(self, dt, platforms, ground_blocks):
        """Update player state"""
        # Store old position for collision detection
        old_x = self.rect.x
        old_y = self.rect.y
        
        # Update jump cooldown
        if self.jump_cooldown > 0:
            self.jump_cooldown -= dt
            if self.jump_cooldown <= 0:
                self.jump_cooldown = 0
                self.can_jump = True
        
        # Remember previous ground state before any collision checks
        was_on_ground = self.on_ground
        
        # Handle ground buffer for stability (coyote time)
        if was_on_ground and self.ground_buffer <= 0:
            # If truly on ground, keep ground buffer at max
            self.ground_buffer = self.ground_buffer_max
        elif self.ground_buffer > 0:
            # Decrement ground buffer if we're not physically on ground
            self.ground_buffer -= 1
        
        # Apply gravity only if jumping or falling
        if self.jumping or not (was_on_ground or self.ground_buffer > 0):
            self.velocity_y += GRAVITY
            if self.velocity_y > TERMINAL_VELOCITY:
                self.velocity_y = TERMINAL_VELOCITY
        
        # Track if jump state should end
        if self.jumping and self.velocity_y > 0:  # Reached apex, now falling
            self.jumping = False
        
        # Check current keyboard state to ensure continuous movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity_x = -PLAYER_SPEED
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity_x = PLAYER_SPEED
        elif not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            self.velocity_x = 0
            
        # Update horizontal position first
        self.rect.x += int(self.velocity_x)
        self.update_foot_rect()
        
        # Horizontal collision detection
        self.check_horizontal_collisions(platforms, ground_blocks, old_x)
        
        # Then update vertical position
        self.rect.y += int(self.velocity_y)
        self.update_foot_rect()
        
        # Reset ground state to check actual collision
        self.on_ground = False
        
        # Vertical collision detection
        self.check_vertical_collisions(platforms, ground_blocks, old_y)
        
        # Update jump state when landing
        if self.on_ground and not was_on_ground:
            self.jumping = False
            self.can_jump = True
            self.ground_buffer = self.ground_buffer_max
        
        # Determine on_ground state using both physical contact and ground buffer
        effective_on_ground = self.on_ground or (self.ground_buffer > 0 and self.velocity_y >= 0)
        
        # Update direction based on movement regardless of being on ground or in air
        if self.velocity_x != 0:
            self.direction = Direction.EAST if self.velocity_x > 0 else Direction.WEST
        
        # Update animation state
        if self.jumping:
            self.animation_state = AnimationState.JUMPING
        elif effective_on_ground:
            if self.velocity_x != 0:
                self.animation_state = AnimationState.WALKING
            else:
                self.animation_state = AnimationState.IDLE
        else:
            self.animation_state = AnimationState.JUMPING
        
        # Update animation frame
        if self.animation_state != AnimationState.IDLE:
            self.animation_time += dt
            if self.animation_time >= self.animation_speed:
                self.animation_frame += 1
                if self.animation_frame >= 4:
                    self.animation_frame = 0
                self.animation_time = 0
        
        # Update image
        self.update_image()
    
    def check_horizontal_collisions(self, platforms, ground_blocks, old_x):
        """Check and resolve horizontal collisions"""
        # Check level boundary collisions
        from level import Level
        if Level.current_instance:
            level_width_pixels = Level.current_instance.level_width_pixels
            # Left boundary check
            if self.rect.left < 0:
                self.rect.left = 0
                # Don't reset velocity_x to 0 - player might still be holding the key
                self.update_foot_rect()
            # Right boundary check
            elif self.rect.right > level_width_pixels:
                self.rect.right = level_width_pixels
                # Don't reset velocity_x to 0 - player might still be holding the key
                self.update_foot_rect()
        
        # Check platform collisions
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # Moving right, hit left side of platform
                if self.velocity_x > 0:
                    self.rect.right = platform.rect.left
                # Moving left, hit right side of platform
                elif self.velocity_x < 0:
                    self.rect.left = platform.rect.right
                # Don't reset velocity_x to 0 - we'll use key_get_pressed to determine direction
                self.update_foot_rect()  # Update foot rect after position change
        
        # Check ground block collisions
        for block in ground_blocks:
            if self.rect.colliderect(block.rect):
                # Moving right, hit left side of block
                if self.velocity_x > 0:
                    self.rect.right = block.rect.left
                # Moving left, hit right side of block
                elif self.velocity_x < 0:
                    self.rect.left = block.rect.right
                # Don't reset velocity_x to 0 - we'll use key_get_pressed to determine direction
                self.update_foot_rect()  # Update foot rect after position change
    
    def check_vertical_collisions(self, platforms, ground_blocks, old_y):
        """Check and resolve vertical collisions"""
        self.on_ground = False
        
        # Special ground sensor rect (extends a bit below player feet)
        ground_sensor = pygame.Rect(self.foot_rect)
        ground_sensor.height = 12  # Extend foot rect more to ensure better ground detection
        ground_sensor.bottom = self.rect.bottom + 2  # Actually check slightly below feet
        
        # Check platform collisions
        for platform in platforms:
            # First check if we could be standing on the platform (using ground sensor)
            if ground_sensor.colliderect(platform.rect) and self.velocity_y >= 0:
                # Adjust to stand exactly on the platform
                self.rect.bottom = platform.rect.top
                self.on_ground = True
                self.velocity_y = 0
                self.update_foot_rect()
                break
                
            # Check standard collision (for hitting platform from below/sides)
            elif self.rect.colliderect(platform.rect):
                # Moving up, hit bottom of platform
                if self.velocity_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity_y = 0
                    self.update_foot_rect()
        
        # Check ground block collisions (only if not already on a platform)
        if not self.on_ground:
            # Use ground sensor for more precise and stable ground detection
            for block in ground_blocks:
                if ground_sensor.colliderect(block.rect) and self.velocity_y >= 0:
                    # Set position exactly at ground level
                    self.rect.bottom = block.rect.top
                    self.on_ground = True
                    self.velocity_y = 0
                    self.update_foot_rect()
                    break
            
            # If still not on ground, check body collisions for hitting ceiling/walls
            if not self.on_ground:
                for block in ground_blocks:
                    if self.rect.colliderect(block.rect):
                        # Moving up, hit bottom of ground block
                        if self.velocity_y < 0:
                            self.rect.top = block.rect.bottom
                            self.velocity_y = 0
                            self.update_foot_rect()
                        # Could still be a ground collision on the edge cases
                        elif self.velocity_y > 0:
                            # Check if we can stand on this block
                            distance_into_block = self.rect.bottom - block.rect.top
                            if distance_into_block < 20:  # Allow more tolerance for fixing position
                                self.rect.bottom = block.rect.top
                                self.on_ground = True
                                self.velocity_y = 0
                                self.update_foot_rect()
        
        # Always ensure foot rect is aligned with player position
        self.update_foot_rect()
    
    def handle_event(self, event):
        """Handle player input events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.velocity_x = -PLAYER_SPEED
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.velocity_x = PLAYER_SPEED
            elif event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
                # Simple jump mechanic - jump immediately when key is pressed
                jumped = self.jump()
                
                # Play sound on successful jump
                if jumped:
                    try:
                        from level import Level
                        if Level.current_instance and Level.current_instance.game and hasattr(Level.current_instance.game, 'jump_sound'):
                            Level.current_instance.game.jump_sound.play()
                    except (ImportError, AttributeError, ValueError) as e:
                        pass
        
        elif event.type == pygame.KEYUP:
            if event.key in [pygame.K_LEFT, pygame.K_a] and self.velocity_x < 0:
                self.velocity_x = 0
            elif event.key in [pygame.K_RIGHT, pygame.K_d] and self.velocity_x > 0:
                self.velocity_x = 0
            # Reset jump key released state when jump key is released
            elif event.key in [pygame.K_SPACE, pygame.K_UP, pygame.K_w]:
                self.jump_released = True
    
    def jump(self):
        """Make the player jump (simple implementation)"""
        # Determine if player can jump using either actual ground contact or buffer (coyote time)
        effective_on_ground = self.on_ground or (self.ground_buffer > 0 and self.velocity_y >= 0)
        
        if effective_on_ground and self.can_jump and self.jump_released:
            # Set jump cooldown to prevent immediate rejump
            self.jump_cooldown = 0.2  # 200ms cooldown
            self.can_jump = False
            
            # Set jump state
            self.jumping = True
            self.on_ground = False  # Force off ground immediately
            self.ground_buffer = 0  # Clear ground buffer
            
            # Set jump velocity
            self.velocity_y = JUMP_STRENGTH
            self.animation_state = AnimationState.JUMPING
            
            # Move the player up by 5 pixels to ensure they're not still touching the ground
            # This prevents the stuttering jump issue where the player immediately gets set back to on_ground
            self.rect.y -= 5
            self.update_foot_rect()
            
            # Mark jump key as not released yet (requires releasing before next jump)
            self.jump_released = False
            
            return True
            
        return False

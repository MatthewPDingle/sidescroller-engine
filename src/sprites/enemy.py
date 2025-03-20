import pygame
import os
from enum import Enum, auto

class EnemyType(Enum):
    BASIC = auto()
    FLYING = auto()
    JUMPING = auto()

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
        self.direction = 1  # 1 = right, -1 = left
        self.patrol_distance = 4 * cell_size  # 4 cells
        self.start_x = pixel_x
        
        # Try to load sprite sheet based on enemy type
        sprite_sheet_path = os.path.join('resources', 'graphics', f'{enemy_type.name.lower()}_enemy_ss.png')
        
        try:
            sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
        except pygame.error:
            # Fallback sprite
            sprite_sheet = pygame.Surface((64, 64))
            sprite_sheet.fill((255, 0, 0))  # Red for missing texture
        
        # Calculate frame size
        sheet_width, sheet_height = sprite_sheet.get_size()
        self.frame_width = sheet_width // 4
        self.frame_height = sheet_height // 4
        
        # Extract animation frames
        self.frames = self._create_animation_frames(sprite_sheet)
        
        # Animation variables
        self.current_frame = 0
        self.animation_speed = 0.15
        self.animation_time = 0
        
        # Rect for collision
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.centerx = pixel_x
        self.rect.bottom = pixel_y  # Bottom-centered like player
        
        # Set behavior based on enemy type
        if enemy_type == EnemyType.BASIC:
            # Patrol back and forth
            self._update = self._update_patrol
        elif enemy_type == EnemyType.FLYING:
            # Fly up and down
            self._update = self._update_flying
            self.flight_height = 2 * cell_size
            self.start_y = pixel_y
            self.flight_direction = 1
        elif enemy_type == EnemyType.JUMPING:
            # Jump periodically
            self._update = self._update_jumping
            self.jump_timer = 0
            self.jump_interval = 2.0  # seconds
            self.jump_strength = -10
            self.gravity = 0.5
            self.velocity_y = 0
            self.on_ground = True
    
    def _create_animation_frames(self, sprite_sheet):
        """Create animation frames from sprite sheet"""
        frames = []
        
        # Use the bottom row (south-facing) frames for enemies
        row = 2  # South-facing
        for col in range(4):
            frame = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
            frame.blit(sprite_sheet, (0, 0), (
                col * self.frame_width, 
                row * self.frame_height, 
                self.frame_width, 
                self.frame_height
            ))
            frames.append(frame)
        
        return frames
    
    def update(self, dt, platforms, ground_blocks):
        """Update enemy based on its type"""
        # Call the appropriate update method based on enemy type
        self._update(dt, platforms, ground_blocks)
        
        # Update animation
        self.animation_time += dt
        if self.animation_time >= self.animation_speed:
            self.current_frame = (self.current_frame + 1) % 4
            self.animation_time = 0
            self.image = self.frames[self.current_frame]
    
    def _update_patrol(self, dt, platforms, ground_blocks):
        """Update logic for patrolling enemies"""
        # Move horizontally
        self.rect.x += self.speed * self.direction
        
        # Check if we've reached the patrol limit
        if self.direction > 0 and self.rect.centerx > self.start_x + self.patrol_distance:
            self.direction = -1
            # Flip frames horizontally
            self.frames = [pygame.transform.flip(frame, True, False) for frame in self.frames]
        elif self.direction < 0 and self.rect.centerx < self.start_x - self.patrol_distance:
            self.direction = 1
            # Flip frames back
            self.frames = [pygame.transform.flip(frame, True, False) for frame in self.frames]
        
        # Check for collisions with platforms and ground blocks
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # Reverse direction
                self.direction *= -1
                # Flip frames
                self.frames = [pygame.transform.flip(frame, True, False) for frame in self.frames]
                break
        
        for block in ground_blocks:
            if self.rect.colliderect(block.rect):
                # Reverse direction
                self.direction *= -1
                # Flip frames
                self.frames = [pygame.transform.flip(frame, True, False) for frame in self.frames]
                break
    
    def _update_flying(self, dt, platforms, ground_blocks):
        """Update logic for flying enemies"""
        # Move up and down
        self.rect.y += self.speed * self.flight_direction
        
        # Check if we've reached the flight limit
        if self.flight_direction > 0 and self.rect.bottom > self.start_y:
            self.flight_direction = -1
        elif self.flight_direction < 0 and self.rect.bottom < self.start_y - self.flight_height:
            self.flight_direction = 1
        
        # Also patrol horizontally like basic enemies
        self._update_patrol(dt, platforms, ground_blocks)
    
    def _update_jumping(self, dt, platforms, ground_blocks):
        """Update logic for jumping enemies"""
        # Apply gravity
        if not self.on_ground:
            self.velocity_y += self.gravity
            self.rect.y += self.velocity_y
        
        # Check for landing
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect) and self.velocity_y > 0:
                self.rect.bottom = platform.rect.top
                self.on_ground = True
                self.velocity_y = 0
                break
        
        for block in ground_blocks:
            if self.rect.colliderect(block.rect) and self.velocity_y > 0:
                self.rect.bottom = block.rect.top
                self.on_ground = True
                self.velocity_y = 0
                break
        
        # Jump timer
        if self.on_ground:
            self.jump_timer += dt
            if self.jump_timer >= self.jump_interval:
                self.velocity_y = self.jump_strength
                self.on_ground = False
                self.jump_timer = 0
        
        # Also patrol horizontally like basic enemies
        self._update_patrol(dt, platforms, ground_blocks)

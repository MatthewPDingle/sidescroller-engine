import pygame
import json
import os
from camera import Camera
from sprites.player import Player
from sprites.platform import Platform, GroundBlock
from sprites.enemy import Enemy, EnemyType
from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_START_X, DEBUG, WHITE, RED, GREEN

class Level:
    # Class variable to track current instance for asset loading
    current_instance = None
    
    def __init__(self, level_path, game):
        # Set as current instance
        Level.current_instance = self
        
        self.game = game
        self.debug = DEBUG
        
        # Load level data
        with open(level_path, 'r') as file:
            self.level_data = json.load(file)
        
        # Extract level dimensions
        self.cell_size = self.level_data['dimensions']['cell_size']
        self.level_width_cells = self.level_data['dimensions']['width']
        self.level_height_cells = self.level_data['dimensions']['height']
        self.level_width_pixels = self.level_width_cells * self.cell_size
        self.level_height_pixels = self.level_height_cells * self.cell_size
        
        # Create camera
        self.camera = Camera(self.level_width_pixels, self.level_height_pixels)
        
        # Set parallax rates
        if 'parallax' in self.level_data:
            self.camera.fg_scroll_rate = self.level_data['parallax']['fg_scroll_rate']
            self.camera.bg_scroll_rate = self.level_data['parallax']['bg_scroll_rate']
        
        # Load assets
        self.load_assets()
        
        # Create sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.ground_blocks = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        
        # Create level elements
        self.create_level()
        
        # Create debug font
        self.debug_font = pygame.font.SysFont(None, 24)
    
    def load_assets(self):
        """Load level assets"""
        # Load background image
        try:
            bg_path = self.level_data['assets']['background']
            if os.path.isabs(bg_path):
                # Extract filename from absolute path
                bg_filename = os.path.basename(bg_path)
                bg_path = os.path.join('resources', 'graphics', bg_filename)
            
            print(f"Loading background from: {bg_path}")
            self.bg_image = pygame.image.load(bg_path).convert_alpha()
        except (pygame.error, KeyError, FileNotFoundError) as e:
            print(f"Warning: Could not load background image: {e}")
            # Create fallback background that's wide enough for proper tiling
            # Use 2048x512 as a common background size for proper tiling
            self.bg_image = pygame.Surface((2048, SCREEN_HEIGHT))
            self.bg_image.fill((100, 150, 255))  # Sky blue
            
            # Add some simple decoration to the fallback background
            # Draw some clouds
            for i in range(10):
                cloud_x = i * 200 + 50
                cloud_y = 50 + (i % 3) * 40
                cloud_radius = 30 + (i % 3) * 10
                pygame.draw.circle(self.bg_image, (255, 255, 255), (cloud_x, cloud_y), cloud_radius)
                pygame.draw.circle(self.bg_image, (255, 255, 255), (cloud_x + 40, cloud_y + 10), cloud_radius - 5)
                pygame.draw.circle(self.bg_image, (255, 255, 255), (cloud_x + 20, cloud_y - 10), cloud_radius - 10)
        
        # Load foreground image
        try:
            fg_path = self.level_data['assets']['foreground']
            if os.path.isabs(fg_path):
                # Extract filename from absolute path
                fg_filename = os.path.basename(fg_path)
                fg_path = os.path.join('resources', 'graphics', fg_filename)
            
            print(f"Loading foreground from: {fg_path}")
            self.fg_image = pygame.image.load(fg_path).convert_alpha()
        except (pygame.error, KeyError, FileNotFoundError) as e:
            print(f"Warning: Could not load foreground image: {e}")
            # Create fallback foreground that matches the background width
            self.fg_image = pygame.Surface((2048, SCREEN_HEIGHT), pygame.SRCALPHA)
            # Draw some hills at the bottom
            pygame.draw.rect(self.fg_image, (100, 80, 60, 180), (0, SCREEN_HEIGHT - 100, 2048, 100))
            for i in range(20):
                hill_x = i * 100
                hill_height = 50 + (i % 5) * 20
                hill_width = 200
                pygame.draw.ellipse(self.fg_image, (120, 100, 80, 180), 
                                    (hill_x, SCREEN_HEIGHT - hill_height, hill_width, hill_height * 2))
            
        # Fix platform image path if present
        if 'platform_image' in self.level_data['assets']:
            platform_path = self.level_data['assets']['platform_image']
            if os.path.isabs(platform_path):
                # Extract filename from absolute path
                platform_filename = os.path.basename(platform_path)
                self.level_data['assets']['platform_image'] = os.path.join('resources', 'graphics', platform_filename)
                print(f"Updated platform image path to: {self.level_data['assets']['platform_image']}")
        
        # Get image dimensions
        self.bg_width, self.bg_height = self.bg_image.get_size()
        self.fg_width, self.fg_height = self.fg_image.get_size()
        
        print(f"Background dimensions: {self.bg_width}x{self.bg_height}")
        print(f"Foreground dimensions: {self.fg_width}x{self.fg_height}")
    
    def create_level(self):
        """Create all level elements"""
        # Create player at the starting position (4th cell from left edge)
        player_x = PLAYER_START_X * self.cell_size
        player_y = 0  # Start at the top and fall down
        self.player = Player(player_x, player_y, self.cell_size)
        self.all_sprites.add(self.player)
        
        # Create platforms
        for platform_data in self.level_data['platforms']:
            platform = Platform(
                platform_data['x'], 
                platform_data['y'], 
                platform_data['width'], 
                platform_data.get('height', 1), 
                self.cell_size
            )
            self.platforms.add(platform)
            self.all_sprites.add(platform)
        
        # Create ground blocks
        for block_data in self.level_data['ground_blocks']:
            block = GroundBlock(
                block_data['x'], 
                block_data['y'], 
                block_data['width'], 
                self.cell_size
            )
            self.ground_blocks.add(block)
            self.all_sprites.add(block)
        
        # Create enemies
        for enemy_data in self.level_data.get('enemies', []):
            try:
                enemy_type_str = enemy_data.get('type', 'BASIC').upper()
                enemy_type = EnemyType[enemy_type_str]
            except (KeyError, ValueError):
                enemy_type = EnemyType.BASIC
                
            enemy = Enemy(
                enemy_data['x'], 
                enemy_data['y'], 
                enemy_type, 
                self.cell_size
            )
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)
    
    def handle_event(self, event):
        """Handle level events"""
        # Pass event to player
        self.player.handle_event(event)
        
        # Toggle debug mode
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
            self.debug = not self.debug
    
    def update(self):
        """Update level state"""
        # Calculate delta time
        dt = self.game.clock.get_time() / 1000.0  # Convert to seconds
        
        # Update player
        self.player.update(dt, self.platforms, self.ground_blocks)
        
        # Update enemies
        for enemy in self.enemies:
            enemy.update(dt, self.platforms, self.ground_blocks)
            
            # Check for player-enemy collision
            if self.player.rect.colliderect(enemy.rect):
                # Player gets hurt or game over logic would go here
                pass
        
        # Update camera to follow player
        self.camera.update(self.player.rect.centerx, self.player.rect.centery)
        
        # DO NOT check for jumps here - this was causing auto-jumping!
        # Jump handling is now done only in the player's handle_event method
    
    def render(self, screen):
        """Render the level"""
        # Fill background with sky color (avoid black flash)
        screen.fill((100, 150, 255))  # Sky blue color
        
        # Get actual screen dimensions (may be different from constants if resized)
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Calculate background placement with parallax effect
        bg_x, bg_y = self.camera.apply_parallax_bg(0, 0, self.bg_width)
        
        # Calculate how many tiles needed to cover screen width
        tiles_needed = (screen_width // self.bg_width) + 3  # Extra tile for safety
        
        # Calculate the visual offset (where the first visible tile starts)
        # For negative bg_x, we need to adjust the offset calculation
        if bg_x < 0:
            # Find appropriate starting tile index for negative offset
            # Using math.floor for correct negative number division
            import math
            tile_idx = math.floor(bg_x / self.bg_width)
            # Calculate the exact offset for the first tile
            bg_offset = bg_x - (tile_idx * self.bg_width)
        else:
            # Positive or zero bg_x is simpler
            tile_idx = 0
            bg_offset = bg_x % self.bg_width
        
        # Draw background tiles with the calculated offset, respecting level boundaries
        for i in range(tiles_needed):
            tile_x = bg_offset + ((tile_idx + i) * self.bg_width)
            
            # Get the actual level end position in screen coordinates
            level_end_screen_x, _ = self.camera.apply(self.level_width_pixels, 0)
            
            # Only draw this tile if it starts before the level's right boundary
            # For background, apply the parallax rate to determine how much of the level is visible
            max_visible_x = level_end_screen_x / self.camera.bg_scroll_rate if self.camera.bg_scroll_rate > 0 else screen_width
            
            # Only draw the tile if it would be at least partially visible on screen within level bounds
            if tile_x < max_visible_x:
                screen.blit(self.bg_image, (tile_x, bg_y))
        
        # Draw tiled foreground (similar but simpler logic since fg_x is always negative or zero)
        fg_x, fg_y = self.camera.apply(0, 0)
        
        # Calculate foreground tiling
        fg_tiles_needed = (SCREEN_WIDTH // self.fg_width) + 3  # Extra tile for safety
        
        # Same logic for foreground
        if fg_x < 0:
            import math
            fg_tile_idx = math.floor(fg_x / self.fg_width)
            fg_offset = fg_x - (fg_tile_idx * self.fg_width)
        else:
            fg_tile_idx = 0
            fg_offset = fg_x % self.fg_width
        
        # Draw foreground tiles, respecting level boundaries
        for i in range(fg_tiles_needed):
            tile_x = fg_offset + ((fg_tile_idx + i) * self.fg_width)
            
            # Get the actual level end position in screen coordinates
            level_end_screen_x, _ = self.camera.apply(self.level_width_pixels, 0)
            
            # Only draw the tile if it would be at least partially visible on screen within level bounds
            # For foreground, we can directly use the level end position
            if tile_x < level_end_screen_x:
                screen.blit(self.fg_image, (tile_x, fg_y))
        
        # Draw all sprites (position them relative to camera)
        for sprite in self.all_sprites:
            if isinstance(sprite, Player):
                # For player, use visual_rect for drawing the sprite
                sprite_screen_pos = self.camera.apply_rect(sprite.visual_rect)
                screen.blit(sprite.image, sprite_screen_pos)
            else:
                sprite_screen_pos = self.camera.apply_rect(sprite.rect)
                
                # In debug mode, show debug versions of ground blocks
                if self.debug and isinstance(sprite, GroundBlock):
                    screen.blit(sprite.debug_image, sprite_screen_pos)
                else:
                    screen.blit(sprite.image, sprite_screen_pos)
        
        # Draw debug info if enabled
        if self.debug:
            self.render_debug_info(screen)
    
    def render_debug_info(self, screen):
        """Render debug information"""
        # Draw grid
        for x in range(0, self.level_width_pixels, self.cell_size):
            screen_x, _ = self.camera.apply(x, 0)
            pygame.draw.line(screen, (50, 50, 50), (screen_x, 0), (screen_x, SCREEN_HEIGHT))
        
        for y in range(0, self.level_height_pixels, self.cell_size):
            _, screen_y = self.camera.apply(0, y)
            pygame.draw.line(screen, (50, 50, 50), (0, screen_y), (max(SCREEN_WIDTH, self.level_width_pixels - self.camera.x), screen_y))
        
        # Draw player position info
        player_cell_x = self.player.rect.centerx // self.cell_size
        player_cell_y = self.player.rect.bottom // self.cell_size
        pos_text = f"Pos: {self.player.rect.centerx}, {self.player.rect.bottom} (Cell: {player_cell_x}, {player_cell_y})"
        text_surface = self.debug_font.render(pos_text, True, WHITE)
        screen.blit(text_surface, (10, 10))
        
        # Draw player velocity and ground state
        effective_on_ground = self.player.on_ground or (self.player.ground_buffer > 0 and self.player.velocity_y >= 0)
        velocity_text = f"Velocity: ({self.player.velocity_x}, {self.player.velocity_y}) Physical Ground: {self.player.on_ground}"
        text_surface = self.debug_font.render(velocity_text, True, GREEN if self.player.on_ground else RED)
        screen.blit(text_surface, (10, 40))
        
        # Draw ground buffer state
        buffer_text = f"Ground Buffer: {self.player.ground_buffer}/{self.player.ground_buffer_max} Effective Ground: {effective_on_ground}"
        text_surface = self.debug_font.render(buffer_text, True, GREEN if effective_on_ground else RED)
        screen.blit(text_surface, (10, 70))
        
        # Draw jump state
        jump_text = f"Can Jump: {self.player.can_jump}, Jumping: {self.player.jumping}, Released: {self.player.jump_released}"
        text_surface = self.debug_font.render(jump_text, True, GREEN if self.player.can_jump else RED)
        screen.blit(text_surface, (10, 100))
        
        # Draw camera info
        camera_text = f"Camera: {self.camera.x}, {self.camera.y}"
        text_surface = self.debug_font.render(camera_text, True, WHITE)
        screen.blit(text_surface, (10, 130))
        
        # Draw FPS
        fps = self.game.clock.get_fps()
        fps_text = f"FPS: {fps:.1f}"
        text_surface = self.debug_font.render(fps_text, True, WHITE)
        screen.blit(text_surface, (10, 130))
        
        # Draw player rectangles in order of size (largest to smallest)
        
        # 1. Draw visual rect (green) - the actual sprite image bounds
        visual_screen_rect = self.camera.apply_rect(self.player.visual_rect)
        pygame.draw.rect(screen, (0, 255, 0), visual_screen_rect, 1)  # Green for visual bounds
        
        # 2. Draw collision rect (red) - narrower than visual rect, used for collisions
        collision_screen_rect = self.camera.apply_rect(self.player.rect)
        pygame.draw.rect(screen, (255, 0, 0), collision_screen_rect, 2)  # Red for collision box
        
        # 3. Draw foot rect (cyan) - used for precise ground detection
        foot_screen_rect = self.camera.apply_rect(self.player.foot_rect)
        pygame.draw.rect(screen, (0, 255, 255), foot_screen_rect, 2)  # Cyan color for foot box
        
        # 4. Draw ground sensor area (yellow) - extends slightly below feet
        ground_sensor = pygame.Rect(self.player.foot_rect)
        ground_sensor.height = 12
        ground_sensor.bottom = self.player.rect.bottom + 2
        ground_sensor_screen_rect = self.camera.apply_rect(ground_sensor)
        pygame.draw.rect(screen, (255, 255, 0), ground_sensor_screen_rect, 1)  # Yellow for ground sensor
        
        # Debug text explaining the rectangles
        rect_text = "Green: Visual | Red: Collision | Cyan: Feet | Yellow: Ground Sensor"
        text_surface = self.debug_font.render(rect_text, True, WHITE)
        screen.blit(text_surface, (10, 160))
        
        # Draw hint for F3 key
        hint_text = "F3: Toggle Debug Mode"
        text_surface = self.debug_font.render(hint_text, True, WHITE)
        screen.blit(text_surface, (SCREEN_WIDTH - text_surface.get_width() - 10, 10))

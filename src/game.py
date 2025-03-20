import pygame
import json
import os
from enum import Enum, auto

from menu import MainMenu
from level import Level
from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE

class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()

class Game:
    def __init__(self):
        # Set up the display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption(TITLE)
        
        # Set up the clock
        self.clock = pygame.time.Clock()
        
        # Game state
        self.state = GameState.MENU
        self.running = True
        self.current_level = None
        
        # Load levels list
        self.levels = self._get_available_levels()
        
        # Create main menu
        self.menu = MainMenu(self)
        
        # Set up audio
        self.init_audio()
        
    def _get_available_levels(self):
        """Find all level files in the levels directory"""
        levels = []
        levels_dir = os.path.join(os.getcwd(), 'levels')
        
        try:
            for file in os.listdir(levels_dir):
                if file.endswith('.json'):
                    level_path = os.path.join(levels_dir, file)
                    level_name = os.path.splitext(file)[0]
                    levels.append((level_name, level_path))
        except Exception as e:
            print(f"Error loading levels: {e}")
        
        return levels
    
    def init_audio(self):
        """Initialize game audio"""
        try:
            pygame.mixer.music.load(os.path.join('resources', 'audio', 'adventure_theme.mp3'))
            pygame.mixer.music.set_volume(0.05)  # Reduced to 10% of original (0.5 -> 0.05)
        except pygame.error as e:
            print(f"Warning: Could not load background music: {e}")
        
        # Jump sound
        try:
            self.jump_sound = pygame.mixer.Sound(os.path.join('resources', 'audio', 'jump.wav'))
            self.jump_sound.set_volume(0.04)  # Reduced to 10% of original (0.4 -> 0.04)
        except pygame.error as e:
            print(f"Warning: Could not load jump sound: {e}")
            # Create dummy sound object to avoid None checks
            self.jump_sound = pygame.mixer.Sound(buffer=bytearray(16))
            self.jump_sound.set_volume(0)
    
    def load_level(self, level_path):
        """Load a level from a JSON file"""
        try:
            self.current_level = Level(level_path, self)
            self.state = GameState.PLAYING
            # Start music if available
            try:
                pygame.mixer.music.play(-1)  # Loop indefinitely
            except pygame.error:
                print("Warning: Could not play background music")
        except Exception as e:
            print(f"Error loading level: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
    
    def handle_events(self):
        """Process all game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Window resize event
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                # Update camera dimensions if we're in a level
                if self.current_level and self.current_level.camera:
                    self.current_level.camera.width = event.w
                    self.current_level.camera.height = event.h
                    self.current_level.camera.screen_resized = True
                
            # Handle ESC key to exit game or return to menu
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.MENU
                    elif self.state == GameState.MENU:
                        self.running = False
                        
            # Pass events to current state handler
            if self.state == GameState.MENU:
                self.menu.handle_event(event)
            elif self.state == GameState.PLAYING and self.current_level:
                self.current_level.handle_event(event)
    
    def update(self):
        """Update game state"""
        if self.state == GameState.MENU:
            self.menu.update()
        elif self.state == GameState.PLAYING and self.current_level:
            self.current_level.update()
    
    def render(self):
        """Render the current game state"""
        # Clear the screen
        self.screen.fill((0, 0, 0))
        
        # Render current state
        if self.state == GameState.MENU:
            self.menu.render(self.screen)
        elif self.state == GameState.PLAYING and self.current_level:
            self.current_level.render(self.screen)
        
        # Flip the display
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            # Process events
            self.handle_events()
            
            # Update game state
            self.update()
            
            # Render
            self.render()
            
            # Control the game speed
            self.clock.tick(FPS)

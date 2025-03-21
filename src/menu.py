import pygame
import os
from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, BLUE, 
    MENU_TITLE_SIZE, MENU_OPTION_SIZE, MENU_PADDING
)

class MainMenu:
    def __init__(self, game):
        self.game = game
        self.selected_option = 0
        self.options = []
        self.title_font = pygame.font.SysFont(None, MENU_TITLE_SIZE)
        self.option_font = pygame.font.SysFont(None, MENU_OPTION_SIZE)
        
        # Background image
        try:
            self.bg_image = pygame.image.load(os.path.join('resources', 'graphics', 'backgrounds', 'menu_bg.png'))
            self.bg_image = pygame.transform.scale(self.bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.bg_image = None
        
        # Update level options whenever levels change
        self.update_options()
    
    def update_options(self):
        # Start with basic options
        self.options = ["Exit"]
        
        # Add level options at the beginning if levels are available
        if hasattr(self.game, 'levels') and self.game.levels:
            for level_name, _ in reversed(self.game.levels):  # Reverse to put newest on top
                self.options.insert(0, f"Play {level_name}")
        else:
            # Add a placeholder option if no levels found
            self.options.insert(0, "No levels found")
            
        # Reset selection to first option
        self.selected_option = 0
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # Navigate menu
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.options)
            # Select option
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.select_option()
    
    def select_option(self):
        selected = self.options[self.selected_option]
        
        # Handle "Exit" option
        if selected == "Exit":
            self.game.running = False
        # Handle level selection
        elif selected.startswith("Play "):
            level_name = selected[5:]  # Remove "Play " prefix
            
            # Find matching level path
            for name, path in self.game.levels:
                if name == level_name:
                    self.game.load_level(path)
                    break
    
    def update(self):
        # Check if the levels list has changed
        if len(self.options) - 1 != len(self.game.levels):  # -1 for Exit option
            self.update_options()
    
    def render(self, screen):
        # Draw background
        if self.bg_image:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill(BLACK)
        
        # Draw title
        title_text = self.title_font.render("Parallax Sidescroller", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_text, title_rect)
        
        # Draw menu options
        for i, option in enumerate(self.options):
            # Highlight selected option
            if i == self.selected_option:
                color = BLUE
                text = f"> {option} <"
            else:
                color = WHITE
                text = option
            
            option_text = self.option_font.render(text, True, color)
            option_rect = option_text.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + (i * (MENU_OPTION_SIZE + MENU_PADDING)))
            )
            screen.blit(option_text, option_rect)

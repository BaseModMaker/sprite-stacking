import pygame
from pygame import mixer, time, display, image, event, KEYUP, QUIT, K_ESCAPE, Surface
from os.path import join, exists
import asyncio
import sys
import os

# Use relative imports instead of absolute imports
from utils.text import Text
from core.entity import Entity
from controllers.player_controller import PlayerController

class Game:
    """Main game class."""
    
    def __init__(self, screen_width, screen_height, fullscreen=False, asset_path="", font_path="", image_path=""):
        """Initialize the game.
        
        Args:
            screen_width (int): Width of screen
            screen_height (int): Height of screen
            fullscreen (bool): Whether to use fullscreen mode
            asset_path (str): Path to asset directory
            font_path (str): Path to font directory
            image_path (str): Path to image directory
        """
        # Setup pygame and display
        mixer.pre_init(44100, -16, 1, 4096)
        pygame.init()
        self.clock = time.Clock()
        
        # Set display mode - never use fullscreen on web
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_fullscreen = fullscreen and not hasattr(sys, '_emscripten_info')
        
        # For debugging
        self.is_web = hasattr(sys, '_emscripten_info')
        print(f"Running on web: {self.is_web}")
        
        # Create the correct display for the platform
        flags = 0
        if self.is_fullscreen:
            flags = pygame.FULLSCREEN
            
        self.screen = display.set_mode((screen_width, screen_height), flags)
        self.caption = display.set_caption("Sprite Stacking Game")
        
        # Store paths
        self.asset_path = asset_path
        self.font_path = font_path
        self.image_path = image_path
        
        # Define colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        
        # Load background
        background_path = join(image_path, "background.jpg")
        if exists(background_path):
            try:
                self.background = image.load(background_path)
                # Convert for better performance
                self.background = self.background.convert()
                # Scale background to fit screen
                self.background = pygame.transform.scale(self.background, (screen_width, screen_height))
            except Exception as e:
                print(f"Error loading background: {e}")
                self._create_default_background()
        else:
            self._create_default_background()
        
        # Game state
        self.running = True
        self.game_started = False
        
        # Load font
        font_file = join(font_path, "blocky.ttf")
        
        # Create car entity - now just using the generic Entity with the "car" type
        car_img_path = join(image_path, "cars-1.png")
        
        # Increased car dimensions for better visibility
        car_width = 60 
        car_height = 100
        
        # For debugging
        print(f"Attempting to load car from: {car_img_path}")
        print(f"File exists: {exists(car_img_path)}")
        
        self.car = Entity(
            x=screen_width // 2,  # x position (center)
            y=screen_height - 150,  # y position (near bottom)
            image_path=car_img_path,
            num_layers=14,
            layer_offset=1,
            width=car_width,
            height=car_height,
            entity_type="car"
        )
        
        # Create and assign a player controller to the car
        self.car_controller = PlayerController()
        self.car.set_controller(self.car_controller)
        
        # Setup text and UI elements - with proper positioning for different screen sizes
        try:
            text_x = screen_width // 2 - 150
            text_y = screen_height // 4
            start_x = screen_width // 2 - 120
            start_y = screen_height // 3
            
            if exists(font_file):
                print(f"Font file found: {font_file}")
                self.font = pygame.font.Font(font_file, 36)
                self.small_font = pygame.font.Font(font_file, 24)
                self.title_text = Text(font_file, 50, "Sprite Stacking Demo", self.WHITE, text_x, text_y)
                self.start_text = Text(font_file, 25, "Press any key to drive", self.WHITE, start_x, start_y)
            else:
                print(f"Font file not found, using system font")
                raise FileNotFoundError("Font file not found")
        except Exception as e:
            print(f"Error loading fonts: {e}")
            # Create fallback text using system font
            self.font = pygame.font.SysFont(None, 36)
            self.small_font = pygame.font.SysFont(None, 24)
            self.title_text = Text(None, 50, "Sprite Stacking Demo", self.WHITE, text_x, text_y)
            self.start_text = Text(None, 25, "Press any key to drive", self.WHITE, start_x, start_y)

    def _create_default_background(self):
        """Create a default background when image can't be loaded."""
        self.background = Surface((self.screen_width, self.screen_height))
        self.background.fill((100, 180, 100))  # Green field
        
        # Draw a simple road
        pygame.draw.rect(self.background, (80, 80, 80), (self.screen_width // 2 - 200, 0, 400, self.screen_height))  # Road
        pygame.draw.rect(self.background, (255, 255, 255), (self.screen_width // 2 - 10, 0, 20, self.screen_height), 0)  # Center line
    
    def handle_events(self):
        """Process input events."""
        self.keys = pygame.key.get_pressed()
        
        for e in event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                self.running = False
            
            # Start game on key press
            if not self.game_started and e.type == KEYUP:
                self.game_started = True
    
    def update(self):
        """Update game state."""
        if self.game_started:
            # Update the car entity
            self.car.update(self.keys)
            
            # Keep car within screen bounds
            self.car.keep_in_bounds(self.screen_width, self.screen_height)
    
    def draw(self):
        """Draw everything to the screen."""
        # Draw background
        self.screen.blit(self.background, (0, 0))
        
        if not self.game_started:
            # Draw menu screen
            self.title_text.draw(self.screen)
            self.start_text.draw(self.screen)
        else:
            # Draw the car entity
            self.car.draw(self.screen)
        
        # Update the display
        display.update()
    
    async def main(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
            await asyncio.sleep(0)
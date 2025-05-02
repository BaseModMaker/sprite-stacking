import pygame
from pygame import mixer, time, display, image, event, KEYUP, QUIT, K_ESCAPE, Surface
from os.path import join, exists, basename
import asyncio
import platform
import os
import sys

# Use relative imports instead of absolute imports
from utils.text import Text
from core.entity import Entity
from controllers.player_controller import PlayerController

class Game:
    """Main game class."""
    
    def __init__(self, screen_width, screen_height, fullscreen=True, asset_path="", font_path="", image_path="", preloaded_assets=None):
        """Initialize the game.
        
        Args:
            screen_width (int): Width of screen
            screen_height (int): Height of screen
            fullscreen (bool): Whether to use fullscreen mode
            asset_path (str): Path to asset directory
            font_path (str): Path to font directory
            image_path (str): Path to image directory
            preloaded_assets (dict): Dictionary of preloaded assets
        """
        # Store preloaded assets
        self.preloaded_assets = preloaded_assets or {}
        
        # Setup pygame and display
        try:
            mixer.pre_init(44100, -16, 1, 4096)
        except Exception as e:
            print(f"Mixer pre-init error (non-critical): {e}")
            
        pygame.init()
        self.clock = time.Clock()
        
        # Set display mode
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_fullscreen = fullscreen
        
        # Always use windowed mode for web compatibility
        if platform.system() == "Emscripten":
            self.is_fullscreen = False
            
        if self.is_fullscreen:
            self.screen = display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
        else:
            self.screen = display.set_mode((screen_width, screen_height))
            
        self.caption = display.set_caption("Sprite Stacking Game")
        
        # Store paths
        self.asset_path = asset_path
        self.font_path = font_path
        self.image_path = image_path
        
        # Debug info
        print(f"Asset path: {asset_path}")
        print(f"Image path: {image_path}")
        print(f"Font path: {font_path}")
        print(f"Preloaded assets: {list(self.preloaded_assets.keys())}")
        
        # Define colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        
        # Create a default background
        self.background = Surface((screen_width, screen_height))
        self.background.fill((100, 180, 100))  # Green field
        
        # Draw a simple road
        pygame.draw.rect(self.background, (80, 80, 80), 
                        (screen_width // 2 - 200, 0, 400, screen_height))  # Road
        pygame.draw.rect(self.background, (255, 255, 255), 
                        (screen_width // 2 - 10, 0, 20, screen_height), 0)  # Center line
        
        # Try to load background image if available
        try:
            bg_filename = "background.jpg"
            # First check preloaded assets
            if bg_filename in self.preloaded_assets:
                print(f"Using preloaded background: {bg_filename}")
                bg_img = self.preloaded_assets[bg_filename]
                self.background = pygame.transform.scale(bg_img, (screen_width, screen_height))
            else:
                # Try to load from file
                background_path = join(image_path, bg_filename)
                if exists(background_path):
                    print(f"Loading background from file: {background_path}")
                    self.background = image.load(background_path).convert()
                    # Scale background to fit screen
                    self.background = pygame.transform.scale(self.background, (screen_width, screen_height))
                    print(f"Successfully loaded background from {background_path}")
        except Exception as e:
            print(f"Error loading background: {e}")
        
        # Game state
        self.running = True
        self.game_started = False
        
        # Car creation with better error handling
        try:
            # Create car entity - using the generic Entity with the "car" type
            car_filename = "cars-1.png"
            car_img_path = None
            car_img = None
            
            # First check if we have this asset preloaded
            if car_filename in self.preloaded_assets:
                print(f"Using preloaded car image: {car_filename}")
                car_img = self.preloaded_assets[car_filename]
                car_img_path = f"{image_path}/{car_filename}"  # Create a path for reference
            else:
                # Try to load from file path
                car_img_path = join(image_path, car_filename)
                print(f"Attempting to load car image from: {car_img_path}")
            
            # Increased car dimensions for better visibility
            car_width = 60 
            car_height = 100
            
            self.car = Entity(
                x=screen_width // 2,  # x position (center)
                y=screen_height - 150,  # y position (near bottom)
                image_path=car_img_path,
                num_layers=14,
                layer_offset=1,
                width=car_width,
                height=car_height,
                entity_type="car",
                preloaded_image=car_img
            )
            
            # Create and assign a player controller to the car
            self.car_controller = PlayerController()
            self.car.set_controller(self.car_controller)
            
            print("Car entity created successfully")
        except Exception as e:
            print(f"Error creating car: {e}")
            # Create a backup car with no image if loading fails
            self.car = Entity(
                x=screen_width // 2,
                y=screen_height - 150,
                image_path=None,
                num_layers=14,
                layer_offset=1,
                width=60,
                height=100,
                entity_type="car"
            )
            self.car_controller = PlayerController()
            self.car.set_controller(self.car_controller)
        
        # Setup text and UI elements with better error handling
        try:
            font_file = join(font_path, "blocky.ttf")
            print(f"Attempting to load font from: {font_file}")
            
            if exists(font_file):
                self.font = pygame.font.Font(font_file, 36)
                self.small_font = pygame.font.Font(font_file, 24)
                self.title_text = Text(font_file, 50, "Sprite Stacking Demo", self.WHITE, screen_width // 2 - 200, screen_height // 4)
                self.start_text = Text(font_file, 25, "Press any key to drive", self.WHITE, screen_width // 2 - 150, screen_height // 3)
                print(f"Font loaded successfully from: {font_file}")
            else:
                raise FileNotFoundError(f"Font file not found: {font_file}")
                
        except Exception as e:
            print(f"Error loading font: {e}")
            # Create fallback text using system font
            pygame.font.init()
            self.font = pygame.font.SysFont(None, 36)
            self.title_text = Text(None, 50, "Sprite Stacking Demo", self.WHITE, screen_width // 2 - 200, screen_height // 4)
            self.start_text = Text(None, 25, "Press any key to drive", self.WHITE, screen_width // 2 - 150, screen_height // 3)
    
    def handle_events(self):
        """Process input events."""
        self.keys = pygame.key.get_pressed()
        
        for e in event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                self.running = False
            
            # Start game on key press
            if not self.game_started and e.type == KEYUP:
                self.game_started = True
                print("Game started by user input")
    
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
        print("Starting main game loop")
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
            await asyncio.sleep(0)
        
        print("Game loop ended")
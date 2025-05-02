import pygame
from pygame import mixer, time, display, image, event, KEYUP, QUIT, K_ESCAPE, Surface
from os.path import join, exists
import asyncio

# Use relative imports instead of absolute imports
from utils.text import Text
from core.entity import Entity
from controllers.player_controller import PlayerController

class Game:
    """Main game class."""
    
    def __init__(self, screen_width, screen_height, fullscreen=True, asset_path="", font_path="", image_path=""):
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
        
        # Set display mode
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_fullscreen = fullscreen
        
        if self.is_fullscreen:
            self.screen = display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
        else:
            self.screen = display.set_mode((screen_width, screen_height))
            
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
            self.background = image.load(background_path).convert()
            # Scale background to fit screen
            self.background = pygame.transform.scale(self.background, (screen_width, screen_height))
        else:
            # Create a default background if image doesn't exist
            self.background = Surface((screen_width, screen_height))
            self.background.fill((100, 180, 100))  # Green field
            
            # Draw a simple road
            pygame.draw.rect(self.background, (80, 80, 80), (screen_width // 2 - 200, 0, 400, screen_height))  # Road
            pygame.draw.rect(self.background, (255, 255, 255), (screen_width // 2 - 10, 0, 20, screen_height), 0)  # Center line
        
        # Game state
        self.running = True
        self.game_started = False
        
        # Load font
        font_file = join(font_path, "blocky.ttf")
        
        # Create car entity - now just using the generic Entity with the "car" type
        car_img_path = join(image_path, "cars-1.png")
        print(f"Loading car from: {car_img_path}")
        self.car = Entity(
            x=screen_width // 2,  # x position (center)
            y=screen_height - 150,  # y position (near bottom)
            image_path=car_img_path,
            num_layers=14,
            layer_offset=1,
            width=15,
            height=31,
            entity_type="car"
        )
        # Check if image loaded correctly - debug output
        print(f"Car sprite stack has {len(self.car.sprite_stack.layers)} layers")
        print(f"Car dimensions: {self.car.width}x{self.car.height}")
        
        # Create and assign a player controller to the car
        self.car_controller = PlayerController()
        self.car.set_controller(self.car_controller)
        
        # Setup text and UI elements
        try:
            self.font = pygame.font.Font(font_file, 36)
            self.small_font = pygame.font.Font(font_file, 24)
            self.title_text = Text(font_file, 50, "Sprite Stacking Demo", self.WHITE, screen_width // 2 - 200, screen_height // 4)
            self.start_text = Text(font_file, 25, "Press any key to drive", self.WHITE, screen_width // 2 - 150, screen_height // 3)
        except Exception as e:
            print(f"Error loading fonts: {e}")
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
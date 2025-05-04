import pygame
from pygame import mixer, time, display, image, event, KEYUP, QUIT, K_ESCAPE, Surface
from os.path import join, exists
import asyncio
import sys
import os
import random
import math

# Use relative imports instead of absolute imports
from utils.text import Text
from core.entity import Entity
from core.gameobject import GameObject
from controllers.player_controller import PlayerController
from core.sun import Sun
from core.shadow import ShadowManager
from core.camera import Camera

class Game:
    """Main game class."""
    
    def __init__(self, screen_width, screen_height, fullscreen=False, asset_path="", font_path="", image_path="", performance_mode=0):
        """Initialize the game.
        
        Args:
            screen_width (int): Width of screen
            screen_height (int): Height of screen
            fullscreen (bool): Whether to use fullscreen mode
            asset_path (str): Path to asset directory
            font_path (str): Path to font directory
            image_path (str): Path to image directory
            performance_mode (int): Ignored - always uses most optimized setting
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
        
        # Setup camera
        self.camera = Camera(screen_width, screen_height)
        
        # Store paths
        self.asset_path = asset_path
        self.font_path = font_path
        self.image_path = image_path
        
        # Define colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.YELLOW = (255, 255, 0)  # Color for sun visualization
        
        # Always use most optimized performance mode (0)
        self.performance_mode = 0
        
        # Initialize sun and shadow management
        self.sun = Sun(horizontal_angle=45, vertical_angle=45)
        self.shadow_manager = ShadowManager(enabled=True)
        
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
        
        # Create player entity - now just using the generic Entity with the "car" type
        car_img_path = join(image_path, "cars-1.png")
        
        # Increased car dimensions for better visibility
        car_width = 60 
        car_height = 100
        
        # For debugging
        print(f"Attempting to load car from: {car_img_path}")
        print(f"File exists: {exists(car_img_path)}")
        
        self.player = Entity(
            x=0,  # Start at origin for infinite world
            y=0,  # Start at origin for infinite world
            image_path=join(image_path, "paras.png"),
            num_layers=44, # 64 60 44
            layer_offset=1,
            width=64,
            height=60,
            entity_type="car",
            outline_enabled=True,
            outline_color=(0, 0, 0),
            outline_thickness=1,
            individual_offset=0.38,
        )
        
        # Register player with shadow manager
        self.shadow_manager.register_object(self.player)
        
        # Create and assign a player controller to the player
        self.player_controller = PlayerController()
        self.player.set_controller(self.player_controller)
        
        # Create tree objects across the infinite world
        self._create_world_objects(image_path)
        
        # Apply initial shadow settings to all objects
        self.shadow_manager.update_all(self.sun)
        
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
                self.start_text = Text(font_file, 25, "Press any key to explore", self.WHITE, start_x, start_y)
            else:
                print(f"Font file not found, using system font")
                raise FileNotFoundError("Font file not found")
        except Exception as e:
            print(f"Error loading fonts: {e}")
            # Create fallback text using system font
            self.font = pygame.font.SysFont(None, 36)
            self.small_font = pygame.font.SysFont(None, 24)
            self.title_text = Text(None, 50, "Sprite Stacking Demo", self.WHITE, text_x, text_y)
            self.start_text = Text(None, 25, "Press any key to explore", self.WHITE, start_x, start_y)

    def _create_world_objects(self, image_path):
        """Create objects throughout the infinite world."""
        tree_img_path = join(image_path, "tree.png")
        self.world_objects = []
        
        # Create trees in a grid pattern around the origin
        # This will give the illusion of an infinite world as we dynamically load more
        grid_size = 2000  # Size of the initial grid area
        num_trees = 50   # Number of trees to create in the initial area
        tree_width = 18
        tree_height = 18
        
        # Generate trees at random positions in the grid
        for _ in range(num_trees):
            # Random position within the grid
            x = random.randint(-grid_size//2, grid_size//2)
            y = random.randint(-grid_size//2, grid_size//2)
            
            # Create tree and add to list
            tree = GameObject(
                x=x,
                y=y,
                image_path=tree_img_path,
                num_layers=36,
                layer_offset=1,
                width=tree_width,
                height=tree_height,
                outline_enabled=True,
            )
            
            # Add tree to list
            self.world_objects.append(tree)
        
        # Register all trees with shadow manager
        self.shadow_manager.register_objects(self.world_objects)
        
    def _generate_world_chunk(self, center_x, center_y, size=2000, num_objects=20):
        """Generate a new chunk of the world as the player explores.
        
        Args:
            center_x (int): X coordinate of the chunk center
            center_y (int): Y coordinate of the chunk center
            size (int): Size of the chunk
            num_objects (int): Number of objects to place in the chunk
        """
        tree_img_path = join(self.image_path, "tree.png")
        tree_width = 18
        tree_height = 18
        
        new_objects = []
        
        # Calculate chunk boundaries
        min_x = center_x - size//2
        max_x = center_x + size//2
        min_y = center_y - size//2
        max_y = center_y + size//2
        
        # Generate objects in this chunk
        for _ in range(num_objects):
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)
            
            # Create tree and add to list
            tree = GameObject(
                x=x,
                y=y,
                image_path=tree_img_path,
                num_layers=36,
                layer_offset=1,
                width=tree_width,
                height=tree_height,
                outline_enabled=True,
            )
            
            # Add tree to list
            new_objects.append(tree)
            self.world_objects.append(tree)
            
        # Register new objects with shadow manager
        self.shadow_manager.register_objects(new_objects)
        return new_objects
        
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
                
            # Handle shadow control keys when game is started
            if self.game_started and e.type == KEYUP:
                # Adjust horizontal angle using Q and D (European layout)
                # Fixed direction: Q = increase angle (clockwise), D = decrease angle (counter-clockwise)
                if e.key == pygame.K_q:
                    self.sun.adjust_horizontal_angle(10)
                    self.shadow_manager.update_all(self.sun)
                elif e.key == pygame.K_d:
                    self.sun.adjust_horizontal_angle(-10)
                    self.shadow_manager.update_all(self.sun)
                # Adjust vertical angle using Z and S (European layout)
                # Fixed direction: Z = increase angle (sun higher), S = decrease angle (sun lower)
                elif e.key == pygame.K_z:
                    self.sun.adjust_vertical_angle(10)
                    self.shadow_manager.update_all(self.sun)
                elif e.key == pygame.K_s:
                    self.sun.adjust_vertical_angle(-10)
                    self.shadow_manager.update_all(self.sun)
                # Toggle sun debug display
                elif e.key == pygame.K_v:
                    self.sun.toggle_debug()
                    print(f"Sun debug: {'on' if self.sun.debug_enabled else 'off'}")
                # Toggle shadows on/off
                elif e.key == pygame.K_x:
                    enabled = self.shadow_manager.toggle_shadows()
                    print(f"Shadows: {'enabled' if enabled else 'disabled'}")
                    self.shadow_manager.update_all(self.sun)
                # Cycle performance modes
                elif e.key == pygame.K_p:
                    self.performance_mode = 0  # Always use most optimized performance mode
                    print("Performance mode: High (best quality)")
    
    def update(self):
        """Update game state."""
        if self.game_started:
            # Update the player entity
            self.player.update(self.keys)
            
            # Update camera to follow player
            self.camera.follow(self.player.x, self.player.y)
            
            # Check if we need to generate new world chunks
            player_chunk_x = int(self.player.x // 2000) * 2000
            player_chunk_y = int(self.player.y // 2000) * 2000
            
            # Store last chunk center to check if we've moved to a new chunk
            if not hasattr(self, 'last_chunk_center'):
                self.last_chunk_center = (player_chunk_x, player_chunk_y)
                
            # If we've moved to a new chunk, generate new content
            if (player_chunk_x, player_chunk_y) != self.last_chunk_center:
                self._generate_world_chunk(player_chunk_x, player_chunk_y)
                self.last_chunk_center = (player_chunk_x, player_chunk_y)
                print(f"Generated new chunk at {player_chunk_x}, {player_chunk_y}")
    
    def draw(self):
        """Draw everything to the screen."""
        # Clear camera surface
        camera_surface = self.camera.get_surface()
        camera_surface.fill((100, 180, 100))  # Green field background
        
        # Draw grid lines to show movement
        self._draw_world_grid(camera_surface)
        
        if not self.game_started:
            # Draw menu screen directly to main screen
            self.screen.blit(self.background, (0, 0))
            self.title_text.draw(self.screen)
            self.start_text.draw(self.screen)
        else:
            # Draw world objects with camera offset
            visible_objects = self._get_visible_objects()
            
            for obj in visible_objects:
                # Convert world coordinates to screen coordinates
                screen_x, screen_y = self.camera.world_to_screen(obj.x, obj.y)
                obj.draw_at_position(camera_surface, screen_x, screen_y, draw_shadow=self.shadow_manager.enabled, performance_mode=self.performance_mode)
            
            # Draw the player at the center of the screen
            center_x = self.camera.width // 2
            center_y = self.camera.height // 2
            self.player.draw_at_position(camera_surface, center_x, center_y, draw_shadow=self.shadow_manager.enabled, performance_mode=self.performance_mode)
            
            # Draw shadow configuration help text and sun
            self.sun.draw_debug_info(camera_surface, self.small_font, self.WHITE)
            
            # Draw sun visualization if debug is enabled
            if self.sun.debug_enabled:
                self.sun.draw(camera_surface, self.camera.width, self.camera.height)
                
            # Draw player coordinates for debugging
            coord_text = f"Position: ({int(self.player.x)}, {int(self.player.y)})"
            coord_surface = self.small_font.render(coord_text, True, self.WHITE)
            camera_surface.blit(coord_surface, (10, self.camera.height - 30))
            
            # Apply camera view to screen
            self.camera.apply_to_screen(self.screen)
        
        # Update the display
        display.update()
    
    def _draw_world_grid(self, surface):
        """Draw a grid to help visualize the infinite world.
        
        Args:
            surface: Surface to draw on
        """
        # Calculate grid lines based on camera position
        grid_size = 200  # Distance between grid lines
        grid_color = (80, 120, 80)  # Light green grid lines
        
        # Calculate the range of grid lines to draw
        half_width = self.camera.width // 2
        half_height = self.camera.height // 2
        
        # Calculate the offset from grid alignment
        offset_x = self.camera.x % grid_size
        offset_y = self.camera.y % grid_size
        
        # Draw vertical grid lines
        for x in range(-half_width - int(offset_x), half_width - int(offset_x) + grid_size, grid_size):
            screen_x = x + half_width
            pygame.draw.line(surface, grid_color, (screen_x, 0), (screen_x, self.camera.height), 1)
            
        # Draw horizontal grid lines
        for y in range(-half_height - int(offset_y), half_height - int(offset_y) + grid_size, grid_size):
            screen_y = y + half_height
            pygame.draw.line(surface, grid_color, (0, screen_y), (self.camera.width, screen_y), 1)
    
    def _get_visible_objects(self):
        """Get only objects that are currently visible on the screen.
        
        Returns:
            list: List of visible game objects
        """
        visible_objects = []
        
        # Calculate the screen bounds in world coordinates
        cam_left = self.camera.x - self.camera.width // 2 - 100  # Add margin
        cam_right = self.camera.x + self.camera.width // 2 + 100
        cam_top = self.camera.y - self.camera.height // 2 - 100
        cam_bottom = self.camera.y + self.camera.height // 2 + 100
        
        # Filter objects to only include those in view
        for obj in self.world_objects:
            if (cam_left <= obj.x <= cam_right and cam_top <= obj.y <= cam_bottom):
                visible_objects.append(obj)
                
        return visible_objects
    
    async def main(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
            await asyncio.sleep(0)
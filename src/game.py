import pygame
from pygame import mixer, time, display, image, event, KEYUP, QUIT, K_ESCAPE, Surface, mouse
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
    """Main game class for Abyssal Gears: Depths of Iron and Steam."""
    
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
        self.caption = display.set_caption("Abyssal Gears: Depths of Iron and Steam")
        
        # Setup camera
        self.camera = Camera(screen_width, screen_height)
        
        # Store paths
        self.asset_path = asset_path
        self.font_path = font_path
        self.image_path = image_path
          # Define colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        
        # Always use most optimized performance mode (0)
        self.performance_mode = 0
        
        # Initialize sun and shadow management with fixed settings
        self.sun = Sun(horizontal_angle=135, vertical_angle=45)  # Fixed sun position
        self.shadow_manager = ShadowManager(enabled=True)  # Shadows always enabled
        
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
        
        # Create player submarine entity
        submarine_img_path = join(image_path, "yellow-submarine.png")
        self.player = Entity(
            x=0,
            y=0,
            image_path=submarine_img_path,
            num_layers=24,  # yellow-submarine.png is 32x16x24
            layer_offset=1,
            width=32,
            height=16,
            entity_type="submarine",
            outline_enabled=True,
            outline_color=(0, 0, 0),
            outline_thickness=1,
            individual_offset=0.75,
            rotation=270,  # Facing up
        )
        self.shadow_manager.register_object(self.player)
          # Create and assign a player controller to the player
        self.player_controller = PlayerController()
        self.player.set_controller(self.player_controller)
        
        # Remove car/tree/road logic and create dungeon objects
        self._create_dungeon_objects(image_path)
        
        # Apply initial shadow settings to all objects
        self.shadow_manager.update_all(self.sun)
        
        # Setup text and UI elements - with proper positioning for different screen sizes
        try:
            text_x = screen_width // 2 - 200
            text_y = screen_height // 4
            start_x = screen_width // 2 - 150
            start_y = screen_height // 3
            
            if exists(font_file):
                print(f"Font file found: {font_file}")
                self.font = pygame.font.Font(font_file, 36)
                self.small_font = pygame.font.Font(font_file, 24)
                self.title_text = Text(font_file, 50, "Abyssal Gears: Depths of Iron and Steam", self.WHITE, text_x, text_y)
                self.start_text = Text(font_file, 25, "Press any key to dive into the depths", self.WHITE, start_x, start_y)
            else:
                print(f"Font file not found, using system font")
                raise FileNotFoundError("Font file not found")
        except Exception as e:
            print(f"Error loading fonts: {e}")            # Create fallback text using system font
            self.font = pygame.font.SysFont(None, 36)
            self.small_font = pygame.font.SysFont(None, 24)
            self.title_text = Text(None, 50, "Abyssal Gears: Depths of Iron and Steam", self.WHITE, text_x, text_y)
            self.start_text = Text(None, 25, "Press any key to dive into the depths", self.WHITE, start_x, start_y)

    def _create_dungeon_objects(self, image_path):
        """Create an underwater cave environment with walls and kelp."""
        self.world_objects = []
        self.wall_objects = []  # Separate list for wall objects to handle collisions
        
        # Cave dimensions
        self.cave_width = 1200
        self.cave_height = 1200
        self.wall_thickness = 80
        
        # Use kelp image for underwater vegetation
        kelp_img_path = join(image_path, "kelp.png")
        tree_img_path = join(image_path, "tree.png")  # We'll use the tree image for walls
        
        # Create cave walls (using tree.png as a placeholder for wall texture)
        self._create_cave_walls(tree_img_path)
        
        # Add kelp inside the cave
        num_kelp = 40
        for _ in range(num_kelp):
            # Place kelp only within the cave boundaries
            x = random.randint(-self.cave_width//2 + self.wall_thickness, 
                              self.cave_width//2 - self.wall_thickness)
            y = random.randint(-self.cave_height//2 + self.wall_thickness, 
                              self.cave_height//2 - self.wall_thickness)
            
            kelp = GameObject(
                x=x,
                y=y,
                image_path=kelp_img_path,
                num_layers=24,  # kelp.png is 11x8x24
                layer_offset=1,
                width=11,
                height=8,
                outline_enabled=False,  # No outline for natural objects
            )
            self.world_objects.append(kelp)
        
        # Register all objects with the shadow manager
        self.shadow_manager.register_objects(self.world_objects)
        self.shadow_manager.register_objects(self.wall_objects)
        
    def _create_cave_walls(self, wall_img_path):
        """Create the walls that form the underwater cave boundary."""
        wall_spacing = 60  # Spacing between wall segments
        
        # Create top and bottom walls
        for x in range(-self.cave_width//2, self.cave_width//2, wall_spacing):
            # Top wall
            self._add_wall_segment(x, -self.cave_height//2, wall_img_path)
            # Bottom wall
            self._add_wall_segment(x, self.cave_height//2, wall_img_path)
            
        # Create left and right walls
        for y in range(-self.cave_height//2, self.cave_height//2, wall_spacing):
            # Left wall
            self._add_wall_segment(-self.cave_width//2, y, wall_img_path)
            # Right wall
            self._add_wall_segment(self.cave_width//2, y, wall_img_path)
    def _add_wall_segment(self, x, y, img_path):
        """Add a single wall segment at the specified position."""
        wall = GameObject(
            x=x,
            y=y,
            image_path=img_path,
            num_layers=24,
            layer_offset=1,
            width=60,
            height=60,
            outline_enabled=False,
        )
        self.wall_objects.append(wall)
        self.world_objects.append(wall)  # Also add to main objects list for rendering

    def _create_default_background(self):
        """Create a deep ocean water background."""
        self.background = Surface((self.screen_width, self.screen_height))
        
        # Create a gradient from dark blue (bottom) to slightly lighter blue (top)
        for y in range(self.screen_height):
            # Calculate gradient color - darker at the bottom, lighter at the top
            depth_factor = y / self.screen_height
            blue = 40 + int(40 * (1 - depth_factor))  # 40-80 range
            green = 65 + int(15 * (1 - depth_factor))  # 65-80 range
            
            # Draw a horizontal line with the calculated color
            pygame.draw.line(
                self.background,
                (10, green, blue),
                (0, y),
                (self.screen_width, y)
            )
        
        # Add some random bubbles for an underwater effect
        for _ in range(50):
            x = random.randint(0, self.screen_width)
            y = random.randint(0, self.screen_height)
            radius = random.randint(1, 5)
            alpha = random.randint(40, 120)
            
            # Create a surface for the semi-transparent bubble
            bubble_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(
                bubble_surface,
                (255, 255, 255, alpha),
                (radius, radius),
                radius
            )
            self.background.blit(bubble_surface, (x, y))
            
        # Add some light rays from the surface
        for _ in range(10):
            start_x = random.randint(0, self.screen_width)
            width = random.randint(20, 80)
            
            # Create a surface for the semi-transparent light ray
            ray_surface = pygame.Surface((width, self.screen_height), pygame.SRCALPHA)
            
            # Fill with a gradient
            for ray_y in range(self.screen_height):
                depth_factor = ray_y / self.screen_height
                alpha = int(25 * (1 - depth_factor))  # Fade out as it goes deeper
                pygame.draw.line(
                    ray_surface,
                    (255, 255, 220, alpha),
                    (width//2, ray_y),
                    (width//2, ray_y)
                )
                
            self.background.blit(ray_surface, (start_x, 0))
            
    def handle_events(self):
        """Process input events."""
        self.keys = pygame.key.get_pressed()
        
        for e in event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                self.running = False
            
            # Start game on key press
            if not self.game_started and e.type == KEYUP:
                self.game_started = True
                
            # Game started key handling
            if self.game_started and e.type == KEYUP:                # Cycle performance modes
                if e.key == pygame.K_p:
                    self.performance_mode = 0  # Always use most optimized performance mode
                    print("Performance mode: High (best quality)")
    
    def update(self):
        """Update game state."""
        if self.game_started:
            # Update the player entity
            self.player.update(self.keys)
            
            # Keep the player within the cave boundaries
            self._keep_player_in_cave()
            
            # Check for arrow key inputs to rotate camera around the submarine
            camera_rotation_speed = 2  # Degrees per frame, adjust for faster/slower rotation
            if self.keys[pygame.K_LEFT]:
                self.camera.set_rotation((self.camera.rotation - camera_rotation_speed) % 360)
            if self.keys[pygame.K_RIGHT]:
                self.camera.set_rotation((self.camera.rotation + camera_rotation_speed) % 360)
            
            # Update camera to follow player
            self.camera.follow(self.player.x, self.player.y)
    
    def _keep_player_in_cave(self):
        """Keep the player within the cave boundaries."""
        # Calculate the boundaries with a buffer to prevent going through walls
        buffer = 30  # Buffer space to prevent getting too close to walls
        min_x = -self.cave_width // 2 + self.wall_thickness + buffer
        max_x = self.cave_width // 2 - self.wall_thickness - buffer
        min_y = -self.cave_height // 2 + self.wall_thickness + buffer
        max_y = self.cave_height // 2 - self.wall_thickness - buffer
        
        # Constrain player position
        self.player.x = max(min_x, min(self.player.x, max_x))
        self.player.y = max(min_y, min(self.player.y, max_y))
    
    def draw(self):
        """Draw everything to the screen."""
        # Clear camera surface with deep blue underwater color
        camera_surface = self.camera.get_surface()
        
        # Create a deep blue gradient background
        for y in range(self.camera.height):
            # Calculate gradient color - darker at the bottom, lighter at the top
            depth_factor = y / self.camera.height
            blue = 40 + int(40 * (1 - depth_factor))  # 40-80 range
            green = 65 + int(15 * (1 - depth_factor))  # 65-80 range
            
            # Draw a horizontal line with the calculated color
            pygame.draw.line(
                camera_surface,
                (10, green, blue),
                (0, y),
                (self.camera.width, y)
            )
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
                # Apply camera rotation to world objects too
                # For objects without their own rotation, we use the camera rotation directly
                obj_rotation = self.camera.rotation
                if hasattr(obj, 'rotation'):
                    obj_rotation = (obj.rotation + self.camera.rotation) % 360
                
                obj.draw_at_position(
                    camera_surface, 
                    screen_x, 
                    screen_y, 
                    draw_shadow=self.shadow_manager.enabled, 
                    performance_mode=self.performance_mode,
                    rotation=obj_rotation
                )
            
            # Draw the player at the center of the screen
            center_x = self.camera.width // 2
            center_y = self.camera.height // 2
            
            # Apply camera rotation to the player's rotation when drawing
            # To make submarine rotate with camera, we add the camera rotation to the player's rotation
            combined_rotation = (self.player.rotation + self.camera.rotation) % 360
            self.player.draw_at_position(
                camera_surface, 
                center_x, 
                center_y, 
                draw_shadow=self.shadow_manager.enabled, 
                performance_mode=self.performance_mode,
                rotation=combined_rotation
            )
            combined_rotation = (self.player.rotation + self.camera.rotation) % 360
            self.player.draw_at_position(
                camera_surface, 
                center_x, 
                center_y, 
                draw_shadow=self.shadow_manager.enabled, 
                performance_mode=self.performance_mode,
                rotation=combined_rotation
            )
            # To make submarine rotate with camera, we add the camera rotation to the player's rotation
            combined_rotation = (self.player.rotation + self.camera.rotation) % 360
            self.player.draw_at_position(
                camera_surface, 
                center_x, 
                center_y, 
                draw_shadow=self.shadow_manager.enabled, 
                performance_mode=self.performance_mode,
                rotation=combined_rotation
            )
            
            # Draw stamina bar
            if hasattr(self.player_controller, 'stamina') and hasattr(self.player_controller, 'max_stamina'):
                stamina_width = 200
                stamina_height = 15
                stamina_x = self.camera.width - stamina_width - 20
                stamina_y = self.camera.height - stamina_height - 20
                
                # Draw background
                pygame.draw.rect(camera_surface, (50, 50, 50), 
                                (stamina_x, stamina_y, stamina_width, stamina_height))
                
                # Draw current stamina
                current_width = int((self.player_controller.stamina / self.player_controller.max_stamina) * stamina_width)
                if self.player_controller.boost_active:
                    # Green when boosting
                    stamina_color = (0, 255, 0)
                elif self.player_controller.stamina < self.player_controller.max_stamina * 0.3:
                    # Red when low
                    stamina_color = (255, 50, 50)
                else:
                    # Blue normally
                    stamina_color = (50, 150, 255)
                    
                pygame.draw.rect(camera_surface, stamina_color, 
                                (stamina_x, stamina_y, current_width, stamina_height))
                
                # Draw border
                pygame.draw.rect(camera_surface, (200, 200, 200), 
                                (stamina_x, stamina_y, stamina_width, stamina_height), 1)
                
                # Label
                stamina_label = self.small_font.render("STAMINA", True, (255, 255, 255))
                camera_surface.blit(stamina_label, (stamina_x, stamina_y - 25))
            
            # Apply camera view to screen
            self.camera.apply_to_screen(self.screen)
        
        # Update the display
        display.update()
    
    def _draw_world_grid(self, surface):
        """Draw subtle underwater grid lines to help with depth perception."""
        # Calculate grid lines based on camera position
        grid_size = 200  # Distance between grid lines
        grid_color = (40, 70, 90, 100)  # Subtle underwater grid color with transparency
        
        # Calculate the range of grid lines to draw
        half_width = self.camera.width // 2
        half_height = self.camera.height // 2
        
        # Calculate the offset from grid alignment
        offset_x = self.camera.x % grid_size
        offset_y = self.camera.y % grid_size
        
        # Create a surface with alpha for semi-transparent grid lines
        grid_surface = pygame.Surface((self.camera.width, self.camera.height), pygame.SRCALPHA)
        
        # Draw vertical grid lines
        for x in range(-half_width - int(offset_x), half_width - int(offset_x) + grid_size, grid_size):
            screen_x = x + half_width
            pygame.draw.line(grid_surface, grid_color, (screen_x, 0), (screen_x, self.camera.height), 1)
            
        # Draw horizontal grid lines
        for y in range(-half_height - int(offset_y), half_height - int(offset_y) + grid_size, grid_size):
            screen_y = y + half_height
            pygame.draw.line(grid_surface, grid_color, (0, screen_y), (self.camera.width, screen_y), 1)
        
        # Apply the grid surface
        surface.blit(grid_surface, (0, 0))
    
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
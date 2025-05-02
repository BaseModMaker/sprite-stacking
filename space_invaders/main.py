from pygame import (
    sprite,
    transform,
    mixer,
    time,
    Surface,
    font,
    K_RIGHT,
    K_LEFT,
    K_UP,
    K_DOWN,
    display,
    image,
    transform,
    event,
    mixer,
    time,
    KEYUP,
    KEYDOWN,
    K_ESCAPE,
    QUIT,
    init,
    key,
    math,
    SRCALPHA,
    draw,
    Rect,
)
import pygame
import sys
from os.path import abspath, dirname, join, exists
import asyncio
import math
from PIL import Image

BASE_PATH = abspath(dirname(__file__))
FONT_PATH = join(BASE_PATH, "fonts")
IMAGE_PATH = join(BASE_PATH, "images")
SOUND_PATH = join(BASE_PATH, "sounds")
SOUND_FORMAT = "ogg"

# Colors (R, G, B)
WHITE = (255, 255, 255)
GREEN = (78, 255, 87)
BLACK = (0, 0, 0)

# Car configuration constants
CAR_WIDTH = 15
CAR_HEIGHT = 31
CAR_LAYERS = 14
CAR_LAYER_OFFSET = 1  # Vertical pixels between each layer

SCREEN = display.set_mode((800, 600))
FONT = join(FONT_PATH, "space_invaders.ttf")

class Text(object):
    def __init__(self, textFont, size, message, color, xpos, ypos):
        self.font = font.Font(textFont, size)
        self.surface = self.font.render(message, True, color)
        self.rect = self.surface.get_rect(topleft=(xpos, ypos))

    def draw(self, surface):
        surface.blit(self.surface, self.rect)


class SpriteStackingUtils:
    @staticmethod
    def create_layers_from_image(img_path, num_layers=8):
        """
        Create sprite stacking layers from a single voxel image.
        Useful when you have a single car image that needs to be sliced into layers.
        """
        try:
            # Open the full image file
            pil_img = Image.open(img_path)
            img_width, img_height = pil_img.size
            layer_height = img_height // num_layers
            
            layers = []
            # Slice the image into horizontal layers from bottom to top
            for i in range(num_layers):
                # Calculate the slice area for this layer (left, top, right, bottom)
                y_start = img_height - (i + 1) * layer_height
                y_end = img_height - i * layer_height
                
                # Slice the image vertically
                layer = pil_img.crop((0, y_start, img_width, y_end))
                
                # Convert PIL Image to pygame surface
                layer_surface = Surface((img_width, layer_height), pygame.SRCALPHA)
                pygame_img_str = layer.tobytes()
                pygame_img = transform.scale(
                    pygame.image.fromstring(pygame_img_str, layer.size, layer.mode).convert_alpha(),
                    (img_width, layer_height)
                )
                layers.append(pygame_img)
            
            return layers
        except Exception as e:
            print(f"Error creating layers: {e}")
            return []
            
    @staticmethod
    def extract_layers_from_files(img_folder, prefix="car_layer", num_layers=8):
        """
        Load separate layer images from files.
        Useful when you already have separate image files for each layer.
        """
        layers = []
        for i in range(num_layers):
            layer_path = join(img_folder, f"{prefix}{i}.png")
            if exists(layer_path):
                layer = image.load(layer_path).convert_alpha()
                layers.append(layer)
            else:
                print(f"Layer image not found: {layer_path}")
        
        return layers


class VoxelCar(sprite.Sprite):
    """Class to handle the sprite stacking rendering of a voxel car."""
    
    def __init__(self, screen):
        sprite.Sprite.__init__(self)
        self.screen = screen
        
        # Car position and movement
        self.x = 400  # Center of the screen horizontally
        self.y = 450  # Near the bottom of the screen
        self.speed = 0
        self.max_speed = 5
        self.acceleration = 0.2
        self.deceleration = 0.1
        self.friction = 0.95
        self.rotation = 180  # Start with car rotated 180 degrees (facing down)
        self.rotation_speed = 3
        self.direction = 0  # Tracking actual movement direction
        
        # Load car layer images
        car_img_path = join(IMAGE_PATH, "cars-1.png")
        self.num_layers = CAR_LAYERS
        
        # Try to create layers from a single image first
        if exists(car_img_path):
            self.layers = SpriteStackingUtils.create_layers_from_image(car_img_path, self.num_layers)
        else:
            # Fall back to loading separate layer files
            self.layers = SpriteStackingUtils.extract_layers_from_files(IMAGE_PATH, "car_layer", self.num_layers)
        
        # If still no layers, create a default car
        if not self.layers:
            self._create_default_car_layers()
        
        # Create a rectangular hitbox
        self.width = self.layers[0].get_width() if self.layers else CAR_WIDTH
        self.height = self.layers[0].get_height() if self.layers else CAR_HEIGHT
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        
        # Set the base image (for compatibility with pygame sprite group)
        self.image = self.layers[0] if self.layers else Surface((CAR_WIDTH, CAR_HEIGHT))
        
        # Drawing offsets for stacking
        self.layer_offset = CAR_LAYER_OFFSET  # Vertical pixels between each layer
        self.shadow_offset_x = 15  # Shadow offset from car position
        self.shadow_offset_y = 15  # Shadow offset from car position
    
    def _create_default_car_layers(self):
        """Create default car layers if no image is found."""
        self.layers = []
        colors = [
            (180, 180, 200),  # Light gray (top)
            (160, 160, 180),
            (140, 140, 160),
            (120, 120, 140),
            (100, 100, 120),
            (80, 80, 100),
            (60, 60, 80),
            (40, 40, 60)     # Dark gray (bottom)
        ]
        
        # Create layers of different colors based on CAR_LAYERS constant
        for i in range(CAR_LAYERS):
            color_index = min(i, len(colors) - 1)
            layer = Surface((CAR_WIDTH, CAR_HEIGHT), pygame.SRCALPHA)
            
            # Car body
            width_ratio = 0.7  # Body width as percentage of car width
            height_ratio = 0.6  # Body height as percentage of car height
            x_offset = int((CAR_WIDTH - (CAR_WIDTH * width_ratio)) / 2)
            y_offset = int((CAR_HEIGHT - (CAR_HEIGHT * height_ratio)) / 2)
            body_width = int(CAR_WIDTH * width_ratio)
            body_height = int(CAR_HEIGHT * height_ratio)
            
            pygame.draw.rect(layer, colors[color_index], (x_offset, y_offset, body_width, body_height), 0)
            
            # Car wheels
            wheel_color = (30, 30, 30)  # Black wheels
            wheel_radius = int(CAR_HEIGHT * 0.18)  # Scale wheel size based on car height
            wheel_y = int(CAR_HEIGHT * 0.78)  # Position wheels near bottom
            wheel_x1 = int(CAR_WIDTH * 0.25)  # Left wheel position
            wheel_x2 = int(CAR_WIDTH * 0.75)  # Right wheel position
            
            pygame.draw.circle(layer, wheel_color, (wheel_x1, wheel_y), wheel_radius)
            pygame.draw.circle(layer, wheel_color, (wheel_x2, wheel_y), wheel_radius)
            
            # Car windows (only on higher layers)
            if i < CAR_LAYERS // 2:
                window_color = (100, 200, 255) if i == 0 else (80, 170, 220)
                window_width = int(CAR_WIDTH * 0.4)
                window_height = int(CAR_HEIGHT * 0.35)
                window_x = int((CAR_WIDTH - window_width) / 2)
                window_y = int(CAR_HEIGHT * 0.15)
                pygame.draw.rect(layer, window_color, (window_x, window_y, window_width, window_height), 0)
            
            self.layers.append(layer)
    
    def update(self, keys, *args):
        # Handle car movement based on its current orientation
        if keys[K_UP]:
            self.speed += self.acceleration
        elif keys[K_DOWN]:
            self.speed -= self.acceleration
        else:
            # Apply friction to gradually slow down
            self.speed *= self.friction
        
        # Cap speed
        self.speed = max(min(self.speed, self.max_speed), -self.max_speed * 0.6)
        
        # Handle rotation - FIXED: Direction matches controller inputs - LEFT arrow turns LEFT, RIGHT arrow turns RIGHT
        if keys[K_LEFT]:
            self.rotation = (self.rotation - self.rotation_speed) % 360  # Left arrow = rotate LEFT
        if keys[K_RIGHT]:
            self.rotation = (self.rotation + self.rotation_speed) % 360  # Right arrow = rotate RIGHT
        
        # Calculate movement based on current rotation
        angle_rad = math.radians(self.rotation)
        move_x = -math.sin(angle_rad) * self.speed
        move_y = math.cos(angle_rad) * self.speed
        
        # Update position
        self.x += move_x
        self.y += move_y
        
        # Keep within screen bounds
        self.x = max(min(self.x, 800 - self.width//2), self.width//2)
        self.y = max(min(self.y, 600 - self.height//2), self.height//2)
        
        # Update rectangle position for collision detection
        self.rect.x = self.x - self.width//2
        self.rect.y = self.y - self.height//2
        
        # Draw the car using sprite stacking
        self.draw()

    def draw(self):
        """Draw the car using sprite stacking technique."""
        # Draw shadow below the car
        shadow_surf = Surface((self.width, self.height//2), pygame.SRCALPHA)
        shadow_color = (0, 0, 0, 80)  # Semi-transparent black
        shadow_rect = pygame.Rect(0, 0, self.width * 0.8, self.height//3)
        shadow_rect.center = (self.width//2, self.height//4)
        pygame.draw.ellipse(shadow_surf, shadow_color, shadow_rect)
        
        # Get the rotated shadow - add 180 degrees to flip the car
        shadow_surf = transform.rotate(shadow_surf, -(self.rotation + 180))
        shadow_rect = shadow_surf.get_rect()
        shadow_rect.center = (self.x + self.shadow_offset_x, self.y + self.shadow_offset_y)
        self.screen.blit(shadow_surf, shadow_rect)
        
        # Draw each layer from bottom to top, with slight offset
        for i, layer in enumerate(self.layers):
            # Rotate the layer with negative angle and add 180 degrees to flip the car
            rotated_layer = transform.rotate(layer, -(self.rotation + 180))
            layer_rect = rotated_layer.get_rect()
            
            # Calculate position with offset for 3D effect
            layer_rect.center = (
                self.x,
                self.y - i * self.layer_offset
            )
            
            # Draw this layer
            self.screen.blit(rotated_layer, layer_rect)


class VoxelCarGame:
    """Main game class for the Voxel Car game."""
    
    def __init__(self):
        # Setup pygame and display
        mixer.pre_init(44100, -16, 1, 4096)
        init()
        self.clock = time.Clock()
        self.screen = SCREEN
        self.caption = display.set_caption("Voxel Car Sprite Stacking")
        
        # Load background
        background_path = join(IMAGE_PATH, "background.jpg")
        if exists(background_path):
            self.background = image.load(background_path).convert()
        else:
            # Create a default background if image doesn't exist
            self.background = Surface((800, 600))
            self.background.fill((100, 180, 100))  # Green field
            
            # Draw a simple road
            pygame.draw.rect(self.background, (80, 80, 80), (200, 0, 400, 600))  # Road
            pygame.draw.rect(self.background, (255, 255, 255), (390, 0, 20, 600), 0)  # Center line
        
        # Game state
        self.running = True
        self.game_started = False
        
        # Create car
        self.car = VoxelCar(self.screen)
        
        # Setup text and UI elements
        try:
            self.font = font.Font(FONT, 36)
            self.small_font = font.Font(FONT, 24)
            self.title_text = Text(FONT, 50, "Voxel Car", WHITE, 300, 120)
            self.start_text = Text(FONT, 25, "Press any key to drive", WHITE, 250, 200)
            self.creator_text = Text(FONT, 20, "Sprite Stacking Demo", GREEN, 580, 570)
        except Exception as e:
            print(f"Error loading fonts: {e}")
            # Create fallback text using system font
            pygame.font.init()
            self.font = pygame.font.SysFont(None, 36)
            self.title_text = Text(None, 50, "Voxel Car", WHITE, 300, 120)
            self.start_text = Text(None, 25, "Press any key to drive", WHITE, 250, 200)
            self.creator_text = Text(None, 20, "Sprite Stacking Demo", GREEN, 580, 570)
    
    def handle_events(self):
        """Process input events."""
        self.keys = key.get_pressed()
        
        for e in event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                self.running = False
            
            # Start game on key press
            if not self.game_started and e.type == KEYUP:
                self.game_started = True
    
    def update(self):
        """Update game state."""
        if self.game_started:
            self.car.update(self.keys)
    
    def draw(self):
        """Draw everything to the screen."""
        # Draw background
        self.screen.blit(self.background, (0, 0))
        
        if not self.game_started:
            # Draw menu screen
            self.title_text.draw(self.screen)
            self.start_text.draw(self.screen)
        else:
            # We ensure the car is explicitly drawn here
            self.car.draw()
        
        # Always draw credits
        self.creator_text.draw(self.screen)
        
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


if __name__ == "__main__":
    game = VoxelCarGame()
    asyncio.run(game.main())

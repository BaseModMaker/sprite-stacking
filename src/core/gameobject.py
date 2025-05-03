import pygame
from pygame import sprite
from .spritestack import SpriteStack

class GameObject(sprite.Sprite):
    """Base class for all game objects."""
    
    def __init__(self, x=0, y=0, image_path=None, num_layers=8, layer_offset=1, width=32, height=32):
        """Initialize a game object.
        
        Args:
            x (int): The x position of the object
            y (int): The y position of the object
            image_path (str): Path to the sprite image
            num_layers (int): Number of layers for sprite stacking
            layer_offset (int): Vertical offset between layers
            width (int): Width of the object if no image is provided
            height (int): Height of the object if no image is provided
        """
        sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        
        # Create sprite stack for rendering
        self.sprite_stack = SpriteStack(
            image_path=image_path, 
            num_layers=num_layers, 
            layer_offset=layer_offset,
            default_width=width,
            default_height=height
        )
        
        # Set basic sprite properties for collision detection
        self.width = self.sprite_stack.width
        self.height = self.sprite_stack.height
        self.image = self.sprite_stack.layers[0] if self.sprite_stack.layers else None
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
    
    def update(self, *args, **kwargs):
        """Update the game object state.
        
        This method should be overridden by subclasses.
        """
        # Update rectangle position
        if self.rect:
            self.rect.x = self.x - self.width//2
            self.rect.y = self.y - self.height//2
    
    def draw(self, surface, draw_shadow=True):
        """Draw the game object on the given surface.
        
        Args:
            surface: The pygame surface to draw on
            draw_shadow (bool): Whether to draw the shadow
        """
        # Draw using sprite stack
        self.sprite_stack.draw(surface, self.x, self.y, 0, draw_shadow)
        
    def configure_shadow(self, horizontal_angle=45, vertical_angle=45, shadow_enabled=True):
        """Configure the shadow by setting sun position parameters.
        
        Args:
            horizontal_angle (int): Horizontal angle of the sun (0-360 degrees)
                0 = North, 90 = East, 180 = South, 270 = West
            vertical_angle (int): Vertical angle of the sun (0-90 degrees)
                0 = sun at horizon (long shadows), 90 = directly overhead (no shadows)
            shadow_enabled (bool): Whether shadows are enabled at all
                
        Returns:
            GameObject: Returns self for method chaining
        """
        self.sprite_stack.configure_sun(horizontal_angle, vertical_angle, shadow_enabled)
        return self
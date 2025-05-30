import math
import pygame
from .gameobject import GameObject

class Entity(GameObject):
    """An entity is a game object that can move and has physics properties."""
    
    def __init__(self, x=0, y=0, image_path=None, num_layers=8, layer_offset=0.5, width=32, height=32, 
                 entity_type="generic", outline_enabled=False, outline_color=(0, 0, 0), outline_thickness=1, outline_offset=1, rotation=0, shadow_enabled=True):
        """Initialize an entity.
        
        Args:
            x (int): The x position of the entity
            y (int): The y position of the entity
            image_path (str): Path to the entity's image
            num_layers (int): Number of layers for sprite stacking
            layer_offset (int): Vertical offset between layers
            width (int): Width of the entity if no image is provided
            height (int): Height of the entity if no image is provided
            entity_type (str): Type of entity for specialized sprite generation
            outline_enabled (bool): Whether to draw an outline around the entity
            outline_color (tuple): RGB color tuple for the outline
            outline_thickness (int): Thickness of the outline in pixels
            individual_offset (float): Offset for individual outlines
            rotation (float): Initial rotation angle in degrees
            shadow_enabled (bool): Whether to draw shadows for this entity
        """
        super().__init__(
            x, y, image_path, num_layers, layer_offset, width, height, 
            outline_enabled, outline_color, outline_thickness, outline_offset, shadow_enabled
        )
        self.speed = 0
        self.max_speed = 5  # Increased for larger map
        self.acceleration = 0.2  # Increased for larger map
        self.deceleration = 0.1
        self.friction = 0.98  # Slightly increased from 0.95 for smoother movement
        self.rotation = rotation
        self.base_angle = rotation  # Base angle without tilt effect
        self.rotation_speed = 2  # Reduced for slower turning
        self.direction = 0
        self.controller = None
        
        # If we have a special type and no image was loaded successfully, customize the sprite stack
        if entity_type == "car" and len(self.sprite_stack.layers) == 0:
            self.sprite_stack.create_car_layers(width, height)
            self.width = self.sprite_stack.width
            self.height = self.sprite_stack.height
    
    def set_controller(self, controller):
        """Set a controller for this entity.
        
        Args:
            controller: The controller to use for this entity
        """
        self.controller = controller
        controller.entity = self
    
    def apply_physics(self):
        """Apply physics calculations to the entity."""
        # Apply friction
        self.speed *= self.friction
        
        # Calculate movement based on current rotation, plus controller offset if available
        effective_rotation = self.rotation
        if self.controller and hasattr(self.controller, 'direction_offset'):
            effective_rotation = (self.rotation + self.controller.direction_offset) % 360
            
        # Convert to radians and calculate movement
        angle_rad = math.radians(effective_rotation)
        move_x = -math.sin(angle_rad) * self.speed
        move_y = math.cos(angle_rad) * self.speed
        
        # Update position
        self.x += move_x
        self.y += move_y
    
    def update(self, *args, **kwargs):
        """Update the entity state.
        
        Updates controller if one exists, then applies physics.
        
        Args:
            args: Variable arguments to pass to controller
            kwargs: Keyword arguments to pass to controller
        """
        # Let the controller update first if it exists
        if self.controller:
            self.controller.update(*args, **kwargs)
        
        # Then apply physics
        self.apply_physics()
        
        # Update rectangle position for collision detection
        if self.rect:
            self.rect.x = self.x - self.width//2
            self.rect.y = self.y - self.height//2
    
    def draw(self, surface, draw_shadow=True, performance_mode=0):
        """Draw the entity on the given surface.
        
        Args:
            surface: The pygame surface to draw on
            draw_shadow (bool): Whether to draw a shadow
            performance_mode (int): 0=Low, 1=Medium, 2=High quality rendering
        """
        # Override the parent draw method to include rotation
        self.sprite_stack.draw(surface, self.x, self.y, self.rotation, draw_shadow, performance_mode)
    
    def keep_in_bounds(self, width, height):
        """Keep the entity within the given bounds.
        
        This method is now a no-op to allow for infinite world movement.
        Kept for compatibility with existing code.
        
        Args:
            width (int): The maximum x coordinate (ignored)
            height (int): The maximum y coordinate (ignored)
        """
        # No longer constrain entity position to allow infinite world
        pass
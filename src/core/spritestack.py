import pygame
from pygame import Surface, transform, draw, Rect, SRCALPHA
from os.path import join, exists
import os
import sys
import math

class SpriteStack:
    """
    A class for handling sprite stacking technique rendering.
    This can be used by any game object that needs sprite stacking visualization.
    """
    
    def __init__(self, image_path=None, num_layers=8, layer_offset=1, default_width=32, default_height=32):
        """Initialize a sprite stack.
        
        Args:
            image_path (str): Path to the sprite sheet or stack image
            num_layers (int): Number of layers to stack
            layer_offset (int): Vertical pixels between each layer
            default_width (int): Default width if no image is provided
            default_height (int): Default height if no image is provided
        """
        self.num_layers = num_layers
        self.layer_offset = layer_offset
        self.default_width = default_width
        self.default_height = default_height
        self.layers = []
        
        # Try to load layers from the provided image path
        if image_path and exists(image_path):
            self.layers = self._create_layers_from_image(image_path)
        else:
            # If no path provided or file doesn't exist, try to load from separate files
            if image_path:
                img_folder = os.path.dirname(image_path)  # Extract folder path
                self.layers = self._extract_layers_from_files(img_folder, "layer", self.num_layers)
        
        # If still no layers, create default ones
        if not self.layers:
            self._create_default_layers()
        
        # Set dimensions based on the first layer
        self.width = self.layers[0].get_width() if self.layers else default_width
        self.height = self.layers[0].get_height() if self.layers else default_height
        
        # Shadow properties
        self.shadow_offset_x = 0  # Will be calculated based on sun position
        self.shadow_offset_y = 0  # Will be calculated based on sun position
        
        # Sun position properties - using only angle-based system now
        self.sun_horizontal_angle = 45      # 0-360 degrees (like a compass: 0=North, 90=East, 180=South, 270=West)
        self.sun_vertical_angle = 45        # 0-90 degrees (0 = sun at horizon, 90 = sun directly overhead)
        self.shadow_enabled = True          # Whether shadows are enabled at all
            
    def _create_layers_from_image(self, img_path):
        """Create sprite stacking layers from a single image.
        
        Args:
            img_path (str): Path to the image file
            
        Returns:
            list: List of pygame surfaces for each layer
        """
        try:
            # Web version needs special handling
            is_web = hasattr(sys, '_emscripten_info')
            
            # Load full image
            full_img = pygame.image.load(img_path)
            
            # Add alpha channel if needed and convert for better performance
            if full_img.get_alpha() is None:
                full_img = full_img.convert()
            else:
                full_img = full_img.convert_alpha()
                
            img_width = full_img.get_width()
            img_height = full_img.get_height()
            layer_height = img_height // self.num_layers
            
            layers = []
            # Split the image into layers
            for i in range(self.num_layers):
                # Calculate the slice area for this layer
                y_start = img_height - (i + 1) * layer_height
                
                # Create a surface for this layer
                layer_surface = pygame.Surface((img_width, layer_height), SRCALPHA)
                
                # Copy the appropriate part of the image to this layer surface
                layer_rect = pygame.Rect(0, y_start, img_width, layer_height)
                layer_surface.blit(full_img, (0, 0), layer_rect)
                
                layers.append(layer_surface)
            
            return layers
        except Exception as e:
            print(f"Error creating layers from image: {e}")
            return []
            
    def _extract_layers_from_files(self, img_folder, prefix="layer", num_layers=8):
        """Load separate layer images from files.
        
        Args:
            img_folder (str): Path to the folder containing layer images
            prefix (str): Prefix for layer file names
            num_layers (int): Number of layer files to look for
            
        Returns:
            list: List of pygame surfaces for each layer
        """
        layers = []
        for i in range(num_layers):
            layer_path = join(img_folder, f"{prefix}{i}.png")
            if exists(layer_path):
                try:
                    layer = pygame.image.load(layer_path)
                    # Convert surface for better performance
                    if layer.get_alpha() is None:
                        layer = layer.convert()
                    else:
                        layer = layer.convert_alpha()
                    layers.append(layer)
                except Exception as e:
                    print(f"Error loading layer image: {e}")
            else:
                print(f"Layer image not found: {layer_path}")
        
        return layers
    
    def _create_default_layers(self):
        """Create default colored layers when no image is provided."""
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
        
        # Extend colors list if needed
        while len(colors) < self.num_layers:
            colors.append(colors[-1])
        
        # Create layers of different colors based on number of layers
        for i in range(self.num_layers):
            color_index = min(i, len(colors) - 1)
            layer = Surface((self.default_width, self.default_height), pygame.SRCALPHA)
            
            # Draw a simple rectangle on each layer
            rect_width = int(self.default_width * 0.8)
            rect_height = int(self.default_height * 0.8)
            x_offset = (self.default_width - rect_width) // 2
            y_offset = (self.default_height - rect_height) // 2
            
            pygame.draw.rect(
                layer, 
                colors[color_index], 
                (x_offset, y_offset, rect_width, rect_height)
            )
            
            self.layers.append(layer)
    
    def draw(self, surface, x, y, rotation=0, draw_shadow=True):
        """Draw the stacked sprite at the specified position.
        
        Args:
            surface: Pygame surface to draw on
            x (int): X position to draw at
            y (int): Y position to draw at
            rotation (float): Rotation angle in degrees
            draw_shadow (bool): Whether to draw a shadow
        """
        if draw_shadow:
            self._draw_shadow(surface, x, y, rotation)
        
        # Draw each layer from bottom to top, with slight offset
        for i, layer in enumerate(self.layers):
            # Only proceed if the layer is valid
            if layer is None:
                continue
                
            # Create a copy to avoid modifying the original
            layer_to_draw = layer.copy()
            
            # Apply rotation
            if rotation != 0:
                layer_to_draw = transform.rotate(layer_to_draw, -rotation)
                
            # Get rect for positioning
            layer_rect = layer_to_draw.get_rect()
            
            # Calculate position with offset for 3D effect
            layer_rect.center = (
                int(x),  # Ensure integer coordinates
                int(y - i * self.layer_offset)
            )
            
            # Draw this layer
            surface.blit(layer_to_draw, layer_rect)
    
    def _draw_shadow(self, surface, x, y, rotation):
        """Draw a shadow beneath the sprite based on sun position and object layers.
        
        Args:
            surface: Pygame surface to draw on
            x (int): X position of the object
            y (int): Y position of the object
            rotation (float): Rotation angle in degrees
        """
        # Check if shadows are enabled
        if not self.shadow_enabled:
            return
            
        # Calculate vertical factor (affects shadow length and intensity)
        # 0° = sun at horizon (long shadows), 90° = sun directly overhead (no shadows)
        vertical_factor = self.sun_vertical_angle / 90.0
        
        # Convert horizontal angle to radians for shadow direction calculations
        horizontal_rad = math.radians(self.sun_horizontal_angle)
        
        # Calculate shadow length based on vertical angle
        # Higher vertical angle (sun higher in sky) = shorter shadow
        shadow_length = self.height * (1.0 - vertical_factor) * 1.5
        
        # Calculate shadow offset based on horizontal angle
        shadow_offset_x = -math.sin(horizontal_rad) * shadow_length
        shadow_offset_y = -math.cos(horizontal_rad) * shadow_length
        
        # Prepare shadow dimensions
        shadow_width = int(self.width * 1.5)
        shadow_height = int(self.height + shadow_length)
        shadow_surf = pygame.Surface((shadow_width, shadow_height), pygame.SRCALPHA)
        
        # Calculate shadow opacity based on vertical angle
        # Higher sun = lighter shadow
        shadow_alpha = int(120 * (1.0 - (vertical_factor * 0.7)))
        
        # Process each layer to create the composite shadow
        for i, layer in enumerate(self.layers):
            if layer is None:
                continue
                
            # Make a copy to avoid modifying the original
            layer_copy = layer.copy()
            
            # Apply rotation if needed
            if rotation != 0:
                layer_copy = transform.rotate(layer_copy, -rotation)
                
            # Create a silhouette of this layer for the shadow
            silhouette = pygame.Surface(layer_copy.get_size(), pygame.SRCALPHA)
            
            # For each pixel, if it's not transparent, make it part of the shadow
            for py in range(layer_copy.get_height()):
                for px in range(layer_copy.get_width()):
                    if layer_copy.get_at((px, py))[3] > 0:  # If pixel is not fully transparent
                        silhouette.set_at((px, py), (0, 0, 0, shadow_alpha))  # Semi-transparent black
            
            # Calculate layer-specific shadow position
            # Lower layers (higher i) cast slightly longer shadows
            layer_factor = 1.0 - (i / self.num_layers)  # 1.0 for first layer, decreasing to 0 for last
            layer_shadow_x = shadow_offset_x * layer_factor
            layer_shadow_y = shadow_offset_y * layer_factor
            
            # Calculate shadow stretch based on vertical angle - lower sun = more stretch
            stretch_factor = 1.0 + (1.0 - vertical_factor) * 0.5
            
            # Only stretch in the direction of the shadow
            if abs(shadow_offset_x) > abs(shadow_offset_y):
                # Horizontal stretch
                stretch_width = int(silhouette.get_width() * stretch_factor)
                silhouette = pygame.transform.scale(silhouette, (stretch_width, silhouette.get_height()))
            else:
                # Vertical stretch
                stretch_height = int(silhouette.get_height() * stretch_factor)
                silhouette = pygame.transform.scale(silhouette, (silhouette.get_width(), stretch_height))
            
            # Position and draw this layer's shadow
            silhouette_rect = silhouette.get_rect()
            center_x = shadow_width // 2 + layer_shadow_x * 0.2  # Subtle shift for staggered shadow
            center_y = shadow_height // 2 + layer_shadow_y * 0.2  # Subtle shift for staggered shadow
            silhouette_rect.center = (int(center_x), int(center_y))
            shadow_surf.blit(silhouette, silhouette_rect)
        
        # Calculate final shadow position
        shadow_rect = shadow_surf.get_rect()
        shadow_rect.center = (int(x + shadow_offset_x * 0.8), int(y + shadow_offset_y * 0.8))
        
        # Draw the final shadow
        surface.blit(shadow_surf, shadow_rect)
    
    def create_car_layers(self, width, height):
        """Create car-specific layers.
        
        Args:
            width (int): Width of the car sprite
            height (int): Height of the car sprite
        """
        self.layers = []
        
        # Extended color palette to support more layers
        colors = [
            (200, 200, 220),  # Lightest gray (top)
            (190, 190, 210),
            (180, 180, 200),
            (170, 170, 190),
            (160, 160, 180),
            (150, 150, 170),
            (140, 140, 160),
            (130, 130, 150),
            (120, 120, 140),
            (110, 110, 130),
            (100, 100, 120),
            (90, 90, 110),
            (80, 80, 100), 
            (70, 70, 90),
            (60, 60, 80),
            (50, 50, 70),
            (40, 40, 60),     # Darkest gray (bottom)
        ]
        
        # Ensure we have enough colors for all layers
        if len(colors) < self.num_layers:
            print(f"Warning: Not enough colors ({len(colors)}) for all layers ({self.num_layers})")
            # Extend colors list if needed
            while len(colors) < self.num_layers:
                colors.append((40, 40, 60))
        
        # Create layers of different colors based on number of layers
        for i in range(self.num_layers):
            color_index = min(i, len(colors) - 1)
            layer = Surface((width, height), pygame.SRCALPHA)
            
            # Car body
            width_ratio = 0.7  # Body width as percentage of car width
            height_ratio = 0.6  # Body height as percentage of car height
            x_offset = int((width - (width * width_ratio)) / 2)
            y_offset = int((height - (height * height_ratio)) / 2)
            body_width = int(width * width_ratio)
            body_height = int(height * height_ratio)
            
            pygame.draw.rect(layer, colors[color_index], (x_offset, y_offset, body_width, body_height), 0)
            
            # Car wheels
            wheel_color = (30, 30, 30)  # Black wheels
            wheel_radius = int(height * 0.18)  # Scale wheel size based on car height
            wheel_y = int(height * 0.78)  # Position wheels near bottom
            wheel_x1 = int(width * 0.25)  # Left wheel position
            wheel_x2 = int(width * 0.75)  # Right wheel position
            
            pygame.draw.circle(layer, wheel_color, (wheel_x1, wheel_y), wheel_radius)
            pygame.draw.circle(layer, wheel_color, (wheel_x2, wheel_y), wheel_radius)
            
            # Car windows (only on higher layers)
            if i < self.num_layers // 2:
                window_color = (100, 200, 255) if i == 0 else (80, 170, 220)
                window_width = int(width * 0.4)
                window_height = int(height * 0.35)
                window_x = int((width - window_width) / 2)
                window_y = int(height * 0.15)
                pygame.draw.rect(layer, window_color, (window_x, window_y, window_width, window_height), 0)
            
            self.layers.append(layer)
        
        # Update dimensions
        self.width = width
        self.height = height

    def configure_sun(self, horizontal_angle=45, vertical_angle=45, shadow_enabled=True):
        """Configure the sun position to control shadow projection.
        
        Args:
            horizontal_angle (int): Horizontal angle of the sun (0-360 degrees)
                0 = North, 90 = East, 180 = South, 270 = West
            vertical_angle (int): Vertical angle of the sun (0-90 degrees)
                0 = sun flat on horizon (long shadows), 90 = sun directly overhead (no shadows)
            shadow_enabled (bool): Whether shadows are enabled at all
        
        Returns:
            SpriteStack: Returns self for method chaining
        """
        # Validate and set angles
        self.sun_horizontal_angle = max(0, min(360, horizontal_angle))
        self.sun_vertical_angle = max(0, min(90, vertical_angle))
        self.shadow_enabled = shadow_enabled
        
        return self
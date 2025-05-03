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
    
    def __init__(self, image_path=None, num_layers=8, layer_offset=1, default_width=32, default_height=32, outline_enabled=False, outline_color=(255, 0, 0), outline_thickness=2):
        """Initialize a sprite stack.
        
        Args:
            image_path (str): Path to the sprite sheet or stack image
            num_layers (int): Number of layers to stack
            layer_offset (int): Vertical pixels between each layer
            default_width (int): Default width if no image is provided
            default_height (int): Default height if no image is provided
            outline_enabled (bool): Whether to draw an outline around the sprite
            outline_color (tuple): RGB color tuple for the outline
            outline_thickness (int): Thickness of the outline in pixels
        """
        self.num_layers = num_layers
        self.layer_offset = layer_offset
        self.default_width = default_width
        self.default_height = default_height
        self.layers = []
        
        # Outline properties
        self.outline_enabled = outline_enabled
        self.outline_color = outline_color
        self.outline_thickness = outline_thickness
        
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
    
    def draw(self, surface, x, y, rotation=0, draw_shadow=True, performance_mode=1):
        """Draw the stacked sprite at the specified position.
        
        Args:
            surface: Pygame surface to draw on
            x (int): X position to draw at
            y (int): Y position to draw at
            rotation (float): Rotation angle in degrees
            draw_shadow (bool): Whether to draw a shadow
            performance_mode (int): Optimization level - ignored in this version
        """
        # Draw shadow first so it appears behind the sprite
        if draw_shadow and self.shadow_enabled:
            self._draw_shadow(surface, x, y, rotation)
        
        # Create rotation cache to avoid redundant transforms
        rotation_cache = {}
        
        # Draw from bottom to top to get correct overlap
        for i in range(len(self.layers)):
            if i >= len(self.layers) or self.layers[i] is None:
                continue
                
            # Cache rotated images to avoid redundant transformations
            if rotation != 0:
                if i not in rotation_cache:
                    rotation_cache[i] = transform.rotate(self.layers[i], -rotation)
                layer_to_draw = rotation_cache[i]
            else:
                layer_to_draw = self.layers[i]
                
            # Position with offset for 3D effect
            layer_rect = layer_to_draw.get_rect()
            layer_rect.center = (int(x), int(y - i * self.layer_offset))
            
            # Draw this layer
            surface.blit(layer_to_draw, layer_rect)
        
        # Draw outline if enabled
        if self.outline_enabled:
            self._draw_outline(surface, x, y, rotation)
    
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
        # Lower sun = longer shadow (inverse relationship with vertical_factor)
        base_shadow_length = self.height * (1.0 - vertical_factor) * 2.5
        
        # Calculate shadow offset based on horizontal angle
        shadow_offset_x = -math.sin(horizontal_rad) * base_shadow_length
        shadow_offset_y = -math.cos(horizontal_rad) * base_shadow_length
        
        # Prepare shadow dimensions - ensure enough room for shifted shadow
        shadow_width = int(self.width * 3.5)
        shadow_height = int(self.height * 3.5)
        shadow_surf = pygame.Surface((shadow_width, shadow_height), pygame.SRCALPHA)
        
        # Calculate shadow opacity based on vertical angle - but make it more opaque
        # Higher sun = lighter shadow, but with a minimum opacity
        shadow_alpha = int(180 * (1.0 - (vertical_factor * 0.5)))  # Increased from 120 to 180, reduced fade factor
        
        # Base position for shadow anchor (center of shadow surface)
        shadow_center_x = shadow_width // 2
        shadow_center_y = shadow_height // 2
        
        # Optimization: Use a subset of layers to balance performance and visual quality
        # Use more layers for smaller sprites, fewer for larger ones
        layer_count = len(self.layers)
        if layer_count <= 8:
            # For few layers, use all of them
            layer_indices = range(0, layer_count)
        else:
            # For many layers, sample evenly
            step = max(1, layer_count // 5)  # At least 5 layers for shadow
            layer_indices = range(0, layer_count, step)
        
        # Cache for rotated images
        rotation_cache = {}
        
        # Process selected layers to create composite shadow
        for i in layer_indices:
            if i >= len(self.layers) or self.layers[i] is None:
                continue
                
            # Apply rotation if needed (with caching)
            if rotation != 0:
                if i not in rotation_cache:
                    rotation_cache[i] = transform.rotate(self.layers[i], -rotation)
                layer_copy = rotation_cache[i]
            else:
                layer_copy = self.layers[i]
                
            # Create a silhouette using mask for this layer
            mask = pygame.mask.from_surface(layer_copy)
            silhouette = mask.to_surface(setcolor=(0, 0, 0, shadow_alpha), unsetcolor=(0, 0, 0, 0))
            
            # Calculate layer factor based on position in stack (0.0 for bottom, 1.0 for top)
            layer_factor = i / max(1, layer_count - 1)
            
            # Calculate layer-specific shadow offset
            # Higher layers cast shadows that are further from the object
            # First layer (i=0) has zero offset to be directly under the object
            if i == 0:  # First layer is directly under the object
                layer_offset_x = 0
                layer_offset_y = 0
            else:
                # Other layers follow the sun angle
                layer_offset_x = shadow_offset_x * layer_factor * 0.6
                layer_offset_y = shadow_offset_y * layer_factor * 0.6
            
            # Position the silhouette with appropriate offset
            silhouette_rect = silhouette.get_rect()
            silhouette_rect.center = (
                int(shadow_center_x + layer_offset_x),
                int(shadow_center_y + layer_offset_y)
            )
            
            # Draw the silhouette to the shadow surface
            shadow_surf.blit(silhouette, silhouette_rect)
        
        # Calculate final shadow position - position directly under the object
        shadow_rect = shadow_surf.get_rect()
        shadow_rect.center = (x, y)  # Place shadow directly under object
        
        # Draw the final composite shadow
        surface.blit(shadow_surf, shadow_rect)
    
    def _draw_outline(self, surface, x, y, rotation):
        """Draw an outline that follows the contour of the sprite-stacked object.
        
        Args:
            surface: Pygame surface to draw on
            x (int): X position of the object
            y (int): Y position of the object
            rotation (float): Rotation angle in degrees
        """
        if not self.outline_enabled:
            return
            
        # Create a combined surface that includes all layers to capture the full shape
        # Calculate the total area needed to contain the sprite stack
        total_height = self.height + (self.num_layers - 1) * self.layer_offset
        
        # Create a temporary surface large enough to contain the stacked sprite
        # Add padding for rotation and outline
        padding = max(self.width, total_height) + 20
        temp_width = self.width + padding * 2
        temp_height = total_height + padding * 2
        
        # Create a temporary surface with alpha channel
        temp_surface = pygame.Surface((temp_width, temp_height), pygame.SRCALPHA)
        
        # Center position on the temporary surface
        temp_x = temp_width // 2
        temp_y = temp_height // 2
        
        # Draw all layers to the temporary surface without outlines or shadows
        rotation_cache = {}
        for i in range(len(self.layers)):
            if i >= len(self.layers) or self.layers[i] is None:
                continue
                
            # Cache rotated images to avoid redundant transformations
            if rotation != 0:
                if i not in rotation_cache:
                    rotation_cache[i] = pygame.transform.rotate(self.layers[i], -rotation)
                layer_to_draw = rotation_cache[i]
            else:
                layer_to_draw = self.layers[i]
                
            # Position with offset for 3D effect
            layer_rect = layer_to_draw.get_rect()
            layer_rect.center = (temp_x, temp_y - i * self.layer_offset)
            
            # Draw this layer to the temporary surface
            temp_surface.blit(layer_to_draw, layer_rect)
            
        # Create a mask from the combined layers to get the shape
        mask = pygame.mask.from_surface(temp_surface)
        
        # Create the outline by drawing slightly offset versions of the shape
        # First create a surface for the outline that's the same size as our temp surface
        outline_surface = pygame.Surface((temp_width, temp_height), pygame.SRCALPHA)
        
        # Get the outline points - these are the points at the edge of the mask
        outline_points = mask.outline()
        
        # If we have outline points, draw them
        if outline_points:
            # Draw the outline by connecting the points with lines
            pygame.draw.polygon(outline_surface, self.outline_color, outline_points, self.outline_thickness)
        
        # Calculate position on the main surface
        outline_rect = outline_surface.get_rect()
        outline_rect.center = (int(x), int(y - (self.num_layers - 1) * self.layer_offset / 2))
        
        # Draw the outline surface
        surface.blit(outline_surface, outline_rect)
    
    def configure_sun(self, horizontal_angle=45, vertical_angle=45, shadow_enabled=True):
        """Configure the sun position for shadow calculations.
        
        Args:
            horizontal_angle (int): Horizontal angle of the sun (0-360 degrees)
                0 = North, 90 = East, 180 = South, 270 = West
            vertical_angle (int): Vertical angle of the sun (0-90 degrees)
                0 = sun at horizon (long shadows), 90 = directly overhead (no shadows)
            shadow_enabled (bool): Whether shadows are enabled at all
                
        Returns:
            SpriteStack: Returns self for method chaining
        """
        self.sun_horizontal_angle = horizontal_angle
        self.sun_vertical_angle = vertical_angle
        self.shadow_enabled = shadow_enabled
        return self


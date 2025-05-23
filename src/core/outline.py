"""
Outline manager for sprite stacking visualization.
This module handles all outline-related functionality for the game objects.
"""
import pygame
from pygame import Surface, SRCALPHA

class OutlineManager:
    """Class to manage outline rendering for sprite stacked objects."""
    
    def __init__(self, enabled=False, color=(0, 0, 0), thickness=1, individual_offset=1):
        """Initialize the outline manager.
        
        Args:
            enabled (bool): Whether the outline is enabled by default
            color (tuple): RGB color tuple for the outline
            thickness (int): Thickness of the outline in pixels
        """
        self.enabled = enabled
        self.color = color
        self.thickness = thickness
        self.individual_offset = individual_offset
    def draw_outline(self, surface, x, y, rotation, layers, width, height, num_layers, layer_offset, tilt_amount=0):
        """Draw an outline that follows the contour of the sprite-stacked object.
        
        Args:
            surface: Pygame surface to draw on
            x (int): X position of the object
            y (int): Y position of the object
            rotation (float): Rotation angle in degrees
            layers (list): List of layer surfaces for the sprite stack
            width (int): Width of the sprite
            height (int): Height of the sprite
            num_layers (int): Number of layers in the sprite stack
            layer_offset (int): Vertical offset between layers
            tilt_amount (float): Amount to tilt the layers (-1 to 1, negative = left tilt)
        """
        if not self.enabled:
            return
            
        # Create a combined surface that includes all layers to capture the full shape
        # Calculate the total area needed to contain the sprite stack
        total_height = height + (num_layers - 1) * layer_offset
        
        # Create a temporary surface large enough to contain the stacked sprite
        # Add padding for rotation and outline
        padding = max(width, total_height) + 20
        temp_width = width + padding * 2
        temp_height = total_height + padding * 2
        
        # Create a temporary surface with alpha channel
        temp_surface = pygame.Surface((temp_width, temp_height), SRCALPHA)
        
        # Center position on the temporary surface
        temp_x = temp_width // 2
        temp_y = temp_height // 2
        
        # Draw all layers to the temporary surface without outlines or shadows
        rotation_cache = {}
        for i in range(len(layers)):
            if i >= len(layers) or layers[i] is None:
                continue
                
            # Cache rotated images to avoid redundant transformations
            if rotation != 0:
                if i not in rotation_cache:
                    rotation_cache[i] = pygame.transform.rotate(layers[i], -rotation)
                layer_to_draw = rotation_cache[i]
            else:
                layer_to_draw = layers[i]
                  # Position with offset for 3D effect and tilt
            layer_rect = layer_to_draw.get_rect()
            
            # Calculate tilt offset based on layer position
            layer_factor = i / max(1, len(layers) - 1)  # 0 for bottom layer, 1 for top layer
            tilt_offset = tilt_amount * layer_factor * 4  # Adjust multiplier for more/less tilt effect
            
            # Apply both vertical stacking and horizontal tilt offsets
            layer_rect.center = (temp_x + tilt_offset, temp_y - i * layer_offset)
            
            # Draw this layer to the temporary surface
            temp_surface.blit(layer_to_draw, layer_rect)
            
        # Create a mask from the combined layers to get the shape
        mask = pygame.mask.from_surface(temp_surface)
        
        # Create the outline by drawing slightly offset versions of the shape
        # First create a surface for the outline that's the same size as our temp surface
        outline_surface = pygame.Surface((temp_width, temp_height), SRCALPHA)
        
        # Get the outline points - these are the points at the edge of the mask
        outline_points = mask.outline()
        
        # If we have enough outline points, draw them
        if len(outline_points) >= 3:  # Need at least 3 points for a polygon
            # Draw the outline by connecting the points with lines
            pygame.draw.polygon(outline_surface, self.color, outline_points, self.thickness)
        elif outline_points:  # If we have at least 2 points
            # Draw a line between the points
            pygame.draw.line(outline_surface, self.color, outline_points[0], outline_points[1], self.thickness)
        # If we have no points, don't draw anything
        
        # Calculate position on the main surface
        # Account for the vertical center of the sprite stack
        vertical_center_offset = (num_layers - 1) * layer_offset / 2
        
        # Add an additional vertical adjustment to move the outline down
        # This helps center it better on the visual appearance of the car
        vertical_adjustment = height * self.individual_offset  # Adjust this value as needed to fine-tune
        
        outline_rect = outline_surface.get_rect()
        outline_rect.center = (int(x), int(y - vertical_center_offset + vertical_adjustment))
        
        # Draw the outline surface
        surface.blit(outline_surface, outline_rect)
    
    def configure(self, enabled=None, color=None, thickness=None):
        """Configure the outline properties.
        
        Args:
            enabled (bool, optional): Whether the outline is enabled
            color (tuple, optional): RGB color tuple for the outline
            thickness (int, optional): Thickness of the outline in pixels
            
        Returns:
            OutlineManager: Returns self for method chaining
        """
        if enabled is not None:
            self.enabled = enabled
        if color is not None:
            self.color = color
        if thickness is not None:
            self.thickness = thickness
        return self
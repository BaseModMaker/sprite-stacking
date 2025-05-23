"""
Camera module for handling view transformations in the game.
This allows for an infinite world where the player stays centered.
"""
import math
import pygame

class Camera:
    """A camera that handles transformations and follows the player."""
    
    def __init__(self, screen_width, screen_height):
        """Initialize a camera.
        
        Args:
            screen_width (int): Width of the screen
            screen_height (int): Height of the screen
        """
        self.width = screen_width
        self.height = screen_height
        
        # Camera position in world coordinates
        self.x = 0
        self.y = 0
        
        # Camera rotation (in degrees, 0 = no rotation)
        self.rotation = 0
          # Camera smoothing (lower = smoother)
        self.smoothing = 0.1
        
        # Create a surface for rendering the camera view
        self.surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        
    def follow(self, target_x, target_y, target_rotation=None):
        """Make the camera follow a target position, keeping it centered.
        
        Args:
            target_x (float): X position to follow in world coordinates
            target_y (float): Y position to follow in world coordinates
            target_rotation (float, optional): Target rotation in degrees for camera alignment
        """
        if target_rotation is not None:
            # Calculate the camera offset to stay behind the submarine
            offset_distance = 0  # No offset needed as we want submarine in center
              # Convert target's rotation to radians
            rad_angle = math.radians(target_rotation)
            
            # Smoothly move camera to target position
            self.x += (target_x - self.x) * self.smoothing
            self.y += (target_y - self.y) * self.smoothing
            
            # Set camera rotation to counter-rotate the world
            # This makes the submarine appear stationary while the world rotates
            self.rotation = (-target_rotation) % 360
        else:
            # Fallback: just follow position without rotation
            self.x += (target_x - self.x) * self.smoothing
            self.y += (target_y - self.y) * self.smoothing
    
    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates.
        
        Args:
            world_x (float): X position in world coordinates
            world_y (float): Y position in world coordinates
            
        Returns:
            tuple: (screen_x, screen_y) coordinates for drawing
        """
        # Calculate offset from camera position
        offset_x = world_x - self.x
        offset_y = world_y - self.y
        
        # Apply rotation if needed
        if self.rotation != 0:
            # Convert to radians
            rad_angle = math.radians(self.rotation)
            cos_val = math.cos(rad_angle)
            sin_val = math.sin(rad_angle)
            
            # Apply rotation matrix
            rotated_x = offset_x * cos_val - offset_y * sin_val
            rotated_y = offset_x * sin_val + offset_y * cos_val
            
            offset_x = rotated_x
            offset_y = rotated_y
        
        # Convert to screen coordinates (centered)
        screen_x = self.width // 2 + offset_x
        screen_y = self.height // 2 + offset_y
        
        return int(screen_x), int(screen_y)
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates.
        
        Args:
            screen_x (float): X position on screen
            screen_y (float): Y position on screen
            
        Returns:
            tuple: (world_x, world_y) coordinates
        """
        # Calculate offset from screen center
        offset_x = screen_x - self.width // 2
        offset_y = screen_y - self.height // 2
        
        # Apply reverse rotation if needed
        if self.rotation != 0:
            # Convert to radians
            rad_angle = math.radians(-self.rotation)  # Negative for reverse rotation
            cos_val = math.cos(rad_angle)
            sin_val = math.sin(rad_angle)
            
            # Apply rotation matrix
            rotated_x = offset_x * cos_val - offset_y * sin_val
            rotated_y = offset_x * sin_val + offset_y * cos_val
            
            offset_x = rotated_x
            offset_y = rotated_y
        
        # Convert to world coordinates
        world_x = self.x + offset_x
        world_y = self.y + offset_y
        
        return world_x, world_y
        
    def get_surface(self):
        """Get the camera's rendering surface.
        
        Returns:
            pygame.Surface: Surface for rendering the camera view
        """
        return self.surface
        
    def apply_to_screen(self, target_surface):
        """Apply the camera content to the target surface.
        
        Args:
            target_surface (pygame.Surface): Surface to draw the camera view on
        """
        target_surface.blit(self.surface, (0, 0))
        
    def set_rotation(self, angle):
        """Set the camera rotation angle.
        
        Args:
            angle (float): Rotation angle in degrees
            
        Returns:
            float: The new rotation angle
        """
        self.rotation = angle % 360
        return self.rotation
    
    def move(self, dx, dy):
        """Manually move the camera by the specified amount.
        
        Args:
            dx (float): Amount to move in x direction
            dy (float): Amount to move in y direction
        """
        self.x += dx
        self.y += dy
      
import pygame
import math

class Sun:
    """Class to manage sun position, appearance, and related calculations."""
    
    def __init__(self, horizontal_angle=45, vertical_angle=45):
        """Initialize the sun with default angles.
        
        Args:
            horizontal_angle (int): Horizontal angle of the sun (0-360 degrees)
                0 = North, 90 = East, 180 = South, 270 = West
            vertical_angle (int): Vertical angle of the sun (0-90 degrees)
                0 = sun at horizon (long shadows), 90 = directly overhead (no shadows)
        """
        self.horizontal_angle = horizontal_angle  # 0-360 degrees (compass direction)
        self.vertical_angle = vertical_angle      # 0-90 degrees (height in sky)
        self.debug_enabled = False                # Debug always disabled
    
    def adjust_horizontal_angle(self, delta):
        """Adjust the horizontal angle of the sun.
        
        Args:
            delta (int): Amount to change the angle by (positive = clockwise)
        """
        self.horizontal_angle = (self.horizontal_angle + delta) % 360
        return self.horizontal_angle
    
    def adjust_vertical_angle(self, delta):
        """Adjust the vertical angle of the sun.
        
        Args:
            delta (int): Amount to change the angle by (positive = higher in sky)
        """
        self.vertical_angle = max(0, min(90, self.vertical_angle + delta))
        return self.vertical_angle
    
    def toggle_debug(self):
        """Debug toggle is disabled."""
        return False
        
    def draw(self, surface, screen_width, screen_height):
        """Draw a visual representation of the sun on the screen.
        
        Args:
            surface: Surface to draw on
            screen_width (int): Width of the screen
            screen_height (int): Height of the screen
        """
        # Calculate sun position based on horizontal angle only
        margin = 150  # Distance from screen edge
        sun_size = 30  # Size of sun circle
        
        # Determine position based on horizontal angle (circular path)
        # Add 90 degrees to correct the sun position to match shadow direction
        display_angle = (self.horizontal_angle + 270) % 360
        rad_angle = math.radians(display_angle)
        x = screen_width // 2 + margin * math.cos(rad_angle)
        y = screen_height // 2 - margin * math.sin(rad_angle)
        
        # Adjust sun color based on vertical angle
        vertical_factor = self.vertical_angle / 90.0  # 0.0 to 1.0
        
        # Base yellow with intensity based on vertical angle
        # Higher vertical angle = more intense white/yellow (sun more overhead)
        # Lower vertical angle = more orange/red (sun closer to horizon)
        if vertical_factor < 0.5:
            # Sunset/sunrise colors (orange/red) for low sun angles
            red = 255
            green = max(0, int(255 * (vertical_factor * 2)))  # Reduces green for redder appearance
            blue = 0
        else:
            # Yellow to white for higher sun angles
            red = 255
            green = 255
            blue = max(0, int(255 * (vertical_factor - 0.5) * 2))  # Increases blue for whiter appearance
        
        sun_color = (red, green, blue)
        
        # Draw the sun with appropriate color
        pygame.draw.circle(surface, sun_color, (int(x), int(y)), sun_size)
        
        # Draw rays from the sun
        ray_length = 15
        for angle in range(0, 360, 45):  # Draw 8 rays
            ray_angle = math.radians(angle)
            end_x = x + ray_length * math.cos(ray_angle)
            end_y = y + ray_length * math.sin(ray_angle)
            pygame.draw.line(surface, sun_color, (int(x), int(y)), (int(end_x), int(end_y)), 3)
            
        # Draw a line from the sun to center of screen to show light direction
        center_x = screen_width // 2
        center_y = screen_height // 2
        pygame.draw.line(surface, (255, 255, 0, 128), (int(x), int(y)), (center_x, center_y), 2)
    
    def draw_debug_info(self, surface, small_font, white_color, y_start=10):
        """Debug information is disabled."""
        # No debug info shown
        return

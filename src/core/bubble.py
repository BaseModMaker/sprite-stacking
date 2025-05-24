"""Bubble particle system for underwater effects."""
import random
import math

class Bubble:
    """A single bubble particle."""
    def __init__(self, x, y, size, lifetime, speed, angle):
        """Initialize a bubble.
        
        Args:
            x (float): Starting X position
            y (float): Starting Y position
            size (int): Radius of the bubble
            lifetime (int): How many frames the bubble lives
            speed (float): Movement speed
            angle (float): Direction of movement in degrees
        """
        self.x = x
        self.y = y
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.speed = speed
        self.angle = angle
        self.alpha = 255  # Bubble transparency
        
    def update(self):
        """Update bubble position and lifetime."""
        # Convert angle to radians for movement calculation
        angle_rad = math.radians(self.angle)
        
        # Move bubble
        self.x += math.cos(angle_rad) * self.speed
        self.y += math.sin(angle_rad) * self.speed
        
        # Decrease lifetime
        self.lifetime -= 1
        
        # Update alpha based on remaining lifetime
        self.alpha = int((self.lifetime / self.max_lifetime) * 200 + 55)  # Keep minimum visibility
        
        return self.lifetime > 0

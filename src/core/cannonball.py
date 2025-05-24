"""Projectile system for submarine combat."""
import math
from .gameobject import GameObject

class Cannonball(GameObject):
    """A projectile fired by the submarine."""
    def __init__(self, x=0, y=0, image_path="assets/images/cannonball-3x3x2.png", direction=0, speed=4.0):
        """Initialize a cannonball.
        
        Args:
            x (float): Starting X position
            y (float): Starting Y position
            image_path (str): Path to the cannonball sprite
            direction (float): Direction in degrees
            speed (float): Movement speed
        """
        super().__init__(
            x=x, 
            y=y, 
            image_path=image_path,
            num_layers=2,  # Cannonballs are smaller than submarines
            width=3,  # Small projectile
            height=3,
            outline_enabled=False,
            shadow_enabled=False,
        )
        
        self.direction = direction
        self.speed = speed
        self.lifetime = 100  # 0.5 seconds at 60 FPS - short range projectiles
        self.damage = 10  # Base damage
        
    def update(self):
        """Update cannonball position and lifetime."""
        # Convert direction to radians for movement
        angle_rad = math.radians(self.direction)
        
        # Move cannonball
        self.x += math.cos(angle_rad) * self.speed
        self.y += math.sin(angle_rad) * self.speed
        
        # Update lifetime
        self.lifetime -= 1
        
        # Return True if cannonball should continue existing
        return self.lifetime > 0

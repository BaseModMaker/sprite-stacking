"""Projectile system for submarine combat."""
import math
from .entity import Entity

class Cannonball(Entity):
    """A projectile fired by the submarine."""
    
    def __init__(self, x=0, y=0, image_path="assets/images/cannonball-3x3x2.png", direction=0, speed=4.0):
        """Initialize a cannonball.
        
        Args:
            x (float): Starting X position
            y (float): Starting Y position
            image_path (str): Path to the cannonball sprite
            direction (float): Direction in degrees            speed (float): Movement speed
        """
        super().__init__(
            x=x, 
            y=y, 
            image_path=image_path,
            num_layers=2,  # Cannonballs are smaller than submarines
            width=3,  # Small projectile
            height=3,
            outline_enabled=False,
            rotation=direction,  # Use Entity's rotation instead of separate direction
            shadow_enabled=False  # Cannonballs don't need shadows
        )
        
        # Set Entity's speed property
        self.speed = speed
        self.lifetime = 100  # 0.5 seconds at 60 FPS - short range projectiles
        self.damage = 10  # Base damage
        
    def update(self):
        """Update cannonball position and lifetime."""
        # Use original cannonball movement instead of Entity's physics
        # Convert rotation to radians for movement
        angle_rad = math.radians(self.rotation)
        
        # Move cannonball using original movement system
        self.x += math.cos(angle_rad) * self.speed
        self.y += math.sin(angle_rad) * self.speed
        
        # Update rectangle position for collision detection
        if self.rect:
            self.rect.x = self.x - self.width//2
            self.rect.y = self.y - self.height//2
        
        # Update lifetime
        self.lifetime -= 1
        
        # Return True if cannonball should continue existing
        return self.lifetime > 0

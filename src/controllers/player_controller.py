from pygame import K_UP, K_DOWN, K_LEFT, K_RIGHT

class PlayerController:
    """Controller for player-controlled entities."""
    
    def __init__(self):
        """Initialize a new player controller."""
        self.entity = None
        self.direction_offset = 180  # Offset angle to make car face the direction of movement
    
    def update(self, keys, *args, **kwargs):
        """Update the entity based on key inputs.
        
        Args:
            keys: Dictionary of key states from pygame.key.get_pressed()
            *args: Additional arguments
            **kwargs: Additional keyword arguments
        """
        if not self.entity:
            return
            
        # Handle acceleration based on key input
        if keys[K_UP]:
            self.entity.speed += self.entity.acceleration
        elif keys[K_DOWN]:
            self.entity.speed -= self.entity.acceleration
            
        # Cap speed
        self.entity.speed = max(min(self.entity.speed, 
                                   self.entity.max_speed), 
                               -self.entity.max_speed * 0.6)
        
        # Handle rotation
        if keys[K_LEFT]:
            self.entity.rotation = (self.entity.rotation - self.entity.rotation_speed) % 360
        if keys[K_RIGHT]:
            self.entity.rotation = (self.entity.rotation + self.entity.rotation_speed) % 360
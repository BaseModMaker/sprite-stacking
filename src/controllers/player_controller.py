from pygame import K_z, K_q, K_s, K_d, K_SPACE, MOUSEBUTTONDOWN

class PlayerController:
    """Controller for submarine player entities in Abyssal Gears."""
    def __init__(self):
        """Initialize a new submarine controller."""
        self.entity = None
        self.direction_offset = 180
        self.boost_active = False
        self.previous_boost_active = False  # Track previous frame's boost state
        self.boost_cooldown = 0
        self.max_boost_cooldown = 60  # Frames
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.stamina_regen_rate = 0.5
        self.boost_stamina_cost = 1.0
        self.firing_left = False
        self.firing_right = False
        self.fire_cooldown_left = 0
        self.fire_cooldown_right = 0
        self.fire_rate = 15  # Frames between shots
        
        # Tilt effect properties
        self.tilt_amount = 0  # Current tilt (-1 for left, 1 for right)
        self.max_tilt = 1.0  # Maximum tilt value
        self.tilt_speed = 0.2  # How fast the tilt changes
        self.layer_offset = 1  # Pixels to offset each layer during tilt
    
    def update(self, keys, *args, **kwargs):
        """Update the entity based on key inputs.
        
        Args:
            keys: Dictionary of key states from pygame.key.get_pressed()
            *args: Additional arguments including mouse buttons
            **kwargs: Additional keyword arguments
        """
        if not self.entity:
            return
        
        # Get mouse buttons if provided
        mouse_buttons = kwargs.get('mouse_buttons', [0, 0, 0])
        
        # Movement controls (ZQSD)
        # Z - Forward
        if keys[K_z]:
            self.entity.speed += self.entity.acceleration
        # S - Backward
        elif keys[K_s]:
            self.entity.speed -= self.entity.acceleration
            
        # Handle rotation and tilt (Q/D for left/right)
        if keys[K_q]:
            # Update rotation
            self.entity.rotation = (self.entity.rotation - self.entity.rotation_speed) % 360
            # Add tilt effect when turning left
            self.tilt_amount = min(self.max_tilt, self.tilt_amount + self.tilt_speed)
        elif keys[K_d]:
            # Update rotation
            self.entity.rotation = (self.entity.rotation + self.entity.rotation_speed) % 360
            # Add tilt effect when turning right
            self.tilt_amount = max(-self.max_tilt, self.tilt_amount - self.tilt_speed)
        else:
            # Return tilt to center when not turning
            if self.tilt_amount > 0:
                self.tilt_amount = max(0, self.tilt_amount - self.tilt_speed)
            elif self.tilt_amount < 0:
                self.tilt_amount = min(0, self.tilt_amount + self.tilt_speed)
        
        # Boost (Spacebar)
        if keys[K_SPACE] and self.stamina > 0 and self.boost_cooldown <= 0:
            self.boost_active = True
            self.stamina -= self.boost_stamina_cost
            if self.stamina <= 0:
                self.boost_active = False
                self.boost_cooldown = self.max_boost_cooldown
        else:
            self.boost_active = False
            
        # Regenerate stamina when not boosting
        if not self.boost_active and self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + self.stamina_regen_rate)
            
        # Decrease boost cooldown
        if self.boost_cooldown > 0:
            self.boost_cooldown -= 1
            
        # Apply boost effect if active
        if self.boost_active:
            max_boost_speed = self.entity.max_speed * 1.5
            self.entity.speed = min(self.entity.speed * 1.2, max_boost_speed)
            
        # Cap speed
        normal_max_speed = self.entity.max_speed
        if self.boost_active:
            normal_max_speed *= 1.5
            
        self.entity.speed = max(min(self.entity.speed, 
                                 normal_max_speed), 
                              -normal_max_speed * 0.6)
        
        # Handle weapon firing
        # Left mouse button - Fire left weapon
        if mouse_buttons[0] and self.fire_cooldown_left <= 0:
            self.firing_left = True
            self.fire_cooldown_left = self.fire_rate
            # Logic for firing left weapon would go here
            print("Firing left weapon")
        else:
            self.firing_left = False
            
        # Right mouse button - Fire right weapon
        if mouse_buttons[2] and self.fire_cooldown_right <= 0:
            self.firing_right = True
            self.fire_cooldown_right = self.fire_rate
            # Logic for firing right weapon would go here
            print("Firing right weapon")
        else:
            self.firing_right = False
            
        # Update cooldowns
        if self.fire_cooldown_left > 0:
            self.fire_cooldown_left -= 1
            
        if self.fire_cooldown_right > 0:
            self.fire_cooldown_right -= 1
            
        # Update previous boost state for next frame
        self.previous_boost_active = self.boost_active
    
    def boost_just_started(self):
        """Check if boost just started this frame.
        
        Returns:
            bool: True if boost just started, False otherwise
        """
        return self.boost_active and not self.previous_boost_active
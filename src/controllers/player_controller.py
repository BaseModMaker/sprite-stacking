from pygame import K_z, K_q, K_s, K_d, K_SPACE, MOUSEBUTTONDOWN
import random
import math
from core.bubble import Bubble
from core.cannonball import Cannonball

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
        
        # Stamina properties
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.stamina_regen_rate = 0.5
        self.boost_stamina_cost = 1.0
        self.teleport_stamina_cost = 30.0  # Cost for teleporting
        self.stamina_locked = False  # Added: prevents stamina use until fully regenerated
          # Teleport properties
        self.space_press_time = 0  # How long space has been pressed
        self.teleport_distance = 100  # Units to teleport
        self.max_teleport_hold = 45  # Max frames to hold for teleport vs boost (about 0.75 seconds at 60fps)
        self.is_teleporting = False  # Track if we're in teleport state
        
        # Combat properties
        self.firing_left = False
        self.firing_right = False
        self.fire_cooldown_left = 0
        self.fire_cooldown_right = 0
        self.fire_rate = 15  # Frames between shots
        self.cannonball_speed = 8.0  # Speed of fired cannonballs
        self.cannonballs = []  # List of active cannonballs
        self.cannon_offset = 30  # Distance cannons are from center of sub
        
        # Tilt effect properties
        self.tilt_amount = 0  # Current tilt (-1 for left, 1 for right)
        self.max_tilt = 1.0  # Maximum tilt value
        self.tilt_speed = 0.2  # How fast the tilt changes
        self.layer_offset = 1  # Pixels to offset each layer during tilt
        
        # Bubble effect properties
        self.bubbles = []  # List of active bubbles
        self.bubble_spawn_timer = 0
        self.bubble_spawn_rate = 10  # Frames between bubble spawns when moving
        self.boost_bubble_rate = 5  # Faster spawn rate when boosting
        self.bubble_lifetime = 60  # How long bubbles last in frames
        self.min_bubble_size = 2
        self.max_bubble_size = 4
        self.bubble_speed = 0.5  # How fast bubbles float up
        self.bubble_spread = 10  # How far bubbles can spread horizontally
    
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
        
        # Update bubbles
        self._update_bubbles()        # Track space bar press duration and handle teleport/boost
        if keys[K_SPACE]:
            self.space_press_time += 1
            
            # Handle boost activation - activate immediately if holding space
            if not self.stamina_locked and self.stamina > 0 and self.boost_cooldown <= 0:
                self.boost_active = True
                self.stamina -= self.boost_stamina_cost
                if self.stamina <= 0:
                    self.boost_active = False
                    self.boost_cooldown = self.max_boost_cooldown
                    self.stamina_locked = True
            else:
                self.boost_active = False
        else:
            # Handle teleport on space release if it was a short press and we have stamina
            if (self.space_press_time > 0 and 
                self.space_press_time <= self.max_teleport_hold and 
                not self.stamina_locked and 
                not self.boost_cooldown):
                # Determine teleport direction based on movement keys, default to forward
                angle = 270  # Default to forward
                if keys[K_s]:  # Backward
                    angle = 90
                elif keys[K_q]:  # Left
                    angle = 180
                elif keys[K_d]:  # Right
                    angle = 0
                
                # Execute teleport
                self.teleport_polar(angle, self.teleport_distance)
                
                # Create bubble burst at end position
                self._create_teleport_bubbles()
                
                # Consume stamina and lock if we don't have enough
                if self.stamina >= self.teleport_stamina_cost:
                    self.stamina -= self.teleport_stamina_cost
                else:
                    # If not enough stamina, deplete it and lock
                    self.stamina = 0
                    self.stamina_locked = True
            
            # Reset teleport/boost state
            self.space_press_time = 0
            self.boost_active = False
        
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
                self.tilt_amount = min(0, self.tilt_amount + self.tilt_speed)          # Boost handling is now managed in the space press duration section above
            
        # Regenerate stamina when not boosting
        if not self.boost_active and self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + self.stamina_regen_rate)
            # Unlock stamina when fully regenerated
            if self.stamina >= self.max_stamina:
                self.stamina_locked = False
            
        # Decrease boost cooldown
        if self.boost_cooldown > 0:
            self.boost_cooldown -= 1
            
        # Apply boost effect if active
        if self.boost_active:
            max_boost_speed = self.entity.max_speed * 2.0
            self.entity.speed = min(self.entity.speed * 1.8, max_boost_speed)
            
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
            self._fire_cannon(-90)  # Fire from left side (-90 degrees relative to sub)
        else:
            self.firing_left = False
            
        # Right mouse button - Fire right weapon
        if mouse_buttons[2] and self.fire_cooldown_right <= 0:
            self.firing_right = True
            self.fire_cooldown_right = self.fire_rate
            self._fire_cannon(90)  # Fire from right side (90 degrees relative to sub)
        else:
            self.firing_right = False
            
        # Update cooldowns
        if self.fire_cooldown_left > 0:
            self.fire_cooldown_left -= 1
            
        if self.fire_cooldown_right > 0:
            self.fire_cooldown_right -= 1
            
        # Update cannonballs
        self._update_cannonballs()
        
        # Update previous boost state for next frame
        self.previous_boost_active = self.boost_active
          # Update previous boost state for next frame
        self.previous_boost_active = self.boost_active
    
    def boost_just_started(self):
        """Check if boost just started this frame.
        
        Returns:
            bool: True if boost just started, False otherwise
        """
        return self.boost_active and not self.previous_boost_active
    
    def _spawn_bubble(self):
        """Spawn a new bubble behind the submarine."""
        if not self.entity:
            return        # Convert polar coordinates to world position
        # angle 0 = front of sub, 180 = back of sub
        # angle_rad = math.radians(self.entity.rotation - 180)  # Adjust angle relative to sub's rotation
        angle_rad = math.radians(self.entity.rotation + 90)  # Adjust angle relative to sub's rotation
        spawn_distance = 50  # Distance from sub's center
        
        # Calculate spawn position using polar coordinates
        spawn_x = self.entity.x + spawn_distance * math.cos(angle_rad)
        spawn_y = self.entity.y + spawn_distance * math.sin(angle_rad)
        
        # Bubbles always move straight up
        move_angle = 90
        
        # Create new bubble
        from core.bubble import Bubble
        bubble = Bubble(
            x=spawn_x,
            y=spawn_y,
            size=random.randint(self.min_bubble_size, self.max_bubble_size),
            lifetime=self.bubble_lifetime,
            speed=self.bubble_speed * random.uniform(0.8, 1.2),
            angle=move_angle + random.uniform(-20, 20)
        )
        self.bubbles.append(bubble)
    
    def _update_bubbles(self):
        """Update and remove dead bubbles."""
        # Update each bubble and keep only the active ones
        self.bubbles = [b for b in self.bubbles if b.update()]
        
        # Spawn new bubbles if moving
        if abs(self.entity.speed) > 0.1:
            self.bubble_spawn_timer -= 1
            if self.bubble_spawn_timer <= 0:
                self._spawn_bubble()
                # Set next spawn time based on boost state
                self.bubble_spawn_timer = self.boost_bubble_rate if self.boost_active else self.bubble_spawn_rate

    def _create_teleport_bubbles(self):
        """Create a burst of bubbles in all directions for teleport effect."""
        if not self.entity:
            return

        num_bubbles = 16  # Number of bubbles in the burst
        for i in range(num_bubbles):
            # Calculate angle for even distribution around the circle
            angle = (i * 360 / num_bubbles) + random.uniform(-10, 10)
            angle_rad = math.radians(angle)
            
            # Random distance from center
            distance = random.uniform(20, 40)
            
            # Calculate bubble position
            spawn_x = self.entity.x + distance * math.cos(angle_rad)
            spawn_y = self.entity.y + distance * math.sin(angle_rad)
            
            # Create bubble with outward movement
            from core.bubble import Bubble
            bubble = Bubble(
                x=spawn_x,
                y=spawn_y,
                size=random.randint(2, 6),  # Slightly larger bubbles for effect
                lifetime=30,  # Shorter lifetime for the effect
                speed=random.uniform(1.0, 2.0),  # Faster speed for burst effect
                angle=angle  # Move in the direction they're spawned
            )
            self.bubbles.append(bubble)

    def teleport_polar(self, angle, distance):
        """Teleport the submarine using polar coordinates relative to its current position and rotation.
        
        Args:
            angle (float): Angle in degrees relative to submarine's front (0 = front, 180 = back)
            distance (float): Distance to teleport in units
        """
        if not self.entity:
            return
            
        # Convert angle to world space by adding submarine's rotation
        world_angle = self.entity.rotation + angle
        # Convert to radians for math calculations
        angle_rad = math.radians(world_angle)
        
        # Calculate new position using polar coordinates
        new_x = self.entity.x + distance * math.cos(angle_rad)
        new_y = self.entity.y + distance * math.sin(angle_rad)
        
        # Update submarine position
        self.entity.x = new_x
        self.entity.y = new_y
        
        # Create teleportation bubble effect
        self._create_teleport_bubbles()
    
    def _fire_cannon(self, side_angle):
        """Fire a cannonball from one of the submarine's cannons.
        
        Args:
            side_angle (float): Angle offset from submarine's direction for cannon position (-90=left, 90=right)
        """
        if not self.entity:
            return
              # Spawn cannonball from the center of the submarine
        spawn_x = self.entity.x
        spawn_y = self.entity.y
        
        # Create the cannonball (90 degree offset since sub's 0 degrees is up)
        ball = Cannonball(
            x=spawn_x,
            y=spawn_y,            image_path="assets/images/cannonball-3x3x2.png",
            direction=self.entity.rotation + side_angle + 90,  # Add side angle and 90 for proper orientation
        )
        self.cannonballs.append(ball)
        
        # Create bubble effect at cannon position
        for _ in range(3):
            bubble = Bubble(
                x=spawn_x,
                y=spawn_y,
                size=random.randint(3, 5),
                lifetime=20,
                speed=random.uniform(1.0, 2.0),
                angle=random.uniform(0, 360)  # Random directions for explosion effect
            )
            self.bubbles.append(bubble)
            
    def _update_cannonballs(self):
        """Update and remove dead cannonballs."""
        # Update each cannonball and keep only the active ones
        self.cannonballs = [c for c in self.cannonballs if c.update()]
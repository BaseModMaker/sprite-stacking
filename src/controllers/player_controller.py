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
        self.camera = None  # Will be set by the game
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
    
    def update(self, input_state, *args, **kwargs):
        """Update the entity based on input state.
        
        Args:
            input_state: InputState object containing current input states
            *args: Additional arguments including mouse buttons
            **kwargs: Additional keyword arguments
        """
        if not self.entity:
            return
            
        # Get mouse buttons if provided (for backward compatibility)
        mouse_buttons = kwargs.get('mouse_buttons', [0, 0, 0])
        
        # Update bubbles
        self._update_bubbles()

        # Track space bar press duration and handle teleport/boost
        if input_state.boost_teleport:
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
                if input_state.backward:  # Backward
                    angle = 90
                elif input_state.turn_left:  # Left
                    angle = 180
                elif input_state.turn_right:  # Right
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
        if input_state.forward:
            self.entity.speed += self.entity.acceleration
        # S - Backward
        elif input_state.backward:
            self.entity.speed -= self.entity.acceleration
            
        # Handle rotation and tilt (Q/D for left/right)
        if input_state.turn_left:
            # Update rotation
            self.entity.rotation = (self.entity.rotation - self.entity.rotation_speed) % 360
            # Add tilt effect when turning left
            self.tilt_amount = min(self.max_tilt, self.tilt_amount + self.tilt_speed)
        elif input_state.turn_right:
            # Update rotation
            self.entity.rotation = (self.entity.rotation + self.entity.rotation_speed) % 360
            # Add tilt effect when turning right
            self.tilt_amount = max(-self.max_tilt, self.tilt_amount - self.tilt_speed)
        else:
            # Return tilt to center when not turning
            if self.tilt_amount > 0:
                self.tilt_amount = max(0, self.tilt_amount - self.tilt_speed)
            elif self.tilt_amount < 0:
                self.tilt_amount = min(0, self.tilt_amount + self.tilt_speed)# Boost handling is now managed in the space press duration section above
            
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
        if input_state.left_mouse and self.fire_cooldown_left <= 0:
            self.firing_left = True
            self.fire_cooldown_left = self.fire_rate
            self._fire_cannon(-90)  # Fire from left side (-90 degrees relative to sub)
        else:
            self.firing_left = False
            
        # Right mouse button - Fire right weapon
        if input_state.right_mouse and self.fire_cooldown_right <= 0:
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
    
    def set_camera(self, camera):
        """Set the camera reference for coordinate transformations.
        
        Args:
            camera: The game's camera instance
        """
        self.camera = camera

    def _get_spawn_position(self, offset_distance=0, angle_offset=0):
        """Get the spawn position for projectiles and bubbles relative to the submarine's center.
        
        Args:
            offset_distance (float): Distance from center to spawn point
            angle_offset (float): Angle offset from sub's rotation
            
        Returns:
            tuple: (spawn_x, spawn_y) coordinates in world space
        """
        if not self.entity:
            return (0, 0)
            
        # Calculate spawn point using polar coordinates
        angle_rad = math.radians(self.entity.rotation + angle_offset)
        spawn_x = self.entity.x + offset_distance * math.cos(angle_rad)
        spawn_y = self.entity.y + offset_distance * math.sin(angle_rad)
        
        return spawn_x, spawn_y    
    
    def get_center_position(self):
        """Get the submarine's center position (where the red dot appears).
        
        Returns:
            tuple: (x, y) coordinates of the center in world space
        """
        if not self.camera:
            return self.entity.x, self.entity.y
            
        # Get the screen center (where red dot is drawn)
        screen_x = self.camera.width // 2
        screen_y = self.camera.height // 2
        
        # Convert to world coordinates
        return self.camera.screen_to_world(screen_x, screen_y)

    def _spawn_bubble(self):
        """Spawn a new bubble behind the submarine."""
        if not self.entity:
            return
              # Get the exact position of the red dot
        spawn_x, spawn_y = self.get_center_position()
        
        # Bubbles always move straight up
        move_angle = 90
        
        # Create new bubble
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
              # Get center position and calculate bubble position relative to it
            center_x, center_y = self.get_center_position()
            spawn_x = center_x + distance * math.cos(angle_rad)
            spawn_y = center_y + distance * math.sin(angle_rad)
            
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
              # Get the exact position of the red dot
        spawn_x, spawn_y = self.get_center_position()
        
        # Create the cannonball
        ball = Cannonball(
            x=spawn_x,
            y=spawn_y,            
            image_path="assets/images/cannonball-3x3x2.png",
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

        # Update previous boost state for next frame
        self.previous_boost_state = self.boost_active
    
    def update_legacy(self, keys, *args, **kwargs):
        """Legacy update method for backward compatibility.
        
        This method converts the old keys dictionary format to the new InputState format.
        This can be removed once all calling code is updated.
        
        Args:
            keys: Dictionary of key states from pygame.key.get_pressed()
            *args: Additional arguments including mouse buttons
            **kwargs: Additional keyword arguments
        """
        # Create a temporary InputState from the legacy keys
        # We'll define a simple class here to avoid import issues
        class TempInputState:
            def __init__(self):
                self.forward = False
                self.backward = False
                self.turn_left = False
                self.turn_right = False
                self.boost_teleport = False
                self.left_mouse = False
                self.right_mouse = False
                self.middle_mouse = False
        
        input_state = TempInputState()
        
        # Convert pygame key constants to InputState attributes
        from pygame import K_z, K_q, K_s, K_d, K_SPACE
        
        input_state.forward = keys.get(K_z, False)
        input_state.backward = keys.get(K_s, False)
        input_state.turn_left = keys.get(K_q, False)
        input_state.turn_right = keys.get(K_d, False)
        input_state.boost_teleport = keys.get(K_SPACE, False)
        
        # Handle mouse buttons
        mouse_buttons = kwargs.get('mouse_buttons', [False, False, False])
        input_state.left_mouse = mouse_buttons[0] if len(mouse_buttons) > 0 else False
        input_state.right_mouse = mouse_buttons[2] if len(mouse_buttons) > 2 else False
        input_state.middle_mouse = mouse_buttons[1] if len(mouse_buttons) > 1 else False
        
        # Call the new update method
        self.update(input_state, *args, **kwargs)
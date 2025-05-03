class ShadowManager:
    """Class to manage shadow configurations across game objects."""
    
    def __init__(self, enabled=True):
        """Initialize the shadow manager.
        
        Args:
            enabled (bool): Whether shadows are enabled by default
        """
        self.enabled = enabled
        self.game_objects = []  # List of objects using this shadow manager
        
    def register_object(self, obj):
        """Register a game object to be managed by this shadow manager.
        
        Args:
            obj: GameObject or Entity with a configure_shadow method
        """
        if obj not in self.game_objects:
            self.game_objects.append(obj)
        
    def register_objects(self, objects):
        """Register multiple game objects at once.
        
        Args:
            objects: List of GameObjects or Entities with configure_shadow methods
        """
        for obj in objects:
            self.register_object(obj)
    
    def update_all(self, sun):
        """Update shadows for all registered objects based on sun position.
        
        Args:
            sun: Sun object with horizontal_angle and vertical_angle properties
        """
        for obj in self.game_objects:
            if hasattr(obj, 'configure_shadow'):
                obj.configure_shadow(
                    sun.horizontal_angle,
                    sun.vertical_angle,
                    self.enabled
                )
                
    def toggle_shadows(self):
        """Toggle whether shadows are enabled."""
        self.enabled = not self.enabled
        return self.enabled
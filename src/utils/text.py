from pygame import font

class Text:
    """Utility class for rendering text in pygame."""
    
    def __init__(self, text_font, size, message, color, xpos, ypos):
        """Initialize text object.
        
        Args:
            text_font: Path to font file or None for system font
            size (int): Font size
            message (str): Text to display
            color: RGB tuple for text color
            xpos (int): X position of text
            ypos (int): Y position of text
        """
        if text_font:
            self.font = font.Font(text_font, size)
        else:
            self.font = font.SysFont(None, size)
            
        self.surface = self.font.render(message, True, color)
        self.rect = self.surface.get_rect(topleft=(xpos, ypos))
    
    def draw(self, surface):
        """Draw the text on the given surface.
        
        Args:
            surface: The pygame surface to draw on
        """
        surface.blit(self.surface, self.rect)
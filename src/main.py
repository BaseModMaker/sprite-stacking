"""
Main entry point for the Sprite Stacking game.
"""
import os
import sys
import asyncio
import pygame

# Add the src directory to sys.path to allow relative imports
sys.path.append(os.path.dirname(__file__))

# Import the Game class directly
from game import Game


async def main():
    # Initialize pygame to get display info
    pygame.init()
    
    # Setup paths - make them work both locally and on web
    if hasattr(sys, '_emscripten_info'):
        # Web/pygbag environment
        base_dir = "."
        asset_dir = "assets"
        
        # For web, get actual browser window dimensions using JavaScript
        from platform import window
        screen_width = window.innerWidth
        screen_height = window.innerHeight
        
        # Set up the display to match browser window exactly
        pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
    else:
        # Local environment
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        asset_dir = os.path.join(base_dir, "assets")
        
        # Get the primary display's current resolution
        screen_info = pygame.display.Info()
        screen_width = screen_info.current_w
        screen_height = screen_info.current_h
    
    font_dir = os.path.join(asset_dir, "fonts")
    image_dir = os.path.join(asset_dir, "images")
    sound_dir = os.path.join(asset_dir, "sounds")
    
    print(f"Screen resolution: {screen_width}x{screen_height}")
    print(f"Asset path: {asset_dir}")
    print(f"Image path: {image_dir}")
    print(f"Font path: {font_dir}")
    
    # Create and run the game
    # Set lower performance mode for web platform to improve performance
    default_performance_mode = 0 if hasattr(sys, '_emscripten_info') else 1
    
    game = Game(
        screen_width=screen_width, 
        screen_height=screen_height,
        fullscreen=False,  # Disable fullscreen mode
        asset_path=asset_dir,
        font_path=font_dir,
        image_path=image_dir,
        performance_mode=default_performance_mode
    )
    
    # Run game loop
    await game.main()


if __name__ == "__main__":
    # Entry point that works both locally and in pygbag
    asyncio.run(main())

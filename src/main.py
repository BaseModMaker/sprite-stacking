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
    # Setup paths - make them work both locally and on web
    if hasattr(sys, '_emscripten_info'):
        # Web/pygbag environment
        base_dir = "."
        asset_dir = "assets"
    else:
        # Local environment
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        asset_dir = os.path.join(base_dir, "assets")
    
    font_dir = os.path.join(asset_dir, "fonts")
    image_dir = os.path.join(asset_dir, "images")
    sound_dir = os.path.join(asset_dir, "sounds")
    
    # Create and run the game with web-friendly resolution 
    # Use a smaller size for better performance in browser
    game = Game(
        screen_width=800, 
        screen_height=600,
        fullscreen=False,  # Fullscreen not supported in browser
        asset_path=asset_dir,
        font_path=font_dir,
        image_path=image_dir
    )
    
    # Run game loop
    await game.main()


if __name__ == "__main__":
    # Entry point that works both locally and in pygbag
    asyncio.run(main())

"""
Main entry point for the Sprite Stacking game.
"""
import os
import sys
import asyncio

# Add the src directory to sys.path to allow relative imports
sys.path.append(os.path.dirname(__file__))

# Import the Game class directly
from game import Game


def main():
    # Setup paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    asset_dir = os.path.join(base_dir, "assets")
    font_dir = os.path.join(asset_dir, "fonts")
    image_dir = os.path.join(asset_dir, "images")
    sound_dir = os.path.join(asset_dir, "sounds")
    
    # Create and run the game
    game = Game(
        screen_width=1280, 
        screen_height=720,
        fullscreen=False,
        asset_path=asset_dir,
        font_path=font_dir,
        image_path=image_dir
    )
    
    # Run game loop
    asyncio.run(game.main())


if __name__ == "__main__":
    main()

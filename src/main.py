"""
Main entry point for the Sprite Stacking game.
"""
import os
import sys
import asyncio
import platform

# Add the src directory to sys.path to allow relative imports
sys.path.append(os.path.dirname(__file__))

# Import the Game class directly
from game import Game


async def main():
    """Main entry point for the game, using async for web compatibility."""
    # Setup paths based on platform
    if platform.system() == "Emscripten":
        # Web environment - paths are relative to HTML file
        base_dir = ""
        asset_dir = "assets"
        font_dir = "assets/fonts"
        image_dir = "assets/images"
        sound_dir = "assets/sounds"
        print("Running in web environment with simplified paths")
    else:
        # Desktop environment - use absolute paths
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        asset_dir = os.path.join(base_dir, "assets")
        font_dir = os.path.join(asset_dir, "fonts")
        image_dir = os.path.join(asset_dir, "images")
        sound_dir = os.path.join(asset_dir, "sounds")
        print(f"Running on desktop with base path: {base_dir}")
    
    # Print paths for debugging
    print(f"Asset path: {asset_dir}")
    print(f"Font path: {font_dir}")
    print(f"Image path: {image_dir}")
    print(f"Sound path: {sound_dir}")
    
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
    await game.main()


# This is the correct way to run asyncio on both desktop and web
if __name__ == "__main__":
    if platform.system() == "Emscripten":
        # For web deployment
        asyncio.run(main())
    else:
        # For desktop
        asyncio.run(main())

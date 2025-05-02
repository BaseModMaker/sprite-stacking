"""
Main entry point for the Sprite Stacking game.
"""
import os
import sys
import asyncio
import platform
import pygame

# Add the src directory to sys.path to allow relative imports
sys.path.append(os.path.dirname(__file__))

# Import the Game class directly
from game import Game


async def preload_assets(image_dir):
    """Preload assets to ensure they're in the cache before game starts."""
    preloaded = {}
    print(f"=== ASSET PRELOADING STARTING from {image_dir} ===")
    
    # Get list of image files in the directory
    try:
        if platform.system() == "Emscripten":
            # For web, hardcode the list of expected assets
            image_files = ["cars-1.png", "background.jpg"]
            for img_file in image_files:
                full_path = f"{image_dir}/{img_file}"
                try:
                    print(f"Preloading: {full_path}")
                    img = pygame.image.load(full_path)
                    preloaded[img_file] = img
                    print(f"Successfully preloaded: {img_file} ({img.get_width()}x{img.get_height()})")
                except Exception as e:
                    print(f"Failed to preload {img_file}: {e}")
        else:
            # For desktop, scan the directory
            for img_file in os.listdir(image_dir):
                if img_file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    full_path = os.path.join(image_dir, img_file)
                    try:
                        img = pygame.image.load(full_path)
                        preloaded[img_file] = img
                        print(f"Successfully preloaded: {img_file}")
                    except Exception as e:
                        print(f"Failed to preload {img_file}: {e}")
    except Exception as e:
        print(f"Error during asset preloading: {e}")
    
    print(f"=== ASSET PRELOADING COMPLETE: {len(preloaded)} assets loaded ===")
    return preloaded


async def main():
    """Main entry point for the game, using async for web compatibility."""
    # Initialize pygame early for asset loading
    pygame.init()
    
    # Setup paths based on platform
    if platform.system() == "Emscripten":
        # Web environment - paths are relative to HTML file
        base_dir = ""
        asset_dir = "assets"
        font_dir = "assets/fonts"
        image_dir = "assets/images"
        sound_dir = "assets/sounds"
        print(f"Running in web environment ({platform.system()}) with simplified paths")
    else:
        # Desktop environment - use absolute paths
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        asset_dir = os.path.join(base_dir, "assets")
        font_dir = os.path.join(asset_dir, "fonts")
        image_dir = os.path.join(asset_dir, "images")
        sound_dir = os.path.join(asset_dir, "sounds")
        print(f"Running on desktop ({platform.system()}) with base path: {base_dir}")
    
    # Print paths for debugging
    print(f"Asset path: {asset_dir}")
    print(f"Font path: {font_dir}")
    print(f"Image path: {image_dir}")
    print(f"Sound path: {sound_dir}")
    
    # Preload assets before creating game
    preloaded_assets = await preload_assets(image_dir)
    
    # Create and run the game
    game = Game(
        screen_width=1280, 
        screen_height=720,
        fullscreen=False,
        asset_path=asset_dir,
        font_path=font_dir,
        image_path=image_dir,
        preloaded_assets=preloaded_assets
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

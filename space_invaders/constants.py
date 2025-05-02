from pygame import display, image
from os.path import abspath, dirname, join

# loading base paths
BASE_PATH = abspath(dirname(__file__))
FONT_PATH = join(BASE_PATH, "fonts")
IMAGE_PATH = join(BASE_PATH, "images")
SOUND_PATH = join(BASE_PATH, "sounds")

# Colors (R, G, B)
WHITE = (255, 255, 255)
GREEN = (78, 255, 87)
YELLOW = (241, 255, 0)
BLUE = (80, 255, 239)
PURPLE = (203, 0, 255)
RED = (237, 28, 36)

SCREEN = display.set_mode((800, 600))
FONT = join(FONT_PATH, "space_invaders.ttf")
IMG_NAMES = [
    "ship",
    "mystery",
    "enemy1_1",
    "enemy1_2",
    "enemy2_1",
    "enemy2_2",
    "enemy3_1",
    "enemy3_2",
    "explosionblue",
    "explosiongreen",
    "explosionpurple",
    "laser",
    "enemylaser",
]
IMAGES = {
    name: image.load(join(IMAGE_PATH, f"{name}.png")).convert_alpha()
    for name in IMG_NAMES
}

BLOCKERS_POSITION = 450
ENEMY_DEFAULT_POSITION = 65  # Initial value for a new game
ENEMY_MOVE_DOWN = 35

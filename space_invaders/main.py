from pygame import (
    sprite,
    transform,
    mixer,
    time,
    Surface,
    font,
    K_RIGHT,
    K_LEFT,
    K_UP,
    K_DOWN,
    display,
    image,
    transform,
    event,
    mixer,
    time,
    KEYUP,
    KEYDOWN,
    K_ESCAPE,
    K_SPACE,
    QUIT,
    init,
    key,
    math,
    SRCALPHA,
    draw,
    Rect,
)
import pygame  # Add explicit pygame import for direct access
import sys
from os.path import abspath, dirname, join, exists
from random import choice
import asyncio
import math
import numpy as np
from PIL import Image

BASE_PATH = abspath(dirname(__file__))
FONT_PATH = join(BASE_PATH, "fonts")
IMAGE_PATH = join(BASE_PATH, "images")
SOUND_PATH = join(BASE_PATH, "sounds")
SOUND_FORMAT = "ogg"

# Colors (R, G, B)
WHITE = (255, 255, 255)
GREEN = (78, 255, 87)
YELLOW = (241, 255, 0)
BLUE = (80, 255, 239)
PURPLE = (203, 0, 255)
RED = (237, 28, 36)
BLACK = (0, 0, 0)

# Car configuration constants
CAR_WIDTH = 15
CAR_HEIGHT = 31
CAR_LAYERS = 14
CAR_LAYER_OFFSET = 1  # Vertical pixels between each layer

SCREEN = display.set_mode((800, 600))
FONT = join(FONT_PATH, "space_invaders.ttf")

# Create empty placeholder images for missing files
def create_placeholder(size=(40, 40), color=(255, 255, 255)):
    surf = Surface(size, SRCALPHA)
    surf.fill((0, 0, 0, 0))  # Transparent background
    draw.rect(surf, color, Rect(5, 5, size[0]-10, size[1]-10))
    return surf

# Image loading with fallback to placeholder
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

# Load images with placeholder fallbacks for missing files
IMAGES = {}
for name in IMG_NAMES:
    img_path = join(IMAGE_PATH, f"{name}.png")
    if exists(img_path):
        IMAGES[name] = image.load(img_path).convert_alpha()
    else:
        # Create a placeholder for missing image
        color = choice([RED, GREEN, BLUE, PURPLE, YELLOW])
        if "laser" in name:
            IMAGES[name] = create_placeholder((5, 15), color)
        elif "explosion" in name:
            IMAGES[name] = create_placeholder((40, 40), color)
        else:
            IMAGES[name] = create_placeholder((40, 40), color)

# Ensure car image is loaded
CAR_IMAGE_PATH = join(IMAGE_PATH, "cars-1.png")
CAR_IMAGE = None
if exists(CAR_IMAGE_PATH):
    try:
        CAR_IMAGE = image.load(CAR_IMAGE_PATH).convert_alpha()
    except Exception as e:
        print(f"Error loading car image: {e}")

BLOCKERS_POSITION = 450
ENEMY_DEFAULT_POSITION = 65  # Initial value for a new game
ENEMY_MOVE_DOWN = 35
DIFFICULTY_LEVEL = 5  # a value between 1 to 10 - number of enemy bullets


class Ship(sprite.Sprite):
    def __init__(self):
        sprite.Sprite.__init__(self)
        self.image = IMAGES["ship"]
        self.rect = self.image.get_rect(topleft=(375, 540))
        self.speed = 5

    def update(self, keys, *args):
        if keys[K_LEFT] and self.rect.x > 10:
            self.rect.x -= self.speed
        if keys[K_RIGHT] and self.rect.x < 740:
            self.rect.x += self.speed
        game.screen.blit(self.image, self.rect)


class Bullet(sprite.Sprite):
    def __init__(self, xpos, ypos, direction, speed, filename, side):
        sprite.Sprite.__init__(self)
        self.image = IMAGES[filename]
        self.rect = self.image.get_rect(topleft=(xpos, ypos))
        self.speed = speed
        self.direction = direction
        self.side = side
        self.filename = filename

    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)
        self.rect.y += self.speed * self.direction
        if self.rect.y < 15 or self.rect.y > 600:
            self.kill()


class Enemy(sprite.Sprite):
    def __init__(self, row, column):
        sprite.Sprite.__init__(self)
        self.row = row
        self.column = column
        self.images = []
        self.load_images()
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()

    def toggle_image(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

    def update(self, *args):
        game.screen.blit(self.image, self.rect)

    def load_images(self):
        images = {
            0: ["1_2", "1_1"],
            1: ["2_2", "2_1"],
            2: ["2_2", "2_1"],
            3: ["3_1", "3_2"],
            4: ["3_1", "3_2"],
        }
        img1, img2 = (IMAGES["enemy{}".format(img_num)] for img_num in images[self.row])
        self.images.append(transform.scale(img1, (40, 35)))
        self.images.append(transform.scale(img2, (40, 35)))


class EnemiesGroup(sprite.Group):
    def __init__(self, columns, rows):
        sprite.Group.__init__(self)
        self.enemies = [[None] * columns for _ in range(rows)]
        self.columns = columns
        self.rows = rows
        self.leftAddMove = 0
        self.rightAddMove = 0
        self.moveTime = 600
        self.direction = 1
        self.rightMoves = 30
        self.leftMoves = 30
        self.moveNumber = 15
        self.timer = time.get_ticks()
        self.bottom = game.enemyPosition + ((rows - 1) * 45) + 35
        self._aliveColumns = list(range(columns))
        self._leftAliveColumn = 0
        self._rightAliveColumn = columns - 1

    def update(self, current_time):
        if current_time - self.timer > self.moveTime:
            if self.direction == 1:
                max_move = self.rightMoves + self.rightAddMove
            else:
                max_move = self.leftMoves + self.leftAddMove

            if self.moveNumber >= max_move:
                self.leftMoves = 30 + self.rightAddMove
                self.rightMoves = 30 + self.leftAddMove
                self.direction *= -1
                self.moveNumber = 0
                self.bottom = 0
                for enemy in self:
                    enemy.rect.y += ENEMY_MOVE_DOWN
                    enemy.toggle_image()
                    if self.bottom < enemy.rect.y + 35:
                        self.bottom = enemy.rect.y + 35
            else:
                velocity = 10 if self.direction == 1 else -10
                for enemy in self:
                    enemy.rect.x += velocity
                    enemy.toggle_image()
                self.moveNumber += 1

            self.timer += self.moveTime

    def add_internal(self, *sprites):
        super(EnemiesGroup, self).add_internal(*sprites)
        for s in sprites:
            self.enemies[s.row][s.column] = s

    def remove_internal(self, *sprites):
        super(EnemiesGroup, self).remove_internal(*sprites)
        for s in sprites:
            self.kill(s)
        self.update_speed()

    def is_column_dead(self, column):
        return not any(self.enemies[row][column] for row in range(self.rows))

    def random_bottom(self):
        col = choice(self._aliveColumns)
        col_enemies = (self.enemies[row - 1][col] for row in range(self.rows, 0, -1))
        return next((en for en in col_enemies if en is not None), None)

    def update_speed(self):
        if len(self) == 1:
            self.moveTime = 200
        elif len(self) <= 10:
            self.moveTime = 400

    def kill(self, enemy):
        self.enemies[enemy.row][enemy.column] = None
        is_column_dead = self.is_column_dead(enemy.column)
        if is_column_dead:
            self._aliveColumns.remove(enemy.column)

        if enemy.column == self._rightAliveColumn:
            while self._rightAliveColumn > 0 and is_column_dead:
                self._rightAliveColumn -= 1
                self.rightAddMove += 5
                is_column_dead = self.is_column_dead(self._rightAliveColumn)

        elif enemy.column == self._leftAliveColumn:
            while self._leftAliveColumn < self.columns and is_column_dead:
                self._leftAliveColumn += 1
                self.leftAddMove += 5
                is_column_dead = self.is_column_dead(self._leftAliveColumn)


class Blocker(sprite.Sprite):
    def __init__(self, size, color, row, column):
        sprite.Sprite.__init__(self)
        self.height = size
        self.width = size
        self.color = color
        self.image = Surface((self.width, self.height))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.row = row
        self.column = column

    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)


class Mystery(sprite.Sprite):
    def __init__(self):
        sprite.Sprite.__init__(self)
        self.image = IMAGES["mystery"]
        self.image = transform.scale(self.image, (75, 35))
        self.rect = self.image.get_rect(topleft=(-80, 45))
        self.row = 5
        self.moveTime = 25000
        self.direction = 1
        self.timer = time.get_ticks()
        self.mysteryEntered = mixer.Sound(join(SOUND_PATH, f"mysteryentered.{SOUND_FORMAT}"))
        self.mysteryEntered.set_volume(0.3)
        self.playSound = True

    def update(self, keys, currentTime, *args):
        resetTimer = False
        passed = currentTime - self.timer
        if passed > self.moveTime:
            if (self.rect.x < 0 or self.rect.x > 800) and self.playSound:
                self.mysteryEntered.play()
                self.playSound = False
            if self.rect.x < 840 and self.direction == 1:
                self.mysteryEntered.fadeout(4000)
                self.rect.x += 2
                game.screen.blit(self.image, self.rect)
            if self.rect.x > -100 and self.direction == -1:
                self.mysteryEntered.fadeout(4000)
                self.rect.x -= 2
                game.screen.blit(self.image, self.rect)

        if self.rect.x > 830:
            self.playSound = True
            self.direction = -1
            resetTimer = True
        if self.rect.x < -90:
            self.playSound = True
            self.direction = 1
            resetTimer = True
        if passed > self.moveTime and resetTimer:
            self.timer = currentTime


class EnemyExplosion(sprite.Sprite):
    def __init__(self, enemy, *groups):
        super(EnemyExplosion, self).__init__(*groups)
        self.image = transform.scale(self.get_image(enemy.row), (40, 35))
        self.image2 = transform.scale(self.get_image(enemy.row), (50, 45))
        self.rect = self.image.get_rect(topleft=(enemy.rect.x, enemy.rect.y))
        self.timer = time.get_ticks()

    @staticmethod
    def get_image(row):
        img_colors = ["purple", "blue", "blue", "green", "green"]
        return IMAGES["explosion{}".format(img_colors[row])]

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 100:
            game.screen.blit(self.image, self.rect)
        elif passed <= 200:
            game.screen.blit(self.image2, (self.rect.x - 6, self.rect.y - 6))
        elif 400 < passed:
            self.kill()


class MysteryExplosion(sprite.Sprite):
    def __init__(self, mystery, score, *groups):
        super(MysteryExplosion, self).__init__(*groups)
        self.text = Text(
            FONT, 20, str(score), WHITE, mystery.rect.x + 20, mystery.rect.y + 6
        )
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 200 or 400 < passed <= 600:
            self.text.draw(game.screen)
        elif 600 < passed:
            self.kill()


class ShipExplosion(sprite.Sprite):
    def __init__(self, ship, *groups):
        super(ShipExplosion, self).__init__(*groups)
        self.image = IMAGES["ship"]
        self.rect = self.image.get_rect(topleft=(ship.rect.x, ship.rect.y))
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if 300 < passed <= 600:
            game.screen.blit(self.image, self.rect)
        elif 900 < passed:
            self.kill()


class Life(sprite.Sprite):
    def __init__(self, xpos, ypos):
        sprite.Sprite.__init__(self)
        self.image = IMAGES["ship"]
        self.image = transform.scale(self.image, (23, 23))
        self.rect = self.image.get_rect(topleft=(xpos, ypos))

    def update(self, *args):
        game.screen.blit(self.image, self.rect)


class Text(object):
    def __init__(self, textFont, size, message, color, xpos, ypos):
        self.font = font.Font(textFont, size)
        self.surface = self.font.render(message, True, color)
        self.rect = self.surface.get_rect(topleft=(xpos, ypos))

    def draw(self, surface):
        surface.blit(self.surface, self.rect)


class SpaceInvaders(object):
    def __init__(self):
        # It seems, in Linux buffersize=512 is not enough, use 4096 to prevent:
        #   ALSA lib pcm.c:7963:(snd_pcm_recover) underrun occurred
        mixer.pre_init(44100, -16, 1, 4096)
        init()
        self.clock = time.Clock()
        self.caption = display.set_caption("Space Invaders")
        self.screen = SCREEN
        self.background = image.load(join(IMAGE_PATH, "background.jpg")).convert()
        self.startGame = False
        self.mainScreen = True
        self.gameOver = False
        # Counter for enemy starting position (increased each new round)
        self.enemyPosition = ENEMY_DEFAULT_POSITION
        self.titleText = Text(FONT, 50, "Space Invaders", WHITE, 164, 120)
        self.titleText2 = Text(FONT, 25, "Press any key to continue", WHITE, 201, 205)
        self.gameOverText = Text(FONT, 50, "Game Over", WHITE, 250, 270)
        self.nextRoundText = Text(FONT, 50, "Next Round", WHITE, 240, 270)
        self.enemy1Text = Text(FONT, 25, "   =   10 pts", GREEN, 368, 270)
        self.enemy2Text = Text(FONT, 25, "   =  20 pts", BLUE, 368, 320)
        self.enemy3Text = Text(FONT, 25, "   =  30 pts", PURPLE, 368, 370)
        self.enemy4Text = Text(FONT, 25, "   =  ?????", RED, 368, 420)
        self.scoreText = Text(FONT, 20, "Score", WHITE, 5, 5)
        self.livesText = Text(FONT, 20, "Lives ", WHITE, 640, 5)
        self.creator_name = Text(FONT, 20, "Sandy Inspires", GREEN, 600, 570)

        self.life1 = Life(715, 3)
        self.life2 = Life(742, 3)
        self.life3 = Life(769, 3)
        self.livesGroup = sprite.Group(self.life1, self.life2, self.life3)

    def reset(self, score):
        self.player = Ship()
        self.playerGroup = sprite.Group(self.player)
        self.explosionsGroup = sprite.Group()
        self.bullets = sprite.Group()
        self.mysteryShip = Mystery()
        self.mysteryGroup = sprite.Group(self.mysteryShip)
        self.enemyBullets = sprite.Group()
        self.make_enemies()
        self.allSprites = sprite.Group(
            self.player, self.enemies, self.livesGroup, self.mysteryShip
        )
        self.keys = key.get_pressed()

        self.timer = time.get_ticks()
        self.noteTimer = time.get_ticks()
        self.shipTimer = time.get_ticks()
        self.score = score
        self.create_audio()
        self.makeNewShip = False
        self.shipAlive = True

    def make_blockers(self, number):
        blockerGroup = sprite.Group()
        for row in range(4):
            for column in range(9):
                blocker = Blocker(10, GREEN, row, column)
                blocker.rect.x = 50 + (200 * number) + (column * blocker.width)
                blocker.rect.y = BLOCKERS_POSITION + (row * blocker.height)
                blockerGroup.add(blocker)
        return blockerGroup

    def create_audio(self):
        self.sounds = {}
        for sound_name in [
            "shoot",
            "shoot2",
            "invaderkilled",
            "mysterykilled",
            "shipexplosion",
        ]:
            self.sounds[sound_name] = mixer.Sound(
                join(SOUND_PATH, f"{sound_name}.{SOUND_FORMAT}")
            )
            self.sounds[sound_name].set_volume(0.2)

        self.musicNotes = [
            mixer.Sound(join(SOUND_PATH, f"{i}.{SOUND_FORMAT}")) for i in range(4)
        ]
        for sound in self.musicNotes:
            sound.set_volume(0.5)

        self.noteIndex = 0

    def play_main_music(self, currentTime):
        if currentTime - self.noteTimer > self.enemies.moveTime:
            self.note = self.musicNotes[self.noteIndex]
            if self.noteIndex < 3:
                self.noteIndex += 1
            else:
                self.noteIndex = 0

            self.note.play()
            self.noteTimer += self.enemies.moveTime

    @staticmethod
    def should_exit(evt):
        return evt.type == QUIT or (evt.type == KEYUP and evt.key == K_ESCAPE)

    def check_input(self):
        self.keys = key.get_pressed()
        for e in event.get():
            if self.should_exit(e):
                sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_SPACE:
                    if len(self.bullets) == 0 and self.shipAlive:
                        if self.score <= 100:
                            bullet = Bullet(
                                self.player.rect.x + 23,
                                self.player.rect.y + 5,
                                -1,
                                15,
                                "laser",
                                "center",
                            )
                            self.bullets.add(bullet)
                            self.allSprites.add(self.bullets)
                            self.sounds["shoot"].play()
                        elif self.score > 100 and self.score <= 200:
                            leftbullet = Bullet(
                                self.player.rect.x + 8,
                                self.player.rect.y + 5,
                                -1,
                                15,
                                "laser",
                                "left",
                            )
                            right_bullet = Bullet(
                                self.player.rect.x + 38,
                                self.player.rect.y + 5,
                                -1,
                                15,
                                "laser",
                                "right",
                            )
                            self.bullets.add(leftbullet)
                            self.bullets.add(right_bullet)
                            self.allSprites.add(self.bullets)
                            self.sounds["shoot2"].play()

                        else:
                            left_bullet = Bullet(
                                self.player.rect.x + 8,
                                self.player.rect.y + 5,
                                -1,
                                15,
                                "laser",
                                "left",
                            )
                            right_bullet = Bullet(
                                self.player.rect.x + 38,
                                self.player.rect.y + 5,
                                -1,
                                15,
                                "laser",
                                "right",
                            )
                            center_bullet = Bullet(
                                self.player.rect.x + 23,
                                self.player.rect.y + 5,
                                -1,
                                15,
                                "laser",
                                "center",
                            )
                            self.bullets.add(left_bullet)
                            self.bullets.add(center_bullet)
                            self.bullets.add(right_bullet)
                            self.allSprites.add(self.bullets)
                            self.sounds["shoot2"].play()

    def make_enemies(self):
        enemies = EnemiesGroup(10, 5)
        for row in range(5):
            for column in range(10):
                enemy = Enemy(row, column)
                enemy.rect.x = 157 + (column * 50)
                enemy.rect.y = self.enemyPosition + (row * 45)
                enemies.add(enemy)

        self.enemies = enemies

    def make_enemies_shoot(self):
        if (time.get_ticks() - self.timer) > 700 and self.enemies:
            enemy = self.enemies.random_bottom()
            self.enemyBullets.add(
                Bullet(
                    enemy.rect.x + 14, enemy.rect.y + 20, 1, 5, "enemylaser", "center"
                )
            )
            self.allSprites.add(self.enemyBullets)
            self.timer = time.get_ticks()

    def calculate_score(self, row):
        scores = {0: 30, 1: 20, 2: 20, 3: 10, 4: 10, 5: choice([50, 100, 150, 300])}

        score = scores[row]
        self.score += score
        return score

    def create_main_menu(self):
        self.enemy1 = IMAGES["enemy3_1"]
        self.enemy1 = transform.scale(self.enemy1, (40, 40))
        self.enemy2 = IMAGES["enemy2_2"]
        self.enemy2 = transform.scale(self.enemy2, (40, 40))
        self.enemy3 = IMAGES["enemy1_2"]
        self.enemy3 = transform.scale(self.enemy3, (40, 40))
        self.enemy4 = IMAGES["mystery"]
        self.enemy4 = transform.scale(self.enemy4, (80, 40))
        self.screen.blit(self.enemy1, (318, 270))
        self.screen.blit(self.enemy2, (318, 320))
        self.screen.blit(self.enemy3, (318, 370))
        self.screen.blit(self.enemy4, (299, 420))

    def check_collisions(self):
        sprite.groupcollide(self.bullets, self.enemyBullets, True, True)

        for enemy in sprite.groupcollide(self.enemies, self.bullets, True, True).keys():
            self.sounds["invaderkilled"].play()
            self.calculate_score(enemy.row)
            EnemyExplosion(enemy, self.explosionsGroup)
            self.gameTimer = time.get_ticks()

        for mystery in sprite.groupcollide(
            self.mysteryGroup, self.bullets, True, True
        ).keys():
            mystery.mysteryEntered.stop()
            self.sounds["mysterykilled"].play()
            score = self.calculate_score(mystery.row)
            MysteryExplosion(mystery, score, self.explosionsGroup)
            newShip = Mystery()
            self.allSprites.add(newShip)
            self.mysteryGroup.add(newShip)

        for player in sprite.groupcollide(
            self.playerGroup, self.enemyBullets, True, True
        ).keys():
            if self.life3.alive():
                self.life3.kill()
            elif self.life2.alive():
                self.life2.kill()
            elif self.life1.alive():
                self.life1.kill()
            else:
                self.gameOver = True
                self.startGame = False
            self.sounds["shipexplosion"].play()
            ShipExplosion(player, self.explosionsGroup)
            self.makeNewShip = True
            self.shipTimer = time.get_ticks()
            self.shipAlive = False

        if self.enemies.bottom >= 540:
            sprite.groupcollide(self.enemies, self.playerGroup, True, True)
            if not self.player.alive() or self.enemies.bottom >= 600:
                self.gameOver = True
                self.startGame = False

        sprite.groupcollide(self.bullets, self.allBlockers, True, True)
        sprite.groupcollide(self.enemyBullets, self.allBlockers, True, True)
        if self.enemies.bottom >= BLOCKERS_POSITION:
            sprite.groupcollide(self.enemies, self.allBlockers, False, True)

    def create_new_ship(self, createShip, currentTime):
        if createShip and (currentTime - self.shipTimer > 900):
            self.player = Ship()
            self.allSprites.add(self.player)
            self.playerGroup.add(self.player)
            self.makeNewShip = False
            self.shipAlive = True

    def create_game_over(self, currentTime):
        self.screen.blit(self.background, (0, 0))
        passed = currentTime - self.timer
        if passed < 750:
            self.gameOverText.draw(self.screen)
        elif 750 < passed < 1500:
            self.screen.blit(self.background, (0, 0))
        elif 1500 < passed < 2250:
            self.gameOverText.draw(self.screen)
        elif 2250 < passed < 2750:
            self.screen.blit(self.background, (0, 0))
        elif passed > 3000:
            self.mainScreen = True

        for e in event.get():
            if self.should_exit(e):
                sys.exit()

    async def main(self):
        while True:
            if self.mainScreen:
                self.screen.blit(self.background, (0, 0))
                self.titleText.draw(self.screen)
                self.titleText2.draw(self.screen)
                self.enemy1Text.draw(self.screen)
                self.enemy2Text.draw(self.screen)
                self.enemy3Text.draw(self.screen)
                self.enemy4Text.draw(self.screen)
                self.creator_name.draw(self.screen)
                self.create_main_menu()
                for e in event.get():
                    if self.should_exit(e):
                        sys.exit()
                    if e.type == KEYUP:
                        # Only create blockers on a new game, not a new round
                        self.allBlockers = sprite.Group(
                            self.make_blockers(0),
                            self.make_blockers(1),
                            self.make_blockers(2),
                            self.make_blockers(3),
                        )
                        self.livesGroup.add(self.life1, self.life2, self.life3)
                        self.reset(0)
                        self.startGame = True
                        self.mainScreen = False

            elif self.startGame:
                if not self.enemies and not self.explosionsGroup:
                    currentTime = time.get_ticks()
                    if currentTime - self.gameTimer < 3000:
                        self.screen.blit(self.background, (0, 0))
                        self.scoreText2 = Text(FONT, 20, str(self.score), GREEN, 85, 5)
                        self.scoreText.draw(self.screen)
                        self.scoreText2.draw(self.screen)
                        self.nextRoundText.draw(self.screen)
                        self.livesText.draw(self.screen)
                        self.livesGroup.update()
                        self.check_input()
                        self.creator_name.draw(self.screen)
                    if currentTime - self.gameTimer > 3000:
                        # Move enemies closer to bottom
                        self.enemyPosition += ENEMY_MOVE_DOWN
                        self.reset(self.score)
                        self.gameTimer += 3000
                else:
                    currentTime = time.get_ticks()
                    self.play_main_music(currentTime)
                    self.screen.blit(self.background, (0, 0))
                    self.allBlockers.update(self.screen)
                    self.scoreText2 = Text(FONT, 20, str(self.score), GREEN, 85, 5)
                    self.scoreText.draw(self.screen)
                    self.scoreText2.draw(self.screen)
                    self.livesText.draw(self.screen)
                    self.check_input()
                    self.enemies.update(currentTime)
                    self.allSprites.update(self.keys, currentTime)
                    self.explosionsGroup.update(currentTime)
                    self.check_collisions()
                    self.create_new_ship(self.makeNewShip, currentTime)
                    self.make_enemies_shoot()
                    self.creator_name.draw(self.screen)

            elif self.gameOver:
                currentTime = time.get_ticks()
                # Reset enemy starting position
                self.enemyPosition = ENEMY_DEFAULT_POSITION
                self.create_game_over(currentTime)

            display.update()
            self.clock.tick(60)
            await asyncio.sleep(0)


class SpriteStackingUtils:
    @staticmethod
    def create_layers_from_image(img_path, num_layers=8):
        """
        Create sprite stacking layers from a single voxel image.
        Useful when you have a single car image that needs to be sliced into layers.
        """
        try:
            # Open the full image file
            pil_img = Image.open(img_path)
            img_width, img_height = pil_img.size
            layer_height = img_height // num_layers
            
            layers = []
            # Slice the image into horizontal layers from bottom to top
            for i in range(num_layers):
                # Calculate the slice area for this layer (left, top, right, bottom)
                y_start = img_height - (i + 1) * layer_height
                y_end = img_height - i * layer_height
                
                # Slice the image vertically
                layer = pil_img.crop((0, y_start, img_width, y_end))
                
                # Convert PIL Image to pygame surface
                layer_surface = Surface((img_width, layer_height), pygame.SRCALPHA)
                pygame_img_str = layer.tobytes()
                pygame_img = transform.scale(
                    pygame.image.fromstring(pygame_img_str, layer.size, layer.mode).convert_alpha(),
                    (img_width, layer_height)
                )
                layers.append(pygame_img)
            
            return layers
        except Exception as e:
            print(f"Error creating layers: {e}")
            return []
            
    @staticmethod
    def extract_layers_from_files(img_folder, prefix="car_layer", num_layers=8):
        """
        Load separate layer images from files.
        Useful when you already have separate image files for each layer.
        """
        layers = []
        for i in range(num_layers):
            layer_path = join(img_folder, f"{prefix}{i}.png")
            if exists(layer_path):
                layer = image.load(layer_path).convert_alpha()
                layers.append(layer)
            else:
                print(f"Layer image not found: {layer_path}")
        
        return layers


class VoxelCar(sprite.Sprite):
    """Class to handle the sprite stacking rendering of a voxel car."""
    
    def __init__(self, screen):
        sprite.Sprite.__init__(self)
        self.screen = screen
        
        # Car position and movement
        self.x = 400  # Center of the screen horizontally
        self.y = 450  # Near the bottom of the screen
        self.speed = 0
        self.max_speed = 5
        self.acceleration = 0.2
        self.deceleration = 0.1
        self.friction = 0.95
        self.rotation = 180  # Start with car rotated 180 degrees (facing down)
        self.rotation_speed = 3
        self.direction = 0  # Tracking actual movement direction
        
        # Load car layer images
        car_img_path = join(IMAGE_PATH, "cars-1.png")
        self.num_layers = CAR_LAYERS
        
        # Try to create layers from a single image first
        if exists(car_img_path):
            self.layers = SpriteStackingUtils.create_layers_from_image(car_img_path, self.num_layers)
        else:
            # Fall back to loading separate layer files
            self.layers = SpriteStackingUtils.extract_layers_from_files(IMAGE_PATH, "car_layer", self.num_layers)
        
        # If still no layers, create a default car
        if not self.layers:
            self._create_default_car_layers()
        
        # Create a rectangular hitbox
        self.width = self.layers[0].get_width() if self.layers else CAR_WIDTH
        self.height = self.layers[0].get_height() if self.layers else CAR_HEIGHT
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        
        # Set the base image (for compatibility with pygame sprite group)
        self.image = self.layers[0] if self.layers else Surface((CAR_WIDTH, CAR_HEIGHT))
        
        # Drawing offsets for stacking
        self.layer_offset = CAR_LAYER_OFFSET  # Vertical pixels between each layer
        self.shadow_offset_x = 15  # Shadow offset from car position
        self.shadow_offset_y = 15  # Shadow offset from car position
    
    def _create_default_car_layers(self):
        """Create default car layers if no image is found."""
        self.layers = []
        colors = [
            (180, 180, 200),  # Light gray (top)
            (160, 160, 180),
            (140, 140, 160),
            (120, 120, 140),
            (100, 100, 120),
            (80, 80, 100),
            (60, 60, 80),
            (40, 40, 60)     # Dark gray (bottom)
        ]
        
        # Create layers of different colors based on CAR_LAYERS constant
        for i in range(CAR_LAYERS):
            color_index = min(i, len(colors) - 1)
            layer = Surface((CAR_WIDTH, CAR_HEIGHT), pygame.SRCALPHA)
            
            # Car body
            width_ratio = 0.7  # Body width as percentage of car width
            height_ratio = 0.6  # Body height as percentage of car height
            x_offset = int((CAR_WIDTH - (CAR_WIDTH * width_ratio)) / 2)
            y_offset = int((CAR_HEIGHT - (CAR_HEIGHT * height_ratio)) / 2)
            body_width = int(CAR_WIDTH * width_ratio)
            body_height = int(CAR_HEIGHT * height_ratio)
            
            pygame.draw.rect(layer, colors[color_index], (x_offset, y_offset, body_width, body_height), 0)
            
            # Car wheels
            wheel_color = (30, 30, 30)  # Black wheels
            wheel_radius = int(CAR_HEIGHT * 0.18)  # Scale wheel size based on car height
            wheel_y = int(CAR_HEIGHT * 0.78)  # Position wheels near bottom
            wheel_x1 = int(CAR_WIDTH * 0.25)  # Left wheel position
            wheel_x2 = int(CAR_WIDTH * 0.75)  # Right wheel position
            
            pygame.draw.circle(layer, wheel_color, (wheel_x1, wheel_y), wheel_radius)
            pygame.draw.circle(layer, wheel_color, (wheel_x2, wheel_y), wheel_radius)
            
            # Car windows (only on higher layers)
            if i < CAR_LAYERS // 2:
                window_color = (100, 200, 255) if i == 0 else (80, 170, 220)
                window_width = int(CAR_WIDTH * 0.4)
                window_height = int(CAR_HEIGHT * 0.35)
                window_x = int((CAR_WIDTH - window_width) / 2)
                window_y = int(CAR_HEIGHT * 0.15)
                pygame.draw.rect(layer, window_color, (window_x, window_y, window_width, window_height), 0)
            
            self.layers.append(layer)
    
    def update(self, keys, *args):
        # Handle car movement based on its current orientation
        if keys[K_UP]:
            self.speed += self.acceleration
        elif keys[K_DOWN]:
            self.speed -= self.acceleration
        else:
            # Apply friction to gradually slow down
            self.speed *= self.friction
        
        # Cap speed
        self.speed = max(min(self.speed, self.max_speed), -self.max_speed * 0.6)
        
        # Handle rotation - FIXED: Direction matches controller inputs - LEFT arrow turns LEFT, RIGHT arrow turns RIGHT
        if keys[K_LEFT]:
            self.rotation = (self.rotation - self.rotation_speed) % 360  # Left arrow = rotate LEFT
        if keys[K_RIGHT]:
            self.rotation = (self.rotation + self.rotation_speed) % 360  # Right arrow = rotate RIGHT
        
        # Calculate movement based on current rotation
        angle_rad = math.radians(self.rotation)
        move_x = -math.sin(angle_rad) * self.speed
        move_y = math.cos(angle_rad) * self.speed
        
        # Update position
        self.x += move_x
        self.y += move_y
        
        # Keep within screen bounds
        self.x = max(min(self.x, 800 - self.width//2), self.width//2)
        self.y = max(min(self.y, 600 - self.height//2), self.height//2)
        
        # Update rectangle position for collision detection
        self.rect.x = self.x - self.width//2
        self.rect.y = self.y - self.height//2
        
        # Draw the car using sprite stacking
        self.draw()

    def draw(self):
        """Draw the car using sprite stacking technique."""
        # Draw shadow below the car
        shadow_surf = Surface((self.width, self.height//2), pygame.SRCALPHA)
        shadow_color = (0, 0, 0, 80)  # Semi-transparent black
        shadow_rect = pygame.Rect(0, 0, self.width * 0.8, self.height//3)
        shadow_rect.center = (self.width//2, self.height//4)
        pygame.draw.ellipse(shadow_surf, shadow_color, shadow_rect)
        
        # Get the rotated shadow - add 180 degrees to flip the car
        shadow_surf = transform.rotate(shadow_surf, -(self.rotation + 180))
        shadow_rect = shadow_surf.get_rect()
        shadow_rect.center = (self.x + self.shadow_offset_x, self.y + self.shadow_offset_y)
        self.screen.blit(shadow_surf, shadow_rect)
        
        # Draw each layer from bottom to top, with slight offset
        for i, layer in enumerate(self.layers):
            # Rotate the layer with negative angle and add 180 degrees to flip the car
            rotated_layer = transform.rotate(layer, -(self.rotation + 180))
            layer_rect = rotated_layer.get_rect()
            
            # Calculate position with offset for 3D effect
            layer_rect.center = (
                self.x,
                self.y - i * self.layer_offset
            )
            
            # Draw this layer
            self.screen.blit(rotated_layer, layer_rect)


class VoxelCarGame:
    """Main game class for the Voxel Car game."""
    
    def __init__(self):
        # Setup pygame and display
        mixer.pre_init(44100, -16, 1, 4096)
        init()
        self.clock = time.Clock()
        self.screen = SCREEN
        self.caption = display.set_caption("Voxel Car Sprite Stacking")
        
        # Load background
        background_path = join(IMAGE_PATH, "background.jpg")
        if exists(background_path):
            self.background = image.load(background_path).convert()
        else:
            # Create a default background if image doesn't exist
            self.background = Surface((800, 600))
            self.background.fill((100, 180, 100))  # Green field
            
            # Draw a simple road
            pygame.draw.rect(self.background, (80, 80, 80), (200, 0, 400, 600))  # Road
            pygame.draw.rect(self.background, (255, 255, 255), (390, 0, 20, 600), 0)  # Center line
        
        # Game state
        self.running = True
        self.game_started = False
        self.game_over = False
        
        # Create car and make it a global reference so all sprite methods can use it
        self.car = VoxelCar(self.screen)
        global game
        game = self  # This makes the new game object accessible to older sprite classes
        
        # Setup text and UI elements
        try:
            self.font = font.Font(FONT, 36)
            self.small_font = font.Font(FONT, 24)
            self.title_text = Text(FONT, 50, "Voxel Car", WHITE, 300, 120)
            self.start_text = Text(FONT, 25, "Press any key to drive", WHITE, 250, 200)
            self.creator_text = Text(FONT, 20, "Sprite Stacking Demo", GREEN, 580, 570)
        except Exception as e:
            print(f"Error loading fonts: {e}")
            # Create fallback text using system font
            pygame.font.init()
            self.font = pygame.font.SysFont(None, 36)
            self.title_text = Text(None, 50, "Voxel Car", WHITE, 300, 120)
            self.start_text = Text(None, 25, "Press any key to drive", WHITE, 250, 200)
            self.creator_text = Text(None, 20, "Sprite Stacking Demo", GREEN, 580, 570)
    
    def handle_events(self):
        """Process input events."""
        self.keys = key.get_pressed()
        
        for e in event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                self.running = False
            
            # Start game on key press
            if not self.game_started and e.type == KEYUP:
                self.game_started = True
    
    def update(self):
        """Update game state."""
        if self.game_started:
            self.car.update(self.keys)
    
    def draw(self):
        """Draw everything to the screen."""
        # Draw background
        self.screen.blit(self.background, (0, 0))
        
        if not self.game_started:
            # Draw menu screen
            self.title_text.draw(self.screen)
            self.start_text.draw(self.screen)
        else:
            # We ensure the car is explicitly drawn here too
            self.car.draw()
        
        # Always draw credits
        self.creator_text.draw(self.screen)
        
        # Update the display
        display.update()
    
    async def main(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
            await asyncio.sleep(0)


if __name__ == "__main__":
    game = VoxelCarGame()
    asyncio.run(game.main())

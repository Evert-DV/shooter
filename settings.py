import pygame as pg

vec = pg.math.Vector2

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (128, 128, 128)
DARKGREY = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
YELLOW = (255, 255, 0)
LIGHTBLUE = (0, 200, 200)
ORANGE = (255, 128, 0)

# Game Settings
WIDTH = 1024
HEIGHT = 640
FPS = 60
TITLE = "Shooter"
FONT = 'arial'
BGCOLOR = WHITE
TILESIZE = 32
GRIDWIDTH = WIDTH / TILESIZE
GRIDHEIGHT = HEIGHT / TILESIZE

# Player Settings
PLAYER_SPEED = 500
MOUSE_RADIUS = 100
PLAYER_HEALTH = 10

# Mob settings
DETECT_RADIUS = 250
MOB_SPEED = 300
MOB_HEALTH = 10

# shoot settings
BARREL_OFFSET = vec(35, 0)
BULLET_SPEED = 1500
BULLET_DAMAGE = 1
RATE = 150

# Mine settings
BLAST_RADIUS = 125

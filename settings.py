# settings.py
# This file contains all the settings for the game.
import pygame

# --- Screen ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# --- Colors ---
BLACK = pygame.Color("#141728")
GREY  = pygame.Color("#727880")
VIOLET = pygame.Color("#5C3A93")
PETROL = pygame.Color("#387487")
BLUE = pygame.Color("#59C3C3")
WHITE = pygame.Color("#EBEBEB")
PINK = pygame.Color("#D154CA")
DARK_SLATE_GRAY = pygame.Color("#2F4F4F")
STEEL_BLUE = pygame.Color("#4682B4")
OLIVE_DRAB = pygame.Color("#6B8E23")
CORAL = pygame.Color("#FF7F50")
KHAKI = pygame.Color("#994C2C")
TEAL = pygame.Color("#008080")
MEDIUM_PURPLE = pygame.Color("#9370DB")
DARK_SEA_GREEN = pygame.Color("#8FBC8F")
LIGHT_SKY_BLUE = pygame.Color("#87CEFA")
CRIMSON = pygame.Color("#740B20")
ORANGE_RED = pygame.Color("#FF4500") # For Hexagon Enemy
GOLD = pygame.Color("#FFF200") # For pickup particles
DARK_BLUE = pygame.Color("#00008B") # For store background

# --- Background Color Cycling ---
BG_CYCLE_COLORS = [
    BLACK,
    DARK_SLATE_GRAY,
    PETROL,
    DARK_BLUE,
    VIOLET,
]
BG_COLOR_TRANSITION_SPEED = 0.02

# --- Player ---
PLAYER_RADIUS = 15
INITIAL_MOVEMENT_SPEED = 200
INITIAL_PLAYER_LEVEL = 1
INITIAL_PLAYER_HEALTH = 10
PLAYER_HEALTH_BAR_WIDTH = 40 # Or perhaps player_radius * 2.5
PLAYER_HEALTH_BAR_HEIGHT = 6
PLAYER_HEALTH_BAR_Y_OFFSET = 15

# Player Trail Settings
MAX_TRAIL_LENGTH = 7  # Number of segments in the trail
TRAIL_MAX_ALPHA = 100 # Max alpha (0-255) for the newest part of the trail (oldest parts will be more transparent)

# --- Shooting ---
INITIAL_SHOOT_COOLDOWN = 1.0

# --- Enemies ---
ENEMY_SPAWN_INTERVAL = 1.5
MAX_ENEMIES = 50
SQUARE_GROUP_SIZE_MIN = 2
SQUARE_GROUP_SIZE_MAX = 4
HEXAGON_ENEMY_RADIUS = 22 # Distance from center to vertex, square size is 18
HEXAGON_ENEMY_HEALTH = 3
HEXAGON_ENEMY_SPEED_MIN = 50
HEXAGON_ENEMY_SPEED_MAX = 90


# --- Pickups ---
SPECIAL_PICKUP_CHANCE = 0.15
SPECIAL_PICKUP_COLOR = PINK
SPECIAL_PICKUP_VALUE = 2
INITIAL_MAX_PICKUPS_FOR_FULL_BAR = 10

# Pickup Particle Ellipse Dimensions
PICKUP_PARTICLE_WIDTH = 10
PICKUP_PARTICLE_HEIGHT = 20
SPECIAL_PICKUP_WIDTH = 15
SPECIAL_PICKUP_HEIGHT = 22

# --- Player Archetype Colors (add new color) ---
FOREST_GREEN = (34, 139, 34)

# --- Sound Effect Paths (add new sound path) ---
SOUND_BOUNCING_SHOT_PATH = "audio/bouncing_shot.wav"

# --- Bouncing Projectile Settings ---
BOUNCING_PARTICLE_LIFETIME = 7  # seconds
BOUNCING_PARTICLE_SPEED = 220
BOUNCING_PARTICLE_RADIUS = 10
BOUNCING_PARTICLE_COLOR = FOREST_GREEN # Or any other color
BOUNCING_PARTICLE_MAX_BOUNCES = 5
# If True and world map exists, bounces off world edges. Otherwise, bounces off visible screen edges.
BOUNCING_PARTICLE_USE_WORLD_BOUNDS = False


# --- UI Bar ---
BAR_HEIGHT = 25
BAR_MAX_WIDTH = 300
# BAR_X will be calculated in main based on screen width
# BAR_Y = 20 (already defined in main, can be moved here)
BAR_BG_COLOR = DARK_SLATE_GRAY
BAR_FILL_COLOR = GOLD
LEVEL_TEXT_COLOR = WHITE
LEVEL_TEXT_OFFSET_X = 10

# --- Store ---
STORE_BG_COLOR = DARK_BLUE
STORE_TEXT_COLOR = WHITE
STORE_BUTTON_COLOR = STEEL_BLUE
STORE_BUTTON_HOVER_COLOR = LIGHT_SKY_BLUE

# --- World/Map ---
WORLD_TILES_X = 5
WORLD_TILES_Y = 5

# --- Asset Paths (example) ---
FONT_DEFAULT_PATH = None # For pygame.font.Font(None, size)
SOUND_BG_MUSIC_PATH = "audio/background_music_stage_1.mp3"
IMAGE_PLAYER_PATH = "graphics/player_1.png"
IMAGE_PLAYER_TRIPLE_SHOT_PATH = "graphics/player_2.png"
IMAGE_PLAYER_NOVA_BURST_PATH = "graphics/player_3.png"
IMAGE_PLAYER_BOUNCING_SHOT_PATH = "graphics/player_4.png"
IMAGE_BACKGROUND_PATH = "graphics/background_stage_1.png"
# ... other asset paths

# Example file showing a circle moving on screen
import pygame
import random
import sys # For pygame.quit()
import pygame.mixer
import math # For hexagon drawing
import settings # Import your new settings file
import audio

# pygame setup
pygame.init()
pygame.mixer.init() # Initialize the mixer for sound effects
screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
clock = pygame.time.Clock()
running = True
dt = 0

# --- Background Color Cycling ---
current_bg_color_index = 0
next_bg_color_index = 1
bg_color_transition_progress = 0.0
dynamic_bg_color = settings.BG_CYCLE_COLORS[current_bg_color_index]

# --- Player Size ---
# Define player_radius here so it can be used for scaling the image if needed
player_radius = settings.PLAYER_RADIUS

# --- Sound Effects --- (Initialize all to None or empty for robust error handling)
background_music_stage_1 = None
standard_shot_sound = None
nova_shot_sound = None
triple_shot_sound = None
damaging_aura_sound = None # Assuming this might be added or was from a previous step
pickup_sound = None
enemy_hit_sound = []
player_death_sound = None
select_archetype_sound = None
standard_player_image = None # For player_1.png
boomerang_shot_sound = None # For boomerang weapon
triple_shot_player_image = None # For player_2.png
nova_burst_player_image = None # For player_3.png
bouncing_shot_player_image = None # For the new bouncing shot player

try:
    background_music_stage_1 = pygame.mixer.Sound(audio.BACKGROUND_MUSIC_STAGE_1)
    if background_music_stage_1:
        background_music_stage_1.set_volume(0.1) # Set volume to 50%
    standard_shot_sound = pygame.mixer.Sound("audio/single_shot.wav")
    nova_shot_sound = pygame.mixer.Sound("audio/nova_shot.wav")
    triple_shot_sound = pygame.mixer.Sound("audio/triple_shot.wav")
    boomerang_shot_sound = pygame.mixer.Sound(audio.BOOMERANG_SHOT_SOUND)
    bouncing_shot_sound = pygame.mixer.Sound(audio.BOUNCING_SHOT)
    # damaging_aura_sound = pygame.mixer.Sound("audio/damaging_aura.wav") # Example if you have it
    pickup_sound = pygame.mixer.Sound("audio/pickup_particle.wav")
    enemy_hit_sound = [
        pygame.mixer.Sound("audio/enemy_hit1.wav"),
        pygame.mixer.Sound("audio/enemy_hit2.wav"),
        pygame.mixer.Sound("audio/enemy_hit3.wav"),
        pygame.mixer.Sound("audio/enemy_hit4.wav"),
    ]
    player_death_sound = pygame.mixer.Sound("audio/player_death.wav")
    select_archetype_sound = pygame.mixer.Sound("audio/select_player.wav")
    _original_player_image = pygame.image.load(settings.IMAGE_PLAYER_PATH).convert_alpha()
    _original_player_triple_image = pygame.image.load(settings.IMAGE_PLAYER_TRIPLE_SHOT_PATH).convert_alpha()
    _original_player_nova_image = pygame.image.load(settings.IMAGE_PLAYER_NOVA_BURST_PATH).convert_alpha()
    _original_player_bouncing_image = pygame.image.load(settings.IMAGE_PLAYER_BOUNCING_SHOT_PATH).convert_alpha()
    if _original_player_image: # Scale it if loaded successfully
        standard_player_image = pygame.transform.smoothscale(_original_player_image, (player_radius * 2, player_radius * 2))
    if _original_player_triple_image:
        triple_shot_player_image = pygame.transform.smoothscale(_original_player_triple_image, (player_radius * 2, player_radius * 2))
    if _original_player_nova_image:
        nova_burst_player_image = pygame.transform.smoothscale(_original_player_nova_image, (player_radius * 2, player_radius * 2))
    if _original_player_bouncing_image:
        bouncing_shot_player_image = pygame.transform.smoothscale(_original_player_bouncing_image, (player_radius * 2, player_radius * 2))
except pygame.error as e:
    print(f"Error loading asset (sound or image): {e}")
    pass # Variables remain None/empty if loading failed or a general error occurred.

# --- Static Background Image ---
try:
    static_background_image = pygame.image.load(settings.IMAGE_BACKGROUND_PATH).convert_alpha()
    # If your image doesn't have alpha, you can use .convert() instead
except pygame.error as e:
    print(f"Error loading static background image: {e}")
    static_background_image = None # Fallback if image doesn't load

# --- World/Map Definition ---
WORLD_TILES_X = settings.WORLD_TILES_X
WORLD_TILES_Y = settings.WORLD_TILES_Y
TILE_WIDTH = 0
TILE_HEIGHT = 0
if static_background_image:
    TILE_WIDTH = static_background_image.get_width()
    TILE_HEIGHT = static_background_image.get_height()

camera_offset = pygame.Vector2(0, 0) # Tracks the top-left of the camera in world coordinates
player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
player_trail_positions = [] # For player trail effect

# --- Particle shoot Setup ---
class Particle:
    def __init__(self, start_pos, target_pos, color=settings.WHITE, speed=250, radius=4):
        # Ensure start_pos is a Vector2. If it's a tuple/list, convert it.
        self.pos = pygame.Vector2(start_pos)
        self.radius = radius
        self.color = color
        self.speed = speed
        # Calculate direction towards the target's position at the moment of firing
        if (target_pos - start_pos).length_squared() > 0:
            self.direction = (target_pos - start_pos).normalize()
        else:
            self.direction = pygame.Vector2(0, -1) # Default upwards if target is at start_pos

    def update(self, dt, screen_width=None, screen_height=None, camera_offset=None, world_bounds=None):
        self.pos += self.direction * self.speed * dt

    def draw(self, surface, camera_offset):
        screen_pos = self.pos - camera_offset
        pygame.draw.circle(surface, self.color, (int(screen_pos.x), int(screen_pos.y)), self.radius)

    def is_alive(self, screen_width, screen_height, camera_offset, world_bounds=None):
        # For standard particles, alive means on-screen (relative to camera)
        screen_pos = self.pos - camera_offset
        on_screen = not (screen_pos.x < -self.radius or screen_pos.x > screen_width + self.radius or
                         screen_pos.y < -self.radius or screen_pos.y > screen_height + self.radius)
        return on_screen

# --- Enemy Triangle Setup ---
class EnemyTriangle:
    def __init__(self, screen_dims, camera_world_tl_pos):
        self.height = 20  # Length from tip to middle of base
        self.base_width = 15  # Full width of the base
        self.speed = random.uniform(70, 110)  # Pixels per second
        self.color = settings.OLIVE_DRAB
        self.collision_radius = self.height * 0.75 # Radius for enemy-enemy collision

        # Spawn on a random edge, with the tip (self.pos) starting off-screen
        edge = random.choice(["top", "bottom", "left", "right"])
        margin = self.height # Ensure it spawns fully off-screen
        world_x, world_y = 0, 0 # Initialize for robustness

        if edge == "top":
            world_x = camera_world_tl_pos.x + random.uniform(0, screen_dims[0])
            world_y = camera_world_tl_pos.y - margin
        elif edge == "bottom":
            world_x = camera_world_tl_pos.x + random.uniform(0, screen_dims[0])
            world_y = camera_world_tl_pos.y + screen_dims[1] + margin
        elif edge == "left":
            world_x = camera_world_tl_pos.x - margin
            world_y = camera_world_tl_pos.y + random.uniform(0, screen_dims[1])
        else:  # right
            world_x = camera_world_tl_pos.x + screen_dims[0] + margin
            world_y = camera_world_tl_pos.y + random.uniform(0, screen_dims[1])
        self.pos = pygame.Vector2(world_x, world_y)

    def update(self, target_pos, dt): # target_pos is player's world_pos
        # Move towards the target_pos
        if (target_pos - self.pos).length_squared() > 0:  # Avoid division by zero if already at target
            direction = (target_pos - self.pos).normalize()
            self.pos += direction * self.speed * dt

    #def draw(self, surface, target_pos):
        # Calculate direction vector towards target for orientation
    def draw(self, surface, target_world_pos, camera_offset): # target_world_pos is player's world_pos
        direction_to_target = pygame.Vector2(0, -1) # Default if on top of target (e.g., point "up")
        if (target_world_pos - self.pos).length_squared() > 0:
            direction_to_target = (target_world_pos - self.pos).normalize()

        # p1 is the tip of the triangle, which is self.pos
        p1_world = self.pos

        # Calculate center of the base (behind the tip)
        base_center_world = self.pos - direction_to_target * self.height
        # Calculate perpendicular vector for the base spread
        perp_vector = pygame.Vector2(-direction_to_target.y, direction_to_target.x)
        p2_world = base_center_world + perp_vector * (self.base_width / 2)
        p3_world = base_center_world - perp_vector * (self.base_width / 2)

        p1_screen = p1_world - camera_offset
        p2_screen = p2_world - camera_offset
        p3_screen = p3_world - camera_offset

        pygame.draw.polygon(surface, self.color, [p1_screen, p2_screen, p3_screen])

# --- Enemy Square Setup ---
class SquareEnemy:
    def __init__(self, pos, screen_width, screen_height, size=18, speed=None):
        self.size = size
        self.pos = pygame.Vector2(pos)
        if speed is None:
            self.speed = random.uniform(60, 100)
        else:
            self.speed = speed
        self.initial_color = settings.STEEL_BLUE
        self.damaged_color = settings.GREY
        self.color = self.initial_color
        self.health = 2
        self.max_health = 2 # Store max health for potential future use (e.g. health bars)
        self.collision_radius = self.size * 0.75 # Radius for enemy-enemy collision (a bit larger than half diagonal)

    def update(self, target_pos, dt):
        if (target_pos - self.pos).length_squared() > 0:
            direction = (target_pos - self.pos).normalize()
            self.pos += direction * self.speed * dt

    def draw(self, surface, camera_offset):
        # Change color if damaged
        if self.health < self.max_health:
            self.color = self.damaged_color
        else:
            self.color = self.initial_color
        
        screen_pos_x = self.pos.x - camera_offset.x - self.size / 2
        screen_pos_y = self.pos.y - camera_offset.y - self.size / 2
        rect = pygame.Rect(screen_pos_x,
                           screen_pos_y,
                           self.size, self.size)
        pygame.draw.rect(surface, self.color, rect)


    def take_damage(self, damage_amount=1): # Add damage_amount parameter
        self.health -= damage_amount
        if self.health <= 0:
            return True # Destroyed
        return False # Still alive


# --- Enemy Hexagon Setup ---
class HexagonEnemy:
    def __init__(self, pos, screen_width, screen_height, radius=settings.HEXAGON_ENEMY_RADIUS, speed=None, health=settings.HEXAGON_ENEMY_HEALTH):
        self.radius_stat = radius # Distance from center to vertex
        self.pos = pygame.Vector2(pos)
        if speed is None:
            self.speed = random.uniform(settings.HEXAGON_ENEMY_SPEED_MIN, settings.HEXAGON_ENEMY_SPEED_MAX)
        else:
            self.speed = speed
        self.initial_color = settings.ORANGE_RED
        self.damaged_color = settings.GREY # Same damaged color as square for consistency
        self.color = self.initial_color
        self.health = health
        self.max_health = health
        self.collision_radius = self.radius_stat # For enemy-enemy collision, use full radius

    def update(self, target_pos, dt):
        if (target_pos - self.pos).length_squared() > 0:
            direction = (target_pos - self.pos).normalize()
            self.pos += direction * self.speed * dt

    def draw(self, surface, camera_offset):
        # Change color if damaged
        if self.health < self.max_health:
            self.color = self.damaged_color
        else:
            self.color = self.initial_color

        points = []
        center_screen_x = self.pos.x - camera_offset.x
        center_screen_y = self.pos.y - camera_offset.y

        for i in range(6):
            # Angle for a point-up hexagon (first point at top)
            angle_rad = math.radians(60 * i - 90)
            x = center_screen_x + self.radius_stat * math.cos(angle_rad)
            y = center_screen_y + self.radius_stat * math.sin(angle_rad)
            points.append((x, y))
        pygame.draw.polygon(surface, self.color, points)

    def take_damage(self, damage_amount=1): # Add damage_amount parameter
        self.health -= damage_amount
        if self.health <= 0:
            return True # Destroyed
        return False # Still alive

    
# --- Orbital Weapon Setup ---
class OrbitalWeapon:
    def __init__(self, player_pos_ref, orbit_distance=settings.ORBITAL_WEAPON_ORBIT_DISTANCE, 
                 rotation_speed=settings.ORBITAL_WEAPON_ROTATION_SPEED, 
                 color=settings.ORBITAL_WEAPON_COLOR, radius=settings.ORBITAL_WEAPON_RADIUS,
                 damage=settings.ORBITAL_WEAPON_DAMAGE):
        self.player_pos_ref = player_pos_ref # Reference to the player's position vector
        self.orbit_distance = orbit_distance
        self.rotation_speed = rotation_speed  # Degrees per second
        self.current_angle = 0  # Degrees
        self.color = color
        self.radius = radius
        self.damage = damage
        self.pos = pygame.Vector2(0, 0) # Will be updated relative to player
        self.last_hit_times = {} # enemy_id: time_of_last_hit
        self.hit_cooldown = settings.ORBITAL_WEAPON_HIT_COOLDOWN # Seconds

    def update(self, dt):
        self.current_angle = (self.current_angle + self.rotation_speed * dt) % 360
        rad_angle = math.radians(self.current_angle)
        
        # Calculate position relative to the player's current position
        offset_x = self.orbit_distance * math.cos(rad_angle)
        offset_y = self.orbit_distance * math.sin(rad_angle)
        self.pos = self.player_pos_ref + pygame.Vector2(offset_x, offset_y)

    def draw(self, surface, camera_offset):
        screen_pos = self.pos - camera_offset
        pygame.draw.circle(surface, self.color, (int(screen_pos.x), int(screen_pos.y)), self.radius)

# --- Pickup Particle Setup ---
class PickupParticle:
    def __init__(self, pos, color=settings.GOLD, width=settings.PICKUP_PARTICLE_WIDTH, height=settings.PICKUP_PARTICLE_HEIGHT, value=1):
        self.pos = pygame.Vector2(pos) # Position where it's dropped
        self.width = width
        self.height = height
        self.color = color
        self.value = value # How much this pickup is worth

    def draw(self, surface, camera_offset):
        screen_pos = self.pos - camera_offset
        # For pygame.draw.ellipse, pos is the top-left of the bounding rect
        ellipse_rect = pygame.Rect(screen_pos.x - self.width / 2,
                                   screen_pos.y - self.height / 2,
                                   self.width, self.height)
        pygame.draw.ellipse(surface, self.color, ellipse_rect)

# --- Bouncing Particle Setup ---
class BouncingParticle(Particle):
    def __init__(self, start_pos, target_pos, color=settings.BOUNCING_PARTICLE_COLOR,
                 speed=settings.BOUNCING_PARTICLE_SPEED, radius=settings.BOUNCING_PARTICLE_RADIUS,
                 lifetime=settings.BOUNCING_PARTICLE_LIFETIME, max_bounces=settings.BOUNCING_PARTICLE_MAX_BOUNCES):
        super().__init__(start_pos, target_pos, color, speed, radius) # Uses its own default color
        self.lifetime = lifetime
        self.age = 0.0
        self.bounces_left = max_bounces
        # self.bounce_sound = pygame.mixer.Sound("audio/bounce_effect.wav") # Optional: specific bounce sound

    def update(self, dt, screen_width, screen_height, camera_offset, world_bounds=None):
        self.age += dt
        if not self.is_alive(screen_width, screen_height, camera_offset, world_bounds): # Check before moving
             return

        self.pos += self.direction * self.speed * dt

        # Determine bounce boundaries
        bounce_off_world = settings.BOUNCING_PARTICLE_USE_WORLD_BOUNDS and world_bounds is not None
        
        min_x_bound, max_x_bound, min_y_bound, max_y_bound = 0,0,0,0

        if bounce_off_world:
            min_x_bound = 0 # World map starts at 0,0
            max_x_bound = world_bounds[0]
            min_y_bound = 0
            max_y_bound = world_bounds[1]
        else: # Bounce off visible screen edges (converted to world coordinates)
            min_x_bound = camera_offset.x
            max_x_bound = camera_offset.x + screen_width
            min_y_bound = camera_offset.y
            max_y_bound = camera_offset.y + screen_height
        
        # Effective collision points for the particle's center based on its radius
        eff_min_x = min_x_bound + self.radius
        eff_max_x = max_x_bound - self.radius
        eff_min_y = min_y_bound + self.radius
        eff_max_y = max_y_bound - self.radius

        bounced_this_frame = False
        # Horizontal bounce
        if self.pos.x <= eff_min_x:
            self.pos.x = eff_min_x + (eff_min_x - self.pos.x) # Reflect position past boundary
            self.direction.x *= -1
            bounced_this_frame = True
        elif self.pos.x >= eff_max_x:
            self.pos.x = eff_max_x - (self.pos.x - eff_max_x) # Reflect position past boundary
            self.direction.x *= -1
            bounced_this_frame = True

        # Vertical bounce
        if self.pos.y <= eff_min_y:
            self.pos.y = eff_min_y + (eff_min_y - self.pos.y) # Reflect position past boundary
            self.direction.y *= -1
            bounced_this_frame = True
        elif self.pos.y >= eff_max_y:
            self.pos.y = eff_max_y - (self.pos.y - eff_max_y) # Reflect position past boundary
            self.direction.y *= -1
            bounced_this_frame = True
        
        if bounced_this_frame:
            self.bounces_left -= 1
            # if self.bounce_sound: self.bounce_sound.play()

    def bounce_off_object(self, object_center_pos, object_radius):
        """Handles the reflection of the particle's direction off a circular object."""
        # Normal vector from object center to particle center
        collision_normal = self.pos - object_center_pos
        if collision_normal.length_squared() > 0:
            collision_normal.normalize_ip()
            
            # Reflect direction: D_new = D_old - 2 * (D_old.dot(N)) * N
            reflection_component = 2 * self.direction.dot(collision_normal) * collision_normal
            self.direction -= reflection_component
            self.direction.normalize_ip() # Ensure it's still a unit vector

            # Nudge particle slightly away from the object to prevent immediate re-collision
            # Place it just outside the combined radii plus a small epsilon
            self.pos = object_center_pos + collision_normal * (object_radius + self.radius + 0.1)

    def is_alive(self, screen_width, screen_height, camera_offset, world_bounds=None):
        return self.age < self.lifetime and self.bounces_left >= 0

# --- Boomerang Projectile Setup ---
class BoomerangProjectile(Particle):
    def __init__(self, start_pos, initial_target_pos,
                 color=settings.BOOMERANG_PROJECTILE_COLOR,
                 speed=settings.BOOMERANG_PROJECTILE_SPEED,
                 radius=settings.BOOMERANG_PROJECTILE_RADIUS,
                 lifetime=settings.BOOMERANG_PROJECTILE_LIFETIME,
                 damage=settings.BOOMERANG_PROJECTILE_DAMAGE):
        super().__init__(start_pos, initial_target_pos, color, speed, radius)
        self.initial_target_pos = pygame.Vector2(initial_target_pos)
        self.lifetime = lifetime
        self.age = 0.0
        self.damage = damage
        self.state = "to_target"  # "to_target" or "returning"
        self.hit_enemies_this_pass = set() # Store IDs of enemies hit in current pass
        self.turn_distance_threshold_sq = 15**2 # How close to target before turning (squared)

    def update(self, dt, player_pos_not_used_for_simple_return, world_bounds=None): # player_pos might be needed for smarter return
        self.age += dt
        if not self.is_alive(0,0,None,None): # Basic lifetime check
            return

        if self.state == "to_target":
            # Check if close enough to initial_target_pos to turn
            if (self.initial_target_pos - self.pos).length_squared() < self.turn_distance_threshold_sq:
                self.state = "returning"
                self.direction *= -1  # Reverse direction
                self.hit_enemies_this_pass.clear() # Allow hitting enemies again
            else:
                # If direction was zero (e.g. spawned on target), set a default return direction
                if self.direction.length_squared() == 0:
                    self.direction = pygame.Vector2(0, -1) # Default upwards
                    self.state = "returning"
                    self.hit_enemies_this_pass.clear()

        # Common movement for both states (direction might have been updated)
        self.pos += self.direction * self.speed * dt

    def draw(self, surface, camera_offset):
        # Could add a slight rotation or different visual for boomerang
        super().draw(surface, camera_offset)

    def is_alive(self, screen_width_unused, screen_height_unused, camera_offset_unused, world_bounds_unused):
        return self.age < self.lifetime

    def on_hit_enemy(self):
        # Boomerangs are not destroyed on hit, they continue until lifetime ends.
        # Logic to prevent multi-hits per pass is handled with self.hit_enemies_this_pass
        pass

# --- Enemy Variables ---
enemies = []
enemy_spawn_timer = 0.0
ENEMY_SPAWN_INTERVAL = settings.ENEMY_SPAWN_INTERVAL
MAX_ENEMIES = settings.MAX_ENEMIES
SQUARE_GROUP_SIZE_MIN = settings.SQUARE_GROUP_SIZE_MIN
SQUARE_GROUP_SIZE_MAX = settings.SQUARE_GROUP_SIZE_MAX
pickup_particles = [] # List to store pickup particles
SPECIAL_PICKUP_CHANCE = settings.SPECIAL_PICKUP_CHANCE
SPECIAL_PICKUP_COLOR = settings.PINK
SPECIAL_PICKUP_VALUE = settings.SPECIAL_PICKUP_VALUE

# --- Shooting Variables
particles = []
# SHOOT_COOLDOWN will be initialized from settings.INITIAL_SHOOT_COOLDOWN
last_shot_time = 0.0

boomerang_projectiles = [] # List to store active boomerang projectiles
has_boomerang_weapon = False
last_boomerang_shot_time = 0.0

# --- Player Variables ---
movement_speed = settings.INITIAL_MOVEMENT_SPEED  # Player movement speed, made global for upgrades
player_level = settings.INITIAL_PLAYER_LEVEL
player_pickup_radius_multiplier = 1.0 # For pickup radius upgrade
max_player_health = settings.INITIAL_PLAYER_HEALTH # Max health can be upgraded
active_orbital_weapons = [] # List to store active orbital weapons
current_player_health = settings.INITIAL_PLAYER_HEALTH

# --- Player Health Bar UI ---
PLAYER_HEALTH_BAR_WIDTH = settings.PLAYER_HEALTH_BAR_WIDTH
PLAYER_HEALTH_BAR_HEIGHT = settings.PLAYER_HEALTH_BAR_HEIGHT
PLAYER_HEALTH_BAR_Y_OFFSET = settings.PLAYER_HEALTH_BAR_Y_OFFSET

# --- Player Archetypes ---
PLAYER_ARCHETYPES = [
    {
        "id": "standard",
        "name": "Standard",
        "color": settings.CRIMSON,
        "description": "Single shot",
        "shoot_cooldown_modifier": 1.0,
        "shoot_function_name": "shoot_standard"
    },
    {
        "id": "triple_shot",
        "name": "Spread",
        "color": settings.MEDIUM_PURPLE,
        "description": "301",
        "shoot_cooldown_modifier": 1.15, # Slightly longer base cooldown
        "shoot_function_name": "shoot_triple"
    },
    {
        "id": "nova_burst",
        "name": "Burst",
        "color": settings.TEAL,
        "description": "Splosion",
        "shoot_cooldown_modifier": 1.6, # Noticeably longer base cooldown
        "shoot_function_name": "shoot_nova"
    },
    {
        "id": "bouncing_shot",
        "name": "Ricochet",
        "color": settings.FOREST_GREEN,
        "description": "Bouncing shot",
        "shoot_cooldown_modifier": 0.8,
        "shoot_function_name": "shoot_bouncing"
    }
]
selected_player_archetype = None # Will hold the chosen dict from PLAYER_ARCHETYPES
character_select_active = True # Start with character selection

# --- Shooting Functions ---
def shoot_standard(player_world_pos, all_enemies, particle_list, particle_color, camera_offset_for_aiming):
    if not all_enemies: return
    nearest_enemy = min(all_enemies, key=lambda e: (e.pos - player_world_pos).length_squared())
    if standard_shot_sound:
        standard_shot_sound.play()
    particle_list.append(Particle(player_world_pos, nearest_enemy.pos, color=particle_color))

def shoot_triple(player_world_pos, all_enemies, particle_list, particle_color, camera_offset_for_aiming):
    if not all_enemies: return
    if triple_shot_sound:
        triple_shot_sound.play()
    nearest_enemy = min(all_enemies, key=lambda e: (e.pos - player_world_pos).length_squared())
    base_direction = (nearest_enemy.pos - player_world_pos).normalize() if (nearest_enemy.pos - player_world_pos).length_squared() > 0 else pygame.Vector2(0, -1)
    for angle_offset in [-15, 0, 15]:
        shot_direction = base_direction.rotate(angle_offset)
        particle_list.append(Particle(player_world_pos, player_world_pos + shot_direction * 100, color=particle_color)) # Target is far point

def shoot_nova(player_world_pos, all_enemies, particle_list, particle_color, camera_offset_for_aiming):
    if nova_shot_sound:
        nova_shot_sound.play()
    for i in range(8): # 8 projectiles
        shot_direction = pygame.Vector2(1, 0).rotate(i * 45) # 360/8 = 45 degrees
        particle_list.append(Particle(player_world_pos, player_world_pos + shot_direction * 100, color=particle_color))

def shoot_bouncing(player_world_pos, all_enemies, particle_list, particle_color_unused, camera_offset_for_aiming):
    if bouncing_shot_sound:
        bouncing_shot_sound.play()

    # Generate a random direction
    random_angle = random.uniform(0, 2 * math.pi) # Angle in radians
    target_direction = pygame.Vector2(math.cos(random_angle), math.sin(random_angle)).normalize()
    
    far_target_pos = player_world_pos + target_direction * 100 # For initial direction calculation

    particle_list.append(BouncingParticle(
        player_world_pos, far_target_pos, # BouncingParticle uses its own color from settings
        # Other params like speed, radius, lifetime, max_bounces are defaults in BouncingParticle constructor
    ))

SHOOT_FUNCTIONS = {
    "shoot_standard": shoot_standard,
    "shoot_triple": shoot_triple,
    "shoot_nova": shoot_nova,
    "shoot_bouncing": shoot_bouncing,
}

# --- UI Bar Setup ---
MAX_PICKUPS_FOR_FULL_BAR = settings.INITIAL_MAX_PICKUPS_FOR_FULL_BAR

BAR_HEIGHT = settings.BAR_HEIGHT
BAR_MAX_WIDTH = settings.BAR_MAX_WIDTH
BAR_X = screen.get_width() // 2 - BAR_MAX_WIDTH // 2
BAR_Y = 20  # Small margin from the top edge
BAR_BG_COLOR = settings.DARK_SLATE_GRAY
BAR_FILL_COLOR = settings.GOLD
current_pickups_count = 0  # How many pickups collected towards the current bar fill
LEVEL_TEXT_COLOR = settings.WHITE
LEVEL_TEXT_OFFSET_X = settings.LEVEL_TEXT_OFFSET_X

# --- Store Setup ---
store_active = False
STORE_BG_COLOR = settings.STORE_BG_COLOR
STORE_TEXT_COLOR = settings.STORE_TEXT_COLOR
STORE_BUTTON_COLOR = settings.STORE_BUTTON_COLOR

SHOOT_COOLDOWN = settings.INITIAL_SHOOT_COOLDOWN # Seconds
STORE_BUTTON_HOVER_COLOR = settings.LIGHT_SKY_BLUE

# --- Game Timer ---
total_game_time_seconds = 0.0
kill_count = 0 # Initialize kill counter
ui_font = None # Will be initialized with store fonts

# --- Game Over State ---
game_over_active = False
game_over_font_large = None # For "GAME OVER" text
# ui_font (store_font_medium) will be used for smaller game over text like score

try:
    store_font_large = pygame.font.Font(settings.FONT_DEFAULT_PATH, 48) # For title
    store_font_medium = pygame.font.Font(settings.FONT_DEFAULT_PATH, 36) # For buttons/text
    game_over_font_large = pygame.font.Font(None, 96) # Larger font for "GAME OVER"
except pygame.error as e:
    print(f"Font loading error: {e}. Using default system font.")
    store_font_large = pygame.font.SysFont(settings.FONT_DEFAULT_PATH, 48)
    store_font_medium = pygame.font.SysFont(settings.FONT_DEFAULT_PATH, 36)
    game_over_font_large = pygame.font.SysFont(None, 96)
ui_font = store_font_medium # Use the medium font for UI elements like the timer


# --- Master Store Items List ---
MASTER_STORE_ITEMS = [
    {"id": "faster_shots", "text": "Faster Shots", "cost_text": "(Full Bar)"},
    {"id": "player_speed", "text": "Player Speed+", "cost_text": "(Full Bar)"},
    {"id": "max_health", "text": "Max Health+", "cost_text": "(Full Bar)"},
    {"id": "pickup_radius", "text": "Pickup Radius+", "cost_text": "(Full Bar)"},
    {"id": "heal_fully", "text": "Heal Fully", "cost_text": "(Full Bar)"},
    {"id": "boomerang_weapon", "text": "Boomerang", "cost_text": "(Full Bar)"},
    {"id": "orbital_weapon", "text": "Orbital Guard", "cost_text": "(Full Bar)"},
    # Add more items here, e.g.:
    # {"id": "damage_boost", "text": "Damage Boost", "cost_text": "(Full Bar)"},
    # {"id": "temp_invincibility", "text": "Brief Shield", "cost_text": "(Full Bar)"},
]
displayed_store_items = [] # Will hold the 3 items currently shown in the store

continue_button_text = "Continue Game"
continue_button_rect = None

# --- Reset Game State ---
def reset_game_state():
    global player_pos, enemies, particles, pickup_particles, total_game_time_seconds
    global current_pickups_count, MAX_PICKUPS_FOR_FULL_BAR, SHOOT_COOLDOWN, movement_speed, camera_offset, current_player_health, max_player_health, kill_count, player_trail_positions, player_pickup_radius_multiplier, active_orbital_weapons, MAX_ENEMIES, boomerang_projectiles, has_boomerang_weapon, last_boomerang_shot_time
    global game_over_active, store_active, enemy_spawn_timer, last_shot_time, player_level

    # Stop any currently playing background music first to avoid overlap on restart
    if background_music_stage_1:
        background_music_stage_1.stop()

    # Calculate world center if map exists, otherwise screen center
    if TILE_WIDTH > 0 and TILE_HEIGHT > 0:
        world_pixel_width = WORLD_TILES_X * TILE_WIDTH
        world_pixel_height = WORLD_TILES_Y * TILE_HEIGHT
        player_pos = pygame.Vector2(world_pixel_width / 2, world_pixel_height / 2)
    else:
        # Fallback to screen center if no tileable map is defined (e.g., image failed to load)
        player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
    enemies.clear()
    particles.clear() # Player shots
    pickup_particles.clear() # Gold particles
    player_trail_positions.clear() # Clear player trail
    active_orbital_weapons.clear() # Clear any active orbital weapons
    boomerang_projectiles.clear() # Clear boomerangs

    total_game_time_seconds = 0.0
    current_pickups_count = 0
    MAX_PICKUPS_FOR_FULL_BAR = settings.INITIAL_MAX_PICKUPS_FOR_FULL_BAR
    SHOOT_COOLDOWN = settings.INITIAL_SHOOT_COOLDOWN
    movement_speed = settings.INITIAL_MOVEMENT_SPEED
    MAX_ENEMIES = settings.MAX_ENEMIES # Reset MAX_ENEMIES to initial value
    player_level = settings.INITIAL_PLAYER_LEVEL
    max_player_health = settings.INITIAL_PLAYER_HEALTH
    current_player_health = max_player_health
    player_pickup_radius_multiplier = 1.0
    has_boomerang_weapon = False

    kill_count = 0 # Reset kill count
    enemy_spawn_timer = 0.0
    last_shot_time = 0.0
    last_boomerang_shot_time = 0.0

    game_over_active = False
    store_active = False # character_select_active is handled separately
    displayed_store_items.clear() # Clear store offerings
    
    # Reset camera based on player's starting position
    camera_offset.x = player_pos.x - screen.get_width() / 2
    camera_offset.y = player_pos.y - screen.get_height() / 2

    # Start background music for the stage if loaded
    if background_music_stage_1:
        background_music_stage_1.play(loops=-1) # Play indefinitely

# --- Populate Store with Random Items ---
def populate_store_offerings():
    global displayed_store_items, has_boomerang_weapon, active_orbital_weapons # Make globals accessible
    displayed_store_items.clear()

    available_master_items = []
    for item_template in MASTER_STORE_ITEMS:
        can_add = True
        if item_template["id"] == "boomerang_weapon" and has_boomerang_weapon:
            can_add = False
        # Example for limiting orbital weapons if desired (currently stackable)
        # MAX_ORBITAL_WEAPONS_ALLOWED = 1 # Define in settings
        # if item_template["id"] == "orbital_weapon" and len(active_orbital_weapons) >= MAX_ORBITAL_WEAPONS_ALLOWED:
        #     can_add = False
        if can_add:
            available_master_items.append(item_template)

    num_to_display = min(len(available_master_items), 3)
    displayed_store_items = random.sample(available_master_items, num_to_display) if available_master_items else []

    for item in displayed_store_items: # Ensure rect is reset
        item["rect"] = None

# --- Draw Game Over Screen ---
def draw_game_over_screen(surface, final_time_seconds):
    # Semi-transparent overlay
    overlay_color = pygame.Color(10, 10, 20, 200) # Dark semi-transparent
    overlay_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    overlay_surface.fill(overlay_color)
    surface.blit(overlay_surface, (0, 0))

    # "GAME OVER" Text
    game_over_text_surf = game_over_font_large.render("GAME OVER", True, settings.CRIMSON)
    game_over_text_rect = game_over_text_surf.get_rect(center=(surface.get_width() / 2, surface.get_height() / 3))
    surface.blit(game_over_text_surf, game_over_text_rect)

    # Final Score (Time)
    minutes = int(final_time_seconds // 60)
    seconds = int(final_time_seconds % 60)
    time_str = f"Time Survived: {minutes:02}:{seconds:02}"
    score_surf = ui_font.render(time_str, True, settings.WHITE) # ui_font is store_font_medium
    score_rect = score_surf.get_rect(center=(surface.get_width() / 2, game_over_text_rect.bottom + 60))
    surface.blit(score_surf, score_rect)

    # Instructions
    quit_text = "Press 'Q' to Quit"
    restart_text = "Press 'R' to Restart"

    quit_surf = ui_font.render(quit_text, True, settings.GREY)
    quit_rect = quit_surf.get_rect(center=(surface.get_width() / 2, score_rect.bottom + 40))
    surface.blit(quit_surf, quit_rect)
    restart_surf = ui_font.render(restart_text, True, settings.GREY)
    restart_rect = restart_surf.get_rect(center=(surface.get_width() / 2, quit_rect.bottom + 30))
    surface.blit(restart_surf, restart_rect)

def draw_store_window(surface):
    global continue_button_rect # Allow modification
    store_width = 500
    store_height = 400
    store_x = (surface.get_width() - store_width) // 2
    store_y = (surface.get_height() - store_height) // 2

    # Draw background
    pygame.draw.rect(surface, STORE_BG_COLOR, (store_x, store_y, store_width, store_height), border_radius=10)
    pygame.draw.rect(surface, settings.WHITE, (store_x, store_y, store_width, store_height), width=2, border_radius=10) # Border

    # Title
    title_surf = store_font_large.render("UPGRADE STORE", True, STORE_TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(store_x + store_width // 2, store_y + 40))
    surface.blit(title_surf, title_rect)

    button_height = 50
    button_padding = 20
    current_y = store_y + 100

    mouse_pos = pygame.mouse.get_pos()

    for i, item in enumerate(displayed_store_items): # Use the currently displayed items
        item_text = f"{item['text']} {item['cost_text']}"
        button_rect = pygame.Rect(store_x + 50, current_y, store_width - 100, button_height)
        item["rect"] = button_rect # Store rect for click detection
        
        btn_color = STORE_BUTTON_HOVER_COLOR if button_rect.collidepoint(mouse_pos) else STORE_BUTTON_COLOR
        pygame.draw.rect(surface, btn_color, button_rect, border_radius=5)
        item_surf = store_font_medium.render(item_text, True, STORE_TEXT_COLOR)
        item_surf_rect = item_surf.get_rect(center=button_rect.center)
        surface.blit(item_surf, item_surf_rect)
        current_y += button_height + button_padding

    # Continue Button
    continue_button_rect = pygame.Rect(store_x + 50, store_y + store_height - 70, store_width - 100, button_height)
    btn_color = STORE_BUTTON_HOVER_COLOR if continue_button_rect.collidepoint(mouse_pos) else STORE_BUTTON_COLOR
    pygame.draw.rect(surface, btn_color, continue_button_rect, border_radius=5)
    continue_surf = store_font_medium.render(continue_button_text, True, STORE_TEXT_COLOR)
    continue_surf_rect = continue_surf.get_rect(center=continue_button_rect.center)
    surface.blit(continue_surf, continue_surf_rect)

# --- Helper for Character Selection Screen ---
def _draw_single_archetype_card(surface, archetype_data, x, y, card_width, card_height, mouse_pos, title_font, desc_font,
                                 img_std, img_triple, img_nova, img_bouncing):
    """Draws a single archetype card on the character selection screen."""
    rect = pygame.Rect(x, y, card_width, card_height)
    archetype_data["rect"] = rect # Store rect for click detection

    # Draw border and fill
    border_color = settings.STORE_BUTTON_HOVER_COLOR if rect.collidepoint(mouse_pos) else settings.WHITE
    pygame.draw.rect(surface, settings.STEEL_BLUE, rect, border_radius=10) # Background
    pygame.draw.rect(surface, border_color, rect, width=3, border_radius=10) # Border

    # Position for the visual element (image or circle)
    visual_center_x = x + card_width / 2
    visual_center_y = y + 40 # Position towards the top of the card
    visual_element_bottom_y = 0 # To track for positioning text below

    # Determine which image to draw
    image_to_render = None
    if archetype_data["id"] == "standard" and img_std: image_to_render = img_std
    elif archetype_data["id"] == "triple_shot" and img_triple: image_to_render = img_triple
    elif archetype_data["id"] == "nova_burst" and img_nova: image_to_render = img_nova
    elif archetype_data["id"] == "bouncing_shot" and img_bouncing: image_to_render = img_bouncing

    if image_to_render:
        img_rect = image_to_render.get_rect(center=(visual_center_x, visual_center_y))
        surface.blit(image_to_render, img_rect)
        visual_element_bottom_y = img_rect.bottom
    else: # Fallback to circle
        default_circle_radius = 20
        pygame.draw.circle(surface, archetype_data["color"], (visual_center_x, visual_center_y), default_circle_radius)
        visual_element_bottom_y = visual_center_y + default_circle_radius

    name_surf = title_font.render(archetype_data["name"], True, settings.WHITE)
    name_rect = name_surf.get_rect(center=(visual_center_x, visual_element_bottom_y + 25))
    surface.blit(name_surf, name_rect)

    desc_lines = archetype_data["description"].splitlines()
    line_y_offset = name_rect.bottom + 10
    for line_idx, line_text in enumerate(desc_lines):
        desc_surf = desc_font.render(line_text, True, settings.LIGHT_SKY_BLUE)
        desc_rect = desc_surf.get_rect(center=(visual_center_x, line_y_offset + line_idx * (desc_font.get_height() + 2)))
        surface.blit(desc_surf, desc_rect)

# --- Draw Character Selection Screen ---
def draw_character_select_screen(surface):
    global PLAYER_ARCHETYPES # To store rects for clicking
    surface.fill(settings.DARK_BLUE) # Simple background for this screen

    title_font = store_font_large # Reuse store font
    desc_font = ui_font # Reuse UI font
    
    title_surf = title_font.render("CHOOSE YOUR VESSEL", True, settings.WHITE)
    title_rect = title_surf.get_rect(center=(surface.get_width() / 2, 80))
    surface.blit(title_surf, title_rect)

    option_width = 300
    option_height = 150 # Increased height for description
    horizontal_padding = 40
    row_padding = 30 # Vertical padding between rows

    mouse_pos = pygame.mouse.get_pos()
    
    num_total_archetypes = len(PLAYER_ARCHETYPES)
    archetypes_for_row1 = []
    archetype_for_row2 = None # Will hold the 4th archetype if it exists

    y_pos_row1 = 0
    y_pos_row2 = 0 

    if num_total_archetypes >= 4: # Two rows needed
        archetypes_for_row1 = PLAYER_ARCHETYPES[:3]
        archetype_for_row2 = PLAYER_ARCHETYPES[3]
        y_pos_row1 = surface.get_height() / 2 - option_height - row_padding / 2
        y_pos_row2 = surface.get_height() / 2 + row_padding / 2
    else: # Single row
        archetypes_for_row1 = PLAYER_ARCHETYPES[:]
        y_pos_row1 = surface.get_height() / 2 - option_height / 2

    # Draw Row 1
    start_x_for_row1 = 0
    if archetypes_for_row1:
        num_in_row1 = len(archetypes_for_row1)
        total_width_row1 = num_in_row1 * option_width + (num_in_row1 - 1) * horizontal_padding
        start_x_for_row1 = (surface.get_width() - total_width_row1) / 2
        for i, archetype in enumerate(archetypes_for_row1):
            option_x = start_x_for_row1 + i * (option_width + horizontal_padding)
            _draw_single_archetype_card(surface, archetype, option_x, y_pos_row1,
                                        option_width, option_height, mouse_pos, title_font, desc_font,
                                        standard_player_image, triple_shot_player_image,
                                        nova_burst_player_image, bouncing_shot_player_image)

    # Draw Row 2 (if the 4th archetype exists)
    if archetype_for_row2:
        # Position the 4th archetype under the 1st archetype of Row 1
        # start_x_for_row1 would be the x-coordinate of the first item in row 1.
        # If row 1 was empty, this would need a fallback, but given the logic,
        # if archetype_for_row2 exists, row 1 (archetypes_for_row1) is guaranteed to be populated.
        option_x_row2 = start_x_for_row1 
        
        _draw_single_archetype_card(surface, archetype_for_row2, option_x_row2, y_pos_row2,
                                    option_width, option_height, mouse_pos, title_font, desc_font,
                                    standard_player_image, triple_shot_player_image,
                                    nova_burst_player_image, bouncing_shot_player_image)


while running:
    # dt is delta time in seconds since last frame, used for framerate-independent physics.
    dt = clock.tick(settings.FPS) / 1000

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if character_select_active:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                for archetype in PLAYER_ARCHETYPES:
                    if archetype.get("rect") and archetype["rect"].collidepoint(mouse_pos):
                        selected_player_archetype = archetype
                        if select_archetype_sound:
                            select_archetype_sound.play()
                        character_select_active = False
                        game_over_active = False # Ensure it's false
                        store_active = False     # Ensure it's false
                        reset_game_state() # Initialize game with selected character
                        print(f"Selected: {selected_player_archetype['name']}")
                        break
        elif game_over_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    reset_game_state() # Restart with the same character
                    game_over_active = False # Explicitly set game_over_active to False
        elif store_active: # Store is active, and game is not over
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Left mouse button
                mouse_pos = pygame.mouse.get_pos()
                for item in displayed_store_items: # Check against displayed items
                    if item["rect"] and item["rect"].collidepoint(mouse_pos):
                        # Apply upgrade
                        if item["id"] == "faster_shots":
                            SHOOT_COOLDOWN = max(0.05, SHOOT_COOLDOWN * 0.85) 
                            print(f"Faster Shots purchased! New cooldown: {SHOOT_COOLDOWN:.2f}")
                        elif item["id"] == "pickup_radius":
                            player_pickup_radius_multiplier *= 1.25
                            print(f"Pickup Radius+ purchased! New multiplier: {player_pickup_radius_multiplier:.2f}")
                        elif item["id"] == "player_speed":
                            movement_speed = int(movement_speed * 1.15)
                            print(f"Player Speed+ purchased! New speed: {movement_speed:.0f}")
                        elif item["id"] == "max_health":
                            max_player_health = int(max_player_health * 1.20)
                            current_player_health = max_player_health # Heal to new max
                            print(f"Max Health+ purchased! New max health: {max_player_health}")
                        elif item["id"] == "heal_fully":
                            current_player_health = max_player_health
                            print(f"Healed Fully! Health: {current_player_health}/{max_player_health}")
                        elif item["id"] == "orbital_weapon":
                            # For now, let's assume only one can be active or they stack somehow
                            # This adds a new one each time. You might want to limit this or enhance existing.
                            new_orbital = OrbitalWeapon(player_pos) # Pass the actual player_pos Vector2 object
                            active_orbital_weapons.append(new_orbital)
                            print(f"Orbital Guard activated! Count: {len(active_orbital_weapons)}")
                        elif item["id"] == "boomerang_weapon":
                            if not has_boomerang_weapon: # Check to prevent re-activating if somehow offered again
                                has_boomerang_weapon = True
                                print("Boomerang Weapon activated!")

                        # Increase the requirement for the next bar fill
                        MAX_PICKUPS_FOR_FULL_BAR = int(MAX_PICKUPS_FOR_FULL_BAR * 1.2 + 1)
                        print(f"Next upgrade will require {MAX_PICKUPS_FOR_FULL_BAR} pickups.")

                        store_active = False
                        current_pickups_count = 0 # Reset bar
                        displayed_store_items.clear() # Clear offerings for next time
                        break 
                # If no item was purchased (due to break), check continue button
                if store_active and continue_button_rect and continue_button_rect.collidepoint(mouse_pos):
                    store_active = False
                    current_pickups_count = 0 # Reset bar
                    displayed_store_items.clear() # Clear offerings
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                store_active = False
                current_pickups_count = 0 # Reset bar when escaping store
                displayed_store_items.clear() # Clear offerings
        else: # Gameplay is active (not game over, not store)
            # Handle other gameplay-specific events if any (currently none besides quit handled globally)
            pass

    # --- Game State Updates ---
    # Background color transition (always active, even on game over screen for effect)
    bg_color_transition_progress += settings.BG_COLOR_TRANSITION_SPEED * dt
    if bg_color_transition_progress >= 1.0:
        bg_color_transition_progress = 0.0 # Reset progress
        current_bg_color_index = next_bg_color_index
        next_bg_color_index = (next_bg_color_index + 1) % len(settings.BG_CYCLE_COLORS)

    # Interpolate between the current and next background color
    color1 = settings.BG_CYCLE_COLORS[current_bg_color_index]
    color2 = settings.BG_CYCLE_COLORS[next_bg_color_index]
    dynamic_bg_color = color1.lerp(color2, bg_color_transition_progress)

    if not game_over_active and not character_select_active: # Only run game logic if not game over and character selected
        if not store_active:
            # --- Active Gameplay Logic ---
            total_game_time_seconds += dt # Increment game timer

            # Player Movement
            move_direction = pygame.Vector2(0, 0)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                move_direction.y -= 1
            if keys[pygame.K_s]:
                move_direction.y += 1
            if keys[pygame.K_a]:
                move_direction.x -= 1
            if keys[pygame.K_d]:
                move_direction.x += 1
            if move_direction.length_squared() > 0:
                move_direction.normalize_ip()
                player_pos += move_direction * movement_speed * dt

            # --- Player Trail Update ---
            # Add current position to the trail history (world coordinates)
            player_trail_positions.append(player_pos.copy())
            if len(player_trail_positions) > settings.MAX_TRAIL_LENGTH:
                player_trail_positions.pop(0) # Remove the oldest position

            # Update camera_offset to keep player centered
            camera_offset.x = player_pos.x - screen.get_width() / 2
            camera_offset.y = player_pos.y - screen.get_height() / 2

            # Clamp player_pos to world boundaries (if a background tile exists)
            if TILE_WIDTH > 0 and TILE_HEIGHT > 0:
                world_width_px = WORLD_TILES_X * TILE_WIDTH
                world_height_px = WORLD_TILES_Y * TILE_HEIGHT
                
                player_pos.x = max(player_radius, min(player_pos.x, world_width_px - player_radius))
                player_pos.y = max(player_radius, min(player_pos.y, world_height_px - player_radius))
                # Re-calculate camera_offset after clamping player_pos to ensure it's also correct at boundaries
                camera_offset.x = player_pos.x - screen.get_width() / 2
                camera_offset.y = player_pos.y - screen.get_height() / 2

            # Shooting Logic
            current_time = pygame.time.get_ticks() / 1000.0
            if selected_player_archetype: # Ensure an archetype is selected
                effective_shoot_cooldown = SHOOT_COOLDOWN * selected_player_archetype["shoot_cooldown_modifier"]
                
                # Allow shooting even if no enemies for Nova, for others require enemies
                can_shoot_condition = enemies or selected_player_archetype["id"] in ["nova_burst", "bouncing_shot"]

                if (current_time - last_shot_time > effective_shoot_cooldown) and can_shoot_condition:
                    last_shot_time = current_time
                    shoot_func = SHOOT_FUNCTIONS[selected_player_archetype["shoot_function_name"]]
                    shoot_func(player_pos, enemies, particles, settings.LIGHT_SKY_BLUE, camera_offset)

            # Boomerang Firing Logic (if weapon acquired)
            if has_boomerang_weapon and enemies and \
               (current_time - last_boomerang_shot_time > settings.BOOMERANG_WEAPON_SHOOT_COOLDOWN):
                last_boomerang_shot_time = current_time
                nearest_enemy = min(enemies, key=lambda e: (e.pos - player_pos).length_squared())
                boomerang_projectiles.append(BoomerangProjectile(player_pos.copy(), nearest_enemy.pos.copy()))
                if boomerang_shot_sound:
                    boomerang_shot_sound.play()

            # Enemy Spawning
            enemy_spawn_timer += dt
            if enemy_spawn_timer >= ENEMY_SPAWN_INTERVAL and len(enemies) < MAX_ENEMIES:
                enemy_spawn_timer = 0.0
                spawn_type_roll = random.random()
                screen_w, screen_h = screen.get_width(), screen.get_height() # Used by all spawns

                # Determine spawn edge and base position (world coordinates)
                edge = random.choice(["top", "bottom", "left", "right"])
                margin = 30 # General margin for spawning off-screen
                world_cx, world_cy = 0, 0

                if edge == "top":
                    world_cx = camera_offset.x + random.uniform(margin * 2, screen_w - margin * 2)
                    world_cy = camera_offset.y - margin
                elif edge == "bottom":
                    world_cx = camera_offset.x + random.uniform(margin * 2, screen_w - margin * 2)
                    world_cy = camera_offset.y + screen_h + margin
                elif edge == "left":
                    world_cx = camera_offset.x - margin
                    world_cy = camera_offset.y + random.uniform(margin * 2, screen_h - margin * 2)
                else:  # right
                    world_cx = camera_offset.x + screen_w + margin
                    world_cy = camera_offset.y + random.uniform(margin * 2, screen_h - margin * 2)

                if spawn_type_roll < 0.40: # 40% chance for Triangle
                    enemies.append(EnemyTriangle((screen.get_width(), screen.get_height()), camera_offset))
                elif spawn_type_roll < 0.75: # 35% chance for Square Group (0.40 + 0.35 = 0.75)
                    num_squares = random.randint(SQUARE_GROUP_SIZE_MIN, SQUARE_GROUP_SIZE_MAX)
                    for _ in range(num_squares):
                        if len(enemies) < MAX_ENEMIES:
                            offset_world_pos = pygame.Vector2(world_cx + random.uniform(-25, 25), world_cy + random.uniform(-25, 25))
                            enemies.append(SquareEnemy(offset_world_pos, screen_w, screen_h))
                else: # 25% chance for Hexagon (remaining)
                    if len(enemies) < MAX_ENEMIES:
                        # Spawn a single hexagon at the calculated edge position
                        enemies.append(HexagonEnemy(pygame.Vector2(world_cx, world_cy), screen_w, screen_h))
            
            # Update Projectiles (Player Shots)
            world_bounds_for_particles = None
            if TILE_WIDTH > 0 and TILE_HEIGHT > 0: # If world map exists
                world_bounds_for_particles = (WORLD_TILES_X * TILE_WIDTH, WORLD_TILES_Y * TILE_HEIGHT)

            for particle in particles[:]:
                particle.update(dt, screen.get_width(), screen.get_height(), camera_offset, world_bounds_for_particles)
                if not particle.is_alive(screen.get_width(), screen.get_height(), camera_offset, world_bounds_for_particles):
                    particles.remove(particle)
            
            # Update Boomerang Projectiles
            for bp in boomerang_projectiles[:]:
                bp.update(dt, player_pos, world_bounds_for_particles) # player_pos for future use, world_bounds for consistency
                if not bp.is_alive(0,0,None,None): # Simpler is_alive check for boomerang
                    boomerang_projectiles.remove(bp)

            # Enemy Update
            for enemy in enemies: # No need to copy if not removing during iteration here
                enemy.update(player_pos, dt)

            # Update Orbital Weapons
            for orbital in active_orbital_weapons:
                orbital.update(dt) # player_pos is already a reference, so it uses the current player_pos

            # Enemy-Enemy Collision Resolution (to prevent stacking)
            for i, enemy1 in enumerate(enemies):
                for j in range(i + 1, len(enemies)):
                    enemy2 = enemies[j]
                    
                    dist_vec = enemy1.pos - enemy2.pos
                    dist_sq = dist_vec.length_squared()
                    total_radii = enemy1.collision_radius + enemy2.collision_radius

                    if dist_sq < total_radii**2 and dist_sq > 0: # They are overlapping and not at the exact same spot
                        distance = dist_vec.length()
                        overlap = total_radii - distance
                        separation_vector = dist_vec.normalize() * (overlap / 2) # Each moves by half the overlap
                        
                        enemy1.pos += separation_vector
                        enemy2.pos -= separation_vector
                    elif dist_sq == 0: # Exactly on top, nudge them apart randomly
                        nudge = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * 0.1
                        enemy1.pos += nudge
                        enemy2.pos -= nudge

            # Collision: Projectile vs Enemy
            for particle in particles[:]:
                for enemy in enemies[:]: # Copy for safe removal
                    enemy_col_radius = 0
                    if isinstance(enemy, EnemyTriangle):
                        enemy_col_radius = enemy.height * 0.5 # Approx radius for triangle tip area
                    elif isinstance(enemy, SquareEnemy):
                        enemy_col_radius = enemy.size * 0.707 # Approx half diagonal for square
                    elif isinstance(enemy, HexagonEnemy):
                        enemy_col_radius = enemy.radius_stat # Hexagon radius (center to vertex)

                    if (particle.pos - enemy.pos).length_squared() < (particle.radius + enemy_col_radius)**2:
                        should_remove_particle = True
                        
                        if isinstance(particle, BouncingParticle):
                            if particle.bounces_left > 0:
                                particle.bounce_off_object(enemy.pos, enemy_col_radius)
                                particle.bounces_left -= 1
                                # Consider adding a specific sound for enemy bounce if desired
                                # if particle.bounce_sound: particle.bounce_sound.play()
                                should_remove_particle = False # Don't remove if it bounced and has bounces left
                            # If bounces_left is 0 (or becomes <0 after decrement), it will be removed

                        if should_remove_particle and particle in particles:
                            particles.remove(particle) # Check if still exists before removing
                        
                        destroyed = enemy.take_damage() if hasattr(enemy, 'take_damage') else True
                        if enemy_hit_sound and destroyed: # Play sound if destroyed and sounds are loaded
                            random.choice(enemy_hit_sound).play()
                        if destroyed:
                            # Chance to drop a special pickup
                            if random.random() < SPECIAL_PICKUP_CHANCE:
                                pickup_particles.append(PickupParticle(enemy.pos, color=settings.SPECIAL_PICKUP_COLOR, width=settings.SPECIAL_PICKUP_WIDTH, height=settings.SPECIAL_PICKUP_HEIGHT, value=settings.SPECIAL_PICKUP_VALUE))
                            else:
                                pickup_particles.append(PickupParticle(enemy.pos, color=settings.GOLD, width=settings.PICKUP_PARTICLE_WIDTH, height=settings.PICKUP_PARTICLE_HEIGHT, value=1))

                            kill_count += 1 # Increment kill count
                            if enemy in enemies: enemies.remove(enemy) # Check if still exists
                        
                        # Particle interacts with one enemy per collision pass.
                        # If it was a standard particle, it's removed. If bouncing, it has bounced.
                        break 

            # Collision: Boomerang Projectile vs Enemy
            for bp in boomerang_projectiles: # Boomerangs are not removed on hit
                for enemy in enemies[:]:
                    enemy_col_radius = 0
                    if isinstance(enemy, EnemyTriangle): enemy_col_radius = enemy.height * 0.5
                    elif isinstance(enemy, SquareEnemy): enemy_col_radius = enemy.size * 0.707
                    elif isinstance(enemy, HexagonEnemy): enemy_col_radius = enemy.radius_stat

                    if (bp.pos - enemy.pos).length_squared() < (bp.radius + enemy_col_radius)**2:
                        enemy_id = id(enemy)
                        if enemy_id not in bp.hit_enemies_this_pass:
                            bp.hit_enemies_this_pass.add(enemy_id)
                            
                            destroyed = False
                            if hasattr(enemy, 'take_damage'):
                                destroyed = enemy.take_damage(bp.damage)
                            else: # Simple enemies might be one-hit
                                destroyed = True 

                            if enemy_hit_sound: random.choice(enemy_hit_sound).play()
                            
                            if destroyed:
                                if random.random() < SPECIAL_PICKUP_CHANCE: pickup_particles.append(PickupParticle(enemy.pos, color=settings.SPECIAL_PICKUP_COLOR, width=settings.SPECIAL_PICKUP_WIDTH, height=settings.SPECIAL_PICKUP_HEIGHT, value=settings.SPECIAL_PICKUP_VALUE))
                                else: pickup_particles.append(PickupParticle(enemy.pos, value=1))
                                kill_count += 1
                                if enemy in enemies: enemies.remove(enemy)
                        # Boomerang continues, does not break from inner loop unless you want it to hit only one enemy per frame

            # Collision: Orbital Weapon vs Enemy
            current_time_seconds = total_game_time_seconds # Use consistent game time
            for orbital in active_orbital_weapons:
                for enemy in enemies[:]: # Iterate over a copy for safe removal
                    enemy_col_radius = 0
                    if isinstance(enemy, EnemyTriangle):
                        enemy_col_radius = enemy.height * 0.5
                    elif isinstance(enemy, SquareEnemy):
                        enemy_col_radius = enemy.size * 0.707
                    elif isinstance(enemy, HexagonEnemy):
                        enemy_col_radius = enemy.radius_stat

                    if (orbital.pos - enemy.pos).length_squared() < (orbital.radius + enemy_col_radius)**2:
                        # Check cooldown for this specific enemy
                        enemy_id = id(enemy) # Get a unique ID for the enemy instance
                        last_hit = orbital.last_hit_times.get(enemy_id, 0)
                        if current_time_seconds - last_hit > orbital.hit_cooldown:
                            orbital.last_hit_times[enemy_id] = current_time_seconds
                            
                            destroyed = enemy.take_damage(orbital.damage) if hasattr(enemy, 'take_damage') else True # Pass orbital's damage
                            if enemy_hit_sound: # Play sound regardless of destruction for orbitals
                                random.choice(enemy_hit_sound).play()
                            if destroyed:
                                if random.random() < SPECIAL_PICKUP_CHANCE: pickup_particles.append(PickupParticle(enemy.pos, color=settings.SPECIAL_PICKUP_COLOR, width=settings.SPECIAL_PICKUP_WIDTH, height=settings.SPECIAL_PICKUP_HEIGHT, value=settings.SPECIAL_PICKUP_VALUE))
                                else: pickup_particles.append(PickupParticle(enemy.pos, value=1))
                                kill_count += 1
                                if enemy in enemies: enemies.remove(enemy)
            # Collision: Player vs Pickup Particle
            pickups_to_keep = []
            for pickup in pickup_particles:
                # AABB collision check: player (circle approximated as square) vs pickup (ellipse bounding box)
                effective_player_pickup_radius = player_radius * player_pickup_radius_multiplier
                player_world_rect = pygame.Rect(player_pos.x - effective_player_pickup_radius,
                                                player_pos.y - effective_player_pickup_radius,
                                                effective_player_pickup_radius * 2, effective_player_pickup_radius * 2)
                pickup_world_rect = pygame.Rect(pickup.pos.x - pickup.width / 2,
                                                pickup.pos.y - pickup.height / 2,
                                                pickup.width, pickup.height)
                if player_world_rect.colliderect(pickup_world_rect):
                    if pickup_sound:
                        pickup_sound.play()
                    if current_pickups_count < MAX_PICKUPS_FOR_FULL_BAR:
                        current_pickups_count += pickup.value
                    if current_pickups_count >= MAX_PICKUPS_FOR_FULL_BAR and not store_active: # Check store_active again
                        # Level up!
                        player_level += 1 # Increment level when bar is full
                        populate_store_offerings() # Choose items for the store
                        MAX_ENEMIES = int(MAX_ENEMIES * 1.25) # Increase max enemies
                        store_active = True
                        current_pickups_count = MAX_PICKUPS_FOR_FULL_BAR # Cap it
                else:
                    pickups_to_keep.append(pickup)
            pickup_particles = pickups_to_keep

            # --- Collision Detection (Player vs Enemy) ---
            for enemy in enemies[:]: # Iterate over a copy in case an enemy is removed (though not in this loop)
                enemy_hitbox_radius_for_player = 0
                if isinstance(enemy, EnemyTriangle):
                    # For triangle, pos is the tip. A smaller radius from the tip for player collision.
                    enemy_hitbox_radius_for_player = enemy.height * 0.4 
                elif isinstance(enemy, SquareEnemy):
                    # For square, pos is the center. Radius is approx half diagonal.
                    enemy_hitbox_radius_for_player = enemy.size * 0.5 
                elif isinstance(enemy, HexagonEnemy):
                    # For hexagon, use its radius, perhaps slightly reduced for player collision
                    enemy_hitbox_radius_for_player = enemy.radius_stat * 0.85
                if (player_pos - enemy.pos).length_squared() < (player_radius + enemy_hitbox_radius_for_player)**2:
                    current_player_health -= 1
                    print(f"Player hit! Health: {current_player_health}/{max_player_health}")
                    # Knockback the enemy slightly or destroy if it's a one-hit type for player collision
                    kill_count +=1 # Increment kill count when player collision destroys an enemy
                    if enemy in enemies: enemies.remove(enemy) # Simple removal on hit, can be more complex

                    if current_player_health <= 0:
                        if player_death_sound:
                            player_death_sound.play()
                        game_over_active = True
                        store_active = False 
                        print(f"GAME OVER: Player health depleted by {type(enemy).__name__} at {enemy.pos}")
                    elif enemy_hit_sound: # Player was hit but not dead
                        random.choice(enemy_hit_sound).play() # Play a generic hit sound
                    # Optional: Clear dynamic elements for a cleaner game over screen
                    # enemies.clear()
                    # particles.clear() 
                    # pickup_particles.clear()
                    break # One collision is enough to end the game
        # else: store is active, most gameplay logic is paused
    # else: game is over, all gameplay logic is paused

    # --- Drawing ---
    screen.fill(dynamic_bg_color) # Always fill screen with current background

    # Draw Tiled Background (if image loaded)
    if static_background_image and TILE_WIDTH > 0 and TILE_HEIGHT > 0:
        # Calculate which tiles are visible
        start_col = int(camera_offset.x // TILE_WIDTH)
        end_col = int((camera_offset.x + screen.get_width()) // TILE_WIDTH)
        start_row = int(camera_offset.y // TILE_HEIGHT)
        end_row = int((camera_offset.y + screen.get_height()) // TILE_HEIGHT)

        for row in range(max(0, start_row), min(WORLD_TILES_Y, end_row + 1)):
            for col in range(max(0, start_col), min(WORLD_TILES_X, end_col + 1)):
                tile_world_x = col * TILE_WIDTH
                tile_world_y = row * TILE_HEIGHT
                
                # Convert tile's world position to screen position
                tile_screen_x = tile_world_x - camera_offset.x
                tile_screen_y = tile_world_y - camera_offset.y
                
                screen.blit(static_background_image, (tile_screen_x, tile_screen_y))
    elif static_background_image: # Fallback if TILE_WIDTH/HEIGHT somehow 0 but image exists
        screen.blit(static_background_image, (0,0)) # Original behavior

    if character_select_active:
        draw_character_select_screen(screen)
    elif game_over_active:
        draw_game_over_screen(screen, total_game_time_seconds)
    else: # Game is active (could be gameplay or store mode)
        # Draw pickup particles (gold)
        for pickup in pickup_particles:
            pickup.draw(screen, camera_offset)
        
        if not store_active: # Only draw these game elements if not in store
            # --- Draw Player Trail ---
            if selected_player_archetype:
                trail_image_base = None
                if selected_player_archetype["id"] == "standard" and standard_player_image:
                    trail_image_base = standard_player_image
                elif selected_player_archetype["id"] == "triple_shot" and triple_shot_player_image:
                    trail_image_base = triple_shot_player_image
                elif selected_player_archetype["id"] == "nova_burst" and nova_burst_player_image:
                    trail_image_base = nova_burst_player_image
                elif selected_player_archetype["id"] == "bouncing_shot" and bouncing_shot_player_image:
                    trail_image_base = bouncing_shot_player_image

                num_trail_segments = len(player_trail_positions)
                for i, trail_world_pos in enumerate(player_trail_positions):
                    # Alpha fades from transparent (oldest) to TRAIL_MAX_ALPHA (newest in trail)
                    alpha = int(((i + 1) / num_trail_segments) * settings.TRAIL_MAX_ALPHA) if num_trail_segments > 0 else settings.TRAIL_MAX_ALPHA
                    
                    trail_screen_pos = trail_world_pos - camera_offset

                    if trail_image_base:
                        temp_trail_image = trail_image_base.copy()
                        temp_trail_image.set_alpha(alpha)
                        trail_image_rect = temp_trail_image.get_rect(center=trail_screen_pos)
                        screen.blit(temp_trail_image, trail_image_rect)
                    else: # Fallback to drawing circles for trail if no image
                        player_draw_color = selected_player_archetype["color"]
                        # Create a temporary surface for the circle to apply alpha
                        # Ensure the surface is large enough for the player_radius
                        trail_circle_surface_size = player_radius * 2
                        trail_circle_surface = pygame.Surface((trail_circle_surface_size, trail_circle_surface_size), pygame.SRCALPHA)
                        pygame.draw.circle(trail_circle_surface, (*player_draw_color, alpha), (player_radius, player_radius), player_radius)

                        trail_circle_rect = trail_circle_surface.get_rect(center=trail_screen_pos)
                        screen.blit(trail_circle_surface, trail_circle_rect)

            # Draw player projectiles (shots)
            for particle in particles: # Player shots
                particle.draw(screen, camera_offset)

            # Draw Boomerang projectiles
            for bp in boomerang_projectiles:
                bp.draw(screen, camera_offset)

            # Draw enemies
            for enemy in enemies:
                if isinstance(enemy, EnemyTriangle):
                    enemy.draw(screen, player_pos, camera_offset) # player_pos is world pos
                else: # SquareEnemy
                    enemy.draw(screen, camera_offset)
        
        # Draw Orbital Weapons (drawn on top of enemies, under player if desired, or adjust order)
        for orbital in active_orbital_weapons:
            orbital.draw(screen, camera_offset)

        # Draw player
        player_screen_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
        drawn_player_bottom_y = player_screen_pos.y + player_radius # Default for circle

        if selected_player_archetype and selected_player_archetype["id"] == "standard" and standard_player_image:
            player_image_rect = standard_player_image.get_rect(center=player_screen_pos)
            screen.blit(standard_player_image, player_image_rect)
            drawn_player_bottom_y = player_image_rect.bottom
        elif selected_player_archetype and selected_player_archetype["id"] == "triple_shot" and triple_shot_player_image:
            player_image_rect = triple_shot_player_image.get_rect(center=player_screen_pos)
            screen.blit(triple_shot_player_image, player_image_rect)
            drawn_player_bottom_y = player_image_rect.bottom
        elif selected_player_archetype and selected_player_archetype["id"] == "nova_burst" and nova_burst_player_image:
            player_image_rect = nova_burst_player_image.get_rect(center=player_screen_pos)
            screen.blit(nova_burst_player_image, player_image_rect)
            drawn_player_bottom_y = player_image_rect.bottom
        elif selected_player_archetype and selected_player_archetype["id"] == "bouncing_shot" and bouncing_shot_player_image:
            player_image_rect = bouncing_shot_player_image.get_rect(center=player_screen_pos)
            screen.blit(bouncing_shot_player_image, player_image_rect)
            drawn_player_bottom_y = player_image_rect.bottom
        elif selected_player_archetype: # Other archetypes or fallback
            player_draw_color = selected_player_archetype["color"]
            pygame.draw.circle(screen, player_draw_color, player_screen_pos, player_radius)
            # drawn_player_bottom_y remains as player_screen_pos.y + player_radius
        else: # Fallback if no archetype selected (should not happen post-selection)
            pygame.draw.circle(screen, settings.CRIMSON, player_screen_pos, player_radius)
            # drawn_player_bottom_y remains as player_screen_pos.y + player_radius

        # Draw Player Health Bar (below player)
        if current_player_health > 0: # Only draw if alive
            health_ratio = current_player_health / max_player_health if max_player_health > 0 else 0
            bar_fill_width = int(PLAYER_HEALTH_BAR_WIDTH * health_ratio)
            bar_x = player_screen_pos.x - PLAYER_HEALTH_BAR_WIDTH / 2
            bar_y = drawn_player_bottom_y + PLAYER_HEALTH_BAR_Y_OFFSET - PLAYER_HEALTH_BAR_HEIGHT # Adjusted Y

            # Background of health bar (e.g., dark red or grey)
            pygame.draw.rect(screen, settings.DARK_SLATE_GRAY, (bar_x, bar_y, PLAYER_HEALTH_BAR_WIDTH, PLAYER_HEALTH_BAR_HEIGHT))
            # Fill of health bar (e.g., green or red)
            pygame.draw.rect(screen, settings.DARK_SEA_GREEN, (bar_x, bar_y, bar_fill_width, PLAYER_HEALTH_BAR_HEIGHT))

        # Draw UI Bar for pickups
        pygame.draw.rect(screen, BAR_BG_COLOR, (BAR_X, BAR_Y, BAR_MAX_WIDTH, BAR_HEIGHT))
        fill_ratio = min(current_pickups_count / MAX_PICKUPS_FOR_FULL_BAR, 1.0) if MAX_PICKUPS_FOR_FULL_BAR > 0 else 0
        actual_fill_width = fill_ratio * BAR_MAX_WIDTH
        pygame.draw.rect(screen, BAR_FILL_COLOR, (BAR_X, BAR_Y, actual_fill_width, BAR_HEIGHT))

        # Draw Player Level
        level_text_str = f"Level: {player_level}"
        level_surf = ui_font.render(level_text_str, True, LEVEL_TEXT_COLOR)
        # Position it to the right of the bar, vertically centered with the bar
        level_rect = level_surf.get_rect(midleft=(BAR_X + BAR_MAX_WIDTH + LEVEL_TEXT_OFFSET_X, BAR_Y + BAR_HEIGHT / 2))
        screen.blit(level_surf, level_rect)

        # Draw Game Timer (top right)
        minutes = int(total_game_time_seconds // 60)
        seconds = int(total_game_time_seconds % 60)
        timer_text = f"{minutes:02}:{seconds:02}"
        timer_surf = ui_font.render(timer_text, True, settings.WHITE)
        timer_rect = timer_surf.get_rect(topright=(screen.get_width() - 20, 20))
        screen.blit(timer_surf, timer_rect)

        # Draw Kill Counter (below timer)
        kill_text_str = f"Kills: {kill_count}"
        kill_surf = ui_font.render(kill_text_str, True, settings.WHITE)
        kill_rect = kill_surf.get_rect(topright=(screen.get_width() - 20, timer_rect.bottom + 5)) # Position below timer
        screen.blit(kill_surf, kill_rect)

        if store_active: # Draw store on top if active (and game not over)
            draw_store_window(screen)

    # flip() the display to put your work on screen
    pygame.display.flip()

pygame.display.quit() # Explicitly quit display before pygame.quit()
pygame.quit()
sys.exit()
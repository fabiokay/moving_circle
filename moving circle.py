# Example file showing a circle moving on screen
import pygame
import random
import sys # For pygame.quit()

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
dt = 0

# --- Colors ---
black = pygame.Color("#141728")
grey  = pygame.Color("#727880") 
violet = pygame.Color("#5C3A93")
petrol = pygame.Color("#387487")
blue = pygame.Color("#59C3C3")
white = pygame.Color("#EBEBEB")
pink = pygame.Color("#D154CA")
dark_slate_gray = pygame.Color("#2F4F4F")
steel_blue = pygame.Color("#4682B4")
olive_drab = pygame.Color("#6B8E23")
coral = pygame.Color("#FF7F50")
khaki = pygame.Color("#994C2C")
teal = pygame.Color("#008080")
medium_purple = pygame.Color("#9370DB")
dark_sea_green = pygame.Color("#8FBC8F")
light_sky_blue = pygame.Color("#87CEFA")
crimson = pygame.Color("#740B20")

# --- Additional Colors ---
gold = pygame.Color("#FFF200") # For pickup particles
dark_blue = pygame.Color("#00008B") # For store background

# --- Background Color Cycling ---
BG_CYCLE_COLORS = [
    pygame.Color("#141728"), # Initial black
    pygame.Color("#2F4F4F"), # dark_slate_gray
    petrol,
    pygame.Color("#00008B"), # dark_blue (used in store, good for a darker phase)
    violet,
]
current_bg_color_index = 0
next_bg_color_index = 1
bg_color_transition_progress = 0.0
BG_COLOR_TRANSITION_SPEED = 0.02 # Speed of transition (0.02 means 50 seconds for a full cycle segment)
dynamic_bg_color = BG_CYCLE_COLORS[current_bg_color_index]

player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
player_radius = 10

# --- Particle shoot Setup ---
class Particle:
    def __init__(self, start_pos, target_pos, color=white, speed=250, radius=4):
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

    def update(self, dt):
        self.pos += self.direction * self.speed * dt

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

    def is_offscreen(self, screen_width, screen_height):
        return (self.pos.x < -self.radius or self.pos.x > screen_width + self.radius or
                self.pos.y < -self.radius or self.pos.y > screen_height + self.radius)


# --- Enemy Triangle Setup ---
class EnemyTriangle:
    def __init__(self, screen_width, screen_height):
        self.height = 20  # Length from tip to middle of base
        self.base_width = 15  # Full width of the base
        self.speed = random.uniform(70, 110)  # Pixels per second
        self.color = olive_drab # You can pick any color or randomize it

        # Spawn on a random edge, with the tip (self.pos) starting off-screen
        edge = random.choice(["top", "bottom", "left", "right"])
        margin = self.height # Ensure it spawns fully off-screen

        if edge == "top":
            self.pos = pygame.Vector2(random.uniform(0, screen_width), -margin)
        elif edge == "bottom":
            self.pos = pygame.Vector2(random.uniform(0, screen_width), screen_height + margin)
        elif edge == "left":
            self.pos = pygame.Vector2(-margin, random.uniform(0, screen_height))
        else:  # right
            self.pos = pygame.Vector2(screen_width + margin, random.uniform(0, screen_height))

    def update(self, target_pos, dt):
        # Move towards the target_pos
        if (target_pos - self.pos).length_squared() > 0:  # Avoid division by zero if already at target
            direction = (target_pos - self.pos).normalize()
            self.pos += direction * self.speed * dt

    def draw(self, surface, target_pos):
        # Calculate direction vector towards target for orientation
        direction_to_target = pygame.Vector2(0, -1) # Default if on top of target (e.g., point "up")
        if (target_pos - self.pos).length_squared() > 0:
            direction_to_target = (target_pos - self.pos).normalize()

        # p1 is the tip of the triangle, which is self.pos
        p1 = self.pos

        # Calculate center of the base (behind the tip)
        base_center = self.pos - direction_to_target * self.height
        # Calculate perpendicular vector for the base spread
        perp_vector = pygame.Vector2(-direction_to_target.y, direction_to_target.x)
        p2 = base_center + perp_vector * (self.base_width / 2)
        p3 = base_center - perp_vector * (self.base_width / 2)
        pygame.draw.polygon(surface, self.color, [p1, p2, p3])

# --- Enemy Square Setup ---
class SquareEnemy:
    def __init__(self, pos, screen_width, screen_height, size=18, speed=None):
        self.size = size
        self.pos = pygame.Vector2(pos)
        if speed is None:
            self.speed = random.uniform(60, 100)
        else:
            self.speed = speed
        self.initial_color = steel_blue
        self.damaged_color = grey
        self.color = self.initial_color
        self.health = 2
        self.max_health = 2 # Store max health for potential future use (e.g. health bars)

    def update(self, target_pos, dt):
        if (target_pos - self.pos).length_squared() > 0:
            direction = (target_pos - self.pos).normalize()
            self.pos += direction * self.speed * dt

    def draw(self, surface):
        # Change color if damaged
        if self.health < self.max_health:
            self.color = self.damaged_color
        else:
            self.color = self.initial_color
        
        rect = pygame.Rect(self.pos.x - self.size / 2, 
                           self.pos.y - self.size / 2, 
                           self.size, self.size)
        pygame.draw.rect(surface, self.color, rect)

    def take_damage(self):
        self.health -= 1
        if self.health <= 0:
            return True # Destroyed
        return False # Still alive


# --- Pickup Particle Setup ---
class PickupParticle:
    def __init__(self, pos, color=gold, radius=7):
        self.pos = pygame.Vector2(pos) # Position where it's dropped
        self.radius = radius
        self.color = color

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

# --- Enemy Variables ---
enemies = []
enemy_spawn_timer = 0.0
ENEMY_SPAWN_INTERVAL = 1.5  # Seconds between spawns
MAX_ENEMIES = 50 # Maximum number of enemies on screen (reduced a bit due to groups)
SQUARE_GROUP_SIZE_MIN = 2
SQUARE_GROUP_SIZE_MAX = 4
pickup_particles = [] # List to store pickup particles

# --- Shooting Variables
particles = []
SHOOT_COOLDOWN = 1.0  # Seconds
last_shot_time = 0.0

# --- Player Variables ---
movement_speed = 200 # Player movement speed, made global for upgrades


# --- UI Bar Setup ---
BAR_HEIGHT = 25  # Height of the horizontal bar (pixels)
BAR_MAX_WIDTH = 300 # Max width of the fillable bar
BAR_X = screen.get_width() // 2 - BAR_MAX_WIDTH // 2 # Centered horizontally
BAR_Y = 20 # Small margin from the top edge
BAR_BG_COLOR = dark_slate_gray # Background color of the bar
BAR_FILL_COLOR = gold # Color of the filling part of the bar
MAX_PICKUPS_FOR_FULL_BAR = 10 # Number of gold particles to collect to fill the bar
current_pickups_count = 0 # How many pickups collected towards the current bar fill

# --- Store Setup ---
store_active = False
STORE_BG_COLOR = dark_blue
STORE_TEXT_COLOR = white
STORE_BUTTON_COLOR = steel_blue
STORE_BUTTON_HOVER_COLOR = light_sky_blue

# --- Game Timer ---
total_game_time_seconds = 0.0
ui_font = None # Will be initialized with store fonts

try:
    store_font_large = pygame.font.Font(None, 48) # For title
    store_font_medium = pygame.font.Font(None, 36) # For buttons/text
except pygame.error as e:
    print(f"Font loading error: {e}. Using default system font.")
    store_font_large = pygame.font.SysFont(None, 48)
    store_font_medium = pygame.font.SysFont(None, 36)
ui_font = store_font_medium # Use the medium font for UI elements like the timer


store_items = [
    {"id": "faster_shots", "text": "Faster Shots", "cost_text": "(Full Bar)", "rect": None},
    {"id": "player_speed", "text": "Player Speed+", "cost_text": "(Full Bar)", "rect": None},
]
continue_button_text = "Continue Game"
continue_button_rect = None

def draw_store_window(surface):
    global continue_button_rect # Allow modification
    store_width = 500
    store_height = 400
    store_x = (surface.get_width() - store_width) // 2
    store_y = (surface.get_height() - store_height) // 2

    # Draw background
    pygame.draw.rect(surface, STORE_BG_COLOR, (store_x, store_y, store_width, store_height), border_radius=10)
    pygame.draw.rect(surface, white, (store_x, store_y, store_width, store_height), width=2, border_radius=10) # Border

    # Title
    title_surf = store_font_large.render("UPGRADE STORE", True, STORE_TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(store_x + store_width // 2, store_y + 40))
    surface.blit(title_surf, title_rect)

    button_height = 50
    button_padding = 20
    current_y = store_y + 100

    mouse_pos = pygame.mouse.get_pos()

    for i, item in enumerate(store_items):
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

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if store_active:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left mouse button
                    mouse_pos = pygame.mouse.get_pos()
                    for item in store_items:
                        if item["rect"] and item["rect"].collidepoint(mouse_pos):
                            # Apply upgrade
                            if item["id"] == "faster_shots":
                                SHOOT_COOLDOWN = max(0.05, SHOOT_COOLDOWN * 0.85) # Decrease by 15%, with a minimum
                                print(f"Faster Shots purchased! New cooldown: {SHOOT_COOLDOWN:.2f}")
                            elif item["id"] == "player_speed":
                                movement_speed *= 1.15 # Increase by 15%
                                print(f"Player Speed+ purchased! New speed: {movement_speed:.0f}")

                            # Increase the requirement for the next bar fill
                            MAX_PICKUPS_FOR_FULL_BAR = int(MAX_PICKUPS_FOR_FULL_BAR * 1.2 + 1)
                            print(f"Next upgrade will require {MAX_PICKUPS_FOR_FULL_BAR} pickups.")

                            store_active = False
                            current_pickups_count = 0 # Reset bar
                            break 
                    # If no item was purchased (due to break), check continue button
                    # Add 'and store_active' to ensure this only runs if the store wasn't closed by a purchase
                    if store_active and continue_button_rect and continue_button_rect.collidepoint(mouse_pos):
                        store_active = False
                        current_pickups_count = 0 # Reset bar
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    store_active = False
                    current_pickups_count = 0 # Reset bar when escaping store

    # --- Background Color Transition Logic ---
    # This should happen every frame, regardless of store state
    bg_color_transition_progress += BG_COLOR_TRANSITION_SPEED * dt

    if bg_color_transition_progress >= 1.0:
        bg_color_transition_progress = 0.0 # Reset progress
        current_bg_color_index = next_bg_color_index
        next_bg_color_index = (next_bg_color_index + 1) % len(BG_CYCLE_COLORS)

    # Interpolate between the current and next background color
    color1 = BG_CYCLE_COLORS[current_bg_color_index]
    color2 = BG_CYCLE_COLORS[next_bg_color_index]
    dynamic_bg_color = color1.lerp(color2, bg_color_transition_progress)

    # fill the screen with a color to wipe away anything from last frame
    screen.fill(dynamic_bg_color)

    if not store_active:
        move_vector = pygame.Vector2(0, 0)
        total_game_time_seconds += dt # Increment game timer only when game is active

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            move_vector.y -= 1
        if keys[pygame.K_s]:
            move_vector.y += 1
        if keys[pygame.K_a]:
            move_vector.x -= 1
        if keys[pygame.K_d]:
            move_vector.x += 1

        if move_vector.length_squared() > 0: # Check if there's any movement
            move_vector.normalize_ip() # Normalize to make length 1
            player_pos += move_vector * movement_speed * dt

        # --- Shooting Logic ---
        current_time = pygame.time.get_ticks() / 1000.0 # Current time in seconds
        if keys[pygame.K_SPACE] and (current_time - last_shot_time > SHOOT_COOLDOWN):
            if enemies: # Only shoot if there are enemies
                last_shot_time = current_time
                # Find nearest enemy
                nearest_enemy = None
                min_dist_sq = float('inf')
                for enemy in enemies:
                    dist_sq = (enemy.pos - player_pos).length_squared()
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        nearest_enemy = enemy
                
                if nearest_enemy:
                    particles.append(Particle(player_pos, nearest_enemy.pos, color=light_sky_blue))

        # --- Enemy Spawning ---
        enemy_spawn_timer += dt
        if enemy_spawn_timer >= ENEMY_SPAWN_INTERVAL and len(enemies) < MAX_ENEMIES:
            enemy_spawn_timer = 0.0  # Reset timer

            # Decide whether to spawn a triangle or a group of squares
            if random.random() < 0.6: # 60% chance to spawn a triangle
                if len(enemies) < MAX_ENEMIES:
                    new_enemy = EnemyTriangle(screen.get_width(), screen.get_height())
                    enemies.append(new_enemy)
            else: # 40% chance to spawn a square group
                num_squares_to_spawn = random.randint(SQUARE_GROUP_SIZE_MIN, SQUARE_GROUP_SIZE_MAX)
                
                # Determine a common spawn edge and general area for the group
                edge = random.choice(["top", "bottom", "left", "right"])
                margin = 30 # Margin from edge for the group's center
                group_center_x, group_center_y = 0, 0
                screen_w, screen_h = screen.get_width(), screen.get_height()

                if edge == "top": group_center_x, group_center_y = random.uniform(margin*2, screen_w-margin*2), -margin
                elif edge == "bottom": group_center_x, group_center_y = random.uniform(margin*2, screen_w-margin*2), screen_h + margin
                elif edge == "left": group_center_x, group_center_y = -margin, random.uniform(margin*2, screen_h-margin*2)
                else: group_center_x, group_center_y = screen_w + margin, random.uniform(margin*2, screen_h-margin*2)

                for _ in range(num_squares_to_spawn):
                    if len(enemies) < MAX_ENEMIES:
                        offset_pos = pygame.Vector2(group_center_x + random.uniform(-25, 25), group_center_y + random.uniform(-25, 25))
                        enemies.append(SquareEnemy(offset_pos, screen_w, screen_h))
        
        # --- Update and Draw Particles ---
        for particle in particles[:]:
            particle.update(dt)
            if particle.is_offscreen(screen.get_width(), screen.get_height()):
                particles.remove(particle)
            else:
                particle.draw(screen)

        # --- Enemy Update and Draw ---
        for enemy in enemies[:]: 
            enemy.update(player_pos, dt)
            if isinstance(enemy, EnemyTriangle):
                enemy.draw(screen, player_pos) 
            else: 
                enemy.draw(screen)

        # --- Collision Detection (Particle vs Enemy) ---
        for particle in particles[:]:
            for enemy in enemies[:]:
                enemy_collision_radius = 0
                if isinstance(enemy, EnemyTriangle):
                    enemy_collision_radius = enemy.height * 0.5 
                elif isinstance(enemy, SquareEnemy):
                    enemy_collision_radius = enemy.size * 0.707 

                if (particle.pos - enemy.pos).length_squared() < (particle.radius + enemy_collision_radius)**2:
                    particles.remove(particle) 
                    destroyed = False
                    if isinstance(enemy, SquareEnemy):
                        if enemy.take_damage(): 
                            destroyed = True
                    else: 
                        destroyed = True
                    
                    if destroyed:
                        pickup_particles.append(PickupParticle(enemy.pos, color=gold, radius=7))
                        enemies.remove(enemy)
                    break 

        # --- Collision Detection (Player vs Pickup Particle) ---
        pickups_to_keep = []
        for pickup in pickup_particles:
            if (player_pos - pickup.pos).length_squared() < (player_radius + pickup.radius)**2:
                if current_pickups_count < MAX_PICKUPS_FOR_FULL_BAR:
                    current_pickups_count += 1
                if current_pickups_count >= MAX_PICKUPS_FOR_FULL_BAR and not store_active:
                    store_active = True
                    current_pickups_count = MAX_PICKUPS_FOR_FULL_BAR # Cap it
            else:
                pickups_to_keep.append(pickup)
        pickup_particles = pickups_to_keep

        # --- Boundary Checks ---
        if player_pos.x - player_radius < 0: player_pos.x = player_radius
        if player_pos.x + player_radius > screen.get_width(): player_pos.x = screen.get_width() - player_radius
        if player_pos.y - player_radius < 0: player_pos.y = player_radius
        if player_pos.y + player_radius > screen.get_height(): player_pos.y = screen.get_height() - player_radius

    # --- Draw Pickup Particles (always draw, even if store is active) ---
    for pickup in pickup_particles: # Draw remaining pickups
        pickup.draw(screen)

    # --- Draw everything ---

    # --- Draw the Horizontal Fill Bar ---
    # Draw bar background
    pygame.draw.rect(screen, BAR_BG_COLOR, (BAR_X, BAR_Y, BAR_MAX_WIDTH, BAR_HEIGHT))
    # Calculate fill width
    fill_ratio = 0
    if MAX_PICKUPS_FOR_FULL_BAR > 0: # Avoid division by zero
        fill_ratio = min(current_pickups_count / MAX_PICKUPS_FOR_FULL_BAR, 1.0)
    
    actual_fill_width = fill_ratio * BAR_MAX_WIDTH
    # Draw the fill part (grows from left to right)
    pygame.draw.rect(screen, BAR_FILL_COLOR, (BAR_X, BAR_Y, actual_fill_width, BAR_HEIGHT))

    # Draw player on top of particles and enemies
    pygame.draw.circle(screen, crimson, player_pos, player_radius)

    # --- Draw Game Timer ---
    minutes = int(total_game_time_seconds // 60)
    seconds = int(total_game_time_seconds % 60)
    timer_text = f"{minutes:02}:{seconds:02}"
    timer_surf = ui_font.render(timer_text, True, white)
    timer_rect = timer_surf.get_rect(topright=(screen.get_width() - 20, 20)) # 20px margin
    screen.blit(timer_surf, timer_rect)



    # --- Draw Store Window (if active) ---
    if store_active:
        draw_store_window(screen)

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.display.quit() # Explicitly quit display before pygame.quit()
pygame.quit()
sys.exit()
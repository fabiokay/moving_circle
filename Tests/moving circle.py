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
INITIAL_MOVEMENT_SPEED = 200
movement_speed = INITIAL_MOVEMENT_SPEED # Player movement speed, made global for upgrades

# --- UI Bar Setup ---
INITIAL_MAX_PICKUPS_FOR_FULL_BAR = 10 # Number of gold particles to collect to fill the bar
MAX_PICKUPS_FOR_FULL_BAR = INITIAL_MAX_PICKUPS_FOR_FULL_BAR

BAR_HEIGHT = 25  # Height of the horizontal bar (pixels)
BAR_MAX_WIDTH = 300 # Max width of the fillable bar
BAR_X = screen.get_width() // 2 - BAR_MAX_WIDTH // 2 # Centered horizontally
BAR_Y = 20 # Small margin from the top edge
BAR_BG_COLOR = dark_slate_gray # Background color of the bar
BAR_FILL_COLOR = gold # Color of the filling part of the bar
current_pickups_count = 0 # How many pickups collected towards the current bar fill

# --- Store Setup ---
store_active = False
STORE_BG_COLOR = dark_blue
STORE_TEXT_COLOR = white
STORE_BUTTON_COLOR = steel_blue

INITIAL_SHOOT_COOLDOWN = 1.0
SHOOT_COOLDOWN = INITIAL_SHOOT_COOLDOWN # Seconds
STORE_BUTTON_HOVER_COLOR = light_sky_blue

# --- Game Timer ---
total_game_time_seconds = 0.0
ui_font = None # Will be initialized with store fonts

# --- Game Over State ---
game_over_active = False
game_over_font_large = None # For "GAME OVER" text
# ui_font (store_font_medium) will be used for smaller game over text like score

try:
    store_font_large = pygame.font.Font(None, 48) # For title
    store_font_medium = pygame.font.Font(None, 36) # For buttons/text
    game_over_font_large = pygame.font.Font(None, 96) # Larger font for "GAME OVER"
except pygame.error as e:
    print(f"Font loading error: {e}. Using default system font.")
    store_font_large = pygame.font.SysFont(None, 48)
    store_font_medium = pygame.font.SysFont(None, 36)
    game_over_font_large = pygame.font.SysFont(None, 96)
ui_font = store_font_medium # Use the medium font for UI elements like the timer


store_items = [
    {"id": "faster_shots", "text": "Faster Shots", "cost_text": "(Full Bar)", "rect": None},
    {"id": "player_speed", "text": "Player Speed+", "cost_text": "(Full Bar)", "rect": None},
]
continue_button_text = "Continue Game"
continue_button_rect = None

# --- Reset Game State ---
def reset_game_state():
    global player_pos, enemies, particles, pickup_particles, total_game_time_seconds
    global current_pickups_count, MAX_PICKUPS_FOR_FULL_BAR, SHOOT_COOLDOWN, movement_speed
    global game_over_active, store_active, enemy_spawn_timer, last_shot_time

    player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
    enemies.clear()
    particles.clear() # Player shots
    pickup_particles.clear() # Gold particles

    total_game_time_seconds = 0.0
    current_pickups_count = 0
    MAX_PICKUPS_FOR_FULL_BAR = INITIAL_MAX_PICKUPS_FOR_FULL_BAR
    SHOOT_COOLDOWN = INITIAL_SHOOT_COOLDOWN
    movement_speed = INITIAL_MOVEMENT_SPEED

    enemy_spawn_timer = 0.0
    last_shot_time = 0.0

    game_over_active = False
    store_active = False

# --- Draw Game Over Screen ---
def draw_game_over_screen(surface, final_time_seconds):
    # Semi-transparent overlay
    overlay_color = pygame.Color(10, 10, 20, 200) # Dark semi-transparent
    overlay_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    overlay_surface.fill(overlay_color)
    surface.blit(overlay_surface, (0, 0))

    # "GAME OVER" Text
    game_over_text_surf = game_over_font_large.render("GAME OVER", True, crimson)
    game_over_text_rect = game_over_text_surf.get_rect(center=(surface.get_width() / 2, surface.get_height() / 3))
    surface.blit(game_over_text_surf, game_over_text_rect)

    # Final Score (Time)
    minutes = int(final_time_seconds // 60)
    seconds = int(final_time_seconds % 60)
    time_str = f"Time Survived: {minutes:02}:{seconds:02}"
    score_surf = ui_font.render(time_str, True, white) # ui_font is store_font_medium
    score_rect = score_surf.get_rect(center=(surface.get_width() / 2, game_over_text_rect.bottom + 60))
    surface.blit(score_surf, score_rect)

    # Instructions
    quit_text = "Press 'Q' to Quit"
    restart_text = "Press 'R' to Restart"

    quit_surf = ui_font.render(quit_text, True, grey)
    quit_rect = quit_surf.get_rect(center=(surface.get_width() / 2, score_rect.bottom + 40))
    surface.blit(quit_surf, quit_rect)
    restart_surf = ui_font.render(restart_text, True, grey)
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
    # dt is delta time in seconds since last frame, used for framerate-independent physics.
    dt = clock.tick(60) / 1000

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_over_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    reset_game_state()
        elif store_active: # Store is active, and game is not over
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Left mouse button
                mouse_pos = pygame.mouse.get_pos()
                for item in store_items:
                    if item["rect"] and item["rect"].collidepoint(mouse_pos):
                        # Apply upgrade
                        if item["id"] == "faster_shots":
                            SHOOT_COOLDOWN = max(0.05, SHOOT_COOLDOWN * 0.85) 
                            print(f"Faster Shots purchased! New cooldown: {SHOOT_COOLDOWN:.2f}")
                        elif item["id"] == "player_speed":
                            movement_speed = int(movement_speed * 1.15)
                            print(f"Player Speed+ purchased! New speed: {movement_speed:.0f}")

                        # Increase the requirement for the next bar fill
                        MAX_PICKUPS_FOR_FULL_BAR = int(MAX_PICKUPS_FOR_FULL_BAR * 1.2 + 1)
                        print(f"Next upgrade will require {MAX_PICKUPS_FOR_FULL_BAR} pickups.")

                        store_active = False
                        current_pickups_count = 0 # Reset bar
                        break 
                # If no item was purchased (due to break), check continue button
                if store_active and continue_button_rect and continue_button_rect.collidepoint(mouse_pos):
                    store_active = False
                    current_pickups_count = 0 # Reset bar
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                store_active = False
                current_pickups_count = 0 # Reset bar when escaping store
        else: # Gameplay is active (not game over, not store)
            # Handle other gameplay-specific events if any (currently none besides quit handled globally)
            pass

    # --- Game State Updates ---
    # Background color transition (always active, even on game over screen for effect)
    bg_color_transition_progress += BG_COLOR_TRANSITION_SPEED * dt
    if bg_color_transition_progress >= 1.0:
        bg_color_transition_progress = 0.0 # Reset progress
        current_bg_color_index = next_bg_color_index
        next_bg_color_index = (next_bg_color_index + 1) % len(BG_CYCLE_COLORS)

    # Interpolate between the current and next background color
    color1 = BG_CYCLE_COLORS[current_bg_color_index]
    color2 = BG_CYCLE_COLORS[next_bg_color_index]
    dynamic_bg_color = color1.lerp(color2, bg_color_transition_progress)

    if not game_over_active:
        if not store_active:
            # --- Active Gameplay Logic ---
            total_game_time_seconds += dt # Increment game timer

            # Player Movement
            move_vector = pygame.Vector2(0, 0)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                move_vector.y -= 1
            if keys[pygame.K_s]:
                move_vector.y += 1
            if keys[pygame.K_a]:
                move_vector.x -= 1
            if keys[pygame.K_d]:
                move_vector.x += 1
            if move_vector.length_squared() > 0:
                move_vector.normalize_ip()
                player_pos += move_vector * movement_speed * dt

            # Shooting Logic
            current_time = pygame.time.get_ticks() / 1000.0
            if keys[pygame.K_SPACE] and (current_time - last_shot_time > SHOOT_COOLDOWN) and enemies:
                last_shot_time = current_time
                nearest_enemy = min(enemies, key=lambda e: (e.pos - player_pos).length_squared())
                if nearest_enemy: # Should always be true if enemies list is not empty
                    particles.append(Particle(player_pos, nearest_enemy.pos, color=light_sky_blue))

            # Enemy Spawning
            enemy_spawn_timer += dt
            if enemy_spawn_timer >= ENEMY_SPAWN_INTERVAL and len(enemies) < MAX_ENEMIES:
                enemy_spawn_timer = 0.0
                if random.random() < 0.6: # Spawn Triangle
                    enemies.append(EnemyTriangle(screen.get_width(), screen.get_height()))
                else: # Spawn Square Group
                    num_squares = random.randint(SQUARE_GROUP_SIZE_MIN, SQUARE_GROUP_SIZE_MAX)
                    edge = random.choice(["top", "bottom", "left", "right"])
                    margin = 30
                    screen_w, screen_h = screen.get_width(), screen.get_height()
                    if edge == "top": cx, cy = random.uniform(margin*2, screen_w-margin*2), -margin
                    elif edge == "bottom": cx, cy = random.uniform(margin*2, screen_w-margin*2), screen_h + margin
                    elif edge == "left": cx, cy = -margin, random.uniform(margin*2, screen_h-margin*2)
                    else: cx, cy = screen_w + margin, random.uniform(margin*2, screen_h-margin*2)
                    for _ in range(num_squares):
                        if len(enemies) < MAX_ENEMIES:
                            offset_pos = pygame.Vector2(cx + random.uniform(-25, 25), cy + random.uniform(-25, 25))
                            enemies.append(SquareEnemy(offset_pos, screen_w, screen_h))
            
            # Update Projectiles (Player Shots)
            for particle in particles[:]:
                particle.update(dt)
                if particle.is_offscreen(screen.get_width(), screen.get_height()):
                    particles.remove(particle)

            # Enemy Update
            for enemy in enemies: # No need to copy if not removing during iteration here
                enemy.update(player_pos, dt)

            # Collision: Projectile vs Enemy
            for particle in particles[:]:
                for enemy in enemies[:]: # Copy for safe removal
                    enemy_col_radius = enemy.height * 0.5 if isinstance(enemy, EnemyTriangle) else enemy.size * 0.707
                    if (particle.pos - enemy.pos).length_squared() < (particle.radius + enemy_col_radius)**2:
                        if particle in particles: particles.remove(particle) # Check if still exists
                        destroyed = enemy.take_damage() if isinstance(enemy, SquareEnemy) else True
                        if destroyed:
                            pickup_particles.append(PickupParticle(enemy.pos, color=gold, radius=7))
                            if enemy in enemies: enemies.remove(enemy) # Check if still exists
                        break # Particle can only hit one enemy

            # Collision: Player vs Pickup Particle
            pickups_to_keep = []
            for pickup in pickup_particles:
                if (player_pos - pickup.pos).length_squared() < (player_radius + pickup.radius)**2:
                    if current_pickups_count < MAX_PICKUPS_FOR_FULL_BAR:
                        current_pickups_count += 1
                    if current_pickups_count >= MAX_PICKUPS_FOR_FULL_BAR and not store_active: # Check store_active again
                        store_active = True
                        current_pickups_count = MAX_PICKUPS_FOR_FULL_BAR # Cap it
                else:
                    pickups_to_keep.append(pickup)
            pickup_particles = pickups_to_keep

            # Player Boundary Checks
            player_pos.x = max(player_radius, min(player_pos.x, screen.get_width() - player_radius))
            player_pos.y = max(player_radius, min(player_pos.y, screen.get_height() - player_radius))

            # --- Collision Detection (Player vs Enemy) ---
            for enemy in enemies: # Iterate without copying if just checking
                enemy_hitbox_radius_for_player = 0
                if isinstance(enemy, EnemyTriangle):
                    # For triangle, pos is the tip. A smaller radius from the tip for player collision.
                    enemy_hitbox_radius_for_player = enemy.height * 0.4 
                elif isinstance(enemy, SquareEnemy):
                    # For square, pos is the center. Radius is approx half diagonal.
                    enemy_hitbox_radius_for_player = enemy.size * 0.5 # Changed to 0.5 instead of 0.7
                
                if (player_pos - enemy.pos).length_squared() < (player_radius + enemy_hitbox_radius_for_player)**2:
                    game_over_active = True
                    store_active = False # Ensure store doesn't open if game over happens simultaneously
                    print(f"GAME OVER: Player collided with {type(enemy).__name__} at {enemy.pos}")
                    # Optional: Clear dynamic elements for a cleaner game over screen
                    # enemies.clear()
                    # particles.clear() 
                    # pickup_particles.clear()
                    break # One collision is enough to end the game
        # else: store is active, most gameplay logic is paused
    # else: game is over, all gameplay logic is paused

    # --- Drawing ---
    screen.fill(dynamic_bg_color) # Always fill screen with current background

    if game_over_active:
        draw_game_over_screen(screen, total_game_time_seconds)
    else: # Game is not over
        # Draw pickup particles (gold)
        for pickup in pickup_particles:
            pickup.draw(screen)
        
        # Draw player projectiles (shots) - only if not in store
        if not store_active:
            for particle in particles: # Player shots
                particle.draw(screen)

        # Draw enemies - only if not in store
        if not store_active:
            for enemy in enemies:
                if isinstance(enemy, EnemyTriangle):
                    enemy.draw(screen, player_pos) 
                else: # SquareEnemy
                    enemy.draw(screen)
        
        # Draw player
        pygame.draw.circle(screen, crimson, player_pos, player_radius)

        # Draw UI Bar for pickups
        pygame.draw.rect(screen, BAR_BG_COLOR, (BAR_X, BAR_Y, BAR_MAX_WIDTH, BAR_HEIGHT))
        fill_ratio = min(current_pickups_count / MAX_PICKUPS_FOR_FULL_BAR, 1.0) if MAX_PICKUPS_FOR_FULL_BAR > 0 else 0
        actual_fill_width = fill_ratio * BAR_MAX_WIDTH
        pygame.draw.rect(screen, BAR_FILL_COLOR, (BAR_X, BAR_Y, actual_fill_width, BAR_HEIGHT))

        # Draw Game Timer (top right)
        minutes = int(total_game_time_seconds // 60)
        seconds = int(total_game_time_seconds % 60)
        timer_text = f"{minutes:02}:{seconds:02}"
        timer_surf = ui_font.render(timer_text, True, white)
        timer_rect = timer_surf.get_rect(topright=(screen.get_width() - 20, 20))
        screen.blit(timer_surf, timer_rect)

        if store_active: # Draw store on top if active (and game not over)
            draw_store_window(screen)

    # flip() the display to put your work on screen
    pygame.display.flip()

pygame.display.quit() # Explicitly quit display before pygame.quit()
pygame.quit()
sys.exit()
import pygame

pygame.init()

clock = pygame.time.Clock()
FPS = 60

# --- create game window ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Background Text Example")

# --- game variables ---
scroll = 0

# --- load images ---
ground_image = pygame.image.load("graphics/ground.png").convert_alpha()
ground_width = ground_image.get_width()
ground_height = ground_image.get_height()

bg_images = []
for i in range(1, 6):
    bg_image = pygame.image.load(f"graphics/layer{i}.png").convert_alpha()
    bg_images.append(bg_image)
bg_width = bg_images[0].get_width()


def draw_bg():
    for x in range(5):
        speed = 1
        for i in bg_images:
            screen.blit(i, ((x * bg_width) - scroll * speed, 0))    
            speed += 0.2
            # Adjust speed for each layer

def draw_ground():
    for x in range(15):
        screen.blit(ground_image, ((x * ground_width) - scroll * 2.2, SCREEN_HEIGHT - ground_height))

# --- game loop ---
run = True

while run:
    clock.tick(FPS)

# --- draw background ---
    draw_bg()
    draw_ground()

# --- get keyboard input ---
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a] and scroll > 0:
        scroll -= 5
    if keys[pygame.K_d] and scroll < 5000:
        scroll += 5

# --- event handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()

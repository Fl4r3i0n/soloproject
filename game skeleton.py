import sys
import pygame

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Target Game - Security Testbed")
clock = pygame.time.Clock()pip install pygame

# Core State Variables (These are your targets for memory tampering!)
player_health = 100
player_score = 0

# Player properties
player_pos = [400, 300]
player_speed = 5

font = pygame.font.SysFont("Arial", 24)

# Main Game Loop
running = True
while running:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False

  # Handle movement controls (Arrow keys or WASD)
  keys = pygame.key.get_pressed()
  if keys[pygame.K_LEFT] or keys[pygame.K_a]:
    player_pos[0] -= player_speed
  if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
    player_pos[0] += player_speed
  if keys[pygame.K_UP] or keys[pygame.K_w]:
    player_pos[1] -= player_speed
  if keys[pygame.K_DOWN] or keys[pygame.K_s]:
    player_pos[1] += player_speed

  # Clear screen (dark grey background)
  screen.fill((30, 30, 30))

  # Draw Player (Blue square)
  pygame.draw.rect(
      screen, (0, 128, 255), (player_pos[0], player_pos[1], 40, 40)
  )

  # Render Health and Score HUD
  health_text = font.render(
      f"Health: {player_health}", True, (255, 255, 255)
  )
  score_text = font.render(f"Score: {player_score}", True, (255, 255, 255))
  screen.blit(health_text, (20, 20))
  screen.blit(score_text, (20, 50))

  pygame.display.flip()
  clock.tick(60)

pygame.quit()
sys.exit()
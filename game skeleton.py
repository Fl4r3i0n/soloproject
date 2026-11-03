import random
import sys
import pygame

# Initialize Pygame
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Target Game - Security Testbed")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 24)
game_over_font = pygame.font.SysFont("Arial", 48)

def reset_game():
  global player_health, player_score, player_pos, enemy_pos, damage_cooldown, is_game_over
  player_health = 100
  player_score = 0
  player_pos = [400, 350]
  enemy_pos = [random.randint(100, 700), random.randint(150, 500)]
  damage_cooldown = 0
  is_game_over = False

# Start game with variables
reset_game()
player_speed = 5
enemy_speed = 2
player_size = 40
enemy_size = 30
border_thickness = 10
arena_top = 120 # keeps playable area below the hud

# Main Game Loop
running = True
while running:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False
    if event.type ==pygame.KEYDOWN:
      if event.key == pygame.K_r and is_game_over:
        reset_game()

  # Handle movement controls (Arrow keys or WASD) and checks if the game is over AND border collision
  if not is_game_over:

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
      player_pos[0] = max(
          border_thickness, player_pos[0] - player_speed
      )  # Left border
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
      player_pos[0] = min(
          SCREEN_WIDTH - player_size - border_thickness,
          player_pos[0] + player_speed,
      )  # Right border
    if keys[pygame.K_UP] or keys[pygame.K_w]:
      player_pos[1] = max(
          arena_top + border_thickness, player_pos[1] - player_speed
      )  # Top border (leaves room for HUD)
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
      player_pos[1] = min(
          SCREEN_HEIGHT - player_size - border_thickness,
          player_pos[1] + player_speed,
      )  # Bottom border

  # Enemy movement (moves slowly towards the player)
  if enemy_pos[0] < player_pos[0]:
    enemy_pos[0] += enemy_speed
  elif enemy_pos[0] > player_pos[0]:
    enemy_pos[0] -= enemy_speed

  if enemy_pos[1] < player_pos[1]:
    enemy_pos[1] += enemy_speed
  elif enemy_pos[1] > player_pos[1]:
    enemy_pos[1] -= enemy_speed

  #Keeps things withinn the arena
  enemy_pos[0] = max(border_thickness, min(SCREEN_WIDTH - enemy_size - border_thickness, enemy_pos[0]))
  enemy_pos[1] = max(arena_top + border_thickness, min(SCREEN_HEIGHT - enemy_size - border_thickness, enemy_pos[1]))


  # Check for collision between player and enemy (player 40x40, enemy 30x30)
  player_rect = pygame.Rect(player_pos[0], player_pos[1], player_size, player_size)
  enemy_rect = pygame.Rect(enemy_pos[0], enemy_pos[1], enemy_size, enemy_size)

  if player_rect.colliderect(enemy_rect):
    player_health = max(0, player_health -1) # Drains health on contact
    damage_cooldown = 180 # 3 second cooldown at 60 fps (no score gain during this time)

  #Manage score and damage cooldown
  if damage_cooldown > 0:
    damage_cooldown -= 1
  else:
    player_score += 1 # score increases when safe

  # Check for game over
  if player_health <= 0:
    is_game_over = True

  # Clear screen (dark grey background)
  screen.fill((30, 30, 30))

  #Draw Borders
  border_color = (200, 200, 200)
  #top border
  pygame.draw.rect(
    screen, 
    border_color, 
    (0, arena_top, SCREEN_WIDTH, border_thickness),
  )
  # left border
  pygame.draw.rect(
    screen, 
    border_color, 
    (0, arena_top, border_thickness, SCREEN_HEIGHT - arena_top - border_thickness),
  )
  # right border
  pygame.draw.rect(
    screen, 
    border_color, 
    (SCREEN_WIDTH - border_thickness, arena_top, border_thickness, SCREEN_HEIGHT - arena_top - border_thickness),
  )
  # bottom border
  pygame.draw.rect(
    screen,
    border_color, 
    (0, SCREEN_HEIGHT - border_thickness, SCREEN_WIDTH, border_thickness),
  )



  # Draw Player (Blue square)
  pygame.draw.rect(
      screen, (0, 128, 255), (player_pos[0], player_pos[1], player_size, player_size)
  )

  #Draw Enemy (Red square)
  pygame.draw.rect(
      screen, (255, 69, 0), (enemy_pos[0], enemy_pos[1], enemy_size, enemy_size)
  )
  
  # Render Health and Score HUD
  health_text = font.render(
      f"Health: {player_health}", True, (255, 255, 255)
  )
  score_text = font.render(f"Score: {player_score}", True, (255, 255, 255))
  screen.blit(health_text, (20, 20))
  screen.blit(score_text, (20, 50))

  # Display Game over message
  if is_game_over:
    game_over_surf = game_over_font.render(
      "Game Over", True, (255, 0, 0)
      )
    restart_surf = font.render(
      "Press 'R' to Restart", True, (255, 255, 255)
      )
    screen.blit(game_over_surf, (300, 240))
    screen.blit(restart_surf, (320, 300))

  pygame.display.flip()
  clock.tick(60)

pygame.quit()
sys.exit()
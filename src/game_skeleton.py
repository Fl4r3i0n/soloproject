import random
import sys
import pygame
import math

# Initialize Pygame
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Target Game - Security Testbed")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 24)
game_over_font = pygame.font.SysFont("Arial", 48)

def reset_game():
  global player_health, player_score, player_pos, enemies, damage_cooldown, is_game_over, score_timer
  global ammo_count, ammo_box_pos, projectiles, combo_multiplier, combo_timer
  global active_powerup, powerup_timer, powerup_spawn_timer, powerup_pos, powerup_type
  global difficulty_timer, global_enemy_speed, pending_enemy_respawns

  player_health = 100
  player_score = 0
  score_timer = 0
  player_pos = [400, 350]

  global_enemy_speed = 2
  enemies = [[random.randint(100, 700), random.randint(150, 500)]]
  pending_enemy_respawns = []

  damage_cooldown = 0
  is_game_over = False

  ammo_count = 0
  ammo_box_pos = [random.randint(50, 750), random.randint(150, 550)]
  projectiles = []
  combo_multiplier = 1
  combo_timer = 0

  active_powerup = None
  powerup_timer = 0
  powerup_spawn_timer = 0
  powerup_pos = [random.randint(50, 750), random.randint(150, 550)]
  powerup_type = None

  difficulty_timer = 0

# Start game with variables
reset_game()
base_player_speed = 5
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
      elif event.key == pygame.K_SPACE and not is_game_over and ammo_count > 0:
        ammo_count -= 1
        if enemies:
          target_enemy = enemies[0]
          dx = target_enemy[0] - player_pos[0]
          dy = target_enemy[1] - player_pos[1]
          dist = math.hypot(dx, dy)
          if dist > 0:
            dx, dy = dx / dist, dy / dist
          else:
            dx, dy = 1, 0
          projectiles.append([player_pos[0] + 15, player_pos[1] + 15, dx * 8, dy * 8])

  # Only updates game state if not game over
  if not is_game_over:
    current_player_speed = (
        base_player_speed + 2 if active_powerup == "speed" else base_player_speed
    )

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
      player_pos[0] = max(
          border_thickness, player_pos[0] - current_player_speed
      )
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
      player_pos[0] = min(
          SCREEN_WIDTH - player_size - border_thickness,
          player_pos[0] + current_player_speed,
      )
    if keys[pygame.K_UP] or keys[pygame.K_w]:
      player_pos[1] = max(
          arena_top + border_thickness, player_pos[1] - current_player_speed
      )
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
      player_pos[1] = min(
          SCREEN_HEIGHT - player_size - border_thickness,
          player_pos[1] + current_player_speed,
      )

    # Difficulty scaling
    difficulty_timer += 1
    if difficulty_timer % 900 == 15:
      if global_enemy_speed < base_player_speed * 2:
        global_enemy_speed = round(global_enemy_speed + 0.2, 1)
    if difficulty_timer % 1800 == 30:
      if len(enemies) + len(pending_enemy_respawns) < 5:
        enemies.append([random.randint(100, 700), random.randint(150, 500)])

    # Enemy respawn management
    for respawn in pending_enemy_respawns[:]:
      respawn['timer'] -= 1
      if respawn['timer'] <= 0:
        enemies.append([random.randint(100, 700), random.randint(150, 500)])
        pending_enemy_respawns.remove(respawn)

    # Enemy movement and arena clamping
    for enemy in enemies:
      if enemy[0] < player_pos[0]:
        enemy[0] += global_enemy_speed
      elif enemy[0] > player_pos[0]:
        enemy[0] -= global_enemy_speed

      if enemy[1] < player_pos[1]:
        enemy[1] += global_enemy_speed
      elif enemy[1] > player_pos[1]:
        enemy[1] -= global_enemy_speed

      enemy[0] = max(
          border_thickness,
          min(SCREEN_WIDTH - enemy_size - border_thickness, enemy[0]),
      )
      enemy[1] = max(
          arena_top + border_thickness,
          min(SCREEN_HEIGHT - enemy_size - border_thickness, enemy[1]),
      )

    # Projectiles and collisions
    for proj in projectiles[:]:
      proj[0] += proj[2]
      proj[1] += proj[3]
      proj_rect = pygame.Rect(proj[0], proj[1], 10, 10)
      hit_enemy = None
      for enemy in enemies:
        enemy_rect = pygame.Rect(enemy[0], enemy[1], enemy_size, enemy_size)
        if proj_rect.colliderect(enemy_rect):
          hit_enemy = enemy
          break
      if hit_enemy:
        projectiles.remove(proj)
        enemies.remove(hit_enemy)
        pending_enemy_respawns.append({'timer': 300})

    player_rect = pygame.Rect(
        player_pos[0], player_pos[1], player_size, player_size
    )

    collided_with_enemy = False
    for enemy in enemies:
      enemy_rect = pygame.Rect(enemy[0], enemy[1], enemy_size, enemy_size)
      if player_rect.colliderect(enemy_rect):
        collided_with_enemy = True
        break

    if collided_with_enemy:
      if active_powerup != 'invincible':
        player_health = max(0, player_health - 1)
        damage_cooldown = 180

    # Collision with ammo box
    if ammo_count < 5:
      ammo_rect = pygame.Rect(ammo_box_pos[0], ammo_box_pos[1], 20, 20)
      if player_rect.colliderect(ammo_rect):
        ammo_count = min(5, ammo_count + 5)
        ammo_box_pos = [random.randint(50, 750), random.randint(150, 550)]

    # Random powerup spawn and collection logic
    if powerup_type is None:
      powerup_spawn_timer += 1
      if powerup_spawn_timer >= 600:
        powerup_type = random.choice(
            ['life', 'ammo', 'multiplier', 'speed', 'invincible']
        )
        powerup_pos = [random.randint(50, 750), random.randint(150, 550)]
        powerup_spawn_timer = 0
    else:
      powerup_rect = pygame.Rect(powerup_pos[0], powerup_pos[1], 25, 25)
      if player_rect.colliderect(powerup_rect):
        if powerup_type == 'life':
          player_health = min(100, player_health + 20)
        elif powerup_type == 'ammo':
          ammo_count = min(5, ammo_count + 5)
        elif powerup_type == 'multiplier':
          combo_multiplier = min(5, combo_multiplier + 1)
        elif powerup_type == 'speed':
          active_powerup = 'speed'
          powerup_timer = 480
        elif powerup_type == 'invincible':
          active_powerup = 'invincible'
          powerup_timer = 300
        powerup_type = None  # Aligned to clear item regardless of type

    if active_powerup:
      powerup_timer -= 1
      if powerup_timer <= 0:
        active_powerup = None

    # Score progression
    if damage_cooldown > 0:
      damage_cooldown -= 1
    else:
      score_timer += 1
      if score_timer >= 60:
        player_score += 1 * combo_multiplier
        score_timer = 0

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

  # Draw Ammo Box
  if ammo_count < 5:
    pygame.draw.rect(
      screen, (0, 255, 128), pygame.Rect(ammo_box_pos[0], ammo_box_pos[1], 20, 20)
  )

  # Draw Random Powerup
  if powerup_type:
    pygame.draw.rect(
      screen, (255, 255, 0), pygame.Rect(powerup_pos[0], powerup_pos[1], 25, 25)
    )
    p_text = font.render(powerup_type[0].upper(), True, (255, 255, 255))
    screen.blit(p_text, (powerup_pos[0] + 5, powerup_pos[1] + 2))

  # Draw Projectiles
  for proj in projectiles:
    pygame.draw.circle(screen, (255, 255, 0), (int(proj[0]), int(proj[1])), 5)

  # Change player color based on active powerup
  player_color = (0, 128, 255)  # Default blue
  if active_powerup == 'invincible':
    player_color = (255, 255, 255) # White for invincible
  elif active_powerup == 'speed':
    player_color = (0, 255, 255) # Cyan for speed
  elif active_powerup == 'multiplier':
    player_color = (255, 215, 0) # Gold for multiplier


  # Draw Player (Blue square)
  pygame.draw.rect(
      screen, 
      player_color, 
      pygame.Rect(player_pos[0], player_pos[1], player_size, player_size)
  )

  #Draw Enemies (Red square)
  for enemy in enemies:
    pygame.draw.rect(
      screen, 
      (255, 69, 0), 
      pygame.Rect(enemy[0], enemy[1], enemy_size, enemy_size)
  )
  
  # Render Health and Score HUD
  health_text = font.render(
      f"Health: {player_health}", True, (255, 255, 255)
  )

  score_text = font.render(
    f"Score: {player_score}, (x{combo_multiplier})",True, 
    (255, 255, 255),
    )
  
  ammo_text = font.render(f"Ammo: {ammo_count}/5", True, (0, 255, 128))
  enemies_text = font.render(
    f"Enemies: {len(enemies)} (Spd: {global_enemy_speed})", True, (255, 100, 100)
  )


  screen.blit(health_text, (20, 10))
  screen.blit(score_text, (20, 35))
  screen.blit(ammo_text, (20, 60))
  screen.blit(enemies_text, (20, 85))

  if active_powerup:
    timer_secs = round(powerup_timer / 60, 1)
    powerup_hud = font.render(
      f"ACTIVE [{active_powerup.upper()}]: {timer_secs}s", True, (255, 0, 255)
    )
    screen.blit(powerup_hud, (450, 20))

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
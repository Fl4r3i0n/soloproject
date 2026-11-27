import math
import random
import sys
import pygame

try:
    from src import config, database, integrity, mock_hacks
except ImportError:
    import config
    import database
    import integrity
    import mock_hacks

# Initialize Pygame
pygame.init()
database.init_db()
guard = integrity.Guard(log_to_db=True)

SCREEN_WIDTH = config.SCREEN_WIDTH
SCREEN_HEIGHT = config.SCREEN_HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("ArenaSentinel - Security Testbed")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 24)
game_over_font = pygame.font.SysFont("Arial", 48)

base_player_speed = 5
player_size = 40
enemy_size = 30
border_thickness = 10
arena_top = 120

def random_arena_pos():
  return [random.randint(50, 750), random.randint(150, 550)]

def reset_game(log_session=True):
  global player_health, player_score, player_pos, enemies, damage_cooldown
  global is_game_over, score_timer, ammo_count, ammo_box_pos, projectiles
  global combo_multiplier, active_powerup, powerup_timer, powerup_spawn_timer
  global powerup_pos, powerup_type, difficulty_timer, global_enemy_speed
  global pending_enemy_respawns

  player_health = config.MAX_HEALTH
  player_score = 0
  score_timer = 0
  player_pos = [400, 350]

  global_enemy_speed = 2
  enemies = [random_arena_pos()]
  pending_enemy_respawns = []

  damage_cooldown = 0
  is_game_over = False

  ammo_count = config.MIN_AMMO
  ammo_box_pos = random_arena_pos()
  projectiles = []
  combo_multiplier = 1
  
  active_powerup = None
  powerup_timer = 0
  powerup_spawn_timer = 0
  powerup_pos = random_arena_pos()
  powerup_type = None

  difficulty_timer = 0
  
  if "guard" in globals():
    guard.reset()
  
  if log_session:
    database.log_event("SESSION_START", f"Health={player_health}, Score={player_score}")


# Start game with variables
reset_game(log_session=False)

# Main Game Loop
if __name__ == "__main__":
  database.log_event("SESSION_START", f"Health={player_health}, Score={player_score}")
  running = True
  
  while running:
    for event in pygame.event.get():
      mock_hacks.handle_event(event)
      if event.type == pygame.QUIT:
        running = False
      if event.type ==pygame.KEYDOWN:
        if event.key == pygame.K_r and is_game_over:
          reset_game()
        elif event.key == pygame.K_SPACE and not is_game_over and ammo_count > 0:
          ammo_count -= 1
          if enemies:
            dx = enemies[0][0] - player_pos[0]
            dy = enemies[0][1] - player_pos[1]
            dist = math.hypot(dx, dy)
            if dist > 0:
              dx, dy = dx / dist, dy / dist
            else:
              dx, dy = 1, 0
            projectiles.append([player_pos[0] + 15, player_pos[1] + 15, dx * 8, dy * 8])

    # Only updates game state if not game over
    if not is_game_over:
      #Player Movement
      speed = base_player_speed + 2 if active_powerup == "speed" else base_player_speed
      keys = pygame.key.get_pressed()

      if keys[pygame.K_LEFT] or keys[pygame.K_a]:
          player_pos[0] = max(border_thickness, player_pos[0] - speed)
      if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
          player_pos[0] = min(SCREEN_WIDTH - player_size - border_thickness, player_pos[0] + speed)
      if keys[pygame.K_UP] or keys[pygame.K_w]:
          player_pos[1] = max(arena_top + border_thickness, player_pos[1] - speed)
      if keys[pygame.K_DOWN] or keys[pygame.K_s]:
          player_pos[1] = min(SCREEN_HEIGHT - player_size - border_thickness, player_pos[1] + speed)


      # Difficulty scaling
      difficulty_timer += 1
      if difficulty_timer % 900 == 15 and global_enemy_speed < base_player_speed * 2:
          global_enemy_speed = round(global_enemy_speed + 0.2, 1)
      if difficulty_timer % 1800 == 30 and len(enemies) + len(pending_enemy_respawns) < 5:
          enemies.append(random_arena_pos())

      # Enemy respawn management
      for respawn in pending_enemy_respawns[:]:
        respawn['timer'] -= 1
        if respawn['timer'] <= 0:
          enemies.append(random_arena_pos())
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

        enemy[0] = max(border_thickness, min(SCREEN_WIDTH - enemy_size - border_thickness, enemy[0]))
        enemy[1] = max(arena_top + border_thickness, min(SCREEN_HEIGHT - enemy_size - border_thickness, enemy[1]))

      # Projectiles and collisions
      for proj in projectiles[:]:
                proj[0] += proj[2]
                proj[1] += proj[3]
                proj_rect = pygame.Rect(proj[0], proj[1], 10, 10)

                for enemy in enemies[:]:
                    enemy_rect = pygame.Rect(enemy[0], enemy[1], enemy_size, enemy_size)
                    if proj_rect.colliderect(enemy_rect):
                        projectiles.remove(proj)
                        enemies.remove(enemy)
                        pending_enemy_respawns.append({"timer": 300})
                        break

      # Player collisions (enemies, ammo box, powerups)
      player_rect = pygame.Rect(player_pos[0], player_pos[1], player_size, player_size)

      for enemy in enemies:
                enemy_rect = pygame.Rect(enemy[0], enemy[1], enemy_size, enemy_size)
                if player_rect.colliderect(enemy_rect):
                    if active_powerup != "invincible":
                        player_health = max(0, player_health - 1)
                        damage_cooldown = 180
                    break

      # Collision with ammo box
      if ammo_count < config.MAX_AMMO:
                ammo_rect = pygame.Rect(ammo_box_pos[0], ammo_box_pos[1], 20, 20)
                if player_rect.colliderect(ammo_rect):
                    ammo_count = min(config.MAX_AMMO, ammo_count + 5)
                    ammo_box_pos = random_arena_pos()

      # Random powerup spawn and collection logic
      if powerup_type is None:
          powerup_spawn_timer += 1
          if powerup_spawn_timer >= 600:
              powerup_type = random.choice(["life", "ammo", "multiplier", "speed", "invincible"])
              powerup_pos = random_arena_pos()
              powerup_spawn_timer = 0
      else:
        powerup_rect = pygame.Rect(powerup_pos[0], powerup_pos[1], 25, 25)
        if player_rect.colliderect(powerup_rect):
          if powerup_type == 'life':
            player_health = min(config.MAX_HEALTH, player_health + 20)
          elif powerup_type == 'ammo':
            ammo_count = min(config.MAX_AMMO, ammo_count + 5)
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
          player_score += combo_multiplier
          score_timer = 0

      if player_health <= config.MIN_HEALTH and not is_game_over:
        is_game_over = True
        database.log_event("GAME_OVER", f"FinalScore={player_score}")

    screen.fill((30, 30, 30))
    border_color = (200, 200, 200)
    pygame.draw.rect(screen, border_color, (0, arena_top, SCREEN_WIDTH, border_thickness))
    pygame.draw.rect(screen, border_color, (0, arena_top, border_thickness, SCREEN_HEIGHT - arena_top - border_thickness))
    pygame.draw.rect(screen, border_color, (SCREEN_WIDTH - border_thickness, arena_top, border_thickness, SCREEN_HEIGHT - arena_top - border_thickness))
    pygame.draw.rect(screen, border_color, (0, SCREEN_HEIGHT - border_thickness, SCREEN_WIDTH, border_thickness))

    # Draw Ammo Box
    if ammo_count < config.MAX_AMMO:
      pygame.draw.rect(screen, (0, 255, 128), pygame.Rect(ammo_box_pos[0], ammo_box_pos[1], 20, 20))

    # Draw Random Powerup
    if powerup_type:
        pygame.draw.rect(screen, (255, 255, 0), (powerup_pos[0], powerup_pos[1], 25, 25))
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

    #Draws the player
    pygame.draw.rect(screen, player_color, (player_pos[0], player_pos[1], player_size, player_size))

    #Draw Enemies (Red square)
    for enemy in enemies:
        pygame.draw.rect(screen, (255, 69, 0), (enemy[0], enemy[1], enemy_size, enemy_size))
    
    screen.blit(font.render(f"Health: {player_health}", True, (255, 255, 255)), (20, 10))
    screen.blit(font.render(f"Score: {player_score} (x{combo_multiplier})", True, (255, 255, 255)), (20, 35))
    screen.blit(font.render(f"Ammo: {ammo_count}/{config.MAX_AMMO}", True, (0, 255, 128)), (20, 60))
    screen.blit(font.render(f"Enemies: {len(enemies)} (Spd: {global_enemy_speed})", True, (255, 100, 100)), (20, 85))

    if active_powerup:
        timer_secs = round(powerup_timer / 60, 1)
        screen.blit(font.render(f"ACTIVE [{active_powerup.upper()}]: {timer_secs}s", True, (255, 0, 255)), (450, 20))

    if is_game_over:
        screen.blit(game_over_font.render("Game Over", True, (255, 0, 0)), (300, 240))
        screen.blit(font.render("Press 'R' to Restart", True, (255, 255, 255)), (320, 300))

   # Apply simulated cheats and run integrity checks
    mock_hacks.apply(globals())
    guard.check(globals())

    pygame.display.flip()
    clock.tick(config.FPS)

  pygame.quit()
  sys.exit()

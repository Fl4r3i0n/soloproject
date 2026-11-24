import sqlite3
import pygame
from src import config, database, integrity, mock_hacks
import src.game_skeleton as game

def _make_clean_state():
    """Helper returning a valid, baseline game state dictionary for Guard checks."""
    return{
        "is_game_over": False,
        "player_pos": [400, 350],
        "player_health": 100,
        "ammo_count": 0,
        "ammo_box_pos": [200, 200],
        "combo_multiplier": 1,
        "powerup_timer": 0,
        "base_player_speed": 5,
        "global_enemy_speed": 2,
        "enemies": [[150, 200]],
        "pending_enemy_respawns": [],
        "player_score": 0,
        "powerup_type": None,
        "active_powerup": None,
    }

# Unit tests (Game state initialization & Boundaries)
def test_unit_reset_game_defaults():
    #checks if everything loads correctly
    game.reset_game(log_session=False)
    assert game.player_health == 100
    assert game.player_score == 0
    assert game.ammo_count == 0
    assert game.combo_multiplier == 1
    assert game.is_game_over is False
    assert len(game.enemies) == 1

def test_unit_spawn_coordinates_within_arena():
    game.reset_game()
    # checks if player spawns in right area
    assert game.player_pos == [400, 350]
    # check if the first enemy spawns in the right bounds
    enemy_x, enemy_y = game.enemies[0]
    assert 100 <= enemy_x <= 700
    assert 150 <= enemy_y <= 500

def test_unit_config_limits():
    assert config.MIN_HEALTH == 0
    assert config.MAX_HEALTH == 100
    assert config.MIN_AMMO == 0
    assert config.MAX_AMMO == 5
    
def test_unit_guard_clean_baseline():
    guard = integrity.Guard(log_to_db=False)
    state = _make_clean_state()
    
    # Simulate 120 frames (2 seconds) of normal movement and score gain
    for frame in range(120):
        state["player_pos"][0] = 400 + (frame % 5)
        if frame == 60:
            state["player_score"] = 1
        guard.check(state)
    
    assert len(guard.flags) == 0

def test_unit_guard_individual_rules():
    guard = integrity.Guard(log_to_db=False)
    base = _make_clean_state()
    guard.check(base) # Establish initial prev frame
    
    # Speed constant & movement delta violation
    tampered = _make_clean_state()
    tampered["base_player_speed"] = 15
    tampered["player_pos"] = [450, 350]
    guard.check(tampered)
    assert "SPEED_CONST" in guard.flags
    assert "TELEPORT_OR_SPEED" in guard.flags
    
    # Out-of-bounds position & impossible score jump
    tampered["player_pos"] = [5, 5]
    tampered["player_score"] = 1000
    guard.check(tampered)
    assert "OUT_OF_BOUNDS" in guard.flags
    assert "SCORE_IMPOSSIBLE" in guard.flags
    
    # Enemy wipe & enemy freeze
    tampered["enemies"] = []
    tampered["global_enemy_speed"] = 0
    guard.check(tampered)
    assert "NO_ENEMIES" in guard.flags
    assert "ENEMY_SPEED" in guard.flags
    
    # Unearned multiplier jump & powerup timer abuse
    tampered["combo_multiplier"] = 5
    tampered["powerup_timer"] = 9999
    guard.check(tampered)
    assert "MULTIPLIER_UNEARNED" in guard.flags
    assert "POWERUP_TIMER" in guard.flags

# Integration tests (Game State + SQLite Database Logging)
def test_integration_game_session_database_logging(tmp_path):
    test_db = tmp_path / "test_game_session.db"
    database.DB_NAME = str(test_db)
    database.init_db()
    
    game.reset_game()
    database.log_event("SESSION_START", f"Health={game.player_health}, Score={game.player_score}")
    
    # simulate gaining score and losing
    game.player_score = 45
    game.player_health = 0
    game.is_game_over = True
    database.log_event("GAME_OVER", f"FinalScore={game.player_score}, GameOver={game.is_game_over}")
    
    conn = sqlite3.connect(str(test_db))
    rows = conn.execute("SELECT event_type, details FROM game_logs").fetchall()
    conn.close()
    
    assert len(rows) == 2
    assert rows[0][0] == "SESSION_START"
    assert "Health=100" in rows [0][1]
    assert rows[1][0] == "GAME_OVER"
    assert "FinalScore=45" in rows [1][1]
    
# End-To-End tests (Lifecycle & Reset)
def test_e2e_full_game_frame_and_restart_cycle(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    
    pygame.init()
    screen = pygame.display.set_mode((game.SCREEN_WIDTH, game.SCREEN_HEIGHT))
    game.reset_game()
    
    #simulates taking damage and game over
    game.player_health = 0
    if game.player_health <= 0:
        game.is_game_over = True
    assert game.is_game_over is True
    
    #simulates when "R" is pressed restarting the game
    game.reset_game()
    assert game.is_game_over is False
    assert game.player_health == 100
    
    screen.fill((30, 30, 30))
    pygame.display.flip()
    pygame.quit()
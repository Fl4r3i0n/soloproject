import os
import sqlite3
import pygame
from src import config, database
import src.game_skeleton as game

# Unit tests (Game state initialization & Boundaries)
def test_unit_reset_game_defaults():
    game.reset_game()
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
    assert config.MAX_AMMO == 5

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
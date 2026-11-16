import os
import sqlite3
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
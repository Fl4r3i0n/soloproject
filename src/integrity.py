try:
    from src import config, database
except ImportError:
    import config
    import database
class Guard:
    def __init__(self, log_to_db=True):
        self.log_to_db = log_to_db
        if self.log_to_db:
            database.init_db()
        self.reset()
        
    def reset(self):
        self.prev = None
        self.ticks = 0
        self.flags = set()
    
    def flag(self, code, msg):
        if code not in self.flags:
            self.flags.add(code)
            print(f"[DETECTED] {code}: {msg}")
            if self.log_to_db:
                database.log_event(f"CHEAT_{code}", str(msg))
    
    def check(self, g):
        if g["is_game_over"]:
            return
        self.ticks += 1
        p = self.prev
        x, y = g["player_pos"]
        
        # Value bounds
        if not config.MIN_HEALTH <= g["player_health"] <= config.MAX_HEALTH:
            self.flag("HEALTH_RANGE", g["player_health"])
        if not config.MIN_AMMO <= g["ammo_count"] <= config.MAX_AMMO:
            self.flag("AMMO_RANGE", g["ammo_count"])
        if not 1 <= g["combo_multiplier"] <= 5:
            self.flag("MULTIPLIER_RANGE", g["combo_multiplier"])
        if g["powerup_timer"] > 480:
            self.flag("POWERUP_TIMER", g["powerup_timer"])
        if g["base_player_speed"] != 5:
            self.flag("SPEED_CONST", g["base_player_speed"])
        if not 2 <= g["global_enemy_speed"] <= 10:
            self.flag("ENEMY_SPEED", g["global_enemy_speed"])
        if len(g["enemies"]) + len(g["pending_enemy_respawns"]) < 1:
            self.flag("NO_ENEMIES", "enemy set emptied")
        
        # Score can never exceed the maximum earnable by time alive
        max_score = (self.ticks // 60 + 1) * 5
        if g["player_score"] > max_score:
            self.flag("SCORE_IMPOSSIBLE", f"{g['player_score']} > {max_score}")
            
        # Position bounds
        if not (10 <= x <= 750 and 130 <= y <= 550):
            self.flag("OUT_OF_BOUNDS", (x, y))
        
        if p:
            # Teleport / speed: per-frame movement limit (max 7 per axis)
            if abs(x - p["x"]) > 7 or abs(y - p["y"]) > 7:
                self.flag("TELEPORT_OR_SPEED", (x - p["x"], y - p["y"]))
            # Health may only rise via a life pickup
            picked_life = p["powerup_type"] == "life" and g["powerup_type"] is None
            if g["player_health"] > p["health"] and not picked_life:
                self.flag("HEALTH_UNEARNED", "rose without pickup")
            # Ammo may only rise via ammo box or ammo powerup pickup
            picked_ammo_box = g["ammo_box_pos"] != p["ammo_box_pos"]
            picked_ammo_powerup = p["powerup_type"] == "ammo" and g["powerup_type"] is None
            if g["ammo_count"] > p["ammo"] and not (picked_ammo_box or picked_ammo_powerup):
                self.flag("AMMO_UNEARNED", "rose without pickup")
            # Multiplier may only rise by 1 via a multiplier pickup
            picked_mult = p["powerup_type"] == "multiplier" and g["powerup_type"] is None
            if g["combo_multiplier"] > p["multiplier"] and (
                not picked_mult or g["combo_multiplier"] - p["multiplier"] > 1
            ):
                self.flag("MULTIPLIER_UNEARNED", f"{p['multiplier']} -> {g['combo_multiplier']}")
            # Powerup may only be activated by collecting one
            if g["active_powerup"] and not p["active"] and p["powerup_type"] not in ("speed", "invincible"):
                self.flag("POWERUP_UNEARNED", g["active_powerup"])
        
        self.prev = {
            "x": x,
            "y": y,
            "health": g["player_health"],
            "ammo": g["ammo_count"],
            "ammo_box_pos": list(g["ammo_box_pos"]),
            "multiplier": g["combo_multiplier"],
            "powerup_type": g["powerup_type"],
            "active": g["active_powerup"],
        }
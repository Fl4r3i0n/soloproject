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
        x, y = g["player_pos"]
        
        # 1. Check static value limits
        if g["player_health"] < config.MIN_HEALTH or g["player_health"] > config.MAX_HEALTH:
            self.flag("HEALTH_RANGE", g["player_health"])

        if g["ammo_count"] < config.MIN_AMMO or g["ammo_count"] > config.MAX_AMMO:
            self.flag("AMMO_RANGE", g["ammo_count"])

        if g["combo_multiplier"] < 1 or g["combo_multiplier"] > 5:
            self.flag("MULTIPLIER_RANGE", g["combo_multiplier"])

        if g["powerup_timer"] > 480:
            self.flag("POWERUP_TIMER", g["powerup_timer"])

        if g["base_player_speed"] != 5:
            self.flag("SPEED_CONST", g["base_player_speed"])

        if g["global_enemy_speed"] < 2 or g["global_enemy_speed"] > 10:
            self.flag("ENEMY_SPEED", g["global_enemy_speed"])

        if len(g["enemies"]) + len(g["pending_enemy_respawns"]) < 1:
            self.flag("NO_ENEMIES", "all enemies removed")
        
        # 2. Check arena boundaries and score ceiling
        if x < 10 or x > 750 or y < 130 or y > 550:
            self.flag("OUT_OF_BOUNDS", (x, y))
            
        # Score can never exceed the maximum earnable by time alive
        max_score = (self.ticks // 60 + 1) * 5
        if g["player_score"] > max_score:
            self.flag("SCORE_IMPOSSIBLE", f"{g['player_score']} > {max_score}")
            
        # 3. Compare current frame against previous frame
        if self.prev is not None:
            dx = abs(x - self.prev["x"])
            dy = abs(y - self.prev["y"])
            if dx > 7 or dy > 7:
                self.flag("TELEPORT_OR_SPEED", (dx, dy))

            got_life = self.prev["powerup_type"] == "life" and g["powerup_type"] is None
            if g["player_health"] > self.prev["health"] and not got_life:
                self.flag("HEALTH_UNEARNED", "health increased without life pickup")

            got_ammo_box = g["ammo_box_pos"] != self.prev["ammo_box_pos"]
            got_ammo_powerup = self.prev["powerup_type"] == "ammo" and g["powerup_type"] is None
            if g["ammo_count"] > self.prev["ammo"] and not (got_ammo_box or got_ammo_powerup):
                self.flag("AMMO_UNEARNED", "ammo increased without pickup")

            got_mult = self.prev["powerup_type"] == "multiplier" and g["powerup_type"] is None
            if g["combo_multiplier"] > self.prev["multiplier"] and not got_mult:
                self.flag("MULTIPLIER_UNEARNED", "multiplier jumped without pickup")

            if g["active_powerup"] and not self.prev["active"] and self.prev["powerup_type"] not in ("speed", "invincible"):
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
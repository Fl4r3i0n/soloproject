class Guard:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.prev = None
        self.ticks = 0
        self.flags = set()
    
    def flag(self, code, msg):
        if code not in self.flags:
            self.flags.add(code)
            print(f"[DETECTED] {code}: {msg}")
    
    def check(self, g):
        if g["is_game_over"]:
            return
        self.ticks += 1
        p = self.prev
        x, y = g["player_pos"]
        
        # Value bounds
        if not 0 <= g["player_health"] <= 100:
            self.flag("HEALTH_RANGE", g["player_health"])
        if not 0 <= g["ammo_count"] <= 5:
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
            # Health should only rise due to a pickup
            picked_life = p["powerup_type"] == "life" and g["powerup_type"] is None
            if g["player_health"] > p["health"] and not picked_life:
                self.flag("HEALTH_UNEARNED", "rose without pickup")
            # Ammo only rises via pickup
            if g["ammo_count"] > p["ammo"] and p["powerup_type"] != "ammo" and p["ammo"] >= 5:
                self.flag("AMMO_UNEARNED", "rose without pickup")
            # Multiplier should only rise by 1 with a multiplier pickup
            picked_mult = p["powerup_type"] == "multiplier" and g["powerup_type"] is None
            if g["combo_multiplier"] > p["multiplier"] and (
                not picked_mult or g["combo_multiplier"] - p["multiplier"] > 1
            ):
                self.flag("MULTIPLIER_UNEARNED", f"{p['multiplier']} -> {g['combo_multiplier']}")
                # powerups only active by collecting one
                if g["active_powerup"] and not p["active"] and p["powerup_type"] not in ("speed, invincible"):
                    self.flag("POWERUP_UNEARNED", g["active_powerup"])
        
        self.prev = {
            "x": x,
            "y": y,
            "health": g["player_health"],
            "ammo": g["ammo_count"],
            "multiplier": g["combo_multiplier"],
            "powerup_type": g["powerup_type"],
            "active": g["active_powerup"],
        }
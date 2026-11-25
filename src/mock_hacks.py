import pygame

ACTIVE = set()
KEYMAP = {
    pygame.K_F1: "godmode",
    pygame.K_F2: "infinite_ammo",
    pygame.K_F3: "score_inject",
    pygame.K_F4: "speed_hack",
    pygame.K_F5: "teleport",
    pygame.K_F6: "max_multiplier",
    pygame.K_F7: "kill_enemies",
    pygame.K_F8: "freeze_enemies",
    pygame.K_F9: "powerup_timer_abuse",
}

def handle_event(event):
    if event.type == pygame.KEYDOWN and event.key in KEYMAP:
        name = KEYMAP[event.key]
        ACTIVE.symmetric_difference_update({name})
        print("[MOCK HACK]", name, "ON" if name in ACTIVE else "OFF")
        
def apply(g):
    if "godmode" in ACTIVE:
        g["player_health"] = 100
    if "infinite_ammo" in ACTIVE:
        g["ammo_count"] = 5
    if "score_inject" in ACTIVE:
        g["player_score"] += 1000
        ACTIVE.discard("score_inject")
    g["base_player_speed"] = 15 if "speed_hack" in ACTIVE else 5
    if "teleport" in ACTIVE:
        g["player_pos"][0], g["player_pos"][1] = 5, 5
        ACTIVE.discard("teleport")
    if "max_multiplier" in ACTIVE:
        g["combo_multiplier"] = 5
    if "powerup_timer_abuse" in ACTIVE:
        g["powerup_timer"] = 9999
    if "kill_enemies" in ACTIVE:
        g["enemies"].clear()
    if "freeze_enemies" in ACTIVE:
        g["global_enemy_speed"] = 0

# Launcher: runs the hacks and the game
if __name__ == "__main__":
    import os
    import runpy
    import sys
    
    import integrity
    
    here = os.path.dirname(os.path.abspath(__file__))
    game = sys.argv[1] if len(sys.argv) > 1 else "game_skeleton.py"
    game = game if os.path.isabs(game) else os.path.join(here, game)
    sys.path.insert(0, os.path.dirname(game))
    
    guard = integrity.Guard()
    state = {"hook": None, "was_over": False}
    
    real_get = pygame.event.get
    
    def patched_get(*args, **kwargs):
        events = real_get(*args, **kwargs)
        for e in events:
            handle_event(e)
        return events
    
    def make_patched(real):
        def patched(*args, **kwargs):
            # Use only the first display call seen, so we run once per frame
            if state["hook"] is None:
                state["hook"] = real
            if state["hook"] is real:
                g = sys._getframe(1).f_globals # the game's globals
                if "player_health" in g:
                    over = g.get("is_game_over", False)
                    if state["was_over"] and not over:
                        guard.reset() # game restarted
                    state["was_over"] = over
                    apply(g)
                    guard.check(g)
            return real(*args, **kwargs)
        return patched
    
    pygame.event.get = patched_get
    pygame.display.flip = make_patched(pygame.display.flip)
    pygame.display.update = make_patched(pygame.display.update)
    
    print("[MOCK HACKS] F1-F9 toggle hacks. Detections print as [DETECTED].")
    runpy.run_path(game, run_name="__main__")
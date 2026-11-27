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
        cheat = KEYMAP[event.key]
        if cheat in ACTIVE:
            ACTIVE.remove(cheat)
            print(f"[MOCK HACK] {cheat} OFF")
        else:
            ACTIVE.add(cheat)
            print(f"[MOCK HACK] {cheat} ON")
        
def apply(g):
    if "godmode" in ACTIVE:
        g["player_health"] = 100
        
    if "infinite_ammo" in ACTIVE:
        g["ammo_count"] = 5
        
    if "score_inject" in ACTIVE:
        g["player_score"] += 1000
        ACTIVE.discard("score_inject")
        
    if "speed_hack" in ACTIVE:
        g["base_player_speed"] = 15
    else:
        g["base_player_speed"] = 5
    
    if "teleport" in ACTIVE:
        g["player_pos"][0] = 5
        g["player_pos"][1] = 5
        ACTIVE.remove("teleport")
        
    if "max_multiplier" in ACTIVE:
        g["combo_multiplier"] = 5
        
    if "powerup_timer_abuse" in ACTIVE:
        g["powerup_timer"] = 9999
        
    if "kill_enemies" in ACTIVE:
        g["enemies"].clear()
        
    if "freeze_enemies" in ACTIVE:
        g["global_enemy_speed"] = 0

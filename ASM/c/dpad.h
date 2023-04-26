#ifndef DPAD_H
#define DPAD_H

#include "dungeon_info.h"
#include "z64.h"

// must match DPAD_ACTIONS in Cosmetics.py
typedef enum {
    DPAD_ACTION_NONE,
    DPAD_ACTION_OCARINA,
    DPAD_ACTION_CHILD_TRADE,
    DPAD_ACTION_IRON_BOOTS,
    DPAD_ACTION_HOVER_BOOTS,
} dpad_action_t;

// PLAYER_STATE1_0 : Scene transition
// PLAYER_STATE1_SWINGING_BOTTLE
// PLAYER_STATE1_7 : Death
// PLAYER_STATE1_10 : Get an item
// PLAYER_STATE1_28 : Using Non-Weapon Item
// PLAYER_STATE1_29 : Environment Frozen/Invulnerability
#define BLOCK_DPAD (0x00000001 | \
                    0x00000002 | \
                    0x00000080 | \
                    0x00000400 | \
                    0x10000000 | \
                    0x20000000)

// PLAYER_STATE1_23 : Riding Epona
// PLAYER_STATE1_11 : Link holding something over his head
// PLAYER_STATE1_21 : Climbing walls
// PLAYER_STATE1_27 : Swimming
#define BLOCK_ITEMS (0x00800000 | \
                     0x00000800 | \
                     0x00200000 | \
                     0x08000000)

extern uint16_t CFG_ADULT_TRADE_SHUFFLE;
extern uint16_t CFG_CHILD_TRADE_SHUFFLE;

#define CAN_DRAW_TRADE_DPAD (z64_game.pause_ctxt.state == 6 && \
                            z64_game.pause_ctxt.screen_idx == 0 && \
                            (!z64_game.pause_ctxt.changing || z64_game.pause_ctxt.changing == 3) && \
                            ((z64_game.pause_ctxt.item_cursor == Z64_SLOT_ADULT_TRADE && CFG_ADULT_TRADE_SHUFFLE) || \
                            (z64_game.pause_ctxt.item_cursor == Z64_SLOT_CHILD_TRADE && CFG_CHILD_TRADE_SHUFFLE)))

#define CAN_USE_TRADE_DPAD  (CAN_DRAW_TRADE_DPAD && z64_game.pause_ctxt.changing != 3)

#define CAN_USE_DPAD        (((z64_link.state_flags_1 & BLOCK_DPAD) == 0) && \
                            ((uint32_t)z64_ctxt.state_dtor==z64_state_ovl_tab[3].vram_dtor) && \
                            (z64_file.game_mode == 0) && \
                            ((z64_event_state_1 & 0x20) == 0) && \
                            (!CAN_DRAW_DUNGEON_INFO || !CFG_DPAD_DUNGEON_INFO_ENABLE))

void handle_dpad();
void draw_dpad();

#endif

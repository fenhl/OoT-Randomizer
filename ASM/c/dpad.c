#include <stdbool.h>

#include "gfx.h"
#include "dpad.h"
#include "trade_quests.h"

extern uint8_t CFG_DISPLAY_DPAD;
extern dpad_action_t CFG_DPAD_ACTIONS[6];

//unknown 00 is a pointer to some vector transformation when the sound is tied to an actor. actor + 0x3E, when not tied to an actor (map), always 80104394
//unknown 01 is always 4 in my testing
//unknown 02 is a pointer to some kind of audio configuration Always 801043A0 in my testing
//unknown 03 is always a3 in my testing
//unknown 04 is always a3 + 0x08 in my testing (801043A8)
typedef void(*playsfx_t)(uint16_t sfx, z64_xyzf_t *unk_00_, int8_t unk_01_ , float *unk_02_, float *unk_03_, float *unk_04_);
typedef void(*usebutton_t)(z64_game_t *game, z64_link_t *link, uint8_t item, uint8_t button);

#define z64_playsfx   ((playsfx_t)      0x800C806C)
#define z64_usebutton ((usebutton_t)    0x8038C9A0)

typedef bool (*dpad_bool_fn)();
typedef int (*dpad_sprite_tile_fn)();
typedef void (*dpad_press_fn)();

typedef struct {
    dpad_bool_fn has_item;
    dpad_bool_fn can_use;
    dpad_bool_fn is_active;
    dpad_sprite_tile_fn sprite_tile;
    dpad_press_fn on_press;
} dpad_row_t;

bool dpad_has_item_none() { return false; }
bool dpad_can_use_none() { return false; }
bool dpad_is_active_none() { return false; }
int dpad_sprite_tile_none() { return 0; }
void dpad_press_none() {}

bool dpad_has_item_ocarina() { return z64_file.items[Z64_SLOT_OCARINA] == Z64_ITEM_FAIRY_OCARINA || z64_file.items[Z64_SLOT_OCARINA] == Z64_ITEM_OCARINA_OF_TIME; }
bool dpad_can_use_ocarina() {
    return (
        // Not in pause menu
        z64_game.pause_ctxt.state == 0 &&
        // Scenes ocarina restrictions, specific to each scene
        !z64_game.restriction_flags.ocarina &&
        // see dpad.h
        ((z64_link.state_flags_1 & BLOCK_ITEMS) == 0) &&
        // Not getting pulled by hookshot
        (!(z64_link.state_flags_3 & (1 << 7))) &&
        // Not playing Bombchu bowling
        z64_game.bombchuBowlingStatus == 0 &&
        // Not playing Shooting Gallery
        z64_game.shootingGalleryStatus == 0
    );
}
bool dpad_is_active_ocarina() { return false; } //TODO show as active while playing? (visible during HUD fadeout)
int dpad_sprite_tile_ocarina() { return z64_file.items[Z64_SLOT_OCARINA]; }
void dpad_press_ocarina() { z64_usebutton(&z64_game, &z64_link, z64_file.items[Z64_SLOT_OCARINA], 2); }

bool dpad_has_item_child_trade() { return z64_file.items[Z64_SLOT_CHILD_TRADE] >= Z64_ITEM_WEIRD_EGG && z64_file.items[Z64_SLOT_CHILD_TRADE] <= Z64_ITEM_MASK_OF_TRUTH; }
bool dpad_can_use_child_trade() {
    return (
        // is child
        z64_file.link_age == 1 &&
        // Not in pause menu
        z64_game.pause_ctxt.state == 0 &&
        // Scenes trade item restrictions, specific to each scene
        !z64_game.restriction_flags.trade_items &&
        // see dpad.h
        ((z64_link.state_flags_1 & BLOCK_ITEMS) == 0)
    );
}
bool dpad_is_active_child_trade() { return z64_link.current_mask >= 1 && z64_link.current_mask <= 9; }
int dpad_sprite_tile_child_trade() { return z64_file.items[Z64_SLOT_CHILD_TRADE]; }
void dpad_press_child_trade() { z64_usebutton(&z64_game, &z64_link, z64_file.items[Z64_SLOT_CHILD_TRADE], 2); }

bool dpad_has_item_iron_boots() { return z64_file.iron_boots; }
bool dpad_can_use_iron_boots() { return z64_file.link_age == 0; }
bool dpad_is_active_iron_boots() { return z64_file.equip_boots == 2; }
int dpad_sprite_tile_iron_boots() { return 69; }
void dpad_press_iron_boots() {
    if (z64_file.equip_boots == 2) {
        z64_file.equip_boots = 1;
    } else {
        z64_file.equip_boots = 2;
    }
    z64_UpdateEquipment(&z64_game, &z64_link);
    z64_playsfx(0x835, (z64_xyzf_t *)0x80104394, 0x04, (float *)0x801043A0, (float *)0x801043A0, (float *)0x801043A8);
}

bool dpad_has_item_hover_boots() { return z64_file.hover_boots; }
bool dpad_can_use_hover_boots() { return z64_file.link_age == 0; }
bool dpad_is_active_hover_boots() { return z64_file.equip_boots == 3; }
int dpad_sprite_tile_hover_boots() { return 70; }
void dpad_press_hover_boots() {
    if (z64_file.equip_boots == 3) {
        z64_file.equip_boots = 1;
    } else {
        z64_file.equip_boots = 3;
    }
    z64_UpdateEquipment(&z64_game, &z64_link);
    z64_playsfx(0x835, (z64_xyzf_t *)0x80104394, 0x04, (float *)0x801043A0, (float *)0x801043A0, (float *)0x801043A8);
}

dpad_row_t dpad_table[] = {
    [DPAD_ACTION_NONE] = { .has_item = dpad_has_item_none, .can_use = dpad_can_use_none, .is_active = dpad_is_active_none, .sprite_tile = dpad_sprite_tile_none, .on_press = dpad_press_none },
    [DPAD_ACTION_OCARINA] = { .has_item = dpad_has_item_ocarina, .can_use = dpad_can_use_ocarina, .is_active = dpad_is_active_ocarina, .sprite_tile = dpad_sprite_tile_ocarina, .on_press = dpad_press_ocarina },
    [DPAD_ACTION_CHILD_TRADE] = { .has_item = dpad_has_item_child_trade, .can_use = dpad_can_use_child_trade, .is_active = dpad_is_active_child_trade, .sprite_tile = dpad_sprite_tile_child_trade, .on_press = dpad_press_child_trade },
    [DPAD_ACTION_IRON_BOOTS] = { .has_item = dpad_has_item_iron_boots, .can_use = dpad_can_use_iron_boots, .is_active = dpad_is_active_iron_boots, .sprite_tile = dpad_sprite_tile_iron_boots, .on_press = dpad_press_iron_boots },
    [DPAD_ACTION_HOVER_BOOTS] = { .has_item = dpad_has_item_hover_boots, .can_use = dpad_can_use_hover_boots, .is_active = dpad_is_active_hover_boots, .sprite_tile = dpad_sprite_tile_hover_boots, .on_press = dpad_press_hover_boots },
};

void handle_dpad() {
    pad_t pad_pressed = z64_game.common.input[0].pad_pressed;
    pad_t pad_held = z64_ctxt.input[0].raw.pad;

    if (CAN_USE_TRADE_DPAD) {
        uint8_t current_trade_item = z64_file.items[z64_game.pause_ctxt.item_cursor];
        if (IsTradeItem(current_trade_item)) {
            uint8_t potential_trade_item = current_trade_item;

            if (pad_pressed.dl) {
                potential_trade_item = SaveFile_PrevOwnedTradeItem(current_trade_item);
            }

            if (pad_pressed.dr) {
                potential_trade_item = SaveFile_NextOwnedTradeItem(current_trade_item);
            }

            if (current_trade_item != potential_trade_item) {
                UpdateTradeEquips(potential_trade_item, z64_game.pause_ctxt.item_cursor);
                PlaySFX(0x4809); // cursor move sound effect NA_SE_SY_CURSOR
            }
        }
    } else if (CAN_USE_DPAD && (!pad_held.a || !CAN_DRAW_DUNGEON_INFO)) {
        int action_index = -1;
        if (z64_file.link_age == 0) {
            if (pad_pressed.dd) {
                action_index = 0;
            } else if (pad_pressed.dr) {
                action_index = 1;
            } else if (pad_pressed.dl) {
                action_index = 2;
            }
        } else {
            if (pad_pressed.dd) {
                action_index = 3;
            } else if (pad_pressed.dr) {
                action_index = 4;
            } else if (pad_pressed.dl) {
                action_index = 5;
            }
        }
        if (action_index != -1) {
            dpad_row_t row = dpad_table[CFG_DPAD_ACTIONS[action_index]];
            if (row.has_item() && row.can_use()) {
                row.on_press();
            }
        }
    }
}

void draw_dpad_icon(z64_disp_buf_t *db, int left, int top, uint16_t alpha, dpad_action_t action) {
    dpad_row_t row = dpad_table[action];
    if (row.has_item()) {
        if (row.can_use()) {
            gDPSetPrimColor(db->p++, 0, 0, 0xFF, 0xFF, 0xFF, alpha);
        } else {
            gDPSetPrimColor(db->p++, 0, 0, 0xFF, 0xFF, 0xFF, alpha * 0x46 / 0xFF);
        }
        sprite_load(db, &items_sprite, row.sprite_tile(), 1);
        if (row.is_active()) {
            sprite_draw(db, &items_sprite, 0, left - 2, top - 2, 16, 16);
        } else {
            sprite_draw(db, &items_sprite, 0, left, top, 12, 12);
        }
    }
}

bool should_draw_dpad() {
    if (CAN_DRAW_DUNGEON_INFO || CAN_DRAW_TRADE_DPAD) { return true; }
    if (!CFG_DISPLAY_DPAD) { return false; }
    bool is_adult = z64_file.link_age == 0;
    if (dpad_table[CFG_DPAD_ACTIONS[is_adult ? 0 : 3]].has_item()) { return true; }
    if (dpad_table[CFG_DPAD_ACTIONS[is_adult ? 1 : 4]].has_item()) { return true; }
    if (dpad_table[CFG_DPAD_ACTIONS[is_adult ? 2 : 5]].has_item()) { return true; }
    return false;
}

void draw_dpad() {
    if (!should_draw_dpad()) { return; }

    z64_disp_buf_t *db = &(z64_ctxt.gfx->overlay);
    gSPDisplayList(db->p++, &setup_db);
    gDPPipeSync(db->p++);
    gDPSetCombineMode(db->p++, G_CC_MODULATEIA_PRIM, G_CC_MODULATEIA_PRIM);
    uint16_t alpha = z64_game.hud_alpha_channels.rupees_keys_magic;

    gDPSetPrimColor(db->p++, 0, 0, 0xFF, 0xFF, 0xFF, alpha);
    sprite_load(db, &dpad_sprite, 0, 1);
    int left = 271;
    if (CAN_DRAW_TRADE_DPAD) {
        uint8_t current_trade_item = z64_file.items[z64_game.pause_ctxt.item_cursor];
        if (IsTradeItem(current_trade_item)) {
            uint8_t prev_trade_item = SaveFile_PrevOwnedTradeItem(current_trade_item);
            uint8_t next_trade_item = SaveFile_NextOwnedTradeItem(current_trade_item);

            if (current_trade_item != next_trade_item) {
                // D-pad under selected trade item slot, if more than one trade item
                left = (z64_game.pause_ctxt.item_cursor == Z64_SLOT_ADULT_TRADE) ? 197 : 230;
                sprite_draw(db, &dpad_sprite, 0, left, 190, 24, 24);

                // Previous trade quest item
                gDPSetPrimColor(db->p++, 0, 0, 0xFF, 0xFF, 0xFF, alpha);
                sprite_load(db, &items_sprite, prev_trade_item, 1);
                sprite_draw(db, &items_sprite, 0, left - 16, 194, 16, 16);

                // Next trade quest item
                gDPSetPrimColor(db->p++, 0, 0, 0xFF, 0xFF, 0xFF, alpha);
                sprite_load(db, &items_sprite, next_trade_item, 1);
                sprite_draw(db, &items_sprite, 0, left + 24, 194, 16, 16);
            }
        }
    }
    if (left == 271) {
        // D-pad under C buttons, if trade slot selector not drawn
        sprite_draw(db, &dpad_sprite, 0, left, 64, 16, 16);
    }

    if (CAN_DRAW_DUNGEON_INFO && CFG_DPAD_DUNGEON_INFO_ENABLE && left == 271) {
        // Zora sapphire on D-down
        sprite_load(db, &stones_sprite, 2, 1);
        sprite_draw(db, &stones_sprite, 0, 273, 77, 12, 12);

        // small key on D-right
        sprite_load(db, &quest_items_sprite, 17, 1);
        sprite_draw(db, &quest_items_sprite, 0, 285, 66, 12, 12);

        // map on D-left
        sprite_load(db, &quest_items_sprite, 16, 1);
        sprite_draw(db, &quest_items_sprite, 0, 260, 66, 12, 12);
    } else if (left == 271) {
        bool is_adult = z64_file.link_age == 0;
        draw_dpad_icon(db, 273, 77, alpha, CFG_DPAD_ACTIONS[is_adult ? 0 : 3]);
        draw_dpad_icon(db, 285, 66, alpha, CFG_DPAD_ACTIONS[is_adult ? 1 : 4]);
        draw_dpad_icon(db, 260, 66, alpha, CFG_DPAD_ACTIONS[is_adult ? 2 : 5]);
    }

    gDPPipeSync(db->p++);
}


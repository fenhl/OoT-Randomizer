#include "agony.h"
#include "dungeon_info.h"
#include "gfx.h"
#include "item_effects.h"
#include "save.h"
#include "z64.h"

typedef struct {
    unsigned char alpha_level : 8;
    signed char   pos         : 2;
    unsigned char next        : 6;
} alpha_data_t;

static const alpha_data_t ALPHA_DATA[] = {
    {0x00,  0,  0}, // 0 - Zero
    {0x33, -1,  2}, // 1 - Fade in from zero
    {0x66,  1,  3}, // 2
    {0x99, -1,  4}, // 3
    {0xCC,  1,  5}, // 4
    {0xFF, -1,  6}, // 5 - Full intensity
    {0xFF,  1,  7}, // 6
    {0xFF, -1,  8}, // 7
    {0xFF,  1,  9}, // 8
    {0xE0, -1, 10}, // 9 - Fade out to hold
    {0xC2,  1, 11}, // 10
    {0xA3, -1, 12}, // 11
    {0x85,  1, 13}, // 12
    {0x66,  0, 13}, // 13 - Hold
    {0x44,  0, 15}, // 14 - Fade out
    {0x22,  0,  0}, // 15
    {0x85, -1, 17}, // 16 - Fade in from hold
    {0xA3,  1, 18}, // 17
    {0xC2, -1, 19}, // 18
    {0xE0,  1,  5}  // 19
};

#define ALPHA_ANIM_TERMINATE  0
#define ALPHA_ANIM_START      1
#define ALPHA_ANIM_HOLD      13
#define ALPHA_ANIM_FADE      14
#define ALPHA_ANIM_INTERRUPT 16

static const alpha_data_t* alpha_frame = ALPHA_DATA + ALPHA_ANIM_TERMINATE;

void agony_inside_radius_setup() {
}

void agony_outside_radius_setup() {
    if (alpha_frame == ALPHA_DATA + ALPHA_ANIM_HOLD) {
        alpha_frame = ALPHA_DATA + ALPHA_ANIM_FADE;
    }
}

void agony_vibrate_setup() {
    if (alpha_frame == ALPHA_DATA + ALPHA_ANIM_TERMINATE) {
        alpha_frame = ALPHA_DATA + ALPHA_ANIM_START;
    }
    else {
        alpha_frame = ALPHA_DATA + ALPHA_ANIM_INTERRUPT;
    }
}

void draw_agony_graphic(int hoffset, int voffset, unsigned char alpha) {
    // terminate if alpha level prohibited (changed areas)
    unsigned char maxalpha = (unsigned char)z64_game.hud_alpha_channels.rupees_keys_magic;

    if (alpha > maxalpha) {
        alpha = maxalpha;
    }

    z64_disp_buf_t *db = &(z64_ctxt.gfx->overlay);
    gSPDisplayList(db->p++, &setup_db);
    gDPPipeSync(db->p++);
    gDPSetCombineMode(db->p++, G_CC_MODULATEIA_PRIM, G_CC_MODULATEIA_PRIM);
    gDPSetPrimColor(db->p++, 0, 0, 0xFF, 0xFF, 0xFF, alpha);
    sprite_load(db, &quest_items_sprite, 9, 1);
    sprite_draw(db, &quest_items_sprite, 0, 27+hoffset, 189+voffset, 16, 16);
    gDPPipeSync(db->p++);
}

void draw_silver_rupee_graphic(int voffset) {
    unsigned char alpha = 0xFF;
    unsigned char maxalpha = (unsigned char)z64_game.hud_alpha_channels.rupees_keys_magic;
    if (maxalpha == 0xAA) maxalpha = 0xFF;

    if (alpha > maxalpha) {
        alpha = maxalpha;
    }

    z64_disp_buf_t *db = &(z64_ctxt.gfx->overlay);
    gSPDisplayList(db->p++, &setup_db);
    gDPPipeSync(db->p++);
    gDPSetCombineMode(db->p++, G_CC_MODULATEIA_PRIM, G_CC_MODULATEIA_PRIM);
    gDPSetPrimColor(db->p++, 0, 0, 0xFF, 0xFF, 0xFF, alpha);
    sprite_load(db, &key_rupee_clock_sprite, 1, 1);
    sprite_draw(db, &key_rupee_clock_sprite, 0, 27, 189+voffset, 16, 16);
    gDPPipeSync(db->p++);
}

int16_t silver_rupee_rooms[CASTLE_ID + 1][24][2] = {
    [DODONGO_ID] = {[2] = {0, 1}},
    [SPIRIT_ID]  = {[0] = {0, 14}, [2] = {12, 0}, [8] = {15, 0}, [13] = {13, 0}, [23] = {0, 16}},
    [SHADOW_ID]  = {[6] = {5, 5}, [9] = {7, 7}, [11] = {8, 8}, [16] = {0, 6}},
    [BOTW_ID]    = {[1] = {4, 0}},
    [ICE_ID]     = {[3] = {2, 0}, [5] = {3, 0}},
    [GTG_ID]     = {[2] = {9, 9}, [6] = {10, 10}, [9] = {11, 11}},
    [CASTLE_ID]  = {[3] = {0, 21}, [6] = {22, 0}, [8] = {18, 0}, [12] = {0, 20}, [14] = {19, 19}, [17] = {17, 0}},
};

void draw_agony() {
    int hoffset = 16;
    int voffset = 0;
    int scene_index = z64_game.scene_index;
    if (scene_index < 0x11 && z64_file.dungeon_keys[scene_index] >= 0) {
        voffset -= 17;
    }
    if (scene_index <= CASTLE_ID && z64_file.void_room_index < 24 && silver_rupee_rooms[scene_index][z64_file.void_room_index][CFG_DUNGEON_IS_MQ[scene_index]]) {
        int16_t silver_rupee_id = silver_rupee_rooms[scene_index][z64_file.void_room_index][CFG_DUNGEON_IS_MQ[scene_index]] - 1;
        uint8_t count = extended_savectx.silver_rupee_counts[silver_rupee_id];
        uint8_t digits[2] = {count % 10, count / 10};
        draw_silver_rupee_graphic(voffset);
        z64_disp_buf_t *db = &(z64_ctxt.gfx->overlay);
        gSPDisplayList(db->p++, &setup_db);
        gDPPipeSync(db->p++);
        gDPSetCombineMode(db->p++, G_CC_MODULATEIA_PRIM, G_CC_MODULATEIA_PRIM);
        if (count == silver_rupee_vars[silver_rupee_id][CFG_DUNGEON_IS_MQ[scene_index]].needed_count) {
            gDPSetPrimColor(db->p++, 0, 0, 0x78, 0xFF, 0x00, 0xFF);
        } else if (count != 0) {
            gDPSetPrimColor(db->p++, 0, 0, 0xFF, 0xFF, 0xFF, 0xFF);
        } else {
            gDPSetPrimColor(db->p++, 0, 0, 0x64, 0x64, 0x64, 0xFF);
        }
        //TODO use the same font used for rupee and small key counts
        sprite_load(db, &counter_digit_sprite, 0, 10);
        for (uint16_t digit = 0; digit < 2; digit++) {
            sprite_draw(db, &counter_digit_sprite, digits[digit], 27+hoffset, 189+voffset, 8, 16);
            hoffset += 8;
        }
        gDPPipeSync(db->p++);
        voffset -= 17;
    }
    if (alpha_frame != ALPHA_DATA + ALPHA_ANIM_TERMINATE) {
        unsigned char alpha = alpha_frame->alpha_level;
        hoffset = alpha_frame->pos;
        alpha_frame = ALPHA_DATA + alpha_frame->next;
        draw_agony_graphic(hoffset, voffset, alpha);
    }
}


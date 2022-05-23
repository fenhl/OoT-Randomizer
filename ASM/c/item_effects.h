#ifndef ITEM_EFFECTS_H
#define ITEM_EFFECTS_H

#include "z64.h"
#include "icetrap.h"
#include "triforce.h"

void no_effect(z64_file_t *save, int16_t arg1, int16_t arg2);
void full_heal(z64_file_t *save, int16_t arg1, int16_t arg2);
void give_triforce_piece(z64_file_t *save, int16_t arg1, int16_t arg2);
void give_tycoon_wallet(z64_file_t *save, int16_t arg1, int16_t arg2);
void give_biggoron_sword(z64_file_t *save, int16_t arg1, int16_t arg2);
void give_bottle(z64_file_t *save, int16_t bottle_item_id, int16_t arg2);
void give_dungeon_item(z64_file_t *save, int16_t mask, int16_t dungeon_id);
void give_small_key(z64_file_t *save, int16_t dungeon_id, int16_t arg2);
void give_small_key_ring(z64_file_t *save, int16_t dungeon_id, int16_t arg2);
void give_silver_rupee(z64_file_t *save, int16_t dungeon_id, int16_t silver_rupee_id);
void give_silver_rupee_pouch(z64_file_t *save, int16_t dungeon_id, int16_t silver_rupee_id);
void give_defense(z64_file_t *save, int16_t arg1, int16_t arg2);
void give_magic(z64_file_t *save, int16_t arg1, int16_t arg2);
void give_double_magic(z64_file_t *save, int16_t arg1, int16_t arg2);
void give_fairy_ocarina(z64_file_t *save, int16_t arg1, int16_t arg2);
void give_song(z64_file_t *save, int16_t quest_bit, int16_t arg2);
void ice_trap_effect(z64_file_t *save, int16_t arg1, int16_t arg2);
void give_bean_pack(z64_file_t *save, int16_t arg1, int16_t arg2);
void fill_wallet_upgrade(z64_file_t *save, int16_t arg1, int16_t arg2);
void clear_excess_hearts(z64_file_t *save, int16_t arg1, int16_t arg2);
void open_mask_shop(z64_file_t *save, int16_t arg1, int16_t arg2);

enum dungeon {
    DEKU_ID    = 0,
    DODONGO_ID = 1,
    JABU_ID    = 2,
    FOREST_ID  = 3,
    FIRE_ID    = 4,
    WATER_ID   = 5,
    SPIRIT_ID  = 6,
    SHADOW_ID  = 7,
    BOTW_ID    = 8,
    ICE_ID     = 9,
    TOWER_ID   = 10,
    GTG_ID     = 11,
    FORT_ID    = 12,
    CASTLE_ID  = 13,
};

typedef struct {
    uint8_t needed_count;
    uint8_t switch_flag;
} silver_rupee_data_t;

silver_rupee_data_t silver_rupee_vars[0x16][2] = {
    //Vanilla,   Master Quest
    {{-1, 0xFF}, { 5, 0x1F}}, // Dodongos Cavern Staircase. Patched to use switch flag 0x1F
    {{ 5, 0x08}, {-1, 0xFF}}, // Ice Cavern Spinning Scythe
    {{ 5, 0x09}, {-1, 0xFF}}, // Ice Cavern Push Block
    {{ 5, 0x1F}, {-1, 0xFF}}, // Bottom of the Well Basement
    {{ 5, 0x01}, { 5, 0x01}}, // Shadow Temple Scythe Shortcut
    {{-1, 0xFF}, {10, 0x03}}, // Shadow Temple Invisible Blades
    {{ 5, 0x09}, { 5, 0x11}}, // Shadow Temple Huge Pit
    {{ 5, 0x08}, {10, 0x08}}, // Shadow Temple Invisible Spikes
    {{ 5, 0x1C}, { 5, 0x1C}}, // Gerudo Training Ground Slopes
    {{ 5, 0x0C}, { 6, 0x0C}}, // Gerudo Training Ground Lava
    {{ 5, 0x1B}, { 3, 0x1B}}, // Gerudo Training Ground Water
    {{ 5, 0x05}, {-1, 0xFF}}, // Spirit Temple Child Early Torches
    {{ 5, 0x02}, {-1, 0xFF}}, // Spirit Temple Adult Boulders
    {{-1, 0xFF}, { 5, 0x1F}}, // Spirit Temple Lobby and Lower Adult. Patched to use switch flag 0x1F
    {{ 5, 0x0A}, {-1, 0xFF}}, // Spirit Temple Sun Block
    {{-1, 0xFF}, { 5, 0x00}}, // Spirit Temple Adult Climb
    {{ 5, 0x0B}, {-1, 0xFF}}, // Ganons Castle Spirit Trial
    {{ 5, 0x12}, {-1, 0xFF}}, // Ganons Castle Light Trial
    {{ 5, 0x09}, { 5, 0x01}}, // Ganons Castle Fire Trial
    {{-1, 0xFF}, { 5, 0x1B}}, // Ganons Castle Shadow Trial
    {{-1, 0xFF}, { 5, 0x02}}, // Ganons Castle Water Trial
    {{ 5, 0x0E}, {-1, 0xFF}}, // Ganons Castle Forest Trial
};

#endif

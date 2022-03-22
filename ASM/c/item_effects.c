#include "item_effects.h"
#include "dungeon_info.h"

#define rupee_cap ((uint16_t*)0x800F8CEC)
volatile uint8_t MAX_RUPEES = 0;

typedef void (*commit_scene_flags_fn)(z64_game_t* game_ctxt);
#define commit_scene_flags ((commit_scene_flags_fn)0x8009D894)
typedef void (*save_game_fn)(void* unk);
#define save_game ((save_game_fn)0x800905D4)

void no_effect(z64_file_t *save, int16_t arg1, int16_t arg2) {
}

void full_heal(z64_file_t *save, int16_t arg1, int16_t arg2) {
    save->refill_hearts = 20 * 0x10;
}

typedef struct {
    uint32_t mask;
    uint8_t  dungeon_idx;
    uint32_t max_vanilla;
    uint32_t max_mq;
} silver_rupee_data_t;

silver_rupee_data_t silver_rupee_data[2][0x20] = {
    {
        [0x17] = {0x03800000,  1,  5, -1}, // Dodongos Cavern Staircase
        [0x14] = {0x00700000,  9,  5, -1}, // Ice Cavern Spinning Scythe
        [0x11] = {0x000e0000,  9,  5, -1}, // Ice Cavern Push Block
        [0x0e] = {0x0001c000,  8,  5, -1}, // Bottom of the Well Basement
        [0x0b] = {0x00003800,  7,  5,  5}, // Shadow Temple Scythe Shortcut
        [0x07] = {0x00000780,  7, -1,  9}, // Shadow Temple Invisible Blades
        [0x04] = {0x00000070,  7,  5,  5}, // Shadow Temple Huge Pit
        [0x00] = {0x0000000f,  7,  5, 10}, // Shadow Temple Invisible Spikes
    },
    {
        [0x1b] = {0x38000000, 11,  5,  5}, // Gerudo Training Ground Slopes
        [0x18] = {0x07000000, 11,  5,  6}, // Gerudo Training Ground Lava
        [0x15] = {0x00e00000, 11,  5,  3}, // Gerudo Training Ground Water
        [0x12] = {0x001c0000,  6,  5, -1}, // Spirit Temple Child Early Torches
        [0x0f] = {0x00038000,  6,  5,  5}, // Spirit Temple Adult Boulders/Lobby and Lower Adult
        [0x0c] = {0x00007000,  6,  5,  5}, // Spirit Temple Sun Block/Adult Climb
        [0x09] = {0x00000e00, 13,  5,  5}, // Ganons Castle Spirit/Shadow Trial
        [0x06] = {0x000001c0, 13,  5,  5}, // Ganons Castle Light/Water Trial
        [0x03] = {0x00000038, 13,  5,  5}, // Ganons Castle Fire Trial
        [0x00] = {0x00000007, 13,  5, -1}, // Ganons Castle Forest Trial
    },
};

void give_silver_rupee(z64_file_t *save, int16_t arg1, int16_t arg2) {
    silver_rupee_data_t data = silver_rupee_data[arg1 - 0x49][arg2];
    uint32_t max = CFG_DUNGEON_IS_MQ[data.dungeon_idx] ? data.max_mq : data.max_vanilla;
    if (((save->scene_flags[arg1].unk_00_ & data.mask) >> arg2) < max) {
        save->scene_flags[arg1].unk_00_ += 1 << arg2;
        if (((save->scene_flags[arg1].unk_00_ & data.mask) >> arg2) == max) {
            //TODO set flag depending on args
            //TODO make sure silver rupee for current scene is handled correctly
            save->scene_flags[0x09].swch |= 0x00800000;
        }
    }
}

void give_silver_rupee_pouch(z64_file_t *save, int16_t arg1, int16_t arg2) {
    silver_rupee_data_t data = silver_rupee_data[arg1 - 0x49][arg2];
    uint32_t max = CFG_DUNGEON_IS_MQ[data.dungeon_idx] ? data.max_mq : data.max_vanilla;
    if (((save->scene_flags[arg1].unk_00_ & data.mask) >> arg2) < max) {
        save->scene_flags[arg1].unk_00_ |= max << arg2;
        //TODO set flag depending on args
        //TODO make sure silver rupee pouch for current scene is handled correctly
        save->scene_flags[0x09].swch |= 0x00800000;
    }
}

void give_triforce_piece(z64_file_t *save, int16_t arg1, int16_t arg2) {
    save->scene_flags[0x48].unk_00_ += 1; //Unused word in scene x48.
    set_triforce_render();

    // Trigger win when the target is hit
    if (save->scene_flags[0x48].unk_00_ == triforce_pieces_requied) {
        // Give GC boss key to allow beating the game again afterwards
        give_dungeon_item(save, 0x01, 10);

        // Save Game
        save->entrance_index = z64_game.entrance_index;
        save->scene_index = z64_game.scene_index;
        commit_scene_flags(&z64_game);
        save_game(&z64_game + 0x1F74);

        // warp to start of credits sequence
        z64_file.cutscene_next = 0xFFF8;
        z64_game.entrance_index = 0x00A0;
        z64_game.scene_load_flag = 0x14;
        z64_game.fadeout_transition = 0x01;
    }
}

void give_tycoon_wallet(z64_file_t *save, int16_t arg1, int16_t arg2) {
    save->wallet = 3;
    if(MAX_RUPEES)
        save->rupees = rupee_cap[arg1];
}

void give_biggoron_sword(z64_file_t *save, int16_t arg1, int16_t arg2) {
    save->bgs_flag = 1; // Set flag to make the sword durable
}

void give_bottle(z64_file_t *save, int16_t bottle_item_id, int16_t arg2) {
    for (int i = Z64_SLOT_BOTTLE_1; i <= Z64_SLOT_BOTTLE_4; i++) {
        if (save->items[i] == -1) {
            save->items[i] = bottle_item_id;
            return;
        }
    }
}

void give_dungeon_item(z64_file_t *save, int16_t mask, int16_t dungeon_id) {
    save->dungeon_items[dungeon_id].items |= mask;
}

char key_counts[14][2] = {
    {0, 0}, // Deku Tree
    {0, 0}, // Dodongo's Cavern
    {0, 0}, // Inside Jabu Jabu's Belly
    {5, 6}, // Forest Temple
    {8, 5}, // Fire Temple
    {6, 2}, // Water Temple
    {5, 7}, // Spirit Temple
    {5, 6}, // Shadow Temple
    {3, 2}, // Bottom of the Well
    {0, 0}, // Ice Cavern
    {0, 0}, // Ganon's Tower
    {9, 3}, // Gerudo Training Ground
    {4, 4}, // Thieves' Hideout
    {2, 3}, // Ganon's Castle
};

void give_small_key(z64_file_t *save, int16_t dungeon_id, int16_t arg2) {
    int8_t keys = save->dungeon_keys[dungeon_id] > 0 ? save->dungeon_keys[dungeon_id] : 0;
    save->dungeon_keys[dungeon_id] = keys + 1;
}

void give_small_key_ring(z64_file_t *save, int16_t dungeon_id, int16_t arg2) {
    int8_t keys = save->dungeon_keys[dungeon_id] > 0 ? save->dungeon_keys[dungeon_id] : 0;
    save->dungeon_keys[dungeon_id] = keys + key_counts[dungeon_id][CFG_DUNGEON_IS_MQ[dungeon_id]];
}

void give_defense(z64_file_t *save, int16_t arg1, int16_t arg2) {
    save->double_defense = 1;
    save->defense_hearts = 20;
    save->refill_hearts = 20 * 0x10;
}

void give_magic(z64_file_t *save, int16_t arg1, int16_t arg2) {
    save->magic_capacity_set = 1; // Set meter level
    save->magic_acquired = 1; // Required for meter to persist on save load
    save->magic_meter_size = 0x30; // Set meter size
    save->magic = 0x30; // Fill meter
}

void give_double_magic(z64_file_t *save, int16_t arg1, int16_t arg2) {
    save->magic_capacity_set = 2; // Set meter level
    save->magic_acquired = 1; // Required for meter to persist on save load
    save->magic_capacity = 1; // Required for meter to persist on save load
    save->magic_meter_size = 0x60; // Set meter size
    save->magic = 0x60; // Fill meter
}

void give_fairy_ocarina(z64_file_t *save, int16_t arg1, int16_t arg2) {
    save->items[Z64_SLOT_OCARINA] = 0x07;
}

void give_song(z64_file_t *save, int16_t quest_bit, int16_t arg2) {
    save->quest_items |= 1 << quest_bit;
}

void ice_trap_effect(z64_file_t *save, int16_t arg1, int16_t arg2) {
    push_pending_ice_trap();
}

void give_bean_pack(z64_file_t *save, int16_t arg1, int16_t arg2) {
    save->items[Z64_SLOT_BEANS] = Z64_ITEM_BEANS;
    save->ammo[14] += 10; // 10 Magic Beans
}

void fill_wallet_upgrade(z64_file_t *save, int16_t arg1, int16_t arg2) {
    if(MAX_RUPEES)
        save->rupees = rupee_cap[arg1];
}

uint8_t OPEN_KAKARIKO = 0;
uint8_t COMPLETE_MASK_QUEST = 0;
void open_mask_shop(z64_file_t *save, int16_t arg1, int16_t arg2) {
    if (OPEN_KAKARIKO) {
        save->inf_table[7] = save->inf_table[7] | 0x40; // "Spoke to Gate Guard About Mask Shop"
        if (!COMPLETE_MASK_QUEST) {
            save->item_get_inf[2] = save->item_get_inf[2] & 0xFB87; // Unset "Obtained Mask" flags just in case of savewarp before Impa.
        }
    }
    if (COMPLETE_MASK_QUEST) {
        save->inf_table[7] = save->inf_table[7] | 0x80; // "Soldier Wears Keaton Mask"
        save->item_get_inf[3] = save->item_get_inf[3] | 0x8F00; // "Sold Masks & Unlocked Masks" / "Obtained Mask of Truth"
        save->event_chk_inf[8] = save->event_chk_inf[8] | 0xF000; // "Paid Back Mask Fees"
    }
}

#include "item_upgrades.h"

#include "get_items.h"
#include "item_table.h"
#include "z64.h"

extern uint32_t FREE_BOMBCHU_DROPS;
extern uint8_t SHUFFLE_CHEST_GAME;
extern uint8_t TCG_REQUIRES_LENS;

// Co-op state
extern uint8_t PLAYER_ID;
extern uint8_t MW_PROGRESSIVE_ITEMS_ENABLE;
extern mw_progressive_items_state_t MW_PROGRESSIVE_ITEMS_STATE[256];


uint16_t no_upgrade(z64_file_t* save, override_t override) {
    return override.value.base.item_id;
}

uint16_t hookshot_upgrade(z64_file_t* save, override_t override) {
    switch ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->items[Z64_SLOT_HOOKSHOT] : MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].hookshot) {
        case ITEM_NONE: case 0: return GI_HOOKSHOT; // Hookshot
        default: return GI_LONGSHOT; // Longshot
    }
}

uint16_t strength_upgrade(z64_file_t* save, override_t override) {
    switch ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->strength_upgrade : MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].strength) {
        case 0: return GI_GORONS_BRACELET; // Goron Bracelet
        case 1: return GI_SILVER_GAUNTLETS; // Silver Gauntlets
        default: return GI_GOLD_GAUNTLETS; // Gold Gauntlets
    }
}

uint16_t bomb_bag_upgrade(z64_file_t* save, override_t override) {
    switch ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->bomb_bag : MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].bomb_bag) {
        case 0: return GI_BOMB_BAG_20; // Bomb Bag
        case 1: return GI_BOMB_BAG_30; // Bigger Bomb Bag
        default: return GI_BOMB_BAG_40; // Biggest Bomb Bag
    }
}

uint16_t bow_upgrade(z64_file_t* save, override_t override) {
    switch ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->quiver : MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].bow) {
        case 0: return GI_BOW; // Bow
        case 1: return GI_QUIVER_40; // Big Quiver
        default: return GI_QUIVER_50; // Biggest Quiver
    }
}

uint16_t slingshot_upgrade(z64_file_t* save, override_t override) {
    switch ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->bullet_bag : MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].slingshot) {
        case 0: return GI_SLINGSHOT; // Slingshot
        case 1: return GI_BULLET_BAG_40; // Bullet Bag (40)
        default: return GI_BULLET_BAG_50; // Bullet Bag (50)
    }
}

uint16_t wallet_upgrade(z64_file_t* save, override_t override) {
    switch ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->wallet : MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].wallet) {
        case 0: return GI_WALLET_ADULT; // Adult's Wallet
        case 1: return GI_WALLET_GIANT; // Giant's Wallet
        default: return GI_TYCOONS_WALLET; // Tycoon's Wallet
    }
}

uint16_t scale_upgrade(z64_file_t* save, override_t override) {
    switch ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->diving_upgrade : MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].scale) {
        case 0: return GI_SCALE_SILVER; // Silver Scale
        default: return GI_SCALE_GOLDEN; // Gold Scale
    }
}

uint16_t nut_upgrade(z64_file_t* save, override_t override) {
    switch ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->nut_upgrade : MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].nuts) {
        case 0: return GI_DEKU_NUT_UPGRADE_30; // 30 Nuts. 0 and 1 are both starting capacity
        case 1: return GI_DEKU_NUT_UPGRADE_30; // 30 Nuts
        default: return GI_DEKU_NUT_UPGRADE_40; // 40 Nuts
    }
}

uint16_t stick_upgrade(z64_file_t* save, override_t override) {
    switch ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->stick_upgrade : MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].sticks) {
        case 0: return GI_DEKU_STICK_UPGRADE_20; // 20 Sticks. 0 and 1 are both starting capacity
        case 1: return GI_DEKU_STICK_UPGRADE_20; // 20 Sticks
        default: return GI_DEKU_STICK_UPGRADE_30; // 30 Sticks
    }
}

uint16_t magic_upgrade(z64_file_t* save, override_t override) {
    switch ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->magic_acquired : MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].magic) {
        case 0: return GI_MAGIC_METER; // Single Magic
        default: return GI_DOUBLE_MAGIC; // Double Magic
    }
}

uint16_t bombchu_upgrade(z64_file_t* save, override_t override) {
    if (save->items[Z64_SLOT_BOMBCHU] == ITEM_NONE) {
        return GI_BOMBCHUS_20; // Bombchu 20 pack
    }
    if (save->ammo[8] <= 5) {
        return GI_BOMBCHUS_10; // Bombchu 10 pack
    }
    return GI_BOMBCHUS_5; // Bombchu 5 pack
}

uint16_t ocarina_upgrade(z64_file_t* save, override_t override) {
    switch ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->items[Z64_SLOT_OCARINA] : MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].ocarina) {
        case ITEM_NONE: case 0: return GI_OCARINA_FAIRY; // Fairy Ocarina
        default: return GI_OCARINA_OF_TIME; // Ocarina of Time
    }
}

uint16_t arrows_to_rupee(z64_file_t* save, override_t override) {
    return ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->quiver : MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].bow) ? override.value.base.item_id : GI_RUPEE_BLUE; // Blue Rupee
}

uint16_t bombs_to_rupee(z64_file_t* save, override_t override) {
    return ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->bomb_bag : MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].bomb_bag) ? override.value.base.item_id : GI_RUPEE_BLUE; // Blue Rupee
}

uint16_t seeds_to_rupee(z64_file_t* save, override_t override) {
    return ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->bullet_bag : MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].slingshot) ? override.value.base.item_id : GI_RUPEE_BLUE; // Blue Rupee
}

uint16_t letter_to_bottle(z64_file_t* save, override_t override) {
    if (save->event_chk_inf[3] & 0x0008) // "King Zora Moved Aside"
        return GI_REDUNDANT_LETTER_BOTTLE; // Redundant Letter Bottle
    if (save->items[Z64_SLOT_BOTTLE_1] == 0x1B || save->items[Z64_SLOT_BOTTLE_2] == 0x1B
     || save->items[Z64_SLOT_BOTTLE_3] == 0x1B || save->items[Z64_SLOT_BOTTLE_4] == 0x1B)
        return GI_REDUNDANT_LETTER_BOTTLE; // Redundant Letter Bottle
    return override.value.base.item_id;
}

uint16_t health_upgrade_cap(z64_file_t* save, override_t override) {
    if (save->energy_capacity >= 20 * 0x10) {  // Already at capped health.
        if (override.value.base.item_id == GI_HEART_PIECE_WIN) {  // Piece of Heart (Chest Game)
            return GI_CAPPED_PIECE_OF_HEART_CHESTGAME;
        }
        if (override.value.base.item_id == GI_HEART_CONTAINER) {  // Heart Container
            return GI_CAPPED_HEART_CONTAINER;
        }
        return GI_CAPPED_PIECE_OF_HEART;          // Piece of Heart / Fallthrough
    }
    return override.value.base.item_id;
}

uint16_t bombchus_to_bag(z64_file_t* save, override_t override) {
    if (FREE_BOMBCHU_DROPS && ((override.value.base.player == PLAYER_ID || !MW_PROGRESSIVE_ITEMS_ENABLE) ? save->items[Z64_SLOT_BOMBCHU] == ITEM_NONE : !MW_PROGRESSIVE_ITEMS_STATE[override.value.base.player].chu_bag)) {
        // First chu pack found, convert to bombchu bag to
        // tell player about chu drops. Different bags
        // to preserve original chu refill count.
        switch (override.value.base.item_id) {
            case GI_BOMBCHUS_5: case GI_BOMBCHUS_5_BIG_CHEST: return GI_BOMBCHU_BAG_5; // 5 pack
            case GI_BOMBCHUS_10: case GI_BOMBCHUS_10_BIG_CHEST: return GI_BOMBCHU_BAG_10; // 10 pack
            case GI_BOMBCHUS_20: case GI_BOMBCHUS_20_BIG_CHEST: return GI_BOMBCHU_BAG_20; // 20 pack
        }
    } else {
        // Subsequent chu packs stay as chu packs
        return override.value.base.item_id;
    }
}

uint16_t tcg_key_to_rupee(z64_file_t* save, override_t override) {
    uint16_t item_id = override.value.base.item_id;
    // Force treasure chest game loss if the setting to require Lens of Truth
    // is enabled. Room index is checked to avoid overriding the salesman's item.
    if (item_id == GI_DOOR_KEY && !SHUFFLE_CHEST_GAME && TCG_REQUIRES_LENS
        && override.value.base.player == PLAYER_ID
        && save->items[Z64_SLOT_LENS] != Z64_ITEM_LENS
        && z64_game.room_index != 0
    ) {
        return GI_RUPEE_GREEN_LOSE; // Green Rupee (Chest Game)
    } else {
        return item_id;
    }
}

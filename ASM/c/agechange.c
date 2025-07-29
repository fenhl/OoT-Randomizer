#include "agechange.h"
extern uint8_t SONG_OF_TIME_CHANGES_AGE;
static uint8_t change_age = 0;

void Ocarina_HandleLastPlayedSong(z64_game_t* play, z64_link_t* player, int16_t lastPlayedSong) {
    // Displaced code
    if (lastPlayedSong == 6) { // OCARINA_SONG_SARIAS
        z64_link.naviTextId = -0xE0;
        z64_link.navi_actor->flags |= (1 << 16); // ACTOR_FLAG_16
    }
    if (lastPlayedSong == 10) { // OCARINA_SONG_TIME

        if (!SONG_OF_TIME_CHANGES_AGE)
        {
            return;
        }
        // Restrict to ocarina free plays. This avoids checking SoT usage like ocarina spots or frogs.
        if (play->msgContext.ocarinaAction != 0x29) // OCARINA_ACTION_FREE_PLAY_DONE
        {
            return;
        }

        // Restrict usage in some areas.
        switch (play->scene_index) {
            case 0x0E: // SCENE_GANONS_TOWER_COLLAPSE_INTERIOR:
            case 0x0F: // SCENE_INSIDE_GANONS_CASTLE_COLLAPSE
            case 0x10: // SCENE_TREASURE_BOX_SHOP
            case 0x4B: // SCENE_BOMBCHU_BOWLING_ALLEY
            //case SCE_OOT_LAIR_GOHMA
            //case SCE_OOT_LAIR_KING_DODONGO
            //case SCE_OOT_LAIR_BARINADE
            //case SCE_OOT_LAIR_PHANTOM_GANON
            //case SCE_OOT_LAIR_VOLVAGIA
            //case SCE_OOT_LAIR_MORPHA
            //case SCE_OOT_LAIR_TWINROVA
            //case SCE_OOT_LAIR_BONGO_BONGO
            //case SCE_OOT_LAIR_GANONDORF
            case 0x1A: // SCENE_GANONS_TOWER_COLLAPSE_EXTERIOR
            case 0x3E: // SCENE_GROTTOS
            case 0x3C: // SCENE_FAIRYS_FOUNTAIN
            case 0x45: // SCENE_CASTLE_COURTYARD_GUARDS_DAY
            case 0x46: // SCENE_CASTLE_COURTYARD_GUARDS_NIGHT
            case 0x4A: // SCENE_CASTLE_COURTYARD_ZELDA
            case 0x4F: // SCENE_GANON_BOSS
            case 0x5F: // SCENE_HYRULE_CASTLE
            case 0x64: // SCENE_OUTSIDE_GANONS_CASTLE
            case 0x1B: // SCENE_MARKET_ENTRANCE_DAY
            case 0x1C: // SCENE_MARKET_ENTRANCE_NIGHT
            case 0x1D: // SCENE_MARKET_ENTRANCE_RUINS
            case 0x1E: // SCENE_BACK_ALLEY_DAY
            case 0x1F: // SCENE_BACK_ALLEY_NIGHT
            case 0x20: // SCENE_MARKET_DAY
            case 0x21: // SCENE_MARKET_NIGHT
            case 0x22: // SCENE_MARKET_RUINS
            case 0x23: // SCENE_TEMPLE_OF_TIME_EXTERIOR_DAY
            case 0x24: // SCENE_TEMPLE_OF_TIME_EXTERIOR_NIGHT
            case 0x25: // SCENE_TEMPLE_OF_TIME_EXTERIOR_RUINS
            case 0x3A: // SCENE_GRAVEKEEPERS_HUT
            case 0x49: // SCENE_FISHING_POND
                z64_DisplayTextbox(play, 0x045F, 0);
                play->msgContext.ocarinaMode = 4; // OCARINA_MODE_END
                return;
            default:
        }

        // Check Song of time block proximity.
        z64_actor_t *actor = play->actor_list[7].first; // 7 = ITEMACTION
        while (actor) {
            if (actor->actor_id == 0x1D1 || actor->actor_id == 0x1D6) { // ACTOR_OBJ_TIMEBLOCK and ACTOR_OBJ_WARP2BLOCK
                if (actor->xzdist_from_link + actor->ydist_from_link < 350) {
                    return;
                }
            }
            actor = actor->next;
        }
        z64_DisplayTextbox(play, 0x045E, 0);
        change_age = 1;
    }
}

void manage_age_change() {

    MessageContext *msgCtx = &(z64_game.msgContext);
    if (change_age == 1) {
        if (Message_ShouldAdvance(&z64_game)) {
            if (msgCtx->choiceIndex == 0) {
                int age = z64_file.link_age;
                z64_file.link_age = z64_game.link_age;
                z64_game.link_age = !z64_game.link_age;
                z64_file.link_age = age;
                z64_game.entrance_index = z64_file.entrance_index;
                z64_Play_SetupRespawnPoint(&z64_game, 1, 0xDFF);
                z64_file.respawn_flag = 2;

                z64_game.scene_load_flag = 0x14;
                z64_game.fadeout_transition = 0x02;
            }
            else {
                msgCtx->ocarinaMode = 4; // OCARINA_MODE_END
            }
            change_age = 0;
        }
    }
}

#include <stdint.h>
#include "z64.h"
#include "en_wonderitem.h"
#include "get_items.h"

static colorRGBA8_t sEffectPrimColorRed = { 255, 0, 0, 0 };
static colorRGBA8_t sEffectPrimColorYellow = {255, 255, 0};
static colorRGBA8_t sEffectEnvColor = { 255, 255, 255, 0 };
static z64_xyzf_t sEffectVelocity = { 0.0f, 0.1f, 0.0f };
static z64_xyzf_t sEffectAccel = { 0.0f, 0.01f, 0.0f };

extern uint16_t drop_collectible_override_flag;

void EnWonderitem_AfterInitHack(z64_actor_t* this, z64_game_t* globalCtx)
{
    if(this->actor_id != 0x112)
        return;

    EnWonderItem* wonderitem = (EnWonderItem*)this;
    wonderitem->overridden = 0;

    EnItem00 dummy;
    dummy.actor.actor_id = 0x15;
    dummy.actor.rot_init.y = this->rot_init.y; //flag was just stored in z rotation
    dummy.actor.variable = 0;

    // Check if the Wonderitem should be overridden
    dummy.override = lookup_override(&(dummy.actor), globalCtx->scene_index, 0);
    if(dummy.override.key.all != 0 && !Get_CollectibleOverrideFlag(&dummy))
    {
        wonderitem->overridden = 1;
    }
}

void EnWonderItem_Multitag_DrawHack(z64_xyzf_t* tags, uint32_t index, EnWonderItem* this)
{
    if(this->overridden)
    {
        colorRGBA8_t* color = &sEffectPrimColorRed;
        if(this->wonderMode == WONDERITEM_MULTITAG_ORDERED)
            color = &sEffectPrimColorYellow;
        z64_xyzf_t pos = tags[index];
        pos.y += 15.0;
        z64_EffectSsKiraKira_SpawnSmall(&z64_game, &pos, &sEffectVelocity, &sEffectAccel, color, &sEffectEnvColor );
    }
    
}

void EnWonderItem_DropCollectible_Hack(EnWonderItem* this, z64_game_t* globalCtx, int32_t autoCollect)
{
    static int16_t dropTable[] = {
        ITEM00_NUTS,        ITEM00_HEART_PIECE,  ITEM00_MAGIC_LARGE,   ITEM00_MAGIC_SMALL,
        ITEM00_HEART,       ITEM00_ARROWS_SMALL, ITEM00_ARROWS_MEDIUM, ITEM00_ARROWS_LARGE,
        ITEM00_RUPEE_GREEN, ITEM00_RUPEE_BLUE,   ITEM00_RUPEE_RED,     ITEM00_FLEXIBLE,
    };
    int16_t i;
    int16_t randomDrop;

    // Override behavior. Spawn an overridden collectible on link
    if(this->overridden)
    {
        drop_collectible_override_flag = this->actor.rot_init.y;
        z64_Item_DropCollectible2(globalCtx, &(z64_link.common.pos_world), dropTable[this->itemDrop]);
        drop_collectible_override_flag = 0;
        z64_ActorKill(&this->actor);
        return;
    }

    // Not overridden so use vanilla behavior
    z64_PlaySFXID(NA_SE_SY_GET_ITEM);

    if (this->dropCount == 0) {
        this->dropCount++;
    }
    for (i = this->dropCount; i > 0; i--) {
        if (this->itemDrop < WONDERITEM_DROP_RANDOM) {
            if ((this->itemDrop == WONDERITEM_DROP_FLEXIBLE) || !autoCollect) {
                z64_Item_DropCollectible(globalCtx, &this->actor.pos_world, dropTable[this->itemDrop]);
            } else {
                drop_collectible_override_flag = this->actor.rot_init.y;
                z64_Item_DropCollectible(globalCtx, &this->actor.pos_world, dropTable[this->itemDrop] | 0x8000);
                drop_collectible_override_flag = 0;
            }
        } else {
            randomDrop = this->itemDrop - WONDERITEM_DROP_RANDOM;
            if (!autoCollect) {
                //Item_DropCollectibleRandom(globalCtx, NULL, &this->actor.world.pos, randomDrop);
            } else {
                //Item_DropCollectibleRandom(globalCtx, NULL, &this->actor.world.pos, randomDrop | 0x8000);
            }
        }
    }
    if (this->switchFlag >= 0) {
        z64_Flags_SetSwitch(globalCtx, this->switchFlag);
    }
    z64_ActorKill(&this->actor);
}

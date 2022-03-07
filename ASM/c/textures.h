#ifndef TEXTURES_H
#define TEXTURES_H

#include "z64.h"
#include "util.h"

#define TEXTURE_ID_NONE             0
#define TEXTURE_ID_POT_GOLD         1
#define TEXTURE_ID_POT_KEY          2
#define TEXTURE_ID_POT_BOSSKEY      3
#define TEXTURE_ID_POT_SKULL        4

#define TEXTURE_ID_CRATE_TOP_DEFAULT    5
#define TEXTURE_ID_CRATE_TOP_GOLD       6
#define TEXTURE_ID_CRATE_TOP_KEY        7
#define TEXTURE_ID_CRATE_TOP_BOSSKEY    8
#define TEXTURE_ID_CRATE_TOP_SKULL      9
#define TEXTURE_ID_CRATE_SIDE_DEFAULT 10
#define TEXTURE_ID_CRATE_SIDE_GOLD 11
#define TEXTURE_ID_CRATE_SIDE_KEY 12
#define TEXTURE_ID_CRATE_SIDE_BOSSKEY 13
#define TEXTURE_ID_CRATE_SIDE_SKULL 14
#define TEXTURE_ID_CRATE_PALETTE_DEFAULT 15
#define TEXTURE_ID_CRATE_PALETTE_GOLD 16
#define TEXTURE_ID_CRATE_PALETTE_SILVER 17
#define TEXTURE_ID_CRATE_PALETTE_BOSSKEY 18
#define TEXTURE_ID_CRATE_PALETTE_SKULL 19

uint8_t* get_texture(uint16_t textureID);
void init_textures();

#endif
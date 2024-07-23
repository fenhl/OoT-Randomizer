#include "gfx.h"

#include "debug.h"
#include "util.h"
#include "z64.h"

extern uint8_t FONT_RESOURCE[];
extern uint8_t DPAD_RESOURCE[];
extern uint8_t TRIFORCE_SPRITE_RESOURCE[];

z64_disp_buf_t* rando_db __attribute__ ((aligned (16)));
const unsigned int RANDO_DB_SIZE = 0x5000;

#if DEBUG_MODE
z64_disp_buf_t* debug_db __attribute__ ((aligned (16)));
const unsigned int DEBUG_DB_SIZE = 0x2000;
#endif

Gfx setup_db[] = {
    gsDPPipeSync(),

    gsSPLoadGeometryMode(0),
    gsDPSetScissor(G_SC_NON_INTERLACE,
                  0, 0, Z64_SCREEN_WIDTH, Z64_SCREEN_HEIGHT),

    gsDPSetOtherMode(G_AD_DISABLE | G_CD_DISABLE |
        G_CK_NONE | G_TC_FILT |
        G_TD_CLAMP | G_TP_NONE |
        G_TL_TILE | G_TT_NONE |
        G_PM_NPRIMITIVE | G_CYC_1CYCLE |
        G_TF_BILERP, // HI
        G_AC_NONE | G_ZS_PRIM |
        G_RM_XLU_SURF | G_RM_XLU_SURF2), // LO

    gsSPEndDisplayList()
};

Gfx empty_dlist[] = { gsSPEndDisplayList() };

sprite_t stones_sprite = {
    NULL, 16, 16, 3,
    G_IM_FMT_RGBA, G_IM_SIZ_32b, 4
};

sprite_t medals_sprite = {
    NULL, 16, 16, 6,
    G_IM_FMT_IA, G_IM_SIZ_8b, 1
};

sprite_t items_sprite = {
    NULL, 32, 32, 90,
    G_IM_FMT_RGBA, G_IM_SIZ_32b, 4
};

sprite_t quest_items_sprite = {
    NULL, 24, 24, 20,
    G_IM_FMT_RGBA, G_IM_SIZ_32b, 4
};

sprite_t font_sprite = {
    NULL, 8, 14, 95,
    G_IM_FMT_IA, G_IM_SIZ_8b, 1
};

sprite_t dpad_sprite = {
    NULL, 32, 32, 1,
    G_IM_FMT_IA, G_IM_SIZ_16b, 2
};

sprite_t triforce_sprite = {
    NULL, 16, 16, 16,
    G_IM_FMT_IA, G_IM_SIZ_8b, 1
};

sprite_t song_note_sprite = {
    NULL, 16, 24, 1,
    G_IM_FMT_IA, G_IM_SIZ_8b, 1
};
sprite_t key_rupee_clock_sprite = {
    NULL, 16, 16, 3,
    G_IM_FMT_IA, G_IM_SIZ_8b, 1
};

sprite_t rupee_digit_sprite = {
    NULL, 8, 16, 10,
    G_IM_FMT_I, G_IM_SIZ_8b, 1
};

sprite_t item_digit_sprite = {
    NULL, 8, 8, 10,
    G_IM_FMT_IA, G_IM_SIZ_8b, 1
};

sprite_t linkhead_skull_sprite = {
    NULL, 16, 16, 2,
    G_IM_FMT_RGBA, G_IM_SIZ_16b, 2
};

sprite_t heart_sprite = {
    NULL, 16, 16, 10,
    G_IM_FMT_IA, G_IM_SIZ_8b, 1
};

sprite_t ocarina_button_sprite = {
    NULL, 16, 16, 5,
    G_IM_FMT_IA, G_IM_SIZ_8b, 1
};

sprite_t buttons_sprite = {
    NULL, 16, 16, 10,
    G_IM_FMT_I, G_IM_SIZ_4b, 1
};


int sprite_bytes_per_tile(sprite_t* sprite) {
    if (sprite->im_siz == G_IM_SIZ_4b) {
        // this format is nibble based, so 4bits = half a byte
        return sprite->tile_w * sprite->tile_h * sprite->bytes_per_texel / 2;
    }
    return sprite->tile_w * sprite->tile_h * sprite->bytes_per_texel;
}

int sprite_bytes(sprite_t* sprite) {
    return sprite->tile_count * sprite_bytes_per_tile(sprite);
}

void sprite_load(z64_disp_buf_t* db, sprite_t* sprite,
        int start_tile, int tile_count) {
    int width = sprite->tile_w;
    int height = sprite->tile_h * tile_count;
    if (sprite->im_siz == G_IM_SIZ_4b) {
        gDPLoadTextureTile_4b(db->p++,
            sprite->buf + start_tile * sprite_bytes_per_tile(sprite),
            sprite->im_fmt,
            width, height,
            0, 0,
            width - 1, height - 1,
            0,
            G_TX_WRAP, G_TX_WRAP,
            G_TX_NOMASK, G_TX_NOMASK,
            G_TX_NOLOD, G_TX_NOLOD);
    }
    else {
        gDPLoadTextureTile(db->p++,
            sprite->buf + start_tile * sprite_bytes_per_tile(sprite),
            sprite->im_fmt, sprite->im_siz,
            width, height,
            0, 0,
            width - 1, height - 1,
            0,
            G_TX_WRAP, G_TX_WRAP,
            G_TX_NOMASK, G_TX_NOMASK,
            G_TX_NOLOD, G_TX_NOLOD);
    }
}

void sprite_texture(z64_disp_buf_t* db, sprite_t* sprite, int tile_index, int16_t left, int16_t top,
        int16_t width, int16_t height) {
    int width_factor = (1<<10) * sprite->tile_w / width;
    int height_factor = (1<<10) * sprite->tile_h / height;
    gDPLoadTextureBlock(db->p++,
        ((uint8_t*)(sprite->buf)) + (tile_index * sprite_bytes_per_tile(sprite)),
        sprite->im_fmt,
        sprite->im_siz,
        sprite->tile_w,
        sprite->tile_h,
        0,
        G_TX_NOMIRROR | G_TX_WRAP,
        G_TX_NOMIRROR | G_TX_WRAP,
        G_TX_NOMASK,
        G_TX_NOMASK,
        G_TX_NOLOD,
        G_TX_NOLOD
    );

    gSPTextureRectangle(db->p++, left * 4, top * 4, (left + width) * 4, (top + height) * 4, G_TX_RENDERTILE, 0,0,width_factor, height_factor);
}

void sprite_texture_4b(z64_disp_buf_t *db, sprite_t *sprite, int tile_index, int16_t left, int16_t top,
                        int16_t width, int16_t height) {

    if (sprite->im_siz != G_IM_SIZ_4b) {
        return;
    }

    int width_factor = (1<<10) * sprite->tile_w / width;
    int height_factor = (1<<10) * sprite->tile_h / height;

    gDPPipeSync(db->p++);
    gDPSetCombineLERP(db->p++, PRIMITIVE, ENVIRONMENT, TEXEL0, ENVIRONMENT, TEXEL0, 0, PRIMITIVE, 0, PRIMITIVE,
        ENVIRONMENT, TEXEL0, ENVIRONMENT, TEXEL0, 0, PRIMITIVE, 0);

    gDPSetEnvColor(db->p++, 0, 0, 0, 255);

    gDPLoadTextureBlock_4b(db->p++,
        ((uint8_t*)(sprite->buf)) + tile_index * sprite_bytes_per_tile(sprite),
        sprite->im_fmt,
        sprite->tile_w,
        sprite->tile_h,
        0,
        G_TX_NOMIRROR | G_TX_CLAMP,
        G_TX_NOMIRROR | G_TX_CLAMP,
        G_TX_NOMASK,
        G_TX_NOMASK,
        G_TX_NOLOD,
        G_TX_NOLOD
    );

    gSPTextureRectangle(db->p++, left * 4, top * 4, (left + width) * 4,
        (top + height) * 4, G_TX_RENDERTILE, 0, 0, width_factor, height_factor);
}

void sprite_draw(z64_disp_buf_t* db, sprite_t* sprite, int tile_index,
        int left, int top, int width, int height) {
    int width_factor = (1<<10) * sprite->tile_w / width;
    int height_factor = (1<<10) * sprite->tile_h / height;

    gSPTextureRectangle(db->p++,
            left<<2, top<<2,
            (left + width)<<2, (top + height)<<2,
            0,
            0, (tile_index * sprite->tile_h)<<5,
            width_factor, height_factor);
}

void rando_display_buffer_init() {
#if DEBUG_MODE
    debug_db = heap_alloc(sizeof(z64_disp_buf_t));
    debug_db->size = DEBUG_DB_SIZE;
    debug_db->buf = heap_alloc(DEBUG_DB_SIZE);
    debug_db->p = &debug_db->buf[0];
#endif
    rando_db = heap_alloc(sizeof(z64_disp_buf_t));
    rando_db->size = RANDO_DB_SIZE;
    rando_db->buf = heap_alloc(RANDO_DB_SIZE);
    rando_db->p = &rando_db->buf[0];
}

void gfx_init() {
    file_t title_static = {
        NULL, z64_file_select_static_vaddr, z64_file_select_static_vsize
    };
    file_init(&title_static);

    file_t icon_item_24_static = {
        NULL, z64_icon_item_24_static_vaddr, z64_icon_item_24_static_vsize
    };
    file_init(&icon_item_24_static);

    file_t icon_item_static = {
        NULL, z64_icon_item_static_vaddr, z64_icon_item_static_vsize
    };
    file_init(&icon_item_static);

    file_t parameter_static = {
        NULL, z64_parameter_static_vaddr, z64_parameter_static_vsize
    };
    file_init(&parameter_static);

    file_t icon_item_dungeon_static = {
        NULL, z64_icon_item_dungeon_static_vaddr, z64_icon_item_dungeon_static_vsize
    };
    file_init(&icon_item_dungeon_static);

    file_t nes_font_static = {
        NULL, z64_nes_font_static_vaddr, z64_nes_font_static_vsize
    };
    file_init(&nes_font_static);

    stones_sprite.buf = title_static.buf + 0x2A300;
    medals_sprite.buf = title_static.buf + 0x2980;
    items_sprite.buf = icon_item_static.buf;
    quest_items_sprite.buf = icon_item_24_static.buf;
    dpad_sprite.buf = DPAD_RESOURCE;
    triforce_sprite.buf = TRIFORCE_SPRITE_RESOURCE;
    song_note_sprite.buf = icon_item_static.buf + 0x00088040;
    key_rupee_clock_sprite.buf = parameter_static.buf + 0x00001E00;
    rupee_digit_sprite.buf = parameter_static.buf + 0x3040;
    item_digit_sprite.buf = parameter_static.buf + 0x000035C0;
    linkhead_skull_sprite.buf = icon_item_dungeon_static.buf + 0x00001980;
    heart_sprite.buf = parameter_static.buf;
    ocarina_button_sprite.buf = parameter_static.buf + 0x2940;
    buttons_sprite.buf = nes_font_static.buf + 0x3F80;

    int font_bytes = sprite_bytes(&font_sprite);
    font_sprite.buf = heap_alloc(font_bytes);
    for (int i = 0; i < font_bytes / 2; i++) {
        font_sprite.buf[2*i] = (FONT_RESOURCE[i] >> 4) | 0xF0;
        font_sprite.buf[2*i + 1] = FONT_RESOURCE[i] | 0xF0;
    }

    rando_display_buffer_init();
}

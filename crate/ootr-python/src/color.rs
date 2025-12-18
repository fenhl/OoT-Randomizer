use {
    std::iter,
    indexmap::{
        IndexMap,
        indexmap,
    },
    lazy_regex::regex_is_match,
    pyo3::{
        exceptions::*,
        intern,
        prelude::*,
    },
};

#[pyclass(frozen)]
#[derive(Clone, Copy)]
struct Color {
    r: u8,
    g: u8,
    b: u8,
}

#[pymethods]
impl Color {
    #[new]
    fn new(r: u8, g: u8, b: u8) -> Self {
        Self { r, g, b }
    }

    fn bytes(&self) -> [u8; 3] {
        [self.r, self.g, self.b]
    }
}

fn tunic_colors() -> IndexMap<&'static str, Color> {
    indexmap![
        "Kokiri Green"  => Color { r: 0x1E, g: 0x69, b: 0x1B },
        "Goron Red"     => Color { r: 0x64, g: 0x14, b: 0x00 },
        "Zora Blue"     => Color { r: 0x00, g: 0x3C, b: 0x64 },
        "Black"         => Color { r: 0x30, g: 0x30, b: 0x30 },
        "White"         => Color { r: 0xF0, g: 0xF0, b: 0xFF },
        "Azure Blue"    => Color { r: 0x13, g: 0x9E, b: 0xD8 },
        "Vivid Cyan"    => Color { r: 0x13, g: 0xE9, b: 0xD8 },
        "Light Red"     => Color { r: 0xF8, g: 0x7C, b: 0x6D },
        "Fuchsia"       => Color { r: 0xFF, g: 0x00, b: 0xFF },
        "Purple"        => Color { r: 0x95, g: 0x30, b: 0x80 },
        "Majora Purple" => Color { r: 0x40, g: 0x00, b: 0x40 },
        "Twitch Purple" => Color { r: 0x64, g: 0x41, b: 0xA5 },
        "Purple Heart"  => Color { r: 0x8A, g: 0x2B, b: 0xE2 },
        "Persian Rose"  => Color { r: 0xFF, g: 0x14, b: 0x93 },
        "Dirty Yellow"  => Color { r: 0xE0, g: 0xD8, b: 0x60 },
        "Blush Pink"    => Color { r: 0xF8, g: 0x6C, b: 0xF8 },
        "Hot Pink"      => Color { r: 0xFF, g: 0x69, b: 0xB4 },
        "Rose Pink"     => Color { r: 0xFF, g: 0x90, b: 0xB3 },
        "Orange"        => Color { r: 0xE0, g: 0x79, b: 0x40 },
        "Gray"          => Color { r: 0xA0, g: 0xA0, b: 0xB0 },
        "Gold"          => Color { r: 0xD8, g: 0xB0, b: 0x60 },
        "Silver"        => Color { r: 0xD0, g: 0xF0, b: 0xFF },
        "Beige"         => Color { r: 0xC0, g: 0xA0, b: 0xA0 },
        "Teal"          => Color { r: 0x30, g: 0xD0, b: 0xB0 },
        "Blood Red"     => Color { r: 0x83, g: 0x03, b: 0x03 },
        "Blood Orange"  => Color { r: 0xFE, g: 0x4B, b: 0x03 },
        "Royal Blue"    => Color { r: 0x40, g: 0x00, b: 0x90 },
        "Sonic Blue"    => Color { r: 0x50, g: 0x90, b: 0xE0 },
        "NES Green"     => Color { r: 0x00, g: 0xD0, b: 0x00 },
        "Dark Green"    => Color { r: 0x00, g: 0x25, b: 0x18 },
        "Lumen"         => Color { r: 0x50, g: 0x8C, b: 0xF0 },
    ]
}

fn navi_colors() -> IndexMap<&'static str, (Color, Color)> {
    indexmap![
        //                      Inner Core Color                     Outer Glow Color
        "Rainbow"           => (Color { r: 0x00, g: 0x00, b: 0x00 }, Color { r: 0x00, g: 0x00, b: 0x00 }),
        "Gold"              => (Color { r: 0xFE, g: 0xCC, b: 0x3C }, Color { r: 0xFE, g: 0xC0, b: 0x07 }),
        "White"             => (Color { r: 0xFF, g: 0xFF, b: 0xFF }, Color { r: 0x00, g: 0x00, b: 0xFF }),
        "Green"             => (Color { r: 0x00, g: 0xFF, b: 0x00 }, Color { r: 0x00, g: 0xFF, b: 0x00 }),
        "Light Blue"        => (Color { r: 0x96, g: 0x96, b: 0xFF }, Color { r: 0x96, g: 0x96, b: 0xFF }),
        "Yellow"            => (Color { r: 0xFF, g: 0xFF, b: 0x00 }, Color { r: 0xC8, g: 0x9B, b: 0x00 }),
        "Red"               => (Color { r: 0xFF, g: 0x00, b: 0x00 }, Color { r: 0xFF, g: 0x00, b: 0x00 }),
        "Magenta"           => (Color { r: 0xFF, g: 0x00, b: 0xFF }, Color { r: 0xC8, g: 0x00, b: 0x9B }),
        "Black"             => (Color { r: 0x00, g: 0x00, b: 0x00 }, Color { r: 0x00, g: 0x00, b: 0x00 }),
        "Tatl"              => (Color { r: 0xFF, g: 0xFF, b: 0xFF }, Color { r: 0xC8, g: 0x98, b: 0x00 }),
        "Tael"              => (Color { r: 0x49, g: 0x14, b: 0x6C }, Color { r: 0xFF, g: 0x00, b: 0x00 }),
        "Fi"                => (Color { r: 0x2C, g: 0x9E, b: 0xC4 }, Color { r: 0x2C, g: 0x19, b: 0x83 }),
        "Ciela"             => (Color { r: 0xE6, g: 0xDE, b: 0x83 }, Color { r: 0xC6, g: 0xBE, b: 0x5B }),
        "Epona"             => (Color { r: 0xD1, g: 0x49, b: 0x02 }, Color { r: 0x55, g: 0x1F, b: 0x08 }),
        "Ezlo"              => (Color { r: 0x62, g: 0x9C, b: 0x5F }, Color { r: 0x3F, g: 0x5D, b: 0x37 }),
        "King of Red Lions" => (Color { r: 0xA8, g: 0x33, b: 0x17 }, Color { r: 0xDE, g: 0xD7, b: 0xC5 }),
        "Linebeck"          => (Color { r: 0x03, g: 0x26, b: 0x60 }, Color { r: 0xEF, g: 0xFF, b: 0xFF }),
        "Loftwing"          => (Color { r: 0xD6, g: 0x2E, b: 0x31 }, Color { r: 0xFD, g: 0xE6, b: 0xCC }),
        "Midna"             => (Color { r: 0x19, g: 0x24, b: 0x26 }, Color { r: 0xD2, g: 0x83, b: 0x30 }),
        "Phantom Zelda"     => (Color { r: 0x97, g: 0x7A, b: 0x6C }, Color { r: 0x6F, g: 0x46, b: 0x67 }),
    ]
}

fn sword_trail_colors() -> IndexMap<&'static str, Color> {
    indexmap![
        "Rainbow" => Color { r: 0x00, g: 0x00, b: 0x00 },
        "White"   => Color { r: 0xFF, g: 0xFF, b: 0xFF },
        "Red"     => Color { r: 0xFF, g: 0x00, b: 0x00 },
        "Green"   => Color { r: 0x00, g: 0xFF, b: 0x00 },
        "Blue"    => Color { r: 0x00, g: 0x00, b: 0xFF },
        "Cyan"    => Color { r: 0x00, g: 0xFF, b: 0xFF },
        "Magenta" => Color { r: 0xFF, g: 0x00, b: 0xFF },
        "Orange"  => Color { r: 0xFF, g: 0xA5, b: 0x00 },
        "Gold"    => Color { r: 0xFF, g: 0xD7, b: 0x00 },
        "Purple"  => Color { r: 0x80, g: 0x00, b: 0x80 },
        "Pink"    => Color { r: 0xFF, g: 0x69, b: 0xB4 },
    ]
}

fn bombchu_trail_colors() -> IndexMap<&'static str, Color> {
    indexmap![
        "Rainbow" => Color { r: 0x00, g: 0x00, b: 0x00 },
        "Red"     => Color { r: 0xFA, g: 0x00, b: 0x00 },
        "Green"   => Color { r: 0x00, g: 0xFF, b: 0x00 },
        "Blue"    => Color { r: 0x00, g: 0x00, b: 0xFF },
        "Cyan"    => Color { r: 0x00, g: 0xFF, b: 0xFF },
        "Magenta" => Color { r: 0xFF, g: 0x00, b: 0xFF },
        "Orange"  => Color { r: 0xFF, g: 0xA5, b: 0x00 },
        "Gold"    => Color { r: 0xFF, g: 0xD7, b: 0x00 },
        "Purple"  => Color { r: 0x80, g: 0x00, b: 0x80 },
        "Pink"    => Color { r: 0xFF, g: 0x69, b: 0xB4 },
    ]
}

fn boomerang_trail_colors() -> IndexMap<&'static str, Color> {
    indexmap![
        "Rainbow" => Color { r: 0x00, g: 0x00, b: 0x00 },
        "Yellow"  => Color { r: 0xFF, g: 0xFF, b: 0x64 },
        "Red"     => Color { r: 0xFF, g: 0x00, b: 0x00 },
        "Green"   => Color { r: 0x00, g: 0xFF, b: 0x00 },
        "Blue"    => Color { r: 0x00, g: 0x00, b: 0xFF },
        "Cyan"    => Color { r: 0x00, g: 0xFF, b: 0xFF },
        "Magenta" => Color { r: 0xFF, g: 0x00, b: 0xFF },
        "Orange"  => Color { r: 0xFF, g: 0xA5, b: 0x00 },
        "Gold"    => Color { r: 0xFF, g: 0xD7, b: 0x00 },
        "Purple"  => Color { r: 0x80, g: 0x00, b: 0x80 },
        "Pink"    => Color { r: 0xFF, g: 0x69, b: 0xB4 },
    ]
}

fn gauntlet_colors() -> IndexMap<&'static str, Color> {
    indexmap![
        "Silver"   => Color { r: 0xFF, g: 0xFF, b: 0xFF },
        "Gold"     => Color { r: 0xFE, g: 0xCF, b: 0x0F },
        "Black"    => Color { r: 0x00, g: 0x00, b: 0x06 },
        "Green"    => Color { r: 0x02, g: 0x59, b: 0x18 },
        "Blue"     => Color { r: 0x06, g: 0x02, b: 0x5A },
        "Bronze"   => Color { r: 0x60, g: 0x06, b: 0x02 },
        "Red"      => Color { r: 0xFF, g: 0x00, b: 0x00 },
        "Sky Blue" => Color { r: 0x02, g: 0x5D, b: 0xB0 },
        "Pink"     => Color { r: 0xFA, g: 0x6A, b: 0x90 },
        "Magenta"  => Color { r: 0xFF, g: 0x00, b: 0xFF },
        "Orange"   => Color { r: 0xDA, g: 0x38, b: 0x00 },
        "Lime"     => Color { r: 0x5B, g: 0xA8, b: 0x06 },
        "Purple"   => Color { r: 0x80, g: 0x00, b: 0x80 },
    ]
}

fn shield_frame_colors() -> IndexMap<&'static str, Color> {
    indexmap![
        "Red"     => Color { r: 0xD7, g: 0x00, b: 0x00 },
        "Green"   => Color { r: 0x00, g: 0xFF, b: 0x00 },
        "Blue"    => Color { r: 0x00, g: 0x40, b: 0xD8 },
        "Yellow"  => Color { r: 0xFF, g: 0xFF, b: 0x64 },
        "Cyan"    => Color { r: 0x00, g: 0xFF, b: 0xFF },
        "Magenta" => Color { r: 0xFF, g: 0x00, b: 0xFF },
        "Orange"  => Color { r: 0xFF, g: 0xA5, b: 0x00 },
        "Gold"    => Color { r: 0xFF, g: 0xD7, b: 0x00 },
        "Purple"  => Color { r: 0x80, g: 0x00, b: 0x80 },
        "Pink"    => Color { r: 0xFF, g: 0x69, b: 0xB4 },
    ]
}

fn heart_colors() -> IndexMap<&'static str, Color> {
    indexmap![
        "Red"    => Color { r: 0xFF, g: 0x46, b: 0x32 },
        "Green"  => Color { r: 0x46, g: 0xC8, b: 0x32 },
        "Blue"   => Color { r: 0x32, g: 0x46, b: 0xFF },
        "Yellow" => Color { r: 0xFF, g: 0xE0, b: 0x00 },
    ]
}

fn magic_colors() -> IndexMap<&'static str, Color> {
    indexmap![
        "Green"  => Color { r: 0x00, g: 0xC8, b: 0x00 },
        "Red"    => Color { r: 0xC8, g: 0x00, b: 0x00 },
        "Blue"   => Color { r: 0x00, g: 0x30, b: 0xFF },
        "Purple" => Color { r: 0xB0, g: 0x00, b: 0xFF },
        "Pink"   => Color { r: 0xFF, g: 0x00, b: 0xC8 },
        "Yellow" => Color { r: 0xFF, g: 0xFF, b: 0x00 },
        "White"  => Color { r: 0xFF, g: 0xFF, b: 0xFF },
    ]
}

/// A Button, Text Cursor, Shop Cursor, Save/Death Cursor, Pause Menu A Cursor, Pause Menu A Icon, A Note
fn a_button_colors() -> IndexMap<&'static str, (Color, Color, Color, Color, Color, Color, Color)> {
    indexmap![
        "N64 Blue" => (
            Color { r: 0x5A, g: 0x5A, b: 0xFF },
            Color { r: 0x00, g: 0x50, b: 0xC8 },
            Color { r: 0x00, g: 0x50, b: 0xFF },
            Color { r: 0x64, g: 0x64, b: 0xFF },
            Color { r: 0x00, g: 0x32, b: 0xFF },
            Color { r: 0x00, g: 0x64, b: 0xFF },
            Color { r: 0x50, g: 0x96, b: 0xFF },
        ),
        "N64 Green" => (
            Color { r: 0x00, g: 0x96, b: 0x00 },
            Color { r: 0x00, g: 0x96, b: 0x00 },
            Color { r: 0x00, g: 0x96, b: 0x00 },
            Color { r: 0x64, g: 0x96, b: 0x64 },
            Color { r: 0x00, g: 0x96, b: 0x00 },
            Color { r: 0x00, g: 0x96, b: 0x00 },
            Color { r: 0x00, g: 0x96, b: 0x00 },
        ),
        "N64 Red" => (
            Color { r: 0xC8, g: 0x00, b: 0x00 },
            Color { r: 0xC8, g: 0x00, b: 0x00 },
            Color { r: 0xC8, g: 0x00, b: 0x00 },
            Color { r: 0xC8, g: 0x64, b: 0x64 },
            Color { r: 0xC8, g: 0x00, b: 0x00 },
            Color { r: 0xC8, g: 0x00, b: 0x00 },
            Color { r: 0xC8, g: 0x00, b: 0x00 },
        ),
        "GameCube Green" => (
            Color { r: 0x00, g: 0xC8, b: 0x32 },
            Color { r: 0x00, g: 0xC8, b: 0x50 },
            Color { r: 0x00, g: 0xFF, b: 0x50 },
            Color { r: 0x64, g: 0xFF, b: 0x64 },
            Color { r: 0x00, g: 0xFF, b: 0x32 },
            Color { r: 0x00, g: 0xFF, b: 0x64 },
            Color { r: 0x50, g: 0xFF, b: 0x96 },
        ),
        "GameCube Red" => (
            Color { r: 0xFF, g: 0x1E, b: 0x1E },
            Color { r: 0xC8, g: 0x00, b: 0x00 },
            Color { r: 0xFF, g: 0x00, b: 0x50 },
            Color { r: 0xFF, g: 0x64, b: 0x64 },
            Color { r: 0xFF, g: 0x1E, b: 0x1E },
            Color { r: 0xFF, g: 0x1E, b: 0x1E },
            Color { r: 0xFF, g: 0x1E, b: 0x1E },
        ),
        "GameCube Grey" => (
            Color { r: 0x78, g: 0x78, b: 0x78 },
            Color { r: 0x78, g: 0x78, b: 0x78 },
            Color { r: 0x78, g: 0x78, b: 0x78 },
            Color { r: 0x78, g: 0x78, b: 0x78 },
            Color { r: 0x78, g: 0x78, b: 0x78 },
            Color { r: 0x78, g: 0x78, b: 0x78 },
            Color { r: 0x78, g: 0x78, b: 0x78 },
        ),
        "Yellow" => (
            Color { r: 0xFF, g: 0xA0, b: 0x00 },
            Color { r: 0xFF, g: 0xA0, b: 0x00 },
            Color { r: 0xFF, g: 0xA0, b: 0x00 },
            Color { r: 0xFF, g: 0xA0, b: 0x00 },
            Color { r: 0xFF, g: 0xFF, b: 0x00 },
            Color { r: 0xFF, g: 0x96, b: 0x00 },
            Color { r: 0xFF, g: 0xFF, b: 0x32 },
        ),
        "Black" => (
            Color { r: 0x10, g: 0x10, b: 0x10 },
            Color { r: 0x00, g: 0x00, b: 0x00 },
            Color { r: 0x00, g: 0x00, b: 0x00 },
            Color { r: 0x10, g: 0x10, b: 0x10 },
            Color { r: 0x00, g: 0x00, b: 0x00 },
            Color { r: 0x18, g: 0x18, b: 0x18 },
            Color { r: 0x18, g: 0x18, b: 0x18 },
        ),
        "White" => (
            Color { r: 0xFF, g: 0xFF, b: 0xFF },
            Color { r: 0xFF, g: 0xFF, b: 0xFF },
            Color { r: 0xFF, g: 0xFF, b: 0xFF },
            Color { r: 0xFF, g: 0xFF, b: 0xFF },
            Color { r: 0xFF, g: 0xFF, b: 0xFF },
            Color { r: 0xFF, g: 0xFF, b: 0xFF },
            Color { r: 0xFF, g: 0xFF, b: 0xFF },
        ),
        "Magenta" => (
            Color { r: 0xFF, g: 0x00, b: 0xFF },
            Color { r: 0xFF, g: 0x00, b: 0xFF },
            Color { r: 0xFF, g: 0x00, b: 0xFF },
            Color { r: 0xFF, g: 0x00, b: 0xFF },
            Color { r: 0xFF, g: 0x00, b: 0xFF },
            Color { r: 0xFF, g: 0x00, b: 0xFF },
            Color { r: 0xFF, g: 0x00, b: 0xFF },
        ),
        "Ruby" => (
            Color { r: 0xFF, g: 0x00, b: 0x00 },
            Color { r: 0xFF, g: 0x00, b: 0x00 },
            Color { r: 0xFF, g: 0x00, b: 0x00 },
            Color { r: 0xFF, g: 0x00, b: 0x00 },
            Color { r: 0xFF, g: 0x00, b: 0x00 },
            Color { r: 0xFF, g: 0x00, b: 0x00 },
            Color { r: 0xFF, g: 0x00, b: 0x00 },
        ),
        "Sapphire" => (
            Color { r: 0x00, g: 0x00, b: 0xFF },
            Color { r: 0x00, g: 0x00, b: 0xFF },
            Color { r: 0x00, g: 0x00, b: 0xFF },
            Color { r: 0x00, g: 0x00, b: 0xFF },
            Color { r: 0x00, g: 0x00, b: 0xFF },
            Color { r: 0x00, g: 0x00, b: 0xFF },
            Color { r: 0x00, g: 0x00, b: 0xFF },
        ),
        "Lime" => (
            Color { r: 0x00, g: 0xFF, b: 0x00 },
            Color { r: 0x00, g: 0xFF, b: 0x00 },
            Color { r: 0x00, g: 0xFF, b: 0x00 },
            Color { r: 0x00, g: 0xFF, b: 0x00 },
            Color { r: 0x00, g: 0xFF, b: 0x00 },
            Color { r: 0x00, g: 0xFF, b: 0x00 },
            Color { r: 0x00, g: 0xFF, b: 0x00 },
        ),
        "Cyan" => (
            Color { r: 0x00, g: 0xFF, b: 0xFF },
            Color { r: 0x00, g: 0xFF, b: 0xFF },
            Color { r: 0x00, g: 0xFF, b: 0xFF },
            Color { r: 0x00, g: 0xFF, b: 0xFF },
            Color { r: 0x00, g: 0xFF, b: 0xFF },
            Color { r: 0x00, g: 0xFF, b: 0xFF },
            Color { r: 0x00, g: 0xFF, b: 0xFF },
        ),
        "Purple" => (
            Color { r: 0x80, g: 0x00, b: 0x80 },
            Color { r: 0x80, g: 0x00, b: 0x80 },
            Color { r: 0x80, g: 0x00, b: 0x80 },
            Color { r: 0x80, g: 0x00, b: 0x80 },
            Color { r: 0x80, g: 0x00, b: 0x80 },
            Color { r: 0x80, g: 0x00, b: 0x80 },
            Color { r: 0x80, g: 0x00, b: 0x80 },
        ),
        "Orange" => (
            Color { r: 0xFF, g: 0x80, b: 0x00 },
            Color { r: 0xFF, g: 0x80, b: 0x00 },
            Color { r: 0xFF, g: 0x80, b: 0x00 },
            Color { r: 0xFF, g: 0x80, b: 0x00 },
            Color { r: 0xFF, g: 0x80, b: 0x00 },
            Color { r: 0xFF, g: 0x80, b: 0x00 },
            Color { r: 0xFF, g: 0x80, b: 0x00 },
        ),
    ]
}

fn b_button_colors() -> IndexMap<&'static str, Color> {
    indexmap![
        "N64 Blue"       => Color { r: 0x5A, g: 0x5A, b: 0xFF },
        "N64 Green"      => Color { r: 0x00, g: 0x96, b: 0x00 },
        "N64 Red"        => Color { r: 0xC8, g: 0x00, b: 0x00 },
        "GameCube Green" => Color { r: 0x00, g: 0xC8, b: 0x32 },
        "GameCube Red"   => Color { r: 0xFF, g: 0x1E, b: 0x1E },
        "GameCube Grey"  => Color { r: 0x78, g: 0x78, b: 0x78 },
        "Yellow"         => Color { r: 0xFF, g: 0xA0, b: 0x00 },
        "Black"          => Color { r: 0x10, g: 0x10, b: 0x10 },
        "White"          => Color { r: 0xFF, g: 0xFF, b: 0xFF },
        "Magenta"        => Color { r: 0xFF, g: 0x00, b: 0xFF },
        "Ruby"           => Color { r: 0xFF, g: 0x00, b: 0x00 },
        "Sapphire"       => Color { r: 0x00, g: 0x00, b: 0xFF },
        "Lime"           => Color { r: 0x00, g: 0xFF, b: 0x00 },
        "Cyan"           => Color { r: 0x00, g: 0xFF, b: 0xFF },
        "Purple"         => Color { r: 0x80, g: 0x00, b: 0x80 },
        "Orange"         => Color { r: 0xFF, g: 0x80, b: 0x00 },
    ]
}

/// C Button, Pause Menu C Cursor, Pause Menu C Icon, C Note
fn c_button_colors() -> IndexMap<&'static str, (Color, Color, Color, Color)> {
    indexmap![
        "N64 Blue" => (
            Color { r: 0x5A, g: 0x5A, b: 0xFF },
            Color { r: 0x00, g: 0x32, b: 0xFF },
            Color { r: 0x00, g: 0x64, b: 0xFF },
            Color { r: 0x50, g: 0x96, b: 0xFF },
        ),
        "N64 Green" => (
            Color { r: 0x00, g: 0x96, b: 0x00 },
            Color { r: 0x00, g: 0x96, b: 0x00 },
            Color { r: 0x00, g: 0x96, b: 0x00 },
            Color { r: 0x00, g: 0x96, b: 0x00 },
        ),
        "N64 Red" => (
            Color { r: 0xC8, g: 0x00, b: 0x00 },
            Color { r: 0xC8, g: 0x00, b: 0x00 },
            Color { r: 0xC8, g: 0x00, b: 0x00 },
            Color { r: 0xC8, g: 0x00, b: 0x00 },
        ),
        "GameCube Green" => (
            Color { r: 0x00, g: 0xC8, b: 0x32 },
            Color { r: 0x00, g: 0xFF, b: 0x32 },
            Color { r: 0x00, g: 0xFF, b: 0x64 },
            Color { r: 0x50, g: 0xFF, b: 0x96 },
        ),
        "GameCube Red" => (
            Color { r: 0xFF, g: 0x1E, b: 0x1E },
            Color { r: 0xFF, g: 0x1E, b: 0x1E },
            Color { r: 0xFF, g: 0x1E, b: 0x1E },
            Color { r: 0xFF, g: 0x1E, b: 0x1E },
        ),
        "GameCube Grey" => (
            Color { r: 0x78, g: 0x78, b: 0x78 },
            Color { r: 0x78, g: 0x78, b: 0x78 },
            Color { r: 0x78, g: 0x78, b: 0x78 },
            Color { r: 0x78, g: 0x78, b: 0x78 },
        ),
        "Yellow" => (
            Color { r: 0xFF, g: 0xA0, b: 0x00 },
            Color { r: 0xFF, g: 0xFF, b: 0x00 },
            Color { r: 0xFF, g: 0x96, b: 0x00 },
            Color { r: 0xFF, g: 0xFF, b: 0x32 },
        ),
        "Black" => (
            Color { r: 0x10, g: 0x10, b: 0x10 },
            Color { r: 0x00, g: 0x00, b: 0x00 },
            Color { r: 0x18, g: 0x18, b: 0x18 },
            Color { r: 0x18, g: 0x18, b: 0x18 },
        ),
        "White" => (
            Color { r: 0xFF, g: 0xFF, b: 0xFF },
            Color { r: 0xFF, g: 0xFF, b: 0xFF },
            Color { r: 0xFF, g: 0xFF, b: 0xFF },
            Color { r: 0xFF, g: 0xFF, b: 0xFF },
        ),
        "Magenta" => (
            Color { r: 0xFF, g: 0x00, b: 0xFF },
            Color { r: 0xFF, g: 0x00, b: 0xFF },
            Color { r: 0xFF, g: 0x00, b: 0xFF },
            Color { r: 0xFF, g: 0x00, b: 0xFF },
        ),
        "Ruby" => (
            Color { r: 0xFF, g: 0x00, b: 0x00 },
            Color { r: 0xFF, g: 0x00, b: 0x00 },
            Color { r: 0xFF, g: 0x00, b: 0x00 },
            Color { r: 0xFF, g: 0x00, b: 0x00 },
        ),
        "Sapphire" => (
            Color { r: 0x00, g: 0x00, b: 0xFF },
            Color { r: 0x00, g: 0x00, b: 0xFF },
            Color { r: 0x00, g: 0x00, b: 0xFF },
            Color { r: 0x00, g: 0x00, b: 0xFF },
        ),
        "Lime" => (
            Color { r: 0x00, g: 0xFF, b: 0x00 },
            Color { r: 0x00, g: 0xFF, b: 0x00 },
            Color { r: 0x00, g: 0xFF, b: 0x00 },
            Color { r: 0x00, g: 0xFF, b: 0x00 },
        ),
        "Cyan" => (
            Color { r: 0x00, g: 0xFF, b: 0xFF },
            Color { r: 0x00, g: 0xFF, b: 0xFF },
            Color { r: 0x00, g: 0xFF, b: 0xFF },
            Color { r: 0x00, g: 0xFF, b: 0xFF },
        ),
        "Purple" => (
            Color { r: 0x80, g: 0x00, b: 0x80 },
            Color { r: 0x80, g: 0x00, b: 0x80 },
            Color { r: 0x80, g: 0x00, b: 0x80 },
            Color { r: 0x80, g: 0x00, b: 0x80 },
        ),
        "Orange" => (
            Color { r: 0xFF, g: 0x80, b: 0x00 },
            Color { r: 0xFF, g: 0x80, b: 0x00 },
            Color { r: 0xFF, g: 0x80, b: 0x00 },
            Color { r: 0xFF, g: 0x80, b: 0x00 },
        ),
    ]
}

fn start_button_colors() -> IndexMap<&'static str, Color> {
    indexmap![
        "N64 Blue"       => Color { r: 0x5A, g: 0x5A, b: 0xFF },
        "N64 Green"      => Color { r: 0x00, g: 0x96, b: 0x00 },
        "N64 Red"        => Color { r: 0xC8, g: 0x00, b: 0x00 },
        "GameCube Green" => Color { r: 0x00, g: 0xC8, b: 0x32 },
        "GameCube Red"   => Color { r: 0xFF, g: 0x1E, b: 0x1E },
        "GameCube Grey"  => Color { r: 0x78, g: 0x78, b: 0x78 },
        "Yellow"         => Color { r: 0xFF, g: 0xA0, b: 0x00 },
        "Black"          => Color { r: 0x10, g: 0x10, b: 0x10 },
        "White"          => Color { r: 0xFF, g: 0xFF, b: 0xFF },
        "Magenta"        => Color { r: 0xFF, g: 0x00, b: 0xFF },
        "Ruby"           => Color { r: 0xFF, g: 0x00, b: 0x00 },
        "Sapphire"       => Color { r: 0x00, g: 0x00, b: 0xFF },
        "Lime"           => Color { r: 0x00, g: 0xFF, b: 0x00 },
        "Cyan"           => Color { r: 0x00, g: 0xFF, b: 0xFF },
        "Purple"         => Color { r: 0x80, g: 0x00, b: 0x80 },
        "Orange"         => Color { r: 0xFF, g: 0x80, b: 0x00 },
    ]
}

const META_COLOR_CHOICES: [&str; 3] = ["Random Choice", "Completely Random", "Custom Color"];

#[pyfunction]
fn get_tunic_colors() -> Vec<&'static str> {
    tunic_colors().into_keys().collect()
}

#[pyfunction]
fn get_tunic_color_options() -> Vec<&'static str> {
    META_COLOR_CHOICES.into_iter()
        .chain(iter::once("Rainbow"))
        .chain(get_tunic_colors())
        .collect()
}

#[pyfunction]
fn get_navi_colors() -> Vec<&'static str> {
    navi_colors().into_keys().collect()
}

#[pyfunction]
#[pyo3(signature = (outer = false))]
fn get_navi_color_options(outer: bool) -> Vec<&'static str> {
    if outer {
        iter::once("[Same as Inner]").chain(META_COLOR_CHOICES).chain(get_navi_colors()).collect()
    } else {
        META_COLOR_CHOICES.into_iter().chain(get_navi_colors()).collect()
    }
}

#[pyfunction]
fn get_sword_trail_colors() -> Vec<&'static str> {
    sword_trail_colors().into_keys().collect()
}

#[pyfunction]
#[pyo3(signature = (outer = false))]
fn get_sword_trail_color_options(outer: bool) -> Vec<&'static str> {
    if outer {
        iter::once("[Same as Inner]").chain(META_COLOR_CHOICES).chain(get_sword_trail_colors()).collect()
    } else {
        META_COLOR_CHOICES.into_iter().chain(get_sword_trail_colors()).collect()
    }
}

#[pyfunction]
fn get_bombchu_trail_colors() -> Vec<&'static str> {
    bombchu_trail_colors().into_keys().collect()
}

#[pyfunction]
#[pyo3(signature = (outer = false))]
fn get_bombchu_trail_color_options(outer: bool) -> Vec<&'static str> {
    if outer {
        iter::once("[Same as Inner]").chain(META_COLOR_CHOICES).chain(get_bombchu_trail_colors()).collect()
    } else {
        META_COLOR_CHOICES.into_iter().chain(get_bombchu_trail_colors()).collect()
    }
}

#[pyfunction]
fn get_boomerang_trail_colors() -> Vec<&'static str> {
    boomerang_trail_colors().into_keys().collect()
}

#[pyfunction]
#[pyo3(signature = (outer = false))]
fn get_boomerang_trail_color_options(outer: bool) -> Vec<&'static str> {
    if outer {
        iter::once("[Same as Inner]").chain(META_COLOR_CHOICES).chain(get_boomerang_trail_colors()).collect()
    } else {
        META_COLOR_CHOICES.into_iter().chain(get_boomerang_trail_colors()).collect()
    }
}

#[pyfunction]
fn get_gauntlet_colors() -> Vec<&'static str> {
    gauntlet_colors().into_keys().collect()
}

#[pyfunction]
fn get_gauntlet_color_options() -> Vec<&'static str> {
    META_COLOR_CHOICES.into_iter().chain(get_gauntlet_colors()).collect()
}

#[pyfunction]
fn get_shield_frame_colors() -> Vec<&'static str> {
    shield_frame_colors().into_keys().collect()
}

#[pyfunction]
fn get_shield_frame_color_options() -> Vec<&'static str> {
    META_COLOR_CHOICES.into_iter().chain(get_shield_frame_colors()).collect()
}

#[pyfunction]
fn get_heart_colors() -> Vec<&'static str> {
    heart_colors().into_keys().collect()
}

#[pyfunction]
fn get_heart_color_options() -> Vec<&'static str> {
    META_COLOR_CHOICES.into_iter().chain(get_heart_colors()).collect()
}

#[pyfunction]
fn get_magic_colors() -> Vec<&'static str> {
    magic_colors().into_keys().collect()
}

#[pyfunction]
fn get_magic_color_options() -> Vec<&'static str> {
    META_COLOR_CHOICES.into_iter().chain(get_magic_colors()).collect()
}

#[pyfunction]
fn get_a_button_colors() -> Vec<&'static str> {
    a_button_colors().into_keys().collect()
}

#[pyfunction]
fn get_a_button_color_options() -> Vec<&'static str> {
    META_COLOR_CHOICES.into_iter().chain(get_a_button_colors()).collect()
}

#[pyfunction]
fn get_b_button_colors() -> Vec<&'static str> {
    b_button_colors().into_keys().collect()
}

#[pyfunction]
fn get_b_button_color_options() -> Vec<&'static str> {
    META_COLOR_CHOICES.into_iter().chain(get_b_button_colors()).collect()
}

#[pyfunction]
fn get_c_button_colors() -> Vec<&'static str> {
    c_button_colors().into_keys().collect()
}

#[pyfunction]
fn get_c_button_color_options() -> Vec<&'static str> {
    META_COLOR_CHOICES.into_iter().chain(get_a_button_colors()).collect()
}

#[pyfunction]
fn get_start_button_colors() -> Vec<&'static str> {
    start_button_colors().into_keys().collect()
}

#[pyfunction]
fn get_start_button_color_options() -> Vec<&'static str> {
    META_COLOR_CHOICES.into_iter().chain(get_start_button_colors()).collect()
}

/// Based on accessibility standards (WCAG 2.0)
#[pyfunction]
fn contrast_ratio(color1: Color, color2: Color) -> f64 {
    let lum1 = relative_luminance(color1);
    let lum2 = relative_luminance(color2);
    (lum1.max(lum2) + 0.05) / (lum1.min(lum2) + 0.05)
}

fn relative_luminance(color: Color) -> f64 {
    let [r, g, b] = color.bytes().map(lum_color_ratio);
    r * 0.299 + g * 0.587 + b * 0.114
}

fn lum_color_ratio(val: u8) -> f64 {
    let val = f64::from(val) / 255.0;
    if val <= 0.03928 {
        val / 12.92
    } else {
        ((val + 0.055) / 1.055).powf(2.4)
    }
}

#[pyfunction]
fn generate_random_color(py: Python<'_>) -> PyResult<Color> {
    let random = py.import(intern!(py, "random"))?;
    let getrandbits = intern!(py, "getrandbits");
    Ok(Color {
        r: random.call_method1(getrandbits, (8,))?.extract()?,
        g: random.call_method1(getrandbits, (8,))?.extract()?,
        b: random.call_method1(getrandbits, (8,))?.extract()?,
    })
}

/// build color from hex code
#[pyfunction]
fn hex_to_color(option: &str) -> PyResult<Color> {
    let option = option.strip_prefix('#').unwrap_or(option);
    if !regex_is_match!("^(?:[0-9a-fA-F]{3}){1,2}$", option) {
        return Err(PyValueError::new_err(format!("Invalid color value provided: {option}")))
    }
    Ok(if option.len() > 3 {
        Color {
            r: u8::from_str_radix(&option[0..2], 16)?,
            g: u8::from_str_radix(&option[2..4], 16)?,
            b: u8::from_str_radix(&option[4..6], 16)?,
        }
    } else {
        Color {
            r: u8::from_str_radix(&format!("{0}{0}", &option[0..1]), 16)?,
            g: u8::from_str_radix(&format!("{0}{0}", &option[1..2]), 16)?,
            b: u8::from_str_radix(&format!("{0}{0}", &option[2..3]), 16)?,
        }
    })
}

#[pyfunction]
fn color_to_hex(color: Color) -> String {
    format!("#{:02X}{:02X}{:02X}", color.r, color.g, color.b)
}

pub(crate) fn module(py: Python<'_>) -> PyResult<Bound<'_, PyModule>> {
    let m = PyModule::new(py, "color")?;
    m.add_class::<Color>()?;
    m.add("tunic_colors", tunic_colors())?;
    m.add("NaviColors", navi_colors())?;
    m.add("sword_trail_colors", sword_trail_colors())?;
    m.add("bombchu_trail_colors", bombchu_trail_colors())?;
    m.add("boomerang_trail_colors", boomerang_trail_colors())?;
    m.add("gauntlet_colors", gauntlet_colors())?;
    m.add("shield_frame_colors", shield_frame_colors())?;
    m.add("heart_colors", heart_colors())?;
    m.add("magic_colors", magic_colors())?;
    m.add("a_button_colors", a_button_colors())?;
    m.add("b_button_colors", b_button_colors())?;
    m.add("c_button_colors", c_button_colors())?;
    m.add("start_button_colors", start_button_colors())?;
    m.add_function(wrap_pyfunction!(get_tunic_colors, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_tunic_color_options, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_navi_colors, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_navi_color_options, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_sword_trail_colors, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_sword_trail_color_options, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_bombchu_trail_colors, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_bombchu_trail_color_options, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_boomerang_trail_colors, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_boomerang_trail_color_options, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_gauntlet_colors, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_gauntlet_color_options, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_shield_frame_colors, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_shield_frame_color_options, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_heart_colors, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_heart_color_options, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_magic_colors, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_magic_color_options, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_a_button_colors, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_a_button_color_options, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_b_button_colors, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_b_button_color_options, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_c_button_colors, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_c_button_color_options, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_start_button_colors, m.clone())?)?;
    m.add_function(wrap_pyfunction!(get_start_button_color_options, m.clone())?)?;
    m.add_function(wrap_pyfunction!(contrast_ratio, m.clone())?)?;
    m.add_function(wrap_pyfunction!(generate_random_color, m.clone())?)?;
    m.add_function(wrap_pyfunction!(hex_to_color, m.clone())?)?;
    m.add_function(wrap_pyfunction!(color_to_hex, m.clone())?)?;
    Ok(m)
}

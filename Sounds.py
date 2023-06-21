# SOUNDS.PY
#
# A data-oriented module created to avoid cluttering (and entangling) other,
# more important modules with sound data.
#
# Tags
# To easily fetch related sounds by their properties. This seems generally
# better than the alternative of defining long lists by hand. You still can, of
# course. Categorizing sounds with more useful tags will require some work. Do
# this as needed.
#
# Sounds
# These are a collection of data structures relating to sounds. Already I'm sure
# you get the picture.
#
# Sound Pools
# These are just groups of sounds, to be referenced by sfx settings. Could
# potentially merit enumerating later on. ¯\_(ツ)_/¯
#
# Sound Hooks
# These are intended to gear themselves toward configurable settings, rather
# than to document every location where a particular sound is used. For example,
# suppose we want a setting to override all of Link's vocalizations. The sound
# hook would contain a bunch of addresses, whether they share the same default
# value or not.

from __future__ import annotations
import os
from dataclasses import dataclass
from enum import Enum

from Rom import Rom
from Utils import data_path


class Tags(Enum):
    LOOPED     = 0
    QUIET      = 1
    IMMEDIATE  = 2      # Delayed sounds are commonly undesirable
    BRIEF      = 3      # Punchy sounds, good for rapid fire
    NEW        = 4
    PAINFUL    = 5      # Eardrum-piercing sounds
    NAVI       = 6      # Navi sounds (hand chosen)
    HPLOW      = 7      # Low HP sounds (hand chosen)
    HOVERBOOT  = 8      # Hover boot sounds (hand chosen)
    NIGHTFALL  = 9      # Nightfall sounds (hand chosen)
    MENUSELECT = 10     # Menu selection sounds (hand chosen, could use some more)
    MENUMOVE   = 11     # Menu movement sounds  (hand chosen, could use some more)
    HORSE      = 12     # Horse neigh sounds (hand chosen)
    INC_NE     = 20     # Incompatible with NAVI_ENEMY? (Verify)
                        # I'm now thinking it has to do with a limit of concurrent sounds)


@dataclass(frozen=True)
class Sound:
    id: int
    keyword: str
    label: str
    tags: list[Tags]


class Sounds(Enum):
    #                          id      keyword                  label                        tags
    NONE               = Sound(0x0000, 'none',                  'None',                      [Tags.NAVI, Tags.HPLOW])
    ARMOS_GROAN        = Sound(0x3848, 'armos',                 'Armos',                     [Tags.HORSE, Tags.PAINFUL])
    BARK               = Sound(0x28D8, 'bark',                  'Bark',                      [Tags.BRIEF, Tags.NAVI, Tags.HPLOW, Tags.HOVERBOOT])
    BOMB_BOUNCE        = Sound(0x282F, 'bomb-bounce',           'Bomb Bounce',               [Tags.QUIET, Tags.HPLOW])
    BONGO_HIGH         = Sound(0x3951, 'bongo-bongo-high',      'Bongo Bongo High',          [Tags.MENUSELECT])
    BONGO_LOW          = Sound(0x3950, 'bongo-bongo-low',       'Bongo Bongo Low',           [Tags.QUIET, Tags.HPLOW, Tags.MENUMOVE])
    BOTTLE_CORK        = Sound(0x286C, 'bottle-cork',           'Bottle Cork',               [Tags.IMMEDIATE, Tags.BRIEF, Tags.QUIET])
    BOW_TWANG          = Sound(0x1830, 'bow-twang',             'Bow Twang',                 [Tags.HPLOW, Tags.MENUMOVE])
    BUBBLE_LOL         = Sound(0x38CA, 'bubble-laugh',          'Bubble Laugh',              [])
    BUSINESS_SCRUB     = Sound(0x3882, 'business-scrub',        'Business Scrub',            [Tags.PAINFUL, Tags.NAVI, Tags.HPLOW])
    CARROT_REFILL      = Sound(0x4845, 'carrot-refill',         'Carrot Refill',             [Tags.NAVI, Tags.HPLOW])
    CARTOON_FALL       = Sound(0x28A0, 'cartoon-fall',          'Cartoon Fall',              [Tags.PAINFUL, Tags.HOVERBOOT])
    CHANGE_ITEM        = Sound(0x0835, 'change-item',           'Change Item',               [Tags.IMMEDIATE, Tags.BRIEF, Tags.MENUSELECT])
    CHEST_OPEN         = Sound(0x2820, 'chest-open',            'Chest Open',                [Tags.PAINFUL])
    CHILD_CRINGE       = Sound(0x683A, 'child-cringe',          'Child Cringe',              [Tags.PAINFUL, Tags.IMMEDIATE, Tags.MENUSELECT])
    CHILD_GASP         = Sound(0x6836, 'child-gasp',            'Child Gasp',                [Tags.PAINFUL])
    CHILD_HURT         = Sound(0x6825, 'child-hurt',            'Child Hurt',                [Tags.PAINFUL])
    CHILD_OWO          = Sound(0x6823, 'child-owo',             'Child owo',                 [Tags.PAINFUL])
    CHILD_PANT         = Sound(0x6829, 'child-pant',            'Child Pant',                [Tags.IMMEDIATE])
    CHILD_SCREAM       = Sound(0x6828, 'child-scream',          'Child Scream',              [Tags.PAINFUL, Tags.IMMEDIATE, Tags.MENUSELECT, Tags.HORSE])
    CUCCO_CLUCK        = Sound(0x2812, 'cluck',                 'Cluck',                     [Tags.BRIEF, Tags.NAVI, Tags.HPLOW])
    CUCCO_CROW         = Sound(0x2813, 'cockadoodledoo',        'Cockadoodledoo',            [Tags.PAINFUL, Tags.NAVI, Tags.NIGHTFALL])
    CURSED_ATTACK      = Sound(0x6868, 'cursed-attack',         'Cursed Attack',             [Tags.PAINFUL, Tags.IMMEDIATE])
    CURSED_SCREAM      = Sound(0x6867, 'cursed-scream',         'Cursed Scream',             [Tags.PAINFUL])
    DEKU_BABA_CHATTER  = Sound(0x3860, 'deku-baba',             'Deku Baba',                 [Tags.MENUMOVE])
    DRAWBRIDGE_SET     = Sound(0x280E, 'drawbridge-set',        'Drawbridge Set',            [Tags.HPLOW])
    DUSK_HOWL          = Sound(0x28AE, 'dusk-howl',             'Dusk Howl',                 [Tags.NAVI])
    EPONA_CHILD        = Sound(0x2844, 'baby-epona',            'Epona (Baby)',              [Tags.PAINFUL])
    EXPLODE_CRATE      = Sound(0x2839, 'exploding-crate',       'Exploding Crate',           [Tags.PAINFUL, Tags.NAVI])
    EXPLOSION          = Sound(0x180E, 'explosion',             'Explosion',                 [Tags.PAINFUL, Tags.NAVI])
    FANFARE_SMALL      = Sound(0x4824, 'fanfare-light',         'Fanfare (Light)',           [])
    FANFARE_MED        = Sound(0x4831, 'fanfare-medium',        'Fanfare (Medium)',          [])
    FIELD_SHRUB        = Sound(0x2877, 'field-shrub',           'Field Shrub',               [])
    FLARE_BOSS_LOL     = Sound(0x3981, 'flare-dancer-laugh',    'Flare Dancer Laugh',        [Tags.PAINFUL, Tags.IMMEDIATE, Tags.HOVERBOOT])
    FLARE_BOSS_STARTLE = Sound(0x398B, 'flare-dancer-startled', 'Flare Dancer Startled',     [])
    GANON_TENNIS       = Sound(0x39CA, 'ganondorf-teh',         'Ganondorf "Teh!"',          [])
    GOHMA_LARVA_CROAK  = Sound(0x395D, 'gohma-larva-croak',     'Gohma Larva Croak',         [])
    GOLD_SKULL_TOKEN   = Sound(0x4843, 'gold-skull-token',      'Gold Skull Token',          [Tags.NIGHTFALL])
    GORON_WAKE         = Sound(0x38FC, 'goron-wake',            'Goron Wake',                [])
    GREAT_FAIRY        = Sound(0x6858, 'great-fairy',           'Great Fairy',               [Tags.PAINFUL, Tags.NAVI, Tags.NIGHTFALL, Tags.HORSE])
    GUAY               = Sound(0x38B6, 'guay',                  'Guay',                      [Tags.BRIEF, Tags.NAVI, Tags.HPLOW])
    GUNSHOT            = Sound(0x4835, 'gunshot',               'Gunshot',                   [])
    HAMMER_BONK        = Sound(0x180A, 'hammer-bonk',           'Hammer Bonk',               [])
    HORSE_NEIGH        = Sound(0x2805, 'horse-neigh',           'Horse Neigh',               [Tags.PAINFUL, Tags.NAVI])
    HORSE_TROT         = Sound(0x2804, 'horse-trot',            'Horse Trot',                [Tags.HPLOW])
    HOVER_BOOTS        = Sound(0x08C9, 'hover-boots',           'Hover Boots',               [Tags.LOOPED, Tags.PAINFUL])
    HP_LOW             = Sound(0x481B, 'low-health',            'HP Low',                    [Tags.INC_NE, Tags.NAVI])
    HP_RECOVER         = Sound(0x480B, 'recover-health',        'HP Recover',                [Tags.NAVI, Tags.HPLOW])
    ICE_SHATTER        = Sound(0x0875, 'shattering-ice',        'Ice Shattering',            [Tags.PAINFUL, Tags.NAVI])
    INGO_WOOAH         = Sound(0x6854, 'ingo-wooah',            'Ingo "Wooah!"',             [Tags.PAINFUL])
    IRON_BOOTS         = Sound(0x080D, 'iron-boots',            'Iron Boots',                [Tags.BRIEF, Tags.HPLOW, Tags.QUIET])
    IRON_KNUCKLE       = Sound(0x3929, 'iron-knuckle',          'Iron Knuckle',              [])
    INGO_KAAH          = Sound(0x6855, 'kaah',                  'Kaah!',                     [Tags.PAINFUL])
    MOBLIN_CLUB_GROUND = Sound(0x38E1, 'moblin-club-ground',    'Moblin Club Ground',        [Tags.PAINFUL])
    MOBLIN_CLUB_SWING  = Sound(0x39EF, 'moblin-club-swing',     'Moblin Club Swing',         [Tags.PAINFUL])
    MOO                = Sound(0x28DF, 'moo',                   'Moo',                       [Tags.NAVI, Tags.NIGHTFALL, Tags.HORSE, Tags.HPLOW])
    MWEEP              = Sound(0x687A, 'mweep',                 'Mweep!',                    [Tags.BRIEF, Tags.NAVI, Tags.MENUMOVE, Tags.MENUSELECT, Tags.NIGHTFALL, Tags.HPLOW, Tags.HORSE, Tags.HOVERBOOT])
    NAVI_HELLO         = Sound(0x6844, 'navi-hello',            'Navi "Hello!"',             [Tags.PAINFUL, Tags.NAVI])
    NAVI_HEY           = Sound(0x685F, 'navi-hey',              'Navi "Hey!"',               [Tags.PAINFUL, Tags.HPLOW])
    NAVI_RANDOM        = Sound(0x6843, 'navi-random',           'Navi Random',               [Tags.PAINFUL, Tags.HPLOW])
    NOTIFICATION       = Sound(0x4820, 'notification',          'Notification',              [Tags.NAVI, Tags.HPLOW])
    PHANTOM_GANON_LOL  = Sound(0x38B0, 'phantom-ganon-laugh',   'Phantom Ganon Laugh',       [])
    PLANT_EXPLODE      = Sound(0x284E, 'plant-explode',         'Plant Explode',             [])
    POE                = Sound(0x38EC, 'poe',                   'Poe',                       [Tags.PAINFUL, Tags.NAVI])
    POT_SHATTER        = Sound(0x2887, 'shattering-pot',        'Pot Shattering',            [Tags.NAVI, Tags.HPLOW])
    REDEAD_MOAN        = Sound(0x38E4, 'redead-moan',           'Redead Moan',               [Tags.NIGHTFALL])
    REDEAD_SCREAM      = Sound(0x38E5, 'redead-scream',         'Redead Scream',             [Tags.PAINFUL, Tags.NAVI, Tags.HORSE])
    RIBBIT             = Sound(0x28B1, 'ribbit',                'Ribbit',                    [Tags.NAVI, Tags.HPLOW])
    RUPEE              = Sound(0x4803, 'rupee',                 'Rupee',                     [])
    RUPEE_SILVER       = Sound(0x28E8, 'silver-rupee',          'Rupee (Silver)',            [Tags.HPLOW])
    RUTO_CHILD_CRASH   = Sound(0x6860, 'ruto-crash',            'Ruto Crash',                [])
    RUTO_CHILD_EXCITED = Sound(0x6861, 'ruto-excited',          'Ruto Excited',              [Tags.PAINFUL])
    RUTO_CHILD_GIGGLE  = Sound(0x6863, 'ruto-giggle',           'Ruto Giggle',               [Tags.PAINFUL, Tags.NAVI])
    RUTO_CHILD_LIFT    = Sound(0x6864, 'ruto-lift',             'Ruto Lift',                 [])
    RUTO_CHILD_THROWN  = Sound(0x6865, 'ruto-thrown',           'Ruto Thrown',               [])
    RUTO_CHILD_WIGGLE  = Sound(0x6866, 'ruto-wiggle',           'Ruto Wiggle',               [Tags.PAINFUL, Tags.HORSE])
    SCRUB_NUTS_UP      = Sound(0x387C, 'scrub-emerge',          'Scrub Emerge',              [])
    SHABOM_BOUNCE      = Sound(0x3948, 'shabom-bounce',         'Shabom Bounce',             [Tags.IMMEDIATE])
    SHABOM_POP         = Sound(0x3949, 'shabom-pop',            'Shabom Pop',                [Tags.IMMEDIATE, Tags.BRIEF, Tags.HOVERBOOT])
    SHELLBLADE         = Sound(0x3849, 'shellblade',            'Shellblade',                [])
    SKULLTULA          = Sound(0x39DA, 'skulltula',             'Skulltula',                 [Tags.BRIEF, Tags.NAVI])
    SOFT_BEEP          = Sound(0x4804, 'soft-beep',             'Soft Beep',                 [Tags.NAVI, Tags.HPLOW])
    SPIKE_TRAP         = Sound(0x38E9, 'spike-trap',            'Spike Trap',                [Tags.LOOPED, Tags.PAINFUL])
    SPIT_NUT           = Sound(0x387E, 'spit-nut',              'Spit Nut',                  [Tags.IMMEDIATE, Tags.BRIEF])
    STALCHILD_ATTACK   = Sound(0x3831, 'stalchild-attack',      'Stalchild Attack',          [Tags.PAINFUL, Tags.HORSE])
    STINGER_CRY        = Sound(0x39A3, 'stinger-squeak',        'Stinger Squeak',            [Tags.PAINFUL])
    SWITCH             = Sound(0x2815, 'switch',                'Switch',                    [Tags.HPLOW])
    SWORD_BONK         = Sound(0x181A, 'sword-bonk',            'Sword Bonk',                [Tags.HPLOW])
    TALON_CRY          = Sound(0x6853, 'talon-cry',             'Talon Cry',                 [Tags.PAINFUL])
    TALON_HMM          = Sound(0x6852, 'talon-hmm',             'Talon "Hmm"',               [])
    TALON_SNORE        = Sound(0x6850, 'talon-snore',           'Talon Snore',               [Tags.NIGHTFALL])
    TALON_WTF          = Sound(0x6851, 'talon-wtf',             'Talon Wtf',                 [])
    TAMBOURINE         = Sound(0x4842, 'tambourine',            'Tambourine',                [Tags.QUIET, Tags.NAVI, Tags.HPLOW, Tags.HOVERBOOT])
    TARGETING_ENEMY    = Sound(0x4830, 'target-enemy',          'Target Enemy',              [])
    TARGETING_NEUTRAL  = Sound(0x480C, 'target-neutral',        'Target Neutral',            [])
    THUNDER            = Sound(0x282E, 'thunder',               'Thunder',                   [Tags.NIGHTFALL])
    TIMER              = Sound(0x481A, 'timer',                 'Timer',                     [Tags.INC_NE, Tags.NAVI, Tags.HPLOW])
    TWINROVA_BICKER    = Sound(0x39E7, 'twinrova-bicker',       'Twinrova Bicker',           [Tags.LOOPED, Tags.PAINFUL])
    WOLFOS_HOWL        = Sound(0x383C, 'wolfos-howl',           'Wolfos Howl',               [Tags.PAINFUL])
    ZELDA_ADULT_GASP   = Sound(0x6879, 'adult-zelda-gasp',      'Zelda Gasp (Adult)',        [Tags.NAVI, Tags.HPLOW])


# Sound pools
standard    = [s for s in Sounds if Tags.LOOPED not in s.value.tags]
looping     = [s for s in Sounds if Tags.LOOPED in s.value.tags]
no_painful  = [s for s in standard if Tags.PAINFUL not in s.value.tags]
navi        = [s for s in Sounds if Tags.NAVI in s.value.tags]
hp_low      = [s for s in Sounds if Tags.HPLOW in s.value.tags]
hover_boots = [s for s in Sounds if Tags.HOVERBOOT in s.value.tags]
nightfall   = [s for s in Sounds if Tags.NIGHTFALL in s.value.tags]
menu_select = [s for s in Sounds if Tags.MENUSELECT in s.value.tags]
menu_cursor = [s for s in Sounds if Tags.MENUMOVE in s.value.tags]
horse_neigh = [s for s in Sounds if Tags.HORSE in s.value.tags]


@dataclass(frozen=True)
class SoundHook:
    name: str
    pool: list[Sounds]
    locations: list[int]
    sfx_flag: bool


class SoundHooks(Enum):
    #                           name                pool         locations  sfx_flag
    NAVI_OVERWORLD  = SoundHook('Navi - Overworld', navi,        [0xAE7EF2, 0xC26C7E], False)
    NAVI_ENEMY      = SoundHook('Navi - Enemy',     navi,        [0xAE7EC6], False)
    HP_LOW          = SoundHook('Low Health',       hp_low,      [0xADBA1A], False)
    BOOTS_HOVER     = SoundHook('Hover Boots',      hover_boots, [0xBDBD8A], True)
    NIGHTFALL       = SoundHook('Nightfall',        nightfall,   [0xAD3466, 0xAD7A2E], False)
    MENU_SELECT     = SoundHook('Menu Select',      no_painful + menu_select,  [
                        0xBA1BBE, 0xBA23CE, 0xBA2956, 0xBA321A, 0xBA72F6, 0xBA8106, 0xBA82EE,
                        0xBA9DAE, 0xBA9EAE, 0xBA9FD2, 0xBAE6D6], False)
    MENU_CURSOR     = SoundHook('Menu Cursor',      no_painful + menu_cursor,  [
                        0xBA165E, 0xBA1C1A, 0xBA2406, 0xBA327E, 0xBA3936, 0xBA77C2, 0xBA7886,
                        0xBA7A06, 0xBA7A6E, 0xBA7AE6, 0xBA7D6A, 0xBA8186, 0xBA822E, 0xBA82A2,
                        0xBAA11E, 0xBAE7C6], False)
    HORSE_NEIGH     = SoundHook('Horse Neigh',      horse_neigh, [
                        0xC18832, 0xC18C32, 0xC19A7E, 0xC19CBE, 0xC1A1F2, 0xC1A3B6, 0xC1B08A,
                        0xC1B556, 0xC1C28A, 0xC1CC36, 0xC1EB4A, 0xC1F18E, 0xC6B136, 0xC6BBA2,
                        0xC1E93A, 0XC6B366, 0XC6B562], False)
    BOOTS_IRON       = SoundHook('Iron Boots',      standard,   [0xBCE1CA, 0xBCE21E, 0xBCE26A], False)
    SILVER_RUPEE    = SoundHook('Silver Rupee',     standard,   [0xDF356A], False)
    BOOMERANG_THROW = SoundHook('Boomerang Throw',  standard,   [0xC5ABD6], True)
    HOOKSHOT_CHAIN = SoundHook('Hookshot Chain',    standard,   [0xCAD5AE], True)
    ARROW_SHOT = SoundHook('Arrow Shot',            standard,   [0xC22002], False)
    SLINGSHOT_SHOT = SoundHook('Slingshot Shot',    standard,   [0xC21FEE], False)
    MAGIC_ARROW_SHOT = SoundHook('Magic Arrow Shot',standard,   [0xC22016], False)
    BOMBCHU_MOVE = SoundHook('Bombchu Move',        standard,   [0xD5F792], True)
    GET_SMALL_ITEM = SoundHook('Get Small Item',    standard,   [0xBDA00E, 0xBE9B4A, 0xBD9FFA, 0xA88EA2], False)
    EXPLOSION = SoundHook('Explosion',              standard,   [0xC0ECA2, 0xC88476], False)
    # Only overrides normal bomb/chu and Bomb flower, Bombchu bowling sounds too weird with it : 0xEECB9A, 0xEED402
    DAYBREAK = SoundHook('Daybreak',                nightfall,  [0xAD342E, 0xAD7B52], False)
    CUCCO = SoundHook('Cucco',                      standard,   [0xC28B9E, 0xC28C92, 0xC28D12, 0xC294EE,
                                                                 0xC29866, 0xC29B82, 0xC2A3BA, 0xC2A3A6,            # Normal cuccos
                                                                 0xE2841E,                                          # Attacking cuccos
                                                                 0xE262B6, 0xE267EE, 0xE26846, 0xE26B1E, 0xE26B36,  # Bowling cuccos
                                                                 0xBEACCE, 0xE2109A, 0xAFD942                       # Chicken, Pocket cucco and Cojiro
                                                                 ], False)

#   # Some enemies have a different cutting sound, making this a bit weird
#   SWORD_SLASH     = SoundHook('Sword Slash',      standard,         [0xAC2942])


def get_patch_dict() -> dict[str, int]:
    return {s.value.keyword: s.value.id for s in Sounds}


def get_hook_pool(sound_hook: SoundHooks, earsafeonly: bool = False) -> list[Sounds]:
    if earsafeonly:
        list = [s for s in sound_hook.value.pool if Tags.PAINFUL not in s.value.tags]
        return list
    else:
        return sound_hook.value.pool


def get_setting_choices(sound_hook: SoundHooks) -> dict[str, str]:
    pool = sound_hook.value.pool
    choices = {s.value.keyword: s.value.label for s in sorted(pool, key=lambda s: s.value.label)}
    result = {
        'default':           'Default',
        'completely-random': 'Completely Random',
        'random-ear-safe':   'Random Ear-Safe',
        'random-choice':     'Random Choice',
        'none':              'None',
        **choices,
    }
    return result


def get_voice_sfx_choices(age: int, include_random: bool = True) -> list[str]:
    # Dynamically populate the SettingsList entry for the voice effects
    # Voice packs should be a folder of .bin files in the Voices/{age} directory
    names = ['Default', 'Silent']
    voices_path = os.path.join(data_path('Voices'), ('Child' if age == 0 else 'Adult'))
    if os.path.isdir(voices_path):
        names += [f for f in os.listdir(voices_path) if os.path.isdir(os.path.join(voices_path, f))]

    # Add a random if multiple options are available
    if len(names) > 2 and include_random:
        names.append('Random')
    return names


def move_audiobank_table(rom: Rom, from_addr: int, to_addr: int) -> None:
    audiobank_table_header = rom.read_bytes(from_addr, 0x10)
    num_entries = (audiobank_table_header[0] << 8) + audiobank_table_header[1]
    audiobank_table_bytes = rom.read_bytes(from_addr, (num_entries+1)*0x10)
    rom.write_bytes(to_addr, audiobank_table_bytes)

import random
from Utils import random_choices
from Item import ItemFactory
from ItemList import item_table
from LocationList import dungeons, location_table
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP


# Generates itempools and places fixed items based on settings.


# in plentiful, one extra copy of each item in this list will be added
# but only if at least one copy already exists in the base pool
# (e.g. items that aren't shuffled aren't duplicated)
plentiful_extra_items = [
    'Biggoron Sword',
    'Kokiri Sword',
    'Boomerang',
    'Lens of Truth',
    'Megaton Hammer',
    'Iron Boots',
    'Goron Tunic',
    'Zora Tunic',
    'Hover Boots',
    'Mirror Shield',
    'Fire Arrows',
    'Light Arrows',
    'Dins Fire',
    'Progressive Hookshot',
    'Progressive Strength Upgrade',
    'Progressive Scale',
    'Progressive Wallet',
    'Magic Meter',
    'Deku Stick Capacity',
    'Deku Nut Capacity',
    'Bow',
    'Slingshot',
    'Bomb Bag',
    'Double Defense',
    'Ocarina',
    'Magic Bean Pack',
    'Small Key (Gerudo Fortress)',
    'Gerudo Membership Card',
    'Small Key (Bottom of the Well)',
    'Small Key (Forest Temple)',
    'Small Key (Fire Temple)',
    'Small Key (Water Temple)',
    'Small Key (Shadow Temple)',
    'Small Key (Spirit Temple)',
    'Small Key (Gerudo Training Grounds)',
    'Small Key (Ganons Castle)',
    'Boss Key (Forest Temple)',
    'Boss Key (Fire Temple)',
    'Boss Key (Water Temple)',
    'Boss Key (Shadow Temple)',
    'Boss Key (Spirit Temple)',
    'Boss Key (Ganons Castle)',
]

item_pool_max = {
    'scarce': {
        'Bombchus': 3,
        'Bombchus (5)': 1,
        'Bombchus (10)': 2,
        'Bombchus (20)': 0,
        'Magic Meter': 1,
        'Double Defense': 0,
        'Deku Stick Capacity': 1,
        'Deku Nut Capacity': 1,
        'Bow': 2,
        'Slingshot': 2,
        'Bomb Bag': 2,
        'Heart Container': 0,
    },
    'minimal': {
        'Bombchus': 1,
        'Bombchus (5)': 1,
        'Bombchus (10)': 0,
        'Bombchus (20)': 0,
        'Nayrus Love': 0,
        'Magic Meter': 1,
        'Double Defense': 0,
        'Deku Stick Capacity': 0,
        'Deku Nut Capacity': 0,
        'Bow': 1,
        'Slingshot': 1,
        'Bomb Bag': 1,
        'Heart Container': 0,
        'Piece of Heart': 0,
    },
}

TriforceCounts = {
    'plentiful': Decimal(2.00),
    'balanced':  Decimal(1.50),
    'scarce':    Decimal(1.25),
    'minimal':   Decimal(1.00),
}


normal_bottles = [
    'Bottle',
    'Bottle with Milk',
    'Bottle with Red Potion',
    'Bottle with Green Potion',
    'Bottle with Blue Potion',
    'Bottle with Fairy',
    'Bottle with Fish',
    'Bottle with Bugs',
    'Bottle with Poe',
    'Bottle with Big Poe',
    'Bottle with Blue Fire',
]


# if shops sell non-shop items, replace some blue rupees with more money and an extra wallet
shopsanity_rupee_upgrades = (
    ['Rupees (20)'] * 5 +
    ['Rupees (50)'] * 3 +
    ['Rupees (200)'] * 2 +
    ['Progressive Wallet']
)

# Make sure these items remain in shops even in shopsanity.
# The total length of this list must remain at 32 or below,
# since that is the number of shop slots available at shopsanity 4.
min_shop_items = (
    ['Buy Deku Shield'] +
    ['Buy Hylian Shield'] +
    ['Buy Goron Tunic'] +
    ['Buy Zora Tunic'] +
    ['Buy Deku Nut (5)'] * 2 + ['Buy Deku Nut (10)'] +
    ['Buy Deku Stick (1)'] * 2 +
    ['Buy Deku Seeds (30)'] +
    ['Buy Arrows (10)'] * 2 + ['Buy Arrows (30)'] + ['Buy Arrows (50)'] +
    ['Buy Bombchu (5)'] + ['Buy Bombchu (10)'] * 2 + ['Buy Bombchu (20)'] +
    ['Buy Bombs (5) [25]'] + ['Buy Bombs (5) [35]'] + ['Buy Bombs (10)'] + ['Buy Bombs (20)'] +
    ['Buy Green Potion'] +
    ['Buy Red Potion [30]'] +
    ['Buy Blue Fire'] +
    ['Buy Fairy\'s Spirit'] +
    ['Buy Bottle Bug'] +
    ['Buy Fish']
)


songlist = [
    'Zeldas Lullaby',
    'Eponas Song',
    'Suns Song',
    'Sarias Song',
    'Song of Time',
    'Song of Storms',
    'Minuet of Forest',
    'Prelude of Light',
    'Bolero of Fire',
    'Serenade of Water',
    'Nocturne of Shadow',
    'Requiem of Spirit',
]


tradeitems = (
    'Pocket Egg',
    'Pocket Cucco',
    'Cojiro',
    'Odd Mushroom',
    'Poachers Saw',
    'Broken Sword',
    'Prescription',
    'Eyeball Frog',
    'Eyedrops',
    'Claim Check',
)

trade_item_options = (
    'pocket_egg',
    'pocket_cucco',
    'cojiro',
    'odd_mushroom',
    'poachers_saw',
    'broken_sword',
    'prescription',
    'eyeball_frog',
    'eyedrops',
    'claim_check',
)


# a useless placeholder item placed at locations that aren't accessible
# (e.g. HC Malon Egg with Skip Child Zelda, or the carpenters with Open Gerudo Fortress)
IGNORE_LOCATION = 'Ice Trap'


# these items are added if there are more locations than items,
# because items have been removed (e.g. Keysy)
# and/or locations have been added (e.g. cow shuffle)
junk_pool_base = [
    ('Bombs (5)',       8),
    ('Bombs (10)',      2),
    ('Arrows (5)',      8),
    ('Arrows (10)',     2),
    ('Deku Stick (1)',  5),
    ('Deku Nuts (5)',   5),
    ('Deku Seeds (30)', 5),
    ('Rupees (5)',      10),
    ('Rupees (20)',     4),
    ('Rupees (50)',     1),
]

junk_pool = []


remove_junk_items = [
    'Bombs (5)',
    'Deku Nuts (5)',
    'Deku Stick (1)',
    'Recovery Heart',
    'Arrows (5)',
    'Arrows (10)',
    'Arrows (30)',
    'Rupees (5)',
    'Rupees (20)',
    'Rupees (50)',
    'Rupees (200)',
    'Deku Nuts (10)',
    'Bombs (10)',
    'Bombs (20)',
    'Deku Seeds (30)',
    'Ice Trap',
]
remove_junk_set = set(remove_junk_items)


def get_junk_item(count=1, pool=None, plando_pool=None):
    if count < 1:
        raise ValueError("get_junk_item argument 'count' must be greater than 0.")

    if pool and plando_pool:
        jw_list = [
            (junk, weight)
            for (junk, weight) in junk_pool
            if junk not in plando_pool or pool.count(junk) < plando_pool[junk].count
        ]
        try:
            junk_items, junk_weights = zip(*jw_list)
        except ValueError:
            raise RuntimeError("Not enough junk is available in the item pool to replace removed items.")
    else:
        junk_items, junk_weights = zip(*junk_pool)

    return random_choices(junk_items, weights=junk_weights, k=count)


def converted_item(item):
    """
    Replaces items that aren't suitable for being shuffled with ones that are.
    May return None to indicate that it should be shuffled as a random junk item.
    """
    return {
        'Buy Arrows (10)': 'Arrows (10)',
        'Buy Arrows (30)': 'Arrows (30)',
        'Buy Arrows (50)': 'Arrows (30)', # Arrows (50) doesn't seem to exist
        'Buy Blue Fire': None,
        'Buy Bombchu (5)': 'Bombchus (5)',
        'Buy Bombchu (10)': 'Bombchus (10)',
        'Buy Bombchu (20)': 'Bombchus (20)',
        'Buy Bombs (5) [25]': 'Bombs (5)',
        'Buy Bombs (5) [35]': 'Bombs (5)',
        'Buy Bombs (10)': 'Bombs (10)',
        'Buy Bombs (20)': 'Bombs (20)',
        'Buy Bombs (30)': 'Bombs (20)', # Bombs (30) doesn't seem to exist
        'Buy Bottle Bug': None,
        'Buy Deku Nut (5)': 'Deku Nuts (5)',
        'Buy Deku Nut (10)': 'Deku Nuts (10)',
        'Buy Deku Seeds (30)': 'Deku Seeds (30)',
        'Buy Deku Shield': 'Deku Shield',
        'Buy Deku Stick (1)': 'Deku Stick (1)',
        'Buy Fairy\'s Spirit': None,
        'Buy Fish': None,
        'Buy Goron Tunic': 'Goron Tunic',
        'Buy Green Potion': None,
        'Buy Heart': 'Recovery Heart',
        'Buy Hylian Shield': 'Hylian Shield',
        'Buy Poe': None,
        'Buy Red Potion [30]': None,
        'Buy Red Potion [40]': None,
        'Buy Red Potion [50]': None,
        'Buy Zora Tunic': 'Zora Tunic',
        'Magic Bean': 'Magic Bean Pack',
        'Milk': None,
    }.get(item, item)


def matches_mq(world, categories):
    return all(
        ('Master Quest' if world.dungeon_mq[dungeon.replace("'", '')] else 'Vanilla') in categories
        for dungeon in dungeons
        if dungeon in categories
    )


def generate_itempool(world):
    junk_pool[:] = list(junk_pool_base)
    if world.junk_ice_traps == 'on':
        junk_pool.append(('Ice Trap', 10))
    elif world.junk_ice_traps in ['mayhem', 'onslaught']:
        junk_pool[:] = [('Ice Trap', 1)]

    # set up item pool
    (pool, placed_items) = get_pool_core(world)
    world.itempool = ItemFactory(pool, world)
    for (location, item) in placed_items.items():
        world.push_item(location, ItemFactory(item, world))
        world.get_location(location).locked = True

    world.initialize_items()
    world.distribution.set_complete_itempool(world.itempool)


# generate an item pool based on the vanilla location/item mapping (sampled in random order)
# and on the settings
def get_pool_core(world):
    pool = []
    placed_items = {}

    extra_rutos_letter = False
    removed_heart_pieces = 0
    remain_shop_items = min_shop_items.copy()
    num_shop_slots = sum(loc_type == 'Shop' for loc_type, _, _, _, _, _ in location_table.values()) - len(world.shop_prices) # number of empty non-special-deal shop locations
    rupee_upgrades = shopsanity_rupee_upgrades.copy()

    for location, (loc_type, scene, _, _, vanilla_item, categories) in random.sample(list(location_table.items()), len(location_table)):
        categories = categories or ()
        if not matches_mq(world, categories):
            continue

        shuffle_condition = True # most locations are always shuffled
        convert_vanilla_item = True # replace the item with one that can be placed anywhere if necessary

        if location in ('HC Zeldas Letter', 'Market Bombchu Bowling Bombchus'):
            shuffle_condition = False
        elif location in ('GC Medigoron', 'Wasteland Bombchu Salesman'):
            shuffle_condition = world.shuffle_medigoron_carpet_salesman
        elif location == 'GF North F1 Carpenter':
            shuffle_condition = world.gerudo_fortress != 'open' and world.shuffle_fortresskeys != 'vanilla'
            if world.gerudo_fortress == 'open':
                vanilla_item = IGNORE_LOCATION
        elif location in ('GF North F2 Carpenter', 'GF South F1 Carpenter', 'GF South F2 Carpenter'):
            shuffle_condition = world.gerudo_fortress not in ('open', 'fast') and world.shuffle_fortresskeys != 'vanilla'
            if world.gerudo_fortress in ('open', 'fast'):
                vanilla_item = IGNORE_LOCATION
        elif location == 'Ganons Tower Boss Key Chest':
            shuffle_condition = world.shuffle_ganon_bosskey not in ('vanilla', 'on_lacs', 'remove', 'triforce')
            if world.shuffle_ganon_bosskey == 'on_lacs':
                vanilla_item = None
            elif world.shuffle_ganon_bosskey in ('remove', 'triforce'):
                world.state.collect(ItemFactory(vanilla_item))
                vanilla_item = None
        elif location == 'ToT Light Arrow Cutscene':
            shuffle_condition = world.shuffle_ganon_bosskey != 'on_lacs'
            if world.shuffle_ganon_bosskey == 'on_lacs':
                # make sure the card is shuffled but the vanilla location is Ganon's boss key
                pool.append('Gerudo Membership Card')
                vanilla_item = 'Boss Key (Ganons Castle)'
        elif location in ('KF Shop Item 8', 'Kak Bazaar Item 4', 'Market Bazaar Item 4'):
            if world.shopsanity == 'off' and world.bombchus_in_logic:
                vanilla_item = 'Buy Bombchu (5)'

        if loc_type in ('Drop', 'Event', 'Hint', 'HintStone'):
            shuffle_condition = False
        elif loc_type == 'GS Token':
            if scene >= 0x0A:
                shuffle_condition = world.tokensanity in ('overworld', 'all')
            else:
                shuffle_condition = world.tokensanity in ('dungeons', 'all')
        elif loc_type == 'Shop':
            shuffle_condition = world.shopsanity != 'off'
            if vanilla_item in remain_shop_items:
                convert_vanilla_item = False
                remain_shop_items.remove(vanilla_item)
                num_shop_slots -= 1
            elif len(remain_shop_items) >= num_shop_slots:
                pass # all remaining shop slots should be filled with remain-shop items, so move this one to the main item pool
            else:
                convert_vanilla_item = False
                num_shop_slots -= 1

        if vanilla_item in ('Bombchus (5)', 'Bombchus (10)', 'Bombchus (20)'):
            if world.bombchus_in_logic and (world.shuffle_medigoron_carpet_salesman or location != 'Wasteland Bombchu Salesman'):
                vanilla_item = 'Bombchus'
        elif vanilla_item == 'Gerudo Membership Card':
            shuffle_condition = world.gerudo_fortress != 'open' and world.shuffle_gerudo_card
            if world.gerudo_fortress == 'open' and world.shuffle_gerudo_card:
                # make sure the card is shuffled but the vanilla location is junk
                pool.append('Gerudo Membership Card')
                vanilla_item = IGNORE_LOCATION
        elif vanilla_item == 'Ice Trap':
            if world.junk_ice_traps == 'off':
                vanilla_item = None
        elif vanilla_item == 'Kokiri Sword':
            shuffle_condition = world.shuffle_kokiri_sword
        elif vanilla_item == 'Magic Bean':
            shuffle_condition = world.shuffle_beans
            if world.shuffle_beans and world.distribution.get_starting_item('Magic Bean') >= 10:
                vanilla_item = None
        elif vanilla_item == 'Ocarina':
            shuffle_condition = world.shuffle_ocarinas
        elif vanilla_item == 'Piece of Heart':
            if world.item_pool_value == 'plentiful':
                # replace heart pieces with heart containers, leaving room for extra major items
                removed_heart_pieces += 1
                if removed_heart_pieces == 4:
                    removed_heart_pieces = 0
                    vanilla_item = 'Heart Container'
                else:
                    vanilla_item = None
        elif vanilla_item == 'Pocket Egg':
            earliest_trade = trade_item_options.index(world.logic_earliest_adult_trade)
            latest_trade = trade_item_options.index(world.logic_latest_adult_trade)
            if earliest_trade > latest_trade:
                earliest_trade, latest_trade = latest_trade, earliest_trade
            trade_item = random.choice(tradeitems[earliest_trade:latest_trade + 1])
            world.selected_adult_trade_item = trade_item
            vanilla_item = trade_item
        elif vanilla_item == 'Rupees (5)':
            if world.shopsanity not in ('off', '0') and rupee_upgrades:
                vanilla_item = rupee_upgrades.pop()
        elif vanilla_item == 'Rutos Letter':
            if world.zora_fountain == 'open':
                vanilla_item = random.choice(normal_bottles)
        elif vanilla_item == 'Weird Egg':
            shuffle_condition = world.shuffle_weird_egg and not world.skip_child_zelda
            if world.skip_child_zelda:
                vanilla_item = IGNORE_LOCATION
        elif vanilla_item in normal_bottles:
            if world.item_pool_value == 'plentiful' and not extra_rutos_letter:
                # Ruto's letter needs special handling in plentiful because it replaces a bottle, not a junk item
                vanilla_item = 'Rutos Letter'
                extra_rutos_letter = True

        if vanilla_item in (*junk_pool_base, 'Recovery Heart', 'Bombs (20)', 'Arrows (30)'):
            # checked here because it should not apply to the extra wallet in shopsanity created by the 'Rupees (5)' check
            if world.junk_ice_traps == 'onslaught':
                vanilla_item = None

        vanilla_item_type, _, _, _ = item_table.get(vanilla_item, (None, ..., ..., ...))
        if vanilla_item_type == 'BossKey':
            shuffle_condition = world.shuffle_bosskeys != 'vanilla'
            if world.shuffle_bosskeys == 'remove':
                world.state.collect(ItemFactory(vanilla_item))
                vanilla_item = None
        elif vanilla_item_type == 'SmallKey':
            shuffle_condition = world.shuffle_smallkeys != 'vanilla'
            if world.shuffle_smallkeys == 'remove':
                world.state.collect(ItemFactory(vanilla_item))
                vanilla_item = None
        elif vanilla_item_type in ('Compass', 'Map'):
            shuffle_condition = world.shuffle_mapcompass != 'vanilla'
            if world.shuffle_mapcompass == 'remove' or world.shuffle_mapcompass == 'startwith':
                world.state.collect(ItemFactory(vanilla_item))
                vanilla_item = None

        if 'Cow' in categories:
            shuffle_condition = world.shuffle_cows
        elif 'Deku Scrub' in categories and 'Deku Scrub Upgrades' not in categories:
            shuffle_condition = world.shuffle_scrubs != 'off'
            if world.shuffle_scrubs != 'off' and vanilla_item in ('Buy Deku Seeds (30)', 'Buy Arrows (30)'):
                # in vanilla, these scrubs sell Deku seeds as child and arrows as adult
                vanilla_item = 'Arrows (30)' if random.randint(0, 3) > 0 else 'Deku Seeds (30)'

        if shuffle_condition:
            if convert_vanilla_item:
                vanilla_item = converted_item(vanilla_item)
            if vanilla_item is not None:
                pool.append(vanilla_item)
        else:
            if vanilla_item is not None:
                placed_items[location] = vanilla_item

    pool += ['Piece of Heart'] * removed_heart_pieces

    if world.item_pool_value == 'plentiful':
        pool += filter(lambda item: item in pool, plentiful_extra_items)
        if world.shuffle_song_items == 'any':
            # songs need special handling in plentiful because there are only extra copies if they're shuffled anywhere
            pool += songlist

    if world.free_scarecrow:
        world.state.collect(ItemFactory('Scarecrow Song'))

    if world.no_epona_race:
        world.state.collect(ItemFactory('Epona', event=True))

    # Logic cannot handle the vanilla key layout in some dungeons.
    # This is because vanilla expects the dungeon major items to be
    # locked behind the keys, which is not always true in rando.
    # We can resolve this by starting with some extra keys...
    if world.shuffle_smallkeys == 'vanilla' and world.dungeon_mq['Spirit Temple']:
        # Yes somehow you need 3 keys. This dungeon is bonkers
        world.state.collect(ItemFactory(['Small Key (Spirit Temple)'] * 3))

    # ...or by unlocking some of the doors.
    if not world.keysanity and not world.dungeon_mq['Fire Temple']:
        # The door to the Boss Key Chest in Fire Temple is unlocked in these settings.
        world.state.collect(ItemFactory('Small Key (Fire Temple)'))

    if world.triforce_hunt:
        triforce_count = int((TriforceCounts[world.item_pool_value] * world.triforce_goal_per_world).to_integral_value(rounding=ROUND_HALF_UP))
        pool += ['Triforce Piece'] * triforce_count

    if world.item_pool_value in item_pool_max:
        # reduce item counts for minimal/scarce
        max_counts = item_pool_max[world.item_pool_value].copy()
        if world.damage_multiplier in ('quadruple', 'ohko'):
            max_counts['Nayrus Love'] = 1
        counts = defaultdict(int)
        new_pool = []
        for item in pool:
            if item not in max_counts or counts[item] < max_counts[item]:
                new_pool.append(item)
                counts[item] += 1
        pool = new_pool

    world.distribution.alter_pool(world, pool)
    world.distribution.configure_starting_items_settings(world)
    world.distribution.collect_starters(world.state)

    return (pool, placed_items)

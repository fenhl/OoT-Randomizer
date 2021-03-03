import random
from Utils import random_choices
from Item import ItemFactory
from ItemList import item_table
from LocationList import dungeons, location_table
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
    'plentiful': {},
    'balanced': {},
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
    'Bottle with Blue Fire']


dungeon_rewards = [
    'Kokiri Emerald',
    'Goron Ruby',
    'Zora Sapphire',
    'Forest Medallion',
    'Fire Medallion',
    'Water Medallion',
    'Shadow Medallion',
    'Spirit Medallion',
    'Light Medallion'
]


normal_rupees = (
    ['Rupees (5)'] * 13 +
    ['Rupees (20)'] * 5 +
    ['Rupees (50)'] * 7 +
    ['Rupees (200)'] * 3)

shopsanity_rupees = (
    ['Rupees (5)'] * 2 +
    ['Rupees (20)'] * 10 +
    ['Rupees (50)'] * 10 +
    ['Rupees (200)'] * 5 +
    ['Progressive Wallet'])


vanilla_shop_items = {
    name: data[4]
    for name, data in location_table.items()
    if data[0] == 'Shop'
}


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
    ['Buy Fish'])


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
    'Requiem of Spirit']


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
    'Claim Check')

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
    'claim_check')


# a useless placeholder item placed at locations that aren't accessible
# (e.g. HC Malon Egg with Skip Child Zelda, or the carpenters with Open Gerudo Fortress)
IGNORE_LOCATION = 'Ice Trap'


vanillaBK = {
    name: data[4]
    for name, data in location_table.items()
    if data[4] is not None and item_table[data[4]][0] == 'BossKey'
}

vanillaMC = {
    name: data[4]
    for name, data in location_table.items()
    if data[4] is not None and item_table[data[4]][0] in ('Compass', 'Map')
}

vanillaSK = {
    name: data[4]
    for name, data in location_table.items()
    if data[4] is not None and item_table[data[4]][0] == 'SmallKey'
}

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

pending_junk_pool = []
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

exclude_from_major = [ 
    'Deliver Letter',
    'Sell Big Poe',
    'Magic Bean',
    'Zeldas Letter',
    'Bombchus (5)',
    'Bombchus (10)',
    'Bombchus (20)',
    'Odd Potion',
    'Triforce Piece'
]

item_groups = {
    'Junk': remove_junk_items,
    'JunkSong': ('Prelude of Light', 'Serenade of Water'),
    'AdultTrade': tradeitems,
    'Bottle': normal_bottles,
    'Spell': ('Dins Fire', 'Farores Wind', 'Nayrus Love'),
    'Shield': ('Deku Shield', 'Hylian Shield'),
    'Song': songlist,
    'NonWarpSong': songlist[0:6],
    'WarpSong': songlist[6:],
    'HealthUpgrade': ('Heart Container', 'Piece of Heart'),
    'ProgressItem': [name for (name, data) in item_table.items() if data[0] == 'Item' and data[1]],
    'MajorItem': [name for (name, data) in item_table.items() if (data[0] == 'Item' or data[0] == 'Song') and data[1] and name not in exclude_from_major],
    'DungeonReward': dungeon_rewards,

    'ForestFireWater': ('Forest Medallion', 'Fire Medallion', 'Water Medallion'),
    'FireWater': ('Fire Medallion', 'Water Medallion'),
}


def get_junk_item(count=1, pool=None, plando_pool=None):
    if count < 1:
        raise ValueError("get_junk_item argument 'count' must be greater than 0.")

    return_pool = []
    if pending_junk_pool:
        pending_count = min(len(pending_junk_pool), count)
        return_pool = [pending_junk_pool.pop() for _ in range(pending_count)]
        count -= pending_count

    if pool and plando_pool:
        jw_list = [(junk, weight) for (junk, weight) in junk_pool
                   if junk not in plando_pool or pool.count(junk) < plando_pool[junk].count]
        try:
            junk_items, junk_weights = zip(*jw_list)
        except ValueError:
            raise RuntimeError("Not enough junk is available in the item pool to replace removed items.")
    else:
        junk_items, junk_weights = zip(*junk_pool)
    return_pool.extend(random_choices(junk_items, weights=junk_weights, k=count))

    return return_pool


def converted_item(item):
    """
    Replaces items that aren't suitable for being shuffled with ones that are.
    May return None to indicate that it should be shuffled as a random junk item.
    """
    return {
        'Buy Arrows (30)': 'Arrows (30)',
        'Buy Bombs (5) [35]': 'Bombs (5)',
        'Buy Deku Nut (5)': 'Deku Nut (5)',
        'Buy Deku Seeds (30)': 'Deku Seeds (30)',
        'Buy Deku Shield': 'Deku Shield',
        'Buy Deku Stick (1)': 'Deku Stick (1)',
        'Buy Green Potion': None,
        'Buy Red Potion [30]': None,
        'Magic Bean': 'Magic Bean Pack',
        'Milk': None,
    }.get(item, item)


def matches_mq(world, categories):
    return all(
        ('Master Quest' if world.dungeon_mq[dungeon.replace("'", '')] else 'Vanilla') in categories
        for dungeon in dungeons
        if dungeon in categories
    )


def replace_max_item(items, item, max):
    count = 0
    for i,val in enumerate(items):
        if val == item:
            if count >= max:
                items[i] = get_junk_item()[0]
            count += 1


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


def get_pool_core(world):
    pool = []
    placed_items = {}

    extra_rutos_letter = False
    removed_heart_pieces = 0

    for location, (loc_type, scene, _, _, vanilla_item, categories) in location_table.items():
        categories = categories or ()
        if not matches_mq(world, categories):
            continue

        shuffle_condition = True # most locations are always shuffled

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

        if vanilla_item in ('Bombchus (5)', 'Bombchus (10)', 'Bombchus (20)'):
            if world.bombchus_in_logic and (world.shuffle_medigoron_carpet_salesman or location != 'Wasteland Bombchu Salesman'):
                vanilla_item = 'Bombchus'
        elif vanilla_item == 'Gerudo Membership Card':
            shuffle_condition = world.gerudo_fortress != 'open' and world.shuffle_gerudo_card
            if world.gerudo_fortress == 'open' and world.shuffle_gerudo_card:
                # make sure the card is shuffled but the vanilla location is junk
                pool.append('Gerudo Membership Card')
                vanilla_item = IGNORE_LOCATION
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

        if 'Cow' in categories:
            shuffle_condition = world.shuffle_cows
        elif 'Deku Scrub' in categories and 'Deku Scrub Upgrades' not in categories:
            shuffle_condition = world.shuffle_scrubs != 'off'
            if world.shuffle_scrubs != 'off' and vanilla_item in ('Buy Deku Seeds (30)', 'Buy Arrows (30)'):
                vanilla_item = 'Arrows (30)' if random.randint(0, 3) > 0 else 'Deku Seeds (30)'

        if shuffle_condition:
            converted_vanilla_item = converted_item(vanilla_item)
            if converted_vanilla_item is not None:
                pool.append(converted_vanilla_item)
        else:
            placed_items[location] = vanilla_item

    pool += ['Piece of Heart'] * removed_heart_pieces

    if world.shopsanity != 'off':
        remain_shop_items = list(vanilla_shop_items.values())
        pool.extend(min_shop_items)
        for item in min_shop_items:
            remain_shop_items.remove(item)

        shop_slots_count = len(remain_shop_items)
        shop_nonitem_count = len(world.shop_prices)
        shop_item_count = shop_slots_count - shop_nonitem_count

        pool.extend(random.sample(remain_shop_items, shop_item_count))
        if shop_nonitem_count:
            pool.extend(get_junk_item(shop_nonitem_count))
        if world.shopsanity == '0':
            pool.extend(normal_rupees)
        else:
            pool.extend(shopsanity_rupees)

    if world.shuffle_song_items == 'any' and world.item_pool_value == 'plentiful':
        # songs need special handling in plentiful because there are only extra copies if they're shuffled anywhere
        pending_junk_pool.extend(songlist)

    if world.free_scarecrow:
        world.state.collect(ItemFactory('Scarecrow Song'))

    if world.no_epona_race:
        world.state.collect(ItemFactory('Epona', event=True))

    if world.shuffle_mapcompass == 'remove' or world.shuffle_mapcompass == 'startwith':
        for item in [item for dungeon in world.dungeons for item in dungeon.dungeon_items]:
            world.state.collect(item)
            pool.extend(get_junk_item())
    if world.shuffle_smallkeys == 'remove':
        for item in [item for dungeon in world.dungeons for item in dungeon.small_keys]:
            world.state.collect(item)
            pool.extend(get_junk_item())
    if world.shuffle_bosskeys == 'remove':
        for item in [item for dungeon in world.dungeons if dungeon.name != 'Ganons Castle' for item in dungeon.boss_key]:
            world.state.collect(item)
            pool.extend(get_junk_item())
    if world.shuffle_ganon_bosskey in ['remove', 'triforce']:
        for item in [item for dungeon in world.dungeons if dungeon.name == 'Ganons Castle' for item in dungeon.boss_key]:
            world.state.collect(item)
            pool.extend(get_junk_item())

    if world.shuffle_mapcompass == 'vanilla':
        for location, item in vanillaMC.items():
            try:
                world.get_location(location)
                placed_items[location] = item
            except KeyError:
                continue
    if world.shuffle_smallkeys == 'vanilla':
        for location, item in vanillaSK.items():
            try:
                world.get_location(location)
                placed_items[location] = item
            except KeyError:
                continue
        # Logic cannot handle vanilla key layout in some dungeons
        # this is because vanilla expects the dungeon major item to be
        # locked behind the keys, which is not always true in rando.
        # We can resolve this by starting with some extra keys
        if world.dungeon_mq['Spirit Temple']:
            # Yes somehow you need 3 keys. This dungeon is bonkers
            world.state.collect(ItemFactory('Small Key (Spirit Temple)'))
            world.state.collect(ItemFactory('Small Key (Spirit Temple)'))
            world.state.collect(ItemFactory('Small Key (Spirit Temple)'))
    if world.shuffle_bosskeys == 'vanilla':
        for location, item in vanillaBK.items():
            try:
                world.get_location(location)
                placed_items[location] = item
            except KeyError:
                continue

    if not world.keysanity and not world.dungeon_mq['Fire Temple']:
        world.state.collect(ItemFactory('Small Key (Fire Temple)'))

    if world.triforce_hunt:
        triforce_count = int((TriforceCounts[world.item_pool_value] * world.triforce_goal_per_world).to_integral_value(rounding=ROUND_HALF_UP))
        pending_junk_pool.extend(['Triforce Piece'] * triforce_count)

    if world.shuffle_ganon_bosskey == 'on_lacs':
        placed_items['ToT Light Arrows Cutscene'] = 'Boss Key (Ganons Castle)'
    elif world.shuffle_ganon_bosskey == 'vanilla':
        placed_items['Ganons Tower Boss Key Chest'] = 'Boss Key (Ganons Castle)'

    if world.item_pool_value == 'plentiful':
        pool += filter(lambda item: item in pool, plentiful_extra_items)

    if not world.shuffle_kokiri_sword:
        replace_max_item(pool, 'Kokiri Sword', 0)

    if world.junk_ice_traps == 'off':
        replace_max_item(pool, 'Ice Trap', 0)
    elif world.junk_ice_traps == 'onslaught':
        for item in [item for item, weight in junk_pool_base] + ['Recovery Heart', 'Bombs (20)', 'Arrows (30)']:
            replace_max_item(pool, item, 0)

    for item, max in item_pool_max[world.item_pool_value].items():
        replace_max_item(pool, item, max)

    if world.damage_multiplier in ['ohko', 'quadruple'] and world.item_pool_value == 'minimal':
        pending_junk_pool.append('Nayrus Love')

    world.distribution.alter_pool(world, pool)

    # Make sure our pending_junk_pool is empty. If not, remove some random junk here.
    if pending_junk_pool:
        for item in set(pending_junk_pool):
            # Ensure pending_junk_pool contents don't exceed values given by distribution file
            if item in world.distribution.item_pool:
                while pending_junk_pool.count(item) > world.distribution.item_pool[item].count:
                    pending_junk_pool.remove(item)
                # Remove pending junk already added to the pool by alter_pool from the pending_junk_pool
                if item in pool:
                    count = min(pool.count(item), pending_junk_pool.count(item))
                    for _ in range(count):
                        pending_junk_pool.remove(item)

        remove_junk_pool, _ = zip(*junk_pool_base)
        # Omits Rupees (200) and Deku Nuts (10)
        remove_junk_pool = list(remove_junk_pool) + ['Recovery Heart', 'Bombs (20)', 'Arrows (30)', 'Ice Trap']

        junk_candidates = [item for item in pool if item in remove_junk_pool]
        while pending_junk_pool:
            pending_item = pending_junk_pool.pop()
            if not junk_candidates:
                raise RuntimeError("Not enough junk exists in item pool for %s to be added." % pending_item)
            junk_item = random.choice(junk_candidates)
            junk_candidates.remove(junk_item)
            pool.remove(junk_item)
            pool.append(pending_item)

    world.distribution.configure_starting_items_settings(world)
    world.distribution.collect_starters(world.state)

    return (pool, placed_items)

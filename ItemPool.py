from collections import namedtuple
import logging
import random
from itertools import chain
from Utils import random_choices
from Item import ItemFactory
from ItemList import item_table
from LocationList import dungeons, location_groups, location_table
from decimal import Decimal, ROUND_HALF_UP


# Generates itempools and places fixed items based on settings.

alwaysitems = ([
    'Biggoron Sword',
    'Boomerang',
    'Lens of Truth',
    'Megaton Hammer',
    'Iron Boots',
    'Goron Tunic',
    'Zora Tunic',
    'Hover Boots',
    'Mirror Shield',
    'Stone of Agony',
    'Fire Arrows',
    'Ice Arrows',
    'Light Arrows',
    'Dins Fire',
    'Farores Wind',
    'Nayrus Love',
    'Rupee (1)']
    + ['Progressive Hookshot'] * 2
    + ['Deku Shield']
    + ['Hylian Shield']
    + ['Progressive Strength Upgrade'] * 3
    + ['Progressive Scale'] * 2
    + ['Recovery Heart'] * 6
    + ['Bow'] * 3
    + ['Slingshot'] * 3
    + ['Bomb Bag'] * 3
    + ['Bombs (5)'] * 2
    + ['Bombs (10)']
    + ['Bombs (20)']
    + ['Arrows (5)']
    + ['Arrows (10)'] * 5
    + ['Progressive Wallet'] * 2
    + ['Magic Meter'] * 2
    + ['Double Defense']
    + ['Deku Stick Capacity'] * 2
    + ['Deku Nut Capacity'] * 2
    + ['Piece of Heart (Treasure Chest Game)'])


easy_items = ([
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
    'Double Defense'] +
    ['Heart Container'] * 16 +
    ['Piece of Heart'] * 3)

normal_items = (
    ['Heart Container'] * 8 +
    ['Piece of Heart'] * 35)


item_difficulty_max = {
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

DT_vanilla = (
    ['Recovery Heart'] * 2)

DT_MQ = (
    ['Deku Shield'] * 2 +
    ['Rupees (50)'])

DC_vanilla = (
    ['Rupees (20)'])

DC_MQ = (
    ['Hylian Shield'] +
    ['Rupees (5)'])

JB_MQ = (
    ['Deku Nuts (5)'] * 4 +
    ['Recovery Heart'] +
    ['Deku Shield'] +
    ['Deku Stick (1)'])

FoT_vanilla = (
    ['Recovery Heart'] +
    ['Arrows (10)'] +
    ['Arrows (30)'])

FoT_MQ = (
    ['Arrows (5)'])

FiT_vanilla = (
    ['Rupees (200)'])

FiT_MQ = (
    ['Bombs (20)'] +
    ['Hylian Shield'])

SpT_vanilla = (
    ['Deku Shield'] * 2 +
    ['Recovery Heart'] +
    ['Bombs (20)'])

SpT_MQ = (
    ['Rupees (50)'] * 2 +
    ['Arrows (30)'])

ShT_vanilla = (
    ['Arrows (30)'])

ShT_MQ = (
    ['Arrows (5)'] * 2 +
    ['Rupees (20)'])

BW_vanilla = (
    ['Recovery Heart'] +
    ['Bombs (10)'] +
    ['Rupees (200)'] +
    ['Deku Nuts (5)'] +
    ['Deku Nuts (10)'] +
    ['Deku Shield'] +
    ['Hylian Shield'])

GTG_vanilla = (
    ['Arrows (30)'] * 3 +
    ['Rupees (200)'])

GTG_MQ = (
    ['Rupee (Treasure Chest Game)'] * 2 +
    ['Arrows (10)'] +
    ['Rupee (1)'] +
    ['Rupees (50)'])

GC_vanilla = (
    ['Rupees (5)'] * 3 +
    ['Arrows (30)'])

GC_MQ = (
    ['Arrows (10)'] * 2 +
    ['Bombs (5)'] +
    ['Rupees (20)'] +
    ['Recovery Heart'])


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

bottle_count = 4


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


vanilla_deku_scrubs = {
    'ZR Deku Scrub Grotto Rear': 'Buy Red Potion [30]',
    'ZR Deku Scrub Grotto Front': 'Buy Green Potion',
    'SFM Deku Scrub Grotto Rear': 'Buy Red Potion [30]',
    'SFM Deku Scrub Grotto Front': 'Buy Green Potion',
    'LH Deku Scrub Grotto Left': 'Buy Deku Nut (5)',
    'LH Deku Scrub Grotto Right': 'Buy Bombs (5) [35]',
    'LH Deku Scrub Grotto Center': 'Buy Arrows (30)',
    'GV Deku Scrub Grotto Rear': 'Buy Red Potion [30]',
    'GV Deku Scrub Grotto Front': 'Buy Green Potion',
    'LW Deku Scrub Near Deku Theater Right': 'Buy Deku Nut (5)',
    'LW Deku Scrub Near Deku Theater Left': 'Buy Deku Stick (1)',
    'LW Deku Scrub Grotto Rear': 'Buy Arrows (30)',
    'Colossus Deku Scrub Grotto Rear': 'Buy Red Potion [30]',
    'Colossus Deku Scrub Grotto Front': 'Buy Green Potion',
    'DMC Deku Scrub': 'Buy Bombs (5) [35]',
    'DMC Deku Scrub Grotto Left': 'Buy Deku Nut (5)',
    'DMC Deku Scrub Grotto Right': 'Buy Bombs (5) [35]',
    'DMC Deku Scrub Grotto Center': 'Buy Arrows (30)',
    'GC Deku Scrub Grotto Left': 'Buy Deku Nut (5)',
    'GC Deku Scrub Grotto Right': 'Buy Bombs (5) [35]',
    'GC Deku Scrub Grotto Center': 'Buy Arrows (30)',
    'LLR Deku Scrub Grotto Left': 'Buy Deku Nut (5)',
    'LLR Deku Scrub Grotto Right': 'Buy Bombs (5) [35]',
    'LLR Deku Scrub Grotto Center': 'Buy Arrows (30)',
}


deku_scrubs_items = (
    ['Deku Nuts (5)'] * 5 +
    ['Deku Stick (1)'] +
    ['Bombs (5)'] * 5 +
    ['Recovery Heart'] * 4 +
    ['Rupees (5)'] * 4) # ['Green Potion']


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

tradeitemoptions = (
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


fixedlocations = {
    name: location_table[name][4]
    for name in ('Ganon', 'Pierre', 'Deliver Rutos Letter', 'Master Sword Pedestal', 'Market Bombchu Bowling Bombchus')
}

droplocations = {
    name: data[4]
    for name, data in location_table.items()
    if data[0] == 'Drop'
}

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

    fixed_locations = list(filter(lambda loc: loc.name in fixedlocations, world.get_locations()))
    for location in fixed_locations:
        item = fixedlocations[location.name]
        world.push_item(location, ItemFactory(item, world))
        location.locked = True

    drop_locations = list(filter(lambda loc: loc.type == 'Drop', world.get_locations()))
    for drop_location in drop_locations:
        item = droplocations[drop_location.name]
        world.push_item(drop_location, ItemFactory(item, world))
        drop_location.locked = True

    # set up item pool
    (pool, placed_items) = get_pool_core(world)
    world.itempool = ItemFactory(pool, world)
    for (location, item) in placed_items.items():
        world.push_item(location, ItemFactory(item, world))
        world.get_location(location).locked = True

    world.initialize_items()
    world.distribution.set_complete_itempool(world.itempool)


def try_collect_heart_container(world, pool):
    if 'Heart Container' in pool:
        pool.remove('Heart Container')
        pool.extend(get_junk_item())
        world.state.collect(ItemFactory('Heart Container'))
        return True
    return False


def try_collect_pieces_of_heart(world, pool):
    n = pool.count('Piece of Heart') + pool.count('Piece of Heart (Treasure Chest Game)')
    if n >= 4:
        for i in range(4):
            if 'Piece of Heart' in pool:
                pool.remove('Piece of Heart')
                world.state.collect(ItemFactory('Piece of Heart'))
            else:
                pool.remove('Piece of Heart (Treasure Chest Game)')
                world.state.collect(ItemFactory('Piece of Heart (Treasure Chest Game)'))
            pool.extend(get_junk_item())
        return True
    return False


def collect_pieces_of_heart(world, pool):
    success = try_collect_pieces_of_heart(world, pool)
    if not success:
        try_collect_heart_container(world, pool)


def collect_heart_container(world, pool):
    success = try_collect_heart_container(world, pool)
    if not success:
        try_collect_pieces_of_heart(world, pool)


def get_pool_core(world):
    pool = []
    placed_items = {
        'HC Zeldas Letter': 'Zeldas Letter',
    }

    def conditional_locations(condition, locations, *, junk=False):
        """
        If `condition` is true, the items in `locations` are shuffled, and the vanilla items from those locations are added to the item pool. Use `junk` to add that many junk items instead.
        If `condition` is false, the `locations` are set to have their vanilla items.
        """
        nonlocal pool, placed_items

        if condition:
            if junk:
                pool += get_junk_item(len(locations))
            else:
                pool += [
                    location_table[location][4]
                    for location in locations
                ]
        else:
            for location in locations:
                placed_items[location] = location_table[location][4]

    conditional_locations(world.shuffle_kokiri_sword, ['KF Kokiri Sword Chest'])

    ruto_bottles = 1
    if world.zora_fountain == 'open':
        ruto_bottles = 0
    elif world.item_pool_value == 'plentiful':
        ruto_bottles += 1

    if world.skip_child_zelda:
        placed_items['HC Malon Egg'] = 'Recovery Heart'
    else:
        conditional_locations(world.shuffle_weird_egg, ['HC Malon Egg'])

    if world.shuffle_ocarinas:
        pool.extend(['Ocarina'] * 2)
        if world.item_pool_value == 'plentiful':
            pending_junk_pool.append('Ocarina')
    else:
        placed_items['LW Gift from Saria'] = 'Ocarina'
        placed_items['HF Ocarina of Time Item'] = 'Ocarina'

    conditional_locations(world.shuffle_cows, [
        'LLR Stables Left Cow',
        'LLR Stables Right Cow',
        'LLR Tower Left Cow',
        'LLR Tower Right Cow',
        'KF Links House Cow',
        'Kak Impas House Cow',
        'GV Cow',
        'DMT Cow Grotto Cow',
        'HF Cow Grotto Cow',
    ], junk=True)
    conditional_locations(world.shuffle_cows and world.dungeon_mq['Jabu Jabus Belly'], ['Jabu Jabus Belly MQ Cow'], junk=True)

    if world.shuffle_beans:
        if world.distribution.get_starting_item('Magic Bean') < 10:
            pool.append('Magic Bean Pack')
            if world.item_pool_value == 'plentiful':
                pending_junk_pool.append('Magic Bean Pack')
        else:
            pool.extend(get_junk_item())
    else:
        placed_items['ZR Magic Bean Salesman'] = 'Magic Bean'

    conditional_locations(world.shuffle_medigoron_carpet_salesman, ['GC Medigoron'])

    skulltula_locations_final = [
        name
        for name, data in location_table.items()
        if data[5] is not None # has categories
        and 'Skulltulas' in data[5]
        and all(
            ('Master Quest' if world.dungeon_mq[dungeon.replace("'", '')] else 'Vanilla') in data[5]
            for dungeon in dungeons
            if dungeon in data[5]
        )
    ]
    if world.tokensanity == 'off':
        for location in skulltula_locations_final:
            placed_items[location] = 'Gold Skulltula Token'
    elif world.tokensanity == 'dungeons':
        for location in skulltula_locations_final:
            if world.get_location(location).scene >= 0x0A:
                placed_items[location] = 'Gold Skulltula Token'
            else:
                pool.append('Gold Skulltula Token')
    elif world.tokensanity == 'overworld':
        for location in skulltula_locations_final:
            if world.get_location(location).scene < 0x0A:
                placed_items[location] = 'Gold Skulltula Token'
            else:
                pool.append('Gold Skulltula Token')
    else:
        pool.extend(['Gold Skulltula Token'] * 100)

    pool.extend(['Bombchus (5)'] + ['Bombchus (10)'] * 2)
    if world.dungeon_mq['Jabu Jabus Belly']:
            pool.extend(['Bombchus (10)'])
    if world.dungeon_mq['Spirit Temple']:
            pool.extend(['Bombchus (10)'] * 2)
    if not world.dungeon_mq['Bottom of the Well']:
            pool.extend(['Bombchus (10)'])
    if world.dungeon_mq['Gerudo Training Grounds']:
            pool.extend(['Bombchus (10)'])
    if world.dungeon_mq['Ganons Castle']:
        pool.extend(['Bombchus (10)'])
    else:
        pool.extend(['Bombchus (20)'])
    if world.shuffle_medigoron_carpet_salesman:
        pool.append('Bombchus (10)')

    if world.bombchus_in_logic:
        pool = [
            'Bombchus' if item in ('Bombchus (5)', 'Bombchus (10)', 'Bombchus (20)') else item
            for item in pool
        ]

    if not world.shuffle_medigoron_carpet_salesman:
        placed_items['Wasteland Bombchu Salesman'] = 'Bombchus (10)'

    pool.extend(['Ice Trap'])
    if not world.dungeon_mq['Gerudo Training Grounds']:
        pool.extend(['Ice Trap'])
    if not world.dungeon_mq['Ganons Castle']:
        pool.extend(['Ice Trap'] * 4)

    if world.gerudo_fortress == 'open':
        placed_items['GF North F1 Carpenter'] = 'Recovery Heart'
        placed_items['GF North F2 Carpenter'] = 'Recovery Heart'
        placed_items['GF South F1 Carpenter'] = 'Recovery Heart'
        placed_items['GF South F2 Carpenter'] = 'Recovery Heart'
    elif world.shuffle_fortresskeys in ['any_dungeon', 'overworld', 'keysanity']:
        if world.gerudo_fortress == 'fast':
            pool.append('Small Key (Gerudo Fortress)')
            placed_items['GF North F2 Carpenter'] = 'Recovery Heart'
            placed_items['GF South F1 Carpenter'] = 'Recovery Heart'
            placed_items['GF South F2 Carpenter'] = 'Recovery Heart'
        else:
            pool.extend(['Small Key (Gerudo Fortress)'] * 4)
        if world.item_pool_value == 'plentiful':
            pending_junk_pool.append('Small Key (Gerudo Fortress)')
    else:
        if world.gerudo_fortress == 'fast':
            placed_items['GF North F1 Carpenter'] = 'Small Key (Gerudo Fortress)'
            placed_items['GF North F2 Carpenter'] = 'Recovery Heart'
            placed_items['GF South F1 Carpenter'] = 'Recovery Heart'
            placed_items['GF South F2 Carpenter'] = 'Recovery Heart'
        else:
            placed_items['GF North F1 Carpenter'] = 'Small Key (Gerudo Fortress)'
            placed_items['GF North F2 Carpenter'] = 'Small Key (Gerudo Fortress)'
            placed_items['GF South F1 Carpenter'] = 'Small Key (Gerudo Fortress)'
            placed_items['GF South F2 Carpenter'] = 'Small Key (Gerudo Fortress)'

    if world.shuffle_gerudo_card and world.gerudo_fortress != 'open':
        pool.append('Gerudo Membership Card')
    elif world.shuffle_gerudo_card:
        pending_junk_pool.append('Gerudo Membership Card')
        placed_items['GF Gerudo Membership Card'] = 'Ice Trap'
    else:
        placed_items['GF Gerudo Membership Card'] = 'Gerudo Membership Card'
    if world.shuffle_gerudo_card and world.item_pool_value == 'plentiful':
        pending_junk_pool.append('Gerudo Membership Card')

    if world.item_pool_value == 'plentiful' and world.shuffle_smallkeys in ['any_dungeon', 'overworld', 'keysanity']:
        pending_junk_pool.append('Small Key (Bottom of the Well)')
        pending_junk_pool.append('Small Key (Forest Temple)')
        pending_junk_pool.append('Small Key (Fire Temple)')
        pending_junk_pool.append('Small Key (Water Temple)')
        pending_junk_pool.append('Small Key (Shadow Temple)')
        pending_junk_pool.append('Small Key (Spirit Temple)')
        pending_junk_pool.append('Small Key (Gerudo Training Grounds)')
        pending_junk_pool.append('Small Key (Ganons Castle)')

    if world.item_pool_value == 'plentiful' and world.shuffle_bosskeys in ['any_dungeon', 'overworld', 'keysanity']:
        pending_junk_pool.append('Boss Key (Forest Temple)')
        pending_junk_pool.append('Boss Key (Fire Temple)')
        pending_junk_pool.append('Boss Key (Water Temple)')
        pending_junk_pool.append('Boss Key (Shadow Temple)')
        pending_junk_pool.append('Boss Key (Spirit Temple)')

    if world.item_pool_value == 'plentiful' and world.shuffle_ganon_bosskey in ['any_dungeon', 'overworld', 'keysanity']:
        pending_junk_pool.append('Boss Key (Ganons Castle)')

    if world.shopsanity == 'off':
        placed_items.update(vanilla_shop_items)
        if world.bombchus_in_logic:
            placed_items['KF Shop Item 8'] = 'Buy Bombchu (5)'
            placed_items['Market Bazaar Item 4'] = 'Buy Bombchu (5)'
            placed_items['Kak Bazaar Item 4'] = 'Buy Bombchu (5)'
        pool.extend(normal_rupees)

    else:
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

    if world.shuffle_scrubs != 'off':
        if world.dungeon_mq['Deku Tree']:
            pool.append('Deku Shield')
        if world.dungeon_mq['Dodongos Cavern']:
            pool.extend(['Deku Stick (1)', 'Deku Shield', 'Recovery Heart'])
        else:
            pool.extend(['Deku Nuts (5)', 'Deku Stick (1)', 'Deku Shield'])
        if not world.dungeon_mq['Jabu Jabus Belly']:
            pool.append('Deku Nuts (5)')
        if world.dungeon_mq['Ganons Castle']:
            pool.extend(['Bombs (5)', 'Recovery Heart', 'Rupees (5)', 'Deku Nuts (5)'])
        else:
            pool.extend(['Bombs (5)', 'Recovery Heart', 'Rupees (5)'])
        pool.extend(deku_scrubs_items)
        for _ in range(7):
            pool.append('Arrows (30)' if random.randint(0,3) > 0 else 'Deku Seeds (30)')

    else:
        if world.dungeon_mq['Deku Tree']:
            placed_items['Deku Tree MQ Deku Scrub'] = 'Buy Deku Shield'
        if world.dungeon_mq['Dodongos Cavern']:
            placed_items['Dodongos Cavern MQ Deku Scrub Lobby Rear'] = 'Buy Deku Stick (1)'
            placed_items['Dodongos Cavern MQ Deku Scrub Lobby Front'] = 'Buy Deku Seeds (30)'
            placed_items['Dodongos Cavern MQ Deku Scrub Staircase'] = 'Buy Deku Shield'
            placed_items['Dodongos Cavern MQ Deku Scrub Side Room Near Lower Lizalfos'] = 'Buy Red Potion [30]'
        else:
            placed_items['Dodongos Cavern Deku Scrub Near Bomb Bag Left'] = 'Buy Deku Nut (5)'
            placed_items['Dodongos Cavern Deku Scrub Side Room Near Dodongos'] = 'Buy Deku Stick (1)'
            placed_items['Dodongos Cavern Deku Scrub Near Bomb Bag Right'] = 'Buy Deku Seeds (30)'
            placed_items['Dodongos Cavern Deku Scrub Lobby'] = 'Buy Deku Shield'
        if not world.dungeon_mq['Jabu Jabus Belly']:
            placed_items['Jabu Jabus Belly Deku Scrub'] = 'Buy Deku Nut (5)'
        if world.dungeon_mq['Ganons Castle']:
            placed_items['Ganons Castle MQ Deku Scrub Right'] = 'Buy Deku Nut (5)'
            placed_items['Ganons Castle MQ Deku Scrub Center-Left'] = 'Buy Bombs (5) [35]'
            placed_items['Ganons Castle MQ Deku Scrub Center'] = 'Buy Arrows (30)'
            placed_items['Ganons Castle MQ Deku Scrub Center-Right'] = 'Buy Red Potion [30]'
            placed_items['Ganons Castle MQ Deku Scrub Left'] = 'Buy Green Potion'
        else:
            placed_items['Ganons Castle Deku Scrub Center-Left'] = 'Buy Bombs (5) [35]'
            placed_items['Ganons Castle Deku Scrub Center-Right'] = 'Buy Arrows (30)'
            placed_items['Ganons Castle Deku Scrub Right'] = 'Buy Red Potion [30]'
            placed_items['Ganons Castle Deku Scrub Left'] = 'Buy Green Potion'
        placed_items.update(vanilla_deku_scrubs)

    pool.extend(alwaysitems)

    if world.dungeon_mq['Deku Tree']:
        pool.extend(DT_MQ)
    else:
        pool.extend(DT_vanilla)
    if world.dungeon_mq['Dodongos Cavern']:
        pool.extend(DC_MQ)
    else:
        pool.extend(DC_vanilla)
    if world.dungeon_mq['Jabu Jabus Belly']:
        pool.extend(JB_MQ)
    if world.dungeon_mq['Forest Temple']:
        pool.extend(FoT_MQ)
    else:
        pool.extend(FoT_vanilla)
    if world.dungeon_mq['Fire Temple']:
        pool.extend(FiT_MQ)
    else:
        pool.extend(FiT_vanilla)
    if world.dungeon_mq['Spirit Temple']:
        pool.extend(SpT_MQ)
    else:
        pool.extend(SpT_vanilla)
    if world.dungeon_mq['Shadow Temple']:
        pool.extend(ShT_MQ)
    else:
        pool.extend(ShT_vanilla)
    if not world.dungeon_mq['Bottom of the Well']:
        pool.extend(BW_vanilla)
    if world.dungeon_mq['Gerudo Training Grounds']:
        pool.extend(GTG_MQ)
    else:
        pool.extend(GTG_vanilla)
    if world.dungeon_mq['Ganons Castle']:
        pool.extend(GC_MQ)
    else:
        pool.extend(GC_vanilla)

    for i in range(bottle_count):
        if i >= ruto_bottles:
            bottle = random.choice(normal_bottles)
            pool.append(bottle)
        else:
            pool.append('Rutos Letter')

    earliest_trade = tradeitemoptions.index(world.logic_earliest_adult_trade)
    latest_trade = tradeitemoptions.index(world.logic_latest_adult_trade)
    if earliest_trade > latest_trade:
        earliest_trade, latest_trade = latest_trade, earliest_trade
    tradeitem = random.choice(tradeitems[earliest_trade:latest_trade+1])
    world.selected_adult_trade_item = tradeitem
    pool.append(tradeitem)

    pool.extend(songlist)
    if world.shuffle_song_items == 'any' and world.item_pool_value == 'plentiful':
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
        #if not world.dungeon_mq['Fire Temple']:
        #    world.state.collect(ItemFactory('Small Key (Fire Temple)'))
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
        pool.extend(easy_items)
    else:
        pool.extend(normal_items)

    if not world.shuffle_kokiri_sword:
        replace_max_item(pool, 'Kokiri Sword', 0)

    if world.junk_ice_traps == 'off':
        replace_max_item(pool, 'Ice Trap', 0)
    elif world.junk_ice_traps == 'onslaught':
        for item in [item for item, weight in junk_pool_base] + ['Recovery Heart', 'Bombs (20)', 'Arrows (30)']:
            replace_max_item(pool, item, 0)

    for item,max in item_difficulty_max[world.item_pool_value].items():
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

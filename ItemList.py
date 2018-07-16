from collections import namedtuple
import logging
import random

from Items import ItemFactory

#This file sets the item pools for various modes. Timed modes and triforce hunt are enforced first, and then extra items are specified per mode to fill in the remaining space.
#Some basic items that various modes require are placed here, including pendants and crystals. Medallion requirements for the two relevant entrances are also decided.

alwaysitems = (['Kokiri Sword', 'Biggoron Sword', 'Boomerang', 'Lens of Truth', 'Hammer', 'Iron Boots', 'Goron Tunic', 'Zora Tunic', 'Hover Boots', 'Mirror Shield', 'Stone of Agony', 'Fire Arrows', 'Ice Arrows', 'Light Arrows', 'Dins Fire', 'Farores Wind', 'Nayrus Love', 'Rupee (1)'] + ['Progressive Hookshot'] * 2 + ['Deku Shield'] * 4 +  ['Hylian Shield'] * 2 + ['Ice Trap'] * 6 +
              ['Progressive Strength Upgrade'] * 3 + ['Progressive Scale'] * 2 + ['Piece of Heart'] * 35 + ['Recovery Heart'] * 11 + ['Rupees (5)'] * 17 + ['Rupees (20)'] * 5 + ['Rupees (50)'] * 7 + ['Rupees (200)'] * 6 + ['Bow'] * 3 + ['Slingshot'] * 3 + ['Bomb Bag'] * 3 + ['Bottle with Letter'] + ['Heart Container'] * 8 + ['Piece of Heart (Treasure Chest Game)'] +
              ['Bombs (5)'] * 2 + ['Bombs (10)'] * 2 + ['Bombs (20)'] * 2 + ['Arrows (5)'] + ['Arrows (10)'] * 6 + ['Arrows (30)'] * 6 + ['Deku Nuts (5)'] + ['Deku Nuts (10)'] + ['Progressive Wallet'] * 2 + ['Deku Stick Capacity'] * 2 + ['Deku Nut Capacity'] * 2 + ['Magic Meter'] * 2 + ['Double Defense'])
# normal_bottles = ['Bottle', 'Bottle with Milk', 'Bottle with Red Potion', 'Bottle with Green Potion', 'Bottle with Blue Potion', 'Bottle with Fairy', 'Bottle with Fish', 'Bottle with Blue Fire', 'Bottle with Bugs', 'Bottle with Poe']
normal_bottles = ['Bottle', 'Bottle with Milk', 'Bottle with Red Potion', 'Bottle with Green Potion', 'Bottle with Blue Potion', 'Bottle with Fairy', 'Bottle with Fish', 'Bottle with Bugs', 'Bottle with Poe']
normal_bottle_count = 3
# notmapcompass = ['Rupees (5)'] * 20
notmapcompass = ['Bombs (5)'] * 4 + ['Arrows (5)'] * 3 + ['Deku Nuts (5)'] * 3 + ['Rupees (5)'] * 7 + ['Rupees (20)'] * 2 + ['Rupees (50)']
rewardlist = ['Kokiri Emerald', 'Goron Ruby', 'Zora Sapphire', 'Forest Medallion', 'Fire Medallion', 'Water Medallion', 'Spirit Medallion', 'Shadow Medallion', 'Light Medallion']
songlist = ['Zeldas Lullaby', 'Eponas Song', 'Suns Song', 'Sarias Song', 'Song of Time', 'Song of Storms', 'Minuet of Forest', 'Prelude of Light', 'Bolero of Fire', 'Serenade of Water', 'Nocturne of Shadow', 'Requiem of Spirit']
skulltulla_locations = (['GS1', 'GS2', 'GS3', 'GS4', 'GS5', 'GS6', 'GS7', 'GS8', 'GS9', 'GS10', 'GS11', 'GS12', 'GS13', 'GS14', 'GS15', 'GS16', 'GS17', 'GS18', 'GS19', 'GS20'] +
                       ['GS21', 'GS22', 'GS23', 'GS24', 'GS25', 'GS26', 'GS27', 'GS28', 'GS29', 'GS30', 'GS31', 'GS32', 'GS33', 'GS34', 'GS35', 'GS36', 'GS37', 'GS38', 'GS39', 'GS40'] +
                       ['GS41', 'GS42', 'GS43', 'GS44', 'GS45', 'GS46', 'GS47', 'GS48', 'GS49', 'GS50', 'GS51', 'GS52', 'GS53', 'GS54', 'GS55', 'GS56', 'GS57', 'GS58', 'GS59', 'GS60'] +
                       ['GS61', 'GS62', 'GS63', 'GS64', 'GS65', 'GS66', 'GS67', 'GS68', 'GS69', 'GS70', 'GS71', 'GS72', 'GS73', 'GS74', 'GS75', 'GS76', 'GS77', 'GS78', 'GS79', 'GS80'] +
                       ['GS81', 'GS82', 'GS83', 'GS84', 'GS85', 'GS86', 'GS87', 'GS88', 'GS89', 'GS90', 'GS91', 'GS92', 'GS93', 'GS94', 'GS95', 'GS96', 'GS97', 'GS98', 'GS99', 'GS100'])
tradeitems = ['Pocket Egg', 'Pocket Cucco', 'Cojiro', 'Odd Mushroom', 'Poachers Saw', 'Broken Sword', 'Prescription', 'Eyeball Frog', 'Eyedrops', 'Claim Check']

eventlocations = {
    'Ganon': 'Triforce',
    'Zeldas Letter': 'Zeldas Letter',
    'Magic Bean Salesman': 'Magic Bean',
    'King Zora Moves': 'Bottle',
    'Ocarina of Time': 'Ocarina',
    'Master Sword Pedestal': 'Master Sword',
    'Epona': 'Epona',
    'Gerudo Fortress Carpenter Rescue': 'Gerudo Membership Card',
    'Ganons Castle Forest Trial Clear': 'Forest Trial Clear',
    'Ganons Castle Fire Trial Clear': 'Fire Trial Clear',
    'Ganons Castle Water Trial Clear': 'Water Trial Clear',
    'Ganons Castle Shadow Trial Clear': 'Shadow Trial Clear',
    'Ganons Castle Spirit Trial Clear': 'Spirit Trial Clear',
    'Ganons Castle Light Trial Clear': 'Light Trial Clear'
}

#total_items_to_place = 5

def generate_itempool(world):
    for location in skulltulla_locations:
        world.push_item(location, ItemFactory('Gold Skulltulla Token'), False)
        world.get_location(location).event = True

    if not world.shuffle_weird_egg:
        eventlocations['Malon Egg'] = 'Weird Egg'
    if not world.shuffle_fairy_ocarina:
        eventlocations['Gift from Saria'] = 'Ocarina'

    for location, item in eventlocations.items():
        world.push_item(location, ItemFactory(item), False)
        world.get_location(location).event = True

    # set up item pool
    (pool, placed_items) = get_pool_core(world)
    world.itempool = ItemFactory(pool)
    for (location, item) in placed_items:
        world.push_item(location, ItemFactory(item), False)
        world.get_location(location).event = True

    choose_trials(world)
    fill_bosses(world)

    world.initialize_items()


def get_pool_core(world):
    pool = []
    placed_items = []

    if not world.place_dungeon_items:
        pool.extend(notmapcompass)
    if world.shuffle_weird_egg:
        pool.append('Weird Egg')
    if world.shuffle_fairy_ocarina:
        pool.append('Ocarina')

    if world.progressive_bombchus:
        pool.extend(['Bombchus'] * 5)
    else:
        pool.extend(['Bombchus (5)'] + ['Bombchus (10)'] * 3 + ['Bombchus (20)'])

    pool.extend(alwaysitems)
    for _ in range(normal_bottle_count):
        bottle = random.choice(normal_bottles)
        pool.append(bottle)
    tradeitem = random.choice(tradeitems)
    pool.append(tradeitem)
    pool.extend(songlist)

    return (pool, placed_items)

def choose_trials(world):
    num_trials = int(world.trials)
    choosen_trials = random.sample(['Forest', 'Fire', 'Water', 'Spirit', 'Shadow', 'Light'], num_trials)
    for trial in world.skipped_trials:
        if trial not in choosen_trials:
            world.skipped_trials[trial] = True

def fill_bosses(world, bossCount=9):
    boss_rewards = ItemFactory(rewardlist)
    boss_locations = [world.get_location('Queen Gohma'), world.get_location('King Dodongo'), world.get_location('Barinade'), world.get_location('Phantom Ganon'),
                      world.get_location('Volvagia'), world.get_location('Morpha'), world.get_location('Bongo Bongo'), world.get_location('Twinrova'), world.get_location('Links Pocket')]
    placed_prizes = [loc.item.name for loc in boss_locations if loc.item is not None]
    unplaced_prizes = [item for item in boss_rewards if item.name not in placed_prizes]
    empty_boss_locations = [loc for loc in boss_locations if loc.item is None]
    prizepool = list(unplaced_prizes)
    prize_locs = list(empty_boss_locations)

    while bossCount:
        bossCount -= 1
        random.shuffle(prizepool)
        random.shuffle(prize_locs)
        item = prizepool.pop()
        loc = prize_locs.pop()
        world.push_item(loc, item, False)
        world.get_location(loc).event = True

import io
import hashlib
import logging
import os
import struct
import random
from collections import OrderedDict
import urllib.request
from urllib.error import URLError, HTTPError
import json

from HintList import getHint, getHintGroup, Hint, hintExclusions
from Item import MakeEventItem
from Messages import update_message_by_id
from Search import Search
from TextBox import line_wrap
from Utils import random_choices, data_path, read_json


bingoBottlesForHints = (
    "Bottle", "Bottle with Red Potion","Bottle with Green Potion", "Bottle with Blue Potion",
    "Bottle with Fairy", "Bottle with Fish", "Bottle with Blue Fire", "Bottle with Bugs",
    "Bottle with Big Poe", "Bottle with Poe",
)


class GossipStone():
    def __init__(self, name, location):
        self.name = name
        self.location = location
        self.reachable = True


class GossipText():
    def __init__(self, text, colors=None, prefix="They say that "):
        text = prefix + text
        text = text[:1].upper() + text[1:]
        self.text = text
        self.colors = colors


    def to_json(self):
        return {'text': self.text, 'colors': self.colors}


    def __str__(self):
        return get_raw_text(line_wrap(colorText(self)))

#   Abbreviations
#       DMC     Death Mountain Crater
#       DMT     Death Mountain Trail
#       GC      Goron City
#       GV      Gerudo Valley
#       HC      Hyrule Castle
#       HF      Hyrule Field
#       KF      Kokiri Forest
#       LH      Lake Hylia
#       LW      Lost Woods
#       SFM     Sacred Forest Meadow
#       ToT     Temple of Time
#       ZD      Zora's Domain
#       ZF      Zora's Fountain
#       ZR      Zora's River

gossipLocations = {
    0x0405: GossipStone('DMC (Bombable Wall)',              'DMC Gossip Stone'),
    0x0404: GossipStone('DMT (Biggoron)',                   'DMT Gossip Stone'),
    0x041A: GossipStone('Colossus (Spirit Temple)',         'Colossus Gossip Stone'),
    0x0414: GossipStone('Dodongos Cavern (Bombable Wall)',  'Dodongos Cavern Gossip Stone'),
    0x0411: GossipStone('GV (Waterfall)',                   'GV Gossip Stone'),
    0x0415: GossipStone('GC (Maze)',                        'GC Maze Gossip Stone'),
    0x0419: GossipStone('GC (Medigoron)',                   'GC Medigoron Gossip Stone'),
    0x040A: GossipStone('Graveyard (Shadow Temple)',        'Graveyard Gossip Stone'),
    0x0412: GossipStone('HC (Malon)',                       'HC Malon Gossip Stone'),
    0x040B: GossipStone('HC (Rock Wall)',                   'HC Rock Wall Gossip Stone'),
    0x0413: GossipStone('HC (Storms Grotto)',               'HC Storms Grotto Gossip Stone'),
    0x041F: GossipStone('KF (Deku Tree Left)',              'KF Deku Tree Gossip Stone (Left)'),
    0x0420: GossipStone('KF (Deku Tree Right)',             'KF Deku Tree Gossip Stone (Right)'),
    0x041E: GossipStone('KF (Outside Storms)',              'KF Gossip Stone'),
    0x0403: GossipStone('LH (Lab)',                         'LH Lab Gossip Stone'),
    0x040F: GossipStone('LH (Southeast Corner)',            'LH Gossip Stone (Southeast)'),
    0x0408: GossipStone('LH (Southwest Corner)',            'LH Gossip Stone (Southwest)'),
    0x041D: GossipStone('LW (Bridge)',                      'LW Gossip Stone'),
    0x0416: GossipStone('SFM (Maze Lower)',                 'SFM Maze Gossip Stone (Lower)'),
    0x0417: GossipStone('SFM (Maze Upper)',                 'SFM Maze Gossip Stone (Upper)'),
    0x041C: GossipStone('SFM (Saria)',                      'SFM Saria Gossip Stone'),
    0x0406: GossipStone('ToT (Left)',                       'ToT Gossip Stone (Left)'),
    0x0407: GossipStone('ToT (Left-Center)',                'ToT Gossip Stone (Left-Center)'),
    0x0410: GossipStone('ToT (Right)',                      'ToT Gossip Stone (Right)'),
    0x040E: GossipStone('ToT (Right-Center)',               'ToT Gossip Stone (Right-Center)'),
    0x0409: GossipStone('ZD (Mweep)',                       'ZD Gossip Stone'),
    0x0401: GossipStone('ZF (Fairy)',                       'ZF Fairy Gossip Stone'),
    0x0402: GossipStone('ZF (Jabu)',                        'ZF Jabu Gossip Stone'),
    0x040D: GossipStone('ZR (Near Grottos)',                'ZR Near Grottos Gossip Stone'),
    0x040C: GossipStone('ZR (Near Domain)',                 'ZR Near Domain Gossip Stone'),
    0x041B: GossipStone('HF (Cow Grotto)',                  'HF Cow Grotto Gossip Stone'),

    0x0430: GossipStone('HF (Near Market Grotto)',          'HF Near Market Grotto Gossip Stone'),
    0x0432: GossipStone('HF (Southeast Grotto)',            'HF Southeast Grotto Gossip Stone'),
    0x0433: GossipStone('HF (Open Grotto)',                 'HF Open Grotto Gossip Stone'),
    0x0438: GossipStone('Kak (Open Grotto)',                'Kak Open Grotto Gossip Stone'),
    0x0439: GossipStone('ZR (Open Grotto)',                 'ZR Open Grotto Gossip Stone'),
    0x043C: GossipStone('KF (Storms Grotto)',               'KF Storms Grotto Gossip Stone'),
    0x0444: GossipStone('LW (Near Shortcuts Grotto)',       'LW Near Shortcuts Grotto Gossip Stone'),
    0x0447: GossipStone('DMT (Storms Grotto)',              'DMT Storms Grotto Gossip Stone'),
    0x044A: GossipStone('DMC (Upper Grotto)',               'DMC Upper Grotto Gossip Stone'),
}

gossipLocations_reversemap = {
    stone.name : stone_id for stone_id, stone in gossipLocations.items()
}

def getItemGenericName(item):
    if item.dungeonitem:
        return item.type
    else:
        return item.name


def isRestrictedDungeonItem(dungeon, item):
    if (item.map or item.compass) and dungeon.world.shuffle_mapcompass == 'dungeon':
        return item in dungeon.dungeon_items
    if item.smallkey and dungeon.world.shuffle_smallkeys == 'dungeon':
        return item in dungeon.small_keys
    if item.bosskey and dungeon.world.shuffle_bosskeys == 'dungeon':
        return item in dungeon.boss_key
    return False


def add_hint(spoiler, world, groups, gossip_text, count, location=None, force_reachable=False):
    random.shuffle(groups)
    skipped_groups = []
    duplicates = []
    first = True
    success = True
    # early failure if not enough
    if len(groups) < int(count):
        return False
    # Randomly round up, if we have enough groups left
    total = int(random.random() + count) if len(groups) > count else int(count)
    while total:
        if groups:
            group = groups.pop(0)

            if any(map(lambda id: gossipLocations[id].reachable, group)):
                stone_names = [gossipLocations[id].location for id in group]
                stone_locations = [world.get_location(stone_name) for stone_name in stone_names]
                if not first or any(map(lambda stone_location: can_reach_stone(spoiler.worlds, stone_location, location), stone_locations)):
                    if first and location:
                        # just name the event item after the gossip stone directly
                        event_item = None
                        for i, stone_name in enumerate(stone_names):
                            # place the same event item in each location in the group
                            if event_item is None:
                                event_item = MakeEventItem(stone_name, stone_locations[i], event_item)
                            else:
                                MakeEventItem(stone_name, stone_locations[i], event_item)

                        # This mostly guarantees that we don't lock the player out of an item hint
                        # by establishing a (hint -> item) -> hint -> item -> (first hint) loop
                        location.add_rule(world.parser.parse_rule(repr(event_item.name)))

                    total -= 1
                    first = False
                    for id in group:
                        spoiler.hints[world.id][id] = gossip_text
                    # Immediately start choosing duplicates from stones we passed up earlier
                    while duplicates and total:
                        group = duplicates.pop(0)
                        total -= 1
                        for id in group:
                            spoiler.hints[world.id][id] = gossip_text
                else:
                    # Temporarily skip this stone but consider it for duplicates
                    duplicates.append(group)
            else:
                if not force_reachable:
                    # The stones are not readable at all in logic, so we ignore any kind of logic here
                    if not first:
                        total -= 1
                        for id in group:
                            spoiler.hints[world.id][id] = gossip_text
                    else:
                        # Temporarily skip this stone but consider it for duplicates
                        duplicates.append(group)
                else:
                    # If flagged to guarantee reachable, then skip
                    # If no stones are reachable, then this will place nothing
                    skipped_groups.append(group)
        else:
            # Out of groups
            if not force_reachable and len(duplicates) >= total:
                # Didn't find any appropriate stones for this hint, but maybe enough completely unreachable ones.
                # We'd rather not use reachable stones for this.
                unr = [group for group in duplicates if all(map(lambda id: not gossipLocations[id].reachable, group))]
                if len(unr) >= total:
                    duplicates = [group for group in duplicates if group not in unr[:total]]
                    for group in unr[:total]:
                        for id in group:
                            spoiler.hints[world.id][id] = gossip_text
                    # Success
                    break
            # Failure
            success = False
            break
    groups.extend(duplicates)
    groups.extend(skipped_groups)
    return success


def can_reach_stone(worlds, stone_location, location):
    if location == None:
        return True

    old_item = location.item
    location.item = None
    search = Search.max_explore([world.state for world in worlds])
    location.item = old_item

    return (search.spot_access(stone_location)
            and search.state_list[location.world.id].guarantee_hint())


def writeGossipStoneHints(spoiler, world, messages):
    for id, gossip_text in spoiler.hints[world.id].items():
        update_message_by_id(messages, id, str(gossip_text), 0x23)


def filterTrailingSpace(text):
    if text.endswith('& '):
        return text[:-1]
    else:
        return text


hintPrefixes = [
    'a few ',
    'some ',
    'plenty of ',
    'a ',
    'an ',
    'the ',
    '',
]

def getSimpleHintNoPrefix(item):
    hint = getHint(item.name, True).text

    for prefix in hintPrefixes:
        if hint.startswith(prefix):
            # return without the prefix
            return hint[len(prefix):]

    # no prefex
    return hint


def colorText(gossip_text):
    colorMap = {
        'White':      '\x40',
        'Red':        '\x41',
        'Green':      '\x42',
        'Blue':       '\x43',
        'Light Blue': '\x44',
        'Pink':       '\x45',
        'Yellow':     '\x46',
        'Black':      '\x47',
    }

    text = gossip_text.text
    colors = list(gossip_text.colors) if gossip_text.colors is not None else []
    color = 'White'

    while '#' in text:
        splitText = text.split('#', 2)
        if len(colors) > 0:
            color = colors.pop()

        for prefix in hintPrefixes:
            if splitText[1].startswith(prefix):
                splitText[0] += splitText[1][:len(prefix)]
                splitText[1] = splitText[1][len(prefix):]
                break

        splitText[1] = '\x05' + colorMap[color] + splitText[1] + '\x05\x40'
        text = ''.join(splitText)

    return text


def get_hint_area(spot):
    if spot.parent_region.dungeon:
        return spot.parent_region.dungeon.hint
    elif spot.parent_region.hint:
        return spot.parent_region.hint
    # Breadth first search for connected regions with a max depth of 2
    for entrance in spot.parent_region.entrances:
        if entrance.parent_region.hint:
            return entrance.parent_region.hint
    for entrance in spot.parent_region.entrances:
        for entrance2 in entrance.parent_region.entrances:
            if entrance2.parent_region.hint:
                return entrance2.parent_region.hint
    raise RuntimeError('No hint area could be found for %s [World %d]' % (spot, spot.world.id))


def get_woth_hint(spoiler, world, checked):
    locations = spoiler.required_locations[world.id]
    locations = list(filter(lambda location:
        location.name not in checked and \
        not (world.woth_dungeon >= world.hint_dist_user['dungeons_woth_limit'] and \
        location.parent_region.dungeon) and \
        (location.name not in world.hint_type_overrides['woth']) and \
        (location.item.name not in world.item_hint_type_overrides['woth']),
        locations))

    if not locations:
        return None

    location = random.choice(locations)
    checked.add(location.name)

    if location.parent_region.dungeon:
        world.woth_dungeon += 1
        location_text = getHint(location.parent_region.dungeon.name, world.clearer_hints).text
    else:
        location_text = get_hint_area(location)

    if world.triforce_hunt:
        return (GossipText('#%s# is on the path of gold.' % location_text, ['Light Blue']), location)
    else:
        return (GossipText('#%s# is on the way of the hero.' % location_text, ['Light Blue']), location)


def get_barren_hint(spoiler, world, checked):
    areas = list(filter(lambda area:
        area not in checked and \
        not (world.barren_dungeon >= world.hint_dist_user['dungeons_barren_limit'] and \
        world.empty_areas[area]['dungeon']),
        world.empty_areas.keys()))

    if not areas:
        return None

    area_weights = [world.empty_areas[area]['weight'] for area in areas]

    area = random_choices(areas, weights=area_weights)[0]
    if world.empty_areas[area]['dungeon']:
        world.barren_dungeon += 1

    checked.add(area)

    return (GossipText("plundering #%s# is a foolish choice." % area, ['Pink']), None)


def is_not_checked(location, checked):
    return not (location.name in checked or get_hint_area(location) in checked)


def get_good_item_hint(spoiler, world, checked):
    locations = [location for location in world.get_filled_locations()
            if is_not_checked(location, checked) and \
            (location.item.majoritem or \
            location.name in world.added_hint_types['item'] or \
            location.item.name in world.item_added_hint_types['item']) and \
            not location.locked and \
            (location.name not in world.hint_type_overrides['item']) and \
            (location.item.name not in world.item_hint_type_overrides['item'])]
    if not locations:
        return None

    location = random.choice(locations)
    checked.add(location.name)

    item_text = getHint(getItemGenericName(location.item), world.clearer_hints).text
    if location.parent_region.dungeon:
        location_text = getHint(location.parent_region.dungeon.name, world.clearer_hints).text
        return (GossipText('#%s# hoards #%s#.' % (location_text, item_text), ['Green', 'Red']), location)
    else:
        location_text = get_hint_area(location)
        return (GossipText('#%s# can be found at #%s#.' % (item_text, location_text), ['Red', 'Green']), location)


def get_specific_item_hint(spoiler, world, checked):
    itemname = world.item_hints.pop(0)
    if itemname == "Bottle" and world.hint_dist == "bingo":
        locations = [
            location for location in world.get_filled_locations()
            if (is_not_checked(location, checked)
                and location.item.name in bingoBottlesForHints
                and not location.locked)
        ]
    else:
        locations = [
            location for location in world.get_filled_locations()
            if (is_not_checked(location, checked)
                and location.item.name == itemname
                and not location.locked)
        ]
    if not locations:
        return None

    location = random.choice(locations)
    checked.add(location.name)

    item_text = getHint(getItemGenericName(location.item), world.clearer_hints).text
    if location.parent_region.dungeon:
        location_text = getHint(location.parent_region.dungeon.name, world.clearer_hints).text
        return (GossipText('#%s# hoards #%s#.' % (location_text, item_text), ['Green', 'Red']), location)
    else:
        location_text = get_hint_area(location)
        return (GossipText('#%s# can be found at #%s#.' % (item_text, location_text), ['Red', 'Green']), location)


def get_random_location_hint(spoiler, world, checked):
    locations = [location for location in world.get_filled_locations()
            if is_not_checked(location, checked) and \
            location.item.type not in ('Drop', 'Event', 'Shop', 'DungeonReward') and \
            not (location.parent_region.dungeon and \
                isRestrictedDungeonItem(location.parent_region.dungeon, location.item)) and
            not location.locked and \
            (location.name not in world.hint_type_overrides['item']) and \
            (location.item.name not in world.item_hint_type_overrides['item'])]
    if not locations:
        return None

    location = random.choice(locations)
    checked.add(location.name)
    dungeon = location.parent_region.dungeon

    item_text = getHint(getItemGenericName(location.item), world.clearer_hints).text
    if dungeon:
        location_text = getHint(dungeon.name, world.clearer_hints).text
        return (GossipText('#%s# hoards #%s#.' % (location_text, item_text), ['Green', 'Red']), location)
    else:
        location_text = get_hint_area(location)
        return (GossipText('#%s# can be found at #%s#.' % (item_text, location_text), ['Red', 'Green']), location)


def get_specific_hint(spoiler, world, checked, type):
    hintGroup = getHintGroup(type, world)
    hintGroup = list(filter(lambda hint: is_not_checked(world.get_location(hint.name), checked), hintGroup))
    if not hintGroup:
        return None

    hint = random.choice(hintGroup)
    location = world.get_location(hint.name)
    checked.add(location.name)

    if location.name in world.hint_text_overrides:
        location_text = world.hint_text_overrides[location.name]
    else:
        location_text = hint.text
    if '#' not in location_text:
        location_text = '#%s#' % location_text
    item_text = getHint(getItemGenericName(location.item), world.clearer_hints).text

    return (GossipText('%s #%s#.' % (location_text, item_text), ['Green', 'Red']), location)


def get_sometimes_hint(spoiler, world, checked):
    return get_specific_hint(spoiler, world, checked, 'sometimes')


def get_song_hint(spoiler, world, checked):
    return get_specific_hint(spoiler, world, checked, 'song')


def get_overworld_hint(spoiler, world, checked):
    return get_specific_hint(spoiler, world, checked, 'overworld')


def get_dungeon_hint(spoiler, world, checked):
    return get_specific_hint(spoiler, world, checked, 'dungeon')


def get_entrance_hint(spoiler, world, checked):
    if world.entrance_shuffle == 'off':
        return None

    entrance_hints = getHintGroup('entrance', world)
    entrance_hints = list(filter(lambda hint: hint.name not in checked, entrance_hints))
    valid_entrance_hints = [entrance_hint for entrance_hint in entrance_hints if world.get_entrance(entrance_hint.name).shuffled]

    if not valid_entrance_hints:
        return None

    entrance_hint = random.choice(valid_entrance_hints)
    entrance = world.get_entrance(entrance_hint.name)
    checked.add(entrance.name)

    entrance_text = entrance_hint.text

    if '#' not in entrance_text:
        entrance_text = '#%s#' % entrance_text

    connected_region = entrance.connected_region
    if connected_region.dungeon:
        region_text = getHint(connected_region.dungeon.name, world.clearer_hints).text
    else:
        region_text = getHint(connected_region.name, world.clearer_hints).text

    if '#' not in region_text:
        region_text = '#%s#' % region_text

    return (GossipText('%s %s.' % (entrance_text, region_text), ['Light Blue', 'Green']), None)


def get_junk_hint(spoiler, world, checked):
    hints = getHintGroup('junk', world)
    hints = list(filter(lambda hint: hint.name not in checked, hints))
    if not hints:
        return None

    hint = random.choice(hints)
    checked.add(hint.name)

    return (GossipText(hint.text, prefix=''), None)


hint_func = {
    'trial':      lambda spoiler, world, checked: None,
    'always':     lambda spoiler, world, checked: None,
    'woth':       get_woth_hint,
    'barren':     get_barren_hint,
    'item':       get_good_item_hint,
    'sometimes':  get_sometimes_hint,
    'song':       get_song_hint,
    'overworld':  get_overworld_hint,
    'dungeon':    get_dungeon_hint,
    'entrance':   get_entrance_hint,
    'random':     get_random_location_hint,
    'junk':       get_junk_hint,
    'named-item': get_specific_item_hint
}

hint_dist_keys = {
    'trial',
    'always',
    'woth',
    'barren',
    'item',
    'song',
    'overworld',
    'dungeon',
    'entrance',
    'sometimes',
    'random',
    'junk',
    'named-item'
}


def buildBingoHintList(boardURL):
    try:
        with urllib.request.urlopen(boardURL + "/board") as board:
            goalList = board.read()
    except (URLError, HTTPError) as e:
        logger = logging.getLogger('')
        logger.info(f"Could not retrieve board info. Using default bingo hints instead: {e}")
        genericBingo = read_json(data_path('Bingo/generic_bingo_hints.json'))
        return genericBingo['settings']['item_hints']

    # Goal list returned from Bingosync is a sequential list of all of the goals on the bingo board, starting at top-left and moving to the right.
    # Each goal is a dictionary with attributes for name, slot, and colours. The only one we use is the name
    goalList = [goal['name'] for goal in json.loads(goalList)]
    goalHintRequirements = read_json(data_path('Bingo/bingo_goals.json'))

    hintsToAdd = {}
    for goal in goalList:
        # Using 'get' here ensures some level of forward compatibility, where new goals added to randomiser bingo won't
        # cause the generator to crash (though those hints won't have item hints for them)
        requirements = goalHintRequirements.get(goal,{})
        if len(requirements) != 0:
            for item in requirements:
                hintsToAdd[item] = max(hintsToAdd.get(item, 0), requirements[item]['count'])

    # Items to be hinted need to be included in the item_hints list once for each instance you want hinted
    # (e.g. if you want all three strength upgrades to be hintes it needs to be in the list three times)
    hints = []
    for key, value in hintsToAdd.items():
        for _ in range(value):
            hints.append(key)
    return hints



def buildGossipHints(spoiler, worlds):
    checkedLocations = dict()
    # Add Light Arrow locations to "checked" locations if Ganondorf is reachable without it.
    for world in worlds:
        location = world.light_arrow_location
        if location is None:
            continue
        # Didn't you know that Ganondorf is a gossip stone?
        if can_reach_stone(worlds, world.get_location("Ganondorf Hint"), location):
            light_arrow_world = location.world
            if light_arrow_world.id not in checkedLocations:
                checkedLocations[light_arrow_world.id] = set()
            checkedLocations[light_arrow_world.id].add(location.name)

    # Build all the hints.
    for world in worlds:
        world.update_useless_areas(spoiler)
        buildWorldGossipHints(spoiler, world, checkedLocations.pop(world.id, None))


# builds out general hints based on location and whether an item is required or not
def buildWorldGossipHints(spoiler, world, checkedLocations=None):
    # rebuild hint exclusion list
    hintExclusions(world, clear_cache=True)

    world.barren_dungeon = 0
    world.woth_dungeon = 0

    search = Search.max_explore([w.state for w in spoiler.worlds])
    for stone in gossipLocations.values():
        stone.reachable = (
            search.spot_access(world.get_location(stone.location))
            and search.state_list[world.id].guarantee_hint())

    if checkedLocations is None:
        checkedLocations = set()

    stoneIDs = list(gossipLocations.keys())

    world.distribution.configure_gossip(spoiler, stoneIDs)

    if 'disabled' in world.hint_dist_user:
        for stone_name in world.hint_dist_user['disabled']:
            try:
                stone_id = gossipLocations_reversemap[stone_name]
            except KeyError:
                raise ValueError(f'Gossip stone location "{stone_name}" is not valid')
            stoneIDs.remove(stone_id)
            (gossip_text, _) = get_junk_hint(spoiler, world, checkedLocations)
            spoiler.hints[world.id][stone_id] = gossip_text

    stoneGroups = []
    if 'groups' in world.hint_dist_user:
        for group_names in world.hint_dist_user['groups']:
            group = []
            for stone_name in group_names:
                try:
                    stone_id = gossipLocations_reversemap[stone_name]
                except KeyError:
                    raise ValueError(f'Gossip stone location "{stone_name}" is not valid')

                stoneIDs.remove(stone_id)
                group.append(stone_id)
            stoneGroups.append(group)
    # put the remaining locations into singleton groups
    stoneGroups.extend([[id] for id in stoneIDs])

    random.shuffle(stoneGroups)

    # Create list of items for which we want hints. If Bingosync URL is supplied, include items specific to that bingo.
    # If not (or if the URL is invalid), use generic bingo hints
    if world.hint_dist == "bingo":
        bingoDefaults = read_json(data_path('Bingo/generic_bingo_hints.json'))
        if world.bingosync_url is not None and "https://bingosync.com" in world.bingosync_url: # Verify that user actually entered a bingosync URL
            logger = logging.getLogger('')
            logger.info("Got Bingosync URL. Building board-specific goals.")
            world.item_hints = buildBingoHintList(world.bingosync_url)
            world.hint_dist_user = bingoDefaults['settings']['hint_dist_user']
        else:
            world.item_hints = bingoDefaults['settings']['item_hints']
            world.hint_dist_user=bingoDefaults['settings']['hint_dist_user']

        if world.tokensanity in ("overworld", "all") and "Suns Song" not in world.item_hints:
            world.item_hints.append("Suns Song")

        if world.shopsanity != "off" and "Progressive Wallet" not in world.item_hints:
            world.item_hints.append("Progressive Wallet")


    # Load hint distro from distribution file or pre-defined settings
    #
    # 'fixed' key is used to mimic the tournament distribution, creating a list of fixed hint types to fill
    # Once the fixed hint type list is exhausted, weighted random choices are taken like all non-tournament sets
    # This diverges from the tournament distribution where leftover stones are filled with sometimes hints (or random if no sometimes locations remain to be hinted)
    sorted_dist = {}
    type_count = 1
    hint_dist = OrderedDict({})
    fixed_hint_types = []
    max_order = 0
    for hint_type in world.hint_dist_user['distribution']:
        if world.hint_dist_user['distribution'][hint_type]['order'] > 0:
            hint_order = int(world.hint_dist_user['distribution'][hint_type]['order'])
            sorted_dist[hint_order] = hint_type
            if max_order < hint_order:
                max_order = hint_order
            type_count = type_count + 1
    if (type_count - 1) < max_order:
        raise Exception("There are gaps in the custom hint orders. Please revise your plando file to remove them.")
    for i in range(1, type_count):
        hint_type = sorted_dist[i]
        hint_dist[hint_type] = (world.hint_dist_user['distribution'][hint_type]['weight'], world.hint_dist_user['distribution'][hint_type]['copies'])
        hint_dist.move_to_end(hint_type)
        fixed_hint_types.extend([hint_type] * int(world.hint_dist_user['distribution'][hint_type]['fixed']))

    hint_types, hint_prob = zip(*hint_dist.items())
    hint_prob, _ = zip(*hint_prob)

    # Add required location hints
    alwaysLocations = getHintGroup('always', world)
    for hint in alwaysLocations:
        location = world.get_location(hint.name)
        checkedLocations.add(hint.name)

        if location.name in world.hint_text_overrides:
            location_text = world.hint_text_overrides[location.name]
        else:
            location_text = getHint(location.name, world.clearer_hints).text
        if '#' not in location_text:
            location_text = '#%s#' % location_text
        item_text = getHint(getItemGenericName(location.item), world.clearer_hints).text
        add_hint(spoiler, world, stoneGroups, GossipText('%s #%s#.' % (location_text, item_text), ['Green', 'Red']), hint_dist['always'][1], location, force_reachable=True)
        logging.getLogger('').debug('Placed always hint for %s.', location.name)

    # Add trial hints
    if world.trials_random and world.trials == 6:
        add_hint(spoiler, world, stoneGroups, GossipText("#Ganon's Tower# is protected by a powerful barrier.", ['Pink']), hint_dist['trial'][1], force_reachable=True)
    elif world.trials_random and world.trials == 0:
        add_hint(spoiler, world, stoneGroups, GossipText("Sheik dispelled the barrier around #Ganon's Tower#.", ['Yellow']), hint_dist['trial'][1], force_reachable=True)
    elif world.trials < 6 and world.trials > 3:
        for trial,skipped in world.skipped_trials.items():
            if skipped:
                add_hint(spoiler, world, stoneGroups,GossipText("the #%s Trial# was dispelled by Sheik." % trial, ['Yellow']), hint_dist['trial'][1], force_reachable=True)
    elif world.trials <= 3 and world.trials > 0:
        for trial,skipped in world.skipped_trials.items():
            if not skipped:
                add_hint(spoiler, world, stoneGroups, GossipText("the #%s Trial# protects Ganon's Tower." % trial, ['Pink']), hint_dist['trial'][1], force_reachable=True)

    # Add user-specified hinted item locations if using a built-in hint distribution
    # Assume 2 stones/hint
    if len(world.item_hints) > 0 and world.hint_dist_user['named_items_required']:
        for i in range(0, len(world.item_hints)):
            hint = get_specific_item_hint(spoiler, world, checkedLocations)
            if hint == None:
                raise Exception('No valid hints for user-provided item')
            else:
                gossip_text, location = hint
                place_ok = add_hint(spoiler, world, stoneGroups, gossip_text, hint_dist['named-item'][1], location)
                if not place_ok:
                    raise Exception('Not enough gossip stones for user-provided item hints')

    hint_types = list(hint_types)
    hint_prob  = list(hint_prob)
    hint_counts = {}

    custom_fixed = True
    while stoneGroups:
        if fixed_hint_types:
            hint_type = fixed_hint_types.pop(0)
            if hint_dist[hint_type][1] > len(stoneGroups):
                raise Exception('Not enough gossip stone locations for fixed hint type %s.' % hint_type)
        else:
            custom_fixed = False
            # Make sure there are enough stones left for each hint type
            num_types = len(hint_types)
            hint_types = list(filter(lambda htype: hint_dist[htype][1] <= len(stoneGroups), hint_types))
            new_num_types = len(hint_types)
            if new_num_types == 0:
                raise Exception('Not enough gossip stone locations for remaining weighted hint types.')
            elif new_num_types < num_types:
                hint_prob = []
                for htype in hint_types:
                    hint_prob.append(hint_dist[htype][0])
            try:
                # Weight the probabilities such that hints that are over the expected proportion
                # will be drawn less, and hints that are under will be drawn more.
                # This tightens the variance quite a bit. The variance can be adjusted via the power
                weighted_hint_prob = []
                for w1_type, w1_prob in zip(hint_types, hint_prob):
                    p = w1_prob
                    if p != 0: # If the base prob is 0, then it's 0
                        for w2_type, w2_prob in zip(hint_types, hint_prob):
                            if w2_prob != 0: # If the other prob is 0, then it has no effect
                                # Raising this term to a power greater than 1 will decrease variance
                                # Conversely, a power less than 1 will increase variance
                                p = p * (((hint_counts.get(w2_type, 0) / w2_prob) + 1) / ((hint_counts.get(w1_type, 0) / w1_prob) + 1))
                    weighted_hint_prob.append(p)

                hint_type = random_choices(hint_types, weights=weighted_hint_prob)[0]
            except IndexError:
                raise Exception('Not enough valid hints to fill gossip stone locations.')

        hint = hint_func[hint_type](spoiler, world, checkedLocations)

        if hint == None:
            index = hint_types.index(hint_type)
            hint_prob[index] = 0
            # Zero out the probability in the base distribution in case the probability list is modified
            # to fit hint types in remaining gossip stones
            hint_dist[hint_type] = (0.0, hint_dist[hint_type][1])
        else:
            gossip_text, location = hint
            place_ok = add_hint(spoiler, world, stoneGroups, gossip_text, hint_dist[hint_type][1], location)
            if place_ok:
                hint_counts[hint_type] = hint_counts.get(hint_type, 0) + 1
                if location is None:
                    logging.getLogger('').debug('Placed %s hint.', hint_type)
                else:
                    logging.getLogger('').debug('Placed %s hint for %s.', hint_type, location.name)
            if not place_ok and custom_fixed:
                logging.getLogger('').debug('Failed to place %s fixed hint for %s.', hint_type, location.name)
                fixed_hint_types.insert(0, hint_type)


# builds boss reward text that is displayed at the temple of time altar for child and adult, pull based off of item in a fixed order.
def buildBossRewardHints(world, messages):
    # text that appears at altar as a child.
    bossRewardsSpiritualStones = [
        ('Kokiri Emerald',   'Green'),
        ('Goron Ruby',       'Red'),
        ('Zora Sapphire',    'Blue'),
    ]
    child_text = '\x08'
    child_text += getHint('Spiritual Stone Text Start', world.clearer_hints).text
    for (reward, color) in bossRewardsSpiritualStones:
        child_text += buildBossString(reward, color, world)
    child_text += getHint('Spiritual Stone Text End', world.clearer_hints).text
    child_text += '\x0B'
    update_message_by_id(messages, 0x707A, get_raw_text(child_text), 0x20)

    # text that appears at altar as an adult.
    bossRewardsMedallions = [
        ('Light Medallion',  'Light Blue'),
        ('Forest Medallion', 'Green'),
        ('Fire Medallion',   'Red'),
        ('Water Medallion',  'Blue'),
        ('Shadow Medallion', 'Pink'),
        ('Spirit Medallion', 'Yellow'),
    ]
    adult_text = '\x08'
    adult_text += getHint('Medallion Text Start', world.clearer_hints).text
    for (reward, color) in bossRewardsMedallions:
        adult_text += buildBossString(reward, color, world)
    adult_text += getHint('Medallion Text End', world.clearer_hints).text
    adult_text += '\x0B'
    update_message_by_id(messages, 0x7057, get_raw_text(adult_text), 0x20)


# pulls text string from hintlist for reward after sending the location to hintlist.
def buildBossString(reward, color, world):
    for location in world.get_filled_locations():
        if location.item.name == reward:
            item_icon = chr(location.item.special['item_id'])
            location_text = getHint(location.name, world.clearer_hints).text
            return str(GossipText("\x08\x13%s%s" % (item_icon, location_text), [color], prefix='')) + '\x04'
    return ''


# fun new lines for Ganon during the final battle
def buildGanonText(world, messages):
    # empty now unused messages to make space for ganon lines
    update_message_by_id(messages, 0x70C8, " ")
    update_message_by_id(messages, 0x70C9, " ")
    update_message_by_id(messages, 0x70CA, " ")

    # lines before battle
    ganonLines = getHintGroup('ganonLine', world)
    random.shuffle(ganonLines)
    text = get_raw_text(ganonLines.pop().text)
    update_message_by_id(messages, 0x70CB, text)

    # light arrow hint or validation chest item
    if world.distribution.get_starting_item('Light Arrows') > 0:
        text = get_raw_text(getHint('Light Arrow Location', world.clearer_hints).text)
        text += "\x05\x42your pocket\x05\x40"
    elif world.light_arrow_location:
        text = get_raw_text(getHint('Light Arrow Location', world.clearer_hints).text)
        location = world.light_arrow_location
        location_hint = get_hint_area(location).replace('Ganon\'s Castle', 'my castle')
        if world.id != location.world.id:
            text += "\x05\x42Player %d's\x05\x40 %s" % (location.world.id +1, get_raw_text(location_hint))
        else:
            text += get_raw_text(location_hint)
    else:
        text = get_raw_text(getHint('Validation Line', world.clearer_hints).text)
        for location in world.get_filled_locations():
            if location.name == 'Ganons Tower Boss Key Chest':
                text += get_raw_text(getHint(getItemGenericName(location.item), world.clearer_hints).text)
                break
    text += '!'

    update_message_by_id(messages, 0x70CC, text)


def get_raw_text(string):
    text = ''
    for char in string:
        if char == '^':
            text += '\x04' # box break
        elif char == '&':
            text += '\x01' # new line
        elif char == '@':
            text += '\x0F' # print player name
        elif char == '#':
            text += '\x05\x40' # sets color to white
        else:
            text += char
    return text

def HintDistList():
    dists_json = os.listdir(data_path('Hints/'))
    dists = {}
    for d in dists_json:
        dist = read_json(os.path.join(data_path('Hints/'), d))
        dist_name = dist['name']
        gui_name = dist['gui_name']
        dists.update({ dist_name: gui_name })
    return dists

def HintDistTips():
    dists_json = os.listdir(data_path('Hints/'))
    tips = ""
    first_dist = True
    line_char_limit = 33
    for d in dists_json:
        if not first_dist:
            tips = tips + "\n"
        else:
            first_dist = False
        dist = read_json(os.path.join(data_path('Hints/'), d))
        gui_name = dist['gui_name']
        desc = dist['description']
        i = 0
        end_of_line = False
        tips = tips + "<b>"
        for c in gui_name:
            if c == " " and end_of_line:
                tips = tips + "\n"
                end_of_line = False
            else:
                tips = tips + c
                i = i + 1
                if i > line_char_limit:
                    end_of_line = True
                    i = 0
        tips = tips + "</b>: "
        i = i + 2
        for c in desc:
            if c == " " and end_of_line:
                tips = tips + "\n"
                end_of_line = False
            else:
                tips = tips + c
                i = i + 1
                if i > line_char_limit:
                    end_of_line = True
                    i = 0
        tips = tips + "\n"
    return tips

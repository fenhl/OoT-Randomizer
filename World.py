from __future__ import annotations
import copy
import json
import logging
import os
import random
from collections import OrderedDict, defaultdict
from collections.abc import Iterable, Iterator
from typing import Any, Optional

from Dungeon import Dungeon
from Entrance import Entrance
from Goals import Goal, GoalCategory
from HintList import get_required_hints, misc_item_hint_table, misc_location_hint_table
from Hints import HintArea, hint_dist_keys, hint_dist_files
from Item import Item, ItemFactory, ItemInfo, make_event_item
from ItemPool import reward_list, triforce_pieces
from Location import Location, LocationFactory
from LocationList import business_scrubs, location_groups, location_table
from OcarinaSongs import generate_song_list, Song
from Plandomizer import WorldDistribution, InvalidFileException
from Region import Region, TimeOfDay
from RuleParser import Rule_AST_Transformer
from Settings import Settings
from SettingsList import SettingInfos, get_settings_from_section
from Spoiler import Spoiler
from State import State
from Utils import data_path, read_logic_file


class World:
    def __init__(self, world_id: int, settings: Settings, resolve_randomized_settings: bool = True) -> None:
        self.id: int = world_id
        self.dungeons: list[Dungeon] = []
        self.regions: list[Region] = []
        self.itempool: list[Item] = []
        self._cached_locations: list[Location] = []
        self._entrance_cache: dict[str, Entrance] = {}
        self._region_cache: dict[str, Region] = {}
        self._location_cache: dict[str, Location] = {}
        self.shop_prices: dict[str, int] = {}
        self.scrub_prices: dict[int, int] = {}
        self.maximum_wallets: int = 0
        self.hinted_dungeon_reward_locations: dict[str, Location] = {}
        self.misc_hint_item_locations: dict[str, Location] = {}
        self.misc_hint_location_items: dict[str, Item] = {}
        self.total_starting_triforce_count: int = 0
        self.empty_areas: dict[HintArea, dict[str, Any]] = {}
        self.barren_dungeon: int = 0
        self.woth_dungeon: int = 0
        self.randomized_list: list[str] = []

        self.parser: Rule_AST_Transformer = Rule_AST_Transformer(self)
        self.event_items: set[str] = set()
        self.settings: Settings = settings
        self.distribution: WorldDistribution = settings.distribution.world_dists[world_id]

        # rename a few attributes...
        self.keysanity: bool = settings.shuffle_smallkeys in ['keysanity', 'remove', 'any_dungeon', 'overworld', 'regional']
        self.shuffle_ganon_bosskey: str = 'triforce' if settings.triforce_hunt else self.settings.shuffle_ganon_bosskey
        self.shuffle_silver_rupees: bool = settings.shuffle_silver_rupees != 'vanilla'
        self.check_beatable_only: bool = settings.reachable_locations != 'all'
        if settings.starting_age == 'adult' and settings.shuffle_song_items == 'vanilla' and settings.reachable_locations == 'all' and not settings.open_door_of_time:
            raise ValueError("Cannot combine songs on vanilla locations, adult start, all locations reachable, and closed Door of Time since access to the Song of Time would be locked behind itself.")

        self.shuffle_special_interior_entrances: bool = settings.shuffle_interior_entrances == 'all'
        self.shuffle_interior_entrances: bool = settings.shuffle_interior_entrances in ['simple', 'all']

        self.shuffle_special_dungeon_entrances: bool = settings.shuffle_dungeon_entrances == 'all'
        self.shuffle_dungeon_entrances: bool = settings.shuffle_dungeon_entrances in ['simple', 'all']

        self.entrance_shuffle: bool = bool(
            self.shuffle_interior_entrances or settings.shuffle_grotto_entrances or self.shuffle_dungeon_entrances
            or settings.shuffle_overworld_entrances or settings.shuffle_gerudo_valley_river_exit or settings.owl_drops or settings.warp_songs
            or settings.spawn_positions or (settings.shuffle_bosses != 'off')
        )

        self.mixed_pools_bosses = False # this setting is still in active development at https://github.com/Roman971/OoT-Randomizer

        self.ensure_tod_access: bool = bool(self.shuffle_interior_entrances or settings.shuffle_overworld_entrances or settings.spawn_positions)
        self.disable_trade_revert: bool = self.shuffle_interior_entrances or settings.shuffle_overworld_entrances or settings.adult_trade_shuffle
        self.skip_child_zelda: bool = 'Zeldas Letter' not in settings.shuffle_child_trade and 'Zeldas Letter' in settings.starting_items
        self.selected_adult_trade_item: str = ''
        self.adult_trade_starting_inventory: str = ''

        if settings.triforce_hunt_mode == 'ice_percent':
            self.triforce_count_per_world = 1
            self.triforce_goal_per_world = 1
        elif settings.triforce_hunt_mode == 'blitz':
            self.triforce_count_per_world = 3
            self.triforce_goal_per_world = 3
        else:
            self.triforce_count_per_world = settings.triforce_count_per_world
            self.triforce_goal_per_world = settings.triforce_goal_per_world
        self.triforce_goal: int = sum(
            1 if world_dist.settings.triforce_hunt_mode == 'ice_percent'
            else 3 if world_dist.settings.triforce_hunt_mode == 'blitz'
            else world_dist.settings.triforce_goal_per_world
            for world_dist in settings.distribution.world_dists
            if world_dist.settings.triforce_hunt
        )
        self.triforce_count: int = sum(
            world_dist.settings.triforce_count_per_world
            + sum(world_dist.settings.starting_items[triforce_piece].count for triforce_piece in triforce_pieces if triforce_piece in world_dist.settings.starting_items)
            for world_dist in settings.distribution.world_dists
            if world_dist.settings.triforce_hunt
        )
        if self.triforce_goal > self.triforce_count:
            raise ValueError("Triforces required cannot be more than the triforce count.")

        # trials that can be skipped will be decided later
        self.skipped_trials: dict[str, bool] = {
            'Forest': False,
            'Fire': False,
            'Water': False,
            'Spirit': False,
            'Shadow': False,
            'Light': False
        }

        # empty dungeons will be decided later
        class EmptyDungeons(dict):
            class EmptyDungeonInfo:
                def __init__(self, boss_name: Optional[str]) -> None:
                    self.empty: bool = False
                    self.boss_name: Optional[str] = boss_name
                    self.hint_name: Optional[HintArea] = None

            def __init__(self):
                super().__init__()
                self['Deku Tree'] = self.EmptyDungeonInfo('Queen Gohma')
                self['Dodongos Cavern'] = self.EmptyDungeonInfo('King Dodongo')
                self['Jabu Jabus Belly'] = self.EmptyDungeonInfo('Barinade')
                self['Forest Temple'] = self.EmptyDungeonInfo('Phantom Ganon')
                self['Fire Temple'] = self.EmptyDungeonInfo('Volvagia')
                self['Water Temple'] = self.EmptyDungeonInfo('Morpha')
                self['Spirit Temple'] = self.EmptyDungeonInfo('Twinrova')
                self['Shadow Temple'] = self.EmptyDungeonInfo('Bongo Bongo')

                for area in HintArea:
                    if area.is_dungeon and area.dungeon_name in self:
                        self[area.dungeon_name].hint_name = area

            def __missing__(self, dungeon_name: str) -> EmptyDungeonInfo:
                return self.EmptyDungeonInfo(None)

        self.empty_dungeons: dict[str, EmptyDungeons.EmptyDungeonInfo] = EmptyDungeons()

        # dungeon forms will be decided later
        self.dungeon_mq: dict[str, bool] = {
            'Deku Tree': False,
            'Dodongos Cavern': False,
            'Jabu Jabus Belly': False,
            'Bottom of the Well': False,
            'Ice Cavern': False,
            'Gerudo Training Ground': False,
            'Forest Temple': False,
            'Fire Temple': False,
            'Water Temple': False,
            'Spirit Temple': False,
            'Shadow Temple': False,
            'Ganons Castle': False
        }

        if resolve_randomized_settings:
            self.resolve_random_settings()

        self.song_notes: dict[str, Song] = generate_song_list(self,
            frog='frog' in settings.ocarina_songs,
            warp='warp' in settings.ocarina_songs,
            frogs2='frogs2' in settings.ocarina_songs,
        )

        if len(settings.hint_dist_user) == 0:
            for d in hint_dist_files():
                with open(d, 'r') as dist_file:
                    dist = json.load(dist_file)
                if dist['name'] == self.settings.hint_dist:
                    self.hint_dist_user: dict[str, Any] = dist
        else:
            self.settings.hint_dist = 'custom'
            self.hint_dist_user = self.settings.hint_dist_user

        # Allow omitting hint types that shouldn't be included
        for hint_type in hint_dist_keys:
            if 'distribution' in self.hint_dist_user and hint_type not in self.hint_dist_user['distribution']:
                self.hint_dist_user['distribution'][hint_type] = {"order": 0, "weight": 0.0, "fixed": 0, "copies": 0}
        if 'use_default_goals' not in self.hint_dist_user:
            self.hint_dist_user['use_default_goals'] = True
        if 'upgrade_hints' not in self.hint_dist_user:
            self.hint_dist_user['upgrade_hints'] = 'off'

        # Validate hint distribution format
        # Originally built when I was just adding the type distributions
        # Location/Item Additions and Overrides are not validated
        hint_dist_valid = False
        if all(key in self.hint_dist_user['distribution'] for key in hint_dist_keys):
            hint_dist_valid = True
            sub_keys = {'order', 'weight', 'fixed', 'copies', 'remove_stones', 'priority_stones'}
            for key in self.hint_dist_user['distribution']:
                if not all(sub_key in sub_keys for sub_key in self.hint_dist_user['distribution'][key]):
                    hint_dist_valid = False
        if not hint_dist_valid:
            raise InvalidFileException("""Hint distributions require all hint types be present in the distro
                                          (trial, always, dual_always, woth, barren, item, song, overworld, dungeon, entrance,
                                          sometimes, dual, random, junk, named-item, goal). If a hint type should not be
                                          shuffled, set its order to 0. Hint type format is \"type\": {
                                          \"order\": 0, \"weight\": 0.0, \"fixed\": 0, \"copies\": 0,
                                          \"remove_stones\": [], \"priority_stones\": [] }""")

        self.added_hint_types: dict[str, list[str]] = {}
        self.item_added_hint_types: dict[str, list[str]] = {}
        self.hint_exclusions: set[str] = set()
        if self.skip_child_zelda:
            self.hint_exclusions.add('Song from Impa')
        self.hint_type_overrides: dict[str, list[str]] = {}
        self.item_hint_type_overrides: dict[str, list[str]] = {}

        for dist in hint_dist_keys:
            self.added_hint_types[dist] = []
            for loc in self.hint_dist_user['add_locations']:
                if 'types' in loc:
                    if dist in loc['types']:
                        self.added_hint_types[dist].append(loc['location'])
            self.item_added_hint_types[dist] = []
            for i in self.hint_dist_user['add_items']:
                if dist in i['types']:
                    self.item_added_hint_types[dist].append(i['item'])
            self.hint_type_overrides[dist] = []
            for loc in self.hint_dist_user['remove_locations']:
                if dist in loc['types']:
                    self.hint_type_overrides[dist].append(loc['location'])
            self.item_hint_type_overrides[dist] = []
            for i in self.hint_dist_user['remove_items']:
                if dist in i['types']:
                    self.item_hint_type_overrides[dist].append(i['item'])

        # Make empty dungeons non-hintable as barren dungeons
        if settings.empty_dungeons_mode != 'none':
            for info in self.empty_dungeons.values():
                if info.empty:
                    self.hint_type_overrides['barren'].append(str(info.hint_name))

        self.hint_text_overrides: dict[str, str] = {}
        for loc in self.hint_dist_user['add_locations']:
            if 'text' in loc:
                # Arbitrarily throw an error at 80 characters to prevent overfilling the text box.
                if len(loc['text']) > 80:
                    raise Exception('Custom hint text too large for %s', loc['location'])
                self.hint_text_overrides.update({loc['location']: loc['text']})

        self.item_hints: list[str] = self.settings.item_hints + self.item_added_hint_types["named-item"]
        self.named_item_pool: list[str] = list(self.item_hints)

        self.always_hints: list[str] = [hint.name for hint in get_required_hints(self)]

        self.dungeon_rewards_hinted: bool = settings.shuffle_mapcompass != 'remove' if settings.enhance_map_compass else 'altar' in settings.misc_hints
        self.misc_hint_items: dict[str, str] = {hint_type: self.hint_dist_user.get('misc_hint_items', {}).get(hint_type, data['default_item']) for hint_type, data in misc_item_hint_table.items()}
        self.misc_hint_locations: dict[str, str] = {hint_type: self.hint_dist_user.get('misc_hint_locations', {}).get(hint_type, data['item_location']) for hint_type, data in misc_location_hint_table.items()}

        self.state: State = State(self)

        # Allows us to cut down on checking whether some items are required
        self.max_progressions: dict[str, int] = {name: item.special.get('progressive', 1) for name, item in ItemInfo.items.items()}
        self.max_tokens: int = 0
        if self.settings.bridge == 'tokens':
            self.max_tokens = max(self.max_tokens, self.settings.bridge_tokens)
        if self.settings.lacs_condition == 'tokens':
            self.max_tokens = max(self.max_tokens, self.settings.lacs_tokens)
        if self.shuffle_ganon_bosskey == 'tokens':
            self.max_tokens = max(self.max_tokens, self.settings.ganon_bosskey_tokens)
        tokens = [50, 40, 30, 20, 10]
        for t in tokens:
            if f'Kak {t} Gold Skulltula Reward' not in self.settings.disabled_locations:
                self.max_tokens = max(self.max_tokens, t)
                break
        self.max_progressions['Gold Skulltula Token'] = self.max_tokens
        max_hearts = 0
        if self.settings.bridge == 'hearts':
            max_hearts = max(max_hearts, self.settings.bridge_hearts)
        if self.settings.lacs_condition == 'hearts':
            max_hearts = max(max_hearts, self.settings.lacs_hearts)
        if self.shuffle_ganon_bosskey == 'hearts':
            max_hearts = max(max_hearts, self.settings.ganon_bosskey_hearts)
        self.max_progressions['Heart Container'] = max_hearts
        self.max_progressions['Piece of Heart'] = max_hearts * 4
        self.max_progressions['Piece of Heart (Treasure Chest Game)'] = max_hearts * 4
        # Additional Ruto's Letter become Bottle, so we may have to collect two.
        self.max_progressions['Rutos Letter'] = 2

        # Available Gold Skulltula Tokens in world. Set to proper value in ItemPool.py.
        self.available_tokens: int = 100

        # Disable goal hints if the hint distro does not require them.
        # WOTH locations are always searched.
        self.enable_goal_hints: bool = any(
            self.has_hint_type(hint_type)
            for hint_type in ('goal', 'goal-count', 'goal-legacy', 'goal-legacy-single', 'unlock-playthrough', 'unlock-woth', 'wanderer')
        )

        # Initialize default goals for win condition
        self.goal_categories: dict[str, GoalCategory] = OrderedDict()
        if self.hint_dist_user['use_default_goals']:
            self.set_goals()

        # import goals from hint plando
        if 'custom_goals' in self.hint_dist_user:
            for category in self.hint_dist_user['custom_goals']:
                if category['category'] in self.goal_categories:
                    cat = self.goal_categories[category['category']]
                else:
                    cat = GoalCategory(category['category'], category['priority'], minimum_goals=category['minimum_goals'])
                for goal in category['goals']:
                    cat.add_goal(Goal(self, goal['name'], goal['hint_text'], goal['color'], items=list({'name': i['name'], 'quantity': i['quantity'], 'minimum': i['minimum'], 'hintable': i['hintable']} for i in goal['items'])))
                if 'count_override' in category:
                    cat.goal_count = category['count_override']
                else:
                    cat.goal_count = len(cat.goals)
                if 'lock_entrances' in category:
                    cat.lock_entrances = list(category['lock_entrances'])
                self.goal_categories[cat.name] = cat

        # Sort goal hint categories by priority
        # For most settings this will be Bridge, GBK
        self.goal_categories = OrderedDict({name: category for (name, category) in sorted(self.goal_categories.items(), key=lambda kv: kv[1].priority)})

        # Turn on one hint per goal if all goal categories contain the same goals.
        # Reduces the changes of randomly choosing one smaller category over and
        # over again after the first round through the categories.
        if len(self.goal_categories) > 0:
            self.one_hint_per_goal = True
            goal_list1 = []
            for category in self.goal_categories.values():
                if category.name != 'door_of_time':
                    goal_list1 = [goal.name for goal in category.goals]
            for category in self.goal_categories.values():
                if goal_list1 != [goal.name for goal in category.goals] and category.name != 'door_of_time':
                    self.one_hint_per_goal = False

        # initialize category check for first rounds of goal hints
        self.hinted_categories = []

        # Quick item lookup for All Goals Reachable setting
        self.goal_items = []
        for cat_name, category in self.goal_categories.items():
            for goal in category.goals:
                for item in goal.items:
                    self.goal_items.append(item['name'])

        # Separate goal categories into locked and unlocked for search optimization
        self.locked_goal_categories: dict[str, GoalCategory] = {name: category for (name, category) in self.goal_categories.items() if category.lock_entrances}
        self.unlocked_goal_categories: dict[str, GoalCategory] = {name: category for (name, category) in self.goal_categories.items() if not category.lock_entrances}

    def copy(self) -> World:
        new_world = World(self.id, self.settings.copy(), False)

        new_world.skipped_trials = copy.copy(self.skipped_trials)
        new_world.dungeon_mq = copy.copy(self.dungeon_mq)
        new_world.empty_dungeons = copy.copy(self.empty_dungeons)
        new_world.shop_prices = copy.copy(self.shop_prices)
        new_world.triforce_goal = self.triforce_goal
        new_world.triforce_count = self.triforce_count
        new_world.total_starting_triforce_count = self.total_starting_triforce_count
        new_world.maximum_wallets = self.maximum_wallets
        new_world.distribution = self.distribution

        new_world.dungeons = [dungeon for dungeon in self.dungeons]
        new_world.regions = [region for region in self.regions]
        new_world.itempool = [item for item in self.itempool]
        new_world.state = self.state.copy(new_world)

        # TODO: Why is this necessary over copying region.entrances on region copy?
        # new_world.initialize_entrances()

        # copy any randomized settings to match the original copy
        new_world.randomized_list = list(self.randomized_list)
        for randomized_item in new_world.randomized_list:
            setattr(new_world, randomized_item, getattr(self.settings, randomized_item))

        new_world.always_hints = list(self.always_hints)
        new_world.max_progressions = copy.copy(self.max_progressions)
        new_world.available_tokens = self.available_tokens

        new_world.song_notes = copy.copy(self.song_notes)

        return new_world

    def has_hint_type(self, hint_type: str) -> bool:
        return (
            'distribution' in self.hint_dist_user
            and hint_type in self.hint_dist_user['distribution']
            and (
                self.hint_dist_user['distribution'][hint_type]['fixed'] != 0
                or self.hint_dist_user['distribution'][hint_type]['weight'] != 0
            )
        )

    def set_random_bridge_values(self) -> None:
        if self.settings.bridge == 'medallions':
            self.settings.bridge_medallions = 6
            self.randomized_list.append('bridge_medallions')
        if self.settings.bridge == 'dungeons':
            self.settings.bridge_rewards = 9
            self.randomized_list.append('bridge_rewards')
        if self.settings.bridge == 'stones':
            self.settings.bridge_stones = 3
            self.randomized_list.append('bridge_stones')

    def resolve_random_settings(self) -> None:
        # evaluate settings (important for logic, nice for spoiler)
        self.randomized_list = []
        dist_keys = set()
        if '_settings' in self.distribution.distribution.src_dict:
            dist_keys = self.distribution.distribution.src_dict['_settings'].keys()
        if self.settings.randomize_settings:
            setting_info = SettingInfos.setting_infos['randomize_settings']
            self.randomized_list.extend(setting_info.disable[True]['settings'])
            for section in setting_info.disable[True]['sections']:
                self.randomized_list.extend(get_settings_from_section(section))
                # Remove settings specified in the distribution
                self.randomized_list = [x for x in self.randomized_list if x not in dist_keys]
            for setting in list(self.randomized_list):
                if (setting == 'bridge_medallions' and self.settings.bridge != 'medallions') \
                        or (setting == 'bridge_stones' and self.settings.bridge != 'stones') \
                        or (setting == 'bridge_rewards' and self.settings.bridge != 'dungeons') \
                        or (setting == 'bridge_tokens' and self.settings.bridge != 'tokens') \
                        or (setting == 'bridge_hearts' and self.settings.bridge != 'hearts') \
                        or (setting == 'lacs_medallions' and self.settings.lacs_condition != 'medallions') \
                        or (setting == 'lacs_stones' and self.settings.lacs_condition != 'stones') \
                        or (setting == 'lacs_rewards' and self.settings.lacs_condition != 'dungeons') \
                        or (setting == 'lacs_tokens' and self.settings.lacs_condition != 'tokens') \
                        or (setting == 'lacs_hearts' and self.settings.lacs_condition != 'hearts') \
                        or (setting == 'ganon_bosskey_medallions' and self.shuffle_ganon_bosskey != 'medallions') \
                        or (setting == 'ganon_bosskey_stones' and self.shuffle_ganon_bosskey != 'stones') \
                        or (setting == 'ganon_bosskey_rewards' and self.shuffle_ganon_bosskey != 'dungeons') \
                        or (setting == 'ganon_bosskey_tokens' and self.shuffle_ganon_bosskey != 'tokens') \
                        or (setting == 'ganon_bosskey_hearts' and self.shuffle_ganon_bosskey != 'hearts'):
                    self.randomized_list.remove(setting)
        if self.settings.big_poe_count_random and 'big_poe_count' not in dist_keys:
            self.settings.big_poe_count = random.randint(1, 10)
            self.randomized_list.append('big_poe_count')
        # If set to random in GUI, we don't want to randomize if it was specified as non-random in the distribution
        if (self.settings.starting_tod == 'random'
            and ('starting_tod' not in dist_keys
             or self.distribution.distribution.src_dict['_settings']['starting_tod'] == 'random')):
            setting_info = SettingInfos.setting_infos['starting_tod']
            choices = [ch for ch in setting_info.choices if ch not in ['default', 'random']]
            self.settings.starting_tod = random.choice(choices)
            self.randomized_list.append('starting_tod')
        if (self.settings.starting_age == 'random'
            and ('starting_age' not in dist_keys
             or self.distribution.distribution.src_dict['_settings']['starting_age'] == 'random')):
            if self.settings.shuffle_song_items == 'vanilla' and self.settings.reachable_locations == 'all' and not self.settings.open_door_of_time:
                # adult is not compatible
                self.settings.starting_age = 'child'
            else:
                self.settings.starting_age = random.choice(['child', 'adult'])
            self.randomized_list.append('starting_age')
        if self.settings.chicken_count_random and 'chicken_count' not in dist_keys:
            self.settings.chicken_count = random.randint(0, 7)
            self.randomized_list.append('chicken_count')

        # Determine dungeons with shortcuts
        dungeons = ['Deku Tree', 'Dodongos Cavern', 'Jabu Jabus Belly', 'Forest Temple', 'Fire Temple', 'Water Temple', 'Shadow Temple', 'Spirit Temple']
        if self.settings.dungeon_shortcuts_choice == 'random':
            self.settings.dungeon_shortcuts = random.sample(dungeons, random.randint(0, len(dungeons)))
            self.randomized_list.append('dungeon_shortcuts')
        elif self.settings.dungeon_shortcuts_choice == 'all':
            self.settings.dungeon_shortcuts = dungeons

        # Determine area with keyring
        if self.settings.key_rings_choice == 'random':
            areas = ['Thieves Hideout', 'Treasure Chest Game', 'Forest Temple', 'Fire Temple', 'Water Temple', 'Shadow Temple', 'Spirit Temple', 'Bottom of the Well', 'Gerudo Training Ground', 'Ganons Castle']
            self.settings.key_rings = random.sample(areas, random.randint(0, len(areas)))
            self.randomized_list.append('key_rings')
        elif self.settings.key_rings_choice == 'all':
            self.settings.key_rings = ['Thieves Hideout', 'Treasure Chest Game', 'Forest Temple', 'Fire Temple', 'Water Temple', 'Shadow Temple', 'Spirit Temple', 'Bottom of the Well', 'Gerudo Training Ground', 'Ganons Castle']

        # Handle random Rainbow Bridge condition
        if (self.settings.bridge == 'random'
            and ('bridge' not in dist_keys
             or self.distribution.distribution.src_dict['_settings']['bridge'] == 'random')):
            possible_bridge_requirements = ["open", "medallions", "dungeons", "stones", "vanilla"]
            self.settings.bridge = random.choice(possible_bridge_requirements)
            self.set_random_bridge_values()
            self.randomized_list.append('bridge')

        # Determine Ganon Trials
        trial_pool = list(self.skipped_trials)
        dist_chosen = self.distribution.configure_trials(trial_pool)
        dist_num_chosen = len(dist_chosen)

        if self.settings.trials_random and 'trials' not in dist_keys:
            self.settings.trials = dist_num_chosen + random.randint(0, len(trial_pool))
            self.randomized_list.append('trials')
        num_trials = int(self.settings.trials)
        if num_trials < dist_num_chosen:
            raise RuntimeError("%d trials set to active on world %d, but only %d active trials allowed." % (dist_num_chosen, self.id, num_trials))
        chosen_trials = random.sample(trial_pool, num_trials - dist_num_chosen)
        for trial in self.skipped_trials:
            if trial not in chosen_trials and trial not in dist_chosen:
                self.skipped_trials[trial] = True

        # Determine empty and MQ Dungeons (avoid having both empty & MQ dungeons unless necessary)
        mq_dungeon_pool = list(self.dungeon_mq)
        empty_dungeon_pool = list(self.empty_dungeons)
        dist_num_mq, dist_num_empty = self.distribution.configure_dungeons(self, mq_dungeon_pool, empty_dungeon_pool)

        if self.settings.empty_dungeons_mode == 'specific':
            for dung in self.settings.empty_dungeons_specific:
                self.empty_dungeons[dung].empty = True

        if self.settings.mq_dungeons_mode == 'specific':
            for dung in self.settings.mq_dungeons_specific:
                self.dungeon_mq[dung] = True

        if self.settings.empty_dungeons_mode == 'count':
            nb_to_pick = self.settings.empty_dungeons_count - dist_num_empty
            if nb_to_pick < 0:
                raise RuntimeError(f"{dist_num_empty} dungeons are set to empty on world {self.id+1}, but only {self.settings.empty_dungeons_count} empty dungeons allowed")
            if len(empty_dungeon_pool) < nb_to_pick:
                non_empty = 8 - dist_num_empty - len(empty_dungeon_pool)
                raise RuntimeError(f"On world {self.id+1}, {dist_num_empty} dungeons are set to empty and {non_empty} to non-empty. Can't reach {self.settings.empty_dungeons_count} empty dungeons.")

            # Prioritize non-Deku dungeons in Require Gohma, then prioritize non-MQ dungeons
            non_mq, mq, deku = [], [], []
            for dung in empty_dungeon_pool:
                if self.settings.require_gohma and dung == 'Deku Tree':
                    deku.append(dung)
                elif self.dungeon_mq[dung]:
                    mq.append(dung)
                else:
                    non_mq.append(dung)
            for collection in (non_mq, mq, deku):
                for dung in random.sample(collection, min(nb_to_pick, len(collection))):
                    self.empty_dungeons[dung].empty = True
                    nb_to_pick -= 1

        if self.settings.mq_dungeons_mode == 'random' and 'mq_dungeons_count' not in dist_keys:
            for dungeon in mq_dungeon_pool:
                self.dungeon_mq[dungeon] = random.choice([True, False])
            self.randomized_list.append('mq_dungeons_count')
        elif self.settings.mq_dungeons_mode in ['mq', 'vanilla']:
            for dung in self.dungeon_mq.keys():
                self.dungeon_mq[dung] = (self.settings.mq_dungeons_mode == 'mq')
        elif self.settings.mq_dungeons_mode != 'specific':
            nb_to_pick = self.settings.mq_dungeons_count - dist_num_mq
            if nb_to_pick < 0:
                raise RuntimeError("%d dungeons are set to MQ on world %d, but only %d MQ dungeons allowed." % (dist_num_mq, self.id+1, self.settings.mq_dungeons_count))
            if len(mq_dungeon_pool) < nb_to_pick:
                non_mq = 8 - dist_num_mq - len(mq_dungeon_pool)
                raise RuntimeError(f"On world {self.id+1}, {dist_num_mq} dungeons are set to MQ and {non_mq} to non-MQ. Can't reach {self.settings.mq_dungeons_count} MQ dungeons.")

            # Prioritize non-empty dungeons
            non_empty, empty = [], []
            for dung in mq_dungeon_pool:
                (empty if self.empty_dungeons[dung].empty else non_empty).append(dung)
            for dung in random.sample(non_empty, min(nb_to_pick, len(non_empty))):
                self.dungeon_mq[dung] = True
                nb_to_pick -= 1
            if nb_to_pick > 0:
                for dung in random.sample(empty, nb_to_pick):
                    self.dungeon_mq[dung] = True

        self.settings.mq_dungeons_count = list(self.dungeon_mq.values()).count(True)
        self.distribution.configure_randomized_settings(self)

        # Determine puzzles with silver rupee pouches
        if self.settings.silver_rupee_pouches_choice == 'random':
            puzzles = self.silver_rupee_puzzles()
            self.settings.silver_rupee_pouches = random.sample(puzzles, random.randint(0, len(puzzles)))
            self.randomized_list.append('silver_rupee_pouches')
        elif self.settings.silver_rupee_pouches_choice == 'all':
            self.settings.silver_rupee_pouches = self.silver_rupee_puzzles()

    def load_regions_from_json(self, file_path: str) -> list[tuple[Entrance, str]]:
        region_json = read_logic_file(file_path)
        savewarps_to_connect = []

        for region in region_json:
            new_region = Region(self, region['region_name'])
            if 'scene' in region:
                new_region.scene = region['scene']
            if 'hint' in region:
                new_region.hint_name = region['hint']
            if 'alt_hint' in region:
                new_region.alt_hint_name = region['alt_hint']
            if 'dungeon' in region:
                new_region.dungeon_name = region['dungeon']
            if 'is_boss_room' in region:
                new_region.is_boss_room = region['is_boss_room']
            if 'time_passes' in region:
                new_region.time_passes = region['time_passes']
                new_region.provides_time = TimeOfDay.ALL
            if new_region.name in ('Ganons Castle Grounds', 'Ganons Castle Ledge'):
                new_region.provides_time = TimeOfDay.DAMPE
            if 'locations' in region:
                for location, rule in region['locations'].items():
                    new_location = LocationFactory(location)
                    new_location.parent_region = new_region
                    new_location.rule_string = rule
                    if self.settings.logic_rules != 'none':
                        self.parser.parse_spot_rule(new_location)
                    if new_location.never:
                        # We still need to fill the location even if ALR is off.
                        logging.getLogger('').debug('Unreachable location: %s', new_location.name)
                    new_location.world = self
                    new_region.locations.append(new_location)
            if 'events' in region:
                for event, rule in region['events'].items():
                    # Allow duplicate placement of events
                    lname = '%s from %s' % (event, new_region.name)
                    new_location = Location(lname, location_type='Event', parent=new_region)
                    new_location.rule_string = rule
                    if self.settings.logic_rules != 'none':
                        self.parser.parse_spot_rule(new_location)
                    if new_location.never:
                        logging.getLogger('').debug('Dropping unreachable event: %s', new_location.name)
                    else:
                        new_location.world = self
                        new_region.locations.append(new_location)
                        make_event_item(event, new_location)
            if 'exits' in region:
                for exit, rule in region['exits'].items():
                    new_exit = Entrance('%s -> %s' % (new_region.name, exit), new_region)
                    new_exit.connected_region = exit
                    new_exit.rule_string = rule
                    if self.settings.logic_rules != 'none':
                        self.parser.parse_spot_rule(new_exit)
                    new_region.exits.append(new_exit)
            if 'savewarp' in region:
                if region['savewarp'] != "Gerudo Fortress -> Hideout 1 Torch Jail" or self.settings.shuffle_hideout_entrances != 'overworld_savewarp':
                    savewarp_target = region['savewarp'].split(' -> ')[1]
                    new_exit = Entrance(f'{new_region.name} -> {savewarp_target}', new_region)
                    new_exit.connected_region = savewarp_target
                    new_region.exits.append(new_exit)
                    new_region.savewarp = new_exit
                    # the replaced entrance may not exist yet so we connect it after all region files have been read
                    savewarps_to_connect.append((new_exit, region['savewarp']))
            self.regions.append(new_region)
        return savewarps_to_connect

    def create_dungeons(self) -> list[tuple[Entrance, str]]:
        savewarps_to_connect = []
        for hint_area in HintArea:
            if (name := hint_area.dungeon_name) is not None:
                logic_folder = 'Glitched World' if self.settings.logic_rules == 'glitched' else 'World'
                file_name = name + (' MQ.json' if self.dungeon_mq[name] else '.json')
                savewarps_to_connect += self.load_regions_from_json(os.path.join(data_path(logic_folder), file_name))
                self.dungeons.append(Dungeon(self, name, hint_area))
        return savewarps_to_connect

    def create_internal_locations(self) -> None:
        self.parser.create_delayed_rules()
        assert self.parser.events <= self.event_items, 'Parse error: undefined items %r' % (self.parser.events - self.event_items)

    def initialize_entrances(self) -> None:
        for region in self.regions:
            for exit in region.exits:
                if exit.connected_region:
                    exit.connect(self.get_region(exit.connected_region))
                exit.world = self

    def initialize_regions(self) -> None:
        for region in self.regions:
            region.world = self
            for location in region.locations:
                location.world = self

    def initialize_items(self, items: Optional[list[Item]] = None) -> None:
        items = self.itempool if items is None else items
        item_dict = defaultdict(list)
        for item in items:
            item_dict[item.name].append(item)
            if (self.settings.shuffle_hideoutkeys in ['fortress', 'regional'] and item.type == 'HideoutSmallKey') or (self.settings.shuffle_tcgkeys == 'regional' and item.type == 'TCGSmallKey'):
                item.priority = True

        for dungeon in self.dungeons:
            dungeon_items = [item for item_name in dungeon.get_item_names() for item in item_dict[item_name]]
            for item in dungeon_items:
                shuffle_setting = None
                dungeon_collection = None
                if item.map or item.compass:
                    dungeon_collection = dungeon.dungeon_items
                    shuffle_setting = self.settings.shuffle_mapcompass
                elif item.smallkey:
                    dungeon_collection = dungeon.small_keys
                    shuffle_setting = self.settings.shuffle_smallkeys
                elif item.bosskey:
                    dungeon_collection = dungeon.boss_key
                    shuffle_setting = self.settings.shuffle_bosskeys
                elif item.type == 'SilverRupee':
                    dungeon_collection = dungeon.silver_rupees
                    shuffle_setting = self.settings.shuffle_silver_rupees
                elif item.type == 'DungeonReward':
                    dungeon_collection = dungeon.reward
                    shuffle_setting = self.settings.shuffle_dungeon_rewards

                if dungeon_collection is not None and item not in dungeon_collection:
                    dungeon_collection.append(item)
                if shuffle_setting in ['any_dungeon', 'overworld', 'regional']:
                    item.priority = True

    def random_shop_prices(self) -> None:
        shop_item_indexes = ['7', '5', '8', '6']
        self.shop_prices = {}
        for region in self.regions:
            if self.settings.shopsanity == 'random':
                shop_item_count = random.randint(0, 4)
            else:
                shop_item_count = int(self.settings.shopsanity)

            for location in region.locations:
                if location.type == 'Shop':
                    if location.name[-1:] in shop_item_indexes[:shop_item_count]:
                        if self.settings.special_deal_price_distribution == 'vanilla':
                            self.shop_prices[location.name] = ItemInfo.items[location.vanilla_item].price
                        elif self.settings.special_deal_price_max < self.settings.special_deal_price_min:
                            raise ValueError('Maximum special deal price is lower than minimum, perhaps you meant to swap them?')
                        elif self.settings.special_deal_price_max == self.settings.special_deal_price_min:
                            self.shop_prices[location.name] = self.settings.special_deal_price_min
                        elif self.settings.special_deal_price_distribution == 'betavariate':
                            self.shop_prices[location.name] = self.settings.special_deal_price_min + int(random.betavariate(1.5, 2) * (self.settings.special_deal_price_max - self.settings.special_deal_price_min) / 5) * 5
                        elif self.settings.special_deal_price_distribution == 'uniform':
                            self.shop_prices[location.name] = random.randrange(self.settings.special_deal_price_min, self.settings.special_deal_price_max + 1, 5)
                        else:
                            raise NotImplementedError(f'Unimplemented special deal distribution: {self.settings.special_deal_price_distribution}')

    def set_scrub_prices(self) -> None:
        # Get Deku Scrub Locations
        scrub_locations = [location for location in self.get_locations() if location.type in ['Scrub', 'GrottoScrub']]
        scrub_dictionary = {}
        for location in scrub_locations:
            if location.default not in scrub_dictionary:
                scrub_dictionary[location.default] = []
            scrub_dictionary[location.default].append(location)

        # Loop through each type of scrub.
        for (scrub_item, default_price, text_id, text_replacement) in business_scrubs:
            price = default_price
            if self.settings.shuffle_scrubs == 'low':
                price = 10
            elif self.settings.shuffle_scrubs == 'random':
                # this is a random value between 0-99
                # average value is ~33 rupees
                price = int(random.betavariate(1, 2) * 99)

            # Set price in the dictionary as well as the location.
            self.scrub_prices[scrub_item] = price
            if scrub_item in scrub_dictionary:
                for location in scrub_dictionary[scrub_item]:
                    location.price = price
                    if location.item is not None:
                        location.item.price = price

    def fill_bosses(self, boss_count: int = 9) -> None:
        boss_rewards = ItemFactory(reward_list, self)
        boss_locations = [self.get_location(loc) for loc in location_groups['Boss']]

        placed_prizes = [loc.item.name for loc in boss_locations if loc.item is not None]
        unplaced_prizes = [item for item in boss_rewards if item.name not in placed_prizes]
        empty_boss_locations = [loc for loc in boss_locations if loc.item is None]
        prizepool = list(unplaced_prizes)
        prize_locs = list(empty_boss_locations)

        boss_count -= self.distribution.fill_bosses(self, prize_locs, prizepool)

        while boss_count:
            boss_count -= 1
            random.shuffle(prizepool)
            random.shuffle(prize_locs)
            loc = prize_locs.pop()
            if self.settings.shuffle_dungeon_rewards == 'vanilla':
                item = next(item for item in prizepool if item.name == location_table[loc.name][4])
            elif self.settings.shuffle_dungeon_rewards == 'reward':
                item = prizepool.pop()
            self.push_item(loc, item)

    def set_goals(self) -> None:
        # Default goals are divided into 3 primary categories:
        # Bridge, Ganon's Boss Key, and Trials
        # The Triforce Hunt goal is mutually exclusive with
        # these categories given the vastly different playstyle.
        #
        # Goal priorities determine where hintable locations are placed.
        # For example, an item required for both trials and bridge would
        # be hinted only for bridge. This accomplishes two objectives:
        #   1) Locations are not double counted for different stages
        #      of the game
        #   2) Later category location lists are not diluted by early
        #      to mid game locations
        #
        # Entrance locks set restrictions on all goals in a category to
        # ensure unreachable goals are not hintable. This is only used
        # for the Rainbow Bridge to filter out goals hard-locked by
        # Inside Ganon's Castle access.
        #
        # Minimum goals for a category tell the randomizer if the
        # category meta-goal is satisfied by starting items. This
        # is straightforward for dungeon reward goals where X rewards
        # is the same as the minimum goals. For Triforce Hunt, Trials,
        # and Skull conditions, there is only one goal in the category
        # requesting X copies within the goal, so minimum goals has to
        # be 1 for these.
        dot = GoalCategory('door_of_time', 5, lock_entrances=['Temple of Time -> Beyond Door of Time'], minimum_goals=1)
        b = GoalCategory('rainbow_bridge', 10, lock_entrances=['Ganons Castle Ledge -> Ganons Castle Lobby'])
        gbk = GoalCategory('ganon_bosskey', 20)
        trials = GoalCategory('trials', 30, minimum_goals=1)
        th = GoalCategory('triforce_hunt', 30, goal_count=round(self.triforce_goal_per_world / 10), minimum_goals=3 if self.settings.triforce_hunt_mode == 'blitz' else 1)
        trial_goal = Goal(self, 'the Tower', 'path to #the Tower#', 'White', items=[], create_empty=True)

        if self.settings.triforce_hunt and self.triforce_goal_per_world > 0:
            # "Hintable" value of False means the goal items themselves cannot
            # be hinted directly. This is used for Triforce Hunt and Skull
            # conditions to restrict hints to useful items instead of the win
            # condition. Dungeon rewards do not need this restriction as they are
            # already unhintable at a lower level.
            #
            # This restriction does NOT apply to Light Arrows or Ganon's Castle Boss
            # Key, which makes these items directly hintable in their respective goals
            # assuming they do not get hinted by another hint type (always, woth with
            # an earlier order in the hint distro, etc).
            if self.settings.triforce_hunt_mode == 'blitz':
                for piece, color in (
                    ('Power', 'Red'),
                    ('Wisdom', 'Blue'),
                    ('Courage', 'Green'),
                ):
                    th.add_goal(Goal(self, piece.lower(), f'path of #{piece.lower()}#', color, items=[{'name': f'Triforce of {piece}', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
            else:
                if self.settings.triforce_hunt_mode == 'easter_egg_hunt':
                    path_name = 'the bunny'
                    path_color = 'Yellow'
                elif self.settings.triforce_hunt_mode == 'ice_percent':
                    path_name = 'ice'
                    path_color = 'Light Blue'
                else:
                    path_name = 'gold'
                    path_color = 'Yellow'
                th.add_goal(Goal(self, path_name, f'path of #{path_name}#', path_color, items=[{'name': 'Triforce Piece', 'quantity': self.triforce_count_per_world, 'minimum': self.triforce_goal_per_world, 'hintable': False}]))
                self.goal_categories[th.name] = th
        # Category goals are defined for each possible setting for each category.
        # Bridge can be Stones, Medallions, Dungeons, Skulls, or Vanilla.
        # Ganon's Boss Key can be Stones, Medallions, Dungeons, Skulls, LACS or
        # one of the keysanity variants.
        # Trials is one goal that is only on if at least one trial is on in the world.
        # If there are no win conditions beyond Kill Ganon (open bridge, GBK removed,
        # no trials), a fallback "path of the hero" clone of WOTH is created. Path
        # wording is used to distinguish the hint type even though the hintable location
        # set is identical to WOTH.
        if not self.settings.triforce_hunt:
            if self.settings.starting_age == 'child':
                dot_items = [{'name': 'Temple of Time Access', 'quantity': 1, 'minimum': 1, 'hintable': True}]
                if not self.settings.open_door_of_time:
                    dot_items.append({'name': 'Song of Time', 'quantity': 2 if self.settings.shuffle_song_items == 'any' and self.settings.item_pool_value == 'plentiful' else 1, 'minimum': 1, 'hintable': True})
                    if self.settings.shuffle_ocarinas:
                        dot_items.append({'name': 'Ocarina', 'quantity': 3 if self.settings.item_pool_value == 'plentiful' else 2, 'minimum': 1, 'hintable': True})
                dot.add_goal(Goal(self, 'Door of Time', 'path of time', 'Light Blue', items=dot_items))
                self.goal_categories[dot.name] = dot

            # Bridge goals will always be defined as they have the most immediate priority
            if self.settings.bridge != 'open' and not self.shuffle_special_dungeon_entrances and not self.settings.shuffle_ganon_tower:
                # "Replace" hint text dictionaries are used to reference the
                # dungeon boss holding the specified reward. Only boss names/paths
                # are defined for this feature, and it is not extendable via plando.
                # Goal hint text colors are based on the dungeon reward, not the boss.
                if (self.settings.bridge_stones > 0 and self.settings.bridge == 'stones') or (self.settings.bridge_rewards > 0 and self.settings.bridge == 'dungeons'):
                    b.add_goal(Goal(self, 'Kokiri Emerald', { 'replace': 'Kokiri Emerald' }, 'Green', items=[{'name': 'Kokiri Emerald', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                    b.add_goal(Goal(self, 'Goron Ruby', { 'replace': 'Goron Ruby' }, 'Red', items=[{'name': 'Goron Ruby', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                    b.add_goal(Goal(self, 'Zora Sapphire', { 'replace': 'Zora Sapphire' }, 'Blue', items=[{'name': 'Zora Sapphire', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                    b.minimum_goals = self.settings.bridge_stones if self.settings.bridge == 'stones' else self.settings.bridge_rewards
                if (self.settings.bridge_medallions > 0 and self.settings.bridge == 'medallions') or (self.settings.bridge_rewards > 0 and self.settings.bridge == 'dungeons'):
                    b.add_goal(Goal(self, 'Forest Medallion', { 'replace': 'Forest Medallion' }, 'Green', items=[{'name': 'Forest Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                    b.add_goal(Goal(self, 'Fire Medallion', { 'replace': 'Fire Medallion' }, 'Red', items=[{'name': 'Fire Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                    b.add_goal(Goal(self, 'Water Medallion', { 'replace': 'Water Medallion' }, 'Blue', items=[{'name': 'Water Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                    b.add_goal(Goal(self, 'Shadow Medallion', { 'replace': 'Shadow Medallion' }, 'Pink', items=[{'name': 'Shadow Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                    b.add_goal(Goal(self, 'Spirit Medallion', { 'replace': 'Spirit Medallion' }, 'Yellow', items=[{'name': 'Spirit Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                    b.add_goal(Goal(self, 'Light Medallion', { 'replace': 'Light Medallion' }, 'Light Blue', items=[{'name': 'Light Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                    b.minimum_goals = self.settings.bridge_medallions if self.settings.bridge == 'medallions' else self.settings.bridge_rewards
                if self.settings.bridge == 'vanilla':
                    b.add_goal(Goal(self, 'Shadow Medallion', { 'replace': 'Shadow Medallion' }, 'Pink', items=[{'name': 'Shadow Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                    b.add_goal(Goal(self, 'Spirit Medallion', { 'replace': 'Spirit Medallion' }, 'Yellow', items=[{'name': 'Spirit Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                    min_goals = 2
                    # With plentiful item pool, multiple copies of Light Arrows are available,
                    # but both are not guaranteed reachable. Setting a goal quantity of the
                    # item pool value with a minimum quantity of 1 attempts to hint all items
                    # required to get all copies of Light Arrows, but will fall back to just
                    # one copy if the other is unreachable.
                    #
                    # Similar criteria is used for Ganon's Boss Key in plentiful keysanity.
                    if not 'Light Arrows' in self.item_added_hint_types['always']:
                        if self.settings.item_pool_value == 'plentiful':
                            arrows = 2
                        else:
                            arrows = 1
                        b.add_goal(Goal(self, 'Evil\'s Bane', 'path to #Evil\'s Bane#', 'Light Blue', items=[{'name': 'Light Arrows', 'quantity': arrows, 'minimum': 1, 'hintable': True}]))
                        min_goals += 1
                    b.minimum_goals = min_goals
                # Goal count within a category is currently unused. Testing is in progress
                # to potentially use this for weighting certain goals for hint selection.
                b.goal_count = len(b.goals)
                if (self.settings.bridge_tokens > 0
                    and self.settings.bridge == 'tokens'
                    and (self.shuffle_ganon_bosskey != 'tokens'
                            or self.settings.bridge_tokens >= self.settings.ganon_bosskey_tokens)
                    and (self.shuffle_ganon_bosskey != 'on_lacs' or self.settings.lacs_condition != 'tokens'
                            or self.settings.bridge_tokens >= self.settings.lacs_tokens)):
                    b.add_goal(Goal(self, 'Skulls', 'path of #Skulls#', 'Pink', items=[{'name': 'Gold Skulltula Token', 'quantity': 100, 'minimum': self.settings.bridge_tokens, 'hintable': False}]))
                    b.goal_count = round(self.settings.bridge_tokens / 10)
                    b.minimum_goals = 1
                if (self.settings.bridge_hearts > self.settings.starting_hearts
                    and self.settings.bridge == 'hearts'
                    and (self.shuffle_ganon_bosskey != 'hearts'
                            or self.settings.bridge_hearts >= self.settings.ganon_bosskey_hearts)
                    and (self.shuffle_ganon_bosskey != 'on_lacs' or self.settings.lacs_condition != 'hearts'
                            or self.settings.bridge_hearts >= self.settings.lacs_hearts)):
                    b.add_goal(Goal(self, 'hearts', 'path of #hearts#', 'Red', items=[{'name': 'Piece of Heart', 'quantity': (20 - self.settings.starting_hearts) * 4, 'minimum': (self.settings.bridge_hearts - self.settings.starting_hearts) * 4, 'hintable': False}]))
                    b.goal_count = round((self.settings.bridge_hearts - 3) / 2)
                    b.minimum_goals = 1
                self.goal_categories[b.name] = b

            # If the Ganon's Boss Key condition is the same or similar conditions
            # as Bridge, do not create the goals if Bridge goals already cover
            # GBK goals. For example, 3 dungeon GBK would not have its own goals
            # if it is 4 medallion bridge.
            #
            # Even if created, there is no guarantee GBK goals will find new
            # locations to hint. If duplicate goals are defined for Bridge and
            # all of these goals are accessible without Ganon's Castle access,
            # the GBK category is redundant and not used for hint selection.
            if ((self.settings.ganon_bosskey_stones > 0
                    and self.shuffle_ganon_bosskey == 'stones'
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.ganon_bosskey_stones > self.settings.bridge_stones or self.settings.bridge != 'stones'))
                or (self.settings.lacs_stones > 0
                    and self.shuffle_ganon_bosskey == 'on_lacs' and self.settings.lacs_condition == 'stones'
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.lacs_stones > self.settings.bridge_stones or self.settings.bridge != 'stones'))
                or (self.settings.ganon_bosskey_rewards > 0
                    and self.shuffle_ganon_bosskey == 'dungeons'
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.ganon_bosskey_rewards > self.settings.bridge_medallions or self.settings.bridge != 'medallions')
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.ganon_bosskey_rewards > self.settings.bridge_stones or self.settings.bridge != 'stones')
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.ganon_bosskey_rewards > self.settings.bridge_rewards or self.settings.bridge != 'dungeons')
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.ganon_bosskey_rewards > 2 or self.settings.bridge != 'vanilla'))
                or (self.settings.lacs_rewards > 0
                    and self.shuffle_ganon_bosskey == 'on_lacs' and self.settings.lacs_condition == 'dungeons'
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.lacs_rewards > self.settings.bridge_medallions or self.settings.bridge != 'medallions')
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.lacs_rewards > self.settings.bridge_stones or self.settings.bridge != 'stones')
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.lacs_rewards > self.settings.bridge_rewards or self.settings.bridge != 'dungeons')
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.lacs_rewards > 2 or self.settings.bridge != 'vanilla'))):
                gbk.add_goal(Goal(self, 'Kokiri Emerald', { 'replace': 'Kokiri Emerald' }, 'Green', items=[{'name': 'Kokiri Emerald', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                gbk.add_goal(Goal(self, 'Goron Ruby', { 'replace': 'Goron Ruby' }, 'Red', items=[{'name': 'Goron Ruby', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                gbk.add_goal(Goal(self, 'Zora Sapphire', { 'replace': 'Zora Sapphire' }, 'Blue', items=[{'name': 'Zora Sapphire', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                gbk.minimum_goals = (self.settings.ganon_bosskey_stones if self.shuffle_ganon_bosskey == 'stones'
                    else self.settings.lacs_stones if self.shuffle_ganon_bosskey == 'on_lacs' and self.settings.lacs_condition == 'stones'
                    else self.settings.ganon_bosskey_rewards if self.shuffle_ganon_bosskey == 'dungeons'
                    else self.settings.lacs_rewards)
            if ((self.settings.ganon_bosskey_medallions > 0
                    and self.shuffle_ganon_bosskey == 'medallions'
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.ganon_bosskey_medallions > self.settings.bridge_medallions or self.settings.bridge != 'medallions')
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.ganon_bosskey_medallions > 2 or self.settings.bridge != 'vanilla'))
                or (self.settings.lacs_medallions > 0
                    and self.shuffle_ganon_bosskey == 'on_lacs' and self.settings.lacs_condition == 'medallions'
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.lacs_medallions > self.settings.bridge_medallions or self.settings.bridge != 'medallions')
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.lacs_medallions > 2 or self.settings.bridge != 'vanilla'))
                or (self.settings.ganon_bosskey_rewards > 0
                    and self.shuffle_ganon_bosskey == 'dungeons'
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.ganon_bosskey_rewards > self.settings.bridge_medallions or self.settings.bridge != 'medallions')
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.ganon_bosskey_rewards > self.settings.bridge_stones or self.settings.bridge != 'stones')
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.ganon_bosskey_rewards > self.settings.bridge_rewards or self.settings.bridge != 'dungeons')
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.ganon_bosskey_rewards > 2 or self.settings.bridge != 'vanilla'))
                or (self.settings.lacs_rewards > 0
                    and self.shuffle_ganon_bosskey == 'on_lacs' and self.settings.lacs_condition == 'dungeons'
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.lacs_rewards > self.settings.bridge_medallions or self.settings.bridge != 'medallions')
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.lacs_rewards > self.settings.bridge_stones or self.settings.bridge != 'stones')
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.lacs_rewards > self.settings.bridge_rewards or self.settings.bridge != 'dungeons')
                    and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.lacs_rewards > 2 or self.settings.bridge != 'vanilla'))):
                gbk.add_goal(Goal(self, 'Forest Medallion', { 'replace': 'Forest Medallion' }, 'Green', items=[{'name': 'Forest Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                gbk.add_goal(Goal(self, 'Fire Medallion', { 'replace': 'Fire Medallion' }, 'Red', items=[{'name': 'Fire Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                gbk.add_goal(Goal(self, 'Water Medallion', { 'replace': 'Water Medallion' }, 'Blue', items=[{'name': 'Water Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                gbk.add_goal(Goal(self, 'Shadow Medallion', { 'replace': 'Shadow Medallion' }, 'Pink', items=[{'name': 'Shadow Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                gbk.add_goal(Goal(self, 'Spirit Medallion', { 'replace': 'Spirit Medallion' }, 'Yellow', items=[{'name': 'Spirit Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                gbk.add_goal(Goal(self, 'Light Medallion', { 'replace': 'Light Medallion' }, 'Light Blue', items=[{'name': 'Light Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                gbk.minimum_goals = (self.settings.ganon_bosskey_medallions if self.shuffle_ganon_bosskey == 'medallions'
                    else self.settings.lacs_medallions if self.shuffle_ganon_bosskey == 'on_lacs' and self.settings.lacs_condition == 'medallions'
                    else self.settings.ganon_bosskey_rewards if self.shuffle_ganon_bosskey == 'dungeons'
                    else self.settings.lacs_rewards)
            if self.shuffle_ganon_bosskey == 'on_lacs' and self.settings.lacs_condition == 'vanilla':
                gbk.add_goal(Goal(self, 'Shadow Medallion', { 'replace': 'Shadow Medallion' }, 'Pink', items=[{'name': 'Shadow Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                gbk.add_goal(Goal(self, 'Spirit Medallion', { 'replace': 'Spirit Medallion' }, 'Yellow', items=[{'name': 'Spirit Medallion', 'quantity': 1, 'minimum': 1, 'hintable': False}]))
                gbk.minimum_goals = 2
            gbk.goal_count = len(gbk.goals)
            if (self.settings.ganon_bosskey_tokens > 0
                and self.shuffle_ganon_bosskey == 'tokens'
                and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower
                        or self.settings.bridge != 'tokens'
                        or self.settings.bridge_tokens < self.settings.ganon_bosskey_tokens)):
                gbk.add_goal(Goal(self, 'Skulls', 'path of #Skulls#', 'Pink', items=[{'name': 'Gold Skulltula Token', 'quantity': 100, 'minimum': self.settings.ganon_bosskey_tokens, 'hintable': False}]))
                gbk.goal_count = round(self.settings.ganon_bosskey_tokens / 10)
                gbk.minimum_goals = 1
            if (self.settings.lacs_tokens > 0
                and self.shuffle_ganon_bosskey == 'on_lacs' and self.settings.lacs_condition == 'tokens'
                and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower
                        or self.settings.bridge != 'tokens'
                        or self.settings.bridge_tokens < self.settings.lacs_tokens)):
                gbk.add_goal(Goal(self, 'Skulls', 'path of #Skulls#', 'Pink', items=[{'name': 'Gold Skulltula Token', 'quantity': 100, 'minimum': self.settings.lacs_tokens, 'hintable': False}]))
                gbk.goal_count = round(self.settings.lacs_tokens / 10)
                gbk.minimum_goals = 1
            if (self.settings.ganon_bosskey_hearts > self.settings.starting_hearts
                and self.shuffle_ganon_bosskey == 'hearts'
                and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower
                        or self.settings.bridge != 'hearts'
                        or self.settings.bridge_hearts < self.settings.ganon_bosskey_hearts)):
                gbk.add_goal(Goal(self, 'hearts', 'path of #hearts#', 'Red', items=[{'name': 'Piece of Heart', 'quantity': (20 - self.settings.starting_hearts) * 4, 'minimum': (self.settings.ganon_bosskey_hearts - self.settings.starting_hearts) * 4, 'hintable': False}]))
                gbk.goal_count = round((self.settings.ganon_bosskey_hearts - 3) / 2)
                gbk.minimum_goals = 1
            if (self.settings.lacs_hearts > self.settings.starting_hearts
                and self.shuffle_ganon_bosskey == 'on_lacs' and self.settings.lacs_condition == 'hearts'
                and (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower
                        or self.settings.bridge != 'hearts'
                        or self.settings.bridge_hearts < self.settings.lacs_hearts)):
                gbk.add_goal(Goal(self, 'hearts', 'path of #hearts#', 'Red', items=[{'name': 'Piece of Heart', 'quantity': (20 - self.settings.starting_hearts) * 4, 'minimum': (self.settings.lacs_hearts - self.settings.starting_hearts) * 4, 'hintable': False}]))
                gbk.goal_count = round((self.settings.lacs_hearts - 3) / 2)
                gbk.minimum_goals = 1

            # Ganon's Boss Key shuffled directly in the world will always
            # generate a category/goal pair, though locations are not
            # guaranteed if the higher priority Bridge category contains
            # all required locations for GBK
            if self.shuffle_ganon_bosskey in ['dungeon', 'overworld', 'any_dungeon', 'keysanity', 'regional']:
                # Make priority even with trials as the goal is no longer centered around dungeon completion or collectibles
                gbk.priority = 30
                gbk.goal_count = 1
                if self.settings.item_pool_value == 'plentiful':
                    keys = 2
                else:
                    keys = 1
                gbk.add_goal(Goal(self, 'the Key', 'path to #the Key#', 'Light Blue', items=[{'name': 'Boss Key (Ganons Castle)', 'quantity': keys, 'minimum': 1, 'hintable': True}]))
                gbk.minimum_goals = 1
            if gbk.goals:
                self.goal_categories[gbk.name] = gbk

            # To avoid too many goals in the hint selection phase,
            # trials are reduced to one goal with six items to obtain.
            if not self.skipped_trials['Forest']:
                trial_goal.items.append({'name': 'Forest Trial Clear', 'quantity': 1, 'minimum': 1, 'hintable': True})
                trials.goal_count += 1
            if not self.skipped_trials['Fire']:
                trial_goal.items.append({'name': 'Fire Trial Clear', 'quantity': 1, 'minimum': 1, 'hintable': True})
                trials.goal_count += 1
            if not self.skipped_trials['Water']:
                trial_goal.items.append({'name': 'Water Trial Clear', 'quantity': 1, 'minimum': 1, 'hintable': True})
                trials.goal_count += 1
            if not self.skipped_trials['Shadow']:
                trial_goal.items.append({'name': 'Shadow Trial Clear', 'quantity': 1, 'minimum': 1, 'hintable': True})
                trials.goal_count += 1
            if not self.skipped_trials['Spirit']:
                trial_goal.items.append({'name': 'Spirit Trial Clear', 'quantity': 1, 'minimum': 1, 'hintable': True})
                trials.goal_count += 1
            if not self.skipped_trials['Light']:
                trial_goal.items.append({'name': 'Light Trial Clear', 'quantity': 1, 'minimum': 1, 'hintable': True})
                trials.goal_count += 1

            # Trials category is finalized and saved only if at least one trial is on
            # If random trials are on and one world in multiworld gets 0 trials, still
            # add the goal to prevent key errors. Since no items fulfill the goal, it
            # will always be invalid for that world and not generate hints.
            if self.settings.trials > 0 or self.settings.trials_random:
                trials.add_goal(trial_goal)
                self.goal_categories[trials.name] = trials

            if (self.shuffle_special_dungeon_entrances or self.settings.shuffle_ganon_tower or self.settings.bridge == 'open') and (self.shuffle_ganon_bosskey == 'remove' or self.shuffle_ganon_bosskey == 'vanilla') and self.settings.trials == 0:
                g = GoalCategory('ganon', 30, goal_count=1)
                # Equivalent to WOTH, but added in case WOTH hints are disabled in favor of goal hints
                g.add_goal(Goal(self, 'the hero', 'path of #the hero#', 'White', items=[{'name': 'Triforce', 'quantity': 1, 'minimum': 1, 'hintable': True}]))
                g.minimum_goals = 1
                self.goal_categories[g.name] = g

    def get_region(self, region_name: str | Region) -> Region:
        if isinstance(region_name, Region):
            return region_name
        if (region := self._region_cache.get(region_name, None)) is not None:
            return region

        for region in self.regions:
            self._region_cache[region.name] = region
        if (region := self._region_cache.get(region_name, None)) is not None:
            return region
        raise KeyError('No such region %s' % region_name)

    def get_entrance(self, entrance_name: str | Entrance) -> Entrance:
        if isinstance(entrance_name, Entrance):
            return entrance_name
        if (entrance := self._entrance_cache.get(entrance_name, None)) is not None:
            return entrance

        for region in self.regions:
            for entrance in region.exits:
                self._entrance_cache[entrance.name] = entrance
        if (entrance := self._entrance_cache.get(entrance_name, None)) is not None:
            return entrance
        raise KeyError('No such entrance %s' % entrance_name)

    def get_location(self, location_name: str | Location) -> Location:
        if isinstance(location_name, Location):
            return location_name
        if (location := self._location_cache.get(location_name, None)) is not None:
            return location

        for region in self.regions:
            for location in region.locations:
                self._location_cache[location.name] = location
        if (location := self._location_cache.get(location_name, None)) is not None:
            return location
        raise KeyError('No such location %s' % location_name)

    def get_itempool_with_dungeon_items(self) -> Iterator[Item]:
        yield from self.get_restricted_dungeon_items()
        yield from self.itempool

    # get a list of items that should stay in their proper dungeon
    def get_restricted_dungeon_items(self) -> Iterator[Item]:
        for dungeon in self.dungeons:
            yield from dungeon.get_restricted_dungeon_items()

    # get a list of items that don't have to be in their proper dungeon
    def get_unrestricted_dungeon_items(self) -> Iterator[Item]:
        for dungeon in self.dungeons:
            yield from dungeon.get_unrestricted_dungeon_items()

    def silver_rupee_puzzles(self) -> list[str]:
        return ([
            'Shadow Temple Scythe Shortcut', 'Shadow Temple Huge Pit', 'Shadow Temple Invisible Spikes',
            'Gerudo Training Ground Slopes', 'Gerudo Training Ground Lava', 'Gerudo Training Ground Water',
            'Ganons Castle Fire Trial']
            + (['Dodongos Cavern Staircase'] if self.dungeon_mq['Dodongos Cavern'] else [])
            + ([] if self.dungeon_mq['Ice Cavern'] else ['Ice Cavern Spinning Scythe', 'Ice Cavern Push Block'])
            + ([] if self.dungeon_mq['Bottom of the Well'] else ['Bottom of the Well Basement'])
            + (['Shadow Temple Invisible Blades'] if self.dungeon_mq['Shadow Temple'] else [])
            + (['Spirit Temple Lobby and Lower Adult', 'Spirit Temple Adult Climb'] if self.dungeon_mq['Spirit Temple'] else ['Spirit Temple Child Early Torches', 'Spirit Temple Adult Boulders', 'Spirit Temple Sun Block'])
            + (['Ganons Castle Shadow Trial', 'Ganons Castle Water Trial'] if self.dungeon_mq['Ganons Castle'] else ['Ganons Castle Spirit Trial', 'Ganons Castle Light Trial', 'Ganons Castle Forest Trial'])
        )

    def find_items(self, item: str) -> list[Location]:
        return [location for location in self.get_locations() if location.item is not None and location.item.name == item]

    def push_item(self, location: str | Location, item: Item, manual: bool = False) -> None:
        if not isinstance(location, Location):
            location = self.get_location(location)

        location.item = item
        item.location = location
        item.price = location.price if location.price is not None else item.price
        location.price = item.price

        logging.getLogger('').debug('Placed %s [World %d] at %s [World %d]', item, item.world.id if hasattr(item, 'world') else -1, location, location.world.id if hasattr(location, 'world') else -1)

    def get_locations(self) -> list[Location]:
        if not self._cached_locations:
            for region in self.regions:
                self._cached_locations.extend(region.locations)
        return self._cached_locations

    def get_unfilled_locations(self) -> Iterable[Location]:
        return filter(Location.has_no_item, self.get_locations())

    def get_filled_locations(self) -> Iterable[Location]:
        return filter(Location.has_item, self.get_locations())

    def get_progression_locations(self) -> Iterable[Location]:
        return filter(Location.has_progression_item, self.get_locations())

    def get_entrances(self) -> list[Entrance]:
        return [exit for region in self.regions for exit in region.exits]

    def get_shufflable_entrances(self, type=None, only_primary=False) -> list[Entrance]:
        return [entrance for entrance in self.get_entrances() if (type is None or entrance.type == type) and (not only_primary or entrance.primary)]

    def get_shuffled_entrances(self, type=None, only_primary=False) -> list[Entrance]:
        return [entrance for entrance in self.get_shufflable_entrances(type=type, only_primary=only_primary) if entrance.shuffled]

    def region_has_shortcuts(self, region_name: str) -> bool:
        region = self.get_region(region_name)
        dungeon_name = HintArea.at(region).dungeon_name
        return dungeon_name in self.settings.dungeon_shortcuts

    # Function to run exactly once after placing items in drop locations for each world
    # Sets all Drop locations to a unique name in order to avoid name issues and to identify locations in the spoiler
    def set_drop_location_names(self):
        for location in self.get_locations():
            if location.type == 'Drop':
                location.name = location.parent_region.name + " " + location.name

    def update_exclude_item_list(self) -> None:
        # these are items that can never be required but are still considered major items
        self.exclude_item_list = [
            'Double Defense',
            'Ice Arrows',
        ]

        if (self.settings.damage_multiplier != 'ohko' and self.settings.damage_multiplier != 'quadruple' and
            self.settings.shuffle_scrubs == 'off' and not self.settings.shuffle_grotto_entrances):
            # Nayru's Love may be required to prevent forced damage
            self.exclude_item_list.append('Nayrus Love')
        if 'logic_grottos_without_agony' in self.settings.allowed_tricks and self.settings.hints != 'agony':
            # Stone of Agony skippable if not used for hints or grottos
            self.exclude_item_list.append('Stone of Agony')
        if not self.shuffle_special_interior_entrances and not self.settings.shuffle_overworld_entrances and not self.settings.warp_songs:
            # Serenade and Prelude are never required unless one of those settings is enabled
            self.exclude_item_list.append('Serenade of Water')
            self.exclude_item_list.append('Prelude of Light')
        if self.settings.logic_rules == 'glitchless':
            # Both two-handed swords can be required in glitch logic, so only consider them foolish in glitchless
            self.exclude_item_list.append('Biggoron Sword')
            self.exclude_item_list.append('Giants Knife')
        if self.settings.plant_beans:
            # Magic Beans are useless if beans are already planted
            self.exclude_item_list.append('Magic Bean')
            self.exclude_item_list.append('Buy Magic Bean')
            self.exclude_item_list.append('Magic Bean Pack')
        if 'logic_lens_botw' in self.settings.allowed_tricks or self.settings.shuffle_pots in ('off', 'overworld'):
            # These silver rupees unlock a door to an area that's also reachable with lens
            self.exclude_item_list.append('Silver Rupee (Bottom of the Well Basement)')
            self.exclude_item_list.append('Silver Rupee Pouch (Bottom of the Well Basement)')
        if self.dungeon_mq['Shadow Temple'] and self.settings.shuffle_mapcompass == 'vanilla':
            # These silver rupees only unlock the map chest
            self.exclude_item_list.append('Silver Rupee (Shadow Temple Scythe Shortcut)')
            self.exclude_item_list.append('Silver Rupee Pouch (Shadow Temple Scythe Shortcut)')
        if 'logic_spirit_sun_chest_no_rupees' in self.settings.allowed_tricks and 'logic_spirit_sun_chest_bow' not in self.settings.allowed_tricks:
            # With this trickset, these silver rupees are logically irrelevant
            self.exclude_item_list.append('Silver Rupee (Spirit Temple Sun Block)')
            self.exclude_item_list.append('Silver Rupee Pouch (Spirit Temple Sun Block)')
        if self.settings.shuffle_pots in ('off', 'overworld') and self.settings.trials == 0:
            # These silver rupees only lock pots and trial completion
            self.exclude_item_list.append('Silver Rupee (Ganons Castle Light Trial)')
            self.exclude_item_list.append('Silver Rupee Pouch (Ganons Castle Light Trial)')
            self.exclude_item_list.append('Silver Rupee (Ganons Castle Fire Trial)')
            self.exclude_item_list.append('Silver Rupee Pouch (Ganons Castle Fire Trial)')
            self.exclude_item_list.append('Silver Rupee (Ganons Castle Shadow Trial)')
            self.exclude_item_list.append('Silver Rupee Pouch (Ganons Castle Shadow Trial)')
            self.exclude_item_list.append('Silver Rupee (Ganons Castle Water Trial)')
            self.exclude_item_list.append('Silver Rupee Pouch (Ganons Castle Water Trial)')
            self.exclude_item_list.append('Silver Rupee (Ganons Castle Forest Trial)')
            self.exclude_item_list.append('Silver Rupee Pouch (Ganons Castle Forest Trial)')
            if self.dungeon_mq['Ganons Castle'] and self.settings.shuffle_freestanding_items in ('off', 'overworld') and not self.shuffle_silver_rupees:
                # MQ Ganon small keys only lock pots, freestanding recovery hearts, silver rupees, and trial completion
                self.exclude_item_list.append('Small Key (Ganons Castle)')
                self.exclude_item_list.append('Small Key Ring (Ganons Castle)')
        if not any(setting in ('medallions', 'dungeons') for setting in (self.settings.bridge, self.shuffle_ganon_bosskey, self.settings.lacs_condition)):
            self.exclude_item_list.append('Light Medallion')
            if 'vanilla' not in (self.settings.bridge, self.settings.lacs_condition):
                self.exclude_item_list.append('Shadow Medallion')
                self.exclude_item_list.append('Spirit Medallion')

        for i in self.item_hint_type_overrides['barren']:
            if i in self.exclude_item_list:
                self.exclude_item_list.remove(i)

        for i in self.item_added_hint_types['barren']:
            if not (i in self.exclude_item_list):
                self.exclude_item_list.append(i)

    # Useless areas are areas that have contain no items that could ever
    # be used to complete the seed. Unfortunately this is very difficult
    # to calculate since that involves trying every possible path and item
    # set collected to know this. To simplify this we instead just get areas
    # that don't have any items that could ever be required in any seed.
    # We further cull this list with woth info. This is an overestimate of
    # the true list of possible useless areas, but this will generate a
    # reasonably sized list of areas that fit this property.
    def update_useless_areas(self, spoiler: Spoiler) -> None:
        areas: dict[HintArea, dict[str, Any]] = {}
        # Link's Pocket and None are not real areas
        excluded_areas = [None, HintArea.ROOT]
        for location in self.get_locations():
            location_hint = HintArea.at(location)

            # We exclude event and locked locations. This means that medallions
            # and stones are not considered here. This is not really an accurate
            # way of doing this, but it's the only way to allow dungeons to appear.
            # So barren hints do not include these dungeon rewards.
            if (
                location_hint in excluded_areas
                or location.locked
                or location.name in self.hint_exclusions
                or location.item is None
                or location.item.type == 'Event'
                or (location.item.type == 'DungeonReward' and location.item.world.settings.shuffle_dungeon_rewards in ('vanilla', 'reward', 'dungeon'))
            ):
                continue

            area = location_hint

            # Build the area list and their items
            if area not in areas:
                areas[area] = {
                    'locations': [],
                }
            areas[area]['locations'].append(location)

        # Generate area list meta data
        for area, area_info in areas.items():
            # whether an area is a dungeon is calculated to prevent too many
            # dungeon barren hints since they are quite powerful. The area
            # names don't quite match the internal dungeon names so we need to
            # check if any location in the area has a dungeon.
            area_info['dungeon'] = False
            for location in area_info['locations']:
                if location.parent_region.dungeon is not None:
                    area_info['dungeon'] = True
                    break
            # Weight the area's chance of being chosen based on its size.
            # Small areas are more likely to barren, so we apply this weight
            # to make all areas have a more uniform chance of being chosen
            area_info['weight'] = len(area_info['locations'])

        # The idea here is that if an item shows up in woth, then the only way
        # that another copy of that major item could ever be required is if it
        # is a progressive item. Normally this applies to things like bows, bombs
        # bombchus, bottles, slingshot, magic and ocarina. However if plentiful
        # item pool is enabled this could be applied to any item.
        duplicate_item_woth = {}
        woth_loc = [location for world_woth in spoiler.required_locations.values() for location in world_woth]
        for world in spoiler.worlds:
            duplicate_item_woth[world.id] = {}
        for location in woth_loc:
            world_id = location.item.world.id
            item = location.item

            if item.name == 'Rutos Letter' and item.name in duplicate_item_woth[world_id]:
                # Only the first Letter counts as a letter, subsequent ones are Bottles.
                # It doesn't matter which one is considered bottle/letter, since they will
                # both we considered not useless.
                item_name = 'Bottle'
            elif item.special.get('bottle', False):
                # Bottles can have many names but they are all generally the same in logic.
                # The letter and big poe bottles will give a bottle item, so no additional
                # checks are required for them.
                item_name = 'Bottle'
            else:
                item_name = item.name

            if item_name not in self.item_hint_type_overrides['barren']:
                if item_name not in duplicate_item_woth[world_id]:
                    duplicate_item_woth[world_id][item_name] = []
                duplicate_item_woth[world_id][item_name].append(location)

        # generate the empty area list
        self.empty_areas = {}

        for area, area_info in areas.items():
            useless_area = True
            for location in area_info['locations']:
                world_id = location.item.world.id
                item = location.item

                if ((not location.item.majoritem) or (location.item.name in location.item.world.exclude_item_list)) and \
                    (location.item.name not in self.item_hint_type_overrides['barren']):
                    # Minor items are always useless in logic
                    continue

                is_bottle = False
                if item.name == 'Rutos Letter' and item.name in duplicate_item_woth[world_id]:
                    # If this is the required Letter then it is not useless
                    dupe_locations = duplicate_item_woth[world_id][item.name]
                    for dupe_location in dupe_locations:
                        if dupe_location.world.id == location.world.id and dupe_location.name == location.name:
                            useless_area = False
                            break
                    # Otherwise it is treated as a bottle
                    is_bottle = True

                if is_bottle or item.special.get('bottle', False):
                    # Bottle Items are all interchangable. Logic currently only needs
                    # a max on 1 bottle, but this might need to be changed in the
                    # future if using multiple bottles for fire temple diving is added
                    # to logic
                    dupe_locations = duplicate_item_woth[world_id].get('Bottle', [])
                    max_progressive = 1
                elif item.name == 'Bottle with Big Poe':
                    # The max number of requred Big Poe Bottles is based on the setting
                    dupe_locations = duplicate_item_woth[world_id].get(item.name, [])
                    max_progressive = self.settings.big_poe_count
                elif item.name == 'Progressive Wallet':
                    dupe_locations = duplicate_item_woth[world_id].get(item.name, [])
                    max_progressive = self.maximum_wallets
                else:
                    dupe_locations = duplicate_item_woth[world_id].get(item.name, [])
                    max_progressive = item.special.get('progressive', 1)

                # If this is a required item location, then it is not useless
                for dupe_location in dupe_locations:
                    if dupe_location.world.id == location.world.id and dupe_location.name == location.name:
                        useless_area = False
                        break

                # If there are sufficient required item known, then the remaining
                # copies of the items are useless.
                if len(dupe_locations) < max_progressive:
                    useless_area = False
                    break

            if useless_area:
                self.empty_areas[area] = area_info

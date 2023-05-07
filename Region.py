from enum import Enum, unique

from ItemList import REWARD_COLORS


@unique
class RegionType(Enum):

    Overworld = 1
    Interior = 2
    Dungeon = 3
    Grotto = 4


    @property
    def is_indoors(self):
        """Shorthand for checking if Interior or Dungeon"""
        return self in (RegionType.Interior, RegionType.Dungeon, RegionType.Grotto)


# Pretends to be an enum, but when the values are raw ints, it's much faster
class TimeOfDay(object):
    NONE = 0
    DAY = 1
    DAMPE = 2
    ALL = DAY | DAMPE


class Region(object):

    def __init__(self, name, type=RegionType.Overworld):
        self.name = name
        self.type = type
        self.entrances = []
        self.exits = []
        self.locations = []
        self.dungeon = None
        self.world = None
        self.hint_name = None
        self.alt_hint_name = None
        self.price = None
        self.world = None
        self.time_passes = False
        self.provides_time = TimeOfDay.NONE
        self.scene = None
        self.is_boss_room = False
        self.savewarp = None


    def copy(self, new_world):
        new_region = Region(self.name, self.type)
        new_region.world = new_world
        new_region.price = self.price
        new_region.hint_name = self.hint_name
        new_region.alt_hint_name = self.alt_hint_name
        new_region.time_passes = self.time_passes
        new_region.provides_time = self.provides_time
        new_region.scene = self.scene
        new_region.is_boss_room = self.is_boss_room
        new_region.savewarp = None if self.savewarp is None else self.savewarp.copy(new_region)

        if self.dungeon:
            new_region.dungeon = self.dungeon.name
        new_region.locations = [location.copy(new_region) for location in self.locations]
        new_region.exits = [exit.copy(new_region) for exit in self.exits]

        return new_region


    @property
    def hint(self):
        from Hints import HintArea

        if self.hint_name is not None:
            return HintArea[self.hint_name]
        if self.dungeon:
            return self.dungeon.hint

    @property
    def alt_hint(self):
        from Hints import HintArea

        if self.alt_hint_name is not None:
            return HintArea[self.alt_hint_name]


    def can_fill(self, item, manual=False):
        from Hints import HintArea
        from ItemPool import closed_forest_restricted_items, triforce_blitz_items

        if not manual and self.world.settings.empty_dungeons_mode != 'none' and item.dungeonitem:
            # An empty dungeon can only store its own dungeon items
            if self.dungeon and self.dungeon.world.empty_dungeons[self.dungeon.name].empty:
                return self.dungeon.is_dungeon_item(item) and item.world.id == self.world.id
            # Items from empty dungeons can only be in their own dungeons
            for dungeon in item.world.dungeons:
                if item.world.empty_dungeons[dungeon.name].empty and dungeon.is_dungeon_item(item):
                    return False

        if not manual and self.world.settings.require_gohma and item.name in (*closed_forest_restricted_items, 'Slingshot'):
            hint_area = HintArea.at(self, gc_woods_warp_is_forest=True)
            if hint_area.color == 'Green' and hint_area != HintArea.FOREST_TEMPLE and self.name != 'Queen Gohma Boss Room':
                # Don't place items that can be used to escape the forest in Forest areas of worlds with Require Gohma
                if item.name in closed_forest_restricted_items:
                    return False
            else:
                # Place at least one slingshot for each player in the Forest area, to avoid requiring one player to leave the forest to get another player's slingshot.
                # This is still not a 100% guarantee because the slingshot could be behind an item that's not in the forest, such as in a bombable grotto entrance in the Lost Woods.
                if item.name == 'Slingshot':
                    return False

        is_self_dungeon_restricted = False
        is_self_region_restricted = None
        is_hint_color_restricted = None
        is_dungeon_restricted = False
        is_overworld_restricted = False

        if item.type in ('Map', 'Compass', 'SmallKey', 'HideoutSmallKey', 'TCGSmallKey', 'BossKey', 'GanonBossKey', 'SilverRupee', 'DungeonReward'):
            shuffle_setting = (
                item.world.settings.shuffle_mapcompass if item.type in ('Map', 'Compass') else
                item.world.settings.shuffle_smallkeys if item.type == 'SmallKey' else
                item.world.settings.shuffle_hideoutkeys if item.type == 'HideoutSmallKey' else
                item.world.settings.shuffle_tcgkeys if item.type == 'TCGSmallKey' else
                item.world.settings.shuffle_bosskeys if item.type == 'BossKey' else
                item.world.settings.shuffle_ganon_bosskey if item.type == 'GanonBossKey' else
                item.world.settings.shuffle_silver_rupees if item.type == 'SilverRupee' else
                item.world.settings.shuffle_dungeon_rewards if item.type == 'DungeonReward' else
                None
            )

            is_self_dungeon_restricted = (shuffle_setting == 'dungeon' or (shuffle_setting == 'vanilla' and item.type != 'DungeonReward')) and item.type not in ('HideoutSmallKey', 'TCGSmallKey')
            is_self_region_restricted = [HintArea.GERUDO_FORTRESS, HintArea.THIEVES_HIDEOUT] if shuffle_setting == 'fortress' else None
            if item.name in REWARD_COLORS:
                is_hint_color_restricted = [REWARD_COLORS[item.name]] if shuffle_setting == 'regional' else None
            else:
                is_hint_color_restricted = [HintArea.for_dungeon(item.name).color] if shuffle_setting == 'regional' else None
            is_dungeon_restricted = shuffle_setting == 'any_dungeon'
            is_overworld_restricted = shuffle_setting == 'overworld'
        elif item.name in triforce_blitz_items:
            is_dungeon_restricted = True

        if is_self_dungeon_restricted and not manual:
            hint_area = HintArea.at(self)
            if item.name == 'Light Medallion':
                return hint_area in (HintArea.ROOT, HintArea.TEMPLE_OF_TIME)
            else:
                return hint_area.is_dungeon and hint_area.is_dungeon_item(item) and item.world.id == self.world.id

        if is_self_region_restricted and not manual:
            return HintArea.at(self) in is_self_region_restricted and item.world.id == self.world.id

        if is_hint_color_restricted and not manual:
            return HintArea.at(self).color in is_hint_color_restricted

        if is_dungeon_restricted and not manual:
            return HintArea.at(self).is_dungeon

        if is_overworld_restricted and not manual:
            return not HintArea.at(self).is_dungeon

        if item.triforce_piece:
            return item.world.id == self.world.id

        return True


    def get_scene(self):
        if self.scene:
            return self.scene
        elif self.dungeon:
            return self.dungeon.name
        else:
            return None


    def __str__(self):
        return str(self.__unicode__())


    def __unicode__(self):
        return '%s' % self.name


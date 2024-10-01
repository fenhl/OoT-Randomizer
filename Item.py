from __future__ import annotations
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Optional, Any, overload

from ItemList import GetItemId, item_table
from RulesCommon import allowed_globals, escape_name

if TYPE_CHECKING:
    from Location import Location
    from World import World


class ItemInfo:
    items: dict[str, ItemInfo] = {}
    events: dict[str, ItemInfo] = {}
    bottles: set[str] = set()
    medallions: set[str] = set()
    stones: set[str] = set()
    junk_weight: dict[str, int] = {}
    ocarina_buttons: set[str] = set()

    solver_ids: dict[str, int] = {}
    bottle_ids: set[int] = set()
    medallion_ids: set[int] = set()
    stone_ids: set[int] = set()
    ocarina_buttons_ids: set[int] = set()

    def __init__(self, name: str = '', event: bool = False) -> None:
        if event:
            item_type = 'Event'
            progressive = True
            item_id = None
            special = None
        else:
            (item_type, progressive, item_id, special) = item_table[name]

        self.name: str = name
        self.advancement: bool = (progressive is True)
        self.priority: bool = (progressive is False)
        self.type: str = item_type
        self.special: dict[str, Any] = special or {}
        self.index: Optional[int] = item_id
        self.price: Optional[int] = self.special.get('price', None)
        self.bottle: bool = self.special.get('bottle', False)
        self.medallion: bool = self.special.get('medallion', False)
        self.stone: bool = self.special.get('stone', False)
        self.alias: Optional[tuple[str, int]] = self.special.get('alias', None)
        self.junk: Optional[int] = self.special.get('junk', None)
        self.trade: bool = self.special.get('trade', False)
        self.ocarina_button: bool = self.special.get('ocarina_button', False)

        self.solver_id: Optional[int] = None
        if name and self.junk is None:
            esc = escape_name(name)
            if esc not in ItemInfo.solver_ids:
                allowed_globals[esc] = ItemInfo.solver_ids[esc] = len(ItemInfo.solver_ids)
            self.solver_id = ItemInfo.solver_ids[esc]


for item_name in item_table:
    iteminfo = ItemInfo.items[item_name] = ItemInfo(item_name)
    if iteminfo.bottle:
        ItemInfo.bottles.add(item_name)
        ItemInfo.bottle_ids.add(ItemInfo.solver_ids[escape_name(item_name)])
    if iteminfo.medallion:
        ItemInfo.medallions.add(item_name)
        ItemInfo.medallion_ids.add(ItemInfo.solver_ids[escape_name(item_name)])
    if iteminfo.stone:
        ItemInfo.stones.add(item_name)
        ItemInfo.stone_ids.add(ItemInfo.solver_ids[escape_name(item_name)])

    if iteminfo.junk is not None:
        ItemInfo.junk_weight[item_name] = iteminfo.junk

    if iteminfo.ocarina_button:
        ItemInfo.ocarina_buttons.add(item_name)
        ItemInfo.ocarina_buttons_ids.add(ItemInfo.solver_ids[escape_name(item_name)])

class Item:
    def __init__(self, name: str = '', world: Optional[World] = None, event: bool = False) -> None:
        self.name: str = name
        self.location: Optional[Location] = None
        self.event: bool = event
        if event:
            if name not in ItemInfo.events:
                ItemInfo.events[name] = ItemInfo(name, event=True)
        self.info: ItemInfo = ItemInfo.events[name] if event else ItemInfo.items[name]
        self.price: Optional[int] = self.info.special.get('price', None)
        self.world: Optional[World] = world
        self.looks_like_item: Optional[Item] = None
        self.priority: bool = self.info.priority
        self.type: str = self.info.type
        self.special: dict = self.info.special
        self.alias: Optional[tuple[str, int]] = self.info.alias

        self.solver_id: Optional[int] = self.info.solver_id
        # Do not alias to junk--it has no solver id!
        self.alias_id: Optional[int] = ItemInfo.solver_ids[escape_name(self.alias[0])] if self.alias else None

    def copy(self) -> Item:
        new_item = Item(name=self.name, world=self.world, event=self.event)

        new_item.location = self.location
        new_item.price = self.price
        new_item.looks_like_item = self.looks_like_item

        return new_item

    @property
    def index(self) -> Optional[int]:
        idx = self.info.index
        if self.type == 'Shop':
            # Some shop items have the same item IDs as unrelated regular items. Make sure these don't get turned into nonsense.
            return idx
        # use different item IDs for items with conditional chest appearances so they appear according to the setting in the item's world, not the location's
        if idx == GetItemId.GI_SKULL_TOKEN:
            big_chest = self.world.settings.bridge == 'tokens' or self.world.settings.lacs_condition == 'tokens' or self.world.shuffle_ganon_bosskey == 'tokens'
            freeze_link = self.world.settings.tokensanity != 'off'
            return {
                (False, False): GetItemId.GI_SKULL_TOKEN,
                (False, True): GetItemId.GI_SKULL_TOKEN_NORMAL_TEXT,
                (True, False): GetItemId.GI_SKULL_TOKEN_BIG_CHEST,
                (True, True): GetItemId.GI_SKULL_TOKEN_BIG_CHEST_NORMAL_TEXT,
            }[big_chest, freeze_link]
        if idx in (GetItemId.GI_HEART_CONTAINER, GetItemId.GI_HEART_PIECE, GetItemId.GI_HEART_PIECE_WIN) and (self.world.settings.bridge == 'hearts' or self.world.settings.lacs_condition == 'hearts' or self.world.shuffle_ganon_bosskey == 'hearts'):
            return {
                GetItemId.GI_HEART_CONTAINER: GetItemId.GI_HEART_CONTAINER_BIG_CHEST,
                GetItemId.GI_HEART_PIECE: GetItemId.GI_HEART_PIECE_BIG_CHEST,
                GetItemId.GI_HEART_PIECE_WIN: GetItemId.GI_HEART_PIECE_WIN_BIG_CHEST,
            }[idx]
        if idx in (GetItemId.GI_SHIELD_DEKU, GetItemId.GI_SHIELD_HYLIAN) and 'shields' in self.world.settings.minor_items_as_major_chest:
            return {
                GetItemId.GI_SHIELD_DEKU: GetItemId.GI_SHIELD_DEKU_BIG_CHEST,
                GetItemId.GI_SHIELD_HYLIAN: GetItemId.GI_SHIELD_HYLIAN_BIG_CHEST,
            }[idx]
        if idx in (GetItemId.GI_BOMBCHUS_5, GetItemId.GI_BOMBCHUS_10, GetItemId.GI_BOMBCHUS_20) and (self.world.settings.free_bombchu_drops or 'bombchus' in self.world.settings.minor_items_as_major_chest):
            return {
                GetItemId.GI_BOMBCHUS_5: GetItemId.GI_BOMBCHUS_5_BIG_CHEST,
                GetItemId.GI_BOMBCHUS_10: GetItemId.GI_BOMBCHUS_10_BIG_CHEST,
                GetItemId.GI_BOMBCHUS_20: GetItemId.GI_BOMBCHUS_20_BIG_CHEST,
            }[idx]
        if idx in (GetItemId.GI_PROGRESSIVE_NUT_CAPACITY, GetItemId.GI_PROGRESSIVE_STICK_CAPACITY) and 'capacity' in self.world.settings.minor_items_as_major_chest:
            return {
                GetItemId.GI_PROGRESSIVE_NUT_CAPACITY: GetItemId.GI_PROGRESSIVE_NUT_CAPACITY_BIG_CHEST,
                GetItemId.GI_PROGRESSIVE_STICK_CAPACITY: GetItemId.GI_PROGRESSIVE_STICK_CAPACITY_BIG_CHEST,
            }[idx]
        # use different item IDs for keyrings that include boss keys so the effect and text box displayed depend on the setting in the item's world, not the location's
        if GetItemId.GI_SMALL_KEY_RING_FOREST_TEMPLE <= idx <= GetItemId.GI_SMALL_KEY_RING_SHADOW_TEMPLE and self.world.settings.keyring_give_bk:
            return idx + GetItemId.GI_SMALL_KEY_RING_FOREST_TEMPLE_WITH_BOSS_KEY - GetItemId.GI_SMALL_KEY_RING_FOREST_TEMPLE
        return idx

    @property
    def key(self) -> bool:
        return self.smallkey or self.bosskey

    @property
    def smallkey(self) -> bool:
        return self.type == 'SmallKey' or self.type == 'HideoutSmallKey' or  self.type == 'TCGSmallKey'

    @property
    def bosskey(self) -> bool:
        return self.type == 'BossKey' or self.type == 'GanonBossKey'

    @property
    def map(self) -> bool:
        return self.type == 'Map'

    @property
    def compass(self) -> bool:
        return self.type == 'Compass'

    @property
    def dungeonitem(self) -> bool:
        return self.smallkey or self.bosskey or self.map or self.compass or self.type == 'SilverRupee'

    @property
    def unshuffled_dungeon_item(self) -> bool:
        if self.world is None:
            return False
        return ((self.type == 'SmallKey' and self.world.settings.shuffle_smallkeys in ('remove', 'vanilla', 'dungeon')) or
                (self.type == 'HideoutSmallKey' and self.world.settings.shuffle_hideoutkeys == 'vanilla') or
                (self.type == 'TCGSmallKey' and self.world.settings.shuffle_tcgkeys in ('remove', 'vanilla')) or
                (self.type == 'BossKey' and self.world.settings.shuffle_bosskeys in ('remove', 'vanilla', 'dungeon')) or
                (self.type == 'GanonBossKey' and self.world.shuffle_ganon_bosskey in ('remove', 'vanilla', 'dungeon')) or
                ((self.map or self.compass) and (self.world.settings.shuffle_mapcompass in ('remove', 'startwith', 'vanilla', 'dungeon'))) or
                (self.type == 'SilverRupee' and self.world.settings.shuffle_silver_rupees in ('remove', 'vanilla', 'dungeon')) or
                (self.type == 'DungeonReward' and self.world.settings.shuffle_dungeon_rewards in ('vanilla', 'reward', 'dungeon')))

    @property
    def majoritem(self) -> bool:
        if self.world is None:
            return False
        if self.type == 'Token':
            return (self.world.settings.bridge == 'tokens' or self.world.shuffle_ganon_bosskey == 'tokens' or
                (self.world.shuffle_ganon_bosskey == 'on_lacs' and self.world.settings.lacs_condition == 'tokens'))

        if self.type in ('Drop', 'Event', 'Shop') or not self.advancement:
            return False

        if self.name.startswith('Bombchus') and not self.world.settings.free_bombchu_drops:
            return False

        if self.name == 'Heart Container' or self.name.startswith('Piece of Heart'):
            return (self.world.settings.bridge == 'hearts' or self.world.shuffle_ganon_bosskey == 'hearts' or
                (self.world.shuffle_ganon_bosskey == 'on_lacs' and self.world.settings.lacs_condition == 'hearts'))

        if self.map or self.compass:
            return False
        if self.type == 'DungeonReward' and self.world.settings.shuffle_dungeon_rewards in ('vanilla', 'reward', 'dungeon'):
            return False
        if self.type == 'SmallKey' and self.world.settings.shuffle_smallkeys in ('dungeon', 'vanilla'):
            return False
        if self.type == 'HideoutSmallKey' and self.world.settings.shuffle_hideoutkeys == 'vanilla':
            return False
        if self.type == 'TCGSmallKey' and self.world.settings.shuffle_tcgkeys == 'vanilla':
            return False
        if self.type == 'BossKey' and self.world.settings.shuffle_bosskeys in ('dungeon', 'vanilla'):
            return False
        if self.type == 'GanonBossKey' and self.world.shuffle_ganon_bosskey in ('dungeon', 'vanilla'):
            return False
        if self.type == 'SilverRupee' and self.world.settings.shuffle_silver_rupees in ('dungeon', 'vanilla'):
            return False

        return True

    @property
    def goalitem(self) -> bool:
        if self.world is None:
            return False
        return self.name in self.world.goal_items

    @property
    def triforce_piece(self) -> bool:
        from ItemPool import triforce_pieces

        return self.name in triforce_pieces

    @property
    def advancement(self) -> bool:
        if self.name == 'Gold Skulltula Token' and self.world is not None and self.world.max_tokens == 0:
            return False
        return self.info.advancement

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.world.__repr__()} {self.name}"


@overload
def ItemFactory(items: str, world: Optional[World] = None, event: bool = False) -> Item:
    pass


@overload
def ItemFactory(items: Iterable[str], world: Optional[World] = None, event: bool = False) -> list[Item]:
    pass


def ItemFactory(items: str | Iterable[str], world: Optional[World] = None, event: bool = False) -> Item | list[Item]:
    if isinstance(items, str):
        if not event and items not in ItemInfo.items:
            raise KeyError('Unknown Item: %s' % items)
        return Item(items, world, event)

    ret = []
    for item in items:
        if not event and item not in ItemInfo.items:
            raise KeyError('Unknown Item: %s' % item)
        ret.append(Item(item, world, event))

    return ret


def make_event_item(name: str, location: Location, item: Optional[Item] = None) -> Item:
    if location.world is None:
        raise Exception(f"`make_event_item` called with location '{location.name}' that doesn't have a world.")
    if item is None:
        item = Item(name, location.world, event=True)
    location.world.push_item(location, item)
    location.locked = True
    if name not in item_table:
        location.internal = True
    location.world.event_items.add(name)
    return item


def is_item(name: str) -> bool:
    return name in item_table


def ItemIterator(predicate: Callable[[Item], bool] = lambda item: True, world: Optional[World] = None) -> Iterable[Item]:
    for item_name in item_table:
        item = ItemFactory(item_name, world)
        if predicate(item):
            yield item

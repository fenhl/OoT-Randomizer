from __future__ import annotations
import enum
from enum import Enum
from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from Region import Region
    from RulesCommon import AccessRule
    from World import World


class EntranceKind(Enum):
    Dungeon         = enum.auto()
    DungeonSpecial  = enum.auto()
    ChildBoss       = enum.auto()
    AdultBoss       = enum.auto()
    SpecialBoss     = enum.auto()
    Interior        = enum.auto()
    SpecialInterior = enum.auto()
    Hideout         = enum.auto()
    Grotto          = enum.auto()
    Grave           = enum.auto()
    Overworld       = enum.auto()
    OverworldOneWay = enum.auto()
    OwlDrop         = enum.auto()
    Spawn           = enum.auto()
    WarpSong        = enum.auto()
    BlueWarp        = enum.auto()
    Extra           = enum.auto()


#TODO rename this class and all instance variables/properties
class NewEntrance:
    def __init__(self, source: Region, target: str, rule: str):
        # Terminology:
        # source_source is the region that contains the loading zone represented by this entrance
        # source_target is the region the loading zone leads to in vanilla
        # target_source is a region leading to target_target in vanilla, to disambiguate the position within the region
        # target_target is the region the loading zone leads to in this randomizer seed
        # For example, if playing Bolero places you in the graveyard standing in front of Dampé's house, this is represented as:
        # source_source = Bolero of Fire Warp, source_target = DMC Central Local, target_source = Graveyard Dampes House, target_target = Graveyard
        self.source_source: Region = source
        self.source_target: str | Region = target
        self.target_source: Optional[Region] = None
        self.target_target: Optional[Region] = None

        self.rule_string: str = rule
        self.access_rule: AccessRule = lambda state, **kwargs: True
        self.access_rules: list[AccessRule] = []

        self.entrance_data: dict[str, Any] = {}
        self.entrance_kind: Optional[EntranceKind] = None
        self.is_shuffled: bool = False
        self.reverse_entrance: Optional[NewEntrance] = None

    def set_rule(self, lambda_rule: AccessRule) -> None:
        self.access_rule = lambda_rule
        self.access_rules = [lambda_rule]

    def bind_two_way(self, other_entrance: NewEntrance) -> None:
        self.reverse_entrance = other_entrance
        other_entrance.reverse_entrance = self

    @property
    def inferred_world(self) -> World:
        return self.source_source.world

    # For compatibility with Location | Entrance duck typing (e.g. Rule_AST_Transformer.current_spot):

    @property
    def name(self) -> str:
        return str(self)

    @property
    def parent_region(self) -> Region:
        return self.source_source

    @property
    def type(self) -> Optional[str]:
        return None

    def __str__(self) -> str:
        return f'{self.source_source} -> {self.source_target}'

    def __repr__(self) -> str:
        if self.target_target is None:
            return f'{self.source_source!r} -> {self.source_target!r} (disconnected)'
        elif self.target_source == self.source_source and self.target_target == self.source_target:
            return f'{self.source_source!r} -> {self.source_target!r} (vanilla)'
        else:
            return f'{self.source_source!r} -> {self.source_target!r} (leads to {self.target_target!r} from {self.target_source!r})'

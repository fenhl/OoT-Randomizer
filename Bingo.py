from __future__ import annotations
from typing import TYPE_CHECKING

from Item import ItemInfo
from RulesCommon import escape_name

if TYPE_CHECKING:
    from State import State


LINES: tuple[tuple[int, ...], ...] = (
    # rows
    (0, 1, 2, 3, 4),
    (5, 6, 7, 8, 9),
    (10, 11, 12, 13, 14),
    (15, 16, 17, 18, 19),
    (20, 21, 22, 23, 24),
    # columns
    (0, 5, 10, 15, 20),
    (1, 6, 11, 16, 21),
    (2, 7, 12, 17, 22),
    (3, 8, 13, 18, 23),
    (4, 9, 14, 19, 24),
    # diagonals
    (0, 6, 12, 18, 24),
    (4, 8, 12, 16, 20),
)

FAIRY_SPELLS: set[int] = {
    ItemInfo.solver_ids[escape_name(item_name)]
    for item_name
    in ('Dins Fire', 'Farores Wind', 'Nayrus Love')
}
Gold_Skulltula_Token: int = ItemInfo.solver_ids['Gold_Skulltula_Token']


def has_goal(state: State, goal: str) -> bool:
    if goal == '15 Different Skulltulas':
        return state.has(Gold_Skulltula_Token, 15)
    elif goal == 'Defeat both Flare Dancers':
        if state.world.dungeon_mq['Fire Temple']:
            raise NotImplementedError() #TODO
        else:
            raise NotImplementedError() #TODO
    elif goal == 'Two Fairy Spells':
        return state.count_of(FAIRY_SPELLS) >= 2
    else:
        raise NotImplementedError(f'Unimplemented bingo goal: {goal!r}') #TODO

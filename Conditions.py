from __future__ import annotations
import ast
from typing import TYPE_CHECKING, Any, NoReturn

from Item import Item, ItemFactory
from Region import TimeOfDay
from RuleParser import escaped_items

if TYPE_CHECKING:
    from Item import Item
    from Rom import Rom
    from RulesCommon import AccessRule
    from World import World


MAX_INSTRUCTIONS: int = 1 # length of condition areas in config.asm, divided by 4


class ConditionCompiler(ast.NodeTransformer):
    def __init__(self, world: World) -> None:
        self.world = world

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        node.values = [self.visit(operand) for operand in node.values]
        return node

    def visit_Constant(self, node: ast.Constant) -> Any:
        if node.value is True:
            return node
        raise NotImplementedError(f'Cannot parse custom Constant rule `{ast.unparse(node)}`')

    def visit_Name(self, node: ast.Name) -> Any:
        #TODO Rule_AST_Transformer attributes
        #TODO logic helpers
        if node.id in escaped_items:
            return ItemFactory(escaped_items[node.id], self.world)
        #TODO World attributes
        #TODO settings
        #TODO State attributes
        #TODO age, spot, tod, TimeOfDay
        #TODO events
        raise NotImplementedError(f'Cannot parse custom Name rule `{ast.unparse(node)}`')

    def generic_visit(self, node: Any) -> NoReturn:
        raise NotImplementedError(f'Cannot parse custom rule `{ast.unparse(node)}` of type {type(node)}')

    # Parse entry point
    def parse_condition(self, rule_string: str) -> Any:
        return self.visit(ast.parse(rule_string, mode='eval').body)

class Condition:
    def __init__(self, world, rule_string) -> None:
        self.world: World = world
        self.rule_string: str = rule_string
        self.access_rule: AccessRule = world.parser.parse_rule(rule_string)
        self.rule: Any = ConditionCompiler(world).parse_condition(rule_string)

    def __len__(self) -> int:
        return num_instructions(self.rule)

    def __repr__(self) -> str:
        return f'Condition({self.world!r}, {self.rule_string!r})'

    def __str__(self) -> str:
        return self.rule_string

    @property
    def required_stones(self) -> int:
        return min_required(self.rule, ['Kokiri Emerald', 'Goron Ruby', 'Zora Sapphire'])

    @property
    def required_medallions(self) -> int:
        return min_required(self.rule, ['Light Medallion', 'Forest Medallion', 'Fire Medallion', 'Water Medallion', 'Shadow Medallion', 'Spirit Medallion'])

    @property
    def required_tokens(self) -> int:
        return min_required(self.rule, ['Gold Skulltula Token'])

    def is_met_by_starting_items(self) -> bool: #TODO include effective starting items?
        spot = self.world.get_region('Root')
        return (self.access_rule(self.world.state, spot=spot, age='adult', tod=TimeOfDay.NONE)
            and self.access_rule(self.world.state, spot=spot, age='child', tod=TimeOfDay.NONE))

    def may_require(self, item: Item) -> bool:
        return may_require(self.rule, item)

    def compile(self, rom: Rom, sym: int) -> None:
        if len(self) > MAX_INSTRUCTIONS:
            raise RuntimeError(f'Code for custom condition `{self}` requires more space in ROM')
        rom.write_bytes(sym, compile_rule(self.rule))


# Returns whether this item may be required if all other items are unavailable.
def may_require(rule: Any, item: Item) -> bool:
    if isinstance(rule, ast.BoolOp):
        return any(may_require(operand, item) for operand in rule.values)
    elif isinstance(rule, Item):
        return item == rule.name or isinstance(item, Item) and item.name == rule.name

    raise NotImplementedError(f'may_require({rule!r}, {item!r})') #TODO

# Returns the minimum number of items required from the given list, assuming all other items are available.
# For example, a 5-dungeon-reward condition will return 2 for the list of medallions, since the other 3 required rewards can be stones.
def min_required(rule: Any, items: list[Item | str]) -> int:
    if isinstance(rule, ast.BoolOp):
        if isinstance(rule.op, ast.And):
            return max(min_required(operand, items) for operand in rule.values)
        elif isinstance(rule.op, ast.Or):
            return min(min_required(operand, items) for operand in rule.values)
    elif isinstance(rule, Item):
        return int(any(item == rule.name or isinstance(item, Item) and item.name == rule.name for item in items))

    raise NotImplementedError(f'min_required({rule!r}, {items!r})') #TODO

def num_instructions(rule: Any) -> int:
    if isinstance(rule, ast.BoolOp):
        return sum(num_instructions(operand) for operand in rule.values) + 2

    return len(compile_rule(rule))

def compile_rule(rule: Any) -> list[int]:
    if isinstance(rule, Item):
        if rule.name == 'Ice Arrows':
            return [
                0x8081007E, # lb at, 0x7E(a0) ; at = item ID in Ice Arrows slot
                0x3408000C, # li t0, 0x0C     ; t0 = item ID for Ice Arrows
                0x14280002, # bne at, t0, 2   ; if at != t0, skip the "li v0, 1" instruction
                0x34020000, # li v0, 0        ; v0 = 0
                0x34020001, # li v0, 1        ; v0 = 1
                0x03E00008, # jr ra           ; return v0
            ]
        else:
            raise NotImplementedError(f'compile_rule for item {rule.name!r}') #TODO

    raise NotImplementedError(f'compile_rule({rule!r})') #TODO

from __future__ import annotations
from math import ceil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Location import Location
    from World import World



def get_all_collectible_flags(world):
    scene_flags = {}
    for i in range(0, 101):
        scene_flags[i] = []
        for location in world.get_locations():
            if(location.scene == i and location.type in ["Freestanding", "Pot", "FlyingPot", "Crate", "SmallCrate", "Beehive", "RupeeTower"]):
                default = location.default
                if(isinstance(default, list)): #List of alternative room/setup/flag to use
                    default = location.default[0] #Use the first tuple as the primary tuple
                if(isinstance(default, tuple)):
                    room, setup, flag = default
                    room_setup = room + (setup << 6)
                    #flag = (room_setup << 8) + flag
                    scene_flags[i].append((room, flag))
                    #scene_flags[i].append(flag)
        scene_flags[i].sort()
        if len(scene_flags[i]) == 0:
            del scene_flags[i]
        #scene_flags.append((i, max_enemy_flag))
    return scene_flags
# Create a dict of dicts of the format:
# {
#   scene_number_n : {
#       room_setup_number: max_flags
#   }
# }
# where room_setup_number defines the room + scene setup as ((setup << 6) + room) for scene n
# and max_flags is the highest used enemy flag for that setup/room
def get_collectible_flag_table(world: World) -> tuple[dict[int, dict[int, int]], list[tuple[Location, tuple[int, int, int], tuple[int, int, int]]]]:
    scene_flags = {}
    alt_list = []
    for i in range(0, 101):
        scene_flags[i] = {}
        for location in world.get_locations():
            if location.scene == i and location.type in ["Freestanding", "Pot", "FlyingPot", "Crate", "SmallCrate", "Beehive", "RupeeTower", "SilverRupee", "Wonderitem", "EnemyDrop", "GossipStone"]:
                default = location.default
                if isinstance(default, list):  # List of alternative room/setup/flag to use
                    primary_tuple = default[0]
                    for c in range(1, len(default)):
                        alt_list.append((location, default[c], primary_tuple))
                    default = location.default[0] #Use the first tuple as the primary tuple
                if isinstance(default, tuple):
                    if location.scene == 0x3E: # Grottos need to be handled separately because they suck
                        room, grotto_id, flag = default #14 rooms (4 bits), 0x1F grottos (5 bits), 
                        room_setup = (room << 5) + grotto_id
                    else:
                        room, setup, flag = default
                        room_setup = room + (setup << 6)
                    if room_setup in scene_flags[i].keys():
                        curr_room_max_flag = scene_flags[i][room_setup]
                        if flag > curr_room_max_flag:
                            scene_flags[i][room_setup] = flag
                    else:
                        scene_flags[i][room_setup] = flag
        if len(scene_flags[i].keys()) == 0:
            del scene_flags[i]
    return scene_flags, alt_list


# Create a byte array from the scene flag table created by get_collectible_flag_table
def get_collectible_flag_table_bytes(scene_flag_table: dict[int, dict[int, int]]) -> tuple[bytearray, int]:
    num_flag_bytes = 0
    bytes = bytearray()
    bytes.append(len(scene_flag_table.keys())) # Append # of scenes
    for scene_id in scene_flag_table.keys(): # For every scene
        if(scene_id == 0x3E): # Grotto
            print("here")
        rooms = scene_flag_table[scene_id]
        room_count = len(rooms.keys())
        bytes.append(scene_id) # Append the scene ID
        bytes.append(room_count) # Append the # of rooms in the scene
        for room in rooms: # For every room in the scene
            if scene_id == 0x3E:
                bytes.append((room & 0x1E0) >> 5)
                bytes.append((room & 0x1F))
            else:
                bytes.append(room) # Append the room #
            bytes.append((num_flag_bytes & 0xFF00) >> 8) # Append the number of bytes
            bytes.append(num_flag_bytes & 0x00FF )
            num_flag_bytes += ceil((rooms[room] + 1) / 8)

    return bytes, num_flag_bytes


def get_alt_list_bytes(alt_list: list[tuple[Location, tuple[int, int, int], tuple[int, int, int]]]) -> bytearray:
    bytes = bytearray()
    for entry in alt_list:
        location, alt, primary = entry
        room, scene_setup, flag = alt
        if location.scene is None:
            continue

        alt_override = (room << 8) + (scene_setup << 14) + flag
        room, scene_setup, flag = primary
        primary_override = (room << 8) + (scene_setup << 14) + flag
        bytes.append(location.scene)
        bytes.append(0x06)
        bytes.append((alt_override & 0xFF00) >> 8)
        bytes.append(alt_override & 0xFF)
        bytes.append(location.scene)
        bytes.append(0x06)
        bytes.append((primary_override & 0xFF00) >> 8)
        bytes.append(primary_override & 0xFF)
    return bytes

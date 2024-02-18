from __future__ import annotations
import random
import sys
from collections.abc import Callable, Sequence
from itertools import chain
from typing import TYPE_CHECKING, Optional

from Fill import ShuffleError

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    TypeAlias = str

if TYPE_CHECKING:
    from Rom import Rom
    from World import World

ActivationTransform: TypeAlias = "Callable[[list[int]], list[int]]"
PlaybackTransform: TypeAlias = "Callable[[list[dict[str, int]]], list[dict[str, int]]]"
Transform: TypeAlias = "ActivationTransform | PlaybackTransform"

PLAYBACK_START: int = 0xB781DC
PLAYBACK_LENGTH: int = 0xA0
ACTIVATION_START: int = 0xB78E5C
ACTIVATION_LENGTH: int = 0x09

FORMAT_ACTIVATION: dict[int, str] = {
    0: 'A',
    1: 'v',
    2: '>',
    3: '<',
    4: '^',
}

READ_ACTIVATION: dict[str, int] = {  # support both Av><^ and ADRLU
    'a': 0,
    'v': 1,
    'd': 1,
    '>': 2,
    'r': 2,
    '<': 3,
    'l': 3,
    '^': 4,
    'u': 4,
}

ACTIVATION_TO_PLAYBACK_NOTE: dict[int, int] = {
    0: 0x02,  # A
    1: 0x05,  # Down
    2: 0x09,  # Right
    3: 0x0B,  # Left
    4: 0x0E,  # Up
    0xFF: 0xFF,  # Rest
}

DIFFICULTY_ORDER: list[str] = [
    'Zeldas Lullaby',
    'Sarias Song',
    'Eponas Song',
    'Song of Storms',
    'Song of Time',
    'Suns Song',
    'Prelude of Light',
    'Minuet of Forest',
    'Bolero of Fire',
    'Serenade of Water',
    'Requiem of Spirit',
    'Nocturne of Shadow',
]

#    Song name:           (rom index, kind,   vanilla activation),
SONG_TABLE: dict[str, tuple[Optional[int], str, str]] = {
    'Zeldas Lullaby':        (   8, 'frog',   '<^><^>'),
    'Eponas Song':           (   7, 'frog',   '^<>^<>'),
    'Sarias Song':           (   6, 'frog',   'v><v><'),
    'Suns Song':             (   9, 'frog',   '>v^>v^'),
    'Song of Time':          (  10, 'frog',   '>Av>Av'),
    'Song of Storms':        (  11, 'frog',   'Av^Av^'),
    'Minuet of Forest':      (   0, 'warp',   'A^<><>'),
    'Bolero of Fire':        (   1, 'warp',   'vAvA>v>v'),
    'Serenade of Water':     (   2, 'warp',   'Av>><'),
    'Requiem of Spirit':     (   3, 'warp',   'AvA>vA'),
    'Nocturne of Shadow':    (   4, 'warp',   '<>>A<>v'),
    'Prelude of Light':      (   5, 'warp',   '^>^><^'),
    'ZR Frogs Ocarina Game': (None, 'frogs2', 'A<>v<>vAvAv><A'),
}


# checks if one list is a sublist of the other (in either direction)
# python is magic.....
def subsong(song1: Song, song2: Song) -> bool:
    # convert both lists to strings
    s1 = ''.join( map(chr, song1.activation))
    s2 = ''.join( map(chr, song2.activation))
    # check if either is a substring of the other
    return (s1 in s2) or (s2 in s1)


# give random durations and volumes to the notes
def fast_playback(activation: list[int]) -> list[dict[str, int]]:
    playback = []
    for note_index, note in enumerate(activation):
        playback.append({'note': note, 'duration': 0x04, 'volume': 0x57})
    return playback


# give random durations and volumes to the notes
def random_playback(activation: list[int]) -> list[dict[str, int]]:
    playback = []
    for note_index, note in enumerate(activation):
        duration = random.randint(0x8, 0x20)
        # make final note longer on average
        if note_index + 1 >= len(activation):
            duration = random.randint(0x10, 0x30)
        volume = random.randint(0x40, 0x60)
        playback.append({'note': note, 'duration': duration, 'volume': volume})
        # randomly rest
        if random.random() < 0.1:
            duration = random.randint(0x8, 0x18)
            playback.append({'note': 0xFF, 'duration': duration, 'volume': 0})
    return playback


# gives random volume and duration to the notes of piece
def random_piece_playback(piece: list[int]) -> list[dict[str, int]]:
    playback = []
    for note in piece:
        duration = random.randint(0x8, 0x20)
        volume = random.randint(0x40, 0x60)
        playback.append({'note': note, 'duration': duration, 'volume': volume})
    return playback


# takes the volume/duration of playback, and notes of piece, and creates a playback piece
# assumes the lists are the same length
def copy_playback_info(playback: list[dict[str, int]], piece: list[int]):
    return [{'note': n, 'volume': p['volume'], 'duration': p['duration']} for (p, n) in zip(playback, piece)]


def identity(x: list[int | dict[str, int]]) -> list[int | dict[str, int]]:
    return x


def random_piece(count: int, allowed: Sequence[int] = range(0, 5)) -> list[int]:
    return random.choices(allowed, k=count)


def invert_piece(piece: list[int]) -> list[int]:
    return [4 - note for note in piece]


def reverse_piece(piece: list[int | dict[str, int]]) -> list[int | dict[str, int]]:
    return piece[::-1]


def clamp(val: int, low: int, high: int) -> int:
    return max(low, min(high, val))


def transpose_piece(amount: int) -> ActivationTransform:
    def transpose(piece: list[int]) -> list[int]:
        return [clamp(note + amount, 0, 4) for note in piece]
    return transpose


def compose(f: Transform, g: Transform) -> Transform:
    return lambda x: f(g(x))


def add_transform_to_piece(piece: list[int], transform: ActivationTransform) -> list[int]:
    return piece + transform(piece)


def repeat(piece: list[int]) -> list[int]:
    return 2 * piece


# a Song contains its simple note data, as well as the data to be stored into the rom
class Song:
    # create a song, based on a given scheme
    def __init__(self, rand_song: bool = True, piece_size: int = 3, extra_position: str = 'none',
                 starting_range: Sequence[int] = range(0, 5), activation_transform: ActivationTransform = identity,
                 playback_transform: PlaybackTransform = identity, *, activation: Optional[list[int]] = None,
                 playback_fast: bool = False) -> None:
        self.length: int = 0
        self.activation: list[int] = []
        self.playback: list[dict[str, int]] = []
        self.activation_data: list[int] = []
        self.playback_data: list[int] = []
        self.total_duration: int = 0

        if activation:
            self.length = len(activation)
            self.activation = activation
        elif rand_song:
            self.length = random.randint(4, 8)
            self.activation = random.choices(range(0, 5), k=self.length)
        else:
            if extra_position != 'none':
                piece_size = 3
            piece = random_piece(piece_size, starting_range)
            self.two_piece_playback(piece, extra_position, activation_transform, playback_transform)

        if playback_fast:
            self.playback = fast_playback(self.activation)
            self.break_repeated_notes(0x03)
        else:
            if not self.playback:
                self.playback = random_playback(self.activation)
            self.break_repeated_notes()

        self.format_activation_data()
        self.format_playback_data()

        if activation:
            self.increase_duration_to(45)

    def increase_duration_to(self, duration: int) -> None:
        if self.total_duration >= duration:
            return

        duration_needed = duration - self.total_duration
        last_note_duration = self.playback[-1]['duration']
        last_note_adds = 0x7F - last_note_duration

        if last_note_adds >= duration_needed:
            self.playback[-1]['duration'] += duration_needed
            self.format_playback_data()
            return
        else:
            self.playback[-1]['duration'] = 0x7F
            duration_needed -= last_note_adds
        while duration_needed >= 0x7F:
            self.playback.append({'note': 0xFF, 'duration': 0x7F, 'volume': 0})
            duration_needed -= 0x7F
        self.playback.append({'note': 0xFF, 'duration': duration_needed, 'volume': 0})
        self.format_playback_data()

    def fix_song_duration(self, duration: int) -> None:
        if self.total_duration == duration:
            return

        # If too short, we just increase it.
        if self.total_duration < duration:
            self.increase_duration_to(duration)
            return

        # Else reduce the duration equitably.
        total_duration_to_cut = self.total_duration - duration
        duration_to_cut_for_each_note = total_duration_to_cut // len(self.playback) + 1
        for note_index, note in enumerate(self.playback):
            if note['duration'] <= duration_to_cut_for_each_note:
                raise ShuffleError('Could not fix song duration')
            note['duration'] -= duration_to_cut_for_each_note
        self.format_playback_data()
        duration_to_add_back_on_last = duration - self.total_duration
        self.playback[-1]['duration'] += duration_to_add_back_on_last
        self.format_playback_data()

    def two_piece_playback(self, piece: list[int], extra_position: str = 'none', activation_transform: ActivationTransform = identity,
                           playback_transform: PlaybackTransform = identity) -> None:
        piece_length = len(piece)
        piece2 = activation_transform(piece)
        # add playback parameters
        playback_piece1 = random_piece_playback(piece)
        playback_piece2 = copy_playback_info(playback_transform(playback_piece1), piece2)
        if extra_position == 'none':
            self.length = 2 * piece_length
            self.activation = piece + piece2
            # add a rest between
            duration = random.randint(0x8, 0x18)
            rest = {'note': 0xFF, 'duration': duration, 'volume': 0}
            self.playback = playback_piece1 + [rest] + playback_piece2
        else:
            self.length = 2 * piece_length + 1
            extra = random_piece(1)
            extra_playback = random_piece_playback(extra)
            if extra_position == 'start':
                self.activation = extra + piece + piece2
                self.playback = extra_playback + playback_piece1 + playback_piece2
            elif extra_position == 'middle':
                self.activation = piece + extra + piece2
                self.playback = playback_piece1 + extra_playback + playback_piece2
            elif extra_position == 'end':
                self.activation = piece + piece2 + extra
                self.playback = playback_piece1 + playback_piece2 + extra_playback

    # add rests between repeated notes in the playback so that they work in-game
    def break_repeated_notes(self, duration: int = 0x08) -> None:
        new_playback = []
        for note_index, note in enumerate(self.playback):
            new_playback.append(note)
            if ( note_index + 1 < len(self.playback) ) and \
               ( self.playback[note_index]['note'] == self.playback[note_index + 1]['note'] ):
                new_playback.append( {'note': 0xFF, 'duration': duration, 'volume': 0} )
        self.playback = new_playback

    # create the list of bytes that will be written into the rom for the activation
    def format_activation_data(self) -> None:
        # data is 1 byte for the song length,
        # len bytes for the song, and the remainder is padding
        padding = [0] * (ACTIVATION_LENGTH - (self.length + 1))
        self.activation_data = [self.length] + self.activation + padding

    # create the list of byte that will  be written in to the rom for the playback
    def format_playback_data(self) -> None:
        self.playback_data = []

        self.total_duration = 0
        for note in self.playback:
            pitch = ACTIVATION_TO_PLAYBACK_NOTE[ note['note'] ]
            self.playback_data += [pitch, 0, 0, note['duration'], note['volume'], 0, 0, 0]
            self.total_duration += note['duration']
        # add a rest at the end
        self.playback_data += [0xFF, 0, 0, 0, 0x5A, 0, 0, 0]
        # pad the rest of the song
        padding = [0] * (PLAYBACK_LENGTH - len(self.playback_data))
        self.playback_data += padding

    def __repr__(self) -> str:
        activation_string = 'Activation Data:\n\t' + ' '.join( map( "{:02x}".format, self.activation_data) )
        # break playback into groups of 8...
        index = 0
        broken_up_playback = []
        while index < len(self.playback_data):
            broken_up_playback.append( self.playback_data[index:index + 8])
            index += 8
        playback_string = 'Playback Data:\n\t' + '\n\t'.join( map( lambda line: ' '.join( map( "{:02x}".format, line) ), broken_up_playback ) )
        return activation_string + '\n' + playback_string

    @classmethod
    def from_str(cls, notes: str) -> Song:
        return cls(activation=[READ_ACTIVATION[note.lower()] for note in notes])

    def __str__(self) -> str:
        return ''.join(FORMAT_ACTIVATION[note] for note in self.activation)


# randomly choose song parameters
def get_random_song() -> Song:
    rand_song = random.choices([True, False], [1, 9])[0]
    piece_size = random.choices([3, 4], [5, 2])[0]
    extra_position = random.choices(['none', 'start', 'middle', 'end'], [12, 1, 1, 1])[0]
    activation_transform = identity
    playback_transform = identity
    weight_damage = 0
    should_transpose = random.choices([True, False], [1, 4])[0]
    starting_range = range(0, 5)
    if should_transpose:
        weight_damage = 2
        direction = random.choices(['up', 'down'], [1, 1])[0]
        if direction == 'up':
            starting_range = range(0, 4)
            activation_transform = transpose_piece(1)
        elif direction == 'down':
            starting_range = range(1, 5)
            activation_transform = transpose_piece(-1)
    should_invert = random.choices([True, False], [3 - weight_damage, 6])[0]
    if should_invert:
        weight_damage += 1
        activation_transform = compose(invert_piece, activation_transform)
    should_reflect = random.choices([True, False], [5 - weight_damage, 4])[0]
    if should_reflect:
        activation_transform = compose(reverse_piece, activation_transform)
        playback_transform = reverse_piece

    # print([rand_song, piece_size, extra_position, starting_range, should_transpose, should_invert, should_reflect])

    song = Song(rand_song, piece_size, extra_position, starting_range, activation_transform, playback_transform)

    # rate its difficulty
    difficulty = piece_size * 12
    if extra_position != 'none':
        difficulty += 12
    if should_transpose:
        difficulty += 25
    if should_reflect:
        difficulty += 10
    if should_invert:
        difficulty += 20
    if rand_song:
        difficulty = 11 * len(song.activation)

    song.difficulty = difficulty
    return song


# create a list of 12 songs, none of which are sub-strings of any other song
def generate_song_list(world: World, frog: bool, warp: bool, frogs2: bool) -> dict[str, Song]:
    fixed_songs = {}
    if not frog:
        fixed_songs.update({name: Song.from_str(notes) for name, (_, kind, notes) in SONG_TABLE.items() if kind == 'frog'})
    if not warp:
        fixed_songs.update({name: Song.from_str(notes) for name, (_, kind, notes) in SONG_TABLE.items() if kind == 'warp'})
    if not frogs2:
        fixed_songs.update({name: Song.from_str(notes) for name, (_, kind, notes) in SONG_TABLE.items() if kind == 'frogs2'})
    fixed_songs.update({name: Song.from_str(notes) for name, notes in world.distribution.configure_songs().items()})
    for name1, song1 in fixed_songs.items():
        if name1 not in SONG_TABLE:
            raise ValueError(f'Unknown song: {name1!r}. Please use one of these: {", ".join(SONG_TABLE)}')
        if not song1.activation:
            raise ValueError(f'{name1} is empty')
        if name1 == 'ZR Frogs Ocarina Game':
            if len(song1.activation) != 14:
                raise ValueError(f'{name1} song must be exactly 14 notes')
        else:
            if len(song1.activation) > 8:
                raise ValueError(f'{name1} is too long (maximum is 8 notes)')
        for name2, song2 in fixed_songs.items():
            if name2 != 'ZR Frogs Ocarina Game' and name1 != name2 and subsong(song1, song2):
                raise ValueError(f'{name2} is unplayable because it contains {name1}')
    random_songs = []

    for _ in range(12 - sum(name != 'ZR Frogs Ocarina Game' for name in fixed_songs)):
        for _ in range(1000):
            # generate a completely random song
            song = get_random_song()
            # test the song against all existing songs
            is_good = True

            for other_song in chain((song for name, song in fixed_songs.items() if name != 'ZR Frogs Ocarina Game'), random_songs):
                if subsong(song, other_song):
                    is_good = False
            if is_good:
                random_songs.append(song)
                break

    if len(fixed_songs) + len(random_songs) < 12:
        # this can happen if the fixed songs are so short that any random set of songs would have them as subsongs
        raise ShuffleError('Could not generate random songs')

    # sort the songs by length
    random_songs.sort(key=lambda s: s.difficulty)
    for name in DIFFICULTY_ORDER:
        if name not in fixed_songs:
            fixed_songs[name] = random_songs.pop(0)

    if 'ZR Frogs Ocarina Game' not in fixed_songs:
        fixed_songs['ZR Frogs Ocarina Game'] = Song(activation=[random.randint(0, 4) for _ in range(14)])

    return fixed_songs


# replace the playback and activation requirements for the ocarina songs
def patch_songs(world: World, rom: Rom) -> None:
    for name, song in world.song_notes.items():
        if str(song) == SONG_TABLE[name][2]:
            continue  # song activation is vanilla (possibly because this row wasn't randomized), don't randomize playback

        if name == 'ZR Frogs Ocarina Game':
            rom.write_bytes(0xB78AA0, [note['note'] for note in song.playback])
            continue

        # fix the song of time
        if name == 'Song of Time':
            song.increase_duration_to(260)

        # Suns Song having a different length than vanilla duration can lead to it sometimes not working, notably in MQ Spirit Symphony room.
        if name == 'Suns Song':
            song.fix_song_duration(208)

        # write the song to the activation table
        cur_offset = ACTIVATION_START + SONG_TABLE[name][0] * ACTIVATION_LENGTH
        rom.write_bytes(cur_offset, song.activation_data)

        # write the songs to the playback table
        song_offset = PLAYBACK_START + SONG_TABLE[name][0] * PLAYBACK_LENGTH
        rom.write_bytes(song_offset, song.playback_data)

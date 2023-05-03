from enum import Enum
import re

from Utils import data_path


ENG_TEXT_START = 0x92_D000
JPN_TEXT_START = 0x8E_B000
GERMAN_TEXT_START = 0x8F_4000
FRENCH_TEXT_START = 0x93_0000
ENG_TEXT_SIZE_LIMIT = 0x3_9000
JPN_TEXT_SIZE_LIMIT = 0x3_B000

JPN_TABLE_START = 0xB8_08AC
ENG_TABLE_START = 0xB8_49EC
PAL_ENG_TABLE_START = 0xB8_01DC
GERMAN_TABLE_START = 0xB8_4404
FRENCH_TABLE_START = 0xB8_6514
CREDITS_TABLE_START = 0xB8_8C0C

JPN_TABLE_SIZE = ENG_TABLE_START - JPN_TABLE_START
ENG_TABLE_SIZE = CREDITS_TABLE_START - ENG_TABLE_START

EXTENDED_TABLE_START = JPN_TABLE_START # start writing entries to the jp table instead of english for more space
EXTENDED_TABLE_SIZE = JPN_TABLE_SIZE + ENG_TABLE_SIZE # 0x8360 bytes, 4204 entries

EXTENDED_TEXT_START = JPN_TABLE_START # start writing text to the jp table instead of english for more space
EXTENDED_TEXT_SIZE_LIMIT = JPN_TEXT_SIZE_LIMIT + ENG_TEXT_SIZE_LIMIT # 0x74000 bytes


# Temporary type-safe wrapper around `str` to help migrate to the new system
class NewText:
    def __init__(self, text=''):
        if not isinstance(text, str):
            raise TypeError()
        self.text = text

    def __iadd__(self, other):
        if not isinstance(other, NewText):
            raise TypeError()
        self.text += other.text
        return self

    def __str__(self):
        return self.text


# convert byte array to an integer
def bytes_to_int(bytes, signed=False):
    return int.from_bytes(bytes, byteorder='big', signed=signed)


# convert int to an array of bytes of the given width
def int_to_bytes(num, width, signed=False):
    return int.to_bytes(num, width, byteorder='big', signed=signed)


MAC_JAPANESE_SINGLE = {}
MAC_JAPANESE_DOUBLE = {}
MAC_JAPANESE_ENCODE = {}
with open(data_path('macjapanese.txt'), encoding='utf-8') as f:
    for line in f:
        if not line.strip() or line.startswith('#'):
            continue
        match = re.match('0x([0-9A-F]+)\t(0x[0-9A-F]+(?:\\+0x[0-9A-F]+)*)\t#', line)
        codepoints = ''.join(
            chr(int(re.fullmatch('0x([0-9A-F]+)', codepoint).group(1), 16))
            for codepoint in match.group(2).split('+')
        )
        MAC_JAPANESE_ENCODE[codepoints] = int_to_bytes(int(match.group(1), 16), len(match.group(1)) // 2)
        if len(match.group(1)) == 2:
            MAC_JAPANESE_SINGLE[int(match.group(1), 16)] = NewText(codepoints)
        elif len(match.group(1)) == 4:
            MAC_JAPANESE_DOUBLE[int(match.group(1), 16)] = NewText(codepoints)
        else:
            raise ValueError('Failed to parse macjapanese.txt')


INTL_COLOR_MAP = {
    'White':      0x40,
    'Red':        0x41,
    'Green':      0x42,
    'Blue':       0x43,
    'Light Blue': 0x44,
    'Pink':       0x45,
    'Yellow':     0x46,
    'Black':      0x47,
}
INTL_REVERSE_COLOR_MAP = {code: name for name, code in INTL_COLOR_MAP.items()}

class ControlSequence:
    def __init__(self, code, param_width):
        self.code = code
        self.param_width = param_width

    # returns a randomizer-specific internal string representation for this control sequence
    def __call__(self, param):
        return NewText(self.code + ''.join(chr(0xEF00 + byte) for byte in int_to_bytes(param, self.param_width)))

def COLOR(color):
    return NewText('\uEE00' + chr(0xEF00 + INTL_COLOR_MAP[color]))

# Randomizer-specific internal string representations of control codes and sequences.
# These are used for consistency between handling Japanese and international text,
# and are placed in a section of Unicode's Private Use Area that's commonly used for encoding hacks but not used by MacJapanese.
# Defining them allows in-game text to be internally represented as Python `str` objects.
BOX_BREAK = NewText('\uEE01')
GAP = ControlSequence('\uEE02', 1)
GO_TO = ControlSequence('\uEE03', 2)
INSTANT = NewText('\uEE04')
UN_INSTANT = NewText('\uEE05')
KEEP_OPEN = NewText('\uEE06')
EVENT = NewText('\uEE07')
BOX_BREAK_AFTER = ControlSequence('\uEE08', 1)
FADE_AFTER = ControlSequence('\uEE09', 1)
PLAYER_NAME = NewText('\uEE0A')
OCARINA = NewText('\uEE0B')
SOUND_EFFECT = ControlSequence('\uEE0C', 2)
ICON = ControlSequence('\uEE0D', 1)
CHARACTER_DELAY = ControlSequence('\uEE0E', 1)
BACKGROUND = ControlSequence('\uEE0F', 3)
MARATHON_TIME = NewText('\uEE10')
RACE_TIME = NewText('\uEE11')
POINTS = NewText('\uEE12')
SKULLTULA_COUNT = NewText('\uEE13')
UNSKIPPABLE = NewText('\uEE14')
TWO_CHOICE = NewText('\uEE15')
THREE_CHOICE = NewText('\uEE16')
FISH_WEIGHT = NewText('\uEE17')
HIGH_SCORE = ControlSequence('\uEE18', 1)
TIME_OF_DAY = NewText('\uEE19')
BUTTON_A = NewText('\uEE1A')
BUTTON_B = NewText('\uEE1B')
BUTTON_C = NewText('\uEE1C')
BUTTON_L = NewText('\uEE1D')
BUTTON_R = NewText('\uEE1E')
BUTTON_Z = NewText('\uEE1F')
BUTTON_C_UP = NewText('\uEE20')
BUTTON_C_DOWN = NewText('\uEE21')
BUTTON_C_LEFT = NewText('\uEE22')
BUTTON_C_RIGHT = NewText('\uEE23')
TRIANGLE = NewText('\uEE24')
CONTROL_STICK = NewText('\uEE25')
COLOR_PLACEHOLDER_0 = NewText('\uEE30')
COLOR_PLACEHOLDER_1 = NewText('\uEE31')
COLOR_PLACEHOLDER_2 = NewText('\uEE32')
COLOR_PLACEHOLDER_3 = NewText('\uEE33')
COLOR_PLACEHOLDER_4 = NewText('\uEE34')
COLOR_PLACEHOLDER_5 = NewText('\uEE35')
COLOR_PLACEHOLDER_6 = NewText('\uEE36')
COLOR_PLACEHOLDER_7 = NewText('\uEE37')
COLOR_PLACEHOLDER_8 = NewText('\uEE38')
COLOR_PLACEHOLDER_9 = NewText('\uEE39')

COLOR_PLACEHOLDERS = [
    COLOR_PLACEHOLDER_0,
    COLOR_PLACEHOLDER_1,
    COLOR_PLACEHOLDER_2,
    COLOR_PLACEHOLDER_3,
    COLOR_PLACEHOLDER_4,
    COLOR_PLACEHOLDER_5,
    COLOR_PLACEHOLDER_6,
    COLOR_PLACEHOLDER_7,
    COLOR_PLACEHOLDER_8,
    COLOR_PLACEHOLDER_9,
]

class Language(Enum):
    ENGLISH = 'English'
    FRENCH = 'Français'
    GERMAN = 'Deutsch'
    JAPANESE = '日本語'

    # reads each of the game's messages into a list of Message objects
    def read_messages(self, rom, fffc_rom):
        if self == Language.ENGLISH:
            if rom.pal:
                raise ValueError('English text must be read from the NTSC rom')
            table_offset = ENG_TABLE_START
        elif self in (Language.FRENCH, Language.GERMAN):
            if not rom.pal:
                raise ValueError('French or German text must be read from the PAL rom')
            table_offset = PAL_ENG_TABLE_START
        elif self == Language.JAPANESE:
            if rom.pal:
                raise ValueError('Japanese text must be read from the NTSC rom')
            table_offset = JPN_TABLE_START
        else:
            raise NotImplementedError(f'Unimplemented language: {self}')
        index = 0
        messages = []
        while True:
            entry = rom.read_bytes(table_offset, 8)
            id = bytes_to_int(entry[0:2])

            if id == 0xFFFD:
                table_offset += 8
                continue # this is only here to give an ending offset
            if id == 0xFFFF:
                break # this marks the end of the table

            messages.append(NewMessage.from_rom(rom, index, self))

            index += 1
            table_offset += 8

        # Also grab 0xFFFC entry from JP table.
        messages.append(read_fffc_message(fffc_rom))
        return messages


# A full entry in the message table. Stored in an encoding dependent on the language setting.
class NewMessage:
    def __init__(self, raw_text, index, id, opts, offset, length, language):
        self.raw_text = raw_text
        self.language = language

        self.index = index
        self.id = id
        self.opts = opts  # Textbox type and y position
        self.box_type = (self.opts & 0xF0) >> 4
        self.position = (self.opts & 0x0F)
        self.offset = offset
        self.length = length

    # read a single message from rom
    @classmethod
    def from_rom(cls, rom, index, language):
        if language == Language.ENGLISH:
            table_start = ENG_TABLE_START
            offset_table_start = None
            text_start = ENG_TEXT_START
        elif language == Language.FRENCH:
            table_start = PAL_ENG_TABLE_START
            offset_table_start = FRENCH_TABLE_START
            text_start = FRENCH_TEXT_START
        elif language == Language.GERMAN:
            table_start = PAL_ENG_TABLE_START
            offset_table_start = GERMAN_TABLE_START
            text_start = GERMAN_TEXT_START
        elif language == Language.JAPANESE:
            table_start = JPN_TABLE_START
            offset_table_start = None
            text_start = JPN_TEXT_START
        entry_offset = table_start + 8 * index
        entry = rom.read_bytes(entry_offset, 8)
        next = rom.read_bytes(entry_offset + 8, 8)
        if offset_table_start is not None:
            entry[4:] = rom.read_bytes(offset_table_start + 4 * index, 4)
            next[4:] = rom.read_bytes(offset_table_start + 4 * (index + 1), 4)

        id = bytes_to_int(entry[0:2])
        opts = entry[2]
        offset = bytes_to_int(entry[5:8])
        length = bytes_to_int(next[5:8]) - offset

        raw_text = rom.read_bytes(text_start + offset, length)

        return cls(raw_text, index, id, opts, offset, length, language)

    # The text of this message, represented as Unicode, with control codes in the Private Use Area range U+EE00-EFFF,
    # and potentially characters from transcoding from MacJapanese in the PUA range U+F800-F89F.
    # This property is a view of the `raw_text` attribute, which stores the text in the ingame representation depending on `language` attribute.
    @property
    def text(self):
        text = NewText()
        index = 0
        found_end = False
        if self.language == Language.JAPANESE:
            while len(self.raw_text) > index:
                next_byte = self.raw_text[index]
                index += 1
                if next_byte == 0x00:
                    continuation_byte = self.raw_text[index]
                    index += 1
                    if continuation_byte == 0x0A:
                        text += NewText('\n')
                    elif continuation_byte == 0x0B:
                        color = bytes_to_int(self.raw_text[index:index + 2])
                        index += 2
                        text += COLOR(color) #TODO decode color for consistency with international
                    else:
                        raise ValueError('Unexpected byte sequence in Japanese text data')
                if next_byte == 0x81:
                    continuation_byte = self.raw_text[index]
                    index += 1
                    if continuation_byte == 0x70:
                        found_end = True
                        break
                    elif continuation_byte == 0x89:
                        text += INSTANT
                    elif continuation_byte == 0x8A:
                        text += UN_INSTANT
                    elif continuation_byte == 0x99:
                        text += UNSKIPPABLE
                    elif continuation_byte == 0x9A:
                        if self.raw_text[index] != 0x00:
                            raise ValueError('Expected zero byte after this control character')
                        icon = self.raw_text[index + 1]
                        index += 2
                        text += ICON(icon)
                    elif continuation_byte == 0x9E:
                        if self.raw_text[index] != 0x00:
                            raise ValueError('Expected zero byte after this control character')
                        frames = self.raw_text[index + 1]
                        index += 2
                        text += FADE_AFTER(frames)
                    elif continuation_byte == 0x9F:
                        text += EVENT
                    elif continuation_byte == 0xA1:
                        text += TIME_OF_DAY
                    elif continuation_byte == 0xA3:
                        if self.raw_text[index] != 0x00:
                            raise ValueError('Expected zero byte after this control character')
                        frames = self.raw_text[index + 1]
                        index += 2
                        text += BOX_BREAK_AFTER(frames)
                    elif continuation_byte == 0xA5:
                        text += BOX_BREAK
                    elif continuation_byte == 0xB8:
                        text += THREE_CHOICE
                    elif continuation_byte == 0xBC:
                        text += TWO_CHOICE
                    elif continuation_byte == 0xCB:
                        next_id = bytes_to_int(self.raw_text[index:index + 2])
                        index += 2
                        text += GO_TO(next_id)
                    elif continuation_byte == 0xF0:
                        text += OCARINA
                    elif continuation_byte == 0xF3:
                        sound = bytes_to_int(self.raw_text[index:index + 2])
                        index += 2
                        text += SOUND_EFFECT(sound)
                    else:
                        text += MAC_JAPANESE_DOUBLE[bytes_to_int([next_byte, continuation_byte])]
                elif next_byte == 0x83:
                    continuation_byte = self.raw_text[index]
                    index += 1
                    if continuation_byte == 0x9F:
                        text += BUTTON_A
                    elif continuation_byte == 0xA0:
                        text += BUTTON_B
                    elif continuation_byte == 0xA1:
                        text += BUTTON_C
                    elif continuation_byte == 0xA2:
                        text += BUTTON_L
                    elif continuation_byte == 0xA3:
                        text += BUTTON_R
                    elif continuation_byte == 0xA4:
                        text += BUTTON_Z
                    elif continuation_byte == 0xA5:
                        text += BUTTON_C_UP
                    elif continuation_byte == 0xA6:
                        text += BUTTON_C_DOWN
                    elif continuation_byte == 0xA7:
                        text += BUTTON_C_LEFT
                    elif continuation_byte == 0xA8:
                        text += BUTTON_C_RIGHT
                    elif continuation_byte == 0xA9:
                        text += TRIANGLE
                    elif continuation_byte == 0xAA:
                        text += CONTROL_STICK
                    else:
                        text += MAC_JAPANESE_DOUBLE[bytes_to_int([next_byte, continuation_byte])]
                elif next_byte == 0x86:
                    continuation_byte = self.raw_text[index]
                    index += 1
                    if continuation_byte == 0x9F:
                        if self.raw_text[index] != 0x00:
                            raise ValueError('Expected zero byte after this control character')
                        score_kind = self.raw_text[index + 1]
                        index += 2
                        text += HIGH_SCORE(score_kind)
                    elif continuation_byte == 0xA3:
                        text += SKULLTULA_COUNT
                    elif continuation_byte == 0xA4:
                        text += FISH_WEIGHT
                    elif continuation_byte == 0xB3:
                        if self.raw_text[index] != 0x00:
                            raise ValueError('Expected zero byte after this control character')
                        background = bytes_to_int(self.raw_text[index + 1:index + 4])
                        index += 4
                        text += BACKGROUND(background)
                    elif continuation_byte == 0xC7:
                        if self.raw_text[index] != 0x00:
                            raise ValueError('Expected zero byte after this control character')
                        pixels = self.raw_text[index + 1]
                        index += 2
                        text += GAP(pixels)
                    elif continuation_byte == 0xC8:
                        text += KEEP_OPEN
                    elif continuation_byte == 0xC9:
                        if self.raw_text[index] != 0x00:
                            raise ValueError('Expected zero byte after this control character')
                        frames = self.raw_text[index + 1]
                        index += 2
                        text += CHARACTER_DELAY(frames)
                    else:
                        text += MAC_JAPANESE_DOUBLE[bytes_to_int([next_byte, continuation_byte])]
                elif next_byte == 0x87:
                    continuation_byte = self.raw_text[index]
                    index += 1
                    if continuation_byte == 0x4F:
                        text += PLAYER_NAME
                    elif continuation_byte == 0x91:
                        text += MARATHON_TIME
                    elif continuation_byte == 0x92:
                        text += RACE_TIME
                    elif continuation_byte == 0x9B:
                        text += POINTS
                    else:
                        text += MAC_JAPANESE_DOUBLE[bytes_to_int([next_byte, continuation_byte])]
                elif next_byte in MAC_JAPANESE_SINGLE:
                    text += MAC_JAPANESE_SINGLE[next_byte]
                else:
                    continuation_byte = self.raw_text[index]
                    index += 1
                    text += MAC_JAPANESE_DOUBLE[bytes_to_int([next_byte, continuation_byte])]
        else: # non-Japanese text
            while len(self.raw_text) > index:
                next_byte = self.raw_text[index]
                index += 1
                if next_byte == 0x01:
                    text += NewText('\n')
                elif next_byte == 0x02:
                    found_end = True
                    break
                elif next_byte == 0x04:
                    text += BOX_BREAK
                elif next_byte == 0x05:
                    color = INTL_REVERSE_COLOR_MAP[self.raw_text[index]]
                    index += 1
                    text += COLOR(color)
                elif next_byte == 0x06:
                    pixels = self.raw_text[index]
                    index += 1
                    text += GAP(pixels)
                elif next_byte == 0x07:
                    next_id = bytes_to_int(self.raw_text[index:index + 2])
                    index += 2
                    text += GO_TO(next_id)
                elif next_byte == 0x08:
                    text += INSTANT
                elif next_byte == 0x09:
                    text += UN_INSTANT
                elif next_byte == 0x0A:
                    text += KEEP_OPEN
                elif next_byte == 0x0B:
                    text += EVENT
                elif next_byte == 0x0C:
                    frames = self.raw_text[index]
                    index += 1
                    text += BOX_BREAK_AFTER(frames)
                elif next_byte == 0x0E:
                    frames = self.raw_text[index]
                    index += 1
                    text += FADE_AFTER(frames)
                elif next_byte == 0x0F:
                    text += PLAYER_NAME
                elif next_byte == 0x10:
                    text += OCARINA
                elif next_byte == 0x12:
                    sound = bytes_to_int(self.raw_text[index:index + 2])
                    index += 2
                    text += SOUND_EFFECT(sound)
                elif next_byte == 0x13:
                    icon = self.raw_text[index]
                    index += 1
                    text += ICON(icon)
                elif next_byte == 0x14:
                    frames = self.raw_text[index]
                    index += 1
                    text += CHARACTER_DELAY(frames)
                elif next_byte == 0x15:
                    background = bytes_to_int(self.raw_text[index:index + 3])
                    index += 3
                    text += BACKGROUND(background)
                elif next_byte == 0x16:
                    text += MARATHON_TIME
                elif next_byte == 0x17:
                    text += RACE_TIME
                elif next_byte == 0x18:
                    text += POINTS
                elif next_byte == 0x19:
                    text += SKULLTULA_COUNT
                elif next_byte == 0x1A:
                    text += UNSKIPPABLE
                elif next_byte == 0x1B:
                    text += TWO_CHOICE
                elif next_byte == 0x1C:
                    text += THREE_CHOICE
                elif next_byte == 0x1D:
                    text += FISH_WEIGHT
                elif next_byte == 0x1E:
                    score_kind = self.raw_text[index]
                    index += 1
                    text += HIGH_SCORE(score_kind)
                elif next_byte == 0x1F:
                    text += TIME_OF_DAY
                elif 0x20 <= next_byte <= 0x7D:
                    text += NewText(chr(next_byte))
                elif next_byte == 0x81:
                    text += NewText('î')
                elif next_byte == 0x83:
                    text += NewText('Ä')
                elif next_byte == 0x8A:
                    text += NewText('Ô')
                elif next_byte == 0x8B:
                    text += NewText('Ö')
                elif next_byte == 0x8E:
                    text += NewText('Ü')
                elif next_byte == 0x8F:
                    text += NewText('ß')
                elif next_byte == 0x90:
                    text += NewText('à')
                elif next_byte == 0x92:
                    text += NewText('â')
                elif next_byte == 0x93:
                    text += NewText('ä')
                elif next_byte == 0x94:
                    text += NewText('ç')
                elif next_byte == 0x95:
                    text += NewText('è')
                elif next_byte == 0x96:
                    text += NewText('é')
                elif next_byte == 0x97:
                    text += NewText('ê')
                elif next_byte == 0x99:
                    text += NewText('ï')
                elif next_byte == 0x9A:
                    text += NewText('ô')
                elif next_byte == 0x9B:
                    text += NewText('ö')
                elif next_byte == 0x9C:
                    text += NewText('ù')
                elif next_byte == 0x9D:
                    text += NewText('û')
                elif next_byte == 0x9E:
                    text += NewText('ü')
                elif next_byte == 0x9F:
                    text += BUTTON_A
                elif next_byte == 0xA0:
                    text += BUTTON_B
                elif next_byte == 0xA1:
                    text += BUTTON_C
                elif next_byte == 0xA2:
                    text += BUTTON_L
                elif next_byte == 0xA3:
                    text += BUTTON_R
                elif next_byte == 0xA4:
                    text += BUTTON_Z
                elif next_byte == 0xA5:
                    text += BUTTON_C_UP
                elif next_byte == 0xA6:
                    text += BUTTON_C_DOWN
                elif next_byte == 0xA7:
                    text += BUTTON_C_LEFT
                elif next_byte == 0xA8:
                    text += BUTTON_C_RIGHT
                elif next_byte == 0xA9:
                    text += TRIANGLE
                elif next_byte == 0xAA:
                    text += CONTROL_STICK
                else:
                    raise ValueError('Unexpected byte in international text data')
        if not found_end:
            raise ValueError('Missing end of text indicator')
        return text


    # Replaces the text with the value given in the Unicode representation.
    # This property is a view of the `raw_text` attribute, which stores the text in the ingame representation depending on `language` attribute.
    # This method also performs line wrapping.
    @text.setter
    def text(self, value):
        if not isinstance(value, NewText):
            raise TypeError()
        #TODO line wrapping
        text = value.text
        if any(color_placeholder in text for color_placeholder in COLOR_PLACEHOLDERS):
            raise ValueError('Tried to encode text with color placeholder')
        raw_text = b''
        if self.language == Language.JAPANESE:
            while text:
                if text[0] == '\n':
                    raw_text += b'\x00\x0A'
                    text = text[1:]
                elif '\uEE00' <= text[0] <= '\uEFFF':
                    code = text[0]
                    text = text[1:]
                    if code == '\uEE00': # COLOR
                        raise NotImplementedError() #TODO support COLOR control sequence (00 0B xx xx)
                    elif code == BOX_BREAK.text:
                        raw_text += b'\x81\xA5'
                    elif code == GAP.code:
                        raw_text += bytes([0x86, 0xC7, 0x00, ord(text[0]) - 0xEF00])
                        text = text[1:]
                    elif code == GO_TO.code:
                        raw_text += bytes([0x81, 0xCB, ord(text[0]) - 0xEF00, ord(text[1]) - 0xEF00])
                        text = text[2:]
                    elif code == INSTANT.text:
                        raw_text += b'\x81\x89'
                    elif code == UN_INSTANT.text:
                        raw_text += b'\x81\x8A'
                    elif code == KEEP_OPEN.text:
                        raw_text += b'\x86\xC8'
                    elif code == EVENT.text:
                        raw_text += b'\x81\x9F'
                    elif code == BOX_BREAK_AFTER.code:
                        raw_text += bytes([0x81, 0xA3, 0x00, ord(text[0]) - 0xEF00])
                        text = text[1:]
                    elif code == FADE_AFTER.code:
                        raw_text += bytes([0x81, 0x9E, 0x00, ord(text[0]) - 0xEF00])
                        text = text[1:]
                    elif code == PLAYER_NAME.text:
                        raw_text += b'\x87\x4F'
                    elif code == OCARINA.text:
                        raw_text += b'\x81\xF0'
                    elif code == SOUND_EFFECT.code:
                        raw_text += bytes([0x81, 0xF3, ord(text[0]) - 0xEF00, ord(text[1]) - 0xEF00])
                        text = text[2:]
                    elif code == ICON.code:
                        raw_text += bytes([0x81, 0x9A, 0x00, ord(text[0]) - 0xEF00])
                        text = text[1:]
                    elif code == CHARACTER_DELAY.code:
                        raw_text += bytes([0x86, 0xC9, 0x00, ord(text[0]) - 0xEF00])
                        text = text[1:]
                    elif code == BACKGROUND.code:
                        raw_text += bytes([0x86, 0xB3, 0x00, ord(text[0]) - 0xEF00, ord(text[1]) - 0xEF00, ord(text[2]) - 0xEF00])
                        text = text[3:]
                    elif code == MARATHON_TIME.text:
                        raw_text += b'\x87\x91'
                    elif code == RACE_TIME.text:
                        raw_text += b'\x87\x92'
                    elif code == POINTS.text:
                        raw_text += b'\x87\x9B'
                    elif code == SKULLTULA_COUNT.text:
                        raw_text += b'\x86\xA3'
                    elif code == UNSKIPPABLE.text:
                        raw_text += b'\x81\x99'
                    elif code == TWO_CHOICE.text:
                        raw_text += b'\x81\xBC'
                    elif code == THREE_CHOICE.text:
                        raw_text += b'\x81\xB8'
                    elif code == FISH_WEIGHT.text:
                        raw_text += b'\x86\xA4'
                    elif code == HIGH_SCORE.code:
                        raw_text += bytes([0x86, 0x9F, 0x00, ord(text[0]) - 0xEF00])
                        text = text[1:]
                    elif code == TIME_OF_DAY.text:
                        raw_text += b'\x81\xA1'
                    elif code == BUTTON_A.text:
                        raw_text += b'\x83\x9F'
                    elif code == BUTTON_B.text:
                        raw_text += b'\x83\xA0'
                    elif code == BUTTON_C.text:
                        raw_text += b'\x83\xA1'
                    elif code == BUTTON_L.text:
                        raw_text += b'\x83\xA2'
                    elif code == BUTTON_R.text:
                        raw_text += b'\x83\xA3'
                    elif code == BUTTON_Z.text:
                        raw_text += b'\x83\xA4'
                    elif code == BUTTON_C_UP.text:
                        raw_text += b'\x83\xA5'
                    elif code == BUTTON_C_DOWN.text:
                        raw_text += b'\x83\xA6'
                    elif code == BUTTON_C_LEFT.text:
                        raw_text += b'\x83\xA7'
                    elif code == BUTTON_C_RIGHT.text:
                        raw_text += b'\x83\xA8'
                    elif code == TRIANGLE.text:
                        raw_text += b'\x83\xA9'
                    elif code == CONTROL_STICK.text:
                        raw_text += b'\x83\xAA'
                    else:
                        raise NotImplementedError('Unknown control code')
                else:
                    for prefix_len in range(len(text), 0, -1):
                        if text[:prefix_len] in MAC_JAPANESE_ENCODE:
                            raw_text += MAC_JAPANESE_ENCODE[text[:prefix_len]]
                            text = text[prefix_len:]
                            break
                    else:
                        raise ValueError('This text cannot be encoded in the Japanese text format')
            raw_text += b'\x81\x70'
        else:
            while text:
                next_char = text[0]
                text = text[1:]
                if next_char == '\n':
                    raw_text += b'\x01'
                elif next_char == BOX_BREAK.text:
                    raw_text += b'\x04'
                elif next_char == '\uEE00': # COLOR
                    raw_text += bytes([0x05, ord(text[0]) - 0xEF00])
                    text = text[1:]
                elif next_char == GAP.code:
                    raw_text += bytes([0x06, ord(text[0]) - 0xEF00])
                    text = text[1:]
                elif next_char == GO_TO.code:
                    raw_text += bytes([0x07, ord(text[0]) - 0xEF00, ord(text[1]) - 0xEF00])
                    text = text[2:]
                elif next_char == INSTANT.text:
                    raw_text += b'\x08'
                elif next_char == UN_INSTANT.text:
                    raw_text += b'\x09'
                elif next_char == KEEP_OPEN.text:
                    raw_text += b'\x0A'
                elif next_char == EVENT.text:
                    raw_text += b'\x0B'
                elif next_char == BOX_BREAK_AFTER.code:
                    raw_text += bytes([0x0C, ord(text[0]) - 0xEF00])
                    text = text[1:]
                elif next_char == FADE_AFTER.code:
                    raw_text += bytes([0x0E, ord(text[0]) - 0xEF00])
                    text = text[1:]
                elif next_char == PLAYER_NAME.text:
                    raw_text += b'\x0F'
                elif next_char == OCARINA.text:
                    raw_text += b'\x10'
                elif next_char == SOUND_EFFECT.code:
                    raw_text += bytes([0x12, ord(text[0]) - 0xEF00, ord(text[1]) - 0xEF00])
                    text = text[2:]
                elif next_char == ICON.code:
                    raw_text += bytes([0x13, ord(text[0]) - 0xEF00])
                    text = text[1:]
                elif next_char == CHARACTER_DELAY.code:
                    raw_text += bytes([0x14, ord(text[0]) - 0xEF00])
                    text = text[1:]
                elif next_char == BACKGROUND.code:
                    raw_text += bytes([0x15, ord(text[0]) - 0xEF00, ord(text[1]) - 0xEF00, ord(text[2]) - 0xEF00])
                    text = text[3:]
                elif next_char == MARATHON_TIME.text:
                    raw_text += b'\x16'
                elif next_char == RACE_TIME.text:
                    raw_text += b'\x17'
                elif next_char == POINTS.text:
                    raw_text += b'\x18'
                elif next_char == SKULLTULA_COUNT.text:
                    raw_text += b'\x19'
                elif next_char == UNSKIPPABLE.text:
                    raw_text += b'\x1A'
                elif next_char == TWO_CHOICE.text:
                    raw_text += b'\x1B'
                elif next_char == THREE_CHOICE.text:
                    raw_text += b'\x1C'
                elif next_char == FISH_WEIGHT.text:
                    raw_text += b'\x1D'
                elif next_char == HIGH_SCORE.code:
                    raw_text += bytes([0x1E, ord(text[0]) - 0xEF00])
                    text = text[1:]
                elif next_char == TIME_OF_DAY.text:
                    raw_text += b'\x1F'
                elif 0x20 <= ord(next_char) <= 0x7D:
                    raw_text += bytes([ord(next_char)])
                elif next_char == 'î':
                    raw_text += '\x81'
                elif next_char == 'Ä':
                    raw_text += '\x83'
                elif next_char == 'Ô':
                    raw_text += '\x8A'
                elif next_char == 'Ö':
                    raw_text += '\x8B'
                elif next_char == 'Ü':
                    raw_text += '\x8E'
                elif next_char == 'ß':
                    raw_text += '\x8F'
                elif next_char == 'à':
                    raw_text += '\x90'
                elif next_char == 'â':
                    raw_text += '\x92'
                elif next_char == 'ä':
                    raw_text += '\x93'
                elif next_char == 'ç':
                    raw_text += '\x94'
                elif next_char == 'è':
                    raw_text += '\x95'
                elif next_char == 'é':
                    raw_text += '\x96'
                elif next_char == 'ê':
                    raw_text += '\x97'
                elif next_char == 'ï':
                    raw_text += '\x99'
                elif next_char == 'ô':
                    raw_text += '\x9A'
                elif next_char == 'ö':
                    raw_text += '\x9B'
                elif next_char == 'ù':
                    raw_text += '\x9C'
                elif next_char == 'û':
                    raw_text += '\x9D'
                elif next_char == 'ü':
                    raw_text += '\x9E'
                elif next_char == BUTTON_A.text:
                    raw_text += '\x9F'
                elif next_char == BUTTON_B.text:
                    raw_text += '\xA0'
                elif next_char == BUTTON_C.text:
                    raw_text += '\xA1'
                elif next_char == BUTTON_L.text:
                    raw_text += '\xA2'
                elif next_char == BUTTON_R.text:
                    raw_text += '\xA3'
                elif next_char == BUTTON_Z.text:
                    raw_text += '\xA4'
                elif next_char == BUTTON_C_UP.text:
                    raw_text += '\xA5'
                elif next_char == BUTTON_C_DOWN.text:
                    raw_text += '\xA6'
                elif next_char == BUTTON_C_LEFT.text:
                    raw_text += '\xA7'
                elif next_char == BUTTON_C_RIGHT.text:
                    raw_text += '\xA8'
                elif next_char == TRIANGLE.text:
                    raw_text += '\xA9'
                elif next_char == CONTROL_STICK.text:
                    raw_text += '\xAA'
                else:
                    raise ValueError('This text cannot be encoded in the international text format')
            raw_text += b'\x02'
        self.raw_text = raw_text


    # check if this is an unused message that just contains it's own id as text
    def is_id_message(self):
        if self.id == 0xFFFC:
            return False
        text = self.text
        if len(text.text) != 4:
            return False
        if self.language == Language.JAPANESE:
            matches = lambda c: '０' <= c <= '９' or 'Ａ' <= c <= 'Ｆ'
        else:
            matches = lambda c: '0' <= c <= '9' or 'A' <= c <= 'F'
        return all(map(matches, text.text))


# wrapper for adding a string message to a list of messages
def add_message(messages, text, id=0, opts=0x00):
    messages.append(NewMessage.from_string(text, id, opts))
    messages[-1].index = len(messages) - 1


# The JP text table is the only source for ID 0xFFFC, which is used by the
# title and file select screens. Preserve this table entry and text data when
# overwriting the JP data. The regular read_messages function only reads English
# data.
def read_fffc_message(rom):
    table_offset = JPN_TABLE_START
    index = 0
    while True:
        entry = rom.read_bytes(table_offset, 8)
        id = bytes_to_int(entry[0:2])

        if id == 0xFFFC:
            message = NewMessage.from_rom(rom, index, Language.JAPANESE)
            break

        index += 1
        table_offset += 8

    return message


# remove all messages that easy to tell are unused to create space in the message index table
def remove_unused_messages(messages):
    messages[:] = [m for m in messages if not m.is_id_message()]
    for index, m in enumerate(messages):
        m.index = index


# write the messages back
def repack_messages(rom, messages, permutation=None, always_allow_skip=True, speed_up_text=True):
    for message in messages:
        if not isinstance(message, NewMessage):
            raise TypeError()

    rom.update_dmadata_record(ENG_TEXT_START, ENG_TEXT_START, ENG_TEXT_START + ENG_TEXT_SIZE_LIMIT)
    rom.update_dmadata_record(JPN_TEXT_START, JPN_TEXT_START, JPN_TEXT_START + JPN_TEXT_SIZE_LIMIT)

    if permutation is None:
        permutation = range(len(messages))

    # repack messages
    offset = 0
    text_start = JPN_TEXT_START
    text_size_limit = EXTENDED_TEXT_SIZE_LIMIT
    text_bank = 0x08 # start with the Japanese text bank
    jp_bytes = 0
    # An extra dummy message is inserted after exhausting the JP text file.
    # Written message IDs are independent of the python list index, but the
    # index has to be maintained for old/new lookups. This wouldn't be an
    # issue if text shuffle didn't exist.
    jp_index_offset = 0

    for old_index, new_index in enumerate(permutation):
        old_message = messages[old_index]
        new_message = messages[new_index]
        remember_id = new_message.id
        new_message.id = old_message.id

        # modify message, making it represent how we want it to be written
        if new_message.id != 0xFFFC:
            new_message.transform(True, old_message.ending, always_allow_skip, speed_up_text)

        # check if there is space to write the message
        message_size = new_message.size()
        if message_size + offset > JPN_TEXT_SIZE_LIMIT and text_start == JPN_TEXT_START:
            # Add a dummy entry to the table for the last entry in the
            # JP file. This is used by the game to calculate message
            # length. Since the next entry in the English table has an
            # offset of zero, which would lead to a negative length.
            # 0xFFFD is used as the text ID for this in vanilla.
            # Text IDs need to be in order across the table for the
            # split to work.
            entry = bytes([0xFF, 0xFD, 0x00, 0x00, text_bank]) + int_to_bytes(offset, 3)
            entry_offset = EXTENDED_TABLE_START + 8 * old_index
            rom.write_bytes(entry_offset, entry)
            # if there is no room then switch to the English text bank
            text_bank = 0x07
            text_start = ENG_TEXT_START
            jp_bytes = offset
            jp_index_offset = 1
            offset = 0

        # Special handling for text ID 0xFFFC, which has hard-coded offsets to
        # the JP file in function Font_LoadOrderedFont in z_kanfont.c
        if new_message.id == 0xFFFC:
            # hard-coded offset including segment
            rom.write_int16(0xAD1CE2, (text_bank << 8) + ((offset & 0xFFFF0000) >> 16) + (1 if offset & 0xFFFF > 0x8000 else 0))
            rom.write_int16(0xAD1CE6, offset & 0XFFFF)
            # hard-coded message length, represented by offset of end of message
            rom.write_int16(0xAD1D16, (text_bank << 8) + (((offset + new_message.size()) & 0xFFFF0000) >> 16) + (1 if (offset + new_message.size()) & 0xFFFF > 0x8000 else 0))
            rom.write_int16(0xAD1D1E, (offset + new_message.size()) & 0XFFFF)
            # hard-coded segment, default JP file (0x08)
            rom.write_int16(0xAD1D12, (text_bank << 8))
            # hard-coded text file start address in rom, default JP
            rom.write_int16(0xAD1D22, ((text_start & 0xFFFF0000) >> 16) + (1 if text_start & 0xFFFF > 0x8000 else 0))
            rom.write_int16(0xAD1D2E, text_start & 0XFFFF)

        # actually write the message
        offset = new_message.write(rom, old_index + jp_index_offset, text_start, offset, text_bank)

        new_message.id = remember_id

    # raise an exception if too much is written
    # we raise it at the end so that we know how much overflow there is
    if jp_bytes + offset > text_size_limit:
        raise(TypeError("Message Text table is too large: 0x" + "{:x}".format(jp_bytes + offset) + " written / 0x" + "{:x}".format(EXTENDED_TEXT_SIZE_LIMIT) + " allowed."))

    # end the table, accounting for additional entry for file split
    table_index = len(messages) + (1 if text_bank == 0x07 else 0)
    entry = bytes([0xFF, 0xFD, 0x00, 0x00, text_bank]) + int_to_bytes(offset, 3)
    entry_offset = EXTENDED_TABLE_START + 8 * table_index
    rom.write_bytes(entry_offset, entry)
    table_index += 1
    entry_offset = EXTENDED_TABLE_START + 8 * table_index
    if 8 * (table_index + 1) > EXTENDED_TABLE_SIZE:
        raise(TypeError("Message ID table is too large: 0x" + "{:x}".format(8 * (table_index + 1)) + " written / 0x" + "{:x}".format(EXTENDED_TABLE_SIZE) + " allowed."))
    rom.write_bytes(entry_offset, [0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])


# wrapper for updating the text of a message, given its message id
# if the id does not exist in the list, then it will add it
def update_message_by_id(messages, id, text, opts=None):
    # get the message index
    index = next((m.index for m in messages if m.id == id), -1)
    # update if it was found
    if index >= 0:
        update_message_by_index(messages, index, text, opts)
    else:
        add_message(messages, text, id, opts)


# wrapper for updating the text of a message, given its index in the list
def update_message_by_index(messages, index, text, opts=None):
    messages[index].text = text
    if opts is not None:
        messages[index].opts = opts

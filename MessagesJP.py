import os
import random
import logging
TEXT_START = 0x8EB000
ENG_TEXT_SIZE_LIMIT = 0x39000
JPN_TEXT_SIZE_LIMIT = 0x3A150

JPN_TABLE_START = 0xB808AC
ENG_TABLE_START = 0xB849EC
CREDITS_TABLE_START = 0xB88C0C

JPN_TABLE_SIZE = ENG_TABLE_START - JPN_TABLE_START
ENG_TABLE_SIZE = CREDITS_TABLE_START - ENG_TABLE_START

EXTENDED_TABLE_START = JPN_TABLE_START # start writing entries to the jp table instead of english for more space
EXTENDED_TABLE_SIZE = JPN_TABLE_SIZE + ENG_TABLE_SIZE # 0x8360 bytes, 4204 entries

CONTROL_CHARS_JP = {
   'LINE_BREAK':   ['&', '\x00\x0A', "\x01"],
   'BOX_BREAK':    ['^', '▼', "\x04"],
   'COLOR':        ['#', '\x00\x0B\x0C', "\x05"],
   'ENDMARK':      ['|', '｝', "\x02"],
   'ICON':         ['~', '★\x00', "\x13"],
   'INSTANTSTART': ['<', '♂', "\x08"],
   'INSTANTEND':   ['>', '♀', "\x09"],
   'SOUND':        ['$', '♭', "\x12"],
   'DELAY_BOX':    ['[', '▲\x00', "\x0C"],
   'PREVENT':      [']', '☆', "\x1A"],
   'EVENT':        ['{', '◆', "\x0B"],
   'PRINT_T':      ['@T', '■', "\x1F"],
   'THREE_C':      [':3', '∈', "\x1C"],
   'TWO_C':        [':2', '⊂', "\x1B"],
   'GO_MESSAGE':   ['}', '⇒', "\x07"],
   'FADE_OUT':     ['*F', '◇\x00', "\x0E"],
}

CONTROL_CHARS_JP_1 = {
   'LINE_BREAK':   ['&&', '\x00\x0A', "\x01"],
   'BOX_BREAK':    ['^^', '▼', "\x04"],
   'COLOR':        ['##', '\x00\x0B\x0C', "\x05"],
   'ENDMARK':      ['||', '｝', "\x02"],
   'ICON':         ['~~', '★\x00', "\x13"],
   'INSTANTSTART': ['<<', '♂', "\x08"],
   'INSTANTEND':   ['>>', '♀', "\x09"],
   'SOUND':        ['$$', '♭', "\x12"],
   'DELAY_BOX':    ['[[', '▲\x00', "\x0C"],
   'PREVENT':      [']]', '☆', "\x1A"],
   'EVENT':        ['{{', '◆', "\x0B"],
   'PRINT_T':      ['@T', '■', "\x1F"],
   'THREE_C':      [':3', '∈', "\x1C"],
   'TWO_C':        [':2', '⊂', "\x1B"],
   'GO_MESSAGE':   ['}}', '⇒', "\x07"],
   'FADE_OUT':     ['*F', '◇\x00', "\x0E"],
}

IGNORE_CHARS = {
    'NAME':         [r'\x40\x4e', r'\x87\x4f', '@N', "\x0F"],
    'PRINT_M':      [r'\x40\x4d', r'\x87\x91', '@M', "\x16"],
    'PRINT_R':      [r'\x40\x52', r'\x87\x92', '@R', "\x17"],
    'PRINT_G':      [r'\x40\x47', r'\x86\xa3', '@G', "\x19"],
    'PRINT_P':      [r'\x40\x50', r'\x87\x9b', '@P', "\x18"],
    'PRINT_H':      [r'\x40\x48', r'\x86\x9f\x00', '@H', "\x1E"],
    'PRINT_L':      [r'\x40\x4c', r'\x86\xa4', '@L', "\x1D"],
    'SETBACK':      [r'\x40\x42', r'\x86\xb3\x00', '@B', "\x15"],
    'SETSPEED':     [r'\x2b\x53', r'\x86\xc9\x00', '+S', "\x14"],
    'SHIFT_TEXT':   [r'\x2b\x54', r'\x86\xc7\x00', '+T', "\x06"],
    'OCARINA':      [r'\x3a\x4f', r'\x81\xf0', ':O', "\x10"],
    'KEEP_OPEN':    [r'\x2a\x4f', r'\x86\xc8', '*O', "\x0A"],
}

IGNORE_CHARS_1 = {
    'NAME':         [r'\x40\x4e', r'\x87\x4f', '@N', "\x0F"],
    'PRINT_M':      [r'\x40\x4d', r'\x87\x91', '@M', "\x16"],
    'PRINT_R':      [r'\x40\x52', r'\x87\x92', '@R', "\x17"],
    'PRINT_G':      [r'\x40\x47', r'\x86\xa3', '@G', "\x19"],
    'PRINT_P':      [r'\x40\x50', r'\x87\x9b', '@P', "\x18"],
    'PRINT_H':      [r'\x40\x48', r'\x86\x9f\x00', '@H', "\x1E"],
    'PRINT_L':      [r'\x40\x4c', r'\x86\xa4', '@L', "\x1D"],
    'SETBACK':      [r'\x40\x42', r'\x86\xb3\x00', '@B', "\x15"],
    'SETSPEED':     [r'\x2b\x53', r'\x86\xc9\x00', '+S', "\x14"],
    'SHIFT_TEXT':   [r'\x2b\x54', r'\x86\xc7\x00', '+T', "\x06"],
    'OCARINA':      [r'\x3a\x4f', r'\x81\xf0', ':O', "\x10"],
    'KEEP_OPEN':    [r'\x2a\x4f', r'\x86\xc8', '*O', "\x0A"],
    'AKINDO':       [r'\x81\xf3', r'\x81\xf3\x38\x82', '$', "AKINDO"],
}

def parsejp(text, mode = 0):
    tag = ""
    ending = "None"
    if (r"\x81\xcb" in text) is True:
        tag += "g"
        ending = "goto"
    if (r"\x86\xc8" in text) is True:
        tag += "k"
        ending = "keep_open"
    if (r"\x81\x9f" in text) is True:
        tag += "e"
        ending = "event"
    if (r"\x81\x9e" in text) is True:
        tag += "f"
        ending = "fade"
    if (r"\x81\xf0" in text) is True:
        tag += "o"
        ending = "ocarina"
    if (r"\x81\xbc" in text) is True:
        tag += "2"
    if (r"\x81\xb8" in text) is True:
        tag += "3"

    if mode == 0:
        return tag
    if mode == 1:
        return ending

# convert byte array to an integer
def bytes_to_int(bytes, signed=False):
    return int.from_bytes(bytes, byteorder='big', signed=signed)


# convert int to an array of bytes of the given width
def int_to_bytes(num, width, signed=False):
    return int.to_bytes(num, width, byteorder='big', signed=signed)

# convert int to an array of bytes of the given width
def text_to_bytes(text, width, signed=False):
    text = text.replace(r"\x" or r"0x", r"")
    num = int(text, 16)
    return int.to_bytes(num, width, byteorder='big', signed=signed)

# mode: 0 normal, 1 scrub, 2 item
def JPencode(text, mode = 0, replace_chars=True):
    rawtext = text
    if replace_chars:
        if mode == 0:
            for char in CONTROL_CHARS_JP.values():
                text = text.replace(char[0],char[1])
        elif mode == 1:
            for char in CONTROL_CHARS_JP.values():
                text = text.replace(char[0],char[1])
        elif mode == 2:
            for char in CONTROL_CHARS_JP_1.values():
                text = text.replace(char[0],char[1])
    jp_text = (''.join([r'\x{:02x}'.format(x) for x in text.encode('cp932')]))
    if mode == 0:
        for char in IGNORE_CHARS.values():
            jp_text = jp_text.replace(char[0],char[1])
    elif mode == 1:
        for char in IGNORE_CHARS_1.values():
            jp_text = jp_text.replace(char[0],char[1])
    elif mode == 2:
        for char in IGNORE_CHARS.values():
            jp_text = jp_text.replace(char[0],char[1])
    return (jp_text)

GOSSIP_STONE_MESSAGES = list( range(0x0401, 0x04FF) ) # ids of the actual hints
GOSSIP_STONE_MESSAGES += [0x2053, 0x2054] # shared initial stone messages
TEMPLE_HINTS_MESSAGES = [0x7057, 0x707A] # dungeon reward hints from the temple of time pedestal
LIGHT_ARROW_HINT = [0x70CC] # ganondorf's light arrow hint line
GS_TOKEN_MESSAGES = [0x00B4, 0x00B5] # Get Gold Skulltula Token messages
ERROR_MESSAGE = 0x0001

ITEM_MESSAGES = {
    0x0001: "<<+T\x30##\x01テキストエラー！##\x00",
    0x9001: "<<~~\x2D##\x01ポケットタマゴ##\x00をお借りした。",
    0x0002: "<<~~\x2Fてのりコッコをお返しして&&##\x01コジロー##\x00を入手！",
    0x0003: "<<~~\x30##\x01あやしいキノコ##\x00を入手。",
    0x0004: "<<~~\x31##\x01あやしいクスリ##\x00を入手！",
    0x0005: "<<~~\x32あやしいクスリを返して&&##\x01密猟者のノコギリ##\x00を入手！",
    0x0007: "<<~~\x48##\x01デクのタネブクロ##\x00だ！&&##\x06４０コ##\x00まで入れられる！",
    0x0008: "<<~~\x33密猟者のノコギリをわたして&&##\x01折れたゴロン刀##\x00を入手！",
    0x0009: "<<~~\x34折れたゴロン刀をあずけて&&##\x01処方せん##\x00を入手！",
    0x000A: "<<~~\x37剛剣ダイゴロン刀！！&&…の##\x01ひきかえ券##\x00を入手。",
    0x000B: "<<~~\x2E##\x01てのりコッコ##\x00を入手！",
    0x000C: "<<~~\x3D巨人のナイフと　交換で&&##\x01剛剣ダイゴロン刀##\x00を入手！",
    0x000D: "<<~~\x35処方せんを渡して&&##\x01メダマガエル##\x00を入手！",
    0x000E: "<<~~\x36メダマガエルを渡して&&##\x01特製本生目薬##\x00を入手！",
    0x0010: "<<~~\x25##\x01ドクロのお面##\x00を借りた！&&魔物の気分が味わえる。",
    0x0011: "<<~~\x26##\x01こわそなお面##\x00を借りた！&&いろんな人をおどかそう。",
    0x0012: "<<~~\x24##\x01キータンのお面##\x00を借りた！&&これでキミも人気者。",
    0x0013: "<<~~\x27##\x01ウサギずきん##\x00を借りた！&&長いお耳が魅力てき！",
    0x0014: "<<~~\x28##\x01ゴロンのお面##\x01を借りた！&&ちょっとカオがデカいです。",
    0x0015: "<<~~\x29##\x01ゾーラのお面##\x01を借りた！&&これでアナタも　ゾーラ族。",
    0x0016: "<<~~\x2A##\x01ゲルドのお面##\x01を借りた！&&これでアナタも　オネエさん？",
    0x0017: "<<~~\x2B##\x01まことの仮面##\x00を借りた！&&いろんな人に　見せてみよう。",
    0x0030: "<<~~\x06##\x01妖精のパチンコ##\x00を入手！",
    0x0031: "<<~~\x03##\x01妖精の弓##\x00を入手！",
    0x0032: "<<~~\x02##\x01バクダン##\x00を入手！",
    0x0033: "<<~~\x09##\x01ボムチュウ##\x00を入手！",
    0x0034: "<<~~\x01##\x01デクの実##\x00を入手！",
    0x0035: "<<~~\x0E##\x01ブーメラン##\x00を入手！",
    0x0036: "<<~~\x0A##\x01フックショット##\x00を入手！",
    0x0037: "<<~~\x00##\x01デクの棒##\x00を入手！",
    0x0038: "<<~~\x11##\x01メガトンハンマー##\x00を入手！&&威力はデカいが両手持ち！",
    0x0039: "<<~~\x0F##\x01まことのメガネ##\x00を入手！&&フシギな物が見えかくれ。",
    0x003A: "<<~~\x08##\x01時のオカリナ##\x00を入手！&&神秘的な光を放っている…",
    0x003C: "<<~~\x67##\x01炎のメダル##\x00を入手！&&ダルニアは　賢者として目覚め&&勇者に力が　宿った！",
    0x003D: "<<~~\x68##\x03水のメダル##\x00を入手！&&ルトは　賢者として目覚め&&勇者に力が　宿った！",
    0x003E: "<<~~\x66##\x02森のメダル##\x00を入手！&&サリアは　賢者として目覚め&&勇者に力が　宿った！",
    0x003F: "<<~~\x69##\x06魂のメダル##\x00を入手！&&ナボールは　賢者として目覚め&&勇者に力が　宿った！",
    0x0040: "<<~~\x6B##\x04光のメダル##\x00を入手！&&ラウルは　賢者として目覚め&&勇者に力が　宿った！",
    0x0041: "<<~~\x6A##\x05闇のメダル##\x00を入手！&&インパは　賢者として目覚め&&勇者に力が　宿った！",
    0x0042: "<<~~\x14##\x01あきビン##\x00を入手！&&なにかとべんり！",
    0x0043: "<<~~\x15##\x01赤いクスリ##\x00を入手！&&体力を回復するぞ！",
    0x0044: "<<~~\x16##\x02緑のクスリ##\x00を入手！&&魔力を回復するぞ！",
    0x0045: "<<~~\x17##\x03青いクスリ##\x00を入手！&&体力、魔力も全復活！",
    0x0046: "<<~~\x18##\x01妖精##\x00をビンにつめた！",
    0x0047: "<<~~\x19##\x01サカナ##\x00をビンにつめた！",
    0x0048: "<<~~\x10##\x01魔法のマメ\x00を入手！&&いい場所さがして　まこう！",
    0x9048: "<<~~\x10##\x01マメブクロ\x00を入手！&&いい場所さがして　まこう！",
    0x004A: "<<~~\x07##\x01妖精のオカリナ##\x00を入手！&&サリアとの思い出の品だ。",
    0x004B: "<<~~\x3D##\x02巨人のナイフ##\x00を入手！&&両手で持って斬る。&&##\x04盾##\x00と同時に使えない。",
    0x004C: "<<~~\x3E##\x04デクの盾##\x00を入手！",
    0x004D: "<<~~\x3F##\x04ハイリアの盾##\x00を入手！",
    0x004E: "<<~~\x40##\x04ミラーシールド##\x00を入手！&&鏡の盾は、光をはじく。",
    0x004F: "<<~~\x0B##\x01ロングフック##\x00を入手！&&長さが##\x01２倍##\x00になった！",
    0x0050: "<<~~\x42##\x01ゴロンの服##\x00を入手！",
    0x0051: "<<~~\x43##\x03ゾーラの服##\x00を入手！",
    0x0052: "<<##\x02魔法のツボ##\x00を入手！&&魔力が回復する！",
    0x0053: "<<~~\x45##\x01ヘビィブーツ##\x00を入手！",
    0x0054: "<<~~\x46##\x01ホバーブーツ##\x00を入手！",
    0x0055: "<<##\x05回復のハート##\x00を入手！&&体力が回復する！",
    0x0056: "<<~~\x4B##\x01大きな矢立て##\x00を入手！&&##\x06４０本##\x00も入る！",
    0x0057: "<<~~\x4C##\x01最大の矢立て##\x00を入手！&&##\x06５０本##\x00も入る！",
    0x0058: "<<~~\x4D##\x01ボム袋##\x00を入手！&&##\x01バクダン２０コ##\x00入り！",
    0x0059: "<<~~\x4E##\x01大きなボム袋##\x00を入手！&&##\x06３０コ##\x00も入る！",
    0x005A: "<<~~\x4F##\x01最大のボム袋##\x00を入手！&&##\x06４０コ##\x00も入る！",
    0x005B: "<<~~\x51##\x03銀のグローブ##\x00を入手！&&そうびすれば　力があふれる。",
    0x005C: "<<~~\x52##\x03金のグローブ##\x00を入手！&&両腕にさらに　力がみなぎる！",
    0x005D: "<<~~\x1C##\x04青い炎##\x00をビンにつめた！",
    0x005E: "<<~~\x56##\x03大人のサイフ##\x00を入手！&&##\x06２００ルピー##\x00まで持てるゾ！",
    0x005F: "<<~~\x57##\x03巨人のサイフ##\x00を入手！&&##\x06５００ルピー##\x00まで持てるゾ！",
    0x0060: "<<~~\x77##\x01小さなカギ##\x00を入手！&&カギ付ドアを開くカギ。&&ここでしか使えません。",
    0x0066: "<<~~\x76##\x01ダンジョン地図##\x00を入手！&&ここの地図のようだ。",
    0x0067: "<<~~\x75##\x01コンパス##\x00を入手！&&ここの物の場所が分かった！",
    0x0068: "<<~~\x6F##\x01もだえ石##\x00を入手！&&秘密がある場所で　ふるえるゾ。",
    0x0069: "<<~~\x23##\x01ゼルダの手紙##\x00を入手！&&ゼルダ姫直筆サイン入り！",
    0x006C: "<<~~\x49##\x01タネブクロ##\x00が大きくなった！&&##\x06５０コ##\x00まで入るぞ！",
    0x006F: "<<##\x02緑ルピー##\x00を入手！&&##\x02１ルピー##\x00だ。",
    0x0070: "<<~~\x04##\x01炎の矢##\x00を入手！&&命中すれば　火ダルマだ！！",
    0x0071: "<<~~\x0C##\x03氷の矢##\x00を入手！&&命中すれば　凍りつく！！",
    0x0072: "<<~~\x12##\x04光の矢##\x00を入手！&&聖なる光が　悪を射る！！",
    0x0073: "<<##\x02森のメヌエット##\x00をおぼえた！",
    0x0074: "<<##\x01炎のボレロ##\x00をおぼえた！",
    0x0075: "<<##\x03水のセレナーデ##\x00をおぼえた！",
    0x0076: "<<##\x06魂のレクイエム##\x00をおぼえた！",
    0x0077: "<<##\x05闇のノクターン##\x00をおぼえた！",
    0x0078: "<<##\x04光のプレリュード##\x00をおぼえた！",
    0x0079: "<<~~\x50##\x01ゴロンのうでわ##\x00を入手！&&バクダン花を引き抜ける。",
    0x007A: "<<~~\x1D##\x01ムシ##\x00をビンに入れた！&&小さな穴にもぐりこみます。",
    0x007B: "<<~~\x70##\x01ゲルドの会員証##\x00を入手！&&ゲルドの修練場に入れます。",
    0x0080: "<<~~\x6C##\x02コキリのヒスイ##\x00を入手！&&デクの樹サマから託された、&&森の精霊石。",
    0x0081: "<<~~\x6D##\x01ゴロンのルビー##\x00を入手！&&ゴロン族に伝わる、炎の精霊石。",
    0x0082: "<<~~\x6E##\x03ゾーラのサファイア##\x00を入手！&&ゾーラ族に伝わる、水の精霊石。",
    0x0090: "<<~~\x00##\x01デクの棒##\x00を##\x06２０本##\x00まで&&持てるようになった！",
    0x0091: "<<~~\x00##\x01デクの棒##\x00を##\x06３０本##\x00まで&&持てるようになった！",
    0x0097: "<<~~\x20##\x01ポウ##\x00をビンにつめた！",
    0x0098: "<<~~\x1A##\x01ロンロン牛乳##\x00をビンにつめた！&&２回飲めるゾ！",
    0x0099: "<<~~\x1B##\x01ルトの手紙##\x00を入手！",
    0x9099: "<<~~\x1Bなかの手紙を取り出して&&##\x01あきビン##\x00を入手！&&なにかとべんり！",
    0x009A: "<<~~\x21##\x01ふしぎなタマゴ##\x00を入手！",
    0x00A4: "<<~~\x3B##\x02コキリの剣##\x00を入手した！",
    0x00A7: "<<~~\x01##\x01デクの実##\x00を##\x06３０コ##\x00まで&持てるようになった！",
    0x00A8: "<<~~\x01##\x01デクの実##\x00を##\x06４０コ##\x00まで&持てるようになった！",
    0x00AD: "<<~~\x05##\x01ディンの炎##\x00を入手！",
    0x00AE: "<<~~\x0D##\x02フロルの風##\x00を入手！",
    0x00AF: "<<~~\x13##\x03ネールの愛##\x00を入手！",
    0x00B4: "<<##\x01スタルチュラトークン##\x00を入手！&&これで##\x01@Gコ##\x00だ！",
    0x00B5: "<<##\x01黄金のスタルチュラ##\x00を倒した！&&倒した「しるし」を入手！", ##Unused
    0x00C2: "<<~~\x73##\x01ハートの欠片##\x00を入手！&&４つで１つの器。",
    0x00C3: "<<~~\x73##\x01ハートの欠片##\x00を入手！&&これで２コ目。",
    0x00C4: "<<~~\x73##\x01ハートの欠片##\x00を入手！&&これで３コ目。",
    0x00C5: "<<~~\x73##\x01ハートの欠片##\x00を入手！&&かけら４コで器が完成！！",
    0x00C6: "<<~~\x72##\x01ハートの器##\x00を入手！&&ライフの上限１ＵＰ！",
    0x00C7: "<<~~\x74##\x01ボスキー##\x00を入手！&&ダンジョンのボスの部屋へ&&入れるようになった！",
    0x9002: "<<##\x01Ｙｏｕ　ａｒｅ　ａ　ＦＯＯＬ！##\x00",
    0x00CC: "<<##\x03青ルピー##\x00を入手！&&##\x03５ルピー##\x00だ。",
    0x00CD: "<<~~\x53##\x03銀のウロコ##\x00を入手！",
    0x00CE: "<<~~\x54##\x03金のウロコ##\x00を入手！",
    0x00D1: "<<##\x02サリアの歌##\x00をおぼえた！",
    0x00D2: "<<##\x01エポナの歌##\x00をおぼえた！",
    0x00D3: "<<##\x06太陽の歌##\x00をおぼえた！",
    0x00D4: "<<##\x03ゼルダの子守歌##\x00をおぼえた！",
    0x00D5: "<<##\x04時の歌##\x00をおぼえた！",
    0x00D6: "<<##\x05嵐の歌##\x00をおぼえた！",
    0x00DC: "<<~~\x58##\x01デクのタネ##\x00を入手！&&パチンコのタマに使えるゾ！",
    0x00DD: "<<秘技##\x01回転斬り##\x00をおぼえた！！",
    0x00E4: "<<##\x02魔力##\x00を入手！！",
    0x00E5: "<<##\x04防御力##\x00が強化された！",
    0x00E6: "<<##\x06矢の束##\x00を入手！",
    0x00E8: "<<魔力が強化された！&&これまでの　##\x01２倍の魔法##\x00が&&使えるようになった。",
    0x00E9: "<<防御力が強化された！&&敵から受けるダメージが&&今までの##\x01半分##\x00になった。",
    0x00F0: "<<##\x01赤ルピー##\x00を入手！&&##\x01２０ルピー##\x00だ。",
    0x00F1: "<<##\x05紫ルピー##\x00を入手！&&##\x05５０ルピー##\x00だ。",
    0x00F2: "<<##\x06金ルピー##\x00を入手！&&##\x06２００ルピー##\x00だ。",
    0x00F9: "<<~~\x1E##\x01ビッグポウ##\x00をビンにつめた！&&##\x01ゴーストショップ##\x00で　売ろう！",
    0x9003: "<<##\x01トライフォースの欠片##\x00を入手！",
}

KEYSANITY_MESSAGES = {
    0x001C: "~~\x74<<##\x01炎の神殿##\x00の##\x01ボスキー##\x00を&&入手！>>",
    0x0006: "~~\x74<<##\x02森の神殿##\x00の##\x01ボスキー##\x00を&&入手！>>",
    0x001D: "~~\x74<<##\x03水の神殿##\x00の##\x01ボスキー##\x00を&&入手！>>",
    0x001E: "~~\x74<<##\x06魂の神殿##\x00の##\x01ボスキー##\x00を&&入手！>>",
    0x002A: "~~\x74<<##\x05闇の神殿##\x00の##\x01ボスキー##\x00を&&入手！>>",
    0x0061: "~~\x74<<##\x01ガノン城##\x00の##\x01ボスキー##\x00を&&入手！>>",
    0x0062: "~~\x75<<##\x02デクの樹##\x00の##\x01コンパス##\x00を&&入手！>>",
    0x0063: "~~\x75<<##\x01ドドンゴ##\x00の##\x01コンパス##\x00を&&入手！>>",
    0x0064: "~~\x75<<##\x03ジャブジャブ##\x00の##\x01コンパス##\x00を&&入手！>>",
    0x0065: "~~\x75<<##\x02森の神殿##\x00の##\x01コンパス##\x00を&&入手！>>",
    0x007C: "~~\x75<<##\x01炎の神殿##\x00の##\x01コンパス##\x00を&&入手！>>",
    0x007D: "~~\x75<<##\x03水の神殿##\x00の##\x01コンパス##\x00を&&入手！>>",
    0x007E: "~~\x75<<##\x06魂の神殿##\x00の##\x01コンパス##\x00を&&入手！>>",
    0x007F: "~~\x75<<##\x05闇の神殿##\x00の##\x01コンパス##\x00を&&入手！>>",
    0x0087: "~~\x75<<##\x04氷の洞窟##\x00の##\x01コンパス##\x00を&&入手！>>",
    0x0088: "~~\x76<<##\x02デクの樹##\x00の##\x01地図##\x00を&&入手！>>",
    0x0089: "~~\x76<<##\x01ドドンゴ##\x00の##\x01地図##\x00を&&入手！>>",
    0x008A: "~~\x76<<##\x03ジャブジャブ##\x00の##\x01地図##\x00を&&入手！>>",
    0x008B: "~~\x76<<##\x02森の神殿##\x00の##\x01地図##\x00を&&入手！>>",
    0x008C: "~~\x76<<##\x01炎の神殿##\x00の##\x01地図##\x00を&&入手！>>",
    0x008E: "~~\x76<<##\x03水の神殿##\x00の##\x01地図##\x00を&&入手！>>",
    0x008F: "~~\x76<<##\x06魂の神殿##\x00の##\x01地図##\x00を&&入手！>>",
    0x0092: "~~\x76<<##\x04氷の洞窟##\x00の##\x01地図##\x00を&&入手！>>",
    0x0093: "~~\x77<<##\x02森の神殿##\x00の##\x01カギ##\x00を&&入手！>>",
    0x0094: "~~\x77<<##\x01炎の神殿##\x00の##\x01カギ##\x00を&&入手！>>",
    0x0095: "~~\x77<<##\x03水の神殿##\x00の##\x01カギ##\x00を&&入手！>>",
    0x009B: "~~\x77<<##\x05井戸の下##\x00の##\x01カギ##\x00を&&入手！>>",
    0x009F: "~~\x77<<##\x06修練場##\x00の##\x01カギ##\x00を&&入手！>>",
    0x00A0: "~~\x77<<##\x06盗賊団##\x00の##\x01カギ##\x00を&&入手！>>",
    0x00A1: "~~\x77<<##\x01ガノン城##\x00の##\x01カギ##\x00を&&入手！>>",
    0x00A2: "~~\x75<<##\x05井戸の下##\x00の##\x01コンパス##\x00を&&入手！>>",
    0x00A3: "~~\x76<<##\x05闇の神殿##\x00の##\x01地図##\x00を&&入手！>>",
    0x00A5: "~~\x76<<##\x05井戸の下##\x00の##\x01地図##\x00を&&入手！>>",
    0x00A6: "~~\x77<<##\x06魂の神殿##\x00の##\x01カギ##\x00を&&入手！>>",
    0x00A9: "~~\x77<<##\x05闇の神殿##\x00の##\x01カギ##\x00を&&入手！>>",
}

REGION_NAMES = {
    # Dungeons
    "デクの樹サマ":                   [['Deku Tree Lobby'], '\x02'],
    "ドドンゴの洞窟":                 [['Dodongos Cavern Beginning'], '\x01'],
    "ジャブジャブ様":                 [['Jabu Jabus Belly Beginning'], '\x03'],
    "森の神殿":                       [['Forest Temple Lobby'], '\x02'],
    "炎の神殿":                       [['Fire Temple Lower'], '\x01'],
    "水の神殿":                       [['Water Temple Lobby'], '\x03'],
    "魂の神殿":                       [['Spirit Temple Lobby'], '\x06'],
    "闇の神殿":                       [['Shadow Temple Entryway'], '\x05'],
    "井戸の下":                       [['Bottom of the Well'], '\x05'],
    "氷の洞窟":                       [['Ice Cavern Beginning'], '\x04'],
    "修練場":                         [['Gerudo Training Ground Lobby'], '\x06'],

    # Indoors
    "ミドの家":                       [['KF Midos House'], '\x04'],
    "サリアの家":                     [['KF Sarias House'], '\x04'],
    "双子の家":                       [['KF House of Twins'], '\x04'],
    "物知り兄弟の家":                 [['KF Know It All House'], '\x04'],
    "コキリの店":                     [['KF Kokiri Shop'], '\x04'],
    "みずうみ研究所":                 [['LH Lab'], '\x04'],
    "つりぼり":                       [['LH Fishing Hole'], '\x04'],
    "大工のテント":                   [['GV Carpenter Tent'], '\x04'],
    "兵士詰所":                       [['Market Guard House'], '\x04'],
    "お面屋":                         [['Market Mask Shop'], '\x04'],
    "ボウリング場":                   [['Market Bombchu Bowling'], '\x04'],
    "クスリ屋":                       [['Market Potion Shop', 'Kak Potion Shop Front', 'Kak Potion Shop Back'], '\x04'],
    "くじ屋":                         [['Market Treasure Chest Game'], '\x04'],
    "ボムチュウ屋":                   [['Market Bombchu Shop'], '\x04'],
    "ミドリの民家":                   [['Market Man in Green House'], '\x04'],
    "大工の家":                       [['Kak Carpenter Boss House'], '\x04'],
    "スタルチュラハウス":             [['Kak House of Skulltula'], '\x04'],
    "インパの家":                     [['Kak Impas House', 'Kak Impas House Back'], '\x04'],
    "フシギなクスリ屋":               [['Kak Odd Medicine Building'], '\x04'],
    "墓守りの小屋":                   [['Graveyard Dampes House'], '\x04'],
    "ゴロンの店":                     [['GC Shop'], '\x04'],
    "ゾーラの店":                     [['ZD Shop'], '\x04'],
    "タロンの家":                     [['LLR Talons House'], '\x04'],
    "馬小屋":                         [['LLR Stables'], '\x04'],
    "納屋":                           [['LLR Tower'], '\x04'],
    "バザー":                         [['Market Bazaar', 'Kak Bazaar'], '\x04'],
    "的当屋":                         [['Market Shooting Gallery', 'Kak Shooting Gallery'], '\x04'],
    "妖精の泉":                       [['Colossus Great Fairy Fountain', 'HC Great Fairy Fountain', 'OGC Great Fairy Fountain', 'DMC Great Fairy Fountain', 'DMT Great Fairy Fountain', 'ZF Great Fairy Fountain'], '\x04'],
    "@Nの家":                         [['KF Links House'], '\x04'],
    "時の神殿":                       [['Temple of Time'], '\x04'],
    "風車小屋":                       [['Kak Windmill'], '\x04'],

    # Overworld
    "コキリの森":                    [['Kokiri Forest'], '\x01'],
    "迷いの森の橋":                  [['LW Bridge From Forest', 'LW Bridge'], '\x02'],
    "迷いの森":                      [['Lost Woods', 'LW Beyond Mido', 'LW Forest Exit'], '\x02'],
    "ゴロンシティ":                  [['GC Woods Warp', 'GC Darunias Chamber', 'Goron City'], '\x01'],
    "ゾーラ川":                      [['Zora River', 'ZR Behind Waterfall', 'ZR Front'], '\x03'],
    "森の聖域":                      [['SFM Entryway'], '\x01'],
    "ハイラル平原":                  [['Hyrule Field'], '\x04'],
    "ハイリア湖畔":                  [['Lake Hylia'], '\x03'],
    "ゲルドの谷":                    [['Gerudo Valley', 'GV Fortress Side'], '\x06'],
    "城下町入口":                    [['Market Entrance'], '\x04'],
    "カカリコ村":                    [['Kakariko Village', 'Kak Behind Gate', 'Kak Impas Ledge'], '\x05'],
    "ロンロン牧場":                  [['Lon Lon Ranch'], '\x06'],
    "ゾーラの里":                    [['Zoras Domain', 'ZD Behind King Zora'], '\x03'],
    "ゲルドの砦":                    [['Gerudo Fortress', 'GF Outside Gate'], '\x01'],
    "幻影の砂漠":                    [['Wasteland Near Fortress', 'Wasteland Near Colossus'], '\x06'],
    "巨大邪神像":                    [['Desert Colossus'], '\x04'],
    "城下町":                        [['Market'], '\x04'],
    "ハイラル城":                    [['Castle Grounds'], '\x04'],
    "時の神殿入口":                  [['ToT Entrance'], '\x04'],
    "墓地":                          [['Graveyard'], '\x05'],
    "登山道":                        [['Death Mountain', 'Death Mountain Summit'], '\x01'],
    "火口":                          [['DMC Lower Local', 'DMC Lower Nearby', 'DMC Upper Local', 'DMC Upper Nearby'], '\x01'],
    "ゾーラの泉":                    [['Zoras Fountain'], '\x03'],

    # Grottos
    "王家の墓穴":                    [['Graveyard Royal Familys Tomb'], '\x04'],
    "ダンペイの墓穴":                [['Graveyard Dampes Grave'], '\x04'],
    "ウルフォス穴":                  [['SFM Wolfos Grotto'], '\x04'],
    "リーデッド穴":                  [['Kak Redead Grotto'], '\x04'],
    "アキンドナッツ":                [['GV Storms Grotto', 'Colossus Grotto', 'LLR Grotto', 'SFM Storms Grotto', 'HF Inside Fence Grotto', 'GC Grotto', 'DMC Hammer Grotto', 'LW Scrubs Grotto', 'LH Grotto', 'ZR Storms Grotto'], '\x04'],
    "テクタイト穴":                  [['HF Tektite Grotto'], '\x04'],
    "お面品評会":                    [['Deku Theater'], '\x04'],
    "穴":                            [['KF Storms Grotto', 'HF Near Market Grotto', 'HF Southeast Grotto', 'ZR Open Grotto', 'DMC Upper Grotto', 'Kak Open Grotto', 'DMT Storms Grotto', 'LW Near Shortcuts Grotto', 'HF Open Grotto'], '\x04'],
    "妖精の泉":                      [['SFM Fairy Grotto', 'HF Fairy Grotto', 'ZD Storms Grotto', 'GF Storms Grotto', 'ZR Fairy Grotto'], '\x04'],
    "オクタン穴":                    [['GV Octorok Grotto'], '\x04'],
    "スタルチュラ穴":                [['HF Near Kak Grotto', 'HC Storms Grotto'], '\x04'],
    "盾の出る墓穴":                  [['Graveyard Shield Grave'], '\x04'],
    "リーデッド墓穴":                [['Graveyard Heart Piece Grave'], '\x04'],
    "牛のいる穴":                    [['DMT Cow Grotto', 'HF Cow Grotto'], '\x04'],
}

MISC_MESSAGES = {
    0x507B: ("<<オレ、ほんとに　見たんだよ！^^<<とっくに　死んだはずの&&墓守りダンペイが##\x01お宝##\x00を持って&&自分の墓の中に消えてくのをサ…", None),
    0x502D: ("<<やるな　ニイチャン！&&オラの足に　ついてこれるとは&&イイ走りしてるじゃネェか、ヘヘヘ！", 0x00),
    0x503B: ("<<コッコ　つかまえてくれて&&ありがとう！^^<<おれいに　コレあげる！&&だいじに　使ってネ！{{", 0x00),
    0x3063: ("<<近くへ来て　足につかまりなさい。&&さあ、勇気を出して。　ホホ～ッ！", 0x00),
    0x4003: ("<<いっしょに　くるなら&&私に　つかまりなさい。",0x03),
    0x4004: ("<<いっしょに　くるなら&&私に　つかまりなさい。",0x00),
    0x0422: ("<<##\x01モーファの呪い##\x00が　解けた後、&&##\x01この岩##\x00をたたくと　ハイリア湖の&&水位が変わるらしい。", 0x23),
    0x401C: ("<<はやく、余の　かわいい　##\x01ルト姫##\x00を&&見つけ出してきてくれぃ…ゾラ！$$\x68\x7A", 0x23),
    0x9100: ("<<ネタ切レシマシタ&&ゴメンネ！&&マタ　来テネ～。", 0x00)
}

SHOP_MESSAGES = {
    0x80B2: "<#\x01デクの実（５コ）１５ルピー#\x00&投げると　目つぶしになる。>*O",
    0x807F: "<デクの実（５コ）１５ルピー&:2#\x02かう&やめとく#\x00>",
    0x80C1: "<#\x01矢（３０本）６０ルピー#\x00&弓がない人には　売れません。>*O",
    0x809B: "<矢（３０本）６０ルピー&:2#\x02かう&やめとく#\x00>",
    0x80B0: "<#\x01矢（５０本）９０ルピー#\x00&弓がない人には　売れません。>*O",
    0x807D: "<矢（５０本）９０ルピー&:2#\x02かう&やめとく#\x00>",
    0x80A3: "<#\x01バクダン（５コ）２５ルピー#\x00&ボム袋がないと　買えません。>*O",
    0x808B: "<バクダン（５コ）２５ルピー&:2#\x02かう&やめとく#\x00>",
    0x80A2: "<#\x01デクの実（１０コ）３０ルピー#\x00&投げると　目つぶしになる。>*O",
    0x8087: "<デクの実（１０コ）３０ルピー&:2#\x02かう&やめとく#\x00>",
    0x80A1: "<#\x01デクの棒（１本）１０ルピー#\x00&武器にもなるが、折れます。>*O",
    0x8088: "<デクの棒（１本）１０ルピー&:2#\x02かう&やめとく#\x00>",
    0x80B1: "<#\x01バクダン（１０コ）５０ルピー#\x00&ボム袋がないと　買えません。>*O",
    0x807C: "<バクダン（１０コ）５０ルピー&:2#\x02かう&やめとく#\x00>",
    0x80B3: "<#\x01サカナ　２００ルピー#\x00&ビンに入れて　保存できる。>*O",
    0x807E: "<サカナ　２００ルピー&:2#\x02かう&やめとく#\x00>",
    0x80A5: "<#\x01赤いクスリ　３０ルピー#\x00&飲むと　体力が　回復する。>*O",
    0x808E: "<赤いクスリ　３０ルピー&:2#\x02かう&やめとく#\x00>",
    0x80A6: "<#\x01緑のクスリ　３０ルピー#\x00&飲むと　魔法の力が　回復する。>*O",
    0x808F: "<緑のクスリ　３０ルピー&:2#\x02かう&やめとく#\x00>",
    0x80A9: "<#\x01ハイリアの盾　８０ルピー#\x00&炎攻撃を防ぐ。>*O",
    0x8092: "<ハイリアの盾　８０ルピー&:2#\x02かう&やめとく#\x00>",
    0x809F: "<#\x01デクの盾　４０ルピー#\x00&火がつくと　燃えてしまう。>*O",
    0x8089: "<デクの盾　４０ルピー&:2#\x02かう&やめとく#\x00>",
    0x80AA: "<#\x01ゴロンの服　２００ルピー#\x00&大人専用の　耐火服。>*O",
    0x8093: "<ゴロンの服　２００ルピー&:2#\x02かう&やめとく#\x00>",
    0x80AB: "<#\x01ゾーラの服　３００ルピー#\x00&大人専用の　潜水服。>*O",
    0x8094: "<ゾーラの服　３００ルピー&:2#\x02かう&やめとく#\x00>",
    0x80AC: "<#\x01回復のハート　１０ルピー#\x00&ハート１つ分、体力回復。>*O",
    0x8095: "<回復のハート　１０ルピー&:2#\x02かう&やめとく#\x00>",
    0x8061: "<#\x01ボムチュウ（２０コ）１８０ルピー#\x00&自分で走る　新型バクダン。>*O",
    0x802A: "<ボムチュウ（２０コ）１８０ルピー&:2#\x02かう&やめとく#\x00>",
    0x80DF: "<#\x01デクのタネ（３０コ）３０ルピー#\x00&パチンコがないと　買えません。>*O",
    0x80DE: "<デクのタネ（３０コ）３０ルピー&:2#\x02かう&やめとく#\x00>",
    0x80B9: "<#\x01青い炎　３００ルピー#\x00&あきビンがないと　買えません。>*O",
    0x80B8: "<青い炎　３００ルピー&:2#\x02かう&やめとく#\x00>",
    0x80BB: "<#\x01ムシ　５０ルピー#\x00&あきビンがないと　買えません。>*O",
    0x80BA: "<ムシ　５０ルピー&:2#\x02かう&やめとく#\x00>",
    0x80B7: "<#\x01妖精の魂　５０ルピー#\x00&あきビンがないと　買えません。>*O",
    0x80B6: "<妖精の魂　５０ルピー&:2#\x02かう&やめとく#\x00>",
    0x80A0: "<#\x01矢（１０本）２０ルピー#\x00&弓がない人には　売れません。>>*O",
    0x808A: "<矢（１０本）２０ルピー&:2#\x02かう&やめとく#\x00>",
    0x801C: "<#\x01バクダン（２０コ）３０ルピー#\x00&ボム袋がないと　買えません。>*O",
    0x8006: "<バクダン（２０コ）３０ルピー&:2#\x02かう&やめとく#\x00>",
    0x801D: "<#\x01バクダン（３０コ）１２０ルピー#\x00&ボム袋がないと　買えません。>*O",
    0x801E: "<バクダン（３０コ）１２０ルピー&:2#\x02かう&やめとく#\x00>",
    0x80CB: "<#\x01バクダン（５コ）３５ルピー#\x00&ボム袋がないと　買えません。>*O",
    0x80CA: "<バクダン（５コ）３５ルピー&:2#\x02かう&やめとく#\x00>",
    0x8064: "<#\x01赤いクスリ　４０ルピー#\x00&飲むと　体力が　回復する。>*O",
    0x8062: "<赤いクスリ　４０ルピー&:2#\x02かう&やめとく#\x00>",
    0x8065: "<#\x01赤いクスリ　５０ルピー#\x00&飲むと　体力が　回復する。>*O",
    0x8063: "<赤いクスリ　５０ルピー&:2#\x02かう&やめとく#\x00>",
    0x80BD: "<#\x01売り切れました#\x00>*O",
}
def jp_start(rom):
    NULLTEXT = bytes([0x00] * JPN_TEXT_SIZE_LIMIT)
    rom.write_bytes(TEXT_START,NULLTEXT)
    NULLTABLE = bytes([0x00] * JPN_TABLE_SIZE)
    rom.write_bytes(EXTENDED_TABLE_START,NULLTABLE)
    lines = open('textJP.py',encoding='utf-8').readlines()
    NewLines = []
    increments = 1

    for line in lines:
        a = ("  '" + str(increments) + "'")
        NewLines.append(line.replace(' :',a))
        increments += 1
        
    with open("temporal.py","w",encoding="utf-8")as new:
        new.write(''.join(NewLines))

        
    with open("temporal.py",'a') as new:
        new.write("\n")
        new.write("MESTEXT = {\n")

class Shop_Item():

    def display(self):
        meta_data = ["#" + str(self.index),
         "Item: 0x" + "{:04x}".format(self.get_item_id),
         "Price: " + str(self.price),
         "Amount: " + str(self.pieces),
         "Object: 0x" + "{:04x}".format(self.object),
         "Model: 0x" + "{:04x}".format(self.model),
         "Description: 0x" + "{:04x}".format(self.description_message),
         "Purchase: 0x" + "{:04x}".format(self.purchase_message),]
        func_data = [
         "func1: 0x" + "{:08x}".format(self.func1),
         "func2: 0x" + "{:08x}".format(self.func2),
         "func3: 0x" + "{:08x}".format(self.func3),
         "func4: 0x" + "{:08x}".format(self.func4),]
        return ', '.join(meta_data) + '\n' + ', '.join(func_data)

    # write the shop item back
    def write(self, rom, shop_table_address, index):

        entry_offset = shop_table_address + 0x20 * index

        bytes = []
        bytes += int_to_bytes(self.object, 2)
        bytes += int_to_bytes(self.model, 2)
        bytes += int_to_bytes(self.func1, 4)
        bytes += int_to_bytes(self.price, 2, signed=True)
        bytes += int_to_bytes(self.pieces, 2)
        bytes += int_to_bytes(self.description_message, 2)
        bytes += int_to_bytes(self.purchase_message, 2)
        bytes += [0x00, 0x00]
        bytes += int_to_bytes(self.get_item_id, 2)
        bytes += int_to_bytes(self.func2, 4)
        bytes += int_to_bytes(self.func3, 4)
        bytes += int_to_bytes(self.func4, 4)

        rom.write_bytes(entry_offset, bytes)

    # read a single message
    def __init__(self, rom, shop_table_address, index):

        entry_offset = shop_table_address + 0x20 * index
        entry = rom.read_bytes(entry_offset, 0x20)

        self.index = index
        self.object = bytes_to_int(entry[0x00:0x02])
        self.model = bytes_to_int(entry[0x02:0x04])
        self.func1 = bytes_to_int(entry[0x04:0x08])
        self.price = bytes_to_int(entry[0x08:0x0A])
        self.pieces = bytes_to_int(entry[0x0A:0x0C])
        self.description_message = bytes_to_int(entry[0x0C:0x0E])
        self.purchase_message = bytes_to_int(entry[0x0E:0x10])
        # 0x10-0x11 is always 0000 padded apparently
        self.get_item_id = bytes_to_int(entry[0x12:0x14])
        self.func2 = bytes_to_int(entry[0x14:0x18])
        self.func3 = bytes_to_int(entry[0x18:0x1C])
        self.func4 = bytes_to_int(entry[0x1C:0x20])

    __str__ = __repr__ = display

def read_shop_items(rom, shop_table_address):
    shop_items = []

    for index in range(0, 100):
        shop_items.append( Shop_Item(rom, shop_table_address, index) )

    return shop_items

def write_shop_items(rom, shop_table_address, shop_items):
    for s in shop_items:
        s.write(rom, shop_table_address, s.index)

# these are unused shop items, and contain text ids that are used elsewhere, and should not be moved
SHOP_ITEM_EXCEPTIONS = [0x0A, 0x0B, 0x11, 0x12, 0x13, 0x14, 0x29]

# returns a set of all message ids used for shop items
def get_shop_message_id_set(shop_items):
    ids = set()
    for shop in shop_items:
        if shop.index not in SHOP_ITEM_EXCEPTIONS:
            ids.add(shop.description_message)
            ids.add(shop.purchase_message)
    return ids

def move_shop_item_messages(messages, shop_items):
    # checks if a message id is in the item message range
    def is_in_item_range(id):
        bytes = int_to_bytes(id, 2)
        return bytes[0] == 0x00
    # update them in the shop item list
    for shop in shop_items:
        if is_in_item_range(shop.description_message):
            shop.description_message |= 0x8000
        if is_in_item_range(shop.purchase_message):
            shop.purchase_message |= 0x8000
            
messages = []
def update_message_jp(messages, id, text, opts=None, mode = 0):
    if mode == 0:
        text = text + "|"
        jptext = (JPencode(text))
    if mode == 1:
        text = text + "|"
        jptext = (JPencode(text, 1))
    if mode == 2:
        text = text + "||"
        jptext = (JPencode(text, 2))
    with open("temporal.py",'a') as new:
        new.write('    0x')
        new.write(str(f'{id:04x}'))
        new.write(":    (r'")
        new.write((jptext))
        new.write("', ")
        if opts is None:
            new.write("None, '")
        else:
            new.write('0x')
            new.write(str(f'{opts:02x}'))
            new.write(", '")
        new.write(parsejp(jptext, 0))
        new.write("', '")
        new.write(parsejp(jptext, 1))
        new.write("'),\n")

def update_item_messages_jp(messages):
    new_item_messages = {**ITEM_MESSAGES, **KEYSANITY_MESSAGES}
    shop_mes = {**SHOP_MESSAGES}
    for id, text in new_item_messages.items():
        update_message_jp(messages, id, text, 0x23, 2)
    for id, text in shop_mes.items():
        update_message_jp(messages, id, text, 0x03)
    for id, (text, opt) in MISC_MESSAGES.items():
        update_message_jp(messages, id, text, opt, 2)
    
def add_item_messages(messages, shop_items, world):
    move_shop_item_messages(messages, shop_items)
    update_item_messages_jp(messages)
    
def reproduce_messages_jp(messages):
    with open("temporal.py",'a') as new:
        new.write("}\n")
        new.write("new_jp = {**RAWTEXT_JP,**MESTEXT}")
    

def write_messages(rom, shuffle = False, shuffle_group = None):
    from temporal import new_jp
    index = 0
    offset = 0
    text_size_limit = JPN_TEXT_SIZE_LIMIT
    with open("temporal.py", "r+")as red:
        for id, (text, opt, tag, ending) in new_jp.items():
            id_bytes = int_to_bytes(id, 2)
            if shuffle is True:
                for (origin, replace) in shuffle_group:
                    if (origin == id)is True:
                        text = replace
            offset_bytes = int_to_bytes(offset, 3)
            opts = int_to_bytes(int(0 if opt is None else opt),1)
            entry = id_bytes + opts + bytes([0x00, 0x08]) + offset_bytes
            entry_offset = EXTENDED_TABLE_START + 8 * index
            rom.write_bytes(entry_offset, entry)
            if (int(offset / 2)* 2 == offset):
                t = int(len(text) / 4)
                text_entry = text_to_bytes(text,t)
            else:
                t = int(1 + len(text) / 4)
                text_entry = text_to_bytes(text,t) + bytes([0x00])
            text_offset = TEXT_START + offset
            rom.write_bytes(text_offset, text_entry)
            offset += t
            index += 1
    entry = bytes([0xFF, 0xFD, 0x00, 0x00, 0x08]) + int_to_bytes(offset, 3)
    entry_offset = EXTENDED_TABLE_START + 8 * index
    if 8 * (index + 1) > EXTENDED_TABLE_SIZE:
        raise(TypeError("Message ID table is too large: 0x" + "{:x}".format(8 * (index + 1)) + " written / 0x" + "{:x}".format(EXTENDED_TABLE_SIZE) + " allowed."))
    rom.write_bytes(entry_offset,entry)
    text_entry = bytes([0x81, 0x70])
    text_offset = TEXT_START + offset
    if offset > text_size_limit:
        raise(TypeError("Message Text table is too large: 0x" + "{:x}".format(offset) + " written / 0x" + "{:x}".format(JPN_TEXT_SIZE_LIMIT) + " allowed."))
    rom.write_bytes(text_offset, text_entry)
    index += 1
    entry_offset = EXTENDED_TABLE_START + 8 * index
    rom.write_bytes(entry_offset, [0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

# shuffles the messages in the game, making sure to keep various message types in their own group
def shuffle_messages_jp(messages, except_hints=True, always_allow_skip=True):

    have_gen_I = []
    have_gen_O = []
    have_ocarina_I = []
    have_ocarina_O = []
    have_two_I = []
    have_two_O = []
    have_three_I = []
    have_three_O = []
    shuffled = []

    def is_exempt(id):
        hint_ids = (
            GOSSIP_STONE_MESSAGES + TEMPLE_HINTS_MESSAGES + LIGHT_ARROW_HINT +
            list(KEYSANITY_MESSAGES.keys()) + list(SHOP_MESSAGES.keys()) +
            [0x10A0, 0x10A1, 0x10A2, 0x10CA, 0x10CB, 0x10CC, 0x10CD, 0x10CE, 0x10CF, 0x10DC, 0x10DD, 0x5036, 0x70F5, 0xFFFC, 0xFFFD, 0xFFFF, 0x088D, 0x088E, 0x088F, 0x0890, 0x0891, 0x0892] # Chicken count and poe count respectively
        )
        shuffle_exempt = [
            0x208D,         # "One more lap!" for Cow in House race.
        ]
        is_hint = (except_hints and str(id) in str(hint_ids))
        is_error_message = (str(id) == str(ERROR_MESSAGE))
        is_shuffle_exempt = (str(id) in str(shuffle_exempt))
        return (is_hint or is_error_message or is_shuffle_exempt)
    with open("temporal.py","r+") as dec:
        from temporal import new_jp
        for id, (text, opt, tag, ending) in new_jp.items():
            if (((("g" in tag)or("k" in tag)or("e" in tag)or("f" in tag))is True) or (("" == text)is True) and not is_exempt(id)):
                have_gen_I.append(text)
                have_gen_O.append(id)
            if(((("o" in tag) is True))and not is_exempt(id)):
                have_ocarina_I.append(text)
                have_ocarina_O.append(id)
            if(((("2" in tag) is True))and not is_exempt(id)):
                have_two_I.append(text)
                have_two_O.append(id)
            if(((("3" in tag) is True))and not is_exempt(id)):
                have_three_I.append(text)
                have_three_O.append(id)

    random.shuffle(have_gen_I)
    random.shuffle(have_ocarina_I)
    random.shuffle(have_two_I)
    random.shuffle(have_three_I)
    gen = [(i, j) for i, j in zip(have_gen_O, have_gen_I)]
    ocarina = [(i, j) for i, j in zip(have_ocarina_O, have_ocarina_I)]
    two = [(i, j) for i, j in zip(have_two_O, have_two_I)]
    three = [(i, j) for i, j in zip(have_three_O, have_three_I)]
    shuffled = (gen + ocarina + two + three)
    return shuffled

#reproduce_messages_jp(messages)            
def update_warp_song_text_jp(messages, world):
    msg_list = {
        0x088D: 'Minuet of Forest Warp -> Sacred Forest Meadow',
        0x088E: 'Bolero of Fire Warp -> DMC Central Local',
        0x088F: 'Serenade of Water Warp -> Lake Hylia',
        0x0890: 'Requiem of Spirit Warp -> Desert Colossus',
        0x0891: 'Nocturne of Shadow Warp -> Graveyard Warp Pad Region',
        0x0892: 'Prelude of Light Warp -> Temple of Time',
    }

    for id, entr in msg_list.items():
        destination_raw = world.get_entrance(entr).connected_region.name

        # Format the region name
        destination, color = None, None
        for formatted_region, info in REGION_NAMES.items():
            raw_region_list, region_color = info
            if destination_raw in raw_region_list:
                destination = formatted_region
                color = region_color
                break
        
            

        # Check if region name isn't found
        if destination is None:
            logging.error("不明：" + destination_raw)
            destination = "謎の場所"
            color = "\x00"

        new_msg = f"<#{color}{destination}へワープ！#\x00>&:2#{color}はい&いいえ#\x00"
        update_message_jp(messages, id, new_msg)
 
# os.remove("temporal.py")

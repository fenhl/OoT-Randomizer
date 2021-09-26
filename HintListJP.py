import random
import re
#   Abbreviations
#       DMC     Death Mountain Crater
#       DMT     Death Mountain Trail
#       GC      Goron City
#       GF      Gerudo's Fortress
#       GS      Gold Skulltula
#       GV      Gerudo Valley
#       HC      Hyrule Castle
#       HF      Hyrule Field
#       KF      Kokiri Forest
#       LH      Lake Hylia
#       LLR     Lon Lon Ranch
#       LW      Lost Woods
#       OGC     Outside Ganon's Castle
#       SFM     Sacred Forest Meadow
#       TH      Thieves' Hideout
#       ZD      Zora's Domain
#       ZF      Zora's Fountain
#       ZR      Zora's River

class Hint(object):
    name = ""
    text = ""
    type = []

    def __init__(self, name, text, type, choice=None):
        self.name = name
        self.type = [type] if not isinstance(type, list) else type

        if isinstance(text, str):
            self.text = text
        else:
            if choice == None:
                self.text = random.choice(text)
            else:
                self.text = text[choice]
                
class HintEX(object):
    name = ""
    text = ""
    type = []

    def __init__(self, name, text, type, choice=None):
        self.name = name
        self.type = [type] if not isinstance(type, list) else type
        self.text = name
        
def has_eng(text):
    if type(text) == list:
        text = text[0]
    if text is None:
        return False
    return re.search(r'[a-z]+', text) is not None
    
def getHint(name, clearer_hint=False):
    textOptions, clearText, type = hintTable[name]
    if clearer_hint:
        if clearText is None:
            if has_eng(textOptions):
                return HintEX(name, textOptions, type, 0)
            return Hint(name, textOptions, type, 0)
        if has_eng(textOptions):
            return HintEX(name, clearText, type)
        return Hint(name, clearText, type)
    else:
        if has_eng(textOptions):
            return HintEX(name, textOptions, type)
        return Hint(name, textOptions, type)


def getHintGroup(group, world):
    ret = []
    for name in hintTable:

        hint = getHint(name, world.settings.clearer_hints)

        if type(hint) != str and hint.name in world.always_hints and group == 'always':
            hint.type = 'always'

        # Hint inclusion override from distribution
        if group in world.added_hint_types or group in world.item_added_hint_types:
            if type(hint) != str and hint.name in world.added_hint_types[group]:
                hint.type = group
            if type(hint) != str and nameIsLocation(name, hint.type, world):
                location = world.get_location(name)
                for i in world.item_added_hint_types[group]:
                    if i == location.item.name:
                        hint.type = group
                for i in world.item_hint_type_overrides[group]:
                    if i == location.item.name:
                        hint.type = []
        type_override = False
        if group in world.hint_type_overrides:
            if name in world.hint_type_overrides[group]:
                type_override = True
        if group in world.item_hint_type_overrides:
            if type(hint) != str and nameIsLocation(name, hint.type, world):
                location = world.get_location(name)
                if location.item.name in world.item_hint_type_overrides[group]:
                    type_override = True

        if type(hint) != str and group in hint.type and (name not in hintExclusions(world)) and not type_override:
            ret.append(hint)
    return ret


def getRequiredHints(world):
    ret = []
    for name in hintTable:
        hint = getHint(name)
        if type(hint) != str and 'always' in hint.type or hint.name in conditional_always and conditional_always[hint.name](world):
            ret.append(hint)
    return ret


# Helpers for conditional always hints
def stones_required_by_settings(world):
    stones = 0
    if world.settings.bridge == 'stones':
        stones = max(stones, world.settings.bridge_stones)
    if world.settings.shuffle_ganon_bosskey == 'on_lacs' and world.settings.lacs_condition == 'stones':
        stones = max(stones, world.settings.lacs_stones)
    if world.settings.shuffle_ganon_bosskey == 'stones':
        stones = max(stones, world.settings.ganon_bosskey_stones)
    if world.settings.bridge == 'dungeons':
        stones = max(stones, world.settings.bridge_rewards - 6)
    if world.settings.shuffle_ganon_bosskey == 'on_lacs' and world.settings.lacs_condition == 'dungeons':
        stones = max(stones, world.settings.lacs_rewards - 6)
    if world.settings.shuffle_ganon_bosskey == 'dungeons':
        stones = max(stones, world.settings.ganon_bosskey_rewards - 6)

    return stones


def medallions_required_by_settings(world):
    medallions = 0
    if world.settings.bridge == 'medallions':
        medallions = max(medallions, world.settings.bridge_medallions)
    if world.settings.shuffle_ganon_bosskey == 'on_lacs' and world.settings.lacs_condition == 'medallions':
        medallions = max(medallions, world.settings.lacs_medallions)
    if world.settings.shuffle_ganon_bosskey == 'medallions':
        medallions = max(medallions, world.settings.ganon_bosskey_medallions)
    if world.settings.bridge == 'dungeons':
        medallions = max(medallions, max(world.settings.bridge_rewards - 3, 0))
    if world.settings.shuffle_ganon_bosskey == 'on_lacs' and world.settings.lacs_condition == 'dungeons':
        medallions = max(medallions, max(world.settings.lacs_rewards - 3, 0))
    if world.settings.shuffle_ganon_bosskey == 'dungeons':
        medallions = max(medallions, max(world.settings.ganon_bosskey_rewards - 3, 0))

    return medallions


def tokens_required_by_settings(world):
    tokens = 0
    if world.settings.bridge == 'tokens':
        tokens = max(tokens, world.settings.bridge_tokens)
    if world.settings.shuffle_ganon_bosskey == 'on_lacs' and world.settings.lacs_condition == 'tokens':
        tokens = max(tokens, world.settings.lacs_tokens)
    if world.settings.shuffle_ganon_bosskey == 'tokens':
        tokens = max(tokens, world.settings.ganon_bosskey_tokens)

    return tokens


# Hints required under certain settings
conditional_always = {
    'Market 10 Big Poes':           lambda world: world.settings.big_poe_count > 3,
    'Deku Theater Mask of Truth':   lambda world: not world.settings.complete_mask_quest,
    'Song from Ocarina of Time':    lambda world: stones_required_by_settings(world) < 2,
    'HF Ocarina of Time Item':      lambda world: stones_required_by_settings(world) < 2,
    'Sheik in Kakariko':            lambda world: medallions_required_by_settings(world) < 5,
    'DMT Biggoron':                 lambda world: world.settings.logic_earliest_adult_trade != 'claim_check' or world.settings.logic_latest_adult_trade != 'claim_check',
    'Kak 30 Gold Skulltula Reward': lambda world: tokens_required_by_settings(world) < 30,
    'Kak 40 Gold Skulltula Reward': lambda world: tokens_required_by_settings(world) < 40,
    'Kak 50 Gold Skulltula Reward': lambda world: tokens_required_by_settings(world) < 50,
}


# table of hints, format is (name, hint text, clear hint text, type of hint) there are special characters that are read for certain in game commands:
# ^ is a box break
# & is a new line
# @ will print the player name
# C sets color to white (currently only used for dungeon reward hints).
hintTable = {
    'Triforce Piece':                                           (["勝利の欠片", "チーズ", "金の欠片"], "トライフォース", "item"),
    'Magic Meter':                                              (["緑の神秘","緑の線"], "魔力増加", 'item'),
    'Double Defense':                                           (["白いハート", "ダメージ減少"], "防御二倍", 'item'),
    'Slingshot':                                                (["タネ飛ばし", "ゴム", "カタパルト"], "パチンコ", 'item'),
    'Boomerang':                                                (["バナナ", "スタン棒"], "ブーメラン", 'item'),
    'Bow':                                                      (["矢飛ばし", "ダーツ飛ばし"], "弓本体", 'item'),
    'Bomb Bag':                                                 (["爆発物の袋", "体飛ばし"], "ボム袋", 'item'),
    'Progressive Hookshot':                                     (["ダンペイの記念品", "取り付く線"], "フックショット", 'item'),
    'Progressive Strength Upgrade':                             (["力のグローブ", "力持ち"], "うでわ", 'item'),
    'Progressive Scale':                                        (["水深増加", "ゾーラの欠片"], "ウロコ", 'item'),
    'Megaton Hammer':                                           (["ドラゴンスマッシャー", "鉄のマレット"], "メガトンハンマー", 'item'),
    'Iron Boots':                                               (["重いクツ", "耐風クツ"], "ヘビーブーツ", 'item'),
    'Hover Boots':                                              (["滑らかなクツ", "聖なるスリッパ", "滑り歩き"], "ホバーブーツ", 'item'),
    'Kokiri Sword':                                             (["バターナイフ", "スターター剣", "飛び出しナイフ"], "コキリの剣", 'item'),
    'Giants Knife':                                             (["脆い刃", "壊れる包丁"], "巨人のナイフ", 'item'),
    'Biggoron Sword':                                           (["最大の刀", "壊れない包丁"], "ダイゴロン刀", 'item'),
    'Master Sword':                                             (["聖なる包丁"], "マスターソード", 'item'),
    'Deku Shield':                                              (["木の盾", "燃える盾"], "デクの盾", 'item'),
    'Hylian Shield':                                            (["鉄の盾", "ライクライクの鉄分"], "ハイリアの盾", 'item'),
    'Mirror Shield':                                            (["跳ね返す城壁", "メデューサの弱点", "顔の映る表面"], "ミラーシールド", 'item'),
    'Farores Wind':                                             (["テレポート", "場所移し", "緑の玉", "緑の風"], "フロルの風", 'item'),
    'Nayrus Love':                                              (["難攻不落のオーラ", "青い守り", "青い玉"], "ネールの愛", 'item'),
    'Dins Fire':                                                (["インフェルノ", "熱波", "赤い玉"], "ディンの炎", 'item'),
    'Fire Arrows':                                              (["燃える矢", "マグマミサイル"], "炎の矢", 'item'),
    'Ice Arrows':                                               (["冷えた矢", "凍る矢", "使えない矢"], "氷の矢", 'item'),
    'Light Arrows':                                             (["光", "飛ばせる輝き", "聖なる矢"], "光の矢", 'item'),
    'Lens of Truth':                                            (["うそ発見器", "霊の追跡機", "真実を見る", "探偵のツール"], "まことのメガネ", 'item'),
    'Ocarina':                                                  (["横笛", "曲鳴らし"], "オカリナ", 'item'),
    'Goron Tunic':                                              (["ルビーの服", "耐火服"], "ゴロンの服", 'item'),
    'Zora Tunic':                                               (["サファイアの服", "スキューバ", "水着"], "ゾーラの服", 'item'),
    'Epona':                                                    (["馬", "四足の友達"], "エポナ", 'item'),
    'Zeldas Lullaby':                                           (["王家の眠り歌", "フォースの歌"], "ゼルダの子守歌", 'item'),
    'Eponas Song':                                              (["馬術の歌", "マロンの歌", "牧場の歌"], "エポナの歌", 'item'),
    'Sarias Song':                                              (["ゴロンの踊る歌", "サリアの電話番号"], "サリアの歌", 'item'),
    'Suns Song':                                                (["晴天の歌", "リーデッドの天敵", "ギブドの天敵"], "太陽の歌", 'item'),
    'Song of Time':                                             (["７年を語る歌", "時をかける歌"], "時の歌", 'item'),
    'Song of Storms':                                           (["雨踊り", "雷雨の歌", "風車を加速する歌"], "嵐の歌", 'item'),
    'Minuet of Forest':                                         (["高木の歌", "樹木の歌", "緑に輝く歌"], "森のメヌエット", 'item'),
    'Bolero of Fire':                                           (["溶岩の歌", "赤に輝く歌", "火山の歌"], "炎のボレロ", 'item'),
    'Serenade of Water':                                        (["湿溝の歌", "青に輝く歌", "川の歌"], "水のセレナーデ", 'item'),
    'Requiem of Spirit':                                        (["砂の宮殿の歌", "橙に輝く歌", "砂漠の歌"], "魂のレクイエム", 'item'),
    'Nocturne of Shadow':                                       (["魂の歌", "墓場の歌", "呪われた歌", "紫に輝く歌"], "闇のノクターン", 'item'),
    'Prelude of Light':                                         (["平和の光の歌", "黄色に輝く歌", "神殿の歌"], "光のプレリュード", 'item'),
    'Bottle':                                                   (["グラス", "万能瓶", "空気瓶"], "空き瓶", 'item'),
    'Rutos Letter':                                             (["助け", "ムニッへの手紙", "ＳＯＳ", "サカナの手紙"], "ルトの手紙", 'item'),
    'Bottle with Milk':                                         (["牛の恵み", "白い瓶", "赤子の食べ物"], "牛乳", 'item'),
    'Bottle with Red Potion':                                   (["活力の瓶", "赤い瓶"], "赤いクスリ", 'item'),
    'Bottle with Green Potion':                                 (["魔法の瓶", "緑の瓶"], "緑のクスリ", 'item'),
    'Bottle with Blue Potion':                                  (["病の特高瓶", "青い瓶"], "青いクスリ", 'item'),
    'Bottle with Fairy':                                        (["囚われた妖精", "１ＵＰ", "ナビィの親戚"], "妖精", 'item'),
    'Bottle with Fish':                                         (["水槽", "ジャブジャブの餌"], "サカナ", 'item'),
    'Bottle with Blue Fire':                                    (["青い引火瓶", "解氷瓶"], "青い炎", 'item'),
    'Bottle with Bugs':                                         (["昆虫", "トークン探知機"], "虫かご", 'item'),
    'Bottle with Poe':                                          (["幽霊", "顔入り瓶"], "ポウ", 'item'),
    'Bottle with Big Poe':                                      (["大いなる幽霊", "大きな幽霊"], "ビッグポウ", 'item'),
    'Stone of Agony':                                           (["震える石", "振動パック（Ｒ）"], "もだえ石", 'item'),
    'Gerudo Membership Card':                                   (["ゲルドクラブ", "部族証"], "ゲルド会員証", 'item'),
    'Progressive Wallet':                                       (["金銭増加", "宝石入れ", "小さな銀行"], "サイフ", 'item'),
    'Deku Stick Capacity':                                      (["棒ストック", "可燃ストック"], "棒増加", 'item'),
    'Deku Nut Capacity':                                        (["目晦まし増加"], "種増加", 'item'),
    'Heart Container':                                          (["愛の器", "本命チョコ", "ボスの心"], "ハートの器", 'item'),
    'Piece of Heart':                                           (["小さな愛", "壊れた心"], "ハートの欠片", 'item'),
    'Piece of Heart (Treasure Chest Game)':                     ("義理チョコ", "ハートの欠片", 'item'),
    'Recovery Heart':                                           (["回復の愛", "友チョコ", "絆創膏"], "回復のハート", 'item'),
    'Rupee (Treasure Chest Game)':                              ("緑のゴミ", '１ルピー', 'item'),
    'Deku Stick (1)':                                           ("壊れる枝", 'デクの棒', 'item'),
    'Rupee (1)':                                                (["１銭", "緑の宝石"], "１ルピー", 'item'),
    'Rupees (5)':                                               (["いつもの", "青いゴミ"], "５ルピー", 'item'),
    'Rupees (20)':                                              (["程良いルピー", "赤い宝石"], "２０ルピー", 'item'),
    'Rupees (50)':                                              (["紫の宝石", "財貨"], "５０ルピー", 'item'),
    'Rupees (200)':                                             (["ジャックポット", "黄色い宝石", "大きいルピー", "富豪"], "２００ルピー", 'item'),
    'Weird Egg':                                                (["コッコのジレンマ"], "不思議なタマゴ", 'item'),
    'Zeldas Letter':                                            (["王家のサイン", "王家の手紙", "姫の手紙"], "ゼルダの手紙", 'item'),
    'Pocket Egg':                                               (["コッコの殻", "ほぼコッコ", "若いコッコ"], "ポケットタマゴ", 'item'),
    'Pocket Cucco':                                             (["目覚まし時計"], "てのりコッコ", 'item'),
    'Cojiro':                                                   (["青いコッコ"], "コジロー", 'item'),
    'Odd Mushroom':                                             (["粉の素材"], "あやしいキノコ", 'item'),
    'Odd Potion':                                               (["おばばのクスリ"], "あやしいクスリ", 'item'),
    'Poachers Saw':                                             (["木殺し"], "ノコギリ", 'item'),
    'Broken Sword':                                             (["壊れた刃"], "折れた刀", 'item'),
    'Prescription':                                             (["クスリの予約表", "医者の書留"], "処方せん", 'item'),
    'Eyeball Frog':                                             (["大人のオタマジャクシ"], "カエル", 'item'),
    'Eyedrops':                                                 (["視力回復"], "目薬", 'item'),
    'Claim Check':                                              (["３日待ち"], "ひきかえ券", 'item'),
    'Map':                                                      (["ダンジョン地図", "見取り図"], "地図", 'item'),
    'Map (Deku Tree)':                                          (["木の地図", "木の見取り図"], "デクの樹の地図", 'item'),
    'Map (Dodongos Cavern)':                                    (["洞窟の地図", "洞窟の案内図"], "ドドンゴの地図", 'item'),
    'Map (Jabu Jabus Belly)':                                   (["水神の地図", "水神の見取り図"], "ジャブジャブの地図", 'item'),
    'Map (Forest Temple)':                                      (["深き森の地図", "深き森の案内図"], "森の神殿の地図", 'item'),
    'Map (Fire Temple)':                                        (["高き山の地図", "高き山の案内図"], "炎の神殿の地図", 'item'),
    'Map (Water Temple)':                                       (["広き湖の地図", "広き湖の見取り図"], "水の神殿の地図", 'item'),
    'Map (Shadow Temple)':                                      (["屍の館の地図", "館の見取り図"], "闇の神殿の地図", 'item'),
    'Map (Spirit Temple)':                                      (["砂の女神の地図", "女神の見取り図"], "魂の神殿の地図", 'item'),
    'Map (Bottom of the Well)':                                 (["井戸の地図", "井戸の見取り図"], "井戸の下の地図", 'item'),
    'Map (Ice Cavern)':                                         (["凍る地図", "凍る案内図"], "氷の洞窟の地図", 'item'),
    'Compass':                                                  (["宝探知機", "羅針盤"], "コンパス", 'item'),
    'Compass (Deku Tree)':                                      (["木の探知機", "木の羅針盤"], "デクの樹のコンパス", 'item'),
    'Compass (Dodongos Cavern)':                                (["洞窟の探知機", "洞窟の羅針盤"], "ドドンゴのコンパス", 'item'),
    'Compass (Jabu Jabus Belly)':                               (["水神の探知機", "水神の羅針盤"], "ジャブジャブのコンパス", 'item'),
    'Compass (Forest Temple)':                                  (["深き森の探知機", "深き森の羅針盤"], "森の神殿のコンパス", 'item'),
    'Compass (Fire Temple)':                                    (["高き山の探知機", "高き山の羅針盤"], "炎の神殿のコンパス", 'item'),
    'Compass (Water Temple)':                                   (["広き湖の探知機", "広き湖の羅針盤"], "水の神殿のコンパス", 'item'),
    'Compass (Shadow Temple)':                                  (["屍の館の探知機", "屍の館の羅針盤"], "闇の神殿のコンパス", 'item'),
    'Compass (Spirit Temple)':                                  (["女神の探知機", "女神の羅針盤"], "魂の神殿のコンパス", 'item'),
    'Compass (Bottom of the Well)':                             (["井戸の探知機", "井戸の羅針盤"], "井戸の下のコンパス", 'item'),
    'Compass (Ice Cavern)':                                     (["凍る探知機", "凍る羅針盤"], "氷の洞窟のコンパス", 'item'),
    'BossKey':                                                  (["解除の達人", "大きなカギ"], "ボスキー", 'item'),
    'GanonBossKey':                                             (["解除の達人", "大きなカギ"], "ボスキー", 'item'),
    'SmallKey':                                                 (["解除のツール", "扉開け", "ロックピック"], "小さなカギ", 'item'),
    'HideoutSmallKey':                                          (["釈放カード"], "牢屋のカギ", 'item'),
    'Boss Key (Forest Temple)':                                 (["解除の達人", "大きなカギ"], "森のボスキー", 'item'),
    'Boss Key (Fire Temple)':                                   (["解除の達人", "大きなカギ"], "炎のボスキー", 'item'),
    'Boss Key (Water Temple)':                                  (["解除の達人", "大きなカギ"], "水のボスキー", 'item'),
    'Boss Key (Shadow Temple)':                                 (["解除の達人", "大きなカギ"], "闇のボスキー", 'item'),
    'Boss Key (Spirit Temple)':                                 (["解除の達人", "大きなカギ"], "魂のボスキー", 'item'),
    'Boss Key (Ganons Castle)':                                 (["解除の達人", "大きなカギ"], "ガノンボスキー", 'item'),
    'Small Key (Forest Temple)':                                (["解除のツール", "扉開け", "ロックピック"], "森のカギ", 'item'),
    'Small Key (Fire Temple)':                                  (["解除のツール", "扉開け", "ロックピック"], "炎のカギ", 'item'),
    'Small Key (Water Temple)':                                 (["解除のツール", "扉開け", "ロックピック"], "水のカギ", 'item'),
    'Small Key (Shadow Temple)':                                (["解除のツール", "扉開け", "ロックピック"], "闇のカギ", 'item'),
    'Small Key (Spirit Temple)':                                (["解除のツール", "扉開け", "ロックピック"], "魂のカギ", 'item'),
    'Small Key (Bottom of the Well)':                           (["解除のツール", "扉開け", "ロックピック"], "井戸下のカギ", 'item'),
    'Small Key (Gerudo Training Ground)':                       (["解除のツール", "扉開け", "ロックピック"], "修練場のカギ", 'item'),
    'Small Key (Ganons Castle)':                                (["解除のツール", "扉開け", "ロックピック"], "ガノンのカギ", 'item'),
    'Small Key (Thieves Hideout)':                              (["釈放カード"], "牢屋のカギ", 'item'),
    'KeyError':                                                 (["けつばん", "なぞのもの"], "エラー（レポートして）", 'item'),
    'Arrows (5)':                                               (["少しの矢"], "矢（５本）", 'item'),
    'Arrows (10)':                                              (["いくつかの矢"], "矢（１０本）", 'item'),
    'Arrows (30)':                                              (["多くの矢"], "矢（３０本）", 'item'),
    'Bombs (5)':                                                (["少しのバクダン"], "バクダン（５コ）", 'item'),
    'Bombs (10)':                                               (["いくつかのバクダン"], "バクダン（１０コ）", 'item'),
    'Bombs (20)':                                               (["多くのバクダン"], "バクダン（２０コ）", 'item'),
    'Ice Trap':                                                 (["ガノンの贈り物", "ＦＯＯＬ"], "アイストラップ", 'item'),
    'Magic Bean':                                               (["不思議なマメ"], "魔法のマメ", 'item'),
    'Magic Bean Pack':                                          (["不思議なマメ"], "魔法のマメ", 'item'),
    'Bombchus':                                                 (["ネズミ", "壁バクダン", "走るバクダン"], "ボムチュウ", 'item'),
    'Bombchus (5)':                                             (["少しのネズミ", "少しの動バクダン", "少しの走バクダン"], "ボムチュウ（５コ）", 'item'),
    'Bombchus (10)':                                            (["いくつかのネズミ", "いくつかの動バクダン", "いくつかの走バクダン"], "ボムチュウ（１０コ）", 'item'),
    'Bombchus (20)':                                            (["多くのネズミ", "多くの動バクダン", "多くの走バクダン"], "ボムチュウ（２０コ）", 'item'),
    'Deku Nuts (5)':                                            (["いくつかの実", "いくつかの目くらまし"], "デクの実（５コ）", 'item'),
    'Deku Nuts (10)':                                           (["多くの実", "多くの目くらまし"], "デクの実（１０コ）", 'item'),
    'Deku Seeds (30)':                                          (["カタパルトの玉", "多くの種"], "デクの種（３０コ）", 'item'),
    'Gold Skulltula Token':                                     (["破壊の証拠", "クモの金", "クモの残し物", "呪いの欠片"], "トークン", 'item'),

    'ZR Frogs Ocarina Game':                                       (["C両生類の合唱Cは", "C聖歌隊の歌Cは", "C歌のフィナーレCは"], "Cカエルの歌Cは", 'always'),
    'KF Links House Cow':                                          ("C乗馬の恵みCは", "C障害物走後の牛Cは", 'always'),

    'Song from Ocarina of Time':                                   ("C時の歌Cは", None, ['song', 'sometimes']),
    'Song from Composers Grave':                                   (["C墓のリーデッドCは", "C作曲家の兄弟Cは"], None, ['song', 'sometimes']),
    'Sheik in Forest':                                             ("C牧草地でC シークは", None, ['song', 'sometimes']),
    'Sheik at Temple':                                             ("シークはC時の神殿Cで", None, ['song', 'sometimes']),
    'Sheik in Crater':                                             ("C火口の歌Cは", None, ['song', 'sometimes']),
    'Sheik in Ice Cavern':                                         ("C氷の洞窟Cは", None, ['song', 'sometimes']),
    'Sheik in Kakariko':                                           ("C荒廃した村Cは", None, ['song', 'sometimes']),
    'Sheik at Colossus':                                           ("C荒れ地の先Cでは", None, ['song', 'sometimes']),

    'Market 10 Big Poes':                                          ("CゴーストハンターCは", "C１０匹のビッグポーCを売ると", ['overworld', 'sometimes']),
    'Deku Theater Skull Mask':                                     ("Cドクロのお面の評価Cは", None, ['overworld', 'sometimes']),
    'Deku Theater Mask of Truth':                                  ("Cウソ無きお面の世論Cは", "Cまことのお面の評価Cは", ['overworld', 'sometimes']),
    'HF Ocarina of Time Item':                                     ("Cゼルダの投げるお宝Cは", None, ['overworld', 'sometimes']),
    'DMT Biggoron':                                                ("CダイゴロンCの持つものは", None, ['overworld', 'sometimes']),
    'Kak 50 Gold Skulltula Reward':                                (["C５０個の虫Cは", "C５０個のクモの魂Cは", "C５０匹のクモCは"], "C５０個のトークンCは", ['overworld', 'sometimes']),
    'Kak 40 Gold Skulltula Reward':                                (["C４０個の虫Cは", "C４０個のクモの魂Cは", "C４０匹のクモCは"], "C４０個のトークンCは", ['overworld', 'sometimes']),
    'Kak 30 Gold Skulltula Reward':                                (["C３０個の虫Cは", "C３０個のクモの魂Cは", "C３０匹のクモCは"], "C３０個のトークンCは", ['overworld', 'sometimes']),
    'Kak 20 Gold Skulltula Reward':                                (["C２０個の虫Cは", "C２０個のクモの魂Cは", "C２０匹のクモCは"], "C２０個のトークンCは", ['overworld', 'sometimes']),
    'Kak Anju as Child':                                           (["C鳥の捕獲Cは"], "Cコッコの捕獲Cは", ['overworld', 'sometimes']),
    'GC Darunias Joy':                                             ("C踊るゴロンCは", "CダルニアCは", ['overworld', 'sometimes']),
    'LW Skull Kid':                                                ("CスタルキッドCは", None, ['overworld', 'sometimes']),
    'LH Sun':                                                      ("C太陽Cを見つめると", "C太陽Cを撃つと", ['overworld', 'sometimes']),
    'Market Treasure Chest Game Reward':                           (["C賭けに勝つCと", "C１／３２の確立Cで"], "C宝箱屋Cは", ['overworld', 'sometimes']),
    'GF HBA 1500 Points':                                          ("CやぶさめCの特賞は", "Cやぶさめで１５００点C取ると", ['overworld', 'sometimes']),
    'Graveyard Heart Piece Grave Chest':                           ("C太陽の歌Cを穴で奏でると", None, ['overworld', 'sometimes']),
    'GC Maze Left Chest':                                          ("CゴロンシティCの錆びたスイッチは", None, ['overworld', 'sometimes']),
    'GV Chest':                                                    ("Cゲルドの谷Cの錆びたスイッチは", None, ['overworld', 'sometimes']),
    'GV Cow':                                                      ("Cゲルドの谷の牛Cは", None, ['overworld', 'sometimes']),
    'HC GS Storms Grotto':                                         ("C穴中の壁裏のクモCは", None, ['overworld', 'sometimes']),
    'HF GS Cow Grotto':                                            ("C穴中の巣に隠れたクモCは", None, ['overworld', 'sometimes']),
    'HF Cow Grotto Cow':                                           ("Cクモにまみれた牛Cは", "C穴中の巣に隠れた牛Cは", ['overworld', 'sometimes']),
    'ZF GS Hidden Cave':                                           ("C氷の上のクモCは", None, ['overworld', 'sometimes']),
    'Wasteland Chest':                                             (["C荒れ地の地下Cには", "C砂下の炎Cは"], None, ['overworld', 'sometimes']),
    'Wasteland GS':                                                ("C荒れ地のクモCは", None, ['overworld', 'sometimes']),
    'Graveyard Composers Grave Chest':                             (["C作曲家の炎Cは", "C作曲家の隠した物Cは"], None, ['overworld', 'sometimes']),
    'ZF Bottom Freestanding PoH':                                  ("C氷の下Cは", None, ['overworld', 'sometimes']),
    'GC Pot Freestanding PoH':                                     ("CゴロンのツボCは", None, ['overworld', 'sometimes']),
    'ZD King Zora Thawed':                                         ("C解けた王Cは", "CキングゾーラCは", ['overworld', 'sometimes']),
    'DMC Deku Scrub':                                              ("C火口のアキンドCは", None, ['overworld', 'sometimes']),
    'DMC GS Crate':                                                ("C火口のクモCは", None, ['overworld', 'sometimes']),

    'Deku Tree MQ After Spinning Log Chest':                       ("C木の中の石Cは", "Cデクの樹の石Cは", ['dungeon', 'sometimes']),
    'Deku Tree MQ GS Basement Graves Room':                        ("C木の中のクモCは", "Cデクの樹のクモCは", ['dungeon', 'sometimes']),
    'Dodongos Cavern MQ GS Song of Time Block Room':               ("C洞窟の石の下のクモCは", "Cドドンゴの石の下のクモCは", ['dungeon', 'sometimes']),
    'Jabu Jabus Belly Boomerang Chest':                            ("C神の中の針Cは", "Cジャブジャブの飲み込んだ針Cは", ['dungeon', 'sometimes']),
    'Jabu Jabus Belly MQ GS Invisible Enemies Room':               ("C神の影に囲まれたクモCは", "Cジャブジャブの影に囲まれたクモCは", ['dungeon', 'sometimes']),
    'Jabu Jabus Belly MQ Cow':                                     ("C神の中の牛Cは", "Cジャブジャブの中の牛Cは", ['dungeon', 'sometimes']),
    'Fire Temple Scarecrow Chest':                                 ("C火口のカカシCは", "C炎の神殿のカカシCは", ['dungeon', 'sometimes']),
    'Fire Temple Megaton Hammer Chest':                            ("C火口の踊り子Cは", "C炎の神殿の踊り子Cは", ['dungeon', 'sometimes']),
    'Fire Temple MQ Chest On Fire':                                ("C火口の踊り子Cは", "C炎の神殿の踊り子Cは", ['dungeon', 'sometimes']),
    'Fire Temple MQ GS Skull On Fire':                             ("C火口の石の下のクモCは", "C炎の神殿の石下のクモCは", ['dungeon', 'sometimes']),
    'Water Temple River Chest':                                    ("C池下の川の先Cには", "C水の神殿の川の先Cには", ['dungeon', 'sometimes']),
    'Water Temple Boss Key Chest':                                 ("C池下の回転岩Cをよけると", "C水の神殿の回転岩Cをよけると", ['dungeon', 'sometimes']),
    'Water Temple GS Behind Gate':                                 ("C池下の門に隠れるクモCは", "C水の神殿の門に隠れるクモCは", ['dungeon', 'sometimes']),
    'Water Temple MQ Freestanding Key':                            ("C池下の箱Cに隠れるのは", "C水の神殿の箱Cに隠れるのは", ['dungeon', 'sometimes']),
    'Water Temple MQ GS Freestanding Key Area':                    ("C池下に閉じ込められたクモCは", "C水の神殿の捕われクモC は", ['dungeon', 'sometimes']),
    'Water Temple MQ GS Triple Wall Torch':                        ("C池下の門に隠れるクモCは", "C水の神殿の門に隠れるクモCは", ['dungeon', 'sometimes']),
    'Gerudo Training Ground Underwater Silver Rupee Chest':        (["C沈んだ銀ルピーCを得た者は", "C水中の銀を集めるC者は"], None, ['dungeon', 'sometimes']),
    'Gerudo Training Ground MQ Underwater Silver Rupee Chest':     (["C沈んだ銀ルピーCを得た者は", "C水中の銀を集めるC者は"], None, ['dungeon', 'sometimes']),
    'Gerudo Training Ground Maze Path Final Chest':                ("C盗人の最後の贈り物Cは", None, ['dungeon', 'sometimes']),
    'Gerudo Training Ground MQ Ice Arrows Chest':                  ("C盗人の最後の贈り物Cは", None, ['dungeon', 'sometimes']),
    'Bottom of the Well Lens of Truth Chest':                      (["C井戸下で掴むモノCは", "C井戸に住む地獄の住民Cは"], "C井戸のデドハンドCは", ['dungeon', 'sometimes']),
    'Bottom of the Well MQ Compass Chest':                         (["C井戸下で掴むモノCは", "C井戸に住む地獄の住民Cは"], "C井戸のデドハンドCは", ['dungeon', 'sometimes']),
    'Spirit Temple Silver Gauntlets Chest':                        ("Cナボールの探し出した宝Cは", "C巨人の右手Cには", ['dungeon', 'sometimes']),
    'Spirit Temple Mirror Shield Chest':                           ("C巨人の左手Cには", None, ['dungeon', 'sometimes']),
    'Spirit Temple MQ Child Hammer Switch Chest':                  ("C神殿内のスイッチCは", "C魂の神殿のスイッチCは", ['dungeon', 'sometimes']),
    'Spirit Temple MQ Symphony Room Chest':                        ("C巨人への情けCは", "C魂の神殿への情けCは", ['dungeon', 'sometimes']),
    'Spirit Temple MQ GS Symphony Room':                           ("C巨人のクモへの同情Cは", "C魂の神殿のクモへの同情Cは", ['dungeon', 'sometimes']),
    'Shadow Temple Invisible Floormaster Chest':                   ("C透明な迷路Cは", None, ['dungeon', 'sometimes']),
    'Shadow Temple MQ Bomb Flower Chest':                          ("C透明な迷路Cは", None, ['dungeon', 'sometimes']),

    'KF Kokiri Sword Chest':                                       ("Cコキリの隠した宝Cは", None, 'exclude'),
    'KF Midos Top Left Chest':                                     ("CコキリのリーダーがC隠したのは", "Cミドの家Cには", 'exclude'),
    'KF Midos Top Right Chest':                                    ("CコキリのリーダーがC隠したのは", "Cミドの家Cには", 'exclude'),
    'KF Midos Bottom Left Chest':                                  ("CコキリのリーダーがC隠したのは", "Cミドの家Cには", 'exclude'),
    'KF Midos Bottom Right Chest':                                 ("CコキリのリーダーがC隠したのは", "Cミドの家Cには", 'exclude'),
    'Graveyard Shield Grave Chest':                                ("C兵士の墓に眠る宝Cは", None, 'exclude'),
    'DMT Chest':                                                   ("C登山道の壁Cには", None, 'exclude'),
    'GC Maze Right Chest':                                         ("CゴロンシティCでの爆破は", None, 'exclude'),
    'GC Maze Center Chest':                                        ("CゴロンシティCでの爆破は", None, 'exclude'),
    'ZD Chest':                                                    ("C滝先の炎Cは", None, 'exclude'),
    'Graveyard Hookshot Chest':                                    ("Cレース霊Cの宝は", "C霊ダンペイCは", 'exclude'),
    'GF Chest':                                                    ("C砂漠のアーチCの上には", None, 'exclude'),
    'Kak Redead Grotto Chest':                                     ("C穴中のゾンビCが守るのは", None, 'exclude'),
    'SFM Wolfos Grotto Chest':                                     ("C穴中の狼Cが守るのは", None, 'exclude'),
    'HF Near Market Grotto Chest':                                 ("C平原の橋近くの穴Cには", None, 'exclude'),
    'HF Southeast Grotto Chest':                                   ("C平原の木の間の穴Cには", None, 'exclude'),
    'HF Open Grotto Chest':                                        ("C平原の穴Cには", None, 'exclude'),
    'Kak Open Grotto Chest':                                       ("C街の穴Cには", None, 'exclude'),
    'ZR Open Grotto Chest':                                        ("Cゾーラ川の穴Cには", None, 'exclude'),
    'KF Storms Grotto Chest':                                      ("C森村の嵐穴Cには", None, 'exclude'),
    'LW Near Shortcuts Grotto Chest':                              ("C迷路の穴Cには", None, 'exclude'),
    'DMT Storms Grotto Chest':                                     ("C登山道の嵐穴Cには", None, 'exclude'),
    'DMC Upper Grotto Chest':                                      ("C火口の穴Cには", None, 'exclude'),

    'ToT Light Arrows Cutscene':                                   ("C姫の最後のプレゼントCは", None, 'exclude'),
    'LW Gift from Saria':                                          ("Cサリアの土産Cは", None, 'exclude'),
    'ZF Great Fairy Reward':                                       ("C風の大妖精Cは", None, 'exclude'),
    'HC Great Fairy Reward':                                       ("C炎の大妖精Cは", None, 'exclude'),
    'Colossus Great Fairy Reward':                                 ("C愛の大妖精Cは", None, 'exclude'),
    'DMT Great Fairy Reward':                                      ("C魔法の大妖精Cは", None, 'exclude'),
    'DMC Great Fairy Reward':                                      ("C魔法の大妖精Cは", None, 'exclude'),
    'OGC Great Fairy Reward':                                      ("C力の大妖精Cは", None, 'exclude'),

    'Song from Impa':                                              ("C城奥でCインパは", None, 'exclude'),
    'Song from Malon':                                             ("C農娘Cの歌は", None, 'exclude'),
    'Song from Saria':                                             ("C森の奥でCサリアは", None, 'exclude'),
    'Song from Windmill':                                          ("C風車の男Cは", None, 'exclude'),

    'HC Malon Egg':                                                ("C父探す娘Cは", None, 'exclude'),
    'HC Zeldas Letter':                                            ("C城にいる姫Cは", None, 'exclude'),
    'ZD Diving Minigame':                                          ("C持続しない仕事Cの報酬は", "CゾーラのルピーCを集めた者は", 'exclude'),
    'LH Child Fishing':                                            ("C少年の釣りCは", None, 'exclude'),
    'LH Adult Fishing':                                            ("C青年の釣りCは", None, 'exclude'),
    'LH Lab Dive':                                                 ("C潜水実験Cでの報酬は", None, 'exclude'),
    'GC Rolling Goron as Adult':                                   ("C心理相談Cは", "C子ゴロンをなだめるC人には", 'exclude'),
    'Market Bombchu Bowling First Prize':                          ("Cボウリングの景品Cは", None, 'exclude'),
    'Market Bombchu Bowling Second Prize':                         ("Cボウリングの景品Cは", None, 'exclude'),
    'Market Lost Dog':                                             ("C犬好きCには", "Cリチャードを助けるC人には", 'exclude'),
    'LW Ocarina Memory Game':                                      (["C譜面合わせCは", "C歌い合わせCは"], "C迷いの森での演奏Cは", 'exclude'),
    'Kak 10 Gold Skulltula Reward':                                (["C１０個の虫Cは", "C１０個のクモの魂Cは", "C１０匹のクモCは"], "C１０個のトークンCは", 'exclude'),
    'Kak Man on Roof':                                             ("C屋根で寛ぐ人Cからは", None, 'exclude'),
    'ZR Magic Bean Salesman':                                      ("C信号の売人Cは", "Cマメ売りCは", 'exclude'),
    'ZR Frogs in the Rain':                                        ("C嵐の蛙Cからは", None, 'exclude'),
    'GF HBA 1000 Points':                                          ("Cやぶさめで１０００点C取ると", None, 'exclude'),
    'Market Shooting Gallery Reward':                              ("C少年の的当てCは", None, 'exclude'),
    'Kak Shooting Gallery Reward':                                 ("C青年の的当てCは", None, 'exclude'),
    'LW Target in Woods':                                          ("C森の的当てCは", None, 'exclude'),
    'Kak Anju as Adult':                                           ("C鳥飼がC青年に託すのは", None, 'exclude'),
    'LLR Talons Chickens':                                         ("CスーパーコッコCを当てた人は", None, 'exclude'),
    'GC Rolling Goron as Child':                                   ("C回るゴロンCを止めると", None, 'exclude'),
    'LH Underwater Item':                                          ("C湖に沈む宝Cは", None, 'exclude'),
    'GF Gerudo Membership Card':                                   ("C捕われた大工Cを助けた人には", None, 'exclude'),
    'Wasteland Bombchu Salesman':                                  ("C布売りCは", None, 'exclude'),

    'Kak Impas House Freestanding PoH':                            ("C家に囚われているCのは", None, 'exclude'),
    'HF Tektite Grotto Freestanding PoH':                          ("C穴の水の底Cには", None, 'exclude'),
    'Kak Windmill Freestanding PoH':                               ("C風車Cには", None, 'exclude'),
    'Graveyard Dampe Race Freestanding PoH':                       ("Cレース霊Cの宝は", "C霊ダンペイCは", 'exclude'),
    'LLR Freestanding PoH':                                        ("C牧場のサイロCには", None, 'exclude'),
    'Graveyard Freestanding PoH':                                  ("C墓場の箱Cには", None, 'exclude'),
    'Graveyard Dampe Gravedigging Tour':                           ("C墓守が掘るCのは", None, 'exclude'),
    'ZR Near Open Grotto Freestanding PoH':                        ("C川の柱の上Cには", None, 'exclude'),
    'ZR Near Domain Freestanding PoH':                             ("C滝近くの川沿いCには", None, 'exclude'),
    'LH Freestanding PoH':                                         ("C研究所の屋根Cには", None, 'exclude'),
    'ZF Iceberg Freestanding PoH':                                 ("C氷に浮かぶCのは", None, 'exclude'),
    'GV Waterfall Freestanding PoH':                               ("Cゲルドの滝の奥Cには", None, 'exclude'),
    'GV Crate Freestanding PoH':                                   ("C谷の箱Cには", None, 'exclude'),
    'Colossus Freestanding PoH':                                   ("C石のアーチの上Cには", None, 'exclude'),
    'DMT Freestanding PoH':                                        ("C山の洞窟の入口Cには", None, 'exclude'),
    'DMC Wall Freestanding PoH':                                   ("C火山の壁Cには", None, 'exclude'),
    'DMC Volcano Freestanding PoH':                                ("C火山灰に隠れるCのは", None, 'exclude'),
    'GF North F1 Carpenter':                                       ("Cアジトの看守Cを倒す人には", None, 'exclude'),
    'GF North F2 Carpenter':                                       ("Cアジトの看守Cを倒す人には", None, 'exclude'),
    'GF South F1 Carpenter':                                       ("Cアジトの看守Cを倒す人には", None, 'exclude'),
    'GF South F2 Carpenter':                                       ("Cアジトの看守Cを倒す人には", None, 'exclude'),

    'Deku Tree Map Chest':                                         ("Cデクの樹の中心Cには", None, 'exclude'),
    'Deku Tree Slingshot Chest':                                   ("デクの樹のCアキンドの近くCには", None, 'exclude'),
    'Deku Tree Slingshot Room Side Chest':                         ("デクの樹のCアキンドの近くCには", None, 'exclude'),
    'Deku Tree Compass Chest':                                     ("デクの樹のC木の柱Cの先には", None, 'exclude'),
    'Deku Tree Compass Room Side Chest':                           ("デクの樹のC木の柱Cの先には", None, 'exclude'),
    'Deku Tree Basement Chest':                                    ("デクの樹でC糸に隠れるCのは", None, 'exclude'),

    'Deku Tree MQ Map Chest':                                      ("Cデクの樹の中心Cには", None, 'exclude'),
    'Deku Tree MQ Compass Chest':                                  ("デクの樹のCクモが守る宝Cは", None, 'exclude'),
    'Deku Tree MQ Slingshot Chest':                                ("デクの樹のC木の柱Cの先には", None, 'exclude'),
    'Deku Tree MQ Slingshot Room Back Chest':                      ("デクの樹のC木の柱Cの先には", None, 'exclude'),
    'Deku Tree MQ Basement Chest':                                 ("デクの樹でC糸に隠れるCのは", None, 'exclude'),
    'Deku Tree MQ Before Spinning Log Chest':                      ("Cデクの樹の炎Cの先は", None, 'exclude'),

    'Dodongos Cavern Boss Room Chest':                             ("Cドドンゴの上Cには", None, 'exclude'),

    'Dodongos Cavern Map Chest':                                   ("C洞窟の壁Cには", None, 'exclude'),
    'Dodongos Cavern Compass Chest':                               ("C洞窟の銅像Cの守るのは", None, 'exclude'),
    'Dodongos Cavern Bomb Flower Platform Chest':                  ("C洞窟の迷路の上Cには", None, 'exclude'),
    'Dodongos Cavern Bomb Bag Chest':                              ("C二匹目のトカゲCの持つものは", None, 'exclude'),
    'Dodongos Cavern End of Bridge Chest':                         ("C洞窟の橋先Cにあるのは", None, 'exclude'),

    'Dodongos Cavern MQ Map Chest':                                ("C洞窟の壁Cには", None, 'exclude'),
    'Dodongos Cavern MQ Bomb Bag Chest':                           ("C洞窟の浮く床Cの上には", None, 'exclude'),
    'Dodongos Cavern MQ Compass Chest':                            ("C洞窟の炎吐くトカゲCは", None, 'exclude'),
    'Dodongos Cavern MQ Larvae Room Chest':                        ("C洞窟の子クモCは", None, 'exclude'),
    'Dodongos Cavern MQ Torch Puzzle Room Chest':                  ("C洞窟の迷路の上Cには", None, 'exclude'),
    'Dodongos Cavern MQ Under Grave Chest':                        ("C洞窟の岩下Cには", None, 'exclude'),

    'Jabu Jabus Belly Map Chest':                                  ("C叩くと固まるモノの先Cには", None, 'exclude'),
    'Jabu Jabus Belly Compass Chest':                              ("C泡Cの先には", None, 'exclude'),

    'Jabu Jabus Belly MQ First Room Side Chest':                   ("C食べられた牛Cは", None, 'exclude'),
    'Jabu Jabus Belly MQ Map Chest':                               (["C弾け石Cは", "C爆破岩Cには"], "C牛近くの岩Cには", 'exclude'),
    'Jabu Jabus Belly MQ Second Room Lower Chest':                 ("C針エレベーターの上Cには", None, 'exclude'),
    'Jabu Jabus Belly MQ Compass Chest':                           ("Cおぼれた牛Cは", None, 'exclude'),
    'Jabu Jabus Belly MQ Second Room Upper Chest':                 ("C解剖Cの先には", None, 'exclude'),
    'Jabu Jabus Belly MQ Basement Near Switches Chest':            ("C二匹の食われた牛Cには", None, 'exclude'),
    'Jabu Jabus Belly MQ Basement Near Vines Chest':               ("C二匹の食われた牛Cには", None, 'exclude'),
    'Jabu Jabus Belly MQ Near Boss Chest':                         ("C食われた最後の牛Cには", None, 'exclude'),
    'Jabu Jabus Belly MQ Falling Like Like Room Chest':            ("C落ちてくる物に守られた牛Cは", None, 'exclude'),
    'Jabu Jabus Belly MQ Boomerang Room Small Chest':              ("C胃の中の針の先Cには", None, 'exclude'),
    'Jabu Jabus Belly MQ Boomerang Chest':                         ("C胃の中の針の先Cには", None, 'exclude'),

    'Forest Temple First Room Chest':                              ("C森の神殿の木Cには", None, 'exclude'),
    'Forest Temple First Stalfos Chest':                           ("C落ちる天井下の敵Cを倒すと", None, 'exclude'),
    'Forest Temple Well Chest':                                    ("C森の神殿に沈む宝Cは", None, 'exclude'),
    'Forest Temple Map Chest':                                     ("森の神殿のC青バブルCは", None, 'exclude'),
    'Forest Temple Raised Island Courtyard Chest':                 ("森の神殿のC孤島Cには", None, 'exclude'),
    'Forest Temple Falling Ceiling Room Chest':                    ("C落ちてくる白黒タイルCの下には", None, 'exclude'),
    'Forest Temple Eye Switch Chest':                              ("森の神殿でC石Cに囲まれているのは", None, 'exclude'),
    'Forest Temple Boss Key Chest':                                ("Cねじれた道Cの先には", None, 'exclude'),
    'Forest Temple Floormaster Chest':                             ("C森で影が守るCのは", None, 'exclude'),
    'Forest Temple Bow Chest':                                     ("森の神殿のCスタルフォスCは", None, 'exclude'),
    'Forest Temple Red Poe Chest':                                 ("CジョオCは", "C赤い霊Cは", 'exclude'),
    'Forest Temple Blue Poe Chest':                                ("CベスCは", "C青い霊Cは", 'exclude'),
    'Forest Temple Basement Chest':                                ("森の神殿のCスタルウォールCは", None, 'exclude'),

    'Forest Temple MQ First Room Chest':                           ("C森の神殿の木Cには", None, 'exclude'),
    'Forest Temple MQ Wolfos Chest':                               ("C落ちる天井下の敵Cを倒すと", None, 'exclude'),
    'Forest Temple MQ Bow Chest':                                  ("森の神殿のCスタルフォスCは", None, 'exclude'),
    'Forest Temple MQ Raised Island Courtyard Lower Chest':        ("森の神殿のC孤島Cには", None, 'exclude'),
    'Forest Temple MQ Raised Island Courtyard Upper Chest':        ("森の神殿のC中庭の上Cには", None, 'exclude'),
    'Forest Temple MQ Well Chest':                                 ("C森の神殿に沈む宝Cは", None, 'exclude'),
    'Forest Temple MQ Map Chest':                                  ("CジョオCは", "C赤い霊Cは", 'exclude'),
    'Forest Temple MQ Compass Chest':                              ("CベスCは", "C青い霊Cは", 'exclude'),
    'Forest Temple MQ Falling Ceiling Room Chest':                 ("C落ちてくる白黒タイルCの下には", None, 'exclude'),
    'Forest Temple MQ Basement Chest':                             ("森の神殿のCスタルウォールCは", None, 'exclude'),
    'Forest Temple MQ Redead Chest':                               ("森の神殿のCリーデッドCは", None, 'exclude'),
    'Forest Temple MQ Boss Key Chest':                             ("Cねじれた道Cの先には", None, 'exclude'),

    'Fire Temple Near Boss Chest':                                 ("C竜の近くCには", None, 'exclude'),
    'Fire Temple Flare Dancer Chest':                              ("Cトーテム裏のフレアダンサーCは", None, 'exclude'),
    'Fire Temple Boss Key Chest':                                  ("Cトーテム先の牢獄Cには", None, 'exclude'),
    'Fire Temple Big Lava Room Blocked Door Chest':                ("C溶岩先で爆破Cすると", None, 'exclude'),
    'Fire Temple Big Lava Room Lower Open Door Chest':             ("C溶岩近くで捕われたゴロンCは", None, 'exclude'),
    'Fire Temple Boulder Maze Lower Chest':                        ("C迷路のゴロンCは", None, 'exclude'),
    'Fire Temple Boulder Maze Upper Chest':                        ("C迷路のゴロンCは", None, 'exclude'),
    'Fire Temple Boulder Maze Side Room Chest':                    ("C迷路のゴロンCは", None, 'exclude'),
    'Fire Temple Boulder Maze Shortcut Chest':                     ("炎の神殿のC行きどまりCには", None, 'exclude'),
    'Fire Temple Map Chest':                                       ("炎の神殿のC鉄格子の中Cには", None, 'exclude'),
    'Fire Temple Compass Chest':                                   ("炎の神殿のC迷路Cには", None, 'exclude'),
    'Fire Temple Highest Goron Chest':                             ("C頂上のゴロンCは", None, 'exclude'),

    'Fire Temple MQ Near Boss Chest':                              ("C竜の近くCには", None, 'exclude'),
    'Fire Temple MQ Megaton Hammer Chest':                         ("C溶岩下のフレアダンサーCは", None, 'exclude'),
    'Fire Temple MQ Compass Chest':                                ("炎の神殿のC行きどまりCには", None, 'exclude'),
    'Fire Temple MQ Lizalfos Maze Lower Chest':                    ("C迷路の箱Cには", None, 'exclude'),
    'Fire Temple MQ Lizalfos Maze Upper Chest':                    ("C迷路の箱Cには", None, 'exclude'),
    'Fire Temple MQ Map Room Side Chest':                          ("炎の神殿のC落ちるモノCは", None, 'exclude'),
    'Fire Temple MQ Map Chest':                                    ("炎の神殿奥でCハンマーCを使うと", None, 'exclude'),
    'Fire Temple MQ Boss Key Chest':                               ("C溶岩を照らすとC", None, 'exclude'),
    'Fire Temple MQ Big Lava Room Blocked Door Chest':             ("C溶岩先で爆破Cすると", None, 'exclude'),
    'Fire Temple MQ Lizalfos Maze Side Room Chest':                ("C迷路のゴロンCは", None, 'exclude'),
    'Fire Temple MQ Freestanding Key':                             ("C石の下に隠れるCのは", None, 'exclude'),

    'Water Temple Map Chest':                                      ("水の神殿のC回転針の近くCには", None, 'exclude'),
    'Water Temple Compass Chest':                                  ("水の神殿のC回転針の近くCには", None, 'exclude'),
    'Water Temple Torches Chest':                                  ("水の神殿内でC炎Cは", None, 'exclude'),
    'Water Temple Dragon Chest':                                   ("水の神殿のC蛇の宝Cは", None, 'exclude'),
    'Water Temple Central Bow Target Chest':                       ("水の神殿のC目くらましCは", None, 'exclude'),
    'Water Temple Central Pillar Chest':                           ("C水の神殿の奥Cには", None, 'exclude'),
    'Water Temple Cracked Wall Chest':                             ("水の神殿のCヒビの奥Cには", None, 'exclude'),
    'Water Temple Longshot Chest':                                 (["C自分と見つめればC", "C影Cが守るのは"], "CダークリンクCは", 'exclude'),

    'Water Temple MQ Central Pillar Chest':                        ("C水の神殿の奥Cには", None, 'exclude'),
    'Water Temple MQ Boss Key Chest':                              ("水の神殿内でC炎Cは", None, 'exclude'),
    'Water Temple MQ Longshot Chest':                              ("水の神殿のCヒビの奥Cには", None, 'exclude'),
    'Water Temple MQ Compass Chest':                               ("水の神殿内でC炎Cは", None, 'exclude'),
    'Water Temple MQ Map Chest':                                   ("水の神殿のC兵士Cは", None, 'exclude'),

    'Spirit Temple Child Bridge Chest':                            ("魂の神殿のC緑炎Cの近くには", None, 'exclude'),
    'Spirit Temple Child Early Torches Chest':                     ("魂の神殿のC鉄格子の中Cには", None, 'exclude'),
    'Spirit Temple Compass Chest':                                 ("魂の神殿のC砂場Cには", None, 'exclude'),
    'Spirit Temple Early Adult Right Chest':                       ("魂の神殿でC銀ルピーCを集めると", None, 'exclude'),
    'Spirit Temple First Mirror Left Chest':                       ("魂の神殿でC光を照らすCと", None, 'exclude'),
    'Spirit Temple First Mirror Right Chest':                      ("魂の神殿でC光を照らすCと", None, 'exclude'),
    'Spirit Temple Map Chest':                                     ("魂の神殿のC巨大な銅像Cの前には", None, 'exclude'),
    'Spirit Temple Child Climb North Chest':                       ("C魂の神殿のトカゲCが守るのは", None, 'exclude'),
    'Spirit Temple Child Climb East Chest':                        ("C魂の神殿のトカゲCが守るのは", None, 'exclude'),
    'Spirit Temple Sun Block Room Chest':                          ("Cビーモス近くの松明Cを灯すと", None, 'exclude'),
    'Spirit Temple Statue Room Hand Chest':                        ("魂の神殿のC巨大な銅像Cには", None, 'exclude'),
    'Spirit Temple Statue Room Northeast Chest':                   ("魂の神殿のC巨大な銅像Cの側には", None, 'exclude'),
    'Spirit Temple Near Four Armos Chest':                         ("魂の神殿のC銅像に光Cを照らすと", None, 'exclude'),
    'Spirit Temple Hallway Right Invisible Chest':                 ("魂の神殿でC真実の目Cにより", None, 'exclude'),
    'Spirit Temple Hallway Left Invisible Chest':                  ("魂の神殿でC真実の目Cにより", None, 'exclude'),
    'Spirit Temple Boss Key Chest':                                ("魂の神殿のC炎の中Cには", None, 'exclude'),
    'Spirit Temple Topmost Chest':                                 ("魂の神殿でC光Cを照らす者には", None, 'exclude'),

    'Spirit Temple MQ Entrance Front Left Chest':                  ("C魂の神殿Cには", None, 'exclude'),
    'Spirit Temple MQ Entrance Back Right Chest':                  ("魂の神殿のC柱Cには", None, 'exclude'),
    'Spirit Temple MQ Entrance Front Right Chest':                 ("魂の神殿でC銀ルピーCを集めると", None, 'exclude'),
    'Spirit Temple MQ Entrance Back Left Chest':                   ("魂の神殿でC真実の目Cにより", None, 'exclude'),
    'Spirit Temple MQ Map Chest':                                  ("魂の神殿のC炎の中Cには", None, 'exclude'),
    'Spirit Temple MQ Map Room Enemy Chest':                       ("C魂の神殿Cには", None, 'exclude'),
    'Spirit Temple MQ Child Climb North Chest':                    ("魂の神殿でC光を照らすCと", None, 'exclude'),
    'Spirit Temple MQ Child Climb South Chest':                    ("C魂の神殿Cには", None, 'exclude'),
    'Spirit Temple MQ Compass Chest':                              ("C巨人の目Cをくらますと", None, 'exclude'),
    'Spirit Temple MQ Statue Room Lullaby Chest':                  ("C王家の歌で巨人Cを覚ますと", None, 'exclude'),
    'Spirit Temple MQ Statue Room Invisible Chest':                ("魂の神殿でC真実の目Cにより", None, 'exclude'),
    'Spirit Temple MQ Silver Block Hallway Chest':                 ("魂の神殿でC見え隠れCするのは", None, 'exclude'),
    'Spirit Temple MQ Sun Block Room Chest':                       ("C魂の迷路に光Cを照らすと", None, 'exclude'),
    'Spirit Temple MQ Leever Room Chest':                          ("魂の神殿のC砂場Cには", None, 'exclude'),
    'Spirit Temple MQ Beamos Room Chest':                          ("魂の神殿のC岩の先Cには", None, 'exclude'),
    'Spirit Temple MQ Chest Switch Chest':                         ("C一石二鳥なチェストCには", None, 'exclude'),
    'Spirit Temple MQ Boss Key Chest':                             ("C岩で遮られた光の先Cには", None, 'exclude'),
    'Spirit Temple MQ Mirror Puzzle Invisible Chest':              ("魂の神殿でC光Cを照らす者には", None, 'exclude'),

    'Shadow Temple Map Chest':                                     ("闇の神殿でC真実の目Cにより", None, 'exclude'),
    'Shadow Temple Hover Boots Chest':                             (["C闇で掴むモノCは", "C闇に住む地獄の住民Cは"], "C闇の神殿のデドハンドCは", 'exclude'),
    'Shadow Temple Compass Chest':                                 ("C真実の目で見えるギブドCは", None, 'exclude'),
    'Shadow Temple Early Silver Rupee Chest':                      ("C回る鎌Cが守るのは", None, 'exclude'),
    'Shadow Temple Invisible Blades Visible Chest':                ("C見えぬ刃Cが守るのは", None, 'exclude'),
    'Shadow Temple Invisible Blades Invisible Chest':              ("C見えぬ刃Cが守るのは", None, 'exclude'),
    'Shadow Temple Falling Spikes Lower Chest':                    ("C落ちる針Cが守るのは", None, 'exclude'),
    'Shadow Temple Falling Spikes Upper Chest':                    ("C落ちる針Cが守るのは", None, 'exclude'),
    'Shadow Temple Falling Spikes Switch Chest':                   ("C落ちる針Cが守るのは", None, 'exclude'),
    'Shadow Temple Invisible Spikes Chest':                        ("C見えぬ針Cが守るのは", None, 'exclude'),
    'Shadow Temple Wind Hint Chest':                               ("C死人の守る見えぬ物Cは", None, 'exclude'),
    'Shadow Temple After Wind Enemy Chest':                        ("C船守るギブドCが隠すのは", None, 'exclude'),
    'Shadow Temple After Wind Hidden Chest':                       ("C船守るギブドCが隠すのは", None, 'exclude'),
    'Shadow Temple Spike Walls Left Chest':                        ("C火球に飲み込まれる壁Cには", None, 'exclude'),
    'Shadow Temple Boss Key Chest':                                ("C火球に飲み込まれる壁Cには", None, 'exclude'),
    'Shadow Temple Freestanding Key':                              ("C燃える骨Cの中には", None, 'exclude'),

    'Shadow Temple MQ Compass Chest':                              ("闇の神殿でC真実の目Cにより", None, 'exclude'),
    'Shadow Temple MQ Hover Boots Chest':                          ("C闇の神殿のデドハンドCは", None, 'exclude'),
    'Shadow Temple MQ Early Gibdos Chest':                         ("C真実の目で見えるギブドCは", None, 'exclude'),
    'Shadow Temple MQ Map Chest':                                  ("C回る鎌Cが守るのは", None, 'exclude'),
    'Shadow Temple MQ Beamos Silver Rupees Chest':                 ("闇の神殿でC銀ルピーCを集めると", None, 'exclude'),
    'Shadow Temple MQ Falling Spikes Switch Chest':                ("C落ちる針Cが守るのは", None, 'exclude'),
    'Shadow Temple MQ Falling Spikes Lower Chest':                 ("C落ちる針Cが守るのは", None, 'exclude'),
    'Shadow Temple MQ Falling Spikes Upper Chest':                 ("C落ちる針Cが守るのは", None, 'exclude'),
    'Shadow Temple MQ Invisible Spikes Chest':                     ("C死人の守る見えぬ物Cは", None, 'exclude'),
    'Shadow Temple MQ Boss Key Chest':                             ("C火球に飲み込まれる壁Cには", None, 'exclude'),
    'Shadow Temple MQ Spike Walls Left Chest':                     ("C火球に飲み込まれる壁Cには", None, 'exclude'),
    'Shadow Temple MQ Stalfos Room Chest':                         ("闇の神殿のC台座の近くCには", None, 'exclude'),
    'Shadow Temple MQ Invisible Blades Invisible Chest':           ("C見えぬ刃Cが守るのは", None, 'exclude'),
    'Shadow Temple MQ Invisible Blades Visible Chest':             ("C見えぬ刃Cが守るのは", None, 'exclude'),
    'Shadow Temple MQ Wind Hint Chest':                            ("C死人の守る見えぬ物Cは", None, 'exclude'),
    'Shadow Temple MQ After Wind Hidden Chest':                    ("C船守るギブドCが隠すのは", None, 'exclude'),
    'Shadow Temple MQ After Wind Enemy Chest':                     ("C船守るギブドCが隠すのは", None, 'exclude'),
    'Shadow Temple MQ Near Ship Invisible Chest':                  ("C船近くCには", None, 'exclude'),
    'Shadow Temple MQ Freestanding Key':                           ("C燃える三つの骨Cの奥には", None, 'exclude'),

    'Bottom of the Well Front Left Fake Wall Chest':               ("井戸でC真実の目Cにより", None, 'exclude'),
    'Bottom of the Well Front Center Bombable Chest':              ("井戸のC恐ろしい欠片Cは", None, 'exclude'),
    'Bottom of the Well Right Bottom Fake Wall Chest':             ("井戸でC真実の目Cにより", None, 'exclude'),
    'Bottom of the Well Compass Chest':                            ("井戸のC隠された入口Cは", None, 'exclude'),
    'Bottom of the Well Center Skulltula Chest':                   ("井戸でCクモCが守るのは", None, 'exclude'),
    'Bottom of the Well Back Left Bombable Chest':                 ("井戸のC恐ろしい欠片Cは", None, 'exclude'),
    'Bottom of the Well Invisible Chest':                          ("井戸のC見えぬ手Cは", None, 'exclude'),
    'Bottom of the Well Underwater Front Chest':                   ("C井戸での音楽Cは", None, 'exclude'),
    'Bottom of the Well Underwater Left Chest':                    ("C井戸での音楽Cは", None, 'exclude'),
    'Bottom of the Well Map Chest':                                ("C井戸の底Cには", None, 'exclude'),
    'Bottom of the Well Fire Keese Chest':                         ("井戸のC穴Cを超えた先には", None, 'exclude'),
    'Bottom of the Well Like Like Chest':                          ("井戸のC鉄格子の中Cには", None, 'exclude'),
    'Bottom of the Well Freestanding Key':                         ("井戸のC墓の中Cには", None, 'exclude'),

    'Bottom of the Well MQ Map Chest':                             ("C井戸での音楽Cは", None, 'exclude'),
    'Bottom of the Well MQ Lens of Truth Chest':                   ("井戸でC亡者Cが守るのは", None, 'exclude'),
    'Bottom of the Well MQ Dead Hand Freestanding Key':            ("井戸のC見えぬ手Cは", None, 'exclude'),
    'Bottom of the Well MQ East Inner Room Freestanding Key':      ("井戸のC見えぬ道Cの先には", None, 'exclude'),

    'Ice Cavern Map Chest':                                        ("C吹雪Cに守られているのは", None, 'exclude'),
    'Ice Cavern Compass Chest':                                    ("C氷の壁Cに守られているのは", None, 'exclude'),
    'Ice Cavern Iron Boots Chest':                                 ("氷の洞窟でC獣Cが守るのは", None, 'exclude'),
    'Ice Cavern Freestanding PoH':                                 ("C氷の壁Cに守られているのは", None, 'exclude'),

    'Ice Cavern MQ Iron Boots Chest':                              ("氷の洞窟でC獣Cが守るのは", None, 'exclude'),
    'Ice Cavern MQ Compass Chest':                                 ("C吹雪Cに守られているのは", None, 'exclude'),
    'Ice Cavern MQ Map Chest':                                     ("C氷の壁Cに守られているのは", None, 'exclude'),
    'Ice Cavern MQ Freestanding PoH':                              ("C吹雪Cに守られているのは", None, 'exclude'),

    'Gerudo Training Ground Lobby Left Chest':                     ("C修練場の目Cを射抜くと", None, 'exclude'),
    'Gerudo Training Ground Lobby Right Chest':                    ("C修練場の目Cを射抜くと", None, 'exclude'),
    'Gerudo Training Ground Stalfos Chest':                        ("修練場のC砂場Cで守られるのは", None, 'exclude'),
    'Gerudo Training Ground Beamos Chest':                         ("修練場でCトカゲCが守るのは", None, 'exclude'),
    'Gerudo Training Ground Hidden Ceiling Chest':                 ("修練場でC真実の目Cにより", None, 'exclude'),
    'Gerudo Training Ground Maze Path First Chest':                ("C盗人の試練Cでの報酬は", None, 'exclude'),
    'Gerudo Training Ground Maze Path Second Chest':               ("C盗人の試練Cでの報酬は", None, 'exclude'),
    'Gerudo Training Ground Maze Path Third Chest':                ("C盗人の試練Cでの報酬は", None, 'exclude'),
    'Gerudo Training Ground Maze Right Central Chest':             ("修練場でC時の歌Cは", None, 'exclude'),
    'Gerudo Training Ground Maze Right Side Chest':                ("修練場でC時の歌Cは", None, 'exclude'),
    'Gerudo Training Ground Hammer Room Clear Chest':              ("修練場でC燃える敵Cが守るのは", None, 'exclude'),
    'Gerudo Training Ground Hammer Room Switch Chest':             ("修練場のC炎に飲まれたC場所には", None, 'exclude'),
    'Gerudo Training Ground Eye Statue Chest':                     ("修練場でC四つの目Cをつぶすと", None, 'exclude'),
    'Gerudo Training Ground Near Scarecrow Chest':                 ("修練場でC四つの目Cをつぶすと", None, 'exclude'),
    'Gerudo Training Ground Before Heavy Block Chest':             ("修練場のC銀の岩の前Cには", None, 'exclude'),
    'Gerudo Training Ground Heavy Block First Chest':              ("修練場ではC力業Cをたたえて", None, 'exclude'),
    'Gerudo Training Ground Heavy Block Second Chest':             ("修練場ではC力業Cをたたえて", None, 'exclude'),
    'Gerudo Training Ground Heavy Block Third Chest':              ("修練場ではC力業Cをたたえて", None, 'exclude'),
    'Gerudo Training Ground Heavy Block Fourth Chest':             ("修練場ではC力業Cをたたえて", None, 'exclude'),
    'Gerudo Training Ground Freestanding Key':                     ("修練場でC時の歌Cは", None, 'exclude'),

    'Gerudo Training Ground MQ Lobby Right Chest':                 ("C修練場Cには", None, 'exclude'),
    'Gerudo Training Ground MQ Lobby Left Chest':                  ("C修練場Cには", None, 'exclude'),
    'Gerudo Training Ground MQ First Iron Knuckle Chest':          ("修練場のC砂場Cで守られるのは", None, 'exclude'),
    'Gerudo Training Ground MQ Before Heavy Block Chest':          ("修練場のC銀の岩の前Cには", None, 'exclude'),
    'Gerudo Training Ground MQ Eye Statue Chest':                  ("修練場でC四つの目Cをつぶすと", None, 'exclude'),
    'Gerudo Training Ground MQ Flame Circle Chest':                ("修練場のC炎に飲まれたC場所には", None, 'exclude'),
    'Gerudo Training Ground MQ Second Iron Knuckle Chest':         ("修練場でC燃える敵Cが守るのは", None, 'exclude'),
    'Gerudo Training Ground MQ Dinolfos Chest':                    ("修練場でCトカゲCが守るのは", None, 'exclude'),
    'Gerudo Training Ground MQ Maze Right Central Chest':          ("修練場のC燃える道Cの先には", None, 'exclude'),
    'Gerudo Training Ground MQ Maze Path First Chest':             ("C盗人の試練Cでの報酬は", None, 'exclude'),
    'Gerudo Training Ground MQ Maze Right Side Chest':             ("修練場のC燃える道Cの先には", None, 'exclude'),
    'Gerudo Training Ground MQ Maze Path Third Chest':             ("C盗人の試練Cでの報酬は", None, 'exclude'),
    'Gerudo Training Ground MQ Maze Path Second Chest':            ("C盗人の試練Cでの報酬は", None, 'exclude'),
    'Gerudo Training Ground MQ Hidden Ceiling Chest':              ("修練場でC真実の目Cにより", None, 'exclude'),
    'Gerudo Training Ground MQ Heavy Block Chest':                 ("修練場ではC力業Cをたたえて", None, 'exclude'),

    'Ganons Tower Boss Key Chest':                                 ("C悪の帝王Cが持つものは", None, 'exclude'),

    'Ganons Castle Forest Trial Chest':                            ("C森の試練Cでは", None, 'exclude'),
    'Ganons Castle Water Trial Left Chest':                        ("C水の試練Cでは", None, 'exclude'),
    'Ganons Castle Water Trial Right Chest':                       ("C水の試練Cでは", None, 'exclude'),
    'Ganons Castle Shadow Trial Front Chest':                      ("C闇の試練での音楽Cは", None, 'exclude'),
    'Ganons Castle Shadow Trial Golden Gauntlets Chest':           ("C闇の試練での光Cは", None, 'exclude'),
    'Ganons Castle Spirit Trial Crystal Switch Chest':             ("C魂の試練Cでは", None, 'exclude'),
    'Ganons Castle Spirit Trial Invisible Chest':                  ("C魂の試練Cでは", None, 'exclude'),
    'Ganons Castle Light Trial First Left Chest':                  ("C光の試練Cでは", None, 'exclude'),
    'Ganons Castle Light Trial Second Left Chest':                 ("C光の試練Cでは", None, 'exclude'),
    'Ganons Castle Light Trial Third Left Chest':                  ("C光の試練Cでは", None, 'exclude'),
    'Ganons Castle Light Trial First Right Chest':                 ("C光の試練Cでは", None, 'exclude'),
    'Ganons Castle Light Trial Second Right Chest':                ("C光の試練Cでは", None, 'exclude'),
    'Ganons Castle Light Trial Third Right Chest':                 ("C光の試練Cでは", None, 'exclude'),
    'Ganons Castle Light Trial Invisible Enemies Chest':           ("C光の試練Cでは", None, 'exclude'),
    'Ganons Castle Light Trial Lullaby Chest':                     ("C光の試練での音楽Cは", None, 'exclude'),

    'Ganons Castle MQ Water Trial Chest':                          ("C水の試練Cでは", None, 'exclude'),
    'Ganons Castle MQ Forest Trial Eye Switch Chest':              ("C森の試練Cでは", None, 'exclude'),
    'Ganons Castle MQ Forest Trial Frozen Eye Switch Chest':       ("C森の試練Cでは", None, 'exclude'),
    'Ganons Castle MQ Light Trial Lullaby Chest':                  ("C光の試練での音楽Cは", None, 'exclude'),
    'Ganons Castle MQ Shadow Trial Bomb Flower Chest':             ("C闇の試練Cでは", None, 'exclude'),
    'Ganons Castle MQ Shadow Trial Eye Switch Chest':              ("C闇の試練Cでは", None, 'exclude'),
    'Ganons Castle MQ Spirit Trial Golden Gauntlets Chest':        ("C魂の試練での光Cは", None, 'exclude'),
    'Ganons Castle MQ Spirit Trial Sun Back Right Chest':          ("C魂の試練での光Cは", None, 'exclude'),
    'Ganons Castle MQ Spirit Trial Sun Back Left Chest':           ("C魂の試練での光Cは", None, 'exclude'),
    'Ganons Castle MQ Spirit Trial Sun Front Left Chest':          ("C魂の試練での光Cは", None, 'exclude'),
    'Ganons Castle MQ Spirit Trial First Chest':                   ("C魂の試練での光Cは", None, 'exclude'),
    'Ganons Castle MQ Spirit Trial Invisible Chest':               ("C魂の試練での光Cは", None, 'exclude'),
    'Ganons Castle MQ Forest Trial Freestanding Key':              ("C森の試練Cでは", None, 'exclude'),

    'Deku Tree Queen Gohma Heart':                                 ("C甲殻寄生獣Cが持つのは", "CゴーマCが持つのは", 'exclude'),
    'Dodongos Cavern King Dodongo Heart':                          ("C猛炎古代竜Cが持つのは", "CキングドドンゴCが持つのは", 'exclude'),
    'Jabu Jabus Belly Barinade Heart':                             ("C電撃旋回虫Cが持つのは", "CバリネードCが持つのは", 'exclude'),
    'Forest Temple Phantom Ganon Heart':                           ("C異次元悪霊Cが持つのは", "CファントムガノンCが持つのは", 'exclude'),
    'Fire Temple Volvagia Heart':                                  ("C灼熱穴居竜Cが持つのは", "CヴァルバジアCが持つのは", 'exclude'),
    'Water Temple Morpha Heart':                                   ("C水棲核細胞Cが持つのは", "CモーファCが持つのは", 'exclude'),
    'Spirit Temple Twinrova Heart':                                ("C双生魔道師Cが持つのは", "CツインローバCが持つのは", 'exclude'),
    'Shadow Temple Bongo Bongo Heart':                             ("C暗黒幻影獣Cが持つのは", "CボンゴボンゴCが持つのは", 'exclude'),

    'Deku Tree GS Basement Back Room':                             ("Cデクの樹の底にいるクモCは", None, 'exclude'),
    'Deku Tree GS Basement Gate':                                  ("デクの樹のC糸に隠れたクモCは", None, 'exclude'),
    'Deku Tree GS Basement Vines':                                 ("デクの樹のC糸に隠れたクモCは", None, 'exclude'),
    'Deku Tree GS Compass Room':                                   ("Cデクの樹の上にいるクモCは", None, 'exclude'),

    'Deku Tree MQ GS Lobby':                                       ("デクの樹のC箱にいるクモCは", None, 'exclude'),
    'Deku Tree MQ GS Compass Room':                                ("デクの樹のC岩壁の裏のクモCは", None, 'exclude'),
    'Deku Tree MQ GS Basement Back Room':                          ("Cデクの樹の底にいるクモCは", None, 'exclude'),

    'Dodongos Cavern GS Vines Above Stairs':                       ("ドドンゴの洞窟でCツタのクモCは", None, 'exclude'),
    'Dodongos Cavern GS Scarecrow':                                ("C爆発するナメクジ近くのクモCは", None, 'exclude'),
    'Dodongos Cavern GS Alcove Above Stairs':                      ("ドドンゴの洞窟でC手届かぬクモCは", None, 'exclude'),
    'Dodongos Cavern GS Back Room':                                ("ドドンゴの洞窟のC銅像裏のクモCは", None, 'exclude'),
    'Dodongos Cavern GS Side Room Near Lower Lizalfos':            ("ドドンゴでのCキース近くのクモCは", None, 'exclude'),

    'Dodongos Cavern MQ GS Scrub Room':                            ("ドドンゴの洞窟のC壁クモCは", None, 'exclude'),
    'Dodongos Cavern MQ GS Lizalfos Room':                         ("ドドンゴのC岩柱のクモCは", None, 'exclude'),
    'Dodongos Cavern MQ GS Larvae Room':                           ("ドドンゴのC箱にいるクモCは", None, 'exclude'),
    'Dodongos Cavern MQ GS Back Area':                             ("ドドンゴの洞窟のC墓クモCは", None, 'exclude'),

    'Jabu Jabus Belly GS Lobby Basement Lower':                    ("胃の中でC姫近くにいるクモCは", None, 'exclude'),
    'Jabu Jabus Belly GS Lobby Basement Upper':                    ("胃の中でC姫近くにいるクモCは", None, 'exclude'),
    'Jabu Jabus Belly GS Near Boss':                               ("Cクラゲに囲まれたクモCは", None, 'exclude'),
    'Jabu Jabus Belly GS Water Switch Room':                       ("胃の中でC針に囲まれたクモCは", None, 'exclude'),

    'Jabu Jabus Belly MQ GS Tailpasaran Room':                     ("胃の中でC電気に囲まれたクモCは", None, 'exclude'),
    'Jabu Jabus Belly MQ GS Boomerang Chest Room':                 ("胃の中でC針に囲まれたクモCは", None, 'exclude'),
    'Jabu Jabus Belly MQ GS Near Boss':                            ("胃の中でC糸に隠れるクモCは", None, 'exclude'),

    'Forest Temple GS Raised Island Courtyard':                    ("森の神殿のC孤島のクモCは", None, 'exclude'),
    'Forest Temple GS First Room':                                 ("森の神殿のC壁クモCは", None, 'exclude'),
    'Forest Temple GS Level Island Courtyard':                     ("森の神殿のC石柱Cのクモは", None, 'exclude'),
    'Forest Temple GS Lobby':                                      ("森の神殿のC霊近くのクモCは", None, 'exclude'),
    'Forest Temple GS Basement':                                   ("森の神殿のC回転壁のクモCは", None, 'exclude'),

    'Forest Temple MQ GS First Hallway':                           ("森の神殿でC蓮に隠れたクモCは", None, 'exclude'),
    'Forest Temple MQ GS Block Push Room':                         ("森の神殿でC隠れた隅にいるクモCは", None, 'exclude'),
    'Forest Temple MQ GS Raised Island Courtyard':                 ("森の神殿のCアーチのクモCは", None, 'exclude'),
    'Forest Temple MQ GS Level Island Courtyard':                  ("森の神殿のC出張りにいるクモCは", None, 'exclude'),
    'Forest Temple MQ GS Well':                                    ("森の神殿のC井戸にいるクモCは", None, 'exclude'),

    'Fire Temple GS Song of Time Room':                            ("C八つのタイルに守られたクモCは", None, 'exclude'),
    'Fire Temple GS Boss Key Loop':                                ("C五つのタイルに守られたクモCは", None, 'exclude'),
    'Fire Temple GS Boulder Maze':                                 ("炎の神殿のC迷路のクモCは", None, 'exclude'),
    'Fire Temple GS Scarecrow Top':                                ("C炎の神殿のクモCは", None, 'exclude'),
    'Fire Temple GS Scarecrow Climb':                              ("C炎の神殿のクモCは", None, 'exclude'),

    'Fire Temple MQ GS Above Fire Wall Maze':                      ("炎の神殿のC迷路のクモCは", None, 'exclude'),
    'Fire Temple MQ GS Fire Wall Maze Center':                     ("炎の神殿のC迷路のクモCは", None, 'exclude'),
    'Fire Temple MQ GS Big Lava Room Open Door':                   ("炎の神殿のCゴロン近くのクモCは", None, 'exclude'),
    'Fire Temple MQ GS Fire Wall Maze Side Room':                  ("炎の神殿のC迷路のクモCは", None, 'exclude'),

    'Water Temple GS Falling Platform Room':                       ("水の神殿のC滝先のクモCは", None, 'exclude'),
    'Water Temple GS Central Pillar':                              ("C水の神殿のクモCは", None, 'exclude'),
    'Water Temple GS Near Boss Key Chest':                         ("C回転岩の下のクモCは", "水の神殿のC回転岩下のクモCは", 'exclude'),
    'Water Temple GS River':                                       ("水の神殿のC川先のクモCは", None, 'exclude'),

    'Water Temple MQ GS Before Upper Water Switch':                ("Cトカゲ穴先のクモCは", None, 'exclude'),
    'Water Temple MQ GS Lizalfos Hallway':                         ("水の神殿でCトカゲが守るクモCは", None, 'exclude'),
    'Water Temple MQ GS River':                                    ("水の神殿のC川先のクモCは", None, 'exclude'),

    'Spirit Temple GS Hall After Sun Block Room':                  ("C騎士の間にいるクモCは", None, 'exclude'),
    'Spirit Temple GS Boulder Room':                               ("C魂の神殿の岩クモCは", None, 'exclude'),
    'Spirit Temple GS Lobby':                                      ("C銅像のそばのクモCは", None, 'exclude'),
    'Spirit Temple GS Sun on Floor Room':                          ("魂の神殿のC柱の上にいるクモCは", None, 'exclude'),
    'Spirit Temple GS Metal Fence':                                ("魂の神殿のCキース近くのクモCは", None, 'exclude'),

    'Spirit Temple MQ GS Leever Room':                             ("魂の神殿のC砂場の上のクモCは", None, 'exclude'),
    'Spirit Temple MQ GS Nine Thrones Room West':                  ("C騎士の間にいるクモCは", None, 'exclude'),
    'Spirit Temple MQ GS Nine Thrones Room North':                 ("C騎士の間にいるクモCは", None, 'exclude'),
    'Spirit Temple MQ GS Sun Block Room':                          ("C魂の神殿の糸クモCは", None, 'exclude'),

    'Shadow Temple GS Single Giant Pot':                           ("C燃える骨近くのクモCは", None, 'exclude'),
    'Shadow Temple GS Falling Spikes Room':                        ("C落ちる針の先のクモCは", None, 'exclude'),
    'Shadow Temple GS Triple Giant Pot':                           ("C燃える三つの骨近くのクモCは", None, 'exclude'),
    'Shadow Temple GS Like Like Room':                             ("C見えぬ刃に守られたクモCは", None, 'exclude'),
    'Shadow Temple GS Near Ship':                                  ("C船近くのクモCは", None, 'exclude'),

    'Shadow Temple MQ GS Falling Spikes Room':                     ("C落ちる針の先のクモCは", None, 'exclude'),
    'Shadow Temple MQ GS Wind Hint Room':                          ("闇の神殿のC突風の中のクモCは", None, 'exclude'),
    'Shadow Temple MQ GS After Wind':                              ("C恐ろしき欠片に隠れるクモCは", None, 'exclude'),
    'Shadow Temple MQ GS After Ship':                              ("C壊れた銅像にいるクモCは", None, 'exclude'),
    'Shadow Temple MQ GS Near Boss':                               ("C吊るされたクモCは", None, 'exclude'),

    'Bottom of the Well GS Like Like Cage':                        ("井戸のC檻の中のクモCは", None, 'exclude'),
    'Bottom of the Well GS East Inner Room':                       ("C井戸の見えぬ道の先Cには", None, 'exclude'),
    'Bottom of the Well GS West Inner Room':                       ("井戸のC地下にいるクモCは", None, 'exclude'),

    'Bottom of the Well MQ GS Basement':                           ("C井戸にいるクモCは", None, 'exclude'),
    'Bottom of the Well MQ GS Coffin Room':                        ("井戸のC墓の近くのクモCは", None, 'exclude'),
    'Bottom of the Well MQ GS West Inner Room':                    ("井戸のC地下にいるクモCは", None, 'exclude'),

    'Ice Cavern GS Push Block Room':                               ("C凍った穴の近くのクモCは", None, 'exclude'),
    'Ice Cavern GS Spinning Scythe Room':                          ("C回る氷の中のクモCは", None, 'exclude'),
    'Ice Cavern GS Heart Piece Room':                              ("C氷の壁に隠れるクモCは", None, 'exclude'),

    'Ice Cavern MQ GS Scarecrow':                                  ("C凍った穴の近くのクモCは", None, 'exclude'),
    'Ice Cavern MQ GS Ice Block':                                  ("氷の洞窟のC糸に隠れるクモCは", None, 'exclude'),
    'Ice Cavern MQ GS Red Ice':                                    ("C燃える氷の中のクモCは", None, 'exclude'),

    'HF GS Near Kak Grotto':                                       ("C穴の中のクモに守られたクモCは", None, 'exclude'),

    'LLR GS Back Wall':                                            ("C牧場の夜クモCは", None, 'exclude'),
    'LLR GS Rain Shed':                                            ("C牧場の夜クモCは", None, 'exclude'),
    'LLR GS House Window':                                         ("C牧場の夜クモCは", None, 'exclude'),
    'LLR GS Tree':                                                 ("C牧場の木のクモCは", None, 'exclude'),

    'KF GS Bean Patch':                                            ("C森のクモCは", None, 'exclude'),
    'KF GS Know It All House':                                     ("C森の夜クモCは", None, 'exclude'),
    'KF GS House of Twins':                                        ("C森の夜クモCは", None, 'exclude'),

    'LW GS Bean Patch Near Bridge':                                ("C森の迷路のクモCは", None, 'exclude'),
    'LW GS Bean Patch Near Theater':                               ("C森の迷路のクモCは", None, 'exclude'),
    'LW GS Above Theater':                                         ("C森の迷路の夜クモCは", None, 'exclude'),
    'SFM GS':                                                      ("C聖なる森の夜クモCは", None, 'exclude'),

    'OGC GS':                                                      ("C暴君の塔外にいるクモCは", None, 'exclude'),
    'HC GS Tree':                                                  ("C暴君の塔外で木にいるクモCは", None, 'exclude'),
    'Market GS Guard House':                                       ("C暴君の塔外で箱にいるクモCは", None, 'exclude'),

    'DMC GS Bean Patch':                                           ("C火山のクモCは", None, 'exclude'),

    'DMT GS Bean Patch':                                           ("C洞窟のそばで埋められたクモCは", None, 'exclude'),
    'DMT GS Near Kak':                                             ("山のC隅に隠れたクモCは", None, 'exclude'),
    'DMT GS Above Dodongos Cavern':                                ("C山のハンマークモCは", None, 'exclude'),
    'DMT GS Falling Rocks Path':                                   ("C山のハンマークモCは", None, 'exclude'),

    'GC GS Center Platform':                                       ("ゴロンシティのC吊るされたクモCは", None, 'exclude'),
    'GC GS Boulder Maze':                                          ("ゴロンシティのC箱のクモCは", None, 'exclude'),

    'Kak GS House Under Construction':                             ("C村の夜クモCは", None, 'exclude'),
    'Kak GS Skulltula House':                                      ("C村の夜クモCは", None, 'exclude'),
    'Kak GS Guards House':                                         ("C村の夜クモCは", None, 'exclude'),
    'Kak GS Tree':                                                 ("C村の夜クモCは", None, 'exclude'),
    'Kak GS Watchtower':                                           ("C村の夜クモCは", None, 'exclude'),
    'Kak GS Above Impas House':                                    ("C村の夜クモCは", None, 'exclude'),

    'Graveyard GS Wall':                                           ("C墓場の夜クモCは", None, 'exclude'),
    'Graveyard GS Bean Patch':                                     ("C墓場のクモCは", None, 'exclude'),

    'ZR GS Ladder':                                                ("C川の夜クモCは", None, 'exclude'),
    'ZR GS Tree':                                                  ("C川沿いの木のクモCは", None, 'exclude'),
    'ZR GS Above Bridge':                                          ("C川の夜クモCは", None, 'exclude'),
    'ZR GS Near Raised Grottos':                                   ("C川の夜クモCは", None, 'exclude'),

    'ZD GS Frozen Waterfall':                                      ("C凍った滝の夜クモCは", None, 'exclude'),
    'ZF GS Above the Log':                                         ("C神近くの夜クモCは", None, 'exclude'),
    'ZF GS Tree':                                                  ("C神近くの木のクモCは", None, 'exclude'),

    'LH GS Bean Patch':                                            ("C湖のクモCは", None, 'exclude'),
    'LH GS Small Island':                                          ("C湖の夜クモCは", None, 'exclude'),
    'LH GS Lab Wall':                                              ("C湖の夜クモCは", None, 'exclude'),
    'LH GS Lab Crate':                                             ("C研究所に沈むクモCは", None, 'exclude'),
    'LH GS Tree':                                                  ("C湖の木の夜クモCは", None, 'exclude'),

    'GV GS Bean Patch':                                            ("C谷のクモCは", None, 'exclude'),
    'GV GS Small Bridge':                                          ("C谷の夜クモCは", None, 'exclude'),
    'GV GS Pillar':                                                ("C谷の夜クモCは", None, 'exclude'),
    'GV GS Behind Tent':                                           ("C谷の夜クモCは", None, 'exclude'),

    'GF GS Archery Range':                                         ("C砦の夜クモCは", None, 'exclude'),
    'GF GS Top Floor':                                             ("C砦の夜クモCは", None, 'exclude'),

    'Colossus GS Bean Patch':                                      ("C砂漠のクモCは", None, 'exclude'),
    'Colossus GS Hill':                                            ("C砂漠の夜クモCは", None, 'exclude'),
    'Colossus GS Tree':                                            ("C砂漠の夜クモCは", None, 'exclude'),

    'KF Shop Item 1':                                              ("C子供の商人Cが売るのは", None, 'exclude'),
    'KF Shop Item 2':                                              ("C子供の商人Cが売るのは", None, 'exclude'),
    'KF Shop Item 3':                                              ("C子供の商人Cが売るのは", None, 'exclude'),
    'KF Shop Item 4':                                              ("C子供の商人Cが売るのは", None, 'exclude'),
    'KF Shop Item 5':                                              ("C子供の商人Cが売るのは", None, 'exclude'),
    'KF Shop Item 6':                                              ("C子供の商人Cが売るのは", None, 'exclude'),
    'KF Shop Item 7':                                              ("C子供の商人Cが売るのは", None, 'exclude'),
    'KF Shop Item 8':                                              ("C子供の商人Cが売るのは", None, 'exclude'),

    'Kak Potion Shop Item 1':                                      ("C薬売りCが売るのは", "C村の薬売りCが売るのは", 'exclude'),
    'Kak Potion Shop Item 2':                                      ("C薬売りCが売るのは", "C村の薬売りCが売るのは", 'exclude'),
    'Kak Potion Shop Item 3':                                      ("C薬売りCが売るのは", "C村の薬売りCが売るのは", 'exclude'),
    'Kak Potion Shop Item 4':                                      ("C薬売りCが売るのは", "C村の薬売りCが売るのは", 'exclude'),
    'Kak Potion Shop Item 5':                                      ("C薬売りCが売るのは", "C村の薬売りCが売るのは", 'exclude'),
    'Kak Potion Shop Item 6':                                      ("C薬売りCが売るのは", "C村の薬売りCが売るのは", 'exclude'),
    'Kak Potion Shop Item 7':                                      ("C薬売りCが売るのは", "C村の薬売りCが売るのは", 'exclude'),
    'Kak Potion Shop Item 8':                                      ("C薬売りCが売るのは", "C村の薬売りCが売るのは", 'exclude'),

    'Market Bombchu Shop Item 1':                                  ("Cボムチュウ屋Cが売るのは", None, 'exclude'),
    'Market Bombchu Shop Item 2':                                  ("Cボムチュウ屋Cが売るのは", None, 'exclude'),
    'Market Bombchu Shop Item 3':                                  ("Cボムチュウ屋Cが売るのは", None, 'exclude'),
    'Market Bombchu Shop Item 4':                                  ("Cボムチュウ屋Cが売るのは", None, 'exclude'),
    'Market Bombchu Shop Item 5':                                  ("Cボムチュウ屋Cが売るのは", None, 'exclude'),
    'Market Bombchu Shop Item 6':                                  ("Cボムチュウ屋Cが売るのは", None, 'exclude'),
    'Market Bombchu Shop Item 7':                                  ("Cボムチュウ屋Cが売るのは", None, 'exclude'),
    'Market Bombchu Shop Item 8':                                  ("Cボムチュウ屋Cが売るのは", None, 'exclude'),

    'Market Potion Shop Item 1':                                   ("C薬売りCが売るのは", "C街の薬売りCが売るのは", 'exclude'),
    'Market Potion Shop Item 2':                                   ("C薬売りCが売るのは", "C街の薬売りCが売るのは", 'exclude'),
    'Market Potion Shop Item 3':                                   ("C薬売りCが売るのは", "C街の薬売りCが売るのは", 'exclude'),
    'Market Potion Shop Item 4':                                   ("C薬売りCが売るのは", "C街の薬売りCが売るのは", 'exclude'),
    'Market Potion Shop Item 5':                                   ("C薬売りCが売るのは", "C街の薬売りCが売るのは", 'exclude'),
    'Market Potion Shop Item 6':                                   ("C薬売りCが売るのは", "C街の薬売りCが売るのは", 'exclude'),
    'Market Potion Shop Item 7':                                   ("C薬売りCが売るのは", "C街の薬売りCが売るのは", 'exclude'),
    'Market Potion Shop Item 8':                                   ("C薬売りCが売るのは", "C街の薬売りCが売るのは", 'exclude'),

    'Market Bazaar Item 1':                                        ("C街Cで売るのは", None, 'exclude'),
    'Market Bazaar Item 2':                                        ("C街Cで売るのは", None, 'exclude'),
    'Market Bazaar Item 3':                                        ("C街Cで売るのは", None, 'exclude'),
    'Market Bazaar Item 4':                                        ("C街Cで売るのは", None, 'exclude'),
    'Market Bazaar Item 5':                                        ("C街Cで売るのは", None, 'exclude'),
    'Market Bazaar Item 6':                                        ("C街Cで売るのは", None, 'exclude'),
    'Market Bazaar Item 7':                                        ("C街Cで売るのは", None, 'exclude'),
    'Market Bazaar Item 8':                                        ("C街Cで売るのは", None, 'exclude'),

    'Kak Bazaar Item 1':                                           ("C村Cで売るのは", None, 'exclude'),
    'Kak Bazaar Item 2':                                           ("C村Cで売るのは", None, 'exclude'),
    'Kak Bazaar Item 3':                                           ("C村Cで売るのは", None, 'exclude'),
    'Kak Bazaar Item 4':                                           ("C村Cで売るのは", None, 'exclude'),
    'Kak Bazaar Item 5':                                           ("C村Cで売るのは", None, 'exclude'),
    'Kak Bazaar Item 6':                                           ("C村Cで売るのは", None, 'exclude'),
    'Kak Bazaar Item 7':                                           ("C村Cで売るのは", None, 'exclude'),
    'Kak Bazaar Item 8':                                           ("C村Cで売るのは", None, 'exclude'),

    'ZD Shop Item 1':                                              ("CゾーラCが売るのは", None, 'exclude'),
    'ZD Shop Item 2':                                              ("CゾーラCが売るのは", None, 'exclude'),
    'ZD Shop Item 3':                                              ("CゾーラCが売るのは", None, 'exclude'),
    'ZD Shop Item 4':                                              ("CゾーラCが売るのは", None, 'exclude'),
    'ZD Shop Item 5':                                              ("CゾーラCが売るのは", None, 'exclude'),
    'ZD Shop Item 6':                                              ("CゾーラCが売るのは", None, 'exclude'),
    'ZD Shop Item 7':                                              ("CゾーラCが売るのは", None, 'exclude'),
    'ZD Shop Item 8':                                              ("CゾーラCが売るのは", None, 'exclude'),

    'GC Shop Item 1':                                              ("CゴロンCが売るのは", None, 'exclude'),
    'GC Shop Item 2':                                              ("CゴロンCが売るのは", None, 'exclude'),
    'GC Shop Item 3':                                              ("CゴロンCが売るのは", None, 'exclude'),
    'GC Shop Item 4':                                              ("CゴロンCが売るのは", None, 'exclude'),
    'GC Shop Item 5':                                              ("CゴロンCが売るのは", None, 'exclude'),
    'GC Shop Item 6':                                              ("CゴロンCが売るのは", None, 'exclude'),
    'GC Shop Item 7':                                              ("CゴロンCが売るのは", None, 'exclude'),
    'GC Shop Item 8':                                              ("CゴロンCが売るのは", None, 'exclude'),

    'Deku Tree MQ Deku Scrub':                                     ("Cデクの樹の商人Cは", None, 'exclude'),

    'HF Deku Scrub Grotto':                                        ("C穴下の商人Cは", None, 'exclude'),
    'LLR Deku Scrub Grotto Left':                                  ("C穴下の商人Cは", None, 'exclude'),
    'LLR Deku Scrub Grotto Right':                                 ("C穴下の商人Cは", None, 'exclude'),
    'LLR Deku Scrub Grotto Center':                                ("C穴下の商人Cは", None, 'exclude'),

    'LW Deku Scrub Near Deku Theater Right':                       ("C迷いの森の商人Cは", None, 'exclude'),
    'LW Deku Scrub Near Deku Theater Left':                        ("C迷いの森の商人Cは", None, 'exclude'),
    'LW Deku Scrub Near Bridge':                                   ("C橋の商人Cは", None, 'exclude'),
    'LW Deku Scrub Grotto Rear':                                   ("C穴下の商人Cは", None, 'exclude'),
    'LW Deku Scrub Grotto Front':                                  ("C穴下の商人Cは", None, 'exclude'),

    'SFM Deku Scrub Grotto Rear':                                  ("C穴下の商人Cは", None, 'exclude'),
    'SFM Deku Scrub Grotto Front':                                 ("C穴下の商人Cは", None, 'exclude'),

    'GC Deku Scrub Grotto Left':                                   ("C穴下の商人Cは", None, 'exclude'),
    'GC Deku Scrub Grotto Right':                                  ("C穴下の商人Cは", None, 'exclude'),
    'GC Deku Scrub Grotto Center':                                 ("C穴下の商人Cは", None, 'exclude'),

    'Dodongos Cavern Deku Scrub Near Bomb Bag Left':               ("C洞窟の商人Cは", None, 'exclude'),
    'Dodongos Cavern Deku Scrub Side Room Near Dodongos':          ("Cリザルフォス近くの商人Cは", None, 'exclude'),
    'Dodongos Cavern Deku Scrub Near Bomb Bag Right':              ("C洞窟の商人Cは", None, 'exclude'),
    'Dodongos Cavern Deku Scrub Lobby':                            ("C洞窟の商人Cは", None, 'exclude'),

    'Dodongos Cavern MQ Deku Scrub Lobby Rear':                    ("C洞窟の商人Cは", None, 'exclude'),
    'Dodongos Cavern MQ Deku Scrub Side Room Near Lower Lizalfos': ("Cリザルフォス近くの商人Cは", None, 'exclude'),
    'Dodongos Cavern MQ Deku Scrub Lobby Front':                   ("C洞窟の商人Cは", None, 'exclude'),
    'Dodongos Cavern MQ Deku Scrub Staircase':                     ("C洞窟の商人Cは", None, 'exclude'),

    'DMC Deku Scrub Grotto Left':                                  ("C穴下の商人Cは", None, 'exclude'),
    'DMC Deku Scrub Grotto Right':                                 ("C穴下の商人Cは", None, 'exclude'),
    'DMC Deku Scrub Grotto Center':                                ("C穴下の商人Cは", None, 'exclude'),

    'ZR Deku Scrub Grotto Rear':                                   ("C穴下の商人Cは", None, 'exclude'),
    'ZR Deku Scrub Grotto Front':                                  ("C穴下の商人Cは", None, 'exclude'),

    'Jabu Jabus Belly Deku Scrub':                                 ("C胃の中の商人Cは", None, 'exclude'),

    'LH Deku Scrub Grotto Left':                                   ("C穴下の商人Cは", None, 'exclude'),
    'LH Deku Scrub Grotto Right':                                  ("C穴下の商人Cは", None, 'exclude'),
    'LH Deku Scrub Grotto Center':                                 ("C穴下の商人Cは", None, 'exclude'),

    'GV Deku Scrub Grotto Rear':                                   ("C穴下の商人Cは", None, 'exclude'),
    'GV Deku Scrub Grotto Front':                                  ("C穴下の商人Cは", None, 'exclude'),

    'Colossus Deku Scrub Grotto Front':                            ("C穴下の商人Cは", None, 'exclude'),
    'Colossus Deku Scrub Grotto Rear':                             ("C穴下の商人Cは", None, 'exclude'),

    'Ganons Castle Deku Scrub Center-Left':                        ("Cガノン城の商人Cは", None, 'exclude'),
    'Ganons Castle Deku Scrub Center-Right':                       ("Cガノン城の商人Cは", None, 'exclude'),
    'Ganons Castle Deku Scrub Right':                              ("Cガノン城の商人Cは", None, 'exclude'),
    'Ganons Castle Deku Scrub Left':                               ("Cガノン城の商人Cは", None, 'exclude'),

    'Ganons Castle MQ Deku Scrub Right':                           ("Cガノン城の商人Cは", None, 'exclude'),
    'Ganons Castle MQ Deku Scrub Center-Left':                     ("Cガノン城の商人Cは", None, 'exclude'),
    'Ganons Castle MQ Deku Scrub Center':                          ("Cガノン城の商人Cは", None, 'exclude'),
    'Ganons Castle MQ Deku Scrub Center-Right':                    ("Cガノン城の商人Cは", None, 'exclude'),
    'Ganons Castle MQ Deku Scrub Left':                            ("Cガノン城の商人Cは", None, 'exclude'),

    'LLR Stables Left Cow':                                        ("C馬小屋の牛Cは", None, 'exclude'),
    'LLR Stables Right Cow':                                       ("C馬小屋の牛Cは", None, 'exclude'),
    'LLR Tower Right Cow':                                         ("Cサイロの牛Cは", None, 'exclude'),
    'LLR Tower Left Cow':                                          ("Cサイロの牛Cは", None, 'exclude'),
    'Kak Impas House Cow':                                         ("C家の中の牛Cは", None, 'exclude'),
    'DMT Cow Grotto Cow':                                          ("C豪華な穴の牛Cは", None, 'exclude'),

    'Desert Colossus -> Colossus Grotto':                       ("C砂漠の岩Cを持ち上げると", None, 'entrance'),
    'GV Grotto Ledge -> GV Octorok Grotto':                     ("C谷の岩Cが隠すのは", None, 'entrance'),
    'GC Grotto Platform -> GC Grotto':                          ("ゴロンシティのC溶岩Cは", None, 'entrance'),
    'Gerudo Fortress -> GF Storms Grotto':                      ("Cゲルドの砦で嵐Cは", None, 'entrance'),
    'Zoras Domain -> ZD Storms Grotto':                         ("Cゾーラの里で嵐Cは", None, 'entrance'),
    'Hyrule Castle Grounds -> HC Storms Grotto':                ("C城の近くで嵐Cは", None, 'entrance'),
    'GV Fortress Side -> GV Storms Grotto':                     ("C谷で嵐Cは", None, 'entrance'),
    'Desert Colossus -> Colossus Great Fairy Fountain':         ("C脆い砂壁Cは", None, 'entrance'),
    'Ganons Castle Grounds -> OGC Great Fairy Fountain':        ("C城前の巨大な岩Cは", None, 'entrance'),
    'Zoras Fountain -> ZF Great Fairy Fountain':                ("C泉の壁Cが隠すのは", None, 'entrance'),
    'GV Fortress Side -> GV Carpenter Tent':                    ("C谷のテントCは", None, 'entrance'),
    'Graveyard Warp Pad Region -> Shadow Temple Entryway':      ("C墓の後ろCには", None, 'entrance'),
    'Lake Hylia -> Water Temple Lobby':                         ("C広大な池の下Cには", None, 'entrance'),
    'Gerudo Fortress -> Gerudo Training Ground Lobby':          ("Cゲルドにお金を払いC行けるのは", None, 'entrance'),
    'Zoras Fountain -> Jabu Jabus Belly Beginning':             ("CジャブジャブCの中には", None, 'entrance'),
    'Kakariko Village -> Bottom of the Well':                   ("C村の井戸Cの中には", None, 'entrance'),

    'KF Links House':                                           ("リンクの家", None, 'region'),
    'Temple of Time':                                           ("C時の神殿C", None, 'region'),
    'KF Midos House':                                           ("ミドの家", None, 'region'),
    'KF Sarias House':                                          ("サリアの家", None, 'region'),
    'KF House of Twins':                                        ("C双子の家C", None, 'region'),
    'KF Know It All House':                                     ("物知り兄弟の家", None, 'region'),
    'KF Kokiri Shop':                                           ("Cコキリの店C", None, 'region'),
    'LH Lab':                                                   ("Cみずうみ研究所C", None, 'region'),
    'LH Fishing Hole':                                          ("CつりぼりC", None, 'region'),
    'GV Carpenter Tent':                                        ("C大工のテントC", None, 'region'),
    'Market Guard House':                                       ("C兵士詰所C", None, 'region'),
    'Market Mask Shop':                                         ("Cお面屋C", None, 'region'),
    'Market Bombchu Bowling':                                   ("CボウリングC", None, 'region'),
    'Market Potion Shop':                                       ("C町のクスリ屋C", None, 'region'),
    'Market Treasure Chest Game':                               ("Cクジ屋C", None, 'region'),
    'Market Bombchu Shop':                                      ("Cボムチュウ屋C", None, 'region'),
    'Market Man in Green House':                                ("民家", None, 'region'),
    'Kak Windmill':                                             ("C風車C", None, 'region'),
    'Kak Carpenter Boss House':                                 ("C大工の家C", None, 'region'),
    'Kak House of Skulltula':                                   ("CスタルチュラハウスC", None, 'region'),
    'Kak Impas House':                                          ("インパの家", None, 'region'),
    'Kak Impas House Back':                                     ("インパの牛小屋", None, 'region'),
    'Kak Odd Medicine Building':                                ("オババのクスリ屋", None, 'region'),
    'Graveyard Dampes House':                                   ("ダンペイの小屋", None, 'region'),
    'GC Shop':                                                  ("Cゴロンの店C", None, 'region'),
    'ZD Shop':                                                  ("Cゾーラの店C", None, 'region'),
    'LLR Talons House':                                         ("タロンの家", None, 'region'),
    'LLR Stables':                                              ("C馬小屋C", None, 'region'),
    'LLR Tower':                                                ("C納屋C", None, 'region'),
    'Market Bazaar':                                            ("C町のなンでも屋C", None, 'region'),
    'Market Shooting Gallery':                                  ("C町の的当屋C", None, 'region'),
    'Kak Bazaar':                                               ("C村のなンでも屋C", None, 'region'),
    'Kak Potion Shop Front':                                    ("C村のクスリ屋C", None, 'region'),
    'Kak Potion Shop Back':                                     ("C村のクスリ屋C", None, 'region'),
    'Kak Shooting Gallery':                                     ("C村の的当屋C", None, 'region'),
    'Colossus Great Fairy Fountain':                            ("C大妖精の泉C", None, 'region'),
    'HC Great Fairy Fountain':                                  ("C大妖精の泉C", None, 'region'),
    'OGC Great Fairy Fountain':                                 ("C大妖精の泉C", None, 'region'),
    'DMC Great Fairy Fountain':                                 ("C大妖精の泉C", None, 'region'),
    'DMT Great Fairy Fountain':                                 ("C大妖精の泉C", None, 'region'),
    'ZF Great Fairy Fountain':                                  ("C大妖精の泉C", None, 'region'),
    'Graveyard Shield Grave':                                   ("C大妖精の泉C", None, 'region'),
    'Graveyard Heart Piece Grave':                              ("C太陽の歌Cで現れるチェスト", None, 'region'),
    'Graveyard Composers Grave':                                ("C作曲家の墓C", None, 'region'),
    'Graveyard Dampes Grave':                                   ("ダンペイの墓", None, 'region'),
    'DMT Cow Grotto':                                           ("孤独なC牛C", None, 'region'),
    'HC Storms Grotto':                                         ("砂っぽいC脆壁の穴C", None, 'region'),
    'HF Tektite Grotto':                                        ("CテクタイトCのいる穴", None, 'region'),
    'HF Near Kak Grotto':                                       ("C２色のクモCのいる穴", None, 'region'),
    'HF Cow Grotto':                                            ("Cクモの巣Cだらけの穴", None, 'region'),
    'Kak Redead Grotto':                                        ("CリーデッドCのいる穴", None, 'region'),
    'SFM Wolfos Grotto':                                        ("CウルフォスCのいる穴", None, 'region'),
    'GV Octorok Grotto':                                        ("CオクタンCのいる穴", None, 'region'),
    'Deku Theater':                                             ("C仮面博覧会C", None, 'region'),
    'ZR Open Grotto':                                           ("C穴C", None, 'region'),
    'DMC Upper Grotto':                                         ("C穴C", None, 'region'),
    'DMT Storms Grotto':                                        ("C穴C", None, 'region'),
    'Kak Open Grotto':                                          ("C穴C", None, 'region'),
    'HF Near Market Grotto':                                    ("C穴C", None, 'region'),
    'HF Open Grotto':                                           ("C穴C", None, 'region'),
    'HF Southeast Grotto':                                      ("C穴C", None, 'region'),
    'KF Storms Grotto':                                         ("C穴C", None, 'region'),
    'LW Near Shortcuts Grotto':                                 ("C穴C", None, 'region'),
    'HF Inside Fence Grotto':                                   ("Cアキンド穴C", None, 'region'),
    'LW Scrubs Grotto':                                         ("Cアキンド穴C", None, 'region'),
    'Colossus Grotto':                                          ("２体のアキンド穴", None, 'region'),
    'ZR Storms Grotto':                                         ("２体のアキンド穴", None, 'region'),
    'SFM Storms Grotto':                                        ("２体のアキンド穴", None, 'region'),
    'GV Storms Grotto':                                         ("２体のアキンド穴", None, 'region'),
    'LH Grotto':                                                ("３体のアキンド穴", None, 'region'),
    'DMC Hammer Grotto':                                        ("３体のアキンド穴", None, 'region'),
    'GC Grotto':                                                ("３体のアキンド穴", None, 'region'),
    'LLR Grotto':                                               ("３体のアキンド穴", None, 'region'),
    'ZR Fairy Grotto':                                          ("C妖精の泉C", None, 'region'),
    'HF Fairy Grotto':                                          ("C妖精の泉C", None, 'region'),
    'SFM Fairy Grotto':                                         ("C妖精の泉C", None, 'region'),
    'ZD Storms Grotto':                                         ("C妖精の泉C", None, 'region'),
    'GF Storms Grotto':                                         ("C妖精の泉C", None, 'region'),

    '1001':                                                     ("<いつでもガノン！", None, 'junk'),
    '1002':                                                     ("<この王国の政治は&あまり良くないよ。", None, 'junk'),
    '1003':                                                     ("<ゼルダ姫は良いリーダー&ではないよ。", None, 'junk'),
    '1004':                                                     ("<ほとんどのヒントは使えるものだ。&これは例外だけど。", None, 'junk'),
    '1006':                                                     ("<風のタクトでゾーラは&沈んだよ。", None, 'junk'),
    '1008':                                                     ("<ガノンはもともと青い豚&だったと言われているよ。", None, 'junk'),
    '1009':                                                     ("<トライフォースなしに&このシリーズは語れないよ。", None, 'junk'),
    '1010':                                                     ("<未来を救え、&幸せのお面屋に会うな。", None, 'junk'),
    '1012':                                                     ("<僕にもイシがある。&なんてね", None, 'junk'),
    '1013':                                                     ("<ホホーゥ！&…と何回言えばいいんだ？", None, 'junk'),
    '1014':                                                     ("<ゴロンは岩を食べるよ。", None, 'junk'),
    '1015':                                                     ("<インゴーによって&ロンロン牧場は建てられたよ。", None, 'junk'),
    '1016':                                                     ("<１ルピーは珍しいアイテムだ。", None, 'junk'),
    '1017':                                                     ("<まことのメガネなしにクジ屋で&勝つのは１／３２の確立らしい。&頑張ってね！", None, 'junk'),
    '1018':                                                     ("<バクダンは安全に扱え。", None, 'junk'),
    '1021':                                                     ("<見つけたぜ、&このニセモノ野郎！", None, 'junk'),
    '1022':                                                     ("<フッ、ニセモノ？ハ、フェイクは君の&ほうじゃないのか？いや、フェイクと&呼ぶには、レベルが違いすぎるか…", None, 'junk'),
    '1023':                                                     ("<言わせておけば！", None, 'junk'),
    '1024':                                                     ("<シークに何があったのかなぁ？", None, 'junk'),
    '1025':                                                     ("<学び行え@。", None, 'junk'),
    '1026':                                                     ("<海戦ゲームは運任せと&聞いたことがあるよ。", None, 'junk'),
    '1027':                                                     ("<青ルピー、フール、詰みマップ、&うっ、頭が", None, 'junk'),
    '1028':                                                     ("<もっとバクダンほしいでしょ。", None, 'junk'),
    '1029':                                                     ("<何もかもダメだったら、&火を使え。", None, 'junk'),
    '1030':                                                     ("<@、アドバイスだ。&落ち着くんだ。", None, 'junk'),
    '1031':                                                     ("<ゲームオーバー&ガノンの帰還", None, 'junk'),
    '1032':                                                     ("<トライフォースが勇者を導くでしょう。", None, 'junk'),
    '1033':                                                     ("<アイテムが見つからない？&アミーボを使え。", None, 'junk'),
    '1034':                                                     ("<このゲームにはいくつか&バグがあるらしい。", None, 'junk'),
    '1035':                                                     ("<トウルルル……　トウルルル……&ハロー！ うるりらじいさんじゃ&？？？番号を　まちがえたみたいだ", None, 'junk'),
    '1036':                                                     ("<チンクル、チンクル、&クルリンパ！", None, 'junk'),
    '1037':                                                     ("<そんな装備で大丈夫か？&大丈夫だ問題ない。", None, 'junk'),
    '1038':                                                     ("<ガノンがスマブラで&剣士になったらしい。", None, 'junk'),
    '1039':                                                     ("<ダイゴロンはブレワイの&開発版を売ってるらしい。", None, 'junk'),
    '1040':                                                     ("<僕にも質問する権利はあるはずだ！", None, 'junk'),
    '1041':                                                     ("<もう少しで詰むところだったな&@。", None, 'junk'),
    '1042':                                                     ("<僕は最も助けになるヒントだ。", None, 'junk'),
    '1043':                                                     ("<@へ&遊びに来て下さい。ケーキを作って&待ってます。　ゼルダより", None, 'junk'),
    '1044':                                                     ("<詰んだら空き瓶を&使うといいらしいよ。", None, 'junk'),
    '1045':                                                     ("<大神は最高のゼルダーゲームらしい。", None, 'junk'),
    '1046':                                                     ("<クエストは話せる石が導くらしいよ。", None, 'junk'),
    '1047':                                                     ("<探しているアイテムは&ハイラルの地にあるらしいよ。", None, 'junk'),
    '1048':                                                     ("<ムニッ&ムニッ&ムニッ^<ムニッ&ムニッ&ムニッ^<ムニッ&ムニッ&ムニッ", None, 'junk'),
    '1049':                                                     ("<バリネードはデクの実が&嫌いらしいよ。", None, 'junk'),
    '1050':                                                     ("<フレアダンサーは&ダイゴロン刀を&恐れないらしいよ。", None, 'junk'),
    '1051':                                                     ("<モーファは角に&追い込みやすいらしいよ。", None, 'junk'),
    '1052':                                                     ("<ボンゴボンゴは&寒いのが嫌いらしいよ。", None, 'junk'),
    '1053':                                                     ("<しゃがみ攻撃は前のダメージを&引き継ぐらしいよ。", None, 'junk'),
    '1054':                                                     ("<バルバジアの入った穴を爆発させると&いいことがあるらしいよ。", None, 'junk'),
    '1055':                                                     ("<透明な幽霊はデクの実で見えるようになるらしいよ。", None, 'junk'),
    '1056':                                                     ("<本物のファントムガノンは&明るくてうるさいらしいよ。", None, 'junk'),
    '1057':                                                     ("<後ろ歩きが一番早いらしいよ。", None, 'junk'),
    '1058':                                                     ("<城下町の門を飛ぶと&いいことがあるらしいよ。", None, 'junk'),
    '1059':                                                     ("<ランダマイザーを日本語化したのは&一人の男性らしいよ。", None, 'junk'),
    '1060':                                                     ("<聖なる岩を見つけた！", None, 'junk'),
    '1061':                                                     ("<棒は剣よりも強し。", None, 'junk'),
    '1062':                                                     ("<@…^@…^目覚めるのです&@！", None, 'junk'),
    '1063':                                                     ("<任意コード実行は&クレジットに&つながるらしいよ。", None, 'junk'),
    '1064':                                                     ("<ツインローバは最初三回は&同じ呪文を唱えるらしいよ。", None, 'junk'),
    '1065':                                                     ("<このバージョンは&不安定かもしれないよ。", None, 'junk'),
    '1066':                                                     ("<あなたはランダマイザーをやっているよ。&楽しんでね！", None, 'junk'),
    '1067':                                                     ("<ガノンの攻撃は&鉄かガラスで返せるらしいよ。", None, 'junk'),
    '1068':                                                     ("<ガノンの尻尾の弱点は&実、矢、剣、&爆発物、ハンマー…^<…棒、&タネ、&ブーメラン…^<…杖、シャベル、&鉄球、起こったハチ…", None, 'junk'),
    '1069':                                                     ("<このヒントを見ることは&無駄な時間だと言われている。&けど僕は違うと思うよ。", None, 'junk'),
    '1070':                                                     ("<ガノンは自分の弱点である&矢の場所を言うらしいよ。", None, 'junk'),
    '1071':                                                     ("<@はこのゲームに詳しいらしい。", None, 'junk'),

    'Deku Tree':                                                ("古代の樹", "デクの樹", 'dungeonName'),
    'Dodongos Cavern':                                          ("巨大な洞窟", "ドドンゴの洞窟", 'dungeonName'),
    'Jabu Jabus Belly':                                         ("神の腹の中", "ジャブジャブ様のお腹", 'dungeonName'),
    'Forest Temple':                                            ("深き森", "森の神殿", 'dungeonName'),
    'Fire Temple':                                              ("高き山", "炎の神殿", 'dungeonName'),
    'Water Temple':                                             ("広き湖", "水の神殿", 'dungeonName'),
    'Shadow Temple':                                            ("屍の館", "闇の神殿", 'dungeonName'),
    'Spirit Temple':                                            ("砂の女神", "魂の神殿", 'dungeonName'),
    'Ice Cavern':                                               ("凍った迷路", "氷の洞窟", 'dungeonName'),
    'Bottom of the Well':                                       ("影の捕う場所", "井戸の底", 'dungeonName'),
    'Gerudo Training Ground':                                   ("盗人のテスト", "ゲルド修練場", 'dungeonName'),
    'Ganons Castle':                                            ("乗っ取られた城", "ガノン城", 'dungeonName'),
    
    'Queen Gohma':                                              ("<一つは　C古代の樹C　に…", "<一つは　Cデクの樹C　に…", 'boss'),
    'King Dodongo':                                             ("<一つは　C巨大な洞窟C　に…", "<一つは　Cドドンゴの洞窟C　に…", 'boss'),
    'Barinade':                                                 ("<一つは　C神の腹の中C　に…", "<一つは　Cジャブジャブ様C　に…", 'boss'),
    'Phantom Ganon':                                            ("<一つは　C深き森C　に…", "<一つは　C森の神殿C　に…", 'boss'),
    'Volvagia':                                                 ("<一つは　C高き山C　に…", "<一つは　C炎の神殿C　に…", 'boss'),
    'Morpha':                                                   ("<一つは　C広き湖C　に…", "<一つは　C水の神殿C　に…", 'boss'),
    'Bongo Bongo':                                              ("<一つは　C屍の館C　に…", "<一つは　C闇の神殿C　に…", 'boss'),
    'Twinrova':                                                 ("<一つは　C砂の女神C　に…", "<一つは　C魂の神殿C　に…", 'boss'),
    'Links Pocket':                                             ("<一つは　C手元C　に…", "<一つは　Cすでに持っているC…", 'boss'),

    'bridge_vanilla':                                           ("C闇と魂のメダルC　そして　C光の矢C", None, 'bridge'),
    'bridge_stones':                                            ("精霊石", None, 'bridge'),
    'bridge_medallions':                                        ("メダル", None, 'bridge'),
    'bridge_dungeons':                                          ("精霊石とメダル", None, 'bridge'),
    'bridge_tokens':                                            ("トークン", None, 'bridge'),

    'ganonBK_dungeon':                                          ("C城の中Cに隠されている", None, 'ganonBossKey'),
    'ganonBK_vanilla':                                          ("C塔の中Cに隠されている", None, 'ganonBossKey'),
    'ganonBK_overworld':                                        ("Cダンジョン外Cに隠されている", None, 'ganonBossKey'),
    'ganonBK_any_dungeon':                                      ("Cダンジョン内Cに隠されている", None, 'ganonBossKey'),
    'ganonBK_keysanity':                                        ("CハイラルのどこかCに隠されている", None, 'ganonBossKey'),
    'ganonBK_triforce':                                         ("CトライフォースCが完成した時渡される", None, 'ganonBossKey'),
    'ganonBK_medallions':                                       ("メダル", None, 'ganonBossKey'),
    'ganonBK_stones':                                           ("精霊石", None, 'ganonBossKey'),
    'ganonBK_dungeons':                                         ("精霊石とメダル", None, 'ganonBossKey'),
    'ganonBK_tokens':                                           ("トークン", None, 'ganonBossKey'),

    'lacs_vanilla':                                             ("C闇と魂のメダルC", None, 'lacs'),
    'lacs_medallions':                                          ("メダル", None, 'lacs'),
    'lacs_stones':                                              ("精霊石", None, 'lacs'),
    'lacs_dungeons':                                            ("精霊石とメダル", None, 'lacs'),
    'lacs_tokens':                                              ("トークン", None, 'lacs'),

    'Spiritual Stone Text Start':                               ("<３つの精霊石がハイラルにある…", None, 'altar'),
    'Child Altar Text End':                                     ("<~\x07勇者なるもの、&ここに立ち、時のオカリナをもって&時の歌を　奏でよ。", None, 'altar'),
    'Adult Altar Text Start':                                   ("<世界が　魔に支配されし時、&聖地からの声に　目覚めし者たち&#\x01五つの神殿#\x00にあり…", None, 'altar'),
    'Adult Altar Text End':                                     ("<目覚めし者たち、&時の勇者を得て、魔を封じ込め…&やがて　平和の光を　取り戻す。", None, 'altar'),

    'Validation Line':                                          ("<フム…　ここまで来たのだ、&この塔でどんなものを取り忘れたか&教えてあげよう。^見よ…^", None, 'validation line'),
    'Light Arrow Location':                                     ("<フハハ…私を倒すには&", None, 'Light Arrow Location'),
    '2001':                                                     ("<@か。&シーカー族の奴らかと思っていたが、&何があったか知っているか？", None, 'ganonLine'),
    '2002':                                                     ("<外に自分の部屋のカギを&置かなければよかった。", None, 'ganonLine'),
    '2003':                                                     ("<テニスの時間のようだ。", None, 'ganonLine'),
    '2004':                                                     ("<剣で私の攻撃を跳ね返し、&光の矢で私を倒すなんて&百年早い！", None, 'ganonLine'),
    '2005':                                                     ("<何故トライデントを砂漠に&置いて行ってしまったんだ&私は。", None, 'ganonLine'),
    '2006':                                                     ("<ゼルダはあんたを&過去に戻したりしようとする&バカな小娘だ。^<こんなバカなやつを助けても&意味があるのか？", None, 'ganonLine'),
    '2007':                                                     ("<ゼルダが私よりも&優れたリーダーになれると&なぜ思う？^<ロンロン牧場を助け、&飢餓を解決し、&そして城を浮かしたのに。", None, 'ganonLine'),
    '2008':                                                     ("<新しい魔法を覚えたが、&後のために取っておくよ！", None, 'ganonLine'),
    '2009':                                                     ("<私は色んなことができる、&助かりたいのなら&手を近づけないのだな！", None, 'ganonLine'),
    '2010':                                                     ("<コホリント島で君がしたことに&比べればこんなこと&ちっぽけだろう？", None, 'ganonLine'),
    '2011':                                                     ("<今、勇者のいない&時間軸が出来上がる！", None, 'ganonLine'),
}
HT = {**hintTable}

# Separate table for goal names to avoid duplicates in the hint table.
# Link's Pocket will always be an empty goal, but it's included here to 
# prevent key errors during the dungeon reward lookup.
goalTable = {
    'Queen Gohma':                                              ("CクモCへの道", "CゴーマCへの道", "Green"),
    'King Dodongo':                                             ("C恐竜Cへの道", "CキングドドンゴCへの道", "Red"),
    'Barinade':                                                 ("C触手Cへの道", "CバリネードCへの道", "Blue"),
    'Phantom Ganon':                                            ("C人形Cへの道", "CファントムガノンCへの道", "Green"),
    'Volvagia':                                                 ("C竜Cへの道", "CヴァルバジアCへの道", "Red"),
    'Morpha':                                                   ("CアメーバCへの道", "CモーファCへの道", "Blue"),
    'Bongo Bongo':                                              ("C手Cへの道", "CボンゴボンゴCへの道", "Pink"),
    'Twinrova':                                                 ("C魔女Cへの道", "CツインローバCへの道", "Yellow"),
    'Links Pocket':                                             ("C手持ちCへの道", "C手元Cへの道", "Light Blue"),
}

# This specifies which hints will never appear due to either having known or known useless contents or due to the locations not existing.
def hintExclusions(world, clear_cache=False):
    if not clear_cache and hintExclusions.exclusions is not None:
        return hintExclusions.exclusions

    hintExclusions.exclusions = []
    hintExclusions.exclusions.extend(world.settings.disabled_locations)

    for location in world.get_locations():
        if location.locked:
            hintExclusions.exclusions.append(location.name)

    world_location_names = [
        location.name for location in world.get_locations()]

    location_hints = []
    for name in hintTable:
        hint = getHint(name, world.settings.clearer_hints)
        if type(hint) != str and any(item in hint.type for item in 
                ['always',
                 'sometimes',
                 'overworld',
                 'dungeon',
                 'song',
                 'exclude']):
            location_hints.append(hint)
    for hint in location_hints:
        if hint.name not in world_location_names and hint.name not in hintExclusions.exclusions:
            hintExclusions.exclusions.append(hint.name)

    return hintExclusions.exclusions

def nameIsLocation(name, hint_type, world):
    if isinstance(hint_type, (list, tuple)):
        for htype in hint_type:
            if htype in ['sometimes', 'song', 'overworld', 'dungeon', 'always', 'exclude'] and name not in hintExclusions(world):
                return True
    elif hint_type in ['sometimes', 'song', 'overworld', 'dungeon', 'always', 'exclude'] and name not in hintExclusions(world):
        return True
    return False

hintExclusions.exclusions = None

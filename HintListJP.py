import random

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

def getHint(name, clearer_hint=False):
    textOptions, clearText, type = hintTable[name]
    if clearer_hint:
        if clearText is None:
            if type == 'exclude':
                return HintEX(name, textOptions, type, 0)
            return Hint(name, textOptions, type, 0)
        if type == 'exclude':
            return HintEX(name, clearText, type)
        return Hint(name, clearText, type)
    else:
        if type == 'exclude':
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

    'KF Kokiri Sword Chest':                                       ("the Chidden treasure of the KokiriC is", None, 'exclude'),
    'KF Midos Top Left Chest':                                     ("the Cleader of the KokiriC hides", "Cinside Mido's houseC is", 'exclude'),
    'KF Midos Top Right Chest':                                    ("the Cleader of the KokiriC hides", "Cinside Mido's houseC is", 'exclude'),
    'KF Midos Bottom Left Chest':                                  ("the Cleader of the KokiriC hides", "Cinside Mido's houseC is", 'exclude'),
    'KF Midos Bottom Right Chest':                                 ("the Cleader of the KokiriC hides", "Cinside Mido's houseC is", 'exclude'),
    'Graveyard Shield Grave Chest':                                ("the Ctreasure of a fallen soldierC is", None, 'exclude'),
    'DMT Chest':                                                   ("hidden behind a wall on a Cmountain trailC is", None, 'exclude'),
    'GC Maze Right Chest':                                         ("in CGoron CityC explosives unlock", None, 'exclude'),
    'GC Maze Center Chest':                                        ("in CGoron CityC explosives unlock", None, 'exclude'),
    'ZD Chest':                                                    ("fire Cbeyond a waterfallC reveals", None, 'exclude'),
    'Graveyard Hookshot Chest':                                    ("a chest hidden by a Cspeedy spectreC holds", "Cdead Dampé's first prizeC is", 'exclude'),
    'GF Chest':                                                    ("on a Crooftop in the desertC lies", None, 'exclude'),
    'Kak Redead Grotto Chest':                                     ("Czombies beneath the earthC guard", None, 'exclude'),
    'SFM Wolfos Grotto Chest':                                     ("Cwolves beneath the earthC guard", None, 'exclude'),
    'HF Near Market Grotto Chest':                                 ("a Chole in a field near a drawbridgeC holds", None, 'exclude'),
    'HF Southeast Grotto Chest':                                   ("a Chole amongst trees in a fieldC holds", None, 'exclude'),
    'HF Open Grotto Chest':                                        ("an Copen hole in a fieldC holds", None, 'exclude'),
    'Kak Open Grotto Chest':                                       ("an Copen hole in a townC holds", None, 'exclude'),
    'ZR Open Grotto Chest':                                        ("a Chole along a riverC holds", None, 'exclude'),
    'KF Storms Grotto Chest':                                      ("a Chole in a forest villageC holds", None, 'exclude'),
    'LW Near Shortcuts Grotto Chest':                              ("a Chole in a wooded mazeC holds", None, 'exclude'),
    'DMT Storms Grotto Chest':                                     ("Chole flooded with rain on a mountainC holds", None, 'exclude'),
    'DMC Upper Grotto Chest':                                      ("a Chole in a volcanoC holds", None, 'exclude'),

    'ToT Light Arrows Cutscene':                                   ("the Cfinal gift of a princessC is", None, 'exclude'),
    'LW Gift from Saria':                                          (["a Cpotato hoarderC holds", "a rooty tooty Cflutey cuteyC gifts"], "CSaria's GiftC is", 'exclude'),
    'ZF Great Fairy Reward':                                       ("the Cfairy of windsC holds", None, 'exclude'),
    'HC Great Fairy Reward':                                       ("the Cfairy of fireC holds", None, 'exclude'),
    'Colossus Great Fairy Reward':                                 ("the Cfairy of loveC holds", None, 'exclude'),
    'DMT Great Fairy Reward':                                      ("a Cmagical fairyC gifts", None, 'exclude'),
    'DMC Great Fairy Reward':                                      ("a Cmagical fairyC gifts", None, 'exclude'),
    'OGC Great Fairy Reward':                                      ("the Cfairy of strengthC holds", None, 'exclude'),

    'Song from Impa':                                              ("Cdeep in a castleC, Impa teaches", None, 'exclude'),
    'Song from Malon':                                             ("Ca farm girlC sings", None, 'exclude'),
    'Song from Saria':                                             ("Cdeep in the forestC, Saria teaches", None, 'exclude'),
    'Song from Windmill':                                          ("a man Cin a windmillC is obsessed with", None, 'exclude'),

    'HC Malon Egg':                                                ("a Cgirl looking for her fatherC gives", None, 'exclude'),
    'HC Zeldas Letter':                                            ("a Cprincess in a castleC gifts", None, 'exclude'),
    'ZD Diving Minigame':                                          ("an Cunsustainable business modelC gifts", "those who Cdive for Zora rupeesC will find", 'exclude'),
    'LH Child Fishing':                                            ("Cfishing in youthC bestows", None, 'exclude'),
    'LH Adult Fishing':                                            ("Cfishing in maturityC bestows", None, 'exclude'),
    'LH Lab Dive':                                                 ("a Cdiving experimentC is rewarded with", None, 'exclude'),
    'GC Rolling Goron as Adult':                                   ("Ccomforting yourselfC provides", "Creassuring a young GoronC is rewarded with", 'exclude'),
    'Market Bombchu Bowling First Prize':                          ("the Cfirst explosive prizeC is", None, 'exclude'),
    'Market Bombchu Bowling Second Prize':                         ("the Csecond explosive prizeC is", None, 'exclude'),
    'Market Lost Dog':                                             ("Cpuppy loversC will find", "Crescuing Richard the DogC is rewarded with", 'exclude'),
    'LW Ocarina Memory Game':                                      (["the prize for a Cgame of Simon SaysC is", "a Cchild sing-a-longC holds"], "Cplaying an Ocarina in Lost WoodsC is rewarded with", 'exclude'),
    'Kak 10 Gold Skulltula Reward':                                (["C10 bug badgesC rewards", "C10 spider soulsC yields", "C10 auriferous arachnidsC lead to"], "slaying C10 Gold SkulltulasC reveals", 'exclude'),
    'Kak Man on Roof':                                             ("a Crooftop wandererC holds", None, 'exclude'),
    'ZR Magic Bean Salesman':                                      ("a seller of Ccolorful cropsC has", "a Cbean sellerC offers", 'exclude'),
    'ZR Frogs in the Rain':                                        ("Cfrogs in a stormC gift", None, 'exclude'),
    'GF HBA 1000 Points':                                          ("scoring 1000 in Chorseback archeryC grants", None, 'exclude'),
    'Market Shooting Gallery Reward':                              ("Cshooting in youthC grants", None, 'exclude'),
    'Kak Shooting Gallery Reward':                                 ("Cshooting in maturityC grants", None, 'exclude'),
    'LW Target in Woods':                                          ("shooting a Ctarget in the woodsC grants", None, 'exclude'),
    'Kak Anju as Adult':                                           ("a Cchicken caretakerC offers adults", None, 'exclude'),
    'LLR Talons Chickens':                                         ("Cfinding Super CuccosC is rewarded with", None, 'exclude'),
    'GC Rolling Goron as Child':                                   ("the prize offered by a Clarge rolling GoronC is", None, 'exclude'),
    'LH Underwater Item':                                          ("the Csunken treasure in a lakeC is", None, 'exclude'),
    'GF Gerudo Membership Card':                                   ("Crescuing captured carpentersC is rewarded with", None, 'exclude'),
    'Wasteland Bombchu Salesman':                                  ("a Ccarpet guruC sells", None, 'exclude'),

    'Kak Impas House Freestanding PoH':                            ("Cimprisoned in a houseC lies", None, 'exclude'),
    'HF Tektite Grotto Freestanding PoH':                          ("Cdeep underwater in a holeC is", None, 'exclude'),
    'Kak Windmill Freestanding PoH':                               ("on a Cwindmill ledgeC lies", None, 'exclude'),
    'Graveyard Dampe Race Freestanding PoH':                       ("Cracing a ghostC leads to", "Cdead Dampé's secondC prize is", 'exclude'),
    'LLR Freestanding PoH':                                        ("in a Cranch siloC lies", None, 'exclude'),
    'Graveyard Freestanding PoH':                                  ("a Ccrate in a graveyardC hides", None, 'exclude'),
    'Graveyard Dampe Gravedigging Tour':                           ("a Cgravekeeper digs upC", None, 'exclude'),
    'ZR Near Open Grotto Freestanding PoH':                        ("on top of a Cpillar in a riverC lies", None, 'exclude'),
    'ZR Near Domain Freestanding PoH':                             ("on a Criver ledge by a waterfallC lies", None, 'exclude'),
    'LH Freestanding PoH':                                         ("high on a Clab rooftopC one can find", None, 'exclude'),
    'ZF Iceberg Freestanding PoH':                                 ("Cfloating on iceC is", None, 'exclude'),
    'GV Waterfall Freestanding PoH':                               ("behind a Cdesert waterfallC is", None, 'exclude'),
    'GV Crate Freestanding PoH':                                   ("a Ccrate in a valleyC hides", None, 'exclude'),
    'Colossus Freestanding PoH':                                   ("on top of an Carch of stoneC lies", None, 'exclude'),
    'DMT Freestanding PoH':                                        ("above a Cmountain cavern entranceC is", None, 'exclude'),
    'DMC Wall Freestanding PoH':                                   ("nestled in a Cvolcanic wallC is", None, 'exclude'),
    'DMC Volcano Freestanding PoH':                                ("obscured by Cvolcanic ashC is", None, 'exclude'),
    'GF North F1 Carpenter':                                       ("Cdefeating Gerudo guardsC reveals", None, 'exclude'),
    'GF North F2 Carpenter':                                       ("Cdefeating Gerudo guardsC reveals", None, 'exclude'),
    'GF South F1 Carpenter':                                       ("Cdefeating Gerudo guardsC reveals", None, 'exclude'),
    'GF South F2 Carpenter':                                       ("Cdefeating Gerudo guardsC reveals", None, 'exclude'),

    'Deku Tree Map Chest':                                         ("in the Ccenter of the Deku TreeC lies", None, 'exclude'),
    'Deku Tree Slingshot Chest':                                   ("the Ctreasure guarded by a scrubC in the Deku Tree is", None, 'exclude'),
    'Deku Tree Slingshot Room Side Chest':                         ("the Ctreasure guarded by a scrubC in the Deku Tree is", None, 'exclude'),
    'Deku Tree Compass Chest':                                     ("Cpillars of woodC in the Deku Tree lead to", None, 'exclude'),
    'Deku Tree Compass Room Side Chest':                           ("Cpillars of woodC in the Deku Tree lead to", None, 'exclude'),
    'Deku Tree Basement Chest':                                    ("Cwebs in the Deku TreeC hide", None, 'exclude'),

    'Deku Tree MQ Map Chest':                                      ("in the Ccenter of the Deku TreeC lies", None, 'exclude'),
    'Deku Tree MQ Compass Chest':                                  ("a Ctreasure guarded by a large spiderC in the Deku Tree is", None, 'exclude'),
    'Deku Tree MQ Slingshot Chest':                                ("Cpillars of woodC in the Deku Tree lead to", None, 'exclude'),
    'Deku Tree MQ Slingshot Room Back Chest':                      ("Cpillars of woodC in the Deku Tree lead to", None, 'exclude'),
    'Deku Tree MQ Basement Chest':                                 ("Cwebs in the Deku TreeC hide", None, 'exclude'),
    'Deku Tree MQ Before Spinning Log Chest':                      ("Cmagical fire in the Deku TreeC leads to", None, 'exclude'),

    'Dodongos Cavern Boss Room Chest':                             ("Cabove King DodongoC lies", None, 'exclude'),

    'Dodongos Cavern Map Chest':                                   ("a Cmuddy wall in Dodongo's CavernC hides", None, 'exclude'),
    'Dodongos Cavern Compass Chest':                               ("a Cstatue in Dodongo's CavernC guards", None, 'exclude'),
    'Dodongos Cavern Bomb Flower Platform Chest':                  ("above a Cmaze of stoneC in Dodongo's Cavern lies", None, 'exclude'),
    'Dodongos Cavern Bomb Bag Chest':                              ("the Csecond lizard cavern battleC yields", None, 'exclude'),
    'Dodongos Cavern End of Bridge Chest':                         ("a Cchest at the end of a bridgeC yields", None, 'exclude'),

    'Dodongos Cavern MQ Map Chest':                                ("a Cmuddy wall in Dodongo's CavernC hides", None, 'exclude'),
    'Dodongos Cavern MQ Bomb Bag Chest':                           ("an Celevated alcoveC in Dodongo's Cavern holds", None, 'exclude'),
    'Dodongos Cavern MQ Compass Chest':                            ("Cfire-breathing lizardsC in Dodongo's Cavern guard", None, 'exclude'),
    'Dodongos Cavern MQ Larvae Room Chest':                        ("Cbaby spidersC in Dodongo's Cavern guard", None, 'exclude'),
    'Dodongos Cavern MQ Torch Puzzle Room Chest':                  ("above a Cmaze of stoneC in Dodongo's Cavern lies", None, 'exclude'),
    'Dodongos Cavern MQ Under Grave Chest':                        ("Cbeneath a headstoneC in Dodongo's Cavern lies", None, 'exclude'),

    'Jabu Jabus Belly Map Chest':                                  ("Ctentacle troubleC in a deity's belly guards", "a Cslimy thingC guards", 'exclude'),
    'Jabu Jabus Belly Compass Chest':                              ("Cbubble troubleC in a deity's belly guards", "CbubblesC guard", 'exclude'),

    'Jabu Jabus Belly MQ First Room Side Chest':                   ("shooting a Cmouth cowC reveals", None, 'exclude'),
    'Jabu Jabus Belly MQ Map Chest':                               (["Cpop rocksC hide", "an Cexplosive palateC holds"], "a Cboulder before cowsC hides", 'exclude'),
    'Jabu Jabus Belly MQ Second Room Lower Chest':                 ("near a Cspiked elevatorC lies", None, 'exclude'),
    'Jabu Jabus Belly MQ Compass Chest':                           ("a Cdrowning cowC unveils", None, 'exclude'),
    'Jabu Jabus Belly MQ Second Room Upper Chest':                 ("Cmoving anatomyC creates a path to", None, 'exclude'),
    'Jabu Jabus Belly MQ Basement Near Switches Chest':            ("a Cpair of digested cowsC hold", None, 'exclude'),
    'Jabu Jabus Belly MQ Basement Near Vines Chest':               ("a Cpair of digested cowsC hold", None, 'exclude'),
    'Jabu Jabus Belly MQ Near Boss Chest':                         ("the Cfinal cows' rewardC in a deity's belly is", None, 'exclude'),
    'Jabu Jabus Belly MQ Falling Like Like Room Chest':            ("Ccows protected by falling monstersC in a deity's belly guard", None, 'exclude'),
    'Jabu Jabus Belly MQ Boomerang Room Small Chest':              ("a school of Cstingers swallowed by a deityC guard", "a school of Cstingers swallowed by Jabu JabuC guard", 'exclude'),
    'Jabu Jabus Belly MQ Boomerang Chest':                         ("a school of Cstingers swallowed by a deityC guard", "a school of Cstingers swallowed by Jabu JabuC guard", 'exclude'),

    'Forest Temple First Room Chest':                              ("a Ctree in the Forest TempleC supports", None, 'exclude'),
    'Forest Temple First Stalfos Chest':                           ("Cdefeating enemies beneath a falling ceilingC in Forest Temple yields", None, 'exclude'),
    'Forest Temple Well Chest':                                    ("a Csunken chest deep in the woodsC contains", None, 'exclude'),
    'Forest Temple Map Chest':                                     ("a Cfiery skullC in Forest Temple guards", None, 'exclude'),
    'Forest Temple Raised Island Courtyard Chest':                 ("a Cchest on a small islandC in the Forest Temple holds", None, 'exclude'),
    'Forest Temple Falling Ceiling Room Chest':                    ("beneath a Ccheckerboard falling ceilingC lies", None, 'exclude'),
    'Forest Temple Eye Switch Chest':                              ("a Csharp eyeC will spot", "Cblocks of stoneC in the Forest Temple surround", 'exclude'),
    'Forest Temple Boss Key Chest':                                ("a Cturned trunkC contains", None, 'exclude'),
    'Forest Temple Floormaster Chest':                             ("deep in the forest Cshadows guard a chestC containing", None, 'exclude'),
    'Forest Temple Bow Chest':                                     ("an Carmy of the deadC guards", "CStalfos deep in the Forest TempleC guard", 'exclude'),
    'Forest Temple Red Poe Chest':                                 ("CJoelleC guards", "a Cred ghostC guards", 'exclude'),
    'Forest Temple Blue Poe Chest':                                ("CBethC guards", "a Cblue ghostC guards", 'exclude'),
    'Forest Temple Basement Chest':                                ("Crevolving wallsC in the Forest Temple conceal", None, 'exclude'),

    'Forest Temple MQ First Room Chest':                           ("a Ctree in the Forest TempleC supports", None, 'exclude'),
    'Forest Temple MQ Wolfos Chest':                               ("Cdefeating enemies beneath a falling ceilingC in Forest Temple yields", None, 'exclude'),
    'Forest Temple MQ Bow Chest':                                  ("an Carmy of the deadC guards", "CStalfos deep in the Forest TempleC guard", 'exclude'),
    'Forest Temple MQ Raised Island Courtyard Lower Chest':        ("a Cchest on a small islandC in the Forest Temple holds", None, 'exclude'),
    'Forest Temple MQ Raised Island Courtyard Upper Chest':        ("Chigh in a courtyardC within the Forest Temple is", None, 'exclude'),
    'Forest Temple MQ Well Chest':                                 ("a Csunken chest deep in the woodsC contains", None, 'exclude'),
    'Forest Temple MQ Map Chest':                                  ("CJoelleC guards", "a Cred ghostC guards", 'exclude'),
    'Forest Temple MQ Compass Chest':                              ("CBethC guards", "a Cblue ghostC guards", 'exclude'),
    'Forest Temple MQ Falling Ceiling Room Chest':                 ("beneath a Ccheckerboard falling ceilingC lies", None, 'exclude'),
    'Forest Temple MQ Basement Chest':                             ("Crevolving wallsC in the Forest Temple conceal", None, 'exclude'),
    'Forest Temple MQ Redead Chest':                               ("deep in the forest Cundead guard a chestC containing", None, 'exclude'),
    'Forest Temple MQ Boss Key Chest':                             ("a Cturned trunkC contains", None, 'exclude'),

    'Fire Temple Near Boss Chest':                                 ("Cnear a dragonC is", None, 'exclude'),
    'Fire Temple Flare Dancer Chest':                              ("the CFlare Dancer behind a totemC guards", None, 'exclude'),
    'Fire Temple Boss Key Chest':                                  ("a Cprison beyond a totemC holds", None, 'exclude'),
    'Fire Temple Big Lava Room Blocked Door Chest':                ("Cexplosives over a lava pitC unveil", None, 'exclude'),
    'Fire Temple Big Lava Room Lower Open Door Chest':             ("a CGoron trapped near lavaC holds", None, 'exclude'),
    'Fire Temple Boulder Maze Lower Chest':                        ("a CGoron at the end of a mazeC holds", None, 'exclude'),
    'Fire Temple Boulder Maze Upper Chest':                        ("a CGoron above a mazeC holds", None, 'exclude'),
    'Fire Temple Boulder Maze Side Room Chest':                    ("a CGoron hidden near a mazeC holds", None, 'exclude'),
    'Fire Temple Boulder Maze Shortcut Chest':                     ("a Cblocked pathC in Fire Temple holds", None, 'exclude'),
    'Fire Temple Map Chest':                                       ("a Ccaged chestC in the Fire Temple hoards", None, 'exclude'),
    'Fire Temple Compass Chest':                                   ("a Cchest in a fiery mazeC contains", None, 'exclude'),
    'Fire Temple Highest Goron Chest':                             ("a CGoron atop the Fire TempleC holds", None, 'exclude'),

    'Fire Temple MQ Near Boss Chest':                              ("Cnear a dragonC is", None, 'exclude'),
    'Fire Temple MQ Megaton Hammer Chest':                         ("the CFlare Dancer in the depths of a volcanoC guards", "the CFlare Dancer in the depths of the Fire TempleC guards", 'exclude'),
    'Fire Temple MQ Compass Chest':                                ("a Cblocked pathC in Fire Temple holds", None, 'exclude'),
    'Fire Temple MQ Lizalfos Maze Lower Chest':                    ("Ccrates in a mazeC contain", None, 'exclude'),
    'Fire Temple MQ Lizalfos Maze Upper Chest':                    ("Ccrates in a mazeC contain", None, 'exclude'),
    'Fire Temple MQ Map Room Side Chest':                          ("a Cfalling slugC in the Fire Temple guards", None, 'exclude'),
    'Fire Temple MQ Map Chest':                                    ("using a Chammer in the depths of the Fire TempleC reveals", None, 'exclude'),
    'Fire Temple MQ Boss Key Chest':                               ("Cilluminating a lava pitC reveals the path to", None, 'exclude'),
    'Fire Temple MQ Big Lava Room Blocked Door Chest':             ("Cexplosives over a lava pitC unveil", None, 'exclude'),
    'Fire Temple MQ Lizalfos Maze Side Room Chest':                ("a CGoron hidden near a mazeC holds", None, 'exclude'),
    'Fire Temple MQ Freestanding Key':                             ("hidden Cbeneath a block of stoneC lies", None, 'exclude'),

    'Water Temple Map Chest':                                      ("Crolling spikesC in the Water Temple surround", None, 'exclude'),
    'Water Temple Compass Chest':                                  ("Croaming stingers in the Water TempleC guard", None, 'exclude'),
    'Water Temple Torches Chest':                                  ("Cfire in the Water TempleC reveals", None, 'exclude'),
    'Water Temple Dragon Chest':                                   ("a Cserpent's prizeC in the Water Temple is", None, 'exclude'),
    'Water Temple Central Bow Target Chest':                       ("Cblinding an eyeC in the Water Temple leads to", None, 'exclude'),
    'Water Temple Central Pillar Chest':                           ("in the Cdepths of the Water TempleC lies", None, 'exclude'),
    'Water Temple Cracked Wall Chest':                             ("Cthrough a crackC in the Water Temple is", None, 'exclude'),
    'Water Temple Longshot Chest':                                 (["Cfacing yourselfC reveals", "a Cdark reflectionC of yourself guards"], "CDark LinkC guards", 'exclude'),

    'Water Temple MQ Central Pillar Chest':                        ("in the Cdepths of the Water TempleC lies", None, 'exclude'),
    'Water Temple MQ Boss Key Chest':                              ("fire in the Water Temple unlocks a Cvast gateC revealing a chest with", None, 'exclude'),
    'Water Temple MQ Longshot Chest':                              ("Cthrough a crackC in the Water Temple is", None, 'exclude'),
    'Water Temple MQ Compass Chest':                               ("Cfire in the Water TempleC reveals", None, 'exclude'),
    'Water Temple MQ Map Chest':                                   ("Csparring soldiersC in the Water Temple guard", None, 'exclude'),

    'Spirit Temple Child Bridge Chest':                            ("a child conquers a Cskull in green fireC in the Spirit Temple to reach", None, 'exclude'),
    'Spirit Temple Child Early Torches Chest':                     ("a child can find a Ccaged chestC in the Spirit Temple with", None, 'exclude'),
    'Spirit Temple Compass Chest':                                 ("Cacross a pit of sandC in the Spirit Temple lies", None, 'exclude'),
    'Spirit Temple Early Adult Right Chest':                       ("Cdodging boulders to collect silver rupeesC in the Spirit Temple yields", None, 'exclude'),
    'Spirit Temple First Mirror Left Chest':                       ("a Cshadow circling reflected lightC in the Spirit Temple guards", None, 'exclude'),
    'Spirit Temple First Mirror Right Chest':                      ("a Cshadow circling reflected lightC in the Spirit Temple guards", None, 'exclude'),
    'Spirit Temple Map Chest':                                     ("Cbefore a giant statueC in the Spirit Temple lies", None, 'exclude'),
    'Spirit Temple Child Climb North Chest':                       ("Clizards in the Spirit TempleC guard", None, 'exclude'),
    'Spirit Temple Child Climb East Chest':                        ("Clizards in the Spirit TempleC guard", None, 'exclude'),
    'Spirit Temple Sun Block Room Chest':                          ("Ctorchlight among BeamosC in the Spirit Temple reveals", None, 'exclude'),
    'Spirit Temple Statue Room Hand Chest':                        ("a Cstatue in the Spirit TempleC holds", None, 'exclude'),
    'Spirit Temple Statue Room Northeast Chest':                   ("on a Cledge by a statueC in the Spirit Temple rests", None, 'exclude'),
    'Spirit Temple Near Four Armos Chest':                         ("those who Cshow the light among statuesC in the Spirit Temple find", None, 'exclude'),
    'Spirit Temple Hallway Right Invisible Chest':                 ("the CEye of Truth in the Spirit TempleC reveals", None, 'exclude'),
    'Spirit Temple Hallway Left Invisible Chest':                  ("the CEye of Truth in the Spirit TempleC reveals", None, 'exclude'),
    'Spirit Temple Boss Key Chest':                                ("a Cchest engulfed in flameC in the Spirit Temple holds", None, 'exclude'),
    'Spirit Temple Topmost Chest':                                 ("those who Cshow the light above the ColossusC find", None, 'exclude'),

    'Spirit Temple MQ Entrance Front Left Chest':                  ("Clying unguardedC in the Spirit Temple is", None, 'exclude'),
    'Spirit Temple MQ Entrance Back Right Chest':                  ("a Cswitch in a pillarC within the Spirit Temple drops", None, 'exclude'),
    'Spirit Temple MQ Entrance Front Right Chest':                 ("Ccollecting rupees through a water jetC reveals", None, 'exclude'),
    'Spirit Temple MQ Entrance Back Left Chest':                   ("an Ceye blinded by stoneC within the Spirit Temple conceals", None, 'exclude'),
    'Spirit Temple MQ Map Chest':                                  ("surrounded by Cfire and wrappingsC lies", None, 'exclude'),
    'Spirit Temple MQ Map Room Enemy Chest':                       ("a child defeats a Cgauntlet of monstersC within the Spirit Temple to find", None, 'exclude'),
    'Spirit Temple MQ Child Climb North Chest':                    ("Cexplosive sunlightC within the Spirit Temple uncovers", None, 'exclude'),
    'Spirit Temple MQ Child Climb South Chest':                    ("Ctrapped by falling enemiesC within the Spirit Temple is", None, 'exclude'),
    'Spirit Temple MQ Compass Chest':                              ("Cblinding the colossusC unveils", None, 'exclude'),
    'Spirit Temple MQ Statue Room Lullaby Chest':                  ("a Croyal melody awakens the colossusC to reveal", None, 'exclude'),
    'Spirit Temple MQ Statue Room Invisible Chest':                ("the CEye of TruthC finds the colossus's hidden", None, 'exclude'),
    'Spirit Temple MQ Silver Block Hallway Chest':                 ("Cthe old hide what the young findC to reveal", None, 'exclude'),
    'Spirit Temple MQ Sun Block Room Chest':                       ("Csunlight in a maze of fireC hides", None, 'exclude'),
    'Spirit Temple MQ Leever Room Chest':                          ("Cacross a pit of sandC in the Spirit Temple lies", None, 'exclude'),
    'Spirit Temple MQ Beamos Room Chest':                          ("where Ctemporal stone blocks the pathC within the Spirit Temple lies", None, 'exclude'),
    'Spirit Temple MQ Chest Switch Chest':                         ("a Cchest of double purposeC holds", None, 'exclude'),
    'Spirit Temple MQ Boss Key Chest':                             ("a Ctemporal stone blocks the lightC leading to", None, 'exclude'),
    'Spirit Temple MQ Mirror Puzzle Invisible Chest':              ("those who Cshow the light above the ColossusC find", None, 'exclude'),

    'Shadow Temple Map Chest':                                     ("the CEye of TruthC pierces a hall of faces to reveal", None, 'exclude'),
    'Shadow Temple Hover Boots Chest':                             ("a Cnether dweller in the Shadow TempleC holds", "CDead Hand in the Shadow TempleC holds", 'exclude'),
    'Shadow Temple Compass Chest':                                 ("Cmummies revealed by the Eye of TruthC guard", None, 'exclude'),
    'Shadow Temple Early Silver Rupee Chest':                      ("Cspinning scythesC protect", None, 'exclude'),
    'Shadow Temple Invisible Blades Visible Chest':                ("Cinvisible bladesC guard", None, 'exclude'),
    'Shadow Temple Invisible Blades Invisible Chest':              ("Cinvisible bladesC guard", None, 'exclude'),
    'Shadow Temple Falling Spikes Lower Chest':                    ("Cfalling spikesC block the path to", None, 'exclude'),
    'Shadow Temple Falling Spikes Upper Chest':                    ("Cfalling spikesC block the path to", None, 'exclude'),
    'Shadow Temple Falling Spikes Switch Chest':                   ("Cfalling spikesC block the path to", None, 'exclude'),
    'Shadow Temple Invisible Spikes Chest':                        ("the Cdead roam among invisible spikesC guarding", None, 'exclude'),
    'Shadow Temple Wind Hint Chest':                               ("an Cinvisible chest guarded by the deadC holds", None, 'exclude'),
    'Shadow Temple After Wind Enemy Chest':                        ("Cmummies guarding a ferryC hide", None, 'exclude'),
    'Shadow Temple After Wind Hidden Chest':                       ("Cmummies guarding a ferryC hide", None, 'exclude'),
    'Shadow Temple Spike Walls Left Chest':                        ("Cwalls consumed by a ball of fireC reveal", None, 'exclude'),
    'Shadow Temple Boss Key Chest':                                ("Cwalls consumed by a ball of fireC reveal", None, 'exclude'),
    'Shadow Temple Freestanding Key':                              ("Cinside a burning skullC lies", None, 'exclude'),

    'Shadow Temple MQ Compass Chest':                              ("the CEye of TruthC pierces a hall of faces to reveal", None, 'exclude'),
    'Shadow Temple MQ Hover Boots Chest':                          ("CDead Hand in the Shadow TempleC holds", None, 'exclude'),
    'Shadow Temple MQ Early Gibdos Chest':                         ("Cmummies revealed by the Eye of TruthC guard", None, 'exclude'),
    'Shadow Temple MQ Map Chest':                                  ("Cspinning scythesC protect", None, 'exclude'),
    'Shadow Temple MQ Beamos Silver Rupees Chest':                 ("Ccollecting rupees in a vast cavernC with the Shadow Temple unveils", None, 'exclude'),
    'Shadow Temple MQ Falling Spikes Switch Chest':                ("Cfalling spikesC block the path to", None, 'exclude'),
    'Shadow Temple MQ Falling Spikes Lower Chest':                 ("Cfalling spikesC block the path to", None, 'exclude'),
    'Shadow Temple MQ Falling Spikes Upper Chest':                 ("Cfalling spikesC block the path to", None, 'exclude'),
    'Shadow Temple MQ Invisible Spikes Chest':                     ("the Cdead roam among invisible spikesC guarding", None, 'exclude'),
    'Shadow Temple MQ Boss Key Chest':                             ("Cwalls consumed by a ball of fireC reveal", None, 'exclude'),
    'Shadow Temple MQ Spike Walls Left Chest':                     ("Cwalls consumed by a ball of fireC reveal", None, 'exclude'),
    'Shadow Temple MQ Stalfos Room Chest':                         ("near an Cempty pedestalC within the Shadow Temple lies", None, 'exclude'),
    'Shadow Temple MQ Invisible Blades Invisible Chest':           ("Cinvisible bladesC guard", None, 'exclude'),
    'Shadow Temple MQ Invisible Blades Visible Chest':             ("Cinvisible bladesC guard", None, 'exclude'),
    'Shadow Temple MQ Wind Hint Chest':                            ("an Cinvisible chest guarded by the deadC holds", None, 'exclude'),
    'Shadow Temple MQ After Wind Hidden Chest':                    ("Cmummies guarding a ferryC hide", None, 'exclude'),
    'Shadow Temple MQ After Wind Enemy Chest':                     ("Cmummies guarding a ferryC hide", None, 'exclude'),
    'Shadow Temple MQ Near Ship Invisible Chest':                  ("Ccaged near a shipC lies", None, 'exclude'),
    'Shadow Temple MQ Freestanding Key':                           ("Cbehind three burning skullsC lies", None, 'exclude'),

    'Bottom of the Well Front Left Fake Wall Chest':               ("the CEye of Truth in the wellC reveals", None, 'exclude'),
    'Bottom of the Well Front Center Bombable Chest':              ("Cgruesome debrisC in the well hides", None, 'exclude'),
    'Bottom of the Well Right Bottom Fake Wall Chest':             ("the CEye of Truth in the wellC reveals", None, 'exclude'),
    'Bottom of the Well Compass Chest':                            ("a Chidden entrance to a cageC in the well leads to", None, 'exclude'),
    'Bottom of the Well Center Skulltula Chest':                   ("a Cspider guarding a cageC in the well protects", None, 'exclude'),
    'Bottom of the Well Back Left Bombable Chest':                 ("Cgruesome debrisC in the well hides", None, 'exclude'),
    'Bottom of the Well Invisible Chest':                          ("CDead Hand's invisible secretC is", None, 'exclude'),
    'Bottom of the Well Underwater Front Chest':                   ("a Croyal melody in the wellC uncovers", None, 'exclude'),
    'Bottom of the Well Underwater Left Chest':                    ("a Croyal melody in the wellC uncovers", None, 'exclude'),
    'Bottom of the Well Map Chest':                                ("in the Cdepths of the wellC lies", None, 'exclude'),
    'Bottom of the Well Fire Keese Chest':                         ("Cperilous pitsC in the well guard the path to", None, 'exclude'),
    'Bottom of the Well Like Like Chest':                          ("Clocked in a cageC in the well lies", None, 'exclude'),
    'Bottom of the Well Freestanding Key':                         ("Cinside a coffinC hides", None, 'exclude'),

    'Bottom of the Well MQ Map Chest':                             ("a Croyal melody in the wellC uncovers", None, 'exclude'),
    'Bottom of the Well MQ Lens of Truth Chest':                   ("an Carmy of the deadC in the well guards", None, 'exclude'),
    'Bottom of the Well MQ Dead Hand Freestanding Key':            ("CDead Hand's explosive secretC is", None, 'exclude'),
    'Bottom of the Well MQ East Inner Room Freestanding Key':      ("an Cinvisible path in the wellC leads to", None, 'exclude'),

    'Ice Cavern Map Chest':                                        ("Cwinds of iceC surround", None, 'exclude'),
    'Ice Cavern Compass Chest':                                    ("a Cwall of iceC protects", None, 'exclude'),
    'Ice Cavern Iron Boots Chest':                                 ("a Cmonster in a frozen cavernC guards", None, 'exclude'),
    'Ice Cavern Freestanding PoH':                                 ("a Cwall of iceC protects", None, 'exclude'),

    'Ice Cavern MQ Iron Boots Chest':                              ("a Cmonster in a frozen cavernC guards", None, 'exclude'),
    'Ice Cavern MQ Compass Chest':                                 ("Cwinds of iceC surround", None, 'exclude'),
    'Ice Cavern MQ Map Chest':                                     ("a Cwall of iceC protects", None, 'exclude'),
    'Ice Cavern MQ Freestanding PoH':                              ("Cwinds of iceC surround", None, 'exclude'),

    'Gerudo Training Ground Lobby Left Chest':                     ("a Cblinded eye in the Gerudo Training GroundC drops", None, 'exclude'),
    'Gerudo Training Ground Lobby Right Chest':                    ("a Cblinded eye in the Gerudo Training GroundC drops", None, 'exclude'),
    'Gerudo Training Ground Stalfos Chest':                        ("Csoldiers walking on shifting sandsC in the Gerudo Training Ground guard", None, 'exclude'),
    'Gerudo Training Ground Beamos Chest':                         ("Creptilian warriorsC in the Gerudo Training Ground protect", None, 'exclude'),
    'Gerudo Training Ground Hidden Ceiling Chest':                 ("the CEye of TruthC in the Gerudo Training Ground reveals", None, 'exclude'),
    'Gerudo Training Ground Maze Path First Chest':                ("the first prize of Cthe thieves' trainingC is", None, 'exclude'),
    'Gerudo Training Ground Maze Path Second Chest':               ("the second prize of Cthe thieves' trainingC is", None, 'exclude'),
    'Gerudo Training Ground Maze Path Third Chest':                ("the third prize of Cthe thieves' trainingC is", None, 'exclude'),
    'Gerudo Training Ground Maze Right Central Chest':             ("the CSong of TimeC in the Gerudo Training Ground leads to", None, 'exclude'),
    'Gerudo Training Ground Maze Right Side Chest':                ("the CSong of TimeC in the Gerudo Training Ground leads to", None, 'exclude'),
    'Gerudo Training Ground Hammer Room Clear Chest':              ("Cfiery foesC in the Gerudo Training Ground guard", None, 'exclude'),
    'Gerudo Training Ground Hammer Room Switch Chest':             ("Cengulfed in flameC where thieves train lies", None, 'exclude'),
    'Gerudo Training Ground Eye Statue Chest':                     ("thieves Cblind four facesC to find", None, 'exclude'),
    'Gerudo Training Ground Near Scarecrow Chest':                 ("thieves Cblind four facesC to find", None, 'exclude'),
    'Gerudo Training Ground Before Heavy Block Chest':             ("Cbefore a block of silverC thieves can find", None, 'exclude'),
    'Gerudo Training Ground Heavy Block First Chest':              ("a Cfeat of strengthC rewards thieves with", None, 'exclude'),
    'Gerudo Training Ground Heavy Block Second Chest':             ("a Cfeat of strengthC rewards thieves with", None, 'exclude'),
    'Gerudo Training Ground Heavy Block Third Chest':              ("a Cfeat of strengthC rewards thieves with", None, 'exclude'),
    'Gerudo Training Ground Heavy Block Fourth Chest':             ("a Cfeat of strengthC rewards thieves with", None, 'exclude'),
    'Gerudo Training Ground Freestanding Key':                     ("the CSong of TimeC in the Gerudo Training Ground leads to", None, 'exclude'),

    'Gerudo Training Ground MQ Lobby Right Chest':                 ("Cthieves prepare for trainingC with", None, 'exclude'),
    'Gerudo Training Ground MQ Lobby Left Chest':                  ("Cthieves prepare for trainingC with", None, 'exclude'),
    'Gerudo Training Ground MQ First Iron Knuckle Chest':          ("Csoldiers walking on shifting sandsC in the Gerudo Training Ground guard", None, 'exclude'),
    'Gerudo Training Ground MQ Before Heavy Block Chest':          ("Cbefore a block of silverC thieves can find", None, 'exclude'),
    'Gerudo Training Ground MQ Eye Statue Chest':                  ("thieves Cblind four facesC to find", None, 'exclude'),
    'Gerudo Training Ground MQ Flame Circle Chest':                ("Cengulfed in flameC where thieves train lies", None, 'exclude'),
    'Gerudo Training Ground MQ Second Iron Knuckle Chest':         ("Cfiery foesC in the Gerudo Training Ground guard", None, 'exclude'),
    'Gerudo Training Ground MQ Dinolfos Chest':                    ("Creptilian warriorsC in the Gerudo Training Ground protect", None, 'exclude'),
    'Gerudo Training Ground MQ Maze Right Central Chest':          ("a Cpath of fireC leads thieves to", None, 'exclude'),
    'Gerudo Training Ground MQ Maze Path First Chest':             ("the first prize of Cthe thieves' trainingC is", None, 'exclude'),
    'Gerudo Training Ground MQ Maze Right Side Chest':             ("a Cpath of fireC leads thieves to", None, 'exclude'),
    'Gerudo Training Ground MQ Maze Path Third Chest':             ("the third prize of Cthe thieves' trainingC is", None, 'exclude'),
    'Gerudo Training Ground MQ Maze Path Second Chest':            ("the second prize of Cthe thieves' trainingC is", None, 'exclude'),
    'Gerudo Training Ground MQ Hidden Ceiling Chest':              ("the CEye of TruthC in the Gerudo Training Ground reveals", None, 'exclude'),
    'Gerudo Training Ground MQ Heavy Block Chest':                 ("a Cfeat of strengthC rewards thieves with", None, 'exclude'),

    'Ganons Tower Boss Key Chest':                                 ("the CEvil KingC hoards", None, 'exclude'),

    'Ganons Castle Forest Trial Chest':                            ("the Ctest of the wildsC holds", None, 'exclude'),
    'Ganons Castle Water Trial Left Chest':                        ("the Ctest of the seasC holds", None, 'exclude'),
    'Ganons Castle Water Trial Right Chest':                       ("the Ctest of the seasC holds", None, 'exclude'),
    'Ganons Castle Shadow Trial Front Chest':                      ("Cmusic in the test of darknessC unveils", None, 'exclude'),
    'Ganons Castle Shadow Trial Golden Gauntlets Chest':           ("Clight in the test of darknessC unveils", None, 'exclude'),
    'Ganons Castle Spirit Trial Crystal Switch Chest':             ("the Ctest of the sandsC holds", None, 'exclude'),
    'Ganons Castle Spirit Trial Invisible Chest':                  ("the Ctest of the sandsC holds", None, 'exclude'),
    'Ganons Castle Light Trial First Left Chest':                  ("the Ctest of radianceC holds", None, 'exclude'),
    'Ganons Castle Light Trial Second Left Chest':                 ("the Ctest of radianceC holds", None, 'exclude'),
    'Ganons Castle Light Trial Third Left Chest':                  ("the Ctest of radianceC holds", None, 'exclude'),
    'Ganons Castle Light Trial First Right Chest':                 ("the Ctest of radianceC holds", None, 'exclude'),
    'Ganons Castle Light Trial Second Right Chest':                ("the Ctest of radianceC holds", None, 'exclude'),
    'Ganons Castle Light Trial Third Right Chest':                 ("the Ctest of radianceC holds", None, 'exclude'),
    'Ganons Castle Light Trial Invisible Enemies Chest':           ("the Ctest of radianceC holds", None, 'exclude'),
    'Ganons Castle Light Trial Lullaby Chest':                     ("Cmusic in the test of radianceC reveals", None, 'exclude'),

    'Ganons Castle MQ Water Trial Chest':                          ("the Ctest of the seasC holds", None, 'exclude'),
    'Ganons Castle MQ Forest Trial Eye Switch Chest':              ("the Ctest of the wildsC holds", None, 'exclude'),
    'Ganons Castle MQ Forest Trial Frozen Eye Switch Chest':       ("the Ctest of the wildsC holds", None, 'exclude'),
    'Ganons Castle MQ Light Trial Lullaby Chest':                  ("Cmusic in the test of radianceC reveals", None, 'exclude'),
    'Ganons Castle MQ Shadow Trial Bomb Flower Chest':             ("the Ctest of darknessC holds", None, 'exclude'),
    'Ganons Castle MQ Shadow Trial Eye Switch Chest':              ("the Ctest of darknessC holds", None, 'exclude'),
    'Ganons Castle MQ Spirit Trial Golden Gauntlets Chest':        ("Creflected light in the test of the sandsC reveals", None, 'exclude'),
    'Ganons Castle MQ Spirit Trial Sun Back Right Chest':          ("Creflected light in the test of the sandsC reveals", None, 'exclude'),
    'Ganons Castle MQ Spirit Trial Sun Back Left Chest':           ("Creflected light in the test of the sandsC reveals", None, 'exclude'),
    'Ganons Castle MQ Spirit Trial Sun Front Left Chest':          ("Creflected light in the test of the sandsC reveals", None, 'exclude'),
    'Ganons Castle MQ Spirit Trial First Chest':                   ("Creflected light in the test of the sandsC reveals", None, 'exclude'),
    'Ganons Castle MQ Spirit Trial Invisible Chest':               ("Creflected light in the test of the sandsC reveals", None, 'exclude'),
    'Ganons Castle MQ Forest Trial Freestanding Key':              ("the Ctest of the wildsC holds", None, 'exclude'),

    'Deku Tree Queen Gohma Heart':                                 ("the CParasitic Armored ArachnidC holds", "CQueen GohmaC holds", 'exclude'),
    'Dodongos Cavern King Dodongo Heart':                          ("the CInfernal DinosaurC holds", "CKing DodongoC holds", 'exclude'),
    'Jabu Jabus Belly Barinade Heart':                             ("the CBio-Electric AnemoneC holds", "CBarinadeC holds", 'exclude'),
    'Forest Temple Phantom Ganon Heart':                           ("the CEvil Spirit from BeyondC holds", "CPhantom GanonC holds", 'exclude'),
    'Fire Temple Volvagia Heart':                                  ("the CSubterranean Lava DragonC holds", "CVolvagiaC holds", 'exclude'),
    'Water Temple Morpha Heart':                                   ("the CGiant Aquatic AmoebaC holds", "CMorphaC holds", 'exclude'),
    'Spirit Temple Twinrova Heart':                                ("the CSorceress SistersC hold", "CTwinrovaC holds", 'exclude'),
    'Shadow Temple Bongo Bongo Heart':                             ("the CPhantom Shadow BeastC holds", "CBongo BongoC holds", 'exclude'),

    'Deku Tree GS Basement Back Room':                             ("a Cspider deep within the Deku TreeC hides", None, 'exclude'),
    'Deku Tree GS Basement Gate':                                  ("a Cweb protects a spiderC within the Deku Tree holding", None, 'exclude'),
    'Deku Tree GS Basement Vines':                                 ("a Cweb protects a spiderC within the Deku Tree holding", None, 'exclude'),
    'Deku Tree GS Compass Room':                                   ("a Cspider atop the Deku TreeC holds", None, 'exclude'),

    'Deku Tree MQ GS Lobby':                                       ("a Cspider in a crateC within the Deku Tree hides", None, 'exclude'),
    'Deku Tree MQ GS Compass Room':                                ("a Cwall of rock protects a spiderC within the Deku Tree holding", None, 'exclude'),
    'Deku Tree MQ GS Basement Back Room':                          ("a Cspider deep within the Deku TreeC hides", None, 'exclude'),

    'Dodongos Cavern GS Vines Above Stairs':                       ("a Cspider entangled in vinesC in Dodongo's Cavern guards", None, 'exclude'),
    'Dodongos Cavern GS Scarecrow':                                ("a Cspider among explosive slugsC hides", None, 'exclude'),
    'Dodongos Cavern GS Alcove Above Stairs':                      ("a Cspider just out of reachC in Dodongo's Cavern holds", None, 'exclude'),
    'Dodongos Cavern GS Back Room':                                ("a Cspider behind a statueC in Dodongo's Cavern holds", None, 'exclude'),
    'Dodongos Cavern GS Side Room Near Lower Lizalfos':            ("a Cspider among batsC in Dodongo's Cavern holds", None, 'exclude'),

    'Dodongos Cavern MQ GS Scrub Room':                            ("a Cspider high on a wallC in Dodongo's Cavern holds", None, 'exclude'),
    'Dodongos Cavern MQ GS Lizalfos Room':                         ("a Cspider on top of a pillar of rockC in Dodongo's Cavern holds", None, 'exclude'),
    'Dodongos Cavern MQ GS Larvae Room':                           ("a Cspider in a crateC in Dodongo's Cavern holds", None, 'exclude'),
    'Dodongos Cavern MQ GS Back Area':                             ("a Cspider among gravesC in Dodongo's Cavern holds", None, 'exclude'),

    'Jabu Jabus Belly GS Lobby Basement Lower':                    ("a Cspider resting near a princessC in Jabu Jabu's Belly holds", None, 'exclude'),
    'Jabu Jabus Belly GS Lobby Basement Upper':                    ("a Cspider resting near a princessC in Jabu Jabu's Belly holds", None, 'exclude'),
    'Jabu Jabus Belly GS Near Boss':                               ("Cjellyfish surround a spiderC holding", None, 'exclude'),
    'Jabu Jabus Belly GS Water Switch Room':                       ("a Cspider guarded by a school of stingersC in Jabu Jabu's Belly holds", None, 'exclude'),

    'Jabu Jabus Belly MQ GS Tailpasaran Room':                     ("a Cspider surrounded by electricityC in Jabu Jabu's Belly holds", None, 'exclude'),
    'Jabu Jabus Belly MQ GS Boomerang Chest Room':                 ("a Cspider guarded by a school of stingersC in Jabu Jabu's Belly holds", None, 'exclude'),
    'Jabu Jabus Belly MQ GS Near Boss':                            ("a Cspider in a web within Jabu Jabu's BellyC holds", None, 'exclude'),

    'Forest Temple GS Raised Island Courtyard':                    ("a Cspider on a small islandC in the Forest Temple holds", None, 'exclude'),
    'Forest Temple GS First Room':                                 ("a Cspider high on a wall of vinesC in the Forest Temple holds", None, 'exclude'),
    'Forest Temple GS Level Island Courtyard':                     ("Cstone columnsC lead to a spider in the Forest Temple hiding", None, 'exclude'),
    'Forest Temple GS Lobby':                                      ("a Cspider among ghostsC in the Forest Temple guards", None, 'exclude'),
    'Forest Temple GS Basement':                                   ("a Cspider within revolving wallsC in the Forest Temple holds", None, 'exclude'),

    'Forest Temple MQ GS First Hallway':                           ("an Civy-hidden spiderC in the Forest Temple hoards", None, 'exclude'),
    'Forest Temple MQ GS Block Push Room':                         ("a Cspider in a hidden nookC within the Forest Temple holds", None, 'exclude'),
    'Forest Temple MQ GS Raised Island Courtyard':                 ("a Cspider on an archC in the Forest Temple holds", None, 'exclude'),
    'Forest Temple MQ GS Level Island Courtyard':                  ("a Cspider on a ledgeC in the Forest Temple holds", None, 'exclude'),
    'Forest Temple MQ GS Well':                                    ("Cdraining a wellC in Forest Temple uncovers a spider with", None, 'exclude'),

    'Fire Temple GS Song of Time Room':                            ("Ceight tiles of maliceC guard a spider holding", None, 'exclude'),
    'Fire Temple GS Boss Key Loop':                                ("Cfive tiles of maliceC guard a spider holding", None, 'exclude'),
    'Fire Temple GS Boulder Maze':                                 ("Cexplosives in a mazeC unveil a spider hiding", None, 'exclude'),
    'Fire Temple GS Scarecrow Top':                                ("a Cspider-friendly scarecrowC atop a volcano hides", "a Cspider-friendly scarecrowC atop the Fire Temple hides", 'exclude'),
    'Fire Temple GS Scarecrow Climb':                              ("a Cspider-friendly scarecrowC atop a volcano hides", "a Cspider-friendly scarecrowC atop the Fire Temple hides", 'exclude'),

    'Fire Temple MQ GS Above Fire Wall Maze':                      ("a Cspider above a fiery mazeC holds", None, 'exclude'),
    'Fire Temple MQ GS Fire Wall Maze Center':                     ("a Cspider within a fiery mazeC holds", None, 'exclude'),
    'Fire Temple MQ GS Big Lava Room Open Door':                   ("a CGoron trapped near lavaC befriended a spider with", None, 'exclude'),
    'Fire Temple MQ GS Fire Wall Maze Side Room':                  ("a Cspider beside a fiery mazeC holds", None, 'exclude'),

    'Water Temple GS Falling Platform Room':                       ("a Cspider over a waterfallC in the Water Temple holds", None, 'exclude'),
    'Water Temple GS Central Pillar':                              ("a Cspider in the center of the Water TempleC holds", None, 'exclude'),
    'Water Temple GS Near Boss Key Chest':                         ("a spider protected by Crolling boulders under the lakeC hides", "a spider protected by Crolling boulders in the Water TempleC hides", 'exclude'),
    'Water Temple GS River':                                       ("a Cspider over a riverC in the Water Temple holds", None, 'exclude'),

    'Water Temple MQ GS Before Upper Water Switch':                ("Cbeyond a pit of lizardsC is a spider holding", None, 'exclude'),
    'Water Temple MQ GS Lizalfos Hallway':                         ("Clizards guard a spiderC in the Water Temple with", None, 'exclude'),
    'Water Temple MQ GS River':                                    ("a Cspider over a riverC in the Water Temple holds", None, 'exclude'),

    'Spirit Temple GS Hall After Sun Block Room':                  ("a spider in the Chall of a knightC guards", None, 'exclude'),
    'Spirit Temple GS Boulder Room':                               ("a Cspider behind a temporal stoneC in the Spirit Temple yields", None, 'exclude'),
    'Spirit Temple GS Lobby':                                      ("a Cspider beside a statueC holds", None, 'exclude'),
    'Spirit Temple GS Sun on Floor Room':                          ("a Cspider at the top of a deep shaftC in the Spirit Temple holds", None, 'exclude'),
    'Spirit Temple GS Metal Fence':                                ("a child defeats a Cspider among batsC in the Spirit Temple to gain", None, 'exclude'),

    'Spirit Temple MQ GS Leever Room':                             ("Cabove a pit of sandC in the Spirit Temple hides", None, 'exclude'),
    'Spirit Temple MQ GS Nine Thrones Room West':                  ("a spider in the Chall of a knightC guards", None, 'exclude'),
    'Spirit Temple MQ GS Nine Thrones Room North':                 ("a spider in the Chall of a knightC guards", None, 'exclude'),
    'Spirit Temple MQ GS Sun Block Room':                          ("Cupon a web of glassC in the Spirit Temple sits a spider holding", None, 'exclude'),

    'Shadow Temple GS Single Giant Pot':                           ("Cbeyond a burning skullC lies a spider with", None, 'exclude'),
    'Shadow Temple GS Falling Spikes Room':                        ("a Cspider beyond falling spikesC holds", None, 'exclude'),
    'Shadow Temple GS Triple Giant Pot':                           ("Cbeyond three burning skullsC lies a spider with", None, 'exclude'),
    'Shadow Temple GS Like Like Room':                             ("a spider guarded by Cinvisible bladesC holds", None, 'exclude'),
    'Shadow Temple GS Near Ship':                                  ("a spider near a Cdocked shipC hoards", None, 'exclude'),

    'Shadow Temple MQ GS Falling Spikes Room':                     ("a Cspider beyond falling spikesC holds", None, 'exclude'),
    'Shadow Temple MQ GS Wind Hint Room':                          ("a Cspider amidst roaring windsC in the Shadow Temple holds", None, 'exclude'),
    'Shadow Temple MQ GS After Wind':                              ("a Cspider beneath gruesome debrisC in the Shadow Temple hides", None, 'exclude'),
    'Shadow Temple MQ GS After Ship':                              ("a Cfallen statueC reveals a spider with", None, 'exclude'),
    'Shadow Temple MQ GS Near Boss':                               ("a Csuspended spiderC guards", None, 'exclude'),

    'Bottom of the Well GS Like Like Cage':                        ("a Cspider locked in a cageC in the well holds", None, 'exclude'),
    'Bottom of the Well GS East Inner Room':                       ("an Cinvisible path in the wellC leads to", None, 'exclude'),
    'Bottom of the Well GS West Inner Room':                       ("a Cspider locked in a cryptC within the well guards", None, 'exclude'),

    'Bottom of the Well MQ GS Basement':                           ("a Cgauntlet of invisible spidersC protects", None, 'exclude'),
    'Bottom of the Well MQ GS Coffin Room':                        ("a Cspider crawling near the deadC in the well holds", None, 'exclude'),
    'Bottom of the Well MQ GS West Inner Room':                    ("a Cspider locked in a cryptC within the well guards", None, 'exclude'),

    'Ice Cavern GS Push Block Room':                               ("a Cspider above icy pitsC holds", None, 'exclude'),
    'Ice Cavern GS Spinning Scythe Room':                          ("Cspinning iceC guards a spider holding", None, 'exclude'),
    'Ice Cavern GS Heart Piece Room':                              ("a Cspider behind a wall of iceC hides", None, 'exclude'),

    'Ice Cavern MQ GS Scarecrow':                                  ("a Cspider above icy pitsC holds", None, 'exclude'),
    'Ice Cavern MQ GS Ice Block':                                  ("a Cweb of iceC surrounds a spider with", None, 'exclude'),
    'Ice Cavern MQ GS Red Ice':                                    ("a Cspider in fiery iceC hoards", None, 'exclude'),

    'HF GS Near Kak Grotto':                                       ("a Cspider-guarded spider in a holeC hoards", None, 'exclude'),

    'LLR GS Back Wall':                                            ("night reveals a Cspider in a ranchC holding", None, 'exclude'),
    'LLR GS Rain Shed':                                            ("night reveals a Cspider in a ranchC holding", None, 'exclude'),
    'LLR GS House Window':                                         ("night reveals a Cspider in a ranchC holding", None, 'exclude'),
    'LLR GS Tree':                                                 ("a spider hiding in a Cranch treeC holds", None, 'exclude'),

    'KF GS Bean Patch':                                            ("a Cspider buried in a forestC holds", None, 'exclude'),
    'KF GS Know It All House':                                     ("night in the past reveals a Cspider in a forestC holding", None, 'exclude'),
    'KF GS House of Twins':                                        ("night in the future reveals a Cspider in a forestC holding", None, 'exclude'),

    'LW GS Bean Patch Near Bridge':                                ("a Cspider buried deep in a forest mazeC holds", None, 'exclude'),
    'LW GS Bean Patch Near Theater':                               ("a Cspider buried deep in a forest mazeC holds", None, 'exclude'),
    'LW GS Above Theater':                                         ("night reveals a Cspider deep in a forest mazeC holding", None, 'exclude'),
    'SFM GS':                                                      ("night reveals a Cspider in a forest meadowC holding", None, 'exclude'),

    'OGC GS':                                                      ("a Cspider outside a tyrant's towerC holds", None, 'exclude'),
    'HC GS Tree':                                                  ("a spider hiding in a Ctree outside of a castleC holds", None, 'exclude'),
    'Market GS Guard House':                                       ("a Cspider in a guarded crateC holds", None, 'exclude'),

    'DMC GS Bean Patch':                                           ("a Cspider buried in a volcanoC holds", None, 'exclude'),

    'DMT GS Bean Patch':                                           ("a Cspider buried outside a cavernC holds", None, 'exclude'),
    'DMT GS Near Kak':                                             ("a Cspider hidden in a mountain nookC holds", None, 'exclude'),
    'DMT GS Above Dodongos Cavern':                                ("the hammer reveals a Cspider on a mountainC holding", None, 'exclude'),
    'DMT GS Falling Rocks Path':                                   ("the hammer reveals a Cspider on a mountainC holding", None, 'exclude'),

    'GC GS Center Platform':                                       ("a Csuspended spiderC in Goron City holds", None, 'exclude'),
    'GC GS Boulder Maze':                                          ("a spider in a CGoron City crateC holds", None, 'exclude'),

    'Kak GS House Under Construction':                             ("night in the past reveals a Cspider in a townC holding", None, 'exclude'),
    'Kak GS Skulltula House':                                      ("night in the past reveals a Cspider in a townC holding", None, 'exclude'),
    'Kak GS Guards House':                                         ("night in the past reveals a Cspider in a townC holding", None, 'exclude'),
    'Kak GS Tree':                                                 ("night in the past reveals a Cspider in a townC holding", None, 'exclude'),
    'Kak GS Watchtower':                                           ("night in the past reveals a Cspider in a townC holding", None, 'exclude'),
    'Kak GS Above Impas House':                                    ("night in the future reveals a Cspider in a townC holding", None, 'exclude'),

    'Graveyard GS Wall':                                           ("night reveals a Cspider in a graveyardC holding", None, 'exclude'),
    'Graveyard GS Bean Patch':                                     ("a Cspider buried in a graveyardC holds", None, 'exclude'),

    'ZR GS Ladder':                                                ("night in the past reveals a Cspider in a riverC holding", None, 'exclude'),
    'ZR GS Tree':                                                  ("a spider hiding in a Ctree by a riverC holds", None, 'exclude'),
    'ZR GS Above Bridge':                                          ("night in the future reveals a Cspider in a riverC holding", None, 'exclude'),
    'ZR GS Near Raised Grottos':                                   ("night in the future reveals a Cspider in a riverC holding", None, 'exclude'),

    'ZD GS Frozen Waterfall':                                      ("night reveals a Cspider by a frozen waterfallC holding", None, 'exclude'),
    'ZF GS Above the Log':                                         ("night reveals a Cspider near a deityC holding", None, 'exclude'),
    'ZF GS Tree':                                                  ("a spider hiding in a Ctree near a deityC holds", None, 'exclude'),

    'LH GS Bean Patch':                                            ("a Cspider buried by a lakeC holds", None, 'exclude'),
    'LH GS Small Island':                                          ("night reveals a Cspider by a lakeC holding", None, 'exclude'),
    'LH GS Lab Wall':                                              ("night reveals a Cspider by a lakeC holding", None, 'exclude'),
    'LH GS Lab Crate':                                             ("a spider deed underwater in a Clab crateC holds", None, 'exclude'),
    'LH GS Tree':                                                  ("night reveals a Cspider by a lake high in a treeC holding", None, 'exclude'),

    'GV GS Bean Patch':                                            ("a Cspider buried in a valleyC holds", None, 'exclude'),
    'GV GS Small Bridge':                                          ("night in the past reveals a Cspider in a valleyC holding", None, 'exclude'),
    'GV GS Pillar':                                                ("night in the future reveals a Cspider in a valleyC holding", None, 'exclude'),
    'GV GS Behind Tent':                                           ("night in the future reveals a Cspider in a valleyC holding", None, 'exclude'),

    'GF GS Archery Range':                                         ("night reveals a Cspider in a fortressC holding", None, 'exclude'),
    'GF GS Top Floor':                                             ("night reveals a Cspider in a fortressC holding", None, 'exclude'),

    'Colossus GS Bean Patch':                                      ("a Cspider buried in the desertC holds", None, 'exclude'),
    'Colossus GS Hill':                                            ("night reveals a Cspider deep in the desertC holding", None, 'exclude'),
    'Colossus GS Tree':                                            ("night reveals a Cspider deep in the desertC holding", None, 'exclude'),

    'KF Shop Item 1':                                              ("a Cchild shopkeeperC sells", None, 'exclude'),
    'KF Shop Item 2':                                              ("a Cchild shopkeeperC sells", None, 'exclude'),
    'KF Shop Item 3':                                              ("a Cchild shopkeeperC sells", None, 'exclude'),
    'KF Shop Item 4':                                              ("a Cchild shopkeeperC sells", None, 'exclude'),
    'KF Shop Item 5':                                              ("a Cchild shopkeeperC sells", None, 'exclude'),
    'KF Shop Item 6':                                              ("a Cchild shopkeeperC sells", None, 'exclude'),
    'KF Shop Item 7':                                              ("a Cchild shopkeeperC sells", None, 'exclude'),
    'KF Shop Item 8':                                              ("a Cchild shopkeeperC sells", None, 'exclude'),

    'Kak Potion Shop Item 1':                                      ("a Cpotion sellerC offers", "the CKakariko Potion ShopC offers", 'exclude'),
    'Kak Potion Shop Item 2':                                      ("a Cpotion sellerC offers", "the CKakariko Potion ShopC offers", 'exclude'),
    'Kak Potion Shop Item 3':                                      ("a Cpotion sellerC offers", "the CKakariko Potion ShopC offers", 'exclude'),
    'Kak Potion Shop Item 4':                                      ("a Cpotion sellerC offers", "the CKakariko Potion ShopC offers", 'exclude'),
    'Kak Potion Shop Item 5':                                      ("a Cpotion sellerC offers", "the CKakariko Potion ShopC offers", 'exclude'),
    'Kak Potion Shop Item 6':                                      ("a Cpotion sellerC offers", "the CKakariko Potion ShopC offers", 'exclude'),
    'Kak Potion Shop Item 7':                                      ("a Cpotion sellerC offers", "the CKakariko Potion ShopC offers", 'exclude'),
    'Kak Potion Shop Item 8':                                      ("a Cpotion sellerC offers", "the CKakariko Potion ShopC offers", 'exclude'),

    'Market Bombchu Shop Item 1':                                  ("a CBombchu merchantC sells", None, 'exclude'),
    'Market Bombchu Shop Item 2':                                  ("a CBombchu merchantC sells", None, 'exclude'),
    'Market Bombchu Shop Item 3':                                  ("a CBombchu merchantC sells", None, 'exclude'),
    'Market Bombchu Shop Item 4':                                  ("a CBombchu merchantC sells", None, 'exclude'),
    'Market Bombchu Shop Item 5':                                  ("a CBombchu merchantC sells", None, 'exclude'),
    'Market Bombchu Shop Item 6':                                  ("a CBombchu merchantC sells", None, 'exclude'),
    'Market Bombchu Shop Item 7':                                  ("a CBombchu merchantC sells", None, 'exclude'),
    'Market Bombchu Shop Item 8':                                  ("a CBombchu merchantC sells", None, 'exclude'),

    'Market Potion Shop Item 1':                                   ("a Cpotion sellerC offers", "the CMarket Potion ShopC offers", 'exclude'),
    'Market Potion Shop Item 2':                                   ("a Cpotion sellerC offers", "the CMarket Potion ShopC offers", 'exclude'),
    'Market Potion Shop Item 3':                                   ("a Cpotion sellerC offers", "the CMarket Potion ShopC offers", 'exclude'),
    'Market Potion Shop Item 4':                                   ("a Cpotion sellerC offers", "the CMarket Potion ShopC offers", 'exclude'),
    'Market Potion Shop Item 5':                                   ("a Cpotion sellerC offers", "the CMarket Potion ShopC offers", 'exclude'),
    'Market Potion Shop Item 6':                                   ("a Cpotion sellerC offers", "the CMarket Potion ShopC offers", 'exclude'),
    'Market Potion Shop Item 7':                                   ("a Cpotion sellerC offers", "the CMarket Potion ShopC offers", 'exclude'),
    'Market Potion Shop Item 8':                                   ("a Cpotion sellerC offers", "the CMarket Potion ShopC offers", 'exclude'),

    'Market Bazaar Item 1':                                        ("the CMarket BazaarC offers", None, 'exclude'),
    'Market Bazaar Item 2':                                        ("the CMarket BazaarC offers", None, 'exclude'),
    'Market Bazaar Item 3':                                        ("the CMarket BazaarC offers", None, 'exclude'),
    'Market Bazaar Item 4':                                        ("the CMarket BazaarC offers", None, 'exclude'),
    'Market Bazaar Item 5':                                        ("the CMarket BazaarC offers", None, 'exclude'),
    'Market Bazaar Item 6':                                        ("the CMarket BazaarC offers", None, 'exclude'),
    'Market Bazaar Item 7':                                        ("the CMarket BazaarC offers", None, 'exclude'),
    'Market Bazaar Item 8':                                        ("the CMarket BazaarC offers", None, 'exclude'),

    'Kak Bazaar Item 1':                                           ("the CKakariko BazaarC offers", None, 'exclude'),
    'Kak Bazaar Item 2':                                           ("the CKakariko BazaarC offers", None, 'exclude'),
    'Kak Bazaar Item 3':                                           ("the CKakariko BazaarC offers", None, 'exclude'),
    'Kak Bazaar Item 4':                                           ("the CKakariko BazaarC offers", None, 'exclude'),
    'Kak Bazaar Item 5':                                           ("the CKakariko BazaarC offers", None, 'exclude'),
    'Kak Bazaar Item 6':                                           ("the CKakariko BazaarC offers", None, 'exclude'),
    'Kak Bazaar Item 7':                                           ("the CKakariko BazaarC offers", None, 'exclude'),
    'Kak Bazaar Item 8':                                           ("the CKakariko BazaarC offers", None, 'exclude'),

    'ZD Shop Item 1':                                              ("a CZora shopkeeperC sells", None, 'exclude'),
    'ZD Shop Item 2':                                              ("a CZora shopkeeperC sells", None, 'exclude'),
    'ZD Shop Item 3':                                              ("a CZora shopkeeperC sells", None, 'exclude'),
    'ZD Shop Item 4':                                              ("a CZora shopkeeperC sells", None, 'exclude'),
    'ZD Shop Item 5':                                              ("a CZora shopkeeperC sells", None, 'exclude'),
    'ZD Shop Item 6':                                              ("a CZora shopkeeperC sells", None, 'exclude'),
    'ZD Shop Item 7':                                              ("a CZora shopkeeperC sells", None, 'exclude'),
    'ZD Shop Item 8':                                              ("a CZora shopkeeperC sells", None, 'exclude'),

    'GC Shop Item 1':                                              ("a CGoron shopkeeperC sells", None, 'exclude'),
    'GC Shop Item 2':                                              ("a CGoron shopkeeperC sells", None, 'exclude'),
    'GC Shop Item 3':                                              ("a CGoron shopkeeperC sells", None, 'exclude'),
    'GC Shop Item 4':                                              ("a CGoron shopkeeperC sells", None, 'exclude'),
    'GC Shop Item 5':                                              ("a CGoron shopkeeperC sells", None, 'exclude'),
    'GC Shop Item 6':                                              ("a CGoron shopkeeperC sells", None, 'exclude'),
    'GC Shop Item 7':                                              ("a CGoron shopkeeperC sells", None, 'exclude'),
    'GC Shop Item 8':                                              ("a CGoron shopkeeperC sells", None, 'exclude'),

    'Deku Tree MQ Deku Scrub':                                     ("a Cscrub in the Deku TreeC sells", None, 'exclude'),

    'HF Deku Scrub Grotto':                                        ("a lonely Cscrub in a holeC sells", None, 'exclude'),
    'LLR Deku Scrub Grotto Left':                                  ("a Ctrio of scrubsC sells", None, 'exclude'),
    'LLR Deku Scrub Grotto Right':                                 ("a Ctrio of scrubsC sells", None, 'exclude'),
    'LLR Deku Scrub Grotto Center':                                ("a Ctrio of scrubsC sells", None, 'exclude'),

    'LW Deku Scrub Near Deku Theater Right':                       ("a pair of Cscrubs in the woodsC sells", None, 'exclude'),
    'LW Deku Scrub Near Deku Theater Left':                        ("a pair of Cscrubs in the woodsC sells", None, 'exclude'),
    'LW Deku Scrub Near Bridge':                                   ("a Cscrub by a bridgeC sells", None, 'exclude'),
    'LW Deku Scrub Grotto Rear':                                   ("a Cscrub underground duoC sells", None, 'exclude'),
    'LW Deku Scrub Grotto Front':                                  ("a Cscrub underground duoC sells", None, 'exclude'),

    'SFM Deku Scrub Grotto Rear':                                  ("a Cscrub underground duoC sells", None, 'exclude'),
    'SFM Deku Scrub Grotto Front':                                 ("a Cscrub underground duoC sells", None, 'exclude'),

    'GC Deku Scrub Grotto Left':                                   ("a Ctrio of scrubsC sells", None, 'exclude'),
    'GC Deku Scrub Grotto Right':                                  ("a Ctrio of scrubsC sells", None, 'exclude'),
    'GC Deku Scrub Grotto Center':                                 ("a Ctrio of scrubsC sells", None, 'exclude'),

    'Dodongos Cavern Deku Scrub Near Bomb Bag Left':               ("a pair of Cscrubs in Dodongo's CavernC sells", None, 'exclude'),
    'Dodongos Cavern Deku Scrub Side Room Near Dodongos':          ("a Cscrub guarded by LizalfosC sells", None, 'exclude'),
    'Dodongos Cavern Deku Scrub Near Bomb Bag Right':              ("a pair of Cscrubs in Dodongo's CavernC sells", None, 'exclude'),
    'Dodongos Cavern Deku Scrub Lobby':                            ("a Cscrub in Dodongo's CavernC sells", None, 'exclude'),

    'Dodongos Cavern MQ Deku Scrub Lobby Rear':                    ("a pair of Cscrubs in Dodongo's CavernC sells", None, 'exclude'),
    'Dodongos Cavern MQ Deku Scrub Lobby Front':                   ("a pair of Cscrubs in Dodongo's CavernC sells", None, 'exclude'),
    'Dodongos Cavern MQ Deku Scrub Staircase':                     ("a Cscrub in Dodongo's CavernC sells", None, 'exclude'),
    'Dodongos Cavern MQ Deku Scrub Side Room Near Lower Lizalfos': ("a Cscrub guarded by LizalfosC sells", None, 'exclude'),

    'DMC Deku Scrub Grotto Left':                                  ("a Ctrio of scrubsC sells", None, 'exclude'),
    'DMC Deku Scrub Grotto Right':                                 ("a Ctrio of scrubsC sells", None, 'exclude'),
    'DMC Deku Scrub Grotto Center':                                ("a Ctrio of scrubsC sells", None, 'exclude'),

    'ZR Deku Scrub Grotto Rear':                                   ("a Cscrub underground duoC sells", None, 'exclude'),
    'ZR Deku Scrub Grotto Front':                                  ("a Cscrub underground duoC sells", None, 'exclude'),

    'Jabu Jabus Belly Deku Scrub':                                 ("a Cscrub in a deityC sells", None, 'exclude'),

    'LH Deku Scrub Grotto Left':                                   ("a Ctrio of scrubsC sells", None, 'exclude'),
    'LH Deku Scrub Grotto Right':                                  ("a Ctrio of scrubsC sells", None, 'exclude'),
    'LH Deku Scrub Grotto Center':                                 ("a Ctrio of scrubsC sells", None, 'exclude'),

    'GV Deku Scrub Grotto Rear':                                   ("a Cscrub underground duoC sells", None, 'exclude'),
    'GV Deku Scrub Grotto Front':                                  ("a Cscrub underground duoC sells", None, 'exclude'),

    'Colossus Deku Scrub Grotto Front':                            ("a Cscrub underground duoC sells", None, 'exclude'),
    'Colossus Deku Scrub Grotto Rear':                             ("a Cscrub underground duoC sells", None, 'exclude'),

    'Ganons Castle Deku Scrub Center-Left':                        ("Cscrubs in Ganon's CastleC sell", None, 'exclude'),
    'Ganons Castle Deku Scrub Center-Right':                       ("Cscrubs in Ganon's CastleC sell", None, 'exclude'),
    'Ganons Castle Deku Scrub Right':                              ("Cscrubs in Ganon's CastleC sell", None, 'exclude'),
    'Ganons Castle Deku Scrub Left':                               ("Cscrubs in Ganon's CastleC sell", None, 'exclude'),

    'Ganons Castle MQ Deku Scrub Right':                           ("Cscrubs in Ganon's CastleC sell", None, 'exclude'),
    'Ganons Castle MQ Deku Scrub Center-Left':                     ("Cscrubs in Ganon's CastleC sell", None, 'exclude'),
    'Ganons Castle MQ Deku Scrub Center':                          ("Cscrubs in Ganon's CastleC sell", None, 'exclude'),
    'Ganons Castle MQ Deku Scrub Center-Right':                    ("Cscrubs in Ganon's CastleC sell", None, 'exclude'),
    'Ganons Castle MQ Deku Scrub Left':                            ("Cscrubs in Ganon's CastleC sell", None, 'exclude'),

    'LLR Stables Left Cow':                                        ("a Ccow in a stableC gifts", None, 'exclude'),
    'LLR Stables Right Cow':                                       ("a Ccow in a stableC gifts", None, 'exclude'),
    'LLR Tower Right Cow':                                         ("a Ccow in a ranch siloC gifts", None, 'exclude'),
    'LLR Tower Left Cow':                                          ("a Ccow in a ranch siloC gifts", None, 'exclude'),
    'Kak Impas House Cow':                                         ("a Ccow imprisoned in a houseC protects", None, 'exclude'),
    'DMT Cow Grotto Cow':                                          ("a Ccow in a luxurious holeC offers", None, 'exclude'),

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
    'HF Inside Fence Grotto':                                   ("C１アキンド穴C", None, 'region'),
    'LW Scrubs Grotto':                                         ("C２アキンド穴C", None, 'region'),
    'Colossus Grotto':                                          ("２アキンド穴", None, 'region'),
    'ZR Storms Grotto':                                         ("２アキンド穴", None, 'region'),
    'SFM Storms Grotto':                                        ("２アキンド穴", None, 'region'),
    'GV Storms Grotto':                                         ("２アキンド穴", None, 'region'),
    'LH Grotto':                                                ("３アキンド穴", None, 'region'),
    'DMC Hammer Grotto':                                        ("３アキンド穴", None, 'region'),
    'GC Grotto':                                                ("３アキンド穴", None, 'region'),
    'LLR Grotto':                                               ("３アキンド穴", None, 'region'),
    'ZR Fairy Grotto':                                          ("C妖精の泉C", None, 'region'),
    'HF Fairy Grotto':                                          ("C妖精の泉C", None, 'region'),
    'SFM Fairy Grotto':                                         ("C妖精の泉C", None, 'region'),
    'ZD Storms Grotto':                                         ("C妖精の泉C", None, 'region'),
    'GF Storms Grotto':                                         ("C妖精の泉C", None, 'region'),

    '1001':                                                     ("<来年もガノン！", None, 'junk'),
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
                 'song']):
            location_hints.append(hint)
    for hint in location_hints:
        if hint.name not in world_location_names and hint.name not in hintExclusions.exclusions:
            hintExclusions.exclusions.append(hint.name)

    return hintExclusions.exclusions

def nameIsLocation(name, hint_type, world):
    if isinstance(hint_type, (list, tuple)):
        for htype in hint_type:
            if htype in ['sometimes', 'song', 'overworld', 'dungeon', 'always'] and name not in hintExclusions(world):
                return True
    elif hint_type in ['sometimes', 'song', 'overworld', 'dungeon', 'always'] and name not in hintExclusions(world):
        return True
    return False

hintExclusions.exclusions = None

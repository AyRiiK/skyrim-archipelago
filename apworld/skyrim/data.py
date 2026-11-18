"""
Pure game data for the Skyrim Special Edition APWorld.

This file has no Archipelago imports on purpose: the game-side mod (and any
tool) can read the same tables, and the IDs here are the contract between the
APWorld and the mod. Once a version is released, never renumber an existing ID.
"""
from __future__ import annotations

from typing import NamedTuple

GAME_NAME = "Skyrim Special Edition"

ITEM_BASE_ID = 0x5359_0000       # "SY" — arbitrary, keeps our IDs recognisable
LOCATION_BASE_ID = 0x5359_1000

# --------------------------------------------------------------------------- #
# Items
# --------------------------------------------------------------------------- #

# Walled cities whose gates stay locked until the key is received.
CITY_KEYS = {
    "Whiterun": "Whiterun Gate Key",
    "Solitude": "Solitude Gate Key",
    "Windhelm": "Windhelm Gate Key",
    "Riften": "Riften Gate Key",
    "Markarth": "Markarth Gate Key",
}

# Shouts are received word by word, always in order (word 1, then 2, then 3).
SHOUTS = [
    "Unrelenting Force",
    "Whirlwind Sprint",
    "Clear Skies",
    "Dragonrend",
    "Call Dragon",
]
WORDS_PER_SHOUT = 3


def progressive_shout(shout: str) -> str:
    return f"Progressive {shout}"


class ItemData(NamedTuple):
    id: int
    kind: str  # "progression" | "useful" | "filler" | "trap"


_items: list[tuple[str, str]] = []
_items += [(key, "progression") for key in CITY_KEYS.values()]
_items += [(progressive_shout(s), "progression") for s in SHOUTS]
_items += [
    ("Perk Point", "useful"),
    ("Dragon Soul", "useful"),
    ("Gold (100)", "filler"),
    ("Gold (500)", "filler"),
    ("Healing Potion", "filler"),
    ("Magicka Potion", "filler"),
    ("Lockpick Bundle", "filler"),
    ("Filled Soul Gem", "filler"),
    ("Dragon Attack Trap", "trap"),
    ("Bounty Trap", "trap"),
    ("Encumbrance Trap", "trap"),
]

# Shouts that are only shuffled with the word_walls option. Appended after the
# original items so that existing item IDs never change.
EXTRA_SHOUTS = [
    "Animal Allegiance",
    "Aura Whisper",
    "Become Ethereal",
    "Disarm",
    "Dismay",
    "Elemental Fury",
    "Fire Breath",
    "Frost Breath",
    "Ice Form",
    "Kyne's Peace",
    "Marked for Death",
    "Slow Time",
    "Storm Call",
    "Throw Voice",
]
_items += [(progressive_shout(s), "useful") for s in EXTRA_SHOUTS]

ITEM_TABLE: dict[str, ItemData] = {
    name: ItemData(ITEM_BASE_ID + i, kind) for i, (name, kind) in enumerate(_items)
}

FILLER_ITEMS = [n for n, d in ITEM_TABLE.items() if d.kind == "filler"]
TRAP_ITEMS = [n for n, d in ITEM_TABLE.items() if d.kind == "trap"]

# Relative weights when picking filler.
FILLER_WEIGHTS = {
    "Gold (100)": 5,
    "Gold (500)": 2,
    "Healing Potion": 4,
    "Magicka Potion": 3,
    "Lockpick Bundle": 2,
    "Filled Soul Gem": 2,
}

# --------------------------------------------------------------------------- #
# Locations
# --------------------------------------------------------------------------- #

# A requirement is (item name, count).
Req = tuple[str, int]


class QuestStep(NamedTuple):
    name: str
    region: str
    # Items needed for this step itself. Steps of the main quest are
    # sequential, so a step also needs everything earlier steps needed.
    requires: tuple[Req, ...] = ()


def has_shout(shout: str, words: int = 1) -> Req:
    return (progressive_shout(shout), words)


# The main quest, in order. Each entry is one check: completing the quest
# (or, for "lessons", the moment the game would normally teach you a shout).
# Prerequisites marked "VERIFY" are believed correct but should be confirmed
# in game before release.
MAIN_QUEST: list[QuestStep] = [
    QuestStep("Unbound", "Skyrim"),
    QuestStep("Before the Storm", "Whiterun"),
    QuestStep("Bleak Falls Barrow", "Whiterun"),
    QuestStep("Dragon Rising", "Whiterun"),
    # The Greybeards ask you to demonstrate the Thu'um.
    # Borri teaches Wuld during the quest and you must sprint through a gate.
    QuestStep("The Way of the Voice", "Skyrim", (has_shout("Unrelenting Force"), has_shout("Whirlwind Sprint"))),
    QuestStep("High Hrothgar - Greybeards' First Lesson", "Skyrim"),
    QuestStep("High Hrothgar - Greybeards' Second Lesson", "Skyrim"),
    QuestStep("The Horn of Jurgen Windcaller", "Skyrim"),
    QuestStep("High Hrothgar - Greybeards' Gift", "Skyrim"),
    QuestStep("A Blade in the Dark", "Skyrim"),
    QuestStep("Diplomatic Immunity", "Solitude"),
    QuestStep("A Cornered Rat", "Riften"),
    QuestStep("Alduin's Wall", "Skyrim"),
    QuestStep("High Hrothgar - Clear Skies Lesson", "Skyrim"),
    QuestStep("The Throat of the World", "Skyrim", (has_shout("Clear Skies"),)),
    QuestStep("Elder Knowledge", "Skyrim"),
    QuestStep("Time-Wound - Elder Scroll Reading", "Skyrim"),
    QuestStep("Alduin's Bane", "Skyrim", (has_shout("Dragonrend"),)),
    QuestStep("High Hrothgar - Call Dragon Lesson", "Skyrim"),
    # VERIFY: if the civil war is active, Jarl Balgruuf first requires
    # "Season Unending". The mod should handle that or the logic must.
    QuestStep("The Fallen", "Whiterun", (has_shout("Call Dragon"),)),
    QuestStep("The World-Eater's Eyrie", "Skyrim"),
    QuestStep("Sovngarde", "Skyrim"),
]

# One well-known quest per walled city, so every key opens something.
CITY_QUESTS: list[QuestStep] = [
    QuestStep("Whiterun - Take Up Arms", "Whiterun"),
    QuestStep("Solitude - Tending the Flames", "Solitude"),
    QuestStep("Windhelm - The White Phial", "Windhelm"),
    QuestStep("Riften - A Chance Arrangement", "Riften"),
    QuestStep("Markarth - The Forsworn Conspiracy", "Markarth"),
]

# Word walls the main quest sends you to.
WORD_WALLS: list[QuestStep] = [
    QuestStep("Bleak Falls Barrow - Word Wall", "Whiterun"),
]

MAX_DRAGON_SOULS = 30


def dragon_soul_location(n: int) -> str:
    return f"Dragon Soul {n}"


def key_for(city: str) -> Req:
    return (CITY_KEYS[city], 1)


class QuestLine(NamedTuple):
    steps: list[QuestStep]
    # Sequential lines must be done in order; a step needs what earlier steps needed.
    sequential: bool


# Optional quest lines (YAML option "quest_lines"). Location names are prefixed
# with the line name. Steps in a city region need that city's key.
QUEST_LINES: dict[str, QuestLine] = {
    "Companions": QuestLine([
        QuestStep("Companions - Proving Honor", "Whiterun"),
        QuestStep("Companions - The Silver Hand", "Whiterun"),
        QuestStep("Companions - Blood's Honor", "Whiterun"),
        QuestStep("Companions - Purity of Revenge", "Whiterun"),
        QuestStep("Companions - Glory of the Dead", "Whiterun"),
    ], sequential=True),
    "College of Winterhold": QuestLine([
        QuestStep("College - First Lessons", "Skyrim"),
        QuestStep("College - Under Saarthal", "Skyrim"),
        QuestStep("College - Hitting the Books", "Skyrim"),
        QuestStep("College - Good Intentions", "Skyrim"),
        QuestStep("College - Revealing the Unseen", "Skyrim"),
        QuestStep("College - Containment", "Skyrim"),
        QuestStep("College - The Staff of Magnus", "Skyrim"),
        QuestStep("College - The Eye of Magnus", "Skyrim"),
    ], sequential=True),
    "Thieves Guild": QuestLine([
        QuestStep("Thieves Guild - Taking Care of Business", "Riften"),
        QuestStep("Thieves Guild - Loud and Clear", "Riften"),
        QuestStep("Thieves Guild - Dampened Spirits", "Riften"),
        QuestStep("Thieves Guild - Scoundrel's Folly", "Riften"),
        QuestStep("Thieves Guild - Speaking With Silence", "Skyrim"),
        QuestStep("Thieves Guild - Hard Answers", "Markarth"),
        QuestStep("Thieves Guild - The Pursuit", "Skyrim"),
        QuestStep("Thieves Guild - Trinity Restored", "Skyrim"),
        QuestStep("Thieves Guild - Blindsighted", "Skyrim"),
        QuestStep("Thieves Guild - Darkness Returns", "Skyrim"),
    ], sequential=True),
    "Dark Brotherhood": QuestLine([
        QuestStep("Dark Brotherhood - Innocence Lost", "Windhelm"),
        QuestStep("Dark Brotherhood - With Friends Like These", "Skyrim"),
        QuestStep("Dark Brotherhood - Sanctuary", "Skyrim"),
        QuestStep("Dark Brotherhood - Mourning Never Comes", "Skyrim"),
        QuestStep("Dark Brotherhood - Whispers in the Dark", "Skyrim"),
        QuestStep("Dark Brotherhood - The Silence Has Been Broken", "Skyrim"),
        QuestStep("Dark Brotherhood - Bound Until Death", "Solitude"),
        QuestStep("Dark Brotherhood - Breaching Security", "Skyrim"),
        QuestStep("Dark Brotherhood - The Cure for Madness", "Skyrim"),
        QuestStep("Dark Brotherhood - Recipe for Disaster", "Skyrim"),
        QuestStep("Dark Brotherhood - To Kill an Empire", "Solitude"),
        QuestStep("Dark Brotherhood - Death Incarnate", "Skyrim"),
        QuestStep("Dark Brotherhood - Hail Sithis!", "Solitude"),
    ], sequential=True),
    "Daedric Quests": QuestLine([
        QuestStep("Daedric - The Black Star", "Skyrim"),
        QuestStep("Daedric - Boethiah's Calling", "Skyrim"),
        QuestStep("Daedric - A Daedra's Best Friend", "Skyrim"),
        QuestStep("Daedric - Discerning the Transmundane", "Skyrim"),
        QuestStep("Daedric - Ill Met by Moonlight", "Skyrim"),
        QuestStep("Daedric - The Cursed Tribe", "Skyrim"),
        QuestStep("Daedric - Pieces of the Past", "Skyrim"),
        QuestStep("Daedric - The Only Cure", "Skyrim"),
        QuestStep("Daedric - The Whispering Door", "Whiterun"),
        QuestStep("Daedric - The Break of Dawn", "Skyrim"),
        QuestStep("Daedric - The House of Horrors", "Markarth"),
        QuestStep("Daedric - The Taste of Death", "Markarth"),
        QuestStep("Daedric - A Night to Remember", "Skyrim"),
        QuestStep("Daedric - The Mind of Madness", "Solitude"),
        QuestStep("Daedric - Waking Nightmare", "Skyrim"),
    ], sequential=False),
    # ---- added in v0.4 (their locations come after the word walls) ----
    "Bards College": QuestLine([
        QuestStep("Bards College - Finn's Lute", "Solitude"),
        QuestStep("Bards College - Pantea's Flute", "Solitude"),
        QuestStep("Bards College - Rjorn's Drum", "Solitude"),
    ], sequential=False),
    "Civil War (Imperial)": QuestLine([
        QuestStep("Civil War (Imperial) - Joining the Legion", "Solitude"),
        QuestStep("Civil War (Imperial) - The Jagged Crown", "Solitude"),
        QuestStep("Civil War (Imperial) - Message to Whiterun", "Whiterun"),
        QuestStep("Civil War (Imperial) - Reunification of Skyrim", "Solitude"),
    ], sequential=True),
    "Civil War (Stormcloak)": QuestLine([
        QuestStep("Civil War (Stormcloak) - Joining the Stormcloaks", "Windhelm"),
        QuestStep("Civil War (Stormcloak) - The Jagged Crown", "Windhelm"),
        QuestStep("Civil War (Stormcloak) - Message to Whiterun", "Whiterun"),
        QuestStep("Civil War (Stormcloak) - Liberation of Skyrim", "Windhelm"),
    ], sequential=True),
    "Dawnguard": QuestLine([
        QuestStep("Dawnguard - Awakening", "Skyrim"),
        QuestStep("Dawnguard - Bloodline", "Skyrim"),
        QuestStep("Dawnguard - Prophet", "Skyrim"),
        QuestStep("Dawnguard - Chasing Echoes", "Skyrim"),
        QuestStep("Dawnguard - Beyond Death", "Skyrim"),
        QuestStep("Dawnguard - Unseen Visions", "Skyrim"),
        QuestStep("Dawnguard - Touching the Sky", "Skyrim"),
        QuestStep("Dawnguard - Kindred Judgment", "Skyrim"),
    ], sequential=True),
    "Dragonborn": QuestLine([
        QuestStep("Dragonborn - Dragonborn", "Skyrim"),
        QuestStep("Dragonborn - The Temple of Miraak", "Skyrim"),
        QuestStep("Dragonborn - The Fate of the Skaal", "Skyrim"),
        QuestStep("Dragonborn - The Path of Knowledge", "Skyrim"),
        QuestStep("Dragonborn - The Gardener of Men", "Skyrim"),
        QuestStep("Dragonborn - At the Summit of Apocrypha", "Skyrim"),
    ], sequential=True),
}

BASE_QUEST_LINES = ["Companions", "College of Winterhold", "Thieves Guild", "Dark Brotherhood", "Daedric Quests"]

# Items needed before a line can start (e.g. the city quest that opens it).
QUEST_LINE_START_KEYS: dict[str, list[Req]] = {
    "Companions": [key_for("Whiterun")],
    "Thieves Guild": [key_for("Riften")],
    "Bards College": [key_for("Solitude")],
    # Miraak's cultists only come after you are known as Dragonborn (Dragon Rising).
    "Dragonborn": [key_for("Whiterun")],
}

# --------------------------------------------------------------------------- #
# Legendary quests (YAML option "legendary_quests")
# --------------------------------------------------------------------------- #
# name -> items needed (city keys of where the quest takes place)
LEGENDARY_QUESTS: dict[str, list[Req]] = {
    "Forbidden Legend": [],
    "The Forgemaster's Fingers": [key_for("Markarth")],
    # Stones of Barenziah hide in every city, and Vex is in Riften.
    "No Stone Unturned": [key_for(c) for c in ("Whiterun", "Solitude", "Windhelm", "Riften", "Markarth")],
    "The Lost Expedition": [key_for("Markarth")],
    "Unfathomable Depths": [],
    "Blood on the Ice": [key_for("Windhelm")],
    "Rise in the East": [key_for("Windhelm")],
    "The Book of Love": [key_for("Riften")],
    "Infiltration": [],
    "Lost to the Ages": [],
    "Lost Legacy": [],
}


def legendary_location(quest: str) -> str:
    return f"Legendary - {quest}"


# --------------------------------------------------------------------------- #
# Dragon priest masks (YAML option "dragon_priest_masks")
# --------------------------------------------------------------------------- #
DRAGON_PRIEST_MASKS = ["Hevnoraak", "Krosis", "Morokei", "Nahkriin", "Otar", "Rahgot", "Vokun", "Volsung", "Konahrik"]


def mask_location(mask: str) -> str:
    return f"Dragon Priest Mask - {mask}"


# --------------------------------------------------------------------------- #
# Levels and skills (YAML options "level_checks" and "skill_checks")
# --------------------------------------------------------------------------- #
LEVEL_STEP = 5
MAX_LEVEL_CHECK = 80
SKILLS = [
    "One-Handed", "Two-Handed", "Archery", "Block", "Smithing", "Heavy Armor", "Light Armor", "Pickpocket",
    "Lockpicking", "Sneak", "Alchemy", "Speech", "Alteration", "Conjuration", "Destruction", "Illusion",
    "Restoration", "Enchanting",
]
SKILL_THRESHOLDS = [25, 50, 75, 100]


def level_location(level: int) -> str:
    return f"Level {level}"


def skill_location(skill: str, value: int) -> str:
    return f"{skill} {value}"


def quest_line_requirements(line_name: str) -> dict[str, list[Req]]:
    """Requirements of each step of a quest line (cumulative if sequential)."""
    line = QUEST_LINES[line_name]
    result: dict[str, list[Req]] = {}
    needed: dict[str, int] = {item: n for item, n in QUEST_LINE_START_KEYS.get(line_name, [])}
    for step in line.steps:
        own = dict(needed) if line.sequential else {item: n for item, n in QUEST_LINE_START_KEYS.get(line_name, [])}
        reqs = list(step.requires)
        if step.region in CITY_KEYS:
            reqs.append(key_for(step.region))
        for item, count in reqs:
            own[item] = max(own.get(item, 0), count)
        if line.sequential:
            needed = own
        result[step.name] = list(own.items())
    return result


# --------------------------------------------------------------------------- #
# Word walls (YAML option "word_walls")
# --------------------------------------------------------------------------- #
# Most word walls teach the next word of their shout you don't know yet, so a
# check can't be tied to one wall. Instead, "Word Wall - <Shout> #k" is sent
# the k-th time the game teaches you a word of that shout (the word is then
# taken back: only Archipelago gives shout words).
#
# Each shout lists its walls from easiest to hardest to reach, as the items
# needed to reach them. Location #k needs the first k walls.

def _wall(*reqs: Req) -> list[Req]:
    return list(reqs)


def word_wall_requirements() -> dict[str, list[list[Req]]]:
    mq = main_quest_requirements(word_walls=True)
    lines = {name: quest_line_requirements(name) for name in QUEST_LINES}
    free: list[Req] = []
    return {
        "Animal Allegiance": [free, free, lines["Companions"]["Companions - Glory of the Dead"]],  # Ysgramor's Tomb
        "Aura Whisper": [free, free, free],
        "Become Ethereal": [free, free, mq["The Horn of Jurgen Windcaller"]],  # Ustengrav
        "Disarm": [free, free, lines["Thieves Guild"]["Thieves Guild - Speaking With Silence"]],  # Snow Veil
        "Dismay": [free, free, free],
        "Elemental Fury": [free, free, free],
        # Dustman's Cairn (Proving Honor), then Paarthurnax teaches Yol on the Throat of the World.
        "Fire Breath": [free, lines["Companions"]["Companions - Proving Honor"],
                        mq["High Hrothgar - Clear Skies Lesson"] + [has_shout("Clear Skies")]],
        "Frost Breath": [free, free, free],
        "Ice Form": [free, free, lines["College of Winterhold"]["College - Under Saarthal"]],
        "Kyne's Peace": [free, free, free],
        "Marked for Death": [free, free, lines["Dark Brotherhood"]["Dark Brotherhood - Sanctuary"]],
        # Labyrinthian (The Staff of Magnus), Korvanjund (civil war, from Solitude).
        "Slow Time": [free, lines["College of Winterhold"]["College - The Staff of Magnus"], [key_for("Solitude")]],
        "Storm Call": [free, free, mq["The World-Eater's Eyrie"]],  # Skuldafn
        "Throw Voice": [free],
        # Borri teaches Wuld during The Way of the Voice (after you shout Fus).
        "Whirlwind Sprint": [free, free, mq["Dragon Rising"] + [has_shout("Unrelenting Force")]],
    }


WORD_WALL_SHOUTS = [*EXTRA_SHOUTS, "Whirlwind Sprint"]
_WALL_COUNTS = {"Throw Voice": 1}


def word_wall_location(shout: str, k: int) -> str:
    return f"Word Wall - {shout} #{k}"


WORD_WALL_LOCATIONS: dict[str, list[str]] = {
    shout: [word_wall_location(shout, k) for k in range(1, _WALL_COUNTS.get(shout, 3) + 1)]
    for shout in WORD_WALL_SHOUTS
}

_locations: list[str] = (
    [s.name for s in MAIN_QUEST]
    + [s.name for s in CITY_QUESTS]
    + [s.name for s in WORD_WALLS]
    + [dragon_soul_location(n) for n in range(1, MAX_DRAGON_SOULS + 1)]
    # New locations are always appended, so existing IDs never change.
    + [s.name for line in BASE_QUEST_LINES for s in QUEST_LINES[line].steps]
    + [name for names in WORD_WALL_LOCATIONS.values() for name in names]
    # v0.4
    + [s.name for line in QUEST_LINES if line not in BASE_QUEST_LINES for s in QUEST_LINES[line].steps]
    + [legendary_location(q) for q in LEGENDARY_QUESTS]
    + [mask_location(m) for m in DRAGON_PRIEST_MASKS]
    + [level_location(lv) for lv in range(LEVEL_STEP, MAX_LEVEL_CHECK + 1, LEVEL_STEP)]
    + [skill_location(sk, v) for sk in SKILLS for v in SKILL_THRESHOLDS]
)

LOCATION_TABLE: dict[str, int] = {
    name: LOCATION_BASE_ID + i for i, name in enumerate(_locations)
}

REGIONS = ["Skyrim", *CITY_KEYS]


def main_quest_requirements(word_walls: bool = False) -> dict[str, list[Req]]:
    """Cumulative requirements for each main quest step.

    Includes the key of every city an earlier step took place in, so that
    e.g. "Alduin's Wall" still requires the Solitude and Riften keys.
    With word_walls, Fire Breath is shuffled too, and Paarthurnax asks you to
    use it on the Throat of the World.
    """
    result: dict[str, list[Req]] = {}
    needed: dict[str, int] = {}
    for step in MAIN_QUEST:
        reqs = list(step.requires)
        if word_walls and step.name == "The Throat of the World":
            reqs.append(has_shout("Fire Breath"))
        if step.region in CITY_KEYS:
            reqs.append((CITY_KEYS[step.region], 1))
        for item, count in reqs:
            needed[item] = max(needed.get(item, 0), count)
        result[step.name] = list(needed.items())
    return result


def mask_requirements() -> dict[str, list[Req]]:
    mq = main_quest_requirements()
    college = quest_line_requirements("College of Winterhold")
    reqs: dict[str, list[Req]] = {m: [] for m in DRAGON_PRIEST_MASKS}
    reqs["Nahkriin"] = mq["The World-Eater's Eyrie"]  # Skuldafn
    reqs["Morokei"] = college["College - The Staff of Magnus"]  # Labyrinthian
    # Konahrik needs the eight other masks.
    merged: dict[str, int] = {}
    for mask in DRAGON_PRIEST_MASKS[:-1]:
        for item, count in reqs[mask]:
            merged[item] = max(merged.get(item, 0), count)
    reqs["Konahrik"] = list(merged.items())
    return reqs

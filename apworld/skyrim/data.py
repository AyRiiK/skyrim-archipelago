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
    QuestStep("The Way of the Voice", "Skyrim", (has_shout("Unrelenting Force"),)),
    QuestStep("High Hrothgar - Greybeards' First Lesson", "Skyrim"),
    QuestStep("High Hrothgar - Greybeards' Second Lesson", "Skyrim"),
    # VERIFY: Ustengrav's timed gates are designed around Whirlwind Sprint.
    QuestStep("The Horn of Jurgen Windcaller", "Skyrim", (has_shout("Whirlwind Sprint"),)),
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


_locations: list[str] = (
    [s.name for s in MAIN_QUEST]
    + [s.name for s in CITY_QUESTS]
    + [s.name for s in WORD_WALLS]
    + [dragon_soul_location(n) for n in range(1, MAX_DRAGON_SOULS + 1)]
)

LOCATION_TABLE: dict[str, int] = {
    name: LOCATION_BASE_ID + i for i, name in enumerate(_locations)
}

REGIONS = ["Skyrim", *CITY_KEYS]


def main_quest_requirements() -> dict[str, list[Req]]:
    """Cumulative requirements for each main quest step.

    Includes the key of every city an earlier step took place in, so that
    e.g. "Alduin's Wall" still requires the Solitude and Riften keys.
    """
    result: dict[str, list[Req]] = {}
    needed: dict[str, int] = {}
    for step in MAIN_QUEST:
        reqs = list(step.requires)
        if step.region in CITY_KEYS:
            reqs.append((CITY_KEYS[step.region], 1))
        for item, count in reqs:
            needed[item] = max(needed.get(item, 0), count)
        result[step.name] = list(needed.items())
    return result

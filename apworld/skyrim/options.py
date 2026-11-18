from dataclasses import dataclass

from Options import Choice, DeathLink, DefaultOnToggle, OptionGroup, OptionSet, PerGameCommonOptions, Range, Toggle

from .data import MAX_DRAGON_SOULS, QUEST_LINES


class Goal(Choice):
    """What you need to do to finish your game.

    alduin: Defeat Alduin in Sovngarde (finish the main quest).
    dragon_souls: Absorb as many dragon souls as there are Dragon Soul checks.
    quest_lines: Finish every quest line chosen in quest_lines
        (for Daedric Quests: every Daedric quest).
    alduin_and_quest_lines: Both of the above.
    """
    display_name = "Goal"
    option_alduin = 0
    option_dragon_souls = 1
    option_quest_lines = 2
    option_alduin_and_quest_lines = 3
    default = 0


class QuestLines(OptionSet):
    """Extra quest lines whose quests send checks. Each one makes the game longer.

    Valid values: Companions, College of Winterhold, Thieves Guild,
    Dark Brotherhood, Daedric Quests.
    """
    display_name = "Quest Lines"
    valid_keys = frozenset(QUEST_LINES)
    default = frozenset()


class DragonSoulChecks(Range):
    """How many absorbed dragon souls send a check (Dragon Soul 1, 2, 3...).

    Must be at least 1 if the goal is dragon_souls.
    """
    display_name = "Dragon Soul Checks"
    range_start = 0
    range_end = MAX_DRAGON_SOULS
    default = 10


class StartWithWhiterunKey(DefaultOnToggle):
    """Start with the Whiterun Gate Key.

    Without it, very few checks are reachable at the start of the game,
    so turning this off makes for a slow beginning in multiworlds.
    """
    display_name = "Start With Whiterun Key"


class PerkPoints(Range):
    """How many Perk Points are shuffled into the item pool."""
    display_name = "Perk Points"
    range_start = 0
    range_end = 20
    default = 5


class TrapChance(Range):
    """Percentage of filler items that are replaced by traps
    (dragon attack, bounty, extra weight)."""
    display_name = "Trap Chance"
    range_start = 0
    range_end = 100
    default = 15


class WordWalls(Toggle):
    """Every word wall becomes a check, and all 20 shouts of the base game are
    shuffled into the item pool (not only the main quest ones).

    Learning a word at a wall sends "Word Wall - <Shout> #1", "#2"... and the
    word is taken back: shout words only come from Archipelago.
    """
    display_name = "Word Walls"


class AutoUnlockShouts(DefaultOnToggle):
    """Received shout words are unlocked immediately, without spending
    dragon souls. If off, you still need dragon souls to unlock them."""
    display_name = "Auto-Unlock Shout Words"


@dataclass
class SkyrimOptions(PerGameCommonOptions):
    goal: Goal
    quest_lines: QuestLines
    word_walls: WordWalls
    dragon_soul_checks: DragonSoulChecks
    start_with_whiterun_key: StartWithWhiterunKey
    perk_points: PerkPoints
    trap_chance: TrapChance
    auto_unlock_shouts: AutoUnlockShouts
    death_link: DeathLink


option_groups = [
    OptionGroup("Goal", [Goal, DragonSoulChecks]),
    OptionGroup("Game Length", [QuestLines, WordWalls]),
    OptionGroup("Item Pool", [StartWithWhiterunKey, PerkPoints, TrapChance]),
    OptionGroup("Gameplay", [AutoUnlockShouts, DeathLink]),
]

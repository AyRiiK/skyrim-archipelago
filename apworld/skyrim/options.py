from dataclasses import dataclass

from Options import Choice, DeathLink, DefaultOnToggle, OptionGroup, OptionSet, PerGameCommonOptions, Range, Toggle

from .data import LEGENDARY_QUESTS, MAX_DRAGON_SOULS, MAX_LEVEL_CHECK, QUEST_LINES


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
    Dark Brotherhood, Daedric Quests, Bards College, Civil War (Imperial),
    Civil War (Stormcloak), Dawnguard, Dragonborn.
    Only one side of the civil war can be chosen.
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


class LegendaryQuests(OptionSet):
    """Side quests with a legendary reward whose completion sends a check.

    Valid values: Forbidden Legend, The Forgemaster's Fingers, No Stone Unturned,
    The Lost Expedition, Unfathomable Depths, Blood on the Ice, Rise in the East,
    The Book of Love, Infiltration, Lost to the Ages, Lost Legacy.
    """
    display_name = "Legendary Quests"
    valid_keys = frozenset(LEGENDARY_QUESTS)
    default = frozenset()


class DragonPriestMasks(Toggle):
    """Picking up each of the nine dragon priest masks (Konahrik included) sends a check."""
    display_name = "Dragon Priest Masks"


class LevelChecks(Range):
    """Reaching every 5th character level sends a check, up to this level.
    0 turns it off (the value is rounded down to a multiple of 5)."""
    display_name = "Level Checks"
    range_start = 0
    range_end = MAX_LEVEL_CHECK
    default = 0


class SkillChecks(Choice):
    """Reaching skill thresholds sends checks (18 skills).

    up_to_25: each skill at 25. up_to_50: at 25 and 50. And so on up to 100.
    """
    display_name = "Skill Checks"
    option_off = 0
    option_up_to_25 = 1
    option_up_to_50 = 2
    option_up_to_75 = 3
    option_up_to_100 = 4
    default = 0


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
    legendary_quests: LegendaryQuests
    dragon_priest_masks: DragonPriestMasks
    level_checks: LevelChecks
    skill_checks: SkillChecks
    dragon_soul_checks: DragonSoulChecks
    start_with_whiterun_key: StartWithWhiterunKey
    perk_points: PerkPoints
    trap_chance: TrapChance
    auto_unlock_shouts: AutoUnlockShouts
    death_link: DeathLink


option_groups = [
    OptionGroup("Goal", [Goal, DragonSoulChecks]),
    OptionGroup("Game Length", [QuestLines, WordWalls, LegendaryQuests, DragonPriestMasks, LevelChecks, SkillChecks]),
    OptionGroup("Item Pool", [StartWithWhiterunKey, PerkPoints, TrapChance]),
    OptionGroup("Gameplay", [AutoUnlockShouts, DeathLink]),
]

from dataclasses import dataclass

from Options import Choice, DeathLink, DefaultOnToggle, OptionGroup, PerGameCommonOptions, Range

from .data import MAX_DRAGON_SOULS


class Goal(Choice):
    """What you need to do to finish your game.

    alduin: Defeat Alduin in Sovngarde (finish the main quest).
    dragon_souls: Absorb as many dragon souls as there are Dragon Soul checks.
    """
    display_name = "Goal"
    option_alduin = 0
    option_dragon_souls = 1
    default = 0


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


class AutoUnlockShouts(DefaultOnToggle):
    """Received shout words are unlocked immediately, without spending
    dragon souls. If off, you still need dragon souls to unlock them."""
    display_name = "Auto-Unlock Shout Words"


@dataclass
class SkyrimOptions(PerGameCommonOptions):
    goal: Goal
    dragon_soul_checks: DragonSoulChecks
    start_with_whiterun_key: StartWithWhiterunKey
    perk_points: PerkPoints
    trap_chance: TrapChance
    auto_unlock_shouts: AutoUnlockShouts
    death_link: DeathLink


option_groups = [
    OptionGroup("Goal", [Goal, DragonSoulChecks]),
    OptionGroup("Item Pool", [StartWithWhiterunKey, PerkPoints, TrapChance]),
    OptionGroup("Gameplay", [AutoUnlockShouts, DeathLink]),
]

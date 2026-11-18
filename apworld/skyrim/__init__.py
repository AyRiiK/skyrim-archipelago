"""Archipelago world for The Elder Scrolls V: Skyrim Special Edition."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from BaseClasses import CollectionState, Item, ItemClassification, Location, Region, Tutorial
from Options import OptionError
from worlds.AutoWorld import WebWorld, World
from worlds.generic.Rules import set_rule

from . import data
from .data import (CITY_KEYS, CITY_QUESTS, GAME_NAME, ITEM_TABLE, LOCATION_TABLE, MAIN_QUEST, QUEST_LINES, SHOUTS,
                   WORD_WALLS, WORDS_PER_SHOUT, Req, dragon_soul_location, progressive_shout,
                   quest_line_requirements)
from .options import SkyrimOptions, option_groups

_CLASSIFICATIONS = {
    "progression": ItemClassification.progression,
    "useful": ItemClassification.useful,
    "filler": ItemClassification.filler,
    "trap": ItemClassification.trap,
}

GOAL_EVENT = "Goal Completed"
VICTORY_ITEM = "Victory"


class SkyrimItem(Item):
    game = GAME_NAME


class SkyrimLocation(Location):
    game = GAME_NAME


class SkyrimWeb(WebWorld):
    theme = "stone"
    option_groups = option_groups
    tutorials = [
        Tutorial(
            "Multiworld Setup Guide",
            "A guide to setting up Skyrim Special Edition for Archipelago.",
            "English",
            "setup_en.md",
            "setup/en",
            ["Skyrim AP contributors"],
        ),
        Tutorial(
            "Guide d'installation Multiworld",
            "Un guide pour configurer Skyrim Special Edition avec Archipelago.",
            "Français",
            "setup_fr.md",
            "setup/fr",
            ["Skyrim AP contributors"],
        ),
    ]


def _has_all(reqs: list[Req], player: int):
    reqs = list(reqs)

    def rule(state: CollectionState) -> bool:
        return all(state.has(item, player, count) for item, count in reqs)
    return rule


class SkyrimWorld(World):
    """
    The Elder Scrolls V: Skyrim is an open-world action RPG. Walled cities stay
    locked until you find their gate keys, shout words come from the multiworld
    instead of word walls, and main quest steps, city quests and dragon souls
    send checks.
    """
    game = GAME_NAME
    web = SkyrimWeb()
    options_dataclass = SkyrimOptions
    options: SkyrimOptions
    origin_region_name = "Skyrim"
    topology_present = False

    item_name_to_id = {name: d.id for name, d in ITEM_TABLE.items()}
    location_name_to_id = dict(LOCATION_TABLE)

    item_name_groups = {
        "City Keys": set(CITY_KEYS.values()),
        "Shouts": {progressive_shout(s) for s in SHOUTS},
        "Traps": set(data.TRAP_ITEMS),
    }
    location_name_groups = {
        "Main Quest": {s.name for s in MAIN_QUEST},
        "City Quests": {s.name for s in CITY_QUESTS},
        "Dragon Souls": {dragon_soul_location(n) for n in range(1, data.MAX_DRAGON_SOULS + 1)},
        **{line: {s.name for s in QUEST_LINES[line].steps} for line in QUEST_LINES},
    }

    # ------------------------------------------------------------------ #
    def generate_early(self) -> None:
        if self.options.goal == self.options.goal.option_dragon_souls and self.options.dragon_soul_checks == 0:
            raise OptionError(f"{self.player_name}: the dragon_souls goal needs dragon_soul_checks of at least 1.")
        if self.options.goal in (self.options.goal.option_quest_lines, self.options.goal.option_alduin_and_quest_lines) \
                and not self.options.quest_lines.value:
            raise OptionError(f"{self.player_name}: the {self.options.goal.current_key} goal needs at least one quest line.")
        if self.options.start_with_whiterun_key:
            self.multiworld.push_precollected(self.create_item(CITY_KEYS["Whiterun"]))

    # ------------------------------------------------------------------ #
    def create_regions(self) -> None:
        skyrim = Region("Skyrim", self.player, self.multiworld)
        regions = {"Skyrim": skyrim}
        for city in CITY_KEYS:
            regions[city] = Region(city, self.player, self.multiworld)

        def add(region: str, name: str) -> None:
            r = regions[region]
            r.locations.append(SkyrimLocation(self.player, name, LOCATION_TABLE[name], r))

        for step in MAIN_QUEST + CITY_QUESTS + WORD_WALLS:
            add(step.region, step.name)
        for n in range(1, self.options.dragon_soul_checks + 1):
            add("Skyrim", dragon_soul_location(n))
        for line in sorted(self.options.quest_lines.value):
            for step in QUEST_LINES[line].steps:
                add(step.region, step.name)

        goal = SkyrimLocation(self.player, GOAL_EVENT, None, skyrim)
        goal.place_locked_item(SkyrimItem(VICTORY_ITEM, ItemClassification.progression, None, self.player))
        skyrim.locations.append(goal)

        for city, key in CITY_KEYS.items():
            skyrim.connect(regions[city], f"{city} Gate", _has_all([(key, 1)], self.player))

        self.multiworld.regions += regions.values()

    # ------------------------------------------------------------------ #
    def create_item(self, name: str) -> SkyrimItem:
        d = ITEM_TABLE[name]
        return SkyrimItem(name, _CLASSIFICATIONS[d.kind], d.id, self.player)

    def _create_with(self, name: str, classification: ItemClassification) -> SkyrimItem:
        return SkyrimItem(name, classification, ITEM_TABLE[name].id, self.player)

    def get_filler_item_name(self) -> str:
        if self.random.randint(1, 100) <= self.options.trap_chance:
            return self.random.choice(data.TRAP_ITEMS)
        names = list(data.FILLER_WEIGHTS)
        return self.random.choices(names, weights=[data.FILLER_WEIGHTS[n] for n in names])[0]

    def create_items(self) -> None:
        pool: list[SkyrimItem] = []

        for city, key in CITY_KEYS.items():
            if city == "Whiterun" and self.options.start_with_whiterun_key:
                continue
            pool.append(self.create_item(key))

        # Logic only ever needs the first word of a shout, so only that copy
        # is progression; the other words are useful.
        for shout in SHOUTS:
            name = progressive_shout(shout)
            pool.append(self.create_item(name))
            pool += [self._create_with(name, ItemClassification.useful) for _ in range(WORDS_PER_SHOUT - 1)]

        total = len(self.multiworld.get_unfilled_locations(self.player))
        if len(pool) > total:
            raise OptionError(f"{self.player_name}: not enough locations ({total}) for the required items "
                              f"({len(pool)}).")

        useful = ["Perk Point"] * self.options.perk_points.value + ["Dragon Soul"] * 3
        pool += [self.create_item(n) for n in useful[: total - len(pool)]]
        pool += [self.create_item(self.get_filler_item_name()) for _ in range(total - len(pool))]

        self.multiworld.itempool += pool

    # ------------------------------------------------------------------ #
    def set_rules(self) -> None:
        mq = data.main_quest_requirements()
        for step in MAIN_QUEST:
            set_rule(self.get_location(step.name), _has_all(mq[step.name], self.player))

        # Dragons only start appearing (and souls can only be absorbed) after Dragon Rising.
        for n in range(1, self.options.dragon_soul_checks + 1):
            set_rule(self.get_location(dragon_soul_location(n)), _has_all(mq["Dragon Rising"], self.player))

        for line in self.options.quest_lines.value:
            reqs = quest_line_requirements(line)
            for step in QUEST_LINES[line].steps:
                set_rule(self.get_location(step.name), _has_all(reqs[step.name], self.player))

        goal_reqs: dict[str, int] = {}
        for item, count in self._goal_requirements():
            goal_reqs[item] = max(goal_reqs.get(item, 0), count)
        set_rule(self.get_location(GOAL_EVENT), _has_all(list(goal_reqs.items()), self.player))

        self.multiworld.completion_condition[self.player] = lambda state: state.has(VICTORY_ITEM, self.player)

    def _goal_locations(self) -> list[str]:
        """Locations the player must complete for the goal (besides dragon souls)."""
        goal = self.options.goal
        names: list[str] = []
        if goal in (goal.option_alduin, goal.option_alduin_and_quest_lines):
            names.append("Sovngarde")
        if goal in (goal.option_quest_lines, goal.option_alduin_and_quest_lines):
            for line in sorted(self.options.quest_lines.value):
                steps = QUEST_LINES[line].steps
                names += [s.name for s in steps] if not QUEST_LINES[line].sequential else [steps[-1].name]
        return names

    def _goal_requirements(self) -> list[Req]:
        mq = data.main_quest_requirements()
        reqs: list[Req] = []
        if self.options.goal == self.options.goal.option_dragon_souls:
            reqs += mq["Dragon Rising"]
        for name in self._goal_locations():
            if name in mq:
                reqs += mq[name]
            else:
                line = next(l for l in QUEST_LINES if name in {s.name for s in QUEST_LINES[l].steps})
                reqs += quest_line_requirements(line)[name]
        return reqs

    # ------------------------------------------------------------------ #
    def fill_slot_data(self) -> Mapping[str, Any]:
        return {
            "goal_locations": [LOCATION_TABLE[n] for n in self._goal_locations()],
            "goal_souls": self.options.dragon_soul_checks.value
            if self.options.goal == self.options.goal.option_dragon_souls else 0,
            "quest_lines": sorted(self.options.quest_lines.value),
            **self.options.as_dict(
                "goal", "dragon_soul_checks", "start_with_whiterun_key", "auto_unlock_shouts", "death_link"
            ),
            "words_per_shout": WORDS_PER_SHOUT,
        }

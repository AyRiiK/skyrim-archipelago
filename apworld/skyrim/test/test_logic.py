from BaseClasses import CollectionState, ItemClassification

from . import SkyrimTestBase


class TestDefault(SkyrimTestBase):
    def test_city_gate_needs_key(self) -> None:
        self.assertFalse(self.can_reach_location("Diplomatic Immunity"))
        self.assertTrue(self.can_reach_location("Before the Storm"))  # Whiterun key is precollected

    def test_sovngarde_needs_everything(self) -> None:
        needed = ["Progressive Unrelenting Force", "Progressive Whirlwind Sprint", "Solitude Gate Key",
                  "Riften Gate Key", "Progressive Clear Skies", "Progressive Dragonrend",
                  "Progressive Call Dragon"]
        for missing in needed:
            with self.subTest(missing=missing):
                state = CollectionState(self.multiworld)
                for item in self.multiworld.precollected_items[self.player]:
                    state.collect(item, True)
                for name in needed:
                    if name != missing:
                        state.collect(self.world.create_item(name), True)
                self.assertFalse(state.can_reach_location("Sovngarde", self.player))
                state.collect(self.world.create_item(missing), True)
                self.assertTrue(state.can_reach_location("Sovngarde", self.player))

    def test_city_quests(self) -> None:
        self.assertAccessDependency(["Markarth - The Forsworn Conspiracy"], [["Markarth Gate Key"]])


class TestNoWhiterunKey(SkyrimTestBase):
    options = {"start_with_whiterun_key": False}

    def test_whiterun_locked(self) -> None:
        self.assertFalse(self.can_reach_location("Before the Storm"))
        self.collect_by_name("Whiterun Gate Key")
        self.assertTrue(self.can_reach_location("Before the Storm"))


class TestDragonSoulGoal(SkyrimTestBase):
    options = {"goal": "dragon_souls", "dragon_soul_checks": 20}


class TestMinimal(SkyrimTestBase):
    options = {"dragon_soul_checks": 0, "perk_points": 20, "trap_chance": 100}


class TestAllQuestLines(SkyrimTestBase):
    options = {
        "quest_lines": ["Companions", "College of Winterhold", "Thieves Guild", "Dark Brotherhood", "Daedric Quests"],
        "goal": "alduin_and_quest_lines",
    }

    def test_thieves_guild_needs_markarth_late(self) -> None:
        self.collect_by_name("Riften Gate Key")
        self.assertTrue(self.can_reach_location("Thieves Guild - Scoundrel's Folly"))
        self.assertFalse(self.can_reach_location("Thieves Guild - Darkness Returns"))
        self.collect_by_name("Markarth Gate Key")
        self.assertTrue(self.can_reach_location("Thieves Guild - Darkness Returns"))

    def test_daedric_quests_are_independent(self) -> None:
        self.assertTrue(self.can_reach_location("Daedric - The Black Star"))
        self.assertFalse(self.can_reach_location("Daedric - The Mind of Madness"))

    def test_slot_data_goal(self) -> None:
        slot_data = self.world.fill_slot_data()
        # Sovngarde + last step of 4 sequential lines + all 15 Daedric quests.
        self.assertEqual(len(slot_data["goal_locations"]), 1 + 4 + 15)


class TestQuestLinesGoalOnly(SkyrimTestBase):
    options = {"quest_lines": ["College of Winterhold"], "goal": "quest_lines"}


class TestWordWalls(SkyrimTestBase):
    options = {"word_walls": True, "quest_lines": ["Companions"]}

    def test_throat_needs_fire_breath(self) -> None:
        self.assertIn("Progressive Fire Breath", {i.name for i in self.multiworld.itempool if i.advancement})
        state = CollectionState(self.multiworld)
        for item in self.multiworld.itempool:
            if item.player == self.player and item.advancement and item.name != "Progressive Fire Breath":
                state.collect(item, True)
        self.assertFalse(state.can_reach_location("The Throat of the World", self.player))
        state.collect(self.world.create_item("Progressive Fire Breath"), True)
        state.collect(self.world._create_with("Progressive Fire Breath", ItemClassification.progression), True)
        self.assertTrue(state.can_reach_location("The Throat of the World", self.player))

    def test_free_walls_reachable(self) -> None:
        self.assertTrue(self.can_reach_location("Word Wall - Aura Whisper #3"))
        self.assertTrue(self.can_reach_location("Word Wall - Throw Voice #1"))
        self.assertFalse(self.can_reach_location("Word Wall - Storm Call #3"))

    def test_slot_data(self) -> None:
        self.assertEqual(self.world.fill_slot_data()["word_walls"], 1)


class TestWordWallsEverything(SkyrimTestBase):
    options = {
        "word_walls": True,
        "quest_lines": ["Companions", "College of Winterhold", "Thieves Guild", "Dark Brotherhood", "Daedric Quests"],
        "goal": "alduin_and_quest_lines",
        "dragon_soul_checks": 30,
        "perk_points": 20,
    }


class TestEverythingV04(SkyrimTestBase):
    options = {
        "word_walls": True,
        "quest_lines": ["Companions", "College of Winterhold", "Thieves Guild", "Dark Brotherhood", "Daedric Quests",
                        "Bards College", "Civil War (Stormcloak)", "Dawnguard", "Dragonborn"],
        "legendary_quests": ["Forbidden Legend", "The Forgemaster's Fingers", "No Stone Unturned",
                             "The Lost Expedition", "Unfathomable Depths", "Blood on the Ice", "Rise in the East",
                             "The Book of Love", "Infiltration", "Lost to the Ages", "Lost Legacy"],
        "dragon_priest_masks": True,
        "level_checks": 80,
        "skill_checks": "up_to_100",
        "goal": "alduin_and_quest_lines",
    }

    def test_counts(self) -> None:
        self.assertEqual(len(self.multiworld.get_locations(self.player)), 285 - 20 - 4 + 1)  # 20 unused dragon souls, the other civil war side, + goal event

    def test_masks(self) -> None:
        self.assertTrue(self.can_reach_location("Dragon Priest Mask - Krosis"))
        self.assertFalse(self.can_reach_location("Dragon Priest Mask - Konahrik"))
        self.assertTrue(self.can_reach_location("Level 80"))
        self.assertTrue(self.can_reach_location("Enchanting 100"))
        self.assertFalse(self.can_reach_location("Legendary - No Stone Unturned"))

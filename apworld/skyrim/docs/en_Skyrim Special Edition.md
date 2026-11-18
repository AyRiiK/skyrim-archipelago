# Skyrim Special Edition

## What does randomization do to this game?

- The five walled cities (Whiterun, Solitude, Windhelm, Riften, Markarth) have their gates locked until you
  receive their **Gate Key**.
- Shouts needed by the main quest (Unrelenting Force, Whirlwind Sprint, Clear Skies, Dragonrend, Call Dragon)
  are no longer learned from word walls or the Greybeards: their words are items, received in order.
- Checks are sent by completing main quest steps, one quest per walled city, the Bleak Falls Barrow word wall,
  and absorbing dragon souls.
- With the `word_walls` option, all 20 base-game shouts are shuffled and every word wall becomes a check: the k-th
  word the game teaches you for a shout sends "Word Wall - <Shout> #k", and the word is taken back.
- Optional quest lines (`quest_lines` option) add more checks: Companions, College of Winterhold, Thieves Guild,
  Dark Brotherhood, Daedric quests, Bards College, one side of the Civil War, Dawnguard and Dragonborn.
- More optional checks: legendary side quests (`legendary_quests`), the nine dragon priest masks
  (`dragon_priest_masks`), every 5th character level (`level_checks`) and skill thresholds (`skill_checks`).

## What is the goal?

Defeat Alduin in Sovngarde, absorb a set number of dragon souls, finish the chosen quest lines, or both Alduin and
the quest lines (see the `goal` option).

## What can show up from other worlds?

Gate keys, shout words, perk points, dragon souls, gold, potions, lockpicks, soul gems, and traps
(a dragon attack, a bounty, extra weight).

## Status

Early development: playable with the SKSE mod from this repository.

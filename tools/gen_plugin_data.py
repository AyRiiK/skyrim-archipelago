"""Generate plugin/dist/SKSE/Plugins/SkyrimArchipelago.json from the APWorld data.

The APWorld (apworld/skyrim/data.py) is the source of truth for item and
location IDs. This script adds what the game side needs: which quest (FormID
in Skyrim.esm) completes each check, and what each item does in game.

Run from the repository root:  python tools/gen_plugin_data.py
"""
from __future__ import annotations

import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("skyrim_data", ROOT / "apworld" / "skyrim" / "data.py")
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)

PLUGIN = "Skyrim.esm"


def form(local_id: int) -> str:
    return f"{PLUGIN}|0x{local_id:06X}"


# Quest FormIDs (Skyrim.esm). "VERIFY" = taken from public lists, to be
# confirmed with the in-game dump (SkyrimArchipelago.log).
Q = {
    "MQ101": 0x03372B,  # Unbound
    "MQ102": 0x04E50D,  # Before the Storm
    "MQ103": 0x0D0800,  # Bleak Falls Barrow
    "MQ104": 0x02610C,  # Dragon Rising
    "MQ105": 0x0242BA,  # The Way of the Voice
    "MQ105Ustengrav": 0x0713DC,  # The Horn of Jurgen Windcaller (VERIFY)
    "MQ106": 0x032926,  # A Blade in the Dark
    "MQ201": 0x035D5F,  # Diplomatic Immunity
    "MQ202": 0x036191,  # A Cornered Rat
    "MQ203": 0x036192,  # Alduin's Wall
    "MQ204": 0x02D515,  # The Throat of the World
    "MQ205": 0x02D516,  # Elder Knowledge
    "MQ206": 0x036193,  # Alduin's Bane
    "MQ301": 0x044C56,  # The Fallen
    "MQ303": 0x046EF0,  # The World-Eater's Eyrie
    "MQ304": 0x046EF1,  # Sovngarde
    "MQ305": 0x046EF2,  # Dragonslayer
    "C00": 0x04B2D9,    # Take Up Arms
    "MS05": 0x053511,   # Tending the Flames
    "MS12": 0x02C258,   # The White Phial
    "TG00": 0x021556,   # A Chance Arrangement
    "MS01": 0x018B4B,   # The Forsworn Conspiracy
}

# Optional quest lines: location name -> (editor ID, FormID). Editor IDs and
# names are printed in SkyrimArchipelago.log at startup for checking.
QUEST_LINE_QUESTS = {
    "Companions - Proving Honor": ("C01", 0x06E803),
    "Companions - The Silver Hand": ("C03", 0x01CEF4),
    "Companions - Blood's Honor": ("C04", 0x01CEF5),
    "Companions - Purity of Revenge": ("C05", 0x06E805),
    "Companions - Glory of the Dead": ("C06", 0x01CEF6),
    "College - First Lessons": ("MG01", 0x01F251),
    "College - Under Saarthal": ("MG02", 0x01F252),
    "College - Hitting the Books": ("MG03", 0x01F253),
    "College - Good Intentions": ("MG04", 0x01F254),
    "College - Revealing the Unseen": ("MG06", 0x01F256),
    "College - Containment": ("MG05", 0x01F255),
    "College - The Staff of Magnus": ("MG07", 0x01F257),
    "College - The Eye of Magnus": ("MG08", 0x01F258),
    "Thieves Guild - Taking Care of Business": ("TG01", 0x01F326),
    "Thieves Guild - Loud and Clear": ("TG02", 0x02154E),
    "Thieves Guild - Dampened Spirits": ("TG03", 0x02154F),
    "Thieves Guild - Scoundrel's Folly": ("TG04", 0x021550),
    "Thieves Guild - Speaking With Silence": ("TG05", 0x021551),
    "Thieves Guild - Hard Answers": ("TG06", 0x021552),
    "Thieves Guild - The Pursuit": ("TG07", 0x021553),
    "Thieves Guild - Trinity Restored": ("TG08A", 0x057F99),
    "Thieves Guild - Blindsighted": ("TG08B", 0x021554),
    "Thieves Guild - Darkness Returns": ("TG09", 0x021555),
    "Dark Brotherhood - Innocence Lost": ("DB01", 0x01EA50),
    "Dark Brotherhood - With Friends Like These": ("DB02", 0x01EA51),
    "Dark Brotherhood - Sanctuary": ("DB02a", 0x022F47),
    "Dark Brotherhood - Mourning Never Comes": ("DB03", 0x01EA52),
    "Dark Brotherhood - Whispers in the Dark": ("DB04", 0x01EA53),
    "Dark Brotherhood - The Silence Has Been Broken": ("DB04a", 0x02AD16),
    "Dark Brotherhood - Bound Until Death": ("DB05", 0x01EA54),
    "Dark Brotherhood - Breaching Security": ("DB06", 0x01EA55),
    "Dark Brotherhood - The Cure for Madness": ("DB07", 0x01EA56),
    "Dark Brotherhood - Recipe for Disaster": ("DB08", 0x01EA57),
    "Dark Brotherhood - To Kill an Empire": ("DB09", 0x01EA58),
    "Dark Brotherhood - Death Incarnate": ("DB10", 0x03CEDA),
    "Dark Brotherhood - Hail Sithis!": ("DB11", 0x01EA59),
    "Daedric - The Black Star": ("DA01", 0x028AD6),
    "Daedric - Boethiah's Calling": ("DA02", 0x04D8D6),
    "Daedric - A Daedra's Best Friend": ("DA03", 0x01BFC4),
    "Daedric - Discerning the Transmundane": ("DA04", 0x02D512),
    "Daedric - Ill Met by Moonlight": ("DA05", 0x02A49A),
    "Daedric - The Cursed Tribe": ("DA06", 0x03B681),
    "Daedric - Pieces of the Past": ("DA07", 0x0240B8),
    "Daedric - The Only Cure": ("DA13", 0x08998D),
    "Daedric - The Whispering Door": ("DA08", 0x04A37B),
    "Daedric - The Break of Dawn": ("DA09", 0x04E4E1),
    "Daedric - The House of Horrors": ("DA10", 0x022F08),
    "Daedric - The Taste of Death": ("DA11", 0x02C358),
    "Daedric - A Night to Remember": ("DA14", 0x01BB9B),
    "Daedric - The Mind of Madness": ("DA15", 0x02AC68),
    "Daedric - Waking Nightmare": ("DA16", 0x0242AF),
}
for _name, (_edid, _fid) in QUEST_LINE_QUESTS.items():
    Q[_edid] = _fid

# Location -> quest whose completion sends it. "Lessons" are approximated by
# the completion of the quest during which the game teaches the shout; this
# matches the APWorld logic for each of them.
LOCATION_QUEST = {
    "Unbound": "MQ101",
    "Before the Storm": "MQ102",
    "Bleak Falls Barrow": "MQ103",
    "Dragon Rising": "MQ104",
    "The Way of the Voice": "MQ105",
    "High Hrothgar - Greybeards' First Lesson": "MQ105",
    "High Hrothgar - Greybeards' Second Lesson": "MQ105",
    "The Horn of Jurgen Windcaller": "MQ105Ustengrav",
    "High Hrothgar - Greybeards' Gift": "MQ105Ustengrav",
    "A Blade in the Dark": "MQ106",
    "Diplomatic Immunity": "MQ201",
    "A Cornered Rat": "MQ202",
    "Alduin's Wall": "MQ203",
    "High Hrothgar - Clear Skies Lesson": "MQ203",
    "The Throat of the World": "MQ204",
    "Elder Knowledge": "MQ205",
    "Time-Wound - Elder Scroll Reading": "MQ205",
    "Alduin's Bane": "MQ206",
    "High Hrothgar - Call Dragon Lesson": "MQ206",
    "The Fallen": "MQ301",
    "The World-Eater's Eyrie": "MQ303",
    "Sovngarde": "MQ304",
    "Whiterun - Take Up Arms": "C00",
    "Solitude - Tending the Flames": "MS05",
    "Windhelm - The White Phial": "MS12",
    "Riften - A Chance Arrangement": "TG00",
    "Markarth - The Forsworn Conspiracy": "MS01",
    "Bleak Falls Barrow - Word Wall": "MQ103",
    **{name: edid for name, (edid, _) in QUEST_LINE_QUESTS.items()},
}

CITIES = {
    # city: (worldspace editor ID, French name)
    "Whiterun": ("WhiterunWorld", "Blancherive"),
    "Solitude": ("SolitudeWorld", "Solitude"),
    "Windhelm": ("WindhelmWorld", "Vendeaume"),
    "Riften": ("RiftenWorld", "Faillaise"),
    "Markarth": ("MarkarthWorld", "Markarth"),
}

SHOUTS = {
    # shout: (FormID, French name)
    "Unrelenting Force": (0x013E07, "Force implacable"),
    "Whirlwind Sprint": (0x02F7BA, "Impulsion"),
    "Clear Skies": (0x03CD34, "Ciel dégagé"),
    "Dragonrend": (0x044250, "Brise-Dragon"),
    "Call Dragon": (0x046B8C, "Appel de dragon"),
}

GOLD = 0x00000F
ITEMS = {
    "Perk Point": {"type": "perk_point", "fr": "Point d'atout"},
    "Dragon Soul": {"type": "dragon_soul", "fr": "Âme de dragon"},
    "Gold (100)": {"type": "item", "form": form(GOLD), "count": 100, "fr": "100 pièces d'or"},
    "Gold (500)": {"type": "item", "form": form(GOLD), "count": 500, "fr": "500 pièces d'or"},
    "Healing Potion": {"type": "item", "form": form(0x03EADE), "count": 1, "fr": "Potion de soins"},
    "Magicka Potion": {"type": "item", "form": form(0x039BE6), "count": 1, "fr": "Potion de magie"},  # VERIFY
    "Lockpick Bundle": {"type": "item", "form": form(0x00000A), "count": 5, "fr": "5 crochets"},
    "Filled Soul Gem": {"type": "item", "form": form(0x02E4FF), "count": 1, "fr": "Grande gemme d'âme pleine"},
    "Dragon Attack Trap": {"type": "trap_dragon", "fr": "Piège : attaque de dragon"},
    "Bounty Trap": {"type": "trap_fine", "percent": 10, "fr": "Piège : amende"},
    "Encumbrance Trap": {"type": "item", "form": form(0x05ACE4), "count": 40, "fr": "Piège : 40 lingots de fer"},
}


def main() -> None:
    items = {}
    for name, d in data.ITEM_TABLE.items():
        if name in data.CITY_KEYS.values():
            city = next(c for c, k in data.CITY_KEYS.items() if k == name)
            entry = {"type": "gate_key", "city": city, "fr": f"Clé de {CITIES[city][1]}"}
        elif name.startswith("Progressive "):
            shout = name.removeprefix("Progressive ")
            fid, fr = SHOUTS[shout]
            entry = {"type": "shout", "shout": form(fid), "fr": f"Mot de pouvoir : {fr}"}
        else:
            entry = dict(ITEMS[name])
        entry["name"] = name
        items[str(d.id)] = entry

    locations = []
    for name, loc_id in data.LOCATION_TABLE.items():
        if name.startswith("Dragon Soul "):
            locations.append({"id": loc_id, "name": name, "dragon_soul": int(name.split()[-1])})
        else:
            locations.append({"id": loc_id, "name": name, "quest": form(Q[LOCATION_QUEST[name]])})

    out = {
        "game": data.GAME_NAME,
        "cities": {c: {"worldspace": ws, "fr": fr} for c, (ws, fr) in CITIES.items()},
        "items": items,
        "locations": locations,
    }
    path = ROOT / "plugin" / "dist" / "SKSE" / "Plugins" / "SkyrimArchipelago.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {path} ({len(items)} items, {len(locations)} locations)")


if __name__ == "__main__":
    main()

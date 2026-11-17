# Skyrim Archipelago

Intégration de **The Elder Scrolls V: Skyrim Special Edition** (Steam, version 1.7.104) avec le randomizer multi-jeux [Archipelago](https://archipelago.gg).

> État : **en développement** (v0.1). L'APWorld génère des parties ; le plugin SKSE est une première version à tester.

## Le principe

- Les cinq villes fortifiées (Blancherive, Solitude, Vendeaume, Faillaise, Markarth) sont **verrouillées** tant que tu n'as pas reçu leur clé.
- Les mots des cris de la quête principale (Force implacable, Impulsion, Ciel dégagé, Brise-Dragon, Appel de dragon) viennent du multiworld.
- Finir des étapes de la quête principale, une quête par grande ville et absorber des âmes de dragon envoie des objets aux autres joueurs.
- Objectif : vaincre Alduin à Sovngarde, ou absorber un nombre donné d'âmes de dragon.

## Contenu du dépôt

| Dossier | Rôle |
|---|---|
| `apworld/skyrim/` | L'APWorld (Python) : items, checks, logique, options. |
| `plugin/` | Le plugin SKSE (C++, CommonLibSSE-NG) qui fait le lien entre le jeu et le serveur. |
| `plugin/dist/SKSE/Plugins/` | Fichiers livrés avec le plugin : configuration (`.ini`) et correspondances jeu ↔ Archipelago (`.json`). |
| `tools/gen_plugin_data.py` | Régénère le `.json` à partir de l'APWorld. |

## Récupérer les fichiers compilés

Chaque modification déclenche une compilation automatique (onglet **Actions** de GitHub). Ouvre le dernier « Build » réussi et télécharge :

- `skyrim-apworld` → contient `skyrim.apworld` (double-clic pour l'installer dans Archipelago) ;
- `skyrim-archipelago-mod` → contient `SkyrimArchipelago-mod.zip`, à installer dans Mod Organizer 2 (« Installer un mod depuis une archive »).

## Configuration en jeu

Dans MO2, édite `SKSE/Plugins/SkyrimArchipelago.ini` du mod :

```ini
Server=archipelago.gg:38281
Slot=TonNomDeJoueur
Password=
```

Lance le jeu via SKSE. Le journal du plugin est dans `Documents/My Games/Skyrim Special Edition/SKSE/SkyrimArchipelago.log`.

## Prérequis

- Skyrim Special Edition 1.7.104 (Steam)
- SKSE64 2.3.1
- Address Library for SKSE Plugins (All in One, v13 ou plus)

## Limites connues (v0.1)

- Les mots de pouvoir appris normalement (murs de mots, Grises-Barbes) ne sont pas encore bloqués.
- Le piège « attaque de dragon » n'est pas encore implémenté.
- DeathLink : géré (option `death_link` du YAML) — à tester.
- Certaines correspondances (quête de la Corne de Jurgen, potion de magie) sont à confirmer avec le journal du plugin.

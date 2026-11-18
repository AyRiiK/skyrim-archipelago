#include "Game.h"

#include "Client.h"
#include "Config.h"

namespace
{
	constexpr auto GAME_NAME = "Skyrim Special Edition";
	constexpr std::uint32_t SAVE_VERSION = 1;
	constexpr std::uint32_t RECORD_STATE = 'STAT';
	constexpr RE::FormID    XMARKER = 0x0000003B;
	constexpr int           CLIENT_STATUS_GOAL = 30;

	// ------------------------------------------------------------------ //
	// Static data from SkyrimArchipelago.json
	// ------------------------------------------------------------------ //
	struct ItemDef
	{
		std::string           name;
		std::string           fr;
		std::string           type;
		std::string           city;
		RE::TESBoundObject*   object{ nullptr };
		RE::TESShout*         shout{ nullptr };
		std::int32_t          count{ 1 };
		std::int32_t          percent{ 0 };
	};

	struct LocationDef
	{
		std::int64_t  id{ 0 };
		std::string   name;
		RE::TESQuest* quest{ nullptr };
		int           dragonSoul{ 0 };
	};

	struct CityDef
	{
		std::string         name;
		std::string         fr;
		std::uint32_t       bit{ 0 };
		RE::TESWorldSpace*  worldspace{ nullptr };
	};

	std::unordered_map<std::int64_t, ItemDef> g_items;
	std::vector<LocationDef>                  g_locations;
	std::vector<CityDef>                      g_cities;

	// ------------------------------------------------------------------ //
	// Per-save state (stored in the SKSE co-save)
	// ------------------------------------------------------------------ //
	struct SaveState
	{
		std::string   seed;
		std::string   slot;
		std::uint32_t itemsApplied{ 0 };
		std::uint32_t soulsAbsorbed{ 0 };
		std::int32_t  lastSouls{ -1 };
		std::uint32_t cityMask{ 0 };
		RE::FormID    marker{ 0 };
	} g_save;

	// ------------------------------------------------------------------ //
	// Session state (this game run)
	// ------------------------------------------------------------------ //
	struct Session
	{
		bool                             gameLoaded{ false };
		bool                             connected{ false };
		bool                             refused{ false };
		bool                             mismatchWarned{ false };
		bool                             goalSent{ false };
		std::string                      seedName;
		int                              slot{ -1 };
		int                              goal{ 0 };
		std::vector<std::int64_t>        goalLocations;
		std::uint32_t                    goalSouls{ 0 };
		int                              dragonSoulChecks{ 0 };
		bool                             autoUnlockShouts{ true };
		bool                             deathLink{ false };
		bool                             wasDead{ false };
		bool                             ignoreNextDeath{ false };
		std::optional<std::string>       pendingDeathFrom;
		std::map<int, std::string>       players;
		std::vector<json>                items;
		std::set<std::int64_t>           checked;
		std::map<RE::TESShout*, int>     shoutsEnsured;
		std::chrono::steady_clock::time_point lastMarkerUpdate{};
		std::string                      lockedWarnedFor;
	} g_session;

	// ------------------------------------------------------------------ //
	// Helpers
	// ------------------------------------------------------------------ //
	template <class... Args>
	void CallStatic(const char* a_class, const char* a_fn, Args&&... a_args)
	{
		auto* vm = RE::BSScript::Internal::VirtualMachine::GetSingleton();
		if (!vm) {
			return;
		}
		RE::BSTSmartPointer<RE::BSScript::IStackCallbackFunctor> callback;
		auto* args = RE::MakeFunctionArguments(std::decay_t<Args>(a_args)...);
		vm->DispatchStaticCall(RE::BSFixedString(a_class), RE::BSFixedString(a_fn), args, callback);
	}

	// "Skyrim.esm|0x03372B" -> form
	RE::TESForm* LookupForm(const std::string& a_ref)
	{
		const auto sep = a_ref.find('|');
		if (sep == std::string::npos) {
			return nullptr;
		}
		const auto plugin = a_ref.substr(0, sep);
		const auto id = static_cast<RE::FormID>(std::stoul(a_ref.substr(sep + 1), nullptr, 16));
		auto* handler = RE::TESDataHandler::GetSingleton();
		return handler ? handler->LookupForm(id, plugin) : nullptr;
	}

	std::string FormInfo(RE::TESForm* a_form)
	{
		if (!a_form) {
			return "NOT FOUND";
		}
		const char* editorID = a_form->GetFormEditorID();
		return fmt::format("{:08X} editorID='{}' name='{}'", a_form->GetFormID(), editorID ? editorID : "",
			a_form->GetName());
	}

	RE::PlayerCharacter* Player()
	{
		return RE::PlayerCharacter::GetSingleton();
	}

	std::string PlayerName(int a_slot)
	{
		const auto it = g_session.players.find(a_slot);
		return it != g_session.players.end() ? it->second : fmt::format("joueur {}", a_slot);
	}

	bool IsBound()
	{
		return g_session.connected && g_session.gameLoaded && !g_session.seedName.empty() &&
		       g_save.seed == g_session.seedName && g_save.slot == Config::Get().slot;
	}

	// ------------------------------------------------------------------ //
	// Network messages
	// ------------------------------------------------------------------ //
	void SendConnect()
	{
		const auto& cfg = Config::Get();
		Client::Get().Send({
			{ "cmd", "Connect" },
			{ "password", cfg.password },
			{ "game", GAME_NAME },
			{ "name", cfg.slot },
			{ "uuid", "skyrim-archipelago-" + cfg.slot },
			{ "version", { { "major", 0 }, { "minor", 6 }, { "build", 4 }, { "class", "Version" } } },
			{ "items_handling", 7 },
			{ "tags", json::array({ "AP" }) },
			{ "slot_data", true },
		});
	}

	void HandleMessage(const json& a_msg)
	{
		const auto cmd = a_msg.value("cmd", std::string{});

		if (cmd == "RoomInfo") {
			g_session.seedName = a_msg.value("seed_name", std::string{});
			SendConnect();
		} else if (cmd == "Connected") {
			g_session.connected = true;
			g_session.mismatchWarned = false;
			g_session.goalSent = false;
			g_session.slot = a_msg.value("slot", -1);
			g_session.players.clear();
			for (const auto& p : a_msg.value("players", json::array())) {
				g_session.players[p.value("slot", -1)] = p.value("alias", p.value("name", std::string{}));
			}
			const auto slotData = a_msg.value("slot_data", json::object());
			g_session.goal = slotData.value("goal", 0);
			g_session.goalLocations.clear();
			g_session.goalSouls = 0;
			if (slotData.contains("goal_locations")) {
				for (const auto& id : slotData["goal_locations"]) {
					g_session.goalLocations.push_back(id.get<std::int64_t>());
				}
				g_session.goalSouls = slotData.value("goal_souls", 0u);
			} else if (g_session.goal == 0) {
				// Worlds from v0.1 only knew "alduin" (= Sovngarde) and "dragon_souls".
				for (const auto& loc : g_locations) {
					if (loc.name == "Sovngarde") {
						g_session.goalLocations.push_back(loc.id);
					}
				}
			} else {
				g_session.goalSouls = static_cast<std::uint32_t>(slotData.value("dragon_soul_checks", 0));
			}
			g_session.dragonSoulChecks = slotData.value("dragon_soul_checks", 0);
			g_session.autoUnlockShouts = slotData.value("auto_unlock_shouts", 1) != 0;
			g_session.deathLink = slotData.value("death_link", 0) != 0;
			if (g_session.deathLink) {
				Client::Get().Send({ { "cmd", "ConnectUpdate" }, { "tags", json::array({ "AP", "DeathLink" }) } });
			}
			g_session.checked.clear();
			for (const auto& id : a_msg.value("checked_locations", json::array())) {
				g_session.checked.insert(id.get<std::int64_t>());
			}
			logger::info("Connected as slot {} (seed {})", g_session.slot, g_session.seedName);
			Game::Notify("Archipelago : connecté !");
		} else if (cmd == "ConnectionRefused") {
			std::string errors;
			for (const auto& e : a_msg.value("errors", json::array())) {
				errors += e.get<std::string>() + " ";
			}
			logger::error("Connection refused: {}", errors);
			Game::Notify("Archipelago : connexion refusée (" + errors + "). Vérifie SkyrimArchipelago.ini.");
			g_session.refused = true;
			std::thread([] { Client::Get().Stop(); }).detach();
		} else if (cmd == "ReceivedItems") {
			const auto index = a_msg.value("index", 0);
			const auto items = a_msg.value("items", json::array());
			if (index == 0) {
				g_session.items.assign(items.begin(), items.end());
			} else if (static_cast<std::size_t>(index) == g_session.items.size()) {
				g_session.items.insert(g_session.items.end(), items.begin(), items.end());
			} else {
				Client::Get().Send({ { "cmd", "Sync" } });
			}
		} else if (cmd == "RoomUpdate") {
			for (const auto& id : a_msg.value("checked_locations", json::array())) {
				g_session.checked.insert(id.get<std::int64_t>());
			}
		} else if (cmd == "PrintJSON") {
			const auto type = a_msg.value("type", std::string{});
			if (type == "ItemSend" && Config::Get().showSentItems) {
				const auto receiving = a_msg.value("receiving", -1);
				const auto sender = a_msg.contains("item") ? a_msg["item"].value("player", -1) : -1;
				if (sender == g_session.slot && receiving != g_session.slot) {
					Game::Notify("Objet envoyé à " + PlayerName(receiving));
				}
			} else if (type == "Chat" || type == "ServerChat") {
				Game::Notify(a_msg.value("message", std::string{}));
			}
		} else if (cmd == "Bounced") {
			const auto tags = a_msg.value("tags", json::array());
			const bool isDeathLink = std::find(tags.begin(), tags.end(), "DeathLink") != tags.end();
			const auto data = a_msg.value("data", json::object());
			const auto source = data.value("source", std::string{});
			if (isDeathLink && g_session.deathLink && source != Config::Get().slot) {
				g_session.pendingDeathFrom = source;
			}
		} else if (cmd == "_closed") {
			if (g_session.connected) {
				Game::Notify("Archipelago : connexion perdue, reconnexion…");
			}
			g_session.connected = false;
		}
	}

	// ------------------------------------------------------------------ //
	// DeathLink
	// ------------------------------------------------------------------ //
	void HandleDeathLink()
	{
		auto*      player = Player();
		const bool dead = player->IsDead(false);

		if (g_session.pendingDeathFrom && !dead) {
			const auto source = *g_session.pendingDeathFrom;
			g_session.pendingDeathFrom.reset();
			g_session.ignoreNextDeath = true;
			Game::Notify("DeathLink : " + source + " est mort. Toi aussi.");
			player->AsActorValueOwner()->DamageActorValue(RE::ActorValue::kHealth, 1000000.0f);
		}

		if (dead && !g_session.wasDead) {
			if (g_session.ignoreNextDeath) {
				g_session.ignoreNextDeath = false;
			} else if (g_session.deathLink) {
				const auto now = std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();
				Client::Get().Send({
					{ "cmd", "Bounce" },
					{ "tags", json::array({ "DeathLink" }) },
					{ "data", { { "time", now }, { "source", Config::Get().slot }, { "cause", Config::Get().slot + " est mort dans Skyrim." } } },
				});
				logger::info("DeathLink sent");
			}
		}
		g_session.wasDead = dead;
	}

	// ------------------------------------------------------------------ //
	// Items
	// ------------------------------------------------------------------ //
	void EnsureShout(RE::TESShout* a_shout, int a_words)
	{
		auto* player = Player();
		if (!player || !a_shout) {
			return;
		}
		auto& ensured = g_session.shoutsEnsured[a_shout];
		if (ensured >= a_words) {
			return;
		}
		player->AddShout(a_shout);
		for (int i = 0; i < std::min(a_words, 3); ++i) {
			auto* word = a_shout->variations[i].word;
			if (!word) {
				continue;
			}
			CallStatic("Game", "TeachWord", word);
			if (g_session.autoUnlockShouts) {
				player->UnlockWord(word);
			}
		}
		ensured = a_words;
	}

	void ApplyConsumable(const ItemDef& a_def)
	{
		auto* player = Player();
		if (a_def.type == "item") {
			if (a_def.object) {
				player->AddObjectToContainer(a_def.object, nullptr, a_def.count, nullptr);
			}
		} else if (a_def.type == "perk_point") {
			auto& stats = player->GetGameStatsData();
			if (stats.perkCount < 255) {
				++stats.perkCount;
			}
		} else if (a_def.type == "dragon_soul") {
			player->AsActorValueOwner()->ModBaseActorValue(RE::ActorValue::kDragonSouls, 1.0f);
			// Not absorbed by the player: don't count it as a Dragon Soul check.
			if (g_save.lastSouls >= 0) {
				++g_save.lastSouls;
			}
		} else if (a_def.type == "trap_fine") {
			auto* gold = RE::TESForm::LookupByID<RE::TESBoundObject>(0x0000000F);
			if (gold) {
				const auto counts = player->GetInventoryCounts([gold](RE::TESBoundObject& a_obj) { return &a_obj == gold; });
				const auto it = counts.find(gold);
				const auto have = it != counts.end() ? it->second : 0;
				const auto fine = have * a_def.percent / 100;
				if (fine > 0) {
					player->RemoveItem(gold, fine, RE::ITEM_REMOVE_REASON::kRemove, nullptr, nullptr);
				}
			}
		} else if (a_def.type == "trap_dragon") {
			// TODO: spawn a dragon near the player once the actor form is confirmed.
			logger::info("Dragon trap received (not implemented yet)");
		}
	}

	void ApplyItems()
	{
		// Persistent effects, recomputed from the full item list.
		std::uint32_t                cityMask = 0;
		std::map<RE::TESShout*, int> shoutWords;
		for (const auto& entry : g_session.items) {
			const auto it = g_items.find(entry.value("item", std::int64_t{ 0 }));
			if (it == g_items.end()) {
				continue;
			}
			const auto& def = it->second;
			if (def.type == "gate_key") {
				for (const auto& city : g_cities) {
					if (city.name == def.city) {
						cityMask |= city.bit;
					}
				}
			} else if (def.type == "shout" && def.shout) {
				++shoutWords[def.shout];
			}
		}
		g_save.cityMask = cityMask;
		for (const auto& [shout, words] : shoutWords) {
			EnsureShout(shout, words);
		}

		// One-time effects and notifications for items not applied in this save yet.
		const auto total = static_cast<std::uint32_t>(g_session.items.size());
		if (g_save.itemsApplied >= total) {
			return;
		}
		const auto newCount = total - g_save.itemsApplied;
		for (auto i = g_save.itemsApplied; i < total; ++i) {
			const auto& entry = g_session.items[i];
			const auto  it = g_items.find(entry.value("item", std::int64_t{ 0 }));
			if (it == g_items.end()) {
				logger::warn("Unknown item id {}", entry.value("item", std::int64_t{ 0 }));
				continue;
			}
			ApplyConsumable(it->second);
			if (newCount <= 5) {
				const auto sender = entry.value("player", -1);
				// Slot 0 is the server itself (starting inventory, /send).
				std::string from = (sender == g_session.slot || sender == 0) ? "" : " (de " + PlayerName(sender) + ")";
				Game::Notify("Reçu : " + it->second.fr + from);
			}
		}
		if (newCount > 5) {
			Game::Notify(fmt::format("Archipelago : {} objets reçus", newCount));
		}
		g_save.itemsApplied = total;
	}

	// ------------------------------------------------------------------ //
	// Checks
	// ------------------------------------------------------------------ //
	void TrackDragonSouls()
	{
		auto*      player = Player();
		const auto current = static_cast<std::int32_t>(player->AsActorValueOwner()->GetActorValue(RE::ActorValue::kDragonSouls));
		if (g_save.lastSouls < 0) {
			g_save.lastSouls = current;
			return;
		}
		if (current > g_save.lastSouls) {
			g_save.soulsAbsorbed += static_cast<std::uint32_t>(current - g_save.lastSouls);
			logger::info("Dragon souls absorbed: {}", g_save.soulsAbsorbed);
		}
		g_save.lastSouls = current;
	}

	void CheckLocations()
	{
		json locations = json::array();
		for (const auto& loc : g_locations) {
			if (g_session.checked.contains(loc.id)) {
				continue;
			}
			bool done = false;
			if (loc.dragonSoul > 0) {
				done = loc.dragonSoul <= g_session.dragonSoulChecks &&
				       g_save.soulsAbsorbed >= static_cast<std::uint32_t>(loc.dragonSoul);
			} else if (loc.quest) {
				done = loc.quest->IsCompleted();
			}
			if (done) {
				locations.push_back(loc.id);
				g_session.checked.insert(loc.id);
				logger::info("Check: {}", loc.name);
			}
		}
		if (!locations.empty()) {
			Client::Get().Send({ { "cmd", "LocationChecks" }, { "locations", locations } });
		}

		if (!g_session.goalSent) {
			bool goal = g_save.soulsAbsorbed >= g_session.goalSouls;
			for (const auto id : g_session.goalLocations) {
				goal = goal && g_session.checked.contains(id);
			}
			goal = goal && (g_session.goalSouls > 0 || !g_session.goalLocations.empty());
			if (goal) {
				Client::Get().Send({ { "cmd", "StatusUpdate" }, { "status", CLIENT_STATUS_GOAL } });
				g_session.goalSent = true;
				Game::Notify("Archipelago : objectif atteint !");
			}
		}
	}

	// ------------------------------------------------------------------ //
	// Locked city gates
	// ------------------------------------------------------------------ //
	RE::TESObjectREFR* GetMarker()
	{
		auto* player = Player();
		RE::TESObjectREFR* marker = g_save.marker ? RE::TESForm::LookupByID<RE::TESObjectREFR>(g_save.marker) : nullptr;
		if (!marker) {
			auto* base = RE::TESForm::LookupByID<RE::TESBoundObject>(XMARKER);
			if (!base) {
				return nullptr;
			}
			auto placed = player->PlaceObjectAtMe(base, true);
			if (!placed) {
				return nullptr;
			}
			marker = placed.get();
			g_save.marker = marker->GetFormID();
		}
		return marker;
	}

	void EnforceGates()
	{
		auto* player = Player();
		auto* ui = RE::UI::GetSingleton();
		if (!player || !ui || ui->IsMenuOpen(RE::LoadingMenu::MENU_NAME)) {
			return;
		}

		const CityDef* locked = nullptr;
		auto*          world = player->GetWorldspace();
		for (const auto& city : g_cities) {
			if (city.worldspace && city.worldspace == world && !(g_save.cityMask & city.bit)) {
				locked = &city;
			}
		}

		if (!locked) {
			g_session.lockedWarnedFor.clear();
			const auto now = std::chrono::steady_clock::now();
			if (now - g_session.lastMarkerUpdate > 2s) {
				g_session.lastMarkerUpdate = now;
				if (auto* marker = GetMarker()) {
					marker->MoveTo(player);
				}
			}
			return;
		}

		if (auto* marker = g_save.marker ? RE::TESForm::LookupByID<RE::TESObjectREFR>(g_save.marker) : nullptr) {
			player->MoveTo(marker);
		}
		if (g_session.lockedWarnedFor != locked->name) {
			g_session.lockedWarnedFor = locked->name;
			Game::Notify("Les portes de " + locked->fr + " sont verrouillées. Il te faut la clé de " + locked->fr + ".");
		}
	}

	// ------------------------------------------------------------------ //
	// Co-save string helpers
	// ------------------------------------------------------------------ //
	void WriteString(SKSE::SerializationInterface* a_intfc, const std::string& a_str)
	{
		const auto len = static_cast<std::uint32_t>(a_str.size());
		a_intfc->WriteRecordData(&len, sizeof(len));
		if (len) {
			a_intfc->WriteRecordData(a_str.data(), len);
		}
	}

	std::string ReadString(SKSE::SerializationInterface* a_intfc)
	{
		std::uint32_t len = 0;
		a_intfc->ReadRecordData(&len, sizeof(len));
		std::string str(len, '\0');
		if (len) {
			a_intfc->ReadRecordData(str.data(), len);
		}
		return str;
	}
}

namespace Game
{
	void Notify(const std::string& a_text)
	{
		logger::info("[notify] {}", a_text);
		CallStatic("Debug", "Notification", RE::BSFixedString(a_text.c_str()));
	}

	void LoadData()
	{
		std::ifstream in("Data/SKSE/Plugins/SkyrimArchipelago.json");
		if (!in) {
			logger::error("SkyrimArchipelago.json not found");
			return;
		}
		const auto data = json::parse(in, nullptr, false);
		if (data.is_discarded()) {
			logger::error("SkyrimArchipelago.json is not valid JSON");
			return;
		}

		std::uint32_t bit = 1;
		for (const auto& [name, city] : data["cities"].items()) {
			CityDef def{ name, city.value("fr", name), bit, nullptr };
			bit <<= 1;
			const auto editorID = city.value("worldspace", std::string{});
			for (auto* ws : RE::TESDataHandler::GetSingleton()->GetFormArray<RE::TESWorldSpace>()) {
				const char* id = ws ? ws->GetFormEditorID() : nullptr;
				if (id && editorID == id) {
					def.worldspace = ws;
				}
			}
			logger::info("City {} -> worldspace {}: {}", name, editorID, FormInfo(def.worldspace));
			g_cities.push_back(std::move(def));
		}

		for (const auto& [id, item] : data["items"].items()) {
			ItemDef def;
			def.name = item.value("name", std::string{});
			def.fr = item.value("fr", def.name);
			def.type = item.value("type", std::string{});
			def.city = item.value("city", std::string{});
			def.count = item.value("count", 1);
			def.percent = item.value("percent", 0);
			if (item.contains("form")) {
				auto* form = LookupForm(item["form"].get<std::string>());
				def.object = form ? form->As<RE::TESBoundObject>() : nullptr;
				logger::info("Item '{}' -> {}", def.name, FormInfo(def.object));
			}
			if (item.contains("shout")) {
				auto* form = LookupForm(item["shout"].get<std::string>());
				def.shout = form ? form->As<RE::TESShout>() : nullptr;
				logger::info("Item '{}' -> shout {}", def.name, FormInfo(def.shout));
				if (def.shout) {
					for (int i = 0; i < 3; ++i) {
						logger::info("    word {}: {}", i + 1, FormInfo(def.shout->variations[i].word));
					}
				}
			}
			g_items[std::stoll(id)] = std::move(def);
		}

		for (const auto& loc : data["locations"]) {
			LocationDef def;
			def.id = loc.value("id", std::int64_t{ 0 });
			def.name = loc.value("name", std::string{});
			def.dragonSoul = loc.value("dragon_soul", 0);
			if (loc.contains("quest")) {
				auto* form = LookupForm(loc["quest"].get<std::string>());
				def.quest = form ? form->As<RE::TESQuest>() : nullptr;
				logger::info("Location '{}' -> quest {}", def.name, FormInfo(def.quest));
			}
			g_locations.push_back(std::move(def));
		}


		logger::info("Loaded {} items, {} locations, {} cities", g_items.size(), g_locations.size(), g_cities.size());
	}

	void OnPreLoadGame()
	{
		g_session.gameLoaded = false;
	}

	void OnGameLoaded()
	{
		g_session.gameLoaded = true;
		g_session.shoutsEnsured.clear();
		g_session.mismatchWarned = false;
		g_session.goalSent = false;
		g_session.lockedWarnedFor.clear();
		g_session.wasDead = false;
		g_session.ignoreNextDeath = false;
		g_session.pendingDeathFrom.reset();
		if (Config::Get().slot.empty()) {
			Notify("Archipelago : renseigne ton nom de joueur dans SkyrimArchipelago.ini.");
		}
	}

	void Tick()
	{
		for (const auto& msg : Client::Get().Poll()) {
			HandleMessage(msg);
		}

		auto* player = Player();
		if (!g_session.gameLoaded || !player || !player->Is3DLoaded()) {
			return;
		}

		// Bind a fresh save to the current multiworld.
		if (g_session.connected && g_save.seed.empty() && !g_session.seedName.empty()) {
			g_save.seed = g_session.seedName;
			g_save.slot = Config::Get().slot;
			Notify("Archipelago : cette sauvegarde est maintenant liée à la partie " + g_save.seed + ".");
		}
		if (g_session.connected && !IsBound() && !g_session.mismatchWarned) {
			g_session.mismatchWarned = true;
			Notify("Archipelago : cette sauvegarde appartient à une autre partie. Rien ne sera envoyé ni reçu.");
		}

		TrackDragonSouls();

		if (IsBound()) {
			HandleDeathLink();
			ApplyItems();
			CheckLocations();
		}

		if (!g_save.seed.empty()) {
			EnforceGates();
		}
	}

	void OnSave(SKSE::SerializationInterface* a_intfc)
	{
		if (!a_intfc->OpenRecord(RECORD_STATE, SAVE_VERSION)) {
			logger::error("Failed to open co-save record");
			return;
		}
		WriteString(a_intfc, g_save.seed);
		WriteString(a_intfc, g_save.slot);
		a_intfc->WriteRecordData(&g_save.itemsApplied, sizeof(g_save.itemsApplied));
		a_intfc->WriteRecordData(&g_save.soulsAbsorbed, sizeof(g_save.soulsAbsorbed));
		a_intfc->WriteRecordData(&g_save.lastSouls, sizeof(g_save.lastSouls));
		a_intfc->WriteRecordData(&g_save.cityMask, sizeof(g_save.cityMask));
		a_intfc->WriteRecordData(&g_save.marker, sizeof(g_save.marker));
	}

	void OnLoad(SKSE::SerializationInterface* a_intfc)
	{
		g_save = {};
		std::uint32_t type, version, length;
		while (a_intfc->GetNextRecordInfo(type, version, length)) {
			if (type != RECORD_STATE || version != SAVE_VERSION) {
				continue;
			}
			g_save.seed = ReadString(a_intfc);
			g_save.slot = ReadString(a_intfc);
			a_intfc->ReadRecordData(&g_save.itemsApplied, sizeof(g_save.itemsApplied));
			a_intfc->ReadRecordData(&g_save.soulsAbsorbed, sizeof(g_save.soulsAbsorbed));
			a_intfc->ReadRecordData(&g_save.lastSouls, sizeof(g_save.lastSouls));
			a_intfc->ReadRecordData(&g_save.cityMask, sizeof(g_save.cityMask));
			RE::FormID marker = 0;
			a_intfc->ReadRecordData(&marker, sizeof(marker));
			RE::FormID resolved = 0;
			if (marker && a_intfc->ResolveFormID(marker, resolved)) {
				g_save.marker = resolved;
			}
		}
		logger::info("Loaded save state: seed='{}' slot='{}' items={} souls={}", g_save.seed, g_save.slot,
			g_save.itemsApplied, g_save.soulsAbsorbed);
	}

	void OnRevert(SKSE::SerializationInterface*)
	{
		g_save = {};
	}
}

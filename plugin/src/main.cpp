#include "Client.h"
#include "Config.h"
#include "Game.h"

namespace
{
	std::atomic_bool g_tickQueued{ false };
	std::thread      g_ticker;

	void SetupLog()
	{
		auto dir = logger::log_directory();
		if (!dir) {
			return;
		}
		*dir /= "SkyrimArchipelago.log";
		auto sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>(dir->string(), true);
		auto log = std::make_shared<spdlog::logger>("global", std::move(sink));
		log->set_level(spdlog::level::info);
		log->flush_on(spdlog::level::info);
		log->set_pattern("[%H:%M:%S] [%l] %v");
		spdlog::set_default_logger(std::move(log));
	}

	// Runs Game::Tick on the main thread twice per second.
	void StartTicker()
	{
		g_ticker = std::thread([] {
			while (true) {
				std::this_thread::sleep_for(500ms);
				if (g_tickQueued.exchange(true)) {
					continue;
				}
				SKSE::GetTaskInterface()->AddTask([] {
					Game::Tick();
					g_tickQueued = false;
				});
			}
		});
		g_ticker.detach();
	}

	void OnMessage(SKSE::MessagingInterface::Message* a_msg)
	{
		switch (a_msg->type) {
		case SKSE::MessagingInterface::kDataLoaded:
			Config::Get().Load();
			Game::LoadData();
			if (!Config::Get().slot.empty()) {
				Client::Get().Start(Config::Get().server);
			}
			StartTicker();
			break;
		case SKSE::MessagingInterface::kPreLoadGame:
			Game::OnPreLoadGame();
			break;
		case SKSE::MessagingInterface::kPostLoadGame:
		case SKSE::MessagingInterface::kNewGame:
			Game::OnGameLoaded();
			break;
		default:
			break;
		}
	}
}

SKSEPluginLoad(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	SetupLog();
	logger::info("Skyrim Archipelago loaded");

	auto* serialization = SKSE::GetSerializationInterface();
	serialization->SetUniqueID('SKAP');
	serialization->SetSaveCallback(Game::OnSave);
	serialization->SetLoadCallback(Game::OnLoad);
	serialization->SetRevertCallback(Game::OnRevert);

	SKSE::GetMessagingInterface()->RegisterListener(OnMessage);
	return true;
}

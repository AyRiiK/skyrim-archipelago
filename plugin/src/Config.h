#pragma once

// Settings read from Data/SKSE/Plugins/SkyrimArchipelago.ini
struct Config
{
	std::string server{ "archipelago.gg:38281" };
	std::string slot;
	std::string password;
	bool        showSentItems{ true };

	static Config& Get()
	{
		static Config instance;
		return instance;
	}

	void Load();
};

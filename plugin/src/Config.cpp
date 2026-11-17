#include "Config.h"

namespace
{
	std::string Trim(std::string s)
	{
		const auto ws = " \t\r\n";
		const auto b = s.find_first_not_of(ws);
		if (b == std::string::npos) {
			return {};
		}
		const auto e = s.find_last_not_of(ws);
		return s.substr(b, e - b + 1);
	}
}

void Config::Load()
{
	const std::filesystem::path path{ "Data/SKSE/Plugins/SkyrimArchipelago.ini" };
	std::ifstream               in(path);
	if (!in) {
		logger::warn("Config file {} not found, using defaults", path.string());
		return;
	}

	std::string line;
	while (std::getline(in, line)) {
		line = Trim(line);
		if (line.empty() || line[0] == ';' || line[0] == '#' || line[0] == '[') {
			continue;
		}
		const auto eq = line.find('=');
		if (eq == std::string::npos) {
			continue;
		}
		const auto key = Trim(line.substr(0, eq));
		const auto value = Trim(line.substr(eq + 1));

		if (key == "Server") {
			server = value;
		} else if (key == "Slot") {
			slot = value;
		} else if (key == "Password") {
			password = value;
		} else if (key == "ShowSentItems") {
			showSentItems = value == "1" || value == "true";
		}
	}
	logger::info("Config: server={} slot={}", server, slot);
}

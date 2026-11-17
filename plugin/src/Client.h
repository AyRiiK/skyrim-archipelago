#pragma once

namespace ix
{
	class WebSocket;
}

// Network side: keeps a websocket connection to the Archipelago server.
// Runs on its own threads; the game thread polls messages with Poll().
class Client
{
public:
	static Client& Get()
	{
		static Client instance;
		return instance;
	}

	void Start(const std::string& a_server);
	void Stop();

	// Thread-safe. Sends one Archipelago command (wrapped in a JSON array).
	void Send(const json& a_command);

	// Called from the game thread: takes every message received so far.
	// Synthetic commands "_open" and "_closed" report the connection state.
	std::vector<json> Poll();

	bool IsOpen() const { return _open.load(); }

	~Client();

private:
	Client() = default;

	void Loop();
	void Push(json a_msg);
	void OnClosed();

	std::vector<std::string> _urls;
	std::size_t              _urlIndex{ 0 };
	bool                     _everOpened{ false };

	std::unique_ptr<ix::WebSocket> _ws;
	std::mutex                     _wsLock;

	std::atomic_bool _running{ false };
	std::atomic_bool _open{ false };
	std::atomic_bool _connecting{ false };
	std::thread      _thread;

	std::mutex       _inboxLock;
	std::deque<json> _inbox;
};

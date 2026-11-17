#include "Client.h"

#include <ixwebsocket/IXNetSystem.h>
#include <ixwebsocket/IXWebSocket.h>

Client::Client() = default;
Client::~Client() = default;

void Client::Start(const std::string& a_server)
{
	if (_running.exchange(true)) {
		return;
	}

	ix::initNetSystem();

	// "archipelago.gg:38281" -> try secure first, then plain websocket.
	if (a_server.starts_with("ws://") || a_server.starts_with("wss://")) {
		_urls = { a_server };
	} else if (a_server.starts_with("localhost") || a_server.starts_with("127.0.0.1")) {
		// A server on this PC never uses TLS.
		_urls = { "ws://" + a_server, "wss://" + a_server };
	} else {
		_urls = { "wss://" + a_server, "ws://" + a_server };
	}

	_thread = std::thread([this] { Loop(); });
}

void Client::Stop()
{
	if (!_running.exchange(false)) {
		return;
	}
	if (_thread.joinable()) {
		_thread.join();
	}
	std::scoped_lock lock(_wsLock);
	if (_ws) {
		_ws->stop();
		_ws.reset();
	}
}

void Client::Loop()
{
	auto nextAttempt = std::chrono::steady_clock::now();

	while (_running.load()) {
		std::this_thread::sleep_for(250ms);

		if (_open.load() || _connecting.load() || std::chrono::steady_clock::now() < nextAttempt) {
			continue;
		}

		std::scoped_lock lock(_wsLock);
		if (_ws) {
			_ws->stop();
			_ws.reset();
		}

		const auto url = _urls[_urlIndex % _urls.size()];
		logger::info("Connecting to {}", url);

		_ws = std::make_unique<ix::WebSocket>();
		_ws->setUrl(url);
		_ws->disableAutomaticReconnection();
		_ws->setPingInterval(30);

		ix::SocketTLSOptions tls;
		tls.caFile = "SYSTEM";
		_ws->setTLSOptions(tls);

		_ws->setOnMessageCallback([this, url](const ix::WebSocketMessagePtr& a_msg) {
			switch (a_msg->type) {
			case ix::WebSocketMessageType::Open:
				logger::info("Connected to {}", url);
				_everOpened = true;
				_connecting = false;
				_open = true;
				Push(json{ { "cmd", "_open" } });
				break;
			case ix::WebSocketMessageType::Message:
				{
					auto parsed = json::parse(a_msg->str, nullptr, false);
					if (parsed.is_array()) {
						for (auto& cmd : parsed) {
							Push(std::move(cmd));
						}
					} else {
						logger::warn("Unexpected message: {}", a_msg->str.substr(0, 200));
					}
				}
				break;
			case ix::WebSocketMessageType::Error:
				logger::warn("Connection error on {}: {}", url, a_msg->errorInfo.reason);
				OnClosed();
				break;
			case ix::WebSocketMessageType::Close:
				logger::info("Connection closed ({})", a_msg->closeInfo.reason);
				OnClosed();
				break;
			default:
				break;
			}
		});

		_connecting = true;
		_ws->start();
		nextAttempt = std::chrono::steady_clock::now() + 5s;
	}
}

void Client::OnClosed()
{
	const bool wasOpen = _open.exchange(false);
	_connecting = false;
	if (!_everOpened) {
		// This URL never worked: try the next scheme.
		++_urlIndex;
	}
	if (wasOpen) {
		Push(json{ { "cmd", "_closed" } });
	}
}

void Client::Send(const json& a_command)
{
	std::scoped_lock lock(_wsLock);
	if (_ws && _open.load()) {
		_ws->send(json::array({ a_command }).dump());
	}
}

void Client::Push(json a_msg)
{
	std::scoped_lock lock(_inboxLock);
	_inbox.push_back(std::move(a_msg));
}

std::vector<json> Client::Poll()
{
	std::scoped_lock  lock(_inboxLock);
	std::vector<json> out(std::make_move_iterator(_inbox.begin()), std::make_move_iterator(_inbox.end()));
	_inbox.clear();
	return out;
}

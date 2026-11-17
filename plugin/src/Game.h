#pragma once

// Game side: everything here runs on Skyrim's main thread.
namespace Game
{
	// Reads SkyrimArchipelago.json and resolves forms. Call at kDataLoaded.
	void LoadData();

	void OnPreLoadGame();
	void OnGameLoaded();

	// Called regularly on the main thread (see main.cpp).
	void Tick();

	// SKSE co-save callbacks.
	void OnSave(SKSE::SerializationInterface* a_intfc);
	void OnLoad(SKSE::SerializationInterface* a_intfc);
	void OnRevert(SKSE::SerializationInterface* a_intfc);

	void Notify(const std::string& a_text);
}

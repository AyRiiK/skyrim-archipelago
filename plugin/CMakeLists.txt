cmake_minimum_required(VERSION 3.25)

project(SkyrimArchipelago VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION_RELEASE ON)

# CommonLibSSE-NG (git submodule, pinned to a release tag so CI can use its prebuilt library).
set(BUILD_TESTS OFF CACHE BOOL "" FORCE)
add_subdirectory(lib/commonlibsse-ng EXCLUDE_FROM_ALL)
if(NOT COMMAND add_commonlibsse_plugin)
	include(lib/commonlibsse-ng/cmake/CommonLibSSE.cmake)
endif()

find_package(nlohmann_json CONFIG REQUIRED)
find_package(ixwebsocket CONFIG REQUIRED)

add_commonlibsse_plugin(
	${PROJECT_NAME}
	NAME "SkyrimArchipelago"
	AUTHOR "Skyrim AP contributors"
	SOURCES
		src/main.cpp
		src/Config.cpp
		src/Client.cpp
		src/Game.cpp
)

target_precompile_headers(${PROJECT_NAME} PRIVATE src/PCH.h)
target_include_directories(${PROJECT_NAME} PRIVATE src)
# Keep <windows.h> from pulling the old winsock.h (conflicts with ixwebsocket) and the min/max macros.
target_compile_definitions(${PROJECT_NAME} PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX)
target_link_libraries(${PROJECT_NAME} PRIVATE nlohmann_json::nlohmann_json ixwebsocket::ixwebsocket)

if(MSVC)
	target_compile_options(${PROJECT_NAME} PRIVATE /utf-8 /Zc:preprocessor /permissive- /W3)
endif()

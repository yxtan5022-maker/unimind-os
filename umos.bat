@echo off
REM UMOS launcher for Windows.
REM Usage: umos [--desktop|--demo|--mcp|--healer|--cluster|subcommand...]

setlocal enabledelayedexpansion
set "UMOS_ROOT=%~dp0"

if "%~1"=="" goto desktop
if "%~1"=="--desktop" goto desktop
if "%~1"=="desktop" goto desktop
if "%~1"=="gui" goto desktop
if "%~1"=="--demo" goto demo
if "%~1"=="demo" goto demo
if "%~1"=="--mcp" goto mcp
if "%~1"=="mcp" goto mcp
if "%~1"=="--healer" goto healer
if "%~1"=="healer" goto healer
if "%~1"=="--cluster" goto cluster
if "%~1"=="cluster" goto cluster
if "%~1"=="--iep" goto iep
if "%~1"=="iep" goto iep
if "%~1"=="--build" goto build
if "%~1"=="build" goto build
if "%~1"=="--test" goto tests
if "%~1"=="test" goto tests
if "%~1"=="--tests" goto tests
if "%~1"=="--help" goto help
if "%~1"=="-h" goto help

:desktop
python "%UMOS_ROOT%gui\app.py" %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:demo
python -m umos_py.demo %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:mcp
python -m bridge.hermes.mcp_server %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:healer
python -m bridge.healer %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:cluster
python -m bridge.distributed.node %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:iep
python -m bridge.iep.dispatcher %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:build
python "%UMOS_ROOT%build_exe.py" %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:tests
python -m pytest "%UMOS_ROOT%tests\" -v %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:help
echo UMOS -- UniMind, a user-space quantum-classical middleware prototype
echo Usage: umos [command] [args...]
echo.
echo Commands:
echo   (default)      Launch Desktop GUI
echo   --desktop      Launch Desktop GUI
echo   --demo         Run CLI demo
echo   --mcp          Start MCP server (stdio)
echo   --healer       Start self-healing daemon
echo   --cluster      Start distributed cluster node
echo   --iep          Start IEP dispatcher demo
echo   --build        Build standalone binary
echo   --test         Run all tests
echo   --help         Show this message
goto :eof

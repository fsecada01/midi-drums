@echo off
setlocal enabledelayedexpansion

for %%I in ("%~dp0..") do set "REPO_ROOT=%%~fI"

set "REAPER_RESOURCE_PATH=%~1"
if "%REAPER_RESOURCE_PATH%"=="" set "REAPER_RESOURCE_PATH=%APPDATA%\REAPER"

if not exist "%REAPER_RESOURCE_PATH%\Scripts" (
    echo REAPER Scripts folder not found at "%REAPER_RESOURCE_PATH%\Scripts"
    echo Pass your REAPER resource path as an argument, e.g.:
    echo   install_reaper_panel.bat "C:\Users\you\AppData\Roaming\REAPER"
    echo ^(Find yours in REAPER: Options -^> Show REAPER resource path in explorer/finder^)
    exit /b 1
)

set "PANEL_LINK=%REAPER_RESOURCE_PATH%\Scripts\midi_drums_panel.lua"
set "MODULE_LINK=%REAPER_RESOURCE_PATH%\Scripts\midi_drums"
set "FAILED=0"

if exist "%PANEL_LINK%" (
    echo Skipping midi_drums_panel.lua - already exists at "%PANEL_LINK%"
) else (
    mklink "%PANEL_LINK%" "%REPO_ROOT%\reaper\midi_drums_panel.lua"
    if errorlevel 1 set "FAILED=1"
)

if exist "%MODULE_LINK%" (
    echo Skipping midi_drums\ - already exists at "%MODULE_LINK%"
) else (
    mklink /D "%MODULE_LINK%" "%REPO_ROOT%\reaper\midi_drums"
    if errorlevel 1 set "FAILED=1"
)

if "%FAILED%"=="1" (
    echo.
    echo mklink failed - it needs either an elevated ^(Administrator^) prompt or
    echo Windows Developer Mode enabled ^(Settings -^> Privacy ^& security -^> For developers^).
    echo Re-run this script from an elevated cmd, or enable Developer Mode and retry.
    exit /b 1
)

echo.
echo Done. In REAPER: Actions -^> Load ReaScript -^> select midi_drums_panel.lua, then assign it a shortcut.
endlocal

#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

REAPER_RESOURCE_PATH="${1:-}"
if [ -z "$REAPER_RESOURCE_PATH" ]; then
    case "$(uname -s)" in
        Darwin) REAPER_RESOURCE_PATH="$HOME/Library/Application Support/REAPER" ;;
        *)      REAPER_RESOURCE_PATH="$HOME/.config/REAPER" ;;
    esac
fi

if [ ! -d "$REAPER_RESOURCE_PATH/Scripts" ]; then
    echo "REAPER Scripts folder not found at $REAPER_RESOURCE_PATH/Scripts"
    echo "Pass your REAPER resource path as an argument, e.g.:"
    echo "  install_reaper_panel.sh \"\$HOME/.config/REAPER\""
    exit 1
fi

PANEL_LINK="$REAPER_RESOURCE_PATH/Scripts/midi_drums_panel.lua"
MODULE_LINK="$REAPER_RESOURCE_PATH/Scripts/midi_drums"

if [ -e "$PANEL_LINK" ]; then
    echo "Skipping midi_drums_panel.lua - already exists at $PANEL_LINK"
else
    ln -s "$REPO_ROOT/reaper/midi_drums_panel.lua" "$PANEL_LINK"
fi

if [ -e "$MODULE_LINK" ]; then
    echo "Skipping midi_drums/ - already exists at $MODULE_LINK"
else
    ln -s "$REPO_ROOT/reaper/midi_drums" "$MODULE_LINK"
fi

echo
echo "Done. In REAPER: Actions -> Load ReaScript -> select midi_drums_panel.lua, then assign it a shortcut."

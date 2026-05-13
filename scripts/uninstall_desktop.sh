#!/usr/bin/env bash
set -euo pipefail

echo "Uninstalling Jarvis Linux Assistant..."

rm -f "$HOME/.local/share/applications/jarvis.desktop"
rm -f "$HOME/.local/bin/jarvis"
rm -f "$HOME/.local/share/icons/hicolor/64x64/apps/jarvis.png"
rm -f "$HOME/.local/share/icons/hicolor/256x256/apps/jarvis.png"

echo "✓ Desktop entry removed"
echo "✓ Launcher script removed"
echo "✓ Icons removed"
echo ""
echo "Config and logs remain in ~/.jarvis/"
echo "Project files remain in $(dirname "$0")/.."
echo "To fully remove, delete the project folder manually."

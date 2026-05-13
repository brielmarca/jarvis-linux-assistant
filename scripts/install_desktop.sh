#!/usr/bin/env bash
set -euo pipefail

APP_NAME="jarvis-linux-assistant"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DESKTOP_FILE="$PROJECT_DIR/packaging/jarvis.desktop"
ICON_256="$PROJECT_DIR/packaging/icons/jarvis-256.png"
ICON_64="$PROJECT_DIR/packaging/icons/jarvis-64.png"
TRAY_ICON="$PROJECT_DIR/jarvis/ui/assets/tray_icon.png"

echo "Installing Jarvis Linux Assistant..."

# Update desktop file with actual path
sed -i "s|Exec=python3 .*|Exec=python3 $PROJECT_DIR/main.py|" "$DESKTOP_FILE"
sed -i "s|Icon=.*|Icon=$PROJECT_DIR/packaging/icons/jarvis|" "$DESKTOP_FILE"

# Install desktop file
DESKTOP_DEST="$HOME/.local/share/applications/jarvis.desktop"
mkdir -p "$HOME/.local/share/applications"
cp "$DESKTOP_FILE" "$DESKTOP_DEST"
echo "  ✓ Desktop file: $DESKTOP_DEST"

# Install icons
for size in 64 256; do
    xdg_dir="$HOME/.local/share/icons/hicolor/${size}x${size}/apps"
    mkdir -p "$xdg_dir"
    cp "$PROJECT_DIR/packaging/icons/jarvis-${size}.png" "$xdg_dir/jarvis.png"
done
echo "  ✓ Icons installed"

# Create launcher script
LAUNCHER="$HOME/.local/bin/jarvis"
mkdir -p "$HOME/.local/bin"
cat > "$LAUNCHER" << 'LAUNCHER_EOF'
#!/usr/bin/env bash
exec python3 "$(dirname "$0")/../JARVIS.MILHONARI_PROJECT/jarvis-linux-assistant/main.py" "$@"
LAUNCHER_EOF
chmod +x "$LAUNCHER"
echo "  ✓ Launcher script: $LAUNCHER"

# Update desktop file launcher path
sed -i "s|Exec=python3 $PROJECT_DIR/main.py|Exec=$LAUNCHER|" "$DESKTOP_DEST"

# Create config directory
mkdir -p "$HOME/.jarvis"
echo "  ✓ Config directory: $HOME/.jarvis"

echo ""
echo "Installation complete!"
echo "You can now:"
echo "  - Launch Jarvis from your app menu"
echo "  - Run 'jarvis' from terminal"
echo "  - Run 'jarvis --cli' for CLI mode"

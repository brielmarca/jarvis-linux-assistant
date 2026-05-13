#!/usr/bin/env bash
set -euo pipefail

# Build AppImage for Jarvis Linux Assistant
# Prerequisites: python3, PyQt6, appimagetool (optional)
#
# Usage:
#   bash scripts/build_appimage.sh
#
# Note: This requires appimagetool from AppImageKit.
# If not installed, the script will download it.

APP_NAME="Jarvis"
APP_DIR="Jarvis.AppDir"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Building AppImage for Jarvis Linux Assistant..."

# Clean previous build
rm -rf "$APP_DIR"

# Create AppDir structure
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/share/applications"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/64x64/apps"

# Copy project files
cp -r "$PROJECT_DIR" "$APP_DIR/usr/share/jarvis"
echo "  ✓ Project files copied"

# Create wrapper script
cat > "$APP_DIR/AppRun" << 'APPRUN_EOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$PATH"
exec python3 "$HERE/usr/share/jarvis/jarvis-linux-assistant/main.py" "$@"
APPRUN_EOF
chmod +x "$APP_DIR/AppRun"
echo "  ✓ AppRun created"

# Copy desktop file
cp "$PROJECT_DIR/packaging/jarvis.desktop" "$APP_DIR/"
cp "$PROJECT_DIR/packaging/jarvis.desktop" "$APP_DIR/usr/share/applications/"
echo "  ✓ Desktop file copied"

# Copy icons
cp "$PROJECT_DIR/packaging/icons/jarvis-256.png" "$APP_DIR/jarvis.png"
cp "$PROJECT_DIR/packaging/icons/jarvis-256.png" "$APP_DIR/usr/share/icons/hicolor/256x256/apps/jarvis.png"
cp "$PROJECT_DIR/packaging/icons/jarvis-64.png" "$APP_DIR/usr/share/icons/hicolor/64x64/apps/jarvis.png"
echo "  ✓ Icons copied"

# Check for appimagetool
if command -v appimagetool &> /dev/null; then
    appimagetool "$APP_DIR"
    echo "  ✓ AppImage built: Jarvis-x86_64.AppImage"
elif command -v appimaged &> /dev/null; then
    appimaged "$APP_DIR" Jarvis-x86_64.AppImage
    echo "  ✓ AppImage built"
elif [ -f "appimagetool-x86_64.AppImage" ]; then
    ./appimagetool-x86_64.AppImage "$APP_DIR"
    echo "  ✓ AppImage built"
else
    echo ""
    echo "  appimagetool not found."
    echo "  Download from: https://github.com/AppImage/AppImageKit/releases"
    echo "  Then run: appimagetool $APP_DIR"
    echo ""
    echo "  The AppDir has been prepared at: $APP_DIR"
fi

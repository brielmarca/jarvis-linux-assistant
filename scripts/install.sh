#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "  Jarvis Linux Assistant - Install"
echo "  =================================="

# Check Python version
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    echo "  Error: Python 3.10+ is required."
    exit 1
fi

PY_VER=$($PYTHON --version 2>&1 | awk '{print $2}')
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

echo "  Python version: $PY_VER"
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo "  Error: Python 3.10+ required, got $PY_VER"
    exit 1
fi

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "  Creating virtual environment..."
    $PYTHON -m venv .venv
fi

source .venv/bin/activate 2>/dev/null || source .venv/bin/activate

# Upgrade pip
echo "  Installing/upgrading pip..."
$PYTHON -m ensurepip --upgrade 2>/dev/null || true
$PYTHON -m pip install --upgrade pip 2>/dev/null || true

# Install Python dependencies
echo "  Installing Python dependencies..."
$PYTHON -m pip install -r requirements.txt 2>/dev/null || {
    # Fallback: install individually
    echo "  Trying individual installs..."
    pip install pyyaml requests PyQt6
}

# Check system dependencies
echo ""
echo "  Checking system dependencies..."
DEPS=(
    "xdotool:window control"
    "wmctrl:window management"
    "playerctl:media playback"
    "pactl:audio control"
    "espeak-ng:TTS fallback"
)

for dep_entry in "${DEPS[@]}"; do
    dep="${dep_entry%%:*}"
    desc="${dep_entry##*:}"
    if command -v "$dep" &>/dev/null; then
        echo "    ✓ $dep ($desc)"
    else
        echo "    ○ $dep ($desc) - optional, install with: sudo apt install -y $dep"
    fi
done

# Create data directories
echo ""
echo "  Creating data directories..."
mkdir -p "$HOME/.jarvis/logs"
mkdir -p "$HOME/.jarvis/memory"
echo "    ✓ ~/.jarvis/"

echo ""
echo "  Health check..."
$PYTHON -c "
import sys; sys.path.insert(0, '.')
try:
    from jarvis.core.health import HealthChecker
    hc = HealthChecker()
    results = hc.check_all()
    for r in results:
        icon = {'ok': '✓', 'warning': '○', 'error': '✗'}.get(r.status, '?')
        print(f'    {icon} {r.component}: {r.message}')
except Exception as e:
    print(f'    Warning: Health check failed ({e})')
"

echo ""
echo "  Install complete!"
echo "  Run: ./scripts/run.sh"
echo "  Or:  source .venv/bin/activate && $PYTHON main.py"

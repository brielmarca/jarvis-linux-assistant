#!/usr/bin/env bash
set -euo pipefail

echo "  Jarvis Model Setup"
echo "  =================="

# Ollama setup
echo ""
echo "  1. Ollama"
if command -v ollama &>/dev/null; then
    echo "  ✓ Ollama found"
    echo "  Pulling recommended model (qwen2.5:7b)..."
    echo "  This may take a while depending on your internet."
    ollama pull qwen2.5:7b
    echo "  ✓ Model downloaded"
else
    echo "  ✗ Ollama not found"
    echo "  Install: curl -fsSL https://ollama.com/install.sh | sh"
    echo "  Or visit: https://ollama.com/download"
fi

# Piper TTS setup
echo ""
echo "  2. Piper TTS"
if command -v piper &>/dev/null; then
    echo "  ✓ Piper found"
else
    echo "  ✗ Piper not found (optional)"
    echo "  Install: sudo apt install -y piper-tts"
    echo "  Or build from source: https://github.com/rhasspy/piper"
fi

# espeak-ng fallback
echo ""
echo "  3. espeak-ng (TTS fallback)"
if command -v espeak-ng &>/dev/null; then
    echo "  ✓ espeak-ng found"
else
    echo "  Installing espeak-ng..."
    sudo apt install -y espeak-ng
fi

echo ""
echo "  Setup complete!"
echo "  Start Ollama: ollama serve"
echo "  Then run:     ./scripts/run.sh"

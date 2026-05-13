# Voice System

## Architecture

```
Microphone → VAD → Wake Word Detector → STT → Assistant → TTS → Speakers
                ↓                           ↑
          Audio Pipeline ←──────────────────┘
          (cooldown, follow-up,
           interruption, ambient mode)
```

## Components

### Voice Activity Detection (`jarvis/voice/vad.py`)
- `VoiceActivityDetector`: Energy-based VAD with adaptive noise floor
  - Tracks noise floor via exponential moving average
  - Detects speech when energy exceeds threshold
  - Reports speech/silence chunk counts
- `EnergyVoiceDetector`: Simpler threshold-based detector
- `AudioEnergyNormalizer`: Normalizes audio before processing

### Audio Pipeline (`jarvis/voice/audio_pipeline.py`)
- **Wake word cooldown**: 2s cooldown after wake word activation to prevent re-triggering
- **Follow-up mode**: 8s window after response where subsequent speech is treated as follow-up (no wake word needed)
- **Interruption handling**: `interrupt_speaking()` flag stops TTS mid-stream
- **Ambient listening**: Passive mode listening for wake word without processing
- **Streaming transcription**: Real-time STT streaming with partial results
- **Callbacks**: waveform data, transcription text, state changes

### Wake Word (`jarvis/voice/wakeword.py`)
- OpenWakeWord integration
- Configurable sensitivity and model selection
- Config: `wake_word`, `wake_word_model`, `wake_word_sensitivity`

### Speech-to-Text (`jarvis/voice/stt.py`)
- faster-whisper for local STT
- Config: `whisper_model` (base/small/medium/large), `whisper_device` (auto/cpu/cuda)

### Text-to-Speech (`jarvis/voice/tts.py`)
- Piper TTS (primary) with espeak-ng fallback
- Config: `tts_model`, `enable_tts`

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `enable_voice` | false | Enable voice assistant |
| `enable_wake_word` | false | Enable wake word detection |
| `enable_tts` | false | Enable text-to-speech |
| `whisper_model` | base | STT model size |
| `whisper_device` | auto | STT compute device |
| `voice_vad_threshold` | 0.5 | VAD sensitivity (0.1–0.9) |
| `voice_wake_word_cooldown` | 2.0 | Seconds between wake word activations |
| `voice_follow_up_timeout` | 8.0 | Seconds to wait for follow-up commands |
| `wake_word` | jarvis | Wake word phrase |
| `wake_word_model` | hey_jarvis | Wake word model name |
| `wake_word_sensitivity` | 0.5 | Wake word sensitivity |

## Dependencies (Optional)
```bash
pip install openwakeword faster-whisper pyaudio numpy soundfile
sudo apt install piper-tts espeak-ng
```

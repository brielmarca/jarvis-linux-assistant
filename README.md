# Jarvis Linux Assistant

A premium, offline-first AI-powered desktop assistant for Linux with contextual awareness, voice control, semantic memory, desktop state tracking, workflow automation, and diagnostics.

![Jarvis](packaging/icons/jarvis-256.png)

---

## Features

### Core Intelligence
- **Semantic Memory** — TF-IDF based memory with search, pinning, tags, importance decay
- **Context Builder** — Rich AI prompt enrichment from project, session, activity, preferences, desktop state
- **Context Window** — Priority-based pruning, token budgeting, sliding window
- **Multi-Agent Architecture** — Intent classification with confidence scoring, routing, fallback chains
- **Skill System** — Hot-reloadable, metadata-rich, cooldown-aware, permission-gated skills
- **Local AI** — Ollama integration for AI fallback

### Desktop Awareness
- **Active window/app tracking** via xdotool
- **Workspace info** via wmctrl
- **Battery status** via sysfs
- **Network state** via nmcli/iwgetid
- **Media playback** via playerctl
- **Monitor layout** via xrandr
- **Top CPU processes** via ps

### Workflow Automation
- Define multi-step workflows with chained actions
- Built-in templates: Programming Mode, Streaming Mode, Morning Routine
- JSON persistence in `~/.jarvis/workflows/`
- Schedule workflows for later execution

### Voice (Optional)
- Wake word detection via OpenWakeWord
- Speech-to-Text via faster-whisper
- Text-to-Speech via Piper TTS or espeak-ng
- VAD with noise floor adaptation, wake word cooldown (2s), follow-up mode (8s)

### Diagnostics & Metrics
- Latency tracking for commands, AI, voice, skills
- Event counters and tracing
- Health check dashboard
- Performance monitoring

### User Interface
- Premium dark glassmorphism theme
- 12 tabs: Dashboard, Skills, Settings, Logs, Monitor, Dev Mode, Voice, Memory, Desktop, Workflows, Diagnostics, Health
- Animated waveform, thinking animation, live system monitor
- Command palette (Ctrl+P/K), sidebar navigation, notifications
- System tray with background operation

---

## Screenshots

| Dashboard | Memory | Desktop |
|-----------|--------|---------|
| *screenshot* | *screenshot* | *screenshot* |

| Workflows | Diagnostics | Settings |
|-----------|-------------|----------|
| *screenshot* | *screenshot* | *screenshot* |

---

## Installation

### Requirements
- **Python 3.10+**
- **Linux** (Ubuntu/Debian/Fedora/Arch)
- **PyQt6** (for GUI)

### Quick Install
```bash
git clone <repo-url> jarvis-linux-assistant
cd jarvis-linux-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Desktop App Install
```bash
bash scripts/install_desktop.sh
```
This installs:
- `.desktop` file → app appears in your system menu
- Icons → 64px and 256px in standard locations
- `jarvis` command → run from terminal
- Config directory → `~/.jarvis/`

### Uninstall
```bash
bash scripts/uninstall_desktop.sh
```

### AppImage (Optional)
```bash
bash scripts/build_appimage.sh
```

---

## Run

```bash
# GUI mode (default)
python3 main.py

# CLI mode
python3 main.py --cli

# Single command
python3 main.py "open firefox"

# Via installed launcher
jarvis
jarvis --cli
jarvis "system info"
```

---

## Voice Setup

### 1. Ollama (Required for AI features)
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull qwen2.5:7b
```

### 2. Piper TTS (Text-to-Speech)
```bash
# Debian/Ubuntu
sudo apt install piper-tts espeak-ng

# Or via pip
pip install piper-tts
```

### 3. OpenWakeWord (Wake word detection)
```bash
pip install openwakeword pyaudio numpy soundfile
```

### 4. faster-whisper (Speech-to-Text)
```bash
pip install faster-whisper
```

### Configure in Settings UI or `config/settings.yaml`:
```yaml
enable_voice: true
enable_wake_word: true
enable_tts: true
whisper_model: base
voice_vad_threshold: 0.5
voice_wake_word_cooldown: 2.0
voice_follow_up_timeout: 8.0
```

---

## Workflows

Create reusable automation workflows with the Workflows tab, or use built-in templates:

### Programming Mode
Opens terminal, VSCode, and launches a coding session

### Streaming Mode
Opens OBS, starts streaming, and configures audio

### Morning Routine
Shows system info, weather, calendar, and news

### Custom Workflows
Create from the UI: name → description → steps (one per line):
```
open terminal
run: ls -la
wait: 2
run: python3 main.py
```

---

## Memory System

### Types
- **Short-term**: Recent commands and context (auto-managed)
- **Long-term**: Persistent memories with importance scoring
- **Semantic**: TF-IDF vector search with pinning, tags, decay
- **Preferences**: Key-value user preferences
- **Projects**: Project path tracking

### Commands
```
remember that <something>
recall <topic>
what do you know about <topic>
forget everything
remember my main project is <name>
```

### Semantic Search
Use the search bar in the Memory tab, or ask: `search memory for <topic>`

---

## Diagnostics

The Diagnostics tab provides:
- **Latency**: Command, AI, voice, and skill latencies (ms)
- **Counters**: Total commands, AI requests, skills called, errors
- **Events**: Real-time event tracing
- **Health Check**: Verify Ollama, memory, desktop state, workflows, semantic memory

---

## Configuration

Settings UI (Settings tab) exposes all config options:
- **AI & Language**: Model, language, context length
- **Speech & Voice**: Whisper model, VAD threshold, cooldowns, follow-up timeout
- **Memory**: Semantic search, short-term limit
- **Context**: Max tokens, desktop state, recent activity
- **Features**: Workflows, metrics toggles
- **Permissions**: Dangerous command confirmation

Settings are stored in `config/settings.yaml` with automatic backup before save.

---

## Project Structure

```
jarvis-linux-assistant/
├── main.py                    # Entry point
├── config/settings.yaml       # Configuration
├── packaging/                 # Desktop app packaging
│   ├── jarvis.desktop         # .desktop file
│   └── icons/                 # App icons (SVG, PNG)
├── scripts/
│   ├── install_desktop.sh     # Desktop integration
│   ├── uninstall_desktop.sh   # Desktop removal
│   └── build_appimage.sh      # AppImage builder
├── jarvis/
│   ├── app.py                 # CLI/GUI launcher + onboarding
│   ├── core/
│   │   ├── assistant.py       # Main assistant logic
│   │   ├── semantic_memory.py # TF-IDF semantic memory
│   │   ├── context_window.py  # Context window management
│   │   ├── metrics.py         # Latency & counters
│   │   ├── events.py          # Event system (17 event types)
│   │   ├── router.py          # Command routing
│   │   ├── permissions.py     # Safety checks
│   │   ├── memory_manager.py  # Short/long term memory
│   │   ├── memory.py          # Basic history & state
│   │   ├── logger.py          # Structured logging
│   │   ├── config_validator.py# YAML validation
│   │   └── health.py          # Health & diagnostics
│   ├── agents/                # Multi-agent system
│   ├── ai/
│   │   ├── ollama_client.py   # Ollama with streaming
│   │   └── context_builder.py # AI context enrichment
│   ├── voice/
│   │   ├── vad.py             # Voice activity detection
│   │   ├── audio_pipeline.py  # Streaming, interruption, cooldown
│   │   ├── wakeword.py        # OpenWakeWord
│   │   ├── stt.py             # faster-whisper
│   │   ├── tts.py             # Piper/espeak
│   │   └── recorder.py        # Audio capture
│   ├── automation/
│   │   ├── workflows.py       # Workflow engine + templates
│   │   ├── linux.py           # System commands
│   │   ├── apps.py            # Application control
│   │   ├── media.py           # Volume & media
│   │   └── terminal.py        # Terminal commands
│   ├── system/
│   │   └── desktop_state.py   # Desktop awareness
│   ├── skills/                # Skill system (7 skills)
│   └── ui/
│       ├── main_window.py     # Main window (12 tabs)
│       ├── theme.py           # Dark glassmorphism theme
│       ├── components/
│       │   ├── memory_tab.py       # Enhanced memory UI
│       │   ├── desktop_tab.py      # Desktop awareness UI
│       │   ├── workflows_tab.py    # Workflow management UI
│       │   ├── diagnostics_tab.py  # Metrics + health UI
│       │   ├── onboarding.py       # First-run wizard
│       │   ├── splash.py           # Startup splash screen
│       │   ├── sidebar.py          # Navigation sidebar
│       │   ├── palette.py          # Command palette
│       │   ├── waveform.py         # Audio waveform
│       │   ├── thinking_animation.py
│       │   ├── system_monitor.py
│       │   ├── notification.py
│       │   ├── status_indicator.py
│       │   ├── command_input.py
│       │   ├── timeline_card.py
│       │   ├── skill_card.py
│       │   ├── health_tab.py
│       │   ├── voice_tab.py
│       │   ├── dev_mode.py
│       │   └── confirmation_dialog.py
└── tests/
    ├── test_core.py
    ├── test_skills.py
    └── test_new_features.py    # 86 tests covering all phases
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Submit command |
| `Up/Down` | Command history |
| `Escape` | Minimize to tray |
| `Ctrl+L` / `Ctrl+Return` | Focus input |
| `Ctrl+P` / `Ctrl+K` | Command palette |
| `Ctrl+1`–`Ctrl+9` | Switch to tab 1–9 |
| `Ctrl+0` | Switch to tab 10 |
| `Ctrl+W` | Close window |

---

## Commands

| Category | Commands |
|----------|----------|
| **System** | `time`, `date`, `system info`, `status`, `shutdown`, `reboot` |
| **Apps** | `open firefox`, `open vscode`, `open terminal`, `docker status` |
| **Browser** | `search for <query>`, `google <query>`, `go to <url>` |
| **Media** | `volume up/down`, `set volume 50`, `mute`, `play`, `next` |
| **Dev** | `programming mode`, `git status`, `open project <name>` |
| **Memory** | `remember that <x>`, `recall <topic>`, `forget everything` |
| **Skills** | `reload skills`, `list skills` |

---

## Safety Model

- Dangerous commands (`rm -rf`, `mkfs`, `dd`, shutdown, reboot) require confirmation
- Permission levels per skill (normal/elevated)
- OpenCode operations require explicit confirmation
- All command execution is logged
- No secrets/credentials stored in code

---

## Troubleshooting

### "No module named PyQt6"
```bash
pip install PyQt6
```

### "Ollama is not available"
```bash
ollama serve
ollama pull qwen2.5:7b
```

### "No module named yaml"
```bash
pip install pyyaml
```

### Voice features not working
Voice features require additional dependencies (see Voice Setup). The app degrades gracefully.

### Tests hang on context_window_prune
This was a deadlock bug that has been fixed (Lock → RLock). Run `pip install pytest && python3 -m pytest tests/ -v`.

---

## Known Limitations

- Voice features require additional dependencies (openwakeword, faster-whisper, pyaudio)
- Desktop state polling requires xdotool, wmctrl, playerctl, nmcli/iwgetid
- GUI requires a display server (X11 or Wayland with XWayland)
- Ollama is required for AI features
- AppImage build requires appimagetool (documented in build script)

---

## Roadmap

- [x] Phase J — Contextual AI + Memory Intelligence
- [x] Phase K — Voice Assistant Improvements (VAD, streaming, cooldown)
- [x] Phase L — Smart Desktop Awareness
- [x] Phase M — Advanced Automation Workflows
- [x] Phase P — Metrics & Observability
- [x] Phase R — Full System Validation (86 tests passing)
- [x] Phase S — Feature UI Integration (4 new UI tabs)
- [x] Phase T — Settings & Config Polish
- [x] Phase U — Packaging & Desktop App
- [x] Phase V — Final Product Polish (onboarding, splash)
- [x] Phase W — Release Quality Docs
- [ ] Phase N — Advanced Dev Assistant (live repo analysis)
- [ ] Phase O — Premium UI System (animations, components)
- [ ] Phase Q — CI/CD, Auto-updater

---

## Extending

### Add a Skill
```python
from jarvis.skills.base import BaseSkill

class MySkill(BaseSkill):
    def metadata(self):
        return {"description": "Does something cool", "category": "custom"}

    def patterns(self):
        return [r"(my command|meu comando) (.+)"]

    def execute(self, command, match):
        return "Custom response"
```

### Add an Agent
```python
from jarvis.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="myagent", description="Custom agent")

    def can_handle(self, command, context=None):
        if "my keyword" in command.lower():
            return True, 0.9
        return False, 0.0

    def execute(self, command, context=None):
        return {"response": "Handled!", "agent": "myagent"}
```

---

## Tests

```bash
# Install pytest
pip install pytest

# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_new_features.py -v
```

**86 tests** covering: core engine, memory system, semantic memory, context window, context builder, voice/VAD, desktop state, workflows, metrics, skill system, permissions, sandbox, and more.

---

## License

MIT

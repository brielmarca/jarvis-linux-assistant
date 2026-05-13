# Contributing to Jarvis Linux Assistant

## Getting Started

1. Fork the repository
2. Create a virtual environment: `python3 -m venv .venv && source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Install dev dependencies: `pip install pytest`
5. Run tests: `python3 -m pytest tests/ -v`

## Development Workflow

### Branch
```bash
git checkout -b feature/your-feature-name
```

### Code Style
- Follow existing code patterns (see `jarvis/skills/base.py`, `jarvis/core/assistant.py`)
- Use the project's Theme class for all UI styling
- No external cloud dependencies — keep it local and offline-first
- Use `JarvisLogger` for all logging
- Handle missing dependencies gracefully (try/except with informative messages)

### Testing
- Add tests to `tests/test_new_features.py` for new features
- Run all tests before submitting: `python3 -m pytest tests/ -v`
- Ensure individual tests pass in isolation

### Design Principles
- **Fast path**: Skill matches → instant execution (no AI needed)
- **AI path**: Agent fails → Ollama generates response with context
- **Safe path**: Dangerous commands require confirmation
- **Offline-first**: All core features work without internet
- **Graceful degradation**: Missing dependencies disable features without crashing

## Pull Request Guidelines

1. Keep changes focused on a single concern
2. Update tests for any new functionality
3. Update documentation if adding features
4. Ensure all existing tests still pass
5. Add CHANGELOG entry

## Project Structure

```
jarvis-linux-assistant/
├── main.py              # Entry point
├── config/              # YAML configuration
├── packaging/           # Desktop integration files
├── scripts/             # Install/uninstall/build scripts
├── jarvis/
│   ├── core/            # Core engine (assistant, memory, events, metrics, context)
│   ├── agents/          # Multi-agent system
│   ├── ai/              # AI integration (Ollama, context builder)
│   ├── voice/           # Voice processing (VAD, wakeword, STT, TTS)
│   ├── automation/      # System automation (workflows, apps, media)
│   ├── system/          # Desktop state awareness
│   ├── skills/          # Skill system (7 built-in skills)
│   └── ui/              # PyQt6 UI (main window, 12+ components)
└── tests/               # Test suite (86 tests)
```

## Adding a New UI Component

1. Create component in `jarvis/ui/components/`
2. Follow the existing patterns (see `desktop_tab.py`, `workflows_tab.py`)
3. Use `Theme.*` constants for all styling
4. Register in `jarvis/ui/main_window.py` (import + instantiate + addTab)
5. Update `jarvis/ui/components/sidebar.py` NAV_ITEMS if adding a navigation entry

## Adding a New Skill

```python
from jarvis.skills.base import BaseSkill

class MySkill(BaseSkill):
    def metadata(self):
        return {"description": "Description", "category": "custom"}

    def patterns(self):
        return [r"(trigger phrase|outra frase) (.+)"]

    def execute(self, command, match):
        return "Response"
```

Add to `enabled_skills` in `config/settings.yaml`.

## Adding a New Agent

```python
from jarvis.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="myagent", description="Custom agent")

    def can_handle(self, command, context=None):
        if "keyword" in command.lower():
            return True, 0.9
        return False, 0.0

    def execute(self, command, context=None):
        return {"response": "Handled!", "agent": "myagent"}
```

Register in `jarvis/core/assistant.py:_load_agents()`.

## Code Review Checklist

- [ ] Follows existing code style and patterns
- [ ] All tests pass (86/86)
- [ ] No external cloud dependencies added
- [ ] Graceful handling of missing optional dependencies
- [ ] UI components use Theme constants
- [ ] New features have test coverage
- [ ] Documentation updated
- [ ] CHANGELOG entry added
- [ ] No blocking/freezing UI operations

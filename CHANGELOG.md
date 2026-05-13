# Changelog

All notable changes to Jarvis Linux Assistant will be documented in this file.

## [1.0.0] — 2026-05-12

### Added
- **Phase J — Contextual AI & Memory Intelligence**
  - Semantic memory with TF-IDF embeddings, cosine similarity, importance decay, pinning
  - Context builder for AI prompt enrichment (project, session, activity, semantic, preferences, desktop)
  - Context window management with priority-based pruning and token budgeting
  - Streaming support in Ollama client
  - 8 new event types (memory, context, interruption, workflow, desktop, metrics)

- **Phase K — Voice Assistant Improvements**
  - Voice Activity Detection (VAD) with adaptive noise floor
  - Wake word cooldown (2s) for natural interaction
  - Conversational follow-up mode (8s window)
  - Interruption handling for multi-turn conversation
  - Ambient listening mode

- **Phase L — Smart Desktop Awareness**
  - Real-time desktop state tracking (active window, app, workspace)
  - Battery, network, media, monitor, CPU process monitoring
  - Background polling with 1s cache TTL

- **Phase M — Advanced Automation Workflows**
  - Reusable workflow system with chained actions
  - 3 built-in templates (programming mode, streaming mode, morning routine)
  - JSON persistence in `~/.jarvis/workflows/`
  - Workflow scheduling support

- **Phase P — Metrics & Observability**
  - Latency tracking, counters, event tracing
  - Metrics singleton integrated into assistant processing pipeline

- **Phase R — Full System Validation**
  - Fixed Lock → RLock deadlock in ContextWindow
  - Fixed BrowserSkill None match handling
  - Fixed SystemSkill "status" pattern
  - All 86 tests passing

- **Phase S — Feature UI Integration**
  - Desktop Awareness tab (real-time stats cards)
  - Workflows tab (list, create, run, templates)
  - Diagnostics tab (latency, counters, events, health check)
  - Enhanced Memory tab (semantic search, pin/unpin, short-term, pinned, forget)
  - Sidebar updated with 12 navigation items
  - Keyboard shortcuts extended (Ctrl+0 for tab 10)

- **Phase T — Settings & Config Polish**
  - 17 new settings exposed in Settings UI
  - Settings grouped by category (AI, Voice, Memory, Context, Features, Permissions)
  - Config backup before save
  - Reset to defaults
  - Restart-required indicators (⚡)
  - Validation feedback

- **Phase U — Packaging & Desktop App**
  - `.desktop` file following Linux standards
  - SVG + PNG icons (64px, 256px)
  - install_desktop.sh, uninstall_desktop.sh
  - build_appimage.sh for AppImage packaging
  - Tray icon added to UI assets

- **Phase V — Final Product Polish**
  - First-run onboarding wizard (6 pages)
  - Startup splash screen enhancements
  - Missing dependency warnings
  - Empty states in all UI tabs

- **Phase W — Release Quality Docs**
  - Comprehensive README.md with full installation, features, architecture
  - CHANGELOG.md
  - CONTRIBUTING.md
  - Architecture documentation (docs/architecture.md)
  - Voice documentation (docs/voice.md)
  - Workflows documentation (docs/workflows.md)
  - Packaging documentation (docs/packaging.md)

### Fixed
- `Lock` → `RLock` in ContextWindow to prevent deadlock in `get_stats()`
- `BrowserSkill.execute()` now handles `None` match gracefully
- `SystemSkill.patterns()` now includes `status` as a match pattern
- System tests now pass without PyYAML dependency (Phase module imports fixed)

### Changed
- `assistant.py` now integrates DesktopState for automatic active context
- `assistant.py` integrates MetricsCollector for automatic latency tracking
- `audio_pipeline.py` completely rewritten with interruption, cooldown, follow-up
- `sidebar.py` updated to 12 navigation items
- `main_window.py` updated to 12 tabs with enhanced Settings
- `memory_tab.py` enhanced with semantic search, pin/unpin, forget
- `app.py` updated with onboarding flow and first-run detection
- `config/settings.yaml` expanded with memory, context, voice, workflows, metrics sections
- `jarvis/ui/assets/tray_icon.png` added (64px app icon)

# Architecture

## Overview

Jarvis Linux Assistant follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│                   UI Layer (PyQt6)                   │
│  MainWindow · Sidebar · Tabs · Palette · Notifs     │
├─────────────────────────────────────────────────────┤
│              Application Layer (app.py)              │
│  CLI/GUI Launcher · Onboarding · Config Loading      │
├─────────────────────────────────────────────────────┤
│                   Core Engine                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │
│  │Assistant │ │  Events  │ │  Memory System   │    │
│  │  Router  │ │   Bus    │ │  short/long/     │    │
│  │  Skills  │ │          │ │  semantic/prefs  │    │
│  │  Agents  │ │          │ │  projects        │    │
│  └──────────┘ └──────────┘ └──────────────────┘    │
├─────────────────────────────────────────────────────┤
│           Context & AI Layer                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │
│  │  Context  │ │  Context │ │   Ollama Client  │    │
│  │  Builder  │ │  Window  │ │   + streaming    │    │
│  └──────────┘ └──────────┘ └──────────────────┘    │
├─────────────────────────────────────────────────────┤
│           Voice Layer (Optional)                    │
│  VAD · Wake Word · STT · TTS · Audio Pipeline      │
├─────────────────────────────────────────────────────┤
│           System Integration Layer                   │
│  Desktop State · Workflows · Apps · Media · Terminal│
├─────────────────────────────────────────────────────┤
│           Observability Layer                       │
│  Metrics · Event Tracing · Health Check · Logging   │
└─────────────────────────────────────────────────────┘
```

## Core Components

### `jarvis/core/assistant.py`
Central orchestrator. Receives commands, routes to skills or agents, falls back to AI. Integrates ContextBuilder, SemanticMemory, DesktopState, and MetricsCollector.

### `jarvis/core/semantic_memory.py`
TF-IDF based vector search. Stores entries with text, tags, importance score. Supports pinning, decay, tag-based retrieval, and cosine similarity search.

### `jarvis/core/context_window.py`
Manages AI context with priority-based sections. Prunes low-priority content when budget exceeded. Token estimation (char/4 ratio).

### `jarvis/ai/context_builder.py`
Builds rich context for AI prompts: project info, session state, recent activity, semantic memories, user preferences, active desktop context.

### `jarvis/core/events.py`
Typed event system with 17 event types. Used for inter-component communication (UI ←→ core).

### `jarvis/core/metrics.py`
Singleton metrics collector tracking latencies, counters, and events. Integrated into assistant processing pipeline.

## Data Flow

### Command Processing
1. User enters command (text or voice)
2. Assistant receives command, builds context
3. Skill Router tries to match against registered skills
4. If matched: skill executes → response returned
5. If not matched: Agent Router tries specialized agents
6. If no agent matches: Ollama AI generates response
7. Response stored in memory, emitted as event, returned to UI

### Memory Storage
1. After each command, assistant calls `_store_semantic()`
2. Semantic memory indexes text with TF-IDF
3. Long-term memory stores command + response pairs
4. Short-term memory tracks recent context

### Desktop State Polling
1. `DesktopState` background thread polls every 1s
2. Caches results to avoid subprocess spam
3. Automatically injected into context via `ContextBuilder`

## Key Design Decisions

- **No cloud APIs**: All processing is local
- **Singleton pattern**: Core services (memory, metrics, events) use singletons
- **Graceful degradation**: Missing optional dependencies disable features without crashing
- **Priority-based pruning**: Context window prunes lowest priority first
- **Reentrant lock**: `RLock` used in ContextWindow to prevent deadlocks
- **Flat config keys**: New settings use flat keys in YAML for simplicity

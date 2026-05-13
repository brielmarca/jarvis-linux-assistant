# Jarvis Linux Assistant — Contexto do Projeto

## Visão Geral

Assistente desktop AI para Linux, offline-first, com consciência contextual, controle de voz, memória semântica, automação de workflows e diagnóstico integrado.

**Stack:** Python 3.10+, PyQt6, Ollama (Qwen2.5:7b), TF-IDF (memória semântica pura), faster-whisper, OpenWakeWord, Piper TTS

---

## Estado Atual (v1.0)

### O que funciona
- **86 testes passando** (0 falhas, 0 erros)
- Engine completa: assistente, roteamento de comandos, skills, agents
- **Memória semântica** com TF-IDF, busca por cosseno, pinagem, decay por importância, busca por tags
- **Context builder** — enriquece prompts da AI com contexto de projeto, sessão, atividade recente, memórias semânticas, preferências, estado do desktop
- **Context window** — gerenciamento de contexto com poda por prioridade e orçamento de tokens
- **Desktop state** — rastreamento em tempo real de janela ativa, app, workspace, bateria, rede, mídia, monitores, CPU
- **Workflows** — automação multi-passo com 3 templates embutidos (modo programador, streaming, rotina matinal)
- **Métricas** — latência, contadores, rastreamento de eventos
- **Voz** — VAD com adaptação de ruído, cooldown de wake word (2s), modo follow-up (8s), interrupção, escuta ambiente
- **UI** — 12 abas, tema escuro glassmorphism, sidebar, paleta de comandos, notificações, bandeja do sistema
- **Settings** — 17 configurações expostas, backup antes de salvar, reset para padrão, indicadores de restart
- **Packaging** — .desktop, ícones SVG/PNG, scripts de instalação/desinstalação, builder AppImage
- **Onboarding** — wizard de primeira execução (6 páginas)
- **Docs** — README, CHANGELOG, CONTRIBUTING, docs/architecture, docs/voice, docs/workflows, docs/packaging

### Bugs conhecidos
- Nenhum conhecido atualmente

### Limitações
- Funcionalidades de voz requerem dependências extras (openwakeword, faster-whisper, pyaudio)
- Desktop state polling requer xdotool, wmctrl, playerctl, nmcli/iwgetid
- GUI requer display server (X11 ou Wayland com XWayland)
- Ollama necessário para funcionalidades de AI
- Teste `test_new_features.py` completo pode travar em headless (xdotool/wmctrl aguardam display)

---

## Arquitetura

```
UI Layer (PyQt6) → Application Layer → Core Engine
                    ↓
              Context & AI Layer
                    ↓
         Voice Layer (opcional)
         System Integration Layer
         Observability Layer
```

### Fluxo de Comando
1. Usuário envia comando (texto ou voz)
2. Assistant constrói contexto (ContextBuilder + DesktopState + SemanticMemory)
3. Skill Router tenta matched skills registradas
4. Se matched: skill executa → resposta retornada
5. Se não: Agent Router tenta agents especializados
6. Se nenhum agent: Ollama AI gera resposta
7. Resposta armazenada em memória + evento emitido + UI atualizada

### Padrões de Código
- **Singleton**: MemoryManager, EventBus, SemanticMemory, MetricsCollector, DesktopState
- **Lock reentrante**: RLock no ContextWindow (previne deadlocks)
- **Degradação graciosa**: Dependências opcionais faltosas desabilitam features sem crash
- **Chaves planas no YAML**: Config novas usam chaves flat (ex: `voice_vad_threshold`)
- **Sem cloud**: Todo processamento é local

---

## Estrutura de Diretórios

```
jarvis-linux-assistant/
├── main.py                          # Entry point
├── config/settings.yaml             # Configuração YAML
├── packaging/                       # Desktop app
│   ├── jarvis.desktop
│   └── icons/ (svg, 64.png, 256.png)
├── scripts/
│   ├── install_desktop.sh
│   ├── uninstall_desktop.sh
│   └── build_appimage.sh
├── jarvis/
│   ├── app.py                       # Launcher CLI/GUI + onboarding
│   ├── core/
│   │   ├── assistant.py             # Orquestrador central
│   │   ├── semantic_memory.py       # Memória semântica TF-IDF
│   │   ├── context_window.py        # Gerenciamento de contexto
│   │   ├── context_builder.py       # Construção de contexto AI
│   │   ├── metrics.py               # Métricas e latência
│   │   ├── events.py                # Sistema de eventos (17 tipos)
│   │   ├── router.py                # Roteamento de comandos
│   │   ├── memory_manager.py        # Memória curta/longa duração
│   │   └── ... (permissions, logger, health, config_validator)
│   ├── agents/                      # Sistema multi-agente
│   ├── ai/
│   │   └── ollama_client.py         # Cliente Ollama com streaming
│   ├── voice/                       # Processamento de voz
│   │   ├── vad.py                   # Detecção de atividade de voz
│   │   ├── audio_pipeline.py        # Streaming, interrupção, cooldown
│   │   └── ... (wakeword, stt, tts, recorder)
│   ├── automation/
│   │   ├── workflows.py             # Engine de workflows + templates
│   │   └── ... (linux, apps, media, terminal)
│   ├── system/
│   │   └── desktop_state.py         # Consciência do desktop
│   ├── skills/                      # 7 skills built-in
│   └── ui/
│       ├── main_window.py           # Janela principal (12 abas)
│       ├── theme.py                 # Tema escuro glassmorphism
│       └── components/ (22 widgets)
├── docs/                            # Documentação
│   ├── architecture.md
│   ├── voice.md
│   ├── workflows.md
│   └── packaging.md
├── CHANGELOG.md
├── CONTRIBUTING.md
└── tests/                           # 86 testes
```

---

## Módulos Detalhados

### `jarvis/core/assistant.py` (337 linhas)
- `process(command, extra_context)` — método principal
- Integra: ContextBuilder, SemanticMemory (auto-store), DesktopState, MetricsCollector
- Fluxo: skill → agent → AI fallback
- Emite eventos: COMMAND_RECEIVED, SKILL_EXECUTED, AI_THINKING_COMPLETED, etc.

### `jarvis/core/semantic_memory.py` (322 linhas)
- TF-IDF puro (sem dependências externas)
- `store(text, source, tags)` → `search(query, top_k)` → `pin/unpin/delete`
- Decaimento por importância, busca por tags, estatísticas

### `jarvis/core/context_window.py` (193 linhas)
- `ContextWindow` — seções com prioridade, poda automática
- `TokenBudget` — orçamento por seção
- `ContextManager` — integração com context_data dict
- Usa `RLock` (reentrante) para prevenir deadlocks

### `jarvis/ai/context_builder.py` (140 linhas)
- `ContextBuilder` — constrói contexto de: projeto, sessão, atividade recente, memórias semânticas, preferências, desktop ativo
- Integrado no `assistant.process()` via `_build_context_data()`

### `jarvis/voice/audio_pipeline.py` (385 linhas)
- Pipeline completo: wake word → VAD → STT → resposta → TTS
- `WAKE_WORD_COOLDOWN = 2.0s` — cooldown após ativação
- `FOLLOW_UP_TIMEOUT = 8.0s` — janela para follow-ups sem wake word
- `_interrupt_flag` — interrupção de TTS
- Modo escuta ambiente (`PipelineState.AMBIENT`)

### `jarvis/system/desktop_state.py` (256 linhas)
- `DesktopState` singleton com polling de background
- `_cache_ttl = 1.0s` — evita spam de subprocessos
- `get_state()` → dict com active_app, active_window, workspace, battery, network, media, monitors, cpu_top
- `describe_state()` → string legível para contexto AI
- Métodos de controle: `media_play/pause/next/prev`, `set_volume`

### `jarvis/automation/workflows.py` (285 linhas)
- `Workflow`, `WorkflowStep`, `WorkflowExecutor`, `WorkflowManager`
- Persistência JSON em `~/.jarvis/workflows/`
- 3 templates built-in: programming_mode, streaming_mode, morning_routine
- Ações: command, wait, open

### `jarvis/core/metrics.py` (120 linhas)
- `MetricsCollector` singleton
- `record_latency(name, seconds)`, `increment(name)`, `trace_event(name, data)`
- `snapshot()` → latências + contadores + eventos
- Decorator `trace_latency`

---

## Configuração (`config/settings.yaml`)

Chaves planas (acessadas via `config.get("key")`):
- `assistant_name`, `language`, `ollama_model`, `ollama_host`, `ollama_context_length`
- `enable_voice`, `enable_wake_word`, `enable_tts`
- `whisper_model`, `whisper_device`
- `require_confirmation_for_dangerous_commands`
- `voice_vad_threshold` (0.1-0.9), `voice_wake_word_cooldown` (1.0-5.0), `voice_follow_up_timeout` (4.0-20.0)
- `memory_max_short_term` (50-500), `memory_semantic_search` (bool), `memory_semantic_enabled` (bool)
- `context_max_tokens` (2048-8192), `context_include_desktop_state` (bool), `context_include_recent_activity` (bool)
- `workflows_enabled` (bool), `metrics_enabled` (bool)

Seções aninhadas (acessadas via `config.get("memory", {})`):
- `memory.semantic_enabled`, `memory.max_semantic_entries`, `memory.decay_rate`, `memory.importance_decay_days`
- `context.max_tokens`, `context.reserve_tokens`, `context.enabled_sections`

---

## Dados do Usuário

| Caminho | Propósito |
|---------|-----------|
| `~/.jarvis/` | Diretório de configuração |
| `~/.jarvis/.onboarding_done` | Marcador de primeira execução |
| `~/.jarvis/workflows/*.json` | Workflows persistidos |
| `config/settings.yaml` | Configuração principal |
| `config/settings.yaml.bak` | Backup automático antes de salvar |

---

## UI — 12 Abas

| # | Aba | Componente | Atalho |
|---|-----|------------|--------|
| 0 | Dashboard | DashboardTab | Ctrl+1 |
| 1 | Skills | SkillsTab | Ctrl+2 |
| 2 | Settings | SettingsTab | Ctrl+3 |
| 3 | Logs | LogsTab | Ctrl+4 |
| 4 | Monitor | MonitorTab | Ctrl+5 |
| 5 | Dev Mode | DevModeTab | Ctrl+6 |
| 6 | Voice | VoiceTab | Ctrl+7 |
| 7 | Memory | MemoryTab | Ctrl+8 |
| 8 | Desktop | DesktopTab | Ctrl+9 |
| 9 | Workflows | WorkflowsTab | Ctrl+0 |
| 10 | Diagnostics | DiagnosticsTab | — |
| 11 | Health | HealthTab | — |

22 componentes UI, 13362 linhas Python no total.

---

## Próximos Passos (Roadmap)

### Fase N — Dev Assistant Avançado
- Análise de repositório ao vivo
- Git diff summaries
- Indexação de projetos
- Sugestões com consciência de terminal

### Fase O — Sistema UI Premium
- Gerenciador de animações
- Gerenciador de layout
- Sistema de componentes unificado
- Animações GPU-friendly

### Fase Q — CI/CD + Auto-updater
- Pipeline de testes automatizados
- Sistema de atualização automática
- Lançamento de releases

---

## Comandos Úteis

```bash
# Testes
python3 -m pytest tests/ -v                         # Todos os testes
python3 -m pytest tests/test_new_features.py -v     # Testes das novas features

# Compilar
python3 -m compileall .                             # Verificar sintaxe

# Executar
python3 main.py                                     # Modo GUI
python3 main.py --cli                                # Modo CLI
python3 main.py "open firefox"                      # Comando único

# Verificar Ollama
curl http://localhost:11434/api/tags                 # Listar modelos

# Instalar desktop
bash scripts/install_desktop.sh

# Contar linhas
find . -name '*.py' -not -path './.venv/*' | xargs wc -l | tail -1
```

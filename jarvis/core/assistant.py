import time
from pathlib import Path

import yaml

from jarvis.core.router import CommandRouter
from jarvis.core.permissions import PermissionManager
from jarvis.core.logger import JarvisLogger
from jarvis.core.memory import Memory
from jarvis.core.memory_manager import MemoryManager
from jarvis.core.semantic_memory import semantic_memory
from jarvis.core.events import EventBus, EventType
from jarvis.core.metrics import metrics
from jarvis.skills.registry import SkillRegistry, SkillMetadata
from jarvis.ai.ollama_client import OllamaClient
from jarvis.ai.context_builder import ContextBuilder


log = JarvisLogger()
_ic = None

def _get_intent_classifier():
    global _ic
    if _ic is None:
        from jarvis.agents.intent_classifier import IntentClassifier
        _ic = IntentClassifier()
    return _ic

router = CommandRouter()
perms = PermissionManager()
memory = Memory()
memory_manager = MemoryManager()
skill_registry = SkillRegistry()
events = EventBus()
agent_router = None


class Assistant:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.config = self._load_config()
        self.name = self.config.get("assistant_name", "Jarvis")
        self.language = self.config.get("language", "pt-PT")
        self.ollama = OllamaClient()
        self._state = "idle"
        self._session_start = time.time()
        self._context_builder = ContextBuilder(memory_manager)
        self._load_skills()
        self._load_agents()
        memory_manager.set_context("session_start", self._session_start)
        memory_manager.set_context("language", self.language)

    def _load_config(self):
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        if config_path.exists():
            return yaml.safe_load(config_path.read_text()) or {}
        return {}

    def _load_skills(self):
        from jarvis.skills.system import SystemSkill
        from jarvis.skills.apps import AppsSkill
        from jarvis.skills.browser import BrowserSkill
        from jarvis.skills.media import MediaSkill
        from jarvis.skills.dev import DevSkill
        from jarvis.skills.opencode import OpenCodeSkill

        enabled = self.config.get("enabled_skills", [])

        skill_map = {
            "system": SystemSkill,
            "apps": AppsSkill,
            "browser": BrowserSkill,
            "media": MediaSkill,
            "dev": DevSkill,
            "opencode": OpenCodeSkill,
        }

        for name, cls in skill_map.items():
            if name in enabled:
                try:
                    skill = cls()
                    meta = skill.skill_metadata
                    skill_meta = SkillMetadata(
                        name=name,
                        description=meta.get("description", ""),
                        category=meta.get("category", "general"),
                        cooldown=meta.get("cooldown", 0.0),
                        timeout=meta.get("timeout", 30.0),
                        async_execution=meta.get("async_execution", False),
                        requires_confirmation=meta.get("requires_confirmation", False),
                        version=meta.get("version", "1.0.0"),
                    )
                    skill_registry.register(skill, skill_meta)
                    router.register(skill)
                    skill.on_load()
                    events.emit(EventType.SKILL_LOADED, {"name": name})
                except Exception as e:
                    log.error(f"Failed to load skill '{name}': {e}")

    def _load_agents(self):
        global agent_router
        from jarvis.agents.agent_router import AgentRouter
        from jarvis.agents.system_agent import SystemAgent
        from jarvis.agents.coding_agent import CodingAgent
        from jarvis.agents.browser_agent import BrowserAgent
        from jarvis.agents.media_agent import MediaAgent
        from jarvis.agents.automation_agent import AutomationAgent
        from jarvis.agents.memory_agent import MemoryAgent

        agent_router = AgentRouter()
        for agent_cls in [SystemAgent, CodingAgent, BrowserAgent, MediaAgent, AutomationAgent, MemoryAgent]:
            try:
                agent = agent_cls()
                agent_router.register_agent(agent)
                log.info(f"Agent loaded: {agent.name}")
            except Exception as e:
                log.error(f"Failed to load agent {agent_cls.__name__}: {e}")

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        events.emit(EventType.ASSISTANT_STATE_CHANGED, {"state": value})

    def _store_semantic(self, text: str, source: str = "system", tags: list[str] | None = None):
        semantic_memory.store(text, source=source, tags=tags)
        events.emit(EventType.MEMORY_STORED, {"text": text[:100], "source": source})

    def process(self, command: str, extra_context: dict | None = None, _skip_intent_gate: bool = False, _force_ai: bool = False) -> dict:
        start = time.time()
        metrics.increment("commands_total")
        events.emit(EventType.COMMAND_RECEIVED, {"command": command})
        self.state = "processing"
        log.info(f"Processing command: {command}")

        if extra_context is None:
            try:
                from jarvis.system.desktop_state import DesktopState
                ds = DesktopState()
                desk = ds.get_state()
                extra_context = {
                    "active_app": desk.get("active_app", ""),
                    "active_window": desk.get("active_window", ""),
                    "workspace": desk.get("workspace", ""),
                    "cwd": str(Path.cwd()),
                }
            except Exception:
                extra_context = {}

        memory_manager.add_short_term({
            "command": command,
            "type": "command",
        })

        safety = perms.check_command_safety(command)
        if not safety["safe"] and safety["requires_confirmation"]:
            result = {
                "success": False,
                "response": f"I detected a potentially dangerous command. Please confirm you want to run: {command}",
                "requires_confirmation": True,
                "command": command,
                "skill": None,
                "execution_time": time.time() - start,
            }
            memory.add_command(command, result["response"], "blocked", result["execution_time"])
            self._store_semantic(
                f"Blocked dangerous command: {command}",
                source="system",
                tags=["dangerous", "blocked"],
            )
            events.emit(EventType.COMMAND_FAILED, result)
            self.state = "idle"
            return result

        if command.lower().strip() in ("reload skills", "recarregar skills", "recarregar"):
            reloaded = skill_registry.reload_skills(router)
            self.state = "idle"
            result = {
                "success": True,
                "response": f"Reloaded {len(reloaded)} skills: {', '.join(reloaded)}",
                "requires_confirmation": False,
                "command": command,
                "skill": "system",
                "execution_time": time.time() - start,
            }
            return result

        if _force_ai:
            skill = None
        else:
            skill, match = router.route(command)

        if skill and not _skip_intent_gate:
            decision = _get_intent_classifier().get_routing_decision(command)
            intent_name = decision.get("intent")
            intent_conf = decision.get("confidence")
            log.debug(f"Intent: {intent_name} ({intent_conf}), action: {decision['action']}, matched skill: {skill.name}")

            if decision["action"] == "ai":
                log.info(f"Gate: {decision['reason']}. Routing '{command}' to AI instead of skill '{skill.name}'")
                skill = None

            elif decision["action"] == "confirm":
                log.info(f"Gate: {decision['reason']}. Requesting confirmation for '{command}' on skill '{skill.name}'")
                elapsed = time.time() - start
                result = {
                    "success": False,
                    "response": "Did you want me to execute a system command?",
                    "reason": f"I'm not sure if you want to run a command (intent: {intent_name}, confidence: {intent_conf:.1f}).",
                    "requires_confirmation": True,
                    "_gate_confirmation": True,
                    "command": command,
                    "skill": skill.name,
                    "execution_time": elapsed,
                }
                memory.add_command(command, "confirmation_requested", "pending", elapsed, skill.name)
                events.emit(EventType.COMMAND_FAILED, result)
                self.state = "idle"
                return result

        if skill:
            can_exec, reason = skill_registry.can_execute(skill.name)
            if not can_exec:
                self.state = "idle"
                return {
                    "success": False,
                    "response": f"Cannot execute {skill.name}: {reason}",
                    "requires_confirmation": False,
                    "command": command,
                    "skill": skill.name,
                    "execution_time": time.time() - start,
                }
            try:
                events.emit(EventType.SKILL_EXECUTED, {"skill": skill.name, "command": command})
                skill.mark_executed()
                skill_registry.mark_executed(skill.name)
                response = skill.execute(command, match)
                elapsed = time.time() - start
                result = {
                    "success": True,
                    "response": response,
                    "requires_confirmation": False,
                    "command": command,
                    "skill": skill.name,
                    "execution_time": elapsed,
                }
                memory.add_command(command, response, "ok", elapsed, skill.name)
                metrics.record_latency(f"skill_{skill.name}", elapsed)
                metrics.increment(f"skill_{skill.name}_count")

                mem_tags = [skill.name, "skill", "ok"]
                if skill.name == "opencode":
                    mem_tags.append("code")
                self._store_semantic(
                    f"Executed {skill.name} command: {command} -> {response[:200]}",
                    source="skill",
                    tags=mem_tags,
                )

                events.emit(EventType.COMMAND_COMPLETED, result)
                self.state = "idle"
                return result
            except Exception as e:
                log.error(f"Skill execution error: {e}")
                elapsed = time.time() - start
                result = {
                    "success": False,
                    "response": f"Error executing command: {e}",
                    "requires_confirmation": False,
                    "command": command,
                    "skill": skill.name,
                    "execution_time": elapsed,
                }
                memory.add_command(command, str(e), "error", elapsed, skill.name)
                self._store_semantic(
                    f"Skill error in {skill.name}: {command} -> {e}",
                    source="system",
                    tags=[skill.name, "error"],
                )
                events.emit(EventType.COMMAND_FAILED, result)
                self.state = "idle"
                return result

        events.emit(EventType.AI_THINKING_STARTED, {"command": command})
        self.state = "ai_thinking"
        try:
            context_data = self._build_context_data(command, extra_context)
            self.ollama.set_context_data(context_data)

            system_prompt = self._context_builder.build_system_prompt(self.config)
            enhanced_prompt = self._context_builder.build_prompt(command, extra_context)
            events.emit(EventType.CONTEXT_BUILT, {"tokens": self.ollama.get_context_stats().get("current_tokens", 0)})

            ai_response = self.ollama.ask(enhanced_prompt, system_prompt=system_prompt)
            elapsed = time.time() - start
            result = {
                "success": True,
                "response": ai_response,
                "requires_confirmation": False,
                "command": command,
                "skill": "ai",
                "execution_time": elapsed,
            }
            memory.add_command(command, ai_response, "ok", elapsed, "ai")
            self._store_semantic(
                f"AI response to '{command}': {ai_response[:200]}",
                source="ai",
                tags=["ai", "conversation"],
            )
            metrics.record_latency("ai_response", elapsed)
            events.emit(EventType.AI_THINKING_COMPLETED, result)
            events.emit(EventType.COMMAND_COMPLETED, result)
            self.state = "idle"
            return result
        except Exception as e:
            log.error(f"AI error: {e}")
            elapsed = time.time() - start
            result = {
                "success": False,
                "response": f"Sorry, I couldn't process that. Error: {e}",
                "requires_confirmation": False,
                "command": command,
                "skill": "ai",
                "execution_time": elapsed,
            }
            memory.add_command(command, str(e), "error", elapsed, "ai")
            self._store_semantic(
                f"AI error for '{command}': {e}",
                source="system",
                tags=["ai", "error"],
            )
            events.emit(EventType.COMMAND_FAILED, result)
            self.state = "idle"
            return result

    def _build_context_data(self, command: str, extra: dict | None = None) -> dict:
        project_context = self._context_builder._build_project_context()
        session_context = self._context_builder._build_session_context()
        recent_activity = self._context_builder._build_recent_activity()
        semantic_context = self._context_builder._build_semantic_context(command)
        preferences = self._context_builder._build_user_preferences()
        active_context = self._context_builder._build_active_context(extra)

        return {
            "command": command,
            "project_context": project_context,
            "session_context": session_context,
            "recent_activity": recent_activity,
            "semantic_context": semantic_context,
            "preferences": preferences,
            "active_context": active_context,
        }

    def get_context_summary(self) -> str:
        return self._context_builder.summarize_context()

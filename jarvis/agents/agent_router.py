import time
from typing import Any

from jarvis.core.logger import JarvisLogger
from jarvis.core.events import EventBus, EventType
from jarvis.core.router import CommandRouter
from jarvis.core.assistant import memory_manager, perms
from jarvis.agents.intent_classifier import IntentClassifier


log = JarvisLogger()
events = EventBus()


class AgentRouter:
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
        self._agents: dict[str, Any] = {}
        self._classifier = IntentClassifier()
        self._fallback_chain = ["system", "automation", "coding", "browser", "media", "memory"]
        self._context: dict[str, Any] = {"last_intent": None, "last_skill": None}

    def register_agent(self, agent):
        self._agents[agent.name] = agent
        log.info(f"Agent registered: {agent.name}")

    def get_agent(self, name: str):
        return self._agents.get(name)

    def get_all_agents(self) -> dict:
        return dict(self._agents)

    def unregister_agent(self, name: str):
        self._agents.pop(name, None)

    def route(self, command: str, router: CommandRouter, ollama) -> dict:
        start = time.time()

        skill, match = router.route(command)
        if skill:
            self._context["last_skill"] = skill.name
            return {"agent": "direct_skill", "skill": skill, "match": match}

        intents = self._classifier.classify(command, self._context)
        log.info(f"Intents for '{command}': {intents}")

        for intent_name, confidence in intents:
            if confidence < 0.3:
                continue

            agent = self._agents.get(intent_name)
            if agent and agent.enabled:
                can_handle, agent_conf = agent.can_handle(command, self._context)
                if can_handle and agent_conf >= 0.3:
                    self._context["last_intent"] = intent_name
                    events.emit(EventType.SKILL_EXECUTED, {"agent": intent_name, "command": command, "confidence": confidence})
                    try:
                        result = agent.execute(command, self._context)
                        return result
                    except Exception as e:
                        log.error(f"Agent {intent_name} failed: {e}")

        for fallback_name in self._fallback_chain:
            agent = self._agents.get(fallback_name)
            if agent and agent.enabled:
                can_handle, agent_conf = agent.can_handle(command, self._context)
                if can_handle:
                    self._context["last_intent"] = fallback_name
                    try:
                        result = agent.execute(command, self._context)
                        return result
                    except Exception:
                        continue

        return {"agent": "ai_fallback", "skill": None, "match": None}

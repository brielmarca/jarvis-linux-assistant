import re
from typing import Any

from jarvis.agents.base_agent import BaseAgent
from jarvis.core.assistant import memory_manager
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="memory", description="Memory and recall commands")

    def can_handle(self, command: str, context: dict | None = None) -> tuple[bool, float]:
        cmd = command.lower()
        if any(kw in cmd for kw in ["remember", "lembrar", "remember that", "guarda", "memorize",
                                     "recall", "lembra", "what do you know", "o que sabe",
                                     "forget", "esquece", "delete memory",
                                     "main project", "projeto principal", "my project"]):
            return True, 0.9
        if "reload skills" in cmd or "recarregar" in cmd:
            return True, 0.9
        return False, 0.0

    def _handle_remember(self, cmd: str) -> str:
        patterns = [
            r"remember that\s+(.+?)(?:\s+as\s+important)?$",
            r"remember\s+(.+?)(?:\s+as\s+important)?$",
            r"lembrar\s+(?:que\s+)?(.+?)(?:\s+como\s+importante)?$",
            r"guarda\s+(?:isso\s+)?(.+)$",
            r"memorize\s+(.+)$",
        ]
        for p in patterns:
            m = re.search(p, cmd, re.IGNORECASE)
            if m:
                text = m.group(1).strip()
                tags = ["user_saved"]
                is_important = "important" in cmd.lower() or "importante" in cmd.lower()
                importance = 0.8 if is_important else 0.5
                memory_manager.remember(text, tags=tags, source="user", importance=importance)
                return f"I'll remember that: '{text}'"
        return "What should I remember?"

    def _handle_recall(self, cmd: str) -> str:
        patterns = [
            r"recall\s+(.+)$",
            r"what do you know about\s+(.+)$",
            r"lembra\s+(?:de\s+)?(.+)$",
            r"o que sabe sobre\s+(.+)$",
            r"(?:search|find)\s+(?:memory|memories?)\s+(.+)$",
            r"remember\s+(?:about\s+)?(.+)$",
        ]
        for p in patterns:
            m = re.search(p, cmd, re.IGNORECASE)
            if m:
                query = m.group(1).strip()
                results = memory_manager.recall(query, n=3)
                if results:
                    lines = [f"- {r['text']}" for r in results]
                    return "I recall:\n" + "\n".join(lines)
                return f"I don't have any memories about '{query}'"

        results = memory_manager.recall(cmd, n=5)
        if results:
            lines = [f"- {r['text']}" for r in results]
            return "Here's what I remember:\n" + "\n".join(lines)
        return "I don't have any relevant memories."

    def _handle_forget(self, cmd: str) -> str:
        memory_manager.reset_all()
        return "All memories have been cleared."

    def _handle_main_project(self, cmd: str) -> str:
        project = memory_manager.get_preference("main_project")
        if project:
            return f"Your main project is: {project}"
        return "You haven't set a main project yet. Tell me: 'remember my main project is X'"

    def execute(self, command: str, context: dict | None = None) -> dict[str, Any]:
        cmd = command.lower().strip()

        if "remember" in cmd or "lembrar" in cmd or "guarda" in cmd or "memorize" in cmd:
            return {"response": self._handle_remember(cmd), "agent": "memory"}

        if "recall" in cmd or "lembra" in cmd or "what do you know" in cmd or "o que sabe" in cmd:
            return {"response": self._handle_recall(cmd), "agent": "memory"}

        if "forget" in cmd or "esquece" in cmd or "delete memory" in cmd:
            return {"response": self._handle_forget(cmd), "agent": "memory"}

        if "main project" in cmd or "projeto principal" in cmd or "my project" in cmd:
            return {"response": self._handle_main_project(cmd), "agent": "memory"}

        if "remember" in cmd and "my main project" in cmd:
            match = re.search(r"(?:remember|lembrar)\s+(?:that\s+)?my main project is\s+(.+)", cmd, re.IGNORECASE)
            if match:
                project_name = match.group(1).strip()
                memory_manager.set_preference("main_project", project_name)
                memory_manager.remember(f"Main project is {project_name}", tags=["project", "preference"], importance=0.9)
                return {"response": f"I'll remember that your main project is {project_name}", "agent": "memory"}

        return {"response": "Memory command not recognized", "agent": "memory"}

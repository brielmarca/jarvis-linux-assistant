import time
from pathlib import Path
from typing import Any

from jarvis.core.semantic_memory import semantic_memory
from jarvis.core.memory_manager import MemoryManager
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class ContextBuilder:
    def __init__(self, memory_manager: MemoryManager):
        self._memory = memory_manager

    def build_prompt(self, command: str, extra_context: dict | None = None) -> str:
        parts = []
        parts.append(self._build_project_context())
        parts.append(self._build_session_context())
        parts.append(self._build_recent_activity())
        parts.append(self._build_semantic_context(command))
        parts.append(self._build_user_preferences())
        parts.append(self._build_active_context(extra_context))

        context_str = "\n\n".join(p for p in parts if p)
        if context_str:
            return f"[Context]\n{context_str}\n\n[Command]\n{command}"
        return command

    def _build_project_context(self) -> str:
        projects = self._memory.get_all_projects()
        if not projects:
            return ""

        lines = ["Current projects:"]
        for name, proj in list(projects.items())[:5]:
            path = proj.get("path", "?")
            last = proj.get("last_opened", "?")[:10]
            lines.append(f"  - {name}: {path} (last: {last})")

        last_project = self._memory.get_context("last_project")
        if last_project:
            lines.append(f"Active project: {last_project}")

        return "\n".join(lines)

    def _build_session_context(self) -> str:
        session_start = self._memory.get_context("session_start")
        language = self._memory.get_context("language", "en")
        if not session_start:
            return ""

        elapsed = time.time() - session_start
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)

        parts = [f"Session: {hours}h {minutes}m, Language: {language}"]

        last_intent = self._memory.get_context("last_intent")
        if last_intent:
            parts.append(f"Last intent: {last_intent}")

        mode = self._memory.get_context("current_mode")
        if mode:
            parts.append(f"Mode: {mode}")

        return " | ".join(parts)

    def _build_recent_activity(self) -> str:
        recent = self._memory.get_short_term(8)
        if not recent:
            return ""

        lines = ["Recent activity:"]
        for entry in recent:
            cmd = entry.get("command") or entry.get("text", "")
            resp = entry.get("response", "")
            skill = entry.get("skill")
            status = entry.get("status", "ok")
            if cmd:
                prefix = f"  [{status}]" if status != "ok" else "  "
                skill_tag = f" ({skill})" if skill else ""
                lines.append(f"{prefix}User: {cmd}{skill_tag}")
                if resp and len(resp) < 120:
                    lines.append(f"  Jarvis: {resp}")
        return "\n".join(lines)

    def _build_semantic_context(self, query: str) -> str:
        related = semantic_memory.search(query, n=5, min_score=0.08)
        if not related:
            return ""

        lines = ["Related memories:"]
        for item in related:
            text = item.get("text", "")[:200]
            tags = item.get("tags", [])
            score = item.get("_score", 0)
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            lines.append(f"  ({score:.2f}){tag_str} {text}")
        return "\n".join(lines)

    def _build_user_preferences(self) -> str:
        prefs = self._memory.get_all_preferences()
        if not prefs:
            return ""

        lines = ["User preferences:"]
        shown = 0
        for key, value in prefs.items():
            if shown >= 8:
                break
            lines.append(f"  {key}: {value}")
            shown += 1
        return "\n".join(lines)

    def _build_active_context(self, extra: dict | None = None) -> str:
        if not extra:
            return ""

        lines = ["Current state:"]
        APP_KEYS = {"active_app", "active_window", "workspace", "cwd", "battery", "network"}
        for key, value in extra.items():
            if key in APP_KEYS and value:
                lines.append(f"  {key}: {value}")
        if len(lines) == 1:
            return ""
        return "\n".join(lines)

    def build_system_prompt(self, config: dict) -> str:
        name = config.get("assistant_name", "Jarvis")
        language = config.get("language", "en")

        return (
            f"You are {name}, a context-aware Linux AI desktop assistant. "
            f"Respond in {language}. Be concise, helpful, and proactive. "
            f"Use the provided context to personalize responses. "
            f"If you remember past interactions, reference them naturally. "
            f"Keep answers brief (1-3 sentences unless asked for detail). "
            f"Ask clarifying questions when context is ambiguous. "
            f"NEVER mention that you are an AI or language model. "
            f"Stay in character as {name} at all times."
        )

    def summarize_context(self) -> str:
        projects = self._memory.get_all_projects()
        prefs = self._memory.get_all_preferences()
        recent = self._memory.get_short_term(5)
        stats = semantic_memory.get_stats()

        lines = [f"Context summary:"]
        if projects:
            lines.append(f"Projects tracked: {len(projects)} ({', '.join(list(projects)[:3])})")
        if prefs:
            lines.append(f"Preferences: {len(prefs)}")
        lines.append(f"Short-term entries: {len(recent)}")
        lines.append(f"Semantic memories: {stats.get('total_entries', 0)} (pinned: {stats.get('pinned', 0)})")
        return "\n".join(lines)

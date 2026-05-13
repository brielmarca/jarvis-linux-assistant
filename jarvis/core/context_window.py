import re
import time
from collections import OrderedDict
from threading import RLock
from typing import Any


TOKEN_ESTIMATE_RATIO = 4.0


def estimate_tokens(text: str) -> int:
    return int(len(text) / TOKEN_ESTIMATE_RATIO) + 1


class ContextWindow:
    def __init__(self, max_tokens: int = 4096, reserve_tokens: int = 1024):
        self._max_tokens = max_tokens
        self._reserve = reserve_tokens
        self._available = max_tokens - reserve_tokens
        self._sections: OrderedDict[str, dict] = OrderedDict()
        self._lock = RLock()

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    @max_tokens.setter
    def max_tokens(self, value: int):
        self._max_tokens = value
        self._available = value - self._reserve

    @property
    def reserve_tokens(self) -> int:
        return self._reserve

    @reserve_tokens.setter
    def reserve_tokens(self, value: int):
        self._reserve = value
        self._available = self._max_tokens - value

    def add_section(self, name: str, content: str, priority: int = 0, max_tokens: int = 0):
        if not content:
            return
        with self._lock:
            self._sections[name] = {
                "content": content,
                "priority": priority,
                "max_tokens": max_tokens,
                "tokens": estimate_tokens(content),
                "added": time.time(),
            }
            self._prune()

    def remove_section(self, name: str):
        with self._lock:
            self._sections.pop(name, None)

    def get_section(self, name: str) -> str | None:
        section = self._sections.get(name)
        if section:
            return section["content"]
        return None

    def get_content(self) -> str:
        with self._lock:
            sorted_sections = sorted(
                self._sections.values(),
                key=lambda s: (-s["priority"], s["added"])
            )
            parts = []
            for section in sorted_sections:
                content = section["content"]
                max_tok = section["max_tokens"]
                if max_tok > 0 and estimate_tokens(content) > max_tok:
                    content = self._truncate(content, max_tok)
                parts.append(content)
            return "\n\n".join(parts)

    def current_tokens(self) -> int:
        with self._lock:
            return sum(s["tokens"] for s in self._sections.values())

    def usage_ratio(self) -> float:
        with self._lock:
            total = sum(s["tokens"] for s in self._sections.values())
            return total / self._available if self._available > 0 else 1.0

    def _prune(self):
        total = sum(s["tokens"] for s in self._sections.values())
        if total <= self._available:
            return

        sorted_items = sorted(
            self._sections.items(),
            key=lambda x: (-x[1]["priority"], x[1]["added"])
        )

        for name, section in reversed(sorted_items):
            self._sections.pop(name, None)
            total -= section["tokens"]
            if total <= self._available:
                break

    def _truncate(self, text: str, max_tok: int) -> str:
        words = text.split()
        target_words = int(max_tok * TOKEN_ESTIMATE_RATIO)
        if len(words) <= target_words:
            return text
        return " ".join(words[:target_words]) + " [...]"

    def clear(self):
        with self._lock:
            self._sections.clear()

    def section_names(self) -> list[str]:
        with self._lock:
            return list(self._sections.keys())

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "sections": len(self._sections),
                "current_tokens": sum(s["tokens"] for s in self._sections.values()),
                "available": self._available,
                "usage_pct": round(self.usage_ratio() * 100, 1),
            }


class TokenBudget:
    def __init__(self):
        self._budgets: dict[str, int] = {}
        self._default_budget = 1024

    def set_budget(self, section: str, tokens: int):
        self._budgets[section] = max(256, min(tokens, 8192))

    def get_budget(self, section: str) -> int:
        return self._budgets.get(section, self._default_budget)

    def all_budgets(self) -> dict[str, int]:
        return dict(self._budgets)

    def reset(self):
        self._budgets = {}


class ContextManager:
    def __init__(self, max_tokens: int = 4096, reserve_tokens: int = 1024):
        self.window = ContextWindow(max_tokens, reserve_tokens)
        self.budget = TokenBudget()

    def set_context(self, command: str, context_data: dict, extra: dict | None = None):
        self.window.clear()

        project = context_data.get("project_context", "")
        session = context_data.get("session_context", "")
        activity = context_data.get("recent_activity", "")
        semantic = context_data.get("semantic_context", "")
        preferences = context_data.get("preferences", "")
        active = context_data.get("active_context", "")

        priorities = {
            "project": 30,
            "session": 20,
            "activity": 40,
            "semantic": 50,
            "preferences": 10,
            "active": 60,
        }

        for name, content, key_name in [
            ("project", project, "project"),
            ("session", session, "session"),
            ("activity", activity, "activity"),
            ("semantic", semantic, "semantic"),
            ("preferences", preferences, "preferences"),
            ("active", active, "active"),
        ]:
            if content:
                self.window.add_section(
                    name,
                    content,
                    priority=priorities[key_name],
                    max_tokens=self.budget.get_budget(key_name),
                )

        self.window.add_section("command", command, priority=100)

    def get_full_context(self) -> str:
        return self.window.get_content()

    def get_stats(self) -> dict:
        return self.window.get_stats()

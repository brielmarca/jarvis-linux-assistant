import asyncio
import re
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

from jarvis.core.logger import JarvisLogger


log = JarvisLogger()
_executor = ThreadPoolExecutor(max_workers=4)


class BaseSkill(ABC):
    def __init__(self):
        self.name = self.__class__.__name__.lower().replace("skill", "")
        self.enabled = True
        self._patterns = self._compile_patterns()
        self._metadata = self._get_default_metadata()
        self._last_executed = 0.0
        self._cooldown = self._metadata.get("cooldown", 0.0)
        self._timeout = self._metadata.get("timeout", 30.0)
        self._async_execution = self._metadata.get("async_execution", False)

    # ── Subclass API ───────────────────────────────────────────────

    @abstractmethod
    def patterns(self) -> list:
        return []

    @abstractmethod
    def execute(self, command: str, match: re.Match) -> str:
        pass

    # ── Optional overrides ─────────────────────────────────────────

    def metadata(self) -> dict:
        return {}

    async def execute_async(self, command: str, match: re.Match) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self.execute, command, match)

    def on_load(self):
        pass

    def on_unload(self):
        pass

    # ── Internal ───────────────────────────────────────────────────

    def _get_default_metadata(self) -> dict:
        defaults = {
            "description": "",
            "version": "1.0.0",
            "author": "",
            "category": "general",
            "permissions": [],
            "cooldown": 0.0,
            "timeout": 30.0,
            "async_execution": False,
            "requires_confirmation": False,
        }
        user_meta = self.metadata() or {}
        defaults.update(user_meta)
        return defaults

    def _compile_patterns(self):
        return [re.compile(p, re.IGNORECASE) for p in self.patterns()]

    def matches(self, text: str) -> Optional[re.Match]:
        for pattern in self._patterns:
            m = pattern.search(text)
            if m:
                return m
        return None

    @property
    def is_on_cooldown(self) -> bool:
        if self._cooldown <= 0:
            return False
        return (time.time() - self._last_executed) < self._cooldown

    @property
    def cooldown_remaining(self) -> float:
        if self._cooldown <= 0:
            return 0.0
        remaining = self._cooldown - (time.time() - self._last_executed)
        return max(0.0, remaining)

    def mark_executed(self):
        self._last_executed = time.time()

    @property
    def skill_metadata(self) -> dict:
        return dict(self._metadata)

    def __repr__(self):
        return f"<Skill {self.name} enabled={self.enabled} cooldown={self._cooldown}s>"

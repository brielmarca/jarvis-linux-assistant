import importlib
import inspect
import time
from pathlib import Path
from typing import Any

from jarvis.core.logger import JarvisLogger
from jarvis.core.events import EventBus, EventType
from jarvis.skills.base import BaseSkill


log = JarvisLogger()
events = EventBus()


class SkillMetadata:
    def __init__(
        self,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        author: str = "",
        category: str = "general",
        permissions: list[str] | None = None,
        cooldown: float = 0.0,
        timeout: float = 30.0,
        async_execution: bool = False,
        requires_confirmation: bool = False,
    ):
        self.name = name
        self.description = description
        self.version = version
        self.author = author
        self.category = category
        self.permissions = permissions or []
        self.cooldown = cooldown
        self.timeout = timeout
        self.async_execution = async_execution
        self.requires_confirmation = requires_confirmation

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "category": self.category,
            "permissions": self.permissions,
            "cooldown": self.cooldown,
            "timeout": self.timeout,
            "async_execution": self.async_execution,
            "requires_confirmation": self.requires_confirmation,
        }


class SkillRegistry:
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
        self._skills: dict[str, BaseSkill] = {}
        self._metadata: dict[str, SkillMetadata] = {}
        self._last_executed: dict[str, float] = {}
        self._skill_dir = Path(__file__).parent
        self._builtin_modules: dict[str, str] = {}

    def register(self, skill: BaseSkill, metadata: SkillMetadata | None = None):
        name = skill.name
        self._skills[name] = skill
        if metadata:
            self._metadata[name] = metadata
        else:
            self._metadata[name] = SkillMetadata(name=name)
        self._last_executed[name] = 0.0
        log.info(f"Skill registered: {name}")
        events.emit(EventType.SKILL_LOADED, {"name": name, "metadata": self._metadata[name].to_dict()})

    def unregister(self, name: str):
        if name in self._skills:
            del self._skills[name]
            self._metadata.pop(name, None)
            self._last_executed.pop(name, None)
            log.info(f"Skill unregistered: {name}")
            events.emit(EventType.SKILL_UNLOADED, {"name": name})

    def get(self, name: str) -> BaseSkill | None:
        return self._skills.get(name)

    def get_all(self) -> dict[str, BaseSkill]:
        return dict(self._skills)

    def get_metadata(self, name: str) -> SkillMetadata | None:
        return self._metadata.get(name)

    def get_all_metadata(self) -> dict[str, dict]:
        return {name: meta.to_dict() for name, meta in self._metadata.items()}

    def can_execute(self, name: str) -> tuple[bool, str]:
        skill = self._skills.get(name)
        if not skill:
            return False, "Skill not found"
        if not skill.enabled:
            return False, "Skill is disabled"
        meta = self._metadata.get(name)
        if meta and meta.cooldown > 0:
            elapsed = time.time() - self._last_executed.get(name, 0)
            if elapsed < meta.cooldown:
                remaining = meta.cooldown - elapsed
                return False, f"Skill on cooldown ({remaining:.1f}s remaining)"
        return True, ""

    def mark_executed(self, name: str):
        self._last_executed[name] = time.time()

    def discover_skills(self) -> list[str]:
        discovered = []
        for fpath in self._skill_dir.glob("*.py"):
            if fpath.name.startswith("_") or fpath.name == "base.py" or fpath.name == "registry.py":
                continue
            module_name = f"jarvis.skills.{fpath.stem}"
            try:
                module = importlib.import_module(module_name)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if inspect.isclass(attr) and issubclass(attr, BaseSkill) and attr is not BaseSkill:
                        discovered.append(attr.__name__)
                        self._builtin_modules[attr.__name__] = module_name
            except Exception as e:
                log.warning(f"Failed to discover skills in {module_name}: {e}")
        return discovered

    def load_skill_class(self, class_name: str) -> type[BaseSkill] | None:
        module_name = self._builtin_modules.get(class_name)
        if not module_name:
            return None
        try:
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
            if inspect.isclass(cls) and issubclass(cls, BaseSkill):
                return cls
        except Exception as e:
            log.error(f"Failed to load skill class {class_name}: {e}")
        return None

    def reload_skills(self, router):
        old_names = set(self._skills.keys())
        self.discover_skills()

        for name in list(old_names):
            self.unregister(name)
            try:
                router.unregister(name)
            except Exception:
                pass

        for class_name in self._builtin_modules:
            cls = self.load_skill_class(class_name)
            if cls:
                try:
                    skill = cls()
                    self.register(skill)
                    router.register(skill)
                    log.info(f"Reloaded skill: {skill.name}")
                except Exception as e:
                    log.error(f"Failed to reload skill {class_name}: {e}")

        events.emit(EventType.SKILL_LOADED, {"name": "__all__", "action": "reload"})
        return list(self._skills.keys())

    def get_skills_by_category(self, category: str) -> list[dict]:
        return [
            meta.to_dict()
            for name, meta in self._metadata.items()
            if meta.category == category
        ]

    def get_categories(self) -> list[str]:
        return list({meta.category for meta in self._metadata.values()})

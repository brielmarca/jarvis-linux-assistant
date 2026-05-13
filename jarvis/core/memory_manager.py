import json
import re
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any, Optional


class MemoryManager:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._base_dir = Path.home() / ".jarvis" / "memory"
        self._base_dir.mkdir(parents=True, exist_ok=True)

        self._short_term: list[dict] = []
        self._max_short_term = 100
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        self._long_term_file = self._base_dir / "long_term.json"
        self._preferences_file = self._base_dir / "preferences.json"
        self._projects_file = self._base_dir / "projects.json"
        self._context_file = self._base_dir / "context.json"
        self._long_term: list[dict] = []
        self._preferences: dict[str, Any] = {}
        self._projects: dict[str, dict] = {}
        self._context: dict[str, Any] = {}

        self._load_all()

    def _load_all(self):
        self._long_term = self._load_json(self._long_term_file, [])
        self._preferences = self._load_json(self._preferences_file, {})
        self._projects = self._load_json(self._projects_file, {})
        self._context = self._load_json(self._context_file, {})

    def _load_json(self, path: Path, default: Any) -> Any:
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return default

    def _save_json(self, path: Path, data: Any):
        try:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except OSError as e:
            pass

    def _now(self) -> str:
        return datetime.now().isoformat()

    def _ts(self) -> float:
        return datetime.now().timestamp()

    def _compute_importance(self, text: str, tags: list[str] | None = None) -> float:
        score = 0.5
        important_keywords = [
            "remember", "important", "critical", "project", "main",
            "lembrar", "importante", "crítico", "projeto", "principal",
            "favorite", "prefer", "preferido",
        ]
        for kw in important_keywords:
            if kw in text.lower():
                score += 0.1
        if tags:
            score += min(len(tags) * 0.05, 0.3)
        return min(score, 1.0)

    # ── Short-term memory ──────────────────────────────────────────

    def add_short_term(self, entry: dict) -> dict:
        entry["_id"] = f"st_{self._ts()}"
        entry["_type"] = "short_term"
        entry["timestamp"] = self._now()
        self._short_term.append(entry)
        if len(self._short_term) > self._max_short_term:
            self._short_term.pop(0)
        return entry

    def get_short_term(self, n: int = 20) -> list[dict]:
        return self._short_term[-n:]

    def get_session_context(self, n: int = 10) -> str:
        recent = self._short_term[-n:]
        if not recent:
            return ""
        lines = []
        for e in recent:
            cmd = e.get("command", e.get("text", ""))
            resp = e.get("response", "")
            lines.append(f"User: {cmd}")
            if resp:
                lines.append(f"Jarvis: {resp}")
        return "\n".join(lines)

    def clear_short_term(self):
        self._short_term = []

    # ── Long-term memory ───────────────────────────────────────────

    def remember(self, text: str, tags: list[str] | None = None, source: str = "user", importance: float | None = None):
        entry = {
            "_id": f"lt_{self._ts()}",
            "_type": "long_term",
            "text": text,
            "tags": tags or [],
            "source": source,
            "importance": importance if importance is not None else self._compute_importance(text, tags),
            "created": self._now(),
            "accessed": self._now(),
            "access_count": 0,
        }
        self._long_term.append(entry)
        self._save_json(self._long_term_file, self._long_term)
        return entry

    def recall(self, query: str, n: int = 5, min_importance: float = 0.0) -> list[dict]:
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored = []
        for mem in self._long_term:
            if mem.get("importance", 0) < min_importance:
                continue
            text_lower = mem.get("text", "").lower()
            text_words = set(text_lower.split())
            tag_match = any(t.lower() in query_lower for t in mem.get("tags", []))
            word_overlap = len(query_words & text_words)
            exact_match = query_lower in text_lower

            score = 0.0
            if exact_match:
                score += 1.0
            if tag_match:
                score += 0.6
            score += word_overlap * 0.1
            score += mem.get("importance", 0) * 0.3

            if score > 0:
                scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, mem in scored[:n]:
            mem["access_count"] = mem.get("access_count", 0) + 1
            mem["accessed"] = self._now()
            results.append(mem)

        self._save_json(self._long_term_file, self._long_term)
        return results

    def forget(self, memory_id: str) -> bool:
        before = len(self._long_term)
        self._long_term = [m for m in self._long_term if m.get("_id") != memory_id]
        if len(self._long_term) != before:
            self._save_json(self._long_term_file, self._long_term)
            return True
        return False

    def search_memories(self, query: str, tags: list[str] | None = None, n: int = 20) -> list[dict]:
        query_lower = query.lower()
        results = []
        for mem in self._long_term:
            text = mem.get("text", "").lower()
            if query_lower in text:
                results.append(mem)
                continue
            if tags:
                mem_tags = [t.lower() for t in mem.get("tags", [])]
                if any(t.lower() in mem_tags for t in tags):
                    if mem not in results:
                        results.append(mem)
        return results[:n]

    def cleanup_long_term(self, max_age_days: int = 365, min_importance: float = 0.1):
        cutoff = self._ts() - (max_age_days * 86400)
        before = len(self._long_term)
        self._long_term = [
            m for m in self._long_term
            if m.get("importance", 0) >= min_importance
            or self._parse_ts(m.get("created", "")) > cutoff
        ]
        if len(self._long_term) != before:
            self._save_json(self._long_term_file, self._long_term)

    def _parse_ts(self, ts: str) -> float:
        try:
            return datetime.fromisoformat(ts).timestamp()
        except (ValueError, TypeError):
            return 0

    def get_all_memories(self, tags: list[str] | None = None) -> list[dict]:
        if not tags:
            return list(self._long_term)
        return [m for m in self._long_term if any(t in m.get("tags", []) for t in tags)]

    # ── User preferences ───────────────────────────────────────────

    def set_preference(self, key: str, value: Any):
        self._preferences[key] = value
        self._save_json(self._preferences_file, self._preferences)

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self._preferences.get(key, default)

    def get_all_preferences(self) -> dict:
        return dict(self._preferences)

    def delete_preference(self, key: str) -> bool:
        if key in self._preferences:
            del self._preferences[key]
            self._save_json(self._preferences_file, self._preferences)
            return True
        return False

    # ── Project memory ─────────────────────────────────────────────

    def set_project(self, name: str, path: str, metadata: dict | None = None):
        self._projects[name.lower()] = {
            "name": name,
            "path": path,
            "metadata": metadata or {},
            "last_opened": self._now(),
            "created": self._now(),
        }
        self._save_json(self._projects_file, self._projects)

    def get_project(self, name: str) -> dict | None:
        return self._projects.get(name.lower())

    def get_project_by_path(self, path: str) -> dict | None:
        for proj in self._projects.values():
            if proj.get("path") == path:
                return proj
        return None

    def search_projects(self, query: str) -> list[dict]:
        q = query.lower()
        results = []
        for proj in self._projects.values():
            if q in proj["name"].lower() or q in proj.get("path", "").lower():
                results.append(proj)
            else:
                meta = proj.get("metadata", {})
                for v in meta.values():
                    if isinstance(v, str) and q in v.lower():
                        results.append(proj)
                        break
        return results

    def get_all_projects(self) -> dict:
        return dict(self._projects)

    def delete_project(self, name: str) -> bool:
        key = name.lower()
        if key in self._projects:
            del self._projects[key]
            self._save_json(self._projects_file, self._projects)
            return True
        return False

    # ── Context memory ─────────────────────────────────────────────

    def set_context(self, key: str, value: Any):
        self._context[key] = {"value": value, "updated": self._now()}
        self._save_json(self._context_file, self._context)

    def get_context(self, key: str, default: Any = None) -> Any:
        entry = self._context.get(key)
        if entry is None:
            return default
        return entry.get("value", default)

    def get_all_context(self) -> dict:
        return {k: v.get("value") for k, v in self._context.items()}

    def clear_context(self):
        self._context = {}
        self._save_json(self._context_file, self._context)

    # ── Lifecycle ──────────────────────────────────────────────────

    def get_stats(self) -> dict:
        return {
            "short_term_count": len(self._short_term),
            "long_term_count": len(self._long_term),
            "preferences_count": len(self._preferences),
            "projects_count": len(self._projects),
            "context_keys": list(self._context.keys()),
            "session_id": self._session_id,
        }

    def full_cleanup(self, max_age_days: int = 365, min_importance: float = 0.1):
        self.cleanup_long_term(max_age_days, min_importance)

    def reset_all(self):
        self._short_term = []
        self._long_term = []
        self._preferences = {}
        self._projects = {}
        self._context = {}
        self._save_json(self._long_term_file, self._long_term)
        self._save_json(self._preferences_file, self._preferences)
        self._save_json(self._projects_file, self._projects)
        self._save_json(self._context_file, self._context)

import json
import math
import re
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any


STOPWORDS = {
    "a", "an", "the", "is", "it", "to", "and", "or", "of", "in", "on",
    "at", "for", "by", "with", "from", "as", "was", "are", "be", "has",
    "have", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "need", "dare", "ought", "used",
    "this", "that", "these", "those", "i", "you", "he", "she", "we",
    "they", "my", "your", "his", "her", "its", "our", "their", "me",
    "him", "us", "them", "what", "which", "who", "whom", "how", "when",
    "where", "why", "if", "then", "else", "also", "just", "some", "any",
    "not", "no", "nor", "so", "very", "too", "quite", "all", "each",
    "every", "both", "few", "more", "most", "other", "such", "only",
    "own", "same", "than", "now", "then", "here", "there", "about",
    "up", "out", "off", "over", "after", "before", "between", "under",
    "again", "further", "once", "um", "uh", "like", "well", "yeah",
    "okay", "ok", "got", "gonna", "wanna", "dont", "doesnt", "didnt",
    "wont", "cant", "couldnt", "wouldnt", "shouldnt", "isnt", "arent",
    "wasnt", "werent", "hasnt", "havent", "hadnt", "da", "nao", "que",
    "com", "uma", "para", "dos", "das", "num", "numa", "ele", "ela",
    "voce", "nos", "eles", "elas", "seu", "sua", "seus", "suas",
    "mais", "mas", "ate", "aqui", "ali", "la", "depois", "antes",
    "sempre", "nunca", "ja", "ainda", "quando", "enquanto", "desde",
    "ate", "contra", "entre", "desde", "durante", "mediante", "sem",
    "sob", "sobre", "tras", "o", "a", "os", "as", "ao", "aos",
    "do", "da", "dos", "das", "no", "na", "nos", "nas", "por",
    "per", "pelo", "pela", "pelos", "pelas", "num", "numa",
}


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    tokens = re.findall(r'\b[a-zA-ZÀ-ÿ0-9]+\b', text)
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def _compute_tf(tokens: list[str]) -> dict[str, float]:
    if not tokens:
        return {}
    counts = Counter(tokens)
    max_freq = max(counts.values())
    return {word: count / max_freq for word, count in counts.items()}


def _compute_idf(documents: list[list[str]]) -> dict[str, float]:
    n = len(documents)
    if n == 0:
        return {}
    df: Counter = Counter()
    for doc in documents:
        unique = set(doc)
        for word in unique:
            df[word] += 1
    return {word: math.log((n + 1) / (count + 1)) + 1 for word, count in df.items()}


def _cosine_similarity(vec1: dict[str, float], vec2: dict[str, float]) -> float:
    common = set(vec1) & set(vec2)
    if not common:
        return 0.0
    dot = sum(vec1[w] * vec2[w] for w in common)
    norm1 = math.sqrt(sum(v * v for v in vec1.values()))
    norm2 = math.sqrt(sum(v * v for v in vec2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class SemanticMemory:
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

        self._entries_file = self._base_dir / "semantic_entries.json"
        self._embeddings_file = self._base_dir / "semantic_embeddings.json"
        self._pins_file = self._base_dir / "memory_pins.json"

        self._entries: list[dict] = []
        self._embeddings: dict[str, dict[str, float]] = {}
        self._pins: set[str] = set()
        self._idf_cache: dict[str, float] = {}

        self._decay_rate = 0.05
        self._max_entries = 2000

        self._load_all()

    def _load_all(self):
        self._entries = self._load_json(self._entries_file, [])
        self._embeddings = self._load_json(self._embeddings_file, {})
        self._pins = set(self._load_json(self._pins_file, []))
        self._rebuild_idf()

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
        except OSError:
            pass

    def _save_all(self):
        self._save_json(self._entries_file, self._entries)
        self._save_json(self._embeddings_file, self._embeddings)
        self._save_json(self._pins_file, list(self._pins))

    def _rebuild_idf(self):
        documents = [_tokenize(e.get("text", "")) for e in self._entries]
        self._idf_cache = _compute_idf(documents)

    def _embed(self, text: str) -> dict[str, float]:
        tokens = _tokenize(text)
        tf = _compute_tf(tokens)
        idf = self._idf_cache
        if not idf:
            idf = {w: 1.0 for w in tf}
        return {word: tf.get(word, 0) * idf.get(word, 1.0) for word in set(tokens)}

    def _now_ts(self) -> float:
        return time.time()

    def _age_days(self, entry: dict) -> float:
        created = entry.get("created", 0)
        return (self._now_ts() - created) / 86400.0

    # ── Public API ────────────────────────────────────────────────

    def store(self, text: str, source: str = "user", tags: list[str] | None = None, metadata: dict | None = None) -> str:
        entry_id = f"sem_{int(self._now_ts() * 1000)}_{len(self._entries)}"
        entry = {
            "id": entry_id,
            "text": text,
            "source": source,
            "tags": tags or [],
            "metadata": metadata or {},
            "created": self._now_ts(),
            "accessed": self._now_ts(),
            "access_count": 0,
            "importance": 0.5,
            "pinned": False,
        }
        self._entries.append(entry)
        self._embeddings[entry_id] = self._embed(text)

        if len(self._entries) > self._max_entries:
            self._trim_oldest()

        self._rebuild_idf()
        self._save_all()
        return entry_id

    def search(self, query: str, n: int = 10, min_score: float = 0.05) -> list[dict]:
        query_embedding = self._embed(query)
        scored = []
        for entry in self._entries:
            eid = entry["id"]
            emb = self._embeddings.get(eid)
            if emb is None:
                emb = self._embed(entry.get("text", ""))
                self._embeddings[eid] = emb
            score = _cosine_similarity(query_embedding, emb)
            if score >= min_score:
                decay = self._compute_decay(entry)
                adjusted = score * (1.0 - decay * 0.3)
                pinned_bonus = 0.2 if entry.get("pinned") else 0.0
                importance_bonus = entry.get("importance", 0.5) * 0.2
                final_score = adjusted + pinned_bonus + importance_bonus
                scored.append((final_score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, entry in scored[:n]:
            entry["access_count"] += 1
            entry["accessed"] = self._now_ts()
            results.append({**entry, "_score": round(score, 4)})

        self._save_all()
        return results

    def _compute_decay(self, entry: dict) -> float:
        days = self._age_days(entry)
        if entry.get("pinned"):
            return 0.0
        return min(days * self._decay_rate, 1.0)

    def _trim_oldest(self):
        unpinned = [e for e in self._entries if not e.get("pinned")]
        unpinned.sort(key=lambda e: e.get("created", 0))
        to_remove = unpinned[:50]
        remove_ids = {e["id"] for e in to_remove}
        self._entries = [e for e in self._entries if e["id"] not in remove_ids]
        for rid in remove_ids:
            self._embeddings.pop(rid, None)

    def pin(self, entry_id: str) -> bool:
        for entry in self._entries:
            if entry["id"] == entry_id:
                entry["pinned"] = True
                entry["importance"] = max(entry.get("importance", 0.5), 0.9)
                self._pins.add(entry_id)
                self._save_all()
                return True
        return False

    def unpin(self, entry_id: str) -> bool:
        for entry in self._entries:
            if entry["id"] == entry_id:
                entry["pinned"] = False
                self._pins.discard(entry_id)
                self._save_all()
                return True
        return False

    def get_pinned(self) -> list[dict]:
        return [e for e in self._entries if e.get("pinned")]

    def is_pinned(self, entry_id: str) -> bool:
        return entry_id in self._pins

    def update_importance(self, entry_id: str, importance: float):
        for entry in self._entries:
            if entry["id"] == entry_id:
                entry["importance"] = max(0.0, min(1.0, importance))
                self._save_all()
                return

    def decay_all(self):
        now = self._now_ts()
        changed = False
        for entry in self._entries:
            if entry.get("pinned"):
                continue
            days = (now - entry.get("created", now)) / 86400.0
            if days > 30:
                new_importance = max(0.05, entry.get("importance", 0.5) - 0.01 * (days / 7))
                if new_importance != entry.get("importance"):
                    entry["importance"] = new_importance
                    changed = True
        if changed:
            self._save_all()

    def get_recent(self, n: int = 20) -> list[dict]:
        sorted_entries = sorted(self._entries, key=lambda e: e.get("created", 0), reverse=True)
        return sorted_entries[:n]

    def get_by_tags(self, tags: list[str], n: int = 50) -> list[dict]:
        tag_set = set(t.lower() for t in tags)
        results = []
        for entry in self._entries:
            entry_tags = set(t.lower() for t in entry.get("tags", []))
            if tag_set & entry_tags:
                results.append(entry)
        return results[:n]

    def get_by_source(self, source: str, n: int = 50) -> list[dict]:
        return [e for e in self._entries if e.get("source") == source][:n]

    def delete(self, entry_id: str) -> bool:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e["id"] != entry_id]
        self._embeddings.pop(entry_id, None)
        self._pins.discard(entry_id)
        if len(self._entries) != before:
            self._rebuild_idf()
            self._save_all()
            return True
        return False

    def count(self) -> int:
        return len(self._entries)

    def get_stats(self) -> dict:
        pinned_count = len(self._pins)
        sources: Counter = Counter(e.get("source", "unknown") for e in self._entries)
        avg_importance = sum(e.get("importance", 0.5) for e in self._entries) / max(len(self._entries), 1)
        return {
            "total_entries": len(self._entries),
            "pinned": pinned_count,
            "sources": dict(sources),
            "avg_importance": round(avg_importance, 3),
            "unique_tokens": len(self._idf_cache),
        }

    def clear(self):
        self._entries = []
        self._embeddings = {}
        self._pins = set()
        self._idf_cache = {}
        self._save_all()


semantic_memory = SemanticMemory()

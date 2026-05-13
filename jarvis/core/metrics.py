import time
from collections import defaultdict
from threading import Lock
from typing import Any

from jarvis.core.events import EventBus, EventType


events = EventBus()


class MetricsCollector:
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
        self._latencies: dict[str, list[float]] = defaultdict(list)
        self._counters: dict[str, int] = defaultdict(int)
        self._events: list[dict] = []
        self._max_events = 500
        self._max_samples = 200
        self._start_time = time.time()
        self._lock = Lock()

    def record_latency(self, name: str, elapsed: float):
        with self._lock:
            self._latencies[name].append(elapsed)
            if len(self._latencies[name]) > self._max_samples:
                self._latencies[name] = self._latencies[name][-self._max_samples:]

    def increment(self, name: str, count: int = 1):
        with self._lock:
            self._counters[name] += count

    def trace(self, event_type: str, data: dict | None = None):
        with self._lock:
            self._events.append({
                "type": event_type,
                "data": data or {},
                "time": time.time(),
            })
            if len(self._events) > self._max_events:
                self._events.pop(0)

    def get_latency_stats(self, name: str) -> dict:
        with self._lock:
            vals = self._latencies.get(name, [])
            if not vals:
                return {"count": 0, "avg": 0, "min": 0, "max": 0, "total": 0}
            return {
                "count": len(vals),
                "avg": round(sum(vals) / len(vals), 4),
                "min": round(min(vals), 4),
                "max": round(max(vals), 4),
                "total": round(sum(vals), 4),
            }

    def get_counter(self, name: str) -> int:
        with self._lock:
            return self._counters.get(name, 0)

    def get_all_latencies(self) -> dict:
        with self._lock:
            return {name: self.get_latency_stats(name) for name in self._latencies}

    def get_all_counters(self) -> dict:
        with self._lock:
            return dict(self._counters)

    def get_recent_events(self, n: int = 50) -> list[dict]:
        with self._lock:
            return list(self._events[-n:])

    def get_uptime(self) -> float:
        return time.time() - self._start_time

    def summary(self) -> dict:
        return {
            "uptime": round(self.get_uptime(), 1),
            "latencies": self.get_all_latencies(),
            "counters": self.get_all_counters(),
            "events_tracked": len(self._events),
        }

    def clear(self):
        with self._lock:
            self._latencies.clear()
            self._counters.clear()
            self._events.clear()


metrics = MetricsCollector()


def trace_latency(name: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            metrics.record_latency(name, elapsed)
            return result
        return wrapper
    return decorator

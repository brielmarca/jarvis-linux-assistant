import functools
import time
from collections import OrderedDict
from threading import Lock, Thread
from typing import Any, Callable

from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class Timer:
    def __init__(self, name: str = ""):
        self.name = name
        self._start: float | None = None
        self._elapsed: float = 0.0

    def __enter__(self):
        self._start = time.time()
        return self

    def __exit__(self, *args):
        if self._start:
            self._elapsed = time.time() - self._start

    @property
    def elapsed(self) -> float:
        return self._elapsed

    def log(self, msg: str = ""):
        label = msg or self.name
        log.debug(f"[TIMER] {label}: {self.elapsed:.3f}s")


class TimingStats:
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
        self._stats: dict[str, list[float]] = {}

    def record(self, name: str, elapsed: float):
        if name not in self._stats:
            self._stats[name] = []
        self._stats[name].append(elapsed)
        if len(self._stats[name]) > 1000:
            self._stats[name] = self._stats[name][-500:]

    def get_stats(self, name: str) -> dict:
        vals = self._stats.get(name, [])
        if not vals:
            return {"count": 0}
        return {
            "count": len(vals),
            "avg": sum(vals) / len(vals),
            "min": min(vals),
            "max": max(vals),
            "total": sum(vals),
        }

    def get_all_stats(self) -> dict:
        return {name: self.get_stats(name) for name in self._stats}

    def summary(self) -> str:
        lines = ["Timing Stats:"]
        for name in sorted(self._stats.keys()):
            s = self.get_stats(name)
            if s["count"] > 0:
                lines.append(
                    f"  {name}: {s['count']} calls, "
                    f"avg={s['avg']*1000:.1f}ms, "
                    f"min={s['min']*1000:.1f}ms, "
                    f"max={s['max']*1000:.1f}ms"
                )
        return "\n".join(lines)

    def clear(self):
        self._stats = {}


timing = TimingStats()


def timed(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        timing.record(func.__qualname__, elapsed)
        return result
    return wrapper


class LRUCache:
    def __init__(self, maxsize: int = 128, ttl: float = 60.0):
        self._maxsize = maxsize
        self._ttl = ttl
        self._cache: OrderedDict = OrderedDict()
        self._times: dict[str, float] = {}
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key not in self._cache:
                return None
            if time.time() - self._times.get(key, 0) > self._ttl:
                self._cache.pop(key, None)
                self._times.pop(key, None)
                return None
            self._cache.move_to_end(key)
            return self._cache[key]

    def set(self, key: str, value: Any):
        with self._lock:
            self._cache[key] = value
            self._times[key] = time.time()
            self._cache.move_to_end(key)
            while len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def invalidate(self, key: str):
        with self._lock:
            self._cache.pop(key, None)
            self._times.pop(key, None)

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._times.clear()

    @property
    def size(self) -> int:
        return len(self._cache)


class BackgroundWorker:
    def __init__(self, name: str = "worker"):
        self._name = name
        self._thread: Thread | None = None
        self._running = False
        self._tasks: list[tuple[Callable, tuple, dict]] = []

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._thread = Thread(target=self._run, name=self._name, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def submit(self, func: Callable, *args, **kwargs):
        self._tasks.append((func, args, kwargs))

    def _run(self):
        while self._running:
            if self._tasks:
                func, args, kwargs = self._tasks.pop(0)
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    log.error(f"Background task error: {e}")
            else:
                time.sleep(0.1)

    @property
    def pending(self) -> int:
        return len(self._tasks)


def lazy_import(module_name: str, attr: str | None = None):
    def _load():
        import importlib
        mod = importlib.import_module(module_name)
        if attr:
            return getattr(mod, attr)
        return mod
    return _load

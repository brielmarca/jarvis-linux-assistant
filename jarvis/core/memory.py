import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class Memory:
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
        self.mem_dir = Path.home() / ".jarvis" / "memory"
        self.mem_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.mem_dir / "history.json"
        self.state_file = self.mem_dir / "state.json"
        self._history = []
        self._state = {}
        self._load()

    def _load(self):
        hf = Path(str(self.history_file))
        sf = Path(str(self.state_file))
        if hf.exists():
            try:
                self._history = json.loads(hf.read_text())
            except Exception:
                self._history = []
        if sf.exists():
            try:
                self._state = json.loads(sf.read_text())
            except Exception:
                self._state = {}

    def _save_history(self):
        Path(str(self.history_file)).write_text(json.dumps(self._history[-500:], indent=2))

    def _save_state(self):
        Path(str(self.state_file)).write_text(json.dumps(self._state, indent=2))

    def add_command(self, command: str, response: str, status: str = "ok", execution_time: Optional[float] = None, skill: Optional[str] = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "response": response,
            "status": status,
            "execution_time": execution_time,
            "skill": skill,
        }
        self._history.append(entry)
        self._save_history()
        return entry

    def get_history(self, n: int = 50) -> list:
        return self._history[-n:]

    def set_state(self, key: str, value):
        self._state[key] = value
        self._save_state()

    def get_state(self, key: str, default=None):
        return self._state.get(key, default)

    def clear_history(self):
        self._history = []
        self._save_history()

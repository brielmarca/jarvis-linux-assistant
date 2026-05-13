import importlib.util
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


@dataclass
class HealthCheckResult:
    component: str
    status: str  # ok, warning, error
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "component": self.component,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }


class HealthChecker:
    def __init__(self):
        self._results: list[HealthCheckResult] = []

    def check_all(self) -> list[HealthCheckResult]:
        self._results = []
        self._check_python()
        self._check_dependencies()
        self._check_commands()
        self._check_ollama()
        self._check_config()
        self._check_dirs()
        self._check_permissions()
        return self._results

    def _add(self, component: str, status: str, message: str = "", details: dict | None = None):
        self._results.append(HealthCheckResult(component, status, message, details or {}))

    def _check_python(self):
        v = sys.version_info
        ok = v.major >= 3 and v.minor >= 10
        self._add(
            "python",
            "ok" if ok else "error",
            f"Python {v.major}.{v.minor}.{v.micro} ({'ok' if ok else 'need 3.10+'})",
            {"version": f"{v.major}.{v.minor}.{v.micro}"},
        )

    def _check_dependencies(self):
        required = ["yaml", "PyQt6"]
        optional = ["faster_whisper", "openwakeword", "numpy", "pyaudio", "soundfile", "requests", "torch"]

        for dep in required:
            spec = importlib.util.find_spec(dep)
            self._add(
                f"dep:{dep}",
                "ok" if spec else "error",
                f"{'Found' if spec else 'Missing'}",
            )

        for dep in optional:
            spec = importlib.util.find_spec(dep)
            if spec:
                self._add(f"dep:{dep}", "ok", f"Found")

    def _check_commands(self):
        commands = {
            "wmctrl": "window control",
            "playerctl": "media playback",
            "pactl": "audio control",
        }
        for cmd, purpose in commands.items():
            found = shutil.which(cmd) is not None
            self._add(
                f"cmd:{cmd}",
                "ok" if found else "warning",
                f"{'Found' if found else 'Not found'} ({purpose})",
            )

    def _check_ollama(self):
        try:
            import requests
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            ok = r.status_code == 200
            self._add(
                "ollama",
                "ok" if ok else "error",
                "Running" if ok else "Not responding",
                {"host": "http://localhost:11434"},
            )
        except Exception:
            self._add(
                "ollama",
                "warning",
                "Not running (AI features unavailable)",
                {"host": "http://localhost:11434"},
            )

    def _check_config(self):
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        if config_path.exists():
            size = config_path.stat().st_size
            self._add("config", "ok", f"Found ({size}b)", {"path": str(config_path)})
        else:
            self._add("config", "error", "Config file not found", {"path": str(config_path)})

    def _check_dirs(self):
        dirs = {
            "memory": Path.home() / ".jarvis" / "memory",
            "logs": Path.home() / ".jarvis" / "logs",
        }
        for name, path in dirs.items():
            ok = path.exists()
            self._add(
                f"dir:{name}",
                "ok" if ok else "warning",
                f"{'Exists' if ok else 'Will be created on first use'}",
                {"path": str(path)},
            )

    def _check_permissions(self):
        critical_path = Path.home() / ".jarvis"
        if critical_path.exists():
            readable = os.access(str(critical_path), os.R_OK)
            writable = os.access(str(critical_path), os.W_OK)
            self._add(
                "permissions",
                "ok" if (readable and writable) else "error",
                f"{'Read/write' if readable and writable else 'Permission issue'}",
            )

    def summary(self) -> str:
        ok_count = sum(1 for r in self._results if r.status == "ok")
        warn_count = sum(1 for r in self._results if r.status == "warning")
        err_count = sum(1 for r in self._results if r.status == "error")
        total = len(self._results)

        lines = [f"Health Check: {ok_count}/{total} ok, {warn_count} warnings, {err_count} errors"]
        for r in self._results:
            icon = {"ok": "✓", "warning": "⚠", "error": "✗"}.get(r.status, "?")
            lines.append(f"  {icon} {r.component}: {r.message}")

        return "\n".join(lines)




import os
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jarvis.core.logger import JarvisLogger


log = JarvisLogger()

DANGEROUS_COMMANDS = [
    "rm -rf", "rm -rf /", "rm -fr", "mkfs", "dd if=", "format",
    "> /dev/", "chmod 777 /", "sudo", "passwd",
    ":(){ :|:& };:", "fork bomb",
    "chown", "chgrp", "fdisk", "parted", "mkswap",
]

DESTRUCTIVE_PATTERNS = [
    r"\bsudo\s+rm\b", r"\brm\s+-rf\s+/", r"\bdd\s+if=",
    r"\bmkfs\b", r"\bformat\b", r"\bmkswap\b",
    r"\bpasswd\b", r"\bfdisk\b",
]


@dataclass
class SandboxResult:
    success: bool = False
    returncode: int = -1
    stdout: str = ""
    stderr: str = ""
    command: str = ""
    execution_time: float = 0.0
    blocked: bool = False
    block_reason: str = ""
    requires_confirmation: bool = False

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "command": self.command,
            "execution_time": self.execution_time,
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "requires_confirmation": self.requires_confirmation,
        }


class CommandSandbox:
    def __init__(self):
        self._allowed_dirs: list[Path] = []
        self._execution_log: list[dict] = []
        self._max_log = 500
        self._dry_run = False
        self._timeout = 30
        self._load_allowed_dirs()

    def _load_allowed_dirs(self):
        try:
            from jarvis.core.memory_manager import MemoryManager
            mem = MemoryManager()
            dirs = mem.get_preference("allowed_dev_dirs", [])
            self._allowed_dirs = [Path(d).resolve() for d in dirs if d]
        except Exception:
            pass
        if not self._allowed_dirs:
            self._allowed_dirs = [Path.home() / "Documents"]

    def add_allowed_dir(self, path: str):
        p = Path(path).expanduser().resolve()
        if p.exists() and p.is_dir():
            if p not in self._allowed_dirs:
                self._allowed_dirs.append(p)
                try:
                    from jarvis.core.memory_manager import MemoryManager
                    MemoryManager().set_preference(
                        "allowed_dev_dirs",
                        [str(d) for d in self._allowed_dirs],
                    )
                except Exception:
                    pass
            return True
        return False

    def remove_allowed_dir(self, path: str):
        p = Path(path).resolve()
        self._allowed_dirs = [d for d in self._allowed_dirs if d != p]

    def get_allowed_dirs(self) -> list[str]:
        return [str(d) for d in self._allowed_dirs]

    @property
    def dry_run(self) -> bool:
        return self._dry_run

    @dry_run.setter
    def dry_run(self, value: bool):
        self._dry_run = value

    @property
    def timeout(self) -> int:
        return self._timeout

    @timeout.setter
    def timeout(self, value: int):
        self._timeout = max(1, min(300, value))

    def check_safety(self, command: str, cwd: str | None = None) -> SandboxResult:
        cmd_lower = command.lower().strip()

        for dangerous in DANGEROUS_COMMANDS:
            if dangerous in cmd_lower:
                return SandboxResult(
                    command=command,
                    blocked=True,
                    block_reason=f"Command contains dangerous pattern: '{dangerous}'",
                    requires_confirmation=True,
                )

        import re
        for pattern in DESTRUCTIVE_PATTERNS:
            if re.search(pattern, cmd_lower):
                return SandboxResult(
                    command=command,
                    blocked=True,
                    block_reason="Command matches destructive pattern",
                    requires_confirmation=True,
                )

        if cwd:
            cwd_path = Path(cwd).resolve()
            is_allowed = any(
                cwd_path == d or d in cwd_path.parents
                for d in self._allowed_dirs
            )
            if not is_allowed:
                return SandboxResult(
                    command=command,
                    blocked=True,
                    block_reason=f"Directory not in allowed list: {cwd}",
                    requires_confirmation=True,
                )

        return SandboxResult(command=command, success=True)

    def execute(self, command: str, cwd: str | None = None, timeout: int | None = None) -> SandboxResult:
        safety = self.check_safety(command, cwd)
        if safety.blocked:
            return safety

        if self._dry_run:
            log.info(f"[DRY RUN] Would execute: {command}")
            return SandboxResult(
                command=command,
                success=True,
                stdout=f"[DRY RUN] {command}",
                blocked=False,
            )

        start = time.time()
        cmd_timeout = timeout or self._timeout

        try:
            result = subprocess.run(
                ["bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=cmd_timeout,
                cwd=cwd or str(self._allowed_dirs[0]) if self._allowed_dirs else None,
            )
            elapsed = time.time() - start
            sr = SandboxResult(
                success=result.returncode == 0,
                returncode=result.returncode,
                stdout=result.stdout[:5000],
                stderr=result.stderr[:2000],
                command=command,
                execution_time=elapsed,
            )
        except subprocess.TimeoutExpired:
            sr = SandboxResult(
                command=command,
                blocked=False,
                success=False,
                stderr=f"Command timed out after {cmd_timeout}s",
                execution_time=time.time() - start,
            )
        except FileNotFoundError:
            sr = SandboxResult(
                command=command,
                blocked=False,
                success=False,
                stderr="Command not found",
            )
        except Exception as e:
            sr = SandboxResult(
                command=command,
                blocked=False,
                success=False,
                stderr=str(e),
            )

        self._log_execution(sr)
        return sr

    def _log_execution(self, result: SandboxResult):
        self._execution_log.append({
            "timestamp": time.time(),
            "command": result.command,
            "success": result.success,
            "returncode": result.returncode,
            "execution_time": result.execution_time,
            "blocked": result.blocked,
        })
        if len(self._execution_log) > self._max_log:
            self._execution_log = self._execution_log[-self._max_log:]

    def get_execution_log(self, n: int = 50) -> list[dict]:
        return self._execution_log[-n:]

    def clear_log(self):
        self._execution_log = []

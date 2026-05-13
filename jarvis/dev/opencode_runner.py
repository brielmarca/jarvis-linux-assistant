import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jarvis.core.logger import JarvisLogger
from jarvis.dev.command_sandbox import CommandSandbox, SandboxResult


log = JarvisLogger()


@dataclass
class OpenCodeTask:
    request: str
    project_path: str
    status: str = "pending"  # pending, running, completed, failed, cancelled
    output: str = ""
    error: str = ""
    execution_time: float = 0.0
    task_id: str = ""

    def to_dict(self) -> dict:
        return {
            "request": self.request,
            "project_path": self.project_path,
            "status": self.status,
            "output": self.output[:500],
            "error": self.error[:200],
            "execution_time": self.execution_time,
            "task_id": self.task_id,
        }


class OpenCodeRunner:
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
        self._sandbox = CommandSandbox()
        self._history: list[OpenCodeTask] = []
        self._available = self._check_available()

    def _check_available(self) -> bool:
        try:
            subprocess.run(["opencode", "--help"], capture_output=True, timeout=5)
            return True
        except Exception:
            return False

    def is_available(self) -> bool:
        return self._available

    def run(self, request: str, project_path: str | None = None, dry_run: bool = False) -> OpenCodeTask:
        if not project_path:
            from jarvis.core.memory_manager import MemoryManager
            mem = MemoryManager()
            project_path = mem.get_preference("main_project_path", str(Path.home() / "Documents"))

        task = OpenCodeTask(
            request=request,
            project_path=project_path,
            task_id=f"oc_{time.time_ns()}",
        )

        if not self._available:
            error_msg = "OpenCode is not installed. Install: pip install opencode"
            task.status = "failed"
            task.error = error_msg
            self._history.append(task)
            log.warning(error_msg)
            return task

        project_dir = Path(project_path).expanduser().resolve()
        if not project_dir.exists():
            error_msg = f"Project path does not exist: {project_path}"
            task.status = "failed"
            task.error = error_msg
            self._history.append(task)
            return task

        if dry_run:
            task.status = "completed"
            task.output = f"[DRY RUN] Would run opencode in {project_dir} with: {request}"
            self._history.append(task)
            return task

        safety = self._sandbox.check_safety(f"opencode {request}", str(project_dir))
        if safety.blocked:
            task.status = "failed"
            task.error = safety.block_reason
            self._history.append(task)
            return task

        task.status = "running"
        start = time.time()

        try:
            log.info(f"OpenCode running in {project_dir}: {request[:100]}...")
            process = subprocess.run(
                ["opencode", request],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
            task.execution_time = time.time() - start

            if process.returncode == 0:
                task.status = "completed"
                task.output = process.stdout or "OpenCode completed successfully"
                log.info(f"OpenCode completed in {task.execution_time:.2f}s")
            else:
                task.status = "failed"
                task.error = process.stderr or f"Exit code {process.returncode}"
                log.error(f"OpenCode failed: {task.error}")

        except subprocess.TimeoutExpired:
            task.status = "failed"
            task.error = "OpenCode timed out after 120s"
            task.execution_time = time.time() - start
            log.error("OpenCode timed out")
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.execution_time = time.time() - start
            log.error(f"OpenCode error: {e}")

        self._history.append(task)
        return task

    def cancel(self, task_id: str) -> bool:
        for task in self._history:
            if task.task_id == task_id and task.status == "running":
                task.status = "cancelled"
                return True
        return False

    def get_history(self, n: int = 20) -> list[dict]:
        return [t.to_dict() for t in self._history[-n:]]

    def get_sandbox(self) -> CommandSandbox:
        return self._sandbox

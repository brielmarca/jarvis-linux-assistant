import json
import subprocess
from pathlib import Path

import yaml

from jarvis.skills.base import BaseSkill
from jarvis.core.permissions import PermissionManager
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()
perms = PermissionManager()


class OpenCodeSkill(BaseSkill):
    def __init__(self):
        super().__init__()
        self.config = self._load_config()

    def _load_config(self):
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        if config_path.exists():
            return yaml.safe_load(config_path.read_text()) or {}
        return {}

    def patterns(self):
        return [
            r"(use|call|run|open)\s+opencode\s+(.+)$",
            r"(opencode|code assistant|coding assistant)",
            r"(change|modify|update|fix|refactor|implement|create|write)\s+(.+)",
        ]

    def _get_project_root(self) -> Path:
        default_paths = self.config.get("default_project_paths", [])
        if default_paths:
            return Path(default_paths[0]).expanduser()
        return Path.home() / "Documents"

    def execute(self, command: str, match) -> str:
        cmd_lower = command.lower()

        if not perms.get_skill_permission("opencode", "require_confirmation"):
            log.info("OpenCode skill used without confirmation flag")

        project_root = self._get_project_root()

        if not project_root.exists():
            return f"Project root {project_root} not found"

        log.info(f"OpenCode skill invoked in {project_root}")

        try:
            subprocess.run(
                ["opencode", command],
                cwd=str(project_root),
                timeout=120,
            )
            return f"OpenCode processed request in {project_root}"
        except FileNotFoundError:
            return (
                "OpenCode is not installed. Install it with:\n"
                "pip install opencode\n"
                "Or visit: https://opencode.ai"
            )
        except subprocess.TimeoutExpired:
            return "OpenCode timed out. The request was too complex."
        except Exception as e:
            log.error(f"OpenCode execution error: {e}")
            return f"OpenCode error: {e}"

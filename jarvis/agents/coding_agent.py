import re
import subprocess
from pathlib import Path
from typing import Any

from jarvis.agents.base_agent import BaseAgent
from jarvis.automation.apps import launch_app, open_project_folder
from jarvis.automation.linux import run_cmd
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="coding", description="Development and coding tasks")
        self._default_path = Path.home() / "Documents"

    def can_handle(self, command: str, context: dict | None = None) -> tuple[bool, float]:
        cmd = command.lower()
        if any(kw in cmd for kw in ["git", "code", "vscode", "programming", "dev mode",
                                     "modo programador", "coding mode", "open project",
                                     "abre projeto", "opencode", "commit", "push", "pull",
                                     "branch", "merge", "fix", "refactor", "implement"]):
            return True, 0.8
        if re.search(r"\b(change|modify|update|create|write)\s+(.+)", cmd):
            return True, 0.5
        return False, 0.0

    def execute(self, command: str, context: dict | None = None) -> dict[str, Any]:
        cmd = command.lower().strip()

        if "programming mode" in cmd or "modo programador" in cmd or "dev mode" in cmd:
            launch_app("code")
            launch_app("terminal")
            return {"response": "Programming mode activated. VS Code and terminal launched.", "agent": "coding"}

        if "code mode" in cmd or "coding mode" in cmd or "modo código" in cmd:
            launch_app("code")
            return {"response": "VS Code launched. Happy coding!", "agent": "coding"}

        if "open project" in cmd or "abre projeto" in cmd:
            match = re.search(r"(?:open project|abre projeto|open o projeto)\s+(.+)", cmd)
            if match:
                path = match.group(1).strip()
                expanded = Path(path).expanduser()
                if expanded.exists():
                    return {"response": open_project_folder(str(expanded)), "agent": "coding"}
                code, out, _ = run_cmd(["bash", "-c", f"find ~/Documents -maxdepth 3 -type d -iname '*{path}*' 2>/dev/null | head -5"])
                if out:
                    paths = out.strip().split("\n")
                    return {"response": open_project_folder(paths[0]), "agent": "coding"}
                return {"response": f"Project '{path}' not found", "agent": "coding"}
            return {"response": "Which project should I open?", "agent": "coding"}

        if "git" in cmd:
            project_path = str(self._default_path)
            code, out, err = run_cmd(["bash", "-c", f"cd {project_path} && {command}"], timeout=15)
            if code == 0:
                return {"response": out[:500] if out else "Git command completed", "agent": "coding"}
            return {"response": f"Git error: {err[:200]}", "agent": "coding"}

        if "opencode" in cmd:
            try:
                subprocess.run(["opencode", command], cwd=str(self._default_path), timeout=120)
                return {"response": f"OpenCode processed request in {self._default_path}", "agent": "coding"}
            except FileNotFoundError:
                return {"response": "OpenCode is not installed. See https://opencode.ai", "agent": "coding"}
            except subprocess.TimeoutExpired:
                return {"response": "OpenCode timed out.", "agent": "coding"}
            except Exception as e:
                return {"response": f"OpenCode error: {e}", "agent": "coding"}

        return {"response": "Dev command not recognized", "agent": "coding"}

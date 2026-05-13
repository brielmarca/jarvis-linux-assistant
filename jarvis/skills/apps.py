from jarvis.skills.base import BaseSkill
from jarvis.automation import apps as apps_auto
from jarvis.automation.linux import run_cmd
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class AppsSkill(BaseSkill):
    def metadata(self):
        return {
            "description": "Launch applications, open projects, Docker status",
            "category": "apps",
            "cooldown": 0.5,
            "timeout": 15.0,
        }

    def patterns(self):
        return [
            r"\b(abre?|open|launch|iniciar)\s+(.+)$",
            r"\b(open|abre?)\s+(project|projeto|folder|pasta)\s+(.+)$",
            r"\b(docker|containers?|status docker)\b",
        ]

    def execute(self, command: str, match) -> str:
        cmd_lower = command.lower().strip()

        if "docker" in cmd_lower:
            return apps_auto.check_docker()

        if match.lastindex and match.lastindex >= 3:
            path = match.group(3).strip()
            from pathlib import Path
            p = Path(path).expanduser()
            if p.exists():
                return apps_auto.open_project_folder(str(p))
            return f"Project path not found: {path}"

        app_name = match.group(2).strip() if match.lastindex >= 2 else ""
        if not app_name:
            return "What should I open?"

        if "project" in cmd_lower or "projeto" in cmd_lower or "folder" in cmd_lower or "pasta" in cmd_lower:
            _, out, _ = run_cmd(["bash", "-c", f"find ~/Documents -maxdepth 2 -type d -iname '*{app_name}*' 2>/dev/null | head -5"])
            if out:
                paths = out.split("\n")
                return apps_auto.open_project_folder(paths[0])
            return f"No project folder found matching '{app_name}'"

        return apps_auto.launch_app(app_name)

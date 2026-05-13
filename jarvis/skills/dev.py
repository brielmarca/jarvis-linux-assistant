from jarvis.skills.base import BaseSkill
from jarvis.automation.apps import launch_app, open_project_folder
from jarvis.automation.linux import run_cmd
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class DevSkill(BaseSkill):
    def patterns(self):
        return [
            r"\b(programming mode|modo programador|dev mode|modo dev)\b",
            r"\b(open project|abre projeto|open (o )?projeto)\s+(.+)$",
            r"\b(code mode|coding mode|modo código)\b",
            r"\b(git status|git branch|git log)\b",
        ]

    def execute(self, command: str, match) -> str:
        cmd_lower = command.lower()

        if "programming mode" in cmd_lower or "modo programador" in cmd_lower or "dev mode" in cmd_lower:
            launch_app("code")
            launch_app("terminal")
            return "Programming mode activated. VS Code and terminal launched."

        if "open project" in cmd_lower or "abre projeto" in cmd_lower or "open o projeto" in cmd_lower:
            if match.lastindex and match.lastindex >= 3:
                path = match.group(match.lastindex).strip()
                expanded = __import__("pathlib").Path(path).expanduser()
                if expanded.exists():
                    return open_project_folder(str(expanded))
                _, out, _ = run_cmd(["bash", "-c", f"find ~/Documents -maxdepth 3 -type d -iname '*{path}*' 2>/dev/null | head -5"])
                if out:
                    paths = out.split("\n")
                    return open_project_folder(paths[0])
                return f"Project '{path}' not found"
            return "Which project should I open?"

        if "code mode" in cmd_lower or "coding mode" in cmd_lower or "modo código" in cmd_lower:
            launch_app("code")
            return "VS Code launched. Happy coding!"

        if "git" in cmd_lower:
            project_path = "/home/brielmarca/Documents/JARVIS.MILHONARI_PROJECT"
            code, out, err = run_cmd(["bash", "-c", f"cd {project_path} && {command}"], timeout=15)
            if code == 0:
                return out[:500] if out else "Git command completed"
            return f"Git error: {err[:200]}"

        return "Dev command not recognized"

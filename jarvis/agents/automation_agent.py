import re
import subprocess
from typing import Any

from jarvis.agents.base_agent import BaseAgent
from jarvis.automation.apps import launch_app
from jarvis.automation.linux import run_cmd
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class AutomationAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="automation", description="Linux automation and app launching")

    def can_handle(self, command: str, context: dict | None = None) -> tuple[bool, float]:
        cmd = command.lower()
        if any(kw in cmd for kw in ["open", "abre", "launch", "iniciar", "docker", "container",
                                     "bluetooth", "wifi", "network", "nmcli", "bluetoothctl",
                                     "terminal", "close", "fecha"]):
            return True, 0.7
        return False, 0.0

    def execute(self, command: str, context: dict | None = None) -> dict[str, Any]:
        cmd = command.lower().strip()

        if "docker" in cmd:
            code, out, err = run_cmd(["docker", "info", "--format", "{{.ServerVersion}}"])
            if code == 0:
                return {"response": f"Docker is running (version: {out})", "agent": "automation"}
            return {"response": "Docker is not running. Start it with 'sudo systemctl start docker'", "agent": "automation"}

        if "terminal" in cmd and ("open" in cmd or "abre" in cmd or "launch" in cmd or "iniciar" in cmd):
            terminal_cmds = ["x-terminal-emulator", "gnome-terminal", "konsole", "xterm", "kitty", "alacritty"]
            for term in terminal_cmds:
                try:
                    subprocess.Popen([term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return {"response": "Terminal opened", "agent": "automation"}
                except FileNotFoundError:
                    continue
            return {"response": "No terminal emulator found", "agent": "automation"}

        if "bluetooth" in cmd:
            code, out, err = run_cmd(["bluetoothctl", "show"], timeout=5)
            if code == 0:
                return {"response": "Bluetooth is available", "agent": "automation"}
            return {"response": "Bluetooth not available or bluetoothctl not found", "agent": "automation"}

        if "open" in cmd or "abre" in cmd or "launch" in cmd or "iniciar" in cmd:
            match = re.search(r"(?:open|abre?|launch|iniciar)\s+(.+)$", cmd)
            if match:
                app = match.group(1).strip()
                return {"response": launch_app(app), "agent": "automation"}

        return {"response": "Automation command not recognized", "agent": "automation"}

import re
from typing import Any

from jarvis.agents.base_agent import BaseAgent
from jarvis.automation import linux as linux_auto
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class SystemAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="system", description="System information and control")

    def can_handle(self, command: str, context: dict | None = None) -> tuple[bool, float]:
        cmd = command.lower()
        if any(kw in cmd for kw in ["time", "date", "hora", "data", "shutdown", "reboot",
                                     "deslig", "reinici", "system info", "system status",
                                     "info sistema", "status", "uptime", "kernel", "cpu",
                                     "memory", "disk", "hostname"]):
            return True, 0.8
        if "systemctl" in cmd or "service" in cmd:
            return True, 0.7
        return False, 0.0

    def execute(self, command: str, context: dict | None = None) -> dict[str, Any]:
        cmd = command.lower().strip()

        if "time" in cmd or "hora" in cmd:
            return {"response": f"The current time is {linux_auto.get_current_time()}", "agent": "system"}
        if "date" in cmd or "data" in cmd:
            return {"response": f"Today is {linux_auto.get_current_date()}", "agent": "system"}
        if "shutdown" in cmd or "deslig" in cmd:
            return {"response": "Shutdown scheduled in 1 minute. Run 'shutdown -c' to cancel.", "agent": "system",
                    "requires_confirmation": True, "command": command}
        if "reboot" in cmd or "reinici" in cmd:
            return {"response": "Reboot scheduled in 1 minute. Run 'shutdown -c' to cancel.", "agent": "system",
                    "requires_confirmation": True, "command": command}

        info = linux_auto.get_system_info()
        os_info = linux_auto.get_os_info()
        response = (
            f"System: {info.get('hostname', 'Unknown')}\n"
            f"OS: {os_info}\n"
            f"Kernel: {info.get('kernel', 'N/A')}\n"
            f"CPU: {info.get('cpu', 'N/A')}\n"
            f"Memory: {info.get('memory', 'N/A')}\n"
            f"Disk: {info.get('disk', 'N/A')}\n"
            f"Uptime: {info.get('uptime', 'N/A')}"
        )
        return {"response": response, "agent": "system"}

from jarvis.skills.base import BaseSkill
from jarvis.automation import linux as linux_auto
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class SystemSkill(BaseSkill):
    def metadata(self):
        return {
            "description": "System information, time, date, shutdown/reboot",
            "category": "system",
            "cooldown": 1.0,
            "timeout": 10.0,
        }

    def patterns(self):
        return [
            r"\b(que horas são|horas?|current time|time now|what time|hora)\b",
            r"\b(que dia é hoje|data de hoje|current date|today date|data)\b",
            r"\b(status|informações? do sistema|system info|system status|info sistema)\b",
            r"\b(desligar|shutdown|desliga)\b",
            r"\b(reiniciar|reboot|reinicia)\b",
        ]

    def execute(self, command: str, match) -> str:
        cmd_lower = command.lower()

        if "time" in cmd_lower or "hora" in cmd_lower:
            return f"The current time is {linux_auto.get_current_time()}"

        if "date" in cmd_lower or "data" in cmd_lower:
            return f"Today is {linux_auto.get_current_date()}"

        if "info" in cmd_lower or "status" in cmd_lower or "sistema" in cmd_lower:
            info = linux_auto.get_system_info()
            return (
                f"System: {info.get('hostname', 'Unknown')}\n"
                f"OS: {linux_auto.get_os_info()}\n"
                f"Kernel: {info.get('kernel', 'N/A')}\n"
                f"CPU: {info.get('cpu', 'N/A')}\n"
                f"Memory: {info.get('memory', 'N/A')}\n"
                f"Disk: {info.get('disk', 'N/A')}\n"
                f"Uptime: {info.get('uptime', 'N/A')}"
            )

        if "shutdown" in cmd_lower or "deslig" in cmd_lower:
            return "Shutdown scheduled in 1 minute. Run 'shutdown -c' to cancel."

        if "reboot" in cmd_lower or "reinici" in cmd_lower:
            return "Reboot scheduled in 1 minute. Run 'shutdown -c' to cancel."

        return "I don't understand that system command"

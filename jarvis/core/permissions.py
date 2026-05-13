import re
from pathlib import Path

import yaml


DANGEROUS_KEYWORDS = [
    "rm -rf", "mkfs", "dd if=", "format",
    "> /dev/", "chmod 777 /", "sudo", "passwd",
]


class PermissionManager:
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
        self.config = self._load_config()

    def _load_config(self):
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        if config_path.exists():
            return yaml.safe_load(config_path.read_text()) or {}
        return {}

    def is_dangerous(self, command: str) -> bool:
        cmd_lower = command.lower()
        for keyword in DANGEROUS_KEYWORDS:
            if keyword in cmd_lower:
                return True
        dangerous = self.config.get("permissions", {}).get("dangerous_commands", [])
        for d in dangerous:
            pattern = r'\b' + re.escape(d.lower()) + r'\b'
            if re.search(pattern, cmd_lower):
                return True
        return False

    def requires_confirmation(self, skill: str, action: str = None) -> bool:
        if self.config.get("require_confirmation_for_dangerous_commands", True):
            if self.is_dangerous(action or ""):
                return True
        skill_perms = self.config.get("permissions", {}).get(skill, {})
        return skill_perms.get("require_confirmation", False)

    def get_skill_permission(self, skill: str, permission: str) -> bool:
        skill_perms = self.config.get("permissions", {}).get(skill, {})
        return skill_perms.get(permission, False)

    def check_command_safety(self, command: str) -> dict:
        result = {
            "safe": True,
            "dangerous": False,
            "requires_confirmation": False,
            "reason": None,
        }
        if self.is_dangerous(command):
            result["safe"] = False
            result["dangerous"] = True
            result["requires_confirmation"] = True
            result["reason"] = "Command contains dangerous operations"
        return result

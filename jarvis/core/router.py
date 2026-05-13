from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class CommandRouter:
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
        self._skills = {}

    def register(self, skill):
        name = skill.name
        self._skills[name] = skill
        log.info(f"Skill registered: {name}")

    def unregister(self, name):
        if name in self._skills:
            del self._skills[name]
            log.info(f"Skill unregistered: {name}")

    def get_skills(self):
        return dict(self._skills)

    def route(self, command: str) -> tuple:
        cmd_lower = command.lower().strip()

        for name, skill in self._skills.items():
            if not skill.enabled:
                continue
            match = skill.matches(cmd_lower)
            if match:
                log.info(f"Routed '{command}' -> skill '{name}'")
                return skill, match

        log.info(f"No skill matched '{command}', routing to AI fallback")
        return None, None

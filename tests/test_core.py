import pytest
from pathlib import Path
import tempfile
import json


class TestLogger:
    def test_singleton(self):
        from jarvis.core.logger import JarvisLogger
        a = JarvisLogger()
        b = JarvisLogger()
        assert a is b

    def test_log_callbacks(self):
        from jarvis.core.logger import JarvisLogger
        log = JarvisLogger()
        received = []

        def cb(level, msg):
            received.append((level, msg))

        log.on_log(cb)
        log.info("test message")
        assert any("test message" in m for _, m in received)


class TestEventBus:
    def test_singleton(self):
        from jarvis.core.events import EventBus, EventType
        a = EventBus()
        b = EventBus()
        assert a is b

    def test_emit_and_receive(self):
        from jarvis.core.events import EventBus, EventType
        bus = EventBus()
        received = []

        def handler(data):
            received.append(data)

        bus.on(EventType.COMMAND_RECEIVED, handler)
        bus.emit(EventType.COMMAND_RECEIVED, {"test": True})
        assert received == [{"test": True}]

    def test_off(self):
        from jarvis.core.events import EventBus, EventType
        bus = EventBus()
        received = []

        def handler(data):
            received.append(data)

        bus.on(EventType.COMMAND_RECEIVED, handler)
        bus.off(EventType.COMMAND_RECEIVED, handler)
        bus.emit(EventType.COMMAND_RECEIVED, {"test": True})
        assert received == []


class TestMemory:
    @pytest.fixture
    def memory(self, tmp_path):
        from jarvis.core.memory import Memory
        mem = Memory()
        mem.mem_dir = tmp_path
        mem.history_file = tmp_path / "history.json"
        mem.state_file = tmp_path / "state.json"
        mem._history = []
        mem._state = {}
        return mem

    def test_add_command(self, memory):
        entry = memory.add_command("test cmd", "test response", "ok", 0.5, "test_skill")
        assert entry["command"] == "test cmd"
        assert entry["response"] == "test response"
        assert entry["status"] == "ok"
        assert entry["execution_time"] == 0.5
        assert entry["skill"] == "test_skill"

    def test_get_history(self, memory):
        memory.add_command("cmd1", "resp1")
        memory.add_command("cmd2", "resp2")
        history = memory.get_history()
        assert len(history) == 2

    def test_state(self, memory):
        memory.set_state("key1", "value1")
        assert memory.get_state("key1") == "value1"
        assert memory.get_state("nonexistent") is None
        assert memory.get_state("nonexistent", "default") == "default"


class TestPermissions:
    @pytest.fixture
    def perms(self):
        from jarvis.core.permissions import PermissionManager
        p = PermissionManager()
        p.config = {
            "require_confirmation_for_dangerous_commands": True,
            "permissions": {
                "opencode": {
                    "require_confirmation": True,
                    "allow_file_ops": False,
                }
            }
        }
        return p

    def test_dangerous_commands(self, perms):
        assert perms.is_dangerous("rm -rf /")
        assert perms.is_dangerous("sudo rm -rf /home")
        assert not perms.is_dangerous("open firefox")

    def test_requires_confirmation(self, perms):
        assert perms.requires_confirmation("opencode", "rm -rf /")
        assert not perms.requires_confirmation("apps", "open firefox")

    def test_check_command_safety(self, perms):
        result = perms.check_command_safety("open firefox")
        assert result["safe"] is True

        result = perms.check_command_safety("rm -rf /")
        assert result["safe"] is False
        assert result["dangerous"] is True


class TestRouter:
    @pytest.fixture
    def router(self):
        from jarvis.core.router import CommandRouter
        r = CommandRouter()
        r._skills = {}
        return r

    def test_register_and_route(self, router):
        from jarvis.skills.system import SystemSkill
        skill = SystemSkill()
        router.register(skill)
        assert "system" in router.get_skills()

        result = router.route("what time is it")
        assert result is not None
        skill_match, match = result
        assert skill_match.name == "system"

    def test_no_match(self, router):
        result = router.route("some completely unknown command xyz123")
        assert result == (None, None)

    def test_docker_routes_to_apps(self, router):
        from jarvis.skills.apps import AppsSkill
        router.register(AppsSkill())
        skill, match = router.route("docker status")
        assert skill is not None
        assert skill.name == "apps"

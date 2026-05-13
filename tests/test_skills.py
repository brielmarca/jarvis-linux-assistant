import pytest


class TestSystemSkill:
    @pytest.fixture
    def skill(self):
        from jarvis.skills.system import SystemSkill
        return SystemSkill()

    def test_patterns(self, skill):
        patterns = skill.patterns()
        assert len(patterns) > 0

    def test_matches_time(self, skill):
        assert skill.matches("what time is it")
        assert skill.matches("que horas são")
        assert skill.matches("current time")

    def test_matches_info(self, skill):
        assert skill.matches("system info")
        assert skill.matches("informações do sistema")
        assert skill.matches("status")

    def test_execute_time(self, skill):
        result = skill.execute("what time is it", None)
        assert "time" in result.lower()

    def test_execute_info(self, skill):
        result = skill.execute("system info", None)
        assert "System" in result


class TestAppsSkill:
    @pytest.fixture
    def skill(self):
        from jarvis.skills.apps import AppsSkill
        return AppsSkill()

    def test_patterns(self, skill):
        assert skill.matches("open firefox")
        assert skill.matches("open terminal")
        assert skill.matches("abre vs code")
        assert skill.matches("docker")

    def test_execute_docker(self, skill):
        result = skill.execute("check docker", None)
        assert "Docker" in result


class TestMediaSkill:
    @pytest.fixture
    def skill(self):
        from jarvis.skills.media import MediaSkill
        return MediaSkill()

    def test_patterns(self, skill):
        assert skill.matches("increase volume")
        assert skill.matches("decrease volume")
        assert skill.matches("mute")
        assert skill.matches("next track")

    def test_execute_mute(self, skill):
        result = skill.execute("mute", None)
        assert result == "Volume toggled mute/unmute"


class TestBrowserSkill:
    @pytest.fixture
    def skill(self):
        from jarvis.skills.browser import BrowserSkill
        return BrowserSkill()

    def test_patterns(self, skill):
        assert skill.matches("search for python tutorials")
        assert skill.matches("google ai news")
        assert skill.matches("open website github.com")

    def test_execute_search(self, skill):
        result = skill.execute("search for python tutorials", None)
        assert "Searching" in result


class TestDevSkill:
    @pytest.fixture
    def skill(self):
        from jarvis.skills.dev import DevSkill
        return DevSkill()

    def test_patterns(self, skill):
        assert skill.matches("programming mode")
        assert skill.matches("modo programador")
        assert skill.matches("git status")

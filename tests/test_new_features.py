import sys
sys.path.insert(0, '.')

import json
from pathlib import Path


def setup_memory():
    from jarvis.core.memory_manager import MemoryManager
    m = MemoryManager()
    m._long_term = []
    m._preferences = {}
    m._projects = {}
    m._context = {}
    return m


def setup_classifier():
    from jarvis.agents.intent_classifier import IntentClassifier
    return IntentClassifier()


def setup_registry():
    from jarvis.skills.registry import SkillRegistry
    r = SkillRegistry()
    r._skills = {}
    r._metadata = {}
    return r


def setup_sandbox():
    from jarvis.dev.command_sandbox import CommandSandbox
    s = CommandSandbox()
    s._execution_log = []
    return s


def setup_detector():
    from jarvis.voice.silence_detector import SilenceDetector
    return SilenceDetector()


def setup_perms():
    from jarvis.core.permissions import PermissionManager
    p = PermissionManager()
    p.config = {
        "require_confirmation_for_dangerous_commands": True,
        "permissions": {},
    }
    return p


# ── Memory Manager Tests ──

def test_memory_remember_recall():
    mem = setup_memory()
    mem.remember("test data", tags=["test"], importance=0.8)
    results = mem.recall("test")
    assert len(results) >= 1
    assert any("test" in r["text"] for r in results)
    print("  ✓ test_memory_remember_recall")


def test_memory_recall_by_importance():
    mem = setup_memory()
    mem.remember("low importance", tags=["test"], importance=0.1)
    mem.remember("high importance", tags=["test"], importance=0.9)
    results = mem.recall("importance", min_importance=0.5)
    assert all(r["importance"] >= 0.5 for r in results)
    print("  ✓ test_memory_recall_by_importance")


def test_memory_preferences():
    mem = setup_memory()
    mem.set_preference("theme", "dark")
    assert mem.get_preference("theme") == "dark"
    assert mem.get_preference("nonexistent") is None
    assert mem.get_preference("nonexistent", "default") == "default"
    mem.delete_preference("theme")
    assert mem.get_preference("theme") is None
    print("  ✓ test_memory_preferences")


def test_memory_projects():
    mem = setup_memory()
    mem.set_project("test-proj", "/tmp/test", {"type": "demo"})
    assert mem.get_project("test-proj") is not None
    assert mem.get_project("test-proj")["path"] == "/tmp/test"
    results = mem.search_projects("test")
    assert len(results) >= 1
    mem.delete_project("test-proj")
    assert mem.get_project("test-proj") is None
    print("  ✓ test_memory_projects")


def test_memory_short_term():
    mem = setup_memory()
    mem.add_short_term({"command": "test cmd", "type": "command"})
    ctx = mem.get_session_context(5)
    assert "test cmd" in ctx
    print("  ✓ test_memory_short_term")


def test_memory_forget():
    mem = setup_memory()
    mem.remember("forget me", tags=["test"])
    mem_id = mem._long_term[0]["_id"]
    assert mem.forget(mem_id)
    assert len(mem.recall("forget")) == 0
    print("  ✓ test_memory_forget")


def test_memory_cleanup():
    mem = setup_memory()
    mem.remember("keep me", tags=["test"], importance=0.9)
    mem.remember("remove me", tags=["test"], importance=0.05)
    mem.cleanup_long_term(max_age_days=0, min_importance=0.1)
    assert len(mem._long_term) >= 1
    print("  ✓ test_memory_cleanup")


def test_memory_search_tags():
    mem = setup_memory()
    mem.remember("tagged item", tags=["python", "code"])
    results = mem.search_memories("python", tags=["python"])
    assert len(results) >= 1
    print("  ✓ test_memory_search_tags")


def test_memory_stats():
    mem = setup_memory()
    stats = mem.get_stats()
    assert "long_term_count" in stats
    assert "preferences_count" in stats
    print("  ✓ test_memory_stats")


def test_memory_context():
    mem = setup_memory()
    mem.set_context("key1", "value1")
    assert mem.get_context("key1") == "value1"
    assert mem.get_context("nonexistent", "default") == "default"
    mem.clear_context()
    assert mem.get_context("key1") is None
    print("  ✓ test_memory_context")


def test_memory_reset():
    mem = setup_memory()
    mem.remember("something", tags=["test"])
    mem.set_preference("k", "v")
    mem.reset_all()
    assert len(mem._long_term) == 0
    assert len(mem._preferences) == 0
    print("  ✓ test_memory_reset")


# ── Agent System Tests ──

def test_intent_system():
    ic = setup_classifier()
    intent, conf = ic.best_intent("what time is it")
    assert intent == "system"
    assert conf > 0.5
    print("  ✓ test_intent_system")


def test_intent_media():
    ic = setup_classifier()
    intent, conf = ic.best_intent("increase volume")
    assert intent == "media_control"
    print("  ✓ test_intent_media")


def test_intent_browser():
    ic = setup_classifier()
    intent, conf = ic.best_intent("search for python")
    assert intent == "browser"
    print("  ✓ test_intent_browser")


def test_intent_coding():
    ic = setup_classifier()
    intent, conf = ic.best_intent("git status")
    assert intent == "coding"
    print("  ✓ test_intent_coding")


def test_intent_memory():
    ic = setup_classifier()
    intent, conf = ic.best_intent("remember my project")
    assert intent == "memory"
    print("  ✓ test_intent_memory")


def test_intent_automation():
    ic = setup_classifier()
    intent, conf = ic.best_intent("open terminal")
    assert intent == "automation"
    print("  ✓ test_intent_automation")


def test_intent_multiple():
    ic = setup_classifier()
    intents = ic.classify("open terminal and run git status")
    assert len(intents) >= 2
    print("  ✓ test_intent_multiple")


# ── Skill Registry Tests ──

def test_registry_register():
    from jarvis.skills.system import SystemSkill
    reg = setup_registry()
    skill = SystemSkill()
    reg.register(skill)
    meta = reg.get_metadata("system")
    assert meta is not None
    assert meta.name == "system"
    print("  ✓ test_registry_register")


def test_registry_can_execute():
    from jarvis.skills.system import SystemSkill
    reg = setup_registry()
    reg.register(SystemSkill())
    can, reason = reg.can_execute("system")
    assert can
    assert reason == ""
    print("  ✓ test_registry_can_execute")


def test_registry_unregister():
    from jarvis.skills.system import SystemSkill
    reg = setup_registry()
    reg.register(SystemSkill())
    reg.unregister("system")
    assert reg.get("system") is None
    print("  ✓ test_registry_unregister")


def test_registry_get_all():
    from jarvis.skills.system import SystemSkill
    from jarvis.skills.media import MediaSkill
    reg = setup_registry()
    reg.register(SystemSkill())
    reg.register(MediaSkill())
    skills = reg.get_all()
    assert len(skills) >= 2
    print("  ✓ test_registry_get_all")


def test_registry_discover():
    reg = setup_registry()
    discovered = reg.discover_skills()
    assert len(discovered) >= 1
    print("  ✓ test_registry_discover")


# ── Command Sandbox Tests ──

def test_sandbox_safe():
    s = setup_sandbox()
    result = s.check_safety("echo hello")
    assert result.success
    assert not result.blocked
    print("  ✓ test_sandbox_safe")


def test_sandbox_dangerous_rm():
    s = setup_sandbox()
    result = s.check_safety("rm -rf /")
    assert result.blocked
    assert result.requires_confirmation
    print("  ✓ test_sandbox_dangerous_rm")


def test_sandbox_dangerous_dd():
    s = setup_sandbox()
    result = s.check_safety("dd if=/dev/zero of=/dev/sda")
    assert result.blocked
    print("  ✓ test_sandbox_dangerous_dd")


def test_sandbox_dangerous_mkfs():
    s = setup_sandbox()
    result = s.check_safety("mkfs.ext4 /dev/sda1")
    assert result.blocked
    print("  ✓ test_sandbox_dangerous_mkfs")


def test_sandbox_dangerous_sudo_rm():
    s = setup_sandbox()
    result = s.check_safety("sudo rm -rf /home")
    assert result.blocked
    print("  ✓ test_sandbox_dangerous_sudo_rm")


def test_sandbox_safe_systemctl():
    s = setup_sandbox()
    result = s.check_safety("systemctl status docker")
    assert not result.blocked
    print("  ✓ test_sandbox_safe_systemctl")


def test_sandbox_execute():
    s = setup_sandbox()
    result = s.execute("echo hello")
    assert result.success
    assert "hello" in result.stdout
    print("  ✓ test_sandbox_execute")


def test_sandbox_dry_run():
    s = setup_sandbox()
    s.dry_run = True
    result = s.execute("echo dry_run_test")
    assert result.success
    assert "[DRY RUN]" in result.stdout
    s.dry_run = False
    print("  ✓ test_sandbox_dry_run")


def test_sandbox_log():
    s = setup_sandbox()
    s.execute("echo log_test")
    logs = s.get_execution_log(5)
    assert len(logs) >= 1
    assert "log_test" in logs[0]["command"]
    print("  ✓ test_sandbox_log")


# ── Performance Tests ──

def test_timer():
    from jarvis.core.performance import Timer
    with Timer("test") as t:
        pass
    assert t.elapsed >= 0
    print("  ✓ test_timer")


def test_lru_cache():
    from jarvis.core.performance import LRUCache
    cache = LRUCache(maxsize=2, ttl=10)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") == 1
    assert cache.get("c") is None
    cache.set("c", 3)
    assert cache.size <= 2
    print("  ✓ test_lru_cache")


def test_timing_stats():
    from jarvis.core.performance import TimingStats
    ts = TimingStats()
    ts.record("op1", 0.1)
    ts.record("op1", 0.2)
    stats = ts.get_stats("op1")
    assert stats["count"] == 2
    assert abs(stats["avg"] - 0.15) < 0.001
    print("  ✓ test_timing_stats")


# ── Config Validator Tests ──

def test_config_valid():
    from jarvis.core.config_validator import validate_config
    result = validate_config()
    assert result.valid or len(result.errors) == 0
    print("  ✓ test_config_valid")


# ── Health Checker Tests ──

def test_health_check():
    from jarvis.core.health import HealthChecker
    hc = HealthChecker()
    results = hc.check_all()
    assert len(results) > 0
    statuses = {r.status for r in results}
    assert statuses.issubset({"ok", "warning", "error"})
    print("  ✓ test_health_check")


# ── Silence Detector Tests ──

def test_silence_default():
    d = setup_detector()
    assert d.get_threshold() == 300
    print("  ✓ test_silence_default")


def test_silence_set_threshold():
    d = setup_detector()
    d.set_threshold(1000)
    assert d.get_threshold() == 1000
    print("  ✓ test_silence_set_threshold")


def test_silence_process():
    d = setup_detector()
    result = d.process_chunk(100, 16000, 1024)
    assert "volume" in result
    assert "is_silent" in result
    assert "should_stop" in result
    print("  ✓ test_silence_process")


def test_silence_reset():
    d = setup_detector()
    d.process_chunk(100, 16000, 1024)
    d.reset()
    result = d.process_chunk(100, 16000, 1024)
    assert result["elapsed"] < 1.0
    print("  ✓ test_silence_reset")


# ── Permission Manager Tests ──

def test_perms_dangerous():
    p = setup_perms()
    assert p.is_dangerous("rm -rf /")
    assert p.is_dangerous("mkfs.ext4")
    assert p.is_dangerous("dd if=/dev/zero")
    assert not p.is_dangerous("open firefox")
    assert not p.is_dangerous("echo hello")
    print("  ✓ test_perms_dangerous")


def test_perms_check_safety():
    p = setup_perms()
    result = p.check_command_safety("open firefox")
    assert result["safe"] is True
    result = p.check_command_safety("rm -rf /")
    assert result["safe"] is False
    assert result["dangerous"] is True
    print("  ✓ test_perms_check_safety")


# ── Phase J: Semantic Memory Tests ──

def test_semantic_store_and_search():
    from jarvis.core.semantic_memory import semantic_memory
    semantic_memory.clear()
    semantic_memory.store("Working on Python backend with Flask", source="user", tags=["python", "backend"])
    semantic_memory.store("Docker container management commands", source="user", tags=["docker", "devops"])
    semantic_memory.store("User prefers dark theme in VSCode", source="user", tags=["preference", "vscode"])
    results = semantic_memory.search("Python backend", n=5)
    assert len(results) >= 1
    assert "Python" in results[0]["text"] or "backend" in results[0]["text"]
    results2 = semantic_memory.search("docker")
    assert len(results2) >= 1
    print("  ✓ test_semantic_store_and_search")


def test_semantic_pin_unpin():
    from jarvis.core.semantic_memory import semantic_memory
    semantic_memory.clear()
    eid = semantic_memory.store("Important project configuration", source="user")
    assert semantic_memory.pin(eid)
    pinned = semantic_memory.get_pinned()
    assert len(pinned) >= 1 and pinned[0]["id"] == eid
    assert semantic_memory.is_pinned(eid)
    assert semantic_memory.unpin(eid)
    assert not semantic_memory.is_pinned(eid)
    print("  ✓ test_semantic_pin_unpin")


def test_semantic_decay():
    from jarvis.core.semantic_memory import SemanticMemory
    sm = SemanticMemory()
    sm.clear()
    sm.store("Old unimportant data", source="test")
    # Manually set entry age to be old
    for entry in sm._entries:
        entry["created"] = sm._now_ts() - (60 * 86400)  # 60 days ago
    sm.decay_all()
    assert all(e["importance"] < 0.5 for e in sm._entries if not e.get("pinned"))
    print("  ✓ test_semantic_decay")


def test_semantic_delete():
    from jarvis.core.semantic_memory import semantic_memory
    semantic_memory.clear()
    eid = semantic_memory.store("Delete me", source="test")
    assert semantic_memory.count() == 1
    assert semantic_memory.delete(eid)
    assert semantic_memory.count() == 0
    print("  ✓ test_semantic_delete")


def test_semantic_by_tags():
    from jarvis.core.semantic_memory import semantic_memory
    semantic_memory.clear()
    semantic_memory.store("Code A", source="user", tags=["code", "python"])
    semantic_memory.store("Code B", source="user", tags=["code", "javascript"])
    results = semantic_memory.get_by_tags(["code"])
    assert len(results) >= 2
    results = semantic_memory.get_by_tags(["python"])
    assert len(results) >= 1
    print("  ✓ test_semantic_by_tags")


def test_semantic_stats():
    from jarvis.core.semantic_memory import semantic_memory
    semantic_memory.clear()
    semantic_memory.store("Stat item 1", source="user", tags=["a"])
    semantic_memory.store("Stat item 2", source="system", tags=["b"])
    stats = semantic_memory.get_stats()
    assert stats["total_entries"] >= 2
    assert "user" in stats["sources"]
    assert "system" in stats["sources"]
    print("  ✓ test_semantic_stats")


# ── Phase J: Context Window Tests ──

def test_context_window_basic():
    from jarvis.core.context_window import ContextWindow
    cw = ContextWindow(max_tokens=4000, reserve_tokens=500)
    assert cw.max_tokens == 4000
    assert cw.reserve_tokens == 500
    cw.add_section("cmd", "test command", priority=100)
    cw.add_section("ctx", "some context", priority=50)
    content = cw.get_content()
    assert "test command" in content
    assert "some context" in content
    print("  ✓ test_context_window_basic")


def test_context_window_prune():
    from jarvis.core.context_window import ContextWindow
    cw = ContextWindow(max_tokens=100, reserve_tokens=10)
    # Add many high-token sections - should prune low priority
    cw.add_section("high", "A" * 200, priority=100)
    cw.add_section("low", "B" * 200, priority=1)
    cw.add_section("medium", "C" * 200, priority=50)
    stats = cw.get_stats()
    assert stats["sections"] <= 3
    assert cw.current_tokens() <= cw.max_tokens - cw.reserve_tokens
    print("  ✓ test_context_window_prune")


def test_context_manager():
    from jarvis.core.context_window import ContextManager
    cm = ContextManager(max_tokens=4096, reserve_tokens=512)
    cm.set_context("test command", {
        "project_context": "Project X",
        "session_context": "Session active",
        "recent_activity": "Recent: git diff",
        "semantic_context": "Related: coding",
        "preferences": "theme: dark",
        "active_context": "app: terminal",
    })
    content = cm.get_full_context()
    assert "Project X" in content
    assert "test command" in content
    assert "app: terminal" in content
    stats = cm.get_stats()
    assert stats["sections"] >= 1
    print("  ✓ test_context_manager")


# ── Phase J: Context Builder Tests ──

def test_context_builder():
    from jarvis.core.memory_manager import MemoryManager
    from jarvis.ai.context_builder import ContextBuilder
    mm = MemoryManager()
    cb = ContextBuilder(mm)
    prompt = cb.build_prompt("hello")
    assert "hello" in prompt
    sysp = cb.build_system_prompt({"assistant_name": "Jarvis", "language": "en"})
    assert "Jarvis" in sysp
    assert "English" in sysp or "en" in sysp
    summary = cb.summarize_context()
    assert "Context summary" in summary
    print("  ✓ test_context_builder")


# ── Phase K: Voice VAD Tests ──

def test_vad_basic():
    from jarvis.voice.vad import VoiceActivityDetector
    vad = VoiceActivityDetector()
    result = vad.is_speech(b'\x00' * 480)
    assert "speech" in result
    assert "energy" in result
    assert "prob" in result
    print("  ✓ test_vad_basic")


def test_energy_vad():
    from jarvis.voice.vad import EnergyVoiceDetector
    evd = EnergyVoiceDetector()
    r = evd.process([0, 0, 0])
    assert "energy" in r
    assert "is_voice" in r
    assert "should_stop" in r
    print("  ✓ test_energy_vad")


# ── Phase L: Desktop State Tests ──

def test_desktop_state():
    from jarvis.system.desktop_state import DesktopState
    ds = DesktopState()
    state = ds.get_state()
    assert "active_window" in state
    assert "active_app" in state
    assert "workspace" in state
    assert "battery" in state
    assert "network" in state
    assert "media" in state
    assert "monitors" in state
    print("  ✓ test_desktop_state")


def test_desktop_describe():
    from jarvis.system.desktop_state import DesktopState
    ds = DesktopState()
    desc = ds.describe_state()
    assert isinstance(desc, str)
    print("  ✓ test_desktop_describe")


# ── Phase M: Workflow Tests ──

def test_workflow_create():
    from jarvis.automation.workflows import WorkflowManager
    wm = WorkflowManager()
    wf = wm.create("unit_test_wf", steps=[
        {"action": "wait", "params": {"seconds": 0.01}, "label": "Short wait"},
    ])
    assert wf is not None
    assert wm.get("unit_test_wf") is not None
    wm.delete("unit_test_wf")
    assert wm.get("unit_test_wf") is None
    print("  ✓ test_workflow_create")


def test_workflow_templates():
    from jarvis.automation.workflows import WorkflowManager
    wm = WorkflowManager()
    wm.load_default_templates()
    templates = wm.get_templates()
    assert len(templates) >= 3
    stats = wm.get_stats()
    assert stats["total"] >= 3
    print("  ✓ test_workflow_templates")


# ── Phase P: Metrics Tests ──

def test_metrics():
    from jarvis.core.metrics import metrics
    metrics.clear()
    metrics.record_latency("op1", 0.1)
    metrics.record_latency("op1", 0.2)
    metrics.increment("cnt1")
    metrics.increment("cnt1", 2)
    lat = metrics.get_latency_stats("op1")
    assert lat["count"] == 2
    assert abs(lat["avg"] - 0.15) < 0.01
    assert metrics.get_counter("cnt1") == 3
    print("  ✓ test_metrics")


# ── Run all ──

if __name__ == "__main__":
    tests = [
        test_memory_remember_recall,
        test_memory_recall_by_importance,
        test_memory_preferences,
        test_memory_projects,
        test_memory_short_term,
        test_memory_forget,
        test_memory_cleanup,
        test_memory_search_tags,
        test_memory_stats,
        test_memory_context,
        test_memory_reset,
        test_intent_system,
        test_intent_media,
        test_intent_browser,
        test_intent_coding,
        test_intent_memory,
        test_intent_automation,
        test_intent_multiple,
        test_registry_register,
        test_registry_can_execute,
        test_registry_unregister,
        test_registry_get_all,
        test_registry_discover,
        test_sandbox_safe,
        test_sandbox_dangerous_rm,
        test_sandbox_dangerous_dd,
        test_sandbox_dangerous_mkfs,
        test_sandbox_dangerous_sudo_rm,
        test_sandbox_safe_systemctl,
        test_sandbox_execute,
        test_sandbox_dry_run,
        test_sandbox_log,
        test_timer,
        test_lru_cache,
        test_timing_stats,
        test_config_valid,
        test_health_check,
        test_silence_default,
        test_silence_set_threshold,
        test_silence_process,
        test_silence_reset,
        test_perms_dangerous,
        test_perms_check_safety,
        # Phase J
        test_semantic_store_and_search,
        test_semantic_pin_unpin,
        test_semantic_decay,
        test_semantic_delete,
        test_semantic_by_tags,
        test_semantic_stats,
        test_context_window_basic,
        test_context_window_prune,
        test_context_manager,
        test_context_builder,
        # Phase K
        test_vad_basic,
        test_energy_vad,
        # Phase L
        test_desktop_state,
        test_desktop_describe,
        # Phase M
        test_workflow_create,
        test_workflow_templates,
        # Phase P
        test_metrics,
    ]

    passed = 0
    failed = 0
    print(f"Running {len(tests)} tests...\n")

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            import traceback
            print(f"  FAIL: {test.__name__}: {e}")
            traceback.print_exc()

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    if failed:
        print("SOME TESTS FAILED ✗")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED ✓")

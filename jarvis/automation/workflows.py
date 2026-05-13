import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Callable

from jarvis.core.events import EventBus, EventType
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()
events = EventBus()

WORKFLOW_DIR = Path.home() / ".jarvis" / "workflows"
WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)


class WorkflowStep:
    def __init__(self, action: str, params: dict | None = None, label: str = ""):
        self.action = action
        self.params = params or {}
        self.label = label or action

    def to_dict(self) -> dict:
        return {"action": self.action, "params": self.params, "label": self.label}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data.get("action", ""), data.get("params", {}), data.get("label", ""))


class Workflow:
    def __init__(self, name: str, steps: list[WorkflowStep] | None = None,
                 description: str = "", category: str = "custom",
                 icon: str = "⚡", tags: list[str] | None = None):
        self.name = name
        self.steps = steps or []
        self.description = description
        self.category = category
        self.icon = icon
        self.tags = tags or []
        self.created = time.time()
        self.modified = time.time()
        self.run_count = 0
        self.last_run: float | None = None
        self.enabled = True

    def add_step(self, action: str, params: dict | None = None, label: str = ""):
        self.steps.append(WorkflowStep(action, params, label))
        self.modified = time.time()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "steps": [s.to_dict() for s in self.steps],
            "description": self.description,
            "category": self.category,
            "icon": self.icon,
            "tags": self.tags,
            "created": self.created,
            "modified": self.modified,
            "run_count": self.run_count,
            "last_run": self.last_run,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict):
        wf = cls(
            name=data.get("name", ""),
            steps=[WorkflowStep.from_dict(s) for s in data.get("steps", [])],
            description=data.get("description", ""),
            category=data.get("category", "custom"),
            icon=data.get("icon", "⚡"),
            tags=data.get("tags", []),
        )
        wf.created = data.get("created", time.time())
        wf.modified = data.get("modified", time.time())
        wf.run_count = data.get("run_count", 0)
        wf.last_run = data.get("last_run")
        wf.enabled = data.get("enabled", True)
        return wf


class WorkflowExecutor:
    def __init__(self):
        self._action_handlers: dict[str, Callable] = {}
        self._register_defaults()

    def register_action(self, name: str, handler: Callable):
        self._action_handlers[name] = handler

    def _register_defaults(self):
        self.register_action("launch_app", lambda p: _try_import("jarvis.automation.apps", "launch_app", p.get("app", "")))
        self.register_action("open_url", lambda p: _try_import("jarvis.automation.browser_agent", "open_url", p.get("url", "")))
        self.register_action("run_command", lambda p: _try_import("jarvis.automation.terminal", "execute_command", p.get("command", "")))
        self.register_action("open_terminal", lambda p: _try_import("jarvis.automation.terminal", "open_terminal"))
        self.register_action("switch_workspace", lambda p: _try_import("jarvis.automation.window_manager", "switch_workspace", p.get("workspace", "")))
        self.register_action("open_project", lambda p: _try_import("jarvis.automation.apps", "open_project_folder", p.get("path", "")))
        self.register_action("volume_set", lambda p: _try_import("jarvis.automation.media", "volume_set", p.get("level", 50)))
        self.register_action("volume_mute", lambda p: _try_import("jarvis.automation.media", "volume_mute"))
        self.register_action("docker_start", lambda p: _try_import("jarvis.automation.docker_tools", "docker_compose_up", p.get("path", ".")))
        self.register_action("docker_stop", lambda p: _try_import("jarvis.automation.docker_tools", "docker_compose_down", p.get("path", ".")))
        self.register_action("wait", lambda p: time.sleep(float(p.get("seconds", 1))))
        self.register_action("notify", lambda p: _notify(p.get("message", "")))
        self.register_action("run_workflow", lambda p: None)

    def execute(self, workflow: Workflow, step_callback: Callable = None) -> list[dict]:
        results = []
        events.emit(EventType.WORKFLOW_STARTED, {"name": workflow.name, "steps": len(workflow.steps)})

        for i, step in enumerate(workflow.steps):
            handler = self._action_handlers.get(step.action)
            if handler is None:
                log.warning(f"Unknown workflow action: {step.action}")
                result = {"step": i, "action": step.action, "success": False, "error": f"Unknown action: {step.action}"}
                results.append(result)
                events.emit(EventType.WORKFLOW_FAILED, result)
                if step_callback:
                    step_callback(result)
                continue

            try:
                log.info(f"Workflow step {i+1}/{len(workflow.steps)}: {step.label}")
                handler(step.params)
                result = {"step": i, "action": step.action, "success": True}
                results.append(result)
                events.emit(EventType.WORKFLOW_STEP_COMPLETED, result)
            except Exception as e:
                log.error(f"Workflow step {i} failed: {e}")
                result = {"step": i, "action": step.action, "success": False, "error": str(e)}
                results.append(result)
                events.emit(EventType.WORKFLOW_FAILED, result)

            if step_callback:
                step_callback(result)

        workflow.run_count += 1
        workflow.last_run = time.time()

        events.emit(EventType.WORKFLOW_COMPLETED, {
            "name": workflow.name,
            "results": results,
            "success": all(r["success"] for r in results),
        })
        return results


def _try_import(module_path: str, func_name: str, *args, **kwargs):
    import importlib
    try:
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        return func(*args, **kwargs)
    except Exception as e:
        log.error(f"Workflow action {module_path}.{func_name} failed: {e}")
        raise


def _notify(message: str):
    try:
        import subprocess
        subprocess.run(["notify-send", "Jarvis", message], timeout=5)
    except Exception:
        pass


class WorkflowManager:
    def __init__(self):
        self._workflows: dict[str, Workflow] = {}
        self._executor = WorkflowExecutor()
        self._lock = Lock()
        self._scheduled: list[dict] = []
        self._scheduler_thread: Thread | None = None
        self._scheduler_running = False
        self._load_all()

    def _workflow_path(self, name: str) -> Path:
        safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in name)
        return WORKFLOW_DIR / f"{safe}.json"

    def _load_all(self):
        for f in WORKFLOW_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                wf = Workflow.from_dict(data)
                self._workflows[wf.name] = wf
            except Exception as e:
                log.error(f"Failed to load workflow {f.name}: {e}")

    def _save(self, workflow: Workflow):
        path = self._workflow_path(workflow.name)
        path.write_text(json.dumps(workflow.to_dict(), indent=2))

    def _delete_file(self, name: str):
        path = self._workflow_path(name)
        if path.exists():
            path.unlink()

    def create(self, name: str, steps: list[dict] | None = None,
               description: str = "", category: str = "custom",
               icon: str = "⚡", tags: list[str] | None = None) -> Workflow:
        with self._lock:
            wf_steps = [WorkflowStep.from_dict(s) for s in (steps or [])]
            wf = Workflow(name, wf_steps, description, category, icon, tags)
            self._workflows[name] = wf
            self._save(wf)
            log.info(f"Workflow created: {name}")
            return wf

    def get(self, name: str) -> Workflow | None:
        return self._workflows.get(name)

    def get_all(self) -> list[Workflow]:
        return list(self._workflows.values())

    def get_by_category(self, category: str) -> list[Workflow]:
        return [w for w in self._workflows.values() if w.category == category]

    def delete(self, name: str) -> bool:
        with self._lock:
            if name in self._workflows:
                del self._workflows[name]
                self._delete_file(name)
                return True
            return False

    def update(self, name: str, **kwargs) -> Workflow | None:
        with self._lock:
            wf = self._workflows.get(name)
            if not wf:
                return None
            for key, value in kwargs.items():
                if hasattr(wf, key):
                    setattr(wf, key, value)
            wf.modified = time.time()
            self._save(wf)
            return wf

    def add_step(self, name: str, action: str, params: dict | None = None, label: str = ""):
        with self._lock:
            wf = self._workflows.get(name)
            if wf:
                wf.add_step(action, params, label)
                self._save(wf)
                return True
            return False

    def execute(self, name: str, step_callback: Callable = None) -> list[dict] | None:
        wf = self.get(name)
        if not wf:
            log.error(f"Workflow not found: {name}")
            return None
        if not wf.enabled:
            log.warning(f"Workflow disabled: {name}")
            return None
        log.info(f"Executing workflow: {name} ({len(wf.steps)} steps)")
        return self._executor.execute(wf, step_callback)

    def execute_async(self, name: str, step_callback: Callable = None):
        thread = Thread(target=self.execute, args=(name, step_callback), daemon=True)
        thread.start()

    def register_action(self, name: str, handler: Callable):
        self._executor.register_action(name, handler)

    def create_template(self, name: str, category: str, steps: list[dict],
                        description: str = "", icon: str = "⚡") -> Workflow:
        return self.create(name, steps, description, category, icon, tags=["template"])

    def get_templates(self) -> list[Workflow]:
        return [w for w in self._workflows.values() if "template" in w.tags]

    def get_stats(self) -> dict:
        total = len(self._workflows)
        enabled = sum(1 for w in self._workflows.values() if w.enabled)
        total_runs = sum(w.run_count for w in self._workflows.values())
        categories = {}
        for w in self._workflows.values():
            categories[w.category] = categories.get(w.category, 0) + 1
        return {
            "total": total,
            "enabled": enabled,
            "total_runs": total_runs,
            "categories": categories,
        }

    # ── Scheduling ─────────────────────────────────────────────

    def schedule(self, workflow_name: str, cron_expr: str, enabled: bool = True) -> str:
        schedule_id = f"sched_{int(time.time())}_{len(self._scheduled)}"
        self._scheduled.append({
            "id": schedule_id,
            "workflow": workflow_name,
            "cron": cron_expr,
            "enabled": enabled,
            "created": time.time(),
            "last_run": None,
        })
        if not self._scheduler_running:
            self._start_scheduler()
        return schedule_id

    def _start_scheduler(self):
        self._scheduler_running = True
        self._scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    def _scheduler_loop(self):
        while self._scheduler_running:
            now = datetime.now()
            for sched in self._scheduled:
                if not sched["enabled"]:
                    continue
                try:
                    parts = sched["cron"].split()
                    if len(parts) < 5:
                        continue
                    minute, hour, _, _, _ = parts
                    if (minute == "*" or int(minute) == now.minute) and \
                       (hour == "*" or int(hour) == now.hour):
                        if sched.get("last_run") != now.strftime("%Y%m%d%H%M"):
                            log.info(f"Scheduled workflow: {sched['workflow']}")
                            self.execute(sched["workflow"])
                            sched["last_run"] = now.strftime("%Y%m%d%H%M")
                except Exception:
                    pass
            time.sleep(30)

    def stop_scheduler(self):
        self._scheduler_running = False

    # ── Built-in templates ────────────────────────────────────

    def load_default_templates(self):
        templates = {
            "programming_mode": {
                "steps": [
                    {"action": "launch_app", "params": {"app": "code"}, "label": "Open VSCode"},
                    {"action": "open_project", "params": {"path": "."}, "label": "Open project"},
                    {"action": "open_terminal", "params": {}, "label": "Open terminal"},
                ],
                "description": "Set up programming environment",
                "category": "development",
                "icon": "💻",
            },
            "streaming_mode": {
                "steps": [
                    {"action": "launch_app", "params": {"app": "obs"}, "label": "Launch OBS"},
                    {"action": "launch_app", "params": {"app": "firefox"}, "label": "Launch browser"},
                    {"action": "notify", "params": {"message": "Streaming mode activated"}, "label": "Notify ready"},
                ],
                "description": "Prepare streaming setup",
                "category": "entertainment",
                "icon": "🎥",
            },
            "morning_routine": {
                "steps": [
                    {"action": "launch_app", "params": {"app": "firefox"}, "label": "Open browser"},
                    {"action": "notify", "params": {"message": "Good morning! Ready for the day"}, "label": "Greeting"},
                ],
                "description": "Start your morning routine",
                "category": "personal",
                "icon": "🌅",
            },
        }
        for name, data in templates.items():
            if name not in self._workflows:
                wf = self.create(
                    name=name,
                    steps=data["steps"],
                    description=data["description"],
                    category=data["category"],
                    icon=data["icon"],
                    tags=["template", "builtin"],
                )


workflow_manager = WorkflowManager()

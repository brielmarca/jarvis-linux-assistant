import json
import os
import re
import subprocess
import time
from pathlib import Path
from threading import Lock, Thread

from jarvis.core.events import EventBus, EventType
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()
events = EventBus()


def _run_cmd(cmd: list, timeout: int = 5) -> tuple:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception:
        return -1, "", ""


class DesktopState:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._state = {
            "active_window": "",
            "active_app": "",
            "workspace": "",
            "workspace_count": 0,
            "processes": [],
            "battery": {},
            "network": {},
            "media": {},
            "monitors": [],
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
        }
        self._cached_workspaces: list[str] = []
        self._thread: Thread | None = None
        self._running = False
        self._update_interval = 2.0
        self._cache_ttl = 1.0
        self._last_update = 0.0
        self._has_xdotool = self._check_tool("xdotool")
        self._has_wmctrl = self._check_tool("wmctrl")
        self._has_playerctl = self._check_tool("playerctl")
        self._has_nmcli = self._check_tool("nmcli")

    def _check_tool(self, name: str) -> bool:
        return _run_cmd(["which", name])[0] == 0

    def _get_active_window(self) -> str:
        if not self._has_xdotool:
            return ""
        code, out, _ = _run_cmd(["xdotool", "getactivewindow", "getwindowname"])
        return out if code == 0 else ""

    def _get_active_app(self) -> str:
        if not self._has_xdotool:
            return ""
        code, out, _ = _run_cmd(["xdotool", "getactivewindow", "getwindowpid"])
        if code != 0:
            return ""
        pid = out.strip()
        if not pid:
            return ""
        code2, out2, _ = _run_cmd(["ps", "-p", pid, "-o", "comm="])
        return out2.strip() if code2 == 0 else ""

    def _get_workspace_info(self) -> tuple[str, int]:
        if not self._has_wmctrl:
            return "", 0
        current = ""
        count = 0
        code, out, _ = _run_cmd(["wmctrl", "-d"])
        if code == 0:
            lines = out.splitlines()
            count = len(lines)
            for line in lines:
                if "*" in line:
                    parts = line.split()
                    if len(parts) > 0:
                        current = parts[0]
                    break
        return current, count

    def _get_battery(self) -> dict:
        result = {"charging": None, "percent": None, "status": "unknown"}
        bat_paths = sorted(Path("/sys/class/power_supply").glob("BAT*"))
        if not bat_paths:
            return result
        try:
            cap = (bat_paths[0] / "capacity").read_text().strip()
            result["percent"] = int(cap)
        except Exception:
            pass
        try:
            status = (bat_paths[0] / "status").read_text().strip()
            result["charging"] = status == "Charging"
            result["status"] = status.lower()
        except Exception:
            pass
        return result

    def _get_network(self) -> dict:
        result = {"ssid": None, "connected": False, "type": "unknown"}
        if self._has_nmcli:
            code, out, _ = _run_cmd(["nmcli", "-t", "-f", "TYPE,STATE,CONNECTION", "device", "status"])
            if code == 0:
                for line in out.splitlines():
                    parts = line.split(":")
                    if len(parts) >= 3 and parts[1] == "connected":
                        result["connected"] = True
                        result["type"] = parts[0]
                        result["ssid"] = parts[2]
                        break
        if not result["connected"]:
            code2, out2, _ = _run_cmd(["iwgetid", "-r"])
            if code2 == 0 and out2:
                result["connected"] = True
                result["ssid"] = out2
                result["type"] = "wifi"
        return result

    def _get_media(self) -> dict:
        result = {"playing": False, "title": "", "artist": "", "app": ""}
        if not self._has_playerctl:
            return result
        code, out, _ = _run_cmd(["playerctl", "--all-players", "metadata", "-f",
                                 "{{xesam:title}}|{{xesam:artist}}|{{playerName}}|{{status}}"])
        if code == 0 and out:
            lines = out.splitlines()
            for line in lines:
                parts = line.split("|")
                if len(parts) >= 4:
                    result["title"] = parts[0]
                    result["artist"] = parts[1] if len(parts) > 1 else ""
                    result["app"] = parts[2] if len(parts) > 2 else ""
                    result["playing"] = parts[3].lower() == "playing"
                    if result["playing"]:
                        break
        if result["playing"]:
            code2, out2, _ = _run_cmd(["playerctl", "position"])
            if code2 == 0 and out2:
                try:
                    pos = float(out2.strip())
                    result["position"] = round(pos, 1)
                except ValueError:
                    pass
        return result

    def _get_monitors(self) -> list[dict]:
        monitors = []
        code, out, _ = _run_cmd(["xrandr", "--query"])
        if code == 0:
            for line in out.splitlines():
                m = re.match(r'(\S+) connected (?:primary )?(\d+x\d+\+\d+\+\d+)', line)
                if m:
                    res_match = re.match(r'(\d+x\d+)', m.group(2))
                    coord_match = re.search(r'\+(\d+)\+(\d+)', m.group(2))
                    monitors.append({
                        "name": m.group(1),
                        "resolution": res_match.group(1) if res_match else "unknown",
                        "x": int(coord_match.group(1)) if coord_match else 0,
                        "y": int(coord_match.group(2)) if coord_match else 0,
                        "primary": "primary" in line,
                    })
        return monitors

    def _get_top_processes(self, n: int = 5) -> list[dict]:
        code, out, _ = _run_cmd(["ps", "axho", "pid,comm,%cpu,%mem", "--sort=-%cpu"])
        if code != 0:
            return []
        processes = []
        for line in out.splitlines()[:n]:
            parts = line.strip().split(None, 3)
            if len(parts) >= 4:
                processes.append({
                    "pid": parts[0],
                    "name": parts[1][:30],
                    "cpu": parts[2],
                    "mem": parts[3],
                })
        return processes

    def update(self) -> dict:
        now = time.time()
        if now - self._last_update < self._cache_ttl:
            return dict(self._state)

        active_window = self._get_active_window()
        active_app = self._get_active_app()
        workspace_id, workspace_count = self._get_workspace_info()
        battery = self._get_battery()
        network = self._get_network()
        media = self._get_media()
        monitors = self._get_monitors()
        top_processes = self._get_top_processes()

        self._state = {
            "active_window": active_window,
            "active_app": active_app,
            "workspace": workspace_id,
            "workspace_count": workspace_count,
            "processes": top_processes,
            "battery": battery,
            "network": network,
            "media": media,
            "monitors": monitors,
            "cpu_percent": float(top_processes[0]["cpu"]) if top_processes else 0.0,
            "memory_percent": float(top_processes[0]["mem"]) if top_processes else 0.0,
        }
        self._last_update = now
        events.emit(EventType.DESKTOP_STATE_CHANGED, self._state)
        return dict(self._state)

    def get_state(self) -> dict:
        return self.update()

    def get_active_window(self) -> str:
        return self._state["active_window"]

    def get_active_app(self) -> str:
        return self._state["active_app"]

    def get_workspace(self) -> str:
        return self._state["workspace"]

    def get_battery(self) -> dict:
        return dict(self._state["battery"])

    def get_network(self) -> dict:
        return dict(self._state["network"])

    def get_media(self) -> dict:
        return dict(self._state["media"])

    def get_monitors(self) -> list[dict]:
        return list(self._state["monitors"])

    def get_top_processes(self, n: int = 5) -> list[dict]:
        return self._state["processes"][:n]

    def _poll_loop(self):
        while self._running:
            self.update()
            time.sleep(self._update_interval)

    def start_background_polling(self, interval: float = 2.0):
        if self._thread and self._thread.is_alive():
            return
        self._update_interval = interval
        self._running = True
        self._thread = Thread(target=self._poll_loop, name="desktop-state", daemon=True)
        self._thread.start()
        log.info("Desktop state polling started")

    def stop_background_polling(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        log.info("Desktop state polling stopped")

    def describe_state(self) -> str:
        state = self.get_state()
        lines = []

        app = state.get("active_app", "")
        window = state.get("active_window", "")
        if app:
            lines.append(f"Active app: {app}")
        if window:
            lines.append(f"Window: {window}")

        ws = state.get("workspace", "")
        ws_count = state.get("workspace_count", 0)
        if ws:
            lines.append(f"Workspace: {ws} (of {ws_count})")

        bat = state.get("battery", {})
        if bat.get("percent") is not None:
            status = "charging" if bat.get("charging") else "discharging"
            lines.append(f"Battery: {bat['percent']}% ({status})")

        net = state.get("network", {})
        if net.get("connected"):
            ssid = net.get("ssid", "")
            lines.append(f"Network: connected to {ssid}" if ssid else "Network: connected")
        else:
            lines.append("Network: disconnected")

        media = state.get("media", {})
        if media.get("playing"):
            title = media.get("title", "?")
            artist = media.get("artist", "?")
            app_name = media.get("app", "?")
            lines.append(f"Playing: {title} - {artist} ({app_name})")

        monitors = state.get("monitors", [])
        if monitors:
            active_mons = [m["name"] for m in monitors]
            lines.append(f"Displays: {', '.join(active_mons)}")

        procs = state.get("processes", [])
        if procs:
            top = ", ".join(f"{p['name']} ({p['cpu']}%)" for p in procs[:3])
            lines.append(f"Top CPU: {top}")

        return "\n".join(lines) if lines else "No desktop state available"

    def pause_media(self) -> bool:
        if not self._has_playerctl:
            return False
        code, _, _ = _run_cmd(["playerctl", "pause"])
        return code == 0

    def play_media(self) -> bool:
        if not self._has_playerctl:
            return False
        code, _, _ = _run_cmd(["playerctl", "play"])
        return code == 0

    def next_track(self) -> bool:
        if not self._has_playerctl:
            return False
        code, _, _ = _run_cmd(["playerctl", "next"])
        return code == 0

    def previous_track(self) -> bool:
        if not self._has_playerctl:
            return False
        code, _, _ = _run_cmd(["playerctl", "previous"])
        return code == 0

    def is_available(self) -> bool:
        return self._has_wmctrl or self._has_xdotool

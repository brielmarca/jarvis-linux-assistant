import json
import shlex
import subprocess
from typing import Any

from jarvis.automation.linux import run_cmd
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


_ACTIVE_WM: str | None = None


def detect_wm() -> str:
    global _ACTIVE_WM
    if _ACTIVE_WM:
        return _ACTIVE_WM

    code, out, _ = run_cmd(["bash", "-c", 'echo "$XDG_CURRENT_DESKTOP"'], timeout=3)
    if out and out.strip():
        _ACTIVE_WM = out.strip().lower()
        return _ACTIVE_WM

    code, out, _ = run_cmd(["bash", "-c", 'echo "$DESKTOP_SESSION"'], timeout=3)
    if out and out.strip():
        _ACTIVE_WM = out.strip().lower()
        return _ACTIVE_WM

    if _has_cmd("hyprctl"):
        _ACTIVE_WM = "hyprland"
        return _ACTIVE_WM
    if _has_cmd("i3-msg"):
        _ACTIVE_WM = "i3"
        return _ACTIVE_WM
    if _has_cmd("swaymsg"):
        _ACTIVE_WM = "sway"
        return _ACTIVE_WM
    if _has_cmd("wmctrl"):
        _ACTIVE_WM = "x11"
        return _ACTIVE_WM

    _ACTIVE_WM = "unknown"
    return _ACTIVE_WM


def _has_cmd(cmd: str) -> bool:
    code, _, _ = run_cmd(["which", cmd], timeout=3)
    return code == 0


def _hyprctl(args: list[str]) -> tuple[int, str, str]:
    return run_cmd(["hyprctl"] + args, timeout=5)


def _i3_msg(args: list[str]) -> tuple[int, str, str]:
    cmd = "swaymsg" if _ACTIVE_WM == "sway" else "i3-msg"
    return run_cmd([cmd] + args, timeout=5)


def get_wm_info() -> str:
    wm = detect_wm()
    info = [f"Window Manager: {wm}"]
    if wm == "hyprland":
        code, out, _ = _hyprctl(["version"])
        if out:
            info.append(f"Version: {out.strip()[:80]}")
    elif wm == "i3":
        code, out, _ = _i3_msg(["-t", "get_version"])
        if out:
            try:
                v = json.loads(out)
                info.append(f"Version: {v.get('human_readable', 'unknown')}")
            except json.JSONDecodeError:
                info.append(f"Version: {out.strip()[:80]}")
    return "\n".join(info)


def get_workspaces() -> str:
    wm = detect_wm()
    try:
        if wm == "hyprland":
            return _hyprland_workspaces()
        elif wm in ("i3", "sway"):
            return _i3_workspaces()
        else:
            return _x11_workspaces()
    except Exception as e:
        return f"Error getting workspaces: {e}"


def _hyprland_workspaces() -> str:
    code, out, _ = _hyprctl(["workspaces"])
    code2, active_out, _ = _hyprctl(["activeworkspace"])
    active_id = ""
    if code2 == 0:
        for line in active_out.split("\n"):
            if "workspace ID" in line.lower():
                parts = line.split(":")
                if len(parts) >= 2:
                    active_id = parts[1].strip()
                    break
    lines = []
    for line in out.strip().split("\n"):
        if "Workspace" in line or "ID" in line:
            marker = "◉" if active_id and active_id in line else "○"
            lines.append(f"  {marker} {line.strip()}")
    return "\n".join(lines[:15]) if lines else "No workspaces found"


def _i3_workspaces() -> str:
    code, out, _ = _i3_msg(["-t", "get_workspaces"])
    if code != 0 or not out:
        return "No workspace info available"
    try:
        workspaces = json.loads(out)
        lines = []
        for ws in workspaces:
            name = ws.get("name", "?")
            focused = ws.get("focused", False)
            marker = "◉" if focused else "○"
            lines.append(f"  {marker} {name} (output: {ws.get('output', '?')})")
        return "\n".join(lines[:15])
    except json.JSONDecodeError:
        return out.strip()[:500]


def _x11_workspaces() -> str:
    code, out, _ = run_cmd(["wmctrl", "-d"], timeout=5)
    if code == 0 and out:
        lines = []
        for line in out.strip().split("\n"):
            parts = line.split(None, 4)
            if len(parts) >= 2:
                is_active = parts[1] == "*" if len(parts) > 1 else False
                marker = "◉" if is_active else "○"
                name = parts[-1] if len(parts) > 4 else parts[0]
                lines.append(f"  {marker} {name}")
        return "\n".join(lines[:15])
    return "No workspaces found"


def switch_workspace(num: int) -> str:
    wm = detect_wm()
    try:
        if wm == "hyprland":
            code, _, err = _hyprctl(["dispatch", "workspace", str(num)])
            if code == 0:
                return f"Switched to workspace {num}"
            return f"Failed: {err[:100]}"
        elif wm in ("i3", "sway"):
            code, _, err = _i3_msg([f"workspace number {num}"])
            if code == 0:
                return f"Switched to workspace {num}"
            return f"Failed: {err[:100]}"
        else:
            code, _, err = run_cmd(["wmctrl", "-s", str(num)], timeout=5)
            if code == 0:
                return f"Switched to workspace {num}"
            return f"Failed: {err[:100]}"
    except Exception as e:
        return f"Error switching workspace: {e}"


def move_window_to_workspace(workspace_num: int) -> str:
    wm = detect_wm()
    try:
        if wm == "hyprland":
            code, _, err = _hyprctl(["dispatch", "movetoworkspace", str(workspace_num)])
            if code == 0:
                return f"Moved window to workspace {workspace_num}"
            return f"Failed: {err[:100]}"
        elif wm in ("i3", "sway"):
            code, _, err = _i3_msg([f"move container to workspace number {workspace_num}"])
            if code == 0:
                return f"Moved window to workspace {workspace_num}"
            return f"Failed: {err[:100]}"
        return "Move window not supported on this WM"
    except Exception as e:
        return f"Error moving window: {e}"


def focus_window(title_fragment: str) -> str:
    wm = detect_wm()
    try:
        if wm == "hyprland":
            code, out, _ = _hyprctl(["clients"])
            if code == 0:
                for line in out.split("\n"):
                    if title_fragment.lower() in line.lower():
                        parts = line.strip().split()
                        if parts and "address" not in line.lower():
                            addr = parts[-1].strip(":")
                            _hyprctl(["dispatch", "focuswindow", f"address:{addr}"])
                            return f"Focused window: {title_fragment}"
                return f"Window '{title_fragment}' not found"
        elif wm in ("i3", "sway"):
            code, _, _ = _i3_msg([f"[title=\"{title_fragment}\"] focus"])
            if code == 0:
                return f"Focused window: {title_fragment}"
            return f"Window '{title_fragment}' not found"
        else:
            code, out, _ = run_cmd(["wmctrl", "-l"], timeout=5)
            if code == 0:
                for line in out.strip().split("\n"):
                    if title_fragment.lower() in line.lower():
                        wid = line.split(None, 1)[0]
                        run_cmd(["wmctrl", "-ia", wid], timeout=3)
                        return f"Focused window: {title_fragment}"
                return f"Window '{title_fragment}' not found"
            return "Cannot list windows"
    except Exception as e:
        return f"Error focusing window: {e}"


def launch_on_workspace(command: str, workspace_num: int) -> str:
    wm = detect_wm()
    try:
        if wm == "hyprland":
            _hyprctl(["dispatch", "workspace", str(workspace_num)])
            subprocess.Popen(shlex.split(command), start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Launched '{command}' on workspace {workspace_num}"
        elif wm in ("i3", "sway"):
            cmd_parts = shlex.split(command)
            _i3_msg([f"workspace number {workspace_num}"])
            subprocess.Popen(cmd_parts, start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Launched '{command}' on workspace {workspace_num}"
        else:
            app = command.split()[0] if " " not in command else command
            subprocess.Popen(shlex.split(command), start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Launched '{command}'"
    except Exception as e:
        return f"Error launching on workspace: {e}"


def move_window(direction: str) -> str:
    wm = detect_wm()
    valid = ("up", "down", "left", "right", "u", "d", "l", "r")
    if direction.lower() not in valid:
        return f"Invalid direction: {direction}. Use up/down/left/right"
    try:
        if wm == "hyprland":
            dirmap = {"u": "up", "d": "down", "l": "left", "r": "right"}
            d = dirmap.get(direction.lower(), direction.lower())
            code, _, err = _hyprctl(["dispatch", "movewindow", d])
            if code == 0:
                return f"Moved window {d}"
            return f"Failed: {err[:100]}"
        elif wm in ("i3", "sway"):
            dirmap = {"u": "left", "d": "down", "l": "left", "r": "right"}
            d = dirmap.get(direction.lower(), direction.lower())
            code, _, err = _i3_msg([f"move {d}"])
            if code == 0:
                return f"Moved window {d}"
            return f"Failed: {err[:100]}"
        return "Move window not supported on this WM"
    except Exception as e:
        return f"Error moving window: {e}"


def resize_window(direction: str, pixels: int = 50) -> str:
    wm = detect_wm()
    valid = ("up", "down", "left", "right", "u", "d", "l", "r")
    if direction.lower() not in valid:
        return f"Invalid direction: {direction}"
    try:
        if wm == "hyprland":
            dirmap = {"u": "u", "d": "d", "l": "l", "r": "r"}
            d = dirmap.get(direction.lower(), direction.lower()[0])
            code, _, err = _hyprctl(["dispatch", "resizeactive", f"{pixels}{d}"])
            if code == 0:
                return f"Resized window {direction} by {pixels}px"
            return f"Failed: {err[:100]}"
        elif wm in ("i3", "sway"):
            dirmap = {"up": "shrink height", "down": "grow height",
                      "left": "shrink width", "right": "grow width"}
            d = dirmap.get(direction.lower(), "")
            if not d:
                return f"Invalid direction: {direction}"
            code, _, err = _i3_msg([f"resize {d} {pixels} px"])
            if code == 0:
                return f"Resized window {direction} by {pixels}px"
            return f"Failed: {err[:100]}"
        return "Resize not supported on this WM"
    except Exception as e:
        return f"Error resizing window: {e}"


def get_active_window() -> str:
    wm = detect_wm()
    try:
        if wm == "hyprland":
            code, out, _ = _hyprctl(["activewindow"])
            if code == 0:
                return out.strip()[:300]
            return "No active window info"
        elif wm in ("i3", "sway"):
            code, out, _ = _i3_msg(["-t", "get_tree"])
            if code == 0:
                try:
                    tree = json.loads(out)
                    focused = _find_focused(tree)
                    if focused:
                        return f"Active: {focused.get('name', 'unknown')}"
                except json.JSONDecodeError:
                    pass
            return "No active window info"
        else:
            code, out, _ = run_cmd(["xdotool", "getactivewindow", "getwindowname"], timeout=3)
            if code == 0 and out:
                return f"Active: {out.strip()[:200]}"
            return "No active window info"
    except Exception as e:
        return f"Error: {e}"


def _find_focused(node: dict) -> dict | None:
    if node.get("focused"):
        return node
    for child in node.get("nodes", []):
        result = _find_focused(child)
        if result:
            return result
    for child in node.get("floating_nodes", []):
        result = _find_focused(child)
        if result:
            return result
    return None


def get_windows() -> str:
    wm = detect_wm()
    try:
        if wm == "hyprland":
            code, out, _ = _hyprctl(["clients"])
            if code == 0:
                windows = [l.strip() for l in out.split("\n") if l and "Window" not in l and "————" not in l]
                lines = ["Open windows:"]
                for w in windows[:15]:
                    lines.append(f"  {w}")
                return "\n".join(lines)
        else:
            code, out, _ = run_cmd(["wmctrl", "-l"], timeout=5)
            if code == 0:
                windows = [l for l in out.strip().split("\n") if l][:15]
                if windows:
                    result = ["Open windows:"]
                    for w in windows:
                        parts = w.split(None, 3)
                        if len(parts) >= 4:
                            result.append(f"  {parts[3]}")
                    return "\n".join(result)
        return "No open windows found"
    except Exception as e:
        return f"Error listing windows: {e}"

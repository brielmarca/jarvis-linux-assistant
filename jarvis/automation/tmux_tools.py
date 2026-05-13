from jarvis.automation.linux import run_cmd
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


def tmux_list_sessions() -> str:
    code, out, err = run_cmd(["tmux", "list-sessions"], timeout=5)
    if code == 0:
        sessions = [s for s in out.strip().split("\n") if s]
        if sessions:
            return "\n".join(sessions[:10])
        return "No tmux sessions"
    return "tmux not available"


def tmux_new_session(name: str | None = None) -> str:
    cmd = ["tmux", "new-session", "-d"]
    if name:
        cmd.extend(["-s", name])
    code, out, err = run_cmd(cmd, timeout=5)
    if code == 0:
        sname = name or "default"
        return f"Created tmux session: {sname}"
    return f"Failed: {err[:100]}"


def tmux_attach(session: str | None = None) -> str:
    cmd = ["tmux", "attach-session"]
    if session:
        cmd.extend(["-t", session])
    code, out, err = run_cmd(cmd, timeout=5)
    if code == 0:
        return f"Attached to session {session or 'default'}"
    return f"Failed: {err[:100]}"


def tmux_kill_session(session: str) -> str:
    code, out, err = run_cmd(["tmux", "kill-session", "-t", session], timeout=5)
    if code == 0:
        return f"Killed tmux session: {session}"
    return f"Failed: {err[:100]}"


def tmux_send_command(session: str, command: str, pane: int = 0) -> str:
    code, out, err = run_cmd(
        ["tmux", "send-keys", "-t", f"{session}:{pane}", command, "Enter"],
        timeout=5,
    )
    if code == 0:
        return f"Sent command to tmux {session}:{pane}"
    return f"Failed: {err[:100]}"


def tmux_list_windows(session: str) -> str:
    code, out, err = run_cmd(["tmux", "list-windows", "-t", session], timeout=5)
    if code == 0:
        return out.strip()[:500]
    return f"Failed: {err[:100]}"


def is_tmux_available() -> bool:
    code, _, _ = run_cmd(["which", "tmux"], timeout=3)
    return code == 0

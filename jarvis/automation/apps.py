import subprocess

from jarvis.core.logger import JarvisLogger
from jarvis.automation.linux import run_cmd


log = JarvisLogger()


APP_COMMANDS = {
    "vscode": ["code"],
    "visual studio code": ["code"],
    "code": ["code"],
    "firefox": ["firefox"],
    "browser": ["firefox"],
    "terminal": ["x-terminal-emulator", "gnome-terminal", "konsole", "xterm"],
    "file manager": ["nautilus", "dolphin", "thunar", "pcmanfm"],
    "nautilus": ["nautilus"],
    "dolphin": ["dolphin"],
    "files": ["nautilus"],
    "discord": ["discord"],
    "spotify": ["spotify"],
    "slack": ["slack"],
    "docker": ["docker", "ps"],
}


def launch_app(app_name: str) -> str:
    app_name = app_name.lower().strip()

    if app_name in APP_COMMANDS:
        commands = APP_COMMANDS[app_name]
        for cmd in commands:
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                log.info(f"Launched: {app_name} ({cmd})")
                return f"Launched {app_name}"
            except FileNotFoundError:
                continue
        return f"Could not find {app_name}. Is it installed?"

    try:
        subprocess.Popen([app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.info(f"Launched: {app_name}")
        return f"Launched {app_name}"
    except FileNotFoundError:
        return f"Application '{app_name}' not found"


def open_project_folder(path: str) -> str:
    import os
    if os.path.isdir(path):
        try:
            subprocess.Popen(["code", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log.info(f"Opened project in VS Code: {path}")
            return f"Opened {path} in VS Code"
        except FileNotFoundError:
            try:
                subprocess.Popen(["nautilus", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Opened {path} in file manager"
            except FileNotFoundError:
                return f"Could not open {path}"
    return f"Path not found: {path}"


def get_running_apps() -> list:
    _, output, _ = run_cmd(["bash", "-c", "wmctrl -l | awk '{$1=$2=$3=\"\"; print $0}' | sed 's/^ *//'"])
    if output:
        return [line.strip() for line in output.split("\n") if line.strip()]
    return []


def close_app(app_name: str) -> str:
    _, output, _ = run_cmd(["bash", "-c", f"wmctrl -c '{app_name}'"])
    log.info(f"Closed: {app_name}")
    return f"Closed {app_name}"


def check_docker() -> str:
    code, out, err = run_cmd(["docker", "info", "--format", "{{.ServerVersion}}"])
    if code == 0:
        return f"Docker is running (version: {out})"
    return "Docker is not running. Start it with 'sudo systemctl start docker'"

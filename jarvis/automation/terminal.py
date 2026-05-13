import subprocess

from jarvis.automation.linux import run_cmd
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


def open_terminal(command: str = None) -> str:
    terminal_cmds = ["x-terminal-emulator", "gnome-terminal", "konsole", "xterm"]

    for term in terminal_cmds:
        try:
            if command:
                subprocess.Popen([term, "--", "bash", "-c", command],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen([term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log.info(f"Terminal opened: {term}")
            return "Terminal opened"
        except FileNotFoundError:
            continue
    return "No terminal emulator found"


def run_in_terminal(command: str) -> str:
    return open_terminal(command)


def execute_command(command: str) -> dict:
    log.info(f"Executing: {command}")
    code, stdout, stderr = run_cmd(["bash", "-c", command], timeout=30)
    return {
        "returncode": code,
        "stdout": stdout,
        "stderr": stderr,
        "success": code == 0,
    }

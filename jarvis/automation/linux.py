import subprocess
from datetime import datetime

from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


def run_cmd(cmd: list, timeout: int = 10) -> tuple:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except FileNotFoundError:
        return -1, "", "Command not found"
    except Exception as e:
        return -1, "", str(e)


def get_current_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


def get_current_date() -> str:
    return datetime.now().strftime("%A, %d %B %Y")


def get_system_info() -> dict:
    info = {}

    _, hostname, _ = run_cmd(["uname", "-n"])
    info["hostname"] = hostname

    _, kernel, _ = run_cmd(["uname", "-r"])
    info["kernel"] = kernel

    _, cpu, _ = run_cmd(["bash", "-c", "lscpu | grep 'Model name' | cut -d: -f2 | xargs"])
    info["cpu"] = cpu or "N/A"

    _, mem, _ = run_cmd(["bash", "-c", "free -h | grep Mem | awk '{print $3\"/\"$2}'"])
    info["memory"] = mem or "N/A"

    _, disk, _ = run_cmd(["bash", "-c", "df -h / | tail -1 | awk '{print $3\"/\"$2}'"])
    info["disk"] = disk or "N/A"

    _, uptime, _ = run_cmd(["bash", "-c", "uptime -p | sed 's/up //'"])
    info["uptime"] = uptime or "N/A"

    return info


def shutdown():
    log.warning("Shutdown requested")
    return run_cmd(["shutdown", "-h", "+1"])


def reboot():
    log.warning("Reboot requested")
    return run_cmd(["shutdown", "-r", "+1"])


def get_os_info() -> str:
    _, os_info, _ = run_cmd(["bash", "-c", "cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"'"])
    return os_info or "Linux"

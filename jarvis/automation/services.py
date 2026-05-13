from jarvis.automation.linux import run_cmd
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


def service_status(service: str) -> str:
    code, out, err = run_cmd(["systemctl", "status", service, "--no-pager", "-l"], timeout=10)
    if code == 0:
        return f"{service}: running"
    if code == 3:
        return f"{service}: inactive (stopped)"
    if code == 4:
        return f"{service}: not found"
    return f"{service}: {err[:100] or 'unknown state'}"


def service_start(service: str) -> str:
    log.warning(f"Starting service: {service}")
    code, out, err = run_cmd(["systemctl", "start", service], timeout=15)
    if code == 0:
        return f"Service {service} started"
    return f"Failed to start {service}: {err[:100]}"


def service_stop(service: str) -> str:
    log.warning(f"Stopping service: {service}")
    code, out, err = run_cmd(["systemctl", "stop", service], timeout=15)
    if code == 0:
        return f"Service {service} stopped"
    return f"Failed to stop {service}: {err[:100]}"


def service_restart(service: str) -> str:
    log.warning(f"Restarting service: {service}")
    code, out, err = run_cmd(["systemctl", "restart", service], timeout=15)
    if code == 0:
        return f"Service {service} restarted"
    return f"Failed to restart {service}: {err[:100]}"


def service_enable(service: str) -> str:
    code, out, err = run_cmd(["systemctl", "enable", service], timeout=10)
    if code == 0:
        return f"Service {service} enabled on boot"
    return f"Failed to enable {service}: {err[:100]}"


def service_disable(service: str) -> str:
    code, out, err = run_cmd(["systemctl", "disable", service], timeout=10)
    if code == 0:
        return f"Service {service} disabled on boot"
    return f"Failed to disable {service}: {err[:100]}"


def list_services(filter_str: str = "") -> str:
    cmd = ["systemctl", "list-units", "--type=service", "--no-pager"]
    if filter_str:
        cmd.extend(["--state", filter_str])
    code, out, err = run_cmd(cmd, timeout=10)
    if code == 0:
        lines = out.split("\n")[:30]
        return "\n".join(lines)
    return f"Failed to list services: {err[:100]}"


def is_systemctl_available() -> bool:
    code, _, _ = run_cmd(["which", "systemctl"], timeout=3)
    return code == 0

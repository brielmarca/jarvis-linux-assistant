from jarvis.automation.linux import run_cmd
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


def docker_status() -> str:
    code, out, err = run_cmd(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=10)
    if code == 0:
        return f"Docker is running (version: {out})"
    return "Docker is not running. Start with: sudo systemctl start docker"


def docker_ps(all_containers: bool = False) -> str:
    cmd = ["docker", "ps", "-a"] if all_containers else ["docker", "ps"]
    code, out, err = run_cmd(cmd, timeout=10)
    if code == 0:
        return out.strip()[:1000] or "No containers running"
    return f"Docker error: {err[:100]}"


def docker_compose_up(path: str | None = None) -> str:
    cwd = path or "."
    code, out, err = run_cmd(["docker", "compose", "up", "-d"], timeout=60)
    if code == 0:
        return "Docker Compose started"
    return f"Docker Compose failed: {err[:200]}"


def docker_compose_down(path: str | None = None) -> str:
    code, out, err = run_cmd(["docker", "compose", "down"], timeout=30)
    if code == 0:
        return "Docker Compose stopped"
    return f"Docker Compose down failed: {err[:100]}"


def docker_images() -> str:
    code, out, err = run_cmd(["docker", "images", "--format", "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"], timeout=10)
    if code == 0:
        return out.strip()[:1000] or "No images found"
    return f"Docker error: {err[:100]}"


def docker_pull(image: str) -> str:
    code, out, err = run_cmd(["docker", "pull", image], timeout=120)
    if code == 0:
        return f"Pulled {image}"
    return f"Failed to pull {image}: {err[:100]}"


def docker_stop(container: str) -> str:
    code, out, err = run_cmd(["docker", "stop", container], timeout=15)
    if code == 0:
        return f"Container {container} stopped"
    return f"Failed: {err[:100]}"


def docker_logs(container: str, lines: int = 20) -> str:
    code, out, err = run_cmd(["docker", "logs", "--tail", str(lines), container], timeout=10)
    if code == 0:
        return out.strip()[:2000]
    return f"Failed: {err[:100]}"


def is_docker_available() -> bool:
    code, _, _ = run_cmd(["which", "docker"], timeout=3)
    return code == 0

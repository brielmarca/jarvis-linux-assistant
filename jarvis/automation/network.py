from jarvis.automation.linux import run_cmd
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


def wifi_status() -> str:
    code, out, err = run_cmd(["nmcli", "-t", "-f", "NAME,SIGNAL,SECURITY", "device", "wifi", "list", "--rescan", "no"], timeout=10)
    if code != 0:
        code, out, err = run_cmd(["nmcli", "radio", "wifi"], timeout=5)
        if code == 0:
            return f"Wi-Fi radio: {out.strip()}"
        return "nmcli not available. Install network-manager."
    connections = [l for l in out.strip().split("\n") if l][:10]
    if not connections:
        return "No Wi-Fi networks found (scan with 'scan for networks')"
    result = ["Available networks:"]
    for conn in connections:
        parts = conn.split(":")
        if len(parts) >= 2:
            name, signal = parts[0], parts[1]
            bars = "█" * (int(signal) // 20) if signal.isdigit() else "?"
            result.append(f"  {bars} {signal}%  {name}")
    return "\n".join(result)


def wifi_connect(ssid: str, password: str | None = None) -> str:
    if password:
        code, out, err = run_cmd(["nmcli", "device", "wifi", "connect", ssid, "password", password], timeout=20)
    else:
        code, out, err = run_cmd(["nmcli", "device", "wifi", "connect", ssid], timeout=20)
    if code == 0:
        return f"Connected to {ssid}"
    return f"Failed to connect to {ssid}: {err[:100]}"


def wifi_disconnect() -> str:
    code, out, err = run_cmd(["nmcli", "device", "disconnect", "wlan0"], timeout=10)
    if code == 0:
        return "Disconnected from Wi-Fi"
    code, out, err = run_cmd(["nmcli", "radio", "wifi", "off"], timeout=5)
    if code == 0:
        return "Wi-Fi turned off"
    return f"Failed to disconnect: {err[:100]}"


def wifi_scan() -> str:
    code, out, err = run_cmd(["nmcli", "device", "wifi", "list"], timeout=15)
    if code == 0:
        lines = out.strip().split("\n")
        if len(lines) <= 1:
            return "No networks found"
        return "\n".join(lines[:15])
    return f"Scan failed: {err[:100]}"


def network_status() -> str:
    lines = []
    code, out, _ = run_cmd(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device", "status"], timeout=5)
    if code == 0:
        lines.append("Network devices:")
        for l in out.strip().split("\n")[:5]:
            if l:
                lines.append(f"  {l.replace(':', ': ')}")
    else:
        lines.append("nmcli not available")
    code, out, _ = run_cmd(["ip", "-br", "addr", "show"], timeout=5)
    if code == 0:
        lines.append("\nIP addresses:")
        for l in out.strip().split("\n")[:5]:
            if l:
                lines.append(f"  {l}")
    return "\n".join(lines)


def is_nmcli_available() -> bool:
    code, _, _ = run_cmd(["which", "nmcli"], timeout=3)
    return code == 0

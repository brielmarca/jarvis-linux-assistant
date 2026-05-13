from jarvis.automation.linux import run_cmd
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


def bluetooth_status() -> str:
    code, out, err = run_cmd(["bluetoothctl", "show"], timeout=5)
    if code == 0:
        powered = "Powered: yes" if "Powered: yes" in out else "Powered: no"
        discovering = "Discovering: yes" if "Discovering: yes" in out else ""
        return f"Bluetooth: {powered}"
    return "bluetoothctl not available. Install bluez."


def bluetooth_on() -> str:
    code, out, err = run_cmd(["bluetoothctl", "power", "on"], timeout=5)
    if code == 0:
        return "Bluetooth turned on"
    return f"Failed: {err[:100]}"


def bluetooth_off() -> str:
    code, out, err = run_cmd(["bluetoothctl", "power", "off"], timeout=5)
    if code == 0:
        return "Bluetooth turned off"
    return f"Failed: {err[:100]}"


def bluetooth_scan(duration: int = 5) -> str:
    code, out, err = run_cmd(["bluetoothctl", "scan", "on"], timeout=duration + 2)
    code2, out2, _ = run_cmd(["bluetoothctl", "devices"], timeout=3)
    if code2 == 0:
        devices = [l for l in out2.strip().split("\n") if l]
        if devices:
            result = ["Discovered devices:"]
            for d in devices[:10]:
                parts = d.split(" ", 2)
                if len(parts) >= 3:
                    result.append(f"  {parts[1]} - {parts[2]}")
            return "\n".join(result)
    return "No devices found"


def bluetooth_pair(device_mac: str) -> str:
    code, out, err = run_cmd(["bluetoothctl", "pair", device_mac], timeout=15)
    if code == 0:
        return f"Paired with {device_mac}"
    return f"Failed to pair: {err[:100]}"


def bluetooth_connect(device_mac: str) -> str:
    code, out, err = run_cmd(["bluetoothctl", "connect", device_mac], timeout=15)
    if code == 0:
        return f"Connected to {device_mac}"
    return f"Failed to connect: {err[:100]}"


def bluetooth_disconnect(device_mac: str) -> str:
    code, out, err = run_cmd(["bluetoothctl", "disconnect", device_mac], timeout=10)
    if code == 0:
        return f"Disconnected from {device_mac}"
    return f"Failed to disconnect: {err[:100]}"


def bluetooth_devices() -> str:
    code, out, _ = run_cmd(["bluetoothctl", "devices"], timeout=3)
    if code == 0:
        devices = [l for l in out.strip().split("\n") if l]
        if devices:
            result = ["Paired devices:"]
            for d in devices:
                parts = d.split(" ", 2)
                if len(parts) >= 3:
                    result.append(f"  {parts[1]} - {parts[2]}")
            return "\n".join(result)
        return "No paired devices"
    return "bluetoothctl not available"


def is_bluetoothctl_available() -> bool:
    code, _, _ = run_cmd(["which", "bluetoothctl"], timeout=3)
    return code == 0

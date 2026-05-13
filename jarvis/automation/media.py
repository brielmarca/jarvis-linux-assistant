from jarvis.automation.linux import run_cmd
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


def volume_up(amount: int = 5) -> str:
    code, _, err = run_cmd(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"+{amount}%"])
    if code == 0:
        return f"Volume increased by {amount}%"
    log.error(f"Volume up failed: {err}")
    return "Failed to increase volume"


def volume_down(amount: int = 5) -> str:
    code, _, err = run_cmd(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"-{amount}%"])
    if code == 0:
        return f"Volume decreased by {amount}%"
    log.error(f"Volume down failed: {err}")
    return "Failed to decrease volume"


def volume_set(percent: int) -> str:
    code, _, err = run_cmd(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{percent}%"])
    if code == 0:
        return f"Volume set to {percent}%"
    log.error(f"Volume set failed: {err}")
    return "Failed to set volume"


def volume_mute() -> str:
    code, _, err = run_cmd(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])
    if code == 0:
        return "Volume toggled mute/unmute"
    log.error(f"Mute toggle failed: {err}")
    return "Failed to toggle mute"


def volume_get() -> int:
    code, out, _ = run_cmd(["bash", "-c", "pactl get-sink-volume @DEFAULT_SINK@ | awk '{print $5}' | head -1"])
    if code == 0 and out:
        try:
            return int(out.replace("%", ""))
        except ValueError:
            pass
    return 0


def media_play_pause() -> str:
    code, _, err = run_cmd(["playerctl", "play-pause"])
    if code == 0:
        return "Toggled play/pause"
    log.error(f"Media play/pause failed: {err}")
    return "No media player found"


def media_next() -> str:
    code, _, err = run_cmd(["playerctl", "next"])
    if code == 0:
        return "Skipped to next track"
    log.error(f"Media next failed: {err}")
    return "No media player found"


def media_previous() -> str:
    code, _, err = run_cmd(["playerctl", "previous"])
    if code == 0:
        return "Went to previous track"
    log.error(f"Media previous failed: {err}")
    return "No media player found"


def media_stop() -> str:
    code, _, err = run_cmd(["playerctl", "stop"])
    if code == 0:
        return "Playback stopped"
    log.error(f"Media stop failed: {err}")
    return "No media player found"


def get_media_status() -> str:
    code, out, _ = run_cmd(["playerctl", "metadata", "--format", "{{artist}} - {{title}}"])
    if code == 0 and out:
        return f"Now playing: {out}"
    return "No media playing"

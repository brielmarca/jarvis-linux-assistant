import re
from typing import Any

from jarvis.agents.base_agent import BaseAgent
from jarvis.automation import media as media_auto
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class MediaAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="media", description="Volume and media playback control")

    def can_handle(self, command: str, context: dict | None = None) -> tuple[bool, float]:
        cmd = command.lower()
        if any(kw in cmd for kw in ["volume", "som", "aumenta", "diminui", "sobe", "baixa",
                                     "mute", "unmute", "silencia", "play", "pause", "tocar",
                                     "pausar", "next", "próximo", "skip", "previous", "anterior",
                                     "stop", "parar", "now playing", "tocando", "current track",
                                     "playerctl", "music", "música", "spotify"]):
            return True, 0.9
        return False, 0.0

    def execute(self, command: str, context: dict | None = None) -> dict[str, Any]:
        cmd = command.lower()

        if "increase" in cmd or "aumenta" in cmd or "sobe" in cmd or "raise" in cmd:
            return {"response": media_auto.volume_up(), "agent": "media"}
        if "decrease" in cmd or "diminui" in cmd or "baixa" in cmd or "lower" in cmd or "reduce" in cmd:
            return {"response": media_auto.volume_down(), "agent": "media"}
        if "set" in cmd or "muda" in cmd or "define" in cmd:
            nums = re.findall(r'\d+', cmd)
            if nums:
                return {"response": media_auto.volume_set(int(nums[0])), "agent": "media"}
            return {"response": f"Current volume: {media_auto.volume_get()}%", "agent": "media"}
        if "mute" in cmd or "silencia" in cmd or "mutar" in cmd or "mudo" in cmd:
            return {"response": media_auto.volume_mute(), "agent": "media"}
        if "unmute" in cmd or "ativar som" in cmd:
            return {"response": media_auto.volume_set(50), "agent": "media"}
        if "play" in cmd or "pause" in cmd or "tocar" in cmd or "pausar" in cmd:
            return {"response": media_auto.media_play_pause(), "agent": "media"}
        if "next" in cmd or "próxim" in cmd or "skip" in cmd or "pular" in cmd:
            return {"response": media_auto.media_next(), "agent": "media"}
        if "previous" in cmd or "anterior" in cmd or "voltar" in cmd:
            return {"response": media_auto.media_previous(), "agent": "media"}
        if "stop" in cmd or "parar" in cmd:
            return {"response": media_auto.media_stop(), "agent": "media"}
        if "now playing" in cmd or "tocando" in cmd or "current track" in cmd or "what's playing" in cmd:
            return {"response": media_auto.get_media_status(), "agent": "media"}

        return {"response": "Media command not recognized", "agent": "media"}

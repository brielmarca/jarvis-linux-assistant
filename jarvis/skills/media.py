from jarvis.skills.base import BaseSkill
from jarvis.automation import media as media_auto
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class MediaSkill(BaseSkill):
    def metadata(self):
        return {
            "description": "Volume control and media playback (playerctl)",
            "category": "media",
            "cooldown": 0.3,
            "timeout": 5.0,
        }

    def patterns(self):
        return [
            r"(aumenta|increase|sobe|raise)\s+(o\s+)?(volume|som)",
            r"(diminui|decrease|baixa|lower|reduce)\s+(o\s+)?(volume|som)",
            r"(muda|set|define)\s+(o\s+)?(volume|som)\s+(para|to)?\s*(\d+)",
            r"\b(mute|silencia|mutar|mudo)\b",
            r"\b(unmute|unmudo|ativar som|som on)\b",
            r"\b(play|pause|tocar|pausar)\b",
            r"\b(next|próxim[ao]|skip|pular)\b",
            r"\b(previous|anterior|voltar)\b",
            r"\b(stop|parar)\b",
            r"\b(now playing|tocando|current track|what's playing)\b",
        ]

    def execute(self, command: str, match) -> str:
        cmd_lower = command.lower()

        if "increase" in cmd_lower or "aumenta" in cmd_lower or "sobe" in cmd_lower or "raise" in cmd_lower:
            return media_auto.volume_up()

        if "decrease" in cmd_lower or "diminui" in cmd_lower or "baixa" in cmd_lower or "lower" in cmd_lower or "reduce" in cmd_lower:
            return media_auto.volume_down()

        if "set" in cmd_lower or "muda" in cmd_lower or "define" in cmd_lower:
            import re
            nums = re.findall(r'\d+', cmd_lower)
            if nums:
                return media_auto.volume_set(int(nums[0]))
            return media_auto.volume_get()

        if "mute" in cmd_lower or "silencia" in cmd_lower or "mutar" in cmd_lower or "mudo" in cmd_lower:
            return media_auto.volume_mute()

        if "unmute" in cmd_lower or "ativar som" in cmd_lower:
            return media_auto.volume_set(50)

        if "play" in cmd_lower or "pause" in cmd_lower or "tocar" in cmd_lower or "pausar" in cmd_lower:
            return media_auto.media_play_pause()

        if "next" in cmd_lower or "próxim" in cmd_lower or "skip" in cmd_lower or "pular" in cmd_lower:
            return media_auto.media_next()

        if "previous" in cmd_lower or "anterior" in cmd_lower or "voltar" in cmd_lower:
            return media_auto.media_previous()

        if "stop" in cmd_lower or "parar" in cmd_lower:
            return media_auto.media_stop()

        if "now playing" in cmd_lower or "tocando" in cmd_lower or "current track" in cmd_lower or "what's playing" in cmd_lower:
            return media_auto.get_media_status()

        return "Media command not recognized"

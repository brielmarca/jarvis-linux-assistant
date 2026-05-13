import subprocess
import tempfile
from pathlib import Path

import yaml

from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class TextToSpeech:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.config = self._load_config()
        self.available = False
        self._check_piper()

    def _load_config(self):
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        if config_path.exists():
            return yaml.safe_load(config_path.read_text()) or {}
        return {}

    def _check_piper(self):
        try:
            subprocess.run(["piper", "--help"], capture_output=True, timeout=5)
            self.available = True
            log.info("Piper TTS available")
        except Exception:
            log.warning("Piper TTS not found. Voice output will use espeak-ng or be silent.")
            self._check_espeak()

    def _check_espeak(self):
        try:
            subprocess.run(["espeak-ng", "--version"], capture_output=True, timeout=5)
            self.available = True
            log.info("espeak-ng available as fallback TTS")
        except Exception:
            self.available = False
            log.warning("No TTS system found. Install piper or espeak-ng for voice output.")

    def speak(self, text: str):
        if not self.available or not self.config.get("enable_tts", False):
            return

        lang = self.config.get("language", "pt-PT")

        try:
            subprocess.run(["piper", "--model", self.config.get("tts_model", "default")],
                          input=text.encode("utf-8"), capture_output=True, timeout=30)
            log.info(f"TTS: {text[:50]}...")
        except Exception:
            try:
                subprocess.run(["espeak-ng", "-v", lang, text], timeout=30)
                log.info(f"TTS (espeak): {text[:50]}...")
            except Exception as e:
                log.error(f"TTS failed: {e}")

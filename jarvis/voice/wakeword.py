from pathlib import Path

import yaml

from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class WakeWordDetector:
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
        self.model = None
        self.available = False
        self._load_model()

    def _load_config(self):
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        if config_path.exists():
            return yaml.safe_load(config_path.read_text()) or {}
        return {}

    def _load_model(self):
        try:
            from openwakeword import Model
            self.model = Model(
                wakeword_models=[self.config.get("wake_word_model", "hey_jarvis")]
            )
            self.available = True
            log.info("OpenWakeWord model loaded")
        except Exception as e:
            log.warning(f"OpenWakeWord not available: {e}")
            self.available = False

    def detect(self, audio_chunk):
        if not self.available or self.model is None:
            return False
        prediction = self.model.predict(audio_chunk)
        threshold = self.config.get("wake_word_sensitivity", 0.5)
        scores = self.model.prediction_scores()
        for name, score in scores.items():
            if score > threshold:
                log.info(f"Wake word detected: {name} (score: {score:.3f})")
                return True
        return False

    def is_available(self) -> bool:
        return self.available

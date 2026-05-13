from pathlib import Path
import yaml

from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


class SpeechToText:
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
        self.model_size = self.config.get("whisper_model", "base")
        self.device = self.config.get("whisper_device", "auto")
        self.model = None
        self.available = False

    def _load_config(self):
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        if config_path.exists():
            return yaml.safe_load(config_path.read_text()) or {}
        return {}

    def _load_model(self):
        if self.model is not None:
            return
        try:
            from faster_whisper import WhisperModel
            device = self.device
            if device == "auto":
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            self.model = WhisperModel(self.model_size, device=device, compute_type=compute_type)
            self.available = True
            log.info(f"Whisper model '{self.model_size}' loaded on {device}")
        except Exception as e:
            log.warning(f"Failed to load Whisper model: {e}")
            self.available = False

    def transcribe(self, audio_data: bytes) -> str:
        self._load_model()
        if not self.available:
            return ""

        import io
        import soundfile as sf

        try:
            data, samplerate = sf.read(io.BytesIO(audio_data))
            if len(data.shape) > 1:
                data = data.mean(axis=1)
            segments, _ = self.model.transcribe(data, beam_size=5, language=self.config.get("language", "pt-PT")[:2])
            text = " ".join(seg.text for seg in segments)
            log.info(f"Transcribed: {text}")
            return text.strip()
        except Exception as e:
            log.error(f"Transcription error: {e}")
            return ""

    def is_available(self) -> bool:
        return self.available

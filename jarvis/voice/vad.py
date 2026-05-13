import time
from collections import deque
from threading import Lock

from jarvis.core.logger import JarvisLogger


log = JarvisLogger()

HAS_NUMPY = False
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    pass


SPEECH_THRESHOLD = 0.15
SILENCE_THRESHOLD = 0.08
MIN_SPEECH_CHUNKS = 3
MIN_SILENCE_CHUNKS = 20
ENERGY_HISTORY_SIZE = 50
FRAME_DURATION_MS = 30


class VoiceActivityDetector:
    def __init__(self, sample_rate: int = 16000, frame_size: int = 480):
        self.sample_rate = sample_rate
        self.frame_size = frame_size
        self._lock = Lock()
        self._reset()

    def _reset(self):
        self._is_speech = False
        self._speech_chunks = 0
        self._silence_chunks = 0
        self._energy_history: deque = deque(maxlen=ENERGY_HISTORY_SIZE)
        self._noise_floor = 0.02
        self._last_speech_time = 0.0
        self._start_time = 0.0
        self._frame_count = 0

    def reset(self):
        with self._lock:
            self._reset()

    def is_speech(self, audio_data: bytes | list) -> dict:
        with self._lock:
            if self._start_time == 0:
                self._start_time = time.time()
            self._frame_count += 1

            if HAS_NUMPY and isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            elif HAS_NUMPY:
                audio_array = np.asarray(audio_data, dtype=np.float32)
                if audio_array.max() > 1.0:
                    audio_array = audio_array / 32768.0
            else:
                return {"speech": False, "energy": 0.0, "prob": 0.0}

            energy = float(np.sqrt(np.mean(audio_array ** 2)))
            self._energy_history.append(energy)

            if len(self._energy_history) > 10:
                self._noise_floor = float(np.percentile(list(self._energy_history), 20))
                self._noise_floor = max(self._noise_floor, 0.005)

            threshold = max(self._noise_floor * 2.5, SPEECH_THRESHOLD * 0.1)
            is_active = energy > threshold

            prob = min(1.0, energy / max(threshold, 0.001))

            if is_active:
                self._speech_chunks += 1
                self._silence_chunks = 0
            else:
                self._silence_chunks += 1
                if self._speech_chunks > 0:
                    self._speech_chunks = max(0, self._speech_chunks - 1)

            if not self._is_speech:
                if self._speech_chunks >= MIN_SPEECH_CHUNKS:
                    self._is_speech = True
                    self._last_speech_time = time.time()
                    self._silence_chunks = 0
            else:
                if self._silence_chunks >= MIN_SILENCE_CHUNKS:
                    self._is_speech = False
                    self._speech_chunks = 0

            if self._is_speech:
                self._last_speech_time = time.time()

            elapsed = time.time() - self._start_time if self._start_time else 0

            return {
                "speech": self._is_speech,
                "energy": round(energy, 6),
                "prob": round(prob, 4),
                "noise_floor": round(self._noise_floor, 6),
                "elapsed": round(elapsed, 3),
                "threshold": round(threshold, 6),
            }

    @property
    def is_active(self) -> bool:
        return self._is_speech

    @property
    def speech_duration(self) -> float:
        if self._is_speech:
            return time.time() - self._last_speech_time
        return 0.0

    @property
    def silence_since_speech(self) -> float:
        if not self._is_speech and self._last_speech_time > 0:
            return time.time() - self._last_speech_time
        return 0.0


class EnergyVoiceDetector:
    def __init__(self, threshold: float = 500.0, min_voice_chunks: int = 3, silence_timeout: float = 0.8):
        self.threshold = threshold
        self.min_voice_chunks = min_voice_chunks
        self.silence_timeout = silence_timeout
        self._voice_chunks = 0
        self._silence_start: float | None = None
        self._recording_start: float | None = None
        self._has_voice = False
        self._chunk_count = 0

    def reset(self):
        self._voice_chunks = 0
        self._silence_start = None
        self._recording_start = None
        self._has_voice = False
        self._chunk_count = 0

    def process(self, audio_data) -> dict:
        if self._recording_start is None:
            self._recording_start = time.time()

        self._chunk_count += 1

        if HAS_NUMPY:
            energy = float(np.abs(audio_data).mean())
        else:
            energy = 100.0

        is_voice = energy > self.threshold

        if is_voice:
            self._voice_chunks += 1
            self._silence_start = None
            if self._voice_chunks >= self.min_voice_chunks:
                self._has_voice = True
        else:
            if self._silence_start is None:
                self._silence_start = time.time()

        elapsed = time.time() - self._recording_start if self._recording_start else 0
        silent_duration = (time.time() - self._silence_start) if self._silence_start and not is_voice else 0.0

        should_stop = False
        stop_reason = None

        if self._has_voice and silent_duration >= self.silence_timeout:
            should_stop = True
            stop_reason = "silence_detected"
        elif elapsed >= 15.0:
            should_stop = True
            stop_reason = "timeout"
        elif self._chunk_count >= 10 and not self._has_voice and elapsed >= 2.0:
            should_stop = True
            stop_reason = "no_voice"

        return {
            "energy": round(energy, 2),
            "is_voice": is_voice,
            "has_voice": self._has_voice,
            "silent_duration": round(silent_duration, 3),
            "elapsed": round(elapsed, 3),
            "should_stop": should_stop,
            "stop_reason": stop_reason,
        }


class AudioEnergyNormalizer:
    def __init__(self, target_level: float = 0.3, adaptation_speed: float = 0.01):
        self.target_level = target_level
        self.adaptation_speed = adaptation_speed
        self._gain = 1.0

    def normalize(self, audio_array) -> list:
        if not HAS_NUMPY:
            return audio_array
        import numpy as np
        current_level = float(np.sqrt(np.mean(audio_array ** 2)))
        if current_level > 0.001:
            target_gain = self.target_level / current_level
            self._gain += (target_gain - self._gain) * self.adaptation_speed
            self._gain = max(0.1, min(self._gain, 10.0))
        return (np.asarray(audio_array) * self._gain).tolist()

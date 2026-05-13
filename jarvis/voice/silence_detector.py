import time
from typing import Any, Callable

from jarvis.core.logger import JarvisLogger


log = JarvisLogger()

HAS_NUMPY = False
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    pass

SILENCE_THRESHOLD_DEFAULT = 300
SILENCE_DURATION_DEFAULT = 1.5
MIN_RECORDING_DURATION = 0.5
MAX_RECORDING_DURATION = 15.0


class SilenceDetector:
    def __init__(self, threshold: int = SILENCE_THRESHOLD_DEFAULT, silence_duration: float = SILENCE_DURATION_DEFAULT):
        self.threshold = threshold
        self.silence_duration = silence_duration
        self._reset()

    def _reset(self):
        self._silent_start: float | None = None
        self._recording_start: float | None = None
        self._has_voice = False
        self._chunk_count = 0

    def process_chunk(self, audio_data, sample_rate: int, chunk_size: int) -> dict:
        if self._recording_start is None:
            self._recording_start = time.time()

        self._chunk_count += 1
        if HAS_NUMPY:
            volume = float(np.abs(audio_data).mean())
        else:
            volume = float(abs(audio_data)) if isinstance(audio_data, (int, float)) else 100.0
        is_silent = volume < self.threshold

        if not is_silent:
            self._has_voice = True
            self._silent_start = None
        elif self._silent_start is None:
            self._silent_start = time.time()

        elapsed = time.time() - self._recording_start if self._recording_start else 0
        silent_duration = (time.time() - self._silent_start) if self._silent_start and is_silent else 0.0

        should_stop = False
        stop_reason = None

        if self._has_voice and silent_duration >= self.silence_duration:
            should_stop = True
            stop_reason = "silence_detected"
        elif elapsed >= MAX_RECORDING_DURATION:
            should_stop = True
            stop_reason = "timeout"
        elif self._chunk_count >= 5 and not self._has_voice and elapsed >= 2.0:
            should_stop = True
            stop_reason = "no_voice_detected"

        return {
            "volume": volume,
            "is_silent": is_silent,
            "silent_duration": silent_duration,
            "elapsed": elapsed,
            "has_voice": self._has_voice,
            "should_stop": should_stop,
            "stop_reason": stop_reason,
        }

    def reset(self):
        self._reset()

    def get_threshold(self) -> int:
        return self.threshold

    def set_threshold(self, threshold: int):
        self.threshold = max(50, min(5000, threshold))

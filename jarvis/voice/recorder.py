import threading
import wave
import io
from pathlib import Path

from jarvis.core.logger import JarvisLogger


log = JarvisLogger()

HAS_NUMPY = True
try:
    import numpy as np
except ImportError:
    HAS_NUMPY = False

HAS_PYAUDIO = True
try:
    import pyaudio
except ImportError:
    HAS_PYAUDIO = False

CHUNK = 1024
FORMAT = None
CHANNELS = 1
RATE = 16000
SILENCE_THRESHOLD = 500
SILENCE_DURATION = 1.5

if HAS_PYAUDIO:
    FORMAT = pyaudio.paInt16


class AudioRecorder:
    def __init__(self):
        self._recording = False
        self._frames = []
        self._stream = None
        self.audio = None
        if HAS_PYAUDIO and HAS_NUMPY:
            self.audio = pyaudio.PyAudio()

    def is_available(self) -> bool:
        return HAS_PYAUDIO and HAS_NUMPY and self.audio is not None

    def start_recording(self):
        if not self.is_available():
            log.warning("Cannot record: pyaudio not available")
            return
        self._recording = True
        self._frames = []
        self._stream = self.audio.open(
            format=FORMAT, channels=CHANNELS, rate=RATE,
            input=True, frames_per_buffer=CHUNK,
        )
        log.info("Recording started")

    def stop_recording(self) -> bytes:
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        self._recording = False
        log.info("Recording stopped")
        return self._get_wav_data()

    def _get_wav_data(self) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(b"".join(self._frames))
        return buf.getvalue()

    def record_until_silence(self, timeout=10) -> bytes:
        if not self.is_available():
            return b""
        self.start_recording()
        silent_chunks = 0
        max_silent_chunks = int(RATE / CHUNK * SILENCE_DURATION)
        total_chunks = 0
        max_chunks = int(RATE / CHUNK * timeout)

        while self._recording and total_chunks < max_chunks:
            data = self._stream.read(CHUNK, exception_on_overflow=False)
            self._frames.append(data)
            audio_array = np.frombuffer(data, dtype=np.int16)
            volume = float(np.abs(audio_array).mean())
            if volume < SILENCE_THRESHOLD:
                silent_chunks += 1
            else:
                silent_chunks = 0
            if silent_chunks > max_silent_chunks:
                break
            total_chunks += 1

        return self.stop_recording()

    def close(self):
        if self.audio:
            self.audio.terminate()

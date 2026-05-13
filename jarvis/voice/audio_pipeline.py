import io
import threading
import time
import wave
from enum import Enum, auto
from typing import Any, Callable

from jarvis.core.logger import JarvisLogger
from jarvis.core.events import EventBus, EventType
from jarvis.core.memory_manager import MemoryManager


log = JarvisLogger()
events = EventBus()

HAS_PYAUDIO = False
HAS_NUMPY = False
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    pass
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    pass

CHUNK = 1024
FORMAT = None
CHANNELS = 1
RATE = 16000
if HAS_PYAUDIO:
    FORMAT = pyaudio.paInt16

WAKE_WORD_COOLDOWN = 2.0
FOLLOW_UP_TIMEOUT = 8.0
AMBIENT_CHECK_INTERVAL = 0.5


class PipelineState(Enum):
    IDLE = auto()
    LISTENING = auto()
    RECORDING = auto()
    PROCESSING = auto()
    SPEAKING = auto()
    AMBIENT = auto()
    ERROR = auto()


class AudioPipeline:
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
        self._state = PipelineState.IDLE
        self._thread: threading.Thread | None = None
        self._stop_flag = threading.Event()
        self._pause_flag = threading.Event()
        self._interrupt_flag = threading.Event()
        self._frames: list[bytes] = []
        self._audio = None
        self._stream = None
        self._mode = "push_to_talk"
        self._transcriber = None
        self._tts = None
        self._wakeword = None
        self._vad = None
        self._device_index: int | None = None
        self._process_callback: Callable | None = None
        self._waveform_callback: Callable | None = None
        self._transcription_callback: Callable | None = None
        self._state_callback: Callable | None = None
        self._available = HAS_PYAUDIO and HAS_NUMPY
        self._last_wake_word_time = 0.0
        self._follow_up_active = False
        self._last_command_time = 0.0
        self._ambient_active = False
        self._load_dependencies()

    def _load_dependencies(self):
        from jarvis.voice.stt import SpeechToText
        from jarvis.voice.tts import TextToSpeech
        from jarvis.voice.vad import VoiceActivityDetector
        self._transcriber = SpeechToText()
        self._tts = TextToSpeech()
        self._wakeword = None
        self._vad = VoiceActivityDetector()
        mem = MemoryManager()
        dev_idx = mem.get_preference("mic_device_index")
        if dev_idx is not None:
            self._device_index = dev_idx
        ww_enabled = mem.get_preference("wake_word_enabled")
        if ww_enabled is None:
            from jarvis.core.assistant import Assistant
            try:
                ww_enabled = Assistant().config.get("enable_wake_word", False)
            except Exception:
                ww_enabled = False

    @property
    def state(self) -> PipelineState:
        return self._state

    @state.setter
    def state(self, value: PipelineState):
        old = self._state
        self._state = value
        events.emit(EventType.MICROPHONE_STATE_CHANGED, {"state": value.name.lower()})
        if self._state_callback and old != value:
            self._state_callback(value)

    @property
    def is_listening(self) -> bool:
        return self._state in (PipelineState.LISTENING, PipelineState.RECORDING, PipelineState.AMBIENT)

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str):
        if value in ("push_to_talk", "continuous", "ambient"):
            self._mode = value
            if value == "ambient":
                self._ambient_active = True
            else:
                self._ambient_active = False

    @property
    def is_speaking(self) -> bool:
        return self._state == PipelineState.SPEAKING

    def is_available(self) -> bool:
        return self._available

    def set_device(self, index: int):
        self._device_index = index

    def set_callbacks(self, process: Callable = None, waveform: Callable = None,
                      transcription: Callable = None, state_change: Callable = None):
        if process:
            self._process_callback = process
        if waveform:
            self._waveform_callback = waveform
        if transcription:
            self._transcription_callback = transcription
        if state_change:
            self._state_callback = state_change

    def interrupt_speaking(self):
        self._interrupt_flag.set()
        events.emit(EventType.INTERRUPTION_DETECTED, {})
        log.info("Speech interrupted")

    def _get_audio(self):
        if self._audio is None:
            import pyaudio
            self._audio = pyaudio.PyAudio()
        return self._audio

    def _open_stream(self):
        audio = self._get_audio()
        device_index = self._device_index
        self._stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK,
        )
        return self._stream

    def _close_stream(self):
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _frames_to_wav(self) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(b"".join(self._frames))
        return buf.getvalue()

    def _get_audio_data(self, data: bytes):
        if not HAS_NUMPY:
            return None
        return np.frombuffer(data, dtype=np.int16)

    def _load_wakeword(self):
        if self._wakeword is not None:
            return
        try:
            from jarvis.voice.wakeword import WakeWordDetector
            self._wakeword = WakeWordDetector()
        except Exception:
            self._wakeword = None

    def _check_wakeword(self, audio_data) -> bool:
        if self._wakeword is None:
            self._load_wakeword()
        if self._wakeword and self._wakeword.is_available():
            try:
                now = time.time()
                if now - self._last_wake_word_time < WAKE_WORD_COOLDOWN:
                    return False
                if self._wakeword.detect(audio_data):
                    self._last_wake_word_time = now
                    self._follow_up_active = False
                    return True
            except Exception:
                pass
        return False

    def _can_follow_up(self) -> bool:
        if not self._follow_up_active:
            return False
        elapsed = time.time() - self._last_command_time
        return elapsed < FOLLOW_UP_TIMEOUT

    def _start_follow_up(self):
        self._follow_up_active = True
        self._last_command_time = time.time()

    def _listen_loop(self):
        self.state = PipelineState.LISTENING if self._mode in ("continuous", "ambient") else PipelineState.RECORDING
        self._stop_flag.clear()
        self._interrupt_flag.clear()
        self._frames = []
        self._vad.reset()

        if self._mode in ("continuous", "ambient"):
            events.emit(EventType.LISTENING_STARTED, {})
            log.info(f"Listening mode: {self._mode}")

        try:
            stream = self._open_stream()
        except Exception as e:
            log.error(f"Failed to open audio stream: {e}")
            self.state = PipelineState.ERROR
            events.emit(EventType.ERROR, {"message": f"Microphone error: {e}"})
            return

        self.state = PipelineState.RECORDING
        log.info("Recording started")

        wakeword_triggered = False
        last_waveform_time = 0
        follow_up_active = self._can_follow_up()

        while not self._stop_flag.is_set():
            if self._interrupt_flag.is_set():
                log.info("Recording interrupted")
                self._interrupt_flag.clear()
                break

            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
            except Exception:
                break

            self._frames.append(data)
            audio_array = self._get_audio_data(data)

            if audio_array is not None:
                vad_result = self._vad.is_speech(audio_array)
                energy = vad_result.get("energy", 0)

                now = time.time()
                if self._waveform_callback and (now - last_waveform_time) >= 0.05:
                    self._waveform_callback(energy * 3000)
                    last_waveform_time = now

                if self._transcription_callback and len(self._frames) % 10 == 0:
                    partial = len(self._frames) * CHUNK / RATE
                    self._transcription_callback({"partial": True, "duration": partial})

                if self._mode in ("continuous", "ambient") and not wakeword_triggered and not follow_up_active:
                    if self._check_wakeword(audio_array):
                        wakeword_triggered = True
                        self._vad.reset()
                        self._frames = [data]
                        events.emit(EventType.WAKE_WORD_DETECTED, {})
                        log.info("Wake word detected, listening for command")
                        continue

                    has_voice = vad_result.get("speech", False) and self._vad.speech_duration > 0.5
                    if has_voice and self._mode == "continuous":
                        wakeword_triggered = True
                        self._vad.reset()
                        self._frames = [data]
                        log.info("Voice detected (continuous mode), listening for command")
                        continue

                if wakeword_triggered or follow_up_active or self._mode == "push_to_talk":
                    silence_since = self._vad.silence_since_speech
                    if silence_since > 1.2 and self._vad.is_active is False:
                        log.info(f"Recording stopped after {silence_since:.1f}s silence")
                        break

            if self._pause_flag.is_set():
                self._pause_flag.wait()

        self._close_stream()
        self.state = PipelineState.PROCESSING
        log.info("Recording finished, transcribing...")

        wav_data = self._frames_to_wav()
        text = self._transcribe(wav_data)

        if text:
            events.emit(EventType.TRANSCRIPTION_READY, {"text": text})
            if self._transcription_callback:
                self._transcription_callback({"text": text, "partial": False})
            self._execute_command(text)
            self._start_follow_up()
        else:
            log.info("No speech detected")
            if self._mode == "ambient":
                self.state = PipelineState.AMBIENT
            else:
                self.state = PipelineState.IDLE

    def _transcribe(self, wav_data: bytes) -> str:
        try:
            return self._transcriber.transcribe(wav_data) if self._transcriber else ""
        except Exception as e:
            log.error(f"Transcription error: {e}")
            return ""

    def _execute_command(self, text: str):
        if self._process_callback:
            try:
                self._process_callback(text)
            except Exception as e:
                log.error(f"Command processing error: {e}")
        self._last_command_time = time.time()
        if self._mode == "ambient":
            self.state = PipelineState.AMBIENT
        else:
            self.state = PipelineState.IDLE

    def start_listening(self):
        if not self._available:
            log.warning("Audio pipeline not available (pyaudio/numpy missing)")
            return
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop_listening(self):
        self._stop_flag.set()
        if self._stream:
            self._close_stream()
        self.state = PipelineState.IDLE
        self._follow_up_active = False
        events.emit(EventType.LISTENING_STOPPED, {})

    def cancel_command(self):
        self._stop_flag.set()
        self._interrupt_flag.set()
        self.state = PipelineState.IDLE
        self._follow_up_active = False

    def speak(self, text: str):
        if not self._tts or not self._tts.available:
            return
        self.state = PipelineState.SPEAKING
        events.emit(EventType.TTS_STARTED, {"text": text[:50]})
        try:
            self._tts.speak(text)
        except Exception as e:
            log.error(f"TTS error: {e}")
        self.state = PipelineState.IDLE
        events.emit(EventType.TTS_COMPLETED, {})

    def speak_async(self, text: str):
        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()

    def set_mic_threshold(self, threshold: int):
        pass

    def get_waveform_data(self) -> float:
        return 0.0

    def close(self):
        self.stop_listening()
        if self._audio:
            try:
                self._audio.terminate()
            except Exception:
                pass
            self._audio = None

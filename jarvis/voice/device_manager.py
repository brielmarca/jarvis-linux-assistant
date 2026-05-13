from typing import Any

from jarvis.core.logger import JarvisLogger


log = JarvisLogger()

HAS_PYAUDIO = False
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    pass


class DeviceInfo:
    def __init__(self, index: int, name: str, channels: int, sample_rate: int, is_default: bool = False):
        self.index = index
        self.name = name
        self.channels = channels
        self.sample_rate = sample_rate
        self.is_default = is_default

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "name": self.name,
            "channels": self.channels,
            "sample_rate": self.sample_rate,
            "is_default": self.is_default,
        }

    def __repr__(self):
        default = " (default)" if self.is_default else ""
        return f"<Device #{self.index}: {self.name}{default}>"


class DeviceManager:
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
        self._audio = None
        self._input_devices: list[DeviceInfo] = []
        self._default_device: DeviceInfo | None = None
        self._available = HAS_PYAUDIO
        if self._available:
            self._scan_devices()

    def _get_audio(self):
        if self._audio is None and HAS_PYAUDIO:
            import pyaudio
            try:
                self._audio = pyaudio.PyAudio()
            except Exception:
                self._available = False
        return self._audio

    def _scan_devices(self):
        audio = self._get_audio()
        if not audio:
            return
        self._input_devices = []
        try:
            default_index = audio.get_default_input_device_info().get("index", 0)
        except Exception:
            default_index = 0

        for i in range(audio.get_device_count()):
            try:
                info = audio.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0:
                    dev = DeviceInfo(
                        index=i,
                        name=info.get("name", f"Device {i}"),
                        channels=int(info.get("maxInputChannels", 1)),
                        sample_rate=int(info.get("defaultSampleRate", 16000)),
                        is_default=(i == default_index),
                    )
                    self._input_devices.append(dev)
                    if dev.is_default:
                        self._default_device = dev
            except Exception:
                continue

        if not self._default_device and self._input_devices:
            self._default_device = self._input_devices[0]

        log.info(f"Found {len(self._input_devices)} input device(s)")

    def list_devices(self) -> list[DeviceInfo]:
        if not self._input_devices:
            self._scan_devices()
        return list(self._input_devices)

    def get_device(self, index: int) -> DeviceInfo | None:
        for dev in self._input_devices:
            if dev.index == index:
                return dev
        return None

    def get_default_device(self) -> DeviceInfo | None:
        if not self._input_devices:
            self._scan_devices()
        return self._default_device

    def select_device(self, index: int) -> DeviceInfo | None:
        dev = self.get_device(index)
        if dev:
            self._default_device = dev
            from jarvis.core.memory_manager import MemoryManager
            MemoryManager().set_preference("mic_device_index", index)
            log.info(f"Selected microphone: {dev.name}")
        return dev

    def is_available(self) -> bool:
        return self._available and len(self._input_devices) > 0

    def close(self):
        if self._audio:
            try:
                self._audio.terminate()
            except Exception:
                pass
            self._audio = None

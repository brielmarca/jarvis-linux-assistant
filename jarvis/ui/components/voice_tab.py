from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QSlider, QCheckBox,
)
from PyQt6.QtCore import Qt, QTimer

from jarvis.ui.theme import Theme
from jarvis.ui.i18n import t, tr
from jarvis.core.events import EventBus, EventType
from jarvis.core.memory_manager import MemoryManager
from jarvis.voice.audio_pipeline import AudioPipeline, PipelineState
from jarvis.voice.device_manager import DeviceManager


events = EventBus()
mem = MemoryManager()
audio = AudioPipeline()
devices = DeviceManager()


class VoiceTab(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main = main_window
        self._listening = False
        self._header = None
        self._listen_btn = None
        self._status_label = None
        self._voice_enabled_cb = None
        self._st_header = None
        self._pipeline_status = None
        self._mic_status = None
        self._asr_status = None
        self._tts_status = None
        self.device_combo = None
        self.mode_combo = None
        self.threshold_slider = None
        self.threshold_label = None
        self.setup_ui()
        self._load_settings()
        events.on(EventType.MICROPHONE_STATE_CHANGED, self._on_mic_state)
        tr.languageChanged.connect(self.retranslate_ui)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        self._header = QLabel(t("voice.title"))
        self._header.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 22px; font-weight: 700; background: transparent;")
        layout.addWidget(self._header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.BORDER}; border: none; max-height: 0.5px;")
        layout.addWidget(sep)

        mic_box = self._make_group("voice.microphone", [
            ("voice.device", self._make_device_selector()),
            ("voice.mode", self._make_mode_selector()),
            ("voice.threshold", self._make_threshold_slider()),
        ])
        layout.addWidget(mic_box)

        ctrl_box = QWidget()
        ctrl_box.setStyleSheet(f"background-color: rgba(28,28,30,0.5); border: 0.5px solid {Theme.BORDER}; border-radius: 10px;")
        ctrl_layout = QHBoxLayout(ctrl_box)
        ctrl_layout.setContentsMargins(16, 12, 16, 12)
        ctrl_layout.setSpacing(12)

        self._listen_btn = QPushButton(t("voice.start_listening"))
        self._listen_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.ACCENT_PRIMARY}; border: none;
            border-radius: 18px; padding: 12px 28px; font-size: 14px; font-weight: 500; color: white; }}
            QPushButton:hover {{ background-color: #0066CC; }}
            QPushButton:disabled {{ background-color: rgba(0,122,255,0.3); }}
        """)
        self._listen_btn.clicked.connect(self._toggle_listening)
        ctrl_layout.addWidget(self._listen_btn)

        self._status_label = QLabel(t("voice.idle"))
        self._status_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        ctrl_layout.addWidget(self._status_label, 1)

        ctrl_layout.addStretch()

        self._voice_enabled_cb = QCheckBox(t("voice.enable_voice"))
        self._voice_enabled_cb.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; spacing: 6px;")
        ctrl_layout.addWidget(self._voice_enabled_cb)

        layout.addWidget(ctrl_box)

        status_box = QWidget()
        status_box.setStyleSheet(f"background-color: rgba(28,28,30,0.5); border: 0.5px solid {Theme.BORDER}; border-radius: 10px;")
        st_layout = QVBoxLayout(status_box)
        st_layout.setContentsMargins(16, 12, 16, 12)
        st_layout.setSpacing(6)

        self._st_header = QLabel(t("voice.pipeline_status"))
        self._st_header.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; font-weight: 500; background: transparent;")
        st_layout.addWidget(self._st_header)

        self._pipeline_status = QLabel(t("voice.pipeline_idle"))
        self._pipeline_status.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px; font-family: {Theme.FONT_MONO}; background: transparent;")
        st_layout.addWidget(self._pipeline_status)

        self._mic_status = QLabel(t("voice.mic_not_active"))
        self._mic_status.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px; background: transparent;")
        st_layout.addWidget(self._mic_status)

        asr_available = audio._transcriber and audio._transcriber.is_available()
        asr_status_text = t("voice.asr_available") if asr_available else t("voice.asr_not_loaded")
        self._asr_status = QLabel(t("voice.asr_label", status=asr_status_text))
        asr_color = Theme.ACCENT_SUCCESS if asr_available else Theme.TEXT_MUTED
        self._asr_status.setStyleSheet(f"color: {asr_color}; font-size: 11px; background: transparent;")
        st_layout.addWidget(self._asr_status)

        tts_available = audio._tts and audio._tts.available
        tts_status_text = t("voice.tts_available") if tts_available else t("voice.tts_offline")
        self._tts_status = QLabel(t("voice.tts_label", status=tts_status_text))
        tts_color = Theme.ACCENT_SUCCESS if tts_available else Theme.TEXT_MUTED
        self._tts_status.setStyleSheet(f"color: {tts_color}; font-size: 11px; background: transparent;")
        st_layout.addWidget(self._tts_status)

        layout.addWidget(status_box)
        layout.addStretch()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_status)
        self._refresh_timer.start(2000)

    def retranslate_ui(self):
        self._header.setText(t("voice.title"))
        self._listen_btn.setText(t("voice.start_listening") if not self._listening else t("voice.stop_listening"))
        self._voice_enabled_cb.setText(t("voice.enable_voice"))
        self._st_header.setText(t("voice.pipeline_status"))

    def _make_device_selector(self):
        self.device_combo = QComboBox()
        self.device_combo.setStyleSheet(f"""
            QComboBox {{ background-color: rgba(44,44,46,0.6); color: {Theme.TEXT_PRIMARY};
            border: 0.5px solid {Theme.BORDER}; border-radius: 6px; padding: 6px 12px; font-size: 12px; min-width: 200px; }}
            QComboBox:hover {{ border-color: {Theme.ACCENT_PRIMARY}; }}
            QComboBox QAbstractItemView {{ background-color: {Theme.BG_CARD_SOLID}; color: {Theme.TEXT_PRIMARY};
            selection-background-color: {Theme.ACCENT_PRIMARY}; border: 0.5px solid {Theme.BORDER}; border-radius: 6px; }}
        """)
        for dev in devices.list_devices():
            label = f"{dev.name} (ch:{dev.channels} rate:{dev.sample_rate})"
            self.device_combo.addItem(label, dev.index)
        self.device_combo.currentIndexChanged.connect(self._on_device_change)
        return self.device_combo

    def _make_mode_selector(self):
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([t("voice.push_to_talk"), t("voice.continuous"), t("voice.wake_word")])
        self.mode_combo.setStyleSheet(self.device_combo.styleSheet())
        self.mode_combo.currentTextChanged.connect(self._on_mode_change)
        return self.mode_combo

    def _make_threshold_slider(self):
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(50, 2000)
        self.threshold_slider.setValue(300)
        self.threshold_slider.setFixedWidth(200)
        self.threshold_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ background: {Theme.BORDER}; height: 4px; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: {Theme.ACCENT_PRIMARY}; width: 16px; height: 16px;
            margin: -6px 0; border-radius: 8px; }}
        """)
        self.threshold_slider.valueChanged.connect(self._on_threshold_change)
        rl.addWidget(self.threshold_slider)

        self.threshold_label = QLabel("300")
        self.threshold_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        self.threshold_label.setFixedWidth(40)
        rl.addWidget(self.threshold_label)

        return row

    def _make_group(self, title_text, widgets):
        group = QWidget()
        group.setStyleSheet(f"background-color: rgba(28,28,30,0.5); border: 0.5px solid {Theme.BORDER}; border-radius: 10px;")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        title = QLabel(t(title_text))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: 600; background: transparent;")
        layout.addWidget(title)
        for name, widget in widgets:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            label = QLabel(t(name))
            label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
            rl.addWidget(label)
            rl.addStretch()
            rl.addWidget(widget)
            layout.addWidget(row)
        return group

    def _load_settings(self):
        mode = mem.get_preference("voice_mode", "push_to_talk")
        idx = {"push_to_talk": 0, "continuous": 1, "wake_word": 2}.get(mode, 0)
        self.mode_combo.setCurrentIndex(idx)
        threshold = mem.get_preference("silence_threshold", 300)
        self.threshold_slider.setValue(threshold)
        voice_enabled = mem.get_preference("enable_voice", False)
        self._voice_enabled_cb.setChecked(voice_enabled)

    def _on_device_change(self, idx):
        dev_idx = self.device_combo.currentData()
        if dev_idx is not None:
            devices.select_device(dev_idx)
            audio.set_device(dev_idx)

    def _on_mode_change(self, text):
        mode_map = {"push_to_talk": 0, "continuous": 1, "wake_word": 2}
        mode_map_rev = {t("voice.push_to_talk"): "push_to_talk", t("voice.continuous"): "continuous", t("voice.wake_word"): "wake_word"}
        mode = mode_map_rev.get(text, "push_to_talk")
        audio.mode = mode
        mem.set_preference("voice_mode", mode)

    def _on_threshold_change(self, val):
        self.threshold_label.setText(str(val))
        audio.set_mic_threshold(val)
        mem.set_preference("silence_threshold", val)

    def _on_mic_state(self, data):
        state = data.get("state", "idle")
        self._status_label.setText(state.title())

    def _toggle_listening(self):
        if self._listening:
            audio.stop_listening()
            self._listening = False
            self._listen_btn.setText(t("voice.start_listening"))
            self._listen_btn.setObjectName("accent")
        else:
            audio.start_listening()
            self._listening = True
            self._listen_btn.setText(t("voice.stop_listening"))
            self._listen_btn.setStyleSheet(f"""
                QPushButton {{ background-color: rgba(255,69,58,0.12); border: 0.5px solid {Theme.ACCENT_ERROR}44;
                border-radius: 18px; padding: 12px 28px; font-size: 14px; font-weight: 500; color: {Theme.ACCENT_ERROR}; }}
                QPushButton:hover {{ background-color: rgba(255,69,58,0.2); }}
            """)

    def _refresh_status(self):
        state_name = audio.state.name.lower() if audio.state else "idle"
        self._pipeline_status.setText(f"Pipeline: {state_name}")
        self._mic_status.setText(t("voice.mic_active") if audio.is_listening else t("voice.mic_not_active"))

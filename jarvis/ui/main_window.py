from datetime import datetime
from pathlib import Path

import yaml

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QScrollArea, QComboBox, QCheckBox,
    QPlainTextEdit, QSystemTrayIcon, QMenu, QFrame, QSizePolicy,
    QGridLayout,
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QShortcut, QPixmap

from jarvis.core.assistant import Assistant, events, EventType, log as jarvis_log
from jarvis.automation import linux as linux_auto
from jarvis.ui.theme import Theme
from jarvis.i18n import t, tr
from jarvis.ui.components.status_indicator import StatusIndicator
from jarvis.ui.components.command_input import CommandInput
from jarvis.ui.components.timeline_card import TimelineCard
from jarvis.ui.components.skill_card import SkillCard
from jarvis.ui.components.confirmation_dialog import ConfirmationDialog
from jarvis.ui.components.waveform import WaveformWidget
from jarvis.ui.components.thinking_animation import ThinkingAnimation
from jarvis.ui.components.system_monitor import SystemMonitorCard
from jarvis.ui.components.notification import NotificationManager
from jarvis.ui.components.sidebar import Sidebar
from jarvis.ui.components.palette import CommandPalette
from jarvis.ui.components.dev_mode import DevModeTab
from jarvis.ui.components.voice_tab import VoiceTab
from jarvis.ui.components.memory_tab import MemoryTab
from jarvis.ui.components.desktop_tab import DesktopTab
from jarvis.ui.components.workflows_tab import WorkflowsTab
from jarvis.ui.components.diagnostics_tab import DiagnosticsTab
from jarvis.ui.components.health_tab import HealthTab


_RESTART_KEYS = {"ollama_model", "whisper_model", "language", "enable_voice"}


def _backup_config():
    import shutil
    src = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
    if src.exists():
        dst = src.with_suffix(".yaml.bak")
        shutil.copy2(str(src), str(dst))
        return True
    return False


DEFAULT_CONFIG = {
    "assistant_name": "Jarvis",
    "language": "pt-PT",
    "ollama_model": "llama3:latest",
    "ollama_context_length": 4096,
    "enable_voice": False,
    "enable_wake_word": False,
    "enable_tts": False,
    "whisper_model": "base",
    "require_confirmation_for_dangerous_commands": True,
    "memory_max_short_term": 100,
    "memory_semantic_search": True,
    "memory_semantic_enabled": True,
    "context_max_tokens": 4096,
    "context_include_desktop_state": True,
    "context_include_recent_activity": True,
    "voice_vad_threshold": 0.5,
    "voice_wake_word_cooldown": 2.0,
    "voice_follow_up_timeout": 8.0,
    "workflows_enabled": True,
    "metrics_enabled": True,
}


def _load_config():
    p = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
    if p.exists():
        return yaml.safe_load(p.read_text()) or {}
    return {}


def _save_config(config):
    p = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
    p.write_text(yaml.dump(config, default_flow_style=False, allow_unicode=True))


CONFIG_CACHE = _load_config()


class DashboardTab(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        self._build_header(layout)
        self._build_quick_actions(layout)

        self.waveform = WaveformWidget()
        self.waveform.setVisible(False)
        layout.addWidget(self.waveform)

        self.thinking_anim = ThinkingAnimation()
        self.thinking_anim.setVisible(False)
        layout.addWidget(self.thinking_anim, 0, Qt.AlignmentFlag.AlignCenter)

        self._build_stats_row(layout)
        self._build_timeline(layout)

    def _build_header(self, layout):
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        h = QHBoxLayout(header)
        h.setContentsMargins(0, 0, 0, 0)

        name = QLabel(t("app.name"))
        name.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 26px; font-weight: 800; background: transparent; letter-spacing: -0.5px;")
        h.addWidget(name)

        ver = QLabel(t("app.version"))
        ver.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px; background: transparent; margin-top: 6px;")
        h.addWidget(ver)

        h.addStretch()

        self.status_indicator = StatusIndicator()
        h.addWidget(self.status_indicator)

        self.status_label = QLabel(t("app.status_idle"))
        self.status_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; font-weight: 500; background: transparent;")
        h.addWidget(self.status_label)

        layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.BORDER}; border: none; max-height: 1px;")
        layout.addWidget(sep)

    def _build_quick_actions(self, layout):
        actions_widget = QWidget()
        actions_widget.setStyleSheet(f"""
            background-color: rgba(20, 20, 38, 0.5);
            border: 1px solid {Theme.BORDER};
            border-radius: {Theme.CARD_RADIUS};
        """)
        actions_widget.setFixedHeight(52)
        a_layout = QHBoxLayout(actions_widget)
        a_layout.setContentsMargins(12, 0, 12, 0)
        a_layout.setSpacing(8)

        actions = [
            ("■", t("dashboard.terminal"), "open terminal"),
            ("◎", t("dashboard.firefox"), "open firefox"),
            ("♪", t("dashboard.volume_up"), "increase volume"),
            ("♪", t("dashboard.volume_down"), "decrease volume"),
            ("⚙", t("dashboard.system"), "system info"),
            ("<>", t("dashboard.code"), "programming mode"),
        ]

        for icon, label, cmd in actions:
            btn = QPushButton(f"{icon}  {label}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(124, 106, 255, 0.08);
                    border: 1px solid rgba(124, 106, 255, 0.15);
                    border-radius: 8px;
                    padding: 6px 14px;
                    font-size: 12px;
                    font-weight: 500;
                    color: {Theme.TEXT_SECONDARY};
                }}
                QPushButton:hover {{
                    background-color: rgba(124, 106, 255, 0.18);
                    border-color: {Theme.ACCENT_PRIMARY};
                    color: {Theme.TEXT_PRIMARY};
                }}
            """)
            btn.clicked.connect(lambda checked, c=cmd: self.main.process_command(c))
            a_layout.addWidget(btn)

        a_layout.addStretch()

        self.mic_status = QLabel("🎤  " + t("app.status_idle"))
        self.mic_status.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px; background: transparent; padding-right: 8px;")
        a_layout.addWidget(self.mic_status)

        live_text = t("dashboard.ai_live") if self.main.assistant.ollama.is_available() else t("dashboard.ai_off")
        self.ai_status = QLabel("AI: " + live_text)
        ai_color = Theme.ACCENT_SUCCESS if self.main.assistant.ollama.is_available() else Theme.ACCENT_ERROR
        self.ai_status.setStyleSheet(f"color: {ai_color}; font-size: 11px; background: transparent;")

        a_layout.addWidget(self.ai_status)

        layout.addWidget(actions_widget)

    def _build_stats_row(self, layout):
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(14)

        self.command_input = CommandInput()
        self.command_input.command_submitted.connect(self.main.process_command)
        rl.addWidget(self.command_input, 3)

        stats_card = self._make_mini_stats()
        rl.addWidget(stats_card, 2)

        layout.addWidget(row)

    def _make_mini_stats(self):
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(20, 20, 38, 0.5);
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.CARD_RADIUS};
            }}
        """)
        card.setMinimumHeight(44)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)

        self.stats_labels = {}
        _stat_names = {"CPU": t("dashboard.cpu"), "Mem": t("dashboard.mem"), "Disk": t("dashboard.disk")}
        for key in ["CPU", "Mem", "Disk"]:
            block = QWidget()
            block.setStyleSheet("background: transparent;")
            bl = QVBoxLayout(block)
            bl.setContentsMargins(0, 0, 0, 0)
            bl.setSpacing(1)
            k = QLabel(_stat_names.get(key, key))
            k.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 9px; background: transparent;")
            k.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bl.addWidget(k)
            v = QLabel("...")
            v.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 11px; font-weight: 600; background: transparent;")
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bl.addWidget(v)
            self.stats_labels[key] = v
            layout.addWidget(block)

        layout.addStretch()

        self.response_label = QLabel("")
        self.response_label.setStyleSheet(f"color: {Theme.ACCENT_SECONDARY}; font-size: 12px; background: transparent;")
        self.response_label.setWordWrap(True)
        self.response_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.response_label, 1)

        return card

    def _build_timeline(self, layout):
        self.timeline = TimelineCard()
        layout.addWidget(self.timeline, 1)

    def update_stats(self, info):
        na = t("dashboard.na")
        cpu = info.get("cpu", na)
        if len(cpu) > 12:
            cpu = cpu.split("@")[0].strip() if "@" in cpu else cpu[:12]
        self.stats_labels["CPU"].setText(cpu)
        self.stats_labels["Mem"].setText(info.get("memory", na))
        self.stats_labels["Disk"].setText(info.get("disk", na))

    def add_timeline_entry(self, entry):
        self.timeline.add_entry(entry)
        self.response_label.setText(entry.get("response", "")[:120])


class SkillsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel(t("skills.title"))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 22px; font-weight: 700; background: transparent; letter-spacing: -0.3px;")
        layout.addWidget(title)

        desc = QLabel(t("skills.description"))
        desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        layout.addWidget(desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.BORDER}; border: none; max-height: 1px;")
        layout.addWidget(sep)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.grid_layout = QVBoxLayout(container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(8)

        skills_data = [
            ("system", True, "normal"),
            ("apps", True, "normal"),
            ("browser", True, "normal"),
            ("media", True, "normal"),
            ("dev", True, "normal"),
            ("opencode", True, "elevated"),
        ]
        for name, enabled, perm in skills_data:
            card = SkillCard(name, enabled, perm)
            self.grid_layout.addWidget(card)

        self.grid_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)


class SettingsTab(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main = main_window
        self.config = dict(CONFIG_CACHE)
        self._dirty_keys = set()
        self._rebuild_required = False
        self.setup_ui()
        self._load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel(t("settings.title"))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 22px; font-weight: 700; background: transparent; letter-spacing: -0.3px;")
        layout.addWidget(title)

        desc = QLabel(t("settings.description"))
        desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        layout.addWidget(desc)

        self.restart_banner = QWidget()
        self.restart_banner.setStyleSheet(f"""
            background-color: rgba(240, 192, 64, 0.12);
            border: 1px solid {Theme.ACCENT_WARNING}66;
            border-radius: 8px;
        """)
        self.restart_banner.setVisible(False)
        rb_layout = QHBoxLayout(self.restart_banner)
        rb_layout.setContentsMargins(14, 8, 14, 8)
        rb_label = QLabel("⚡ " + t("settings.restart_banner"))
        rb_label.setStyleSheet(f"color: {Theme.ACCENT_WARNING}; font-size: 12px; background: transparent;")
        rb_layout.addWidget(rb_label)
        layout.addWidget(self.restart_banner)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.BORDER}; border: none; max-height: 1px;")
        layout.addWidget(sep)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.cl = QVBoxLayout(container)
        self.cl.setSpacing(12)

        self.cl.addWidget(self._make_group(t("settings.group_ai"), [
            (t("settings.ollama_model"), QComboBox(), "ollama_model", ["llama3:latest", "llama3.1:8b", "mistral", "phi3:mini", "llama3.2:3b"]),
            (t("settings.language"), QComboBox(), "language", ["pt-PT", "en-US", "es-ES", "fr-FR", "de-DE"]),
            (t("settings.context_length"), QComboBox(), "ollama_context_length", ["2048", "4096", "8192", "16384"]),
        ]))

        self.cl.addWidget(self._make_group(t("settings.group_voice"), [
            (t("settings.whisper_model"), QComboBox(), "whisper_model", ["base", "small", "medium", "large"]),
            (t("settings.enable_voice"), QCheckBox(), "enable_voice", None),
            (t("settings.enable_wake_word"), QCheckBox(), "enable_wake_word", None),
            (t("settings.enable_tts"), QCheckBox(), "enable_tts", None),
            (t("settings.vad_threshold"), QComboBox(), "voice_vad_threshold", ["0.1", "0.3", "0.5", "0.7", "0.9"]),
            (t("settings.wake_word_cooldown"), QComboBox(), "voice_wake_word_cooldown", ["1.0", "2.0", "3.0", "5.0"]),
            (t("settings.follow_up_timeout"), QComboBox(), "voice_follow_up_timeout", ["4.0", "8.0", "12.0", "20.0"]),
        ]))

        self.cl.addWidget(self._make_group(t("settings.group_memory"), [
            (t("settings.semantic_search"), QCheckBox(), "memory_semantic_search", None),
            (t("settings.semantic_enabled"), QCheckBox(), "memory_semantic_enabled", None),
            (t("settings.max_short_term"), QComboBox(), "memory_max_short_term", ["50", "100", "200", "500"]),
        ]))

        self.cl.addWidget(self._make_group(t("settings.group_context"), [
            (t("settings.max_tokens"), QComboBox(), "context_max_tokens", ["2048", "4096", "8192"]),
            (t("settings.include_desktop_state"), QCheckBox(), "context_include_desktop_state", None),
            (t("settings.include_recent_activity"), QCheckBox(), "context_include_recent_activity", None),
        ]))

        self.cl.addWidget(self._make_group(t("settings.group_features"), [
            (t("settings.workflows_enabled"), QCheckBox(), "workflows_enabled", None),
            (t("settings.metrics_enabled"), QCheckBox(), "metrics_enabled", None),
        ]))

        self.cl.addWidget(self._make_group(t("settings.group_permissions"), [
            (t("settings.confirm_dangerous"), QCheckBox(), "require_confirmation_for_dangerous_commands", None),
        ]))

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        save_btn = QPushButton(t("settings.save"))
        save_btn.setObjectName("accent")
        save_btn.setFixedHeight(44)
        save_btn.clicked.connect(self._save_settings)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT_PRIMARY};
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                color: white;
            }}
            QPushButton:hover {{ background-color: #8a7aff; }}
        """)
        btn_row.addWidget(save_btn)

        reset_btn = QPushButton(t("settings.reset"))
        reset_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(255,64,112,0.08); border: 1px solid {Theme.ACCENT_ERROR}44;
            border-radius: 10px; padding: 12px 24px; font-size: 14px; font-weight: 500; color: {Theme.ACCENT_ERROR}; }}
            QPushButton:hover {{ background-color: rgba(255,64,112,0.18); }}
        """)
        reset_btn.clicked.connect(self._reset_defaults)
        btn_row.addWidget(reset_btn)

        btn_row.addStretch()

        status_label = QLabel("")
        status_label.setObjectName("settings_status")
        status_label.setStyleSheet(f"color: {Theme.ACCENT_SUCCESS}; font-size: 12px; background: transparent;")
        btn_row.addWidget(status_label)

        self.cl.addLayout(btn_row)

        self.cl.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

    def _make_group(self, title_text, fields):
        group = QWidget()
        group.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(20, 20, 38, 0.5);
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.CARD_RADIUS};
            }}
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        title = QLabel(title_text)
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: 700; background: transparent;")
        layout.addWidget(title)

        self._field_widgets = getattr(self, '_field_widgets', {})

        for field_info in fields:
            if len(field_info) == 4:
                name, widget, config_key, options = field_info
            else:
                continue

            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)

            label = QLabel(name)
            label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
            rl.addWidget(label)
            rl.addStretch()

            if config_key in _RESTART_KEYS:
                restart_icon = QLabel("⚡")
                restart_icon.setToolTip(t("settings.restart_tooltip"))
                restart_icon.setStyleSheet(f"color: {Theme.ACCENT_WARNING}; font-size: 11px; background: transparent;")
                rl.addWidget(restart_icon)

            if isinstance(widget, QComboBox):
                widget.addItems(options or [])
                widget.setStyleSheet(f"""
                    QComboBox {{
                        background-color: rgba(12, 12, 22, 0.6);
                        color: {Theme.TEXT_PRIMARY};
                        border: 1px solid {Theme.BORDER};
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-size: 12px;
                        min-width: 140px;
                    }}
                    QComboBox:hover {{ border-color: {Theme.ACCENT_PRIMARY}; }}
                    QComboBox::drop-down {{ border: none; width: 20px; }}
                    QComboBox QAbstractItemView {{
                        background-color: {Theme.BG_CARD_SOLID};
                        color: {Theme.TEXT_PRIMARY};
                        selection-background-color: {Theme.ACCENT_PRIMARY};
                        border: 1px solid {Theme.BORDER};
                        border-radius: 6px;
                    }}
                """)
                widget.currentIndexChanged.connect(lambda idx, k=config_key: self._mark_dirty(k))
            elif isinstance(widget, QCheckBox):
                widget.setStyleSheet(f"""
                    QCheckBox {{ color: {Theme.TEXT_SECONDARY}; spacing: 8px; font-size: 13px; }}
                    QCheckBox::indicator {{
                        width: 18px; height: 18px; border-radius: 4px;
                        border: 1px solid {Theme.BORDER};
                        background-color: rgba(20, 20, 35, 0.6);
                    }}
                    QCheckBox::indicator:checked {{
                        background-color: {Theme.ACCENT_PRIMARY};
                        border-color: {Theme.ACCENT_PRIMARY};
                    }}
                    QCheckBox::indicator:hover {{ border-color: {Theme.ACCENT_PRIMARY}; }}
                """)
                widget.stateChanged.connect(lambda state, k=config_key: self._mark_dirty(k))

            self._field_widgets[config_key] = widget
            rl.addWidget(widget)
            layout.addWidget(row)

        return group

    def _mark_dirty(self, key):
        self._dirty_keys.add(key)
        if key in _RESTART_KEYS:
            self.restart_banner.setVisible(True)

    def _load_settings(self):
        for key, widget in getattr(self, '_field_widgets', {}).items():
            val = self.config.get(key)
            if val is None:
                continue
            if isinstance(widget, QComboBox):
                idx = widget.findText(str(val))
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(val))

    def _save_settings(self):
        _backup_config()
        changed = []
        for key, widget in getattr(self, '_field_widgets', {}).items():
            if isinstance(widget, QComboBox):
                new_val = widget.currentText()
            elif isinstance(widget, QCheckBox):
                new_val = widget.isChecked()
            else:
                continue
            old_val = self.config.get(key)
            self.config[key] = new_val
            if str(old_val) != str(new_val):
                changed.append(key)

        _save_config(self.config)
        CONFIG_CACHE.update(self.config)
        if "language" in changed:
            lang_map = {"en-US": "en", "es-ES": "es", "fr-FR": "fr", "de-DE": "de", "pt-PT": "pt_BR"}
            new_lang = lang_map.get(self.config.get("language", "en-US"), "en")
            tr.set_language(new_lang)
        self._dirty_keys.clear()

        status = self.findChild(QLabel, "settings_status")
        if status:
            if changed:
                count = len(changed)
                if count == 1:
                    status.setText("✓ " + t("settings.saved", count=count))
                else:
                    status.setText("✓ " + t("settings.saved_plural", count=count))
            else:
                status.setText("✓ " + t("settings.no_changes"))
        self.restart_banner.setVisible(bool(self._dirty_keys & _RESTART_KEYS))

    def _reset_defaults(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, t("settings.reset_title"),
            t("settings.reset_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        for key, default in DEFAULT_CONFIG.items():
            self.config[key] = default
            widget = self._field_widgets.get(key)
            if isinstance(widget, QComboBox):
                idx = widget.findText(str(default))
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(default))
        self._save_settings()


class LogsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._max_lines = 500
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        header = QWidget()
        header.setStyleSheet("background: transparent;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(t("logs.title"))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 22px; font-weight: 700; background: transparent; letter-spacing: -0.3px;")
        h_layout.addWidget(title)

        h_layout.addStretch()

        clear_btn = QPushButton(t("logs.clear"))
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 64, 112, 0.08);
                color: {Theme.ACCENT_ERROR};
                border: 1px solid rgba(255, 64, 112, 0.2);
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 64, 112, 0.18);
            }}
        """)
        clear_btn.clicked.connect(self._clear_logs)
        h_layout.addWidget(clear_btn)

        layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.BORDER}; border: none; max-height: 1px;")
        layout.addWidget(sep)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: rgba(12, 12, 22, 0.7);
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.CARD_RADIUS};
                padding: 14px;
                font-family: {Theme.FONT_MONO};
                font-size: 12px;
                line-height: 1.6;
            }}
        """)
        layout.addWidget(self.log_view, 1)

    def append_log(self, level, message):
        colors = {
            "info": Theme.TEXT_SECONDARY,
            "debug": Theme.TEXT_MUTED,
            "warning": Theme.ACCENT_WARNING,
            "error": Theme.ACCENT_ERROR,
            "critical": Theme.ACCENT_ERROR,
        }
        color = colors.get(level, Theme.TEXT_PRIMARY)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_view.appendPlainText(f"[{timestamp}] [{level.upper()}] {message}")

        doc = self.log_view.document()
        if doc.blockCount() > self._max_lines:
            cursor = self.log_view.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            for _ in range(doc.blockCount() - self._max_lines):
                cursor.select(cursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()

    def _clear_logs(self):
        self.log_view.clear()


class MonitorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel(t("monitor.title"))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 22px; font-weight: 700; background: transparent; letter-spacing: -0.3px;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.BORDER}; border: none; max-height: 1px;")
        layout.addWidget(sep)

        self.monitor = SystemMonitorCard()
        layout.addWidget(self.monitor, 1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.assistant = Assistant()
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_tray()
        self.setup_events()
        self.start_refresh_timer()
        tr.on_change(self.retranslate_ui)

    def setup_ui(self):
        self.setWindowTitle(t("app.name"))
        self.setMinimumSize(1024, 720)
        self.resize(1200, 800)
        self.setStyleSheet(Theme.get_stylesheet())

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.navigation_requested.connect(self._on_sidebar_nav)
        main_layout.addWidget(self.sidebar)

        content_area = QWidget()
        content_area.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {Theme.TEXT_MUTED};
                padding: 12px 28px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 13px;
                font-weight: 500;
                letter-spacing: 0.3px;
            }}
            QTabBar::tab:selected {{
                color: {Theme.ACCENT_PRIMARY};
                border-bottom: 2px solid {Theme.ACCENT_PRIMARY};
            }}
            QTabBar::tab:hover {{
                color: {Theme.TEXT_SECONDARY};
            }}
        """)
        content_layout.addWidget(self.tabs)

        main_layout.addWidget(content_area, 1)

        self.dashboard = DashboardTab(self)
        self.skills_tab = SkillsTab()
        self.settings_tab = SettingsTab(self)
        self.logs_tab = LogsTab()
        self.monitor_tab = MonitorTab()
        self.dev_mode_tab = DevModeTab(self)
        self.voice_tab = VoiceTab(self)
        self.memory_tab = MemoryTab()
        self.desktop_tab = DesktopTab()
        self.workflows_tab = WorkflowsTab()
        self.diagnostics_tab = DiagnosticsTab()
        self.health_tab = HealthTab()

        self._tab_labels = [
            t("sidebar.dashboard"), t("sidebar.skills"), t("sidebar.settings"),
            t("sidebar.logs"), t("sidebar.monitor"), t("sidebar.dev_mode"),
            t("sidebar.voice"), t("sidebar.memory"), t("sidebar.desktop"),
            t("sidebar.workflows"), t("sidebar.diagnostics"), t("sidebar.health"),
        ]
        tabs_data = [
            self.dashboard, self.skills_tab, self.settings_tab, self.logs_tab,
            self.monitor_tab, self.dev_mode_tab, self.voice_tab, self.memory_tab,
            self.desktop_tab, self.workflows_tab, self.diagnostics_tab, self.health_tab,
        ]
        for i, tab in enumerate(tabs_data):
            self.tabs.addTab(tab, self._tab_labels[i])

        self.notifications = NotificationManager(self)
        self.notifications.setFixedWidth(360)
        self.notifications.move(self.width() - 380, 60)

        self.command_palette = CommandPalette(self)
        self.command_palette.command_selected.connect(self.process_command)
        self.command_palette.closed.connect(self._focus_input)

    def retranslate_ui(self):
        self.setWindowTitle(t("app.name"))
        self.tray_icon.setToolTip(t("app.title"))
        new_tab_labels = [
            t("sidebar.dashboard"), t("sidebar.skills"), t("sidebar.settings"),
            t("sidebar.logs"), t("sidebar.monitor"), t("sidebar.dev_mode"),
            t("sidebar.voice"), t("sidebar.memory"), t("sidebar.desktop"),
            t("sidebar.workflows"), t("sidebar.diagnostics"), t("sidebar.health"),
        ]
        for i, label in enumerate(new_tab_labels):
            self.tabs.setTabText(i, label)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Return"), self, self._focus_input)
        QShortcut(QKeySequence("Ctrl+L"), self, self._focus_input)
        QShortcut(QKeySequence("Ctrl+W"), self, self.close)
        QShortcut(QKeySequence("Escape"), self, self._minimize_to_tray)
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self.tabs.setCurrentIndex(0))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self.tabs.setCurrentIndex(1))
        QShortcut(QKeySequence("Ctrl+3"), self, lambda: self.tabs.setCurrentIndex(2))
        QShortcut(QKeySequence("Ctrl+4"), self, lambda: self.tabs.setCurrentIndex(3))
        QShortcut(QKeySequence("Ctrl+5"), self, lambda: self.tabs.setCurrentIndex(4))
        QShortcut(QKeySequence("Ctrl+6"), self, lambda: self.tabs.setCurrentIndex(5))
        QShortcut(QKeySequence("Ctrl+7"), self, lambda: self.tabs.setCurrentIndex(6))
        QShortcut(QKeySequence("Ctrl+8"), self, lambda: self.tabs.setCurrentIndex(7))
        QShortcut(QKeySequence("Ctrl+9"), self, lambda: self.tabs.setCurrentIndex(8))
        QShortcut(QKeySequence("Ctrl+0"), self, lambda: self.tabs.setCurrentIndex(9))
        QShortcut(QKeySequence("Ctrl+P"), self, self._toggle_palette)
        QShortcut(QKeySequence("Ctrl+K"), self, self._toggle_palette)

    def setup_tray(self):
        icon_path = Path(__file__).parent / "assets" / "tray_icon.png"
        if icon_path.exists():
            self.tray_icon = QSystemTrayIcon(QIcon(str(icon_path)), self)
        else:
            self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip(t("app.title"))

        tray_menu = QMenu()
        show_action = tray_menu.addAction(t("tray.show"))
        show_action.triggered.connect(self.show_and_focus)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction(t("tray.quit"))
        quit_action.triggered.connect(self.close)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_and_focus()

    def show_and_focus(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self._focus_input()

    def _focus_input(self):
        self.tabs.setCurrentIndex(0)
        self.dashboard.command_input.focus()

    def _toggle_palette(self):
        if self.command_palette.isVisible():
            self.command_palette.close()
        else:
            self.command_palette.show_palette()

    def _on_sidebar_nav(self, index):
        if index < self.tabs.count():
            self.tabs.setCurrentIndex(index)
            if index == 0:
                self._focus_input()

    def _minimize_to_tray(self):
        self.hide()
        self.tray_icon.showMessage(
            t("app.name"),
            t("app.running_background"),
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def closeEvent(self, event):
        event.ignore()
        self._minimize_to_tray()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.notifications.move(self.width() - 380, 60)

    def setup_events(self):
        events.on(EventType.ASSISTANT_STATE_CHANGED, self._on_state_changed)
        events.on(EventType.COMMAND_COMPLETED, self._on_command_completed)
        events.on(EventType.COMMAND_FAILED, self._on_command_failed)
        jarvis_log.on_log(self._on_log)

    def _on_state_changed(self, data):
        state = data.get("state", "idle")
        self.dashboard.status_indicator.set_state(state)
        state_map = {
            "idle": t("app.status_idle"),
            "listening": t("app.status_listening"),
            "processing": t("app.status_processing"),
            "ai_thinking": t("app.status_ai_thinking"),
        }
        self.dashboard.status_label.setText(state_map.get(state, state.replace("_", " ").title()))

        if state == "listening":
            self.dashboard.waveform.set_active(True)
            self.dashboard.waveform.setVisible(True)
            self.dashboard.thinking_anim.stop()
        elif state == "ai_thinking":
            self.dashboard.waveform.set_active(False)
            self.dashboard.waveform.setVisible(False)
            self.dashboard.thinking_anim.start()
        elif state == "processing":
            self.dashboard.waveform.set_active(False)
            self.dashboard.waveform.setVisible(False)
            self.dashboard.thinking_anim.stop()
        else:
            self.dashboard.waveform.set_active(False)
            self.dashboard.waveform.setVisible(False)
            self.dashboard.thinking_anim.stop()

    def _on_command_completed(self, data):
        self.dashboard.add_timeline_entry(data)
        skill = data.get("skill", "")
        response = data.get("response", "")
        if response and len(response) < 100:
            self.notifications.notify(response, "success", 3000)

    def _on_command_failed(self, data):
        self.dashboard.add_timeline_entry(data)
        response = data.get("response", t("app.command_failed"))
        self.notifications.notify(response[:100], "error", 5000)

    def _on_log(self, level, message):
        self.logs_tab.append_log(level, message)

    def process_command(self, command: str):
        result = self.assistant.process(command)

        if result.get("requires_confirmation"):
            dialog = ConfirmationDialog(command, result.get("reason"), self)
            dialog.confirmed.connect(self._execute_confirmed)
            if result.get("_gate_confirmation"):
                dialog.cancelled.connect(lambda cmd=command: self._handle_gate_cancellation(cmd))
            else:
                dialog.cancelled.connect(lambda: jarvis_log.info("Command cancelled by user"))
            dialog.exec()

    def _execute_confirmed(self, command):
        self.assistant.process(command, _skip_intent_gate=True)

    def _handle_gate_cancellation(self, command):
        jarvis_log.info(f"Gate confirmation cancelled, routing '{command}' to AI")
        self.assistant.process(command, _force_ai=True)

    def start_refresh_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_stats)
        self.timer.start(5000)

    def _refresh_stats(self):
        try:
            info = linux_auto.get_system_info()
            self.dashboard.update_stats(info)
        except Exception:
            pass

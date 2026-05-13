from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea,
)
from PyQt6.QtCore import Qt, QTimer

from jarvis.ui.theme import Theme
from jarvis.ui.i18n import t, tr


class StatCard(QWidget):
    def __init__(self, label: str, value: str = "...", icon: str = "", color: str = Theme.ACCENT_PRIMARY):
        super().__init__()
        self._value = value
        self._color = color
        self._label_widget = None
        self.value_label = None
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {Theme.BG_CARD_SOLID};
                border: 0.5px solid {Theme.BORDER};
                border-radius: {Theme.CARD_RADIUS};
            }}
        """)
        self.setMinimumSize(160, 80)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        self._label_widget = QLabel(label)
        self._label_widget.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 10px; font-weight: 500; background: transparent;")
        hl.addWidget(self._label_widget)
        hl.addStretch()
        layout.addWidget(header)
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: 600; background: transparent;")
        layout.addWidget(self.value_label)

    def set_value(self, val: str):
        self.value_label.setText(val)

    def set_label(self, text: str):
        self._label_widget.setText(text)


class DesktopTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._header = None
        self._desc = None
        self._refresh_btn = None
        self.cards: dict[str, StatCard] = {}
        self._card_defs = []
        self.setup_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(2000)
        self._refresh()
        tr.languageChanged.connect(self.retranslate_ui)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        self._header = QLabel(t("desktop.title"))
        self._header.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 22px; font-weight: 700; background: transparent;")
        layout.addWidget(self._header)

        self._desc = QLabel(t("desktop.description"))
        self._desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        layout.addWidget(self._desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.BORDER}; border: none; max-height: 0.5px;")
        layout.addWidget(sep)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 4, 0, 0)
        grid.setSpacing(10)

        self._card_defs = [
            ("active_app", "desktop.active_app", Theme.ACCENT_INFO),
            ("active_window", "desktop.active_window", Theme.ACCENT_SECONDARY),
            ("workspace", "desktop.workspace", Theme.ACCENT_PRIMARY),
            ("battery", "desktop.battery", Theme.ACCENT_SUCCESS),
            ("network", "desktop.network", Theme.ACCENT_INFO),
            ("media", "desktop.media", Theme.ACCENT_WARNING),
            ("monitors", "desktop.monitors", Theme.ACCENT_PRIMARY),
            ("cpu_top", "desktop.cpu_top", Theme.ACCENT_ERROR),
        ]
        for i, (key, label_key, color) in enumerate(self._card_defs):
            card = StatCard(t(label_key), "...", "", color)
            self.cards[key] = card
            grid.addWidget(card, i // 2, i % 2)

        grid.setRowStretch(len(self._card_defs) // 2 + 1, 1)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self._refresh_btn = QPushButton(t("desktop.refresh"))
        self._refresh_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(0,122,255,0.08); border: 0.5px solid {Theme.ACCENT_PRIMARY}44;
            border-radius: 14px; padding: 6px 18px; font-size: 12px; font-weight: 400; color: {Theme.ACCENT_PRIMARY}; }}
            QPushButton:hover {{ background-color: rgba(0,122,255,0.15); }}
        """)
        self._refresh_btn.clicked.connect(self._refresh)
        layout.addWidget(self._refresh_btn, 0, Qt.AlignmentFlag.AlignLeft)

    def retranslate_ui(self):
        self._header.setText(t("desktop.title"))
        self._desc.setText(t("desktop.description"))
        self._refresh_btn.setText(t("desktop.refresh"))
        for key, label_key, _ in self._card_defs:
            if key in self.cards:
                self.cards[key].set_label(t(label_key))

    def _refresh(self):
        try:
            from jarvis.system.desktop_state import DesktopState
            ds = DesktopState()
            desk = ds.get_state()
        except Exception:
            desk = {}

        self.cards["active_app"].set_value(desk.get("active_app", "N/A") or "N/A")
        self.cards["active_window"].set_value(desk.get("active_window", "N/A")[:60] or "N/A")
        self.cards["workspace"].set_value(desk.get("workspace", "N/A") or "N/A")

        batt = desk.get("battery", {})
        if isinstance(batt, dict):
            pct = batt.get("percentage", "?")
            status = batt.get("status", "")
            self.cards["battery"].set_value(f"{pct}% ({status})" if status else f"{pct}%")
        else:
            self.cards["battery"].set_value(str(batt))

        net = desk.get("network", {})
        if isinstance(net, dict):
            ssid = net.get("ssid", net.get("connected", "disconnected"))
            self.cards["network"].set_value(str(ssid))
        else:
            self.cards["network"].set_value(str(net))

        media = desk.get("media", {})
        if isinstance(media, dict):
            artist = media.get("artist", "")
            title = media.get("title", "")
            status = media.get("status", "stopped")
            txt = f"{artist} - {title}"[:50] if artist and title else status
            self.cards["media"].set_value(txt)
        else:
            self.cards["media"].set_value(str(media))

        monitors = desk.get("monitors", [])
        if isinstance(monitors, list) and monitors:
            txt = ", ".join(f"{m.get('w','?')}x{m.get('h','?')}" for m in monitors[:2])
            self.cards["monitors"].set_value(txt)
        else:
            self.cards["monitors"].set_value("N/A")

        cpu_top = desk.get("cpu_top", [])
        if isinstance(cpu_top, list) and cpu_top:
            lines = []
            for p in cpu_top[:3]:
                lines.append(f"{p.get('name','?')} {p.get('cpu','?')}%")
            self.cards["cpu_top"].set_value(" | ".join(lines))
        else:
            self.cards["cpu_top"].set_value("N/A")

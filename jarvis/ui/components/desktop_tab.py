from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea,
)
from PyQt6.QtCore import Qt, QTimer

from jarvis.ui.theme import Theme


class StatCard(QWidget):
    def __init__(self, label: str, value: str = "...", icon: str = "", color: str = Theme.ACCENT_PRIMARY):
        super().__init__()
        self._value = value
        self._color = color
        self.setStyleSheet(f"""
            StatCard {{
                background-color: rgba(20, 20, 38, 0.5);
                border: 1px solid {Theme.BORDER};
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
        if icon:
            ic = QLabel(icon)
            ic.setStyleSheet(f"font-size: 18px; background: transparent;")
            hl.addWidget(ic)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background: transparent;")
        hl.addWidget(lbl)
        hl.addStretch()
        layout.addWidget(header)
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: 700; background: transparent;")
        layout.addWidget(self.value_label)

    def set_value(self, val: str):
        self.value_label.setText(val)


class DesktopTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(2000)
        self._refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        header = QLabel("Desktop Awareness")
        header.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 22px; font-weight: 700; background: transparent; letter-spacing: -0.3px;")
        layout.addWidget(header)

        desc = QLabel("Real-time desktop state, active apps, system resources, and peripherals")
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
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 4, 0, 0)
        grid.setSpacing(10)

        self.cards = {}
        card_defs = [
            ("active_app", "Active App", "⚡", Theme.ACCENT_INFO),
            ("active_window", "Active Window", "⊞", Theme.ACCENT_SECONDARY),
            ("workspace", "Workspace", "◻", Theme.ACCENT_PRIMARY),
            ("battery", "Battery", "🔋", Theme.ACCENT_SUCCESS),
            ("network", "Network", "🌐", Theme.ACCENT_INFO),
            ("media", "Media", "♪", Theme.ACCENT_WARNING),
            ("monitors", "Monitors", "🖥", Theme.ACCENT_PRIMARY),
            ("cpu_top", "Top CPU", "⚙", Theme.ACCENT_ERROR),
        ]
        for i, (key, label, icon, color) in enumerate(card_defs):
            card = StatCard(label, "...", icon, color)
            self.cards[key] = card
            grid.addWidget(card, i // 2, i % 2)

        grid.setRowStretch(len(card_defs) // 2 + 1, 1)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        refresh_btn = QPushButton("Refresh Now")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(124,106,255,0.1); border: 1px solid {Theme.ACCENT_PRIMARY}44;
            border-radius: 6px; padding: 6px 18px; font-size: 12px; font-weight: 500; color: {Theme.ACCENT_PRIMARY}; }}
            QPushButton:hover {{ background-color: rgba(124,106,255,0.2); }}
        """)
        refresh_btn.clicked.connect(self._refresh)
        layout.addWidget(refresh_btn, 0, Qt.AlignmentFlag.AlignLeft)

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

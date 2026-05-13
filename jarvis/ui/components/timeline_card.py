from datetime import datetime

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen

from jarvis.ui.theme import Theme


STATUS_COLORS = {
    "ok": Theme.ACCENT_SUCCESS,
    "error": Theme.ACCENT_ERROR,
    "blocked": Theme.ACCENT_WARNING,
    "ai": Theme.ACCENT_INFO,
}

STATUS_ICONS = {
    "ok": "✓",
    "error": "✗",
    "blocked": "⚠",
    "ai": "◆",
}


class TimelineEntry(QWidget):
    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_SMALL};
            }}
            QWidget:hover {{
                background-color: {Theme.BG_CARD_HOVER};
                border-color: {Theme.BORDER_HEAVY};
            }}
        """)
        self.setMinimumHeight(52)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        status = self.entry.get("status", "ok")
        skill = self.entry.get("skill", "?")
        color = STATUS_COLORS.get(status, Theme.TEXT_TERTIARY)
        icon = STATUS_ICONS.get(status, "○")

        header = QWidget()
        header.setStyleSheet("background: transparent; border: none;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(8)

        status_label = QLabel(icon)
        status_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 600; background: transparent;")
        status_label.setFixedWidth(20)
        h_layout.addWidget(status_label)

        cmd = self.entry.get("command", "")
        cmd_label = QLabel(cmd)
        cmd_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-weight: 500; font-size: 13px; background: transparent;")
        cmd_label.setWordWrap(True)
        h_layout.addWidget(cmd_label, 1)

        elapsed = self.entry.get("execution_time", 0)
        if elapsed:
            time_label = QLabel(f"{elapsed:.2}s")
            time_label.setStyleSheet(f"color: {Theme.TEXT_TERTIARY}; font-size: 11px; background: transparent;")
            time_label.setFixedWidth(48)
            time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            h_layout.addWidget(time_label)

        c = QColor(color)
        skill_label = QLabel(skill)
        skill_label.setStyleSheet(f"""
            color: {color};
            font-size: 10px;
            background-color: rgba({c.red()}, {c.green()}, {c.blue()}, 0.1);
            border: none;
            border-radius: {Theme.RADIUS_TINY};
            padding: 2px 8px;
            font-weight: 600;
            letter-spacing: 0.3px;
        """)
        skill_label.setFixedWidth(60)
        skill_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(skill_label)

        layout.addWidget(header)

        response = self.entry.get("response", "")
        if response:
            resp_label = QLabel(response[:150] + ("..." if len(response) > 150 else ""))
            resp_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
            resp_label.setWordWrap(True)
            layout.addWidget(resp_label)


class TimelineCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._count = 0
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"""
            TimelineCard {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_CARD};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        header = QWidget()
        header.setStyleSheet("background: transparent;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Timeline")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: 600; background: transparent;")
        h_layout.addWidget(title)

        h_layout.addStretch()

        self.count_label = QLabel("0 commands")
        self.count_label.setStyleSheet(f"color: {Theme.TEXT_TERTIARY}; font-size: 11px; background: transparent;")
        self.count_label.setFixedWidth(80)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        h_layout.addWidget(self.count_label)

        layout.addWidget(header)

        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {Theme.SEPARATOR}; border: none;")
        layout.addWidget(separator)

        self.empty_label = QLabel("  No commands yet.\n  Type a command or click a quick action to get started.")
        self.empty_label.setStyleSheet(f"color: {Theme.TEXT_TERTIARY}; font-size: 12px; background: transparent; padding: 24px 0;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(6)
        self.container_layout.addStretch()

        scroll.setWidget(self.container)
        layout.addWidget(scroll, 1)

    def add_entry(self, entry: dict):
        self.empty_label.hide()
        widget = TimelineEntry(entry)
        self.container_layout.insertWidget(self.container_layout.count() - 1, widget)

        self._count += 1
        self.count_label.setText(f"{self._count} command{'s' if self._count != 1 else ''}")

        max_visible = 50
        while self.container_layout.count() - 1 > max_visible:
            item = self.container_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def clear(self):
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._count = 0
        self.count_label.setText("0 commands")

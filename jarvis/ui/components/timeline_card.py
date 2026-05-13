from datetime import datetime

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen

from jarvis.ui.theme import Theme
from jarvis.ui.i18n import t, tr


STATUS_COLORS = {
    "ok": Theme.ACCENT_SUCCESS,
    "error": Theme.ACCENT_ERROR,
    "blocked": Theme.ACCENT_WARNING,
    "ai": Theme.ACCENT_INFO,
}


class TimelineEntry(QWidget):
    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.BG_CARD_SOLID};
                border: 0.5px solid {Theme.BORDER};
                border-radius: 8px;
            }}
            QWidget:hover {{
                background-color: rgba(255, 255, 255, 0.05);
                border-color: rgba(0, 122, 255, 0.3);
            }}
        """)
        self.setMinimumHeight(56)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        status = self.entry.get("status", "ok")
        skill = self.entry.get("skill", "?")
        color = STATUS_COLORS.get(status, Theme.TEXT_MUTED)

        header = QWidget()
        header.setStyleSheet("background: transparent; border: none;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(8)

        cmd = self.entry.get("command", "")
        cmd_label = QLabel(cmd)
        cmd_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-weight: 500; font-size: 13px; background: transparent;")
        cmd_label.setWordWrap(True)
        h_layout.addWidget(cmd_label, 1)

        elapsed = self.entry.get("execution_time", 0)
        if elapsed:
            time_label = QLabel(f"{elapsed:.2}s")
            time_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px; background: transparent;")
            time_label.setFixedWidth(48)
            time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            h_layout.addWidget(time_label)

        c = QColor(color)
        skill_label = QLabel(skill)
        skill_label.setStyleSheet(f"""
            color: {color};
            font-size: 10px;
            background-color: rgba({c.red()}, {c.green()}, {c.blue()}, 0.12);
            border: none;
            border-radius: 4px;
            padding: 2px 8px;
            font-weight: 500;
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
        self._title = None
        self._count_label = None
        self._empty_label = None
        self.setup_ui()
        tr.languageChanged.connect(self.retranslate_ui)

    def setup_ui(self):
        self.setStyleSheet(f"""
            TimelineCard {{
                background-color: {Theme.BG_CARD_SOLID};
                border: 0.5px solid {Theme.BORDER};
                border-radius: {Theme.CARD_RADIUS};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        header = QWidget()
        header.setStyleSheet("background: transparent;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)

        self._title = QLabel(t("dashboard.timeline"))
        self._title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 15px; font-weight: 600; background: transparent;")
        h_layout.addWidget(self._title)

        h_layout.addStretch()

        self._count_label = QLabel(t("dashboard.command_count_singular", count=0))
        self._count_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px; background: transparent;")
        self._count_label.setFixedWidth(80)
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        h_layout.addWidget(self._count_label)

        layout.addWidget(header)

        separator = QWidget()
        separator.setFixedHeight(0.5)
        separator.setStyleSheet(f"background-color: {Theme.BORDER}; border: none;")
        layout.addWidget(separator)

        self._empty_label = QLabel(t("dashboard.no_commands"))
        self._empty_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 12px; background: transparent; padding: 24px 0;")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._empty_label)

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

    def retranslate_ui(self):
        self._title.setText(t("dashboard.timeline"))
        self._empty_label.setText(t("dashboard.no_commands"))
        self._update_count_label()

    def _update_count_label(self):
        if self._count == 1:
            self._count_label.setText(t("dashboard.command_count_singular", count=1))
        else:
            self._count_label.setText(t("dashboard.command_count", count=self._count))

    def add_entry(self, entry: dict):
        self._empty_label.hide()
        widget = TimelineEntry(entry)
        self.container_layout.insertWidget(self.container_layout.count() - 1, widget)

        self._count += 1
        self._update_count_label()

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
        self._update_count_label()

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath

from jarvis.ui.theme import Theme


class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked=True, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._hover = False
        self.setFixedSize(40, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        h = self.height()
        w = self.width()

        track_color = Theme.ACCENT_PRIMARY if self._checked else "rgba(255,255,255,0.15)"
        track = QColor(track_color)
        painter.setPen(Qt.PenStyle.NoPen)

        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, h / 2, h / 2)
        painter.setBrush(track)
        painter.drawPath(path)

        thumb_r = h - 6
        thumb_x = w - h + 3 if self._checked else 3
        thumb_y = 3

        thumb_gradient = QColor(255, 255, 255, 230 if self._checked else 180)
        painter.setBrush(thumb_gradient)
        painter.setPen(QPen(QColor(255, 255, 255, 50), 0.5))
        painter.drawEllipse(int(thumb_x), int(thumb_y), int(thumb_r), int(thumb_r))

        painter.end()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.update()
        self.toggled.emit(self._checked)

    def is_checked(self):
        return self._checked

    def set_checked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self.update()


class SkillCard(QWidget):
    def __init__(self, name: str, enabled: bool = True, permission_level: str = "normal", description: str = "", parent=None):
        super().__init__(parent)
        self.skill_name = name
        self._enabled = enabled
        self.permission_level = permission_level
        self._description = description
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"""
            SkillCard {{
                background-color: {Theme.BG_CARD_SOLID};
                border: 0.5px solid {Theme.BORDER};
                border-radius: 10px;
            }}
            SkillCard:hover {{
                background-color: rgba(255, 255, 255, 0.05);
                border-color: rgba(0, 122, 255, 0.3);
            }}
        """)
        self.setMinimumHeight(74)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        icon_label = QLabel(self._get_icon())
        icon_label.setStyleSheet(f"""
            font-size: 16px;
            color: {Theme.TEXT_SECONDARY};
            background: transparent;
            border: none;
        """)
        icon_label.setFixedWidth(30)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        text_area = QWidget()
        text_area.setStyleSheet("background: transparent; border: none;")
        t_layout = QVBoxLayout(text_area)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(2)

        name_label = QLabel(self.skill_name.capitalize())
        name_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        t_layout.addWidget(name_label)

        desc = self._description or self._default_description()
        desc_label = QLabel(desc)
        desc_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; background: transparent; border: none;")
        t_layout.addWidget(desc_label)

        layout.addWidget(text_area, 1)

        badge_color = Theme.ACCENT_SECONDARY if self.permission_level == "normal" else Theme.ACCENT_WARNING
        badge = QLabel(self.permission_level)
        badge.setStyleSheet(f"""
            color: {badge_color};
            font-size: 10px;
            font-weight: 500;
            background-color: {badge_color}1f;
            border: none;
            border-radius: 4px;
            padding: 2px 8px;
        """)
        badge.setFixedHeight(20)
        layout.addWidget(badge)

        self.toggle = ToggleSwitch(self._enabled)
        self.toggle.toggled.connect(self._on_toggle)
        layout.addWidget(self.toggle)

    def _get_icon(self):
        return ""

    def _default_description(self):
        descs = {
            "system": "System info, time, date, shutdown",
            "apps": "Launch apps, open projects, Docker",
            "browser": "Web search, open URLs",
            "media": "Volume and media playback control",
            "dev": "Dev mode, open projects, git",
            "opencode": "AI-assisted code changes",
        }
        return descs.get(self.skill_name, f"Handles {self.skill_name} commands")

    def _on_toggle(self, checked):
        self._enabled = checked

    @property
    def enabled(self):
        return self._enabled

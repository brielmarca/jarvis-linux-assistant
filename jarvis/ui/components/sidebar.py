from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor

from jarvis.ui.theme import Theme


NAV_ITEMS = [
    ("Dashboard", "◉", 0),
    ("Skills", "⚡", 1),
    ("Settings", "⚙", 2),
    ("Logs", "≡", 3),
    ("Monitor", "◎", 4),
    ("Dev Mode", "◆", 5),
    ("Voice", "♪", 6),
    ("Memory", "◈", 7),
    ("Desktop", "⊞", 8),
    ("Workflows", "⚡", 9),
    ("Diagnostics", "◉", 10),
    ("Health", "♥", 11),
]


class SidebarButton(QPushButton):
    def __init__(self, icon: str, label: str, active: bool = False, parent=None):
        super().__init__(parent)
        self._active = active
        self._icon = icon
        self._label = label
        self.setup_ui()

    def setup_ui(self):
        self.setText(f"{self._icon}  {self._label}")
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setChecked(self._active)
        self.update_style()

    def update_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(124, 106, 255, 0.12);
                    border: none;
                    border-radius: 8px;
                    padding: 10px 16px;
                    font-size: 12px;
                    font-weight: 600;
                    color: {Theme.ACCENT_PRIMARY};
                    text-align: left;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 16px;
                    font-size: 12px;
                    font-weight: 500;
                    color: {Theme.TEXT_SECONDARY};
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: rgba(124, 106, 255, 0.06);
                    color: {Theme.TEXT_PRIMARY};
                }}
            """)

    def set_active(self, active: bool):
        self._active = active
        self.setChecked(active)
        self.update_style()


class Sidebar(QWidget):
    navigation_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: list[SidebarButton] = []
        self.setup_ui()

    def setup_ui(self):
        self.setFixedWidth(180)
        self.setStyleSheet(f"""
            Sidebar {{
                background-color: rgba(10, 10, 18, 0.85);
                border-right: 1px solid {Theme.BORDER};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 16, 10, 16)
        layout.setSpacing(4)

        logo = QLabel("JARVIS")
        logo.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 18px; font-weight: 800; letter-spacing: 2px; background: transparent; padding: 8px 6px 16px 6px;")
        layout.addWidget(logo)

        for icon, label, idx in NAV_ITEMS:
            btn = SidebarButton(icon, label, active=(idx == 0))
            btn.clicked.connect(lambda checked, i=idx: self._navigate(i))
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        version = QLabel("v1.0")
        version.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 10px; background: transparent; padding: 8px 6px;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

    def _navigate(self, index: int):
        for i, btn in enumerate(self._buttons):
            btn.set_active(i == index)
        self.navigation_requested.emit(index)

    def set_active(self, index: int):
        for i, btn in enumerate(self._buttons):
            btn.set_active(i == index)

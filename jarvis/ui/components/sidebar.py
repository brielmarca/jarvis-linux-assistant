from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

from jarvis.ui.theme import Theme


NAV_ITEMS = [
    ("Dashboard", 0),
    ("Skills", 1),
    ("Settings", 2),
    ("Logs", 3),
    ("Monitor", 4),
    ("Dev Mode", 5),
    ("Voice", 6),
    ("Memory", 7),
    ("Desktop", 8),
    ("Workflows", 9),
    ("Diagnostics", 10),
    ("Health", 11),
]


class SidebarButton(QPushButton):
    def __init__(self, label: str, active: bool = False, parent=None):
        super().__init__(parent)
        self._active = active
        self._label = label
        self.setup_ui()

    def setup_ui(self):
        self.setText(self._label)
        self.setFixedHeight(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setChecked(self._active)
        self.update_style()

    def update_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.BG_SELECTED};
                    border: none;
                    border-radius: 6px;
                    padding: 5px 12px;
                    font-size: 12px;
                    font-weight: 600;
                    color: {Theme.TEXT_PRIMARY};
                    text-align: left;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                    padding: 5px 12px;
                    font-size: 12px;
                    font-weight: 400;
                    color: {Theme.TEXT_SECONDARY};
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {Theme.BG_HOVER};
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
        self.setFixedWidth(Theme.SIDEBAR_WIDTH)
        self.setStyleSheet(f"""
            Sidebar {{
                background-color: {Theme.BG_SIDEBAR};
                border-right: 1px solid {Theme.SEPARATOR};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 14, 10, 14)
        layout.setSpacing(1)

        logo = QLabel("Jarvis")
        logo.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY}; font-size: 16px; font-weight: 700;
            letter-spacing: -0.3px; background: transparent; padding: 8px 12px 18px 12px;
        """)
        layout.addWidget(logo)

        for label, idx in NAV_ITEMS:
            btn = SidebarButton(label, active=(idx == 0))
            btn.clicked.connect(lambda checked, i=idx: self._navigate(i))
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        version = QLabel("v1.0")
        version.setStyleSheet(f"""
            color: {Theme.TEXT_TERTIARY}; font-size: 10px;
            background: transparent; padding: 8px 12px;
        """)
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

    def _navigate(self, index: int):
        for i, btn in enumerate(self._buttons):
            btn.set_active(i == index)
        self.navigation_requested.emit(index)

    def set_active(self, index: int):
        for i, btn in enumerate(self._buttons):
            btn.set_active(i == index)

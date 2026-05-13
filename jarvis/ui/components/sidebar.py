from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

from jarvis.ui.theme import Theme
from jarvis.ui.i18n import t, tr


NAV_ITEMS = [
    ("sidebar.dashboard", 0),
    ("sidebar.skills", 1),
    ("sidebar.settings", 2),
    ("sidebar.logs", 3),
    ("sidebar.monitor", 4),
    ("sidebar.dev_mode", 5),
    ("sidebar.voice", 6),
    ("sidebar.memory", 7),
    ("sidebar.desktop", 8),
    ("sidebar.workflows", 9),
    ("sidebar.diagnostics", 10),
    ("sidebar.health", 11),
]


class SidebarButton(QPushButton):
    def __init__(self, label_key: str, active: bool = False, parent=None):
        super().__init__(parent)
        self._label_key = label_key
        self._active = active
        self.setup_ui()

    def setup_ui(self):
        self.setText(t(self._label_key))
        self.setFixedHeight(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setChecked(self._active)
        self.update_style()

    def update_label(self):
        self.setText(t(self._label_key))

    def update_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.BG_SELECTED};
                    border: none;
                    border-radius: 6px;
                    padding: 5px 12px;
                    font-size: 12px;
                    font-weight: 500;
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
        self._logo = None
        self._version = None
        self.setup_ui()
        tr.languageChanged.connect(self.retranslate_ui)

    def setup_ui(self):
        self.setFixedWidth(Theme.SIDEBAR_WIDTH)
        self.setStyleSheet(f"""
            Sidebar {{
                background-color: {Theme.BG_SIDEBAR};
                border-right: 0.5px solid {Theme.SEPARATOR};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 14, 10, 14)
        layout.setSpacing(1)

        self._logo = QLabel(t("sidebar.logo"))
        self._logo.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY}; font-size: 16px; font-weight: 600;
            background: transparent; padding: 8px 12px 18px 12px;
        """)
        layout.addWidget(self._logo)

        for label_key, idx in NAV_ITEMS:
            btn = SidebarButton(label_key, active=(idx == 0))
            btn.clicked.connect(lambda checked, i=idx: self._navigate(i))
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        self._version = QLabel(t("app.version"))
        self._version.setStyleSheet(f"""
            color: {Theme.TEXT_TERTIARY}; font-size: 10px;
            background: transparent; padding: 8px 12px;
        """)
        self._version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._version)

    def retranslate_ui(self):
        self._logo.setText(t("sidebar.logo"))
        self._version.setText(t("app.version"))
        for btn in self._buttons:
            btn.update_label()

    def _navigate(self, index: int):
        for i, btn in enumerate(self._buttons):
            btn.set_active(i == index)
        self.navigation_requested.emit(index)

    def set_active(self, index: int):
        for i, btn in enumerate(self._buttons):
            btn.set_active(i == index)

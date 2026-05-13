from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeyEvent

from jarvis.ui.theme import Theme
from jarvis.i18n import t


QUICK_COMMANDS = [
    ("open terminal", t("palette.open_terminal")),
    ("open firefox", t("palette.open_firefox")),
    ("system info", t("palette.system_info")),
    ("increase volume", t("palette.volume_up")),
    ("decrease volume", t("palette.volume_down")),
    ("mute", t("palette.mute")),
    ("play/pause", t("palette.play_pause")),
    ("next track", t("palette.next_track")),
    ("search for ", t("palette.search")),
    ("open project ", t("palette.open_project")),
    ("git status", t("palette.git_status")),
    ("programming mode", t("palette.programming_mode")),
    ("docker status", t("palette.docker_status")),
    ("shutdown", t("palette.shutdown")),
    ("reboot", t("palette.reboot")),
    ("reload skills", t("palette.reload_skills")),
    ("remember ", t("palette.remember")),
    ("recall ", t("palette.recall")),
]


class CommandPalette(QWidget):
    command_selected = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowFlags(
            Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 400)

        outer = QWidget()
        outer.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(14, 14, 26, 0.95);
                border: 1px solid {Theme.BORDER};
                border-radius: 14px;
            }}
        """)
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t("palette.placeholder"))
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(20, 20, 40, 0.6);
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.ACCENT_PRIMARY}33;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {Theme.ACCENT_PRIMARY};
            }}
        """)
        self.search_input.textChanged.connect(self._filter)
        layout.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                color: {Theme.TEXT_SECONDARY};
                padding: 10px 14px;
                border-radius: 6px;
                font-size: 13px;
            }}
            QListWidget::item:selected {{
                background-color: rgba(124, 106, 255, 0.15);
                color: {Theme.TEXT_PRIMARY};
            }}
            QListWidget::item:hover {{
                background-color: rgba(124, 106, 255, 0.08);
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(self.list_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(outer)

        self._populate()
        self.search_input.returnPressed.connect(self._execute_selected)
        self.list_widget.itemClicked.connect(lambda item: self._execute(item))
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)

    def _populate(self, filter_text: str = ""):
        self.list_widget.clear()
        ft = filter_text.lower()
        for cmd, desc in QUICK_COMMANDS:
            if ft in cmd.lower() or ft in desc.lower():
                item = QListWidgetItem(f"  {cmd}")
                item.setData(Qt.ItemDataRole.UserRole, cmd)
                item.setToolTip(desc)
                self.list_widget.addItem(item)

    def _filter(self, text: str):
        self._populate(text)

    def _execute_selected(self):
        item = self.list_widget.currentItem()
        if item:
            self._execute(item)

    def _execute(self, item):
        cmd = item.data(Qt.ItemDataRole.UserRole)
        if cmd:
            self.command_selected.emit(cmd)
            self.close()

    def _on_selection_changed(self):
        pass

    def show_palette(self):
        self._populate()
        self.search_input.clear()
        self.search_input.setFocus()
        parent = self.parent()
        if parent:
            center = parent.geometry().center()
            x = center.x() - self.width() / 2
            y = center.y() - self.height() / 2 - 60
            self.move(int(x), int(y))
        self.show()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Down:
            idx = self.list_widget.currentRow()
            self.list_widget.setCurrentRow(min(idx + 1, self.list_widget.count() - 1))
        elif event.key() == Qt.Key.Key_Up:
            idx = self.list_widget.currentRow()
            self.list_widget.setCurrentRow(max(idx - 1, 0))
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)

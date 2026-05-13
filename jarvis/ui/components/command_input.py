from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent

from jarvis.ui.theme import Theme


class CommandInput(QWidget):
    command_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = []
        self._history_index = -1
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.mic_btn = QPushButton()
        self.mic_btn.setFixedSize(44, 44)
        self.mic_btn.setToolTip("Voice input (not available)")
        self.mic_btn.setEnabled(False)
        self.mic_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                border: 0.5px solid {Theme.BORDER};
                border-radius: 22px;
                font-size: 18px;
                padding: 0;
            }}
            QPushButton:hover {{
                border-color: {Theme.ACCENT_SECONDARY};
            }}
        """)
        layout.addWidget(self.mic_btn)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask me anything...")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_PRIMARY};
                border: 0.5px solid {Theme.BORDER};
                border-radius: 22px;
                padding: 11px 20px;
                font-size: 14px;
                font-weight: 400;
            }}
            QLineEdit:focus {{
                border-color: {Theme.ACCENT_PRIMARY};
                background-color: rgba(0, 122, 255, 0.04);
            }}
        """)
        self.input_field.returnPressed.connect(self._submit)
        layout.addWidget(self.input_field, 1)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("accent")
        self.send_btn.setFixedWidth(90)
        self.send_btn.setFixedHeight(44)
        self.send_btn.clicked.connect(self._submit)
        layout.addWidget(self.send_btn)

    def _submit(self):
        text = self.input_field.text().strip()
        if text:
            self._history.append(text)
            self._history_index = len(self._history)
            self.command_submitted.emit(text)
            self.input_field.clear()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Up and self._history:
            if self._history_index > 0:
                self._history_index -= 1
                self.input_field.setText(self._history[self._history_index])
        elif event.key() == Qt.Key.Key_Down and self._history:
            if self._history_index < len(self._history) - 1:
                self._history_index += 1
                self.input_field.setText(self._history[self._history_index])
            else:
                self._history_index = len(self._history)
                self.input_field.clear()
        elif event.key() == Qt.Key.Key_Escape:
            self.input_field.clear()
        else:
            super().keyPressEvent(event)

    def focus(self):
        self.input_field.setFocus()

    def set_placeholder(self, text):
        self.input_field.setPlaceholderText(text)

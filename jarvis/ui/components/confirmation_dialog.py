from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from jarvis.ui.theme import Theme
from jarvis.ui.i18n import t, tr


class ConfirmationDialog(QDialog):
    confirmed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, command: str, reason: str = None, parent=None):
        super().__init__(parent)
        self.command = command
        self.reason = reason
        self._title_label = None
        self._cancel_btn = None
        self._confirm_btn = None
        self.setup_ui()
        tr.languageChanged.connect(self.retranslate_ui)

    def setup_ui(self):
        self.setWindowTitle(t("confirmation.title"))
        self.setFixedSize(480, 220)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_CARD_SOLID};
                border: 0.5px solid {Theme.BORDER};
                border-radius: 16px;
            }}
        """)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(10)

        self._title_label = QLabel(t("confirmation.confirm_command"))
        self._title_label.setStyleSheet(f"font-size: 17px; font-weight: 600; color: {Theme.TEXT_PRIMARY}; background: transparent;")
        header.addWidget(self._title_label, 1)

        layout.addLayout(header)

        cmd_box = QFrame()
        cmd_box.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 69, 58, 0.08);
                border: 0.5px solid rgba(255, 69, 58, 0.2);
                border-radius: 8px;
                padding: 10px 14px;
            }}
        """)
        cmd_layout = QVBoxLayout(cmd_box)
        cmd_layout.setContentsMargins(14, 10, 14, 10)
        cmd_layout.setSpacing(4)

        cmd_label = QLabel(t("confirmation.requires"))
        cmd_label.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_SECONDARY}; background: transparent;")
        cmd_layout.addWidget(cmd_label)

        cmd_text = QLabel(self.command)
        cmd_text.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {Theme.ACCENT_ERROR};
            font-family: {Theme.FONT_MONO};
            background: transparent;
        """)
        cmd_text.setWordWrap(True)
        cmd_layout.addWidget(cmd_text)

        if self.reason:
            reason_label = QLabel(self.reason)
            reason_label.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED}; background: transparent;")
            cmd_layout.addWidget(reason_label)

        layout.addWidget(cmd_box)

        layout.addStretch()

        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        self._cancel_btn = QPushButton(t("confirmation.cancel"))
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 69, 58, 0.08);
                border: 0.5px solid rgba(255, 69, 58, 0.3);
                border-radius: 18px;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: 500;
                color: {Theme.ACCENT_ERROR};
            }}
            QPushButton:hover {{
                background-color: rgba(255, 69, 58, 0.15);
            }}
        """)
        self._cancel_btn.clicked.connect(self._cancel)
        buttons.addWidget(self._cancel_btn)

        buttons.addStretch()

        self._confirm_btn = QPushButton(t("confirmation.execute"))
        self._confirm_btn.setObjectName("accent")
        self._confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT_PRIMARY};
                border: none;
                border-radius: 18px;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: 500;
                color: white;
            }}
            QPushButton:hover {{
                background-color: #0066CC;
            }}
        """)
        self._confirm_btn.clicked.connect(self._confirm)
        self._confirm_btn.setDefault(True)
        buttons.addWidget(self._confirm_btn)

        layout.addLayout(buttons)

    def retranslate_ui(self):
        self.setWindowTitle(t("confirmation.title"))
        self._title_label.setText(t("confirmation.confirm_command"))
        self._cancel_btn.setText(t("confirmation.cancel"))
        self._confirm_btn.setText(t("confirmation.execute"))

    def _confirm(self):
        self.confirmed.emit(self.command)
        self.accept()

    def _cancel(self):
        self.cancelled.emit()
        self.reject()

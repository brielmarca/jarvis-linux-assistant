from PyQt6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter

from jarvis.ui.theme import Theme


class SplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QWidget().grab() if hasattr(QWidget, 'grab') else None
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 240)

        self.widget = QWidget(self)
        self.widget.setGeometry(0, 0, 400, 240)
        self.widget.setStyleSheet(f"""
            background-color: {Theme.BG_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 16px;
        """)

        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        title = QLabel("Jarvis")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY}; font-size: 32px; font-weight: 700;
            letter-spacing: -0.5px; background: transparent;
        """)
        layout.addWidget(title)

        subtitle = QLabel("Linux Assistant")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            color: {Theme.ACCENT_PRIMARY}; font-size: 13px; font-weight: 500;
            letter-spacing: 3px; background: transparent;
        """)
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"""
            color: {Theme.TEXT_TERTIARY}; font-size: 11px; background: transparent;
        """)
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(2)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ background-color: rgba(50,50,80,0.2); border: none; border-radius: 1px; }}
            QProgressBar::chunk {{ background-color: {Theme.ACCENT_PRIMARY}; border-radius: 1px; }}
        """)
        layout.addWidget(self.progress)

        version = QLabel("v1.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(f"""
            color: {Theme.TEXT_TERTIARY}; font-size: 9px; background: transparent;
        """)
        layout.addWidget(version)

    def set_status(self, text: str):
        self.status_label.setText(text)
        self.status_label.repaint()

    def finish_with(self, window):
        self.finish(window)

    def closeEvent(self, event):
        self.hide()
        event.accept()

from PyQt6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter

from jarvis.ui.theme import Theme
from jarvis.i18n import t


class SplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QWidget().grab() if hasattr(QWidget, 'grab') else None
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(440, 260)

        self.widget = QWidget(self)
        self.widget.setGeometry(0, 0, 440, 260)
        self.widget.setStyleSheet(f"""
            background-color: {Theme.BG_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: 20px;
        """)

        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        title = QLabel(t("splash.title"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY}; font-size: 36px; font-weight: 800;
            letter-spacing: -1px; background: transparent;
        """)
        layout.addWidget(title)

        subtitle = QLabel(t("splash.subtitle"))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            color: {Theme.ACCENT_PRIMARY}; font-size: 14px; font-weight: 500;
            letter-spacing: 4px; background: transparent;
        """)
        layout.addWidget(subtitle)

        layout.addSpacing(12)

        self.status_label = QLabel(t("splash.initializing"))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"""
            color: {Theme.TEXT_MUTED}; font-size: 11px; background: transparent;
        """)
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(3)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ background-color: rgba(50,50,80,0.3); border: none; border-radius: 2px; }}
            QProgressBar::chunk {{ background-color: {Theme.ACCENT_PRIMARY}; border-radius: 2px; }}
        """)
        layout.addWidget(self.progress)

        version = QLabel(t("app.version"))
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 9px; background: transparent;")
        layout.addWidget(version)

    def set_status(self, text: str):
        self.status_label.setText(text)
        self.status_label.repaint()

    def finish_with(self, window):
        self.finish(window)

    def closeEvent(self, event):
        self.hide()
        event.accept()

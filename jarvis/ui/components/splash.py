from PyQt6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter

from jarvis.ui.theme import Theme
from jarvis.ui.i18n import t, tr


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
            border: 0.5px solid {Theme.BORDER};
            border-radius: 20px;
        """)

        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        self._title = QLabel(t("splash.title"))
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(f"""
            color: {Theme.TEXT_PRIMARY}; font-size: 36px; font-weight: 700;
            background: transparent;
        """)
        layout.addWidget(self._title)

        self._subtitle = QLabel(t("splash.subtitle"))
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle.setStyleSheet(f"""
            color: {Theme.ACCENT_PRIMARY}; font-size: 14px; font-weight: 400;
            letter-spacing: 4px; background: transparent;
        """)
        layout.addWidget(self._subtitle)

        layout.addSpacing(12)

        self._status_label = QLabel(t("splash.initializing"))
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(f"""
            color: {Theme.TEXT_MUTED}; font-size: 11px; background: transparent;
        """)
        layout.addWidget(self._status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(3)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ background-color: rgba(255,255,255,0.08); border: none; border-radius: 2px; }}
            QProgressBar::chunk {{ background-color: {Theme.ACCENT_PRIMARY}; border-radius: 2px; }}
        """)
        layout.addWidget(self.progress)

        version = QLabel(t("app.version"))
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 9px; background: transparent;")
        layout.addWidget(version)

        tr.languageChanged.connect(self.retranslate_ui)

    def retranslate_ui(self):
        self._title.setText(t("splash.title"))
        self._subtitle.setText(t("splash.subtitle"))
        self._status_label.setText(t("splash.initializing"))

    def set_status(self, text: str):
        self._status_label.setText(text)
        self._status_label.repaint()

    def finish_with(self, window):
        self.finish(window)

    def closeEvent(self, event):
        self.hide()
        event.accept()

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect
from PyQt6.QtGui import QColor

from jarvis.ui.theme import Theme


NOTIFICATION_TYPES = {
    "info": (Theme.ACCENT_INFO, "○"),
    "success": (Theme.ACCENT_SUCCESS, "✓"),
    "warning": (Theme.ACCENT_WARNING, "⚠"),
    "error": (Theme.ACCENT_ERROR, "✗"),
}


class NotificationWidget(QWidget):
    dismissed = pyqtSignal(object)

    def __init__(self, message: str, ntype: str = "info", duration: int = 4000, parent=None):
        super().__init__(parent)
        self._message = message
        self._type = ntype
        self._duration = duration
        self._alpha = 0.0
        self.setup_ui()
        self._start_animation()

    def setup_ui(self):
        color, icon = NOTIFICATION_TYPES.get(self._type, NOTIFICATION_TYPES["info"])
        self.setStyleSheet(f"""
            NotificationWidget {{
                background-color: rgba(16, 16, 32, 0.92);
                border: 1px solid {color}44;
                border-radius: 10px;
            }}
        """)
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 700; background: transparent;")
        icon_label.setFixedWidth(20)
        layout.addWidget(icon_label)

        msg_label = QLabel(self._message)
        msg_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px; background: transparent;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label, 1)

        if self._duration > 0:
            self._hide_timer = QTimer(self)
            self._hide_timer.setSingleShot(True)
            self._hide_timer.timeout.connect(self._fade_out)
            self._hide_timer.start(self._duration)

    def _start_animation(self):
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(300)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def _fade_out(self):
        self._anim_out = QPropertyAnimation(self, b"windowOpacity")
        self._anim_out.setDuration(300)
        self._anim_out.setStartValue(1.0)
        self._anim_out.setEndValue(0.0)
        self._anim_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._anim_out.finished.connect(lambda: self.dismissed.emit(self))
        self._anim_out.start()


class NotificationManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        self._layout = layout

        self.setFixedWidth(360)

    def notify(self, message: str, ntype: str = "info", duration: int = 4000):
        notification = NotificationWidget(message, ntype, duration)
        notification.dismissed.connect(self._remove)
        self._layout.insertWidget(0, notification)

    def _remove(self, notification):
        self._layout.removeWidget(notification)
        notification.deleteLater()

    def clear_all(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

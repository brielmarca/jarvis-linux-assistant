import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QPainterPath, QPen

from jarvis.ui.theme import Theme


class StatusIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = "idle"
        self._phase = 0.0
        self.setFixedSize(18, 18)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def set_state(self, state):
        self._state = state
        self.update()

    def _tick(self):
        self._phase = (self._phase + 0.04) % (math.pi * 2)
        if self._state in ("processing", "ai_thinking", "listening"):
            self.update()

    def state_color_pair(self):
        if self._state == "idle":
            return QColor(Theme.ACCENT_SUCCESS), QColor(Theme.ACCENT_SUCCESS_GLOW)
        elif self._state == "processing":
            return QColor(Theme.ACCENT_PRIMARY), QColor(Theme.ACCENT_PRIMARY_GLOW)
        elif self._state == "ai_thinking":
            return QColor(Theme.ACCENT_WARNING), QColor(Theme.ACCENT_WARNING_GLOW)
        elif self._state == "listening":
            return QColor(Theme.ACCENT_SECONDARY), QColor(Theme.ACCENT_SECONDARY_GLOW)
        elif self._state == "error":
            return QColor(Theme.ACCENT_ERROR), QColor(Theme.ACCENT_ERROR_GLOW)
        return QColor(Theme.ACCENT_SUCCESS), QColor(Theme.ACCENT_SUCCESS_GLOW)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c, glow_c = self.state_color_pair()
        cx, cy = self.rect().center().x(), self.rect().center().y()
        r = self.width() / 2

        breath = 1.0
        if self._state in ("processing", "ai_thinking", "listening"):
            breath = 0.7 + 0.3 * abs(math.sin(self._phase))

        glow_r = r * 2.5 * breath
        gradient = QRadialGradient(QPointF(cx, cy), glow_r)
        gc = QColor(c)
        gc.setAlpha(int(70 * breath))
        gradient.setColorAt(0, gc)
        gc2 = QColor(c)
        gc2.setAlpha(15)
        gradient.setColorAt(0.4, gc2)
        gradient.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 0))
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

        dot_r = r - 2
        dot_gradient = QRadialGradient(QPointF(cx - 1, cy - 1), dot_r)
        dot_gradient.setColorAt(0, QColor(255, 255, 255, 200))
        dot_gradient.setColorAt(0.6, c)
        dot_gradient.setColorAt(1, c.darker(120))
        painter.setBrush(dot_gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), dot_r, dot_r)

        painter.end()

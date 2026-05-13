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
        self.setFixedSize(10, 10)

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

    def state_color(self):
        if self._state == "idle":
            return QColor(Theme.ACCENT_SUCCESS)
        elif self._state == "processing":
            return QColor(Theme.ACCENT_PRIMARY)
        elif self._state == "ai_thinking":
            return QColor(Theme.ACCENT_WARNING)
        elif self._state == "listening":
            return QColor(Theme.ACCENT_SECONDARY)
        elif self._state == "error":
            return QColor(Theme.ACCENT_ERROR)
        return QColor(Theme.ACCENT_SUCCESS)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = self.state_color()
        cx, cy = self.rect().center().x(), self.rect().center().y()
        r = self.width() / 2

        breath = 1.0
        if self._state in ("processing", "ai_thinking", "listening"):
            breath = 0.6 + 0.4 * abs(math.sin(self._phase))

        dot_r = r - 1
        c.setAlpha(int(200 * breath))
        painter.setBrush(c)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), dot_r, dot_r)

        painter.end()

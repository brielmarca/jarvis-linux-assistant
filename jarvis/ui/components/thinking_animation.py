import math

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QPen, QPainterPath

from jarvis.ui.theme import Theme


class ThinkingAnimation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._phase = 0.0
        self._visible = False
        self._dot_count = 3

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

        self.setFixedSize(80, 30)

    def start(self):
        self._visible = True
        self.show()

    def stop(self):
        self._visible = False
        self.hide()

    def _tick(self):
        if self._visible:
            self._phase += 0.06
            self.update()

    def paintEvent(self, event):
        if not self._visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cy = h / 2
        spacing = 14
        total_w = self._dot_count * spacing
        start_x = (w - total_w) / 2 + spacing / 2
        dot_r = 4

        for i in range(self._dot_count):
            delay = i * 0.8
            bounce = abs(math.sin(self._phase + delay))
            scale = 0.5 + 0.5 * bounce
            r = dot_r * scale

            x = start_x + i * spacing
            y = cy - (bounce * 6)

            alpha = int(100 + 155 * bounce)
            color = QColor(Theme.ACCENT_PRIMARY)
            color.setAlpha(alpha)

            gradient = QRadialGradient(QPointF(x, y), r)
            gradient.setColorAt(0, QColor(255, 255, 255, 200))
            gradient.setColorAt(0.5, color)
            gradient.setColorAt(1, color.darker(130))
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(x, y), r, r)

        painter.end()

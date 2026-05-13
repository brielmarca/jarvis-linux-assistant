import math
import random

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen

from jarvis.ui.theme import Theme


class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._amplitude = 0.0
        self._target_amplitude = 0.0
        self._phase = 0.0
        self._bars = 48
        self._smoothing = 0.08
        self._active = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

        self.setMinimumHeight(50)
        self.setMaximumHeight(100)

    def set_active(self, active: bool):
        self._active = active
        self._target_amplitude = 0.8 if active else 0.0

    def set_amplitude(self, amp: float):
        self._target_amplitude = max(0.0, min(1.0, amp))

    def _tick(self):
        self._amplitude += (self._target_amplitude - self._amplitude) * self._smoothing
        self._phase += 0.03
        if self._amplitude > 0.01 or self._target_amplitude > 0.01:
            self.update()

    def paintEvent(self, event):
        if self._amplitude < 0.005 and not self._active:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2

        bar_width = w / self._bars
        gap = bar_width * 0.3
        bar_w = bar_width - gap

        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QColor(Theme.ACCENT_PRIMARY))
        gradient.setColorAt(0.5, QColor(Theme.ACCENT_SECONDARY))
        gradient.setColorAt(1, QColor(Theme.ACCENT_PRIMARY))
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)

        for i in range(self._bars):
            t = i / self._bars
            angle = t * math.pi * 2 + self._phase
            breath = 0.3 + 0.7 * abs(math.sin(angle))

            raw = (math.sin(angle * 3.0) * 0.5 + 0.5) * breath
            bar_h = raw * self._amplitude * h * 0.35
            bar_h = max(bar_h, 1.0)

            x = i * bar_width + gap / 2
            y = cy - bar_h / 2

            alpha = int(80 + 175 * breath)
            bar_color = QColor(Theme.ACCENT_PRIMARY)
            bar_color.setAlpha(alpha)
            painter.setBrush(bar_color)

            radius = bar_w / 2
            painter.drawRoundedRect(int(x), int(y), int(bar_w), int(bar_h), radius, radius)

        painter.end()

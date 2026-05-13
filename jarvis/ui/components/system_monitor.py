import subprocess
from typing import Any

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar
from PyQt6.QtCore import Qt, QTimer

from jarvis.ui.theme import Theme
from jarvis.automation.linux import run_cmd


def _get_gpu_stats() -> dict:
    stats = {"available": False, "gpu": 0, "memory": 0, "name": ""}
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,name",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(",")
            stats["available"] = True
            stats["gpu"] = int(parts[0].strip())
            stats["memory_used"] = int(parts[1].strip())
            stats["memory_total"] = int(parts[2].strip())
            stats["memory_pct"] = int((stats["memory_used"] / max(stats["memory_total"], 1)) * 100)
            stats["name"] = parts[3].strip() if len(parts) > 3 else "NVIDIA GPU"
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["rocm-smi", "--showuse", "--json"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            stats["available"] = True
            stats["name"] = "AMD GPU"
    except Exception:
        pass
    return stats


def _get_cpu_percent() -> int:
    code, out, _ = run_cmd(["bash", "-c", "top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}' | cut -d. -f1"])
    if code == 0 and out:
        try:
            return int(out.strip())
        except ValueError:
            pass
    return 0


def _get_memory_percent() -> int:
    code, out, _ = run_cmd(["bash", "-c", "free | grep Mem | awk '{print int($3/$2 * 100)}'"])
    if code == 0 and out:
        try:
            return int(out.strip())
        except ValueError:
            pass
    return 0


def _get_disk_percent() -> int:
    code, out, _ = run_cmd(["bash", "-c", "df / | tail -1 | awk '{print int($5)}'"])
    if code == 0 and out:
        try:
            return int(out.strip().replace("%", ""))
        except ValueError:
            pass
    return 0


class StatBar(QWidget):
    def __init__(self, label: str, color: str, parent=None):
        super().__init__(parent)
        self._label = label
        self._color = color
        self._value = 0
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.name_label = QLabel(self._label)
        self.name_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: 400; background: transparent;")
        self.name_label.setFixedWidth(50)
        layout.addWidget(self.name_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {self._color};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress, 1)

        self.value_label = QLabel("0%")
        self.value_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 10px; font-weight: 500; background: transparent;")
        self.value_label.setFixedWidth(36)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.value_label)

    def set_value(self, value: int):
        self._value = min(100, max(0, value))
        self.progress.setValue(self._value)
        self.value_label.setText(f"{self._value}%")


class SystemMonitorCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(3000)

    def setup_ui(self):
        self.setStyleSheet(f"""
            SystemMonitorCard {{
                background-color: {Theme.BG_CARD_SOLID};
                border: 0.5px solid {Theme.BORDER};
                border-radius: {Theme.CARD_RADIUS};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QLabel("System Monitor")
        header.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; font-weight: 600; background: transparent;")
        layout.addWidget(header)

        self.cpu_bar = StatBar("CPU", Theme.ACCENT_PRIMARY)
        layout.addWidget(self.cpu_bar)

        self.mem_bar = StatBar("RAM", Theme.ACCENT_SECONDARY)
        layout.addWidget(self.mem_bar)

        self.disk_bar = StatBar("Disk", Theme.ACCENT_WARNING)
        layout.addWidget(self.disk_bar)

        self.gpu_bar = StatBar("GPU", Theme.ACCENT_INFO)
        self.gpu_bar.hide()
        layout.addWidget(self.gpu_bar)

        self.gpu_mem_bar = StatBar("VRAM", Theme.ACCENT_ERROR)
        self.gpu_mem_bar.hide()
        layout.addWidget(self.gpu_mem_bar)

    def _refresh(self):
        self.cpu_bar.set_value(_get_cpu_percent())
        self.mem_bar.set_value(_get_memory_percent())
        self.disk_bar.set_value(_get_disk_percent())

        gpu = _get_gpu_stats()
        if gpu.get("available"):
            self.gpu_bar.set_value(gpu.get("gpu", 0))
            self.gpu_bar.show()
            self.gpu_mem_bar.set_value(gpu.get("memory_pct", 0))
            self.gpu_mem_bar.show()
        else:
            self.gpu_bar.hide()
            self.gpu_mem_bar.hide()

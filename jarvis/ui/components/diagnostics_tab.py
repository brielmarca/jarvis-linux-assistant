from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QTextEdit, QScrollArea, QTabWidget,
)
from PyQt6.QtCore import Qt, QTimer

from jarvis.ui.theme import Theme
from jarvis.core.metrics import metrics
from jarvis.core.events import EventBus, EventType


class DiagnosticsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(3000)
        self._refresh()

    def _make_stat_block(self, label: str, value: str = "0", color: str = Theme.ACCENT_PRIMARY):
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_CARD};
            }}
        """)
        card.setMinimumSize(130, 60)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(2)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {Theme.TEXT_TERTIARY}; font-size: 9px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background: transparent;")
        layout.addWidget(lbl)
        val = QLabel(value)
        val.setObjectName("diag_value")
        val.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: 700; background: transparent;")
        layout.addWidget(val)
        return card, val

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(14)

        header = QLabel("Diagnostics")
        header.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 24px; font-weight: 700; background: transparent; letter-spacing: -0.4px;")
        layout.addWidget(header)

        desc = QLabel("Performance metrics, latency tracking, event traces, and error summaries")
        desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        layout.addWidget(desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.SEPARATOR}; border: none; max-height: 1px;")
        layout.addWidget(sep)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: transparent; }}
            QTabBar::tab {{ background: transparent; color: {Theme.TEXT_TERTIARY}; padding: 8px 20px;
            border: none; border-bottom: 2px solid transparent; font-size: 12px; font-weight: 500; }}
            QTabBar::tab:selected {{ color: {Theme.ACCENT_PRIMARY}; border-bottom: 2px solid {Theme.ACCENT_PRIMARY}; }}
            QTabBar::tab:hover {{ color: {Theme.TEXT_SECONDARY}; }}
        """)

        tabs.addTab(self._build_latency_tab(), "Latency")
        tabs.addTab(self._build_counters_tab(), "Counters")
        tabs.addTab(self._build_events_tab(), "Events")
        tabs.addTab(self._build_health_tab(), "Health")

        layout.addWidget(tabs, 1)

    def _build_latency_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setSpacing(10)

        self.latency_widgets = {}
        latencies = [
            ("cmd_latency", "Cmd Latency", "0ms", Theme.ACCENT_INFO),
            ("ai_latency", "AI Latency", "0ms", Theme.ACCENT_PRIMARY),
            ("voice_latency", "Voice Latency", "0ms", Theme.ACCENT_SECONDARY),
            ("skill_latency", "Skill Latency", "0ms", Theme.ACCENT_WARNING),
        ]
        for i, (key, label, val, color) in enumerate(latencies):
            card, vlabel = self._make_stat_block(label, val, color)
            self.latency_widgets[key] = vlabel
            grid.addWidget(card, 0, i)

        self.latency_log = QTextEdit()
        self.latency_log.setReadOnly(True)
        self.latency_log.setStyleSheet(f"""
            QTextEdit {{ background-color: {Theme.BG_CARD}; color: {Theme.TEXT_SECONDARY};
            border: 1px solid {Theme.BORDER}; border-radius: {Theme.RADIUS_SMALL}; padding: 12px;
            font-family: {Theme.FONT_MONO}; font-size: 11px; }}
        """)
        layout.addLayout(grid)
        layout.addWidget(self.latency_log, 1)
        return tab

    def _build_counters_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setSpacing(10)

        self.counter_widgets = {}
        counters = [
            ("commands_total", "Commands", "0", Theme.ACCENT_PRIMARY),
            ("ai_requests", "AI Requests", "0", Theme.ACCENT_INFO),
            ("skills_called", "Skills Called", "0", Theme.ACCENT_SECONDARY),
            ("errors", "Errors", "0", Theme.ACCENT_ERROR),
        ]
        for i, (key, label, val, color) in enumerate(counters):
            card, vlabel = self._make_stat_block(label, val, color)
            self.counter_widgets[key] = vlabel
            grid.addWidget(card, 0, i)

        self.counter_log = QTextEdit()
        self.counter_log.setReadOnly(True)
        self.counter_log.setStyleSheet(f"""
            QTextEdit {{ background-color: {Theme.BG_CARD}; color: {Theme.TEXT_SECONDARY};
            border: 1px solid {Theme.BORDER}; border-radius: {Theme.RADIUS_SMALL}; padding: 12px;
            font-family: {Theme.FONT_MONO}; font-size: 11px; }}
        """)
        layout.addLayout(grid)
        layout.addWidget(self.counter_log, 1)
        return tab

    def _build_events_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)

        self.events_log = QTextEdit()
        self.events_log.setReadOnly(True)
        self.events_log.setStyleSheet(f"""
            QTextEdit {{ background-color: {Theme.BG_CARD}; color: {Theme.TEXT_SECONDARY};
            border: 1px solid {Theme.BORDER}; border-radius: {Theme.RADIUS_SMALL}; padding: 12px;
            font-family: {Theme.FONT_MONO}; font-size: 11px; }}
        """)
        layout.addWidget(self.events_log)
        return tab

    def _build_health_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setSpacing(10)

        self.health_widgets = {}
        checks = [
            ("ollama", "Ollama", "⋯", Theme.ACCENT_WARNING),
            ("voice", "Voice Engine", "⋯", Theme.ACCENT_WARNING),
            ("vad", "VAD", "⋯", Theme.ACCENT_WARNING),
            ("tts", "TTS", "⋯", Theme.ACCENT_WARNING),
            ("memory", "Memory", "⋯", Theme.ACCENT_WARNING),
            ("semantic", "Semantic", "⋯", Theme.ACCENT_WARNING),
            ("desktop", "Desktop State", "⋯", Theme.ACCENT_WARNING),
            ("workflows", "Workflows", "⋯", Theme.ACCENT_WARNING),
        ]
        for i, (key, label, val, color) in enumerate(checks):
            card, vlabel = self._make_stat_block(label, val, color)
            self.health_widgets[key] = vlabel
            grid.addWidget(card, i // 4, i % 4)

        layout.addLayout(grid)

        btn_row = QHBoxLayout()
        check_btn = QPushButton("Run Health Check")
        check_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(124,106,255,0.1); border: 1px solid {Theme.ACCENT_PRIMARY}44;
            border-radius: {Theme.RADIUS_SMALL}; padding: 8px 24px; font-size: 12px; font-weight: 500; color: {Theme.ACCENT_PRIMARY}; }}
            QPushButton:hover {{ background-color: rgba(124,106,255,0.2); }}
        """)
        check_btn.clicked.connect(self._run_health_check)
        btn_row.addWidget(check_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.health_log = QTextEdit()
        self.health_log.setReadOnly(True)
        self.health_log.setStyleSheet(f"""
            QTextEdit {{ background-color: {Theme.BG_CARD}; color: {Theme.TEXT_SECONDARY};
            border: 1px solid {Theme.BORDER}; border-radius: {Theme.RADIUS_SMALL}; padding: 12px;
            font-family: {Theme.FONT_MONO}; font-size: 11px; }}
        """)
        layout.addWidget(self.health_log, 1)
        return tab

    def _refresh(self):
        try:
            data = metrics.snapshot() if hasattr(metrics, 'snapshot') else {}
        except Exception:
            data = {}

        latencies = data.get('latencies', {}) if isinstance(data, dict) else {}
        counters = data.get('counters', {}) if isinstance(data, dict) else {}

        for key, widget in self.latency_widgets.items():
            val = latencies.get(key, 0)
            if isinstance(val, (int, float)):
                widget.setText(f"{val*1000:.0f}ms" if val < 1 else f"{val:.1f}s")
            else:
                widget.setText(str(val))

        for key, widget in self.counter_widgets.items():
            val = counters.get(key, 0)
            widget.setText(str(val))

        events_text = []
        try:
            from jarvis.core.events import events as ev
            if hasattr(ev, '_history'):
                for e in ev._history[-50:]:
                    events_text.append(f"[{e.get('time','')}] {e.get('type','')}: {e.get('data',{})}")
        except Exception:
            pass
        if events_text:
            self.events_log.setPlainText("\n".join(events_text))

        latency_text = []
        for k, v in (latencies.items() if isinstance(latencies, dict) else []):
            if isinstance(v, (int, float)):
                latency_text.append(f"{k}: {v*1000:.0f}ms")
            else:
                latency_text.append(f"{k}: {v}")
        self.latency_log.setPlainText("\n".join(latency_text) if latency_text else "No latency data recorded yet.")

        counter_text = []
        for k, v in (counters.items() if isinstance(counters, dict) else []):
            counter_text.append(f"{k}: {v}")
        self.counter_log.setPlainText("\n".join(counter_text) if counter_text else "No counter data recorded yet.")

    def _run_health_check(self):
        self.health_log.setPlainText("Running health check...\n")
        checks = {}

        try:
            from jarvis.core.semantic_memory import semantic_memory
            stats = semantic_memory.get_stats()
            checks["semantic"] = f"OK ({stats.get('total_entries', 0)} entries)"
            self.health_widgets["semantic"].setStyleSheet(f"color: {Theme.ACCENT_SUCCESS}; font-size: 20px; font-weight: 700; background: transparent;")
            self.health_widgets["semantic"].setText("✓")
        except Exception as e:
            checks["semantic"] = f"FAIL: {e}"
            self.health_widgets["semantic"].setStyleSheet(f"color: {Theme.ACCENT_ERROR}; font-size: 20px; font-weight: 700; background: transparent;")
            self.health_widgets["semantic"].setText("✕")

        try:
            from jarvis.system.desktop_state import DesktopState
            ds = DesktopState()
            _ = ds.get_state()
            checks["desktop"] = "OK"
            self.health_widgets["desktop"].setStyleSheet(f"color: {Theme.ACCENT_SUCCESS}; font-size: 20px; font-weight: 700; background: transparent;")
            self.health_widgets["desktop"].setText("✓")
        except Exception as e:
            checks["desktop"] = f"FAIL: {e}"
            self.health_widgets["desktop"].setStyleSheet(f"color: {Theme.ACCENT_ERROR}; font-size: 20px; font-weight: 700; background: transparent;")
            self.health_widgets["desktop"].setText("✕")

        try:
            from jarvis.core.memory_manager import MemoryManager
            mm = MemoryManager()
            checks["memory"] = f"OK ({len(mm.get_all_memories())} memories)"
            self.health_widgets["memory"].setStyleSheet(f"color: {Theme.ACCENT_SUCCESS}; font-size: 20px; font-weight: 700; background: transparent;")
            self.health_widgets["memory"].setText("✓")
        except Exception as e:
            checks["memory"] = f"FAIL: {e}"
            self.health_widgets["memory"].setStyleSheet(f"color: {Theme.ACCENT_ERROR}; font-size: 20px; font-weight: 700; background: transparent;")
            self.health_widgets["memory"].setText("✕")

        try:
            from jarvis.automation.workflows import WorkflowManager
            wm = WorkflowManager()
            wf_count = len(wm.list_workflows())
            checks["workflows"] = f"OK ({wf_count} workflows)"
            self.health_widgets["workflows"].setStyleSheet(f"color: {Theme.ACCENT_SUCCESS}; font-size: 20px; font-weight: 700; background: transparent;")
            self.health_widgets["workflows"].setText("✓")
        except Exception as e:
            checks["workflows"] = f"FAIL: {e}"
            self.health_widgets["workflows"].setStyleSheet(f"color: {Theme.ACCENT_ERROR}; font-size: 20px; font-weight: 700; background: transparent;")
            self.health_widgets["workflows"].setText("✕")

        import urllib.request
        import json
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                models = [m["name"] for m in data.get("models", [])]
                checks["ollama"] = f"OK ({', '.join(models[:3])})"
                self.health_widgets["ollama"].setStyleSheet(f"color: {Theme.ACCENT_SUCCESS}; font-size: 20px; font-weight: 700; background: transparent;")
                self.health_widgets["ollama"].setText("✓")
        except Exception as e:
            checks["ollama"] = f"FAIL: {e}"
            self.health_widgets["ollama"].setStyleSheet(f"color: {Theme.ACCENT_ERROR}; font-size: 20px; font-weight: 700; background: transparent;")
            self.health_widgets["ollama"].setText("✕")

        for svc in ["voice", "vad", "tts"]:
            checks[svc] = "Not checked (requires audio hardware)"
            self.health_widgets[svc].setStyleSheet(f"color: {Theme.TEXT_TERTIARY}; font-size: 20px; font-weight: 700; background: transparent;")
            self.health_widgets[svc].setText("—")

        lines = [f"[{'✓' if 'OK' in v else '✕'}] {k}: {v}" for k, v in checks.items()]
        self.health_log.setPlainText("\n".join(lines))

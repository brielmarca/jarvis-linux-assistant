from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QFrame, QCheckBox, QListWidget,
    QListWidgetItem, QSplitter, QComboBox, QGroupBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from jarvis.ui.theme import Theme
from jarvis.i18n import t
from jarvis.dev.command_sandbox import CommandSandbox
from jarvis.dev.opencode_runner import OpenCodeRunner
from jarvis.ui.components.terminal_widget import TerminalWidget


sandbox = CommandSandbox()
opencode = OpenCodeRunner()


_STYLE_ACCENT_BTN = f"""
    QPushButton {{ background-color: {Theme.ACCENT_PRIMARY}; border: none;
    border-radius: 6px; padding: 8px 20px; font-size: 12px; font-weight: 600; color: white; }}
    QPushButton:hover {{ background-color: #8a7aff; }}
    QPushButton:disabled {{ background-color: rgba(124,106,255,0.3); }}
"""

_STYLE_SECONDARY_BTN = f"""
    QPushButton {{ background-color: rgba(124,106,255,0.1); border: 1px solid {Theme.ACCENT_PRIMARY}44;
    border-radius: 6px; padding: 6px 16px; font-size: 11px; font-weight: 500; color: {Theme.ACCENT_PRIMARY}; }}
    QPushButton:hover {{ background-color: rgba(124,106,255,0.2); }}
"""

_STYLE_DANGER_BTN = f"""
    QPushButton {{ background-color: rgba(255,64,112,0.08); border: 1px solid rgba(255,64,112,0.2);
    border-radius: 6px; padding: 6px 16px; font-size: 11px; font-weight: 500; color: {Theme.ACCENT_ERROR}; }}
    QPushButton:hover {{ background-color: rgba(255,64,112,0.18); }}
"""


class DevModeTab(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main = main_window
        self._sandbox = sandbox
        self._opencode = opencode
        self._tasks: list[dict] = []
        self.setup_ui()
        self._load_dirs()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QWidget()
        header.setStyleSheet("background: transparent;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(t("dev_mode.title"))
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 22px; font-weight: 700; letter-spacing: -0.3px; background: transparent;")
        h_layout.addWidget(title)

        h_layout.addStretch()

        self.status_badge = QLabel("○ " + t("dev_mode.idle"))
        self.status_badge.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px; font-weight: 500; background: transparent; padding: 4px 10px; border: 1px solid {Theme.BORDER}; border-radius: 10px;")
        h_layout.addWidget(self.status_badge)

        layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.BORDER}; border: none; max-height: 1px;")
        layout.addWidget(sep)

        vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        vertical_splitter.setStyleSheet("QSplitter::handle { background-color: rgba(50,50,80,0.3); height: 2px; }")

        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.setStyleSheet("QSplitter::handle { background-color: rgba(50,50,80,0.3); width: 2px; }")

        top_splitter.addWidget(self._build_opencode_panel())
        top_splitter.addWidget(self._build_execution_panel())
        top_splitter.setSizes([400, 400])

        vertical_splitter.addWidget(top_splitter)
        vertical_splitter.addWidget(self._build_terminal_section())
        vertical_splitter.setSizes([300, 300])

        layout.addWidget(vertical_splitter, 1)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_ui)
        self._refresh_timer.start(2000)

    # ── OpenCode Panel ─────────────────────────────────────────────

    def _build_opencode_panel(self):
        panel = QWidget()
        panel.setStyleSheet(f"background-color: rgba(12,12,22,0.5); border: 1px solid {Theme.BORDER}; border-radius: 10px;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)

        header = QLabel(t("dev_mode.opencode_title"))
        header.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; font-weight: 700; background: transparent;")
        layout.addWidget(header)

        input_row = QHBoxLayout()
        self.oc_input = QLineEdit()
        self.oc_input.setPlaceholderText(t("dev_mode.opencode_placeholder"))
        self.oc_input.setStyleSheet(f"""
            QLineEdit {{ background-color: rgba(20,20,40,0.6); color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER}; border-radius: 6px; padding: 8px 12px; font-size: 12px; }}
            QLineEdit:focus {{ border-color: {Theme.ACCENT_PRIMARY}; }}
        """)
        input_row.addWidget(self.oc_input, 1)
        layout.addLayout(input_row)

        options_row = QHBoxLayout()
        self.dry_run_cb = QCheckBox(t("dev_mode.dry_run"))
        self.dry_run_cb.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; spacing: 4px;")
        options_row.addWidget(self.dry_run_cb)

        self.project_selector = QComboBox()
        self.project_selector.setStyleSheet(f"""
            QComboBox {{ background-color: rgba(20,20,40,0.6); color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER}; border-radius: 4px; padding: 4px 10px; font-size: 11px; min-width: 180px; }}
            QComboBox:hover {{ border-color: {Theme.ACCENT_PRIMARY}; }}
            QComboBox QAbstractItemView {{ background-color: {Theme.BG_CARD_SOLID}; color: {Theme.TEXT_PRIMARY};
            selection-background-color: {Theme.ACCENT_PRIMARY}; border: 1px solid {Theme.BORDER}; border-radius: 4px; }}
        """)
        options_row.addWidget(QLabel(t("dev_mode.project")))
        options_row.addWidget(self.project_selector, 1)
        layout.addLayout(options_row)

        btn_row = QHBoxLayout()
        run_oc_btn = QPushButton(t("dev_mode.run_task"))
        run_oc_btn.setStyleSheet(_STYLE_ACCENT_BTN)
        run_oc_btn.clicked.connect(self._run_opencode)
        btn_row.addWidget(run_oc_btn)

        cancel_oc_btn = QPushButton(t("dev_mode.cancel"))
        cancel_oc_btn.setStyleSheet(_STYLE_DANGER_BTN)
        cancel_oc_btn.clicked.connect(self._cancel_opencode)
        btn_row.addWidget(cancel_oc_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.oc_output = QTextEdit()
        self.oc_output.setReadOnly(True)
        self.oc_output.setMaximumHeight(100)
        self.oc_output.setStyleSheet(f"""
            QTextEdit {{ background-color: rgba(10,10,18,0.7); color: {Theme.TEXT_SECONDARY};
            border: 1px solid {Theme.BORDER}; border-radius: 4px; padding: 8px;
            font-family: {Theme.FONT_MONO}; font-size: 10px; }}
        """)
        layout.addWidget(self.oc_output)

        recent_label = QLabel(t("dev_mode.recent_tasks"))
        recent_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 10px; font-weight: 600; background: transparent;")
        layout.addWidget(recent_label)

        self.task_list = QListWidget()
        self.task_list.setMaximumHeight(80)
        self.task_list.setStyleSheet(f"""
            QListWidget {{ background-color: rgba(10,10,18,0.5); border: 1px solid {Theme.BORDER};
            border-radius: 4px; color: {Theme.TEXT_SECONDARY}; font-size: 10px; }}
            QListWidget::item {{ padding: 3px 6px; }}
        """)
        layout.addWidget(self.task_list)

        return panel

    # ── Execution Logs Panel ───────────────────────────────────────

    def _build_execution_panel(self):
        panel = QWidget()
        panel.setStyleSheet(f"background-color: rgba(12,12,22,0.5); border: 1px solid {Theme.BORDER}; border-radius: 10px;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        header = QLabel(t("dev_mode.execution_logs"))
        header.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; font-weight: 700; background: transparent;")
        header_row.addWidget(header)
        header_row.addStretch()

        clear_log_btn = QPushButton(t("dev_mode.clear"))
        clear_log_btn.setStyleSheet(_STYLE_DANGER_BTN)
        clear_log_btn.clicked.connect(self._clear_logs)
        header_row.addWidget(clear_log_btn)
        layout.addLayout(header_row)

        self.log_list = QListWidget()
        self.log_list.setStyleSheet(f"""
            QListWidget {{ background-color: rgba(10,10,18,0.5); border: 1px solid {Theme.BORDER};
            border-radius: 4px; color: {Theme.TEXT_SECONDARY}; font-size: 10px; }}
            QListWidget::item {{ padding: 4px 8px; border-bottom: 1px solid rgba(50,50,80,0.15); }}
        """)
        layout.addWidget(self.log_list, 1)

        quick_actions_label = QLabel(t("dev_mode.quick_actions"))
        quick_actions_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 10px; font-weight: 600; background: transparent;")
        layout.addWidget(quick_actions_label)

        qa_grid = QWidget()
        qa_grid.setStyleSheet("background: transparent;")
        qa_layout = QHBoxLayout(qa_grid)
        qa_layout.setContentsMargins(0, 0, 0, 0)
        qa_layout.setSpacing(6)

        actions = [
            ("git status", "git status"),
            ("git log", "git log --oneline -10"),
            ("pip list", "pip list 2>/dev/null | head -20"),
            ("disk usage", "df -h /"),
            ("memory", "free -h"),
        ]
        for label, cmd in actions:
            btn = QPushButton(label)
            btn.setStyleSheet(_STYLE_SECONDARY_BTN)
            btn.setFixedHeight(26)
            btn.clicked.connect(lambda checked, c=cmd: self._send_to_terminal(c))
            qa_layout.addWidget(btn)
        qa_layout.addStretch()
        layout.addWidget(qa_grid)

        return panel

    # ── Terminal Section ───────────────────────────────────────────

    def _build_terminal_section(self):
        container = QWidget()
        container.setStyleSheet(f"background-color: rgba(12,12,22,0.5); border: 1px solid {Theme.BORDER}; border-radius: 10px;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 10, 14, 10)

        header = QLabel(t("dev_mode.terminal"))
        header.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 13px; font-weight: 700; background: transparent;")
        layout.addWidget(header)

        self.terminal = TerminalWidget()
        self.terminal.command_executed.connect(self._on_terminal_command)
        self.terminal.status_changed.connect(self._on_terminal_status)
        layout.addWidget(self.terminal, 1)

        return container

    # ── Actions ────────────────────────────────────────────────────

    def _run_opencode(self):
        request = self.oc_input.text().strip()
        if not request:
            return

        project = self.project_selector.currentData() or str(Path.home() / "Documents")
        self.oc_output.setText(f"Running: {request[:80]}...")
        self.status_badge.setText("● " + t("dev_mode.running"))
        self.status_badge.setStyleSheet(f"color: {Theme.ACCENT_SUCCESS}; font-size: 11px; font-weight: 600; background: transparent; padding: 4px 10px; border: 1px solid {Theme.ACCENT_SUCCESS}44; border-radius: 10px;")

        task = self._opencode.run(request, project_path=project, dry_run=self.dry_run_cb.isChecked())
        out = task.output or task.error or "Completed"
        self.oc_output.setText(f"[{task.status}] {out[:500]}")

        self._tasks.append(task.to_dict())
        self._refresh_task_list()

        colors = {"completed": Theme.ACCENT_SUCCESS, "failed": Theme.ACCENT_ERROR, "cancelled": Theme.ACCENT_WARNING}
        color = colors.get(task.status, Theme.TEXT_MUTED)
        self.status_badge.setText(f"{'✓' if task.status == 'completed' else '✗'} {task.status.title()}")
        self.status_badge.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 600; background: transparent; padding: 4px 10px; border: 1px solid {color}44; border-radius: 10px;")

    def _cancel_opencode(self):
        if self._tasks:
            last = self._tasks[-1]
            self._opencode.cancel(last.get("task_id", ""))
            self.oc_output.setText("Cancelled")

    def _send_to_terminal(self, command: str):
        self.terminal.input_line.setText(command)
        self.terminal.execute_command(command)

    def _on_terminal_command(self, command: str, exit_code: int):
        log = self._sandbox.get_execution_log(1)
        self._refresh_log_list()

    def _on_terminal_status(self, status: str):
        icons = {"running": Theme.ACCENT_SUCCESS, "idle": Theme.TEXT_MUTED, "error": Theme.ACCENT_ERROR, "cancelled": Theme.ACCENT_WARNING}
        labels = {"running": "● " + t("dev_mode.running"), "idle": "○ " + t("dev_mode.idle"), "error": "● " + t("dev_mode.error"), "cancelled": "● " + t("dev_mode.cancelled")}
        color = icons.get(status, Theme.TEXT_MUTED)
        label = labels.get(status, status.title())
        self.status_badge.setText(label)
        self.status_badge.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 600; background: transparent; padding: 4px 10px; border: 1px solid {color}44; border-radius: 10px;")

    def _clear_logs(self):
        self._sandbox.clear_log()
        self.log_list.clear()

    def _load_dirs(self):
        dirs = self._sandbox.get_allowed_dirs()
        for d in dirs:
            self.project_selector.addItem(d, d)

    def _refresh_ui(self):
        self._refresh_log_list()
        self._refresh_task_list()

    def _refresh_log_list(self):
        log = self._sandbox.get_execution_log(20)
        self.log_list.clear()
        for entry in reversed(log):
            icon = "✓" if entry.get("success") else "✗"
            cmd = entry.get("command", "")[:60]
            item = QListWidgetItem(f"  {icon}  {cmd}")
            item.setForeground(QColor(Theme.ACCENT_SUCCESS if entry.get("success") else Theme.ACCENT_ERROR))
            self.log_list.addItem(item)

    def _refresh_task_list(self):
        self.task_list.clear()
        for task in reversed(self._tasks[-10:]):
            icon_map = {"completed": "✓", "failed": "✗", "cancelled": "⊘", "running": "●"}
            icon = icon_map.get(task.get("status", ""), "?")
            req = task.get("request", "")[:50]
            item = QListWidgetItem(f"  {icon}  {req}")
            color_map = {"completed": Theme.ACCENT_SUCCESS, "failed": Theme.ACCENT_ERROR, "cancelled": Theme.ACCENT_WARNING, "running": Theme.ACCENT_PRIMARY}
            color = color_map.get(task.get("status", ""), Theme.TEXT_MUTED)
            item.setForeground(QColor(color))
            self.task_list.addItem(item)

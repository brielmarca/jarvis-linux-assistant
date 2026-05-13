import re
import time
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QFrame, QCheckBox, QComboBox,
)
from PyQt6.QtCore import Qt, QTimer, QProcess, pyqtSignal
from PyQt6.QtGui import QColor, QTextCursor

from jarvis.ui.theme import Theme
from jarvis.dev.command_sandbox import CommandSandbox


sandbox = CommandSandbox()


def _ansi_to_html(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace(" ", "&nbsp;").replace("\n", "<br>")
    ansi_pattern = re.compile(r"\x1b\[([0-9;]*)m")
    styles = {
        "0": ("", ""),
        "1": ("font-weight: bold;", ""),
        "3": ("font-style: italic;", ""),
        "4": ("text-decoration: underline;", ""),
        "30": ("color: #2e3440;", ""),
        "31": ("color: #bf616a;", ""),
        "32": ("color: #a3be8c;", ""),
        "33": ("color: #ebcb8b;", ""),
        "34": ("color: #81a1c1;", ""),
        "35": ("color: #b48ead;", ""),
        "36": ("color: #88c0d0;", ""),
        "37": ("color: #e5e9f0;", ""),
        "90": ("color: #4c566a;", ""),
        "91": ("color: #bf616a;", ""),
        "92": ("color: #a3be8c;", ""),
        "93": ("color: #ebcb8b;", ""),
        "94": ("color: #81a1c1;", ""),
        "95": ("color: #b48ead;", ""),
        "96": ("color: #88c0d0;", ""),
        "97": ("color: #e5e9f0;", ""),
    }
    parts = []
    pos = 0
    for m in ansi_pattern.finditer(text):
        start, end = m.start(), m.end()
        if start > pos:
            parts.append(text[pos:start])
        codes = m.group(1).split(";") if m.group(1) else ["0"]
        if codes[0] == "0" or codes[0] == "":
            parts.append("</span>")
        else:
            style = ""
            for c in codes:
                if c in styles:
                    style += styles[c][0]
            if "color" in style:
                parts.append(f'<span style="{style}">')
            else:
                parts.append("</span>")
        pos = end
    if pos < len(text):
        parts.append(text[pos:])
    result = "".join(parts)
    result = result.replace("</span></span>", "</span>")
    return result


class TerminalWidget(QWidget):
    command_executed = pyqtSignal(str, int)
    status_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.started.connect(self._on_started)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_error)

        self._history: list[str] = []
        self._history_index = -1
        self._command_buffer = ""
        self._start_time = 0.0
        self._sandbox_mode = False
        self._running = False
        self._scrollback: list[str] = []
        self._max_scrollback = 10000
        self._output_buffer = ""

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header = QWidget()
        header.setStyleSheet("background: transparent;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)

        self.status_icon = QLabel("○")
        self.status_icon.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 14px; background: transparent;")
        h_layout.addWidget(self.status_icon)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px; font-weight: 500; background: transparent;")
        h_layout.addWidget(self.status_label)

        self.timer_label = QLabel("")
        self.timer_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 10px; font-family: {Theme.FONT_MONO}; background: transparent;")
        h_layout.addWidget(self.timer_label)

        h_layout.addStretch()

        self.sandbox_cb = QCheckBox("Sandbox")
        self.sandbox_cb.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; spacing: 4px;")
        self.sandbox_cb.stateChanged.connect(self._toggle_sandbox)
        h_layout.addWidget(self.sandbox_cb)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(26)
        clear_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(255,64,112,0.08); color: {Theme.ACCENT_ERROR};
            border: 1px solid rgba(255,64,112,0.2); border-radius: 4px; padding: 2px 12px; font-size: 10px; font-weight: 500; }}
            QPushButton:hover {{ background-color: rgba(255,64,112,0.18); }}
        """)
        clear_btn.clicked.connect(self.clear_output)
        h_layout.addWidget(clear_btn)

        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setFixedHeight(26)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(255,64,112,0.12); color: {Theme.ACCENT_ERROR};
            border: 1px solid rgba(255,64,112,0.3); border-radius: 4px; padding: 2px 12px; font-size: 10px; font-weight: 600; }}
            QPushButton:hover {{ background-color: rgba(255,64,112,0.25); }}
            QPushButton:disabled {{ opacity: 0.3; }}
        """)
        self.stop_btn.clicked.connect(self.stop_command)
        h_layout.addWidget(self.stop_btn)

        layout.addWidget(header)

        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(8, 8, 14, 0.85);
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 10px;
                font-family: {Theme.FONT_MONO};
                font-size: 12px;
                line-height: 1.5;
                selection-background-color: {Theme.ACCENT_PRIMARY}55;
            }}
        """)
        self.output_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self.output_area, 1)

        input_container = QWidget()
        input_container.setStyleSheet("background: transparent;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(6)

        prompt_label = QLabel("$")
        prompt_label.setStyleSheet(f"color: {Theme.ACCENT_SECONDARY}; font-size: 13px; font-weight: 600; background: transparent; font-family: {Theme.FONT_MONO};")
        prompt_label.setFixedWidth(14)
        input_layout.addWidget(prompt_label)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Enter command...")
        self.input_line.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(12, 12, 22, 0.6);
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                font-family: {Theme.FONT_MONO};
            }}
            QLineEdit:focus {{ border-color: {Theme.ACCENT_PRIMARY}; }}
        """)
        self.input_line.returnPressed.connect(self._submit_command)
        self.input_line.keyPressEvent = self._input_key_press
        input_layout.addWidget(self.input_line, 1)

        run_btn = QPushButton("Run")
        run_btn.setFixedHeight(32)
        run_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.ACCENT_PRIMARY}; border: none;
            border-radius: 6px; padding: 6px 18px; font-size: 12px; font-weight: 600; color: white; }}
            QPushButton:hover {{ background-color: #8a7aff; }}
            QPushButton:disabled {{ background-color: rgba(124,106,255,0.3); }}
        """)
        run_btn.clicked.connect(self._submit_command)
        input_layout.addWidget(run_btn)

        layout.addWidget(input_container)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_timer)
        self._timer.setInterval(100)

    def _input_key_press(self, event):
        if event.key() == Qt.Key.Key_Up:
            if self._history:
                self._history_index = (self._history_index - 1) % len(self._history)
                self.input_line.setText(self._history[self._history_index])
                return
        elif event.key() == Qt.Key.Key_Down:
            if self._history:
                self._history_index = (self._history_index + 1) % len(self._history)
                self.input_line.setText(self._history[self._history_index])
                return
        elif event.key() == Qt.Key.Key_Escape:
            self.input_line.clear()
            return
        super(QLineEdit, self.input_line).keyPressEvent(event)

    def _submit_command(self):
        cmd = self.input_line.text().strip()
        if not cmd or self._running:
            return
        self.input_line.clear()
        self.execute_command(cmd)

    def execute_command(self, command: str, cwd: str | None = None):
        if self._running:
            self._append_output("[ERROR] A command is already running\n", "error")
            return

        if self._sandbox_mode:
            result = sandbox.execute(command, cwd)
            if result.blocked:
                self._append_output(f"[BLOCKED] {result.block_reason}\n", "error")
                return
            self._append_output(f"$ {command}\n", "prompt")
            self._append_output(f"[SANDBOX MODE] Would execute: {command}\n", "info")
            return

        self._running = True
        self._start_time = time.time()
        self._command_buffer = ""
        self._output_buffer = ""

        self.status_icon.setStyleSheet(f"color: {Theme.ACCENT_SUCCESS}; font-size: 14px; background: transparent;")
        self.status_label.setText("Running")
        self.status_label.setStyleSheet(f"color: {Theme.ACCENT_SUCCESS}; font-size: 11px; font-weight: 600; background: transparent;")
        self.stop_btn.setEnabled(True)
        self.status_changed.emit("running")

        self._append_output(f"$ {command}\n", "prompt")

        if command not in self._history:
            self._history.append(command)
        self._history_index = len(self._history)

        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.start("bash", ["-c", command])

    def _on_started(self):
        self._timer.start()

    def _on_stdout(self):
        data = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self._output_buffer += data
        self._render_output(data)

    def _on_finished(self, exit_code, exit_status):
        self._timer.stop()
        self._running = False
        elapsed = time.time() - self._start_time

        self.stop_btn.setEnabled(False)

        if exit_code == 0:
            self.status_icon.setStyleSheet(f"color: {Theme.ACCENT_SUCCESS}; font-size: 14px; background: transparent;")
            self.status_label.setText(f"Done ({elapsed:.1f}s)")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_SUCCESS}; font-size: 11px; font-weight: 500; background: transparent;")
        else:
            self.status_icon.setStyleSheet(f"color: {Theme.ACCENT_ERROR}; font-size: 14px; background: transparent;")
            self.status_label.setText(f"Exit {exit_code} ({elapsed:.1f}s)")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_ERROR}; font-size: 11px; font-weight: 500; background: transparent;")

        self.command_executed.emit(self._command_buffer, exit_code)
        self.status_changed.emit("idle")

    def _on_error(self, error):
        self._timer.stop()
        self._running = False
        self.stop_btn.setEnabled(False)
        self.status_icon.setStyleSheet(f"color: {Theme.ACCENT_ERROR}; font-size: 14px; background: transparent;")
        self.status_label.setText("Error")
        self.status_label.setStyleSheet(f"color: {Theme.ACCENT_ERROR}; font-size: 11px; font-weight: 500; background: transparent;")
        self._append_output(f"[ERROR] {self._process.errorString()}\n", "error")
        self.status_changed.emit("error")

    def _render_output(self, text: str):
        html = _ansi_to_html(text)
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html)
        scrollbar = self.output_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _append_output(self, text: str, style: str = "default"):
        color_map = {
            "error": Theme.ACCENT_ERROR,
            "prompt": Theme.ACCENT_SECONDARY,
            "info": Theme.TEXT_MUTED,
            "success": Theme.ACCENT_SUCCESS,
            "default": Theme.TEXT_PRIMARY,
        }
        color = color_map.get(style, Theme.TEXT_PRIMARY)
        html = f'<span style="color: {color};">{text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;").replace("\n", "<br>")}</span>'
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html)
        scrollbar = self.output_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def stop_command(self):
        if self._running:
            self._process.kill()
            self._timer.stop()
            self._running = False
            self.stop_btn.setEnabled(False)
            self.status_icon.setStyleSheet(f"color: {Theme.ACCENT_WARNING}; font-size: 14px; background: transparent;")
            self.status_label.setText("Killed")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_WARNING}; font-size: 11px; font-weight: 500; background: transparent;")
            self._append_output("\n[KILLED]\n", "error")
            self.status_changed.emit("cancelled")

    def clear_output(self):
        self.output_area.clear()
        self._output_buffer = ""

    def _toggle_sandbox(self, state):
        self._sandbox_mode = bool(state)

    def _update_timer(self):
        elapsed = time.time() - self._start_time
        self.timer_label.setText(f"{elapsed:.1f}s")
        self.timer_label.setStyleSheet(f"color: {Theme.ACCENT_SUCCESS}; font-size: 10px; font-family: {Theme.FONT_MONO}; background: transparent;")

    def set_sandbox_mode(self, enabled: bool):
        self._sandbox_mode = enabled
        self.sandbox_cb.setChecked(enabled)

    def is_running(self) -> bool:
        return self._running

    def closeEvent(self, event):
        if self._running:
            self._process.kill()
        super().closeEvent(event)

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QTextEdit, QListWidget,
    QListWidgetItem, QSplitter, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from jarvis.ui.theme import Theme


def _hex_to_rgba(hex_color: str, alpha: float = 0.1) -> str:
    c = QColor(hex_color)
    return f"rgba({c.red()},{c.green()},{c.blue()},{alpha})"


class WorkflowCard(QWidget):
    def __init__(self, name: str, desc: str, steps: int, on_run=None, on_edit=None, on_delete=None):
        super().__init__()
        self.setStyleSheet(f"""
            WorkflowCard {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_CARD};
            }}
        """)
        self.setMinimumHeight(68)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        info = QVBoxLayout()
        info.setSpacing(2)
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: 600; background: transparent;")
        info.addWidget(name_lbl)
        desc_lbl = QLabel(desc[:80])
        desc_lbl.setStyleSheet(f"color: {Theme.TEXT_TERTIARY}; font-size: 11px; background: transparent;")
        info.addWidget(desc_lbl)
        if steps:
            step_lbl = QLabel(f"{steps} step{'s' if steps != 1 else ''}")
            step_lbl.setStyleSheet(f"color: {Theme.TEXT_TERTIARY}; font-size: 10px; background: transparent;")
            info.addWidget(step_lbl)
        layout.addLayout(info, 1)

        btns = QHBoxLayout()
        btns.setSpacing(6)
        for text, color, cb in [("▶ Run", Theme.ACCENT_SUCCESS, on_run),
                                 ("✎", Theme.ACCENT_INFO, on_edit),
                                 ("✕", Theme.ACCENT_ERROR, on_delete)]:
            if cb:
                btn = QPushButton(text)
                btn.setFixedSize(48 if len(text) == 1 else 72, 30)
                btn.setStyleSheet(f"""
                    QPushButton {{ background-color: {_hex_to_rgba(color, 0.08)};
                    border: 1px solid {color}44; border-radius: {Theme.RADIUS_SMALL}; font-size: 11px; font-weight: 500; color: {color}; }}
                    QPushButton:hover {{ background-color: {_hex_to_rgba(color, 0.18)}; }}
                """)
                btn.clicked.connect(cb)
                btns.addWidget(btn)
        layout.addLayout(btns)


class WorkflowsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = None
        self.setup_ui()
        self._refresh_list()

    def _get_manager(self):
        if self._manager is None:
            from jarvis.automation.workflows import WorkflowManager
            self._manager = WorkflowManager()
        return self._manager

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(14)

        header = QWidget()
        header.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Workflows")
        title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 24px; font-weight: 700; background: transparent; letter-spacing: -0.4px;")
        hl.addWidget(title)
        hl.addStretch()

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {Theme.ACCENT_SUCCESS}; font-size: 11px; background: transparent;")
        hl.addWidget(self.status_label)

        create_btn = QPushButton("+ New Workflow")
        create_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(124,106,255,0.1); border: 1px solid {Theme.ACCENT_PRIMARY}44;
            border-radius: {Theme.RADIUS_SMALL}; padding: 6px 18px; font-size: 12px; font-weight: 500; color: {Theme.ACCENT_PRIMARY}; }}
            QPushButton:hover {{ background-color: rgba(124,106,255,0.2); }}
        """)
        create_btn.clicked.connect(self._show_create)
        hl.addWidget(create_btn)

        layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.SEPARATOR}; border: none; max-height: 1px;")
        layout.addWidget(sep)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        left_panel.setStyleSheet("background: transparent;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        templates_btn = QPushButton("Load Templates")
        templates_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(92,224,208,0.08); border: 1px solid {Theme.ACCENT_SECONDARY}44;
            border-radius: {Theme.RADIUS_SMALL}; padding: 6px 18px; font-size: 12px; font-weight: 500; color: {Theme.ACCENT_SECONDARY}; }}
            QPushButton:hover {{ background-color: rgba(92,224,208,0.18); }}
        """)
        templates_btn.clicked.connect(self._load_templates)
        left_layout.addWidget(templates_btn)

        self.workflow_list = QListWidget()
        self.workflow_list.setStyleSheet(f"""
            QListWidget {{ background-color: {Theme.BG_CARD}; border: 1px solid {Theme.BORDER};
            border-radius: {Theme.RADIUS_SMALL}; color: {Theme.TEXT_SECONDARY}; font-size: 12px; padding: 6px; outline: none; }}
            QListWidget::item {{ padding: 8px 12px; border-radius: {Theme.RADIUS_TINY}; }}
            QListWidget::item:selected {{ background-color: {Theme.BG_SELECTED}; color: {Theme.TEXT_PRIMARY}; }}
            QListWidget::item:hover {{ background-color: {Theme.BG_HOVER}; }}
        """)
        self.workflow_list.currentRowChanged.connect(self._on_select)
        left_layout.addWidget(self.workflow_list, 1)

        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_panel.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 0, 0, 0)
        right_layout.setSpacing(8)

        self.detail_name = QLabel("Select a workflow")
        self.detail_name.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 18px; font-weight: 700; background: transparent;")
        right_layout.addWidget(self.detail_name)

        self.detail_desc = QLabel("")
        self.detail_desc.setWordWrap(True)
        self.detail_desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        right_layout.addWidget(self.detail_desc)

        self.detail_steps = QTextEdit()
        self.detail_steps.setReadOnly(True)
        self.detail_steps.setStyleSheet(f"""
            QTextEdit {{ background-color: {Theme.BG_CARD}; color: {Theme.TEXT_SECONDARY};
            border: 1px solid {Theme.BORDER}; border-radius: {Theme.RADIUS_SMALL}; padding: 12px;
            font-family: {Theme.FONT_MONO}; font-size: 11px; }}
        """)
        right_layout.addWidget(self.detail_steps, 1)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500])
        layout.addWidget(splitter, 1)

        self.create_panel = QWidget()
        self.create_panel.setStyleSheet(f"""
            background-color: {Theme.BG_CARD};
            border: 1px solid {Theme.BORDER};
            border-radius: {Theme.RADIUS_CARD};
        """)
        self.create_panel.setVisible(False)
        form = QVBoxLayout(self.create_panel)
        form.setContentsMargins(16, 12, 16, 12)
        form.setSpacing(8)
        form_title = QLabel("Create New Workflow")
        form_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: 600; background: transparent;")
        form.addWidget(form_title)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name:"))
        self.create_name = QLineEdit()
        self.create_name.setPlaceholderText("my_workflow")
        name_row.addWidget(self.create_name)
        form.addLayout(name_row)

        desc_row = QHBoxLayout()
        desc_row.addWidget(QLabel("Description:"))
        self.create_desc = QLineEdit()
        self.create_desc.setPlaceholderText("What this workflow does")
        desc_row.addWidget(self.create_desc)
        form.addLayout(desc_row)

        steps_row = QHBoxLayout()
        steps_row.addWidget(QLabel("Steps (one per line):"))
        self.create_steps = QTextEdit()
        self.create_steps.setPlaceholderText("open terminal\nrun: ls -la\nwait: 2")
        self.create_steps.setMaximumHeight(80)
        steps_row.addWidget(self.create_steps)
        form.addLayout(steps_row)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("accent")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._save_workflow)
        btn_row.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(36)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(255,64,112,0.08); border: 1px solid {Theme.ACCENT_ERROR}44;
            border-radius: {Theme.RADIUS_SMALL}; padding: 8px 24px; font-size: 12px; font-weight: 500; color: {Theme.ACCENT_ERROR}; }}
            QPushButton:hover {{ background-color: rgba(255,64,112,0.18); }}
        """)
        cancel_btn.clicked.connect(lambda: self.create_panel.setVisible(False))
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        form.addLayout(btn_row)

        layout.addWidget(self.create_panel)

    def _show_create(self):
        self.create_panel.setVisible(True)

    def _save_workflow(self):
        name = self.create_name.text().strip()
        desc = self.create_desc.text().strip()
        steps_text = self.create_steps.toPlainText().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Workflow name is required.")
            return
        steps = [s.strip() for s in steps_text.split("\n") if s.strip()]
        steps_data = []
        for s in steps:
            if s.startswith("run:") or s.startswith("command:"):
                steps_data.append({"action": "command", "params": {"command": s.split(":", 1)[1].strip()}})
            elif s.startswith("wait:"):
                steps_data.append({"action": "wait", "params": {"seconds": float(s.split(":", 1)[1].strip())}})
            elif s.startswith("open"):
                steps_data.append({"action": "open", "params": {"app": s.split("open", 1)[1].strip()}})
            else:
                steps_data.append({"action": "command", "params": {"command": s}})

        mgr = self._get_manager()
        mgr.create_workflow(name, steps_data, description=desc)
        self._refresh_list()
        self.create_panel.setVisible(False)
        self.status_label.setText(f"✓ Created '{name}'")
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))

    def _load_templates(self):
        from jarvis.automation.workflows import load_default_templates
        load_default_templates()
        self._refresh_list()
        self.status_label.setText("✓ Templates loaded")
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))

    def _refresh_list(self):
        self.workflow_list.blockSignals(True)
        self.workflow_list.clear()
        try:
            mgr = self._get_manager()
            workflows = mgr.list_workflows()
        except Exception:
            workflows = {}
        if not workflows:
            item = QListWidgetItem("No workflows yet. Create one or load templates.")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.workflow_list.addItem(item)
        else:
            for name in sorted(workflows.keys()):
                self.workflow_list.addItem(name)
        self.workflow_list.blockSignals(False)

    def _on_select(self, row):
        if row < 0:
            return
        item = self.workflow_list.item(row)
        if not item or not (item.flags() & Qt.ItemFlag.ItemIsSelectable):
            return
        name = item.text()
        try:
            mgr = self._get_manager()
            wf = mgr.get_workflow(name)
        except Exception:
            self.detail_name.setText("Error loading workflow")
            return
        if wf:
            self.detail_name.setText(wf.name)
            self.detail_desc.setText(getattr(wf, 'description', '') or '')
            steps_text = "\n".join(
                f"{i+1}. [{s.get('action','?')}] {s.get('params',{})}"
                for i, s in enumerate(getattr(wf, 'steps', []))
            )
            self.detail_steps.setText(steps_text or "No steps")

    def _run_workflow(self, name):
        try:
            from jarvis.automation.workflows import WorkflowExecutor
            mgr = self._get_manager()
            wf = mgr.get_workflow(name)
            if wf:
                executor = WorkflowExecutor(wf)
                executor.run()
                self.status_label.setText(f"▶ Running '{name}'")
                QTimer.singleShot(3000, lambda: self.status_label.setText(""))
        except Exception as e:
            self.status_label.setText(f"✕ Error: {e}")
            QTimer.singleShot(5000, lambda: self.status_label.setText(""))

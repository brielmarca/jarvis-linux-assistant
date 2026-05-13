from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QTextEdit, QListWidget,
    QListWidgetItem, QSplitter, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from jarvis.ui.theme import Theme
from jarvis.ui.i18n import t, tr


def _hex_to_rgba(hex_color: str, alpha: float = 0.1) -> str:
    c = QColor(hex_color)
    return f"rgba({c.red()},{c.green()},{c.blue()},{alpha})"


class WorkflowCard(QWidget):
    def __init__(self, name: str, desc: str, steps: int, on_run=None, on_edit=None, on_delete=None):
        super().__init__()
        self.setStyleSheet(f"""
            WorkflowCard {{
                background-color: {Theme.BG_CARD_SOLID};
                border: 0.5px solid {Theme.BORDER};
                border-radius: {Theme.CARD_RADIUS};
            }}
        """)
        self.setMinimumHeight(72)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        info = QVBoxLayout()
        info.setSpacing(2)
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 15px; font-weight: 500; background: transparent;")
        info.addWidget(name_lbl)
        desc_lbl = QLabel(desc[:80])
        desc_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px; background: transparent;")
        info.addWidget(desc_lbl)
        if steps:
            step_key = "workflows.step_count_plural" if steps != 1 else "workflows.step_count"
            step_lbl = QLabel(t(step_key, count=steps))
            step_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 10px; background: transparent;")
            info.addWidget(step_lbl)
        layout.addLayout(info, 1)

        btns = QHBoxLayout()
        btns.setSpacing(6)
        for text, color, cb in [(t("workflows.run"), Theme.ACCENT_SUCCESS, on_run),
                                 (t("workflows.edit"), Theme.ACCENT_INFO, on_edit),
                                 (t("workflows.del"), Theme.ACCENT_ERROR, on_delete)]:
            if cb:
                btn = QPushButton(text)
                btn.setFixedSize(64, 30)
                btn.setStyleSheet(f"""
                    QPushButton {{ background-color: {_hex_to_rgba(color, 0.08)};
                    border: 0.5px solid {color}44; border-radius: 14px; font-size: 11px; font-weight: 400; color: {color}; }}
                    QPushButton:hover {{ background-color: {_hex_to_rgba(color, 0.18)}; }}
                """)
                btn.clicked.connect(cb)
                btns.addWidget(btn)
        layout.addLayout(btns)


class WorkflowsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = None
        self._title = None
        self._status_label = None
        self._create_btn = None
        self._templates_btn = None
        self._detail_name = None
        self._detail_desc = None
        self.detail_steps = None
        self.create_panel = None
        self.create_name = None
        self.create_desc = None
        self.create_steps = None
        self.setup_ui()
        self._refresh_list()
        tr.languageChanged.connect(self.retranslate_ui)

    def _get_manager(self):
        if self._manager is None:
            from jarvis.automation.workflows import WorkflowManager
            self._manager = WorkflowManager()
        return self._manager

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        header = QWidget()
        header.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        self._title = QLabel(t("workflows.title"))
        self._title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 22px; font-weight: 700; background: transparent;")
        hl.addWidget(self._title)
        hl.addStretch()

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"color: {Theme.ACCENT_SUCCESS}; font-size: 11px; background: transparent;")
        hl.addWidget(self._status_label)

        self._create_btn = QPushButton(t("workflows.new"))
        self._create_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(0,122,255,0.08); border: 0.5px solid {Theme.ACCENT_PRIMARY}44;
            border-radius: 14px; padding: 6px 18px; font-size: 12px; font-weight: 400; color: {Theme.ACCENT_PRIMARY}; }}
            QPushButton:hover {{ background-color: rgba(0,122,255,0.15); }}
        """)
        self._create_btn.clicked.connect(self._show_create)
        hl.addWidget(self._create_btn)

        layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.BORDER}; border: none; max-height: 0.5px;")
        layout.addWidget(sep)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        left_panel.setStyleSheet("background: transparent;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self._templates_btn = QPushButton(t("workflows.load_templates"))
        self._templates_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(48,209,88,0.08); border: 0.5px solid {Theme.ACCENT_SECONDARY}44;
            border-radius: 14px; padding: 6px 18px; font-size: 12px; font-weight: 400; color: {Theme.ACCENT_SECONDARY}; }}
            QPushButton:hover {{ background-color: rgba(48,209,88,0.15); }}
        """)
        self._templates_btn.clicked.connect(self._load_templates)
        left_layout.addWidget(self._templates_btn)

        self.workflow_list = QListWidget()
        self.workflow_list.setStyleSheet(f"""
            QListWidget {{ background-color: rgba(28,28,30,0.5); border: 0.5px solid {Theme.BORDER};
            border-radius: 8px; color: {Theme.TEXT_SECONDARY}; font-size: 12px; padding: 6px; outline: none; }}
            QListWidget::item {{ padding: 8px 12px; border-radius: 4px; }}
            QListWidget::item:selected {{ background-color: rgba(0,122,255,0.15); color: {Theme.TEXT_PRIMARY}; }}
            QListWidget::item:hover {{ background-color: rgba(0,122,255,0.06); }}
        """)
        self.workflow_list.currentRowChanged.connect(self._on_select)
        left_layout.addWidget(self.workflow_list, 1)

        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_panel.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 0, 0, 0)
        right_layout.setSpacing(8)

        self._detail_name = QLabel(t("workflows.select_hint"))
        self._detail_name.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 18px; font-weight: 600; background: transparent;")
        right_layout.addWidget(self._detail_name)

        self._detail_desc = QLabel("")
        self._detail_desc.setWordWrap(True)
        self._detail_desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        right_layout.addWidget(self._detail_desc)

        self.detail_steps = QTextEdit()
        self.detail_steps.setReadOnly(True)
        self.detail_steps.setStyleSheet(f"""
            QTextEdit {{ background-color: rgba(28,28,30,0.5); color: {Theme.TEXT_SECONDARY};
            border: 0.5px solid {Theme.BORDER}; border-radius: 8px; padding: 12px;
            font-family: {Theme.FONT_MONO}; font-size: 11px; }}
        """)
        right_layout.addWidget(self.detail_steps, 1)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500])
        layout.addWidget(splitter, 1)

        self.create_panel = QWidget()
        self.create_panel.setStyleSheet(f"""
            background-color: {Theme.BG_CARD_SOLID};
            border: 0.5px solid {Theme.BORDER};
            border-radius: {Theme.CARD_RADIUS};
        """)
        self.create_panel.setVisible(False)
        form = QVBoxLayout(self.create_panel)
        form.setContentsMargins(16, 12, 16, 12)
        form.setSpacing(8)
        form_title = QLabel(t("workflows.create_title"))
        form_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: 500; background: transparent;")
        form.addWidget(form_title)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel(t("workflows.name")))
        self.create_name = QLineEdit()
        self.create_name.setPlaceholderText(t("workflows.name_placeholder"))
        name_row.addWidget(self.create_name)
        form.addLayout(name_row)

        desc_row = QHBoxLayout()
        desc_row.addWidget(QLabel(t("workflows.description")))
        self.create_desc = QLineEdit()
        self.create_desc.setPlaceholderText(t("workflows.desc_placeholder"))
        desc_row.addWidget(self.create_desc)
        form.addLayout(desc_row)

        steps_row = QHBoxLayout()
        steps_row.addWidget(QLabel(t("workflows.steps_label")))
        self.create_steps = QTextEdit()
        self.create_steps.setPlaceholderText(t("workflows.steps_placeholder"))
        self.create_steps.setMaximumHeight(80)
        steps_row.addWidget(self.create_steps)
        form.addLayout(steps_row)

        btn_row = QHBoxLayout()
        save_btn = QPushButton(t("workflows.save"))
        save_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.ACCENT_PRIMARY}; border: none; border-radius: 16px;
            padding: 8px 24px; font-size: 12px; font-weight: 500; color: white; }}
            QPushButton:hover {{ background-color: #0066CC; }}
        """)
        save_btn.clicked.connect(self._save_workflow)
        btn_row.addWidget(save_btn)

        cancel_btn = QPushButton(t("workflows.cancel"))
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(255,69,58,0.08); border: 0.5px solid {Theme.ACCENT_ERROR}44;
            border-radius: 16px; padding: 8px 24px; font-size: 12px; font-weight: 400; color: {Theme.ACCENT_ERROR}; }}
            QPushButton:hover {{ background-color: rgba(255,69,58,0.15); }}
        """)
        cancel_btn.clicked.connect(lambda: self.create_panel.setVisible(False))
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        form.addLayout(btn_row)

        layout.addWidget(self.create_panel)

    def retranslate_ui(self):
        self._title.setText(t("workflows.title"))
        self._create_btn.setText(t("workflows.new"))
        self._templates_btn.setText(t("workflows.load_templates"))
        self._detail_name.setText(t("workflows.select_hint"))

    def _show_create(self):
        self.create_panel.setVisible(True)

    def _save_workflow(self):
        name = self.create_name.text().strip()
        desc = self.create_desc.text().strip()
        steps_text = self.create_steps.toPlainText().strip()
        if not name:
            QMessageBox.warning(self, t("workflows.validation_title"), t("workflows.name_required"))
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
        self._status_label.setText(t("workflows.created", name=name))
        QTimer.singleShot(3000, lambda: self._status_label.setText(""))

    def _load_templates(self):
        from jarvis.automation.workflows import load_default_templates
        load_default_templates()
        self._refresh_list()
        self._status_label.setText(t("workflows.templates_loaded"))
        QTimer.singleShot(3000, lambda: self._status_label.setText(""))

    def _refresh_list(self):
        self.workflow_list.blockSignals(True)
        self.workflow_list.clear()
        try:
            mgr = self._get_manager()
            workflows = mgr.list_workflows()
        except Exception:
            workflows = {}
        if not workflows:
            item = QListWidgetItem(t("workflows.no_workflows"))
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
            self._detail_name.setText(t("workflows.error_loading"))
            return
        if wf:
            self._detail_name.setText(wf.name)
            self._detail_desc.setText(getattr(wf, 'description', '') or '')
            steps_text = "\n".join(
                f"{i+1}. [{s.get('action','?')}] {s.get('params',{})}"
                for i, s in enumerate(getattr(wf, 'steps', []))
            )
            self.detail_steps.setText(steps_text or t("workflows.no_steps"))

    def _run_workflow(self, name):
        try:
            from jarvis.automation.workflows import WorkflowExecutor
            mgr = self._get_manager()
            wf = mgr.get_workflow(name)
            if wf:
                executor = WorkflowExecutor(wf)
                executor.run()
                self._status_label.setText(t("workflows.running", name=name))
                QTimer.singleShot(3000, lambda: self._status_label.setText(""))
        except Exception as e:
            self._status_label.setText(t("workflows.error", error=e))
            QTimer.singleShot(5000, lambda: self._status_label.setText(""))

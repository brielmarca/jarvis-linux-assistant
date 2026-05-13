from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from jarvis.ui.theme import Theme
from jarvis.core.health import HealthChecker
from jarvis.core.config_validator import validate_config


STATUS_COLORS = {
    "ok": Theme.ACCENT_SUCCESS,
    "warning": Theme.ACCENT_WARNING,
    "error": Theme.ACCENT_ERROR,
}
STATUS_ICONS = {
    "ok": "✓",
    "warning": "⚠",
    "error": "✗",
}


class HealthTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QLabel("Health & Diagnostics")
        header.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 22px; font-weight: 700; background: transparent; letter-spacing: -0.3px;")
        layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.BORDER}; border: none; max-height: 1px;")
        layout.addWidget(sep)

        desc = QLabel("System health, dependency checks, configuration validation")
        desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        layout.addWidget(desc)

        self.summary_label = QLabel("Run a health check to see results")
        self.summary_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 13px; background: transparent;")
        layout.addWidget(self.summary_label)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Component", "Status", "Message"])
        self.table.setStyleSheet(f"""
            QTableWidget {{ background-color: rgba(12,12,22,0.5); border: 1px solid {Theme.BORDER};
            border-radius: 8px; color: {Theme.TEXT_SECONDARY}; font-size: 12px;
            gridline-color: rgba(50,50,80,0.2); }}
            QTableWidget::item {{ padding: 8px 12px; }}
            QHeaderView::section {{ background-color: rgba(20,20,40,0.7); color: {Theme.TEXT_PRIMARY};
            border: none; border-bottom: 1px solid {Theme.BORDER}; padding: 8px; font-weight: 600; font-size: 11px; }}
        """)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()

        health_btn = QPushButton("Run Health Check")
        health_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.ACCENT_PRIMARY}; border: none;
            border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: 600; color: white; }}
            QPushButton:hover {{ background-color: #8a7aff; }}
        """)
        health_btn.clicked.connect(self._run_health_check)
        btn_row.addWidget(health_btn)

        config_btn = QPushButton("Validate Config")
        config_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(92,224,208,0.15); border: 1px solid {Theme.ACCENT_SECONDARY}44;
            border-radius: 8px; padding: 10px 24px; font-size: 13px; font-weight: 600; color: {Theme.ACCENT_SECONDARY}; }}
            QPushButton:hover {{ background-color: rgba(92,224,208,0.25); }}
        """)
        config_btn.clicked.connect(self._validate_config)
        btn_row.addWidget(config_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _run_health_check(self):
        hc = HealthChecker()
        results = hc.check_all()

        self.table.setRowCount(len(results))
        ok_count = warn_count = err_count = 0

        for i, r in enumerate(results):
            color = STATUS_COLORS.get(r.status, Theme.TEXT_MUTED)
            icon = STATUS_ICONS.get(r.status, "?")

            comp_item = QTableWidgetItem(f"  {r.component}")
            comp_item.setForeground(QColor(Theme.TEXT_PRIMARY))
            self.table.setItem(i, 0, comp_item)

            status_item = QTableWidgetItem(f"  {icon}  {r.status.upper()}")
            status_item.setForeground(QColor(color))
            self.table.setItem(i, 1, status_item)

            msg_item = QTableWidgetItem(r.message)
            msg_item.setForeground(QColor(Theme.TEXT_SECONDARY))
            self.table.setItem(i, 2, msg_item)

            if r.status == "ok":
                ok_count += 1
            elif r.status == "warning":
                warn_count += 1
            else:
                err_count += 1

        total = len(results)
        parts = []
        parts.append(f"✓ {ok_count}/{total} passed")
        if warn_count:
            parts.append(f"⚠ {warn_count} warnings")
        if err_count:
            parts.append(f"✗ {err_count} errors")
        self.summary_label.setText(" | ".join(parts))
        self.summary_label.setStyleSheet(
            f"color: {Theme.ACCENT_ERROR if err_count else Theme.ACCENT_SUCCESS}; font-size: 13px; font-weight: 600; background: transparent;"
        )

    def _validate_config(self):
        from pathlib import Path
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "settings.yaml"
        result = validate_config(config_path)

        items = []
        if result.errors:
            for e in result.errors:
                items.append(("config", "error", e))
        if result.warnings:
            for w in result.warnings:
                items.append(("config", "warning", w))
        if result.fixed:
            for f in result.fixed:
                items.append(("config", "ok", f))
        if not items:
            items.append(("config", "ok", "Configuration is valid"))

        self.table.setRowCount(len(items))
        for i, (comp, status, msg) in enumerate(items):
            color = STATUS_COLORS.get(status, Theme.TEXT_MUTED)
            self.table.setItem(i, 0, QTableWidgetItem(f"  {comp}"))
            self.table.setItem(i, 0).setForeground(QColor(Theme.TEXT_PRIMARY))
            self.table.setItem(i, 1, QTableWidgetItem(f"  {STATUS_ICONS.get(status, '?')}  {status.upper()}"))
            self.table.setItem(i, 1).setForeground(QColor(color))
            self.table.setItem(i, 2, QTableWidgetItem(msg))
            self.table.setItem(i, 2).setForeground(QColor(Theme.TEXT_SECONDARY))

        self.summary_label.setText(result.summary()[:100])
        self.summary_label.setStyleSheet(
            f"color: {Theme.ACCENT_ERROR if result.has_errors() else Theme.ACCENT_SUCCESS}; font-size: 13px; font-weight: 600; background: transparent;"
        )

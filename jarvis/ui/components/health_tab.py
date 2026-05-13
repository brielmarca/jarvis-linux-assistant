from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from jarvis.ui.theme import Theme
from jarvis.ui.i18n import t, tr
from jarvis.core.health import HealthChecker
from jarvis.core.config_validator import validate_config


STATUS_COLORS = {
    "ok": Theme.ACCENT_SUCCESS,
    "warning": Theme.ACCENT_WARNING,
    "error": Theme.ACCENT_ERROR,
}


class HealthTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._header = None
        self._desc = None
        self._summary_label = None
        self.table = None
        self._health_btn = None
        self._config_btn = None
        self.setup_ui()
        tr.languageChanged.connect(self.retranslate_ui)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        self._header = QLabel(t("health.title"))
        self._header.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 22px; font-weight: 700; background: transparent;")
        layout.addWidget(self._header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.BORDER}; border: none; max-height: 0.5px;")
        layout.addWidget(sep)

        self._desc = QLabel(t("health.description"))
        self._desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        layout.addWidget(self._desc)

        self._summary_label = QLabel(t("health.run_hint"))
        self._summary_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 13px; background: transparent;")
        layout.addWidget(self._summary_label)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        headers = [t("health.col_component"), t("health.col_status"), t("health.col_message")]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background-color: rgba(28,28,30,0.5); border: 0.5px solid {Theme.BORDER};
            border-radius: 8px; color: {Theme.TEXT_SECONDARY}; font-size: 12px;
            gridline-color: rgba(255,255,255,0.05); }}
            QTableWidget::item {{ padding: 8px 12px; }}
            QHeaderView::section {{ background-color: rgba(44,44,46,0.7); color: {Theme.TEXT_PRIMARY};
            border: none; border-bottom: 0.5px solid {Theme.BORDER}; padding: 8px; font-weight: 500; font-size: 11px; }}
        """)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()

        self._health_btn = QPushButton(t("health.run_check"))
        self._health_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.ACCENT_PRIMARY}; border: none;
            border-radius: 18px; padding: 10px 24px; font-size: 13px; font-weight: 500; color: white; }}
            QPushButton:hover {{ background-color: #0066CC; }}
        """)
        self._health_btn.clicked.connect(self._run_health_check)
        btn_row.addWidget(self._health_btn)

        self._config_btn = QPushButton(t("health.validate_config"))
        self._config_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(48,209,88,0.08); border: 0.5px solid {Theme.ACCENT_SECONDARY}44;
            border-radius: 18px; padding: 10px 24px; font-size: 13px; font-weight: 400; color: {Theme.ACCENT_SECONDARY}; }}
            QPushButton:hover {{ background-color: rgba(48,209,88,0.15); }}
        """)
        self._config_btn.clicked.connect(self._validate_config)
        btn_row.addWidget(self._config_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def retranslate_ui(self):
        self._header.setText(t("health.title"))
        self._desc.setText(t("health.description"))
        self._summary_label.setText(t("health.run_hint"))
        self._health_btn.setText(t("health.run_check"))
        self._config_btn.setText(t("health.validate_config"))
        headers = [t("health.col_component"), t("health.col_status"), t("health.col_message")]
        self.table.setHorizontalHeaderLabels(headers)

    def _run_health_check(self):
        hc = HealthChecker()
        results = hc.check_all()

        self.table.setRowCount(len(results))
        ok_count = warn_count = err_count = 0

        for i, r in enumerate(results):
            color = STATUS_COLORS.get(r.status, Theme.TEXT_MUTED)
            comp_item = QTableWidgetItem(f"  {r.component}")
            comp_item.setForeground(QColor(Theme.TEXT_PRIMARY))
            self.table.setItem(i, 0, comp_item)

            status_key = f"health.status_{r.status}" if r.status in ("ok", "warning", "error") else r.status
            status_text = t(status_key) if r.status in ("ok", "warning", "error") else r.status.upper()
            status_item = QTableWidgetItem(f"  {status_text}  {r.status.upper()}")
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
        parts = [f"OK {ok_count}/{total}"]
        if warn_count:
            parts.append(f"WARN {warn_count}")
        if err_count:
            parts.append(f"ERR {err_count}")
        self._summary_label.setText(" | ".join(parts))
        self._summary_label.setStyleSheet(
            f"color: {Theme.ACCENT_ERROR if err_count else Theme.ACCENT_SUCCESS}; font-size: 13px; font-weight: 500; background: transparent;"
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
            items.append(("config", "ok", t("health.config_valid")))

        self.table.setRowCount(len(items))
        for i, (comp, status, msg) in enumerate(items):
            color = STATUS_COLORS.get(status, Theme.TEXT_MUTED)
            self.table.setItem(i, 0, QTableWidgetItem(f"  {comp}"))
            self.table.setItem(i, 0).setForeground(QColor(Theme.TEXT_PRIMARY))
            status_key = f"health.status_{status}" if status in ("ok", "warning", "error") else status
            status_text = t(status_key) if status in ("ok", "warning", "error") else status.upper()
            self.table.setItem(i, 1, QTableWidgetItem(f"  {status_text}  {status.upper()}"))
            self.table.setItem(i, 1).setForeground(QColor(color))
            self.table.setItem(i, 2, QTableWidgetItem(msg))
            self.table.setItem(i, 2).setForeground(QColor(Theme.TEXT_SECONDARY))

        self._summary_label.setText(result.summary()[:100])
        self._summary_label.setStyleSheet(
            f"color: {Theme.ACCENT_ERROR if result.has_errors() else Theme.ACCENT_SUCCESS}; font-size: 13px; font-weight: 500; background: transparent;"
        )

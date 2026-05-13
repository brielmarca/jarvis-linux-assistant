from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QTextEdit, QLineEdit, QMessageBox, QSplitter,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from jarvis.ui.theme import Theme
from jarvis.ui.i18n import t, tr
from jarvis.core.memory_manager import MemoryManager
from jarvis.core.semantic_memory import semantic_memory


def _hex_to_rgba(hex_color: str, alpha: float = 0.1) -> str:
    c = QColor(hex_color)
    return f"rgba({c.red()},{c.green()},{c.blue()},{alpha})"


mem = MemoryManager()


class MemoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._header = None
        self._desc = None
        self.search_input = None
        self._search_btn = None
        self._clear_search_btn = None
        self._refresh_btn = None
        self.setup_ui()
        self._refresh()
        tr.languageChanged.connect(self.retranslate_ui)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        self._header = QLabel(t("memory.title"))
        self._header.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 22px; font-weight: 700; background: transparent;")
        layout.addWidget(self._header)

        self._desc = QLabel(t("memory.description"))
        self._desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        layout.addWidget(self._desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.BORDER}; border: none; max-height: 0.5px;")
        layout.addWidget(sep)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t("memory.search_placeholder"))
        self.search_input.setStyleSheet(f"""
            QLineEdit {{ background-color: rgba(28,28,30,0.6); color: {Theme.TEXT_PRIMARY};
            border: 0.5px solid {Theme.BORDER}; border-radius: 8px; padding: 10px 14px;
            font-size: 13px; }}
            QLineEdit:focus {{ border-color: {Theme.ACCENT_PRIMARY}; }}
        """)
        self.search_input.returnPressed.connect(self._semantic_search)
        search_row.addWidget(self.search_input, 1)

        self._search_btn = QPushButton(t("memory.search"))
        self._search_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(0,122,255,0.08); border: 0.5px solid {Theme.ACCENT_PRIMARY}44;
            border-radius: 14px; padding: 6px 18px; font-size: 12px; font-weight: 400; color: {Theme.ACCENT_PRIMARY}; }}
            QPushButton:hover {{ background-color: rgba(0,122,255,0.15); }}
        """)
        self._search_btn.clicked.connect(self._semantic_search)
        search_row.addWidget(self._search_btn)

        self._clear_search_btn = QPushButton(t("memory.clear"))
        self._clear_search_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(255,69,58,0.08); border: 0.5px solid {Theme.ACCENT_ERROR}44;
            border-radius: 14px; padding: 6px 18px; font-size: 12px; font-weight: 400; color: {Theme.ACCENT_ERROR}; }}
            QPushButton:hover {{ background-color: rgba(255,69,58,0.15); }}
        """)
        self._clear_search_btn.clicked.connect(lambda: [self.search_input.clear(), self._refresh()])
        search_row.addWidget(self._clear_search_btn)
        layout.addLayout(search_row)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: transparent; }}
            QTabBar::tab {{ background: transparent; color: {Theme.TEXT_MUTED}; padding: 8px 20px;
            border: none; border-bottom: 2px solid transparent; font-size: 12px; font-weight: 400; }}
            QTabBar::tab:selected {{ color: {Theme.ACCENT_PRIMARY}; border-bottom: 2px solid {Theme.ACCENT_PRIMARY}; }}
            QTabBar::tab:hover {{ color: {Theme.TEXT_SECONDARY}; }}
        """)

        tabs.addTab(self._build_memories_tab(), t("memory.tab_long_term"))
        tabs.addTab(self._build_short_term_tab(), t("memory.tab_short_term"))
        tabs.addTab(self._build_pinned_tab(), t("memory.tab_pinned"))
        tabs.addTab(self._build_preferences_tab(), t("memory.tab_preferences"))
        tabs.addTab(self._build_projects_tab(), t("memory.tab_projects"))
        tabs.addTab(self._build_semantic_tab(), t("memory.tab_semantic"))
        tabs.addTab(self._build_stats_tab(), t("memory.tab_stats"))

        layout.addWidget(tabs, 1)

        btn_row = QHBoxLayout()
        self._refresh_btn = QPushButton(t("memory.refresh"))
        self._refresh_btn.clicked.connect(self._refresh)
        btn_row.addWidget(self._refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def retranslate_ui(self):
        self._header.setText(t("memory.title"))
        self._desc.setText(t("memory.description"))
        self.search_input.setPlaceholderText(t("memory.search_placeholder"))
        self._search_btn.setText(t("memory.search"))
        self._clear_search_btn.setText(t("memory.clear"))
        self._refresh_btn.setText(t("memory.refresh"))

        tabs = self.findChild(QTabWidget)
        if tabs:
            tab_keys = ["memory.tab_long_term", "memory.tab_short_term", "memory.tab_pinned",
                        "memory.tab_preferences", "memory.tab_projects", "memory.tab_semantic", "memory.tab_stats"]
            for i, key in enumerate(tab_keys):
                if i < tabs.count():
                    tabs.setTabText(i, t(key))

    def _make_table(self, cols: int, headers: list[str], col_stretch: int = 0):
        table = QTableWidget()
        table.setColumnCount(cols)
        table.setHorizontalHeaderLabels(headers)
        table.setStyleSheet(f"""
            QTableWidget {{ background-color: rgba(28,28,30,0.5); border: 0.5px solid {Theme.BORDER};
            border-radius: 8px; color: {Theme.TEXT_SECONDARY}; font-size: 11px;
            gridline-color: rgba(255,255,255,0.05); }}
            QTableWidget::item {{ padding: 6px 10px; }}
            QHeaderView::section {{ background-color: rgba(44,44,46,0.7); color: {Theme.TEXT_PRIMARY};
            border: none; border-bottom: 0.5px solid {Theme.BORDER}; padding: 8px; font-weight: 500; font-size: 11px; }}
        """)
        table.horizontalHeader().setStretchLastSection(True)
        if col_stretch >= 0:
            table.horizontalHeader().setSectionResizeMode(col_stretch, QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        return table

    def _build_memories_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        headers = [t("memory.col_text"), t("memory.col_tags"), t("memory.col_importance"), t("memory.col_created"), ""]
        self.mem_table = self._make_table(5, headers, 0)
        self.mem_table.setColumnWidth(4, 60)
        layout.addWidget(self.mem_table)
        return tab

    def _build_short_term_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        headers = [t("memory.col_text"), t("memory.col_context"), t("memory.col_timestamp")]
        self.short_table = self._make_table(3, headers, 0)
        layout.addWidget(self.short_table)
        return tab

    def _build_pinned_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        headers = [t("memory.col_text"), t("memory.col_tags"), t("memory.col_importance"), ""]
        self.pinned_table = self._make_table(4, headers, 0)
        self.pinned_table.setColumnWidth(3, 60)
        layout.addWidget(self.pinned_table)
        return tab

    def _build_preferences_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        headers = [t("memory.col_key"), t("memory.col_value")]
        self.pref_table = self._make_table(2, headers, 1)
        layout.addWidget(self.pref_table)
        return tab

    def _build_projects_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        headers = [t("memory.col_name"), t("memory.col_path"), t("memory.col_last_opened")]
        self.proj_table = self._make_table(3, headers, 0)
        layout.addWidget(self.proj_table)
        return tab

    def _build_semantic_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)

        row = QHBoxLayout()
        add_input = QLineEdit()
        add_input.setPlaceholderText(t("memory.add_placeholder"))
        add_input.setStyleSheet(f"""
            QLineEdit {{ background-color: rgba(28,28,30,0.6); color: {Theme.TEXT_PRIMARY};
            border: 0.5px solid {Theme.BORDER}; border-radius: 6px; padding: 8px 12px; font-size: 12px; }}
        """)
        row.addWidget(add_input, 1)
        add_btn = QPushButton(t("memory.add"))
        add_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(0,122,255,0.08); border: 0.5px solid {Theme.ACCENT_PRIMARY}44;
            border-radius: 14px; padding: 6px 18px; font-size: 12px; font-weight: 400; color: {Theme.ACCENT_PRIMARY}; }}
            QPushButton:hover {{ background-color: rgba(0,122,255,0.15); }}
        """)
        add_btn.clicked.connect(lambda: self._add_semantic(add_input))
        row.addWidget(add_btn)
        layout.addLayout(row)

        headers = [t("memory.col_text"), t("memory.col_tags"), t("memory.col_score"), t("memory.col_pinned"), ""]
        self.semantic_table = self._make_table(5, headers, 0)
        self.semantic_table.setColumnWidth(3, 60)
        self.semantic_table.setColumnWidth(4, 60)
        layout.addWidget(self.semantic_table, 1)
        return tab

    def _build_stats_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet(f"""
            QTextEdit {{ background-color: rgba(28,28,30,0.5); color: {Theme.TEXT_SECONDARY};
            border: 0.5px solid {Theme.BORDER}; border-radius: 8px; padding: 14px;
            font-family: {Theme.FONT_MONO}; font-size: 12px; }}
        """)
        layout.addWidget(self.stats_text)
        return tab

    def _add_semantic(self, input_field):
        text = input_field.text().strip()
        if text:
            semantic_memory.store(text, source="user", tags=["manual"])
            input_field.clear()
            self._refresh()

    def _semantic_search(self):
        query = self.search_input.text().strip()
        if not query:
            self._refresh()
            return
        results = semantic_memory.search(query, top_k=20)
        self.semantic_table.setRowCount(len(results))
        for i, r in enumerate(results):
            self.semantic_table.setItem(i, 0, QTableWidgetItem(r.get("text", "")[:100]))
            tags = ", ".join(r.get("tags", []))
            self.semantic_table.setItem(i, 1, QTableWidgetItem(tags[:50]))
            score = f"{r.get('score', 0):.3f}"
            score_item = QTableWidgetItem(score)
            score_item.setForeground(QColor(Theme.ACCENT_PRIMARY if r.get('score', 0) > 0.5 else Theme.TEXT_MUTED))
            self.semantic_table.setItem(i, 2, score_item)
            self.semantic_table.setItem(i, 3, QTableWidgetItem(""))
            self._add_pin_btn(self.semantic_table, i, r.get("id", ""))
        self.mem_table.setRowCount(len(results))
        for i, r in enumerate(results):
            self.mem_table.setItem(i, 0, QTableWidgetItem(r.get("text", "")[:100]))
            tags = ", ".join(r.get("tags", []))
            self.mem_table.setItem(i, 1, QTableWidgetItem(tags[:50]))
            imp = str(r.get("score", 0))
            imp_item = QTableWidgetItem(imp)
            imp_item.setForeground(QColor(Theme.ACCENT_PRIMARY if r.get('score', 0) > 0.3 else Theme.TEXT_MUTED))
            self.mem_table.setItem(i, 2, imp_item)
            self.mem_table.setItem(i, 3, QTableWidgetItem(""))

    def _add_pin_btn(self, table, row, entry_id):
        if not entry_id:
            return
        btn = QPushButton(t("memory.pin") if not semantic_memory.is_pinned(entry_id) else t("memory.unpin"))
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {_hex_to_rgba(Theme.ACCENT_PRIMARY, 0.08)};
            border: 0.5px solid {Theme.ACCENT_PRIMARY}44; border-radius: 4px; padding: 2px 8px;
            font-size: 10px; font-weight: 400; color: {Theme.ACCENT_PRIMARY}; }}
            QPushButton:hover {{ background-color: {_hex_to_rgba(Theme.ACCENT_PRIMARY, 0.18)}; }}
        """)
        def toggle_pin(eid=entry_id, b=btn):
            try:
                if semantic_memory.is_pinned(eid):
                    semantic_memory.unpin(eid)
                    b.setText(t("memory.pin"))
                else:
                    semantic_memory.pin(eid)
                    b.setText(t("memory.unpin"))
                self._refresh()
            except Exception:
                pass
        btn.clicked.connect(toggle_pin)
        table.setCellWidget(row, 4, btn)

    def _refresh(self):
        memories = mem.get_all_memories()
        self.mem_table.setRowCount(len(memories))
        for i, m in enumerate(memories):
            self.mem_table.setItem(i, 0, QTableWidgetItem(m.get("text", "")[:100]))
            tags = ", ".join(m.get("tags", []))
            self.mem_table.setItem(i, 1, QTableWidgetItem(tags[:50]))
            imp = str(m.get("importance", 0))
            imp_item = QTableWidgetItem(imp)
            imp_item.setForeground(QColor(Theme.ACCENT_PRIMARY if float(imp) > 0.5 else Theme.TEXT_MUTED))
            self.mem_table.setItem(i, 2, imp_item)
            created = m.get("created", "")[:19] if m.get("created") else ""
            self.mem_table.setItem(i, 3, QTableWidgetItem(created))
            del_btn = QPushButton(t("memory.delete"))
            del_btn.setStyleSheet(f"""
                QPushButton {{ background-color: rgba(255,69,58,0.08); border: 0.5px solid {Theme.ACCENT_ERROR}44;
                border-radius: 4px; padding: 2px 8px; font-size: 10px; color: {Theme.ACCENT_ERROR}; }}
                QPushButton:hover {{ background-color: rgba(255,69,58,0.15); }}
            """)
            cmd_text = m.get("text", "")
            del_btn.clicked.connect(lambda checked, t=cmd_text: self._forget_memory(t))
            self.mem_table.setCellWidget(i, 4, del_btn)

        prefs = mem.get_all_preferences()
        self.pref_table.setRowCount(len(prefs))
        for i, (k, v) in enumerate(sorted(prefs.items())):
            self.pref_table.setItem(i, 0, QTableWidgetItem(k))
            self.pref_table.setItem(i, 1, QTableWidgetItem(str(v)[:80]))

        projects = mem.get_all_projects()
        self.proj_table.setRowCount(len(projects))
        for i, (name, proj) in enumerate(sorted(projects.items())):
            self.proj_table.setItem(i, 0, QTableWidgetItem(proj.get("name", name)))
            self.proj_table.setItem(i, 1, QTableWidgetItem(proj.get("path", "")))
            self.proj_table.setItem(i, 2, QTableWidgetItem(proj.get("last_opened", "")[:19] or ""))

        try:
            sem_all = semantic_memory.search("", top_k=200)
        except Exception:
            sem_all = []
        try:
            pinned_list = [m for m in sem_all if m.get("pinned")]
        except Exception:
            pinned_list = []

        self.semantic_table.setRowCount(len(sem_all))
        for i, r in enumerate(sem_all):
            self.semantic_table.setItem(i, 0, QTableWidgetItem(r.get("text", "")[:100]))
            tags = ", ".join(r.get("tags", []))
            self.semantic_table.setItem(i, 1, QTableWidgetItem(tags[:50]))
            score = f"{r.get('score', 0):.3f}"
            score_item = QTableWidgetItem(score)
            score_item.setForeground(QColor(Theme.ACCENT_PRIMARY if r.get('score', 0) > 0.3 else Theme.TEXT_MUTED))
            self.semantic_table.setItem(i, 2, score_item)
            self.semantic_table.setItem(i, 3, QTableWidgetItem(""))
            self._add_pin_btn(self.semantic_table, i, r.get("id", ""))

        self.pinned_table.setRowCount(len(pinned_list))
        for i, r in enumerate(pinned_list):
            self.pinned_table.setItem(i, 0, QTableWidgetItem(r.get("text", "")[:100]))
            tags = ", ".join(r.get("tags", []))
            self.pinned_table.setItem(i, 1, QTableWidgetItem(tags[:50]))
            imp = str(r.get("score", 0))
            self.pinned_table.setItem(i, 2, QTableWidgetItem(imp))
            unpin_btn = QPushButton(t("memory.unpin"))
            unpin_btn.setStyleSheet(f"""
                QPushButton {{ background-color: rgba(0,122,255,0.08); border: 0.5px solid {Theme.ACCENT_PRIMARY}44;
                border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: 400; color: {Theme.ACCENT_PRIMARY}; }}
                QPushButton:hover {{ background-color: rgba(0,122,255,0.15); }}
            """)
            eid = r.get("id", "")
            unpin_btn.clicked.connect(lambda checked, eid=eid: [semantic_memory.unpin(eid), self._refresh()])
            self.pinned_table.setCellWidget(i, 3, unpin_btn)

        try:
            short = mem.get_short_term_memories() if hasattr(mem, 'get_short_term_memories') else []
        except Exception:
            short = []
        self.short_table.setRowCount(len(short))
        for i, s in enumerate(short):
            text = s.get("text", s.get("command", ""))[:100]
            self.short_table.setItem(i, 0, QTableWidgetItem(text))
            ctx = s.get("context", "")[:50]
            self.short_table.setItem(i, 1, QTableWidgetItem(ctx))
            ts = s.get("timestamp", s.get("created", ""))[:19] if s.get("timestamp") or s.get("created") else ""
            self.short_table.setItem(i, 2, QTableWidgetItem(ts))

        stats = mem.get_stats()
        sem_stats = semantic_memory.get_stats() if hasattr(semantic_memory, 'get_stats') else {}
        lines = [f"{k}: {v}" for k, v in stats.items()]
        lines.append("")
        lines.append(t("memory.semantic_header"))
        for k, v in sem_stats.items():
            lines.append(f"{k}: {v}")
        self.stats_text.setText("\n".join(lines))

    def _forget_memory(self, text):
        reply = QMessageBox.question(self, t("memory.forget_title"),
            f"{t('memory.forget_confirm')}\n\n{text[:100]}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            mem.forget(text)
            self._refresh()

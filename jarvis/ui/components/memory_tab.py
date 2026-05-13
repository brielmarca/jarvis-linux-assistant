from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QTextEdit, QLineEdit, QMessageBox, QSplitter,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from jarvis.ui.theme import Theme
from jarvis.core.memory_manager import MemoryManager
from jarvis.core.semantic_memory import semantic_memory


def _hex_to_rgba(hex_color: str, alpha: float = 0.1) -> str:
    c = QColor(hex_color)
    return f"rgba({c.red()},{c.green()},{c.blue()},{alpha})"


mem = MemoryManager()


class MemoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self._refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QLabel("Memory")
        header.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 22px; font-weight: 700; background: transparent; letter-spacing: -0.3px;")
        layout.addWidget(header)

        desc = QLabel("Short-term context, long-term memories, semantic search, preferences, and project data")
        desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        layout.addWidget(desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {Theme.BORDER}; border: none; max-height: 1px;")
        layout.addWidget(sep)

        # Semantic search bar
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search memories semantically...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{ background-color: rgba(12,12,22,0.6); color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER}; border-radius: 8px; padding: 10px 14px;
            font-size: 13px; }}
            QLineEdit:focus {{ border-color: {Theme.ACCENT_PRIMARY}; }}
        """)
        self.search_input.returnPressed.connect(self._semantic_search)
        search_row.addWidget(self.search_input, 1)

        search_btn = QPushButton("Search")
        search_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(124,106,255,0.1); border: 1px solid {Theme.ACCENT_PRIMARY}44;
            border-radius: 6px; padding: 6px 18px; font-size: 12px; font-weight: 500; color: {Theme.ACCENT_PRIMARY}; }}
            QPushButton:hover {{ background-color: rgba(124,106,255,0.2); }}
        """)
        search_btn.clicked.connect(self._semantic_search)
        search_row.addWidget(search_btn)

        clear_search_btn = QPushButton("Clear")
        clear_search_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(255,64,112,0.08); border: 1px solid {Theme.ACCENT_ERROR}44;
            border-radius: 6px; padding: 6px 18px; font-size: 12px; font-weight: 500; color: {Theme.ACCENT_ERROR}; }}
            QPushButton:hover {{ background-color: rgba(255,64,112,0.18); }}
        """)
        clear_search_btn.clicked.connect(lambda: [self.search_input.clear(), self._refresh()])
        search_row.addWidget(clear_search_btn)
        layout.addLayout(search_row)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: transparent; }}
            QTabBar::tab {{ background: transparent; color: {Theme.TEXT_MUTED}; padding: 8px 20px;
            border: none; border-bottom: 2px solid transparent; font-size: 12px; font-weight: 500; }}
            QTabBar::tab:selected {{ color: {Theme.ACCENT_PRIMARY}; border-bottom: 2px solid {Theme.ACCENT_PRIMARY}; }}
            QTabBar::tab:hover {{ color: {Theme.TEXT_SECONDARY}; }}
        """)

        tabs.addTab(self._build_memories_tab(), "Long-term")
        tabs.addTab(self._build_short_term_tab(), "Short-term")
        tabs.addTab(self._build_pinned_tab(), "Pinned")
        tabs.addTab(self._build_preferences_tab(), "Preferences")
        tabs.addTab(self._build_projects_tab(), "Projects")
        tabs.addTab(self._build_semantic_tab(), "Semantic")
        tabs.addTab(self._build_stats_tab(), "Stats")

        layout.addWidget(tabs, 1)

        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh)
        btn_row.addWidget(refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _make_table(self, cols: int, headers: list[str], col_stretch: int = 0):
        table = QTableWidget()
        table.setColumnCount(cols)
        table.setHorizontalHeaderLabels(headers)
        table.setStyleSheet(f"""
            QTableWidget {{ background-color: rgba(12,12,22,0.5); border: 1px solid {Theme.BORDER};
            border-radius: 8px; color: {Theme.TEXT_SECONDARY}; font-size: 11px;
            gridline-color: rgba(50,50,80,0.2); }}
            QTableWidget::item {{ padding: 6px 10px; }}
            QHeaderView::section {{ background-color: rgba(20,20,40,0.7); color: {Theme.TEXT_PRIMARY};
            border: none; border-bottom: 1px solid {Theme.BORDER}; padding: 8px; font-weight: 600; font-size: 11px; }}
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
        self.mem_table = self._make_table(5, ["Text", "Tags", "Importance", "Created", ""], 0)
        self.mem_table.setColumnWidth(4, 80)
        layout.addWidget(self.mem_table)
        return tab

    def _build_short_term_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        self.short_table = self._make_table(3, ["Text", "Context", "Timestamp"], 0)
        layout.addWidget(self.short_table)
        return tab

    def _build_pinned_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        self.pinned_table = self._make_table(4, ["Text", "Tags", "Importance", ""], 0)
        self.pinned_table.setColumnWidth(3, 80)
        layout.addWidget(self.pinned_table)
        return tab

    def _build_preferences_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        self.pref_table = self._make_table(2, ["Key", "Value"], 1)
        layout.addWidget(self.pref_table)
        return tab

    def _build_projects_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        self.proj_table = self._make_table(3, ["Name", "Path", "Last Opened"], 0)
        layout.addWidget(self.proj_table)
        return tab

    def _build_semantic_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)

        row = QHBoxLayout()
        add_input = QLineEdit()
        add_input.setPlaceholderText("Add semantic memory entry...")
        add_input.setStyleSheet(f"""
            QLineEdit {{ background-color: rgba(12,12,22,0.6); color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER}; border-radius: 6px; padding: 8px 12px; font-size: 12px; }}
        """)
        row.addWidget(add_input, 1)
        add_btn = QPushButton("Add")
        add_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(124,106,255,0.1); border: 1px solid {Theme.ACCENT_PRIMARY}44;
            border-radius: 6px; padding: 6px 18px; font-size: 12px; font-weight: 500; color: {Theme.ACCENT_PRIMARY}; }}
            QPushButton:hover {{ background-color: rgba(124,106,255,0.2); }}
        """)
        add_btn.clicked.connect(lambda: self._add_semantic(add_input))
        row.addWidget(add_btn)
        layout.addLayout(row)

        self.semantic_table = self._make_table(5, ["Text", "Tags", "Score", "Pinned", ""], 0)
        self.semantic_table.setColumnWidth(3, 60)
        self.semantic_table.setColumnWidth(4, 80)
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
            QTextEdit {{ background-color: rgba(12,12,22,0.5); color: {Theme.TEXT_SECONDARY};
            border: 1px solid {Theme.BORDER}; border-radius: 8px; padding: 14px;
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
            pinned = "✓" if r.get("pinned") else ""
            self.semantic_table.setItem(i, 3, QTableWidgetItem(pinned))
            self._add_pin_btn(self.semantic_table, i, r.get("id", ""))
        # Also show semantic results in the main memory table view
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
        btn = QPushButton("Pin" if not semantic_memory.is_pinned(entry_id) else "Unpin")
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {_hex_to_rgba(Theme.ACCENT_PRIMARY, 0.08)};
            border: 1px solid {Theme.ACCENT_PRIMARY}44; border-radius: 4px; padding: 2px 8px;
            font-size: 10px; font-weight: 500; color: {Theme.ACCENT_PRIMARY}; }}
            QPushButton:hover {{ background-color: {_hex_to_rgba(Theme.ACCENT_PRIMARY, 0.18)}; }}
        """)
        def toggle_pin(eid=entry_id, b=btn):
            try:
                if semantic_memory.is_pinned(eid):
                    semantic_memory.unpin(eid)
                    b.setText("Pin")
                else:
                    semantic_memory.pin(eid)
                    b.setText("Unpin")
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
            del_btn = QPushButton("✕")
            del_btn.setStyleSheet(f"""
                QPushButton {{ background-color: rgba(255,64,112,0.08); border: 1px solid {Theme.ACCENT_ERROR}44;
                border-radius: 4px; padding: 2px 8px; font-size: 10px; color: {Theme.ACCENT_ERROR}; }}
                QPushButton:hover {{ background-color: rgba(255,64,112,0.18); }}
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

        # Semantic memories
        try:
            sem_all = semantic_memory.search("", top_k=200)
        except Exception:
            sem_all = []
        # Also get pinned
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
            pinned = "✓" if r.get("pinned") else ""
            self.semantic_table.setItem(i, 3, QTableWidgetItem(pinned))
            self._add_pin_btn(self.semantic_table, i, r.get("id", ""))

        self.pinned_table.setRowCount(len(pinned_list))
        for i, r in enumerate(pinned_list):
            self.pinned_table.setItem(i, 0, QTableWidgetItem(r.get("text", "")[:100]))
            tags = ", ".join(r.get("tags", []))
            self.pinned_table.setItem(i, 1, QTableWidgetItem(tags[:50]))
            imp = str(r.get("score", 0))
            self.pinned_table.setItem(i, 2, QTableWidgetItem(imp))
            unpin_btn = QPushButton("Unpin")
            unpin_btn.setStyleSheet(f"""
                QPushButton {{ background-color: rgba(124,106,255,0.08); border: 1px solid {Theme.ACCENT_PRIMARY}44;
                border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: 500; color: {Theme.ACCENT_PRIMARY}; }}
                QPushButton:hover {{ background-color: rgba(124,106,255,0.18); }}
            """)
            eid = r.get("id", "")
            unpin_btn.clicked.connect(lambda checked, eid=eid: [semantic_memory.unpin(eid), self._refresh()])
            self.pinned_table.setCellWidget(i, 3, unpin_btn)

        # Short-term memories from MemoryManager
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
        lines.append("--- Semantic Memory ---")
        for k, v in sem_stats.items():
            lines.append(f"{k}: {v}")
        self.stats_text.setText("\n".join(lines))

    def _forget_memory(self, text):
        reply = QMessageBox.question(self, "Forget Memory",
            f"Forget this memory?\n\n{text[:100]}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            mem.forget(text)
            self._refresh()

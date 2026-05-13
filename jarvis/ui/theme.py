from PyQt6.QtGui import QColor


class Theme:
    BG_PRIMARY = "#0a0a0f"
    BG_SECONDARY = "#12121a"
    BG_CARD = "rgba(20, 20, 35, 0.85)"
    BG_CARD_SOLID = "#141423"
    BG_HOVER = "rgba(40, 40, 70, 0.6)"
    BG_GLASS = "rgba(16, 16, 28, 0.75)"

    TEXT_PRIMARY = "#e8e8f0"
    TEXT_SECONDARY = "#9090b0"
    TEXT_MUTED = "#505070"

    ACCENT_PRIMARY = "#7c6aff"
    ACCENT_PRIMARY_GLOW = "rgba(124, 106, 255, 0.25)"
    ACCENT_SECONDARY = "#5ce0d0"
    ACCENT_SECONDARY_GLOW = "rgba(92, 224, 208, 0.2)"
    ACCENT_WARNING = "#f0c040"
    ACCENT_WARNING_GLOW = "rgba(240, 192, 64, 0.2)"
    ACCENT_ERROR = "#ff4070"
    ACCENT_ERROR_GLOW = "rgba(255, 64, 112, 0.2)"
    ACCENT_SUCCESS = "#20d0a0"
    ACCENT_SUCCESS_GLOW = "rgba(32, 208, 160, 0.2)"
    ACCENT_INFO = "#5090f0"
    ACCENT_INFO_GLOW = "rgba(80, 144, 240, 0.2)"

    BORDER = "rgba(50, 50, 80, 0.5)"
    BORDER_FOCUS = "#7c6aff"

    FONT_FAMILY = "SF Pro Display, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    FONT_MONO = "JetBrains Mono, Fira Code, monospace"

    CARD_RADIUS = "12px"
    BUTTON_RADIUS = "8px"
    INPUT_RADIUS = "10px"

    @classmethod
    def glass_style(cls, bg=None):
        b = bg or cls.BG_GLASS
        return f"""
            background-color: {b};
            border: 1px solid {cls.BORDER};
            border-radius: {cls.CARD_RADIUS};
        """

    @classmethod
    def card_style(cls):
        return f"""
            background-color: {cls.BG_CARD};
            border: 1px solid {cls.BORDER};
            border-radius: {cls.CARD_RADIUS};
        """

    @classmethod
    def get_stylesheet(cls):
        return f"""
        QMainWindow, QWidget {{
            background-color: {cls.BG_PRIMARY};
            color: {cls.TEXT_PRIMARY};
            font-family: {cls.FONT_FAMILY};
        }}
        QLabel {{
            color: {cls.TEXT_PRIMARY};
            background: transparent;
        }}
        QPushButton {{
            background-color: {cls.BG_CARD};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: {cls.BUTTON_RADIUS};
            padding: 8px 18px;
            font-size: 13px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {cls.BG_HOVER};
            border-color: {cls.ACCENT_PRIMARY};
        }}
        QPushButton:pressed {{
            background-color: {cls.ACCENT_PRIMARY};
            border-color: {cls.ACCENT_PRIMARY};
        }}
        QPushButton#accent {{
            background-color: {cls.ACCENT_PRIMARY};
            border: none;
            color: white;
            font-weight: 600;
        }}
        QPushButton#accent:hover {{
            background-color: #8a7aff;
        }}
        QPushButton#danger {{
            background-color: rgba(255, 64, 112, 0.15);
            border: 1px solid {cls.ACCENT_ERROR};
            color: {cls.ACCENT_ERROR};
        }}
        QPushButton#danger:hover {{
            background-color: rgba(255, 64, 112, 0.25);
        }}
        QLineEdit {{
            background-color: {cls.BG_SECONDARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: {cls.INPUT_RADIUS};
            padding: 11px 16px;
            font-size: 14px;
        }}
        QLineEdit:focus {{
            border-color: {cls.ACCENT_PRIMARY};
            background-color: rgba(124, 106, 255, 0.04);
        }}
        QTextEdit, QPlainTextEdit {{
            background-color: {cls.BG_SECONDARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: {cls.CARD_RADIUS};
            padding: 12px;
            font-family: {cls.FONT_MONO};
            font-size: 12px;
        }}
        QScrollBar:vertical {{
            background-color: transparent;
            width: 6px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background-color: {cls.BORDER};
            border-radius: 3px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {cls.ACCENT_PRIMARY};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background-color: transparent;
            height: 6px;
            border: none;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {cls.BORDER};
            border-radius: 3px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {cls.ACCENT_PRIMARY};
        }}
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        QTabWidget::pane {{
            border: none;
            background-color: transparent;
        }}
        QTabBar::tab {{
            background-color: transparent;
            color: {cls.TEXT_MUTED};
            padding: 10px 24px;
            border: none;
            border-bottom: 2px solid transparent;
            font-size: 13px;
            font-weight: 500;
            letter-spacing: 0.3px;
        }}
        QTabBar::tab:selected {{
            color: {cls.ACCENT_PRIMARY};
            border-bottom: 2px solid {cls.ACCENT_PRIMARY};
        }}
        QTabBar::tab:hover {{
            color: {cls.TEXT_SECONDARY};
        }}
        QComboBox {{
            background-color: {cls.BG_CARD};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: 6px;
            padding: 7px 12px;
            font-size: 13px;
            min-width: 140px;
        }}
        QComboBox:hover {{
            border-color: {cls.ACCENT_PRIMARY};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {cls.BG_CARD_SOLID};
            color: {cls.TEXT_PRIMARY};
            selection-background-color: {cls.ACCENT_PRIMARY};
            selection-color: white;
            border: 1px solid {cls.BORDER};
            border-radius: 6px;
            padding: 4px;
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 6px 12px;
            border-radius: 4px;
        }}
        QCheckBox {{
            color: {cls.TEXT_SECONDARY};
            spacing: 10px;
            font-size: 13px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 1px solid {cls.BORDER};
            background-color: rgba(20, 20, 35, 0.6);
        }}
        QCheckBox::indicator:checked {{
            background-color: {cls.ACCENT_PRIMARY};
            border-color: {cls.ACCENT_PRIMARY};
        }}
        QCheckBox::indicator:hover {{
            border-color: {cls.ACCENT_PRIMARY};
        }}
        QProgressBar {{
            background-color: {cls.BG_SECONDARY};
            border: none;
            border-radius: 3px;
            height: 6px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {cls.ACCENT_PRIMARY};
            border-radius: 3px;
        }}
        """

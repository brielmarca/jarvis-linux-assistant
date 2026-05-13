from PyQt6.QtGui import QColor


class Theme:
    BG_PRIMARY = "#1a1a1e"
    BG_SECONDARY = "#2c2c2e"
    BG_TERTIARY = "#3a3a3c"
    BG_SIDEBAR = "#151518"
    BG_CARD = "rgba(255, 255, 255, 0.055)"
    BG_CARD_HOVER = "rgba(255, 255, 255, 0.085)"
    BG_CARD_SOLID = "#242426"
    BG_HOVER = "rgba(255, 255, 255, 0.06)"
    BG_SELECTED = "rgba(124, 106, 255, 0.15)"
    BG_GLASS = "rgba(44, 44, 46, 0.72)"

    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "rgba(255, 255, 255, 0.65)"
    TEXT_TERTIARY = "rgba(255, 255, 255, 0.35)"
    TEXT_MUTED = "rgba(255, 255, 255, 0.22)"

    ACCENT_PRIMARY = "#7c6aff"
    ACCENT_PRIMARY_HOVER = "#8f7dff"
    ACCENT_PRIMARY_ACTIVE = "#6a58e0"
    ACCENT_PRIMARY_GLOW = "rgba(124, 106, 255, 0.2)"
    ACCENT_SECONDARY = "#5ce0d0"
    ACCENT_SECONDARY_GLOW = "rgba(92, 224, 208, 0.15)"
    ACCENT_WARNING = "#f0c040"
    ACCENT_WARNING_GLOW = "rgba(240, 192, 64, 0.15)"
    ACCENT_ERROR = "#ff4070"
    ACCENT_ERROR_GLOW = "rgba(255, 64, 112, 0.15)"
    ACCENT_SUCCESS = "#30d158"
    ACCENT_SUCCESS_GLOW = "rgba(48, 209, 88, 0.15)"
    ACCENT_INFO = "#5ac8fa"
    ACCENT_INFO_GLOW = "rgba(90, 200, 250, 0.15)"

    BORDER = "rgba(255, 255, 255, 0.1)"
    BORDER_HEAVY = "rgba(255, 255, 255, 0.15)"
    BORDER_FOCUS = "#7c6aff"
    SEPARATOR = "rgba(255, 255, 255, 0.06)"

    FONT_FAMILY = "-apple-system, SF Pro Display, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, sans-serif"
    FONT_MONO = "SF Mono, JetBrains Mono, Fira Code, monospace"

    RADIUS_WINDOW = "12px"
    RADIUS_CARD = "10px"
    RADIUS_BUTTON = "8px"
    RADIUS_INPUT = "8px"
    RADIUS_SMALL = "6px"
    RADIUS_TINY = "4px"

    SIDEBAR_WIDTH = 200
    TITLEBAR_HEIGHT = 38

    @classmethod
    def glass_style(cls, bg=None):
        b = bg or cls.BG_GLASS
        return f"""
            background-color: {b};
            border: 1px solid {cls.BORDER};
            border-radius: {cls.RADIUS_CARD};
        """

    @classmethod
    def card_style(cls):
        return f"""
            background-color: {cls.BG_CARD};
            border: 1px solid {cls.BORDER};
            border-radius: {cls.RADIUS_CARD};
        """

    @classmethod
    def panel_style(cls):
        return f"""
            background-color: {cls.BG_CARD_SOLID};
            border: 1px solid {cls.BORDER};
            border-radius: {cls.RADIUS_CARD};
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
            border: none;
        }}
        QPushButton {{
            background-color: {cls.BG_CARD};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: {cls.RADIUS_BUTTON};
            padding: 7px 18px;
            font-size: 12px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {cls.BG_CARD_HOVER};
            border-color: {cls.BORDER_HEAVY};
        }}
        QPushButton:pressed {{
            background-color: {cls.BG_TERTIARY};
        }}
        QPushButton#accent {{
            background-color: {cls.ACCENT_PRIMARY};
            border: none;
            color: white;
            font-weight: 600;
        }}
        QPushButton#accent:hover {{
            background-color: {cls.ACCENT_PRIMARY_HOVER};
        }}
        QPushButton#accent:pressed {{
            background-color: {cls.ACCENT_PRIMARY_ACTIVE};
        }}
        QPushButton#danger {{
            background-color: rgba(255, 64, 112, 0.1);
            border: 1px solid {cls.ACCENT_ERROR}66;
            color: {cls.ACCENT_ERROR};
        }}
        QPushButton#danger:hover {{
            background-color: rgba(255, 64, 112, 0.18);
        }}
        QLineEdit {{
            background-color: {cls.BG_SECONDARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: {cls.RADIUS_INPUT};
            padding: 10px 14px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border-color: {cls.ACCENT_PRIMARY};
        }}
        QTextEdit, QPlainTextEdit {{
            background-color: {cls.BG_SECONDARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: {cls.RADIUS_CARD};
            padding: 12px;
            font-family: {cls.FONT_MONO};
            font-size: 12px;
        }}
        QScrollBar:vertical {{
            background-color: transparent;
            width: 5px;
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
            height: 5px;
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
            color: {cls.TEXT_TERTIARY};
            padding: 10px 24px;
            border: none;
            border-bottom: 2px solid transparent;
            font-size: 12px;
            font-weight: 500;
        }}
        QTabBar::tab:selected {{
            color: {cls.ACCENT_PRIMARY};
            border-bottom: 2px solid {cls.ACCENT_PRIMARY};
        }}
        QTabBar::tab:hover {{
            color: {cls.TEXT_SECONDARY};
        }}
        QComboBox {{
            background-color: {cls.BG_SECONDARY};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: {cls.RADIUS_SMALL};
            padding: 6px 12px;
            font-size: 12px;
            min-width: 130px;
        }}
        QComboBox:hover {{
            border-color: {cls.BORDER_HEAVY};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 22px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {cls.BG_CARD_SOLID};
            color: {cls.TEXT_PRIMARY};
            selection-background-color: {cls.ACCENT_PRIMARY};
            selection-color: white;
            border: 1px solid {cls.BORDER};
            border-radius: {cls.RADIUS_SMALL};
            padding: 4px;
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 6px 12px;
            border-radius: {cls.RADIUS_TINY};
        }}
        QCheckBox {{
            color: {cls.TEXT_SECONDARY};
            spacing: 8px;
            font-size: 13px;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border-radius: {cls.RADIUS_TINY};
            border: 1px solid {cls.BORDER};
            background-color: {cls.BG_CARD};
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
            height: 4px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {cls.ACCENT_PRIMARY};
            border-radius: 3px;
        }}
        QTableWidget {{
            background-color: {cls.BG_CARD};
            border: 1px solid {cls.BORDER};
            border-radius: {cls.RADIUS_CARD};
            color: {cls.TEXT_SECONDARY};
            font-size: 12px;
            gridline-color: {cls.SEPARATOR};
        }}
        QTableWidget::item {{
            padding: 8px 12px;
        }}
        QHeaderView::section {{
            background-color: {cls.BG_SIDEBAR};
            color: {cls.TEXT_SECONDARY};
            border: none;
            border-bottom: 1px solid {cls.BORDER};
            padding: 8px 12px;
            font-weight: 600;
            font-size: 11px;
        }}
        """

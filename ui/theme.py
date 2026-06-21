"""Global QSS theme for Nexora LMS."""

FONT_FAMILY = "Segoe UI"

COLORS = {
    "bg": "#EBEEF2",
    "surface": "#FFFFFF",
    "sidebar": "#1A2B3C",
    "sidebar_hover": "#243447",
    "sidebar_active": "#0D6E6E",
    "text": "#1A2B3C",
    "text_secondary": "#6B7C8F",
    "text_muted": "#94A3B8",
    "text_on_dark": "#E2E8F0",
    "accent": "#0D6E6E",
    "accent_hover": "#0A5555",
    "border": "#D8DEE6",
    "border_subtle": "#E2E8F0",
    "success": "#2E7D5B",
    "warning": "#C47A00",
    "danger": "#C0392B",
}

STAT_COLORS = ("#0D6E6E", "#2563EB", "#7C3AED", "#2E7D5B")

STAT_VALUE_STYLE = (
    "font-size: 32px; font-weight: 700; color: {color}; "
    f"font-family: '{FONT_FAMILY}';"
)
STAT_TITLE_STYLE = (
    f"font-size: 13px; font-weight: 600; color: {COLORS['text']}; "
    f"font-family: '{FONT_FAMILY}';"
)
STAT_DESC_STYLE = (
    f"font-size: 11px; color: {COLORS['text_muted']}; "
    f"font-family: '{FONT_FAMILY}';"
)
STAT_CARD_STYLE = (
    f"background: {COLORS['surface']}; border-radius: 12px; "
    f"border: 1px solid {COLORS['border']}; min-height: 108px;"
)


def application_stylesheet():
    c = COLORS
    return f"""
    * {{
        font-family: "{FONT_FAMILY}";
        font-size: 13px;
    }}

    QMainWindow, QDialog {{
        background-color: {c['bg']};
    }}

    QWidget#contentRoot {{
        background-color: {c['bg']};
    }}

    QStackedWidget#pageStack,
    QWidget[class="pageRoot"] {{
        background-color: {c['bg']};
    }}

    QScrollArea#contentScroll {{
        background-color: {c['bg']};
        border: none;
    }}

    QScrollArea#contentScroll > QWidget > QWidget {{
        background-color: {c['bg']};
    }}

    QLabel {{
        color: {c['text']};
        background: transparent;
    }}

    QWidget#contentRoot QLabel {{
        color: {c['text']};
    }}

    QWidget#topHeader QLabel {{
        color: {c['text']};
    }}

    QWidget#loginBrandPanel QLabel[class="brandTitle"] {{
        font-size: 26px;
        font-weight: 700;
        color: white;
    }}

    QWidget#loginBrandPanel QLabel[class="brandSubtitle"] {{
        font-size: 14px;
        color: {c['text_on_dark']};
    }}

    QWidget#sidebarRoot QLabel[class="brandTitle"] {{
        font-size: 26px;
        font-weight: 700;
        color: white;
    }}

    QWidget#sidebarRoot QLabel[class="brandSubtitle"] {{
        font-size: 14px;
        color: {c['text_on_dark']};
    }}

    QLabel[class="pageTitle"] {{
        font-size: 24px;
        font-weight: 700;
        color: {c['text']};
        padding: 16px 0 20px 0;
        background: transparent;
    }}

    QLabel[class="welcomeHeading"] {{
        font-size: 24px;
        font-weight: 700;
        color: {c['text']};
        padding: 0 0 4px 0;
        background: transparent;
    }}

    QLabel[class="headerUser"] {{
        color: {c['text_secondary']};
        font-size: 13px;
        padding-right: 12px;
    }}

    QLabel[class="pageSubtitle"] {{
        font-size: 13px;
        color: {c['text_secondary']};
        padding-bottom: 16px;
    }}

    QLabel[class="loginHeading"] {{
        font-size: 20px;
        font-weight: 700;
        color: {c['text']};
    }}

    QFormLayout QLabel {{
        color: {c['text_secondary']};
    }}

    QGroupBox {{
        font-weight: 600;
        font-size: 14px;
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 12px;
        margin-top: 18px;
        padding: 20px 16px 16px 16px;
        background-color: {c['surface']};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 16px;
        padding: 0 8px;
        color: {c['text']};
    }}

    QGroupBox[class="actionsBar"] {{
        border: none;
        background: transparent;
        margin-top: 4px;
        padding: 0;
    }}

    QGroupBox[class="actionsBar"]::title {{
        subcontrol-position: top left;
        padding: 0 0 8px 0;
    }}

    QLabel[class="sectionTitle"] {{
        font-size: 15px;
        font-weight: 600;
        color: {c['text']};
        padding: 4px 0 10px 0;
        background: transparent;
    }}

    QWidget[class="sectionPanel"] {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 12px;
    }}

    QWidget[class="loginCard"] {{
        background-color: {c['surface']};
        border: none;
        border-radius: 12px;
        min-width: 340px;
        max-width: 380px;
    }}

    QLabel[class="statTitle"] {{
        font-size: 13px;
        font-weight: 600;
        color: {c['text']};
    }}

    QLabel[class="statDesc"] {{
        font-size: 11px;
        color: {c['text_secondary']};
    }}

    QWidget[class="statCard"] {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 12px;
        min-height: 118px;
    }}

    QListWidget[class="flatList"] {{
        background-color: transparent;
        border: none;
        padding: 0;
    }}

    QLineEdit {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 10px 12px;
        color: {c['text']};
        min-height: 20px;
    }}

    QLineEdit:focus {{
        border: 1px solid {c['accent']};
    }}

    QPushButton {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 10px 18px;
        font-weight: 600;
        min-height: 20px;
        outline: none;
    }}

    QPushButton:hover {{
        background-color: #F1F5F9;
        border-color: #CBD5E1;
        color: {c['text']};
    }}

    QPushButton:pressed {{
        background-color: #E2E8F0;
    }}

    QPushButton[class="headerBtn"] {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 7px 16px;
        font-weight: 500;
        min-width: 88px;
    }}

    QPushButton[class="headerBtn"]:hover {{
        background-color: #F8FAFC;
        border-color: #CBD5E1;
    }}

    QPushButton[class="actionBtn"] {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        min-height: 20px;
    }}

    QPushButton[class="actionBtn"]:hover {{
        background-color: #F8FAFC;
        border-color: #CBD5E1;
    }}

    QPushButton[class="primary"] {{
        background-color: {c['accent']};
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        padding: 10px 22px;
        font-weight: 600;
        min-height: 38px;
        min-width: 100px;
    }}

    QPushButton[class="primary"]:hover {{
        background-color: {c['accent_hover']};
        color: #FFFFFF;
    }}

    QPushButton[class="sidebarNav"] {{
        background-color: transparent;
        color: {c['text_on_dark']};
        border: none;
        border-radius: 10px;
        text-align: left;
        padding: 12px 16px;
        font-weight: 500;
    }}

    QPushButton[class="sidebarNav"]:hover {{
        background-color: {c['sidebar_hover']};
    }}

    QPushButton[class="sidebarNavActive"] {{
        background-color: {c['sidebar_active']};
        color: white;
        border: none;
        border-radius: 10px;
        text-align: left;
        padding: 12px 16px;
        font-weight: 600;
    }}

    QTableWidget {{
        background-color: {c['surface']};
        alternate-background-color: #F8FAFC;
        border: none;
        border-radius: 8px;
        gridline-color: {c['border']};
        selection-background-color: #D1FAF0;
        selection-color: {c['text']};
        color: {c['text']};
        outline: none;
    }}

    QTableWidget::item {{
        color: {c['text']};
    }}

    QHeaderView::section {{
        background-color: #F8FAFC;
        color: {c['text_secondary']};
        padding: 10px 8px;
        border: none;
        border-bottom: 1px solid {c['border']};
        font-weight: 600;
        font-size: 12px;
    }}

    QProgressBar {{
        border: none;
        border-radius: 6px;
        background-color: #E2E8F0;
        text-align: center;
        color: {c['text']};
        min-height: 22px;
    }}

    QProgressBar::chunk {{
        background-color: {c['accent']};
        border-radius: 6px;
    }}

    QListWidget {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 4px;
        color: {c['text']};
    }}

    QListWidget::item {{
        padding: 6px 8px;
        border-radius: 4px;
        color: {c['text']};
    }}

    QListWidget::item:selected {{
        background-color: #CCEDED;
        color: {c['text']};
    }}

    QTabWidget::pane {{
        border: none;
        background: transparent;
    }}

    QTabBar::tab {{
        display: none;
    }}

    QScrollArea {{
        border: none;
        background: transparent;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: #CBD5E1;
        border-radius: 5px;
        min-height: 24px;
    }}

    QDialog QLabel {{
        color: {c['text']};
    }}

    QStatusBar {{
        background-color: {c['surface']};
        color: {c['text_secondary']};
        border-top: 1px solid {c['border']};
    }}

    QWidget#loginBrandPanel {{
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['accent']}, stop:1 {c['accent_hover']}
        );
    }}

    QWidget#loginFormPanel {{
        background-color: {c['surface']};
    }}

    QWidget#sidebarRoot {{
        background-color: {c['sidebar']};
    }}

    QWidget#topHeader {{
        background-color: {c['surface']};
        border-bottom: 1px solid {c['border']};
        padding: 0 4px;
    }}
    """

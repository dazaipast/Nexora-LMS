from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from constants import APP_FULL_NAME
from ui.style_helpers import styled_widget
from ui.theme import COLORS


class SidebarNav(QWidget):
    """Left navigation with stacked content pages."""

    page_selected = pyqtSignal(int)

    def __init__(
        self,
        pages,
        brand=APP_FULL_NAME,
        subtitle="",
        header_widget=None,
        parent=None,
    ):
        super().__init__(parent)
        self._page_titles = []
        self._nav_buttons = []
        self._stack = styled_widget(QStackedWidget(), "pageStack")
        self._stack.setObjectName("pageStack")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = styled_widget(QWidget(), "sidebarRoot")
        sidebar.setObjectName("sidebarRoot")
        sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 24, 20, 24)
        sidebar_layout.setSpacing(6)

        brand_label = QLabel(brand)
        brand_label.setProperty("class", "brandTitle")
        brand_label.setWordWrap(True)
        sidebar_layout.addWidget(brand_label)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setProperty("class", "brandSubtitle")
            sub.setWordWrap(True)
            sidebar_layout.addWidget(sub)

        sidebar_layout.addSpacing(24)

        for index, (title, page) in enumerate(pages):
            widget = page() if callable(page) else page
            styled_widget(widget, "pageRoot")
            self._page_titles.append(title)
            self._stack.addWidget(widget)

            btn = QPushButton(title)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, i=index: self.select_page(i))
            self._nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()
        root.addWidget(sidebar)

        content_wrapper = styled_widget(QWidget(), "contentRoot")
        content_wrapper.setObjectName("contentRoot")
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(28, 0, 28, 24)
        content_layout.setSpacing(0)

        if header_widget is not None:
            content_layout.addWidget(header_widget)

        self.page_title = QLabel()
        styled_widget(self.page_title, "pageTitle")
        content_layout.addWidget(self.page_title)

        scroll = QScrollArea()
        scroll.setObjectName("contentScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.viewport().setAutoFillBackground(True)
        scroll.viewport().setStyleSheet(f"background-color: {COLORS['bg']}; border: none;")
        scroll.setStyleSheet(f"background-color: {COLORS['bg']}; border: none;")
        scroll.setWidget(self._stack)
        content_layout.addWidget(scroll, 1)

        root.addWidget(content_wrapper, 1)

        if pages:
            self.select_page(0)

    @property
    def stack(self):
        return self._stack

    def select_page(self, index):
        if index < 0 or index >= self._stack.count():
            return
        self._stack.setCurrentIndex(index)
        self.page_title.setText(self._page_titles[index])
        for i, btn in enumerate(self._nav_buttons):
            btn.setProperty("class", "sidebarNavActive" if i == index else "sidebarNav")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.page_selected.emit(index)

    def select_page_by_title(self, title):
        try:
            index = self._page_titles.index(title)
        except ValueError:
            return
        self.select_page(index)

    def page_title_at(self, index):
        if 0 <= index < len(self._page_titles):
            return self._page_titles[index]
        return ""


class SidebarTabProxy:
    """Proxy so QuickActionsMixin._switch_to_tab works with SidebarNav."""

    def __init__(self, sidebar):
        self._sidebar = sidebar

    def count(self):
        return self._sidebar.stack.count()

    def tabText(self, index):
        return self._sidebar.page_title_at(index)

    def setCurrentIndex(self, index):
        self._sidebar.select_page(index)

"""Helpers to apply QSS classes and card elevation."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect


def styled_widget(widget, css_class=None):
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    if css_class:
        widget.setProperty("class", css_class)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
    return widget


def apply_card_shadow(widget, blur=20, offset_y=3, alpha=28):
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, offset_y)
    effect.setColor(QColor(26, 43, 60, alpha))
    widget.setGraphicsEffect(effect)
    return widget

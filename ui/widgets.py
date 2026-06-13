"""Reusable styled layout blocks."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout

from ui.style_helpers import styled_widget


def create_section_header(title):
    label = QLabel(title)
    styled_widget(label, "sectionTitle")
    return label


def create_section_panel(margins=(16, 16, 16, 16), spacing=12):
    panel = styled_widget(QWidget(), "sectionPanel")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return panel, layout


def create_stat_grid(stat_cards, columns=3, spacing=12):
    grid = QGridLayout()
    grid.setSpacing(spacing)
    for index, card in enumerate(stat_cards):
        grid.addWidget(card, index // columns, index % columns)
    for column in range(columns):
        grid.setColumnStretch(column, 1)
    return grid

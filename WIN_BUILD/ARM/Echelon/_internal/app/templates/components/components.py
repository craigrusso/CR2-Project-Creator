# ui_components.py

from PyQt6.QtWidgets import (QWidget, QScrollArea, QVBoxLayout, QFrame, QLabel, 
                             QLineEdit, QHBoxLayout, QToolTip)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from .utils import SYSTEM_FONT
from .color_scheme import colors

class ScrollableFrame(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        content_widget = QWidget()
        self.setWidget(content_widget)
        self.layout = QVBoxLayout(content_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def add_widget(self, widget):
        self.layout.addWidget(widget)


class CardFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"""
            background-color: {colors["card_bg"]};
            border-radius: 6px;
        """)


class ToolTip:
    @staticmethod
    def show_tooltip(widget, message):
        QToolTip.setFont(QFont(SYSTEM_FONT, 10))
        QToolTip.showText(widget.mapToGlobal(widget.rect().center()), message)


class SearchBox(QWidget):
    textChanged = pyqtSignal(str)

    def __init__(self, parent=None, placeholder="Search..."):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel("🔍")
        label.setFont(QFont(SYSTEM_FONT, 14))
        layout.addWidget(label)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.textChanged.connect(self.textChanged.emit)
        layout.addWidget(self.line_edit)

        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors["card_bg"]};
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }}
            QLineEdit:focus {{
                background-color: {colors["hover_bg"]};
            }}
            QLabel {{
                color: #FFFFFF;
                background: transparent;
            }}
        """)

    def text(self):
        return self.line_edit.text()

    def clear(self):
        self.line_edit.clear()
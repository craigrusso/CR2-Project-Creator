#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Custom menu action classes for the CR2 Project Creator PyQt UI
Provides specialized action types that can be styled differently
"""

from PyQt6.QtWidgets import QAction, QMenu, QWidgetAction, QLabel
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal
from app.ui.color_scheme_pyqt import colors

class DeleteLabel(QLabel):
    """
    Custom QLabel that changes styling on hover for the Delete action
    """
    clicked = pyqtSignal()
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMouseTracking(True)
        self.normalStyle = "color: #FF5555; font-weight: bold; padding: 5px 15px;"
        self.hoverStyle = "color: white; font-weight: bold; background-color: #FF3333; padding: 5px 15px; border-radius: 3px;"
        self.setStyleSheet(self.normalStyle)
        
    def enterEvent(self, event):
        self.setStyleSheet(self.hoverStyle)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.setStyleSheet(self.normalStyle)
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class CustomMenu(QMenu):
    """
    A QMenu with special styling for the Delete action.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Basic menu styling
        self.setStyleSheet("""
            QMenu {
                background-color: #252526;
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                padding: 5px;
                border-radius: 4px;
            }
            QMenu::item {
                padding: 5px 20px 5px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #2C4F76;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #3C3C3C;
                margin: 5px 0px 5px 0px;
            }
        """)
    
    def addRedDeleteAction(self, parent=None, callback=None, text="Delete"):
        """
        Add a Delete action with red text using QWidgetAction for maximum control.
        This bypasses stylesheet limitations on macOS.
        
        Parameters:
        - parent: The parent widget for the action
        - callback: Function to call when clicked
        - text: Custom text for the delete action (default is "Delete")
        """
        # Create a custom widget action
        widget_action = QWidgetAction(parent or self)
        
        # Use our custom DeleteLabel that handles hover and click events
        label = DeleteLabel(text)
        
        # Connect the label's clicked signal to the callback
        if callback:
            label.clicked.connect(callback)
            
        # Set the label as the default widget for our action
        widget_action.setDefaultWidget(label)
        
        # Add to this menu
        self.addAction(widget_action)
        return widget_action

# For compatibility with existing code
ContextMenu = CustomMenu 
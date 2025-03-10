#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QMenu)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QMimeData, QByteArray
from PyQt5.QtGui import QCursor, QFont, QDrag, QPixmap

from app.ui.color_scheme_pyqt import colors

# Constants for styling
BLUE_HIGHLIGHT = colors["highlight_bg"]
CARD_NORMAL = colors["card_bg"]
CARD_HOVER = colors["hover_bg"]
CARD_SELECTED = colors["highlight_bg"]

# Get suitable system font for different platforms
def get_system_font():
    """Return an appropriate system font based on platform"""
    system = platform.system()
    if system == "Windows":
        return "Segoe UI"
    elif system == "Darwin":  # macOS
        return "Helvetica Neue"  # Just use Helvetica which is guaranteed to exist
    else:  # Linux and others
        return "Ubuntu,DejaVu Sans,Liberation Sans,Arial"

# System font to use throughout the app
SYSTEM_FONT = get_system_font()

class TemplateCard(QFrame):
    """Template card widget for displaying a template in the gallery"""
    
    clicked = pyqtSignal(object)
    
    def __init__(self, parent=None, template=None, app=None):
        super().__init__(parent)
        self.template = template
        self.app = app
        self.selected = False
        self.hover = False
        self.drag_start_position = None  # Initialize drag start position
        
        # Configure frame appearance
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(1)
        self.setCursor(Qt.PointingHandCursor)
        
        # Style settings
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_NORMAL};
                border: 1px solid {colors["border"]};
                border-radius: 5px;
                padding: 10px;
            }}
        """)
        
        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # Icon label - use emoji for simplicity
        icon = template.get("icon", "📄")
        self.icon_label = QLabel(icon)
        self.icon_label.setFont(QFont(SYSTEM_FONT, 24))
        self.icon_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
        self.layout.addWidget(self.icon_label)
        
        # Info section
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(3)
        self.layout.addLayout(self.info_layout, 1)  # Stretch
        
        # Template name
        self.name_label = QLabel(template.get("name", "Unnamed Template"))
        self.name_label.setFont(QFont(SYSTEM_FONT, 11, QFont.Bold))
        self.name_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
        self.info_layout.addWidget(self.name_label)
        
        # Category
        self.category_label = QLabel(template.get("category", "Custom"))
        self.category_label.setFont(QFont(SYSTEM_FONT, 9))
        self.category_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
        self.info_layout.addWidget(self.category_label)
        
        # Description
        description = template.get("description", "")
        if description:
            self.desc_label = QLabel(description)
            self.desc_label.setFont(QFont(SYSTEM_FONT, 9))
            self.desc_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
            self.desc_label.setWordWrap(True)
            self.info_layout.addWidget(self.desc_label)
        
        # Connect events
        self.mousePressEvent = self._on_mouse_press
        self.mouseMoveEvent = self._on_mouse_move
        self.enterEvent = self._on_hover_enter
        self.leaveEvent = self._on_hover_leave
        self.contextMenuEvent = self._on_context_menu
    
    def _on_mouse_press(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.LeftButton:
            # Store drag start position
            self.drag_start_position = event.pos()
            # Emit clicked signal
            self.clicked.emit(self.template)
    
    def _on_mouse_move(self, event):
        """Handle mouse move event for drag and drop"""
        # Skip if drag start position is not set or left button is not pressed
        if not self.drag_start_position or not (event.buttons() & Qt.LeftButton):
            return
            
        # Compute distance to determine if it's a drag
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return
        
        print(f"[DEBUG] TemplateCard: Starting drag for template '{self.template.get('name', '')}'")
        
        # Create a drag object
        drag = QDrag(self)
        
        # Create mime data with template information
        mime_data = QMimeData()
        
        # Add the template name as text for simple drag/drop operations
        template_name = self.template.get('name', '')
        mime_data.setText(template_name)
        print(f"[DEBUG] TemplateCard: Added template name '{template_name}' as text to mime data")
        
        # Also add the complete template as JSON data for more advanced operations
        try:
            import json
            template_json = json.dumps(self.template).encode()
            mime_data.setData("application/json", QByteArray(template_json))
            print(f"[DEBUG] TemplateCard: Added template as JSON to mime data")
        except Exception as e:
            print(f"[DEBUG] TemplateCard: Error adding JSON data: {e}")
        
        # Set the mime data on the drag object
        drag.setMimeData(mime_data)
        
        # Create a pixmap for the drag feedback
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        
        # Execute the drag operation
        print(f"[DEBUG] TemplateCard: Executing drag operation")
        result = drag.exec_(Qt.CopyAction)
        print(f"[DEBUG] TemplateCard: Drag operation completed with result: {result}")
        
        # Reset drag start position
        self.drag_start_position = None
    
    def _on_hover_enter(self, event):
        """Handle hover enter event"""
        if not self.selected:
            self.hover = True
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {CARD_HOVER};
                    border: 1px solid {colors["border"]};
                    border-radius: 5px;
                    padding: 10px;
                }}
            """)
    
    def _on_hover_leave(self, event):
        """Handle hover leave event"""
        if not self.selected:
            self.hover = False
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {CARD_NORMAL};
                    border: 1px solid {colors["border"]};
                    border-radius: 5px;
                    padding: 10px;
                }}
            """)
    
    def _on_context_menu(self, event):
        """Handle context menu event"""
        if self.app:
            # TODO: Implement context menu
            pass
    
    def set_highlighted(self, highlighted):
        """Set highlighted state"""
        self.selected = highlighted
        self._update_styling()

    def set_selected(self, selected):
        """Set selected state (alias for set_highlighted for compatibility)"""
        self.set_highlighted(selected)
    
    def _update_styling(self):
        """Update styling based on selected and hover state"""
        if self.selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {CARD_SELECTED};
                    border: 1px solid {colors["highlight_border"]};
                    border-radius: 5px;
                    padding: 10px;
                }}
            """)
            self.icon_label.setStyleSheet(f"color: white; background: transparent;")
            self.name_label.setStyleSheet(f"color: white; background: transparent;")
            self.category_label.setStyleSheet(f"color: white; background: transparent;")
            if hasattr(self, 'desc_label'):
                self.desc_label.setStyleSheet(f"color: white; background: transparent;")
        elif self.hover:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {CARD_HOVER};
                    border: 1px solid {colors["border"]};
                    border-radius: 5px;
                    padding: 10px;
                }}
            """)
            self.icon_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
            self.name_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
            self.category_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
            if hasattr(self, 'desc_label'):
                self.desc_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {CARD_NORMAL};
                    border: 1px solid {colors["border"]};
                    border-radius: 5px;
                    padding: 10px;
                }}
            """)
            self.icon_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
            self.name_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
            self.category_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
            if hasattr(self, 'desc_label'):
                self.desc_label.setStyleSheet(f"color: {colors['text']}; background: transparent;") 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import platform
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                           QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QTimer
from PyQt5.QtGui import QFont

from app.ui.color_scheme_pyqt import colors

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

class TemplateListItem(QFrame):
    """Template list item widget for displaying a template in list view"""
    
    clicked = pyqtSignal(object)
    
    def __init__(self, parent=None, template=None, app=None):
        super().__init__(parent)
        self.template = template
        self.app = app
        self.selected = False
        self.hover = False
        self.is_odd_row = False  # Add this attribute to fix list view disappearing
        
        # Configure frame appearance - use clean, borderless macOS style
        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(0)
        self.setFixedHeight(40)  # Slightly reduced height for macOS-like compactness
        self.setCursor(Qt.PointingHandCursor)
        
        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(10)
        
        # Template icon
        icon_text = template.get('icon', '📄')
        self.icon_label = QLabel(icon_text)
        self.icon_label.setFont(QFont(SYSTEM_FONT, 20))
        self.icon_label.setStyleSheet(f"color: {colors['accent']}; background: transparent;")
        self.icon_label.setFixedWidth(40)
        self.layout.addWidget(self.icon_label)
        
        # Template name and description
        self.info_layout = QVBoxLayout()
        self.info_layout.setContentsMargins(0, 0, 0, 0)
        self.info_layout.setSpacing(0)
        
        # Template name
        self.name_label = QLabel(template.get('name', 'Unnamed Template'))
        self.name_label.setFont(QFont(SYSTEM_FONT, 12))
        self.name_label.setStyleSheet("color: white; font-weight: bold; background: transparent;")
        self.info_layout.addWidget(self.name_label)
        
        # Template description (truncated)
        description = template.get('description', '')
        if len(description) > 50:
            description = description[:47] + "..."
        self.desc_label = QLabel(description)
        self.desc_label.setFont(QFont(SYSTEM_FONT, 9))
        self.desc_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
        self.info_layout.addWidget(self.desc_label)
        
        self.layout.addLayout(self.info_layout, 1)  # Give it stretch factor
        
        # Category/Type
        category = template.get('category', 'General')
        self.category_label = QLabel(category)
        self.category_label.setFont(QFont(SYSTEM_FONT, 9))
        self.category_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
        self.layout.addWidget(self.category_label)
        
        # Install event filter
        self.installEventFilter(self)
        self._update_styling()
    
    def eventFilter(self, obj, event):
        """Filter events for mouse tracking"""
        if obj is self:
            if event.type() == QEvent.MouseButtonPress:
                self.clicked.emit(self.template)
                return True
            elif event.type() == QEvent.Enter:
                if not self.hover:  # Only update if hover state changes
                    self.hover = True
                    self._update_styling()
                return True  # Return True to handle the event completely
            elif event.type() == QEvent.Leave:
                if self.hover:  # Only update if hover state changes
                    self.hover = False
                    
                    # Explicit reset to the correct background color
                    if self.property("row_type") == "odd":
                        bg_color = colors["card_bg"]  # Darker for odd rows
                    else:
                        bg_color = colors["bg"]  # Lighter for even rows
                        
                    self.setStyleSheet(f"""
                        QFrame {{
                            background-color: {bg_color};
                            border: none;
                            border-radius: 0px;
                        }}
                    """)
                    
                    self._update_styling()
                return True  # Return True to handle the event completely
        return super().eventFilter(obj, event)
    
    def _on_hover_enter(self):
        self.hover = True
        self._update_styling()
    
    def _on_hover_leave(self):
        self.hover = False
        self._update_styling()
    
    def set_selected(self, selected):
        """Set the selected state of this template item"""
        self.selected = selected
        self._update_styling()
        
    def set_row_type(self, row_type):
        """Set whether this is an odd or even row for styling"""
        self.setProperty("row_type", row_type)
        self._update_styling()
    
    def _update_styling(self):
        """Update the styling based on current state - macOS style"""
        if self.selected:
            # Selected style (blue background, white text)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["highlight_bg"]};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            # Update other labels safely
            if hasattr(self, 'desc_label'):
                self.desc_label.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent;")
            if hasattr(self, 'category_label'):
                self.category_label.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent;")
            if hasattr(self, 'icon_label'):
                self.icon_label.setStyleSheet(f"color: {colors['highlight_text']}; background: transparent;")
            if hasattr(self, 'name_label'):
                self.name_label.setStyleSheet(f"color: {colors['highlight_text']}; font-weight: bold; background: transparent;")
        elif self.hover:
            # Hover style (slightly lighter background)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors["hover_bg"]};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            # Update other labels safely
            if hasattr(self, 'desc_label'):
                self.desc_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
            if hasattr(self, 'category_label'):
                self.category_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
            if hasattr(self, 'icon_label'):
                self.icon_label.setStyleSheet(f"color: {colors['folder_icon']}; background: transparent;")
            if hasattr(self, 'name_label'):
                self.name_label.setStyleSheet(f"color: white; font-weight: bold; background: transparent;")
        else:
            # Normal style - use clean macOS style (no borders, alternate row colors for list)
            # Use proper colors based on row type for consistent appearance
            if self.property("row_type") == "odd":
                bg_color = colors["card_bg"]  # Darker for odd rows
            else:
                bg_color = colors["bg"]  # Lighter for even rows
                
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border: none;
                    border-radius: 0px;
                }}
            """)
            # Update other labels safely
            if hasattr(self, 'desc_label'):
                self.desc_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
            if hasattr(self, 'category_label'):
                self.category_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
            if hasattr(self, 'icon_label'):
                self.icon_label.setStyleSheet(f"color: {colors['folder_icon']}; background: transparent;")
            if hasattr(self, 'name_label'):
                self.name_label.setStyleSheet("color: white; font-weight: bold; background: transparent;")

    def leaveEvent(self, event):
        """Explicit leave event handler to ensure hover state is reset when mouse exits the widget"""
        # Force hover state to False
        self.hover = False
        
        # Explicit styling reset
        if self.property("row_type") == "odd":
            bg_color = colors["card_bg"]  # Darker for odd rows
        else:
            bg_color = colors["bg"]  # Lighter for even rows
            
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: none;
                border-radius: 0px;
            }}
        """)
        
        # Complete update of all labels
        self._update_styling()
        
        # Call the base class method
        super().leaveEvent(event)
        
    def mouseMoveEvent(self, event):
        """Handle mouse move events to update hover state"""
        # Only set hover state if the mouse is actually over the widget
        rect = self.rect()
        if rect.contains(event.pos()):
            if not self.hover:
                self.hover = True
                self._update_styling()
        else:
            if self.hover:
                self.hover = False
                self._update_styling()
        super().mouseMoveEvent(event)

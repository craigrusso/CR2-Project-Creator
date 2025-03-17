#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template list item component for the template gallery.
This is a simplified version that includes just the necessary methods
to avoid crashes from missing methods.
"""

import time
import datetime
import os
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QFont, QPalette, QColor

# Simple, stable implementation with minimal dependencies
class TemplateListItem(QFrame):
    """List item for template in list view"""
    
    # Initialize signals
    clicked = pyqtSignal(object)  # Signal for click - passes template data
    doubleClicked = pyqtSignal(object)  # Signal for double-click - passes template data
    deleteRequested = pyqtSignal(str)  # Signal for delete request - passes template name
    
    def __init__(self, template, gallery=None, row_index=None):
        super().__init__()
        
        # Store essential parameters
        self.template = template
        self.gallery = gallery
        self.row_index = row_index  # For striped rows
        
        # Initialize state
        self.selected = False
        self.multi_selected = False
        self.hover = False  # Initialize hover state explicitly
        
        # Configure frame appearance
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        
        # Set size policy to expand horizontally
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)
        
        # Icon label (template icon)
        self.icon_label = QLabel("📄")
        self.icon_label.setFixedWidth(24)
        layout.addWidget(self.icon_label)
        
        # Name label
        template_name = template.get('name', 'Untitled Template') if isinstance(template, dict) else str(template)
        self.name_label = QLabel(template_name)
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.name_label, 1)
        
        # Format timestamps safely
        created_timestamp = template.get('created', time.time()) if isinstance(template, dict) else time.time()
        modified_timestamp = template.get('modified', created_timestamp) if isinstance(template, dict) else time.time()
        
        created_date_str = self._format_date(created_timestamp)
        modified_date_str = self._format_date(modified_timestamp)
        
        # Created date
        self.created_date_label = QLabel(created_date_str)
        self.created_date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.created_date_label.setFixedWidth(130)
        layout.addWidget(self.created_date_label)
        
        # Modified date
        self.modified_date_label = QLabel(modified_date_str)
        self.modified_date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.modified_date_label.setFixedWidth(130)
        layout.addWidget(self.modified_date_label)
        
        # Apply initial styling
        self._update_styling()
        
        # Install event filter for hover effects
        self.installEventFilter(self)

    def _format_date(self, timestamp):
        """Format a timestamp into a readable date string"""
        try:
            if isinstance(timestamp, (int, float)):
                dt = datetime.datetime.fromtimestamp(timestamp)
                return dt.strftime("%Y-%m-%d %H:%M")
            return "Unknown"
        except Exception as e:
            print(f"Error formatting date: {e}")
            return "Unknown"
            
    def _update_styling(self):
        """Update styling based on selection and hover state"""
        try:
            # Set background color based on state
            if self.selected:
                bg_color = "#2C4F76"  # Blue for selected
                text_color = "white"
                font_weight = "bold"
            elif self.hover:
                bg_color = "#404040"  # Darker gray for hover
                text_color = "white"
                font_weight = "bold"
            elif self.row_index is not None and self.row_index % 2 == 1:
                bg_color = "#2A2A2A"  # Alternate row color
                text_color = "#CCCCCC"
                font_weight = "normal"
            else:
                bg_color = "transparent"
                text_color = "#CCCCCC"
                font_weight = "normal"
            
            # Apply styles
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border: none;
                    border-radius: 4px;
                }}
            """)
            
            label_style = f"color: {text_color}; font-weight: {font_weight};"
            self.name_label.setStyleSheet(label_style)
            self.icon_label.setStyleSheet(label_style)
            self.created_date_label.setStyleSheet(label_style)
            self.modified_date_label.setStyleSheet(label_style)
            
        except Exception as e:
            print(f"Error updating list item styling: {e}")
    
    def setSelected(self, selected):
        """Set the selection state"""
        if self.selected != selected:
            self.selected = selected
            self._update_styling()
    
    def setMultiSelected(self, multi_selected):
        """Set the multi-selection state"""
        if self.multi_selected != multi_selected:
            self.multi_selected = multi_selected
            self._update_styling()
    
    def setRowIndex(self, index):
        """Set the row index for striped rows"""
        self.row_index = index
        self._update_styling()
    
    def mousePressEvent(self, event):
        """Handle mouse press event"""
        super().mousePressEvent(event)
        self.clicked.emit(self.template)
    
    def mouseDoubleClickEvent(self, event):
        """Handle mouse double click event"""
        super().mouseDoubleClickEvent(event)
        self.doubleClicked.emit(self.template)
    
    def enterEvent(self, event):
        """Handle mouse enter event"""
        self.hover = True
        self._update_styling()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event"""
        self.hover = False
        self._update_styling()
        super().leaveEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events for template operations"""
        # Handle both Delete and Backspace (for Mac) for template deletion when selected
        if (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace) and self.selected:
            # If we have a gallery reference and it has multi-selection, handle accordingly
            has_multi = (self.gallery and hasattr(self.gallery, 'multi_selected_templates') and 
                        self.gallery.multi_selected_templates and 
                        len(self.gallery.multi_selected_templates) > 0)
                        
            if has_multi:
                # Use the TemplateCard's multi-selection delete logic to ensure consistent handling
                from app.templates.components.template_card import TemplateCard
                dummy_card = TemplateCard(parent=self.parent(), template=self.template, app=self.gallery.app)
                dummy_card._delete_multi_selected(self.gallery)
                # Prevent further processing of the event
                event.accept()
                return
            else:
                # Just delete this template
                if isinstance(self.template, dict) and 'name' in self.template:
                    template_name = self.template['name']
                    self.deleteRequested.emit(template_name)
                    # Prevent further processing of the event
                    event.accept()
                    return
        
        super().keyPressEvent(event)
        
    def eventFilter(self, obj, event):
        """Filter events for hover state"""
        if obj == self:
            if event.type() == QEvent.Enter:
                self.hover = True
                self._update_styling()
            elif event.type() == QEvent.Leave:
                self.hover = False
                self._update_styling()
        return super().eventFilter(obj, event) 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Custom Item Delegates for UI components

This module provides specialized item delegates for various UI components
to enhance their appearance and behavior beyond what's possible with stylesheets.
"""

from PyQt6.QtWidgets import QStyledItemDelegate, QStyle, QApplication
from PyQt6.QtCore import Qt, QRect, QPoint, QEvent
from PyQt6.QtGui import QPalette, QPainter, QColor

from app.ui.color_scheme_pyqt import colors

class HoverItemDelegate(QStyledItemDelegate):
    """
    A custom item delegate that ensures hover effects work properly 
    in QComboBox dropdowns and similar widgets.
    
    This delegate extends the standard styled delegate to forcibly apply
    hover effects by tracking mouse movements and explicitly drawing the
    hovered item with custom styling.
    """
    
    def __init__(self, parent=None):
        """Initialize the delegate with parent widget"""
        super().__init__(parent)
        self.hovered_index = None
        self.parent_view = parent
        
        # Register for event filtering if parent is provided
        if parent:
            parent.viewport().installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Filter events to track mouse position for hover effects"""
        if event.type() == QEvent.Type.MouseMove:
            # Get the index under the mouse
            pos = event.pos()
            index = self.parent_view.indexAt(pos)
            
            # If the index is different from the currently hovered one
            if index != self.hovered_index:
                # Store the old index to repaint (remove hover effect)
                old_index = self.hovered_index
                # Update the hovered index
                self.hovered_index = index
                
                # Trigger repaint of both old and new indices
                if old_index and old_index.isValid():
                    self.parent_view.update(old_index)
                if index.isValid():
                    self.parent_view.update(index)
        
        # Handle mouse leave events
        elif event.type() == QEvent.Type.Leave:
            # Clear the hovered index and trigger repaint
            if self.hovered_index and self.hovered_index.isValid():
                old_index = self.hovered_index
                self.hovered_index = None
                self.parent_view.update(old_index)
        
        # Allow the event to be processed further
        return super().eventFilter(obj, event)
    
    def paint(self, painter, option, index):
        """
        Paint the item with custom styling for hover, selection, etc.
        
        Args:
            painter: QPainter to use for drawing
            option: Style options for the item
            index: Model index of the item being painted
        """
        # Check if this is a header/divider item (usually has UserRole = False)
        is_header = index.data(Qt.ItemDataRole.UserRole) is False
        
        # Determine if this item is being hovered
        is_hovered = (self.hovered_index is not None and 
                     self.hovered_index.row() == index.row() and 
                     self.hovered_index.column() == index.column())
        
        # Get selection state
        is_selected = option.state & QStyle.StateFlag.State_Selected
        
        # Make a copy of the option to modify
        my_option = option
        
        # Clear the selection state so we can draw our own
        my_option.state &= ~QStyle.StateFlag.State_Selected
        my_option.state &= ~QStyle.StateFlag.State_MouseOver
        
        # Handle different visual states
        if is_header:
            # Headers should not have hover effects, just paint them differently
            painter.save()
            painter.fillRect(option.rect, QColor(colors['card_bg']))
            painter.setPen(QColor(colors['secondary_text']))
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            
            # Draw header text
            text_rect = option.rect.adjusted(5, 0, -5, 0)  # Add some padding
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, 
                           index.data(Qt.ItemDataRole.DisplayRole))
            painter.restore()
            
        elif is_hovered:
            # Draw custom hover style
            painter.save()
            painter.fillRect(option.rect, QColor(colors['accent']))
            painter.setPen(QColor('white'))
            
            # Optional: Add a left border for emphasis
            border_rect = QRect(option.rect.left(), option.rect.top(), 
                               3, option.rect.height())
            painter.fillRect(border_rect, QColor('white'))
            
            # Draw text
            text_rect = option.rect.adjusted(6, 0, -5, 0)  # Add some padding
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, 
                           index.data(Qt.ItemDataRole.DisplayRole))
            painter.restore()
            
        elif is_selected:
            # Draw custom selection style
            painter.save()
            painter.fillRect(option.rect, QColor(colors['highlight_bg']))
            painter.setPen(QColor(colors['highlight_text']))
            
            # Add a left border
            border_rect = QRect(option.rect.left(), option.rect.top(), 
                               3, option.rect.height())
            painter.fillRect(border_rect, QColor(colors['highlight_border']))
            
            # Draw text
            text_rect = option.rect.adjusted(6, 0, -5, 0)  # Add some padding
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, 
                           index.data(Qt.ItemDataRole.DisplayRole))
            painter.restore()
            
        else:
            # Standard rendering for normal items
            super().paint(painter, my_option, index)

def apply_hover_delegate(combo_box):
    """
    Apply the HoverItemDelegate to a combo box to ensure hover effects work.
    
    Args:
        combo_box: The QComboBox widget to enhance
        
    Returns:
        The delegate instance that was applied
    """
    # Get the view used by the combo box
    view = combo_box.view()
    
    # Create and apply the delegate
    delegate = HoverItemDelegate(view)
    view.setItemDelegate(delegate)
    
    # Apply some minimal styling to ensure our delegate's work is visible
    view.setStyleSheet(f"""
        QAbstractItemView {{
            outline: none;
            background-color: {colors['card_bg']};
            selection-background-color: transparent; /* Let our delegate handle this */
        }}
    """)
    
    # Return the delegate in case caller needs to customize it further
    return delegate 
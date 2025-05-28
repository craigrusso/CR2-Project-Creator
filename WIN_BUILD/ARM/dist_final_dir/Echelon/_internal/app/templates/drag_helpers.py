#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Helper functions for drag and drop operations in the Echelon application.
Provides consistent drag-and-drop behavior across different views (grid, list, etc.).
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QSize, QRect, QRectF, QByteArray, QMimeData
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor, QPen, QFont, QPainterPath, QIcon

from app.ui.color_scheme_pyqt import colors

# Define MIME type constants directly in this module to avoid circular imports
TEMPLATE_NAMES_MIME_TYPE = "application/x-echelon-template-names"
TEMPLATE_MULTI_DRAG_MIME_TYPE = "application/x-template-multi-drag"


def create_drag_pixmap(widget, source_pixmap=None, item_count=1, highlight=True):
    """
    Create a drag preview pixmap with a count indicator for multiple items.
    
    Args:
        widget: The source widget for the drag operation
        source_pixmap: Optional existing pixmap to use as the base
        item_count: Number of items being dragged
        highlight: Whether to apply a highlight effect to the pixmap
        
    Returns:
        QPixmap: A pixmap representing the drag operation
    """
    # If no source_pixmap is provided, create one from the widget
    if source_pixmap is None:
        source_pixmap = QPixmap(widget.size())
        widget.render(source_pixmap)
    
    # Create a slightly larger pixmap to accommodate the count badge
    padding = 10
    pixmap_size = source_pixmap.size()
    result_pixmap = QPixmap(pixmap_size.width() + padding, pixmap_size.height() + padding)
    result_pixmap.fill(Qt.transparent)
    
    painter = QPainter(result_pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    
    # Apply a highlight effect if requested
    if highlight:
        # Draw a rounded rectangle behind the pixmap
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, pixmap_size.width(), pixmap_size.height()), 6, 6)
        
        # Use accent color for the background
        painter.fillPath(path, QBrush(QColor(colors.get('accent', '#2C4F76'))))
        
        # Draw a light border
        pen = QPen(QColor(colors.get('highlight_text', '#FFFFFF')))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path)
    
    # Draw the source pixmap
    painter.drawPixmap(0, 0, source_pixmap)
    
    # Only draw a count badge if there's more than one item
    if item_count > 1:
        # Draw a count badge in the top-right corner
        badge_size = 24
        badge_x = pixmap_size.width() - badge_size + 4
        badge_y = -4
        
        # Create a circular background
        badge_rect = QRect(badge_x, badge_y, badge_size, badge_size)
        painter.setBrush(QBrush(QColor(colors.get('error', '#E8574C'))))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(badge_rect)
        
        # Draw the count text
        painter.setPen(QColor(colors.get('highlight_text', '#FFFFFF')))
        font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(badge_rect, Qt.AlignmentFlagFlagFlag.AlignCenter, str(item_count))
    
    painter.end()
    return result_pixmap


def setup_drag_mime_data(templates_to_drag, mime_data, set_multi_drag=True):
    """
    Set up standard MIME data for template drag operations.
    
    Args:
        templates_to_drag: List of template data dictionaries
        mime_data: QMimeData object to populate
        set_multi_drag: Whether to set the multi-drag MIME type when applicable
        
    Returns:
        list: List of template names that were encoded
    """
    # Extract template names
    template_names = []
    for template in templates_to_drag:
        if isinstance(template, dict):
            name = template.get('name', '')
            if name:
                template_names.append(name)
        elif isinstance(template, str):
            template_names.append(template)
    
    # Encode template names (newline separated)
    encoded_data = QByteArray(bytes('\n'.join(template_names), 'utf-8'))
    
    # Set MIME data
    mime_data.setData(TEMPLATE_NAMES_MIME_TYPE, encoded_data)
    
    # Also set text for compatibility with older code
    mime_data.setText('\n'.join(template_names))
    
    # Set multi-drag flag if there are multiple templates and requested
    if set_multi_drag and len(template_names) > 1:
        mime_data.setData(TEMPLATE_MULTI_DRAG_MIME_TYPE, QByteArray(b'1'))
    
    return template_names 
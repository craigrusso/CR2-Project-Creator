#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QFrame
from PyQt5.QtCore import Qt
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, COMBOBOX_STYLE, LINEEDIT_STYLE, LABEL_STYLE

def configure_styles(app):
    """Configure the application styles"""
    # Set application stylesheet
    app.setStyleSheet(f"""
        QMainWindow, QDialog, QWidget {{
            background-color: {colors['bg']};
        }}
        
        QMenuBar {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors['highlight_bg']};
            color: {colors['highlight_text']};
        }}
        
        QMenu {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
        }}
        
        QMenu::item:selected {{
            background-color: {colors['highlight_bg']};
            color: {colors['highlight_text']};
        }}
        
        QStatusBar {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
        }}
        
        QScrollArea, QScrollBar {{
            background-color: {colors['bg']};
            color: {colors['text']};
        }}
        
        QScrollBar:vertical {{
            border: none;
            background: {colors['card_bg']};
            width: 10px;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {colors['border']};
            min-height: 20px;
            border-radius: 5px;
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            border: none;
            background: {colors['card_bg']};
            height: 10px;
            margin: 0px;
        }}
        
        QScrollBar::handle:horizontal {{
            background: {colors['border']};
            min-width: 20px;
            border-radius: 5px;
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """)

def apply_theme_to_widgets(widget_or_app):
    """Apply theme to all widgets in the application"""
    # Determine if we're dealing with an app object or a widget
    if hasattr(widget_or_app, 'setStyleSheet'):
        # It's a QApplication
        app = widget_or_app
        configure_styles(app)
    elif hasattr(widget_or_app, 'centralWidget'):
        # It's a main window
        main_window = widget_or_app
        update_widget_colors(main_window.centralWidget())
    else:
        # It's a widget
        update_widget_colors(widget_or_app)

def update_widget_colors(widget):
    """Recursively update colors for a widget and its children"""
    try:
        # Handle different widget types
        if isinstance(widget, QFrame):
            widget.setStyleSheet(f"background-color: {colors['card_bg']}; color: {colors['text']};")
        
        elif isinstance(widget, QLabel):
            # Check if this is a title label or regular label
            font = widget.font()
            if font.bold():
                widget.setStyleSheet(f"color: {colors['text']}; font-weight: bold;")
            else:
                widget.setStyleSheet(f"color: {colors['text']};")
        
        elif isinstance(widget, QLineEdit):
            widget.setStyleSheet(LINEEDIT_STYLE)
        
        elif isinstance(widget, QPushButton):
            # Check if this is an accent button
            if hasattr(widget, 'objectName') and "accent" in widget.objectName().lower():
                widget.setStyleSheet(ACCENT_BUTTON_STYLE)
            else:
                widget.setStyleSheet(BUTTON_STYLE)
        
        elif isinstance(widget, QComboBox):
            widget.setStyleSheet(COMBOBOX_STYLE)
        
    except Exception as e:
        # Skip widgets we can't configure or that don't have these properties
        print(f"Error updating widget {widget}: {e}")
    
    # Process children of this widget
    try:
        for child in widget.findChildren(QWidget):
            update_widget_colors(child)
    except Exception as e:
        # Some widgets might cause issues
        print(f"Error processing children of {widget}: {e}")

def apply_dark_theme_to_template_gallery(widget):
    """Apply dark theme styling to template gallery components"""
    if not widget:
        return
    
    # Apply dark theme to template cards and gallery components
    widget.setStyleSheet(f"""
        QWidget {{
            background-color: {colors['bg']};
            color: {colors['text']};
        }}
        
        QFrame {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border-radius: 5px;
            border: 1px solid {colors['border']};
        }}
        
        QLabel {{
            color: {colors['text']};
        }}
        
        QPushButton {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 5px 10px;
        }}
        
        QPushButton:hover {{
            background-color: {colors['hover_bg']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['accent']};
        }}
        
        QPushButton:checked {{
            background-color: {colors['highlight_bg']};
            color: white;
        }}
        
        QLineEdit {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 5px;
        }}
        
        QScrollArea {{
            border: none;
            background-color: {colors['bg']};
        }}
        
        QScrollArea > QWidget > QWidget {{
            background-color: {colors['bg']};
        }}
        
        QTreeWidget {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
        }}
        
        QTreeWidget::item:selected {{
            background-color: {colors['highlight_bg']};
            color: white;
        }}
    """)
    
    # Explicitly set background color for the gallery widget and scroll area if they exist
    if hasattr(widget, 'gallery_widget'):
        widget.gallery_widget.setStyleSheet(f"background-color: {colors['bg']};")
    
    if hasattr(widget, 'gallery_scroll'):
        widget.gallery_scroll.setStyleSheet(f"background-color: {colors['bg']};")

def apply_dark_theme_to_template_section(app):
    """Apply dark grey theme to template file section"""
    # Find the template file frame in PyQt version
    template_frame = None
    
    if hasattr(app, 'template_file_frame'):
        template_frame = app.template_file_frame
    elif hasattr(app, 'template_section'):
        template_frame = app.template_section
    
    if template_frame:
        # Apply darker background to the template section
        template_frame.setStyleSheet(f"""
            background-color: #282828;
            color: {colors['text']};
        """)
        
        # Update all child widgets
        for child in template_frame.findChildren(QWidget):
            if isinstance(child, QLabel) or isinstance(child, QFrame):
                child.setStyleSheet(f"background-color: #282828; color: {colors['text']};")
    
    # Update other template container elements if they exist
    for widget_name in ['template_file_container', 'recent_templates_frame']:
        if hasattr(app, widget_name):
            widget = getattr(app, widget_name)
            widget.setStyleSheet(f"background-color: #282828; color: {colors['text']};")
            
            # Also update all child widgets
            for child in widget.findChildren(QWidget):
                if isinstance(child, QLabel) or isinstance(child, QFrame):
                    child.setStyleSheet(f"background-color: #282828; color: {colors['text']};") 
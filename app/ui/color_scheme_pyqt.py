#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Color Scheme File for CR2 Project Creator (PyQt version)
This file provides a centralized place for all color definitions
to ensure consistency across the application.
"""

from PyQt5.QtGui import QColor

# Main application colors
APP_COLORS = {
    # Main background colors
    "bg": "#1E1E1E",              # Main application background
    "card_bg": "#252526",         # Card background (darker than bg)
    "card_bg_alt": "#2A2A2A",     # Alternative card background (for alternating rows)
    
    # Text colors
    "text": "#CCCCCC",            # Primary text color
    "secondary_text": "#858585",  # Secondary/dimmed text
    
    # Accent colors
    "accent": "#2C4F76",          # Dark blue accent color - more subtle and elegant
    "accent_hover": "#36648B",    # Darker blue for hover states
    
    # Status/notification colors
    "success": "#4CAF50",         # Success (green)
    "success_text": "#003300",    # Text on success backgrounds
    "warning": "#F1AE3C",         # Warning (yellow/amber)
    "error": "#E8574C",           # Error (red)
    "error_text": "#FF5555",      # Bright red for destructive actions
    "error_hover": "#FFAAAA",     # Light red for destructive action hover
    
    # Selection/highlight colors
    "highlight_border": "#4682B4", # Steel Blue for highlight borders
    "highlight_bg": "#2C4F76",    # Dark blue for highlight backgrounds - consistent with accent
    "highlight_bg_transparent": "#2C4F7633",  # Transparent highlight background (33=20% opacity)
    "highlight_darker": "#36648B", # Darker blue for hover on highlighted items
    "highlight_text": "#FFFFFF",  # White text for highlighted items
    
    # Hover effect colors
    "hover_bg": "#454545",        # Much darker grey hover effect for better visibility
    "hover_bg_transparent": "#45454533",  # Transparent hover background (33=20% opacity)
    
    # Border colors
    "border": "#3C3C3C",          # Border for cards and sections
    
    # File browser colors
    "folder_icon": "#E8BA36",     # Golden yellow for folder icons
}

# Function to get a specific color by name
def get_color(name):
    """Get a color by name from the color scheme"""
    return APP_COLORS.get(name, APP_COLORS["text"])  # Default to text color if not found

# For backward compatibility with existing 'colors' dictionary
colors = APP_COLORS

# Function to get QColor from hex color
def qcolor(color_hex):
    """Convert a hex color string to QColor object"""
    color = color_hex.lstrip('#')
    return QColor(int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))

# Style sheets for common components
BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        padding: 5px 10px;
        border-radius: 3px;
    }}
    QPushButton:hover {{
        background-color: {colors['hover_bg']};
        border: 1px solid {colors['accent']};
    }}
    QPushButton:pressed {{
        background-color: {colors['accent']};
        color: {colors['highlight_text']};
    }}
"""

ACCENT_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {colors['accent']};
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 3px;
    }}
    QPushButton:hover {{
        background-color: {colors['accent_hover']};
    }}
    QPushButton:pressed {{
        background-color: {colors['highlight_darker']};
    }}
"""

COMBOBOX_STYLE = f"""
    QComboBox {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        padding: 5px 25px 5px 5px;  /* Right padding for arrow */
        border-radius: 3px;
        min-height: 22px;
    }}
    
    /* Main combobox hover */
    QComboBox:hover {{
        border: 1px solid {colors['accent']};
        background-color: {colors['hover_bg']};
        color: {colors['highlight_text']};
    }}
    
    QComboBox:focus {{
        border: 1px solid {colors['accent']};
        background-color: {colors['highlight_bg_transparent']};
    }}
    
    /* Drop-down button styling */
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left-width: 1px;
        border-left-color: {colors['border']};
        border-left-style: solid;
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
    }}
    
    QComboBox::drop-down:hover {{
        background-color: {colors['accent']};
        border-left-color: {colors['accent']};
    }}
    
    /* Arrow styling */
    QComboBox::down-arrow {{
        image: url(app/assets/css/dropdown_arrow.svg);
        width: 16px;
        height: 16px;
        border: none;
        background-color: transparent;
    }}
    
    QComboBox::down-arrow:on {{
        image: url(app/assets/css/dropdown_arrow_up.svg);
    }}
    
    /* Popup widget styling */
    QComboBox QAbstractItemView {{
        border: 1px solid {colors['accent']};
        background-color: {colors['card_bg']};
        color: {colors['text']};
        outline: none; /* Remove focus outline */
    }}
    
    /* Default item styling in popup */
    QComboBox QAbstractItemView::item {{
        border-left: 3px solid transparent;
        padding: 6px;
        min-height: 24px;
    }}
    
    /* Very direct styling for hover state */
    QComboBox QAbstractItemView::item:hover {{
        background-color: {colors['accent']};
        color: white;  /* White text on hover for maximum contrast */
        font-weight: bold;  /* Bold text on hover */
        border-left: 5px solid white;  /* White left border for emphasis */
    }}
    
    /* Selected item (when dropdown is closed) */
    QComboBox QAbstractItemView::item:selected {{
        background-color: {colors['highlight_bg']};
        color: {colors['highlight_text']};
        border-left: 3px solid {colors['accent']};
    }}
"""

# Create a specialized style just for QListView in popups - this will be applied directly
LISTVIEW_POPUP_STYLE = f"""
    QListView {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        border: 1px solid {colors['accent']};
        outline: none;
        border-radius: 3px;
        padding: 1px;
        selection-background-color: transparent;
    }}
    
    QListView::item {{
        border-left: 3px solid transparent;
        padding: 6px;
        min-height: 24px;
        margin: 2px;
        border-radius: 2px;
    }}
    
    QListView::item:hover {{
        background-color: {colors['accent']};
        color: white;
        font-weight: bold;
        border-left: 5px solid white;
        border-bottom: 1px solid white;
        border-top: 1px solid white;
    }}
    
    QListView::item:selected {{
        background-color: {colors['highlight_bg']};
        color: {colors['highlight_text']};
        border-left: 3px solid {colors['accent']};
    }}

    /* Force immediate hover response */
    QListView::item:hover:!selected {{
        background-color: {colors['accent']};
        color: white;
        font-weight: bold;
        border-left: 5px solid white;
    }}
"""

# Context menu styling with hover effects
CONTEXT_MENU_STYLE = f"""
    QMenu {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        border-radius: 3px;
        padding: 2px;
    }}
    
    QMenu::item {{
        padding: 5px 25px 5px 20px;
        border: 1px solid transparent;
        border-radius: 2px;
        min-width: 150px;
    }}
    
    QMenu::item:selected {{
        background-color: {colors['hover_bg']};
        color: {colors['highlight_text']};
        border: 1px solid {colors['accent']};
    }}
    
    QMenu::item:disabled {{
        color: {colors['secondary_text']};
    }}
    
    /* Special styling for destructive actions */
    QMenu::item[destructive="true"] {{
        color: {colors['error_text']};
    }}
    
    QMenu::item[destructive="true"]:selected {{
        background-color: {colors['error_hover']};
        color: {colors['error']};
        border: 1px solid {colors['error']};
    }}
"""

LINEEDIT_STYLE = f"""
    QLineEdit {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        padding: 5px;
        border-radius: 3px;
    }}
    QLineEdit:hover, QLineEdit:focus {{
        border: 1px solid {colors['accent']};
    }}
"""

LABEL_STYLE = f"""
    QLabel {{
        color: {colors['text']};
    }}
"""

SECONDARY_LABEL_STYLE = f"""
    QLabel {{
        color: {colors['secondary_text']};
    }}
"""

# Destructive action style (for delete buttons, menu items, etc.)
DESTRUCTIVE_ACTION_STYLE = f"""
    color: {colors['error_text']};
"""

# Special style for delete menu items in context menus
MENU_DESTRUCTIVE_ITEM_STYLE = f"""
    QMenu {{
        background-color: #252526;
        color: #CCCCCC;
        border: 1px solid #3C3C3C;
        padding: 5px;
        border-radius: 4px;
    }}
    QMenu::item {{
        padding: 5px 20px 5px 20px;
        border-radius: 3px;
    }}
    QMenu::item:selected {{
        background-color: #2C4F76;
        color: white;
    }}
    
    /* Style the destructive action - improved specificity for better macOS support */
    QMenu QAction[destructive="true"] {{
        color: {colors['error_text']};
        font-weight: bold;
    }}
    
    /* Use a more specific selector for Qt on macOS */
    QMenu::item[destructive="true"]:!selected {{
        color: {colors['error_text']};
        font-weight: bold;
    }}
    
    /* Use red background for destructive actions when hovered */
    QMenu::item[destructive="true"]:selected {{
        color: white;
        background-color: #AA3333;
        font-weight: bold;
    }}
    
    QMenu::separator {{
        height: 1px;
        background: #3C3C3C;
        margin: 5px 0px 5px 0px;
    }}
"""

# Add a specific style for the Delete text that can be applied directly
DELETE_TEXT_STYLE = f"""
    color: {colors['error_text']};
    font-weight: bold;
"""

# Export specific color combinations for different UI elements
CARD_NORMAL = {
    "bg": APP_COLORS["card_bg"],
    "border": APP_COLORS["card_bg"],
    "text": APP_COLORS["text"],
    "secondary_text": APP_COLORS["secondary_text"]
}

CARD_HOVER = {
    "bg": APP_COLORS["hover_bg"],
    "border": APP_COLORS["hover_bg"],
    "text": APP_COLORS["text"],
    "secondary_text": APP_COLORS["secondary_text"]
}

CARD_SELECTED = {
    "bg": APP_COLORS["highlight_bg"],
    "border": APP_COLORS["highlight_border"],
    "text": APP_COLORS["highlight_text"],
    "secondary_text": APP_COLORS["highlight_text"]
} 
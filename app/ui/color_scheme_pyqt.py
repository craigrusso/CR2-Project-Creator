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
    
    # Text colors
    "text": "#CCCCCC",            # Primary text color
    "secondary_text": "#858585",  # Secondary/dimmed text
    
    # Accent colors
    "accent": "#007ACC",          # Blue accent color
    "accent_hover": "#0066B3",    # Darker blue for hover states
    
    # Status/notification colors
    "success": "#4CAF50",         # Success (green)
    "success_text": "#003300",    # Text on success backgrounds
    "warning": "#F1AE3C",         # Warning (yellow/amber)
    "error": "#E8574C",           # Error (red)
    
    # Selection/highlight colors
    "highlight_border": "#4682B4", # Steel Blue for highlight borders
    "highlight_bg": "#2C4F76",    # Darker blue for highlight backgrounds
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
        padding: 5px;
        border-radius: 3px;
    }}
    QComboBox:hover {{
        border: 1px solid {colors['accent']};
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        selection-background-color: {colors['highlight_bg']};
        selection-color: {colors['highlight_text']};
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
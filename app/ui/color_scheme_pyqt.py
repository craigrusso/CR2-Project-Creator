#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Color Scheme File for CR2 Project Creator (PyQt version)
This file provides a centralized place for all color definitions
to ensure consistency across the application.
"""

from PyQt6.QtGui import QColor
import sys
import os
from app.constants import get_resource_path

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
    "macos_folder_icon": "#3897F0",  # Exact match for macOS folder icon blue
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

# Style for dialog message box buttons
MESSAGE_BOX_BUTTON_STYLE = f"""
    /* Base style for all QMessageBox buttons */
    QMessageBox QPushButton {{
        min-width: 80px;
        min-height: 22px;
        border-radius: 3px;
        padding: 5px 10px;
    }}
    
    /* Style for "Yes" and "OK" buttons - blue accent color */
    QMessageBox QPushButton[text="Yes"], 
    QMessageBox QPushButton[text="OK"],
    QMessageBox QPushButton[text="&Yes"] {{
        background-color: {colors['accent']};
        color: white;
        border: none;
    }}
    
    QMessageBox QPushButton[text="Yes"]:hover, 
    QMessageBox QPushButton[text="OK"]:hover,
    QMessageBox QPushButton[text="&Yes"]:hover {{
        background-color: {colors['accent_hover']};
    }}
    
    QMessageBox QPushButton[text="Yes"]:pressed, 
    QMessageBox QPushButton[text="OK"]:pressed,
    QMessageBox QPushButton[text="&Yes"]:pressed {{
        background-color: {colors['highlight_darker']};
    }}
    
    /* Style for "No" and cancel buttons - gray color */
    QMessageBox QPushButton[text="No"],
    QMessageBox QPushButton[text="Cancel"],
    QMessageBox QPushButton[text="&No"] {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
    }}
    
    QMessageBox QPushButton[text="No"]:hover,
    QMessageBox QPushButton[text="Cancel"]:hover,
    QMessageBox QPushButton[text="&No"]:hover {{
        background-color: {colors['hover_bg']};
        border: 1px solid {colors['accent']};
    }}
    
    QMessageBox QPushButton[text="No"]:pressed,
    QMessageBox QPushButton[text="Cancel"]:pressed,
    QMessageBox QPushButton[text="&No"]:pressed {{
        background-color: {colors['hover_bg']};
        color: {colors['highlight_text']};
    }}
"""

# Style for dialog buttons in QInputDialog and other standard dialogs
DIALOG_BUTTON_STYLE = f"""
    /* Base style for all dialog buttons */
    QDialog QPushButton {{
        min-width: 80px;
        min-height: 22px;
        border-radius: 3px;
        padding: 5px 10px;
    }}
    
    /* Style for "OK" button - blue accent color */
    QDialog QPushButton[text="OK"],
    QDialog QPushButton[text="&OK"] {{
        background-color: {colors['accent']};
        color: white;
        border: none;
    }}
    
    QDialog QPushButton[text="OK"]:hover,
    QDialog QPushButton[text="&OK"]:hover {{
        background-color: {colors['accent_hover']};
    }}
    
    QDialog QPushButton[text="OK"]:pressed,
    QDialog QPushButton[text="&OK"]:pressed {{
        background-color: {colors['highlight_darker']};
    }}
    
    /* Style for "Cancel" button - gray color */
    QDialog QPushButton[text="Cancel"],
    QDialog QPushButton[text="&Cancel"] {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
    }}
    
    QDialog QPushButton[text="Cancel"]:hover,
    QDialog QPushButton[text="&Cancel"]:hover {{
        background-color: {colors['hover_bg']};
        border: 1px solid {colors['accent']};
    }}
    
    QDialog QPushButton[text="Cancel"]:pressed,
    QDialog QPushButton[text="&Cancel"]:pressed {{
        background-color: {colors['hover_bg']};
        color: {colors['highlight_text']};
    }}
"""

# Get SVG icon paths using resource helper
import platform
import os

# Use platform-specific dropdown arrow SVGs
system = platform.system()
if system == "Windows":
    # For Windows, use white arrows for better contrast on dark backgrounds
    dropdown_arrow_path = get_resource_path('app/assets/css/dropdown_arrow_windows.svg')
    dropdown_arrow_up_path = get_resource_path('app/assets/css/dropdown_arrow_up_windows.svg')
    
    # Windows-specific vertical arrows for spinboxes
    v_arrow_path = get_resource_path('app/assets/css/v_arrow_windows.svg')
    v_arrow_up_path = get_resource_path('app/assets/css/v_arrow_up_windows.svg')
    
    # If the Windows-specific arrows don't exist, fall back to regular ones
    if not os.path.exists(dropdown_arrow_path):
        print(f"[WARNING] Windows dropdown arrow not found at {dropdown_arrow_path}")
        dropdown_arrow_path = get_resource_path('app/assets/css/dropdown_arrow.svg')
        dropdown_arrow_up_path = get_resource_path('app/assets/css/dropdown_arrow_up.svg')
    
    # Fall back to regular vertical arrows if Windows-specific ones don't exist
    if not os.path.exists(v_arrow_path):
        print(f"[WARNING] Windows vertical arrow not found at {v_arrow_path}")
        v_arrow_path = get_resource_path('app/assets/css/v_arrow.svg') 
        v_arrow_up_path = get_resource_path('app/assets/css/v_arrow_up.svg')
else:
    # Default arrows for macOS/Linux
    dropdown_arrow_path = get_resource_path('app/assets/css/dropdown_arrow.svg')
    dropdown_arrow_up_path = get_resource_path('app/assets/css/dropdown_arrow_up.svg')
    v_arrow_path = get_resource_path('app/assets/css/v_arrow.svg')
    v_arrow_up_path = get_resource_path('app/assets/css/v_arrow_up.svg')

# For Qt stylesheets, always use forward slashes regardless of platform
dropdown_arrow_path = dropdown_arrow_path.replace('\\', '/')
dropdown_arrow_up_path = dropdown_arrow_up_path.replace('\\', '/')
v_arrow_path = v_arrow_path.replace('\\', '/')
v_arrow_up_path = v_arrow_up_path.replace('\\', '/')

# Debug output to help diagnose path issues
print(f"[DEBUG] {system} dropdown arrow path: {dropdown_arrow_path}")
print(f"[DEBUG] {system} dropdown arrow up path: {dropdown_arrow_up_path}")
print(f"[DEBUG] {system} vertical arrow path: {v_arrow_path}")
print(f"[DEBUG] {system} vertical arrow up path: {v_arrow_up_path}")
print(f"[DEBUG] Path exists (arrow): {os.path.exists(dropdown_arrow_path)}")
print(f"[DEBUG] Path exists (arrow up): {os.path.exists(dropdown_arrow_up_path)}")
print(f"[DEBUG] Path exists (v arrow): {os.path.exists(v_arrow_path)}")
print(f"[DEBUG] Path exists (v arrow up): {os.path.exists(v_arrow_up_path)}")

# Style for combobox
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
        border: 1px solid {colors['highlight_border']}; /* Use highlight_border for consistency */
        background-color: {colors['hover_bg']};
    }}
    
    QComboBox:focus {{
        border: 1px solid {colors['highlight_border']};
        background-color: {colors['highlight_bg_transparent']};
    }}
    
    /* Drop-down button styling */
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border: none;
        border-left: 1px solid {colors['border']};
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
    }}
    
    QComboBox::drop-down:hover {{
        background-color: {colors['accent']};
    }}
    
    /* Arrow styling with explicit paths */
    QComboBox::down-arrow {{
        image: url("{dropdown_arrow_path}");
        width: 16px;
        height: 16px;
    }}
    
    QComboBox::down-arrow:on {{
        image: url("{dropdown_arrow_up_path}");
    }}
    
    /* Popup widget styling */
    QComboBox QAbstractItemView {{
        border: 1px solid {colors['highlight_border']};
        background-color: {colors['card_bg']};
        color: {colors['text']};
        outline: none; /* Remove focus outline */
        selection-background-color: {colors['highlight_bg']}; /* Set selection background */
        selection-color: {colors['highlight_text']}
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

# Style for spinbox - matches combobox design with up/down arrows
SPINBOX_STYLE = f"""
    QSpinBox {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        padding: 5px 25px 5px 5px;  /* Right padding for buttons */
        border-radius: 3px;
        min-height: 22px;
    }}
    
    /* Main spinbox hover */
    QSpinBox:hover {{
        border: 1px solid {colors['highlight_border']};
        background-color: {colors['hover_bg']};
    }}
    
    QSpinBox:focus {{
        border: 1px solid {colors['highlight_border']};
        background-color: {colors['highlight_bg_transparent']};
    }}
    
    /* Up button styling */
    QSpinBox::up-button {{
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid {colors['border']};
        border-right: none;
        border-top: none;
        border-bottom: none;
        border-top-right-radius: 3px;
        background-color: {colors['card_bg']};
    }}
    
    QSpinBox::up-button:hover {{
        background-color: {colors['accent']};
        border-left: 1px solid {colors['border']};
    }}
    
    QSpinBox::up-button:pressed {{
        background-color: {colors['accent_hover']};
        border-left: 1px solid {colors['border']};
    }}
    
    /* Down button styling */
    QSpinBox::down-button {{
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 20px;
        border-left: 1px solid {colors['border']};
        border-right: none;
        border-bottom: none;
        border-top: none;
        border-bottom-right-radius: 3px;
        background-color: {colors['card_bg']};
    }}
    
    QSpinBox::down-button:hover {{
        background-color: {colors['accent']};
        border-left: 1px solid {colors['border']};
    }}
    
    QSpinBox::down-button:pressed {{
        background-color: {colors['accent_hover']};
        border-left: 1px solid {colors['border']};
    }}
    
    /* Arrow styling */
    QSpinBox::up-arrow {{
        image: url("{v_arrow_up_path}");
        width: 12px;
        height: 12px;
        margin-top: 1px;
        margin-bottom: 0px;
    }}
    
    QSpinBox::up-arrow:hover {{
        image: url("{v_arrow_up_path}");
    }}
    
    QSpinBox::down-arrow {{
        image: url("{v_arrow_path}");
        width: 12px;
        height: 12px;
        margin-top: 0px;
        margin-bottom: 1px;
        margin-left: 3px;
    }}
    
    QSpinBox::down-arrow:hover {{
        image: url("{v_arrow_path}");
    }}
    
    /* Disabled state */
    QSpinBox:disabled {{
        background-color: {colors['bg']};
        color: {colors['secondary_text']};
        border: 1px solid {colors['secondary_text']};
    }}
    
    QSpinBox::up-button:disabled, QSpinBox::down-button:disabled {{
        background-color: {colors['bg']};
        border-left: 1px solid {colors['secondary_text']};
    }}
"""

# Create a specialized style just for QListView in popups - this will be applied directly
LISTVIEW_POPUP_STYLE = f"""
    QListView {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        border: 1px solid {colors['highlight_border']};
        outline: none;
        border-radius: 3px;
        padding: 2px;
        selection-background-color: {colors['highlight_bg']};
        selection-color: {colors['highlight_text']};
    }}
    
    QListView::item {{
        border-left: 3px solid transparent;
        padding: 2px;
        min-height: 20px;
        margin: 0px;
        border-radius: 2px;
    }}
    
    QListView::item:hover {{
        background-color: {colors['accent']};
        color: white;
        border-left: 3px solid white;
    }}
    
    QListView::item:selected {{
        background-color: {colors['highlight_bg']};
        color: {colors['highlight_text']};
        border-left: 3px solid {colors['highlight_border']};
    }}

    /* Force immediate hover response even when selected */
    QListView::item:hover:selected {{
        background-color: {colors['accent_hover']};
        color: white;
        border-left: 3px solid white;
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
        background-color: {colors['highlight_bg']};
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
    QLineEdit:hover {{
        border: 1px solid {colors['accent']};
    }}
    QLineEdit:focus {{
        border: 2px solid {colors['highlight_border']};
        padding: 4px;
        background-color: {QColor(colors['card_bg']).lighter(110).name()};
    }}
    QLineEdit[readOnly="true"] {{
        background-color: {QColor(colors['card_bg']).darker(110).name()};
        color: {colors['secondary_text']};
        border: 1px solid {colors['border']};
    }}
"""

LABEL_STYLE = f"""
    QLabel {{
        color: {colors['text']};
        background-color: transparent; /* Ensure no background color is set */
        padding: 2px; /* Add small padding for better spacing */
    }}

    /* Specific styling for labels used as section headers */
    QLabel[class="section-header"] {{
        color: {colors['text']}; /* Use text color for section headers */
        font-size: 10pt; /* Slightly larger font */
        font-weight: bold;
        padding-top: 8px;
        padding-bottom: 4px;
        border-bottom: 1px solid {colors['border']}; /* Optional: add a separator line */
        margin-bottom: 5px; /* Space below the header */
    }}

    /* Styling for labels in status bars */
    QStatusBar QLabel {{
        color: {colors['secondary_text']}; /* Use secondary text color for status bar */
        font-size: 8pt; /* Smaller font for status bar */
        padding: 0px; /* No padding for status bar labels */
        margin: 0px; /* No margin */
    }}
"""

SECONDARY_LABEL_STYLE = f"""
    QLabel {{
        color: {colors['secondary_text']};
    }}
"""

# Add GroupBox style
GROUPBOX_STYLE = f"""
    QGroupBox {{
        border: 1px solid {colors['border']};
        margin-top: 10px; /* Space for the title */
        padding: 10px;
        border-radius: 3px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px 0 5px;
        left: 10px; /* Indent title slightly */
        color: {colors['text']}; /* Set title color */
        background-color: {colors['bg']}; /* Match main background */
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

ACTION_LINK_STYLE = f"""
    QPushButton {{
        background-color: transparent;
        color: {colors['accent']};
        border: none;
        padding: 5px;
        text-align: left; /* Align text to the left like a link */
    }}
    QPushButton:hover {{
        color: {colors['accent_hover']};
        text-decoration: underline;
    }}
    QPushButton:pressed {{
        color: {colors['highlight_darker']};
    }}
"""

# Create a reusable calendar styling function for app-wide consistency
# TEMPORARILY DISABLED DUE TO STARTUP ISSUES
# def apply_standard_calendar_styling(calendar_widget):
#     """
#     Apply standardized calendar styling to any QCalendarWidget.
#     This ensures consistent appearance across the entire application.
#     
#     Args:
#         calendar_widget: The QCalendarWidget to style
#     """
#     if not calendar_widget:
#         return
#     
#     try:
#         from PyQt6.QtGui import QTextCharFormat, QColor
#         from PyQt6.QtCore import Qt
#         
#         # Set weekend text format to be dimmer grey (not red)
#         weekend_format = QTextCharFormat()
#         weekend_format.setForeground(QColor('#888888'))  # Dimmer grey for weekends
#         calendar_widget.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend_format)
#         calendar_widget.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend_format)
#         
#         # Set weekday text format to standard app text color
#         weekday_format = QTextCharFormat()
#         weekday_format.setForeground(QColor(colors['text']))
#         for day in [Qt.DayOfWeek.Monday, Qt.DayOfWeek.Tuesday, Qt.DayOfWeek.Wednesday, 
#                    Qt.DayOfWeek.Thursday, Qt.DayOfWeek.Friday]:
#             calendar_widget.setWeekdayTextFormat(day, weekday_format)
#         
#         # Apply consistent stylesheet
#         calendar_widget.setStyleSheet(f"""
#             QCalendarWidget {{
#                 background-color: {colors['card_bg']};
#                 color: {colors['text']};
#                 border: 1px solid {colors['border']};
#                 font-size: 12px;
#                 min-width: 280px;
#                 min-height: 200px;
#             }}
#             QCalendarWidget QWidget {{
#                 background-color: {colors['card_bg']};
#                 color: {colors['text']};
#             }}
#             QCalendarWidget QAbstractItemView {{
#                 background-color: {colors['card_bg']};
#                 selection-background-color: {colors['accent']};
#                 gridline-color: {colors['border']};
#             }}
#             QCalendarWidget QAbstractItemView:enabled {{
#                 color: {colors['text']};
#                 background-color: {colors['card_bg']};
#                 selection-background-color: {colors['accent']};
#                 selection-color: white;
#             }}
#             QCalendarWidget QMenu {{
#                 background-color: {colors['card_bg']};
#                 color: {colors['text']};
#                 border: 1px solid {colors['border']};
#             }}
#             QCalendarWidget QSpinBox {{
#                 background-color: {colors['card_bg']};
#                 color: {colors['text']};
#                 border: 1px solid {colors['border']};
#                 selection-background-color: {colors['accent']};
#                 selection-color: white;
#             }}
#             QCalendarWidget QToolButton {{
#                 background-color: {colors['card_bg']};
#                 color: {colors['text']};
#                 border: 1px solid {colors['border']};
#                 border-radius: 3px;
#                 padding: 2px;
#             }}
#             QCalendarWidget QToolButton:hover {{
#                 background-color: {colors['hover_bg']};
#                 border: 1px solid {colors['accent']};
#             }}
#             QCalendarWidget QToolButton:pressed {{
#                 background-color: {colors['accent']};
#                 color: white;
#             }}
#         """)
#         
#     except Exception as e:
#         print(f"Error applying calendar styling: {e}")

# TEMPORARILY DISABLED DUE TO STARTUP ISSUES  
# def ensure_combobox_consistency(combobox):
#     """
#     Ensure a QComboBox has consistent styling and hover effects.
#     This applies the app-wide COMBOBOX_STYLE and hover delegate.
#     
#     Args:
#         combobox: The QComboBox to style consistently
#     """
#     if not combobox:
#         return
#     
#     try:
#         # Apply the standard combobox style
#         combobox.setStyleSheet(COMBOBOX_STYLE)
#         
#         # Apply hover delegate for proper hover effects
#         from app.ui.custom_delegates import apply_hover_delegate
#         apply_hover_delegate(combobox)
#         
#     except Exception as e:
#         print(f"Error applying combobox consistency: {e}") 
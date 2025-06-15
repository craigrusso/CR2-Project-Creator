#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Styles for dialog components used throughout the application.
"""

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, GROUPBOX_STYLE, SPINBOX_STYLE
from app.constants import get_resource_path

# Label styles
LABEL_STYLE = f"""
    QLabel {{
        color: {colors['text']};
        background-color: transparent; /* Ensure labels have transparent background */
    }}
"""

SECONDARY_LABEL_STYLE = f"""
    QLabel {{
        color: {colors['secondary_text']};
        background-color: transparent;
    }}
"""

# Input field styles
LINEEDIT_STYLE = f"""
    QLineEdit {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        padding: 5px;
        border-radius: 3px;
    }}
    QLineEdit:focus {{
        border: 1px solid {colors['accent']};
        background-color: {colors['hover_bg']};
    }}
    QLineEdit:read-only {{
        background-color: {colors['bg']}; /* Slightly different bg for read-only */
        color: {colors['secondary_text']};
    }}
"""

# Checkbox style
CHECKBOX_STYLE = f"""
    QCheckBox {{
        color: {colors['text']};
        spacing: 5px; /* Space between indicator and text */
    }}
    
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {colors['border']};
        border-radius: 3px;
        background-color: {colors['card_bg']};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {colors['accent']};
        border: 1px solid {colors['accent']};
        image: none;
        background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path fill="white" d="M6.5,12.5 L3,9 L4.5,7.5 L6.5,9.5 L11.5,4.5 L13,6 L6.5,12.5 Z"/></svg>');
    }}
    
    QCheckBox::indicator:hover {{
        border: 1px solid {colors['accent']};
    }}
"""

# Spinbox style is now imported from color_scheme_pyqt for consistency

# Tab widget style
TABWIDGET_STYLE = f"""
    QTabWidget::pane {{ /* The tab widget frame */
        border: 1px solid {colors['border']};
        border-radius: 5px;
        background-color: {colors['bg']};
        margin-top: -1px; /* Align pane top with tab bottom */
    }}

    QTabBar::tab {{
        background: {colors['card_bg']};
        color: {colors['secondary_text']};
        border: 1px solid {colors['border']};
        border-bottom: none; /* Hide bottom border for non-selected */
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        padding: 8px 15px;
        margin-right: 2px; /* Space between tabs */
    }}

    QTabBar::tab:hover {{
        background: {colors['hover_bg']};
        color: {colors['text']};
    }}

    QTabBar::tab:selected {{
        background: {colors['bg']}; /* Match pane background */
        color: {colors['text']};
        border-color: {colors['border']};
        border-bottom-color: {colors['bg']}; /* Make bottom border match background */
        font-weight: bold;
    }}

    /* Style the content widgets within tabs */
    QTabWidget QWidget {{
        background-color: {colors['bg']};
        color: {colors['text']};
    }}
"""

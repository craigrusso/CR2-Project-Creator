#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Styles for dialog components used throughout the application.
"""

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, GROUPBOX_STYLE

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
    }}
    
    QCheckBox::indicator:checked::after {{
        content: "X";
        color: white;
        position: absolute;
        left: 4px;
        top: -1px;
        font-size: 14px;
    }}
    
    QCheckBox::indicator:hover {{
        border: 1px solid {colors['accent']};
    }}
"""

# Spinbox style
SPINBOX_STYLE = f"""
    QSpinBox {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        padding: 5px;
        border-radius: 3px;
    }}
    QSpinBox:focus {{
        border: 1px solid {colors['accent']};
        background-color: {colors['hover_bg']};
    }}
    /* Style the up/down buttons */
    QSpinBox::up-button, QSpinBox::down-button {{
        subcontrol-origin: border;
        background-color: {colors['card_bg']};
        border: none;
        width: 16px;
    }}
    QSpinBox::up-button {{
        subcontrol-position: top right; /* position at the top right corner */
        border-bottom: 1px solid {colors['border']}; /* Separator line */
    }}
    QSpinBox::down-button {{
        subcontrol-position: bottom right; /* position at bottom right corner */
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: {colors['hover_bg']};
    }}
    QSpinBox::up-arrow {{
        image: url(app/assets/css/v_arrow_up.svg);
        width: 10px;
        height: 10px;
    }}
    QSpinBox::down-arrow {{
        image: url(app/assets/css/v_arrow.svg);
        width: 10px;
        height: 10px;
    }}
"""

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

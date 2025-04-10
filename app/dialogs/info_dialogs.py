#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Dialog windows for displaying information and tutorials.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTabWidget, QWidget)
from PyQt5.QtCore import Qt

# Import from the same place as APP_NAME and APP_VERSION for consistency
from app.config.app_config import APP_NAME, APP_VERSION
# Define a fallback build number in case import fails
APP_BUILD_NUMBER = "250"
try:
    # Try to import from constants if available
    from app.constants import APP_BUILD_NUMBER
except ImportError:
    try:
        # Try alternative location if first import fails
        from app.config.constants import APP_BUILD_NUMBER
    except ImportError:
        # Keep the fallback value if both imports fail
        pass

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE

def show_about(app):
    """Show the about dialog"""
    dialog = QDialog(app)
    dialog.setWindowTitle("About")
    dialog.resize(450, 320)
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(10)
    
    # App name and version with build number
    title_label = QLabel(f"{APP_NAME}")
    font = title_label.font()
    font.setBold(True)
    font.setPointSize(16)
    title_label.setFont(font)
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(title_label)
    
    # Version with build in parentheses
    version_label = QLabel(f"{APP_VERSION} <span style='color: {colors['secondary_text']}; font-size: 10px;'>(build {APP_BUILD_NUMBER})</span>")
    version_label.setAlignment(Qt.AlignCenter)
    version_label.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(version_label)
    
    # Copyright info
    copyright_label = QLabel("© 2023-present Craig P. Russo and CR2 Creative")
    copyright_label.setAlignment(Qt.AlignCenter)
    copyright_label.setStyleSheet(f"color: {colors['secondary_text']};")
    layout.addWidget(copyright_label)
    
    # Description
    description = QLabel(
        "Echelon is a professional project creation tool designed to "
        "streamline your workflow by creating consistent project structures and files "
        "from customizable templates."
    )
    description.setWordWrap(True)
    description.setAlignment(Qt.AlignCenter)
    description.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(description)
    
    # Spacer
    layout.addStretch()
    
    # Close button
    close_button = QPushButton("Close")
    close_button.setStyleSheet(BUTTON_STYLE)
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)
    
    dialog.exec_()

def show_tutorial(app):
    """Show the tutorial dialog"""
    dialog = QDialog(app)
    dialog.setWindowTitle("Tutorial")
    dialog.resize(600, 500)
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(10)
    
    # Title
    title_label = QLabel("Getting Started with Echelon")
    font = title_label.font()
    font.setBold(True)
    font.setPointSize(14)
    title_label.setFont(font)
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(title_label)
    
    # Tutorial content
    tab_widget = QTabWidget()
    tab_widget.setStyleSheet(f"""
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            background-color: {colors['card_bg']};
        }}
        QTabBar::tab {{
            background-color: {colors['bg']};
            color: {colors['text']};
            padding: 8px 12px;
            border: 1px solid {colors['border']};
            border-bottom: none;
        }}
        QTabBar::tab:selected {{
            background-color: {colors['card_bg']};
            border-bottom: none;
            border-top: 2px solid {colors['accent']};
        }}
    """)
    
    # Add tabs
    tabs = ["Templates", "Project Creation", "Customization"]
    
    for tab_name in tabs:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        
        # Placeholder content
        content = QLabel(f"{tab_name} tutorial content will be shown here.")
        content.setWordWrap(True)
        content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        content.setStyleSheet(f"color: {colors['text']};")
        tab_layout.addWidget(content)
        
        tab_widget.addTab(tab, tab_name)
    
    layout.addWidget(tab_widget)
    
    # Close button
    close_button = QPushButton("Close")
    close_button.setStyleSheet(BUTTON_STYLE)
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)
    
    dialog.exec_()

#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Pattern UI Components Module
Handles UI component creation for custom patterns dialog
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, 
    QComboBox, QGroupBox, QWidget, QGridLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class PatternUIComponents:
    """Handles UI component creation for custom patterns dialog"""
    
    def __init__(self, dialog):
        """Initialize UI components handler"""
        self.dialog = dialog
        self.colors = None
        self.styles = None
        
    def setup_styles(self):
        """Setup color scheme and styles"""
        from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, COMBOBOX_STYLE
        self.colors = colors
        self.styles = {
            'button': BUTTON_STYLE,
            'accent_button': ACCENT_BUTTON_STYLE,
            'combobox': COMBOBOX_STYLE
        }
        
    def create_title_section(self, layout, is_folder=False):
        """Create the title section"""
        if not self.colors:
            self.setup_styles()
            
        item_type = "Folder" if is_folder else "File"
        title = QLabel(f"Custom {item_type} Naming Patterns")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"""
            color: {self.colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-bottom: 8px;
        """)
        layout.addWidget(title)
        return title
        
    def create_variables_section(self, layout, is_folder=False):
        """Create the available variables section"""
        variables_header = QLabel("Available Variables:")
        variables_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        variables_header.setStyleSheet(f"""
            color: {self.colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-bottom: 3px;
        """)
        layout.addWidget(variables_header)
        
        # Tags widget
        tags_widget = QWidget()
        tags_widget.setStyleSheet(f"background-color: transparent; border: none;")
        tags_layout = QGridLayout(tags_widget)
        tags_layout.setSpacing(6)
        
        # Different tags for files vs folders
        if is_folder:
            tags = [
                ("${PROJECT_NAME}", "Project name"),
                ("${DATE}", "Current date (YYYYMMDD)"),
                ("${TIME}", "Current time (HHMMSS)"),
                ("${COUNTER}", "Incremental counter (001, 002, etc.)"),
                ("${CUSTOM}", "Custom dropdown options"),
                ("${CUSTOM1}", "First custom option"),
                ("${CUSTOM2}", "Second custom option"),
                ("${CUSTOM3}", "Third custom option")
            ]
        else:
            tags = [
                ("${PROJECT_NAME}", "Project name"),
                ("${BASE}", "Original filename without extension"),
                ("${DATE}", "Current date (YYYYMMDD)"),
                ("${TIME}", "Current time (HHMMSS)"),
                ("${CUSTOM}", "Custom dropdown options"),
                ("${CUSTOM1}", "First custom option"),
                ("${CUSTOM2}", "Second custom option"),
                ("${CUSTOM3}", "Third custom option")
            ]
        
        tag_buttons = []
        for i, (tag, description) in enumerate(tags):
            tag_button = QPushButton(tag)
            tag_button.setToolTip(description)
            tag_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.colors['card_bg_alt']};
                    color: {self.colors['text']};
                    border: 1px solid {self.colors['border']};
                    padding: 2px 6px;
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: normal;
                    min-width: 50px;
                    max-height: 20px;
                }}
                QPushButton:hover {{
                    background-color: {self.colors['accent']};
                    border: 1px solid {self.colors['highlight_border']};
                }}
                QPushButton:pressed {{
                    background-color: {self.colors['highlight_bg']};
                    color: {self.colors['highlight_text']};
                }}
            """)
            row = i // 3
            col = i % 3
            tags_layout.addWidget(tag_button, row, col)
            tag_buttons.append(tag_button)
        
        layout.addWidget(tags_widget)
        return tags, tag_buttons
        
    def create_separator_section(self, layout):
        """Create the separator selection section"""
        separator_header = QLabel("Choose separator for pattern elements:")
        separator_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        separator_header.setStyleSheet(f"""
            color: {self.colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-top: 6px;
            margin-bottom: 3px;
        """)
        layout.addWidget(separator_header)
        
        # Separator selection widget
        separator_widget = QWidget()
        separator_widget.setStyleSheet(f"background-color: transparent; border: none;")
        separator_layout = QHBoxLayout(separator_widget)
        separator_layout.setSpacing(10)
        
        separator_combo = QComboBox()
        separator_combo.addItems([
            "_ (underscore)",
            "- (dash)", 
            ". (dot)",
            "  (space)",
            "Custom..."
        ])
        separator_combo.setCurrentIndex(0)  # Default to underscore
        separator_combo.setStyleSheet(self.styles['combobox'])
        separator_layout.addWidget(separator_combo)
        
        # Custom separator input (hidden by default)
        custom_separator_edit = QLineEdit()
        custom_separator_edit.setPlaceholderText("Enter custom separator...")
        custom_separator_edit.setMaxLength(3)  # Limit to 3 characters
        custom_separator_edit.setVisible(False)
        custom_separator_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.colors['card_bg']};
                color: {self.colors['text']};
                border: 2px solid {self.colors['border']};
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 100px;
                max-width: 100px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.colors['accent']};
            }}
        """)
        separator_layout.addWidget(custom_separator_edit)
        
        separator_layout.addStretch()
        layout.addWidget(separator_widget)
        
        return separator_combo, custom_separator_edit
        
    def create_pattern_input_section(self, layout, is_folder=False):
        """Create the pattern input section"""
        pattern_header = QLabel("Enter your naming pattern:")
        pattern_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        pattern_header.setStyleSheet(f"""
            color: {self.colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-top: 6px;
            margin-bottom: 3px;
        """)
        layout.addWidget(pattern_header)
        
        pattern_edit = QLineEdit()
        if is_folder:
            pattern_edit.setPlaceholderText("e.g., ${PROJECT_NAME}_${CUSTOM}_Folder or Shot_${COUNTER}")
        else:
            pattern_edit.setPlaceholderText("e.g., ${PROJECT_NAME}_${CUSTOM}_TRAILER (extension auto-added)")
        
        pattern_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.colors['card_bg']};
                color: {self.colors['text']};
                border: 2px solid {self.colors['accent']};
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
                font-family: 'Courier New', monospace;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.colors['accent_hover']};
                background-color: {self.colors['highlight_bg_transparent']};
            }}
        """)
        layout.addWidget(pattern_edit)
        
        return pattern_edit
        
    def create_group_box(self, title, visible=False):
        """Create a styled group box"""
        group_box = QGroupBox(title)
        group_box.setVisible(visible)
        group_box.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {self.colors['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: {self.colors['text']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: {self.colors['text']};
                background-color: {self.colors['bg']};
            }}
        """)
        return group_box
        
    def create_help_label(self, text):
        """Create a styled help label"""
        help_label = QLabel(text)
        help_label.setStyleSheet(f"""
            color: {self.colors['secondary_text']};
            background-color: transparent;
            border: none;
            padding: 5px 0px;
        """)
        return help_label
        
    def create_styled_combo_box(self, items):
        """Create a styled combo box with items"""
        combo_box = QComboBox()
        combo_box.addItems(items)
        combo_box.setStyleSheet(self.styles['combobox'])
        
        # Apply hover delegate
        try:
            from app.ui.custom_delegates import apply_hover_delegate
            apply_hover_delegate(combo_box)
        except ImportError:
            pass
            
        return combo_box 
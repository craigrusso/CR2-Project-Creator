#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Custom Options Manager Module
Handles custom dropdown options for pattern variables
"""

import re
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QWidget, QPushButton
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class CustomOptionsManager:
    """Handles custom dropdown options management"""
    
    def __init__(self, dialog):
        """Initialize custom options manager"""
        self.dialog = dialog
        self.custom_option_editors = {}
        self.colors = None
        
    def setup_styles(self):
        """Setup color scheme"""
        from app.ui.color_scheme_pyqt import colors
        self.colors = colors
        
    def create_custom_options_group(self, layout):
        """Create the custom options group box"""
        if not self.colors:
            self.setup_styles()
            
        from .pattern_ui_components import PatternUIComponents
        ui_components = PatternUIComponents(self.dialog)
        ui_components.setup_styles()
        
        custom_options_group = ui_components.create_group_box("Custom Dropdown Options", visible=False)
        custom_layout = QVBoxLayout()
        
        custom_help = ui_components.create_help_label("Configure options for each CUSTOM placeholder:")
        custom_layout.addWidget(custom_help)
        
        # Container for custom option editors - will be populated dynamically
        custom_editors_container = QWidget()
        custom_editors_layout = QVBoxLayout(custom_editors_container)
        custom_editors_layout.setContentsMargins(0, 0, 0, 0)
        custom_editors_layout.setSpacing(10)
        custom_layout.addWidget(custom_editors_container)
        
        custom_options_group.setLayout(custom_layout)
        layout.addWidget(custom_options_group)
        
        return custom_options_group, custom_editors_container, custom_editors_layout

    def update_custom_editors(self, custom_placeholders, custom_editors_layout):
        """Update custom option editors based on placeholders found in pattern"""
        # Clear existing editors
        self.clear_custom_editors(custom_editors_layout)
        
        for placeholder in custom_placeholders:
            self.create_custom_editor(placeholder, custom_editors_layout)

    def create_custom_editor(self, placeholder, layout):
        """Create a custom option editor for a specific placeholder"""
        if not self.colors:
            self.setup_styles()
            
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(5)
        
        # Label for the placeholder
        label = QLabel(f"Options for {placeholder}:")
        label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        label.setStyleSheet(f"""
            color: {self.colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
        """)
        editor_layout.addWidget(label)
        
        # Input field for comma-separated options
        options_edit = QLineEdit()
        options_edit.setPlaceholderText("Enter options separated by commas (e.g., Option1, Option2, Option3)")
        options_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.colors['card_bg']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.colors['accent']};
            }}
        """)
        editor_layout.addWidget(options_edit)
        
        # Store the editor
        self.custom_option_editors[placeholder] = options_edit
        
        layout.addWidget(editor_widget)

    def clear_custom_editors(self, layout):
        """Clear all custom option editors"""
        # Remove all widgets from layout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Clear the editors dictionary
        self.custom_option_editors.clear()

    def get_custom_placeholders(self, pattern):
        """Extract custom placeholders from pattern"""
        if not pattern:
            return []
            
        # Find all CUSTOM placeholders
        custom_placeholders = []
        
        # Look for ${CUSTOM}, ${CUSTOM1}, ${CUSTOM2}, ${CUSTOM3}
        matches = re.findall(r'\$\{(CUSTOM\d*)\}', pattern)
        for match in matches:
            placeholder = f"${{{match}}}"
            if placeholder not in custom_placeholders:
                custom_placeholders.append(placeholder)
        
        return sorted(custom_placeholders)

    def get_custom_options_data(self):
        """Get all custom options data"""
        custom_options = {}
        
        for placeholder, editor in self.custom_option_editors.items():
            options_text = editor.text().strip()
            if options_text:
                # Split by comma and clean up
                options = [opt.strip() for opt in options_text.split(',') if opt.strip()]
                custom_options[placeholder] = options
        
        return custom_options

    def load_custom_options_data(self, pattern_data):
        """Load custom options data into editors"""
        if not pattern_data:
            return
            
        custom_options = pattern_data.get('custom_options', {})
        
        for placeholder, editor in self.custom_option_editors.items():
            if placeholder in custom_options:
                options = custom_options[placeholder]
                if isinstance(options, list):
                    editor.setText(', '.join(options))
                elif isinstance(options, str):
                    editor.setText(options)

    def validate_custom_options(self):
        """Validate custom options"""
        errors = []
        
        for placeholder, editor in self.custom_option_editors.items():
            options_text = editor.text().strip()
            if not options_text:
                errors.append(f"Please provide options for {placeholder}")
                continue
                
            # Check if options are valid
            options = [opt.strip() for opt in options_text.split(',') if opt.strip()]
            if len(options) < 1:
                errors.append(f"Please provide at least one option for {placeholder}")
            elif len(options) > 10:
                errors.append(f"Too many options for {placeholder} (maximum 10)")
            
            # Check for duplicate options
            if len(options) != len(set(options)):
                errors.append(f"Duplicate options found for {placeholder}")
            
            # Check option length
            for option in options:
                if len(option) > 50:
                    errors.append(f"Option '{option}' is too long (maximum 50 characters)")
                elif len(option) < 1:
                    errors.append(f"Empty option found for {placeholder}")
        
        return errors

    def get_sample_custom_values(self):
        """Get sample values for custom placeholders for preview"""
        sample_values = {}
        
        for placeholder, editor in self.custom_option_editors.items():
            options_text = editor.text().strip()
            if options_text:
                options = [opt.strip() for opt in options_text.split(',') if opt.strip()]
                if options:
                    sample_values[placeholder] = options[0]  # Use first option as sample
                else:
                    sample_values[placeholder] = "Option1"
            else:
                sample_values[placeholder] = "Option1"
        
        return sample_values

    def has_custom_placeholders(self, pattern):
        """Check if pattern has any custom placeholders"""
        return bool(self.get_custom_placeholders(pattern))

    def get_placeholder_options_count(self, placeholder):
        """Get the number of options for a specific placeholder"""
        if placeholder not in self.custom_option_editors:
            return 0
            
        editor = self.custom_option_editors[placeholder]
        options_text = editor.text().strip()
        if not options_text:
            return 0
            
        options = [opt.strip() for opt in options_text.split(',') if opt.strip()]
        return len(options)

    def clear_all_options(self):
        """Clear all custom options"""
        for editor in self.custom_option_editors.values():
            editor.clear()

    def set_placeholder_options(self, placeholder, options):
        """Set options for a specific placeholder"""
        if placeholder in self.custom_option_editors:
            if isinstance(options, list):
                self.custom_option_editors[placeholder].setText(', '.join(options))
            elif isinstance(options, str):
                self.custom_option_editors[placeholder].setText(options) 
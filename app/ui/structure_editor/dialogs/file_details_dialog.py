#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
File Details Dialog

Dialog for entering file details when adding new files to the structure.
Extracted from the monolithic file_operations.py for better organization.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt

# Import styling
from app.ui.color_scheme_pyqt import colors


class FileDetailsDialog(QDialog):
    """Dialog for entering file details"""
    
    def __init__(self, parent, title, message, file_name="", categories=None, 
                selected_type="", show_binary=True, is_binary=False):
        """Initialize the dialog"""
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Add message
        if message:
            label = QLabel(message)
            layout.addWidget(label)
        
        # File name field
        name_layout = QHBoxLayout()
        name_label = QLabel("File name:")
        name_layout.addWidget(name_label)
        
        self.file_name_edit = QLineEdit(file_name)
        self.file_name_edit.setPlaceholderText("Enter file name with extension")
        name_layout.addWidget(self.file_name_edit)
        
        layout.addLayout(name_layout)
        
        # File type dropdown
        type_layout = QHBoxLayout()
        type_label = QLabel("File type:")
        type_layout.addWidget(type_label)
        
        self.file_type_combo = QComboBox()
        if categories:
            self.file_type_combo.addItems(categories)
            if selected_type and selected_type in categories:
                self.file_type_combo.setCurrentText(selected_type)
                
        self.file_type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.file_type_combo)
        
        layout.addLayout(type_layout)
        
        # Binary checkbox
        if show_binary:
            self.binary_checkbox = QCheckBox("Binary file (will be cached)")
            self.binary_checkbox.setChecked(is_binary)
            layout.addWidget(self.binary_checkbox)
        else:
            self.binary_checkbox = None
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        button_layout.addStretch()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        
        # Apply styles
        self._apply_styles()
    
    def _apply_styles(self):
        """Apply consistent styling to the dialog"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg']};
                color: {colors['text']};
            }}
            QLabel {{
                color: {colors['text']};
            }}
            QLineEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {colors['accent']};
            }}
            QComboBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px 30px 8px 12px;
                font-size: 14px;
                min-height: 20px;
            }}
            QComboBox:focus {{
                border: 2px solid {colors['accent']};
            }}
            QComboBox:hover {{
                border: 2px solid {colors['accent_hover']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border: none;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: {colors['card_bg_alt']};
            }}
            QComboBox::drop-down:hover {{
                background-color: {colors['accent']};
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
                background: transparent;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {colors['text']};
                margin-top: 2px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                selection-background-color: {colors['accent']};
                selection-color: {colors['text']};
                outline: none;
            }}
            QPushButton {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {colors['accent']};
                border: 2px solid {colors['accent']};
            }}
            QCheckBox {{
                color: {colors['text']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {colors['border']};
                border-radius: 3px;
                background-color: {colors['card_bg']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors['accent']};
                border: 2px solid {colors['accent']};
            }}
        """)
    
    def _on_type_changed(self, index):
        """Handle file type change"""
        # Could update UI based on selected type in the future
        pass
    
    def get_file_name(self):
        """Get the entered file name"""
        return self.file_name_edit.text().strip()
    
    def get_file_type(self):
        """Get the selected file type"""
        return self.file_type_combo.currentText()
    
    def is_binary(self):
        """Get binary file status"""
        if self.binary_checkbox:
            return self.binary_checkbox.isChecked()
        return False 
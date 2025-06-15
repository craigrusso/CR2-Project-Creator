#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Versioning Dialog

Dialog for configuring file versioning patterns.
Extracted from the monolithic file_operations.py for better organization.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QSpinBox, QTextEdit
)
from PyQt6.QtGui import QFont

# Import styling
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, COMBOBOX_STYLE, SPINBOX_STYLE
from app.ui.custom_delegates import apply_hover_delegate


class VersioningDialog(QDialog):
    """Dialog for configuring file versioning"""
    
    def __init__(self, parent, item):
        super().__init__(parent)
        self.item = item
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Configure Versioning")
        self.setMinimumSize(500, 500)
        self.resize(600, 600)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg']};
                color: {colors['text']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("File Versioning Configuration")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Versioning format
        format_label = QLabel("Version Format:")
        format_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        format_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-bottom: 5px;
        """)
        layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "v01, v02, v03...",
            "V01, V02, V03...",
            "_v1, _v2, _v3...",
            "_V1, _V2, _V3...",
            "(v01), (v02), (v03)...",
            "001, 002, 003...",
            "_001, _002, _003..."
        ])
        
        # Apply consistent styling
        self.format_combo.setStyleSheet(COMBOBOX_STYLE)
        apply_hover_delegate(self.format_combo)
        
        layout.addWidget(self.format_combo)
        
        # Starting number
        start_label = QLabel("Starting Number:")
        start_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        start_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-top: 10px;
            margin-bottom: 5px;
        """)
        layout.addWidget(start_label)
        
        self.start_spin = QSpinBox()
        self.start_spin.setMinimum(1)
        self.start_spin.setMaximum(999)
        self.start_spin.setValue(1)
        self.start_spin.setStyleSheet(SPINBOX_STYLE)
        layout.addWidget(self.start_spin)
        
        # Number of versions
        count_label = QLabel("Number of Versions to Generate:")
        count_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        count_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-top: 10px;
            margin-bottom: 5px;
        """)
        layout.addWidget(count_label)
        
        self.count_spin = QSpinBox()
        self.count_spin.setMinimum(1)
        self.count_spin.setMaximum(50)
        self.count_spin.setValue(5)
        self.count_spin.setStyleSheet(SPINBOX_STYLE)
        layout.addWidget(self.count_spin)
        
        # Preview
        preview_label = QLabel("Preview:")
        preview_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        preview_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-top: 10px;
            margin-bottom: 5px;
        """)
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(120)
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 12px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.preview_text)
        
        # Connect signals
        self.format_combo.currentTextChanged.connect(self.update_preview)
        self.start_spin.valueChanged.connect(self.update_preview)
        self.count_spin.valueChanged.connect(self.update_preview)
        
        # Initial preview
        self.update_preview()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()  # Push buttons to the right
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet(BUTTON_STYLE)
        cancel_button.setMinimumSize(100, 35)
        button_layout.addWidget(cancel_button)
        
        apply_button = QPushButton("Apply Versioning")
        apply_button.clicked.connect(self.accept)
        apply_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        apply_button.setMinimumSize(150, 35)
        button_layout.addWidget(apply_button)
        
        layout.addLayout(button_layout)
    
    def update_preview(self):
        """Update the versioning preview"""
        format_text = self.format_combo.currentText()
        start_num = self.start_spin.value()
        count = self.count_spin.value()
        
        base_name = "filename"
        extension = ".txt"
        
        preview_lines = []
        
        for i in range(count):
            version_num = start_num + i
            
            if format_text.startswith("v0"):
                version_str = f"v{version_num:02d}"
            elif format_text.startswith("V0"):
                version_str = f"V{version_num:02d}"
            elif format_text.startswith("_v"):
                version_str = f"_v{version_num}"
            elif format_text.startswith("_V"):
                version_str = f"_V{version_num}"
            elif format_text.startswith("(v0"):
                version_str = f"(v{version_num:02d})"
            elif format_text.startswith("00"):
                version_str = f"{version_num:03d}"
            elif format_text.startswith("_00"):
                version_str = f"_{version_num:03d}"
            else:
                version_str = f"v{version_num:02d}"
            
            filename = f"{base_name}_{version_str}{extension}"
            preview_lines.append(filename)
        
        self.preview_text.setPlainText("\n".join(preview_lines))
    
    def get_versioning_data(self):
        """Get the versioning configuration data"""
        return {
            'versioning_format': self.format_combo.currentText(),
            'versioning_start': self.start_spin.value(),
            'versioning_count': self.count_spin.value(),
            'uses_versioning': True,
            'rename_flag': True
        } 
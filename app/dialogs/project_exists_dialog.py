#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Dialog for handling cases where a project already exists
"""

import os
import re
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QCheckBox,
                             QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE


class ProjectExistsDialog(QDialog):
    """Dialog shown when trying to create a project that already exists"""
    
    # Result constants
    CANCEL = 0
    OVERWRITE = 1
    CREATE_VERSION = 2
    
    def __init__(self, parent, project_name, project_path, suggested_version=None):
        """Initialize the dialog
        
        Args:
            parent: Parent widget
            project_name (str): Name of the project that already exists
            project_path (str): Full path to the existing project
            suggested_version (str, optional): Suggested version name (e.g., "ProjectName_V02")
        """
        super().__init__(parent)
        self.project_name = project_name
        self.project_path = project_path
        self.suggested_version = suggested_version or f"{project_name}_V02"
        self.result_action = self.CANCEL
        self.backup_existing = True
        self.version_name = self.suggested_version
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Project Already Exists")
        self.setFixedSize(500, 350)
        self.setModal(True)
        
        # Apply styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['background']};
                color: {colors['text']};
            }}
            QLabel {{
                color: {colors['text']};
            }}
            QLineEdit {{
                background-color: {colors['input_background']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 8px;
                color: {colors['text']};
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {colors['accent']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Warning icon and message
        header_layout = QHBoxLayout()
        
        # Warning label
        warning_label = QLabel("⚠️")
        warning_label.setFont(QFont("Arial", 24))
        header_layout.addWidget(warning_label)
        
        # Title
        title_label = QLabel("Project Already Exists")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {colors['warning']};")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Explanation
        explanation = QLabel(f"A project named '{self.project_name}' already exists at:")
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        
        # Path label
        path_label = QLabel(self.project_path)
        path_label.setStyleSheet(f"""
            QLabel {{
                background-color: {colors['input_background']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-family: monospace;
                font-size: 12px;
            }}
        """)
        path_label.setWordWrap(True)
        layout.addWidget(path_label)
        
        # Options label
        options_label = QLabel("Choose an action:")
        options_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(options_label)
        
        # Version name input
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("Create as version:"))
        
        self.version_input = QLineEdit(self.version_name)
        self.version_input.textChanged.connect(self.on_version_changed)
        version_layout.addWidget(self.version_input)
        
        layout.addLayout(version_layout)
        
        # Backup checkbox for overwrite option
        self.backup_checkbox = QCheckBox("Create backup when overwriting")
        self.backup_checkbox.setChecked(True)
        self.backup_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {colors['text']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:unchecked {{
                background-color: {colors['input_background']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors['accent']};
                border: 1px solid {colors['accent']};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.backup_checkbox)
        
        # Add some spacing
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(BUTTON_STYLE)
        cancel_btn.clicked.connect(self.cancel_action)
        button_layout.addWidget(cancel_btn)
        
        # Overwrite button
        overwrite_btn = QPushButton("Overwrite Existing")
        overwrite_btn.setStyleSheet(BUTTON_STYLE)
        overwrite_btn.clicked.connect(self.overwrite_action)
        button_layout.addWidget(overwrite_btn)
        
        # Create version button
        version_btn = QPushButton("Create Version")
        version_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        version_btn.clicked.connect(self.create_version_action)
        version_btn.setDefault(True)  # Make this the default action
        button_layout.addWidget(version_btn)
        
        layout.addLayout(button_layout)
        
    def on_version_changed(self, text):
        """Handle version name input changes"""
        self.version_name = text.strip()
        
    def cancel_action(self):
        """User chose to cancel"""
        self.result_action = self.CANCEL
        self.reject()
        
    def overwrite_action(self):
        """User chose to overwrite existing project"""
        self.result_action = self.OVERWRITE
        self.backup_existing = self.backup_checkbox.isChecked()
        self.accept()
        
    def create_version_action(self):
        """User chose to create a versioned project"""
        if not self.version_name:
            return  # Don't allow empty version names
            
        self.result_action = self.CREATE_VERSION
        self.accept()
        
    def get_result(self):
        """Get the user's choice and related data
        
        Returns:
            tuple: (action, data) where:
                - action is one of CANCEL, OVERWRITE, CREATE_VERSION
                - data is a dict with relevant information
        """
        if self.result_action == self.CANCEL:
            return self.CANCEL, {}
        elif self.result_action == self.OVERWRITE:
            return self.OVERWRITE, {"backup_existing": self.backup_existing}
        elif self.result_action == self.CREATE_VERSION:
            return self.CREATE_VERSION, {"version_name": self.version_name}
        
    @staticmethod
    def get_next_version_name(base_name, output_dir):
        """Get the next available version name for a project
        
        Args:
            base_name (str): Base project name
            output_dir (str): Output directory to check
            
        Returns:
            str: Next available version name (e.g., "ProjectName_V02")
        """
        # Look for existing versions
        existing_versions = []
        
        try:
            if os.path.exists(output_dir):
                for item in os.listdir(output_dir):
                    # Check for version pattern: basename_V## or basename_v##
                    pattern = f"^{re.escape(base_name)}_[Vv](\\d+)$"
                    match = re.match(pattern, item)
                    if match and os.path.isdir(os.path.join(output_dir, item)):
                        version_num = int(match.group(1))
                        existing_versions.append(version_num)
        except Exception:
            pass  # If there's an error reading directory, just continue
        
        # Find next available version number
        if existing_versions:
            next_version = max(existing_versions) + 1
        else:
            next_version = 2  # Start with V02 if no versions exist
            
        return f"{base_name}_V{next_version:02d}" 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QTextEdit, QScrollArea, QWidget, QApplication)
from PyQt6.QtCore import Qt, QCoreApplication, QSettings
from PyQt6.QtGui import QFont

from app.constants import get_resource_path
from app.utils.logging_utils import debug, info, warning, error

class EULADialog(QDialog):
    """
    Dialog to display the End User License Agreement (EULA) to the user.
    This is shown on first run or when the EULA is updated.
    """
    
    def __init__(self, parent=None, title="License Agreement", app=None):
        """Initialize the EULA dialog."""
        super().__init__(parent)
        
        self.app = app  # Store reference to main app
        self.eula_version_in_file = None
        self.accepted_version = None
        
        # Set up UI
        self.setWindowTitle(title)
        self.resize(800, 600)
        self.setModal(True)
        
        # Load EULA settings
        self.settings = QSettings()
        self.load_eula_settings()
        
        # Load EULA content
        eula_content = self.load_eula_content()
        if not eula_content:
            # Failed to load EULA
            self.reject()
            return
        
        # Create UI components
        self.create_ui_components(eula_content)
        
        # Set up layout
        self.setup_layout()
        
        # Center dialog on screen
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def load_eula_settings(self):
        """Load EULA settings from QSettings."""
        # Get current accepted EULA version
        self.accepted_version = self.settings.value("eula/accepted_version", "")
        
    def save_eula_acceptance(self):
        """Save EULA acceptance to settings."""
        if self.eula_version_in_file:
            self.settings.setValue("eula/accepted_version", self.eula_version_in_file)
            self.settings.sync()
            debug(f"Saved accepted EULA version {self.eula_version_in_file} to settings.")

    def load_eula_content(self):
        """Load EULA content from file."""
        # Try to find EULA file
        eula_path = get_resource_path("eula.txt")
        if not os.path.exists(eula_path):
            error(f"EULA file not found at expected path: {eula_path}")
            return None
        
        try:
            with open(eula_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Check if content begins with version tag (e.g., "# Version: 1.0")
                lines = content.splitlines()
                if lines and lines[0].startswith("# Version:"):
                    self.eula_version_in_file = lines[0].replace("# Version:", "").strip()
                    debug(f"Found EULA version in file: {self.eula_version_in_file}")
                else:
                    warning("EULA file does not start with version marker. Using full file.")
                    
                return content
        except Exception as e:
            error(f"Failed to read EULA file at {eula_path}: {e}")
            return None

    def create_ui_components(self, eula_content):
        """Create UI components for the dialog."""
        # Title label
        self.title_label = QLabel("End User License Agreement (EULA)")
        self.title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignmentFlagFlagFlag.AlignCenter)
        
        # EULA text area
        self.eula_text = QTextEdit()
        self.eula_text.setReadOnly(True)
        self.eula_text.setPlainText(eula_content)
        
        # Buttons
        self.accept_button = QPushButton("Accept")
        self.accept_button.clicked.connect(self.on_accept)
        self.accept_button.setMinimumWidth(120)
        
        self.decline_button = QPushButton("Decline")
        self.decline_button.clicked.connect(self.reject)
        self.decline_button.setMinimumWidth(120)

    def setup_layout(self):
        """Set up the layout for the dialog."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.eula_text)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.accept_button)
        button_layout.addWidget(self.decline_button)
        
        main_layout.addLayout(button_layout)

    def needs_to_show(self):
        """Check if EULA needs to be shown to the user."""
        # Show if:
        # 1. No previous acceptance record, or
        # 2. EULA version in file is different from accepted version
        if not self.accepted_version or (self.eula_version_in_file and self.eula_version_in_file != self.accepted_version):
            debug(f"EULA needs display. File Version: {self.eula_version_in_file}, Accepted Version: {self.accepted_version}")
            return True
        
        debug(f"EULA already accepted for version {self.accepted_version}.")
        return False

    def on_accept(self):
        """Handle EULA acceptance."""
        self.save_eula_acceptance()
        self.accept()

    @staticmethod
    def show_and_verify(parent=None, title="License Agreement", app=None):
        """
        Show EULA dialog if needed and verify acceptance.
        Returns True if EULA is accepted, False otherwise.
        """
        try:
            dialog = EULADialog(parent, title, app)
            if not dialog.eula_version_in_file:
                error("EULA Dialog initialization failed (missing EULA file?). Exiting.")
                return False
            
            if dialog.needs_to_show():
                debug("Displaying EULA dialog.")
                result = dialog.exec()
                if result == QDialog.Accepted:
                    debug("EULA accepted by user.")
                    return True
                else:
                    debug("EULA declined by user or dialog closed.")
                    return False
            else:
                # EULA already accepted
                return True
        except Exception as e:
            error(f"Error showing EULA dialog: {e}")
            return False 
            
    @staticmethod
    def show_eula_if_needed():
        """
        Backward compatibility wrapper for show_and_verify.
        Used by the old main.py code.
        """
        return EULADialog.show_and_verify(None, "License Agreement", None) 
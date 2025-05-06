# app/dialogs/eula_dialog.py
import sys
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton, 
                             QDialogButtonBox, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont

from app.constants import get_resource_path, APP_NAME

class EulaDialog(QDialog):
    """
    A dialog to display the End-User License Agreement (EULA) and require acceptance.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.eula_version_in_file = None
        self.accepted_version = None
        self._load_settings()
        self.eula_content = self._load_eula()

        if not self.eula_content:
            # Handle case where EULA file is missing or invalid
            QMessageBox.critical(self, "Error", "Could not load the End-User License Agreement. Please reinstall the application.")
            # Rejecting automatically closes the dialog, signaling failure
            QTimer.singleShot(0, self.reject) 
            return

        self.setWindowTitle(f"{APP_NAME} - End-User License Agreement")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)

        # --- Text Area ---
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(self.eula_content) 
        # Slightly smaller font for readability of long text
        font = QFont()
        font.setPointSize(font.pointSize() - 1) 
        self.text_edit.setFont(font)
        layout.addWidget(self.text_edit)

        # --- Buttons ---
        self.button_box = QDialogButtonBox()
        self.accept_button = self.button_box.addButton("Accept", QDialogButtonBox.AcceptRole)
        self.decline_button = self.button_box.addButton("Decline", QDialogButtonBox.RejectRole)
        
        # Initially disable Accept button until scrolled to bottom
        self.accept_button.setEnabled(False) 
        
        layout.addWidget(self.button_box)

        # --- Connections ---
        self.button_box.accepted.connect(self.accept_eula)
        self.button_box.rejected.connect(self.reject) # Default reject behavior is fine
        
        # Enable Accept button when scrolled to the bottom
        self.text_edit.verticalScrollBar().valueChanged.connect(self.check_scroll_position)
        
        # Check initial position in case content is short
        self.check_scroll_position(self.text_edit.verticalScrollBar().value())

    def _load_settings(self):
        """Load accepted EULA version from settings."""
        settings = QSettings()
        self.accepted_version = settings.value("eula/accepted_version", None)

    def _save_settings(self):
        """Save the accepted EULA version to settings."""
        if self.eula_version_in_file:
            settings = QSettings()
            settings.setValue("eula/accepted_version", self.eula_version_in_file)
            print(f"DEBUG: Saved accepted EULA version {self.eula_version_in_file} to settings.")

    def _load_eula(self):
        """Loads the EULA text from the file and extracts the version."""
        eula_path_relative = "EULA.txt"
        eula_path = get_resource_path(eula_path_relative)
        
        if not eula_path or not os.path.exists(eula_path):
            print(f"ERROR: EULA file not found at expected path: {eula_path}")
            return None
        
        try:
            with open(eula_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                # Look for version marker like "# EULA Version: 1.0"
                if first_line.startswith("# EULA Version:"):
                    self.eula_version_in_file = first_line.split(":", 1)[1].strip()
                    print(f"DEBUG: Found EULA version in file: {self.eula_version_in_file}")
                else:
                     print(f"WARN: EULA file does not start with version marker. Using full file.")
                     # If no version marker, treat the whole file as content
                     f.seek(0) # Reset read pointer
                
                content = f.read()
                return content
        except Exception as e:
            print(f"ERROR: Failed to read EULA file at {eula_path}: {e}")
            return None

    def needs_display(self):
        """Check if the EULA needs to be displayed and accepted."""
        if not self.eula_version_in_file:
            # If EULA has no version, maybe always show? Or treat as error?
            # For now, assume if file exists but no version, it needs acceptance once.
            return self.accepted_version is None 
        
        # Display if no version accepted yet, or if file version is newer than accepted one
        needs_accept = self.accepted_version is None or self.accepted_version != self.eula_version_in_file
        if needs_accept:
             print(f"DEBUG: EULA needs display. File Version: {self.eula_version_in_file}, Accepted Version: {self.accepted_version}")
        else:
             print(f"DEBUG: EULA already accepted for version {self.accepted_version}.")
        return needs_accept

    def accept_eula(self):
        """Saves the accepted version and closes the dialog."""
        self._save_settings()
        self.accept() # Signal acceptance

    def check_scroll_position(self, value):
        """Enables the Accept button only when scrolled to the bottom."""
        scrollbar = self.text_edit.verticalScrollBar()
        # Enable if scrollbar is at its maximum value (or if no scrollbar needed)
        is_at_bottom = (scrollbar.maximum() == 0) or (value == scrollbar.maximum())
        self.accept_button.setEnabled(is_at_bottom)

    @staticmethod
    def show_eula_if_needed(parent=None):
        """Static method to create, check, and execute the dialog if necessary."""
        dialog = EulaDialog(parent)
        
        # Check if EULA loading failed in __init__
        if not dialog.eula_content:
            print("ERROR: EULA Dialog initialization failed (missing EULA file?). Exiting.")
            return False # Indicate failure to proceed

        if dialog.needs_display():
            print("DEBUG: Displaying EULA dialog.")
            result = dialog.exec_()
            if result == QDialog.Accepted:
                print("DEBUG: EULA accepted by user.")
                return True # User accepted
            else:
                print("DEBUG: EULA declined by user or dialog closed.")
                return False # User declined or closed
        else:
            # EULA already accepted for the current version
            return True # No need to show, proceed 
# app/dialogs/privacy_policy_dialog.py
import sys
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton, 
                             QDialogButtonBox, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QFont

from app.constants import get_resource_path, APP_NAME

class PrivacyPolicyDialog(QDialog):
    """
    A dialog to display the Privacy Policy.
    """
    def __init__(self, parent=None, mark_as_shown=False):
        """
        Initializes the dialog.
        Args:
            parent: The parent widget.
            mark_as_shown (bool): If True, update settings to mark this version as shown upon closing.
        """
        super().__init__(parent)
        self.policy_version_in_file = None
        self.shown_version = None
        self.mark_as_shown_on_close = mark_as_shown
        self._load_settings() 
        self.policy_content = self._load_policy()

        if not self.policy_content:
            QMessageBox.critical(self, "Error", "Could not load the Privacy Policy.")
            QTimer.singleShot(0, self.reject) 
            return

        self.setWindowTitle(f"{APP_NAME} - Privacy Policy")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)

        # --- Text Area ---
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(self.policy_content)
        font = QFont()
        font.setPointSize(font.pointSize() - 1)
        self.text_edit.setFont(font)
        layout.addWidget(self.text_edit)

        # --- Buttons ---
        # Only needs a Close button
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        layout.addWidget(self.button_box)

        # --- Connections ---
        self.button_box.rejected.connect(self.close_dialog) # Connect close to our method

    def _load_settings(self):
        """Load the last shown policy version from settings."""
        settings = QSettings()
        self.shown_version = settings.value("privacy_policy/shown_version", None)

    def _save_settings(self):
        """Save the current policy version as shown in settings."""
        if self.policy_version_in_file:
            settings = QSettings()
            settings.setValue("privacy_policy/shown_version", self.policy_version_in_file)
            print(f"DEBUG: Saved shown Privacy Policy version {self.policy_version_in_file} to settings.")

    def _load_policy(self):
        """Loads the Privacy Policy text from the file and extracts the version."""
        policy_path_relative = "PrivacyPolicy.txt"
        policy_path = get_resource_path(policy_path_relative)

        if not policy_path or not os.path.exists(policy_path):
            print(f"ERROR: Privacy Policy file not found at expected path: {policy_path}")
            return None
        
        try:
            with open(policy_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                # Look for version marker like "# Privacy Policy Version: 1.0"
                if first_line.startswith("# Privacy Policy Version:"):
                    self.policy_version_in_file = first_line.split(":", 1)[1].strip()
                    print(f"DEBUG: Found Privacy Policy version in file: {self.policy_version_in_file}")
                else:
                    # print(f"WARN: Privacy Policy file does not start with version marker. Using full file.")
                    # If no version marker, treat the whole file as content
                    f.seek(0) # Reset read pointer
                
                content = f.read()
                return content
        except Exception as e:
            print(f"ERROR: Failed to read Privacy Policy file at {policy_path}: {e}")
            return None

    def needs_display(self):
        """Check if the policy needs to be shown (first run or updated version)."""
        if not self.policy_version_in_file:
             # If no version in file, maybe always show on first run?
             # For now, treat as needing display only if never shown before.
            return self.shown_version is None

        # Display if no version shown yet, or if file version is newer than shown one
        needs_show = self.shown_version is None or self.shown_version != self.policy_version_in_file
        if needs_show:
             print(f"DEBUG: Privacy Policy needs display. File Version: {self.policy_version_in_file}, Shown Version: {self.shown_version}")
        else:
             print(f"DEBUG: Privacy Policy already shown for version {self.shown_version}.")
        return needs_show

    def close_dialog(self):
        """Closes the dialog and marks the version as shown if required."""
        if self.mark_as_shown_on_close:
            self._save_settings()
        self.accept() # Use accept() to close, doesn't imply agreement here

    @staticmethod
    def show_policy(parent=None):
        """Static method to create and show the dialog (e.g., from a menu)."""
        # When shown from menu, don't automatically mark as shown again
        dialog = PrivacyPolicyDialog(parent=parent, mark_as_shown=False) 
        if dialog.policy_content: # Check if loading succeeded
            dialog.exec_()

    @staticmethod
    def show_policy_if_needed(parent=None):
        """Static method to check if the policy needs showing and display it if so."""
        dialog = PrivacyPolicyDialog(parent=parent, mark_as_shown=True)
        
        if not dialog.policy_content:
            print("ERROR: Privacy Policy Dialog initialization failed (missing file?). Skipping first run check.")
            return # Don't block startup

        if dialog.needs_display():
            print("DEBUG: Displaying Privacy Policy dialog (first run/updated).")
            dialog.exec_() # Show modally
        else:
            # Policy already shown for the current version
            pass # Do nothing 
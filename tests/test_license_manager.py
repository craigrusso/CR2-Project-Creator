#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for the license manager
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
    from PyQt5.QtCore import Qt
    
    from app.utils.security.license_manager import (
        LicenseManager, LicenseActivationDialog, TrialNagDialog
    )
    from app.dialogs.license_management import LicenseManagementDialog
    
    class TestWindow(QMainWindow):
        """Test window for license manager testing"""
        
        def __init__(self):
            super().__init__()
            self.license_manager = LicenseManager()
            self.setup_ui()
            
        def setup_ui(self):
            """Set up the test UI"""
            self.setWindowTitle("License Manager Test")
            self.setGeometry(100, 100, 500, 400)
            
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Layout
            layout = QVBoxLayout(central_widget)
            
            # Status label
            self.status_label = QLabel("License Status: Checking...")
            self.update_status_label()
            layout.addWidget(self.status_label)
            
            # License info button
            info_button = QPushButton("Show License Information")
            info_button.clicked.connect(self.show_license_info)
            layout.addWidget(info_button)
            
            # Activate license button
            activate_button = QPushButton("Activate License")
            activate_button.clicked.connect(self.show_activation_dialog)
            layout.addWidget(activate_button)
            
            # Deactivate license button
            deactivate_button = QPushButton("Deactivate License")
            deactivate_button.clicked.connect(self.deactivate_license)
            layout.addWidget(deactivate_button)
            
            # Show trial dialog button
            trial_button = QPushButton("Show Trial Dialog")
            trial_button.clicked.connect(self.show_trial_dialog)
            layout.addWidget(trial_button)
            
            # Clear license data button
            clear_button = QPushButton("Clear License Data")
            clear_button.clicked.connect(self.clear_license_data)
            layout.addWidget(clear_button)
        
        def update_status_label(self):
            """Update the status label with current license information"""
            if self.license_manager.is_licensed():
                self.status_label.setText("License Status: Licensed")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                days_left = self.license_manager.get_trial_days_remaining()
                if days_left > 0:
                    self.status_label.setText(f"License Status: Trial ({days_left} days left)")
                    self.status_label.setStyleSheet("color: blue; font-weight: bold;")
                else:
                    self.status_label.setText("License Status: Unlicensed (Trial expired)")
                    self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        def show_license_info(self):
            """Show the license management dialog"""
            dialog = LicenseManagementDialog(self, self.license_manager)
            dialog.exec_()
            self.update_status_label()
        
        def show_activation_dialog(self):
            """Show the activation dialog"""
            dialog = LicenseActivationDialog(self, self.license_manager)
            dialog.exec_()
            self.update_status_label()
        
        def deactivate_license(self):
            """Deactivate the current license"""
            success, message = self.license_manager.deactivate_license()
            if success:
                self.status_label.setText(f"License Status: {message}")
            else:
                self.status_label.setText(f"License Status: Error - {message}")
            self.update_status_label()
        
        def show_trial_dialog(self):
            """Show the trial nag dialog"""
            days_left = self.license_manager.get_trial_days_remaining()
            dialog = TrialNagDialog(self, self.license_manager, days_left)
            dialog.exec_()
            self.update_status_label()
        
        def clear_license_data(self):
            """Clear all license data"""
            self.license_manager.clear_license_data()
            self.update_status_label()
    
    def main():
        """Main function for the test script"""
        app = QApplication(sys.argv)
        window = TestWindow()
        window.show()
        sys.exit(app.exec_())
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure PyQt5 is installed and the application is properly set up.")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 
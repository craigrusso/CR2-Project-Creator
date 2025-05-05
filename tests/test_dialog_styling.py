#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for dialog button styling.
Tests both standard dialogs and our styled versions to verify button appearance.
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QInputDialog, QDialog
from app.ui.dialog_styling import StyledMessageBox, StyledInputDialog
from app.ui.app_theme_pyqt import force_app_palette, configure_styles

class TestWindow(QMainWindow):
    """A test window with buttons to trigger different dialogs."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dialog Styling Test")
        self.resize(400, 300)
        
        # Create central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # Create test buttons
        self.btn_standard_input = QPushButton("Test Standard Input Dialog")
        self.btn_styled_input = QPushButton("Test Styled Input Dialog")
        self.btn_styled_info = QPushButton("Test Styled Message Box")
        
        # Connect buttons to test functions
        self.btn_standard_input.clicked.connect(self.test_standard_input)
        self.btn_styled_input.clicked.connect(self.test_styled_input)
        self.btn_styled_info.clicked.connect(self.test_styled_info)
        
        # Add buttons to layout
        layout.addWidget(self.btn_standard_input)
        layout.addWidget(self.btn_styled_input)
        layout.addWidget(self.btn_styled_info)
        
        # Set central widget
        self.setCentralWidget(central_widget)
    
    def test_standard_input(self):
        """Test a standard QInputDialog."""
        text, ok = QInputDialog.getText(
            self,
            "Rename Template",
            "Enter a new name for the imported template:",
            text="NFL STUDIO (Imported)"
        )
        
        if ok:
            print(f"Standard Input: {text}")
    
    def test_styled_input(self):
        """Test our StyledInputDialog."""
        text, ok = StyledInputDialog.get_text(
            self,
            "Rename Template",
            "Enter a new name for the imported template:",
            "NFL STUDIO (Imported)"
        )
        
        if ok:
            print(f"Styled Input: {text}")
    
    def test_styled_info(self):
        """Test the styled information dialog."""
        StyledMessageBox.show_information(
            self,
            "Import Successful",
            "Template imported successfully!",
            "Please restart the application for changes to take effect."
        )

def main():
    """Main entry point for the test application."""
    app = QApplication(sys.argv)
    
    # Apply theme
    force_app_palette(app)
    configure_styles(app)
    
    # Create and show the main window
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
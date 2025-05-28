#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for the StyledMessageBox class.
This script runs quick tests to verify the styled message box buttons are displaying correctly.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
from app.ui.dialog_styling import StyledMessageBox
from app.ui.app_theme_pyqt import force_app_palette, configure_styles

class TestWindow(QMainWindow):
    """A test window with buttons to trigger different message boxes."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Message Box Test")
        self.resize(400, 300)
        
        # Create central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # Create test buttons
        self.btn_styled_question = QPushButton("Test Styled Question Dialog")
        self.btn_styled_info = QPushButton("Test Styled Information Dialog")
        self.btn_regular_question = QPushButton("Test Regular Question Dialog")
        self.btn_template_exists = QPushButton("Test Template Exists Dialog")
        
        # Connect buttons to test functions
        self.btn_styled_question.clicked.connect(self.test_styled_question)
        self.btn_styled_info.clicked.connect(self.test_styled_info)
        self.btn_regular_question.clicked.connect(self.test_regular_question)
        self.btn_template_exists.clicked.connect(self.test_template_exists)
        
        # Add buttons to layout
        layout.addWidget(self.btn_styled_question)
        layout.addWidget(self.btn_styled_info)
        layout.addWidget(self.btn_regular_question)
        layout.addWidget(self.btn_template_exists)
        
        # Set central widget
        self.setCentralWidget(central_widget)
    
    def test_styled_question(self):
        """Test the styled question dialog."""
        result = StyledMessageBox.show_question(
            self,
            "Styled Question",
            "This is a styled question dialog.",
            "Do you want to proceed with this operation?"
        )
        
        if result == QMessageBox.Yes:
            print("User clicked Yes")
        else:
            print("User clicked No")
    
    def test_styled_info(self):
        """Test the styled information dialog."""
        StyledMessageBox.show_information(
            self,
            "Styled Information",
            "This is a styled information dialog.",
            "This is additional information."
        )
    
    def test_regular_question(self):
        """Test a regular QMessageBox for comparison."""
        msgbox = QMessageBox(self)
        msgbox.setWindowTitle("Regular Question")
        msgbox.setText("This is a regular question dialog.")
        msgbox.setInformativeText("Do you want to proceed with this operation?")
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setDefaultButton(QMessageBox.No)
        
        result = msgbox.exec()
        
        if result == QMessageBox.Yes:
            print("User clicked Yes")
        else:
            print("User clicked No")
    
    def test_template_exists(self):
        """Test a dialog that mimics the Template Exists dialog."""
        msgbox = StyledMessageBox(self)
        msgbox.setWindowTitle("Template Exists")
        msgbox.setText("A template named 'NFL STUDIO' already exists.")
        msgbox.setInformativeText("Do you want to overwrite it with the imported template?")
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setDefaultButton(QMessageBox.No)
        
        result = msgbox.exec()
        
        if result == QMessageBox.Yes:
            print("User clicked Yes")
        else:
            print("User clicked No")

def main():
    """Main entry point for the test application."""
    app = QApplication(sys.argv)
    
    # Apply theme
    force_app_palette(app)
    configure_styles(app)
    
    # Create and show the main window
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
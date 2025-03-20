#!/usr/bin/env python3
# Test script to check for app crashes

import sys
from PyQt5.QtWidgets import QApplication
from app.core.app_module_pyqt import ProjectCreatorApp

def main():
    """Run the application in test mode"""
    print("Starting Project Creator test...")
    
    # Initialize the PyQt application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    main_window = ProjectCreatorApp()
    main_window.show()
    
    # Start the application main loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
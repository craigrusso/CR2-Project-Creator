#!/usr/bin/env python3
# Test script to reproduce structure editor crash

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from app.core.app_config import setup_dpi_awareness
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder
from app.dialogs.dialog_windows_pyqt import show_structure_editor

class TestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Structure Editor Test")
        self.resize(300, 200)
        
        # Create template manager and project builder
        self.template_manager = TemplateManager()
        self.project_builder = ProjectBuilder(self.template_manager)
        
        # Create main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create test button
        test_button = QPushButton("Open Structure Editor")
        test_button.clicked.connect(self.open_structure_editor)
        layout.addWidget(test_button)
        
        # Show the window
        self.show()
    
    def open_structure_editor(self):
        print("Opening structure editor...")
        # Try to open the structure editor with debugging output
        try:
            # Test 1: No parameters
            print("\nTest 1: No parameters")
            result = show_structure_editor(self)
            print(f"Result: {result}")
            
            # Test 2: With structure_type
            print("\nTest 2: With structure_type")
            result = show_structure_editor(self, structure_type="Video Editing - Standard")
            print(f"Result: {result}")
            
            # Test 3: With callback
            print("\nTest 3: With callback")
            def callback(name, structure):
                print(f"Callback called with name: {name}")
                return True
            result = show_structure_editor(self, callback=callback)
            print(f"Result: {result}")
            
            # Test 4: With is_new=True
            print("\nTest 4: With is_new=True")
            result = show_structure_editor(self, is_new=True)
            print(f"Result: {result}")
            
            # Test 5: With suggested_name
            print("\nTest 5: With suggested_name")
            result = show_structure_editor(self, suggested_name="My Test Structure")
            print(f"Result: {result}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    # Setup DPI awareness
    setup_dpi_awareness()
    
    app = QApplication(sys.argv)
    window = TestApp()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
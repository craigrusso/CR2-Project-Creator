#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for the refactored Enhanced Structure Editor
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

# Import the editor
from app.ui.structure_editor_enhanced import EnhancedStructureEditor, show_enhanced_structure_editor

class TestWindow(QMainWindow):
    """Test window for the Enhanced Structure Editor"""
    
    def __init__(self):
        super().__init__()
        
        # Setup window
        self.setWindowTitle("Structure Editor Test")
        self.setGeometry(100, 100, 400, 200)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Create layout
        layout = QVBoxLayout(central)
        
        # Add buttons
        self.test_empty_btn = QPushButton("Test Empty Editor")
        self.test_empty_btn.clicked.connect(self.test_empty_editor)
        layout.addWidget(self.test_empty_btn)
        
        self.test_structure_btn = QPushButton("Test With Structure")
        self.test_structure_btn.clicked.connect(self.test_with_structure)
        layout.addWidget(self.test_structure_btn)
        
        self.test_function_btn = QPushButton("Test Function")
        self.test_function_btn.clicked.connect(self.test_function)
        layout.addWidget(self.test_function_btn)
        
        # Create a simple test structure
        self.test_structure = [
            {"Project Root": [
                {"Footage": []},
                {"Audio": []},
                {"Graphics": []},
                {"Exports": []}
            ]}
        ]
    
    def test_empty_editor(self):
        """Test the editor with no structure"""
        editor = EnhancedStructureEditor(self)
        result = editor.exec()
        
        if result:
            print("Editor accepted")
            result_data = editor.get_result()
            print(f"Result: {result_data}")
        else:
            print("Editor canceled")
    
    def test_with_structure(self):
        """Test the editor with a pre-defined structure"""
        editor = EnhancedStructureEditor(
            self,
            structure_name="Test Structure",
            structure=self.test_structure
        )
        result = editor.exec()
        
        if result:
            print("Editor accepted")
            result_data = editor.get_result()
            print(f"Result: {result_data}")
        else:
            print("Editor canceled")
    
    def test_function(self):
        """Test the show_enhanced_structure_editor function"""
        print("Testing show_enhanced_structure_editor function")
        success, structure, structure_name = show_enhanced_structure_editor(
            self,
            structure_name="Function Test",
            structure=self.test_structure
        )
        
        if success:
            print(f"Function returned success")
            print(f"Structure name: {structure_name}")
            print(f"Structure: {structure}")
        else:
            print("Function canceled")

def main():
    """Main entry point"""
    # Create the application
    app = QApplication(sys.argv)
    
    # Enable High DPI scaling
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create and show the main window
    window = TestWindow()
    window.show()
    
    # Start the application main loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
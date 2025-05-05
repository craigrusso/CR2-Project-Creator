#!/usr/bin/env python3
"""
Manual verification script to confirm the drag-and-drop and UI button fixes
"""

import os
import sys
import glob
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# Add the application directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def cleanup_test_files():
    """Remove any test template files created during testing"""
    test_files = glob.glob("Template_Test*.json")
    for file in test_files:
        try:
            os.remove(file)
            print(f"Removed test file: {file}")
        except Exception as e:
            print(f"Error removing {file}: {e}")

def verify_ui_buttons():
    """
    Manually verify that there are no duplicate UI buttons
    
    Instructions:
    1. This will launch the structure editor
    2. Visually confirm that there are no duplicate buttons (only one Save and one Cancel)
    3. Close the window when finished checking
    """
    print("\n=== VERIFYING UI BUTTONS ===")
    print("Instructions:")
    print("1. The structure editor will open")
    print("2. CHECK VISUALLY: There should be only ONE Save button and ONE Cancel button")
    print("3. Close the window when done\n")
    
    from app.ui.structure_editor_enhanced import EnhancedStructureEditor
    
    app = QApplication(sys.argv)
    editor = EnhancedStructureEditor(structure_name="TestUIButtons", is_new=True)
    editor.show()
    app.exec_()
    
    return True  # Manual verification

def verify_drag_drop():
    """
    Manually verify the drag-and-drop functionality
    
    Instructions:
    1. This will launch the main application
    2. Create a new template
    3. Drag a folder from your computer to the structure editor
    4. Verify that the folder name is preserved correctly
    5. Try to drag the same folder again - confirm the dialog appears asking to replace/add/cancel
    6. Choose replace and verify the structure is still correct
    """
    print("\n=== VERIFYING DRAG AND DROP ===")
    print("Instructions:")
    print("1. The main application will start")
    print("2. Create a new template (+ button)")
    print("3. Drag a folder from your computer to the structure editor")
    print("4. CHECK VISUALLY: The folder name should be preserved correctly")
    print("5. Try to drag the same folder again - a dialog should appear asking to replace/add/cancel")
    print("6. Choose 'Replace' and verify the structure is still correct")
    print("7. Save the template and close the window\n")
    
    # Run the main application
    os.system("python3 main.py")
    
    return True  # Manual verification

class VerificationWindow(QMainWindow):
    """Simple window to provide verification options"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fix Verification")
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Instructions
        title = QLabel("<h1>Manual Verification Tests</h1>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        instructions = QLabel("""
        <p>These tests require manual verification to confirm the fixes are working.</p>
        <p>Please follow the on-screen instructions for each test.</p>
        """)
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)
        
        # Test buttons
        self.btn_ui = QPushButton("Test UI Buttons Fix")
        self.btn_ui.clicked.connect(verify_ui_buttons)
        layout.addWidget(self.btn_ui)
        
        self.btn_drag_drop = QPushButton("Test Drag & Drop Fix")
        self.btn_drag_drop.clicked.connect(verify_drag_drop)
        layout.addWidget(self.btn_drag_drop)
        
        self.btn_cleanup = QPushButton("Cleanup Test Files")
        self.btn_cleanup.clicked.connect(cleanup_test_files)
        layout.addWidget(self.btn_cleanup)
        
        self.btn_exit = QPushButton("Exit")
        self.btn_exit.clicked.connect(self.close)
        layout.addWidget(self.btn_exit)

def main():
    """Main function to run verification tests"""
    app = QApplication(sys.argv)
    
    window = VerificationWindow()
    window.show()
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main()) 
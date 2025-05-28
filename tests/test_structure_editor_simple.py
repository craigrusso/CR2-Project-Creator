#!/usr/bin/env python3
# Simple test for structure editor
# Tests just the opening of the structure editor with minimal dependencies

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from app.ui.structure_editor_enhanced import EnhancedStructureEditor, show_enhanced_structure_editor

class TestWindow(QMainWindow):
    """Simple window to test structure editor"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Structure Editor Test")
        self.setGeometry(100, 100, 400, 200)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Layout
        layout = QVBoxLayout(central)
        
        # Test buttons
        new_btn = QPushButton("New Structure")
        new_btn.clicked.connect(self.test_new_structure)
        layout.addWidget(new_btn)
        
        edit_btn = QPushButton("Edit Structure")
        edit_btn.clicked.connect(self.test_edit_structure)
        layout.addWidget(edit_btn)
        
        simple_btn = QPushButton("Open via Helper Function")
        simple_btn.clicked.connect(self.test_helper_function)
        layout.addWidget(simple_btn)
        
        # Status indicator
        self.status_label = QPushButton("Exit Test")
        self.status_label.clicked.connect(self.close)
        layout.addWidget(self.status_label)
    
    def test_new_structure(self):
        """Test creating a new structure"""
        print("Testing new structure creation...")
        try:
            editor = EnhancedStructureEditor(self, is_new=True)
            editor.show()
            print("Success: Opened new structure editor")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    def test_edit_structure(self):
        """Test editing an existing structure"""
        print("Testing structure editing...")
        try:
            # Create a simple test structure
            structure = [
                "README.md",
                {"src": ["index.js", "app.js"]},
                "package.json"
            ]
            editor = EnhancedStructureEditor(self, structure_name="Test Structure", structure=structure)
            editor.show()
            print("Success: Opened structure editor with existing structure")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    def test_helper_function(self):
        """Test using the helper function"""
        print("Testing helper function...")
        try:
            # Create a simple test structure
            structure = [
                "README.md",
                {"src": ["index.js", "app.js"]},
                "package.json"
            ]
            show_enhanced_structure_editor(self, structure_name="Test Structure", structure=structure)
            print("Success: Opened structure editor via helper function")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Run the test"""
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
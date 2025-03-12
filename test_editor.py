#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# Import the structure editors
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
try:
    from app.ui.ui_components_pyqt import StructureEditor
    has_structure_editor = True
except ImportError:
    has_structure_editor = False

class TestApp(QMainWindow):
    """Test application for structure editors"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Structure Editor Test")
        self.resize(300, 200)
        
        # Create a central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create a layout
        layout = QVBoxLayout(central_widget)
        
        # Create buttons for testing
        enhanced_btn = QPushButton("Test Enhanced Editor")
        enhanced_btn.clicked.connect(self.test_enhanced_editor)
        layout.addWidget(enhanced_btn)
        
        if has_structure_editor:
            basic_btn = QPushButton("Test Basic Editor")
            basic_btn.clicked.connect(self.test_basic_editor)
            layout.addWidget(basic_btn)
        
        # Simple template manager for testing
        self.template_manager = SimpleTemplateManager()
        
    def test_enhanced_editor(self):
        """Test the EnhancedStructureEditor"""
        editor = EnhancedStructureEditor(
            self,
            structure_name="Test Structure",
            structure=[{"folder1": [{"subfolder": []}]}, {"folder2": []}],
            save_callback=lambda name, structure: print(f"Saved structure '{name}' with {len(structure)} items")
        )
        editor.exec_()
    
    def test_basic_editor(self):
        """Test the basic StructureEditor"""
        if has_structure_editor:
            editor = StructureEditor(
                self,
                structure={"folder1": {"subfolder": {}}, "folder2": {}},
                save_callback=lambda name, structure: print(f"Saved structure '{name}' with {len(structure)} items")
            )
            editor.exec_()


class SimpleTemplateManager:
    """Simple template manager for testing"""
    
    def __init__(self):
        self.custom_structures = {}
    
    def get_structure(self, name):
        """Get a structure by name"""
        from app.constants import DEFAULT_STRUCTURES
        
        # Check built-in structures
        if name in DEFAULT_STRUCTURES:
            return DEFAULT_STRUCTURES[name]
        
        # Check custom structures
        if name in self.custom_structures:
            return self.custom_structures[name].get("directories", [])
        
        return []
    
    def save_custom_structure(self, name, structure):
        """Save a custom structure"""
        self.custom_structures[name] = {"directories": structure}
        return True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestApp()
    window.show()
    sys.exit(app.exec_()) 
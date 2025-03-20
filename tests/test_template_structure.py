#!/usr/bin/env python3
# Test script for template creation with fixed structure format

import os
import sys
import tempfile
import shutil
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import Qt

# Import app modules
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder
from app.dialogs.dialog_windows_pyqt import preview_structure
from app.templates.gallery_events import GalleryEvents

# Test structure with various folder types - both empty and with children
TEST_STRUCTURE = [
    {"01_FOLDER": []},  # Empty folder using new format
    {"02_FOLDER_WITH_CHILDREN": [
        {"SUBFOLDER_1": []},  # Nested empty folder
        {"SUBFOLDER_2": [
            "file1.txt",
            "file2.txt"
        ]},
        "file_in_parent.txt"
    ]},
    "root_file.txt",  # File in root
    "03_FOLDER/"  # Legacy format empty folder (for compatibility testing)
]

class TemplateStructureTestDialog(QDialog):
    """Dialog to test template creation with fixed structure format"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Template Structure Test")
        self.resize(700, 600)
        
        # Create template manager
        self.template_manager = TemplateManager()
        
        # UI setup
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Template Structure Test")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # Instructions
        instructions = QLabel(
            "This test simulates the template creation process with the fixed structure format.\n"
            "It shows how the structure is formatted and displayed."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Preview section - simulate gallery preview
        preview_label = QLabel("Structure Preview (Gallery Style):")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(preview_label)
        
        self.gallery_preview = QTextEdit()
        self.gallery_preview.setReadOnly(True)
        self.gallery_preview.setMinimumHeight(150)
        self.gallery_preview.setStyleSheet("""
            background-color: #2A2A2A;
            color: #FFFFFF;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
        """)
        layout.addWidget(self.gallery_preview)
        
        # Raw JSON representation
        json_label = QLabel("Raw JSON Representation:")
        json_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(json_label)
        
        self.json_preview = QTextEdit()
        self.json_preview.setReadOnly(True)
        self.json_preview.setMinimumHeight(100)
        self.json_preview.setStyleSheet("""
            background-color: #2A2A2A;
            color: #FFFFFF;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
        """)
        layout.addWidget(self.json_preview)
        
        # Buttons
        preview_btn = QPushButton("Show Gallery Style Preview")
        preview_btn.clicked.connect(self.show_gallery_preview)
        layout.addWidget(preview_btn)
        
        tree_btn = QPushButton("Show Tree Preview")
        tree_btn.clicked.connect(self.show_tree_preview)
        layout.addWidget(tree_btn)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("margin-top: 10px; color: #666;")
        layout.addWidget(self.status_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        # Initialize with JSON representation
        self.show_json()
    
    def show_gallery_preview(self):
        """Simulate the gallery preview format"""
        self.status_label.setText("Showing gallery style preview...")
        
        # Create a format_structure function like in gallery_events.py
        def format_structure(items, indent=""):
            result = []
            
            for item in items:
                if isinstance(item, dict):
                    # It's a directory with children (or empty directory)
                    for dir_name, children in item.items():
                        result.append(f"{indent}📁 {dir_name}/")
                        if children:  # Only process if there are children
                            child_result = format_structure(children, indent + "  ")
                            if child_result:
                                result.append(child_result)
                elif isinstance(item, str):
                    # It's a file or legacy empty directory
                    if item.endswith('/'):
                        result.append(f"{indent}📁 {item.rstrip('/')}/")
                    else:
                        result.append(f"{indent}📄 {item}")
            
            return "\n".join(result)
        
        preview = format_structure(TEST_STRUCTURE)
        self.gallery_preview.setText(preview)
        self.status_label.setText("Gallery preview displayed")
    
    def show_tree_preview(self):
        """Show the tree preview dialog"""
        self.status_label.setText("Showing tree preview...")
        preview_structure(self, TEST_STRUCTURE)
        self.status_label.setText("Tree preview displayed")
    
    def show_json(self):
        """Show the raw JSON representation"""
        # Format the JSON-like structure for display
        import json
        json_str = json.dumps(TEST_STRUCTURE, indent=2)
        self.json_preview.setText(json_str)

def run_test():
    """Run the template structure test"""
    app = QApplication(sys.argv)
    dialog = TemplateStructureTestDialog()
    dialog.show()
    app.exec_()

if __name__ == "__main__":
    run_test()

 
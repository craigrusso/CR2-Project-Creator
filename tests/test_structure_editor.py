#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for the Enhanced Structure Editor
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# Import from our app
from app.ui.structure_editor_functions import (
    show_enhanced_structure_editor,
    create_new_structure,
    duplicate_structure,
    import_structure_from_file,
    export_structure_to_file
)

class TestWindow(QMainWindow):
    """Test window for structure editor"""
    
    def __init__(self):
        super().__init__()
        
        # Mock template manager for testing
        from app.templates.template_manager import TemplateManager
        self.template_manager = TemplateManager()
        
        # Set up UI
        self.setWindowTitle("Structure Editor Test")
        self.setGeometry(100, 100, 400, 300)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Create layout
        layout = QVBoxLayout(central)
        
        # Add buttons
        new_btn = QPushButton("Create New Structure")
        new_btn.clicked.connect(self.on_new_structure)
        layout.addWidget(new_btn)
        
        edit_btn = QPushButton("Edit Existing Structure")
        edit_btn.clicked.connect(self.on_edit_structure)
        layout.addWidget(edit_btn)
        
        duplicate_btn = QPushButton("Duplicate Structure")
        duplicate_btn.clicked.connect(self.on_duplicate_structure)
        layout.addWidget(duplicate_btn)
        
        import_btn = QPushButton("Import Structure from File")
        import_btn.clicked.connect(self.on_import_structure)
        layout.addWidget(import_btn)
        
        export_btn = QPushButton("Export Structure to File")
        export_btn.clicked.connect(self.on_export_structure)
        layout.addWidget(export_btn)
        
        # Add some test structures
        self._add_test_structures()
    
    def _add_test_structures(self):
        """Add some test structures to the template manager"""
        # Simple structure
        simple_structure = [
            {"Project Root": [
                "README.md",
                "LICENSE",
                {"src": [
                    "main.py",
                    "utils.py"
                ]},
                {"docs": [
                    "index.md",
                    "installation.md"
                ]}
            ]}
        ]
        
        # More complex structure
        complex_structure = [
            {"Web Project": [
                "README.md",
                "package.json",
                ".gitignore",
                {"src": [
                    "index.js",
                    "app.js",
                    {"components": [
                        "Header.jsx",
                        "Footer.jsx",
                        "Sidebar.jsx"
                    ]},
                    {"styles": [
                        "main.css",
                        "variables.css"
                    ]}
                ]},
                {"public": [
                    "index.html",
                    "favicon.ico",
                    {"images": [
                        "logo.png",
                        "background.jpg"
                    ]}
                ]},
                {"tests": [
                    "app.test.js",
                    "utils.test.js"
                ]}
            ]}
        ]
        
        # Save structures
        self.template_manager.save_structure("Simple Project", simple_structure)
        self.template_manager.save_structure("Web Application", complex_structure)
    
    def on_new_structure(self):
        """Create a new structure"""
        success, structure, name = create_new_structure(
            self,
            default_name="New Test Structure",
            project_type="Development"
        )
        
        if success:
            print(f"Created new structure '{name}' with {len(structure)} items")
    
    def on_edit_structure(self):
        """Edit an existing structure"""
        # Choose one of our test structures
        success, structure, name = show_enhanced_structure_editor(
            self,
            structure_name="Simple Project",
            is_new=False
        )
        
        if success:
            print(f"Edited structure '{name}' with {len(structure)} items")
    
    def on_duplicate_structure(self):
        """Duplicate an existing structure"""
        # Duplicate the web application structure
        success, structure, name = duplicate_structure(
            self,
            original_name="Web Application",
            new_name="Copy of Web Application"
        )
        
        if success:
            print(f"Duplicated structure as '{name}' with {len(structure)} items")
    
    def on_import_structure(self):
        """Import a structure from a file"""
        success, structure, name = import_structure_from_file(self)
        
        if success:
            print(f"Imported structure '{name}' with {len(structure)} items")
            # Save it to our template manager
            self.template_manager.save_structure(name, structure)
    
    def on_export_structure(self):
        """Export a structure to a file"""
        success = export_structure_to_file(self, "Web Application")
        
        if success:
            print("Exported structure to file")

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Setup DPI scaling
    from app.core.app_config import setup_dpi_awareness
    setup_dpi_awareness()
    
    # Create and show the test window
    window = TestWindow()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
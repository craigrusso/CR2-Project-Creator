#!/usr/bin/env python3
# Test script for structure format and preview

import os
import sys
import tempfile
import shutil
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt

# Import app modules
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder
from app.dialogs.dialog_windows_pyqt import preview_structure

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

class StructureTestDialog(QDialog):
    """Dialog to test structure preview and project creation"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Structure Format Test")
        self.resize(600, 400)
        
        # Create template manager
        self.template_manager = TemplateManager()
        
        # Create project builder
        self.project_builder = ProjectBuilder(self.template_manager)
        
        # Create temp directory for test project
        self.temp_dir = tempfile.mkdtemp()
        print(f"Created temp directory: {self.temp_dir}")
        
        # UI setup
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Structure Format and Preview Test")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # Instructions
        instructions = QLabel(
            "This test validates the structure format and preview changes.\n"
            "1. Preview Structure - Shows the structure in the UI.\n"
            "2. Create Test Project - Creates a project with the structure.\n"
            "3. Clean Up - Removes the test directory."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Structure info
        structure_info = QLabel("Test structure includes:")
        structure_info.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(structure_info)
        
        structure_details = QLabel(
            "• Empty folder using new dictionary format\n"
            "• Folder with nested subfolders (both empty and with files)\n"
            "• Files at various levels\n"
            "• Legacy format folder (with trailing slash)"
        )
        layout.addWidget(structure_details)
        
        # Buttons
        preview_btn = QPushButton("Preview Structure")
        preview_btn.clicked.connect(self.show_preview)
        layout.addWidget(preview_btn)
        
        create_btn = QPushButton("Create Test Project")
        create_btn.clicked.connect(self.create_project)
        layout.addWidget(create_btn)
        
        cleanup_btn = QPushButton("Clean Up")
        cleanup_btn.clicked.connect(self.cleanup)
        layout.addWidget(cleanup_btn)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("margin-top: 10px; color: #666;")
        layout.addWidget(self.status_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def show_preview(self):
        """Show preview of the test structure"""
        self.status_label.setText("Showing structure preview...")
        preview_structure(self, TEST_STRUCTURE)
        self.status_label.setText("Preview displayed")
    
    def create_project(self):
        """Create a test project with the structure"""
        project_name = "test_structure_project"
        
        # Create project
        self.status_label.setText(f"Creating project '{project_name}'...")
        success, result = self.project_builder.create_project(
            project_name=project_name,
            output_dir=self.temp_dir,
            structure_name=None,  # We'll pass the structure directly
            batch_mode=False
        )
        
        if success:
            project_path = result
            self.status_label.setText(f"Project created at: {project_path}")
            
            # Now create our test structure in the project
            self.project_builder._create_folder_structure(project_path, TEST_STRUCTURE)
            
            # Print the created structure
            print("Created project structure:")
            self._print_directory_structure(project_path)
            
            # Open the folder in finder/explorer
            self._open_folder(project_path)
        else:
            self.status_label.setText(f"Error creating project: {result}")
    
    def cleanup(self):
        """Clean up test files"""
        try:
            shutil.rmtree(self.temp_dir)
            self.status_label.setText(f"Cleaned up temporary directory: {self.temp_dir}")
            print(f"Removed temp directory: {self.temp_dir}")
        except Exception as e:
            self.status_label.setText(f"Error during cleanup: {str(e)}")
            print(f"Error during cleanup: {e}")
    
    def _print_directory_structure(self, start_path):
        """Print the directory structure for verification"""
        for root, dirs, files in os.walk(start_path):
            level = root.replace(start_path, '').count(os.sep)
            indent = ' ' * 4 * level
            print(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                print(f"{sub_indent}{f}")
    
    def _open_folder(self, path):
        """Open the folder in file explorer for visual inspection"""
        if os.path.exists(path):
            if sys.platform == 'darwin':  # macOS
                os.system(f"open '{path}'")
            elif sys.platform == 'win32':  # Windows
                os.system(f'explorer "{path}"')
            else:  # Linux and other
                os.system(f"xdg-open '{path}'")

def run_test():
    """Run the structure test"""
    app = QApplication(sys.argv)
    dialog = StructureTestDialog()
    dialog.show()
    app.exec()

if __name__ == "__main__":
    run_test() 
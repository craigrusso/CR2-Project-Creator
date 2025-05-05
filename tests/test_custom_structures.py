#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative
# Test for file vs folder detection in folder structure creation

import os
import sys
import tempfile
import shutil
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import Qt

# Import app modules
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder

class FileFolderTestDialog(QDialog):
    """Dialog to test file vs folder detection in the folder structure"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File vs Folder Detection Test")
        self.resize(800, 600)
        
        # Create template manager and project builder
        self.template_manager = TemplateManager()
        self.project_builder = ProjectBuilder(self.template_manager)
        
        # Create temp directory for test projects
        self.temp_dir = tempfile.mkdtemp()
        print(f"Created temp directory: {self.temp_dir}")
        
        # UI setup
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("File vs Folder Detection Test")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # Instructions
        instructions = QLabel(
            "This test validates the detection of files vs folders in the structure creation process.\n"
            "Specifically focusing on JSON files being incorrectly created as folders."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Test structures
        test_structures_label = QLabel("Test Structures:")
        test_structures_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(test_structures_label)
        
        # Structure 1 - Basic file vs folder test
        structure1_btn = QPushButton("Test 1: Basic Files vs Folders")
        structure1_btn.clicked.connect(self.test_basic_file_folder)
        layout.addWidget(structure1_btn)
        
        # Structure 2 - JSON file vs folder with same name
        structure2_btn = QPushButton("Test 2: JSON Files vs Same-named Folders")
        structure2_btn.clicked.connect(self.test_json_file_folder)
        layout.addWidget(structure2_btn)
        
        # Structure 3 - File extensions detection
        structure3_btn = QPushButton("Test 3: File Extensions Detection")
        structure3_btn.clicked.connect(self.test_file_extensions)
        layout.addWidget(structure3_btn)
        
        # Log output
        log_label = QLabel("Log:")
        log_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(log_label)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)
        
        # Cleanup and close
        cleanup_btn = QPushButton("Cleanup Test Files")
        cleanup_btn.clicked.connect(self.cleanup)
        layout.addWidget(cleanup_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def log(self, message):
        """Add a message to the log"""
        self.log_output.append(message)
        print(message)
    
    def test_basic_file_folder(self):
        """Test basic detection of files vs folders"""
        project_name = "basic_file_folder_test"
        self.log(f"Running Test 1: Basic Files vs Folders with project '{project_name}'")
        
        # Create a simple structure with clearly defined files and folders
        structure = [
            {"src": []},  # Empty folder
            {"docs": ["readme.txt"]},  # Folder with file
            "file1.txt",  # File in root
            "config.ini",  # Config file
            "script.py",   # Python file
            "data.json"    # JSON file
        ]
        
        # Create project
        success, result = self.project_builder.create_project(
            project_name=project_name,
            output_dir=self.temp_dir,
            structure_name=None,
            batch_mode=False
        )
        
        if success:
            project_path = result
            self.log(f"Project created at: {project_path}")
            
            # Create the structure
            self.project_builder._create_folder_structure(project_path, structure)
            
            # Verify results
            self.verify_structure(project_path, {
                "src": "dir",
                "docs": "dir",
                "docs/readme.txt": "file",
                "file1.txt": "file",
                "config.ini": "file",
                "script.py": "file",
                "data.json": "file"
            })
            
            # Open the folder
            self._open_folder(project_path)
        else:
            self.log(f"Error creating project: {result}")
    
    def test_json_file_folder(self):
        """Test JSON files vs folders with the same name"""
        project_name = "json_file_folder_test"
        self.log(f"Running Test 2: JSON Files vs Same-named Folders with project '{project_name}'")
        
        # Create structure with both JSON files and folders with the same name
        structure = [
            {"config": []},  # Folder named config
            "config.json",   # File named config.json
            {"data.json": []},  # Folder named data.json (with .json extension)
            "data.txt"       # Regular file
        ]
        
        # Create project
        success, result = self.project_builder.create_project(
            project_name=project_name,
            output_dir=self.temp_dir,
            structure_name=None,
            batch_mode=False
        )
        
        if success:
            project_path = result
            self.log(f"Project created at: {project_path}")
            
            # Create the structure
            self.project_builder._create_folder_structure(project_path, structure)
            
            # Verify results
            self.verify_structure(project_path, {
                "config": "dir",
                "config.json": "file",
                "data.json": "dir",
                "data.txt": "file"
            })
            
            # Open the folder
            self._open_folder(project_path)
        else:
            self.log(f"Error creating project: {result}")
    
    def test_file_extensions(self):
        """Test file extension detection"""
        project_name = "file_extension_test"
        self.log(f"Running Test 3: File Extensions Detection with project '{project_name}'")
        
        # Create structure with various file extensions
        structure = [
            "document.txt",  # Plain text
            "image.jpg",     # Image
            "video.mp4",     # Video
            "archive.zip",   # Archive
            "code.js",       # Code
            "data.json",     # JSON data
            "config.yml",    # YAML config
            "settings.xml",  # XML data
            "no_extension",  # No extension (should be file)
            {"folder.with.dots": []},  # Folder with dots
            {"images": ["photo.jpg", "logo.png"]}  # Nested files
        ]
        
        # Create project
        success, result = self.project_builder.create_project(
            project_name=project_name,
            output_dir=self.temp_dir,
            structure_name=None,
            batch_mode=False
        )
        
        if success:
            project_path = result
            self.log(f"Project created at: {project_path}")
            
            # Create the structure
            self.project_builder._create_folder_structure(project_path, structure)
            
            # Verify results
            self.verify_structure(project_path, {
                "document.txt": "file",
                "image.jpg": "file",
                "video.mp4": "file",
                "archive.zip": "file",
                "code.js": "file",
                "data.json": "file",
                "config.yml": "file",
                "settings.xml": "file",
                "no_extension": "file",
                "folder.with.dots": "dir",
                "images": "dir",
                "images/photo.jpg": "file",
                "images/logo.png": "file"
            })
            
            # Open the folder
            self._open_folder(project_path)
        else:
            self.log(f"Error creating project: {result}")
    
    def verify_structure(self, base_path, expected_items):
        """Verify that the structure was created correctly
        
        Args:
            base_path: Base path of the project
            expected_items: Dictionary of paths and expected types ("file" or "dir")
        """
        self.log("\nVerifying structure:")
        errors = 0
        
        for rel_path, expected_type in expected_items.items():
            full_path = os.path.join(base_path, rel_path)
            path_exists = os.path.exists(full_path)
            
            is_dir = os.path.isdir(full_path) if path_exists else False
            is_file = os.path.isfile(full_path) if path_exists else False
            
            if not path_exists:
                self.log(f"❌ Error: '{rel_path}' does not exist")
                errors += 1
            elif expected_type == "dir" and not is_dir:
                self.log(f"❌ Error: '{rel_path}' expected to be a directory but is a file")
                errors += 1
            elif expected_type == "file" and not is_file:
                self.log(f"❌ Error: '{rel_path}' expected to be a file but is a directory")
                errors += 1
            else:
                self.log(f"✅ Success: '{rel_path}' is correctly a {expected_type}")
        
        if errors == 0:
            self.log("\n✅ All items verified correctly!")
        else:
            self.log(f"\n❌ {errors} errors found in the structure")
    
    def cleanup(self):
        """Clean up test files"""
        try:
            shutil.rmtree(self.temp_dir)
            self.log(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            self.log(f"Error during cleanup: {str(e)}")
    
    def _open_folder(self, path):
        """Open the folder in file explorer"""
        if os.path.exists(path):
            if sys.platform == 'darwin':  # macOS
                os.system(f"open '{path}'")
            elif sys.platform == 'win32':  # Windows
                os.system(f'explorer "{path}"')
            else:  # Linux and other
                os.system(f"xdg-open '{path}'")

def run_test():
    """Run the file vs folder detection test"""
    app = QApplication(sys.argv)
    dialog = FileFolderTestDialog()
    dialog.show()
    app.exec_()

if __name__ == "__main__":
    run_test() 
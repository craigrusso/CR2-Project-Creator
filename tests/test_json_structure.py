#!/usr/bin/env python3
# Test script to verify JSON file vs folder structure handling

import os
import sys
import json
import tempfile
import shutil
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel, QTextEdit, QComboBox, QGroupBox, QRadioButton, QGridLayout, QHBoxLayout
from PyQt6.QtCore import Qt

# Import required modules
from app.core.project_builder import ProjectBuilder
from app.templates.template_manager import TemplateManager
from app.utils.utils import get_config_paths

class JsonStructureTestDialog(QDialog):
    """Dialog to test JSON file vs folder structure handling"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JSON File vs Folder Structure Test")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Test description
        description = QLabel(
            "This test verifies that JSON files and folders with the same name are correctly handled. "
            "The test creates a structure with both JSON files and folders, and verifies that they are correctly identified."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Create test structure section
        structure_group = QGroupBox("Test Structures")
        structure_layout = QGridLayout(structure_group)
        
        # Create test structure options
        self.test1_radio = QRadioButton("Basic JSON File Test")
        self.test1_radio.setChecked(True)
        structure_layout.addWidget(self.test1_radio, 0, 0)
        
        self.test2_radio = QRadioButton("JSON File and Folder with Same Name")
        structure_layout.addWidget(self.test2_radio, 1, 0)
        
        self.test3_radio = QRadioButton("Complex Structure with Multiple JSON Files")
        structure_layout.addWidget(self.test3_radio, 2, 0)
        
        layout.addWidget(structure_group)
        
        # Create a structure preview
        preview_label = QLabel("Structure Preview:")
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        
        # Create test output area
        output_label = QLabel("Test Output:")
        layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        self.create_button = QPushButton("Create Test Structure")
        self.create_button.clicked.connect(self.create_test_structure)
        button_layout.addWidget(self.create_button)
        
        self.run_button = QPushButton("Run Test")
        self.run_button.clicked.connect(self.run_test)
        button_layout.addWidget(self.run_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # Initialize
        self.temp_dir = None
        self.structure_name = None
        self.template_manager = TemplateManager()
        self.project_builder = ProjectBuilder(self.template_manager)
        
        # Show the initial structure preview
        self.update_preview()
        
        # Connect radio buttons to update preview
        self.test1_radio.toggled.connect(self.update_preview)
        self.test2_radio.toggled.connect(self.update_preview)
        self.test3_radio.toggled.connect(self.update_preview)
    
    def update_preview(self):
        """Update the structure preview based on selected test"""
        structure = self.get_selected_structure()
        self.preview_text.setText(json.dumps(structure, indent=2))
    
    def get_selected_structure(self):
        """Get the structure based on selected test"""
        if self.test1_radio.isChecked():
            return [
                "config.json",
                "README.md",
                "settings.json"
            ]
        elif self.test2_radio.isChecked():
            return [
                "config.json",
                {"config.json": []},  # This is a folder with the same name as a file
                "data.json",
                {"data": ["info.txt", "stats.csv"]}
            ]
        else:  # test3
            return [
                "package.json",
                {"src": [
                    "index.js",
                    {"components": [
                        "App.js",
                        "config.json",
                        "data.json"
                    ]},
                    {"utils": [
                        "helpers.js",
                        "config.json"  # Same name as folder in another location
                    ]}
                ]},
                {"config.json": [  # Folder with same name as a file
                    "settings.json",
                    "defaults.json"
                ]},
                "tsconfig.json"
            ]
    
    def log(self, message):
        """Add message to output log"""
        self.output_text.append(message)
        print(message)
    
    def create_test_structure(self):
        """Create the test structure in the template manager"""
        self.log("Creating test structure...")
        
        # Get selected structure
        structure = self.get_selected_structure()
        
        # Create a unique name for the structure
        import time
        self.structure_name = f"json_test_structure_{int(time.time())}"
        
        # Save the structure
        success = self.template_manager.save_custom_structure(self.structure_name, structure)
        
        if success:
            self.log(f"Structure '{self.structure_name}' created successfully")
            return True
        else:
            self.log("Failed to create structure")
            return False
    
    def run_test(self):
        """Run the test by creating a project with the structure"""
        # Create the structure if it doesn't exist
        if not self.structure_name:
            if not self.create_test_structure():
                return
        
        # Create a temporary directory for the test project
        self.temp_dir = tempfile.mkdtemp()
        self.log(f"Created temporary directory: {self.temp_dir}")
        
        # Create a test project name
        import time
        project_name = f"json_test_project_{int(time.time())}"
        project_path = os.path.join(self.temp_dir, project_name)
        
        # Create the project
        self.log(f"Creating project '{project_name}' with structure '{self.structure_name}'...")
        success, message = self.project_builder.create_project(
            project_name=project_name,
            output_dir=self.temp_dir,
            structure_name=self.structure_name
        )
        
        if success:
            self.log(f"Project created successfully: {project_path}")
            
            # Verify the structure
            self.verify_structure(project_path)
            
            # Open the folder in explorer
            self.open_folder(project_path)
        else:
            self.log(f"Failed to create project: {message}")
    
    def verify_structure(self, project_path):
        """Verify that the structure was created correctly"""
        self.log("\nVerifying structure:")
        
        # Get the expected structure for verification
        expected_structure = self.get_selected_structure()
        
        # Walk through the directory and log what was found
        for root, dirs, files in os.walk(project_path):
            rel_path = os.path.relpath(root, project_path)
            if rel_path == '.':
                self.log("\nRoot directory contains:")
                
                # Check each directory
                for dir_name in dirs:
                    self.log(f"  Directory: {dir_name}")
                
                # Check each file
                for file_name in files:
                    self.log(f"  File: {file_name}")
                    
                    # Specifically verify JSON files in the root
                    if file_name.endswith('.json'):
                        self.log(f"    Verified JSON file: {file_name}")
            else:
                self.log(f"\nSubdirectory {rel_path} contains:")
                
                # Check each directory
                for dir_name in dirs:
                    self.log(f"  Directory: {os.path.join(rel_path, dir_name)}")
                
                # Check each file
                for file_name in files:
                    self.log(f"  File: {os.path.join(rel_path, file_name)}")
        
        # Specific verification for test case 2
        if self.test2_radio.isChecked():
            # Verify that both config.json file and config.json folder exist
            file_path = os.path.join(project_path, "config.json")
            folder_path = os.path.join(project_path, "config.json")
            
            if os.path.isfile(file_path):
                self.log("\nSUCCESS: config.json file exists")
            else:
                self.log("\nFAILURE: config.json file does not exist")
            
            if os.path.isdir(folder_path):
                self.log("SUCCESS: config.json folder exists")
            else:
                self.log("FAILURE: config.json folder does not exist")
    
    def open_folder(self, path):
        """Open the folder in file explorer"""
        if os.path.exists(path):
            if sys.platform == 'darwin':  # macOS
                os.system(f"open '{path}'")
            elif sys.platform == 'win32':  # Windows
                os.system(f'explorer "{path}"')
            else:  # Linux and other
                os.system(f"xdg-open '{path}'")
    
    def closeEvent(self, event):
        """Clean up when the dialog is closed"""
        # Remove temporary directory if it exists
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                print(f"Removed temporary directory: {self.temp_dir}")
            except Exception as e:
                print(f"Failed to remove temporary directory: {e}")
        
        super().closeEvent(event)

def run_test():
    """Run the test"""
    app = QApplication(sys.argv)
    dialog = JsonStructureTestDialog()
    dialog.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_test() 
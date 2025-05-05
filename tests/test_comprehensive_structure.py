#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative
# Comprehensive test for structure editor, preview, and template functionality

import os
import sys
import tempfile
import shutil
import json
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt

# Import app modules
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder
from app.dialogs.dialog_windows_pyqt import preview_structure, show_structure_editor
from app.templates.structure_operations import StructureOperations

# Test structures with various file and folder combinations
SIMPLE_TEST_STRUCTURE = [
    {"01_FOLDER": []},  # Empty folder
    {"02_FOLDER_WITH_CHILDREN": [
        {"SUBFOLDER_1": []},  # Nested empty folder
        {"SUBFOLDER_2": [
            "file1.txt",
            "file2.txt"
        ]},
        "file_in_parent.txt"
    ]},
    "root_file.txt",  # File in root
    "root_file2.json"  # JSON file in root
]

COMPLEX_TEST_STRUCTURE = [
    {"01_PROJECT_FILES": [
        {"Assets": [
            {"Images": [
                "logo.png",
                "icon.png"
            ]},
            {"Audio": []},
            {"Video": []}
        ]},
        {"Documents": [
            "requirements.txt",
            "specifications.docx"
        ]},
        "project_plan.md"
    ]},
    {"02_SOURCE_CODE": [
        {"src": [
            {"components": [
                "main.js",
                "helper.js"
            ]},
            {"utils": [
                "formatter.js",
                "validator.js"
            ]},
            "index.js"
        ]},
        {"tests": [
            "main.test.js",
            "helper.test.js"
        ]},
        "README.md"
    ]},
    "config.json",
    "package.json"
]

class StructureTestDialog(QDialog):
    """Dialog to test structure editor, preview, and template functionality"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Comprehensive Structure Test")
        self.resize(800, 600)
        
        # Create template manager and other components
        self.template_manager = TemplateManager()
        self.project_builder = ProjectBuilder(self.template_manager)
        
        # Create temp directory for test projects
        self.temp_dir = tempfile.mkdtemp()
        print(f"Created temp directory: {self.temp_dir}")
        
        # UI setup
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Structure and Template Comprehensive Test")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # Instructions
        instructions = QLabel(
            "This test validates the complete structure and template functionality:\n"
            "1. Structure Editor - Test creating and editing structures\n"
            "2. Structure Preview - Test structure visualization\n"
            "3. Template Creation - Test creating templates with structures\n"
            "4. Files vs Folders - Test proper handling of files vs folders in structure"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Test Buttons
        # Structure Editor Tests
        self.add_section_label(layout, "Structure Editor Tests")
        
        editor_btn = QPushButton("1. Open Structure Editor (Empty)")
        editor_btn.clicked.connect(self.test_structure_editor_empty)
        layout.addWidget(editor_btn)
        
        editor_simple_btn = QPushButton("2. Open Structure Editor (Simple Structure)")
        editor_simple_btn.clicked.connect(self.test_structure_editor_simple)
        layout.addWidget(editor_simple_btn)
        
        editor_complex_btn = QPushButton("3. Open Structure Editor (Complex Structure)")
        editor_complex_btn.clicked.connect(self.test_structure_editor_complex)
        layout.addWidget(editor_complex_btn)
        
        # Structure Preview Tests
        self.add_section_label(layout, "Structure Preview Tests")
        
        preview_simple_btn = QPushButton("4. Preview Simple Structure")
        preview_simple_btn.clicked.connect(self.test_preview_simple)
        layout.addWidget(preview_simple_btn)
        
        preview_complex_btn = QPushButton("5. Preview Complex Structure")
        preview_complex_btn.clicked.connect(self.test_preview_complex)
        layout.addWidget(preview_complex_btn)
        
        # Project Creation Tests
        self.add_section_label(layout, "Project Creation Tests")
        
        create_simple_btn = QPushButton("6. Create Project with Simple Structure")
        create_simple_btn.clicked.connect(self.test_create_simple_project)
        layout.addWidget(create_simple_btn)
        
        create_complex_btn = QPushButton("7. Create Project with Complex Structure")
        create_complex_btn.clicked.connect(self.test_create_complex_project)
        layout.addWidget(create_complex_btn)
        
        # File vs Folder Handling Tests
        self.add_section_label(layout, "File vs Folder Handling Tests")
        
        file_folder_test_btn = QPushButton("8. Test JSON File vs Folder Handling")
        file_folder_test_btn.clicked.connect(self.test_json_file_folder_handling)
        layout.addWidget(file_folder_test_btn)
        
        save_load_structure_btn = QPushButton("9. Test Save and Load Structure")
        save_load_structure_btn.clicked.connect(self.test_save_load_structure)
        layout.addWidget(save_load_structure_btn)
        
        # Clean up and close buttons
        self.add_section_label(layout, "Cleanup")
        
        cleanup_btn = QPushButton("Clean Up Test Files")
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
    
    def add_section_label(self, layout, text):
        """Add a section label to the layout"""
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        layout.addWidget(label)
    
    # Structure Editor Tests
    
    def test_structure_editor_empty(self):
        """Test opening the structure editor with an empty structure"""
        self.status_label.setText("Opening structure editor with empty structure...")
        result = show_structure_editor(self, structure_type=None, callback=self.editor_callback)
        self.status_label.setText(f"Structure editor result: {result}")
    
    def test_structure_editor_simple(self):
        """Test opening the structure editor with a simple structure"""
        self.status_label.setText("Opening structure editor with simple structure...")
        
        # First save the structure to a custom structure
        structure_name = "Test_Simple_Structure"
        success = self.template_manager.save_custom_structure(structure_name, SIMPLE_TEST_STRUCTURE)
        
        if success:
            result = show_structure_editor(self, structure_type=structure_name, callback=self.editor_callback)
            self.status_label.setText(f"Structure editor result: {result}")
        else:
            self.status_label.setText("Failed to save test structure")
    
    def test_structure_editor_complex(self):
        """Test opening the structure editor with a complex structure"""
        self.status_label.setText("Opening structure editor with complex structure...")
        
        # First save the structure to a custom structure
        structure_name = "Test_Complex_Structure"
        success = self.template_manager.save_custom_structure(structure_name, COMPLEX_TEST_STRUCTURE)
        
        if success:
            result = show_structure_editor(self, structure_type=structure_name, callback=self.editor_callback)
            self.status_label.setText(f"Structure editor result: {result}")
        else:
            self.status_label.setText("Failed to save test structure")
    
    def editor_callback(self, name, structure):
        """Callback for structure editor"""
        print(f"Structure editor callback: name={name}")
        print(f"Structure: {structure}")
        self.status_label.setText(f"Structure saved as: {name}")
        return True
    
    # Structure Preview Tests
    
    def test_preview_simple(self):
        """Test preview of the simple structure"""
        self.status_label.setText("Showing preview of simple structure...")
        preview_structure(self, SIMPLE_TEST_STRUCTURE)
        self.status_label.setText("Simple structure preview displayed")
    
    def test_preview_complex(self):
        """Test preview of the complex structure"""
        self.status_label.setText("Showing preview of complex structure...")
        preview_structure(self, COMPLEX_TEST_STRUCTURE)
        self.status_label.setText("Complex structure preview displayed")
    
    # Project Creation Tests
    
    def test_create_simple_project(self):
        """Test creating a project with the simple structure"""
        project_name = "simple_structure_test"
        
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
            
            # Create our test structure in the project
            self.project_builder._create_folder_structure(project_path, SIMPLE_TEST_STRUCTURE)
            
            # Print the created structure
            print("Created project structure:")
            self._print_directory_structure(project_path)
            
            # Open the folder in finder/explorer
            self._open_folder(project_path)
        else:
            self.status_label.setText(f"Error creating project: {result}")
    
    def test_create_complex_project(self):
        """Test creating a project with the complex structure"""
        project_name = "complex_structure_test"
        
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
            
            # Create our test structure in the project
            self.project_builder._create_folder_structure(project_path, COMPLEX_TEST_STRUCTURE)
            
            # Print the created structure
            print("Created project structure:")
            self._print_directory_structure(project_path)
            
            # Open the folder in finder/explorer
            self._open_folder(project_path)
        else:
            self.status_label.setText(f"Error creating project: {result}")
    
    # File vs Folder Handling Tests
    
    def test_json_file_folder_handling(self):
        """Test handling of JSON files vs folders in structure"""
        project_name = "json_file_folder_test"
        
        # Structure with both JSON files and folders
        test_structure = [
            {"config": []},  # Folder named config
            "config.json",   # File named config.json
            {"data.json": []},  # Folder named data.json
            "data.txt"       # File named data.txt
        ]
        
        # Create project
        self.status_label.setText(f"Creating project to test JSON file vs folder handling...")
        success, result = self.project_builder.create_project(
            project_name=project_name,
            output_dir=self.temp_dir,
            structure_name=None,
            batch_mode=False
        )
        
        if success:
            project_path = result
            self.status_label.setText(f"Project created at: {project_path}")
            
            # Create the structure
            self.project_builder._create_folder_structure(project_path, test_structure)
            
            # Verify that both the folder and the file exist and are of the correct type
            config_folder_path = os.path.join(project_path, "config")
            config_file_path = os.path.join(project_path, "config.json")
            data_json_folder_path = os.path.join(project_path, "data.json")
            data_txt_path = os.path.join(project_path, "data.txt")
            
            # Perform checks
            status_messages = []
            if os.path.isdir(config_folder_path):
                status_messages.append("✓ 'config' created as folder")
            else:
                status_messages.append("✗ 'config' not created as folder")
            
            if os.path.isfile(config_file_path):
                status_messages.append("✓ 'config.json' created as file")
            else:
                status_messages.append("✗ 'config.json' not created as file")
                
            if os.path.isdir(data_json_folder_path):
                status_messages.append("✓ 'data.json' created as folder")
            else:
                status_messages.append("✗ 'data.json' not created as folder")
                
            if os.path.isfile(data_txt_path):
                status_messages.append("✓ 'data.txt' created as file")
            else:
                status_messages.append("✗ 'data.txt' not created as file")
            
            # Print results
            print("\nJSON File vs Folder Test Results:")
            for msg in status_messages:
                print(msg)
            
            self.status_label.setText("\n".join(status_messages))
            
            # Open the folder in finder/explorer
            self._open_folder(project_path)
        else:
            self.status_label.setText(f"Error creating project: {result}")
    
    def test_save_load_structure(self):
        """Test saving and loading a structure containing both files and folders"""
        structure_name = "FileAndFolderTest"
        
        # Structure with both files and folders, including JSON files
        test_structure = [
            {"assets": [
                "image.png",
                "sound.mp3",
                {"textures": ["wood.jpg", "metal.jpg"]},
            ]},
            "settings.json",
            {"config.json": []},  # This is a folder with name "config.json"
            "README.md"
        ]
        
        # Save the structure
        self.status_label.setText(f"Saving test structure '{structure_name}'...")
        success = self.template_manager.save_custom_structure(structure_name, test_structure)
        
        if success:
            self.status_label.setText(f"Structure saved successfully. Now loading...")
            
            # Load the structure
            loaded_structure = self.template_manager.get_structure(structure_name)
            
            # Verify the loaded structure
            success = self._verify_structure_equality(test_structure, loaded_structure)
            
            if success:
                self.status_label.setText("Structure saved and loaded successfully.")
                print("Structure Save/Load Test: PASSED")
                print(f"Original: {test_structure}")
                print(f"Loaded: {loaded_structure}")
            else:
                self.status_label.setText("Structure loaded but does not match original.")
                print("Structure Save/Load Test: FAILED")
                print(f"Original: {test_structure}")
                print(f"Loaded: {loaded_structure}")
        else:
            self.status_label.setText(f"Failed to save structure '{structure_name}'")
    
    def _verify_structure_equality(self, original, loaded):
        """Verify that two structures are equivalent"""
        # Convert to JSON and back to normalize formatting
        original_json = json.dumps(original, sort_keys=True)
        loaded_json = json.dumps(loaded, sort_keys=True)
        
        # Compare the normalized structures
        return original_json == loaded_json
    
    def cleanup(self):
        """Clean up test files"""
        try:
            shutil.rmtree(self.temp_dir)
            self.status_label.setText(f"Cleaned up temporary directory: {self.temp_dir}")
            print(f"Removed temp directory: {self.temp_dir}")
            
            # Clean up custom structures
            for name in ["Test_Simple_Structure", "Test_Complex_Structure", "FileAndFolderTest"]:
                try:
                    self.template_manager.delete_custom_structure(name)
                    print(f"Removed custom structure: {name}")
                except:
                    pass
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
    """Run the comprehensive structure test"""
    app = QApplication(sys.argv)
    dialog = StructureTestDialog()
    dialog.show()
    app.exec_()

if __name__ == "__main__":
    run_test() 
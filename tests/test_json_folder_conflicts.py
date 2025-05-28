#!/usr/bin/env python3
# Test script specifically focusing on JSON file vs folder conflict issues

import os
import sys
import tempfile
import shutil
import time
import json
from PyQt6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QTextEdit, QGridLayout,
                           QTabWidget, QWidget, QMessageBox, QRadioButton)
from PyQt6.QtCore import Qt

# Import app modules
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder

class JsonVsFolderTester(QDialog):
    """Test harness specifically for JSON file vs folder conflicts"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JSON vs Folder Conflict Tester")
        self.setMinimumSize(800, 600)
        
        # Create managers
        self.template_manager = TemplateManager()
        self.project_builder = ProjectBuilder(self.template_manager)
        
        # Setup UI
        self.init_ui()
        
        # Track test state
        self.temp_dir = None
        self.current_test_structure = None
        self.current_test_name = None
        
    def init_ui(self):
        """Initialize the test UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("JSON File vs Folder Conflict Test")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # Description
        description = QLabel(
            "This test specifically targets issues with JSON files vs folders with the same name. "
            "It creates various test structures and verifies that files and folders are correctly "
            "detected and created."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Create tab widget for test cases
        self.tabs = QTabWidget()
        
        # Tab 1: Basic Test Cases
        self.basic_tab = QWidget()
        basic_layout = QVBoxLayout(self.basic_tab)
        
        # Test case selection
        test_group = QGridLayout()
        
        # Test case 1
        self.test1_radio = QRadioButton("Test 1: Basic JSON files and folders")
        self.test1_radio.setChecked(True)
        test_group.addWidget(self.test1_radio, 0, 0)
        test1_desc = QLabel("Tests simple JSON files and normal folders")
        test_group.addWidget(test1_desc, 0, 1)
        
        # Test case 2
        self.test2_radio = QRadioButton("Test 2: JSON file and folder with same name")
        test_group.addWidget(self.test2_radio, 1, 0)
        test2_desc = QLabel("Tests a JSON file and folder with identical names")
        test_group.addWidget(test2_desc, 1, 1)
        
        # Test case 3
        self.test3_radio = QRadioButton("Test 3: Multiple JSON file/folder conflicts")
        test_group.addWidget(self.test3_radio, 2, 0)
        test3_desc = QLabel("Tests multiple JSON files and folders with same names in different locations")
        test_group.addWidget(test3_desc, 2, 1)
        
        # Test case 4
        self.test4_radio = QRadioButton("Test 4: Nested JSON file/folder conflicts")
        test_group.addWidget(self.test4_radio, 3, 0)
        test4_desc = QLabel("Tests nested structure with JSON file/folder name conflicts")
        test_group.addWidget(test4_desc, 3, 1)
        
        basic_layout.addLayout(test_group)
        
        # Structure preview
        preview_label = QLabel("Structure Preview:")
        basic_layout.addWidget(preview_label)
        
        self.structure_preview = QTextEdit()
        self.structure_preview.setReadOnly(True)
        self.structure_preview.setMinimumHeight(150)
        basic_layout.addWidget(self.structure_preview)
        
        # Button to update preview
        update_preview_btn = QPushButton("Update Preview")
        update_preview_btn.clicked.connect(self.update_preview)
        basic_layout.addWidget(update_preview_btn)
        
        # Run test button
        run_test_btn = QPushButton("Run Selected Test")
        run_test_btn.clicked.connect(self.run_selected_test)
        basic_layout.addWidget(run_test_btn)
        
        # Tab 2: Structure Editor Test
        self.editor_tab = QWidget()
        editor_layout = QVBoxLayout(self.editor_tab)
        
        editor_desc = QLabel(
            "This test will create the same test structures in the structure editor "
            "and verify that the JSON files and folders are correctly detected and saved."
        )
        editor_desc.setWordWrap(True)
        editor_layout.addWidget(editor_desc)
        
        editor_test_btn = QPushButton("Open Structure Editor Test")
        editor_test_btn.clicked.connect(self.open_structure_editor_test)
        editor_layout.addWidget(editor_test_btn)
        
        # Tab 3: Project Creation Test
        self.project_tab = QWidget()
        project_layout = QVBoxLayout(self.project_tab)
        
        project_desc = QLabel(
            "This test will create actual projects from the test structures and "
            "verify that the JSON files and folders are correctly created."
        )
        project_desc.setWordWrap(True)
        project_layout.addWidget(project_desc)
        
        project_test_btn = QPushButton("Create Test Project")
        project_test_btn.clicked.connect(self.create_test_project)
        project_layout.addWidget(project_test_btn)
        
        # Add tabs to tab widget
        self.tabs.addTab(self.basic_tab, "Basic Tests")
        self.tabs.addTab(self.editor_tab, "Editor Test")
        self.tabs.addTab(self.project_tab, "Project Test")
        
        layout.addWidget(self.tabs)
        
        # Results area
        results_label = QLabel("Test Results:")
        layout.addWidget(results_label)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
        # Bottom buttons
        btn_layout = QHBoxLayout()
        
        run_all_btn = QPushButton("Run All Tests")
        run_all_btn.clicked.connect(self.run_all_tests)
        btn_layout.addWidget(run_all_btn)
        
        clear_btn = QPushButton("Clear Results")
        clear_btn.clicked.connect(self.clear_results)
        btn_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # Connect radio buttons to update preview
        self.test1_radio.toggled.connect(self.update_preview)
        self.test2_radio.toggled.connect(self.update_preview)
        self.test3_radio.toggled.connect(self.update_preview)
        self.test4_radio.toggled.connect(self.update_preview)
        
        # Update the preview initially
        self.update_preview()
        
    def log_result(self, message, is_error=False):
        """Log a test result"""
        timestamp = time.strftime("%H:%M:%S")
        if is_error:
            formatted_msg = f"[{timestamp}] ERROR: {message}"
        else:
            formatted_msg = f"[{timestamp}] {message}"
            
        self.results_text.append(formatted_msg)
        print(formatted_msg)
        
        # Scroll to bottom
        self.results_text.moveCursor(self.results_text.textCursor().End)
        
        # Process events to update UI
        QApplication.processEvents()
    
    def clear_results(self):
        """Clear test results"""
        self.results_text.clear()
    
    def get_current_test_structure(self):
        """Get the structure for the selected test"""
        if self.test1_radio.isChecked():
            # Simple structure with JSON files and normal folders
            return [
                "README.md",
                {"src": [
                    "index.js",
                    "app.js",
                    "config.json"
                ]},
                "package.json",
                "tsconfig.json",
                {"data": [
                    "sample.json",
                    "info.txt"
                ]}
            ]
        elif self.test2_radio.isChecked():
            # JSON file and folder with same name
            return [
                "config.json",
                {"config.json": [
                    "settings.json",
                    "defaults.json"
                ]},
                "README.md"
            ]
        elif self.test3_radio.isChecked():
            # Multiple JSON file/folder conflicts
            return [
                "config.json",
                {"config.json": [
                    "settings.json",
                    "defaults.json"
                ]},
                "data.json",
                {"data.json": [
                    "records.json",
                    "schema.json"
                ]},
                "package.json",
                {"assets": [
                    "config.json",
                    {"config.json": [
                        "theme.json"
                    ]}
                ]}
            ]
        else:  # test4_radio
            # Nested structure with JSON file/folder conflicts
            return [
                "package.json",
                {"src": [
                    "index.js",
                    {"components": [
                        "App.js",
                        "config.json",
                        {"config.json": [
                            "theme.json",
                            "routes.json"
                        ]}
                    ]},
                    {"utils": [
                        "helpers.js",
                        "data.json"
                    ]}
                ]},
                {"config.json": [
                    "settings.json",
                    "defaults.json"
                ]},
                "config.json",
                "tsconfig.json"
            ]
    
    def update_preview(self):
        """Update the structure preview"""
        structure = self.get_current_test_structure()
        self.current_test_structure = structure
        
        # Format as JSON for display
        json_str = json.dumps(structure, indent=2)
        self.structure_preview.setText(json_str)
        
        # Store the test name
        if self.test1_radio.isChecked():
            self.current_test_name = "basic_json"
        elif self.test2_radio.isChecked():
            self.current_test_name = "same_name"
        elif self.test3_radio.isChecked():
            self.current_test_name = "multiple_conflicts"
        else:
            self.current_test_name = "nested_conflicts"
    
    def run_selected_test(self):
        """Run the selected test"""
        # Get the current structure
        self.update_preview()
        
        # Log the test start
        self.log_result(f"Starting test: {self.current_test_name}")
        
        # Create a temporary directory
        self.create_temp_dir()
        
        # Create the test structure in the template manager
        self.create_test_structure()
        
        # Show the structure preview
        self.show_structure_preview()
        
        # Create a test project
        self.create_project_from_structure()
        
        # Verify the project structure
        self.verify_project_structure()
        
        # Clean up
        self.clean_up()
        
        self.log_result(f"Test {self.current_test_name} completed")
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.clear_results()
        self.log_result("Starting all tests...")
        
        # Run each test
        self.test1_radio.setChecked(True)
        self.run_selected_test()
        
        self.test2_radio.setChecked(True)
        self.run_selected_test()
        
        self.test3_radio.setChecked(True)
        self.run_selected_test()
        
        self.test4_radio.setChecked(True)
        self.run_selected_test()
        
        self.log_result("All tests completed")
    
    def open_structure_editor_test(self):
        """Open the structure editor with the selected test structure"""
        from app.ui.structure_editor_enhanced import EnhancedStructureEditor
        
        # Get the current structure
        self.update_preview()
        
        # Create a unique name for the test
        structure_name = f"test_{self.current_test_name}_{int(time.time())}"
        
        # Save the structure first
        success = self.template_manager.save_custom_structure(structure_name, self.current_test_structure)
        if not success:
            self.log_result("Failed to create test structure", True)
            return
        
        # Open the structure in the editor
        try:
            self.log_result(f"Opening structure '{structure_name}' in editor")
            editor = EnhancedStructureEditor(
                self,
                structure_name=structure_name,
                structure=self.current_test_structure
            )
            editor.show()
        except Exception as e:
            self.log_result(f"Error opening structure editor: {e}", True)
    
    def create_test_project(self):
        """Create a test project from the selected structure"""
        # Get the current structure
        self.update_preview()
        
        # Create a temporary directory
        self.create_temp_dir()
        
        # Create the test structure in the template manager
        self.create_test_structure()
        
        # Create a project from the structure
        self.create_project_from_structure()
        
        # Open the project folder
        self.open_project_folder()
    
    def create_temp_dir(self):
        """Create a temporary directory for tests"""
        try:
            # Clean up existing temp dir if it exists
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                
            # Create a new temp dir
            self.temp_dir = tempfile.mkdtemp()
            self.log_result(f"Created temporary directory at: {self.temp_dir}")
            return True
        except Exception as e:
            self.log_result(f"Error creating temporary directory: {e}", True)
            return False
    
    def create_test_structure(self):
        """Create the test structure in the template manager"""
        try:
            # Create a unique name for the test
            structure_name = f"test_{self.current_test_name}_{int(time.time())}"
            
            # Save the structure
            success = self.template_manager.save_custom_structure(structure_name, self.current_test_structure)
            if success:
                self.log_result(f"Created test structure: {structure_name}")
                self.current_test_name = structure_name
                return True
            else:
                self.log_result("Failed to create test structure", True)
                return False
        except Exception as e:
            self.log_result(f"Error creating test structure: {e}", True)
            return False
    
    def show_structure_preview(self):
        """Show a simple structure preview dialog"""
        try:
            self.log_result("Showing structure preview")
            
            # Create a simple preview dialog
            preview_dialog = QDialog(self)
            preview_dialog.setWindowTitle("Structure Preview")
            preview_dialog.setMinimumSize(500, 400)
            
            layout = QVBoxLayout(preview_dialog)
            
            # Title
            title = QLabel(f"Preview of Structure: {self.current_test_name}")
            title.setStyleSheet("font-size: 14px; font-weight: bold;")
            layout.addWidget(title)
            
            # Structure content
            content = QTextEdit()
            content.setReadOnly(True)
            content.setText(json.dumps(self.current_test_structure, indent=2))
            layout.addWidget(content)
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(preview_dialog.accept)
            layout.addWidget(close_btn)
            
            # Show the dialog
            preview_dialog.exec()
            return True
        except Exception as e:
            self.log_result(f"Error showing structure preview: {e}", True)
            return False
    
    def create_project_from_structure(self):
        """Create a test project from the structure"""
        try:
            # Create a project name
            project_name = f"test_project_{int(time.time())}"
            
            # Create the project
            self.log_result(f"Creating project '{project_name}' with structure '{self.current_test_name}'")
            success, message = self.project_builder.create_project(
                project_name=project_name,
                output_dir=self.temp_dir,
                structure_name=self.current_test_name
            )
            
            if success:
                self.log_result(f"Project created successfully: {os.path.join(self.temp_dir, project_name)}")
                return True
            else:
                self.log_result(f"Failed to create project: {message}", True)
                return False
        except Exception as e:
            self.log_result(f"Error creating project: {e}", True)
            return False
    
    def verify_project_structure(self):
        """Verify the created project structure"""
        try:
            # Find the project directory
            project_dir = None
            for item in os.listdir(self.temp_dir):
                if os.path.isdir(os.path.join(self.temp_dir, item)):
                    project_dir = os.path.join(self.temp_dir, item)
                    break
            
            if not project_dir:
                self.log_result("No project directory found", True)
                return False
            
            # Print the project structure
            self.log_result("\nVerifying project structure:")
            self.log_result("Directory structure:")
            
            # Walk through the directory and log what was found
            for root, dirs, files in os.walk(project_dir):
                rel_path = os.path.relpath(root, project_dir)
                if rel_path == '.':
                    self.log_result("\nRoot directory contains:")
                    
                    # Check each directory
                    for dir_name in dirs:
                        self.log_result(f"  Directory: {dir_name}")
                    
                    # Check each file
                    for file_name in files:
                        self.log_result(f"  File: {file_name}")
                        
                        # Specifically verify JSON files in the root
                        if file_name.endswith('.json'):
                            self.log_result(f"    Verified JSON file: {file_name}")
                else:
                    self.log_result(f"\nSubdirectory {rel_path} contains:")
                    
                    # Check each directory
                    for dir_name in dirs:
                        self.log_result(f"  Directory: {os.path.join(rel_path, dir_name)}")
                    
                    # Check each file
                    for file_name in files:
                        self.log_result(f"  File: {os.path.join(rel_path, file_name)}")
            
            # Perform specific verification for the test case
            if self.test2_radio.isChecked() or self.test3_radio.isChecked():
                # Verify that both config.json file and folder exist
                file_path = os.path.join(project_dir, "config.json")
                folder_path = os.path.join(project_dir, "config.json_folder")
                
                if os.path.isfile(file_path):
                    self.log_result("\nSUCCESS: config.json file exists")
                else:
                    self.log_result("\nFAILURE: config.json file does not exist", True)
                
                if os.path.isdir(folder_path):
                    self.log_result("SUCCESS: config.json_folder exists")
                else:
                    self.log_result("FAILURE: config.json_folder does not exist", True)
            
            # Special verification for nested conflicts test
            elif self.test4_radio.isChecked():
                # Verify that config_file.json and config.json folder exist in root
                file_path = os.path.join(project_dir, "config_file.json")
                folder_path = os.path.join(project_dir, "config.json")
                
                if os.path.isfile(file_path):
                    self.log_result("\nSUCCESS: config_file.json exists")
                else:
                    self.log_result("\nFAILURE: config_file.json does not exist", True)
                
                if os.path.isdir(folder_path):
                    self.log_result("SUCCESS: config.json directory exists")
                else:
                    self.log_result("FAILURE: config.json directory does not exist", True)
            
            return True
        except Exception as e:
            self.log_result(f"Error verifying project structure: {e}", True)
            return False
    
    def open_project_folder(self):
        """Open the project folder in file explorer"""
        try:
            # Find the project directory
            project_dir = None
            for item in os.listdir(self.temp_dir):
                if os.path.isdir(os.path.join(self.temp_dir, item)):
                    project_dir = os.path.join(self.temp_dir, item)
                    break
            
            if not project_dir:
                self.log_result("No project directory found", True)
                return False
            
            # Open the folder
            self.log_result(f"Opening project folder: {project_dir}")
            
            if sys.platform == 'darwin':  # macOS
                os.system(f"open '{project_dir}'")
            elif sys.platform == 'win32':  # Windows
                os.system(f'explorer "{project_dir}"')
            else:  # Linux and other
                os.system(f"xdg-open '{project_dir}'")
                
            return True
        except Exception as e:
            self.log_result(f"Error opening project folder: {e}", True)
            return False
    
    def clean_up(self):
        """Clean up temporary files and directories"""
        try:
            # Don't clean up temp directory yet, as we might want to inspect it
            # Just log that we'll clean it up on exit
            self.log_result("Temporary files will be cleaned up when the application exits")
            return True
        except Exception as e:
            self.log_result(f"Error during cleanup: {e}", True)
            return False
    
    def closeEvent(self, event):
        """Clean up when the dialog is closed"""
        try:
            # Clean up temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            print(f"Error cleaning up: {e}")
        
        super().closeEvent(event)

def run_tests():
    """Run the test suite"""
    app = QApplication.instance() or QApplication(sys.argv)
    tester = JsonVsFolderTester()
    tester.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_tests() 
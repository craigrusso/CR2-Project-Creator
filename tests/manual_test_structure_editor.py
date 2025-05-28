#!/usr/bin/env python3
"""
Manual test script for the Structure Editor.
This script creates a structure editor dialog and allows you to interact with it directly.
"""

import os
import sys
import tempfile
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel
from PyQt6.QtCore import Qt

from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.templates.template_operations import TemplateOperations

class StructureEditorTestHarness(QWidget):
    """Test harness for the structure editor"""
    
    def __init__(self):
        super().__init__()
        
        # Create a temporary directory for test structures
        self.temp_dir = tempfile.mkdtemp()
        
        # Set up UI
        self.init_ui()
        
        # Sample structure for testing
        self.sample_structure = [
            {"name": "Folder 1", "type": "folder", "children": [
                {"name": "Subfolder 1", "type": "folder", "children": []},
                {"name": "File 1.txt", "type": "file"}
            ]},
            {"name": "File 2.txt", "type": "file", "use_project_name": True},
            {"name": "Folder 2", "type": "folder", "children": []}
        ]
        
        # Create mock template manager
        self.template_manager = self.create_mock_template_manager()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Structure Editor Test Harness")
        self.setGeometry(100, 100, 600, 400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add instructions
        instructions = QLabel("This test harness allows you to test the structure editor functionality.\n"
                             "Use the buttons below to create different editor instances.")
        layout.addWidget(instructions)
        
        # Add buttons
        new_editor_btn = QPushButton("New Structure Editor")
        new_editor_btn.clicked.connect(self.create_new_editor)
        layout.addWidget(new_editor_btn)
        
        edit_existing_btn = QPushButton("Edit Existing Structure")
        edit_existing_btn.clicked.connect(self.edit_existing_structure)
        layout.addWidget(edit_existing_btn)
        
        # Add log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        
        # Add quit button
        quit_btn = QPushButton("Quit")
        quit_btn.clicked.connect(self.close)
        layout.addWidget(quit_btn)
        
    def log(self, message):
        """Log a message to the log area"""
        self.log_area.append(message)
        print(message)
        
    def create_mock_template_manager(self):
        """Create a mock template manager for testing"""
        template_ops = TemplateOperations()
        
        # Set up the paths
        template_ops.paths = {
            "structures_dir": self.temp_dir,
            "templates_dir": self.temp_dir,
            "custom_structures_dir": self.temp_dir
        }
        
        # Set up preferences
        template_ops.preferences = {
            "categories": ["Category 1", "Category 2", "Category 3"]
        }
        
        # Create a sample structure and template file
        test_structure = self.sample_structure
        test_template_info = {
            "name": "Test Template",
            "description": "This is a test template",
            "tags": ["test", "template", "example"],
            "category": "Category 1",
            "folder": "Default"
        }
        
        # Save the sample structure and template info to files
        try:
            with open(os.path.join(self.temp_dir, "Test_Template.json"), 'w') as f:
                json.dump(test_structure, f, indent=2)
            
            with open(os.path.join(self.temp_dir, "Template_Test_Template.json"), 'w') as f:
                json.dump(test_template_info, f, indent=2)
                
            self.log(f"Created sample files in {self.temp_dir}")
        except Exception as e:
            self.log(f"Error creating sample files: {e}")
        
        # Initialize the custom_structures attribute
        template_ops.custom_structures = {}
        template_ops.custom_structures["Test_Template"] = {
            "name": "Test_Template",
            "directories": test_structure,
            "created": "2023-01-01T00:00:00"
        }
        
        # Add get_template_info method to the template_ops object
        def get_template_info(template_name):
            self.log(f"Getting template info for: {template_name}")
            if template_name == "Test_Template" or template_name == "Test Template":
                return test_template_info
            
            # Try to load from disk
            template_file = os.path.join(self.temp_dir, f"Template_{template_name.replace(' ', '_')}.json")
            if os.path.exists(template_file):
                try:
                    with open(template_file, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    self.log(f"Error loading template info: {e}")
            
            # Return default if not found
            return {
                "name": template_name,
                "description": "Default template description",
                "tags": ["default"],
                "category": "Category 1",
                "folder": "Default"
            }
            
        template_ops.get_template_info = get_template_info
        
        # Add save_custom_structure method to correctly handle structure saving
        def save_custom_structure(name, structure):
            self.log(f"Saving custom structure: {name}")
            try:
                # Format the structure data correctly
                structure_data = {
                    "name": name,
                    "directories": structure,
                    "created": "2023-01-01T00:00:00"
                }
                
                # Save to memory
                template_ops.custom_structures[name] = structure_data
                
                # Save to file
                sanitized_name = name.replace(' ', '_').replace('/', '-').replace('\\', '-')
                file_path = os.path.join(self.temp_dir, f"{sanitized_name}.json")
                with open(file_path, 'w') as f:
                    json.dump(structure_data, f, indent=2)
                
                self.log(f"Successfully saved structure to {file_path}")
                return True
            except Exception as e:
                self.log(f"Error saving custom structure: {e}")
                return False
                
        template_ops.save_custom_structure = save_custom_structure
        
        # Add get_structure method to retrieve structures
        def get_structure(name):
            self.log(f"Getting structure: {name}")
            if name in template_ops.custom_structures:
                return template_ops.custom_structures[name].get("directories", [])
            
            # Try with and without underscore
            sanitized_name = name.replace(' ', '_')
            if sanitized_name in template_ops.custom_structures:
                return template_ops.custom_structures[sanitized_name].get("directories", [])
                
            # Try with Template_ prefix
            if not name.startswith("Template_"):
                template_name = f"Template_{name}"
                if template_name in template_ops.custom_structures:
                    return template_ops.custom_structures[template_name].get("directories", [])
                    
            # Try loading from file
            file_path = os.path.join(self.temp_dir, f"{name.replace(' ', '_')}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    if isinstance(data, dict) and "directories" in data:
                        return data["directories"]
                    return data
                except Exception as e:
                    self.log(f"Error loading structure file: {e}")
            
            return self.sample_structure
            
        template_ops.get_structure = get_structure
        
        # Add save_template_info method
        def save_template_info(name, info):
            self.log(f"Saving template info: {name}")
            try:
                # Save to file
                sanitized_name = name.replace(' ', '_').replace('/', '-').replace('\\', '-')
                file_path = os.path.join(self.temp_dir, f"Template_{sanitized_name}.json")
                with open(file_path, 'w') as f:
                    json.dump(info, f, indent=2)
                
                self.log(f"Successfully saved template info to {file_path}")
                return True
            except Exception as e:
                self.log(f"Error saving template info: {e}")
                return False
                
        template_ops.save_template_info = save_template_info
        
        return template_ops
        
    def create_new_editor(self):
        """Create a new structure editor"""
        self.log("Creating new structure editor...")
        try:
            editor = EnhancedStructureEditor(
                self,
                structure_name=None,
                structure=None,
                is_new=True
            )
            
            # Set the template manager on the editor
            editor.template_manager = self.template_manager
            
            result = editor.exec()
            self.log(f"Editor closed with result: {result}")
            
            if result == 1:  # Accepted
                self.log("Structure saved successfully")
            else:
                self.log("Structure editing cancelled")
                
        except Exception as e:
            self.log(f"Error creating editor: {e}")
            import traceback
            self.log(traceback.format_exc())
            
    def edit_existing_structure(self):
        """Edit an existing structure"""
        self.log("Editing existing structure...")
        try:
            # Create a structure editor with existing structure
            editor = EnhancedStructureEditor(
                self,
                structure_name="Test_Template",
                structure=self.sample_structure
            )
            
            # Set the template manager on the editor
            editor.template_manager = self.template_manager
            
            # Special case: manually set the template name since it's coming from a test
            if hasattr(editor, 'name_input') and editor.name_input:
                editor.name_input.setText("Test Template")
                
            result = editor.exec()
            self.log(f"Editor closed with result: {result}")
            
            if result == 1:  # Accepted
                self.log("Structure saved successfully")
            else:
                self.log("Structure editing cancelled")
                
        except Exception as e:
            self.log(f"Error editing structure: {e}")
            import traceback
            self.log(traceback.format_exc())

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    test_harness = StructureEditorTestHarness()
    test_harness.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
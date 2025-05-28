#!/usr/bin/env python3
# Test script for debugging template editing functionality

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import required modules
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
from PyQt6.QtCore import Qt

from app.templates.template_operations import TemplateOperations
from app.ui.structure_editor_enhanced import show_enhanced_structure_editor
from app.templates.template_manager import TemplateManager

class MockMainWindow(QMainWindow):
    """Mock main window to host the template editor"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Template Editor Test")
        self.resize(800, 600)
        
        # Create a central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create a layout
        layout = QVBoxLayout(central_widget)
        
        # Create test environment
        self.temp_dir = tempfile.mkdtemp()
        print(f"Created temporary directory: {self.temp_dir}")
        
        # Create template directories
        self.structures_dir = os.path.join(self.temp_dir, "structures")
        self.templates_dir = os.path.join(self.temp_dir, "templates")
        self.custom_structures_dir = os.path.join(self.temp_dir, "custom_structures")
        
        os.makedirs(self.structures_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.custom_structures_dir, exist_ok=True)
        
        # Create test buttons
        self.create_template_btn = QPushButton("Create Test Template")
        self.create_template_btn.clicked.connect(self.create_test_template)
        layout.addWidget(self.create_template_btn)
        
        self.edit_template_btn = QPushButton("Edit Test Template")
        self.edit_template_btn.clicked.connect(self.edit_test_template)
        layout.addWidget(self.edit_template_btn)
        
        self.check_template_btn = QPushButton("Check Template Structure")
        self.check_template_btn.clicked.connect(self.check_template_structure)
        layout.addWidget(self.check_template_btn)
        
        # Initialize template manager
        self.template_manager = self.create_template_manager()
        
        # Store sample structure for comparison
        self.sample_structure = [
            {"type": "folder", "name": "Project Root", "children": [
                {"type": "folder", "name": "Assets", "children": []},
                {"type": "folder", "name": "Source", "children": [
                    {"type": "file", "name": "main.py"}
                ]}
            ]}
        ]
    
    def create_template_manager(self):
        """Create a template manager with test data"""
        # Create a custom TemplateManager that tracks operations
        class DebugTemplateManager(TemplateManager):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                print("DEBUG: Initialized TemplateManager")
                self.custom_structures = {}
                
            def get_structure(self, structure_name):
                print(f"DEBUG: get_structure called with: {structure_name}")
                
                # Skip template_ops and use our direct implementation
                # Direct custom structures lookup
                if hasattr(self, 'custom_structures') and structure_name in self.custom_structures:
                    print(f"DEBUG: Found structure in custom_structures dict")
                    return self.custom_structures[structure_name]
                
                # Try to load from disk
                custom_path = os.path.join(self.custom_structures_dir, f"{structure_name}.json")
                if os.path.exists(custom_path):
                    try:
                        with open(custom_path, 'r') as f:
                            data = json.load(f)
                            print(f"DEBUG: Loaded structure from disk: {custom_path}")
                            # Store in memory for future use
                            if hasattr(self, 'custom_structures'):
                                self.custom_structures[structure_name] = data
                            return data
                    except Exception as e:
                        print(f"ERROR: Failed to load structure from {custom_path}: {e}")
                
                # If we still couldn't find it, try template_ops as a last resort
                if hasattr(self, 'template_ops') and hasattr(self.template_ops, 'get_structure'):
                    try:
                        structure = self.template_ops.get_structure(structure_name)
                        print(f"DEBUG: get_structure from template_ops returned: {structure is not None}")
                        return structure
                    except Exception as e:
                        print(f"ERROR: Failed to get structure from template_ops: {e}")
                
                print(f"DEBUG: No structure found for {structure_name}")
                return None
                
            def save_custom_structure(self, name, structure):
                print(f"DEBUG: save_custom_structure called with name: {name}")
                print(f"DEBUG: Structure type: {type(structure)}")
                
                # Store in memory
                if not hasattr(self, 'custom_structures'):
                    self.custom_structures = {}
                self.custom_structures[name] = structure
                
                # Save to disk
                try:
                    file_path = os.path.join(self.custom_structures_dir, f"{name}.json")
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w') as f:
                        json.dump(structure, f, indent=2)
                    print(f"DEBUG: Saved structure to {file_path}")
                    return True
                except Exception as e:
                    print(f"ERROR: Failed to save structure: {e}")
                    return False
                
            def get_template_info(self, template_name):
                print(f"DEBUG: get_template_info called with: {template_name}")
                
                # Check if we have this template in memory
                if hasattr(self, 'templates') and template_name in self.templates:
                    print(f"DEBUG: Found template info in templates dict")
                    return self.templates[template_name]
                
                # Check if template_ops has this method
                if hasattr(self, 'template_ops') and hasattr(self.template_ops, 'get_template_info'):
                    info = self.template_ops.get_template_info(template_name)
                    if info:
                        print(f"DEBUG: Found template info via template_ops")
                        return info
                
                # Try to load from disk
                template_path = os.path.join(self.templates_dir, f"{template_name}.json")
                if os.path.exists(template_path):
                    try:
                        with open(template_path, 'r') as f:
                            data = json.load(f)
                            print(f"DEBUG: Loaded template info from disk: {template_path}")
                            return data
                    except Exception as e:
                        print(f"ERROR: Failed to load template info from {template_path}: {e}")
                
                print(f"DEBUG: No template info found for {template_name}")
                return {"name": template_name, "description": "", "category": "Custom"}
        
        # Create template manager instance
        template_manager = DebugTemplateManager()
        template_manager.structures_dir = self.structures_dir
        template_manager.templates_dir = self.templates_dir
        template_manager.custom_structures_dir = self.custom_structures_dir
        
        # Set up template operations - initialize first, then modify paths
        template_manager.template_ops = TemplateOperations()
        
        # Update paths in the template_ops object
        if hasattr(template_manager.template_ops, 'paths'):
            template_manager.template_ops.paths["structures_dir"] = self.structures_dir
            template_manager.template_ops.paths["templates_dir"] = self.templates_dir
            template_manager.template_ops.paths["custom_structures_dir"] = self.custom_structures_dir
        
        # Initialize custom_structures attribute in template_ops if it doesn't exist
        if hasattr(template_manager.template_ops, 'custom_structures'):
            # If it exists, copy our structures to it
            for name, structure in template_manager.custom_structures.items():
                template_manager.template_ops.custom_structures[name] = structure
        else:
            # If it doesn't exist, create it
            template_manager.template_ops.custom_structures = {}
        
        print(f"DEBUG: Initialized template manager with directories:")
        print(f"  - structures_dir: {self.structures_dir}")
        print(f"  - templates_dir: {self.templates_dir}")
        print(f"  - custom_structures_dir: {self.custom_structures_dir}")
        
        return template_manager
    
    def create_test_template(self):
        """Create a test template with a basic structure"""
        print("\n=== Creating Test Template ===")
        
        # Template details
        template_name = "Test_Template"
        structure_name = "Template_Test_Template"
        
        # Create a basic structure
        structure = self.sample_structure.copy()
        
        # Save the structure
        saved = self.template_manager.save_custom_structure(structure_name, structure)
        
        # Create template info
        template_info = {
            "name": template_name,
            "description": "Test template for debugging",
            "category": "Test",
            "tags": ["test"]
        }
        
        # Save template info
        template_info_path = os.path.join(self.templates_dir, f"{template_name}.json")
        os.makedirs(os.path.dirname(template_info_path), exist_ok=True)
        with open(template_info_path, 'w') as f:
            json.dump(template_info, f, indent=2)
        
        # Store in manager's templates dict/list
        if not hasattr(self.template_manager, 'templates'):
            self.template_manager.templates = {}  # Initialize as dict for our test
            
        # Check if templates is a list or dict and handle accordingly
        if isinstance(self.template_manager.templates, list):
            # For list, add the template_info dictionary
            # First remove any existing template with the same name
            self.template_manager.templates = [t for t in self.template_manager.templates if t.get('name') != template_name]
            # Now add the new template info
            self.template_manager.templates.append(template_info)
        else:
            # For dict, add with template_name as key
            self.template_manager.templates[template_name] = template_info
        
        print(f"Created test template: {template_name}")
        print(f"Created structure: {structure_name}")
        print(f"Structure saved: {saved}")
        
        # Show success message
        QMessageBox.information(self, "Success", f"Test template '{template_name}' created successfully.")
    
    def edit_test_template(self):
        """Open the enhanced structure editor to edit the test template"""
        print("\n=== Editing Test Template ===")
        
        template_name = "Test_Template"
        structure_name = "Template_Test_Template"
        
        # Verify structure exists
        structure = self.template_manager.get_structure(structure_name)
        
        print(f"Structure found for editing: {structure is not None}")
        if structure:
            print(f"Structure content type: {type(structure)}")
            print(f"Structure content (first level): {json.dumps(structure[0] if isinstance(structure, list) and structure else structure, indent=2)}")
        
        # Call the enhanced structure editor
        print(f"DEBUG: Calling show_enhanced_structure_editor with structure_name={structure_name}")
        success, updated_structure, updated_name = show_enhanced_structure_editor(
            self,
            structure_name=structure_name,
            structure=structure,
            is_new=False
        )
        
        print(f"Structure editor result: success={success}, updated_name={updated_name}")
        if success and updated_structure:
            print(f"Updated structure type: {type(updated_structure)}")
            print(f"Updated structure content (first level): {json.dumps(updated_structure[0] if isinstance(updated_structure, list) and updated_structure else updated_structure, indent=2)}")
            
            # Save the updated structure
            if updated_name and updated_name != structure_name:
                # Name changed, save with new name
                print(f"Name changed from {structure_name} to {updated_name}")
                self.template_manager.save_custom_structure(updated_name, updated_structure)
            else:
                # Same name, update existing structure
                self.template_manager.save_custom_structure(structure_name, updated_structure)
            
            QMessageBox.information(self, "Success", "Template edited successfully.")
        else:
            QMessageBox.warning(self, "Canceled", "Template editing was canceled or failed.")
    
    def check_template_structure(self):
        """Check the saved structure for the test template"""
        print("\n=== Checking Template Structure ===")
        
        template_name = "Test_Template"
        structure_name = "Template_Test_Template"
        
        # Try to load the structure directly from disk
        structure_path = os.path.join(self.custom_structures_dir, f"{structure_name}.json")
        disk_structure = None
        
        if os.path.exists(structure_path):
            try:
                with open(structure_path, 'r') as f:
                    disk_structure = json.load(f)
                print(f"Structure loaded from disk: {structure_path}")
                print(f"Structure content type: {type(disk_structure)}")
                print(f"Structure content (first level): {json.dumps(disk_structure[0] if isinstance(disk_structure, list) and disk_structure else disk_structure, indent=2)}")
            except Exception as e:
                print(f"ERROR: Failed to load structure from disk: {e}")
        else:
            print(f"Structure file not found on disk: {structure_path}")
        
        # Also check in-memory structure
        memory_structure = None
        if hasattr(self.template_manager, 'custom_structures') and structure_name in self.template_manager.custom_structures:
            memory_structure = self.template_manager.custom_structures[structure_name]
            print(f"Structure found in memory")
            print(f"Memory structure type: {type(memory_structure)}")
            print(f"Memory structure content (first level): {json.dumps(memory_structure[0] if isinstance(memory_structure, list) and memory_structure else memory_structure, indent=2)}")
        else:
            print(f"Structure not found in memory")
        
        # Load through the get_structure method
        api_structure = self.template_manager.get_structure(structure_name)
        if api_structure:
            print(f"Structure loaded through API")
            print(f"API structure type: {type(api_structure)}")
            print(f"API structure content (first level): {json.dumps(api_structure[0] if isinstance(api_structure, list) and api_structure else api_structure, indent=2)}")
        else:
            print(f"Structure not found through API")
        
        # Show summary in message box
        summary = f"""Structure Check Results:
        
Disk: {"Found" if disk_structure else "Not Found"}
Memory: {"Found" if memory_structure else "Not Found"}
API: {"Found" if api_structure else "Not Found"}
"""
        QMessageBox.information(self, "Structure Check", summary)
    
    def cleanup(self):
        """Clean up temporary directory"""
        try:
            shutil.rmtree(self.temp_dir)
            print(f"Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            print(f"Failed to remove temporary directory: {e}")

def main():
    """Main entry point for the test application"""
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = MockMainWindow()
    window.show()
    
    # Run the application
    result = app.exec()
    
    # Clean up
    window.cleanup()
    
    # Exit
    sys.exit(result)

if __name__ == "__main__":
    main() 
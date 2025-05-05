#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
import json
import tempfile
import shutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.templates.template_manager import TemplateManager
from app.ui.structure_editor_enhanced import EnhancedStructureEditor

class FileFormatTest(QMainWindow):
    """Test to diagnose file vs folder structure issues"""
    
    def __init__(self):
        super().__init__()
        
        # Create a temporary directory for our test
        self.temp_dir = tempfile.mkdtemp()
        self.templates_dir = os.path.join(self.temp_dir, "templates")
        self.custom_structures_dir = os.path.join(self.temp_dir, "custom_structures")
        
        # Create the directories
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.custom_structures_dir, exist_ok=True)
        
        print(f"[DEBUG] Test environment initialized")
        print(f"[DEBUG] Templates dir: {self.templates_dir}")
        print(f"[DEBUG] Custom structures dir: {self.custom_structures_dir}")
        
        # Create the template manager
        self.template_manager = TemplateManager(
            templates_dir=self.templates_dir,
            custom_structures_dir=self.custom_structures_dir
        )
        
        # Set up the UI
        self.setWindowTitle('File Format Test')
        self.setGeometry(100, 100, 800, 600)
        
        # Create a central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create a layout
        self.layout = QVBoxLayout(self.central_widget)
        
        # Create a tree widget for displaying the structure
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Structure Items'])
        self.layout.addWidget(self.tree)
        
        # Create buttons for testing
        self.test_file_structure_btn = QPushButton('Test File Structure Extraction')
        self.test_file_structure_btn.clicked.connect(self.test_file_structure_extraction)
        self.layout.addWidget(self.test_file_structure_btn)
        
        self.test_roundtrip_btn = QPushButton('Test Roundtrip Structure')
        self.test_roundtrip_btn.clicked.connect(self.test_roundtrip_structure)
        self.layout.addWidget(self.test_roundtrip_btn)
    
    def closeEvent(self, event):
        """Clean up on close"""
        print(f"[DEBUG] Cleaning up test environment...")
        # Remove the temporary directory
        try:
            shutil.rmtree(self.temp_dir)
            print(f"[DEBUG] Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            print(f"[ERROR] Could not remove temporary directory: {e}")
        
        super().closeEvent(event)
    
    def create_test_structure(self):
        """Create a test structure with both files and folders"""
        structure = [
            {
                "name": "Footage", 
                "type": "folder", 
                "children": [
                    {
                        "name": "Camera_A",
                        "type": "folder",
                        "children": []
                    },
                    {
                        "name": "test_video.mp4",
                        "type": "file"
                    }
                ]
            },
            {
                "name": "Project_Files",
                "type": "folder",
                "children": [
                    {
                        "name": "project.prproj",
                        "type": "file",
                        "use_project_name": True
                    }
                ]
            },
            {
                "name": "README.txt",
                "type": "file"
            }
        ]
        return structure
    
    def create_structure_with_files_and_paths(self):
        """Create a structure with files that have paths"""
        structure = [
            {
                "name": "Footage", 
                "type": "folder", 
                "children": [
                    {
                        "name": "Camera_A",
                        "type": "folder",
                        "children": []
                    },
                    {
                        "name": "test_video.mp4",
                        "type": "file",
                        "path": "/path/to/test_video.mp4"
                    }
                ]
            },
            {
                "name": "Project_Files",
                "type": "folder",
                "children": [
                    {
                        "name": "project.prproj",
                        "type": "file",
                        "use_project_name": True,
                        "path": "/path/to/project.prproj"
                    }
                ]
            }
        ]
        return structure
    
    def display_structure(self, structure):
        """Display a structure in the tree widget"""
        self.tree.clear()
        
        # Create root item
        root_item = QTreeWidgetItem(self.tree, ["Project Root"])
        root_item.setExpanded(True)
        
        # Add structure items to the tree
        for item in structure:
            self._add_structure_item(root_item, item)
        
        # Expand all items
        self.tree.expandAll()
    
    def _add_structure_item(self, parent, item_data):
        """Add a structure item to the tree"""
        if isinstance(item_data, dict):
            # Handle dictionary item
            if "name" in item_data and "type" in item_data:
                name = item_data["name"]
                item_type = item_data["type"]
                
                # Create tree item
                tree_item = QTreeWidgetItem(parent, [f"{name} ({item_type})"])
                
                # Add additional attributes
                for key, value in item_data.items():
                    if key not in ["name", "type", "children"]:
                        QTreeWidgetItem(tree_item, [f"{key}: {value}"])
                
                # Add children
                if "children" in item_data and isinstance(item_data["children"], list):
                    for child in item_data["children"]:
                        self._add_structure_item(tree_item, child)
            
            elif len(item_data) == 1:
                # Old format: {"folder_name": [children]}
                folder_name = list(item_data.keys())[0]
                children = list(item_data.values())[0]
                
                tree_item = QTreeWidgetItem(parent, [f"{folder_name} (folder)"])
                
                if isinstance(children, list):
                    for child in children:
                        self._add_structure_item(tree_item, child)
        
        elif isinstance(item_data, str):
            # Simple string = filename
            QTreeWidgetItem(parent, [f"{item_data} (file)"])
    
    def test_file_structure_extraction(self):
        """Test the extraction of file structure"""
        print("\n=== Testing File Structure Extraction ===")
        
        # Create a test structure
        structure = self.create_test_structure()
        
        # Display the original structure
        print("[DEBUG] Original structure:")
        print(json.dumps(structure, indent=2))
        self.display_structure(structure)
        
        # Create a template using this structure
        template_name = "Test_File_Structure"
        
        # Save the structure
        structure_path = os.path.join(self.custom_structures_dir, f"{template_name}.json")
        with open(structure_path, 'w') as f:
            json.dump(structure, f, indent=2)
        
        # Save template info
        template_info = {
            "name": template_name,
            "description": "Test template for file structure",
            "tags": ["test"],
            "type": "Standard",
            "structure_name": template_name
        }
        
        template_path = os.path.join(self.templates_dir, f"{template_name}.json")
        with open(template_path, 'w') as f:
            json.dump(template_info, f, indent=2)
        
        print(f"[DEBUG] Saved structure to {structure_path}")
        print(f"[DEBUG] Saved template info to {template_path}")
        
        # Reload the template manager
        self.template_manager.reload_templates()
        
        # Now create an editor with this structure
        editor = EnhancedStructureEditor(
            self,
            structure_name=template_name,
            structure=None,  # Let it load from the template manager
            project_type=None,
            save_callback=None,
            is_new=False
        )
        
        # Get the structure from the editor
        result = editor.get_result()
        retrieved_structure = result['structure']
        
        # Display the retrieved structure
        print("[DEBUG] Retrieved structure:")
        print(json.dumps(retrieved_structure, indent=2))
        
        # Now extract from tree and compare
        tree_structure = editor.extract_structure_from_tree()
        
        print("[DEBUG] Structure extracted from tree:")
        print(json.dumps(tree_structure, indent=2))
        
        # Check for any issues with the structure
        self._check_structure_for_issues(tree_structure)
        
        print("=== File Structure Extraction Test Complete ===\n")
    
    def test_roundtrip_structure(self):
        """Test a full roundtrip of structure save and load"""
        print("\n=== Testing Roundtrip Structure ===")
        
        # Create a test structure with file paths
        structure = self.create_structure_with_files_and_paths()
        
        # Display the original structure
        print("[DEBUG] Original structure with file paths:")
        print(json.dumps(structure, indent=2))
        self.display_structure(structure)
        
        # Create a template using this structure
        template_name = "Test_Roundtrip"
        
        # Save the structure
        structure_path = os.path.join(self.custom_structures_dir, f"{template_name}.json")
        with open(structure_path, 'w') as f:
            json.dump(structure, f, indent=2)
        
        # Save template info
        template_info = {
            "name": template_name,
            "description": "Test template for roundtrip test",
            "tags": ["test"],
            "type": "Standard",
            "structure_name": template_name
        }
        
        template_path = os.path.join(self.templates_dir, f"{template_name}.json")
        with open(template_path, 'w') as f:
            json.dump(template_info, f, indent=2)
        
        print(f"[DEBUG] Saved structure to {structure_path}")
        print(f"[DEBUG] Saved template info to {template_path}")
        
        # Reload the template manager
        self.template_manager.reload_templates()
        
        # First load the structure into an editor
        editor1 = EnhancedStructureEditor(
            self,
            structure_name=template_name,
            structure=None,  # Let it load from the template manager
            project_type=None,
            save_callback=None,
            is_new=False
        )
        
        # Extract structure from the tree
        extracted_structure = editor1.extract_structure_from_tree()
        
        print("[DEBUG] First extraction from tree:")
        print(json.dumps(extracted_structure, indent=2))
        
        # Check for any issues with the structure
        self._check_structure_for_issues(extracted_structure)
        
        # Now create a new editor with the extracted structure
        editor2 = EnhancedStructureEditor(
            self,
            structure_name="Roundtrip_Test_2",
            structure=extracted_structure,
            project_type=None,
            save_callback=None,
            is_new=True
        )
        
        # Extract the structure again
        final_structure = editor2.extract_structure_from_tree()
        
        print("[DEBUG] Second extraction from tree:")
        print(json.dumps(final_structure, indent=2))
        
        # Check for any issues with the structure
        self._check_structure_for_issues(final_structure)
        
        print("=== Roundtrip Structure Test Complete ===\n")
    
    def _check_structure_for_issues(self, structure, path="root"):
        """Check a structure for any issues like list values instead of strings"""
        if isinstance(structure, list):
            # Process each item in the list
            for i, item in enumerate(structure):
                self._check_structure_for_issues(item, f"{path}[{i}]")
        
        elif isinstance(structure, dict):
            # Check each key-value pair in the dictionary
            for key, value in structure.items():
                # Check if the key is a list
                if isinstance(key, list):
                    print(f"[WARNING] Key is a list at {path}: {key}")
                
                # Check if any value that should be a string is a list
                if key in ['name', 'type', 'path'] and isinstance(value, list):
                    print(f"[ERROR] Found list value for '{key}' at {path}: {value}")
                
                # Recurse into nested structures
                if isinstance(value, (dict, list)):
                    self._check_structure_for_issues(value, f"{path}.{key}")
                
                # Check use_project_name is a boolean
                if key == 'use_project_name' and not isinstance(value, bool):
                    print(f"[ERROR] 'use_project_name' is not a boolean at {path}: {value}")
        
        # String values are fine
        elif isinstance(structure, str):
            pass
        
        # Other scalar values are fine
        elif isinstance(structure, (int, float, bool, type(None))):
            pass
        
        else:
            print(f"[WARNING] Unexpected data type at {path}: {type(structure).__name__}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_window = FileFormatTest()
    test_window.show()
    sys.exit(app.exec_()) 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for diagnosing structure saving and loading issues.
This script simulates saving a structure with nested folders and files,
then loading it back to verify the structure is preserved correctly.
"""

import sys
import os
import json
import tempfile
import shutil
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem, QMessageBox

# Create application instance before importing UI components
app = QApplication(sys.argv)

# Import template manager and structure editor
from app.templates.template_manager import TemplateManager
from app.ui.structure_editor.structure_converter import StructureConverter
from app.ui.structure_editor_enhanced import EnhancedStructureEditor

class StructureTester:
    """Class to test structure saving and loading"""
    
    def __init__(self):
        """Initialize the tester"""
        self.manager = TemplateManager()
        self.temp_dir = tempfile.mkdtemp()
        print(f"Test directory: {self.temp_dir}")
        
    def create_test_structure(self):
        """Create a test structure with nested folders and files"""
        # Create a complex nested structure for testing
        structure = [
            {"TopFolder": [
                {"SubFolder1": [
                    {"NestedFolder1": [
                        "nested_file1.txt",
                        "nested_file2.txt"
                    ]},
                    "sub_file1.txt"
                ]},
                {"SubFolder2": [
                    "sub2_file1.txt",
                    "sub2_file2.txt"
                ]},
                "root_file.txt"
            ]}
        ]
        
        return structure
    
    def print_structure(self, structure, indent=0):
        """Print a structure in a readable format"""
        spacing = "  " * indent
        
        if isinstance(structure, list):
            for item in structure:
                self.print_structure(item, indent)
        elif isinstance(structure, dict):
            for folder_name, items in structure.items():
                print(f"{spacing}📁 {folder_name}/")
                self.print_structure(items, indent + 1)
        else:
            print(f"{spacing}📄 {structure}")
    
    def save_and_load_test(self):
        """Test saving and loading a structure"""
        # Create a test structure
        original_structure = self.create_test_structure()
        
        # Structure name for testing
        structure_name = "TestStructure"
        
        print("\n=== ORIGINAL STRUCTURE ===")
        self.print_structure(original_structure)
        
        # Save the structure
        print("\n=== SAVING STRUCTURE ===")
        try:
            success = self.manager.save_custom_structure(structure_name, original_structure)
            if success:
                print(f"Structure saved successfully with name: {structure_name}")
            else:
                print(f"Failed to save structure with name: {structure_name}")
                return False
        except Exception as e:
            print(f"Error saving structure: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Load the structure back
        print("\n=== LOADING SAVED STRUCTURE ===")
        try:
            loaded_structure = self.manager.get_structure(structure_name)
            if loaded_structure:
                print(f"Structure loaded successfully with name: {structure_name}")
                
                print("\n=== LOADED STRUCTURE ===")
                self.print_structure(loaded_structure)
                
                # Compare structures
                print("\n=== COMPARING STRUCTURES ===")
                if self.structures_match(original_structure, loaded_structure):
                    print("✅ Structures match exactly")
                else:
                    print("❌ Structures DO NOT match")
                    print("\n=== STRUCTURE COMPARISON DEBUG ===")
                    self.compare_structures(original_structure, loaded_structure)
            else:
                print(f"Failed to load structure with name: {structure_name}")
                return False
        except Exception as e:
            print(f"Error loading structure: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test loading into an editor
        print("\n=== TESTING EDITOR LOAD ===")
        editor = EnhancedStructureEditor(
            structure_name=structure_name,
            is_new=False
        )
        
        # Instead of showing the editor, just check if the structure is loaded correctly
        if editor.tree_widget:
            # Get the structure from the editor
            converter = StructureConverter(editor.tree_widget)
            editor_structure = converter.create_structure_from_tree()
            
            print("\n=== STRUCTURE FROM EDITOR ===")
            self.print_structure(editor_structure)
            
            # Compare with original
            print("\n=== COMPARING WITH ORIGINAL ===")
            if self.structures_match(original_structure, editor_structure):
                print("✅ Editor structure matches original")
            else:
                print("❌ Editor structure DOES NOT match original")
                print("\n=== EDITOR STRUCTURE COMPARISON DEBUG ===")
                self.compare_structures(original_structure, editor_structure)
                
        return True
    
    def structures_match(self, struct1, struct2):
        """Check if two structures match exactly"""
        # Convert to JSON and back for normalization
        struct1_json = json.dumps(struct1, sort_keys=True)
        struct2_json = json.dumps(struct2, sort_keys=True)
        
        return struct1_json == struct2_json
    
    def compare_structures(self, struct1, struct2, path=""):
        """Compare structures and print differences"""
        # Handle different types
        if type(struct1) != type(struct2):
            print(f"Type mismatch at {path}: {type(struct1)} vs {type(struct2)}")
            return
        
        # Handle lists
        if isinstance(struct1, list):
            if len(struct1) != len(struct2):
                print(f"List length mismatch at {path}: {len(struct1)} vs {len(struct2)}")
                
            # Compare list items
            for i, (item1, item2) in enumerate(zip(struct1, struct2)):
                self.compare_structures(item1, item2, f"{path}[{i}]")
                
            # Check for extra items
            if len(struct1) > len(struct2):
                for i in range(len(struct2), len(struct1)):
                    print(f"Extra item in struct1 at {path}[{i}]: {struct1[i]}")
            elif len(struct2) > len(struct1):
                for i in range(len(struct1), len(struct2)):
                    print(f"Extra item in struct2 at {path}[{i}]: {struct2[i]}")
                    
        # Handle dictionaries
        elif isinstance(struct1, dict):
            # Check keys
            keys1 = set(struct1.keys())
            keys2 = set(struct2.keys())
            
            if keys1 != keys2:
                print(f"Key mismatch at {path}:")
                print(f"  Keys in struct1 but not struct2: {keys1 - keys2}")
                print(f"  Keys in struct2 but not struct1: {keys2 - keys1}")
            
            # Compare common keys
            for key in keys1 & keys2:
                self.compare_structures(struct1[key], struct2[key], f"{path}.{key}")
        
        # Compare primitive values
        elif struct1 != struct2:
            print(f"Value mismatch at {path}: {struct1} vs {struct2}")
    
    def cleanup(self):
        """Clean up test resources"""
        try:
            shutil.rmtree(self.temp_dir)
            print(f"Removed test directory: {self.temp_dir}")
        except Exception as e:
            print(f"Error removing test directory: {e}")

if __name__ == "__main__":
    try:
        tester = StructureTester()
        tester.save_and_load_test()
        tester.cleanup()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 
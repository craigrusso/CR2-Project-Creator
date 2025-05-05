#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test Script for Structure Converter

This script tests the structure conversion functionality to help debug issues
with loading and saving structures.
"""

import os
import sys
import json
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import Qt

# Make sure we can import from app directory
script_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(script_dir)
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.ui.structure_editor.structure_converter import StructureConverter
from app.ui.structure_editor_functions import test_structure_conversion
from app.templates.structure_operations import StructureOperations


def print_separator(title=""):
    """Print a separator line with optional title"""
    width = 80
    if title:
        print(f"\n{'=' * 10} {title} {'=' * (width - 12 - len(title))}")
    else:
        print(f"\n{'=' * width}")


def test_sample_structure():
    """Test with a sample structure"""
    print_separator("TESTING SAMPLE STRUCTURE")
    
    # Create a sample structure
    sample_structure = [
        {"type": "folder", "name": "Project Files", "children": [
            {"type": "file", "name": "project_name.prproj"},
            {"type": "file", "name": "project_name.aep"}
        ]},
        {"type": "folder", "name": "Assets", "children": [
            {"type": "folder", "name": "Images", "children": []},
            {"type": "folder", "name": "Audio", "children": []}
        ]},
        {"type": "folder", "name": "Exports", "children": []}
    ]
    
    # Create app and editor
    app = QApplication.instance() or QApplication(sys.argv)
    editor = EnhancedStructureEditor(structure_name="Test Structure")
    
    # Run the test
    results = test_structure_conversion(editor, sample_structure)
    
    # Display results
    print("\nTEST RESULTS:")
    print(f"Input structure: {results['input']['type']} with {results['input']['length']} items")
    print(f"Normalized structure: {results['normalized']['type']} with {results['normalized']['length']} items")
    print(f"Tree state: {results['tree_state']['top_level_count']} top-level items")
    print(f"Result structure: {results['result']['type']} with {results['result']['length']} items")
    
    # Check if structure was preserved
    if results['input']['length'] == results['result']['length']:
        print("\n✅ SUCCESS: Structure item count preserved")
    else:
        print("\n❌ ERROR: Structure item count changed")
        print(f"  Input: {results['input']['length']} items")
        print(f"  Output: {results['result']['length']} items")
    
    return results


def test_load_save_cycle():
    """Test loading and saving a structure"""
    print_separator("TESTING LOAD-SAVE CYCLE")
    
    # Create app and editor
    app = QApplication.instance() or QApplication(sys.argv)
    editor = EnhancedStructureEditor(structure_name="Test Structure")
    
    # Create a sample structure
    sample_structure = [
        {"Footage": [
            "Raw Files",
            "Processed Files"
        ]},
        {"Audio": [
            "Music",
            "SFX",
            "VO"
        ]},
        {"Assets": [
            "Graphics",
            "Text"
        ]}
    ]
    
    print(f"Initial structure: {sample_structure}")
    
    # 1. Load the structure
    print("\nLoading structure...")
    if hasattr(editor, 'load_structure'):
        result = editor.load_structure(sample_structure)
        print(f"Load result: {result}")
    elif hasattr(editor, 'structure_converter') and editor.structure_converter:
        result = editor.structure_converter.load_structure(sample_structure)
        print(f"Load result via converter: {result}")
    else:
        print("❌ ERROR: No load_structure method available")
        return False
    
    # 2. Get the structure back
    print("\nGetting structure...")
    if hasattr(editor, 'get_structure'):
        result_structure = editor.get_structure()
    elif hasattr(editor, 'structure_converter') and editor.structure_converter:
        result_structure = editor.structure_converter.get_structure()
    else:
        print("❌ ERROR: No get_structure method available")
        return False
    
    print(f"Result structure: {result_structure}")
    
    # 3. Verify the result
    if len(sample_structure) == len(result_structure):
        print("\n✅ SUCCESS: Structure item count preserved")
    else:
        print("\n❌ ERROR: Structure item count changed")
        print(f"  Input: {len(sample_structure)} items")
        print(f"  Output: {len(result_structure)} items")
    
    return result_structure


def test_load_from_file():
    """Test loading a structure from a file"""
    print_separator("TESTING LOAD FROM FILE")
    
    # Initialize structure operations
    structure_ops = StructureOperations()
    
    # Get all available structures
    structures = structure_ops.get_structures()
    print(f"Available structures: {structures}")
    
    if not structures:
        print("No structures available to test")
        return False
    
    # Choose first structure to test
    test_structure_name = structures[0]
    print(f"\nTesting with structure: {test_structure_name}")
    
    # Load the structure
    structure_data = structure_ops.get_structure(test_structure_name)
    
    if not structure_data:
        print(f"❌ ERROR: Could not load structure '{test_structure_name}'")
        return False
    
    print(f"Loaded structure data: {type(structure_data)}")
    if isinstance(structure_data, list):
        print(f"Structure has {len(structure_data)} items")
        if structure_data:
            print(f"First item: {structure_data[0]}")
    
    # Create app and editor
    app = QApplication.instance() or QApplication(sys.argv)
    editor = EnhancedStructureEditor(structure_name=test_structure_name)
    
    # Load the structure into the editor
    if hasattr(editor, 'load_structure'):
        result = editor.load_structure(structure_data)
        print(f"Load result: {result}")
    elif hasattr(editor, 'structure_converter') and editor.structure_converter:
        result = editor.structure_converter.load_structure(structure_data)
        print(f"Load result via converter: {result}")
    else:
        print("❌ ERROR: No load_structure method available")
        return False
    
    # Get the structure back
    if hasattr(editor, 'get_structure'):
        result_structure = editor.get_structure()
    elif hasattr(editor, 'structure_converter') and editor.structure_converter:
        result_structure = editor.structure_converter.get_structure()
    else:
        print("❌ ERROR: No get_structure method available")
        return False
    
    # Verify structure was preserved
    if isinstance(structure_data, list) and isinstance(result_structure, list):
        if len(structure_data) == len(result_structure):
            print("\n✅ SUCCESS: Structure item count preserved")
        else:
            print("\n❌ ERROR: Structure item count changed")
            print(f"  Input: {len(structure_data)} items")
            print(f"  Output: {len(result_structure)} items")
    
    return result_structure


if __name__ == "__main__":
    # Ensure we have a QApplication instance
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Run the tests
    test_sample_structure()
    test_load_save_cycle()
    test_load_from_file()
    
    print("\nAll tests completed. Check results above for any issues.") 
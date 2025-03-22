#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Structure Editor Functions

This module provides functions for working with the enhanced structure editor.
"""

import os
import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QComboBox, QDialog, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QMainWindow, QFileDialog
)

from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.templates.template_manager import TemplateManager


def show_enhanced_structure_editor(
    parent=None,
    structure_name="",
    structure=None,
    is_new=False,
    project_type=None,
    template_name=None,
    focus_name_field=False,
    template_manager=None,
    callback=None
):
    """Show the enhanced structure editor dialog
    
    Args:
        parent: The parent widget
        structure_name: Name of the structure to edit
        structure: The structure data to edit
        is_new: Whether this is a new structure
        project_type: The project type for default structure
        template_name: The template name (optional)
        focus_name_field: Whether to focus the name field
        template_manager: Optional template manager instance
        callback: Optional callback function for when dialog is accepted
        
    Returns:
        tuple: (success, updated_structure, updated_structure_name)
    """
    print(f"🔧 STRUCTURE EDITOR: Showing editor for '{structure_name}' (is_new={is_new})")
    
    # Import EnhancedStructureEditor class
    from app.ui.structure_editor_enhanced import EnhancedStructureEditor
    
    # Create the editor instance
    editor = EnhancedStructureEditor(
        parent=parent,
        structure_name=structure_name,
        is_new=is_new,
        structure=structure,
        project_type=project_type
    )
    
    # If template_name is provided, set it explicitly
    if template_name:
        if hasattr(editor, 'set_template_name'):
            editor.set_template_name(template_name)
    
    # Store template manager reference if provided
    if template_manager:
        editor.template_manager = template_manager
    
    # Ensure we have a valid Template_ prefix
    if structure_name and not structure_name.startswith("Template_"):
        structure_name = f"Template_{structure_name}"
    
    # If template_name is provided, use it as the initial name without Template_ prefix
    initial_name = template_name
    if not initial_name and structure_name and structure_name.startswith("Template_"):
        initial_name = structure_name[9:]  # Remove "Template_" prefix
    
    # Store original template name for rename detection
    original_template_name = initial_name
    
    # Import here to avoid circular imports
    try:
        from app.ui.enhanced_structure_editor import EnhancedStructureEditor
    except ImportError:
        print("❌ STRUCTURE EDITOR: Failed to import EnhancedStructureEditor")
        # Fallback to the default editor (or handle the error)
        return False, None, None, None, None
    
    # Check if the parent is a QWidget
    from PyQt5.QtWidgets import QWidget
    valid_parent = parent if isinstance(parent, QWidget) else None
    if parent is not None and not isinstance(parent, QWidget):
        print(f"⚠️ STRUCTURE EDITOR: Invalid parent type ({type(parent)}), using None instead")
    
    # Load template data and structure from template manager if not provided
    if template_manager and structure_name and not structure:
        # Try to get the structure from the template manager
        print(f"🔧 STRUCTURE EDITOR: Getting structure '{structure_name}' from template manager")
        
        # Try multiple methods to get the structure
        try:
            # First check if there's a template with this name that has a structure
            template = template_manager.get_template_by_name(structure_name)
            if template and isinstance(template, dict) and 'structure' in template and template['structure']:
                structure = template['structure']
                print(f"🔧 STRUCTURE EDITOR: Got structure from template object: {structure is not None}")
            
            # If not found, try to get structure directly
            if not structure and hasattr(template_manager, 'get_structure'):
                structure = template_manager.get_structure(structure_name)
                print(f"🔧 STRUCTURE EDITOR: Got structure using get_structure: {structure is not None}")
                
            # If not found, try custom_structures or other means
            if not structure:
                # Check if there's a template with a structure_name field matching our structure_name
                for template in template_manager.templates:
                    if isinstance(template, dict) and template.get('structure_name') == structure_name:
                        if 'structure' in template and template['structure']:
                            structure = template['structure']
                            print(f"🔧 STRUCTURE EDITOR: Got structure from template with matching structure_name")
                            break
                
                # If still not found and we have a template_name, try that
                if not structure and template_name:
                    template = template_manager.get_template_by_name(template_name)
                    if template and isinstance(template, dict) and 'structure' in template:
                        structure = template['structure']
                        print(f"🔧 STRUCTURE EDITOR: Got structure from template by template_name: {template_name}")
                        
                # Last resort - check custom_structures directly
                if not structure and hasattr(template_manager, 'custom_structures'):
                    if structure_name in template_manager.custom_structures:
                        structure_data = template_manager.custom_structures[structure_name]
                        if isinstance(structure_data, dict) and 'directories' in structure_data:
                            structure = structure_data['directories']
                            print(f"🔧 STRUCTURE EDITOR: Got structure from custom_structures directories field")
                        else:
                            structure = structure_data
                            print(f"🔧 STRUCTURE EDITOR: Got structure from custom_structures directly")
        except Exception as e:
            print(f"❌ STRUCTURE EDITOR: Error loading structure: {e}")
            import traceback
            traceback.print_exc()
            
        if not structure:
            print(f"WARNING: No structure found for {structure_name}")
            structure = []  # Empty structure as fallback
            print(f"DEBUG: Created empty structure")
    
    # Setup the dialog with initial values
    if structure_name:
        # editor.set_structure_name(structure_name)
        # Since editor has no set_structure_name method, use the attribute directly
        editor.original_structure_name = structure_name
        editor.template_name = structure_name
        if structure_name and structure_name.startswith("Template_"):
            editor.template_name = structure_name[len("Template_"):]
    
    if initial_name:
        if hasattr(editor, 'set_template_name'):
            editor.set_template_name(initial_name)
        elif hasattr(editor, 'ui_builder') and hasattr(editor.ui_builder, 'template_name_field'):
            editor.ui_builder.template_name_field.setText(initial_name)
            editor.template_name = initial_name
    
    if structure:
        print(f"🔧 STRUCTURE EDITOR: Loading structure into dialog")
        if hasattr(editor, 'load_structure'):
            editor.load_structure(structure)
        elif hasattr(editor, 'structure_converter') and editor.structure_converter:
            editor.structure_converter.load_structure(structure)
            print(f"🔧 STRUCTURE EDITOR: Loaded structure into converter directly")
        else:
            editor.initial_structure = structure
            print(f"🔧 STRUCTURE EDITOR: Set initial_structure attribute")
    
    # Store original template name
    editor.original_template_name = original_template_name
    
    # Focus the name field if requested
    if focus_name_field and hasattr(editor, 'focus_name_field'):
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, lambda: editor.focus_name_field())
    
    # Connect to template_renamed signal if available
    if template_manager and hasattr(editor, 'template_renamed'):
        editor.template_renamed.connect(
            lambda old_name, new_name: on_template_renamed(template_manager, old_name, new_name)
        )
    
    # Show the dialog and get the result
    result = editor.exec_()
    
    if result == editor.Accepted:
        print(f"🔧 STRUCTURE EDITOR: Dialog accepted")
        
        # Get structure
        if hasattr(editor, 'get_structure'):
            updated_structure = editor.get_structure()
        elif hasattr(editor, 'structure_converter') and editor.structure_converter:
            updated_structure = editor.structure_converter.get_structure()
        else:
            updated_structure = []
        
        # Get structure name
        if hasattr(editor, 'get_structure_name'):
            updated_structure_name = editor.get_structure_name()
        else:
            # Construct the structure name based on template name
            template_name = editor.template_name if hasattr(editor, 'template_name') else ""
            if template_name and not template_name.startswith("Template_"):
                updated_structure_name = f"Template_{template_name}"
            else:
                updated_structure_name = template_name or structure_name
        
        # Get template name
        if hasattr(editor, 'get_template_name'):
            updated_template_name = editor.get_template_name()
        else:
            updated_template_name = editor.template_name if hasattr(editor, 'template_name') else ""
        
        # Check if this was a rename operation
        is_rename = original_template_name and updated_template_name and original_template_name != updated_template_name
        
        # Preserve existing structure name if this is an edit operation
        # unless explicitly changed in the dialog
        if not is_new and structure_name and updated_structure_name != structure_name:
            print(f"🔧 STRUCTURE EDITOR: Structure name changed from '{structure_name}' to '{updated_structure_name}'")
        
        if is_rename:
            print(f"🔧 STRUCTURE EDITOR: Template renamed from '{original_template_name}' to '{updated_template_name}'")
        
        # If we have a callback, call it with the updated structure
        if callable(callback):
            print(f"🔧 STRUCTURE EDITOR: Calling callback with updated structure")
            callback_result = callback({
                'name': updated_template_name,
                'original_name': original_template_name,
                'structure_name': updated_structure_name,
                'structure': updated_structure,
                'is_new': is_new,
                'is_rename': is_rename
            })
            
            # Return expanded information about the result
            return callback_result, updated_structure, updated_structure_name, original_template_name, updated_template_name
        
        # Return expanded information about the result
        return True, updated_structure, updated_structure_name, original_template_name, updated_template_name
    else:
        print(f"🔧 STRUCTURE EDITOR: Dialog cancelled")
        return False, None, None, None, None

def on_template_renamed(template_manager, old_name, new_name):
    """
    Handle template rename event
    
    Args:
        template_manager: Instance of the template manager
        old_name: Previous template name
        new_name: New template name
    """
    print(f"🔄 TEMPLATE RENAMED: '{old_name}' to '{new_name}'")
    
    # Notify template manager of the rename
    if template_manager:
        # Ensure the manager reloads templates
        template_manager.load_templates()
        template_manager.load_custom_structures()
    
    # No need to force gallery refresh here - the calling code will handle it
    # after the dialog is closed and template is updated.


def load_structure_to_editor(editor, structure_name, structure_data):
    """
    Load a structure into an editor instance
    
    Args:
        editor: EnhancedStructureEditor instance
        structure_name: Name of the structure
        structure_data: Structure data to load
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if editor has structure_converter attribute
    if not hasattr(editor, 'structure_converter') or not editor.structure_converter:
        print("ERROR: Editor has no structure_converter")
        return False
    
    # Try to load the structure
    try:
        editor.structure_converter.load_structure(structure_data)
        return True
    except Exception as e:
        print(f"ERROR: Failed to load structure '{structure_name}': {e}")
        import traceback
        traceback.print_exc()
        return False


def save_structure_with_project_type(app, name, structure, project_type=None):
    """
    Save a structure with its associated project type
    
    Args:
        app: The app instance
        name: Name of the structure
        structure: Structure data to save
        project_type: Optional project type
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if app has template_manager
    if not hasattr(app, 'template_manager'):
        print("ERROR: App has no template_manager")
        return False
    
    try:
        # Basic save without project type
        success = app.template_manager.save_custom_structure(name, structure)
        
        # If we have a project type, store the association
        if success and project_type and hasattr(app.template_manager, 'set_structure_project_type'):
            app.template_manager.set_structure_project_type(name, project_type)
            
        # Update UI if needed
        if success and hasattr(app, '_update_structure_combo'):
            app._update_structure_combo()
            
        return success
    except Exception as e:
        print(f"ERROR: Failed to save structure '{name}': {e}")
        import traceback
        traceback.print_exc()
        return False

def test_structure_conversion(editor, structure_data):
    """
    Test the structure conversion process for debugging
    
    Args:
        editor: EnhancedStructureEditor instance
        structure_data: Structure data to test
        
    Returns:
        dict: Test results with conversion data
    """
    print(f"🔎 TESTING STRUCTURE CONVERSION")
    
    if not hasattr(editor, 'structure_converter') or not editor.structure_converter:
        print("❌ ERROR: Editor has no structure_converter")
        return {"error": "No structure_converter available"}
    
    converter = editor.structure_converter
    
    # 1. First check what structure we're starting with
    print(f"INPUT STRUCTURE: {type(structure_data)}")
    if isinstance(structure_data, list):
        print(f"INPUT STRUCTURE ITEMS: {len(structure_data)}")
        if structure_data and len(structure_data) > 0:
            print(f"FIRST ITEM: {structure_data[0]}")
    
    # 2. Normalize the structure
    try:
        normalized = converter._normalize_structure_format(structure_data)
        print(f"NORMALIZED STRUCTURE: {type(normalized)}")
        if isinstance(normalized, list):
            print(f"NORMALIZED ITEMS: {len(normalized)}")
            if normalized and len(normalized) > 0:
                print(f"FIRST NORMALIZED ITEM: {normalized[0]}")
    except Exception as e:
        print(f"❌ ERROR NORMALIZING: {e}")
        import traceback
        traceback.print_exc()
        normalized = None
    
    # 3. Load the structure into the tree
    try:
        print(f"LOADING STRUCTURE INTO TREE...")
        converter.load_structure(structure_data)
        
        # Verify tree state after loading
        tree_state = converter.verify_structure()
        print(f"TREE STATE AFTER LOADING: {tree_state}")
    except Exception as e:
        print(f"❌ ERROR LOADING STRUCTURE: {e}")
        import traceback
        traceback.print_exc()
        tree_state = {"error": str(e)}
    
    # 4. Get structure back from tree
    try:
        print(f"GETTING STRUCTURE FROM TREE...")
        result_structure = converter.get_structure()
        print(f"RESULT STRUCTURE: {type(result_structure)}")
        if isinstance(result_structure, list):
            print(f"RESULT ITEMS: {len(result_structure)}")
            if result_structure and len(result_structure) > 0:
                print(f"FIRST RESULT ITEM: {result_structure[0]}")
    except Exception as e:
        print(f"❌ ERROR GETTING STRUCTURE: {e}")
        import traceback
        traceback.print_exc()
        result_structure = None
    
    # Return comprehensive test results
    return {
        "input": {
            "type": str(type(structure_data)),
            "length": len(structure_data) if isinstance(structure_data, list) else "not a list",
            "sample": structure_data[:3] if isinstance(structure_data, list) else str(structure_data)[:100]
        },
        "normalized": {
            "type": str(type(normalized)),
            "length": len(normalized) if isinstance(normalized, list) else "not a list",
            "sample": normalized[:3] if isinstance(normalized, list) else str(normalized)[:100]
        },
        "tree_state": tree_state,
        "result": {
            "type": str(type(result_structure)),
            "length": len(result_structure) if isinstance(result_structure, list) else "not a list",
            "sample": result_structure[:3] if isinstance(result_structure, list) else str(result_structure)[:100]
        }
    } 
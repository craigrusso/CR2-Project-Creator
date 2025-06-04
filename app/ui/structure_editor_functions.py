#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Structure Editor Functions

This module provides functions for working with the enhanced structure editor.
"""

import os
import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QComboBox, QDialog, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QMainWindow, QFileDialog
)

from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.templates.template_manager import TemplateManager
from app.ui.tree_styling import apply_styling_to_all_tree_widgets


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
        tuple: (success, updated_structure, updated_structure_name, category, description)
    """
    import traceback
    print(f"🚨 STRUCTURE EDITOR TRACE: Called for '{structure_name}' (is_new={is_new})")
    stack = traceback.extract_stack()
    print(f"🚨 STRUCTURE EDITOR TRACE: Call stack:")
    for frame in stack[:-1]:  # Skip current function
        print(f"   - File: {frame.filename}, Line: {frame.lineno}, Function: {frame.name}")
    
    print(f"🔧 STRUCTURE EDITOR: Showing editor for '{structure_name}' (is_new={is_new})")
    
    try:
        # Import our dependencies
        from app.ui.structure_editor_enhanced import EnhancedStructureEditor
        from app.ui.tree_styling import apply_styling_to_all_tree_widgets
        
        # Try to pre-fetch template data if editing an existing template
        fetched_template_data = None
        if not is_new and template_manager and template_name:
            print(f"🔧 STRUCTURE EDITOR: Pre-fetching data for template '{template_name}'")
            # Use get_template_by_name for robust matching
            fetched_template_data = template_manager.get_template_by_name(template_name) 
            if fetched_template_data:
                print(f"🔧 STRUCTURE EDITOR: Successfully pre-fetched template data.")
                # Make sure template_name is set from the fetched data if available
                template_name = fetched_template_data.get('name', template_name)
            else:
                print(f"⚠️ STRUCTURE EDITOR: Failed to pre-fetch template data for '{template_name}'. Editor will use defaults.")

        # Handle the case where template_name might be None but structure_name contains the name
        if not template_name and structure_name and structure_name.startswith("Template_"):
            template_name = structure_name[len("Template_"):]
            print(f"🔧 STRUCTURE EDITOR: Derived template_name '{template_name}' from structure_name")
        
        print(f"🔧 STRUCTURE EDITOR: Final template_name value: '{template_name}'")

        # Create the editor instance, passing pre-fetched data
        editor = EnhancedStructureEditor(
            parent=parent,
            structure_name=structure_name,
            is_new=is_new,
            structure=structure,
            project_type=project_type,
            template_manager=template_manager, # Pass manager instance
            template_data=fetched_template_data # Pass fetched data
        )
        
        # If template_name is provided, set it explicitly in multiple ways to ensure it's properly set
        if template_name:
            if hasattr(editor, 'set_template_name'):
                print(f"🔧 STRUCTURE EDITOR: Explicitly setting template name to '{template_name}'")
                editor.set_template_name(template_name)
            
            # Directly set the name field text if found
            if hasattr(editor, 'name_field') and editor.name_field:
                print(f"🔧 STRUCTURE EDITOR: Directly setting name_field text to '{template_name}'")
                from PyQt6.QtWidgets import QApplication
                editor.name_field.blockSignals(True)
                try:
                    editor.name_field.setText(template_name)
                finally:
                    editor.name_field.blockSignals(False)
                QApplication.processEvents()
        
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
        
        # Apply tree styling to all tree widgets in the dialog
        apply_styling_to_all_tree_widgets(editor)
        
        # --- Force setting the name field text right before showing --- 
        if template_name and hasattr(editor, 'name_field') and editor.name_field:
            print(f"🔧 STRUCTURE EDITOR: Force setting name field text to '{template_name}' before exec_")
            editor.name_field.setText(template_name)
        # ----------------------------------------------------------
        
        # Show the dialog and get the result
        result = editor.exec()
        
        # After dialog is shown, verify name field still has the template name
        # This code will only execute after the dialog is closed
        
        if result == QDialog.DialogCode.Accepted:
            print(f"🔧 STRUCTURE EDITOR: Dialog accepted")
            
            # Get UI values (name, category, description)
            try:
                ui_values = editor.ui_builder.get_ui_values()
                updated_template_name = ui_values.get('template_name')
                selected_category = ui_values.get('category', 'General')
                template_description = ui_values.get('description', '')
                print(f"[DEBUG] Editor UI Values: Name='{updated_template_name}', Category='{selected_category}'")
                
                # Get structure data
                if not editor.structure_converter:
                    raise ValueError("Structure converter is not initialized")
                updated_structure = editor.structure_converter.get_structure()
                print(f"[DEBUG] Structure retrieved from tree: {len(updated_structure)} items")
                
                # Get structure name (ensure Template_ prefix)
                updated_structure_name = updated_template_name
                if updated_structure_name and not updated_structure_name.startswith("Template_"):
                    updated_structure_name = f"Template_{updated_template_name}"
                print(f"[DEBUG] Final structure name: {updated_structure_name}")
                
            except Exception as e:
                print(f"[ERROR] Failed to get data from editor: {e}")
                QMessageBox.warning(parent, "Error", f"Could not retrieve template details from editor: {e}")
                # Return failure, indicating no changes should be saved
                return False, None, None, None, None, None, None # Added None for category/description
            
            # Check if template name is empty
            if not updated_template_name:
                QMessageBox.warning(editor, "Missing Name", "Please enter a name for the template.")
                if editor.ui_builder and editor.ui_builder.template_name_field:
                    editor.ui_builder.template_name_field.setFocus()
                # Re-show dialog? Or just fail? For now, return failure.
                return False, None, None, None, None, None, None # Added None for category/description
            
            # Determine if it was a rename operation
            is_rename = not is_new and original_template_name and updated_template_name != original_template_name
            if is_rename:
                print(f"🔧 STRUCTURE EDITOR: Template renamed from '{original_template_name}' to '{updated_template_name}'")
            
            # If we have a callback, call it with all the updated data
            if callable(callback):
                print(f"🔧 STRUCTURE EDITOR: Calling callback with updated structure and info")
                callback_result = callback({
                    'name': updated_template_name,
                    'original_name': original_template_name,
                    'structure_name': updated_structure_name,
                    'structure': updated_structure,
                    'category': selected_category, # Pass category
                    'description': template_description, # Pass description
                    'is_new': is_new,
                    'is_rename': is_rename
                })
                
                # Return expanded information about the result, including category/description
                return callback_result, updated_structure, updated_structure_name, original_template_name, updated_template_name, selected_category, template_description
            else:
                # If no callback, return the data directly
                return True, updated_structure, updated_structure_name, original_template_name, updated_template_name, selected_category, template_description
        else:
            print(f"🔧 STRUCTURE EDITOR: Dialog cancelled")
            return False, None, None, None, None, None, None # Added None for category/description
    except Exception as e:
        print(f"ERROR showing enhanced structure editor: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to basic structure editor
        return show_basic_structure_editor(parent, structure_name, structure, is_new, callback)

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
    Save a structure, potentially setting a project type.
    Used as a callback for the EnhancedStructureEditor when creating new structures.
    
    Args:
        app: The app instance
        name: Name of the structure
        structure: Structure data to save
        project_type: Optional project type
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Save the structure
    # success = app.template_manager.save_custom_structure(name, structure)
    # For now, assume success, as the actual saving should be handled by the editor if it's a full template,
    # or this path needs review if it's for standalone structures only.
    success = True # Placeholder

    if success:
        # Update UI if needed
        if success and hasattr(app, '_update_structure_combo'):
            app._update_structure_combo()
            
        return success
    else:
        print(f"ERROR: Failed to save structure '{name}'")
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

def show_basic_structure_editor(parent, structure_name, structure, is_new=False, callback=None):
    """
    Show a basic structure editor dialog as a fallback
    
    Args:
        parent: Parent widget
        structure_name: Name of the structure
        structure: Structure data
        is_new: Whether this is a new structure
        callback: Callback function to call when structure is saved
        
    Returns:
        tuple: (success, structure, structure_name, original_template_name, updated_template_name)
    """
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit, QPushButton, QHBoxLayout
    from PyQt6.QtCore import Qt
    
    print(f"🔧 BASIC STRUCTURE EDITOR: Showing basic editor for '{structure_name}'")
    
    # Create the dialog
    dialog = QDialog(parent)
    dialog.setWindowTitle("Basic Structure Editor")
    dialog.resize(600, 400)
    
    # Create layout
    layout = QVBoxLayout(dialog)
    
    # Add name field
    name_layout = QHBoxLayout()
    name_label = QLabel("Template Name:")
    name_layout.addWidget(name_label)
    
    # Strip "Template_" prefix for display
    display_name = structure_name
    if display_name.startswith("Template_"):
        display_name = display_name[9:]
    
    name_field = QLineEdit(display_name)
    name_layout.addWidget(name_field)
    layout.addLayout(name_layout)
    
    # Add tree widget
    tree = QTreeWidget(dialog)
    tree.setHeaderLabels(["Name"])
    layout.addWidget(tree)
    
    # Apply styling to the tree
    from app.ui.tree_styling import setup_tree_for_structure_editing
    try:
        setup_tree_for_structure_editing(tree)
    except Exception as e:
        print(f"WARNING: Failed to apply tree styling: {e}")
    
    # Load the structure into the tree
    def add_structure_items(parent_item, structure_items):
        if not structure_items:
            return
            
        for item in structure_items:
            if isinstance(item, dict):
                # Handle dictionary format (new format)
                item_name = item.get('name', '')
                item_type = item.get('type', 'folder')
                children = item.get('children', [])
                
                tree_item = QTreeWidgetItem(parent_item)
                tree_item.setText(0, item_name)
                tree_item.setFlags(tree_item.flags() | Qt.ItemFlag.ItemIsEditable)
                
                # Store item data
                tree_item.setData(0, Qt.ItemDataRole.UserRole, {'type': item_type, 'name': item_name})
                
                # Set icon based on type
                if item_type == 'folder':
                    # Use folder icon
                    from PyQt6.QtWidgets import QStyle, QApplication
                    tree_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                    
                    # Add children
                    add_structure_items(tree_item, children)
                else:
                    # Use file icon
                    from PyQt6.QtWidgets import QStyle, QApplication
                    tree_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
            elif isinstance(item, str):
                # Handle string format (file in old format)
                tree_item = QTreeWidgetItem(parent_item)
                tree_item.setText(0, item)
                tree_item.setFlags(tree_item.flags() | Qt.ItemFlag.ItemIsEditable)
                
                # Set file icon and data
                from PyQt6.QtWidgets import QStyle, QApplication
                tree_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                tree_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'file', 'name': item})
            elif isinstance(item, dict) and len(item) == 1:
                # Handle old format structure (dictionary with single key)
                folder_name = list(item.keys())[0]
                folder_contents = item[folder_name]
                
                folder_item = QTreeWidgetItem(parent_item)
                folder_item.setText(0, folder_name)
                folder_item.setFlags(folder_item.flags() | Qt.ItemFlag.ItemIsEditable)
                
                # Set folder icon and data
                from PyQt6.QtWidgets import QStyle, QApplication
                folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                folder_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'folder', 'name': folder_name})
                
                # Add children
                add_structure_items(folder_item, folder_contents)
    
    # Load structure data
    if structure:
        try:
            add_structure_items(tree.invisibleRootItem(), structure if isinstance(structure, list) else [structure])
        except Exception as e:
            print(f"ERROR: Failed to load structure: {e}")
    
    # Add buttons
    button_layout = QHBoxLayout()
    cancel_button = QPushButton("Cancel")
    save_button = QPushButton("Save")
    button_layout.addWidget(cancel_button)
    button_layout.addStretch()
    button_layout.addWidget(save_button)
    layout.addLayout(button_layout)
    
    # Extract structure data from tree
    def get_structure_from_tree():
        result = []
        root = tree.invisibleRootItem()
        
        for i in range(root.childCount()):
            item = root.child(i)
            result.append(get_item_data(item))
            
        return result
    
    def get_item_data(item):
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        item_type = item_data.get('type', 'folder') if isinstance(item_data, dict) else 'folder'
        item_name = item.text(0)
        
        if item_type == 'folder':
            # Create folder item with children
            if item.childCount() > 0:
                children = []
                for i in range(item.childCount()):
                    children.append(get_item_data(item.child(i)))
                    
                return {
                    'name': item_name,
                    'type': 'folder',
                    'children': children
                }
            else:
                # Empty folder
                return {
                    'name': item_name,
                    'type': 'folder'
                }
        else:
            # File item
            return {
                'name': item_name,
                'type': 'file'
            }
    
    # Connect signals
    cancel_button.clicked.connect(dialog.reject)
    save_button.clicked.connect(dialog.accept)
    
    # Set result variables
    result = False
    updated_structure = None
    updated_structure_name = structure_name
    original_template_name = display_name
    updated_template_name = display_name
    
    # Show the dialog and process the result
    if dialog.exec() == QDialog.DialogCode.Accepted:
        # Get structure, name and description from the dialog
        updated_template_name = name_field.text()
        
        # Build structure name with Template_ prefix
        if is_new or not updated_structure_name.startswith("Template_"):
            updated_structure_name = f"Template_{updated_template_name}"
        
        # Extract structure from tree
        updated_structure = get_structure_from_tree()
        
        # Call callback if provided
        if callable(callback):
            callback_result = callback({
                'name': updated_template_name,
                'original_name': original_template_name,
                'structure_name': updated_structure_name,
                'structure': updated_structure,
                'is_new': is_new,
                'is_rename': original_template_name != updated_template_name
            })
            
            # Use callback result as success flag
            result = bool(callback_result)
        else:
            result = True
    
    return result, updated_structure, updated_structure_name, original_template_name, updated_template_name 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QMessageBox, QInputDialog, QListWidget,
                            QAbstractItemView, QScrollArea, QWidget, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal

# Import from our centralized color scheme
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE
# Import the enhanced structure editor instead of the basic one
from app.ui.structure_editor_enhanced import EnhancedStructureEditor, save_structure_with_project_type


def create_custom_structure(app):
    """Create a new custom folder structure"""
    # Use the enhanced editor with is_new=True
    editor = EnhancedStructureEditor(
        app, 
        is_new=True,
        save_callback=lambda name, structure: save_structure_with_project_type(app, name, structure)
    )
    editor.exec_()


def save_custom_structure(app, name, structure):
    """Save a custom structure"""
    # Save the structure
    success = app.template_manager.save_custom_structure(name, structure)
    
    if success:
        # Update UI if needed
        if hasattr(app, '_update_structure_combo'):
            app._update_structure_combo()
    
    return success


def edit_structure(app):
    """Edit the selected custom structure"""
    structure_name = app.structure_combo.currentText()
    if structure_name == "Default":
        QMessageBox.information(app, "Information", "Cannot edit the default structure. Create a new custom structure instead.")
        return
    
    # Get the structure
    structure = app.template_manager.get_structure(structure_name)
    
    # Open enhanced editor
    editor = EnhancedStructureEditor(
        app, 
        structure_name=structure_name,
        structure=structure,
        save_callback=lambda name, s: update_custom_structure(app, structure_name, name, s)
    )
    editor.exec_()


def update_custom_structure(app, old_name, new_name, structure):
    """Update a custom structure"""
    # If the name has changed, create a new one and delete the old
    success = False
    
    if old_name != new_name:
        # Create the new structure
        success = app.template_manager.save_custom_structure(new_name, structure)
        
        if success:
            # Delete the old structure
            app.template_manager.delete_custom_structure(old_name)
            
            # Update UI
            if hasattr(app, 'structure_combo'):
                app.structure_combo.setCurrentText(new_name)
    else:
        # Update the existing structure
        success = app.template_manager.save_custom_structure(new_name, structure)
    
    # Update UI
    if success and hasattr(app, '_update_structure_combo'):
        app._update_structure_combo()
    
    return success


def delete_custom_structure(app, name):
    """Delete a custom structure"""
    # Confirm deletion
    confirm = QMessageBox.question(app, "Confirm Deletion", 
                                 f"Are you sure you want to delete the structure '{name}'?",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    
    if confirm == QMessageBox.Yes:
        # Delete the structure
        success = app.template_manager.delete_custom_structure(name)
        
        if success:
            # Update UI
            if hasattr(app, '_update_structure_combo'):
                app._update_structure_combo()
                
            # Select Default if available
            if hasattr(app, 'structure_combo'):
                default_index = app.structure_combo.findText("Default")
                if default_index >= 0:
                    app.structure_combo.setCurrentIndex(default_index)
            
            return True
    
    return False


def manage_structures(app):
    """Show dialog to manage structures"""
    # Create dialog
    dialog = QDialog(app)
    dialog.setWindowTitle("Manage Structures")
    dialog.resize(600, 400)
    
    # Layout
    layout = QVBoxLayout(dialog)
    
    # Instructions
    instructions = QLabel("Manage your custom folder structures:")
    layout.addWidget(instructions)
    
    # Create list of structures
    structures_list = QListWidget()
    structures_list.setSelectionMode(QAbstractItemView.SingleSelection)
    layout.addWidget(structures_list)
    
    # Populate list with custom structures
    for name in sorted(app.template_manager.custom_structures.keys()):
        structures_list.addItem(name)
    
    # Buttons
    button_layout = QHBoxLayout()
    
    edit_btn = QPushButton("Edit")
    edit_btn.clicked.connect(lambda: edit_structure_from_list(app, structures_list, dialog))
    button_layout.addWidget(edit_btn)
    
    delete_btn = QPushButton("Delete")
    delete_btn.clicked.connect(lambda: delete_structure_from_list(app, structures_list, dialog))
    button_layout.addWidget(delete_btn)
    
    layout.addLayout(button_layout)
    
    # Close button
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    layout.addWidget(close_btn)
    
    # Show dialog
    dialog.exec_()


def edit_structure_from_list(app, listbox, structures):
    """Edit a custom structure from the management list"""
    selected_items = listbox.selectedItems()
    if not selected_items:
        QMessageBox.critical(app, "Error", "Please select a structure to edit")
        return
    
    selected_item = selected_items[0]
    row = listbox.row(selected_item)
    name = selected_item.text()
    
    # Get the structure
    structure = app.template_manager.get_structure(name)
    
    # Open enhanced editor
    editor = EnhancedStructureEditor(
        app, 
        structure_name=name,
        structure=structure,
        save_callback=lambda new_name, s: update_custom_structure_from_list(
            app, name, new_name, s, listbox, structures, row)
    )
    editor.exec_()


def update_custom_structure_from_list(app, old_name, new_name, structure, listbox, structures, row):
    """Update a custom structure from the management list"""
    # Save the structure
    success = update_custom_structure(app, old_name, new_name, structure)
    
    if success:
        # Update the list
        if old_name != new_name:
            # Remove the old item and add the new one
            listbox.takeItem(row)
            
            # Add the new item
            listbox.addItem(new_name)
            
            # Sort the list
            listbox.sortItems()
        
        return True
    
    return False


def delete_structure_from_list(app, listbox, structures):
    """Delete a custom structure from the management list"""
    selected_items = listbox.selectedItems()
    if not selected_items:
        QMessageBox.critical(app, "Error", "Please select a structure to delete")
        return
    
    selected_item = selected_items[0]
    row = listbox.row(selected_item)
    name = selected_item.text()
    
    # Delete the structure
    success = delete_custom_structure(app, name)
    
    if success:
        # Remove from list
        listbox.takeItem(row)


def update_structure_dropdown(app):
    """Update the structure dropdown with available structures"""
    # Save current selection
    current = app.structure_combo.currentText()
    
    # Clear and repopulate
    app.structure_combo.clear()
    
    # Add default structure
    app.structure_combo.addItem("Default")
    
    # Add custom structures
    for structure_name in app.template_manager.custom_structures:
        app.structure_combo.addItem(structure_name)
    
    # Restore selection if possible, otherwise select Default
    index = app.structure_combo.findText(current)
    if index >= 0:
        app.structure_combo.setCurrentIndex(index)
    else:
        app.structure_combo.setCurrentIndex(0)  # Default


def highlight_current_structure(app):
    """Highlight the currently selected structure in the dropdown"""
    # In PyQt, this might be handled differently or may not be needed
    pass


def _update_structure_combo(app):
    """Initialize the structure dropdown"""
    # Add default structure
    app.structure_combo.addItem("Default")
    
    # Add custom structures
    for structure_name in app.template_manager.custom_structures:
        app.structure_combo.addItem(structure_name)
    
    # Set to Default initially
    app.structure_combo.setCurrentIndex(0)
    
    # Update it using saved config if needed
    last_structure = app.config.get("last_structure", "Default")
    idx = app.structure_combo.findText(last_structure)
    if idx >= 0:
        app.structure_combo.setCurrentIndex(idx)


def _preview_structure(app):
    """Preview the selected structure"""
    structure_name = app.structure_combo.currentText()
    structure = app.template_manager.get_structure(structure_name)
    
    # Display preview - this should call the PyQt version of preview_structure
    from app.dialogs.dialog_windows_pyqt import preview_structure
    preview_structure(app, structure)


def _edit_structure(app):
    """Edit the selected structure"""
    structure_name = app.structure_combo.currentText()
    if structure_name == "Default":
        QMessageBox.information(app, "Information", 
                              "Cannot edit the default structure. Create a new custom structure instead.")
    else:
        edit_structure(app) 
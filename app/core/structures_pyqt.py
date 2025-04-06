#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QMessageBox, QInputDialog, QListWidget,
                            QAbstractItemView, QScrollArea, QWidget, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem

# Import from our centralized color scheme
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE
# Import the enhanced structure editor instead of the basic one
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.ui.structure_editor_functions import save_structure_with_project_type


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
    """Update the structure dropdown with available structures using a model."""
    # Get the TemplateManager instance safely
    template_manager = getattr(app, 'template_manager', None)
    if not template_manager:
        print("Error: TemplateManager not found in update_structure_dropdown")
        return

    # Get custom structures safely
    custom_structures = getattr(template_manager, 'custom_structures', {})
    # Get default structures (assuming it's available, e.g., from constants)
    # You might need to import DEFAULT_STRUCTURES if it's defined elsewhere
    try:
        # Assuming DEFAULT_STRUCTURES is available in scope or imported
        from app.constants import DEFAULT_STRUCTURES 
    except ImportError:
        print("Warning: DEFAULT_STRUCTURES not found, cannot populate default structures.")
        DEFAULT_STRUCTURES = {} # Fallback to empty dict

    # Save current selection text
    current_text = app.structure_combo.currentText()

    # Create a standard item model
    model = QStandardItemModel(app.structure_combo)

    # Add default structures header
    item_default_header = QStandardItem("---- Default Structures ----")
    item_default_header.setEnabled(False) # Make it non-selectable
    item_default_header.setFlags(item_default_header.flags() & ~Qt.ItemIsSelectable) # Ensure non-selectable visually
    model.appendRow(item_default_header)

    # Add default structures
    for structure_name in sorted(DEFAULT_STRUCTURES.keys()):
        item = QStandardItem(structure_name)
        model.appendRow(item)

    # Add custom structures header (if any custom structures exist)
    if custom_structures:
        # Add separator line visually if needed (optional)
        # separator = QStandardItem()
        # separator.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable) # Make it like a separator line visually
        # separator.setData(QVariant(QSize(0, 1)), Qt.SizeHintRole) # Set size hint
        # model.appendRow(separator)

        item_custom_header = QStandardItem("---- Custom Structures ----")
        item_custom_header.setEnabled(False) # Make it non-selectable
        item_custom_header.setFlags(item_custom_header.flags() & ~Qt.ItemIsSelectable) # Ensure non-selectable visually
        model.appendRow(item_custom_header)

        # Add custom structures
        for structure_name in sorted(custom_structures.keys()):
            item = QStandardItem(structure_name)
            model.appendRow(item)

    # Set the model to the combo box
    app.structure_combo.setModel(model)

    # Restore selection if possible, otherwise select the first valid item
    if current_text:
        index_to_select = -1
        for i in range(model.rowCount()):
            item = model.item(i)
            # Find the first enabled item matching the text
            if item and item.isEnabled() and item.text() == current_text:
                index_to_select = i
                break
        
        if index_to_select != -1:
            app.structure_combo.setCurrentIndex(index_to_select)
        else:
            # If previous selection not found/valid, select first enabled item
            for i in range(model.rowCount()):
                item = model.item(i)
                if item and item.isEnabled():
                    app.structure_combo.setCurrentIndex(i)
                    break
            else: # If no enabled items exist (unlikely)
                 app.structure_combo.setCurrentIndex(-1) # No selection

    else:
         # If no previous text, select first enabled item
         for i in range(model.rowCount()):
             item = model.item(i)
             if item and item.isEnabled():
                 app.structure_combo.setCurrentIndex(i)
                 break
         else:
             app.structure_combo.setCurrentIndex(-1) # No selection


def highlight_current_structure(app):
    """Highlight the currently selected structure in the dropdown"""
    # In PyQt, this might be handled differently or may not be needed
    pass


def _update_structure_combo(app):
    """Initialize the structure dropdown"""
    # Add default structures header
    item_default_header = QStandardItem("---- Default Structures ----")
    item_default_header.setEnabled(False)
    model.appendRow(item_default_header)
    
    # Add default structures
    for structure_name in sorted(DEFAULT_STRUCTURES.keys()):
        item = QStandardItem(structure_name)
        model.appendRow(item)
    
    # Add custom structures header (if any custom structures exist)
    if app.template_manager and app.template_manager.custom_structures:
        item_custom_header = QStandardItem("---- Custom Structures ----")
        item_custom_header.setEnabled(False)
        model.appendRow(item_custom_header)
    
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
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
from app.ui.ui_components_pyqt import StructureEditor


def create_custom_structure(app):
    """Create a new custom folder structure"""
    editor = StructureEditor(app, save_callback=lambda name, structure: save_custom_structure(app, name, structure))
    editor.exec_()


def save_custom_structure(app, name, structure):
    """Save a custom folder structure"""
    success = app.template_manager.save_custom_structure(name, structure)
    if success:
        QMessageBox.information(app, "Success", f"Structure '{name}' saved successfully")
        app.template_manager.load_custom_structures()
        update_structure_dropdown(app)
        # In PyQt we use comboBox.setCurrentText instead of StringVar.set
        app.structure_combo.setCurrentText(name)
        highlight_current_structure(app)
    else:
        QMessageBox.critical(app, "Error", f"Failed to save structure '{name}'")


def edit_structure(app):
    """Edit the selected custom structure"""
    structure_name = app.structure_combo.currentText()
    if structure_name == "Default":
        QMessageBox.information(app, "Information", "Cannot edit the default structure. Create a new custom structure instead.")
        return
    
    # Get the structure
    structure = app.template_manager.get_structure(structure_name)
    
    # Open editor
    editor = StructureEditor(app, structure=structure, title=f"Edit Structure - {structure_name}",
                            save_callback=lambda name, s: update_custom_structure(app, structure_name, name, s))
    # Set the name in PyQt
    # editor.name_input.setText(structure_name)
    editor.exec_()


def update_custom_structure(app, old_name, new_name, structure):
    """Update an existing custom structure"""
    # If name changed, rename first
    if old_name != new_name:
        renamed = app.template_manager.rename_custom_structure(old_name, new_name)
        if not renamed:
            QMessageBox.critical(app, "Error", f"Failed to rename structure from '{old_name}' to '{new_name}'")
            return
    
    # Save the updated structure
    success = app.template_manager.save_custom_structure(new_name, structure)
    if success:
        QMessageBox.information(app, "Success", f"Structure '{new_name}' updated successfully")
        app.template_manager.load_custom_structures()
        update_structure_dropdown(app)
        app.structure_combo.setCurrentText(new_name)
        highlight_current_structure(app)
    else:
        QMessageBox.critical(app, "Error", f"Failed to update structure '{new_name}'")


def manage_structures(app):
    """Manage custom folder structures"""
    manage_dialog = QDialog(app)
    manage_dialog.setWindowTitle("Manage Custom Structures")
    manage_dialog.resize(500, 400)
    
    # Main layout
    layout = QVBoxLayout(manage_dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(10)
    
    # Header
    header_label = QLabel("Custom Folder Structures")
    header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
    layout.addWidget(header_label)
    
    # Structure list
    structure_listbox = QListWidget()
    structure_listbox.setSelectionMode(QAbstractItemView.SingleSelection)
    layout.addWidget(structure_listbox)
    
    # Load structures
    structures = list(app.template_manager.custom_structures.keys())
    for structure in structures:
        structure_listbox.addItem(structure)
    
    # Buttons frame
    button_layout = QHBoxLayout()
    layout.addLayout(button_layout)
    
    # Buttons
    rename_btn = QPushButton("Rename")
    rename_btn.clicked.connect(lambda: rename_structure(app, structure_listbox, structures))
    button_layout.addWidget(rename_btn)
    
    edit_btn = QPushButton("Edit")
    edit_btn.clicked.connect(lambda: edit_structure_from_list(app, structure_listbox, structures))
    button_layout.addWidget(edit_btn)
    
    delete_btn = QPushButton("Delete")
    delete_btn.clicked.connect(lambda: delete_structure(app, structure_listbox, structures))
    button_layout.addWidget(delete_btn)
    
    new_btn = QPushButton("New Structure")
    new_btn.clicked.connect(lambda: create_custom_structure(app))
    button_layout.addWidget(new_btn)
    
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(manage_dialog.close)
    button_layout.addWidget(close_btn, 1, Qt.AlignRight)
    
    # Show dialog
    manage_dialog.exec_()


def rename_structure(app, listbox, structures):
    """Rename a custom structure from the management list"""
    selected_items = listbox.selectedItems()
    if not selected_items:
        QMessageBox.critical(app, "Error", "Please select a structure to rename")
        return
    
    selected_item = selected_items[0]
    row = listbox.row(selected_item)
    name = selected_item.text()
    
    # Get new name
    new_name, ok = QInputDialog.getText(app, "Rename Structure", 
                                       "Enter new name:", text=name)
    
    if ok and new_name and new_name != name:
        # Rename the structure
        success = app.template_manager.rename_custom_structure(name, new_name)
        
        if success:
            # Update list
            structures[row] = new_name
            selected_item.setText(new_name)
            
            # Update dropdown
            update_structure_dropdown(app)
            
            # Update selected if needed
            if app.structure_combo.currentText() == name:
                app.structure_combo.setCurrentText(new_name)
                highlight_current_structure(app)
            
            QMessageBox.information(app, "Success", f"Structure renamed to '{new_name}'")
        else:
            QMessageBox.critical(app, "Error", f"Failed to rename structure")


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
    
    # Open editor
    editor = StructureEditor(app, structure=structure, title=f"Edit Structure - {name}",
                           save_callback=lambda new_name, s: update_custom_structure_from_list(
                               app, name, new_name, s, listbox, structures, row))
    # Set the name
    # editor.name_input.setText(name)
    editor.exec_()


def update_custom_structure_from_list(app, old_name, new_name, structure, listbox, structures, index):
    """Update a custom structure from the management list"""
    # If name changed, rename first
    if old_name != new_name:
        renamed = app.template_manager.rename_custom_structure(old_name, new_name)
        if not renamed:
            QMessageBox.critical(app, "Error", f"Failed to rename structure from '{old_name}' to '{new_name}'")
            return
        
        # Update list
        structures[index] = new_name
        listbox.item(index).setText(new_name)
        
        # Update dropdown
        update_structure_dropdown(app)
        
        # Update selected if needed
        if app.structure_combo.currentText() == old_name:
            app.structure_combo.setCurrentText(new_name)
            highlight_current_structure(app)
    
    # Save the updated structure
    success = app.template_manager.save_custom_structure(new_name, structure)
    if success:
        QMessageBox.information(app, "Success", f"Structure '{new_name}' updated successfully")
        app.template_manager.load_custom_structures()
    else:
        QMessageBox.critical(app, "Error", f"Failed to update structure '{new_name}'")


def delete_structure(app, listbox, structures):
    """Delete a custom structure from the management list"""
    selected_items = listbox.selectedItems()
    if not selected_items:
        QMessageBox.critical(app, "Error", "Please select a structure to delete")
        return
    
    selected_item = selected_items[0]
    row = listbox.row(selected_item)
    name = selected_item.text()
    
    # Confirm deletion
    confirm = QMessageBox.question(app, "Confirm Deletion", 
                                 f"Are you sure you want to delete the structure '{name}'?",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if confirm != QMessageBox.Yes:
        return
    
    # Delete the structure
    success = app.template_manager.delete_custom_structure(name)
    
    if success:
        # Update list
        del structures[row]
        listbox.takeItem(row)
        
        # Update dropdown
        update_structure_dropdown(app)
        
        # Reset selected if needed
        if app.structure_combo.currentText() == name:
            app.structure_combo.setCurrentText("Default")
            highlight_current_structure(app)
        
        QMessageBox.information(app, "Success", f"Structure '{name}' deleted")
    else:
        QMessageBox.critical(app, "Error", f"Failed to delete structure '{name}'")


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
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem,
                            QMessageBox, QGroupBox, QComboBox, QCheckBox,
                            QMenu, QAction, QStyle, QApplication, QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE

class EnhancedStructureEditor(QDialog):
    """
    Enhanced folder structure editor
    """
    
    def __init__(self, parent, structure_name=None, structure=None, project_type=None, save_callback=None, is_new=False):
        super().__init__(parent)
        self.parent = parent
        self.structure_name = structure_name
        self.project_type = project_type
        self.template_manager = parent.template_manager if hasattr(parent, 'template_manager') else None
        self.is_built_in = False  # Flag to track if this is a built-in structure
        self.save_callback = save_callback
        
        # If structure name is provided but no structure, try to load it
        if structure_name and not structure and self.template_manager:
            from app.constants import DEFAULT_STRUCTURES
            if structure_name in DEFAULT_STRUCTURES:
                structure = DEFAULT_STRUCTURES[structure_name]
                self.is_built_in = True
            elif hasattr(self.template_manager, 'custom_structures') and structure_name in self.template_manager.custom_structures:
                structure = self.template_manager.custom_structures[structure_name].get("directories", [])
                
        # If we still don't have a structure but have a project type, use the default for that type
        if not structure and project_type and self.template_manager:
            from app.constants import PROJECT_TYPE_TO_STRUCTURE
            default_structure_name = PROJECT_TYPE_TO_STRUCTURE.get(project_type)
            if default_structure_name:
                structure = self.template_manager.get_structure(default_structure_name)
                # If we're using the default structure, set the structure name accordingly
                if not self.structure_name:
                    self.structure_name = default_structure_name
                    # Check if it's a built-in structure
                    from app.constants import DEFAULT_STRUCTURES
                    if default_structure_name.lower() in [s.lower() for s in DEFAULT_STRUCTURES.keys()]:
                        self.is_built_in = True
        
        self.structure = structure or []
        self.original_structure_name = structure_name  # Keep track of original name for saving
        
        # Check if this is a built-in structure
        from app.constants import DEFAULT_STRUCTURES
        if structure_name and structure_name.lower() in [s.lower() for s in DEFAULT_STRUCTURES.keys()]:
            self.is_built_in = True
        
        self.setWindowTitle("Project Structure Editor")
        self.resize(800, 600)
        
        self.init_ui()
        
        # If is_new is True, create a new structure right away
        if is_new:
            self.create_new_structure()
        else:
            self.populate_structure()
            self.populate_structure_dropdown()
        
    def init_ui(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout(self)
        
        # Top info section
        info_group = QGroupBox("Structure Information")
        info_layout = QVBoxLayout(info_group)
        
        # Name input with label
        name_layout = QHBoxLayout()
        name_label = QLabel("Structure Name:")
        self.name_input = QLineEdit()
        if self.structure_name:
            self.name_input.setText(self.structure_name)
        
        # If this is a built-in structure, add a note and disable the name field
        if self.is_built_in:
            self.name_input.setReadOnly(True)
            self.name_input.setStyleSheet("background-color: #f0f0f0;")
            built_in_note = QLabel("This is a built-in structure. To modify it, save as a new structure.")
            built_in_note.setStyleSheet("color: #cc0000; font-style: italic;")
            info_layout.addWidget(built_in_note)
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        info_layout.addLayout(name_layout)
        
        # Template selection dropdown
        template_layout = QHBoxLayout()
        template_label = QLabel("Choose Structure:")
        self.structure_combo = QComboBox()
        self.structure_combo.setMinimumWidth(250)
        
        # Add "New Structure" option at the top
        self.new_structure_button = QPushButton("Create New")
        self.new_structure_button.clicked.connect(self.create_new_structure)
        self.new_structure_button.setStyleSheet(BUTTON_STYLE)
        
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.structure_combo)
        template_layout.addWidget(self.new_structure_button)
        info_layout.addLayout(template_layout)
        
        # Structure description
        description_label = QLabel("This structure defines how your project folders will be organized when creating a new project using this template.")
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #666; font-style: italic;")
        info_layout.addWidget(description_label)
        
        main_layout.addWidget(info_group)
        
        # Structure Tree
        tree_group = QGroupBox("Folder Structure")
        tree_layout = QVBoxLayout(tree_group)
        
        # Tree widget for the structure
        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        tree_layout.addWidget(self.tree)
        
        # Buttons for structure manipulation
        structure_buttons = QHBoxLayout()
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.add_folder)
        add_folder_btn.setStyleSheet(BUTTON_STYLE)
        
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self.add_file)
        add_file_btn.setStyleSheet(BUTTON_STYLE)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_item)
        delete_btn.setStyleSheet(BUTTON_STYLE)
        
        structure_buttons.addWidget(add_folder_btn)
        structure_buttons.addWidget(add_file_btn)
        structure_buttons.addWidget(delete_btn)
        tree_layout.addLayout(structure_buttons)
        
        main_layout.addWidget(tree_group)
        
        # Bottom buttons
        bottom_buttons = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        self.save_as_btn = QPushButton("Save As...")
        self.save_as_btn.clicked.connect(self.save_structure_as)
        self.save_as_btn.setStyleSheet(BUTTON_STYLE)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_structure)
        save_btn.setStyleSheet(BUTTON_STYLE)
        
        bottom_buttons.addWidget(cancel_btn)
        bottom_buttons.addWidget(self.save_as_btn)
        bottom_buttons.addWidget(save_btn)
        
        main_layout.addLayout(bottom_buttons)
        
    def populate_structure_dropdown(self):
        """Populate the structure dropdown with available structures"""
        self.structure_combo.clear()
        self.structure_combo.addItem("Select a structure...", None)
        
        # Import the default structures and PROJECT_TYPE_TO_STRUCTURE mapping
        from app.constants import DEFAULT_STRUCTURES, PROJECT_TYPE_TO_STRUCTURE
        
        # Add built-in structures section
        self.structure_combo.addItem("=== Built-in Structures ===", None)
        
        # If project_type is provided, filter structures related to that project type
        if self.project_type:
            # Get the related structure for this project type
            related_structure = PROJECT_TYPE_TO_STRUCTURE.get(self.project_type)
            
            # Filter built-in structures that contain the project type in their name
            filtered_structures = []
            for name in sorted(DEFAULT_STRUCTURES.keys()):
                if self.project_type.lower() in name.lower() or (related_structure and related_structure.lower() == name.lower()):
                    filtered_structures.append(name)
                    
            # Add the filtered structures to the dropdown
            for name in filtered_structures:
                self.structure_combo.addItem(name, name)
        else:
            # No project type filter, add all built-in structures
            for name in sorted(DEFAULT_STRUCTURES.keys()):
                self.structure_combo.addItem(name, name)
        
        # Add custom structures section if template manager is available
        if self.template_manager and hasattr(self.template_manager, 'custom_structures'):
            self.structure_combo.addItem("=== Custom Structures ===", None)
            
            # If project_type is provided, filter custom structures as well
            if self.project_type:
                for name in sorted(self.template_manager.custom_structures.keys()):
                    if self.project_type.lower() in name.lower():
                        self.structure_combo.addItem(name, name)
            else:
                # No project type filter, add all custom structures
                for name in sorted(self.template_manager.custom_structures.keys()):
                    self.structure_combo.addItem(name, name)
        
        # Set current structure if specified
        if self.structure_name:
            index = self.structure_combo.findText(self.structure_name)
            if index >= 0:
                self.structure_combo.setCurrentIndex(index)
        
        # Connect signal for dropdown changes
        self.structure_combo.currentIndexChanged.connect(self.on_structure_selected)
    
    def on_structure_selected(self, index):
        """Handle structure selection from dropdown"""
        # Skip if it's a separator or header
        if index <= 0 or self.structure_combo.currentData() is None:
            return
            
        # Get selected structure name
        structure_name = self.structure_combo.currentData()
        
        # Check if it's a built-in structure
        from app.constants import DEFAULT_STRUCTURES
        self.is_built_in = structure_name.lower() in [s.lower() for s in DEFAULT_STRUCTURES.keys()]
        
        # Load the structure
        if self.template_manager:
            structure = self.template_manager.get_structure(structure_name)
            if structure:
                # Update name input
                self.name_input.setText(structure_name)
                self.original_structure_name = structure_name
                
                # If it's a built-in structure, make name field read-only
                if self.is_built_in:
                    self.name_input.setReadOnly(True)
                    self.name_input.setStyleSheet("background-color: #f0f0f0;")
                else:
                    self.name_input.setReadOnly(False)
                    self.name_input.setStyleSheet("")
                
                # Update structure and tree
                self.structure = structure
                self.populate_structure()
    
    def create_new_structure(self):
        """Create a new blank structure"""
        # Clear structure name and tree
        self.name_input.setText("New Structure")
        self.name_input.setReadOnly(False)
        self.name_input.setStyleSheet("")
        self.is_built_in = False
        self.original_structure_name = None
        
        # Create a basic empty structure
        self.structure = []
        self.populate_structure()
        
        # Set focus to name input for editing
        self.name_input.selectAll()
        self.name_input.setFocus()
        
    def save_structure_as(self):
        """Save the structure with a new name"""
        # Get current structure name from input
        current_name = self.name_input.text().strip()
        
        # Prompt for a new name
        new_name, ok = QInputDialog.getText(
            self, 
            "Save Structure As", 
            "Enter new structure name:", 
            text=f"{current_name}_copy" if current_name else "New Structure"
        )
        
        if ok and new_name:
            # Update the name field
            self.name_input.setText(new_name)
            self.is_built_in = False
            self.name_input.setReadOnly(False)
            self.name_input.setStyleSheet("")
            
            # Save with the new name
            self.save_structure()

    def populate_structure(self):
        """Populate the structure tree"""
        if self.structure is None:
            self.structure = []
        
        self.tree.clear()
        
        # Add root item
        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, "Project Root")
        root_item.setExpanded(True)
        
        # Recursively add structure items
        self.add_structure_items(root_item, self.structure)
    
    def add_structure_items(self, parent_item, items):
        """Add structure items recursively"""
        for item in items:
            if isinstance(item, dict):
                # Handle dictionary item (folder with subitems)
                for folder_name, sub_items in item.items():
                    folder_item = QTreeWidgetItem(parent_item)
                    folder_item.setText(0, folder_name)
                    folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                    # Store that this is a folder in the data
                    folder_item.setData(0, Qt.UserRole, "folder")
                    self.add_structure_items(folder_item, sub_items)
            else:
                # Handle string item
                name = item
                is_folder = name.endswith('/')
                
                if is_folder:
                    name = name[:-1]  # Remove trailing slash
                
                item_widget = QTreeWidgetItem(parent_item)
                item_widget.setText(0, name)
                
                if is_folder:
                    # Empty folder - set folder icon
                    item_widget.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                    # Store that this is a folder in the data
                    item_widget.setData(0, Qt.UserRole, "folder")
                else:
                    # File
                    item_widget.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
                    # Store that this is a file in the data
                    item_widget.setData(0, Qt.UserRole, "file")
                    
    def show_context_menu(self, position):
        """Show context menu for tree items"""
        item = self.tree.itemAt(position)
        if not item:
            return
            
        menu = QMenu(self)
        
        add_folder_action = QAction("Add Folder", self)
        add_folder_action.triggered.connect(lambda: self.add_folder(item))
        
        add_file_action = QAction("Add File", self)
        add_file_action.triggered.connect(lambda: self.add_file(item))
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_item(item))
        
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self.rename_item(item))
        
        # Add actions to menu
        menu.addAction(add_folder_action)
        menu.addAction(add_file_action)
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        
        menu.exec_(self.tree.viewport().mapToGlobal(position))
        
    def add_folder(self, parent=None):
        """Add a folder to the structure"""
        # If no parent specified, use selected item or root
        if parent is None:
            parent = self.tree.currentItem()
            
        # If still no parent, use root
        if parent is None:
            parent = self.tree.invisibleRootItem().child(0)
            
        folder_name, ok = QInputDialog.getText(self, "Add Folder", "Folder name:")
        if ok and folder_name:
            folder_item = QTreeWidgetItem(parent)
            folder_item.setText(0, folder_name)
            folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
            # Mark this item as a folder in user data
            folder_item.setData(0, Qt.UserRole, "folder")
            
            # Expand parent if it's a valid QTreeWidgetItem
            if hasattr(parent, 'setExpanded'):
                parent.setExpanded(True)
            
    def add_file(self, parent=None):
        """Add a file to the structure"""
        # If no parent specified, use selected item or root
        if parent is None:
            parent = self.tree.currentItem()
            
        # If still no parent, use root
        if parent is None:
            parent = self.tree.invisibleRootItem().child(0)
            
        file_name, ok = QInputDialog.getText(self, "Add File", "File name:")
        if ok and file_name:
            file_item = QTreeWidgetItem(parent)
            file_item.setText(0, file_name)
            file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
            # Mark this item as a file in user data
            file_item.setData(0, Qt.UserRole, "file")
            
            # Expand parent if it's a valid QTreeWidgetItem
            if hasattr(parent, 'setExpanded'):
                parent.setExpanded(True)
            
    def delete_item(self, item=None):
        """Delete an item from the structure"""
        # If no item specified, use selected item
        if item is None:
            item = self.tree.currentItem()
            
        # Can't delete if no item or if it's the root
        if item is None or item == self.tree.invisibleRootItem().child(0):
            return
            
        # Make sure item is a valid QTreeWidgetItem
        if not hasattr(item, 'text') or not callable(item.text):
            return
            
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{item.text(0)}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Get parent of the item
            parent = item.parent()
            
            # If parent exists, remove the item from the parent
            if parent:
                parent.removeChild(item)
            else:
                # If no parent, get index and remove directly from the tree
                index = self.tree.indexOfTopLevelItem(item)
                if index >= 0:
                    self.tree.takeTopLevelItem(index)
                    
    def rename_item(self, item=None):
        """Rename an item in the structure"""
        # If no item specified, use selected item
        if item is None:
            item = self.tree.currentItem()
            
        # Can't rename if no item or if it's the root
        if item is None or item == self.tree.invisibleRootItem().child(0):
            return
            
        # Make sure item is a valid QTreeWidgetItem
        if not hasattr(item, 'text') or not callable(item.text):
            return
            
        # Get current name
        current_name = item.text(0)
        
        # Get new name
        new_name, ok = QInputDialog.getText(
            self, 
            "Rename", 
            "Enter new name:", 
            text=current_name
        )
        
        if ok and new_name:
            item.setText(0, new_name)
            
    def get_structure_from_tree(self):
        """Convert tree to structure format"""
        root_item = self.tree.invisibleRootItem().child(0)
        if not root_item:
            return []
            
        return self._get_structure_from_item(root_item)
        
    def _get_structure_from_item(self, item):
        """Recursively convert tree item to structure format"""
        result = []
        
        for i in range(item.childCount()):
            child = item.child(i)
            child_name = child.text(0)
            
            if child.childCount() > 0:
                # Directory with children
                children = self._get_structure_from_item(child)
                result.append({child_name: children})
            else:
                # Check if it's an empty folder or a file
                item_type = child.data(0, Qt.UserRole)
                if item_type == "folder":
                    # It's an empty folder - represent as a dict with empty list
                    # This makes the format consistent with non-empty folders
                    result.append({child_name: []})
                else:
                    # It's a file
                    result.append(child_name)
                
        return result
        
    def save_structure(self):
        """Save the structure"""
        # Get name
        structure_name = self.name_input.text().strip()
        if not structure_name:
            QMessageBox.warning(self, "Error", "Structure name is required")
            return
        
        # If this is a built-in structure, prompt to save as new
        if self.is_built_in:
            confirm = QMessageBox.question(
                self,
                "Save Built-in Structure",
                "This is a built-in structure that cannot be modified directly.\n\nWould you like to save it as a new structure?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if confirm == QMessageBox.Yes:
                self.save_structure_as()
                return
            else:
                return
        
        # Get structure from tree
        structure = self.get_structure_from_tree()
        
        # Call save callback
        if self.save_callback:
            success = self.save_callback(structure_name, structure)
            
            if success:
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to save structure")
        else:
            # No callback, just accept dialog
            self.accept()
            
# Utility functions for working with the enhanced structure editor

def save_structure_with_project_type(app, name, structure):
    """Save a structure with project type association"""
    # Check that we have a template manager
    if not hasattr(app, 'template_manager'):
        return False
    
    # Save the structure
    success = app.template_manager.save_custom_structure(name, structure)
    
    return success
    
def show_enhanced_structure_editor(parent, structure_name=None, structure=None, is_new=False, project_type=None):
    """Show the enhanced structure editor dialog"""
    editor = EnhancedStructureEditor(
        parent,
        structure_name=structure_name,
        structure=structure,
        project_type=project_type,
        save_callback=lambda name, structure: save_structure_with_project_type(parent, name, structure),
        is_new=is_new
    )
    
    return editor.exec_() 
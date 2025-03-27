#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative
"""
Enhanced Structure Editor - Main dialog for editing template structures
"""

import os
import json
import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QGroupBox,
    QFormLayout, QMessageBox, QInputDialog, QDialogButtonBox, QAbstractItemView,
    QMenu, QApplication, QStyle, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore

from app.utils.file_operations import FileOperationsHandler
from app.utils.template_validator import TemplateValidator

class EnhancedStructureEditor(QDialog):
    """
    Enhanced Structure Editor Dialog for creating and editing templates
    with their associated structures
    """
    # Define signals
    template_renamed = pyqtSignal(str, str)  # old_name, new_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Edit Template")
        self.resize(800, 600)  # Set initial size
        
        # Initialize properties
        self._template_name = ""
        self._structure_name = ""
        self._template_description = ""
        self._template_category = "Custom"
        self._is_new = False
        
        # Initialize file operations handler
        self.file_operations = FileOperationsHandler(self)
        
        # Initialize structure converter for handling conversions between tree and data structure
        self._init_structure_converter()
        
        # Create UI
        self._create_ui()
        
        # Initialize drag and drop handling
        self.init_drag_drop_handlers()
    
    def _create_ui(self):
        """Create the main user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Template details section
        details_group = QGroupBox("Template Details")
        details_layout = QFormLayout(details_group)
        
        # Name field
        self.name_field = QLineEdit()
        self.name_field.setPlaceholderText("Enter template name")
        self.name_field.textChanged.connect(self.on_template_name_changed)
        details_layout.addRow("Name:", self.name_field)
        
        # Description field
        self.description_field = QTextEdit()
        self.description_field.setPlaceholderText("Enter template description")
        self.description_field.setMaximumHeight(80)
        details_layout.addRow("Description:", self.description_field)
        
        # Category dropdown
        self.category_field = QComboBox()
        self.category_field.addItems(["Custom", "Web", "Desktop", "Mobile", "Other"])
        self.category_field.setEditable(True)
        details_layout.addRow("Category:", self.category_field)
        
        main_layout.addWidget(details_group)
        
        # Project structure section
        structure_group = QGroupBox("Project Structure")
        structure_layout = QVBoxLayout(structure_group)
        
        # Tree widget for structure
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Type"])
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        structure_layout.addWidget(self.tree)
        
        # Buttons for manipulating structure
        button_layout = QHBoxLayout()
        
        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.clicked.connect(self.add_folder)
        button_layout.addWidget(self.add_folder_btn)
        
        self.add_file_btn = QPushButton("Add File")
        self.add_file_btn.clicked.connect(self.add_file)
        button_layout.addWidget(self.add_file_btn)
        
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_item)
        button_layout.addWidget(self.edit_btn)
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_item)
        button_layout.addWidget(self.remove_btn)
        
        structure_layout.addLayout(button_layout)
        main_layout.addWidget(structure_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def set_template_name(self, name):
        """Set the template name"""
        self._template_name = name
        self.name_field.setText(name)
    
    def get_template_name(self):
        """Get the current template name"""
        return self._template_name
    
    def set_structure_name(self, name):
        """Set the structure name"""
        self._structure_name = name
        # Update window title
        self.setWindowTitle(f"Edit Template: {name}")
    
    def get_structure_name(self):
        """Get the current structure name"""
        # Ensure it has the Template_ prefix
        name = self._structure_name
        if name and not name.startswith("Template_"):
            name = f"Template_{name}"
        return name
    
    def focus_name_field(self):
        """Focus the name field"""
        if self.name_field:
            self.name_field.setFocus()
            self.name_field.selectAll()
    
    def on_template_name_changed(self, text):
        """Handle changes to the template name"""
        old_name = self._template_name
        new_name = text
        
        # Don't process if not changed
        if old_name == new_name:
            return
        
        # Update internal name
        self._template_name = new_name
        
        # If this is a new template, update structure name to match
        if self._is_new or not self._structure_name:
            # Only update structure name for new templates
            structure_name = f"Template_{new_name}"
            self._structure_name = structure_name
            print(f"📝 STRUCTURE EDITOR: Updated structure name to '{structure_name}' (is_new={self._is_new})")
        
        # Emit signal if name actually changed and isn't empty
        if old_name and new_name and old_name != new_name:
            print(f"📝 STRUCTURE EDITOR: Template name changed from '{old_name}' to '{new_name}'")
            self.template_renamed.emit(old_name, new_name)
    
    def init_drag_drop_handlers(self):
        """Initialize drag and drop handlers for the tree"""
        try:
            # Import the drag drop handler
            from app.ui.structure_editor.drag_drop import DragDropHandler
            
            # Enable drag and drop operations for the tree
            self.tree.setDragEnabled(True)
            self.tree.setAcceptDrops(True)
            self.tree.setDropIndicatorShown(True)
            self.tree.setDragDropMode(QAbstractItemView.DragDrop)  # Allow external drops
            
            # Set up context menu
            self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
            self.tree.customContextMenuRequested.connect(self.show_context_menu)
            
            # Create and attach the drag drop handler
            self.drag_drop_handler = DragDropHandler(self.tree, self)
            
            # Enable external drops (from OS file explorer)
            self.drag_drop_handler.enable_external_drops(True)
            
            print("DEBUG: Drag and drop handlers initialized successfully")
        except Exception as e:
            print(f"ERROR initializing drag and drop: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to basic drag-drop
            self.tree.setDragEnabled(True)
            self.tree.setAcceptDrops(True)
            self.tree.setDropIndicatorShown(True)
            self.tree.setDragDropMode(QAbstractItemView.InternalMove)
    
    def _init_structure_converter(self):
        """Initialize the structure converter"""
        try:
            # Import structure converter
            from app.ui.structure_editor.structure_converter import StructureConverter
            
            # Create instance - pass self as the editor
            self.structure_converter = StructureConverter(editor=self)
            
            # Set the tree reference if it exists
            if hasattr(self, 'tree'):
                self.structure_converter.tree_widget = self.tree
                print("DEBUG: Set tree on structure converter")
                
            print("DEBUG: Structure converter initialized")
        except Exception as e:
            print(f"ERROR initializing structure converter: {e}")
            import traceback
            traceback.print_exc()
    
    def load_structure(self, structure):
        """Load a structure into the tree widget"""
        try:
            print(f"DEBUG: EnhancedStructureEditor.load_structure called with: {structure}")
            
            # Clear the tree
            self.tree.clear()
            
            if not structure:
                print("DEBUG: No structure provided to load")
                return
            
            # Use structure converter if available
            if hasattr(self, 'structure_converter') and self.structure_converter:
                print("DEBUG: Using structure converter to load structure")
                self.structure_converter.load_structure(structure)
                return
                
            # Fallback to direct loading if no converter
            print("DEBUG: No structure converter available, using direct loading")
            
            # Normalize structure format to handle different structure formats
            normalized_structure = self._normalize_structure_format(structure)
            print(f"DEBUG: Normalized structure: {normalized_structure}")
            
            # Load structure elements into the tree
            for item in normalized_structure:
                if isinstance(item, dict) and "name" in item and "type" in item:
                    tree_item = QTreeWidgetItem([item["name"], item["type"]])
                    
                    # Store the full item data as user data
                    tree_item.setData(0, Qt.UserRole, item)
                    
                    # If it's a folder, add children
                    if item["type"] == "folder" and "children" in item:
                        self._add_children(tree_item, item["children"])
                    
                    self.tree.addTopLevelItem(tree_item)
                else:
                    print(f"DEBUG: Skipping invalid structure item: {item}")
            
            # Expand all items for better visibility
            self.tree.expandAll()
            
        except Exception as e:
            print(f"ERROR loading structure: {e}")
            import traceback
            traceback.print_exc()
    
    def _normalize_structure_format(self, structure):
        """Normalize structure format to handle different structure representations"""
        if not structure:
            return []
            
        # If the structure is already a list of items, use it directly
        if isinstance(structure, list):
            return structure
            
        # If the structure is a dictionary with 'directories' key, use that
        if isinstance(structure, dict) and "directories" in structure:
            return structure["directories"]
            
        # If we have a different format, try to convert it
        normalized = []
        
        # Handle case where structure is a dictionary with file/folder entries
        if isinstance(structure, dict):
            for name, entry in structure.items():
                if isinstance(entry, list):
                    # This is a folder with children
                    folder = {"name": name, "type": "folder", "children": self._normalize_structure_format(entry)}
                    normalized.append(folder)
                else:
                    # This is a file
                    file = {"name": name, "type": "file"}
                    normalized.append(file)
        
        return normalized
    
    def _add_children(self, parent_item, children):
        """Add child items to a parent item recursively"""
        for child in children:
            if isinstance(child, dict) and "name" in child and "type" in child:
                child_item = QTreeWidgetItem([child["name"], child["type"]])
                
                # Store the full item data as user data
                child_item.setData(0, Qt.UserRole, child)
                
                # If it's a folder, add children recursively
                if child["type"] == "folder" and "children" in child:
                    self._add_children(child_item, child["children"])
                
                parent_item.addChild(child_item)
            else:
                print(f"DEBUG: Skipping invalid child item: {child}")
    
    def get_structure(self):
        """Get the current structure from the tree widget"""
        structure = []
        
        # Process all top-level items
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            structure.append(self._process_item(item))
        
        return structure
    
    def _process_item(self, item):
        """Process a tree item and its children into a structure dictionary"""
        result = {
            "name": item.text(0),
            "type": item.text(1)
        }
        
        # If it's a folder, process children
        if item.text(1) == "folder":
            children = []
            for i in range(item.childCount()):
                child = item.child(i)
                children.append(self._process_item(child))
            result["children"] = children
        
        return result
    
    def add_folder(self):
        """Add a new folder to the structure"""
        print("DEBUG: add_folder method called")
        # Get parent item (if any)
        selected = self.tree.selectedItems()
        parent = None
        
        if selected:
            item = selected[0]
            # Only folders can have children
            if item.text(1) == "folder":
                parent = item
        
        # Get folder name
        folder_name, ok = QInputDialog.getText(self, "Add Folder", "Folder name:")
        if ok and folder_name:
            print(f"DEBUG: Adding folder '{folder_name}'")
            new_item = QTreeWidgetItem([folder_name, "folder"])
            
            # Add to parent or top level
            if parent:
                parent.addChild(new_item)
                parent.setExpanded(True)
                print(f"DEBUG: Added folder '{folder_name}' to parent '{parent.text(0)}'")
            else:
                self.tree.addTopLevelItem(new_item)
                print(f"DEBUG: Added folder '{folder_name}' to top level")
        else:
            print("DEBUG: Folder creation canceled or empty name")
    
    def add_file(self):
        """Add a new file to the structure"""
        print("DEBUG: add_file method called")
        # Get parent item (if any)
        selected = self.tree.selectedItems()
        parent = None
        
        if selected:
            item = selected[0]
            # Only folders can have children
            if item.text(1) == "folder":
                parent = item
        
        # Get file name
        file_name, ok = QInputDialog.getText(self, "Add File", "File name:")
        if ok and file_name:
            print(f"DEBUG: Adding file '{file_name}'")
            new_item = QTreeWidgetItem([file_name, "file"])
            
            # Add to parent or top level
            if parent:
                parent.addChild(new_item)
                parent.setExpanded(True)
                print(f"DEBUG: Added file '{file_name}' to parent '{parent.text(0)}'")
            else:
                self.tree.addTopLevelItem(new_item)
                print(f"DEBUG: Added file '{file_name}' to top level")
        else:
            print("DEBUG: File creation canceled or empty name")
    
    def edit_item(self):
        """Edit the selected item"""
        selected = self.tree.selectedItems()
        if not selected:
            return
        
        item = selected[0]
        name = item.text(0)
        item_type = item.text(1)
        
        # Get new name
        new_name, ok = QInputDialog.getText(self, f"Edit {item_type.capitalize()}", 
                                         f"{item_type.capitalize()} name:", 
                                         text=name)
        if ok and new_name:
            item.setText(0, new_name)
    
    def remove_item(self):
        """Remove the selected item"""
        selected = self.tree.selectedItems()
        if not selected:
            return
        
        item = selected[0]
        
        # Confirm deletion
        result = QMessageBox.question(self, "Confirm Deletion", 
                                   f"Are you sure you want to delete '{item.text(0)}'?", 
                                   QMessageBox.Yes | QMessageBox.No)
        
        if result == QMessageBox.Yes:
            # Get the parent item
            parent = item.parent()
            
            # Remove from parent or top level
            if parent:
                parent.removeChild(item)
            else:
                index = self.tree.indexOfTopLevelItem(item)
                self.tree.takeTopLevelItem(index)
    
    def show_context_menu(self, position):
        """Show context menu for the tree widget"""
        selected = self.tree.selectedItems()
        if not selected:
            return
        
        item = selected[0]
        menu = QMenu()
        
        # Add action depends on selection
        if item.text(1) == "folder":
            add_folder = menu.addAction("Add Folder Here")
            add_file = menu.addAction("Add File Here")
        
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")
        
        # Show the menu
        action = menu.exec_(self.tree.viewport().mapToGlobal(position))
        
        # Handle action
        if not action:
            return
        
        if item.text(1) == "folder":
            if action == add_folder:
                # Get folder name
                folder_name, ok = QInputDialog.getText(self, "Add Folder", "Folder name:")
                if ok and folder_name:
                    new_item = QTreeWidgetItem([folder_name, "folder"])
                    item.addChild(new_item)
                    item.setExpanded(True)
            elif action == add_file:
                # Get file name
                file_name, ok = QInputDialog.getText(self, "Add File", "File name:")
                if ok and file_name:
                    new_item = QTreeWidgetItem([file_name, "file"])
                    item.addChild(new_item)
                    item.setExpanded(True)
        
        if action == edit_action:
            self.edit_item()
        elif action == delete_action:
            self.remove_item()
    
    def accept(self):
        """Handle dialog acceptance"""
        from app.utils.template_validator import TemplateValidator
        from PyQt5.QtWidgets import QMessageBox, QApplication
        
        print("DEBUG: Starting accept method")
        
        # Get values from form
        template = {
            "name": self.name_field.text().strip(),
            "type": self.category_field.currentText(),
            "description": self.description_field.toPlainText().strip(),
            "path": self.get_current_path() if hasattr(self, 'get_current_path') else ""
        }
        
        print(f"DEBUG: Initial template data: {template}")
        
        # Validate and fix template data
        is_valid, fixed_template, messages = TemplateValidator.validate_and_fix_template(template)
        
        # If name was empty and auto-generated
        if fixed_template["name"] != template["name"]:
            print(f"DEBUG: Name was auto-generated: {fixed_template['name']}")
            
            # Update UI with new name
            self.name_field.setText(fixed_template["name"])
            QApplication.processEvents()
            
            # Update internal state
            self._template_name = fixed_template["name"]
            
            # Inform user
            QMessageBox.information(self, "Auto-generated Name", 
                                  f"No template name was provided. Your template will be saved as '{fixed_template['name']}'.\n\n"
                                  "You can rename it later from the template gallery.")
        
        # Show any other validation messages
        if messages:
            QMessageBox.information(self, "Template Validation", "\n".join(messages))
        
        # If not valid, show error and return
        if not is_valid:
            QMessageBox.critical(self, "Validation Error", "Please fix the following issues:\n\n" + "\n".join(messages))
            return
        
        # Check if this is a rename operation
        if hasattr(self, 'original_template_name') and self.original_template_name and self.original_template_name != fixed_template["name"]:
            print(f"DEBUG: This is a rename operation from '{self.original_template_name}' to '{fixed_template['name']}'")
            # Emit signal again to ensure rename is processed
            self.template_renamed.emit(self.original_template_name, fixed_template["name"])
        
        # Get updated structure from tree
        updated_structure = self.get_structure()
        
        # Generate complete structure data
        structure_data = {
            'name': self.get_structure_name(),
            'display_name': fixed_template["name"],
            'directories': updated_structure
        }
        
        print(f"DEBUG: Final structure data: {structure_data}")
        
        # Accept the dialog
        super().accept() 
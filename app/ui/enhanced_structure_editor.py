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
    
    def __init__(self, parent=None, structure_name="", structure=None, is_new=False, project_type=None, template_manager=None, template_data=None):
        super().__init__(parent)
        self.parent = parent
        
        print(f"DEBUG EnhancedStructureEditor.__init__ called")
        print(f"  structure_name: {structure_name}")
        print(f"  is_new: {is_new}")
        print(f"  template_data provided: {template_data is not None}")
        
        # Store template manager instance
        self.template_manager = template_manager
        
        # Initialize properties based on passed arguments or defaults
        self._is_new = is_new
        self._structure_name = structure_name if structure_name else ""
        
        # Extract initial values from template_data if provided
        initial_name = ""
        initial_description = ""
        initial_category = "Custom" # Default category
        
        if template_data and isinstance(template_data, dict):
            initial_name = template_data.get('name', '')
            initial_description = template_data.get('description', '')
            initial_category = template_data.get('category', template_data.get('type', 'Custom'))
            self._structure_name = template_data.get('structure_name', self._structure_name)
            print(f"  Loaded from template_data: name='{initial_name}', desc='{initial_description}', category='{initial_category}', struct_name='{self._structure_name}'")
        elif structure_name and structure_name.startswith("Template_"):
            initial_name = structure_name[len("Template_"):]
            print(f"  Derived name from structure_name: '{initial_name}'")
        
        self._template_name = initial_name
        self._template_description = initial_description
        self._template_category = initial_category
        
        # Set window title based on mode and name
        title = "Add New Template" if self._is_new else f"Edit Template: {self._template_name}"
        self.setWindowTitle(title)
        self.resize(800, 600)  # Set initial size
        
        # Initialize file operations handler
        self.file_operations = FileOperationsHandler(self)
        
        # Initialize structure converter BEFORE creating UI
        self._init_structure_converter() 
        
        # Create UI Builder and UI components
        self.ui_builder = None # Initialize ui_builder reference
        self._create_ui() # This method should assign self.ui_builder and create widgets like self.name_field

        # --- Direct population of UI fields AFTER creation ---
        if hasattr(self, 'name_field') and self.name_field: 
            print(f"  Clearing placeholder text before setting name...")
            self.name_field.setPlaceholderText("") # Clear placeholder
            
            # Block signals, set text, unblock signals
            print(f"  Blocking signals for name_field")
            self.name_field.blockSignals(True)
            try:
                self.name_field.setText(self._template_name)
                print(f"  Directly set name_field text (signals blocked) to: '{self._template_name}'")
            finally:
                self.name_field.blockSignals(False)
                print(f"  Unblocked signals for name_field")
                
            # Force immediate UI update attempt (Keep this for now)
            # self.name_field.repaint()
            # QApplication.processEvents()
        else:
            # print("  WARN: name_field not found after _create_ui() in __init__")
            pass # name_field might be intentionally absent for some sub-classes
            
        if hasattr(self, 'description_field') and self.description_field:
            self.description_field.setPlainText(self._template_description)
        
        if hasattr(self, 'category_field') and self.category_field:
            category_index = self.category_field.findText(self._template_category)
            if category_index != -1:
                self.category_field.setCurrentIndex(category_index)
            else:
                self.category_field.addItem(self._template_category)
                self.category_field.setCurrentText(self._template_category)
        # -----------------------------------------------------
            
        print(f"  UI Populated Check: name='{self.name_field.text() if hasattr(self, 'name_field') else 'N/A'}', category='{self.category_field.currentText() if hasattr(self, 'category_field') else 'N/A'}'")

        # Load structure data AFTER tree widget exists
        structure_to_load = structure if structure else (template_data.get('structure') if template_data else None)
        if structure_to_load:
            print(f"  Loading structure...")
            self.load_structure(structure_to_load)
        else:
             print(f"  No initial structure to load.")

        # Initialize drag and drop AFTER tree widget exists
        self.init_drag_drop_handlers()
        
        # Setup a timer to ensure the name field is populated after the dialog is fully initialized
        QTimer.singleShot(100, self._ensure_name_field_populated)
    
    def _create_ui(self):
        """Create the main user interface"""
        print("DEBUG: _create_ui called")
        # Import UIBuilder locally if needed or ensure it's imported at module level
        from app.ui.structure_editor.ui_components import UIBuilder
        
        # Create the UI Builder instance
        # Pass self (the editor instance) to UIBuilder
        self.ui_builder = UIBuilder(self)
        print("DEBUG: UIBuilder instance created")
        
        # Get the main layout from the UI Builder
        main_layout = self.ui_builder.init_ui()
        print("DEBUG: UIBuilder.init_ui() called, main_layout obtained")
        
        # --- Assign widget references created by UIBuilder to self --- 
        if hasattr(self.ui_builder, 'template_name_field'):
            self.name_field = self.ui_builder.template_name_field
            print("DEBUG: Assigned self.name_field from ui_builder")
        else:
            # print("WARN: ui_builder missing template_name_field")
            self.name_field = None # Or some default QLineEdit
            
        if hasattr(self.ui_builder, 'template_category_field'):
            self.category_field = self.ui_builder.template_category_field
            print("DEBUG: Assigned self.category_field from ui_builder")
        else:
            # print("WARN: ui_builder missing template_category_field")
            self.category_field = None # Or some default QComboBox
            
        if hasattr(self.ui_builder, 'template_info_field'):
            self.description_field = self.ui_builder.template_info_field # Assuming this maps to description
            print("DEBUG: Assigned self.description_field from ui_builder.template_info_field")
        else:
            # print("WARN: ui_builder missing template_info_field")
            self.description_field = None # Or some default QTextEdit
            
        if hasattr(self.ui_builder, 'tree'):
            self.tree = self.ui_builder.tree
            print("DEBUG: Assigned self.tree from ui_builder")
            # Connect context menu AFTER tree is assigned
            if hasattr(self, 'show_context_menu'):
                 self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
                 self.tree.customContextMenuRequested.connect(self.show_context_menu)
        else:
            # print("WARN: ui_builder missing tree")
            self.tree = None # Or some default QTreeWidget
        # ----------------------------------------------------------
        
        # Set the layout for the dialog
        self.setLayout(main_layout)
        print("DEBUG: Main layout set for EnhancedStructureEditor dialog")
    
    def set_template_name(self, name):
        """Set the template name"""
        print(f"DEBUG EnhancedStructureEditor.set_template_name called with: {name}")
        if not hasattr(self, 'name_field') or self.name_field is None:
            # print("  WARN: name_field not found in set_template_name")
            return
        self.name_field.setText(name)
        self._template_name = name
        if hasattr(self, 'name_field') and self.name_field:
            self.name_field.setText(name)
            print(f"  set_template_name updated name_field text to: '{name}'")
        else:
            print("  WARN: name_field not found in set_template_name")
    
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
    
    def on_template_name_changed(self, text):
        """Handle changes to the template name FIELD"""
        print(f"DEBUG: on_template_name_changed triggered with text: '{text}'")
        # Get the current text directly from the sender widget to be sure
        sender = self.sender() 
        current_widget_text = sender.text() if sender else text # Fallback to argument
        print(f"  Current widget text: '{current_widget_text}'")
        print(f"  Internal _template_name BEFORE update: '{self._template_name}'")

        # Only update internal state if the change wasn't programmatic (prevents feedback loop)
        # We assume programmatic changes correctly updated _template_name already.
        # Compare widget text to internal state.
        if current_widget_text == self._template_name:
             print("  Widget text matches internal state. Likely programmatic change or no actual change. Ignoring.")
             return

        print(f"  Widget text '{current_widget_text}' differs from internal '{self._template_name}'. User edit detected.")

        # Update internal name based on the actual USER change in the widget
        old_internal_name = self._template_name
        self._template_name = current_widget_text # Update internal state from widget
        new_internal_name = self._template_name
        
        print(f"  Internal _template_name AFTER update: '{self._template_name}'")

        # If this is a new template, update structure name to match
        if self._is_new or not self._structure_name:
            structure_name = f"Template_{new_internal_name}"
            if self._structure_name != structure_name:
                 self._structure_name = structure_name
                 print(f"📝 STRUCTURE EDITOR: Updated structure name to '{structure_name}' (is_new={self._is_new})")
        
        # Emit signal if name actually changed and isn't empty
        # Compare the internal names before/after update
        if old_internal_name is not None and new_internal_name and old_internal_name != new_internal_name:
            print(f"📝 STRUCTURE EDITOR: Emitting template_renamed from '{old_internal_name}' to '{new_internal_name}'")
            self.template_renamed.emit(old_internal_name, new_internal_name)
        else:
             print("  Not emitting template_renamed (no change or empty)")
    
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
        
        print("DEBUG: EnhancedStructureEditor.accept method called")
        
        # --- Get the template name with fallbacks ---
        template_name = ""
        if hasattr(self, 'name_field') and self.name_field:
            template_name = self.name_field.text().strip()
            print(f"DEBUG: Got name from name_field: '{template_name}'")
        
        # If name field is empty, try using the internal template name
        if not template_name and self._template_name:
            template_name = self._template_name
            print(f"DEBUG: Name field empty, using internal _template_name: '{template_name}'")
            
            # Also update the name field for consistency
            if hasattr(self, 'name_field') and self.name_field:
                self.name_field.setText(template_name)
                QApplication.processEvents()
        
        # If still empty, extract from window title as last resort
        if not template_name:
            # Extract from window title (format: "Edit Template: template_name")
            window_title = self.windowTitle()
            if window_title and ":" in window_title:
                template_name = window_title.split(":", 1)[1].strip()
                print(f"DEBUG: Extracted name from window title: '{template_name}'")
        
        # Get values from form, prioritizing our multi-fallback name
        template = {
            "name": template_name, 
            "type": self.category_field.currentText() if hasattr(self, 'category_field') else "Custom",
            "description": self.description_field.toPlainText().strip() if hasattr(self, 'description_field') else "",
            "path": self.get_current_path() if hasattr(self, 'get_current_path') else ""
        }
        
        print(f"DEBUG: Template data for validation: {template}")
        
        # Validate and fix template data (including generating name if still empty)
        is_valid, fixed_template, messages = TemplateValidator.validate_and_fix_template(template)
        
        # If name was empty and auto-generated
        if fixed_template["name"] != template["name"]:
            print(f"DEBUG: Name was auto-generated: {fixed_template['name']}")
            
            # Update UI with new name
            if hasattr(self, 'name_field') and self.name_field:
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
        
        # Accept the dialog - call the parent class accept method
        super().accept()

    def _ensure_name_field_populated(self):
        """Ensure the name field is populated with the template name after the dialog is fully initialized"""
        print(f"DEBUG: _ensure_name_field_populated called, template name is: '{self._template_name}'")
        if hasattr(self, 'name_field') and self.name_field and self._template_name:
            current_text = self.name_field.text()
            if not current_text and self._template_name:
                print(f"DEBUG: Name field is empty, setting to: '{self._template_name}'")
                self.name_field.setText(self._template_name)
                
                # Force UI update
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
                
                # Extra check to verify the text was set
                if self.name_field.text() != self._template_name:
                    print(f"WARNING: Failed to set name field text, current text: '{self.name_field.text()}'")
                    # Try again with blocked signals
                    self.name_field.blockSignals(True)
                    try:
                        self.name_field.setText(self._template_name)
                    finally:
                        self.name_field.blockSignals(False)
                        
                    QApplication.processEvents()
                    print(f"DEBUG: After second attempt, name field text is: '{self.name_field.text()}'")
            else:
                print(f"DEBUG: Name field already has text: '{current_text}', no need to set")
        else:
            print("DEBUG: Could not find name field or template name is empty")

    def showEvent(self, event):
        """This event is called when the dialog is shown on screen"""
        super().showEvent(event)
        
        print(f"DEBUG: EnhancedStructureEditor.showEvent called, template name is: '{self._template_name}'")
        
        # Ensure name field is properly populated
        if hasattr(self, 'name_field') and self.name_field and self._template_name:
            current_text = self.name_field.text()
            if not current_text or current_text != self._template_name:
                print(f"DEBUG: showEvent - Setting name field to: '{self._template_name}'")
                self.name_field.blockSignals(True)
                try:
                    self.name_field.setText(self._template_name)
                finally:
                    self.name_field.blockSignals(False)
                
                # Force UI update
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
                
                print(f"DEBUG: showEvent - After setting, name field text is: '{self.name_field.text()}'")
            else:
                print(f"DEBUG: showEvent - Name field already has correct text: '{current_text}'")
        else:
            print("DEBUG: showEvent - Could not find name field or template name is empty")
            
    def keyPressEvent(self, event):
        """Handle key press events for the dialog"""
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QApplication, QLineEdit, QTextEdit, QComboBox
        
        # Handle Delete key press
        if event.key() == Qt.Key_Delete:
            print("DEBUG: Delete key pressed, calling delete_selected()")
            self.delete_selected()
            # Don't pass to parent class
            event.accept()
            return True
            
        # Handle Escape key
        elif event.key() == Qt.Key_Escape:
            print("DEBUG: Escape key pressed, rejecting dialog")
            self.reject()  # Close dialog without saving
            event.accept()
            return
            
        # Handle Return/Enter key in special cases
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Only handle Return key if the focus is not in a text field
            focused_widget = QApplication.focusWidget()
            if not isinstance(focused_widget, (QLineEdit, QTextEdit, QComboBox)):
                print("DEBUG: Enter key pressed with no text field focused, accepting dialog")
                self.accept()  # Save and close
                event.accept()
                return
        
        # Let parent class handle any other keys
        print(f"DEBUG: Passing key {event.key()} to parent class")
        super().keyPressEvent(event)
    
    def delete_selected(self):
        """Delete the selected items from the tree"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
        
        print(f"DEBUG: delete_selected - {len(selected_items)} items selected for deletion")
        deleted_count = 0
        
        for item in selected_items[:]:  # Make a copy of the list to avoid modification issues
            # Get parent
            parent = item.parent()
            
            try:
                if parent:
                    # If item has a parent, remove it from the parent
                    print(f"DEBUG: delete_selected - removing child item '{item.text(0)}' from parent '{parent.text(0)}'")
                    parent.removeChild(item)
                    deleted_count += 1
                    print(f"DEBUG: delete_selected - child item removed successfully")
                else:
                    # If item is a top-level item, remove it from the tree
                    print(f"DEBUG: delete_selected - removing top-level item '{item.text(0)}'")
                    index = self.tree.indexOfTopLevelItem(item)
                    if index >= 0:  # Make sure the item is actually found in the tree
                        self.tree.takeTopLevelItem(index)
                        deleted_count += 1
                        print(f"DEBUG: delete_selected - top-level item removed successfully")
            except Exception as e:
                print(f"ERROR: Failed to delete item '{item.text(0)}': {e}")
        
        print(f"DEBUG: delete_selected - {deleted_count} items deleted successfully")
        
        # Return True to indicate success
        return True 
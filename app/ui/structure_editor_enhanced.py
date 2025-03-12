#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem,
                            QMessageBox, QGroupBox, QComboBox, QCheckBox,
                            QMenu, QAction, QStyle, QApplication, QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, COMBOBOX_STYLE

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
        self.structure_combo.setStyleSheet(COMBOBOX_STYLE)
        
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
        
        # Add drag and drop hint
        drag_drop_hint = QLabel("Tip: You can drag and drop folders from your file system to quickly import an existing structure.")
        drag_drop_hint.setWordWrap(True)
        drag_drop_hint.setStyleSheet("color: #666; font-style: italic; font-size: 12px;")
        info_layout.addWidget(drag_drop_hint)
        
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
        
        # Enable drag and drop for the tree widget
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDragDropMode(QTreeWidget.DragDrop)
        self.tree.viewport().setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        
        # Override drag and drop events
        self.tree.dragEnterEvent = self._tree_dragEnterEvent
        self.tree.dragMoveEvent = self._tree_dragMoveEvent
        self.tree.dropEvent = self._tree_dropEvent
        
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
        delete_btn.clicked.connect(lambda: self.delete_item(None))
        delete_btn.setStyleSheet(BUTTON_STYLE)
        
        import_btn = QPushButton("Import from Folder")
        import_btn.clicked.connect(self.import_from_folder)
        import_btn.setStyleSheet(BUTTON_STYLE)
        
        structure_buttons.addWidget(add_folder_btn)
        structure_buttons.addWidget(add_file_btn)
        structure_buttons.addWidget(delete_btn)
        structure_buttons.addWidget(import_btn)
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
        
        # Always show all built-in structures, regardless of project type
        for name in sorted(DEFAULT_STRUCTURES.keys()):
            self.structure_combo.addItem(name, name)
        
        # Add custom structures section if template manager is available
        if self.template_manager and hasattr(self.template_manager, 'custom_structures'):
            self.structure_combo.addItem("=== Custom Structures ===", None)
            
            # Always show all custom structures
            for name in sorted(self.template_manager.custom_structures.keys()):
                self.structure_combo.addItem(name, name)
        
        # If a structure_name was provided, try to select it
        if self.structure_name:
            index = self.structure_combo.findText(self.structure_name)
            if index >= 0:
                self.structure_combo.setCurrentIndex(index)
        # Otherwise if project_type is provided, find and select the default structure for that type
        elif self.project_type:
            default_structure = PROJECT_TYPE_TO_STRUCTURE.get(self.project_type)
            if default_structure:
                index = self.structure_combo.findText(default_structure)
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
        print("DEBUG: EnhancedStructureEditor.add_folder called")
        
        # Handle boolean (from signal) same as None
        if isinstance(parent, bool):
            print("DEBUG: Received boolean instead of parent item, using None")
            parent = None
        
        # If no parent specified, use selected item or root
        if parent is None:
            parent = self.tree.currentItem()
            
        # If still no parent, use root
        if parent is None:
            parent = self.tree.invisibleRootItem().child(0)
        
        # Ensure parent is a QTreeWidgetItem
        if not hasattr(parent, 'text') or not hasattr(parent, 'childCount'):
            print("DEBUG: Invalid parent for add_folder")
            parent = self.tree.invisibleRootItem().child(0)
            
        # If parent is a file, use its parent
        if parent and parent.data(0, Qt.UserRole) == "file":
            parent = parent.parent() or self.tree.invisibleRootItem().child(0)
            
        folder_name, ok = QInputDialog.getText(self, "Add Folder", "Folder name:")
        if ok and folder_name:
            print(f"DEBUG: Creating folder '{folder_name}'")
            
            # Create folder item
            folder_item = QTreeWidgetItem(parent)
            folder_item.setText(0, folder_name)
            folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
            # Mark this item as a folder in user data
            folder_item.setData(0, Qt.UserRole, "folder")
            
            # Expand parent if it's a valid QTreeWidgetItem
            if hasattr(parent, 'setExpanded'):
                parent.setExpanded(True)
                
            # Force the tree to update
            self.tree.update()
            
            # Make the new folder visible by selecting it
            self.tree.setCurrentItem(folder_item)
            
            print(f"DEBUG: Added folder '{folder_name}' successfully")
            
    def add_file(self, parent=None):
        """Add a file to the structure"""
        print("DEBUG: EnhancedStructureEditor.add_file called")
        
        # Handle boolean (from signal) same as None
        if isinstance(parent, bool):
            print("DEBUG: Received boolean instead of parent item, using None")
            parent = None
        
        # If no parent specified, use selected item or root
        if parent is None:
            parent = self.tree.currentItem()
            
        # If still no parent, use root
        if parent is None:
            parent = self.tree.invisibleRootItem().child(0)
            
        # Ensure parent is a QTreeWidgetItem
        if not hasattr(parent, 'text') or not hasattr(parent, 'childCount'):
            print("DEBUG: Invalid parent for add_file")
            parent = self.tree.invisibleRootItem().child(0)
            
        # If parent is a file, use its parent
        if parent and parent.data(0, Qt.UserRole) == "file":
            parent = parent.parent() or self.tree.invisibleRootItem().child(0)
        
        # First try to browse for an existing file
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*)"
        )
        
        if file_path and os.path.exists(file_path):
            # Get file name and suggest a placeholder version
            original_filename = os.path.basename(file_path)
            filename_base, filename_ext = os.path.splitext(original_filename)
            suggested_name = f"{{{{PROJECT_NAME}}}}{filename_ext}"
            
            # Ask user to confirm or modify the filename
            file_name, ok = QInputDialog.getText(
                self, 
                "File Name", 
                "Enter file name (use {{PROJECT_NAME}} as placeholder):",
                text=suggested_name
            )
            
            if ok and file_name:
                # Create file item
                file_item = QTreeWidgetItem(parent)
                file_item.setText(0, file_name)
                file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
                # Mark this item as a file in user data
                file_item.setData(0, Qt.UserRole, "file")
                
                # Expand parent if it's a valid QTreeWidgetItem
                if hasattr(parent, 'setExpanded'):
                    parent.setExpanded(True)
                
                # Force the tree to update
                self.tree.update()
                
                # Make the new file visible by selecting it
                self.tree.setCurrentItem(file_item)
                
                print(f"DEBUG: Added file '{file_name}' successfully")
                return
                
        # If no file selected, fall back to just entering a name
        file_name, ok = QInputDialog.getText(self, "Add File", "File name:")
        if ok and file_name:
            # Create file item
            file_item = QTreeWidgetItem(parent)
            file_item.setText(0, file_name)
            file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
            # Mark this item as a file in user data
            file_item.setData(0, Qt.UserRole, "file")
            
            # Expand parent if it's a valid QTreeWidgetItem
            if hasattr(parent, 'setExpanded'):
                parent.setExpanded(True)
            
            # Force the tree to update
            self.tree.update()
            
            # Make the new file visible by selecting it
            self.tree.setCurrentItem(file_item)
            
            print(f"DEBUG: Added file '{file_name}' successfully")
            
    def delete_item(self, item=None):
        """Delete an item from the structure"""
        print("DEBUG: EnhancedStructureEditor.delete_item called")
        
        # Properly handle triggered signals that might pass a boolean
        # Qt signals often pass True when triggered, which we need to handle
        if isinstance(item, bool):
            print("DEBUG: Received boolean instead of item, using current selection")
            item = None
            
        # If no item specified or boolean passed instead, use selected item
        if item is None:
            item = self.tree.currentItem()
            if item is None:
                print("DEBUG: No item selected for deletion")
                return
            
        # Check if this is the root item
        root_item = self.tree.invisibleRootItem().child(0)
        if item == root_item:
            print("DEBUG: Cannot delete root item")
            return
            
        # Safety check for item validity
        try:
            item_text = item.text(0)
            print(f"DEBUG: Attempting to delete item: '{item_text}'")
        except Exception as e:
            print(f"DEBUG: Invalid item for deletion: {e}")
            return
            
        # No confirmation dialog - directly delete the item
        try:
            # Get parent of the item
            parent = item.parent()
            
            # Remove the item
            if parent:
                index = parent.indexOfChild(item)
                if index >= 0:
                    # Use takeChild which properly detaches the item
                    taken_item = parent.takeChild(index)
                    
                    # Select the parent after deletion
                    self.tree.setCurrentItem(parent)
            else:
                # If no parent, get index and remove directly from the tree
                index = self.tree.indexOfTopLevelItem(item)
                if index >= 0:
                    taken_item = self.tree.takeTopLevelItem(index)
            
            # Force the tree to update
            self.tree.update()
            self.tree.viewport().update()
            
            print(f"DEBUG: Deleted item '{item_text}' successfully")
        except Exception as e:
            print(f"DEBUG: Error deleting item: {e}")
            QMessageBox.warning(self, "Delete Error", f"Could not delete item: {str(e)}")
                
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
            
    def _tree_dragEnterEvent(self, event):
        """Custom drag enter event for the tree widget"""
        print("DEBUG: Tree dragEnterEvent")
        if event.mimeData().hasUrls():
            print("DEBUG: Drag has URLs - accepting")
            event.acceptProposedAction()
        else:
            print("DEBUG: Internal drag - letting tree widget handle it")
            # For internal drag/drop operations
            QTreeWidget.dragEnterEvent(self.tree, event)
            
    def _tree_dragMoveEvent(self, event):
        """Custom drag move event for the tree widget"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            # For internal drag/drop operations
            QTreeWidget.dragMoveEvent(self.tree, event)
    
    def _tree_dropEvent(self, event):
        """Custom drop event for the tree widget"""
        print("DEBUG: Tree dropEvent called")
        if event.mimeData().hasUrls():
            print("DEBUG: External drop with URLs")
            # Get drop position
            drop_item = self.tree.itemAt(event.pos())
            if not drop_item:
                drop_item = self.tree.invisibleRootItem().child(0)  # Root item
                print("DEBUG: No item at drop position, using root")
            else:
                print(f"DEBUG: Dropping onto item: '{drop_item.text(0)}'")
                
            # Process the dropped URLs
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                
                # Clean up the path - remove trailing slashes
                file_path = file_path.rstrip(os.path.sep)
                
                print(f"DEBUG: Processing dropped URL: {file_path}")
                
                # Make sure path exists
                if not os.path.exists(file_path):
                    print(f"DEBUG: Path does not exist: {file_path}")
                    continue
                    
                # If it's a directory, import its structure
                if os.path.isdir(file_path):
                    print(f"DEBUG: Importing directory structure: {file_path}")
                    self._process_dropped_directory(file_path, drop_item)
                else:
                    print(f"DEBUG: Skipping file drop (only directories supported): {file_path}")
                    
            # Accept the drop action
            event.acceptProposedAction()
        else:
            # Handle internal drag/drop - custom implementation for moving items
            print("DEBUG: Internal tree drag-and-drop")
            try:
                # Get the current item being dragged
                current_item = self.tree.currentItem()
                if not current_item:
                    print("DEBUG: No item selected for drag")
                    event.ignore()
                    return
                
                # Can't move the root item
                root_item = self.tree.invisibleRootItem().child(0)
                if current_item == root_item:
                    print("DEBUG: Cannot move root item")
                    event.ignore()
                    return
                
                # Get the target item
                target_item = self.tree.itemAt(event.pos())
                if not target_item:
                    target_item = root_item  # Default to root
                    print("DEBUG: No target item at position, using root")
                    
                print(f"DEBUG: Moving '{current_item.text(0)}' to '{target_item.text(0)}'")
                
                # If target is a file, use its parent as the target
                if target_item.data(0, Qt.UserRole) == "file":
                    target_item = target_item.parent() or root_item
                    print(f"DEBUG: Target is a file, using parent: '{target_item.text(0)}'")
                
                # Prevent dropping an item onto itself
                if current_item == target_item:
                    print("DEBUG: Cannot drop item onto itself")
                    event.ignore()
                    return
                
                # Prevent dropping an item into one of its children
                parent = target_item
                while parent:
                    if parent == current_item:
                        print("DEBUG: Cannot drop item into its own child")
                        event.ignore()
                        return
                    parent = parent.parent()
                
                # Store current item's data and properties
                item_text = current_item.text(0)
                item_type = current_item.data(0, Qt.UserRole)
                item_expanded = current_item.isExpanded()
                
                print(f"DEBUG: Creating new item '{item_text}' in target")
                # Create a new item in the target location
                new_item = QTreeWidgetItem(target_item)
                new_item.setText(0, item_text)
                new_item.setData(0, Qt.UserRole, item_type)
                
                # Set proper icon based on type
                if item_type == "folder":
                    new_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                else:
                    new_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
                
                # If the item has children, recursively move them too
                child_count = current_item.childCount()
                if child_count > 0:
                    print(f"DEBUG: Moving {child_count} children")
                    self._move_children(current_item, new_item)
                
                # Delete the original item - save parent reference before deletion
                orig_parent = current_item.parent()
                if orig_parent:
                    print(f"DEBUG: Removing original item from parent '{orig_parent.text(0)}'")
                else:
                    print("DEBUG: Removing original item from top level")
                
                # Remove from parent
                if orig_parent:
                    index = orig_parent.indexOfChild(current_item)
                    if index >= 0:
                        orig_parent.takeChild(index)
                else:
                    index = self.tree.indexOfTopLevelItem(current_item)
                    if index >= 0:
                        self.tree.takeTopLevelItem(index)
                
                # Expand the new item if the original was expanded
                new_item.setExpanded(item_expanded)
                
                # Make the new item visible by selecting it
                self.tree.setCurrentItem(new_item)
                target_item.setExpanded(True)
                
                # Accept the drop
                event.acceptProposedAction()
                print(f"DEBUG: Successfully moved '{item_text}'")
            except Exception as e:
                print(f"DEBUG: Error during internal drag/drop: {e}")
                # Do not call the default handler to avoid duplicating the item
                event.ignore()
    
    def _move_children(self, source_item, target_item):
        """Recursively move children from source to target"""
        # Copy all children
        for i in range(source_item.childCount()):
            child = source_item.child(i)
            child_text = child.text(0)
            child_type = child.data(0, Qt.UserRole)
            
            print(f"DEBUG: Moving child '{child_text}' ({child_type})")
            
            # Create new child
            new_child = QTreeWidgetItem(target_item)
            new_child.setText(0, child_text)
            new_child.setData(0, Qt.UserRole, child_type)
            
            # Set proper icon
            if child_type == "folder":
                new_child.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
            else:
                new_child.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
            
            # Preserve expanded state
            new_child.setExpanded(child.isExpanded())
            
            # Recursively handle children's children
            if child.childCount() > 0:
                print(f"DEBUG: Processing {child.childCount()} sub-children of '{child_text}'")
                self._move_children(child, new_child)
                
    def import_from_folder(self):
        """Import structure from a folder"""
        print("DEBUG: EnhancedStructureEditor.import_from_folder called")
        
        from PyQt5.QtWidgets import QFileDialog
        
        # Get selected folder
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Import Structure From",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not folder_path or not os.path.isdir(folder_path):
            return
            
        # Get the target item (selected or root)
        selected_items = self.tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.tree.invisibleRootItem().child(0)
        
        # Ensure parent is a QTreeWidgetItem
        if not hasattr(parent_item, 'text') or not hasattr(parent_item, 'childCount'):
            print("DEBUG: Invalid parent for import_from_folder")
            parent_item = self.tree.invisibleRootItem().child(0)
        
        # Check if selected item is a file
        if selected_items and selected_items[0].data(0, Qt.UserRole) == "file":
            parent_item = selected_items[0].parent() or self.tree.invisibleRootItem().child(0)
        
        # Process the folder structure
        folder_item = self._process_dropped_directory(folder_path, parent_item)
        
        # Force the tree to update visually
        self.tree.update()
        self.tree.viewport().update()
        self.tree.repaint()
        
        # Make the imported folder visible by selecting it (if it was created)
        if folder_item and hasattr(folder_item, 'setSelected'):
            folder_item.setSelected(True)
            self.tree.scrollToItem(folder_item)
        
        print(f"DEBUG: Imported folder structure from {folder_path}")
        
    def _process_dropped_directory(self, dir_path, parent_item):
        """Process a dropped directory and add it to the structure"""
        # Remove trailing slash if present to ensure we get the correct folder name
        if dir_path.endswith(os.path.sep):
            dir_path = dir_path.rstrip(os.path.sep)
            
        # Get folder name from path
        dir_name = os.path.basename(dir_path)
        
        print(f"DEBUG: Processing directory: '{dir_path}', name: '{dir_name}'")
        
        # If dir_name is empty after removing trailing slash, use the last part of the path
        if not dir_name:
            # Try to extract a meaningful name from the path
            path_parts = dir_path.split(os.path.sep)
            dir_name = next((part for part in reversed(path_parts) if part), "Unnamed Folder")
            print(f"DEBUG: Empty directory name, using '{dir_name}' from path parts")
        
        # Create a folder item
        folder_item = QTreeWidgetItem(parent_item)
        folder_item.setText(0, dir_name)
        folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
        folder_item.setData(0, Qt.UserRole, "folder")
        
        # Expand the parent
        parent_item.setExpanded(True)
        folder_item.setExpanded(True)
        
        # Recursively process subdirectories and files
        try:
            # First, process folders to keep them at the top
            folders = []
            files = []
            
            # Sort items into folders and files
            for item in sorted(os.listdir(dir_path)):
                # Skip hidden files (starting with '.')
                if item.startswith('.'):
                    continue
                    
                item_full_path = os.path.join(dir_path, item)
                if os.path.isdir(item_full_path):
                    folders.append(item_full_path)
                else:
                    files.append(item_full_path)
            
            # Process folders first
            for folder_path in folders:
                self._process_dropped_directory(folder_path, folder_item)
                
            # Then process files
            for file_path in files:
                file_name = os.path.basename(file_path)
                file_item = QTreeWidgetItem(folder_item)
                file_item.setText(0, file_name)
                file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
                file_item.setData(0, Qt.UserRole, "file")
                
            # If this folder has no children but had a name extracted from the path, keep it
            if folder_item.childCount() == 0 and not os.path.basename(dir_path):
                print(f"DEBUG: Empty folder with extracted name: '{dir_name}'")
        except Exception as e:
            print(f"ERROR: Problem processing directory contents: {e}")
            
        return folder_item

    def keyPressEvent(self, event):
        """Handle key press events"""
        # Check for Delete key press or Backspace key (common on Mac)
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            # Delete the selected item(s)
            self.delete_item()
            event.accept()
        else:
            # Pass other key events to parent class
            super().keyPressEvent(event)

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
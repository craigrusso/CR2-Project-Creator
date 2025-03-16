#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QGroupBox, QComboBox, QCheckBox,
    QMenu, QAction, QStyle, QApplication, QInputDialog,
    QSplitter, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QFont, QIcon

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, LINEEDIT_STYLE, LABEL_STYLE, COMBOBOX_STYLE, CONTEXT_MENU_STYLE
from app.templates.components.menu_actions import CustomMenu

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
        # Apply color scheme styling to the input field
        self.name_input.setStyleSheet(LINEEDIT_STYLE)
        if self.structure_name:
            self.name_input.setText(self.structure_name)
        
        # If this is a built-in structure, add a note and disable the name field
        if self.is_built_in:
            self.name_input.setReadOnly(True)
            # Use color style for read-only field
            self.name_input.setStyleSheet(f"""
                background-color: {colors['hover_bg']}; 
                color: {colors['secondary_text']}; 
                border: 1px solid {colors['border']}; 
                padding: 5px; 
                border-radius: 3px;
            """)
            built_in_note = QLabel("This is a built-in structure. To modify it, save as a new structure.")
            built_in_note.setStyleSheet(f"color: {colors['error_text']}; font-style: italic;")
            info_layout.addWidget(built_in_note)
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        info_layout.addLayout(name_layout)
        
        # Category selector (for custom structures only)
        if not self.is_built_in:
            category_layout = QHBoxLayout()
            category_label = QLabel("Category:")
            self.category_combo = QComboBox()
            self.category_combo.setMinimumWidth(250)
            self.category_combo.setStyleSheet(COMBOBOX_STYLE)
            self.populate_category_dropdown()
            
            category_layout.addWidget(category_label)
            category_layout.addWidget(self.category_combo)
            category_layout.addStretch()
            info_layout.addLayout(category_layout)
        
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
        
        # Add "Manage Structures" button
        self.manage_structures_button = QPushButton("Manage")
        self.manage_structures_button.clicked.connect(self.manage_structures)
        self.manage_structures_button.setStyleSheet(BUTTON_STYLE)
        self.manage_structures_button.setToolTip("Organize, rename, or delete structures")
        
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.structure_combo)
        template_layout.addWidget(self.new_structure_button)
        template_layout.addWidget(self.manage_structures_button)
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
        
        # Enable multi-selection
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        
        # Connect double-click event to rename
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        
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
        
        # Apply consistent styling to the tree widget - improved visual feedback
        self.tree.setStyleSheet(f"""
            QTreeWidget {{ 
                background-color: {colors['card_bg']}; 
                color: {colors['text']}; 
                border: 1px solid {colors['border']}; 
            }}
            QTreeWidget::item {{ 
                padding: 3px; 
                border-radius: 2px;
            }}
            QTreeWidget::item:hover {{ 
                background-color: {colors['hover_bg']};
            }}
            QTreeWidget::item:selected {{ 
                background-color: {colors['highlight_bg']}; 
                color: {colors['highlight_text']}; 
                border: 1px solid {colors['accent']};
            }}
            QTreeWidget::item:selected:active {{ 
                background-color: {colors['highlight_bg']}; 
                color: {colors['highlight_text']}; 
            }}
        """)
        
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
        cancel_btn.setStyleSheet(BUTTON_STYLE)
        
        self.save_as_btn = QPushButton("Save As...")
        self.save_as_btn.clicked.connect(self.save_structure_as)
        self.save_as_btn.setStyleSheet(BUTTON_STYLE)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
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
        
        # Check if we should show default structures
        show_default_structures = True
        
        # Try to load preference from template manager
        if self.template_manager and hasattr(self.template_manager, 'preferences'):
            show_default_structures = self.template_manager.preferences.get('show_default_structures', True)
        
        # Add built-in structures section
        if show_default_structures:
            self.structure_combo.addItem("=== Built-in Structures ===", None)
            
            # Always show all built-in structures, regardless of project type
            for name in sorted(DEFAULT_STRUCTURES.keys()):
                self.structure_combo.addItem(name, name)
        
        # Add custom structures section if template manager is available
        if self.template_manager and hasattr(self.template_manager, 'custom_structures'):
            self.structure_combo.addItem("=== Custom Structures ===", None)
            
            # Get category assignments if available
            structure_assignments = {}
            if hasattr(self.template_manager, 'preferences'):
                structure_assignments = self.template_manager.preferences.get('structure_assignments', {})
                
            # Get categories from preferences
            categories = {}
            default_category_name = "Custom Structures"  # Default category name
            
            if hasattr(self.template_manager, 'preferences'):
                # Get custom categories from preferences
                user_categories = self.template_manager.preferences.get('structure_categories', {})
                
                # Check if default category has been renamed
                if 'default_category_name' in self.template_manager.preferences:
                    default_category_name = self.template_manager.preferences.get('default_category_name')
                
                # Add default category and user categories to our categories dict
                categories[default_category_name] = []
                categories.update(user_categories)
            else:
                # If no preferences, just use default category
                categories[default_category_name] = []
            
            # First, group structures by category
            categorized_structures = {category: [] for category in categories.keys()}
            
            # Add all structures to appropriate categories
            for name in sorted(self.template_manager.custom_structures.keys()):
                category = structure_assignments.get(name, default_category_name)
                if category in categorized_structures:
                    categorized_structures[category].append(name)
                else:
                    # If assigned category doesn't exist, use default
                    categorized_structures[default_category_name].append(name)
            
            # Now add items by category
            for category in sorted(categories.keys()):
                if categorized_structures[category]:
                    # Add category header if it has structures
                    self.structure_combo.addItem(f"--- {category} ---", None)
                    
                    # Add all structures in this category
                    for name in sorted(categorized_structures[category]):
                        self.structure_combo.addItem(f"  {name}", name)
            
            # Add any uncategorized structures
            uncategorized = []
            for name in sorted(self.template_manager.custom_structures.keys()):
                if all(name not in category_list for category_list in categorized_structures.values()):
                    uncategorized.append(name)
                    
            if uncategorized:
                for name in sorted(uncategorized):
                    self.structure_combo.addItem(name, name)
        
        # If a structure_name was provided, try to select it
        if self.structure_name:
            index = self.structure_combo.findData(self.structure_name)
            if index >= 0:
                self.structure_combo.setCurrentIndex(index)
            else:
                # Try finding by text too (for backward compatibility)
                index = self.structure_combo.findText(self.structure_name)
                if index >= 0:
                    self.structure_combo.setCurrentIndex(index)
        # Otherwise if project_type is provided, find and select the default structure for that type
        elif self.project_type:
            default_structure = PROJECT_TYPE_TO_STRUCTURE.get(self.project_type)
            if default_structure:
                index = self.structure_combo.findData(default_structure)
                if index >= 0:
                    self.structure_combo.setCurrentIndex(index)
                else:
                    # Try finding by text too
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
                    # Use color style for read-only field
                    self.name_input.setStyleSheet(f"""
                        background-color: {colors['hover_bg']}; 
                        color: {colors['secondary_text']}; 
                        border: 1px solid {colors['border']}; 
                        padding: 5px; 
                        border-radius: 3px;
                    """)
                else:
                    self.name_input.setReadOnly(False)
                    # Use standard line edit style
                    self.name_input.setStyleSheet(LINEEDIT_STYLE)
                    
                    # Update category dropdown if this is a custom structure
                    if hasattr(self, 'category_combo'):
                        # Ensure the category dropdown is populated
                        self.populate_category_dropdown()
                
                # Update structure and tree
                self.structure = structure
                self.populate_structure()
    
    def create_new_structure(self):
        """Create a new blank structure"""
        # Clear structure name and tree
        self.name_input.setText("New Structure")
        self.name_input.setReadOnly(False)
        # Use standard line edit style
        self.name_input.setStyleSheet(LINEEDIT_STYLE)
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
        
        # Set a suggested name
        self.name_input.setText(f"{current_name}_copy" if current_name else "New Structure")
        
        # Select the text to make it easy to change
        self.name_input.selectAll()
        self.name_input.setFocus()
        
        # Set built-in flag to false since this is a new custom structure
        self.is_built_in = False
        self.name_input.setReadOnly(False)
        # Use standard line edit style
        self.name_input.setStyleSheet(LINEEDIT_STYLE)
        
    def populate_structure(self):
        """Populate the structure tree"""
        if self.structure is None:
            self.structure = []
        
        self.tree.clear()
        
        # Add root item
        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, "Project Root")
        root_item.setExpanded(True)
        # Make root item not editable
        root_item.setFlags(root_item.flags() & ~Qt.ItemIsEditable)
        
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
                    # Make folder items editable
                    folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
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
                    # Make folder items editable
                    item_widget.setFlags(item_widget.flags() | Qt.ItemIsEditable)
                else:
                    # File
                    item_widget.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
                    # Store that this is a file in the data
                    item_widget.setData(0, Qt.UserRole, "file")
                    # Make file items editable
                    item_widget.setFlags(item_widget.flags() | Qt.ItemIsEditable)
                    
    def show_context_menu(self, position):
        """Show context menu for tree items"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
            
        menu = CustomMenu(self)
        
        # Check if multiple items are selected
        if len(selected_items) > 1:
            # Group selected items by type to determine available actions
            folders = []
            files = []
            
            for item in selected_items:
                item_data = item.data(0, Qt.UserRole)
                if isinstance(item_data, str) and item_data == "folder":
                    folders.append(item)
                elif isinstance(item_data, str) and item_data == "file":
                    files.append(item)
            
            # Only show delete option for multiple selection
            if folders or files:
                # Skip if root item is in selection
                root_item = self.tree.invisibleRootItem().child(0)
                if root_item in selected_items:
                    return
                    
                delete_action = QAction(f"Delete {len(selected_items)} Items", self)
                delete_action.triggered.connect(self.delete_item)
                menu.addRedDeleteAction(
                    parent=self,
                    callback=self.delete_item
                )
        else:
            # Single item selected - show full context menu
            item = selected_items[0]
            item_data = item.data(0, Qt.UserRole)
            
            # Check if item_data is a dictionary before trying to use get()
            if isinstance(item_data, dict) and item_data.get("type") == "category":
                # Context menu for category items
                if item_data.get("is_built_in", False):
                    # No actions for built-in category
                    return
                    
                rename_action = QAction("Rename Category", self)
                rename_action.triggered.connect(lambda: self.edit_category(item))
                menu.addAction(rename_action)
                
                # Don't allow deleting the default category
                if not item_data.get("is_default", False):
                    # Add the Delete action with red styling
                    menu.addRedDeleteAction(
                        parent=self,
                        callback=lambda: self.delete_category(item)
                    )
                    
            elif isinstance(item_data, dict) and item_data.get("type") in ["custom", "default"]:
                # Context menu for structure items
                if item_data.get("type") == "custom":
                    rename_action = QAction("Rename...", self)
                    rename_action.triggered.connect(lambda: self.rename_structure_from_item(item))
                    menu.addAction(rename_action)
                    
                    # Add the Delete action with red styling
                    menu.addRedDeleteAction(
                        parent=self,
                        callback=lambda: self.delete_structure_from_item(item)
                    )
                
                duplicate_action = QAction("Duplicate...", self)
                duplicate_action.triggered.connect(lambda: self.duplicate_structure_from_item(item))
                menu.addAction(duplicate_action)
            # Add handling for string item_data (folder or file items)
            elif isinstance(item_data, str) and item_data in ["folder", "file"]:
                # Skip root item
                root_item = self.tree.invisibleRootItem().child(0)
                if item == root_item:
                    return
                    
                # Context menu for folder and file items
                rename_action = QAction("Rename...", self)
                rename_action.triggered.connect(lambda: self.rename_item(item))
                menu.addAction(rename_action)
                
                # Add red styling for delete action
                menu.addRedDeleteAction(
                    parent=self,
                    callback=lambda: self.delete_item(item)
                )
        
        if not menu.isEmpty():
            menu.exec_(self.tree.viewport().mapToGlobal(position))
    
    def edit_category(self, item):
        """Edit a category by making it editable"""
        if item and item.flags() & Qt.ItemIsEditable:
            self.tree.editItem(item, 0)
            
    def delete_category(self, item):
        """Delete a category and reassign structures to default category"""
        if not item:
            return
            
        item_data = item.data(0, Qt.UserRole)
        if not isinstance(item_data, dict) or item_data.get("type") != "category" or item_data.get("is_default", False) or item_data.get("is_built_in", False):
            return
            
        # Get the category name
        category_name = item.text(0)
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Category Deletion",
            f"Are you sure you want to delete the category '{category_name}'?\n\nAll structures in this category will be moved to the default category.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
            
        # Get default category name
        default_category_name = "Custom Structures"
        if self.template_manager and hasattr(self.template_manager, 'preferences'):
            default_category_name = self.template_manager.preferences.get('default_category_name', "Custom Structures")
            
        # Make sure default category exists
        if default_category_name not in self.category_items:
            # This shouldn't happen, but just in case
            QMessageBox.warning(self, "Error", "Default category not found. Cannot delete category.")
            return
            
        # Move all structures in this category to the default category
        default_item = self.category_items[default_category_name]
        structures_to_move = []
        
        # First, get all structures from this category
        for i in range(item.childCount()):
            child = item.child(i)
            child_data = child.data(0, Qt.UserRole)
            if child_data and child_data.get("type") == "custom":
                structures_to_move.append((child.text(0), child_data))
                
        # Move structures to default category and update assignments
        if self.template_manager and hasattr(self.template_manager, 'preferences'):
            structure_assignments = self.template_manager.preferences.get('structure_assignments', {})
            
            for name, data in structures_to_move:
                # Update assignment in preferences
                if name in structure_assignments:
                    structure_assignments[name] = default_category_name
            
            # Delete category from preferences
            if 'structure_categories' in self.template_manager.preferences:
                if category_name in self.template_manager.preferences['structure_categories']:
                    del self.template_manager.preferences['structure_categories'][category_name]
                    
            # Save preferences
            self.save_preferences()
        
        # Refresh the list to reflect changes
        self.populate_structure()
        
        # Inform user
        QMessageBox.information(self, "Success", f"Category '{category_name}' has been deleted.")
        
    def rename_structure_from_item(self, item):
        """Rename structure from context menu"""
        if item:
            item_data = item.data(0, Qt.UserRole)
            if isinstance(item_data, dict) and item_data.get("type") == "custom":
                # Create a temporary selection
                self.structures_list.setCurrentItem(item)
                # Call the main rename function
                self.rename_structure()
                
    def delete_structure_from_item(self, item):
        """Delete structure from context menu"""
        if item:
            item_data = item.data(0, Qt.UserRole)
            if isinstance(item_data, dict) and item_data.get("type") == "custom":
                # Create a temporary selection
                self.structures_list.setCurrentItem(item)
                # Call the main delete function
                self.delete_structure()
                
    def duplicate_structure_from_item(self, item):
        """Duplicate structure from context menu"""
        if item:
            item_data = item.data(0, Qt.UserRole)
            if item_data:
                # Create a temporary selection
                self.structures_list.setCurrentItem(item)
                # Call the main duplicate function
                self.duplicate_structure()

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
            # Make folder editable
            folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
            
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
                # Make file editable
                file_item.setFlags(file_item.flags() | Qt.ItemIsEditable)
                
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
            # Make file editable
            file_item.setFlags(file_item.flags() | Qt.ItemIsEditable)
            
            # Expand parent if it's a valid QTreeWidgetItem
            if hasattr(parent, 'setExpanded'):
                parent.setExpanded(True)
            
            # Force the tree to update
            self.tree.update()
            
            # Make the new file visible by selecting it
            self.tree.setCurrentItem(file_item)
            
            print(f"DEBUG: Added file '{file_name}' successfully")
            
    def delete_item(self, item=None):
        """Delete an item from the tree"""
        print("DEBUG: EnhancedStructureEditor.delete_item called")
        
        # If no item specified, use selected items
        selected_items = []
        if item is None:
            selected_items = self.tree.selectedItems()
        else:
            selected_items = [item]
            
        if not selected_items:
            return

        # Skip deletion if any selected item is the root
        root_item = self.tree.invisibleRootItem().child(0)
        if root_item in selected_items:
            print("DEBUG: Cannot delete root item")
            return
            
        # Confirm deletion if multiple items selected
        if len(selected_items) > 1:
            confirm = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete {len(selected_items)} items?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm != QMessageBox.Yes:
                return
        
        # Process deletions in reverse order of tree traversal to maintain valid parent-child relationships
        # First, convert selected items to a list and sort by depth (deepest first)
        items_to_delete = []
        for item in selected_items:
            depth = 0
            parent = item.parent()
            while parent:
                depth += 1
                parent = parent.parent()
            items_to_delete.append((depth, item))
        
        # Sort by depth in descending order
        items_to_delete.sort(reverse=True)
        
        # Now delete items
        for _, item in items_to_delete:
            print(f"DEBUG: Attempting to delete item: '{item.text(0)}'")
            parent = item.parent()
            if parent:
                index = parent.indexOfChild(item)
                parent.takeChild(index)
                print(f"DEBUG: Deleted item '{item.text(0)}' successfully")
    
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
        
        # Simply start editing the item inline
        self.tree.editItem(item, 0)
    
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
        """Save the current structure with the given name"""
        print("DEBUG: save_structure method called")
        
        # Get the current structure from the tree
        structure = self.get_structure_from_tree()
        print(f"DEBUG: Got structure with {len(structure)} items")
        
        # Ensure we have a valid structure name
        if not self.name_input.text():
            print("DEBUG: No structure name provided")
            QMessageBox.warning(self, "Error", "Please enter a structure name.")
            self.name_input.setFocus()
            return False
            
        structure_name = self.name_input.text()
        print(f"DEBUG: Saving structure with name: '{structure_name}'")
        
        # Check if we're trying to overwrite a built-in structure
        from app.constants import DEFAULT_STRUCTURES
        if structure_name in DEFAULT_STRUCTURES and not self.is_built_in:
            print("DEBUG: Creating custom version of built-in structure")
        
        # Store the result for returning, regardless of template manager
        self.result_structure = structure
        self.result_name = structure_name
        print(f"DEBUG: Stored result structure with {len(structure)} items and name '{structure_name}'")
        
        # Save the structure to the template manager
        if hasattr(self, 'template_manager') and self.template_manager:
            print(f"DEBUG: Saving to template manager: {structure_name}")
            success = self.template_manager.save_custom_structure(structure_name, structure)
            print(f"DEBUG: Saved structure '{structure_name}' to template manager")
            
            # Call the save callback if provided
            if self.save_callback:
                print("DEBUG: Calling save callback")
                self.save_callback(structure_name, structure)
            
            # Return success
            return success
        else:
            # If we don't have a template manager, just call the callback
            print("DEBUG: No template manager, calling callback directly")
            if self.save_callback:
                self.save_callback(structure_name, structure)
                
            # Return success
            return True
            
        print("DEBUG: Failed to save structure")
        return False
        
    def accept(self):
        """Override accept to save the structure before closing"""
        print("DEBUG: accept method called")
        # Call save_structure but don't call accept() again
        success = self.save_structure()
        print(f"DEBUG: save_structure returned {success}")
        
        if success:
            # Also save the category assignment if this is a custom structure
            if not self.is_built_in and self.template_manager and hasattr(self.template_manager, 'preferences'):
                structure_name = self.name_input.text().strip()
                
                # Get selected category
                if hasattr(self, 'category_combo'):
                    selected_category = self.category_combo.currentData()
                    
                    # Save the assignment
                    if 'structure_assignments' not in self.template_manager.preferences:
                        self.template_manager.preferences['structure_assignments'] = {}
                        
                    self.template_manager.preferences['structure_assignments'][structure_name] = selected_category
                    
                    # Save preferences
                    if hasattr(self.template_manager, 'save_preferences'):
                        self.template_manager.save_preferences()
            
            # Store a successful result flag to indicate dialog was accepted
            print("DEBUG: Setting dialog result code to 1 (Accepted)")
            self.setResult(1)  # Explicitly set result to Accepted (1) 
            print("DEBUG: Calling super().accept() to close dialog")
            # Call the parent's accept method to close the dialog
            super(EnhancedStructureEditor, self).accept()
        else:
            print("DEBUG: Not closing dialog due to save failure")
        
    def get_result(self):
        """Get the edited structure if the dialog was accepted"""
        if hasattr(self, 'result_structure'):
            return self.result_structure
        return None

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
        """Handle drop events on the tree"""
        print("DEBUG: Tree dropEvent called")
        
        # Determine target item (where the drop occurred)
        drop_position = event.pos()
        target_item = self.tree.itemAt(drop_position)
        
        if target_item:
            print(f"DEBUG: Dropping onto item: '{target_item.text(0)}'")
        else:
            print("DEBUG: No item at drop position, using root")
            target_item = self.tree.invisibleRootItem().child(0)
        
        # Handle external drops (files from file system)
        mime_data = event.mimeData()
        
        if mime_data.hasUrls():
            print("DEBUG: External drop with URLs")
            event.accept()
            
            # Process each URL
            for url in mime_data.urls():
                # Convert QUrl to local file path
                file_path = url.toLocalFile()
                print(f"DEBUG: Processing dropped URL: {file_path}")
                
                if os.path.isdir(file_path):
                    # Import directory structure
                    print(f"DEBUG: Importing directory structure: {file_path}")
                    self._process_dropped_directory(file_path, target_item)
                elif os.path.isfile(file_path):
                    # Add as a file
                    file_name = os.path.basename(file_path)
                    file_item = QTreeWidgetItem(target_item)
                    file_item.setText(0, file_name)
                    file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
                    file_item.setData(0, Qt.UserRole, "file")
                    # Make file editable
                    file_item.setFlags(file_item.flags() | Qt.ItemIsEditable)
            
            # Expand the target item
            target_item.setExpanded(True)
            
            return
        
        # Handle internal drag and drop (items within the tree)
        if event.source() == self.tree:
            event.accept()
            
            # Get all selected items
            source_items = self.tree.selectedItems()
            
            # Skip if no items selected or if target is in selected items
            if not source_items or target_item in source_items:
                return
                
            # Check if target is a child of any source item (can't move to own child)
            for source_item in source_items:
                current = target_item
                while current:
                    if current == source_item:
                        print(f"DEBUG: Can't move an item to its own child")
                        return
                    current = current.parent()
            
            # Sort items by their depth to maintain hierarchy (deepest items first)
            items_to_move = []
            for item in source_items:
                depth = 0
                parent = item.parent()
                while parent:
                    depth += 1
                    parent = parent.parent()
                items_to_move.append((depth, item))
            
            # Sort by depth in descending order
            items_to_move.sort(reverse=True)
            
            # Get item data before moving
            items_data = []
            for _, item in items_to_move:
                children = []
                for i in range(item.childCount()):
                    children.append(item.child(i))
                items_data.append({
                    'text': item.text(0),
                    'data': item.data(0, Qt.UserRole),
                    'children': children
                })
            
            # Process each item
            for _, source_item in items_to_move:
                # Skip root item
                if source_item == self.tree.invisibleRootItem().child(0):
                    continue
                    
                # Get source item parent and index
                source_parent = source_item.parent()
                if not source_parent:
                    continue  # Skip if no parent (shouldn't happen)
                
                source_index = source_parent.indexOfChild(source_item)
                
                # Determine if source_item is a file or folder
                item_data = source_item.data(0, Qt.UserRole)
                is_folder = item_data == "folder"
                
                # Create new item in target
                new_item = QTreeWidgetItem(target_item)
                new_item.setText(0, source_item.text(0))
                
                # Set appropriate icon and data
                if is_folder:
                    new_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                    new_item.setData(0, Qt.UserRole, "folder")
                else:
                    new_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
                    new_item.setData(0, Qt.UserRole, "file")
                
                # Copy flags
                new_item.setFlags(source_item.flags())
                
                # Move all children to the new item
                self._move_children(source_item, new_item)
                
                # Remove the original item
                source_parent.takeChild(source_index)
            
            # Expand the target
            target_item.setExpanded(True)
    
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
        # Make folder editable
        folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
        
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
                # Make file editable
                file_item.setFlags(file_item.flags() | Qt.ItemIsEditable)
                
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

    def manage_structures(self):
        """Open the structure management dialog"""
        dialog = StructureManagerDialog(self)
        if dialog.exec_():
            # Refresh the structure dropdown after management
            self.populate_structure_dropdown()
            
            # Also refresh the category dropdown in case categories were renamed
            if hasattr(self, 'category_combo'):
                self.populate_category_dropdown()

    def populate_category_dropdown(self):
        """Populate the category dropdown"""
        self.category_combo.clear()
        
        # Default category
        self.category_combo.addItem("Custom Structures", "Custom Structures")
        
        # Add custom categories if available
        if self.template_manager and hasattr(self.template_manager, 'preferences'):
            categories = self.template_manager.preferences.get('structure_categories', {})
            
            # Add each category
            for category_name in sorted(categories.keys()):
                self.category_combo.addItem(category_name, category_name)
                
        # Set the current category if this is an existing structure
        if self.template_manager and hasattr(self.template_manager, 'preferences') and self.structure_name:
            structure_assignments = self.template_manager.preferences.get('structure_assignments', {})
            current_category = structure_assignments.get(self.structure_name, "Custom Structures")
            
            # Find and select this category
            index = self.category_combo.findData(current_category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

    def on_item_double_clicked(self, item, column):
        """Handle double-click event to rename items in the tree widget"""
        if column == 0:
            self.rename_item(item)

# Add this new dialog class at the bottom of the file, before the utility functions
class StructureManagerDialog(QDialog):
    """Dialog for managing folder structures"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.template_manager = parent.template_manager
        
        # Settings for showing default structures - load from preferences
        self.show_default_structures = True
        self.load_preferences()
        
        self.setWindowTitle("Manage Folder Structures")
        self.resize(600, 500)
        
        # Apply dark theme to the dialog
        self.setStyleSheet(f"background-color: {colors['bg']}; color: {colors['text']};")
        
        self.init_ui()
        self.populate_structures()
        
    def keyPressEvent(self, event):
        """Handle key press events for Delete/Backspace keys"""
        # Check for Delete key press or Backspace key (common on Mac)
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            # If delete button is enabled, trigger delete action
            if self.delete_button.isEnabled():
                self.delete_structure()
                event.accept()
                return
        
        # Pass other key events to parent class
        super().keyPressEvent(event)
        
    def init_ui(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout(self)
        
        # Option to show/hide default structures
        default_option_layout = QHBoxLayout()
        self.show_defaults_checkbox = QCheckBox("Show default structures")
        self.show_defaults_checkbox.setChecked(self.show_default_structures)
        self.show_defaults_checkbox.stateChanged.connect(self.toggle_default_structures)
        # Apply consistent styling to the checkbox
        self.show_defaults_checkbox.setStyleSheet(f"color: {colors['text']}; spacing: 5px;")
        default_option_layout.addWidget(self.show_defaults_checkbox)
        default_option_layout.addStretch()
        main_layout.addLayout(default_option_layout)
        
        # Structure list
        list_group = QGroupBox("Available Structures")
        list_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {colors['bg']}; 
                color: {colors['text']}; 
                border: 1px solid {colors['border']};
                margin-top: 20px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: {colors['bg']};
            }}
        """)
        
        list_layout = QVBoxLayout(list_group)
        
        # Tree widget for the structure list
        self.structures_list = QTreeWidget()
        self.structures_list.setHeaderLabels(["Name", "Type"])
        self.structures_list.setColumnWidth(0, 250)
        self.structures_list.setAlternatingRowColors(True)
        self.structures_list.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.structures_list.itemSelectionChanged.connect(self.update_buttons)
        # Connect itemChanged signal to handle category renaming
        self.structures_list.itemChanged.connect(self.on_item_changed)
        # Enable context menu for right-click actions
        self.structures_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.structures_list.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set column widths for better readability - make Name column wider
        self.structures_list.setColumnWidth(0, 380)  # Name column takes most of the space
        self.structures_list.setColumnWidth(1, 100)  # Type column is narrower
        
        # Apply consistent styling to the tree widget - use slightly lighter bg 
        self.structures_list.setStyleSheet(f"""
            QTreeWidget {{ 
                background-color: {colors['card_bg']}; 
                color: {colors['text']}; 
                border: 1px solid {colors['border']}; 
            }}
            QTreeWidget::item {{ 
                padding: 3px; 
                border-radius: 2px;
            }}
            QTreeWidget::item:hover {{ 
                background-color: {colors['hover_bg']};
            }}
            QTreeWidget::item:selected {{ 
                background-color: {colors['highlight_bg']}; 
                color: {colors['highlight_text']}; 
                border: 1px solid {colors['accent']};
            }}
            QTreeWidget::item:selected:active {{ 
                background-color: {colors['highlight_bg']}; 
                color: {colors['highlight_text']}; 
            }}
            QHeaderView::section {{
                background-color: {colors['hover_bg']};
                color: {colors['text']};
                padding: 5px;
                border: 1px solid {colors['border']};
            }}
        """)
        
        # Enable drag and drop for reordering
        self.structures_list.setDragEnabled(True)
        self.structures_list.setAcceptDrops(True)
        self.structures_list.setDragDropMode(QTreeWidget.InternalMove)
        # Only allow dropping on categories (not on structure items)
        self.structures_list.setDefaultDropAction(Qt.MoveAction)
        
        list_layout.addWidget(self.structures_list)
        
        # Buttons for structure management
        buttons_layout = QHBoxLayout()
        
        self.rename_button = QPushButton("Rename...")
        self.rename_button.clicked.connect(self.rename_structure)
        self.rename_button.setStyleSheet(BUTTON_STYLE)
        self.rename_button.setEnabled(False)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_structure)
        self.delete_button.setStyleSheet(BUTTON_STYLE)
        self.delete_button.setEnabled(False)
        
        self.duplicate_button = QPushButton("Duplicate...")
        self.duplicate_button.clicked.connect(self.duplicate_structure)
        self.duplicate_button.setStyleSheet(BUTTON_STYLE)
        self.duplicate_button.setEnabled(False)
        
        # Category/organization management
        self.add_category_button = QPushButton("Add Category")
        self.add_category_button.clicked.connect(self.add_category)
        self.add_category_button.setStyleSheet(BUTTON_STYLE)
        
        buttons_layout.addWidget(self.rename_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.duplicate_button)
        buttons_layout.addWidget(self.add_category_button)
        list_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(list_group)
        
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet(BUTTON_STYLE)
        bottom_layout.addStretch()
        bottom_layout.addWidget(close_button)
        main_layout.addLayout(bottom_layout)
        
    def populate_structures(self):
        """Populate the structures list"""
        self.structures_list.clear()
        
        # Import the default structures
        from app.constants import DEFAULT_STRUCTURES
        
        # Get default category name from preferences
        default_category_name = "Custom Structures"
        if self.template_manager and hasattr(self.template_manager, 'preferences'):
            default_category_name = self.template_manager.preferences.get('default_category_name', "Custom Structures")
        
        # First, add the categories from preferences if they exist
        categories = {"Default Structures": []}
        categories[default_category_name] = []
        
        # Add additional user-defined categories if available
        if self.template_manager and hasattr(self.template_manager, 'preferences'):
            user_categories = self.template_manager.preferences.get('structure_categories', {})
            # Add only categories that aren't already in our list
            for cat_name, cat_value in user_categories.items():
                if cat_name not in categories:
                    categories[cat_name] = cat_value
        
        # Create category items first (so they're at the top)
        self.category_items = {}
        
        # Always add default custom structures category
        self.category_items[default_category_name] = QTreeWidgetItem(self.structures_list)
        self.category_items[default_category_name].setText(0, default_category_name)
        # Make it editable, so users can rename it
        self.category_items[default_category_name].setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsDropEnabled)
        self.category_items[default_category_name].setExpanded(True)
        # Set data to identify this is the default category
        self.category_items[default_category_name].setData(0, Qt.UserRole, {"type": "category", "is_default": True})
        
        # Add Default Structures category if visible
        if self.show_default_structures:
            self.category_items["Default Structures"] = QTreeWidgetItem(self.structures_list)
            self.category_items["Default Structures"].setText(0, "Default Structures")
            self.category_items["Default Structures"].setFlags(Qt.ItemIsEnabled)  # Can't drop on defaults
            self.category_items["Default Structures"].setExpanded(True)
            # Set data to identify this is the built-in category
            self.category_items["Default Structures"].setData(0, Qt.UserRole, {"type": "category", "is_built_in": True})
        
        # Add user-defined categories
        for category_name in sorted(categories.keys()):
            if category_name not in ["Default Structures", default_category_name]:
                self.category_items[category_name] = QTreeWidgetItem(self.structures_list)
                self.category_items[category_name].setText(0, category_name)
                self.category_items[category_name].setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsDropEnabled)
                self.category_items[category_name].setExpanded(True)
                # Set data to identify this is a user category
                self.category_items[category_name].setData(0, Qt.UserRole, {"type": "category", "is_user": True})
        
        # Now add the structures
        if self.show_default_structures and "Default Structures" in self.category_items:
            # Add default structures
            for name in sorted(DEFAULT_STRUCTURES.keys()):
                item = QTreeWidgetItem(self.category_items["Default Structures"])
                item.setText(0, name)
                item.setText(1, "Default")
                item.setData(0, Qt.UserRole, {"name": name, "type": "default"})
                # Use folder icon
                item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                # No drag and drop for default structures
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        
        # Add custom structures to their respective categories
        if self.template_manager and hasattr(self.template_manager, 'custom_structures'):
            # Check if we have structure category assignments
            structure_assignments = {}
            if hasattr(self.template_manager, 'preferences'):
                structure_assignments = self.template_manager.preferences.get('structure_assignments', {})
            
            # Process all custom structures
            for name in sorted(self.template_manager.custom_structures.keys()):
                # Determine which category this structure belongs to
                category_name = structure_assignments.get(name, default_category_name)
                
                # Make sure the category exists
                if category_name not in self.category_items:
                    category_name = default_category_name  # Default fallback
                
                # Create the item in the appropriate category
                item = QTreeWidgetItem(self.category_items[category_name])
                item.setText(0, name)
                item.setText(1, "Custom")
                item.setData(0, Qt.UserRole, {"name": name, "type": "custom", "category": category_name})
                # Use custom folder icon
                item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                
                # Enable drag and drop and editing for custom structures
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEditable)
    
    def add_category(self):
        """Add a new custom category"""
        # Create default category name
        category_name = "New Category"
        
        # Check if name already exists, append number if needed
        index = 1
        temp_name = category_name
        while temp_name in self.category_items:
            temp_name = f"{category_name} {index}"
            index += 1
        category_name = temp_name
        
        # Add to preferences
        if self.template_manager and hasattr(self.template_manager, 'preferences'):
            if 'structure_categories' not in self.template_manager.preferences:
                self.template_manager.preferences['structure_categories'] = {}
                
            self.template_manager.preferences['structure_categories'][category_name] = []
            self.save_preferences()
        
        # Update the UI
        self.populate_structures()
        
        # Find and select the new category
        for i in range(self.structures_list.topLevelItemCount()):
            category = self.structures_list.topLevelItem(i)
            if category.text(0) == category_name:
                category.setSelected(True)
                self.structures_list.scrollToItem(category)
                # Make the category editable and start editing immediately
                category.setFlags(category.flags() | Qt.ItemIsEditable)
                self.structures_list.editItem(category, 0)
                return

    def accept(self):
        """Override accept to save the category arrangement before closing"""
        self.save_category_arrangements()
        super().accept()
        
    def save_category_arrangements(self):
        """Save the current arrangement of structures in categories"""
        # Skip if template manager or preferences aren't available
        if not self.template_manager or not hasattr(self.template_manager, 'preferences'):
            return
            
        # Create or update the structure assignments
        structure_assignments = {}
        
        # Check all categories except Default Structures
        for category_name, category_item in self.category_items.items():
            if category_name == "Default Structures":
                continue
                
            # Process all items in this category
            for i in range(category_item.childCount()):
                child = category_item.child(i)
                structure_data = child.data(0, Qt.UserRole)
                
                if structure_data and structure_data.get("type") == "custom":
                    structure_name = structure_data.get("name")
                    if structure_name:
                        structure_assignments[structure_name] = category_name
            
        # Save to preferences
        self.template_manager.preferences['structure_assignments'] = structure_assignments
        self.save_preferences()
        
    def dropEvent(self, event):
        """Custom drop event to handle structure organization"""
        # Make sure we have valid data
        if not event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.ignore()
            return
            
        # Let the standard handler process the drop
        super().dropEvent(event)
        
        # After it's complete, check which structures were moved and update preferences
        self.save_category_arrangements()

    def load_preferences(self):
        """Load user preferences for the structure manager"""
        if self.template_manager:
            # Try to load the preference from the template manager
            if hasattr(self.template_manager, 'preferences'):
                self.show_default_structures = self.template_manager.preferences.get(
                    'show_default_structures', True)
            else:
                # Create preferences dictionary if it doesn't exist
                self.template_manager.preferences = {}
                self.template_manager.preferences['show_default_structures'] = True
                self.save_preferences()
        
    def save_preferences(self):
        """Save user preferences for the structure manager"""
        if self.template_manager and hasattr(self.template_manager, 'preferences'):
            self.template_manager.preferences['show_default_structures'] = self.show_default_structures
            
            # Save preferences to file if possible
            if hasattr(self.template_manager, 'save_preferences'):
                self.template_manager.save_preferences()
            else:
                # Create a simple file-based preferences saver if not available
                try:
                    import os
                    import json
                    
                    if hasattr(self.template_manager, 'paths'):
                        prefs_path = os.path.join(self.template_manager.paths.get(
                            'templates_dir', ''), 'preferences.json')
                        
                        with open(prefs_path, 'w') as f:
                            json.dump(self.template_manager.preferences, f, indent=2)
                except Exception as e:
                    print(f"Error saving preferences: {e}")

    def toggle_default_structures(self, state):
        """Toggle showing default structures"""
        self.show_default_structures = state == Qt.Checked
        self.save_preferences()
        self.populate_structures()
    
    def update_buttons(self):
        """Update button states based on selection"""
        selected_items = self.structures_list.selectedItems()
        if not selected_items:
            self.rename_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.duplicate_button.setEnabled(False)
            return
        
        selected_item = selected_items[0]
        item_data = selected_item.data(0, Qt.UserRole)
        
        if not item_data:
            # Category header is selected
            self.rename_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.duplicate_button.setEnabled(False)
            return
            
        structure_type = item_data.get("type")
        
        # Enable/disable buttons based on structure type
        self.duplicate_button.setEnabled(True)  # Always allow duplicating
        
        if structure_type == "default":
            # Default structures can't be renamed or deleted
            self.rename_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        else:
            # Custom structures can be renamed and deleted
            self.rename_button.setEnabled(True)
            self.delete_button.setEnabled(True)
    
    def rename_structure(self):
        """Rename the selected structure"""
        # Get selected item
        selected_items = self.structures_list.selectedItems()
        if not selected_items:
            return
            
        selected_item = selected_items[0]
        item_data = selected_item.data(0, Qt.UserRole)
        
        if not isinstance(item_data, dict) or item_data.get("type") == "default":
            return
        
        # Make sure the item is editable
        selected_item.setFlags(selected_item.flags() | Qt.ItemIsEditable)
        
        # Start editing the item inline
        self.structures_list.editItem(selected_item, 0)
    
    def delete_structure(self):
        selected_items = self.structures_list.selectedItems()
        if not selected_items:
            return
        
        # Check if any of the selected structures are default structures
        default_structures = []
        deletable_structures = []
        
        for selected_item in selected_items:
            item_data = selected_item.data(0, Qt.UserRole)
            
            if not isinstance(item_data, dict) or item_data.get("type") == "default":
                default_structures.append(selected_item.text(0))
            else:
                deletable_structures.append(selected_item)
                
        # Warn about default structures that can't be deleted
        if default_structures:
            if len(default_structures) == 1:
                QMessageBox.warning(self, "Cannot Delete", f"'{default_structures[0]}' is a default structure and cannot be deleted.")
            else:
                QMessageBox.warning(self, "Cannot Delete", f"The following are default structures and cannot be deleted:\n• {', '.join(default_structures)}")
                
        # If no deletable structures, return
        if not deletable_structures:
            return
            
        # Confirm deletion
        confirm_message = f"Are you sure you want to delete {len(deletable_structures)} structure(s)?"
        confirm = QMessageBox.question(
            self, 
            "Confirm Delete", 
            confirm_message,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
            
        # Delete each structure
        for item in deletable_structures:
            structure_name = item.data(0, Qt.UserRole).get("name")
            
            if self.template_manager and structure_name:
                success = self.template_manager.delete_custom_structure(structure_name)
                if success:
                    # If parent is a category, remove from the category
                    parent = item.parent()
                    if parent:
                        parent.removeChild(item)
                else:
                    QMessageBox.warning(self, "Error", f"Failed to delete structure '{structure_name}'")
    
    def duplicate_structure(self):
        """Duplicate the selected structure"""
        selected_items = self.structures_list.selectedItems()
        if not selected_items:
            return
            
        selected_item = selected_items[0]
        item_data = selected_item.data(0, Qt.UserRole)
        
        if not item_data:
            return
            
        structure_name = item_data.get("name")
        
        # Create a default new name
        new_name = f"{structure_name}_copy"
        
        # Get the structure
        structure = None
        if self.template_manager:
            structure = self.template_manager.get_structure(structure_name)
            
        if structure:
            # Save with the new name
            success = self.template_manager.save_custom_structure(new_name, structure)
            
            if success:
                # Refresh the list
                self.populate_structures()
                
                # Find and select the new item
                for i in range(self.structures_list.topLevelItemCount()):
                    category = self.structures_list.topLevelItem(i)
                    for j in range(category.childCount()):
                        item = category.child(j)
                        if item.text(0) == new_name:
                            item.setSelected(True)
                            self.structures_list.scrollToItem(item)
                            # Make the new item editable and start editing immediately
                            item.setFlags(item.flags() | Qt.ItemIsEditable)
                            self.structures_list.editItem(item, 0)
                            return
            else:
                QMessageBox.warning(self, "Error", f"Failed to duplicate structure '{structure_name}'")

    def on_item_changed(self, item, column=0):
        """Handle item change in the structure list (category renaming and structure renaming)"""
        # Only process changes to the name column (0)
        if column != 0:
            return
            
        # Get the item data
        item_data = item.data(0, Qt.UserRole)
        if not isinstance(item_data, dict):
            return
            
        # Handle category renaming
        if item_data.get("type") == "category":
            # Get the new category name
            new_name = item.text(0)
            
            # Get the old name by finding this item in our category_items dictionary
            old_name = None
            for name, category_item in self.category_items.items():
                if category_item == item:
                    old_name = name
                    break
                    
            if not old_name or old_name == new_name:
                return  # No change or couldn't find old name
                
            # Check if this is the default category
            is_default = item_data.get("is_default", False)
            
            # Update the template manager preferences
            if self.template_manager and hasattr(self.template_manager, 'preferences'):
                # Update the default category name if this is the default category
                if is_default:
                    self.template_manager.preferences['default_category_name'] = new_name
                    
                # Update structure category assignments
                structure_assignments = self.template_manager.preferences.get('structure_assignments', {})
                for structure_name, category in structure_assignments.items():
                    if category == old_name:
                        structure_assignments[structure_name] = new_name
                        
                # If this was a user-defined category, update it in the categories dictionary
                if not is_default and "structure_categories" in self.template_manager.preferences:
                    categories = self.template_manager.preferences['structure_categories']
                    if old_name in categories:
                        categories[new_name] = categories.pop(old_name)
                        
                # Save the changes
                self.save_preferences()
                
            # Update our internal category_items dictionary
            if old_name in self.category_items:
                self.category_items[new_name] = self.category_items.pop(old_name)
                
            # If this dialog was opened from an EnhancedStructureEditor, update its category dropdown
            if self.parent and isinstance(self.parent, EnhancedStructureEditor):
                if hasattr(self.parent, 'category_combo'):
                    self.parent.populate_category_dropdown()
        
        # Handle structure renaming
        elif item_data.get("type") == "custom":
            # Get the new and old structure names
            new_name = item.text(0)
            old_name = item_data.get("name")
            
            if not old_name or old_name == new_name:
                return  # No change or couldn't get old name
            
            # Update the data in the item
            item_data["name"] = new_name
            item.setData(0, Qt.UserRole, item_data)
            
            # Attempt to rename the structure
            if self.template_manager and hasattr(self.template_manager, "rename_custom_structure"):
                success = self.template_manager.rename_custom_structure(old_name, new_name)
                
                if not success:
                    # Restore the old name if renaming failed
                    item.setText(0, old_name)
                    item_data["name"] = old_name
                    item.setData(0, Qt.UserRole, item_data)
                    QMessageBox.warning(self, "Error", f"Failed to rename structure '{old_name}'")
            else:
                # Legacy method - save as new name and delete old
                if self.template_manager:
                    # Get the structure
                    structure = self.template_manager.get_structure(old_name)
                    if structure:
                        # Save with new name
                        success1 = self.template_manager.save_custom_structure(new_name, structure)
                        # Delete old structure
                        success2 = self.template_manager.delete_custom_structure(old_name)
                        
                        if not (success1 and success2):
                            # Restore the old name if renaming failed
                            item.setText(0, old_name)
                            item_data["name"] = old_name
                            item.setData(0, Qt.UserRole, item_data)
                            QMessageBox.warning(self, "Error", f"Failed to rename structure '{old_name}'")

    def show_context_menu(self, position):
        """Show context menu for structures list items"""
        selected_items = self.structures_list.selectedItems()
        if not selected_items:
            return
            
        menu = CustomMenu(self)
        
        # Check if multiple items are selected
        if len(selected_items) > 1:
            # Check if all items are of the same type to determine available actions
            all_custom = True
            all_default = True
            
            for item in selected_items:
                item_data = item.data(0, Qt.UserRole)
                if not isinstance(item_data, dict):
                    all_custom = False
                    all_default = False
                    break
                    
                if item_data.get("type") != "custom":
                    all_custom = False
                    
                if item_data.get("type") != "default":
                    all_default = False
            
            # Only show delete option for multiple custom structures
            if all_custom:
                delete_action = QAction(f"Delete {len(selected_items)} Structures", self)
                delete_action.triggered.connect(self.delete_structure)
                menu.addRedDeleteAction(
                    parent=self,
                    callback=self.delete_structure
                )
            
            # Show duplicate for either all custom or all default
            if all_custom or all_default:
                duplicate_action = QAction("Duplicate Selected Structures", self)
                duplicate_action.triggered.connect(self.duplicate_selected_structures)
                menu.addAction(duplicate_action)
        else:
            # Single item selected - show full context menu
            item = selected_items[0]
            item_data = item.data(0, Qt.UserRole)
            
            # Check if item_data is a dictionary before trying to use get()
            if isinstance(item_data, dict) and item_data.get("type") == "category":
                # Context menu for category items
                if item_data.get("is_built_in", False):
                    # No actions for built-in category
                    return
                    
                rename_action = QAction("Rename Category", self)
                rename_action.triggered.connect(lambda: self.edit_category(item))
                menu.addAction(rename_action)
                
                # Don't allow deleting the default category
                if not item_data.get("is_default", False):
                    # Add the Delete action with red styling
                    menu.addRedDeleteAction(
                        parent=self,
                        callback=lambda: self.delete_category(item)
                    )
                    
            elif isinstance(item_data, dict) and item_data.get("type") in ["custom", "default"]:
                # Context menu for structure items
                if item_data.get("type") == "custom":
                    rename_action = QAction("Rename...", self)
                    rename_action.triggered.connect(lambda: self.rename_structure_from_item(item))
                    menu.addAction(rename_action)
                    
                    # Add the Delete action with red styling
                    menu.addRedDeleteAction(
                        parent=self,
                        callback=lambda: self.delete_structure_from_item(item)
                    )
                
                duplicate_action = QAction("Duplicate...", self)
                duplicate_action.triggered.connect(lambda: self.duplicate_structure_from_item(item))
                menu.addAction(duplicate_action)
        
        if not menu.isEmpty():
            menu.exec_(self.structures_list.viewport().mapToGlobal(position))
            
    def edit_category(self, item):
        """Edit a category by making it editable"""
        if item and item.flags() & Qt.ItemIsEditable:
            self.structures_list.editItem(item, 0)
            
    def delete_category(self, item):
        """Delete a category and reassign structures to default category"""
        if not item:
            return
            
        item_data = item.data(0, Qt.UserRole)
        if not isinstance(item_data, dict) or item_data.get("type") != "category" or item_data.get("is_default", False) or item_data.get("is_built_in", False):
            return
            
        # Get the category name
        category_name = item.text(0)
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Category Deletion",
            f"Are you sure you want to delete the category '{category_name}'?\n\nAll structures in this category will be moved to the default category.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
            
        # Get default category name
        default_category_name = "Custom Structures"
        if self.template_manager and hasattr(self.template_manager, 'preferences'):
            default_category_name = self.template_manager.preferences.get('default_category_name', "Custom Structures")
            
        # Make sure default category exists
        if default_category_name not in self.category_items:
            # This shouldn't happen, but just in case
            QMessageBox.warning(self, "Error", "Default category not found. Cannot delete category.")
            return
            
        # Move all structures in this category to the default category
        default_item = self.category_items[default_category_name]
        structures_to_move = []
        
        # First, get all structures from this category
        for i in range(item.childCount()):
            child = item.child(i)
            child_data = child.data(0, Qt.UserRole)
            if child_data and child_data.get("type") == "custom":
                structures_to_move.append((child.text(0), child_data))
                
        # Move structures to default category and update assignments
        if self.template_manager and hasattr(self.template_manager, 'preferences'):
            structure_assignments = self.template_manager.preferences.get('structure_assignments', {})
            
            for name, data in structures_to_move:
                # Update assignment in preferences
                if name in structure_assignments:
                    structure_assignments[name] = default_category_name
            
            # Delete category from preferences
            if 'structure_categories' in self.template_manager.preferences:
                if category_name in self.template_manager.preferences['structure_categories']:
                    del self.template_manager.preferences['structure_categories'][category_name]
                    
            # Save preferences
            self.save_preferences()
        
        # Refresh the list to reflect changes
        self.populate_structures()
        
        # Inform user
        QMessageBox.information(self, "Success", f"Category '{category_name}' has been deleted.")
        
    def rename_structure_from_item(self, item):
        """Rename structure from context menu"""
        if item:
            item_data = item.data(0, Qt.UserRole)
            if isinstance(item_data, dict) and item_data.get("type") == "custom":
                # Create a temporary selection
                self.structures_list.setCurrentItem(item)
                # Call the main rename function
                self.rename_structure()
                
    def delete_structure_from_item(self, item):
        """Delete structure from context menu"""
        if item:
            item_data = item.data(0, Qt.UserRole)
            if isinstance(item_data, dict) and item_data.get("type") == "custom":
                # Create a temporary selection
                self.structures_list.setCurrentItem(item)
                # Call the main delete function
                self.delete_structure()
                
    def duplicate_structure_from_item(self, item):
        """Duplicate structure from context menu"""
        if item:
            item_data = item.data(0, Qt.UserRole)
            if item_data:
                # Create a temporary selection
                self.structures_list.setCurrentItem(item)
                # Call the main duplicate function
                self.duplicate_structure()

    def duplicate_selected_structures(self):
        """Duplicate multiple selected structures"""
        selected_items = self.structures_list.selectedItems()
        if not selected_items:
            return
            
        # Gather structure information
        structures_to_duplicate = []
        for item in selected_items:
            item_data = item.data(0, Qt.UserRole)
            if isinstance(item_data, dict):
                structure_name = item_data.get("name")
                if structure_name and self.template_manager:
                    structure = self.template_manager.get_structure(structure_name)
                    if structure:
                        structures_to_duplicate.append((structure_name, structure))
        
        # Duplicate each structure
        duplicated_count = 0
        for original_name, structure in structures_to_duplicate:
            # Create a default new name with numeric suffix to avoid conflicts
            base_name = f"{original_name}_copy"
            new_name = base_name
            suffix = 1
            
            # Check if the name already exists and generate a unique name
            while self.template_manager.structure_exists(new_name):
                suffix += 1
                new_name = f"{base_name}_{suffix}"
            
            # Save with the new name
            success = self.template_manager.save_custom_structure(new_name, structure)
            if success:
                duplicated_count += 1
        
        # Refresh the structure list if any duplicates were created
        if duplicated_count > 0:
            self.populate_structures()
            
            # Show success message
            if duplicated_count == 1:
                QMessageBox.information(self, "Success", f"1 structure was duplicated successfully.")
            else:
                QMessageBox.information(self, "Success", f"{duplicated_count} structures were duplicated successfully.")

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
    print(f"DEBUG: show_enhanced_structure_editor called with structure_name={structure_name}")
    
    # Create and show the dialog
    structure_editor = EnhancedStructureEditor(
        parent, 
        structure_name=structure_name, 
        structure=structure, 
        project_type=project_type,
        is_new=is_new
    )
    
    # Show the dialog modally
    result = structure_editor.exec_()
    print(f"DEBUG: Editor dialog returned result={result}")
    
    # If successful, retrieve both the structure and name
    if result:
        updated_structure = structure_editor.get_result()
        updated_name = getattr(structure_editor, 'result_name', structure_name)
        print(f"DEBUG: Returning success with structure of {len(updated_structure) if updated_structure else 'None'} items and name '{updated_name}'")
        return True, updated_structure, updated_name
    
    # If canceled, return False and None values
    print("DEBUG: Returning failure (canceled)")
    return False, None, None 
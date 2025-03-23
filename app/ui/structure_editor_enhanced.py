#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Enhanced Structure Editor for Template Management

This module defines the enhanced structure editor for creating and editing project templates.
It provides a tree-based interface for managing files and folders in the template structure.
"""

import os
import sys
import json
import time
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QComboBox, QMessageBox, QInputDialog,
    QFileDialog, QMenu, QWidget, QFormLayout, QSplitter, QAbstractItemView,
    QHeaderView, QAction, QFrame, QShortcut, QGroupBox, QSizePolicy, QApplication
)
from PyQt5.QtGui import QFont, QColor, QIcon, QDrag, QBrush, QKeySequence, QPixmap, QPainter, QPen

# Import from app modules
from app.ui.color_scheme_pyqt import colors, APP_COLORS
from app.ui.structure_editor.ui_components import UIBuilder

class EnhancedStructureEditor(QDialog):
    """Enhanced structure editor for project templates"""
    
    # Add signals for important events
    template_renamed = pyqtSignal(str, str)  # old_name, new_name
    
    def __init__(self, parent=None, structure_name="", is_new=True, structure=None, project_type=None):
        """
        Initialize the enhanced structure editor
        
        Args:
            parent: Parent widget
            structure_name: Name of the structure to edit
            is_new: Whether this is a new structure
            structure: Structure data to load (optional)
            project_type: Associated project type (optional)
        """
        super(EnhancedStructureEditor, self).__init__(parent)
        
        # Reset state
        self.tree_widget = None
        self.structure_converter = None
        self.ui_builder = None
        self.have_file_ops = False
        self.initial_structure = structure  # Store the provided structure
        self.project_type = project_type
        
        # Set window properties
        self.is_new = is_new
        self.setWindowTitle("Structure Editor")
        self.setMinimumSize(800, 600)
        
        print(f"DEBUG: Creating structure editor - structure_name: {structure_name}, is_new: {is_new}")
        
        # Store original name for later comparison
        self.original_structure_name = structure_name
        
        # Clean template name for UI display (remove Template_ prefix if it exists)
        self.template_name = structure_name
        if structure_name and structure_name.startswith("Template_"):
            self.template_name = structure_name[len("Template_"):]
        
        # Set window title based on whether we're creating a new template or editing existing
        title = "Add New Template" if is_new else f"Edit Template: {self.template_name}"
        self.setWindowTitle(title)
        
        print(f"DEBUG: Template name set to: {self.template_name}")
        
        self.is_rename_operation = False
        self.old_template_name = ""
        self.new_template_name = ""
        
        self.create_structure_editor()
        
    def create_structure_editor(self):
        """Create and initialize the structure editor"""
        try:
            # Create storage for cached binary files
            self.files_to_cache = {}
            
            # Safety attributes to prevent crashes
            self._components_initialized = False
            
            # Create main layout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(5)
            
            # Create splitter for tree and options
            splitter = QSplitter(Qt.Horizontal)
            layout.addWidget(splitter)
            
            # Init UI builder (creates the layout and form fields)
            self.ui_builder = UIBuilder(self, self.template_name)
            
            # Initialize the tree widget and add to layout
            self.tree_widget = QTreeWidget()
            self.tree_widget.setHeaderLabels(["Name"])
            self.tree_widget.setMinimumWidth(300)
            self.tree_widget.setDragEnabled(True)
            self.tree_widget.setAcceptDrops(True)
            self.tree_widget.setDropIndicatorShown(True)
            self.tree_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
            self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
            self.tree_widget.customContextMenuRequested.connect(self._show_context_menu)
            
            # Apply styling for better appearance
            self.tree_widget.setStyleSheet("""
                QTreeWidget {
                    background-color: #2A2A2A;
                    color: #E0E0E0;
                    border: 1px solid #3A3A3A;
                    border-radius: 4px;
                    padding: 5px;
                    outline: none;
                }
                QTreeWidget::item {
                    padding: 4px;
                    border-bottom: 1px solid #3A3A3A;
                    border: none;
                    outline: none;
                }
                QTreeWidget::item:selected {
                    background-color: #2C4F76;
                    color: white;
                    border-radius: 3px;
                    border: none;
                    outline: none;
                }
                QTreeWidget::item:hover {
                    background-color: #3A3A3A;
                    border-radius: 3px;
                }
                QTreeWidget::branch {
                    border: none;
                    outline: none;
                }
                /* Style the item editor (QLineEdit when editing) */
                QTreeWidget QLineEdit {
                    background-color: #404040;
                    color: white;
                    border: 1px solid #5080B0;
                    border-radius: 3px;
                    padding: 2px 4px;
                    selection-background-color: #2C4F76;
                    min-height: 22px;
                    margin: 1px 1px;
                }
            """)
            
            # Store original keyPressEvent
            self.tree_widget._old_keyPressEvent = self.tree_widget.keyPressEvent
            # Override keyPressEvent
            self.tree_widget.keyPressEvent = self._handle_key_press
            
            # Initialize file operations handler - Always initialize this before doing anything with the tree
            try:
                from app.ui.structure_editor.file_operations import FileOperations
                self.file_operations = FileOperations(tree_widget=self.tree_widget, editor=self)
                self.have_file_ops = True
                print("DEBUG: Initialized file operations handler")
            except Exception as e:
                print(f"ERROR initializing file operations: {e}")
                import traceback
                traceback.print_exc()
                self.file_operations = None
                self.have_file_ops = False
            
            # Initialize UI components
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            left_widget.setLayout(left_layout)
            
            # Add tree widget
            left_layout.addWidget(self.tree_widget)
            
            # Setup right panel with properties
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            right_widget.setLayout(right_layout)
            
            # Add UI builder components - UIBuilder is not a QWidget
            # So create a container widget and add the UI builder's layout to it
            ui_container = QWidget()
            ui_layout = self.ui_builder.init_ui()
            ui_container.setLayout(ui_layout)
            right_layout.addWidget(ui_container)
            
            # Add left and right to splitter
            splitter.addWidget(left_widget)
            splitter.addWidget(right_widget)
            
            # Add buttons at the bottom - ONLY ONE SET OF BUTTONS
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            # Create properly styled buttons
            try:
                from app.ui.color_scheme_pyqt import BUTTON_STYLE
                button_style = BUTTON_STYLE
            except ImportError:
                button_style = """
                    QPushButton {
                        background-color: #404040;
                        color: white;
                        border: 1px solid #555555;
                        padding: 5px 15px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #4B4B4B;
                    }
                    QPushButton:pressed {
                        background-color: #353535;
                    }
                """
            
            # Create Save button - connect to accept method
            self.save_button = QPushButton("Save")
            self.save_button.setStyleSheet(button_style)
            self.save_button.clicked.connect(self.accept)
            
            # Create Cancel button - connect to reject method
            self.cancel_button = QPushButton("Cancel")
            self.cancel_button.setStyleSheet(button_style)
            self.cancel_button.clicked.connect(self.reject)
            
            button_layout.addWidget(self.cancel_button)
            button_layout.addWidget(self.save_button)
            layout.addLayout(button_layout)
            
            # Initialize drag-drop handling
            try:
                from app.ui.structure_editor.drag_drop import DragDropHandler
                self.drag_drop_handler = DragDropHandler(self.tree_widget, self)
                print("DEBUG: Initialized drag/drop handlers")
            except Exception as e:
                print(f"ERROR initializing drag/drop: {e}")
                import traceback
                traceback.print_exc()
            
            # Initialize the structure converter
            from app.ui.structure_editor.structure_converter import StructureConverter
            self.structure_converter = StructureConverter(self.tree_widget)
            
            # Create empty structure for new templates
            if self.is_new:
                # For new templates, if a structure was provided, use it
                if hasattr(self, 'initial_structure') and self.initial_structure:
                    print(f"DEBUG: Loading provided initial structure with {len(self.initial_structure)} items")
                    self.structure_converter.load_structure(self.initial_structure)
                else:
                    # Otherwise, create an empty structure
                    self.structure_converter.create_empty_structure()
            else:
                # For existing templates, attempt to load the structure
                # First, check if a structure was provided directly
                if hasattr(self, 'initial_structure') and self.initial_structure:
                    print(f"DEBUG: Loading provided structure with {len(self.initial_structure)} items")
                    self.structure_converter.load_structure(self.initial_structure)
                else:
                    # Attempt to load the structure from the template manager
                    from app.templates.template_manager import TemplateManager
                    template_manager = TemplateManager()
                    
                    # Try to get the structure - support both with and without Template_ prefix
                    structure = None
                    try:
                        # Try the original name first
                        structure = template_manager.get_structure(self.original_structure_name)
                        if not structure and self.original_structure_name.startswith("Template_"):
                            # Try without prefix
                            clean_name = self.original_structure_name[len("Template_"):]
                            structure = template_manager.get_structure(clean_name)
                        elif not structure and not self.original_structure_name.startswith("Template_"):
                            # Try with prefix
                            prefixed_name = f"Template_{self.original_structure_name}"
                            structure = template_manager.get_structure(prefixed_name)
                    except Exception as e:
                        print(f"ERROR: Failed to get structure: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    if structure:
                        print(f"DEBUG: Loading structure for {self.original_structure_name} with {len(structure)} items")
                        self.structure_converter.load_structure(structure)
                    else:
                        print(f"WARNING: No structure found for {self.original_structure_name}")
                        # Create an empty structure as fallback
                        self.structure_converter.create_empty_structure()
            
            # Connect template name field to handler
            if hasattr(self.ui_builder, 'template_name_field'):
                self.ui_builder.template_name_field.textChanged.connect(self._on_template_name_changed)
            
            self._components_initialized = True
            print("DEBUG: Structure editor initialization complete")
            
        except Exception as e:
            import traceback
            print(f"ERROR creating structure editor: {e}")
            traceback.print_exc()
            
    def _connect_signals(self):
        """Connect UI signals to their handlers"""
        print("DEBUG: Connecting signals in EnhancedStructureEditor")
        
        # Connect tree widget signals
        if hasattr(self, 'tree_widget') and self.tree_widget:
            print("DEBUG: Connecting tree widget signals")
            
            # Connect item clicks and context menu
            self.tree_widget.itemDoubleClicked.connect(self._rename_item)
            self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
            self.tree_widget.customContextMenuRequested.connect(self._show_context_menu)
            
            # Connect key press event
            self.tree_widget.keyPressEvent = self._handle_key_press
            print("DEBUG: Connected tree widget signals successfully")
        else:
            print("WARNING: No tree widget found in EnhancedStructureEditor")
            
        # Connect accept/reject signals from dialog buttons
        if hasattr(self, 'save_button') and self.save_button and hasattr(self, 'cancel_button') and self.cancel_button:
            print("DEBUG: Connecting dialog button signals")
            self.save_button.clicked.connect(self.accept)
            self.cancel_button.clicked.connect(self.reject)
            print("DEBUG: Connected dialog button signals")
        
        # Connect template name field change signal
        if hasattr(self.ui_builder, 'template_name_field') and self.ui_builder.template_name_field:
            print("DEBUG: Connecting template name field change signal")
            self.ui_builder.template_name_field.textChanged.connect(self._on_template_name_changed)
            print("DEBUG: Connected template name field signal")
            
        # Connect action buttons
        if hasattr(self, 'save_button') and self.save_button:
            print("DEBUG: Connecting save button")
            self.save_button.clicked.connect(self.accept)
            
        if hasattr(self, 'cancel_button') and self.cancel_button:
            print("DEBUG: Connecting cancel button")
            self.cancel_button.clicked.connect(self.reject)
            
        if hasattr(self, 'delete_selected') and self.delete_selected:
            print("DEBUG: Connecting delete button")
            self.delete_selected.clicked.connect(self.delete_selected)
            
        # Debug: Verify structure_converter connection
        if hasattr(self, 'structure_converter'):
            print(f"DEBUG: StructureConverter is initialized: {self.structure_converter is not None}")
        else:
            print("WARNING: No structure_converter found in EnhancedStructureEditor")
            
            # Try to initialize structure_converter if needed
            from app.ui.structure_editor.structure_converter import StructureConverter
            if hasattr(self, 'tree_widget'):
                print("DEBUG: Creating structure_converter")
                self.structure_converter = StructureConverter(self.tree_widget, self)
                print(f"DEBUG: Structure converter created: {self.structure_converter is not None}")
        
        print("DEBUG: All signals connected in EnhancedStructureEditor")
        
    def _rename_item(self, item, column):
        """
        Rename a tree item
        
        Args:
            item: The tree item to rename
            column: The column index
        """
        if not item:
            return
            
        # Just start editing the item
        if hasattr(self, 'tree_widget') and self.tree_widget and not item.isExpanded():
            self.tree_widget.editItem(item, column)
            
    def get_result(self):
        """
        Get the dialog result
        
        Returns:
            dict: Dictionary with result data (empty dict if canceled)
        """
        if not hasattr(self, 'structure_converter') or not self.structure_converter:
            print("ERROR: No structure converter available")
            return {'result': False, 'structure_name': self.original_structure_name, 'structure': []}
        
        # Get UI values first (in case template name has been updated)
        ui_values = {}
        if hasattr(self, 'ui_builder') and self.ui_builder:
            ui_values = self.ui_builder.get_ui_values()
        
        # Get the template name from UI or fallback to the stored one
        template_name = ui_values.get('template_name', self.template_name) if ui_values else self.template_name
        
        # Get structure from converter
        structure = self.structure_converter.get_structure()
        
        # For existing templates, maintain the Template_ prefix 
        if self.original_structure_name.startswith("Template_"):
            structure_name = f"Template_{template_name}"
        elif self.is_new:  # For new templates, add Template_ prefix
            structure_name = f"Template_{template_name}"
        else:  # No change needed
            structure_name = template_name
        
        print(f"DEBUG: Returning structure with {len(structure)} items")
        print(f"DEBUG: Template name: {template_name}, Structure name: {structure_name}")
        
        # Return the result data
        return {
            'result': True,
            'structure_name': structure_name,
            'template_name': template_name,
            'structure': structure,
            'ui_values': ui_values
        }
        
    def add_file(self, parent_item=None):
        """Add a file to the structure"""
        if hasattr(self, 'file_operations') and self.file_operations:
            self.file_operations.add_file(parent_item)
        else:
            print("ERROR: File operations not available")
    
    def add_folder(self, parent_item=None):
        """Add a folder to the structure"""
        if hasattr(self, 'file_operations') and self.file_operations:
            # Modify file_operations to create untitled folder and immediately trigger rename
            root = self.tree_widget.invisibleRootItem()
            if not parent_item:
                selected_items = self.tree_widget.selectedItems()
                if selected_items:
                    parent_item = selected_items[0]
                    
                    # If selected item is a file, use its parent
                    item_data = parent_item.data(0, Qt.UserRole)
                    if isinstance(item_data, dict) and 'type' in item_data and item_data['type'] == 'file':
                        if parent_item.parent():
                            parent_item = parent_item.parent()
                        else:
                            parent_item = root
                else:
                    parent_item = root
                    
            # Create untitled folder with inline editing
            folder_item = QTreeWidgetItem(parent_item)
            folder_item.setText(0, "Untitled Folder")
            folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
            
            # Set folder icon
            # Try to get the icon in multiple ways to ensure we have one
            folder_icon = None
            
            # Try system theme icon first
            folder_icon = QIcon.fromTheme("folder")
            
            # If that failed, try a hardcoded path for standard icon
            if folder_icon is None or folder_icon.isNull():
                # Check if we can find an icon in a common location
                icon_paths = [
                    os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons", "folder.png"),
                    os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons", "folder.png"),
                    os.path.join(os.path.dirname(__file__), "icons", "folder.png"),
                    "icons/folder.png"
                ]
                
                for path in icon_paths:
                    if os.path.exists(path):
                        folder_icon = QIcon(path)
                        if not folder_icon.isNull():
                            break
                
            # If we still don't have an icon, use a fallback emoji
            if folder_icon is None or folder_icon.isNull():
                # We don't have an icon, just set the text with a folder emoji
                folder_item.setText(0, "📁 Untitled Folder")
            else:
                folder_item.setIcon(0, folder_icon)
                
            # Set user data
            folder_data = {'type': 'folder', 'name': 'Untitled Folder'}
            folder_item.setData(0, Qt.UserRole, folder_data)
            
            # Style the folder item to make it stand out but without the blue box
            font = folder_item.font(0)
            font.setBold(True)
            folder_item.setFont(0, font)
            
            # Expand parent to show new folder
            if parent_item != root:
                parent_item.setExpanded(True)
                
            # Start editing immediately
            self.tree_widget.editItem(folder_item, 0)
            
            return folder_item
        else:
            print("ERROR: File operations not available")
    
    def delete_selected(self):
        """Delete selected items"""
        if hasattr(self, 'file_operations') and self.file_operations:
            self.file_operations.delete_selected()
        else:
            print("ERROR: File operations not available")
            
    def _show_context_menu(self, position):
        """Show context menu for tree widget"""
        # Check if file operations has its own context menu handler
        if hasattr(self, 'file_operations') and hasattr(self.file_operations, 'create_context_menu'):
            # Get item at position
            item = self.tree_widget.itemAt(position)
            
            # Let file operations create the context menu
            menu = self.file_operations.create_context_menu(item, position)
            if menu:
                # Execute the menu here instead of in create_context_menu
                menu.exec_(self.tree_widget.mapToGlobal(position))
                return
                
        # If file_operations not available or context menu creation failed, create our own menu
        # Create menu
        menu = QMenu(self)
        
        # Style the menu
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D30;
                color: #FFFFFF;
                border: 1px solid #3F3F46;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px 5px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #264F78;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3F3F46;
                margin: 5px;
            }
        """)
        
        # Get item at position
        item = self.tree_widget.itemAt(position)
        
        # Add common actions
        add_file_action = menu.addAction("Add File")
        add_folder_action = menu.addAction("Add Folder")
        
        # Add item-specific actions if an item is clicked
        if item:
            menu.addSeparator()
            rename_action = menu.addAction("Rename")
            delete_action = menu.addAction("Delete")
            
            # Add "Use Project Name" action for files
            item_data = item.data(0, Qt.UserRole)
            if isinstance(item_data, dict) and item_data.get('type') == 'file':
                menu.addSeparator()
                use_project_name_action = menu.addAction("Use Project Name")
                use_project_name_action.setEnabled(True)
            else:
                use_project_name_action = None
        else:
            rename_action = None
            delete_action = None
            use_project_name_action = None
        
        # Show menu and get selected action
        action = menu.exec_(self.tree_widget.mapToGlobal(position))
        
        # Handle action
        if action:
            print(f"DEBUG: Context menu action: {action.text()}")
            if action == add_file_action:
                self.add_file(item)
            elif action == add_folder_action:
                self.add_folder(item)
            elif item and action == rename_action:
                self.tree_widget.editItem(item, 0)
            elif item and action == delete_action:
                print(f"DEBUG: Delete action triggered from context menu for item: {item.text(0)}")
                self._delete_item(item)
            elif item and action == use_project_name_action:
                print(f"DEBUG: Use Project Name action triggered for item: {item.text(0)}")
                self._use_project_name_for_file(item)
    
    def _delete_item(self, item):
        """Delete an item from the tree"""
        # Confirm delete
        reply = QMessageBox.question(
            self, 
            "Confirm Delete",
            f"Are you sure you want to delete '{item.text(0)}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            print(f"DEBUG: Deleting item '{item.text(0)}'")
            # Get parent
            parent = item.parent()
            
            # Get root item
            root = self.tree_widget.invisibleRootItem()
            
            if parent:
                print(f"DEBUG: Item has parent, removing child using parent.removeChild")
                # Remove child from parent
                parent.removeChild(item)
            else:
                # For top-level items, use the root item's methods
                print(f"DEBUG: Item is a top-level item, removing from root")
                # Find the index of the item in the root
                index = root.indexOfChild(item)
                print(f"DEBUG: Top-level item index: {index}")
                if index >= 0:
                    # Remove the item from the root
                    root.takeChild(index)
                    print(f"DEBUG: Successfully removed top-level item at index {index}")
                else:
                    print(f"ERROR: Could not find index of top-level item")
                    return False
                
            # Refresh the tree view to ensure UI is updated
            self.tree_widget.update()
            
            print(f"DEBUG: Item deleted successfully")
            return True
        
        return False
    
    def _use_project_name_for_file(self, item):
        """Set a file to use the project name"""
        if not item:
            print("DEBUG: use_project_name - no item provided")
            return
        
        # Get item data
        item_data = item.data(0, Qt.UserRole)
        if not isinstance(item_data, dict) or item_data.get('type') != 'file':
            print(f"DEBUG: use_project_name - item is not a file: {item.text(0)}")
            return
        
        # Get file extension (if any)
        name = item.text(0)
        extension = ""
        if "." in name:
            extension = "." + name.split(".")[-1]
        
        # Use ${PROJECT_NAME} as the placeholder that will be replaced later
        # This ensures it's clear this will be dynamically replaced
        placeholder = "${PROJECT_NAME}"
        
        # Log placeholder details for debugging
        print(f"🔍 PLACEHOLDER DEBUG: Raw placeholder: '{placeholder}'")
        print(f"🔍 PLACEHOLDER DEBUG: Placeholder length: {len(placeholder)}")
        print(f"🔍 PLACEHOLDER DEBUG: Placeholder bytes: {placeholder.encode('utf-8')}")
        print(f"🔍 PLACEHOLDER DEBUG: First character: '{placeholder[0]}' (code: {ord(placeholder[0])})")
        
        # Set the display name to explicitly show the placeholder
        # This makes it very clear to the user that this will be replaced
        new_name = f"{placeholder}{extension}"
        
        print(f"DEBUG: use_project_name - changing name from '{name}' to '{new_name}'")
        print(f"🔍 PLACEHOLDER DEBUG: New name first char: '{new_name[0]}' (code: {ord(new_name[0])})")
        print(f"🔍 PLACEHOLDER DEBUG: New name bytes: {new_name.encode('utf-8')}")
        
        # Update item display text with the actual placeholder
        item.setText(0, new_name)
        
        # Update data - store both the display name and the placeholder
        item_data['name'] = new_name
        item_data['uses_project_name'] = True
        item_data['placeholder'] = placeholder  # Store the placeholder that will be replaced
        item_data['original_extension'] = extension
        item.setData(0, Qt.UserRole, item_data)
        
        # Apply styling to indicate dynamic name - make it VERY clear this is special
        font = item.font(0)
        font.setItalic(True)
        item.setFont(0, font)
        
        # Use blue color from our app color scheme for consistency
        try:
            from app.ui.color_scheme_pyqt import colors
            item.setForeground(0, QBrush(QColor(colors.get("accent", "#4A9BFF"))))
        except (ImportError, AttributeError):
            # Fallback if color scheme isn't available
            item.setForeground(0, QBrush(QColor("#4A9BFF")))
        
        print(f"DEBUG: use_project_name - file marked to use project name: {new_name}")
        
        # After setting text, verify what the item actually displays
        displayed_text = item.text(0)
        print(f"🔍 PLACEHOLDER DEBUG: Displayed text: '{displayed_text}'")
        print(f"🔍 PLACEHOLDER DEBUG: Displayed text first char: '{displayed_text[0]}' (code: {ord(displayed_text[0])})")
        print(f"🔍 PLACEHOLDER DEBUG: Displayed text bytes: {displayed_text.encode('utf-8')}")
        
        # Check if the placeholder was correctly applied
        if displayed_text != new_name:
            print(f"🚨 WARNING: Displayed text doesn't match expected new name!")
            print(f"🚨 Expected: '{new_name}', got: '{displayed_text}'")

    def _on_template_name_changed(self, new_name):
        """Handle template name changed event"""
        if not new_name:
            return
        
        # Debug logging for rename tracking
        old_template_name = self.template_name if hasattr(self, 'template_name') else "None"
        old_structure_name = self.structure_name if hasattr(self, 'structure_name') else "None"
        
        print(f"🔶 TEMPLATE NAME LISTENER: Name changing from '{old_template_name}' to '{new_name}'")
        print(f"🔶 TEMPLATE NAME LISTENER: Original structure name: '{self.original_structure_name}'")
        
        # Remove any Template_ prefix from display name
        clean_name = new_name
        if clean_name.startswith("Template_"):
            clean_name = clean_name[9:]  # Remove prefix
        
        # Update template name attribute - storing the clean name without prefix
        self.template_name = clean_name
        
        # Update window title
        self.setWindowTitle(f"{'Add New' if self.is_new else 'Edit'} Template - {clean_name}")
        
        # For structure_name, preserve Template_ prefix for existing templates
        if not self.is_new and self.original_structure_name.startswith("Template_"):
            # Structure name should include Template_ prefix
            self.structure_name = f"Template_{clean_name}"
        else:
            # For new templates or templates without prefix, set structure name to match template name
            # The prefix will be added when saving if needed
            self.structure_name = clean_name
        
        print(f"🔶 TEMPLATE NAME LISTENER: Template name changed to '{clean_name}', structure_name='{self.structure_name}'")
        print(f"🔶 TEMPLATE NAME LISTENER: Will be stored as '{self.structure_name}' in template manager")
        
        # Update UI builder if available
        if hasattr(self, 'ui_builder') and hasattr(self.ui_builder, 'template_name_field'):
            # Only update if the text has actually changed to avoid recursion
            current_text = self.ui_builder.template_name_field.text()
            if current_text != clean_name:
                print(f"🔶 TEMPLATE NAME LISTENER: Updated template name field to '{clean_name}'")
                self.ui_builder.template_name_field.setText(clean_name)
        
        # If we have access to the template manager, check if this name already exists
        template_manager = None
        if hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'template_manager'):
            template_manager = self.parent.template_manager
        elif hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'app') and hasattr(self.parent.app, 'template_manager'):
            template_manager = self.parent.app.template_manager
        
        # Check if we need to update the UI or notify listeners of the name change
        if not self.is_new and old_template_name != clean_name:
            # This is a rename operation - store the information for later use during save
            print(f"🔶 TEMPLATE NAME LISTENER: Detected template rename from '{old_template_name}' to '{clean_name}'")
            
            # Store the rename information for the accept method
            self.is_rename_operation = True
            self.old_template_name = old_template_name
            self.new_template_name = clean_name
            
            # Emit a signal if this editor has one
            if hasattr(self, 'template_renamed') and callable(getattr(self, 'template_renamed', None)):
                print(f"🔶 TEMPLATE NAME LISTENER: Emitting template_renamed signal")
                self.template_renamed.emit(old_template_name, clean_name)
        
        if template_manager and hasattr(template_manager, 'get_template_by_name'):
            existing_template = template_manager.get_template_by_name(clean_name)
            if existing_template and (not hasattr(self, 'original_structure_name') or 
                                     (self.original_structure_name != clean_name and
                                      f"Template_{self.original_structure_name}" != self.original_structure_name)):
                print(f"🔶 TEMPLATE NAME LISTENER: WARNING: Template name '{clean_name}' already exists. This may overwrite an existing template.")

    def _handle_key_press(self, event):
        """
        Handle key press events
        
        Args:
            event: The key press event
        """
        # Check if we have file operations
        have_file_ops = hasattr(self, 'file_operations') and self.file_operations
        
        # Delete key for removing selected items
        if event.key() == Qt.Key_Delete and have_file_ops:
            print("DEBUG: Delete key pressed, calling delete_selected()")
            self.file_operations.delete_selected()
            event.accept()  # Mark as handled
            return True  # Return True to indicate the event was handled
        
        # Ctrl+A for select all
        if event.key() == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            self.tree_widget.selectAll()
            event.accept()  # Mark as handled
            return True
        
        # Ctrl+C for copy (handled by file operations)
        if event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier and have_file_ops:
            selected = self.tree_widget.selectedItems()
            if selected and hasattr(self.file_operations, '_copy_item'):
                self.file_operations._copy_item(selected[0])
                event.accept()  # Mark as handled
                return True
            
        # Ctrl+V for paste (handled by file operations)
        if event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier and have_file_ops:
            selected = self.tree_widget.selectedItems()
            parent = selected[0] if selected else self.tree_widget.invisibleRootItem() 
            if hasattr(self.file_operations, '_paste_item'):
                self.file_operations._paste_item(parent)
                event.accept()  # Mark as handled
                return True
        
        # F2 for rename
        if event.key() == Qt.Key_F2 and have_file_ops:
            selected = self.tree_widget.selectedItems()
            if selected and hasattr(self.file_operations, 'rename_item'):
                self.file_operations.rename_item(selected[0])
                event.accept()  # Mark as handled
                return True
        
        # Call original event handler
        QTreeWidget.keyPressEvent(self.tree_widget, event) 

    def closeEvent(self, event):
        """
        Handle dialog close event
        
        Args:
            event: Close event
        """
        # Clean up resources before closing
        self._cleanup()
        event.accept()

    def _cleanup(self):
        """Clean up resources before closing"""
        try:
            # Disconnect signals
            if hasattr(self, 'ui_builder') and hasattr(self.ui_builder, 'template_name_field'):
                try:
                    self.ui_builder.template_name_field.textChanged.disconnect()
                except:
                    pass

            if hasattr(self, 'tree_widget'):
                # Disconnect tree signals
                try:
                    self.tree_widget.itemDoubleClicked.disconnect()
                except:
                    pass
                
                # Reset key event handler
                if hasattr(self.tree_widget, '_old_keyPressEvent'):
                    self.tree_widget.keyPressEvent = self.tree_widget._old_keyPressEvent
                
            print("DEBUG: Cleaned up structure editor resources")
        except Exception as e:
            print(f"WARNING: Error during cleanup: {e}")
            # Continue with cleanup anyway 

    def accept(self):
        """Dialog accepted - save data and close"""
        try:
            # Get the template name from the UI
            template_name = ""
            structure_name = ""
            if hasattr(self, 'ui_builder') and hasattr(self.ui_builder, 'template_name_field'):
                template_name = self.ui_builder.template_name_field.text()
                
                # Use UI structure name if available
                if hasattr(self, 'structure_name'):
                    structure_name = self.structure_name
                else:
                    # Derive structure name from template name
                    if not template_name.startswith("Template_"):
                        structure_name = f"Template_{template_name}"
                    else:
                        structure_name = template_name
            else:
                # Use stored structure name
                if hasattr(self, 'template_name') and self.template_name:
                    template_name = self.template_name
                if hasattr(self, 'structure_name') and self.structure_name:
                    structure_name = self.structure_name
            
            print(f"DEBUG: Template name: {template_name}, Structure name: {structure_name}")
            
            # Get the structure data from the editor
            structure = []
            if hasattr(self, 'structure_converter') and self.structure_converter:
                structure = self.structure_converter.get_structure()
                
            print(f"DEBUG: Structure has {len(structure)} items")
            
            # Store the UI values in the result data
            ui_values = {}
            if hasattr(self, 'ui_builder') and hasattr(self.ui_builder, 'get_ui_values'):
                ui_values = self.ui_builder.get_ui_values()
            
            # Store data for return
            self.result_data = {
                'result': True,
                'template_name': template_name,
                'structure_name': structure_name,
                'structure': structure,
                'ui_values': ui_values,
                'is_rename': hasattr(self, 'is_rename_operation') and self.is_rename_operation
            }
            
            # If this is a rename operation, add the old name
            if hasattr(self, 'is_rename_operation') and self.is_rename_operation:
                self.result_data['old_template_name'] = self.old_template_name
                self.result_data['new_template_name'] = self.new_template_name
                print(f"DEBUG: This is a rename operation from '{self.old_template_name}' to '{self.new_template_name}'")
                
                # Emit the template_renamed signal if it's defined
                if hasattr(self, 'template_renamed'):
                    self.template_renamed.emit(self.old_template_name, self.new_template_name)
            
            # Close the dialog
            super().accept()
        except Exception as e:
            print(f"ERROR in accept: {e}")
            import traceback
            traceback.print_exc()
            super().reject() 

    def load_structure(self, structure):
        """Load a structure into the editor
        
        Args:
            structure: The structure data to load
        """
        print(f"DEBUG: Loading structure in EnhancedStructureEditor: {type(structure)}")
        
        # Ensure structure_converter is initialized
        if not hasattr(self, 'structure_converter') or not self.structure_converter:
            print("DEBUG: Initializing structure_converter in load_structure")
            from app.ui.structure_editor.structure_converter import StructureConverter
            if hasattr(self, 'tree_widget'):
                self.structure_converter = StructureConverter(self.tree_widget, self)
            else:
                print("ERROR: Cannot initialize structure_converter - no tree widget found")
                return False
        
        # Load the structure
        try:
            print(f"DEBUG: Calling structure_converter.load_structure with {len(structure) if isinstance(structure, list) else 'non-list'} structure")
            result = self.structure_converter.load_structure(structure)
            print(f"DEBUG: Structure loading result: {result}")
            
            # Store the loaded structure
            self.initial_structure = structure
            
            # Verify the structure was loaded correctly by checking tree
            if hasattr(self.structure_converter, 'verify_structure'):
                print(f"DEBUG: Verifying structure after loading")
                verification = self.structure_converter.verify_structure()
                print(f"DEBUG: Structure verification: {verification}")
            
            return True
        except Exception as e:
            print(f"ERROR: Failed to load structure: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_structure(self):
        """Get the current structure
        
        Returns:
            list: The current structure
        """
        print("DEBUG: Getting structure from EnhancedStructureEditor")
        
        # Ensure we have a structure_converter
        if not hasattr(self, 'structure_converter') or not self.structure_converter:
            print("DEBUG: No structure_converter found, initializing")
            from app.ui.structure_editor.structure_converter import StructureConverter
            
            # Get tree widget
            tree_widget = None
            if hasattr(self, 'tree_widget'):
                tree_widget = self.tree_widget
            
            if tree_widget:
                self.structure_converter = StructureConverter(tree_widget, self)
                print(f"DEBUG: Created structure_converter: {self.structure_converter is not None}")
            else:
                print("ERROR: Cannot create structure_converter - no tree widget found")
                # Return empty structure as fallback
                return []
        
        try:
            # Get the structure from the converter
            print("DEBUG: Calling structure_converter.get_structure")
            structure = self.structure_converter.get_structure()
            
            print(f"DEBUG: Got structure with {len(structure)} items")
            
            # Do a quick verification
            if hasattr(self.structure_converter, 'verify_structure'):
                verification = self.structure_converter.verify_structure()
                print(f"DEBUG: Structure verification on get: {verification}")
                
            return structure
        except Exception as e:
            print(f"ERROR: Failed to get structure: {e}")
            import traceback
            traceback.print_exc()
            # Return empty structure as fallback
            return [] 
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
import platform # Added platform import
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QComboBox, QMessageBox, QInputDialog,
    QFileDialog, QMenu, QWidget, QFormLayout, QSplitter, QAbstractItemView,
    QHeaderView, QAction, QFrame, QShortcut, QGroupBox, QSizePolicy, QApplication
)
from PyQt5.QtGui import QFont, QColor, QIcon, QDrag, QBrush, QKeySequence, QPixmap, QPainter, QPen

# Import from app modules
from app.ui.color_scheme_pyqt import colors, APP_COLORS, ACCENT_BUTTON_STYLE
from app.ui.structure_editor.ui_components import UIBuilder

class EnhancedStructureEditor(QDialog):
    """Enhanced structure editor for project templates"""
    
    # Add signals for important events
    template_renamed = pyqtSignal(str, str)  # old_name, new_name
    
    # Signal emitted when the structure is saved
    structureSaved = pyqtSignal(dict) 
    
    def __init__(self, parent=None, structure_name="", is_new=True, structure=None, project_type=None, template_manager=None, template_data=None):
        """
        Initialize the enhanced structure editor
        
        Args:
            parent: Parent widget
            structure_name: Name of the structure to edit
            is_new: Whether this is a new structure
            structure: Structure data to load (optional)
            project_type: Associated project type (optional)
            template_manager: Template manager instance (optional)
            template_data: Pre-fetched template data (optional)
        """
        super(EnhancedStructureEditor, self).__init__(parent)
        
        # Store template manager instance
        self.template_manager = template_manager
        self.template_data = template_data # Store passed template data
        
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
        self.setMinimumSize(800, 800)
        
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
            
            # Create the UI Builder instance
            self.ui_builder = UIBuilder(self, self.template_name)
            # Connect the UIBuilder signal to the editor's method
            self.ui_builder.manage_categories_requested.connect(self._open_category_manager)
            
            # Initialize file operations handler - Always initialize this before doing anything with the tree
            try:
                from app.ui.structure_editor.file_operations import FileOperations
                self.tree_widget = None  # Will be created by UIBuilder
                self.file_operations = FileOperations(tree_widget=None, editor=self)
                self.have_file_ops = True
                print("DEBUG: Initialized file operations handler")
            except Exception as e:
                print(f"ERROR initializing file operations: {e}")
                import traceback
                traceback.print_exc()
                self.file_operations = None
                self.have_file_ops = False
            
            # Create the UI using the UIBuilder's unified layout
            ui_layout = self.ui_builder.init_ui()
            
            # Add the UIBuilder layout to the main layout
            content_widget = QWidget()
            content_widget.setLayout(ui_layout)
            layout.addWidget(content_widget, 1)  # Give it stretch factor of 1
            
            # Get reference to the tree widget created by UIBuilder
            self.tree_widget = self.ui_builder.tree
            
            # Ensure consistent styling with branch indicators and folder icons
            try:
                from app.ui.tree_styling import apply_enhanced_tree_styling
                apply_enhanced_tree_styling(self.tree_widget)
                print("DEBUG: Applied enhanced tree styling with branch indicators")
            except Exception as e:
                print(f"WARNING: Could not apply enhanced tree styling: {e}")
            
            # Setup QShortcut for Delete key on the tree_widget
            if self.tree_widget:
                delete_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self.tree_widget)
                delete_shortcut.activated.connect(self._schedule_delete_operation)
                delete_shortcut.setContext(Qt.WidgetShortcut)
                print("DEBUG: QShortcut for Delete key connected to _schedule_delete_operation")

                # Add Backspace shortcut for macOS
                if platform.system() == "Darwin":
                    backspace_shortcut = QShortcut(QKeySequence(Qt.Key_Backspace), self.tree_widget)
                    backspace_shortcut.activated.connect(self._schedule_delete_operation)
                    backspace_shortcut.setContext(Qt.WidgetShortcut)
                    print("DEBUG: QShortcut for Backspace key (macOS) connected to _schedule_delete_operation")
            
            # Connect tree widget signals
            if self.tree_widget:
                # Connect context menu
                self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
                self.tree_widget.customContextMenuRequested.connect(self._show_context_menu)
                
                # Store original keyPressEvent
                self.tree_widget._old_keyPressEvent = self.tree_widget.keyPressEvent
                # Override keyPressEvent
                self.tree_widget.keyPressEvent = self._handle_key_press
                
                # Update file operations handler with the tree
                if self.file_operations:
                    self.file_operations.tree = self.tree_widget
            
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
            # Use ACCENT_BUTTON_STYLE for primary action
            self.save_button.setStyleSheet(ACCENT_BUTTON_STYLE)
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
            
            # Load initial structure if provided
            if self.initial_structure is not None:
                print(f"DEBUG: Loading provided initial structure: {type(self.initial_structure)}")
                try:
                    # Load structure into the tree
                    self.load_structure(self.initial_structure)
                    print("DEBUG: Initial structure loaded into tree")
                except Exception as e:
                    print(f"ERROR loading initial structure: {e}")
                    QMessageBox.warning(self, "Load Error", f"Failed to load initial structure: {e}")

            # --- Use Passed Template Info and Set UI ---
            if not self.is_new and self.template_data:
                self.ui_builder.set_ui_values(self.template_data)
            else:
                print(f"DEBUG: Setting name field to: {self.template_name}")
                self.ui_builder.template_name_field.setText(self.template_name)
                # Explicitly set dropdown to 'No Category' for new templates
                if self.is_new:
                    no_cat_index = self.ui_builder.template_category_field.findText("No Category")
                    if no_cat_index >= 0:
                        self.ui_builder.template_category_field.setCurrentIndex(no_cat_index)

            # Set initial focus
            if self.ui_builder and self.ui_builder.template_name_field:
                self.ui_builder.template_name_field.setFocus()
                self.ui_builder.template_name_field.selectAll()
                print("DEBUG: Set focus to template name field")
            
            self._components_initialized = True
            print("DEBUG: Structure editor components initialized")
            
        except Exception as e:
            print(f"CRITICAL ERROR during structure editor creation: {e}")
            import traceback
            traceback.print_exc()
            # Ensure dialog still exists for error message
            if not self.parent(): # Check if parent exists before showing message box
                app = QApplication.instance()
                if app: # Check if QApplication instance exists
                    QMessageBox.critical(None, "Editor Error", f"Failed to create structure editor: {e}")
            else:
                QMessageBox.critical(self.parent(), "Editor Error", f"Failed to create structure editor: {e}")
            # Optionally, close the dialog automatically on critical failure
            # self.reject() # or self.close()
            
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
        
        # Store original name if we don't already have it
        current_name = item.text(0)
        if 'original_name' not in item_data:
            item_data['original_name'] = current_name
        
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
        display_placeholder_name = f"{placeholder}{extension}"
        
        print(f"DEBUG: use_project_name - changing display from '{name}' to '{display_placeholder_name}'")
        print(f"🔍 PLACEHOLDER DEBUG: New name first char: '{display_placeholder_name[0]}' (code: {ord(display_placeholder_name[0])})")
        print(f"🔍 PLACEHOLDER DEBUG: New name bytes: {display_placeholder_name.encode('utf-8')}")
        
        # Update item display text with the actual placeholder (for visual feedback only)
        item.setText(0, display_placeholder_name)
        
        # Update data - keep the original name but set the flags
        # IMPORTANT: Don't modify the 'name' field, just add the flags
        # Set both flags for backward compatibility, but rename_flag is the primary flag
        item_data['rename_flag'] = True  # Primary flag for indicating that file should be renamed
        item_data['uses_project_name'] = True  # Keep for backward compatibility
        item_data['original_extension'] = extension
        item.setData(0, Qt.UserRole, item_data)
        
        # Apply styling to indicate this is a dynamic file
        font = item.font(0)
        font.setItalic(True)
        item.setFont(0, font)
        
        # Also use a different color to make it clear
        item.setForeground(0, QBrush(QColor("#4A9BFF")))
        
        return True
        
    def _toggle_project_name_for_file(self, item):
        """Toggle between using project name and original name for a file"""
        if not item:
            return False
            
        # Get item data
        item_data = item.data(0, Qt.UserRole)
        if not isinstance(item_data, dict) or item_data.get('type') != 'file':
            return False
            
        # Check current state - prioritize rename_flag but check uses_project_name for backward compatibility
        rename_flag = item_data.get('rename_flag', False)
        uses_project_name = item_data.get('uses_project_name', False)
        
        if rename_flag or uses_project_name:
            # Currently using project name, switch back to original name display
            original_name = item_data.get('original_name')
            if not original_name:
                print("ERROR: Original name not found, cannot toggle")
                return False
                
            # Update display to show original name
            item.setText(0, original_name)
            
            # Update data - turn off both flags but keep original_name for future use
            item_data['rename_flag'] = False  # Primary flag indicating rename should not happen
            item_data['uses_project_name'] = False  # Keep in sync for backward compatibility
            
            # Restore normal styling
            font = item.font(0)
            font.setItalic(False)
            item.setFont(0, font)
            item.setForeground(0, QBrush(QColor("#000000")))
            
            print(f"DEBUG: Toggled file back to original name display: {original_name}")
        else:
            # Not using project name, switch to using project name
            return self._use_project_name_for_file(item)
            
        # Update the data
        item.setData(0, Qt.UserRole, item_data)
        
        return True

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

        # First, let the original event handler try to process the event.
        # This is important for allowing default Qt behaviors.
        if hasattr(self.tree_widget, '_old_keyPressEvent') and self.tree_widget._old_keyPressEvent is not None:
            self.tree_widget._old_keyPressEvent(event)
        else:
            # Fallback if _old_keyPressEvent isn't there
            super(QTreeWidget, self.tree_widget).keyPressEvent(event)

        # Custom key handling (if not already handled by base)
        # Note: Qt.Key_Delete is now handled by QShortcut, so it's removed from here.
        
        # Ctrl+A for select all (typically handled well by base, but can be explicit)
        if event.key() == Qt.Key_A and event.modifiers() & Qt.ControlModifier: # Changed from elif to if
            if hasattr(self, 'tree_widget') and self.tree_widget and not event.isAccepted():
                self.tree_widget.selectAll()
                event.accept()
        
        # Ctrl+C for copy (if not already handled)
        elif event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier and have_file_ops and not event.isAccepted():
            selected = self.tree_widget.selectedItems()
            if selected and hasattr(self.file_operations, '_copy_item'):
                self.file_operations._copy_item(selected[0])
                event.accept()
            
        # Ctrl+V for paste (if not already handled)
        elif event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier and have_file_ops and not event.isAccepted():
            selected = self.tree_widget.selectedItems()
            parent = selected[0] if selected else self.tree_widget.invisibleRootItem() 
            if hasattr(self.file_operations, '_paste_item'):
                self.file_operations._paste_item(parent)
                event.accept()
        
        # F2 for rename (if not already handled)
        elif event.key() == Qt.Key_F2 and have_file_ops and not event.isAccepted():
            selected = self.tree_widget.selectedItems()
            if selected and hasattr(self.file_operations, 'rename_item'):
                self.file_operations.rename_item(selected[0])
                event.accept()
        
        # The method must return a boolean. event.isAccepted() reflects if any handler
        # (ours or the base's) accepted the event.
        return event.isAccepted()

    def _schedule_delete_operation(self):
        """Schedules the delete operation to run after the current event processing."""
        QTimer.singleShot(0, self._perform_delete_operation)

    def _perform_delete_operation(self):
        """Performs the actual deletion of selected items."""
        if hasattr(self, 'file_operations') and self.file_operations:
            print("DEBUG: Performing scheduled delete operation via file_operations.delete_selected()")
            self.file_operations.delete_selected()
        else:
            print("DEBUG: Scheduled delete operation: file_operations not available.")

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
        """Handle the dialog acceptance (Save)"""
        print("\n[DEBUG] EnhancedStructureEditor.accept called")

        # --- 1. Get UI Data ---
        try:
            ui_values = self.ui_builder.get_ui_values()
            updated_template_name = ui_values.get('template_name')
            selected_category = ui_values.get('category', 'General') # Get category, default to 'General'
            template_description = ui_values.get('description', '')
            print(f"[DEBUG] UI Values retrieved: Name='{updated_template_name}', Category='{selected_category}'")
        except Exception as e:
            print(f"[ERROR] Failed to get UI values: {e}")
            QMessageBox.warning(self, "Error", "Could not retrieve template details from form.")
            return

        # Check if template name is empty
        if not updated_template_name:
            QMessageBox.warning(self, "Missing Name", "Please enter a name for the template.")
            if self.ui_builder and self.ui_builder.template_name_field:
                self.ui_builder.template_name_field.setFocus()
            return

        # --- 2. Get Structure Data ---
        try:
            if not self.structure_converter:
                raise ValueError("Structure converter is not initialized")
            updated_structure = self.structure_converter.get_structure()
            print(f"[DEBUG] Structure retrieved from tree: {len(updated_structure)} items")
        except Exception as e:
            print(f"[ERROR] Failed to get structure from tree: {e}")
            QMessageBox.warning(self, "Error", f"Could not retrieve structure from tree: {e}")
            return

        # --- 3. Construct Structure Name ---
        # Ensure structure name always starts with "Template_"
        if updated_template_name.startswith("Template_"):
            updated_structure_name = updated_template_name
        else:
            updated_structure_name = f"Template_{updated_template_name}"

        # --- 4. Determine if Renaming ---
        is_rename = not self.is_new and self.original_structure_name and updated_structure_name != self.original_structure_name
        print(f"[DEBUG] Is Rename: {is_rename} (Original: '{self.original_structure_name}', New: '{updated_structure_name}')")

        # --- 5. Save Structure ---
        try:
            # Check if template manager is available
            # Use self.template_manager if it was passed during initialization
            # or attempt to get it from the parent if not directly available.
            template_manager_instance = None
            if hasattr(self, 'template_manager') and self.template_manager:
                template_manager_instance = self.template_manager
            elif hasattr(self.parent(), 'template_manager'):
                template_manager_instance = self.parent().template_manager
                print("[DEBUG] Acquired template_manager from parent")
            
            if not template_manager_instance:
                raise AttributeError("Template manager instance is not available.")

            print(f"[DEBUG] Attempting to save structure: Name='{updated_structure_name}', TemplateName='{updated_template_name}'")
            
            # Create save parameters with additional info for rename operations
            save_params = {
                "name": updated_structure_name,
                "structure": updated_structure,
                "category": selected_category
            }
            
            # If this is a rename operation, add the original name to ensure proper cleanup
            if is_rename:
                save_params["original_name"] = self.original_structure_name
                print(f"[DEBUG] Adding original_name '{self.original_structure_name}' for rename operation")
            
            # Pass the save parameters to the save function
            success = template_manager_instance.save_custom_structure(**save_params)

            if not success:
                raise RuntimeError("Failed to save the structure via Template Manager.")
            print(f"[DEBUG] Structure saved successfully for '{updated_structure_name}'")

            # After successfully saving the structure and template data, refresh the gallery
            # Check if the parent object (likely the gallery or main app) has a refresh method
            parent_widget = self.parent()
            if parent_widget and hasattr(parent_widget, 'refresh_gallery'):
                print(f"[DEBUG] Calling parent widget's refresh_gallery method")
                parent_widget.refresh_gallery()
            elif parent_widget and hasattr(parent_widget, 'populate_gallery'): # Alternative refresh method
                print(f"[DEBUG] Calling parent widget's populate_gallery method")
                parent_widget.populate_gallery(force_refresh=True)
            elif hasattr(self, 'template_manager') and self.template_manager and hasattr(self.template_manager, 'load_templates'):
                # Fallback: Reload templates in the manager if direct refresh isn't found
                print(f"[DEBUG] Refresh method not found on parent, reloading templates in manager")
                self.template_manager.load_templates()

        except Exception as e:
            print(f"[ERROR] Failed to save structure: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Save Failed", f"Could not save the template structure: {e}")
            return # Important: Do not accept the dialog if save fails

        # --- 6. Handle Rename (if applicable) ---
        if is_rename:
            print(f"[DEBUG] Handling rename from '{self.original_structure_name}' to '{updated_structure_name}'")
            # Perform rename logic if needed, maybe in template manager?
            # Currently, save_custom_structure handles creating new/updating existing
            # We might need to explicitly delete the old file if the name format changes filename
            # Example: If old name was "My Template" -> Template_My_Template.json
            # And new name is "My Renamed Template" -> Template_My_Renamed_Template.json
            # We need to ensure the old file is removed.
            # TemplateManager.rename_template might be better suited here?
            # For now, assume save handles the update correctly.

            # Emit signal for rename
            self.template_renamed.emit(self.original_structure_name.replace("Template_", ""), updated_template_name)

        # --- 7. Cleanup and Accept ---
        self._cleanup()
        super(EnhancedStructureEditor, self).accept()
        print("[DEBUG] EnhancedStructureEditor accepted successfully")

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

    def _open_category_manager(self):
        """Opens the category manager dialog."""
        # Try accessing template_manager through self.app, fallback to parent's app
        template_manager = None
        if hasattr(self, 'app') and self.app and hasattr(self.app, 'template_manager'):
            template_manager = self.app.template_manager
        elif self.parent() and hasattr(self.parent(), 'app') and self.parent().app and hasattr(self.parent().app, 'template_manager'):
             print("DEBUG: Accessing template_manager via parent widget.")
             template_manager = self.parent().app.template_manager
        
        if not template_manager:
            print("ERROR: Template manager not available via self.app or parent().app")
            # Optionally, show an error message to the user
            QMessageBox.critical(self, "Error", "Could not access category data.")
            return

        # Get current categories from the reliable source
        current_categories = template_manager.get_categories()

        # Create and execute the category manager dialog
        from app.ui.structure_editor.category_manager import CategoryManager
        manager_dialog = CategoryManager(parent=self, categories=current_categories)
        result = manager_dialog.exec_()

        if result == QDialog.Accepted:
            print("DEBUG: Category Manager accepted. Dropdown updates handled dynamically.")
            # Updates are handled dynamically by the CategoryManager itself now.
            # No explicit update needed here, but we could refresh internal state if necessary.
            # self.ui_builder.categories = template_manager.get_categories()
        else:
            print("DEBUG: Category Manager cancelled.") 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
File Operations Module for Structure Editor
Main coordinator for file and folder operations, context menus, and versioning
"""

import os
from PyQt6.QtWidgets import QTreeWidgetItem, QDialog
from PyQt6.QtCore import Qt

# Import all the refactored modules
from .utils.file_type_detector import FileTypeDetector
from .utils.tree_item_helpers import TreeItemHelpers
from .handlers.binary_file_handler import BinaryFileHandler
from .operations.basic_file_operations import BasicFileOperations
from .operations.import_operations import ImportOperations
from .operations.context_menu_operations import ContextMenuOperations
from .operations.item_operations import ItemOperations
from .operations.tree_operations import TreeOperations
from .patterns.pattern_applier import PatternApplier
from .patterns.versioning_applier import VersioningApplier
from .patterns.date_applier import DateApplier
from .dialogs.file_details_dialog import FileDetailsDialog
from .dialogs.versioning_dialog import VersioningDialog
from .dialogs.date_sequence_dialog import DateSequenceDialog
from .dialogs.custom_patterns.pattern_ui_components import PatternUIComponents
from .dialogs.custom_patterns.custom_options_manager import CustomOptionsManager
from .dialogs.custom_patterns.format_managers import FormatManagers
from .dialogs.custom_patterns.pattern_logic import PatternLogic
from .dialogs.custom_patterns.pattern_data_handler import PatternDataHandler


class FileOperations:
    """Main coordinator for file and folder operations in the structure editor"""
    
    def __init__(self, tree_widget=None, editor=None):
        """Initialize file operations handler"""
        self.tree_widget = tree_widget
        self.editor = editor
        self.current_context_item = None
        self._context_menu_connected = False
        
        # Initialize all component modules
        self.file_type_detector = FileTypeDetector()
        self.tree_item_helpers = TreeItemHelpers()
        self.binary_handler = BinaryFileHandler()
        self.basic_operations = BasicFileOperations(self)
        self.import_operations = ImportOperations(self)
        self.context_menu_operations = ContextMenuOperations(self)
        self.item_operations = ItemOperations(self)
        self.tree_operations = TreeOperations(self)
        self.pattern_applier = PatternApplier(self)
        self.versioning_applier = VersioningApplier(self)
        self.date_applier = DateApplier(self)
        
        # Connect context menu if tree widget is available
        if self.tree_widget:
            self._connect_context_menu()
            print("DEBUG: Connected context menu to tree widget")
        else:
            print("DEBUG: No tree widget provided to FileOperations")
        
        print("DEBUG: Initialized file operations handler with all modules")

    def _connect_context_menu(self):
        """Connect context menu signal only if not already connected"""
        if self.tree_widget and not self._context_menu_connected:
            self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.tree_widget.customContextMenuRequested.connect(self.create_context_menu)
            self._context_menu_connected = True
            print("DEBUG: Context menu signal connected")
        elif self._context_menu_connected:
            print("DEBUG: Context menu already connected, skipping duplicate connection")

    def set_tree_widget(self, tree_widget):
        """Set or update the tree widget reference"""
        # Disconnect from old tree widget if needed
        if self.tree_widget and self._context_menu_connected:
            try:
                self.tree_widget.customContextMenuRequested.disconnect(self.create_context_menu)
                self._context_menu_connected = False
                print("DEBUG: Disconnected context menu from old tree widget")
            except:
                pass  # Connection might not exist
        
        self.tree_widget = tree_widget
        if self.tree_widget:
            self._connect_context_menu()
            print("DEBUG: Updated tree widget reference and connected context menu")
        else:
            print("DEBUG: Tree widget set to None")
            self._context_menu_connected = False

    # Delegate core operations to specialized modules
    def add_file(self, parent_item=None, file_name=None, file_type=None):
        """Add a new file to the structure"""
        return self.basic_operations.add_file(parent_item, file_name, file_type)

    def add_folder(self, parent_item=None, folder_name=None):
        """Add a new folder to the structure"""
        return self.basic_operations.add_folder(parent_item, folder_name)

    def delete_selected(self):
        """Delete selected items from the tree"""
        return self.basic_operations.delete_selected()

    def rename_item(self, item):
        """Rename an item in the tree"""
        return self.basic_operations.rename_item(item)

    def import_directory(self, target_item=None):
        """Import a directory structure"""
        return self.import_operations.import_directory(target_item)

    def import_file(self, target_item=None):
        """Import a single file"""
        return self.import_operations.import_file(target_item)

    def create_context_menu(self, position):
        """Create and show context menu"""
        return self.context_menu_operations.create_context_menu(position)

    # Pattern application methods
    def _apply_pattern_to_item(self, item, pattern_data):
        """Apply pattern to an item"""
        return self.pattern_applier.apply_pattern_to_item(item, pattern_data)

    def _apply_versioning_to_item(self, item, versioning_data):
        """Apply versioning to an item"""
        return self.versioning_applier.apply_versioning_to_item(item, versioning_data)

    def _apply_date_sequence_to_item(self, item, date_data):
        """Apply date sequence to an item"""
        return self.date_applier.apply_date_sequence_to_item(item, date_data)

    # Configuration methods
    def _configure_custom_patterns(self, item):
        """Configure custom patterns for an item"""
        dialog = CustomPatternsDialog(self.tree_widget, item)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pattern_data = dialog.get_pattern_data()
            if pattern_data:
                self._apply_pattern_to_item(item, pattern_data)
                self.item_operations.update_item_display(item)

    def _configure_versioning(self, item):
        """Configure versioning for an item"""
        dialog = VersioningDialog(self.tree_widget, item)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            versioning_data = dialog.get_versioning_data()
            if versioning_data:
                self._apply_versioning_to_item(item, versioning_data)
                self.item_operations.update_item_display(item)

    def _configure_date_sequences(self, item):
        """Configure date sequences for an item"""
        dialog = DateSequenceDialog(self.tree_widget, item)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            date_data = dialog.get_date_data()
            if date_data:
                self._apply_date_sequence_to_item(item, date_data)
                self.item_operations.update_item_display(item)

    # Utility methods
    def is_binary_file(self, file_path):
        """Check if a file is binary"""
        return self.binary_handler.is_binary_file(file_path)

    # Legacy compatibility methods - delegate to appropriate modules
    def _set_project_name_mode(self, item, mode):
        """Set project name mode for an item"""
        return self.item_operations.set_project_name_mode(item, mode)

    def _update_item_display(self, item):
        """Update item display"""
        return self.item_operations.update_item_display(item)

    def _copy_folder_children(self, source_folder, target_folder):
        """Copy folder children"""
        return self.pattern_applier.copy_folder_children(source_folder, target_folder)


class CustomPatternsDialog(QDialog):
    """Custom patterns configuration dialog"""
    
    def __init__(self, parent, item):
        super().__init__(parent)
        self.item = item
        self.parent_widget = parent
        
        # Initialize component modules
        self.ui_components = PatternUIComponents(self)
        self.custom_options_manager = CustomOptionsManager(self)
        self.format_managers = FormatManagers(self)
        self.pattern_logic = PatternLogic(self)
        self.pattern_data_handler = PatternDataHandler(self)
        
        # UI elements will be set by init_ui
        self.pattern_edit = None
        self.separator_combo = None
        self.custom_separator_edit = None
        self.date_combo = None
        self.time_combo = None
        self.custom_editors_layout = None
        
        self.init_ui()
        self._load_existing_pattern_data()

    def _is_folder_item(self, item):
        """Check if item is a folder"""
        if not item:
            return False
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return item_data.get('is_folder', False)

    def init_ui(self):
        """Initialize the user interface"""
        self.ui_components.init_ui()

    def insert_tag(self, tag):
        """Insert a tag at cursor position"""
        self.pattern_logic.insert_tag(tag, self.pattern_edit)
        self.update_preview()

    def update_preview(self):
        """Update the preview display"""
        if not self.pattern_edit:
            return
        
        pattern = self.pattern_edit.text()
        is_folder = self._is_folder_item(self.item)
        
        preview = self.pattern_logic.generate_sample_preview(
            pattern, self.custom_options_manager, self.format_managers,
            self.date_combo, self.time_combo, is_folder
        )
        
        # Update preview in UI
        self.ui_components.update_preview_display(preview)

    def validate_pattern(self):
        """Validate the current pattern"""
        pattern = self.pattern_edit.text() if self.pattern_edit else ""
        errors = self.pattern_logic.validate_pattern(
            pattern, self.custom_options_manager, self.format_managers,
            self.date_combo, self.time_combo
        )
        
        if errors:
            self.pattern_logic.show_validation_errors(errors)
            return False
        
        return True

    def on_apply(self):
        """Handle apply button click"""
        if self.validate_pattern():
            self.accept()

    def get_pattern_data(self):
        """Get all pattern data from the dialog"""
        return self.pattern_data_handler.get_pattern_data(
            self.pattern_edit, self.custom_options_manager, self.format_managers,
            self.separator_combo, self.custom_separator_edit, 
            self.date_combo, self.time_combo
        )

    def _load_existing_pattern_data(self):
        """Load existing pattern data from item"""
        self.pattern_data_handler.load_existing_pattern_data(
            self.item, self.pattern_edit, self.custom_options_manager,
            self.format_managers, self.separator_combo, self.custom_separator_edit,
            self.date_combo, self.time_combo, self.custom_editors_layout
        )
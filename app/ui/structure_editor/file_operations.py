#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
File Operations Module for Structure Editor
Main coordinator for file and folder operations, context menus, and versioning
"""

import os
from PyQt6.QtWidgets import QTreeWidgetItem, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime

# Import all the refactored modules
from .utils.file_type_detector import FileTypeDetector
from .utils.tree_item_helpers import TreeItemHelpers
from .handlers.binary_file_handler import BinaryFileHandler
from .operations.file_operations import BasicFileOperations
from .operations.import_operations import ImportOperations
from .operations.context_menu import ContextMenuOperations
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
        self.context_menu_operations = ContextMenuOperations(tree_widget, editor)
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
        print(f"DEBUG: FileOperations.set_tree_widget called with: {tree_widget}")
        
        # Update tree widget reference in all component modules that need it
        if hasattr(self.context_menu_operations, 'set_tree_widget'):
            self.context_menu_operations.set_tree_widget(tree_widget)
            print(f"DEBUG: Updated context_menu_operations tree widget to: {tree_widget}")
        if hasattr(self.basic_operations, 'set_tree_widget'):
            self.basic_operations.set_tree_widget(tree_widget)
        if hasattr(self.import_operations, 'set_tree_widget'):
            self.import_operations.set_tree_widget(tree_widget)
        if hasattr(self.item_operations, 'set_tree_widget'):
            self.item_operations.set_tree_widget(tree_widget)
        if hasattr(self.tree_operations, 'set_tree_widget'):
            self.tree_operations.set_tree_widget(tree_widget)
        if hasattr(self.pattern_applier, 'set_tree_widget'):
            self.pattern_applier.set_tree_widget(tree_widget)
        if hasattr(self.versioning_applier, 'set_tree_widget'):
            self.versioning_applier.set_tree_widget(tree_widget)
        if hasattr(self.date_applier, 'set_tree_widget'):
            self.date_applier.set_tree_widget(tree_widget)
        
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
        """Check if the item is a folder"""
        if not item:
            return False
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(item_data, dict):
            return item_data.get('type') == 'folder'
        return False

    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Custom Naming Patterns")
        self.setModal(True)
        self.resize(600, 500)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Determine if this is a folder
        is_folder = self._is_folder_item(self.item)
        
        # Create UI sections using the component methods
        self.ui_components.create_title_section(main_layout, is_folder)
        
        # Variables section
        self.tags, self.tag_buttons = self.ui_components.create_variables_section(main_layout, is_folder)
        
        # Connect tag buttons to insert text
        for tag_button in self.tag_buttons:
            tag_button.clicked.connect(lambda checked, tag=tag_button.text(): self._insert_tag(tag))
        
        # Separator section
        self.separator_combo, self.custom_separator_edit = self.ui_components.create_separator_section(main_layout)
        
        # Connect separator combo change
        self.separator_combo.currentTextChanged.connect(self._on_separator_changed)
        self.custom_separator_edit.textChanged.connect(self._update_preview)
        
        # Pattern input section
        self.pattern_edit = self.ui_components.create_pattern_input_section(main_layout, is_folder)
        self.pattern_edit.textChanged.connect(self._update_preview)
        
        # Custom options section
        self.custom_options_group = self.ui_components.create_group_box("Custom Options", visible=False)
        custom_options_layout = QVBoxLayout(self.custom_options_group)
        
        # Custom option inputs
        self.custom_inputs = []
        for i in range(3):
            custom_input = QLineEdit()
            custom_input.setPlaceholderText(f"Custom option {i+1}")
            custom_input.textChanged.connect(self._update_preview)
            custom_options_layout.addWidget(custom_input)
            self.custom_inputs.append(custom_input)
        
        main_layout.addWidget(self.custom_options_group)
        
        # Preview section
        preview_label = QLabel("Preview:")
        preview_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        main_layout.addWidget(preview_label)
        
        self.preview_label = QLabel("Enter a pattern to see preview...")
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        main_layout.addWidget(self.preview_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        self.apply_button = QPushButton("Apply Pattern")
        self.apply_button.clicked.connect(self.accept)
        self.apply_button.setEnabled(False)
        button_layout.addWidget(self.apply_button)
        
        main_layout.addLayout(button_layout)
        
        # Load existing pattern data if available
        self._load_existing_pattern_data()

    def _insert_tag(self, tag):
        """Insert a tag into the pattern input"""
        if hasattr(self, 'pattern_edit'):
            cursor_pos = self.pattern_edit.cursorPosition()
            current_text = self.pattern_edit.text()
            new_text = current_text[:cursor_pos] + tag + current_text[cursor_pos:]
            self.pattern_edit.setText(new_text)
            self.pattern_edit.setCursorPosition(cursor_pos + len(tag))
            self._update_preview()
            
    def _on_separator_changed(self, text):
        """Handle separator combo box changes"""
        if text == "Custom...":
            self.custom_separator_edit.setVisible(True)
            self.custom_separator_edit.setFocus()
        else:
            self.custom_separator_edit.setVisible(False)
        self._update_preview()
        
    def _update_preview(self):
        """Update the preview display"""
        if not hasattr(self, 'pattern_edit'):
            return
            
        pattern = self.pattern_edit.text().strip()
        if not pattern:
            self.preview_label.setText("Enter a pattern to see preview...")
            self.apply_button.setEnabled(False)
            return
            
        # Show/hide custom options based on pattern content
        has_custom = any(tag in pattern for tag in ['${CUSTOM}', '${CUSTOM1}', '${CUSTOM2}', '${CUSTOM3}'])
        self.custom_options_group.setVisible(has_custom)
        
        # Generate preview using a simple approach since we don't have all the managers
        try:
            preview = self._generate_simple_preview(pattern)
            self.preview_label.setText(f"Preview: {preview}")
            self.apply_button.setEnabled(True)
        except Exception as e:
            self.preview_label.setText(f"Error: {str(e)}")
            self.apply_button.setEnabled(False)
            
    def _generate_simple_preview(self, pattern):
        """Generate a simple preview of the pattern"""
        if not pattern:
            return "Enter a pattern to see preview"
        
        # Get sample values for different placeholders
        sample_values = {
            '${PROJECT_NAME}': 'MyProject',
            '${BASE}': 'filename',
            '${DATE}': datetime.now().strftime('%Y%m%d'),
            '${TIME}': datetime.now().strftime('%H%M%S'),
            '${COUNTER}': '001',
            '${CUSTOM}': 'Option1',
            '${CUSTOM1}': 'Option1',
            '${CUSTOM2}': 'Option2',
            '${CUSTOM3}': 'Option3'
        }
        
        # Replace placeholders in pattern
        preview = pattern
        for placeholder, value in sample_values.items():
            preview = preview.replace(placeholder, value)
        
        # Add extension for files if not a folder
        is_folder = self._is_folder_item(self.item)
        if not is_folder and not any(preview.endswith(ext) for ext in ['.txt', '.mp4', '.jpg', '.png', '.pdf', '.prproj']):
            # Try to preserve original extension if available
            item_data = self.item.data(0, Qt.ItemDataRole.UserRole) if self.item else {}
            if isinstance(item_data, dict) and 'name' in item_data:
                original_name = item_data['name']
                if '.' in original_name:
                    ext = '.' + original_name.split('.')[-1]
                    preview += ext
                else:
                    preview += '.txt'
            else:
                preview += '.txt'
        
        return preview
        
    def _get_current_separator(self):
        """Get the currently selected separator"""
        if not hasattr(self, 'separator_combo'):
            return "_"
            
        separator_text = self.separator_combo.currentText()
        if separator_text == "Custom...":
            return self.custom_separator_edit.text() or "_"
        elif separator_text == "_ (underscore)":
            return "_"
        elif separator_text == "- (dash)":
            return "-"
        elif separator_text == ". (dot)":
            return "."
        elif separator_text == "  (space)":
            return " "
        else:
            return "_"
            
    def _load_existing_pattern_data(self):
        """Load existing pattern data if available"""
        # This method can be implemented later if needed
        pass
        
    def validate_pattern(self):
        """Validate the current pattern"""
        if not hasattr(self, 'pattern_edit'):
            return False
        pattern = self.pattern_edit.text().strip()
        if not pattern:
            return False
        return True
        
    def get_pattern_data(self):
        """Get all pattern data from the dialog"""
        if not hasattr(self, 'pattern_edit'):
            return {}
            
        return {
            'pattern': self.pattern_edit.text().strip(),
            'separator': self._get_current_separator(),
            'custom_options': [input_field.text().strip() for input_field in self.custom_inputs if hasattr(self, 'custom_inputs')]
        }
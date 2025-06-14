#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
File Operations Module for Structure Editor
Main coordinator for file and folder operations, context menus, and versioning
"""

import os
from PyQt6.QtWidgets import QTreeWidgetItem, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QWidget, QTextEdit, QScrollArea
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
    
    def _revert_to_original_name(self, item):
        """Revert an item to its original name - delegates to item_operations"""
        return self.item_operations.reset_item_to_original(item)
    
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
        
        # Initialize separator controller for centralized separator management
        from .dialogs.custom_patterns.separator_controller import SeparatorController
        self.separator_controller = SeparatorController(self)
        
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
        self.resize(650, 600)
        
        # Apply consistent dialog styling
        self._apply_dialog_styling()
        
        # Main layout with minimal spacing
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title section (fixed at top)
        is_folder = self._is_folder_item(self.item)
        self.ui_components.create_title_section(main_layout, is_folder)
        
        # Create scroll area for the main content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {self.ui_components.colors['bg']};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.ui_components.colors['border']};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.ui_components.colors['accent']};
            }}
        """)
        
        # Scrollable content widget
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)  # Tight spacing between sections
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        # Variables section with tighter spacing
        self.tags, self.tag_buttons = self.ui_components.create_variables_section(scroll_layout, is_folder)
        for tag_button in self.tag_buttons:
            tag_button.clicked.connect(lambda checked, tag=tag_button.text(): self._insert_tag(tag))
        
        # Separator section - tighter to variables
        self.separator_combo, self.custom_separator_edit = self.ui_components.create_separator_section(scroll_layout)
        self.separator_combo.currentTextChanged.connect(self._on_separator_changed)
        self.custom_separator_edit.textChanged.connect(self._on_custom_separator_changed)
        
        # Pattern input section - tighter to separator
        self.pattern_edit = self.ui_components.create_pattern_input_section(scroll_layout, is_folder)
        self.pattern_edit.textChanged.connect(self._update_preview)
        
        # Custom options section - will be populated dynamically, tight spacing
        self.custom_options_group = self.ui_components.create_group_box("Custom Dropdown Options", visible=False)
        self.custom_options_layout = QVBoxLayout(self.custom_options_group)
        self.custom_options_layout.setSpacing(6)
        
        # Help text for custom options with tighter margins
        help_text = QLabel("Enter one option per line for each custom placeholder:")
        help_text.setStyleSheet(f"""
            color: {self.ui_components.colors['secondary_text']};
            background-color: transparent;
            border: none;
            padding: 2px 0px;
            margin: 0px;
        """)
        self.custom_options_layout.addWidget(help_text)
        
        # Dictionary to store custom option text areas
        self.custom_text_areas = {}
        
        scroll_layout.addWidget(self.custom_options_group)
        
        # Date and time format sections - will be shown dynamically, tight spacing
        self.date_format_group, self.date_combo = self.format_managers.create_date_format_group(scroll_layout)
        self.time_format_group, self.time_combo = self.format_managers.create_time_format_group(scroll_layout)
        
        # Connect format combo changes to preview update
        self.date_combo.currentTextChanged.connect(self._update_preview)
        self.time_combo.currentTextChanged.connect(self._update_preview)
        
        # Add flexible space at bottom for dynamic content expansion
        scroll_layout.addStretch(1)
        
        # Set scroll content
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)  # Give scroll area the main space
        
        # Fixed bottom section - Preview and buttons (non-scrollable)
        # Add separator line
        separator_line = QWidget()
        separator_line.setFixedHeight(1)
        separator_line.setStyleSheet(f"background-color: {self.ui_components.colors['border']};")
        main_layout.addWidget(separator_line)
        
        # Preview section (fixed at bottom)
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setSpacing(8)
        bottom_layout.setContentsMargins(0, 12, 0, 0)
        
        preview_label = QLabel("Preview:")
        preview_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self._apply_label_styling(preview_label)
        bottom_layout.addWidget(preview_label)
        
        self.preview_label = QLabel("Enter a pattern to see preview...")
        self._apply_preview_styling(self.preview_label)
        bottom_layout.addWidget(self.preview_label)
        
        # Buttons with proper spacing
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setMinimumSize(100, 32)
        self._apply_button_styling(cancel_button, is_accent=False)
        button_layout.addWidget(cancel_button)
        
        self.apply_button = QPushButton("Apply Pattern")
        self.apply_button.clicked.connect(self.accept)
        self.apply_button.setEnabled(False)
        self.apply_button.setMinimumSize(120, 32)
        self._apply_button_styling(self.apply_button, is_accent=True)
        button_layout.addWidget(self.apply_button)
        
        bottom_layout.addLayout(button_layout)
        main_layout.addWidget(bottom_widget)
        
        # Initialize separator controller after UI is created
        if hasattr(self, 'separator_controller'):
            self.separator_controller.initialize_from_ui(self.separator_combo, self.custom_separator_edit)

    def _insert_tag(self, tag):
        """Insert a tag into the pattern input using PatternLogic for automatic separator handling"""
        if hasattr(self, 'pattern_edit') and hasattr(self, 'pattern_logic'):
            self.pattern_logic.insert_tag(tag, self.pattern_edit, self.separator_combo, self.custom_separator_edit)
            self._update_preview()
            
    def _on_separator_changed(self, text):
        """Handle separator combo box changes and act as master switch"""
        if text == "Custom...":
            self.custom_separator_edit.setVisible(True)
            self.custom_separator_edit.setFocus()
        else:
            self.custom_separator_edit.setVisible(False)
        
        # Use the separator controller to handle the change
        if hasattr(self, 'separator_controller'):
            # Initialize from UI first if not already done
            if not hasattr(self, '_separator_initialized'):
                self.separator_controller.initialize_from_ui(self.separator_combo, self.custom_separator_edit)
                self._separator_initialized = True
            
            # Get the new separator
            separator_text = self.separator_combo.currentText()
            if separator_text == "_ (underscore)":
                new_separator = "_"
            elif separator_text == "- (dash)":
                new_separator = "-"
            elif separator_text == ". (dot)":
                new_separator = "."
            elif separator_text == "  (space)":
                new_separator = " "
            elif separator_text == "Custom...":
                new_separator = self.custom_separator_edit.text() or "_"
            else:
                new_separator = "_"
            
            # Set the master separator (this will update all dependent components)
            self.separator_controller.set_master_separator(new_separator)
        else:
            # Fallback to old behavior if controller not available
            new_separator = self.pattern_logic.get_current_separator(self.separator_combo, self.custom_separator_edit) if hasattr(self, 'pattern_logic') else self._get_current_separator()
            
            # Update existing pattern separators
            if hasattr(self, 'pattern_edit') and hasattr(self, 'pattern_logic'):
                current_pattern = self.pattern_edit.text()
                if current_pattern.strip():
                    updated_pattern = self.pattern_logic.update_pattern_separators(current_pattern, new_separator)
                    self.pattern_edit.setText(updated_pattern)
            
            # Update preview
            self._update_preview()

    def _on_custom_separator_changed(self):
        """Handle custom separator input changes and act as master switch"""
        # Use the separator controller to handle the change
        if hasattr(self, 'separator_controller'):
            custom_text = self.custom_separator_edit.text() or "_"
            self.separator_controller.set_master_separator(custom_text)
        else:
            # Fallback to old behavior if controller not available
            new_separator = self.pattern_logic.get_current_separator(self.separator_combo, self.custom_separator_edit) if hasattr(self, 'pattern_logic') else self._get_current_separator()
            
            # Update existing pattern separators
            if hasattr(self, 'pattern_edit') and hasattr(self, 'pattern_logic'):
                current_pattern = self.pattern_edit.text()
                if current_pattern.strip():
                    updated_pattern = self.pattern_logic.update_pattern_separators(current_pattern, new_separator)
                    self.pattern_edit.setText(updated_pattern)
            
            # Update preview
            self._update_preview()
        
    def _update_preview(self):
        """Update the preview display"""
        if not hasattr(self, 'pattern_edit'):
            return
            
        pattern = self.pattern_edit.text().strip()
        if not pattern:
            self.preview_label.setText("Enter a pattern to see preview...")
            self.apply_button.setEnabled(False)
            self._clear_custom_options()
            return
            
        # Update custom options based on pattern content
        self._update_custom_options_for_pattern(pattern)
        
        # Update format groups based on pattern content
        self._update_format_groups_for_pattern(pattern)
        
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
        
        # Import datetime if needed
        from datetime import datetime
        
        # Get custom options data
        custom_options = self._get_custom_options_data()
        
        # Get sample values for different placeholders
        sample_values = {
            '${PROJECT_NAME}': 'MyProject',
            '${BASE}': 'filename',
            '${COUNTER}': '001'
        }
        
        # Add formatted date/time values using format managers
        if hasattr(self, 'format_managers') and hasattr(self, 'date_combo') and hasattr(self, 'time_combo'):
            format_values = self.format_managers.get_sample_format_values(self.date_combo, self.time_combo)
            sample_values.update(format_values)
        else:
            # Fallback to basic formatting
            sample_values['${DATE}'] = datetime.now().strftime('%Y%m%d')
            sample_values['${TIME}'] = datetime.now().strftime('%H%M%S')
        
        # Add custom options with first option from each list
        for placeholder, options in custom_options.items():
            if options:  # If there are options available
                sample_values[placeholder] = options[0]  # Use first option
            else:
                sample_values[placeholder] = f'[No options for {placeholder}]'
        
        # Add default values for custom placeholders that don't have options yet
        custom_placeholders = self._get_custom_placeholders_from_pattern(pattern)
        for placeholder in custom_placeholders:
            if placeholder not in sample_values:
                sample_values[placeholder] = f'[Enter options for {placeholder}]'
        
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
        if not self.item:
            print("DEBUG: No item provided to load pattern data")
            return
        
        try:
            # Get item data
            item_data = self.item.data(0, Qt.ItemDataRole.UserRole)
            if not isinstance(item_data, dict):
                print(f"DEBUG: Item data is not a dict: {type(item_data)}")
                return
            
            print(f"DEBUG: Loading pattern data from item_data keys: {list(item_data.keys())}")
            
            # Look for pattern in multiple possible locations
            pattern = None
            custom_options = None
            separator = "_"
            date_format = None
            time_format = None
            
            # Check direct item_data level
            if 'pattern' in item_data:
                pattern = item_data['pattern']
                custom_options = item_data.get('custom_options')
                separator = item_data.get('separator', '_')
                date_format_text = item_data.get('date_format_text')
                time_format_text = item_data.get('time_format_text')
                print(f"DEBUG: Found pattern at top level: {pattern}")
                print(f"DEBUG: Found custom_options at top level: {custom_options}")
                print(f"DEBUG: Found date_format_text at top level: {date_format_text}")
                print(f"DEBUG: Found time_format_text at top level: {time_format_text}")
            
            # Check user_data level  
            elif 'user_data' in item_data and isinstance(item_data['user_data'], dict):
                user_data = item_data['user_data']
                if 'pattern' in user_data:
                    pattern = user_data['pattern']
                    custom_options = user_data.get('custom_options')
                    separator = user_data.get('separator', '_')
                    date_format_text = user_data.get('date_format_text')
                    time_format_text = user_data.get('time_format_text')
                    print(f"DEBUG: Found pattern in user_data: {pattern}")
                    print(f"DEBUG: Found custom_options in user_data: {custom_options}")
                    print(f"DEBUG: Found date_format_text in user_data: {date_format_text}")
                    print(f"DEBUG: Found time_format_text in user_data: {time_format_text}")
                    
                # Check if user_data has nested user_data
                elif 'user_data' in user_data and isinstance(user_data['user_data'], dict):
                    nested_user_data = user_data['user_data']
                    if 'pattern' in nested_user_data:
                        pattern = nested_user_data['pattern']
                        custom_options = nested_user_data.get('custom_options')
                        separator = nested_user_data.get('separator', '_')
                        date_format_text = nested_user_data.get('date_format_text')
                        time_format_text = nested_user_data.get('time_format_text')
                        print(f"DEBUG: Found pattern in nested user_data: {pattern}")
                        print(f"DEBUG: Found custom_options in nested user_data: {custom_options}")
                        print(f"DEBUG: Found date_format_text in nested user_data: {date_format_text}")
                        print(f"DEBUG: Found time_format_text in nested user_data: {time_format_text}")
            
            # If pattern found, load it
            if pattern:
                print(f"DEBUG: Loading pattern: {pattern}")
                self.pattern_edit.setText(pattern)
                
                # Update custom options for this pattern
                self._update_custom_options_for_pattern(pattern)
                
                # Load custom options data if available
                if custom_options:
                    print(f"DEBUG: Loading custom options: {custom_options}")
                    self._load_custom_options_into_text_areas(custom_options)
                
                # Load separator settings
                if separator:
                    print(f"DEBUG: Loading separator: {separator}")
                    separator_data = {'separator': separator}
                    self._load_separator_settings(separator_data)
                
                # Load date/time format settings
                if date_format_text or time_format_text:
                    print(f"DEBUG: Loading format settings - date: {date_format_text}, time: {time_format_text}")
                    format_data = {}
                    if date_format_text:
                        format_data['date_format_text'] = date_format_text
                    if time_format_text:
                        format_data['time_format_text'] = time_format_text
                    self.format_managers.load_format_settings(format_data, self.date_combo, self.time_combo)
                
                # Update preview after loading
                self._update_preview()
            else:
                print("DEBUG: No pattern found in item data")
            
        except Exception as e:
            print(f"ERROR: Error loading existing pattern data: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_custom_options_into_text_areas(self, custom_options):
        """Load custom options data into the text areas"""
        if not isinstance(custom_options, dict):
            return
        
        for placeholder, options in custom_options.items():
            if placeholder in self.custom_text_areas:
                text_area = self.custom_text_areas[placeholder]['text_area']
                if isinstance(options, list):
                    # Convert list to newline-separated text
                    text_content = '\n'.join(options)
                    text_area.setPlainText(text_content)
                elif isinstance(options, str):
                    text_area.setPlainText(options)
    
    def _load_separator_settings(self, item_data):
        """Load separator settings from item data"""
        separator = item_data.get('separator', '_')
        
        # Map separator to dropdown text
        separator_map = {
            '_': "_ (underscore)",
            '-': "- (dash)",
            '.': ". (dot)",
            ' ': "  (space)"
        }
        
        separator_text = separator_map.get(separator, "Custom...")
        
        # Find and set the separator in combo
        for i in range(self.separator_combo.count()):
            if self.separator_combo.itemText(i) == separator_text:
                self.separator_combo.setCurrentIndex(i)
                break
        else:
            # If not found, set to custom and show custom input
            for i in range(self.separator_combo.count()):
                if self.separator_combo.itemText(i) == "Custom...":
                    self.separator_combo.setCurrentIndex(i)
                    self.custom_separator_edit.setText(separator)
                    self.custom_separator_edit.setVisible(True)
                    break
        
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
        
        pattern_data = {
            'pattern': self.pattern_edit.text().strip(),
            'separator': self._get_current_separator(),
            'custom_options': self._get_custom_options_data()
        }
        
        # Add date and time format settings if available
        if hasattr(self, 'format_managers') and hasattr(self, 'date_combo') and hasattr(self, 'time_combo'):
            format_settings = self.format_managers.get_format_settings(self.date_combo, self.time_combo)
            pattern_data.update(format_settings)
        
        return pattern_data
    
    def _apply_dialog_styling(self):
        """Apply consistent dialog styling"""
        from app.ui.color_scheme_pyqt import colors
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg']};
                color: {colors['text']};
            }}
        """)
    
    def _apply_label_styling(self, label):
        """Apply consistent label styling"""
        from app.ui.color_scheme_pyqt import colors
        
        label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                background-color: transparent;
                border: none;
                padding: 0px;
            }}
        """)
    
    def _apply_lineedit_styling(self, lineedit):
        """Apply consistent line edit styling"""
        from app.ui.color_scheme_pyqt import colors
        
        lineedit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                min-height: 20px;
            }}
            QLineEdit:focus {{
                border: 2px solid {colors['accent']};
                background-color: {colors['highlight_bg_transparent']};
            }}
            QLineEdit:disabled {{
                background-color: {colors['bg']};
                color: {colors['secondary_text']};
                border: 2px solid {colors['border']};
            }}
        """)
    
    def _apply_preview_styling(self, preview_label):
        """Apply consistent preview label styling"""
        from app.ui.color_scheme_pyqt import colors
        
        preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 6px;
                padding: 12px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                min-height: 40px;
            }}
        """)
    
    def _apply_button_styling(self, button, is_accent=False):
        """Apply consistent button styling"""
        from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE
        
        if is_accent:
            button.setStyleSheet(ACCENT_BUTTON_STYLE)
        else:
            button.setStyleSheet(BUTTON_STYLE)
    
    def _get_custom_placeholders_from_pattern(self, pattern):
        """Extract CUSTOM placeholders from the pattern"""
        import re
        if not pattern:
            return []
        
        # Find all CUSTOM placeholders: ${CUSTOM}, ${CUSTOM1}, ${CUSTOM2}, ${CUSTOM3}
        matches = re.findall(r'\$\{(CUSTOM\d*)\}', pattern)
        unique_placeholders = []
        for match in matches:
            placeholder = f"${{{match}}}"
            if placeholder not in unique_placeholders:
                unique_placeholders.append(placeholder)
        
        return sorted(unique_placeholders)
    
    def _update_custom_options_for_pattern(self, pattern):
        """Update custom options text areas based on pattern placeholders"""
        placeholders = self._get_custom_placeholders_from_pattern(pattern)
        
        if not placeholders:
            self.custom_options_group.setVisible(False)
            self._clear_custom_options()
            return
        
        # Show the custom options group
        self.custom_options_group.setVisible(True)
        
        # Remove text areas for placeholders no longer in use
        for placeholder in list(self.custom_text_areas.keys()):
            if placeholder not in placeholders:
                self._remove_custom_text_area(placeholder)
        
        # Add text areas for new placeholders
        for placeholder in placeholders:
            if placeholder not in self.custom_text_areas:
                self._add_custom_text_area(placeholder)
    
    def _add_custom_text_area(self, placeholder):
        """Add a text area for a specific custom placeholder"""
        from PyQt6.QtWidgets import QTextEdit
        from app.ui.color_scheme_pyqt import colors
        
        # Create container for this placeholder
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 10, 0, 0)
        container_layout.setSpacing(5)
        
        # Add label for this placeholder
        label = QLabel(f"Options for {placeholder}:")
        label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                background-color: transparent;
                border: none;
                font-weight: bold;
                padding: 0px;
            }}
        """)
        container_layout.addWidget(label)
        
        # Create text area
        text_area = QTextEdit()
        text_area.setPlaceholderText(f"Enter options for {placeholder}, one per line:\nOption 1\nOption 2\nOption 3")
        text_area.setMaximumHeight(120)  # Limit height to keep dialog manageable
        text_area.setMinimumHeight(80)   # Ensure minimum usable height
        
        # Apply consistent styling
        text_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                font-family: 'Arial', sans-serif;
            }}
            QTextEdit:focus {{
                border: 2px solid {colors['accent']};
                background-color: {colors['highlight_bg_transparent']};
            }}
        """)
        
        # Connect to update preview
        text_area.textChanged.connect(self._update_preview)
        
        container_layout.addWidget(text_area)
        
        # Store references
        self.custom_text_areas[placeholder] = {
            'container': container,
            'text_area': text_area,
            'label': label
        }
        
        # Add to layout
        self.custom_options_layout.addWidget(container)
    
    def _remove_custom_text_area(self, placeholder):
        """Remove text area for a specific placeholder"""
        if placeholder in self.custom_text_areas:
            container = self.custom_text_areas[placeholder]['container']
            self.custom_options_layout.removeWidget(container)
            container.deleteLater()
            del self.custom_text_areas[placeholder]
    
    def _clear_custom_options(self):
        """Clear all custom option text areas"""
        for placeholder in list(self.custom_text_areas.keys()):
            self._remove_custom_text_area(placeholder)
    
    def _get_custom_options_data(self):
        """Get custom options data from all text areas"""
        custom_options = {}
        
        for placeholder, widgets in self.custom_text_areas.items():
            text_area = widgets['text_area']
            text_content = text_area.toPlainText().strip()
            
            if text_content:
                # Split by lines and filter out empty lines
                options = [line.strip() for line in text_content.split('\n') if line.strip()]
                if options:
                    custom_options[placeholder] = options
        
        return custom_options
    
    def _update_format_groups_for_pattern(self, pattern):
        """Update format groups visibility based on pattern content"""
        if not pattern:
            self.date_format_group.setVisible(False)
            self.time_format_group.setVisible(False)
            return
        
        # Show/hide date format group based on ${DATE} presence
        has_date = self.format_managers.has_date_placeholder(pattern)
        self.date_format_group.setVisible(has_date)
        
        # Show/hide time format group based on ${TIME} presence
        has_time = self.format_managers.has_time_placeholder(pattern)
        self.time_format_group.setVisible(has_time)
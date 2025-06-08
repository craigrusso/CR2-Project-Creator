#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
File Operations Module for Structure Editor
Handles file and folder operations, context menus, and versioning
"""

import os
import json
import datetime
from datetime import timedelta
from PyQt6.QtWidgets import (
    QMenu, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, 
    QLineEdit, QSpinBox, QComboBox, QTextEdit, QDateEdit, QCheckBox,
    QTabWidget, QWidget, QFormLayout, QListWidget, QMessageBox,
    QTreeWidgetItem, QApplication
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont

# Import binary file handler
from app.utils.binary_file_handler import BinaryFileHandler

# Constants for file types
FILE_TYPES = {
    'video': ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.prproj'],
    'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.aiff'],
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg'],
    'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
    'spreadsheet': ['.xls', '.xlsx', '.csv', '.ods'],
    'presentation': ['.ppt', '.pptx', '.odp'],
    'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'script': ['.py', '.js', '.html', '.css', '.xml', '.json'],
    'other': []
}

class BinaryFileHandler:
    """Utility class for handling binary files"""
    
    @staticmethod
    def is_binary_file(file_path):
        # Very basic check
        try:
            with open(file_path, 'tr') as check_file:
                check_file.read(1024)
                return False
        except:
            return True
    
    @staticmethod
    def should_embed_binary_file(file_path, max_size_kb=500):
        """Check if a binary file should be embedded based on size"""
        try:
            size_kb = os.path.getsize(file_path) / 1024
            return size_kb <= max_size_kb
        except:
            return False

    @staticmethod
    def get_file_type_from_extension(file_path):
        """Determine file type from extension"""
        ext = os.path.splitext(file_path.lower())[1]
        
        for file_type, extensions in FILE_TYPES.items():
            if ext in extensions:
                return file_type
        return 'other'

    @staticmethod
    def get_file_icon(file_type):
        """Get appropriate icon for file type"""
        icon_map = {
            'video': '🎬',
            'audio': '🎵',
            'image': '🖼️',
            'document': '📄',
            'spreadsheet': '📊',
            'presentation': '📽️',
            'archive': '📦',
            'script': '💻',
            'folder': '',
            'other': '📄'
        }
        return icon_map.get(file_type, '📄')


class FileOperations:
    """Handles file and folder operations in the structure editor"""
    
    def __init__(self, tree_widget=None, editor=None):
        """Initialize file operations handler"""
        self.tree_widget = tree_widget
        self.editor = editor
        self.binary_handler = BinaryFileHandler()
        self.current_context_item = None
        
        # Connect context menu if tree widget is available
        if self.tree_widget:
            self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.tree_widget.customContextMenuRequested.connect(self.create_context_menu)
            print("DEBUG: Connected context menu to tree widget")
        else:
            print("DEBUG: No tree widget provided to FileOperations")
        
        print("DEBUG: Initialized file operations handler")

    def set_tree_widget(self, tree_widget):
        """Set or update the tree widget reference"""
        self.tree_widget = tree_widget
        if self.tree_widget:
            self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.tree_widget.customContextMenuRequested.connect(self.create_context_menu)
            print("DEBUG: Updated tree widget reference and connected context menu")
        else:
            print("DEBUG: Tree widget set to None")

    def add_file(self, parent_item=None, file_name=None, file_type=None):
        """Add a new file to the structure"""
        if not self.tree_widget:
            print("ERROR: No tree widget available")
            return None

        # Get categories from the editor
        categories = []
        if self.editor and hasattr(self.editor, 'template_manager'):
            try:
                categories = list(FILE_TYPES.keys())
                categories.remove('other')  # Remove 'other' from selectable categories
            except:
                categories = ['video', 'audio', 'image', 'document']

        # Show file details dialog
        dialog = FileDetailsDialog(
            self.tree_widget,
            "Add New File",
            "Enter details for the new file:",
            file_name or "",
            categories,
            file_type or ""
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            file_name = dialog.get_file_name()
            file_type = dialog.get_file_type()
            is_binary = dialog.is_binary()
            
            if file_name:
                # Create the file item
                file_item = self._add_file_item(parent_item, file_name, file_type)
                
                # Set binary flag if needed
                if is_binary:
                    data = file_item.data(0, Qt.ItemDataRole.UserRole) or {}
                    data['is_binary'] = True
                    file_item.setData(0, Qt.ItemDataRole.UserRole, data)
                
                return file_item
        
        return None

    def _add_file_item(self, parent_item, file_name, file_type=None, original_path=None):
        """Internal method to add a file item to the tree"""
        if not self.tree_widget:
            return None

        # Create the tree item
        if parent_item:
            file_item = QTreeWidgetItem(parent_item)
        else:
            file_item = QTreeWidgetItem(self.tree_widget)

        file_item.setText(0, file_name)
        
        # Set item data
        item_data = {
            'name': file_name,
            'type': 'file',
            'file_type': file_type or self.binary_handler.get_file_type_from_extension(file_name)
        }
        
        if original_path:
            item_data['original_path'] = original_path
            item_data['is_binary'] = self.binary_handler.is_binary_file(original_path)
        
        file_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Set display text without emoji icons
        file_item.setText(0, file_name)
        
        # Expand parent if needed
        if parent_item:
            parent_item.setExpanded(True)
        
        print(f"DEBUG: Added file '{file_name}' to tree")
        return file_item

    def add_folder(self, parent_item=None, folder_name=None):
        """Add a new folder to the structure"""
        if not self.tree_widget:
            print("ERROR: No tree widget available")
            return None

        # Get folder name from user if not provided
        if not folder_name:
            text, ok = QInputDialog.getText(
                self.tree_widget, 
                'Add Folder', 
                'Enter folder name:'
            )
            if ok and text.strip():
                folder_name = text.strip()
            else:
                return None

        # Create the tree item
        if parent_item:
            folder_item = QTreeWidgetItem(parent_item)
        else:
            folder_item = QTreeWidgetItem(self.tree_widget)

        folder_item.setText(0, folder_name)
        
        # Set item data
        item_data = {
            'name': folder_name,
            'type': 'folder'
        }
        folder_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Expand parent if needed
        if parent_item:
            parent_item.setExpanded(True)
        
        # Expand the new folder
        folder_item.setExpanded(True)
        
        print(f"DEBUG: Added folder '{folder_name}' to tree")
        return folder_item

    def delete_selected(self):
        """Delete the selected items"""
        if not self.tree_widget:
            return

        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            return

        # Confirm deletion
        count = len(selected_items)
        item_text = "item" if count == 1 else "items"
        
        reply = QMessageBox.question(
            self.tree_widget,
            "Confirm Deletion",
            f"Are you sure you want to delete the selected {count} {item_text}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                # Get parent before deletion
                parent = item.parent()
                
                # Remove the item
                if parent:
                    parent.removeChild(item)
                else:
                    index = self.tree_widget.indexOfTopLevelItem(item)
                    if index >= 0:
                        self.tree_widget.takeTopLevelItem(index)
                
                print(f"DEBUG: Deleted item '{item.text(0)}'")

    def rename_item(self, item):
        """Rename the selected item"""
        if not item:
            return
        
        # Get current name (remove emoji prefix)
        current_text = item.text(0)
        if " " in current_text and any(current_text.startswith(emoji) for emoji in ["🎬", "🎵", "🖼️", "📄", "📊", "📽️", "📦", "💻"]):
            current_name = current_text.split(" ", 1)[1]
        else:
            current_name = current_text
        
        # Get new name from user
        text, ok = QInputDialog.getText(
            self.tree_widget,
            'Rename Item',
            'Enter new name:',
            QLineEdit.EchoMode.Normal,
            current_name
        )
        
        if ok and text.strip() and text.strip() != current_name:
            new_name = text.strip()
            
            # Update item data
            data = item.data(0, Qt.ItemDataRole.UserRole) or {}
            data['name'] = new_name
            item.setData(0, Qt.ItemDataRole.UserRole, data)
            
            # Update display text without emoji icons
            item.setText(0, new_name)
            
            print(f"DEBUG: Renamed item to '{new_name}'")

    def import_directory(self, target_item=None):
        """Import a directory structure"""
        if not self.tree_widget:
            return

        # Get directory from user
        dir_path = QFileDialog.getExistingDirectory(
            self.tree_widget,
            "Select Directory to Import",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if not dir_path:
            return
        
        try:
            # Import the directory contents
            self._import_directory_contents(dir_path, target_item)
            print(f"DEBUG: Successfully imported directory: {dir_path}")
        except Exception as e:
            QMessageBox.critical(
                self.tree_widget,
                "Import Error",
                f"Failed to import directory:\n{str(e)}"
            )

    def _import_directory_contents(self, dir_path, parent_item):
        """Recursively import directory contents"""
        try:
            for item_name in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item_name)
                
                if os.path.isdir(item_path):
                    # Create folder item
                    folder_item = self.add_folder(parent_item, item_name)
                    # Recursively import subdirectory
                    self._import_directory_contents(item_path, folder_item)
                else:
                    # Create file item
                    file_type = self.binary_handler.get_file_type_from_extension(item_path)
                    self._add_file_item(parent_item, item_name, file_type, item_path)
                    
        except Exception as e:
            print(f"ERROR: Failed to import directory contents: {e}")
            raise

    def import_file(self, target_item=None):
        """Import a single file"""
        if not self.tree_widget:
            return

        # Get file from user
        file_path, _ = QFileDialog.getOpenFileName(
            self.tree_widget,
            "Select File to Import",
            "",
            "All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            file_name = os.path.basename(file_path)
            file_type = self.binary_handler.get_file_type_from_extension(file_path)
            
            # Add the file item
            self._add_file_item(target_item, file_name, file_type, file_path)
            print(f"DEBUG: Successfully imported file: {file_name}")
            
        except Exception as e:
            QMessageBox.critical(
                self.tree_widget,
                "Import Error",
                f"Failed to import file:\n{str(e)}"
            )

    def is_binary_file(self, file_path):
        """Check if a file is binary"""
        return self.binary_handler.is_binary_file(file_path)

    def create_context_menu(self, position):
        """Create and show context menu"""
        print(f"DEBUG: create_context_menu called with position {position}")
        
        if not self.tree_widget:
            print("DEBUG: create_context_menu - no tree widget available")
            return
        
        # Check if tree_widget is still valid (not deleted)
        try:
            # Try to access the tree widget to verify it's still valid
            if not hasattr(self.tree_widget, 'itemAt'):
                print("DEBUG: create_context_menu - tree widget is invalid")
                return
        except (RuntimeError, AttributeError):
            print("DEBUG: create_context_menu - tree widget has been deleted")
            return
        
        print("DEBUG: create_context_menu - tree widget available, creating context menu")
        
        # Store current item for context - with proper error handling
        try:
            self.current_context_item = self.tree_widget.itemAt(position)
            item = self.current_context_item
        except (RuntimeError, AttributeError):
            print("DEBUG: create_context_menu - error getting item at position")
            return
        
        # Safely get item text for debugging
        try:
            item_text = item.text(0) if item else 'None'
        except (RuntimeError, AttributeError):
            item_text = 'Invalid/Deleted Item'
        print(f"DEBUG: Item at position: {item_text}")
        
        # Create menu with error handling
        try:
            menu = QMenu(self.tree_widget)
        except (RuntimeError, AttributeError):
            print("DEBUG: Failed to create menu - tree widget invalid")
            return
        
        # Style the menu to match application theme - using the original UIBuilder styling
        from app.ui.color_scheme_pyqt import APP_COLORS
        colors = APP_COLORS
        
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 5px;
            }}
            QMenu::item {{
                padding: 5px 15px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: {colors['highlight_bg']};
                color: {colors['highlight_text']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {colors['border']};
                margin: 5px 2px;
            }}
        """)
        
        # Add basic actions first (like the original)
        add_file_action = menu.addAction("Add File")
        add_file_action.triggered.connect(lambda: self.editor.add_file() if hasattr(self.editor, 'add_file') else None)
        
        add_folder_action = menu.addAction("Add Folder")
        add_folder_action.triggered.connect(lambda: self.editor.add_folder() if hasattr(self.editor, 'add_folder') else None)
        
        if item:
            try:
                menu.addSeparator()
                
                # Item-specific actions
                rename_action = menu.addAction("Rename")
                rename_action.triggered.connect(lambda: self.tree_widget.editItem(item, 0) if self.tree_widget else None)

                delete_action = menu.addAction("Delete")
                delete_action.triggered.connect(lambda: self._delete_item(item))
                    
                # Get item data for file-specific actions - with error handling
                try:
                    item_data = item.data(0, Qt.ItemDataRole.UserRole) if item else {}
                except (RuntimeError, AttributeError):
                    item_data = {}
                    
                if isinstance(item_data, dict) and item_data.get('type') == 'file':
                    menu.addSeparator()
                    
                    # Original project name action
                    action_text = "Revert to Original Name" if item_data.get('rename_flag') or item_data.get('uses_project_name') else "Use Project Name"
                    use_project_name_action = menu.addAction(action_text)
                    use_project_name_action.triggered.connect(lambda: self.editor._toggle_project_name_for_file(item) if hasattr(self.editor, '_toggle_project_name_for_file') else None)
                
                # Versioning menu for files
                versioning_menu = menu.addMenu("Versioning")
                
                # Date sequence option
                date_action = versioning_menu.addAction("Date Sequences...")
                date_action.triggered.connect(lambda: self._configure_date_sequences(item))
                
                # Separator and project name options
                menu.addSeparator()
                
                # Project name mode actions
                project_menu = menu.addMenu("Project Name")
                
                prepend_action = project_menu.addAction("Prepend Project Name")
                prepend_action.triggered.connect(lambda: self._set_project_name_mode(item, 'prepend'))
                
                append_action = project_menu.addAction("Append Project Name")
                append_action.triggered.connect(lambda: self._set_project_name_mode(item, 'append'))
                
                replace_action = project_menu.addAction("Replace with Project Name")
                replace_action.triggered.connect(lambda: self._set_project_name_mode(item, 'replace'))
                
                menu.addSeparator()
                
                # Custom patterns
                patterns_action = menu.addAction("Custom Naming Patterns...")
                patterns_action.triggered.connect(lambda: self._configure_custom_patterns(item))
                
                # Separator and other options
                menu.addSeparator()
                
            except (RuntimeError, AttributeError) as e:
                print(f"DEBUG: Error building context menu for item: {e}")
        
        # Show menu if it has actions
        if not menu.isEmpty():
            try:
                if self.tree_widget and hasattr(self.tree_widget, 'mapToGlobal'):
                    global_pos = self.tree_widget.mapToGlobal(position)
                    print(f"DEBUG: Executing context menu at global position {global_pos}")
                    menu.exec(global_pos)
                else:
                    print("DEBUG: Tree widget invalid during menu execution")
            except (RuntimeError, AttributeError) as e:
                print(f"DEBUG: Error executing context menu: {e}")
            finally:
                # Always clean up the menu
                try:
                    menu.deleteLater()
                except:
                    pass
        else:
            print("DEBUG: Context menu is empty, not showing")
            try:
                menu.deleteLater()
            except:
                pass

    def _set_project_name_mode(self, item, mode):
        """Set project name mode for a file"""
        if not item:
            return
        
        # Get current item data
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        
        # Update the project name mode
        item_data['project_name_mode'] = mode
        item_data['uses_project_name'] = True
        item_data['rename_flag'] = True
        
        # Update the tree item data
        item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        print(f"DEBUG: Set {mode} mode for {item.text(0)}")
        
        # Update visual display if needed
        self._update_item_display(item)
    
    def _configure_custom_patterns(self, item):
        """Configure custom naming patterns for file"""
        dialog = CustomPatternsDialog(self.tree_widget, item)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pattern_data = dialog.get_pattern_data()
            self._apply_pattern_to_item(item, pattern_data)
    
    def _update_item_display(self, item):
        """Update the visual display of an item based on its data"""
        if not item:
            return
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        original_name = item_data.get('original_name', item.text(0))
        
        # Clean any existing display formatting
        display_name = original_name
        if ' ' in display_name and any(display_name.startswith(icon) for icon in ['🎬', '🎵', '🖼️', '📄', '📊', '📽️', '📦', '💻']):
            display_name = display_name.split(' ', 1)[1]
        
        # Apply project name placeholder if needed
        if item_data.get('uses_project_name', False):
            mode = item_data.get('project_name_mode', 'replace')
            if mode == 'replace':
                display_name = "${PROJECT_NAME}"
                if '.' in original_name:
                    extension = original_name.split('.')[-1]
                    display_name = f"${{PROJECT_NAME}}.{extension}"
            elif mode == 'prepend':
                display_name = f"${{PROJECT_NAME}}.{original_name}"
            elif mode == 'append':
                if '.' in original_name:
                    base, ext = original_name.rsplit('.', 1)
                    display_name = f"{base}.${{PROJECT_NAME}}.{ext}"
                else:
                    display_name = f"{original_name}.${{PROJECT_NAME}}"
        
        # Set display text without emoji icons
        item.setText(0, display_name)
    
    def _configure_versioning(self, item):
        """Configure versioning for file"""
        if not item:
            return
        
        dialog = VersioningDialog(self.tree_widget, item)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            versioning_data = dialog.get_versioning_data()
            self._apply_versioning_to_item(item, versioning_data)
    
    def _configure_date_sequences(self, item):
        """Configure date sequences for file versioning"""
        dialog = DateSequenceDialog(self.tree_widget, item)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            date_data = dialog.get_date_data()
            self._apply_date_sequence_to_item(item, date_data)
    
    def _apply_pattern_to_item(self, item, pattern_data):
        """Apply custom pattern to item"""
        data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        data.update(pattern_data)
        item.setData(0, Qt.ItemDataRole.UserRole, data)
        
        # Update display
        if pattern_data.get('pattern'):
            item.setText(0, pattern_data['pattern'])
    
    def _apply_versioning_to_item(self, item, versioning_data):
        """Apply versioning configuration to item"""
        if not item or not self.tree_widget:
            print("DEBUG: _apply_versioning_to_item - missing item or tree widget")
            return
            
        print(f"DEBUG: Applying versioning to item: {item.text(0)}")
        print(f"DEBUG: Versioning data: {versioning_data}")
        
        # Get parent item
        parent_item = item.parent()
        
        # Get original item data
        original_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        original_name = original_data.get('name', item.text(0))
        
        # Clean original name of any existing icons or prefixes if available
        if 'name' in original_data:
            original_name = original_data['name']
            if ' ' in original_name and any(original_name.startswith(icon) for icon in ['🎬', '🎵', '🖼️', '📄', '📊', '📽️', '📦', '💻']):
                original_name = original_name.split(' ', 1)[1]
                original_data['original_name'] = original_name
        
        # Ensure we have original_name stored for future reference
        if 'original_name' not in original_data:
            original_data['original_name'] = original_name
        
        # Extract base name and extension
        if '.' in original_name:
            base_name, extension = os.path.splitext(original_name)
        else:
            base_name = original_name
            extension = '.txt'  # Default extension
        
        # Get versioning parameters
        format_text = versioning_data.get('versioning_format', 'v01, v02, v03...')
        start_num = versioning_data.get('versioning_start', 1)
        count = versioning_data.get('versioning_count', 5)
        
        # Generate version strings and create new items
        created_items = []
        
        for i in range(count):
            version_num = start_num + i
            
            # Generate version string based on format
            if format_text.startswith("v0"):
                version_str = f"v{version_num:02d}"
            elif format_text.startswith("V0"):
                version_str = f"V{version_num:02d}"
            elif format_text.startswith("_v"):
                version_str = f"_v{version_num}"
            elif format_text.startswith("_V"):
                version_str = f"_V{version_num}"
            elif format_text.startswith("(v0"):
                version_str = f"(v{version_num:02d})"
            elif format_text.startswith("00"):
                version_str = f"{version_num:03d}"
            elif format_text.startswith("_00"):
                version_str = f"_{version_num:03d}"
            else:
                version_str = f"v{version_num:02d}"
            
            # Create new filename
            new_filename = f"{base_name}_{version_str}{extension}"
            
            # Create new tree item
            if i == 0:
                # Update the first item (original item)
                new_item = item
                new_item.setText(0, new_filename)
            else:
                # Create additional items
                if parent_item:
                    new_item = QTreeWidgetItem(parent_item)
                else:
                    new_item = QTreeWidgetItem(self.tree_widget)
                
                new_item.setText(0, new_filename)
            
            # Copy and update item data
            new_data = original_data.copy()
            new_data.update(versioning_data)
            new_data['name'] = new_filename
            new_data['original_name'] = original_name  # Keep reference to original
            new_data['version_number'] = version_num
            new_data['version_string'] = version_str
            
            new_item.setData(0, Qt.ItemDataRole.UserRole, new_data)
            
            # Set display text without emoji icons
            new_item.setText(0, new_filename)
            
            created_items.append(new_item)
            print(f"DEBUG: Created versioned file: {new_filename}")
        
        # Expand parent if needed
        if parent_item:
            parent_item.setExpanded(True)
        
        print(f"DEBUG: Successfully created {len(created_items)} versioned files")
    
    def _apply_date_sequence_to_item(self, item, date_data):
        """Apply date sequence configuration to item"""
        if not item or not self.tree_widget:
            print("DEBUG: _apply_date_sequence_to_item - missing item or tree widget")
            return
            
        print(f"DEBUG: Applying date sequence to item: {item.text(0)}")
        print(f"DEBUG: Date data: {date_data}")
        
        # Get parent item
        parent_item = item.parent()
        
        # Get original item data
        original_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        original_name = original_data.get('name', item.text(0))
        item_type = original_data.get('type', 'file')
        
        # Clean original name of any existing icons or prefixes
        if ' ' in original_name and any(original_name.startswith(icon) for icon in ['🎬', '🎵', '🖼️', '📄', '📊', '📽️', '📦', '💻']):
            original_name = original_name.split(' ', 1)[1]
        
        # Ensure we have original_name stored for future reference
        if 'original_name' not in original_data:
            original_data['original_name'] = original_name
        
        # Extract date sequence data
        date_format = date_data.get('date_format', 'YYYY-MM-DD')
        start_date = date_data.get('date_start')
        end_date = date_data.get('date_end')
        interval_value = date_data.get('date_interval_value', 1)
        interval_type = date_data.get('date_interval_type', 'Days')
        
        # Parse original filename/foldername to get base name and extension
        base_name = original_name
        extension = ""
        if item_type == 'file' and '.' in original_name:
            base_name, extension = original_name.rsplit('.', 1)
            extension = '.' + extension
        
        current_date = start_date
        created_items = []
        item_index = 0
        
        # Create items for each date in the sequence (limit to 10 for performance)
        while current_date <= end_date and len(created_items) < 10:
            # Format date string
            if date_format == "YYYY-MM-DD":
                date_str = current_date.strftime("%Y-%m-%d")
            elif date_format == "YYYYMMDD":
                date_str = current_date.strftime("%Y%m%d")
            elif date_format == "MM-DD-YYYY":
                date_str = current_date.strftime("%m-%d-%Y")
            elif date_format == "DD-MM-YYYY":
                date_str = current_date.strftime("%d-%m-%Y")
            elif date_format == "YYYY/MM/DD":
                date_str = current_date.strftime("%Y/%m/%d")
            elif date_format == "MM/DD/YYYY":
                date_str = current_date.strftime("%m/%d/%Y")
            else:
                date_str = current_date.strftime("%Y-%m-%d")  # Default format
            
            # Create new name with date
            new_name = f"{base_name}_{date_str}{extension}"
            
            # Create new tree item
            if item_index == 0:
                # Update the first item (original item)
                new_item = item
                new_item.setText(0, new_name)
            else:
                # Create additional items
                if parent_item:
                    new_item = QTreeWidgetItem(parent_item)
                else:
                    new_item = QTreeWidgetItem(self.tree_widget)
                
                new_item.setText(0, new_name)
                
                # For folders, copy all children to the new folder
                if item_type == 'folder' and item.childCount() > 0:
                    self._copy_folder_children(item, new_item)
            
            # Copy and update item data - ensure all data is JSON serializable
            new_data = original_data.copy()
            
            # Only copy JSON-serializable fields from date_data
            json_safe_date_data = {
                'date_format': date_data.get('date_format'),
                'date_start_iso': date_data.get('date_start_iso'),
                'date_end_iso': date_data.get('date_end_iso'),
                'date_interval_value': date_data.get('date_interval_value'),
                'date_interval_type': date_data.get('date_interval_type'),
                'uses_date_sequence': date_data.get('uses_date_sequence'),
                'rename_flag': date_data.get('rename_flag')
            }
            
            new_data.update(json_safe_date_data)
            new_data['name'] = new_name
            new_data['original_name'] = original_name  # Keep reference to original
            new_data['date_sequence_index'] = item_index
            new_data['date_sequence_date'] = current_date.isoformat()  # Convert to string
            
            # Set data on the tree item
            new_item.setData(0, Qt.ItemDataRole.UserRole, new_data)
            
            # Set display text without emoji icons
            new_item.setText(0, new_name)
            
            created_items.append(new_item)
            print(f"DEBUG: Created date sequence {item_type}: {new_name}")
            
            # Move to next date
            if interval_type == "Days":
                current_date += timedelta(days=interval_value)
            elif interval_type == "Weeks":
                current_date += timedelta(weeks=interval_value)
            elif interval_type == "Months":
                # Approximate month calculation
                current_date += timedelta(days=interval_value * 30)
            
            item_index += 1
        
        print(f"DEBUG: Successfully created {len(created_items)} date sequence {item_type}s")
        
        # Expand parent if it has children
        if parent_item:
            parent_item.setExpanded(True)
        
        # Refresh the tree widget
        if self.tree_widget:
            self.tree_widget.update()
    
    def _copy_folder_children(self, source_folder, target_folder):
        """Copy all children from source folder to target folder"""
        for i in range(source_folder.childCount()):
            source_child = source_folder.child(i)
            source_data = source_child.data(0, Qt.ItemDataRole.UserRole) or {}
            
            # Create new child item
            new_child = QTreeWidgetItem(target_folder)
            
            # Copy data and set proper display text
            source_name = source_data.get('name', source_child.text(0))
            # Clean any existing icons from the name
            if ' ' in source_name and any(source_name.startswith(icon) for icon in ['🎬', '🎵', '🖼️', '📄', '📊', '📽️', '📦', '💻']):
                source_name = source_name.split(' ', 1)[1]
            
            # Set display text without emoji icons
            new_child.setText(0, source_name)
            
            new_child.setData(0, Qt.ItemDataRole.UserRole, source_data.copy())
            
            # Recursively copy if this child is also a folder
            if source_data.get('type') == 'folder' and source_child.childCount() > 0:
                self._copy_folder_children(source_child, new_child)
    
    def _apply_to_folder(self, item):
        """Apply settings to all files in folder"""
        print(f"DEBUG: Apply to folder: {item.text(0)}")
    
    def _rename_item(self, item):
        """Rename an item"""
        if item and self.tree_widget:
            self.tree_widget.editItem(item, 0)
    
    def _delete_item(self, item):
        """Delete an item from the tree"""
        if not item or not self.tree_widget:
            return
        
        # Use the editor's delete functionality if available
        if hasattr(self.editor, 'delete_selected'):
            # Set the item as current before deleting
            self.tree_widget.setCurrentItem(item)
            self.editor.delete_selected()
        else:
            # Fallback - direct deletion
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                index = self.tree_widget.indexOfTopLevelItem(item)
                if index >= 0:
                    self.tree_widget.takeTopLevelItem(index)
    
    def _add_file(self):
        """Add a new file"""
        print("DEBUG: Add file")
    
    def _add_folder(self):
        """Add a new folder"""
        print("DEBUG: Add folder")

    def _configure_versioning_for_folder(self, item):
        """Configure versioning for all files in folder"""
        if not item:
            return
        
        dialog = VersioningDialog(self.tree_widget, item)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            versioning_data = dialog.get_versioning_data()
            self._apply_versioning_to_folder(item, versioning_data)
    
    def _configure_date_sequences_for_folder(self, folder_item):
        """Configure date sequences for all files in a folder"""
        dialog = DateSequenceDialog(self.tree_widget, folder_item)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            date_data = dialog.get_date_data()
            
            # Apply to all file children
            for i in range(folder_item.childCount()):
                child = folder_item.child(i)
                child_data = child.data(0, Qt.ItemDataRole.UserRole) or {}
                if child_data.get('type') == 'file':
                    self._apply_date_sequence_to_item(child, date_data)
    
    def _apply_versioning_to_folder(self, folder_item, versioning_data):
        """Apply versioning to all files in a folder"""
        if not folder_item:
            return
        
        print(f"DEBUG: Applying versioning to folder: {folder_item.text(0)}")
        
        # Find all file items in the folder
        file_items = []
        for i in range(folder_item.childCount()):
            child = folder_item.child(i)
            child_data = child.data(0, Qt.ItemDataRole.UserRole) or {}
            if child_data.get('type') == 'file':
                file_items.append(child)
        
        # Apply versioning to each file
        for file_item in file_items:
            self._apply_versioning_to_item(file_item, versioning_data)
        
        print(f"DEBUG: Applied versioning to {len(file_items)} files in folder")
    
    def _apply_date_sequence_to_folder(self, folder_item, date_data):
        """Apply date sequence to all files in a folder"""
        if not folder_item:
            return
        
        print(f"DEBUG: Applying date sequence to folder: {folder_item.text(0)}")
        
        # Find all file items in the folder
        file_items = []
        for i in range(folder_item.childCount()):
            child = folder_item.child(i)
            child_data = child.data(0, Qt.ItemDataRole.UserRole) or {}
            if child_data.get('type') == 'file':
                file_items.append(child)
        
        # Apply date sequence to each file
        for file_item in file_items:
            self._apply_date_sequence_to_item(file_item, date_data)
        
        print(f"DEBUG: Applied date sequence to {len(file_items)} files in folder")
    
    def _apply_project_name_to_folder(self, folder_item, mode):
        """Apply project name mode to all files in a folder"""
        if not folder_item:
            return
        
        print(f"DEBUG: Applying project name {mode} to folder: {folder_item.text(0)}")
        
        # Find all file items in the folder
        file_items = []
        for i in range(folder_item.childCount()):
            child = folder_item.child(i)
            child_data = child.data(0, Qt.ItemDataRole.UserRole) or {}
            if child_data.get('type') == 'file':
                file_items.append(child)
        
        # Apply project name mode to each file
        for file_item in file_items:
            self._set_project_name_mode(file_item, mode)
        
        print(f"DEBUG: Applied project name {mode} to {len(file_items)} files in folder")

    def _add_folder_context_actions(self, menu, item):
        """Add folder-specific context menu actions"""
        # Versioning operations for folders
        versioning_menu = menu.addMenu("Versioning")
        
        # Apply versioning to the folder itself
        date_folder_action = versioning_menu.addAction("Date Sequences (This Folder)...")
        date_folder_action.triggered.connect(lambda: self._configure_date_sequences(item))
        
        versioning_menu.addSeparator()
        
        # Apply versioning to files within folder
        folder_files_menu = versioning_menu.addMenu("Apply to All Files in Folder")
        
        date_action = folder_files_menu.addAction("Date Sequences...")
        date_action.triggered.connect(lambda: self._configure_date_sequences_for_folder(item))
        
        # Project name operations for all files in folder
        project_menu = folder_files_menu.addMenu("Project Name")
        
        prepend_folder_action = project_menu.addAction("Prepend Project Name")
        prepend_folder_action.triggered.connect(lambda: self._apply_project_name_to_folder(item, 'prepend'))
        
        append_folder_action = project_menu.addAction("Append Project Name")
        append_folder_action.triggered.connect(lambda: self._apply_project_name_to_folder(item, 'append'))
        
        replace_folder_action = project_menu.addAction("Replace with Project Name")
        replace_folder_action.triggered.connect(lambda: self._apply_project_name_to_folder(item, 'replace'))


class CustomPatternsDialog(QDialog):
    """Dialog for configuring custom naming patterns"""
    
    def __init__(self, parent, item):
        super().__init__(parent)
        self.item = item
        self.pattern_data = {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Custom Naming Patterns")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Custom File Naming Patterns")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Pattern input
        pattern_label = QLabel("Naming Pattern:")
        layout.addWidget(pattern_label)
        
        self.pattern_edit = QLineEdit()
        self.pattern_edit.setPlaceholderText("e.g., ${PROJECT_NAME}_${VERSION}_${DATE}")
        self.pattern_edit.textChanged.connect(self.update_preview)
        layout.addWidget(self.pattern_edit)
        
        # Available variables
        variables_label = QLabel("Available Variables:")
        layout.addWidget(variables_label)
        
        variables_text = QTextEdit()
        variables_text.setMaximumHeight(150)
        variables_text.setPlainText("""
${PROJECT_NAME} - Project name
${BASE} - Original filename without extension
${EXT} - File extension
${VERSION} - Version number (v01, v02, etc.)
${DATE} - Current date (YYYYMMDD)
${TIME} - Current time (HHMMSS)
${COUNTER} - Incremental counter (001, 002, etc.)
${CUSTOM} - Custom text field
        """.strip())
        variables_text.setReadOnly(True)
        layout.addWidget(variables_text)
        
        # Preview
        preview_label = QLabel("Preview:")
        layout.addWidget(preview_label)
        
        self.preview_label = QLabel("(Enter pattern above)")
        self.preview_label.setStyleSheet("background-color: #2b2b2b; color: #ffffff; padding: 8px; border-radius: 4px;")
        layout.addWidget(self.preview_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        apply_button = QPushButton("Apply Pattern")
        apply_button.clicked.connect(self.accept)
        button_layout.addWidget(apply_button)
        
        layout.addLayout(button_layout)
    
    def update_preview(self):
        """Update the preview based on current pattern"""
        pattern = self.pattern_edit.text()
        if not pattern:
            self.preview_label.setText("(Enter pattern above)")
            return
        
        # Create preview with sample data
        preview = pattern
        preview = preview.replace('${PROJECT_NAME}', 'MyProject')
        preview = preview.replace('${BASE}', 'filename')
        preview = preview.replace('${EXT}', '.txt')
        preview = preview.replace('${VERSION}', 'v01')
        preview = preview.replace('${DATE}', datetime.datetime.now().strftime('%Y%m%d'))
        preview = preview.replace('${TIME}', datetime.datetime.now().strftime('%H%M%S'))
        preview = preview.replace('${COUNTER}', '001')
        preview = preview.replace('${CUSTOM}', 'custom')
        
        self.preview_label.setText(f"Preview: {preview}")
    
    def get_pattern_data(self):
        """Get the configured pattern data"""
        return {
            'pattern': self.pattern_edit.text(),
            'uses_custom_pattern': True,
            'rename_flag': True
        }


class VersioningDialog(QDialog):
    """Dialog for configuring file versioning"""
    
    def __init__(self, parent, item):
        super().__init__(parent)
        self.item = item
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Configure Versioning")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("File Versioning Configuration")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Versioning format
        format_label = QLabel("Version Format:")
        layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "v01, v02, v03...",
            "V01, V02, V03...",
            "_v1, _v2, _v3...",
            "_V1, _V2, _V3...",
            "(v01), (v02), (v03)...",
            "001, 002, 003...",
            "_001, _002, _003..."
        ])
        layout.addWidget(self.format_combo)
        
        # Starting number
        start_label = QLabel("Starting Number:")
        layout.addWidget(start_label)
        
        self.start_spin = QSpinBox()
        self.start_spin.setMinimum(1)
        self.start_spin.setMaximum(999)
        self.start_spin.setValue(1)
        layout.addWidget(self.start_spin)
        
        # Number of versions
        count_label = QLabel("Number of Versions to Generate:")
        layout.addWidget(count_label)
        
        self.count_spin = QSpinBox()
        self.count_spin.setMinimum(1)
        self.count_spin.setMaximum(50)
        self.count_spin.setValue(5)
        layout.addWidget(self.count_spin)
        
        # Preview
        preview_label = QLabel("Preview:")
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(120)
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        
        # Connect signals
        self.format_combo.currentTextChanged.connect(self.update_preview)
        self.start_spin.valueChanged.connect(self.update_preview)
        self.count_spin.valueChanged.connect(self.update_preview)
        
        # Initial preview
        self.update_preview()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        apply_button = QPushButton("Apply Versioning")
        apply_button.clicked.connect(self.accept)
        button_layout.addWidget(apply_button)
        
        layout.addLayout(button_layout)
    
    def update_preview(self):
        """Update the versioning preview"""
        format_text = self.format_combo.currentText()
        start_num = self.start_spin.value()
        count = self.count_spin.value()
        
        base_name = "filename"
        extension = ".txt"
        
        preview_lines = []
        
        for i in range(count):
            version_num = start_num + i
            
            if format_text.startswith("v0"):
                version_str = f"v{version_num:02d}"
            elif format_text.startswith("V0"):
                version_str = f"V{version_num:02d}"
            elif format_text.startswith("_v"):
                version_str = f"_v{version_num}"
            elif format_text.startswith("_V"):
                version_str = f"_V{version_num}"
            elif format_text.startswith("(v0"):
                version_str = f"(v{version_num:02d})"
            elif format_text.startswith("00"):
                version_str = f"{version_num:03d}"
            elif format_text.startswith("_00"):
                version_str = f"_{version_num:03d}"
            else:
                version_str = f"v{version_num:02d}"
            
            filename = f"{base_name}_{version_str}{extension}"
            preview_lines.append(filename)
        
        self.preview_text.setPlainText("\n".join(preview_lines))
    
    def get_versioning_data(self):
        """Get the versioning configuration data"""
        return {
            'versioning_format': self.format_combo.currentText(),
            'versioning_start': self.start_spin.value(),
            'versioning_count': self.count_spin.value(),
            'uses_versioning': True,
            'rename_flag': True
        }


class DateSequenceDialog(QDialog):
    """Dialog for configuring date sequences for file versioning"""
    
    def __init__(self, parent, item):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("Configure Date Sequence")
        self.setModal(True)
        self.resize(500, 400)
        self.init_ui()
        
    def _qdate_to_python(self, qdate):
        """Convert QDate to Python datetime.date safely for PyQt6"""
        if hasattr(qdate, 'toPython'):
            return qdate.toPython()
        else:
            # PyQt6 alternative - use the QDate properties
            return datetime.date(qdate.year(), qdate.month(), qdate.day())
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Date Sequence Configuration")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Date format
        format_label = QLabel("Date Format:")
        layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "YYYY-MM-DD",
            "YYYYMMDD", 
            "MM-DD-YYYY",
            "DD-MM-YYYY",
            "YYYY/MM/DD",
            "MM/DD/YYYY",
            "DD/MM/YYYY",
            "Mon DD, YYYY",
            "DD Mon YYYY"
        ])
        layout.addWidget(self.format_combo)
        
        # Date range
        range_layout = QHBoxLayout()
        
        start_label = QLabel("Start Date:")
        range_layout.addWidget(start_label)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        range_layout.addWidget(self.start_date)
        
        end_label = QLabel("End Date:")
        range_layout.addWidget(end_label)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate().addDays(7))
        self.end_date.setCalendarPopup(True)
        range_layout.addWidget(self.end_date)
        
        layout.addLayout(range_layout)
        
        # Interval
        interval_layout = QHBoxLayout()
        
        interval_label = QLabel("Interval:")
        interval_layout.addWidget(interval_label)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setMaximum(365)
        self.interval_spin.setValue(1)
        interval_layout.addWidget(self.interval_spin)
        
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["Days", "Weeks", "Months"])
        interval_layout.addWidget(self.interval_combo)
        
        layout.addLayout(interval_layout)
        
        # Preview
        preview_label = QLabel("Preview (first 10 dates):")
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        
        # Connect signals
        self.format_combo.currentTextChanged.connect(self.update_preview)
        self.start_date.dateChanged.connect(self.update_preview)
        self.end_date.dateChanged.connect(self.update_preview)
        self.interval_spin.valueChanged.connect(self.update_preview)
        self.interval_combo.currentTextChanged.connect(self.update_preview)
        
        # Initial preview
        self.update_preview()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        apply_button = QPushButton("Apply Date Sequence")
        apply_button.clicked.connect(self.accept)
        button_layout.addWidget(apply_button)
        
        layout.addLayout(button_layout)
    
    def update_preview(self):
        """Update the preview of date sequences"""
        if not hasattr(self, 'preview_text'):
            return
            
        try:
            # Get date range
            start_date = self._qdate_to_python(self.start_date.date())
            end_date = self._qdate_to_python(self.end_date.date())
            
            # Get interval
            interval_value = self.interval_spin.value()
            interval_type = self.interval_combo.currentText()
            
            # Get item name and parse extension
            item_name = self.item.text(0) if self.item else "example_file"
            
            # Clean item name of icons
            if ' ' in item_name and any(item_name.startswith(icon) for icon in ['🎬', '🎵', '🖼️', '📄', '📊', '📽️', '📦', '💻']):
                item_name = item_name.split(' ', 1)[1]
            
            # Parse filename to get base name and extension
            base_name = item_name
            extension = ""
            if '.' in item_name:
                base_name, extension = item_name.rsplit('.', 1)
                extension = '.' + extension
            
            # Generate preview dates
            dates = []
            current_date = start_date
            
            while current_date <= end_date and len(dates) < 10:  # Limit preview to 10 items
                # Format date according to selected format
                format_text = self.format_combo.currentText()
                if format_text == "YYYY-MM-DD":
                    date_str = current_date.strftime("%Y-%m-%d")
                elif format_text == "YYYYMMDD":
                    date_str = current_date.strftime("%Y%m%d")
                elif format_text == "MM-DD-YYYY":
                    date_str = current_date.strftime("%m-%d-%Y")
                elif format_text == "DD-MM-YYYY":
                    date_str = current_date.strftime("%d-%m-%Y")
                elif format_text == "YYYY/MM/DD":
                    date_str = current_date.strftime("%Y/%m/%d")
                elif format_text == "MM/DD/YYYY":
                    date_str = current_date.strftime("%m/%d/%Y")
                else:
                    date_str = current_date.strftime("%Y-%m-%d")  # Default
                
                # Create example filename
                example_filename = f"{base_name}_{date_str}{extension}"
                dates.append(example_filename)
                
                # Move to next date
                if interval_type == "Days":
                    current_date += timedelta(days=interval_value)
                elif interval_type == "Weeks":
                    current_date += timedelta(weeks=interval_value)
                elif interval_type == "Months":
                    # Approximate month calculation
                    current_date += timedelta(days=interval_value * 30)
            
            # Update preview text
            preview_text = "Preview of generated files:\n\n"
            for i, filename in enumerate(dates, 1):
                preview_text += f"{i}. {filename}\n"
            
            if len(dates) >= 10:
                preview_text += "\n... (showing first 10 items)"
            
            self.preview_text.setPlainText(preview_text)
            
        except Exception as e:
            print(f"DEBUG: Error updating date preview: {e}")
            if hasattr(self, 'preview_text'):
                self.preview_text.setPlainText("Error generating preview")
    
    def get_date_data(self):
        """Get the date sequence configuration data"""
        # Convert dates to ISO format strings for JSON serialization
        start_date = self._qdate_to_python(self.start_date.date())
        end_date = self._qdate_to_python(self.end_date.date())
        
        return {
            'date_format': self.format_combo.currentText(),
            'date_start': start_date,  # Keep as date object for processing
            'date_end': end_date,      # Keep as date object for processing
            'date_start_iso': start_date.isoformat(),  # Store string version for JSON
            'date_end_iso': end_date.isoformat(),      # Store string version for JSON
            'date_interval_value': self.interval_spin.value(),
            'date_interval_type': self.interval_combo.currentText(),
            'uses_date_sequence': True,
            'rename_flag': True
        }


class FileDetailsDialog(QDialog):
    """Dialog for entering file details"""
    
    def __init__(self, parent, title, message, file_name="", categories=None, 
                selected_type="", show_binary=True, is_binary=False):
        """Initialize the dialog"""
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Add message
        if message:
            label = QLabel(message)
            layout.addWidget(label)
        
        # File name field
        name_layout = QHBoxLayout()
        name_label = QLabel("File name:")
        name_layout.addWidget(name_label)
        
        self.file_name_edit = QLineEdit(file_name)
        self.file_name_edit.setPlaceholderText("Enter file name with extension")
        name_layout.addWidget(self.file_name_edit)
        
        layout.addLayout(name_layout)
        
        # File type dropdown
        type_layout = QHBoxLayout()
        type_label = QLabel("File type:")
        type_layout.addWidget(type_label)
        
        self.file_type_combo = QComboBox()
        if categories:
            self.file_type_combo.addItems(categories)
            if selected_type and selected_type in categories:
                self.file_type_combo.setCurrentText(selected_type)
                
        self.file_type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.file_type_combo)
        
        layout.addLayout(type_layout)
        
        # Binary checkbox
        if show_binary:
            self.binary_checkbox = QCheckBox("Binary file (will be cached)")
            self.binary_checkbox.setChecked(is_binary)
            layout.addWidget(self.binary_checkbox)
        else:
            self.binary_checkbox = None
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        button_layout.addStretch()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        
        # Apply styles
        self.setStyleSheet("""
            QDialog {
                background-color: #2D2D30;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
            }
            QLineEdit, QComboBox {
                background-color: #3E3E42;
                color: #FFFFFF;
                border: 1px solid #3F3F46;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #007ACC;
            }
            QPushButton {
                background-color: #3E3E42;
                color: #FFFFFF;
                border: 1px solid #3F3F46;
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #4E4E52;
            }
        """)
    
    def _on_type_changed(self, index):
        """Handle file type change"""
        # Could update UI based on selected type
        pass
    
    def get_file_name(self):
        """Get the entered file name"""
        return self.file_name_edit.text().strip()
    
    def get_file_type(self):
        """Get the selected file type"""
        return self.file_type_combo.currentText()
    
    def is_binary(self):
        """Get binary file status"""
        if self.binary_checkbox:
            return self.binary_checkbox.isChecked()
        return False 
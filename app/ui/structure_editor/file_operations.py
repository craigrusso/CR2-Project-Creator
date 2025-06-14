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
    QTreeWidgetItem, QApplication, QSpacerItem, QSizePolicy, QGroupBox
)
from PyQt6.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QBrush, QColor
import re

# Import binary file handler
from app.utils.binary_file_handler import BinaryFileHandler

# Import styling
from app.ui.color_scheme_pyqt import colors, COMBOBOX_STYLE, BUTTON_STYLE, ACCENT_BUTTON_STYLE

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
        self._context_menu_connected = False  # Track connection state
        
        # Connect context menu if tree widget is available
        if self.tree_widget:
            self._connect_context_menu()
            print("DEBUG: Connected context menu to tree widget")
        else:
            print("DEBUG: No tree widget provided to FileOperations")
        
        print("DEBUG: Initialized file operations handler")

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
        
        # Set proper folder icon immediately
        try:
            from app.ui.icon_utilities import get_folder_icon
            folder_item.setIcon(0, get_folder_icon(False))  # Initially collapsed
        except ImportError:
            # Fallback to standard icon
            from PyQt6.QtWidgets import QApplication, QStyle
            folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        
        # Make folder editable
        folder_item.setFlags(folder_item.flags() | Qt.ItemFlag.ItemIsEditable)
        
        # Expand parent if needed
        if parent_item:
            parent_item.setExpanded(True)
        
        # Expand the new folder
        folder_item.setExpanded(True)
        
        # Force immediate icon refresh to ensure proper system folder icon
        try:
            from app.ui.tree_styling import update_item_icon
            update_item_icon(folder_item)
        except ImportError:
            pass
        
        print(f"DEBUG: Added folder '{folder_name}' to tree with proper icon")
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
        
        # Get selected items and item at position
        try:
            selected_items = self.tree_widget.selectedItems()
            item_at_position = self.tree_widget.itemAt(position)
            
            # If clicked item is not in selection, select just that item
            if item_at_position and item_at_position not in selected_items:
                self.tree_widget.setCurrentItem(item_at_position)
                selected_items = [item_at_position]
            
            # Use the clicked item or first selected item as context
            self.current_context_item = item_at_position or (selected_items[0] if selected_items else None)
            
        except (RuntimeError, AttributeError):
            print("DEBUG: create_context_menu - error getting items")
            return
        
        print(f"DEBUG: Selected items count: {len(selected_items)}")
        
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
        
        if selected_items:
            try:
                menu.addSeparator()
                
                # Multi-selection vs single selection actions
                if len(selected_items) == 1:
                    item = selected_items[0]
                    # Single item actions
                    rename_action = menu.addAction("Rename")
                    rename_action.triggered.connect(lambda: self.tree_widget.editItem(item, 0) if self.tree_widget else None)
                
                # Delete action (works for single or multiple)
                delete_text = f"Delete {len(selected_items)} items" if len(selected_items) > 1 else "Delete"
                delete_action = menu.addAction(delete_text)
                delete_action.triggered.connect(lambda: self._delete_selected_items(selected_items))
                
                # Check if we have any files or folders selected
                file_items = []
                folder_items = []
                for item in selected_items:
                    try:
                        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
                        if isinstance(item_data, dict):
                            if item_data.get('type') == 'file':
                                file_items.append(item)
                            elif item_data.get('type') == 'folder':
                                folder_items.append(item)
                    except (RuntimeError, AttributeError):
                        continue
                
                # Handle folder-specific actions
                if folder_items and len(selected_items) == 1:
                    # Single folder selected
                    menu.addSeparator()
                    self._add_folder_context_actions(menu, folder_items[0])
                
                if file_items:
                    menu.addSeparator()
                    
                    if len(file_items) == 1:
                        # Single file - original actions
                        item_data = file_items[0].data(0, Qt.ItemDataRole.UserRole) or {}
                        action_text = "Revert to Original Name" if item_data.get('rename_flag') or item_data.get('uses_project_name') else "Use Project Name"
                        use_project_name_action = menu.addAction(action_text)
                        use_project_name_action.triggered.connect(lambda: self.editor._toggle_project_name_for_file(file_items[0]) if hasattr(self.editor, '_toggle_project_name_for_file') else None)
                        
                        # Versioning menu for single file
                        versioning_menu = menu.addMenu("Versioning")
                        date_action = versioning_menu.addAction("Date Sequences...")
                        date_action.triggered.connect(lambda: self._configure_date_sequences(file_items[0]))
                        
                        patterns_action = menu.addAction("Custom Naming Patterns...")
                        patterns_action.triggered.connect(lambda: self._configure_custom_patterns(file_items[0]))
                    else:
                        # Multiple files - bulk operations
                        bulk_menu = menu.addMenu(f"Bulk Operations ({len(file_items)} files)")
                        
                        # Bulk project name operations
                        prepend_bulk_action = bulk_menu.addAction("Prepend Project Name to All")
                        prepend_bulk_action.triggered.connect(lambda: self._bulk_set_project_name_mode(file_items, 'prepend'))
                        
                        append_bulk_action = bulk_menu.addAction("Append Project Name to All")
                        append_bulk_action.triggered.connect(lambda: self._bulk_set_project_name_mode(file_items, 'append'))
                        
                        replace_bulk_action = bulk_menu.addAction("Replace All with Project Name")
                        replace_bulk_action.triggered.connect(lambda: self._bulk_set_project_name_mode(file_items, 'replace'))
                        
                        bulk_menu.addSeparator()
                        
                        revert_bulk_action = bulk_menu.addAction("Revert All to Original Names")
                        revert_bulk_action.triggered.connect(lambda: self._bulk_revert_to_original(file_items))
                    
                    # Project name mode actions (available for single or multiple)
                    menu.addSeparator()
                    project_menu = menu.addMenu("Project Name")
                    
                    prepend_action = project_menu.addAction("Prepend Project Name")
                    prepend_action.triggered.connect(lambda: self._bulk_set_project_name_mode(file_items, 'prepend'))
                    
                    append_action = project_menu.addAction("Append Project Name")
                    append_action.triggered.connect(lambda: self._bulk_set_project_name_mode(file_items, 'append'))
                    
                    replace_action = project_menu.addAction("Replace with Project Name")
                    replace_action.triggered.connect(lambda: self._bulk_set_project_name_mode(file_items, 'replace'))
                
            except (RuntimeError, AttributeError) as e:
                print(f"DEBUG: Error building context menu for items: {e}")
        
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
        
        # Store original name if not already stored
        if 'original_name' not in item_data:
            item_data['original_name'] = item.text(0)
        
        # Update the project name mode
        item_data['project_name_mode'] = mode
        item_data['uses_project_name'] = True
        item_data['rename_flag'] = True
        
        # Update the tree item data
        item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Update the display name
        self._update_project_name_display(item, mode)
        
        # Update visual styling
        self._update_item_display(item)
        
        print(f"DEBUG: Set {mode} mode for {item.text(0)}")
    
    def _configure_custom_patterns(self, item):
        """Configure custom naming patterns for file"""
        dialog = CustomPatternsDialog(self.tree_widget, item)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pattern_data = dialog.get_pattern_data()
            self._apply_pattern_to_item(item, pattern_data)
            
            # Clear any pending events to prevent unwanted context menu triggers
            if self.tree_widget:
                # Temporarily disable context menu to prevent spurious triggers
                original_policy = self.tree_widget.contextMenuPolicy()
                self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
                
                # Also disable the structure editor's context menu if available
                if self.editor and hasattr(self.editor, '_disable_context_menu_temporarily'):
                    self.editor._disable_context_menu_temporarily()
                
                # Process any pending events to clear the event queue
                from PyQt6.QtWidgets import QApplication
                QApplication.processEvents()
                
                # Use a timer to restore context menu after a short delay
                QTimer.singleShot(100, lambda: self._restore_context_menu(original_policy))
                
                # Ensure focus is properly managed
                self.tree_widget.clearFocus()
                self.tree_widget.setFocus()
    
    def _update_item_display(self, item):
        """Update the visual display of an item based on its properties"""
        if not item:
            return
        
        try:
            item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
            
            # Apply styling based on item properties
            if item_data.get('uses_custom_pattern'):
                # Custom pattern files - purple and italic
                font = item.font(0)
                font.setItalic(True)
                item.setFont(0, font)
                item.setForeground(0, QBrush(QColor("#9A4AFF")))  # Purple for custom patterns
            elif item_data.get('uses_project_name') or item_data.get('rename_flag'):
                # Project name files - blue and italic
                font = item.font(0)
                font.setItalic(True)
                item.setFont(0, font)
                item.setForeground(0, QBrush(QColor("#4A9BFF")))  # Blue for project name
            else:
                # Reset to normal styling
                font = item.font(0)
                font.setItalic(False)
                item.setFont(0, font)
                
                # Reset color to default
                item.setForeground(0, QBrush())
                
        except (RuntimeError, AttributeError) as e:
            print(f"DEBUG: Error updating item display: {e}")

    def _configure_versioning(self, item):
        """Configure versioning for file"""
        if not item:
            return
        
        dialog = VersioningDialog(self.tree_widget, item)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            versioning_data = dialog.get_versioning_data()
            self._apply_versioning_to_item(item, versioning_data)
            
            # Clear any pending events to prevent unwanted context menu triggers
            if self.tree_widget:
                # Temporarily disable context menu to prevent spurious triggers
                original_policy = self.tree_widget.contextMenuPolicy()
                self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
                
                # Also disable the structure editor's context menu if available
                if self.editor and hasattr(self.editor, '_disable_context_menu_temporarily'):
                    self.editor._disable_context_menu_temporarily()
                
                # Process any pending events to clear the event queue
                from PyQt6.QtWidgets import QApplication
                QApplication.processEvents()
                
                # Use a timer to restore context menu after a short delay
                QTimer.singleShot(100, lambda: self._restore_context_menu(original_policy))
                
                # Ensure focus is properly managed
                self.tree_widget.clearFocus()
                self.tree_widget.setFocus()
    
    def _configure_date_sequences(self, item):
        """Configure date sequences for file versioning"""
        dialog = DateSequenceDialog(self.tree_widget, item)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            date_data = dialog.get_date_data()
            self._apply_date_sequence_to_item(item, date_data)
            
            # Clear any pending events to prevent unwanted context menu triggers
            if self.tree_widget:
                # Temporarily disable context menu to prevent spurious triggers
                original_policy = self.tree_widget.contextMenuPolicy()
                self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
                
                # Also disable the structure editor's context menu if available
                if self.editor and hasattr(self.editor, '_disable_context_menu_temporarily'):
                    self.editor._disable_context_menu_temporarily()
                
                # Process any pending events to clear the event queue
                from PyQt6.QtWidgets import QApplication
                QApplication.processEvents()
                
                # Use a timer to restore context menu after a short delay
                # This prevents any immediate context menu triggers from stray events
                QTimer.singleShot(100, lambda: self._restore_context_menu(original_policy))
                
                # Ensure focus is properly managed
                self.tree_widget.clearFocus()
                self.tree_widget.setFocus()
    
    def _restore_context_menu(self, original_policy):
        """Restore the context menu policy after a delay"""
        if self.tree_widget:
            self.tree_widget.setContextMenuPolicy(original_policy)
            print("DEBUG: Context menu policy restored after date sequence dialog")
    
    def _apply_pattern_to_item(self, item, pattern_data):
        """Apply custom pattern to item"""
        data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        
        # Store original name if not already stored
        if 'original_name' not in data:
            data['original_name'] = item.text(0)
        
        # Update data with pattern information
        data.update(pattern_data)
        data['uses_custom_pattern'] = True
        data['rename_flag'] = True
        # Clear conflicting flags
        data['uses_project_name'] = False
        
        item.setData(0, Qt.ItemDataRole.UserRole, data)
        
        # Update display to show the pattern
        if pattern_data.get('pattern'):
            # Display the pattern as-is for template editing
            item.setText(0, pattern_data['pattern'])
            
            # Apply styling to indicate this item uses a custom pattern
            font = item.font(0)
            font.setItalic(True)
            item.setFont(0, font)
            
            # Use a different color for custom pattern files
            from PyQt6.QtGui import QBrush, QColor
            item.setForeground(0, QBrush(QColor("#9A4AFF")))  # Purple for custom patterns
            
            print(f"DEBUG: Applied custom pattern '{pattern_data['pattern']}' to item '{data.get('original_name', item.text(0))}'")
        
        # Update visual styling
        self._update_item_display(item)
    
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
                
                # Set proper icon and properties based on item type
                if item_type == 'folder':
                    # Set proper folder icon immediately
                    try:
                        from app.ui.icon_utilities import get_folder_icon
                        new_item.setIcon(0, get_folder_icon(False))  # Initially collapsed
                    except ImportError:
                        # Fallback to standard icon
                        from PyQt6.QtWidgets import QApplication, QStyle
                        new_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                    
                    # Make folder editable
                    new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
                    
                    # Copy all children to the new folder if it's a folder
                    if item.childCount() > 0:
                        self._copy_folder_children(item, new_item)
                else:
                    # Set proper file icon
                    try:
                        from app.ui.icon_utilities import get_file_icon
                        new_item.setIcon(0, get_file_icon(new_filename))
                    except ImportError:
                        # Fallback to standard icon
                        from PyQt6.QtWidgets import QApplication, QStyle
                        new_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                    
                    # Make file editable
                    new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
            
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
            
            # Force immediate icon refresh to ensure proper system icons
            try:
                from app.ui.tree_styling import update_item_icon
                update_item_icon(new_item)
            except ImportError:
                pass
            
            created_items.append(new_item)
            print(f"DEBUG: Created versioned {item_type}: {new_filename} with proper icon")
        
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
                
                # Set proper icon and properties based on item type
                if item_type == 'folder':
                    # Set proper folder icon immediately
                    try:
                        from app.ui.icon_utilities import get_folder_icon
                        new_item.setIcon(0, get_folder_icon(False))  # Initially collapsed
                    except ImportError:
                        # Fallback to standard icon
                        from PyQt6.QtWidgets import QApplication, QStyle
                        new_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                    
                    # Make folder editable
                    new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
                    
                    # Copy all children to the new folder
                    if item.childCount() > 0:
                        self._copy_folder_children(item, new_item)
                else:
                    # Set proper file icon
                    try:
                        from app.ui.icon_utilities import get_file_icon
                        new_item.setIcon(0, get_file_icon(new_name))
                    except ImportError:
                        # Fallback to standard icon
                        from PyQt6.QtWidgets import QApplication, QStyle
                        new_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                    
                    # Make file editable
                    new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
            
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
            
            # If the original item had project name settings, apply them to the date sequence name
            if original_data.get('uses_project_name') and item_type == 'file':
                # Apply project name to the date-sequenced filename
                mode = original_data.get('project_name_mode', 'prepend')
                self._update_project_name_display(new_item, mode)
                # Update visual styling
                self._update_item_display(new_item)
            else:
                # Set display text without emoji icons
                new_item.setText(0, new_name)
            
            # Force immediate icon refresh to ensure proper system icons
            try:
                from app.ui.tree_styling import update_item_icon
                update_item_icon(new_item)
            except ImportError:
                pass
            
            created_items.append(new_item)
            print(f"DEBUG: Created date sequence {item_type}: {new_name} with proper icon")
            
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
            
            # Set proper icon and properties based on item type
            child_type = source_data.get('type', 'file')
            if child_type == 'folder':
                # Set proper folder icon
                try:
                    from app.ui.icon_utilities import get_folder_icon
                    new_child.setIcon(0, get_folder_icon(False))  # Initially collapsed
                except ImportError:
                    # Fallback to standard icon
                    from PyQt6.QtWidgets import QApplication, QStyle
                    new_child.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                
                # Make folder editable
                new_child.setFlags(new_child.flags() | Qt.ItemFlag.ItemIsEditable)
                
                # Recursively copy if this child is also a folder
                if source_child.childCount() > 0:
                    self._copy_folder_children(source_child, new_child)
            else:
                # Set proper file icon
                try:
                    from app.ui.icon_utilities import get_file_icon
                    new_child.setIcon(0, get_file_icon(source_name))
                except ImportError:
                    # Fallback to standard icon
                    from PyQt6.QtWidgets import QApplication, QStyle
                    new_child.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                
                # Make file editable
                new_child.setFlags(new_child.flags() | Qt.ItemFlag.ItemIsEditable)
            
            # Force immediate icon refresh
            try:
                from app.ui.tree_styling import update_item_icon
                update_item_icon(new_child)
            except ImportError:
                pass
    
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
            
            # Clear any pending events to prevent unwanted context menu triggers
            if self.tree_widget:
                # Temporarily disable context menu to prevent spurious triggers
                original_policy = self.tree_widget.contextMenuPolicy()
                self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
                
                # Also disable the structure editor's context menu if available
                if self.editor and hasattr(self.editor, '_disable_context_menu_temporarily'):
                    self.editor._disable_context_menu_temporarily()
                
                # Process any pending events to clear the event queue
                from PyQt6.QtWidgets import QApplication
                QApplication.processEvents()
                
                # Use a timer to restore context menu after a short delay
                QTimer.singleShot(100, lambda: self._restore_context_menu(original_policy))
                
                # Ensure focus is properly managed
                self.tree_widget.clearFocus()
                self.tree_widget.setFocus()
    
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
            
            # Clear any pending events to prevent unwanted context menu triggers
            if self.tree_widget:
                # Temporarily disable context menu to prevent spurious triggers
                original_policy = self.tree_widget.contextMenuPolicy()
                self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
                
                # Also disable the structure editor's context menu if available
                if self.editor and hasattr(self.editor, '_disable_context_menu_temporarily'):
                    self.editor._disable_context_menu_temporarily()
                
                # Process any pending events to clear the event queue
                from PyQt6.QtWidgets import QApplication
                QApplication.processEvents()
                
                # Use a timer to restore context menu after a short delay
                QTimer.singleShot(100, lambda: self._restore_context_menu(original_policy))
                
                # Ensure focus is properly managed
                self.tree_widget.clearFocus()
                self.tree_widget.setFocus()
    
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
        date_folder_action = versioning_menu.addAction("Date Sequences (This Folder)...")
        date_folder_action.triggered.connect(lambda: self._configure_date_sequences(item))
        versioning_menu.addSeparator()
        folder_files_menu = versioning_menu.addMenu("Apply to All Files in Folder")
        date_action = folder_files_menu.addAction("Date Sequences...")
        date_action.triggered.connect(lambda: self._configure_date_sequences_for_folder(item))
        project_menu = folder_files_menu.addMenu("Project Name")
        prepend_folder_action = project_menu.addAction("Prepend Project Name")
        prepend_folder_action.triggered.connect(lambda: self._apply_project_name_to_folder(item, 'prepend'))
        append_folder_action = project_menu.addAction("Append Project Name")
        append_folder_action.triggered.connect(lambda: self._apply_project_name_to_folder(item, 'append'))
        replace_folder_action = project_menu.addAction("Replace with Project Name")
        replace_folder_action.triggered.connect(lambda: self._apply_project_name_to_folder(item, 'replace'))
        # --- Add custom pattern for folders ---
        menu.addSeparator()
        custom_pattern_action = menu.addAction("Custom Naming Pattern...")
        custom_pattern_action.triggered.connect(lambda: self._configure_custom_patterns(item))

    def _delete_selected_items(self, items):
        """Delete multiple selected items"""
        if not items or not self.tree_widget:
            return

        # Confirm deletion
        count = len(items)
        item_text = "item" if count == 1 else "items"
        
        reply = QMessageBox.question(
            self.tree_widget,
            "Confirm Deletion",
            f"Are you sure you want to delete the selected {count} {item_text}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for item in items:
                try:
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
                except (RuntimeError, AttributeError) as e:
                    print(f"DEBUG: Error deleting item: {e}")

    def _bulk_set_project_name_mode(self, items, mode):
        """Set project name mode for multiple files"""
        if not items:
            return
        
        print(f"DEBUG: Setting {mode} mode for {len(items)} files")
        
        for item in items:
            try:
                # Get current item data
                item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
                
                # Only apply to files
                if item_data.get('type') != 'file':
                    continue
                
                # Store original name if not already stored
                if 'original_name' not in item_data:
                    item_data['original_name'] = item.text(0)
                
                # Update the project name mode
                item_data['project_name_mode'] = mode
                item_data['uses_project_name'] = True
                item_data['rename_flag'] = True
                
                # Update the tree item data
                item.setData(0, Qt.ItemDataRole.UserRole, item_data)
                
                # Update the display name
                self._update_project_name_display(item, mode)
                
                # Update visual styling
                self._update_item_display(item)
                
                print(f"DEBUG: Set {mode} mode for {item.text(0)}")
            except (RuntimeError, AttributeError) as e:
                print(f"DEBUG: Error setting project name mode for item: {e}")

    def _bulk_revert_to_original(self, items):
        """Revert multiple files to their original names"""
        if not items:
            return
        
        print(f"DEBUG: Reverting {len(items)} files to original names")
        
        for item in items:
            try:
                # Get current item data
                item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
                
                # Only apply to files that use project name
                if item_data.get('type') != 'file' or not item_data.get('uses_project_name'):
                    continue
                
                # Get original name
                original_name = item_data.get('original_name', item.text(0))
                
                # Reset project name flags
                item_data['uses_project_name'] = False
                item_data['rename_flag'] = False
                item_data.pop('project_name_mode', None)
                
                # Update the tree item data
                item.setData(0, Qt.ItemDataRole.UserRole, item_data)
                
                # Reset display name
                item.setText(0, original_name)
                
                # Update visual styling
                self._update_item_display(item)
                
                print(f"DEBUG: Reverted {item.text(0)} to original name")
            except (RuntimeError, AttributeError) as e:
                print(f"DEBUG: Error reverting item to original name: {e}")

    def _update_project_name_display(self, item, mode):
        """Update the display name of an item based on project name mode"""
        if not item:
            return
        
        try:
            item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
            original_name = item_data.get('original_name', item.text(0))
            
            # Split filename into base and extension
            name_parts = original_name.rsplit('.', 1)
            if len(name_parts) == 2:
                base_name, extension = name_parts
                extension = '.' + extension
            else:
                base_name = original_name
                extension = ''
            
            # Create the display name based on mode
            placeholder = "${PROJECT_NAME}"
            separator = "_"
            
            if mode == 'replace':
                display_name = f"{placeholder}{extension}"
            elif mode == 'prepend':
                display_name = f"{placeholder}{separator}{base_name}{extension}"
            elif mode == 'append':
                display_name = f"{base_name}{separator}{placeholder}{extension}"
            else:
                # Default to replace
                display_name = f"{placeholder}{extension}"
            
            # Update the display
            item.setText(0, display_name)
            print(f"DEBUG: Updated display name to: {display_name}")
            
        except (RuntimeError, AttributeError) as e:
            print(f"DEBUG: Error updating project name display: {e}")


class CustomPatternsDialog(QDialog):
    """Dialog for configuring custom naming patterns"""
    def __init__(self, parent, item):
        super().__init__(parent)
        self.item = item
        self.pattern_data = {}
        self.is_folder = self._is_folder_item(item)
        self.init_ui()
        self._load_existing_pattern_data()

    def _is_folder_item(self, item):
        """Check if the item is a folder"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return item_data.get('type') == 'folder' or item.childCount() > 0

    def init_ui(self):
        """Initialize the user interface"""
        from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE
        self.setWindowTitle("Custom Naming Patterns")
        self.setMinimumSize(900, 1000)
        self.resize(1000, 1100)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg']};
                color: {colors['text']};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Title
        item_type = "Folder" if self.is_folder else "File"
        title = QLabel(f"Custom {item_type} Naming Patterns")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Available variables
        variables_header = QLabel("Available Variables:")
        variables_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        variables_header.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-bottom: 5px;
        """)
        layout.addWidget(variables_header)
        
        # Tags widget
        tags_widget = QWidget()
        tags_widget.setStyleSheet(f"background-color: transparent; border: none;")
        tags_layout = QGridLayout(tags_widget)
        tags_layout.setSpacing(8)
        
        # Different tags for files vs folders
        if self.is_folder:
            self.tags = [
                ("${PROJECT_NAME}", "Project name"),
                ("${DATE}", "Current date (YYYYMMDD)"),
                ("${TIME}", "Current time (HHMMSS)"),
                ("${COUNTER}", "Incremental counter (001, 002, etc.)"),
                ("${CUSTOM}", "Custom dropdown options"),
                ("${CUSTOM1}", "First custom option"),
                ("${CUSTOM2}", "Second custom option"),
                ("${CUSTOM3}", "Third custom option")
            ]
        else:
            self.tags = [
                ("${PROJECT_NAME}", "Project name"),
                ("${BASE}", "Original filename without extension"),
                ("${DATE}", "Current date (YYYYMMDD)"),
                ("${TIME}", "Current time (HHMMSS)"),
                ("${CUSTOM}", "Custom dropdown options"),
                ("${CUSTOM1}", "First custom option"),
                ("${CUSTOM2}", "Second custom option"),
                ("${CUSTOM3}", "Third custom option")
            ]
        
        for i, (tag, description) in enumerate(self.tags):
            tag_button = QPushButton(tag)
            tag_button.setToolTip(description)
            tag_button.clicked.connect(lambda checked, tag=tag: self.insert_tag(tag))
            tag_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['card_bg_alt']};
                    color: {colors['text']};
                    border: 1px solid {colors['border']};
                    padding: 2px 6px;
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: normal;
                    min-width: 50px;
                    max-height: 20px;
                }}
                QPushButton:hover {{
                    background-color: {colors['accent']};
                    border: 1px solid {colors['highlight_border']};
                }}
                QPushButton:pressed {{
                    background-color: {colors['highlight_bg']};
                    color: {colors['highlight_text']};
                }}
            """)
            row = i // 3
            col = i % 3
            tags_layout.addWidget(tag_button, row, col)
        layout.addWidget(tags_widget)
        
        # Separator options
        separator_header = QLabel("Choose separator for pattern elements:")
        separator_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        separator_header.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-top: 10px;
            margin-bottom: 5px;
        """)
        layout.addWidget(separator_header)
        
        # Separator selection widget
        separator_widget = QWidget()
        separator_widget.setStyleSheet(f"background-color: transparent; border: none;")
        separator_layout = QHBoxLayout(separator_widget)
        separator_layout.setSpacing(10)
        
        self.separator_combo = QComboBox()
        self.separator_combo.addItems([
            "_ (underscore)",
            "- (dash)", 
            ". (dot)",
            "  (space)",
            "Custom..."
        ])
        self.separator_combo.setCurrentIndex(0)  # Default to underscore
        self.separator_combo.setStyleSheet(COMBOBOX_STYLE)
        self.separator_combo.currentTextChanged.connect(self._on_separator_changed)
        separator_layout.addWidget(self.separator_combo)
        
        # Custom separator input (hidden by default)
        self.custom_separator_edit = QLineEdit()
        self.custom_separator_edit.setPlaceholderText("Enter custom separator...")
        self.custom_separator_edit.setMaxLength(3)  # Limit to 3 characters
        self.custom_separator_edit.setVisible(False)
        self.custom_separator_edit.textChanged.connect(self._on_custom_separator_changed)
        self.custom_separator_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 100px;
                max-width: 100px;
            }}
            QLineEdit:focus {{
                border: 2px solid {colors['accent']};
            }}
        """)
        separator_layout.addWidget(self.custom_separator_edit)
        
        separator_layout.addStretch()
        layout.addWidget(separator_widget)
        
        # Pattern input
        pattern_header = QLabel("Enter your naming pattern:")
        pattern_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        pattern_header.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-top: 10px;
            margin-bottom: 5px;
        """)
        layout.addWidget(pattern_header)
        
        self.pattern_edit = QLineEdit()
        if self.is_folder:
            self.pattern_edit.setPlaceholderText("e.g., ${PROJECT_NAME}_${CUSTOM}_Folder or Shot_${COUNTER}")
        else:
            self.pattern_edit.setPlaceholderText("e.g., ${PROJECT_NAME}_${CUSTOM}_TRAILER (extension auto-added)")
        self.pattern_edit.textChanged.connect(self.update_preview)
        self.pattern_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['accent']};
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
                font-family: 'Courier New', monospace;
            }}
            QLineEdit:focus {{
                border: 2px solid {colors['accent_hover']};
                background-color: {colors['highlight_bg_transparent']};
            }}
        """)
        layout.addWidget(self.pattern_edit)
        
        # Custom options group (hidden by default)
        self.custom_options_group = QGroupBox("Custom Dropdown Options")
        self.custom_options_group.setVisible(False)
        self.custom_options_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {colors['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: {colors['text']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: {colors['text']};
                background-color: {colors['bg']};
            }}
        """)
        custom_layout = QVBoxLayout()
        
        custom_help = QLabel("Configure options for each CUSTOM placeholder:")
        custom_help.setStyleSheet(f"""
            color: {colors['secondary_text']};
            background-color: transparent;
            border: none;
            padding: 5px 0px;
        """)
        custom_layout.addWidget(custom_help)
        
        # Container for custom option editors - will be populated dynamically
        self.custom_editors_container = QWidget()
        self.custom_editors_layout = QVBoxLayout(self.custom_editors_container)
        self.custom_editors_layout.setContentsMargins(0, 0, 0, 0)
        self.custom_editors_layout.setSpacing(10)
        custom_layout.addWidget(self.custom_editors_container)
        
        # Store custom option editors
        self.custom_option_editors = {}
        
        self.custom_options_group.setLayout(custom_layout)
        layout.addWidget(self.custom_options_group)
        
        # Date format options group (hidden by default)
        self.date_format_group = QGroupBox("Date Format Options (for ${DATE})")
        self.date_format_group.setVisible(False)
        self.date_format_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {colors['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: {colors['text']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: {colors['text']};
                background-color: {colors['bg']};
            }}
        """)
        date_layout = QVBoxLayout()
        
        date_help = QLabel("Choose how the ${DATE} tag will be formatted:")
        date_help.setStyleSheet(f"""
            color: {colors['secondary_text']};
            background-color: transparent;
            border: none;
            padding: 5px 0px;
        """)
        date_layout.addWidget(date_help)
        
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems([
            "YYYYMMDD (20240115)",
            "YYYY_MM_DD (2024_01_15)",
            "YYYY-MM-DD (2024-01-15)",
            "YYYY.MM.DD (2024.01.15)",
            "YYYY MM DD (2024 01 15)",
            "MM_DD_YYYY (01_15_2024)",
            "MM-DD-YYYY (01-15-2024)",
            "MM.DD.YYYY (01.15.2024)",
            "MM DD YYYY (01 15 2024)",
            "DD_MM_YYYY (15_01_2024)",
            "DD-MM-YYYY (15-01-2024)",
            "DD.MM.YYYY (15.01.2024)",
            "DD MM YYYY (15 01 2024)"
        ])
        self.date_format_combo.setStyleSheet(COMBOBOX_STYLE)
        self.date_format_combo.currentTextChanged.connect(self.update_preview)
        date_layout.addWidget(self.date_format_combo)
        
        self.date_format_group.setLayout(date_layout)
        layout.addWidget(self.date_format_group)
        
        # Time format options group (hidden by default)
        self.time_format_group = QGroupBox("Time Format Options (for ${TIME})")
        self.time_format_group.setVisible(False)
        self.time_format_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {colors['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: {colors['text']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: {colors['text']};
                background-color: {colors['bg']};
            }}
        """)
        time_layout = QVBoxLayout()
        
        time_help = QLabel("Choose how the ${TIME} tag will be formatted:")
        time_help.setStyleSheet(f"""
            color: {colors['secondary_text']};
            background-color: transparent;
            border: none;
            padding: 5px 0px;
        """)
        time_layout.addWidget(time_help)
        
        self.time_format_combo = QComboBox()
        self.time_format_combo.addItems([
            "HHMMSS (143022)",
            "HH_MM_SS (14_30_22)",
            "HH-MM-SS (14-30-22)",
            "HH.MM.SS (14.30.22)",
            "HH MM SS (14 30 22)",
            "HHMM (1430)",
            "HH_MM (14_30)",
            "HH-MM (14-30)",
            "HH.MM (14.30)",
            "HH MM (14 30)"
        ])
        self.time_format_combo.setStyleSheet(COMBOBOX_STYLE)
        self.time_format_combo.currentTextChanged.connect(self.update_preview)
        time_layout.addWidget(self.time_format_combo)
        
        self.time_format_group.setLayout(time_layout)
        layout.addWidget(self.time_format_group)
        
        # Sequence settings group (hidden by default, only for folders)
        if self.is_folder:
            self.sequence_group = QGroupBox("Sequence Settings (for ${COUNTER})")
            self.sequence_group.setVisible(False)
            self.sequence_group.setStyleSheet(f"""
                QGroupBox {{
                    font-weight: bold;
                    border: 2px solid {colors['border']};
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 10px;
                    color: {colors['text']};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    color: {colors['text']};
                    background-color: {colors['bg']};
                }}
            """)
            seq_layout = QHBoxLayout()
            self.seq_start = QSpinBox(); self.seq_start.setMinimum(1); self.seq_start.setValue(1)
            self.seq_count = QSpinBox(); self.seq_count.setMinimum(1); self.seq_count.setValue(5)
            self.seq_padding = QSpinBox(); self.seq_padding.setMinimum(1); self.seq_padding.setMaximum(10); self.seq_padding.setValue(3)
            seq_layout.addWidget(QLabel("Start:")); seq_layout.addWidget(self.seq_start)
            seq_layout.addWidget(QLabel("Count:")); seq_layout.addWidget(self.seq_count)
            seq_layout.addWidget(QLabel("Padding:")); seq_layout.addWidget(self.seq_padding)
            self.sequence_group.setLayout(seq_layout)
            layout.addWidget(self.sequence_group)
        
        # Preview
        preview_header = QLabel("Preview:")
        preview_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        preview_header.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-bottom: 5px;
        """)
        layout.addWidget(preview_header)
        
        self.preview_label = QLabel("Preview will appear here once you create a pattern above")
        self.preview_label.setMinimumHeight(60)
        self.preview_label.setWordWrap(True)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.preview_label.setStyleSheet(f"""
            background-color: {colors['card_bg_alt']};
            color: {colors['text']};
            padding: 15px;
            border-radius: 6px;
            border: 1px solid {colors['border']};
            font-family: 'Courier New', monospace;
            font-size: 13px;
        """)
        layout.addWidget(self.preview_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 20, 0, 0)  # Add top margin
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet(BUTTON_STYLE)
        cancel_button.setMinimumSize(120, 40)
        button_layout.addWidget(cancel_button)
        
        button_layout.addStretch()
        
        apply_button = QPushButton("Apply Pattern")
        apply_button.clicked.connect(self.on_apply)
        apply_button.setDefault(True)
        apply_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        apply_button.setMinimumSize(140, 40)
        button_layout.addWidget(apply_button)
        layout.addLayout(button_layout)
        
        self.pattern_edit.setFocus()

    def _on_separator_changed(self):
        """Handle separator selection change"""
        separator_text = self.separator_combo.currentText()
        if separator_text == "Custom...":
            self.custom_separator_edit.setVisible(True)
            self.custom_separator_edit.setFocus()
        else:
            self.custom_separator_edit.setVisible(False)
        
        # Auto-update existing pattern to use new separator
        self._update_pattern_separators()
        self.update_preview()
    
    def _on_custom_separator_changed(self):
        """Handle custom separator text change"""
        # Auto-update existing pattern to use new custom separator
        self._update_pattern_separators()
        self.update_preview()
    
    def _update_pattern_separators(self):
        """Update existing pattern to use the currently selected separator as master switch"""
        current_pattern = self.pattern_edit.text()
        if not current_pattern:
            return
        
        # Get the new separator
        new_separator = self._get_current_separator()
        
        # Update pattern separators between variables
        self._update_pattern_variable_separators(current_pattern, new_separator)
        
        # Update date and time format dropdowns to match separator (master switch)
        self._update_datetime_formats_to_separator(new_separator)
    
    def _update_pattern_variable_separators(self, current_pattern, new_separator):
        """Update separators between variables in the pattern"""
        import re
        variables = re.findall(r'\$\{[A-Z_]+\}', current_pattern)
        if len(variables) < 2:
            return  # No need to add separators for single variables
        
        pattern = current_pattern
        
        # Replace all separators between variables with new separator
        for i in range(len(variables) - 1):
            var1 = variables[i]
            var2 = variables[i + 1]
            
            var1_end = pattern.find(var1) + len(var1)
            var2_start = pattern.find(var2, var1_end)
            
            if var2_start > var1_end:
                # There's something between variables, replace it with new separator
                between_text = pattern[var1_end:var2_start]
                # Replace any separator characters with new separator
                if re.match(r'^[_\-\.\s]+$', between_text):
                    pattern = pattern[:var1_end] + new_separator + pattern[var2_start:]
                    # Recalculate positions after replacement
                    variables = re.findall(r'\$\{[A-Z_]+\}', pattern)
            elif var2_start == var1_end:
                # Variables are consecutive, add separator
                pattern = pattern[:var1_end] + new_separator + pattern[var2_start:]
                # Recalculate positions after insertion
                variables = re.findall(r'\$\{[A-Z_]+\}', pattern)
        
        self.pattern_edit.setText(pattern)
    
    def _update_datetime_formats_to_separator(self, separator):
        """Update date and time format dropdowns to match the separator (master switch)"""
        # Update date format to match separator
        if "${DATE}" in self.pattern_edit.text():
            current_date_format = self.date_format_combo.currentText()
            new_date_format = self._convert_format_to_separator(current_date_format, separator, is_date=True)
            
            # Find and set the matching format in dropdown
            for i in range(self.date_format_combo.count()):
                dropdown_format = self.date_format_combo.itemText(i).split(' (')[0]
                if dropdown_format == new_date_format:
                    self.date_format_combo.setCurrentIndex(i)
                    break
        
        # Update time format to match separator  
        if "${TIME}" in self.pattern_edit.text():
            current_time_format = self.time_format_combo.currentText()
            new_time_format = self._convert_format_to_separator(current_time_format, separator, is_date=False)
            
            # Find and set the matching format in dropdown
            for i in range(self.time_format_combo.count()):
                dropdown_format = self.time_format_combo.itemText(i).split(' (')[0]
                if dropdown_format == new_time_format:
                    self.time_format_combo.setCurrentIndex(i)
                    break
    
    def _convert_format_to_separator(self, current_format, new_separator, is_date=True):
        """Convert a date/time format to use the new separator"""
        # Extract the format pattern from the display text (before the parentheses)
        format_pattern = current_format.split(' (')[0]
        
        if is_date:
            # Date format conversion - match exact dropdown options
            if format_pattern == "YYYYMMDD":
                return "YYYYMMDD"  # No separator format stays the same
            elif format_pattern.startswith("YYYY"):
                return f"YYYY{new_separator}MM{new_separator}DD"
            elif format_pattern.startswith("MM"):
                return f"MM{new_separator}DD{new_separator}YYYY"
            elif format_pattern.startswith("DD"):
                return f"DD{new_separator}MM{new_separator}YYYY"
        else:
            # Time format conversion - match exact dropdown options
            if format_pattern == "HHMMSS":
                return "HHMMSS"  # No separator format stays the same
            elif format_pattern == "HHMM":
                return "HHMM"  # No separator format stays the same
            elif "SS" in format_pattern:  # Has seconds
                return f"HH{new_separator}MM{new_separator}SS"
            else:  # Just hours and minutes
                return f"HH{new_separator}MM"
        
        return format_pattern  # Return original if no conversion needed
    
    def _get_current_separator(self):
        """Get the currently selected separator"""
        separator_text = self.separator_combo.currentText()
        if separator_text == "Custom...":
            return self.custom_separator_edit.text() or "_"
        elif separator_text.startswith("_ "):
            return "_"
        elif separator_text.startswith("- "):
            return "-"
        elif separator_text.startswith(". "):
            return "."
        elif separator_text.startswith("  "):
            return " "
        else:
            return "_"  # Default fallback
    
    def _detect_manual_separators(self, pattern):
        """Detect if user has manually added separators in the pattern"""
        # Check if pattern contains separators between variables
        import re
        variables = re.findall(r'\$\{[A-Z_]+\}', pattern)
        if len(variables) < 2:
            return False
        
        # Check for separators between consecutive variables
        for i in range(len(variables) - 1):
            var1_end = pattern.find(variables[i]) + len(variables[i])
            var2_start = pattern.find(variables[i + 1], var1_end)
            between_text = pattern[var1_end:var2_start]
            if between_text.strip():  # If there's text between variables
                return True
        return False

    def insert_tag(self, tag):
        cursor_pos = self.pattern_edit.cursorPosition()
        current_text = self.pattern_edit.text()
        
        # Check if we should add separator automatically
        separator = self._get_current_separator()
        
        # If there's already text and we're not at the beginning, add separator
        if current_text and cursor_pos > 0 and not current_text[cursor_pos-1] in ['_', '-', '.', ' ']:
            # Don't add separator if user has manually added separators
            if not self._detect_manual_separators(current_text):
                tag = separator + tag
        
        new_text = current_text[:cursor_pos] + tag + current_text[cursor_pos:]
        self.pattern_edit.setText(new_text)
        self.pattern_edit.setCursorPosition(cursor_pos + len(tag))
        self.pattern_edit.setFocus()
        self.update_preview()

    def update_preview(self):
        pattern = self.pattern_edit.text()
        if not pattern:
            self.preview_label.setText("Preview will appear here once you create a pattern above")
            self.custom_options_group.setVisible(False)
            self.date_format_group.setVisible(False)
            self.time_format_group.setVisible(False)
            if hasattr(self, 'sequence_group'):
                self.sequence_group.setVisible(False)
            return
        
        # Check for any custom placeholders (CUSTOM, CUSTOM1, CUSTOM2, etc.)
        import re
        custom_matches = re.findall(r'\$\{CUSTOM\d*\}', pattern)
        has_custom = len(custom_matches) > 0
        
        # Show custom options group if any ${CUSTOM} variants are present
        if has_custom:
            self.custom_options_group.setVisible(True)
            self._update_custom_editors(custom_matches)
        else:
            self.custom_options_group.setVisible(False)
            self._clear_custom_editors()
        
        # Show date format group if ${DATE} is present
        if "${DATE}" in pattern:
            self.date_format_group.setVisible(True)
        else:
            self.date_format_group.setVisible(False)
        
        # Show time format group if ${TIME} is present
        if "${TIME}" in pattern:
            self.time_format_group.setVisible(True)
        else:
            self.time_format_group.setVisible(False)
        
        # Show sequence group if ${COUNTER} is present and this is a folder
        if self.is_folder and "${COUNTER}" in pattern:
            self.sequence_group.setVisible(True)
            start = self.seq_start.value()
            count = self.seq_count.value()
            padding = self.seq_padding.value()
            preview = []
            for i in range(start, start + min(count, 5)):
                counter_str = str(i).zfill(padding)
                sample_preview = self._generate_sample_preview(pattern.replace("${COUNTER}", counter_str))
                preview.append(sample_preview)
            self.preview_label.setText("\n".join(preview))
        else:
            if hasattr(self, 'sequence_group'):
                self.sequence_group.setVisible(False)
            preview = self._generate_sample_preview(pattern)
            self.preview_label.setText(f"Preview: {preview}")
    
    def _update_custom_editors(self, custom_placeholders):
        """Update the custom option editors based on placeholders found in pattern"""
        from app.ui.color_scheme_pyqt import colors
        
        # Clear existing editors
        self._clear_custom_editors()
        
        # Create editor for each unique placeholder
        unique_placeholders = list(set(custom_placeholders))
        unique_placeholders.sort()  # Sort for consistent order
        
        for placeholder in unique_placeholders:
            placeholder_name = placeholder.replace('${', '').replace('}', '')  # Remove ${ }
            
            # Create container for this placeholder's editor
            editor_widget = QWidget()
            editor_layout = QVBoxLayout(editor_widget)
            editor_layout.setContentsMargins(0, 0, 0, 0)
            editor_layout.setSpacing(5)
            
            # Label for this placeholder
            label = QLabel(f"Options for {placeholder}:")
            label.setStyleSheet(f"""
                color: {colors['text']};
                font-weight: bold;
                background-color: transparent;
                border: none;
            """)
            editor_layout.addWidget(label)
            
            # Text editor for options
            text_edit = QTextEdit()
            text_edit.setPlaceholderText(f"Enter options for {placeholder} (one per line):\nROUGH\nFINAL\nREVIEW")
            text_edit.setMinimumHeight(80)
            text_edit.setMaximumHeight(120)
            text_edit.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {colors['card_bg']};
                    color: {colors['text']};
                    border: 1px solid {colors['border']};
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 13px;
                }}
            """)
            text_edit.textChanged.connect(self.update_preview)
            editor_layout.addWidget(text_edit)
            
            # Store the editor
            self.custom_option_editors[placeholder_name] = text_edit
            
            # Add to layout
            self.custom_editors_layout.addWidget(editor_widget)
    
    def _clear_custom_editors(self):
        """Clear all custom option editors"""
        # Remove all widgets from layout
        for i in reversed(range(self.custom_editors_layout.count())):
            child = self.custom_editors_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Clear the editors dictionary
        self.custom_option_editors.clear()

    def _generate_sample_preview(self, pattern):
        """Generate a sample preview for the pattern"""
        preview = pattern
        
        # Get formatted date/time values based on user selection
        now = datetime.datetime.now()
        separator = self._get_current_separator()
        
        # Auto-adjust date/time formats to match separator if not manually set
        manual_separators = self._detect_manual_separators(pattern)
        
        # Format date based on selection or auto-adjust to separator
        if "${DATE}" in pattern:
            date_format_text = self.date_format_combo.currentText()
            
            # If user hasn't manually set separators, auto-adjust format to match separator
            if not manual_separators and separator != "_":
                if separator == "-":
                    date_str = now.strftime('%Y-%m-%d')
                elif separator == ".":
                    date_str = now.strftime('%Y.%m.%d')
                elif separator == " ":
                    date_str = now.strftime('%Y %m %d')
                else:
                    date_str = now.strftime('%Y_%m_%d')  # Default to underscore
            else:
                # Use user's explicit format choice
                if "YYYYMMDD" in date_format_text:
                    date_str = now.strftime('%Y%m%d')
                elif "YYYY_MM_DD" in date_format_text:
                    date_str = now.strftime('%Y_%m_%d')
                elif "YYYY-MM-DD" in date_format_text:
                    date_str = now.strftime('%Y-%m-%d')
                elif "YYYY.MM.DD" in date_format_text:
                    date_str = now.strftime('%Y.%m.%d')
                elif "YYYY MM DD" in date_format_text:
                    date_str = now.strftime('%Y %m %d')
                elif "MM_DD_YYYY" in date_format_text:
                    date_str = now.strftime('%m_%d_%Y')
                elif "MM-DD-YYYY" in date_format_text:
                    date_str = now.strftime('%m-%d-%Y')
                elif "MM.DD.YYYY" in date_format_text:
                    date_str = now.strftime('%m.%d.%Y')
                elif "MM DD YYYY" in date_format_text:
                    date_str = now.strftime('%m %d %Y')
                elif "DD_MM_YYYY" in date_format_text:
                    date_str = now.strftime('%d_%m_%Y')
                elif "DD-MM-YYYY" in date_format_text:
                    date_str = now.strftime('%d-%m-%Y')
                elif "DD.MM.YYYY" in date_format_text:
                    date_str = now.strftime('%d.%m.%Y')
                elif "DD MM YYYY" in date_format_text:
                    date_str = now.strftime('%d %m %Y')
                else:
                    date_str = now.strftime('%Y%m%d')  # Default
        else:
            date_str = now.strftime('%Y%m%d')
        
        # Format time based on selection or auto-adjust to separator
        if "${TIME}" in pattern:
            time_format_text = self.time_format_combo.currentText()
            
            # If user hasn't manually set separators, auto-adjust format to match separator
            if not manual_separators and separator != "_":
                if separator == "-":
                    time_str = now.strftime('%H-%M-%S')
                elif separator == ".":
                    time_str = now.strftime('%H.%M.%S')
                elif separator == " ":
                    time_str = now.strftime('%H %M %S')
                else:
                    time_str = now.strftime('%H_%M_%S')  # Default to underscore
            else:
                # Use user's explicit format choice
                if "HHMMSS" in time_format_text:
                    time_str = now.strftime('%H%M%S')
                elif "HH_MM_SS" in time_format_text:
                    time_str = now.strftime('%H_%M_%S')
                elif "HH-MM-SS" in time_format_text:
                    time_str = now.strftime('%H-%M-%S')
                elif "HH.MM.SS" in time_format_text:
                    time_str = now.strftime('%H.%M.%S')
                elif "HH MM SS" in time_format_text:
                    time_str = now.strftime('%H %M %S')
                elif "HHMM" in time_format_text:
                    time_str = now.strftime('%H%M')
                elif "HH_MM" in time_format_text:
                    time_str = now.strftime('%H_%M')
                elif "HH-MM" in time_format_text:
                    time_str = now.strftime('%H-%M')
                elif "HH.MM" in time_format_text:
                    time_str = now.strftime('%H.%M')
                elif "HH MM" in time_format_text:
                    time_str = now.strftime('%H %M')
                else:
                    time_str = now.strftime('%H%M%S')  # Default
        else:
            time_str = now.strftime('%H%M%S')
        
        # Replace basic placeholders
        preview = preview.replace('${PROJECT_NAME}', 'MyProject')
        preview = preview.replace('${DATE}', date_str)
        preview = preview.replace('${TIME}', time_str)
        
        if not self.is_folder:
            # For files, use original filename parts and auto-add extension
            original_name = self.item.text(0)
            if '.' in original_name:
                base, ext = os.path.splitext(original_name)
                preview = preview.replace('${BASE}', base)
                # Automatically append extension if not already present
                if not preview.endswith(ext):
                    preview += ext
            else:
                preview = preview.replace('${BASE}', original_name)
        
        # Handle custom options - support multiple CUSTOM placeholders with dedicated editors
        import re
        custom_matches = re.findall(r'\$\{(CUSTOM\d*)\}', preview)
        if custom_matches:
            for match in custom_matches:
                placeholder = f"${{{match}}}"
                
                # Get options from the specific editor for this placeholder
                if match in self.custom_option_editors:
                    editor = self.custom_option_editors[match]
                    custom_options = editor.toPlainText().strip().split('\n')
                    custom_options = [opt.strip() for opt in custom_options if opt.strip()]
                    
                    if custom_options:
                        # Use the first option as preview
                        replacement = custom_options[0]
                    else:
                        replacement = f"[{match}]"
                else:
                    replacement = f"[{match}]"
                
                preview = preview.replace(placeholder, replacement)
        
        return preview

    def validate_pattern(self):
        pattern = self.pattern_edit.text()
        errors = []
        sequence = None
        custom_options = []
        
        # Validate sequence settings for folders
        if self.is_folder and "${COUNTER}" in pattern:
            sequence = {
                'start': self.seq_start.value(),
                'count': self.seq_count.value(),
                'padding': self.seq_padding.value()
            }
            if not all(isinstance(sequence[k], int) and sequence[k] > 0 for k in ("start", "count", "padding")):
                errors.append("All sequence fields must be positive integers.")
        
        # Validate custom options - support multiple CUSTOM placeholders with dedicated editors
        import re
        custom_matches = re.findall(r'\$\{CUSTOM\d*\}', pattern)
        if custom_matches:
            # Check each placeholder has options
            for match in custom_matches:
                placeholder_name = match.replace('CUSTOM', 'CUSTOM') if match == 'CUSTOM' else match
                
                if placeholder_name in self.custom_option_editors:
                    editor = self.custom_option_editors[placeholder_name]
                    custom_text = editor.toPlainText().strip()
                    
                    if not custom_text:
                        errors.append(f"Options are required for ${{{match}}}.")
                    else:
                        placeholder_options = [opt.strip() for opt in custom_text.split('\n') if opt.strip()]
                        if not placeholder_options:
                            errors.append(f"At least one option is required for ${{{match}}}.")
                        # Store options for this specific placeholder
                        if not custom_options:
                            custom_options = {}
                        custom_options[match] = placeholder_options
                else:
                    errors.append(f"No options configured for ${{{match}}}.")
        
        # Check for unsupported variables
        if self.is_folder:
            allowed_vars = ("PROJECT_NAME", "DATE", "TIME", "COUNTER", "CUSTOM", "CUSTOM1", "CUSTOM2", "CUSTOM3")
        else:
            allowed_vars = ("PROJECT_NAME", "BASE", "DATE", "TIME", "CUSTOM", "CUSTOM1", "CUSTOM2", "CUSTOM3")
        
        for var in re.findall(r"\$\{([A-Z_\d]+)\}", pattern):
            if var not in allowed_vars:
                if var in ("COUNTER", "VERSION") and not self.is_folder:
                    errors.append(f"${{{var}}} is only available for folders, not files.")
                else:
                    errors.append(f"Unsupported variable: ${{{var}}}")
        
        return errors, sequence, custom_options

    def on_apply(self):
        errors, sequence, custom_options = self.validate_pattern()
        if errors:
            self.preview_label.setText("Validation error:\n" + "\n".join(errors))
            self.preview_label.setStyleSheet("color: red;")
            return
        
        self.pattern_data = {
            'pattern': self.pattern_edit.text(),
            'uses_custom_pattern': True,
            'rename_flag': True
        }
        
        if sequence:
            self.pattern_data['sequence'] = sequence
        
        if custom_options:
            self.pattern_data['custom_options'] = custom_options
        
        # Save date format preference
        if "${DATE}" in self.pattern_edit.text():
            self.pattern_data['date_format'] = self.date_format_combo.currentText()
        
        # Save time format preference
        if "${TIME}" in self.pattern_edit.text():
            self.pattern_data['time_format'] = self.time_format_combo.currentText()
        
        # Save separator preference
        self.pattern_data['separator'] = self._get_current_separator()
        self.pattern_data['separator_choice'] = self.separator_combo.currentText()
        if self.separator_combo.currentText() == "Custom...":
            self.pattern_data['custom_separator'] = self.custom_separator_edit.text()
        
        # --- Save pattern to item data for persistence ---
        item_data = self.item.data(0, Qt.ItemDataRole.UserRole) or {}
        item_data.update(self.pattern_data)
        self.item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        self.accept()

    def get_pattern_data(self):
        return self.pattern_data

    def _load_existing_pattern_data(self):
        """Load existing pattern data from the item if available"""
        if not self.item:
            return
        
        print(f"DEBUG: Loading existing pattern: {self.pattern_edit.text()}")
        
        # Get item data safely
        item_data = self.item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(item_data, dict):
            print(f"DEBUG: No valid item data found")
            return
        
        # Check for pattern data in multiple locations with safety checks
        pattern_data = None
        
        # Try to get from user_data first
        user_data = item_data.get('user_data')
        if isinstance(user_data, dict):
            # Look for pattern data
            if 'pattern' in user_data:
                pattern_data = user_data
                print(f"DEBUG: Found pattern data in user_data")
            # Also check for nested user_data (avoid infinite recursion)
            elif 'user_data' in user_data and isinstance(user_data['user_data'], dict):
                nested_data = user_data['user_data']
                if 'pattern' in nested_data:
                    pattern_data = nested_data
                    print(f"DEBUG: Found pattern data in nested user_data")
        
        # If no pattern data found, return early
        if not pattern_data:
            print(f"DEBUG: No existing pattern data found in item")
            return
        
        # Load pattern safely
        pattern = pattern_data.get('pattern', '')
        if pattern:
            print(f"DEBUG: Loading existing pattern: {pattern}")
            self.pattern_edit.setText(pattern)
        
        # Load custom options safely
        custom_options = pattern_data.get('custom_options', [])
        if custom_options:
            print(f"DEBUG: Loading existing custom options: {custom_options}")
            # Handle both old format (list) and new format (dict)
            if isinstance(custom_options, dict):
                # New format - each placeholder has its own options
                for placeholder, options in custom_options.items():
                    if placeholder in self.custom_option_editors:
                        editor = self.custom_option_editors[placeholder]
                        if isinstance(options, list):
                            editor.setPlainText('\n'.join(options))
            elif isinstance(custom_options, list):
                # Old format - single list of options, apply to first editor if available
                if self.custom_option_editors:
                    first_editor = next(iter(self.custom_option_editors.values()))
                    first_editor.setPlainText('\n'.join(custom_options))
        
        # Load other settings safely
        self._load_format_settings(pattern_data)
        self._load_sequence_settings(pattern_data)
        self._load_separator_settings(pattern_data)
        
        # Update preview to show loaded data
        try:
            self.update_preview()
        except Exception as e:
            print(f"DEBUG: Error updating preview after loading data: {e}")
        
        print(f"DEBUG: Successfully loaded pattern data from item")
    
    def _load_format_settings(self, pattern_data):
        """Load date/time format settings safely"""
        try:
            # Load date format preference
            date_format = pattern_data.get('date_format', '')
            if date_format and hasattr(self, 'date_format_combo'):
                index = self.date_format_combo.findText(date_format)
                if index >= 0:
                    self.date_format_combo.setCurrentIndex(index)
            
            # Load time format preference
            time_format = pattern_data.get('time_format', '')
            if time_format and hasattr(self, 'time_format_combo'):
                index = self.time_format_combo.findText(time_format)
                if index >= 0:
                    self.time_format_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"DEBUG: Error loading format settings: {e}")
    
    def _load_sequence_settings(self, pattern_data):
        """Load sequence settings safely"""
        try:
            sequence = pattern_data.get('sequence', {})
            if self.is_folder and hasattr(self, 'seq_start') and sequence:
                self.seq_start.setValue(sequence.get('start', 1))
                self.seq_count.setValue(sequence.get('count', 5))
                self.seq_padding.setValue(sequence.get('padding', 3))
        except Exception as e:
            print(f"DEBUG: Error loading sequence settings: {e}")
    
    def _load_separator_settings(self, pattern_data):
        """Load separator settings safely"""
        try:
            separator_choice = pattern_data.get('separator_choice', '_ (underscore)')
            custom_separator = pattern_data.get('custom_separator', '')
            
            if separator_choice and hasattr(self, 'separator_combo'):
                index = self.separator_combo.findText(separator_choice)
                if index >= 0:
                    self.separator_combo.setCurrentIndex(index)
                    if (separator_choice == "Custom..." and 
                        custom_separator and 
                        hasattr(self, 'custom_separator_edit')):
                        self.custom_separator_edit.setText(custom_separator)
                        self.custom_separator_edit.setVisible(True)
        except Exception as e:
            print(f"DEBUG: Error loading separator settings: {e}")


class VersioningDialog(QDialog):
    """Dialog for configuring file versioning"""
    
    def __init__(self, parent, item):
        super().__init__(parent)
        self.item = item
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE
        self.setWindowTitle("Configure Versioning")
        self.setMinimumSize(500, 500)
        self.resize(600, 600)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg']};
                color: {colors['text']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("File Versioning Configuration")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Versioning format
        format_label = QLabel("Version Format:")
        format_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        format_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-bottom: 5px;
        """)
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
        self.format_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px 30px 8px 12px;
                font-size: 14px;
                min-height: 20px;
            }}
            QComboBox:focus {{
                border: 2px solid {colors['accent']};
            }}
            QComboBox:hover {{
                border: 2px solid {colors['accent_hover']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border: none;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: {colors['card_bg_alt']};
            }}
            QComboBox::drop-down:hover {{
                background-color: {colors['accent']};
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
                background: transparent;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {colors['text']};
                margin-top: 2px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                selection-background-color: {colors['accent']};
                selection-color: {colors['text']};
                outline: none;
            }}
        """)
        layout.addWidget(self.format_combo)
        
        # Starting number
        start_label = QLabel("Starting Number:")
        start_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        start_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-top: 10px;
            margin-bottom: 5px;
        """)
        layout.addWidget(start_label)
        
        self.start_spin = QSpinBox()
        self.start_spin.setMinimum(1)
        self.start_spin.setMaximum(999)
        self.start_spin.setValue(1)
        self.start_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
            QSpinBox:focus {{
                border: 2px solid {colors['accent']};
            }}
        """)
        layout.addWidget(self.start_spin)
        
        # Number of versions
        count_label = QLabel("Number of Versions to Generate:")
        count_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        count_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-top: 10px;
            margin-bottom: 5px;
        """)
        layout.addWidget(count_label)
        
        self.count_spin = QSpinBox()
        self.count_spin.setMinimum(1)
        self.count_spin.setMaximum(50)
        self.count_spin.setValue(5)
        self.count_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
            QSpinBox:focus {{
                border: 2px solid {colors['accent']};
            }}
        """)
        layout.addWidget(self.count_spin)
        
        # Preview
        preview_label = QLabel("Preview:")
        preview_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        preview_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-top: 10px;
            margin-bottom: 5px;
        """)
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(120)
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 12px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.preview_text)
        
        # Connect signals
        self.format_combo.currentTextChanged.connect(self.update_preview)
        self.start_spin.valueChanged.connect(self.update_preview)
        self.count_spin.valueChanged.connect(self.update_preview)
        
        # Initial preview
        self.update_preview()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()  # Push buttons to the right
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet(BUTTON_STYLE)
        cancel_button.setMinimumSize(100, 35)
        button_layout.addWidget(cancel_button)
        
        apply_button = QPushButton("Apply Versioning")
        apply_button.clicked.connect(self.accept)
        apply_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        apply_button.setMinimumSize(150, 35)
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
        from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE
        self.setWindowTitle("Date Sequence Configuration")
        self.setMinimumSize(500, 600)
        self.resize(600, 700)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg']};
                color: {colors['text']};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Date Sequence Configuration")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Date format
        format_label = QLabel("Date Format:")
        format_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        format_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-bottom: 5px;
        """)
        layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "YYYY_MM_DD",
            "YYYYMMDD", 
            "MM_DD_YYYY",
            "DD_MM_YYYY",
            "YYYY-MM-DD",
            "MM-DD-YYYY",
            "DD-MM-YYYY",
            "YYYY.MM.DD",
            "MM.DD.YYYY",
            "DD.MM.YYYY",
            "YYYY MM DD",
            "MM DD YYYY",
            "DD MM YYYY"
        ])
        self.format_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px 30px 8px 12px;
                font-size: 14px;
                min-height: 20px;
            }}
            QComboBox:focus {{
                border: 2px solid {colors['accent']};
            }}
            QComboBox:hover {{
                border: 2px solid {colors['accent_hover']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border: none;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: {colors['card_bg_alt']};
            }}
            QComboBox::drop-down:hover {{
                background-color: {colors['accent']};
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
                background: transparent;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {colors['text']};
                margin-top: 2px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                selection-background-color: {colors['accent']};
                selection-color: {colors['text']};
                outline: none;
            }}
        """)
        layout.addWidget(self.format_combo)
        
        # Date range
        range_label = QLabel("Date Range:")
        range_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        range_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-top: 10px;
            margin-bottom: 5px;
        """)
        layout.addWidget(range_label)
        
        range_layout = QHBoxLayout()
        range_layout.setSpacing(15)
        
        start_label = QLabel("Start Date:")
        start_label.setStyleSheet(f"color: {colors['text']};")
        range_layout.addWidget(start_label)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.setStyleSheet(f"""
            QDateEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
            QDateEdit:focus {{
                border: 2px solid {colors['accent']};
            }}
        """)
        range_layout.addWidget(self.start_date)
        
        end_label = QLabel("End Date:")
        end_label.setStyleSheet(f"color: {colors['text']};")
        range_layout.addWidget(end_label)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate().addDays(7))
        self.end_date.setCalendarPopup(True)
        self.end_date.setStyleSheet(f"""
            QDateEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
            QDateEdit:focus {{
                border: 2px solid {colors['accent']};
            }}
        """)
        range_layout.addWidget(self.end_date)
        
        layout.addLayout(range_layout)
        
        # Interval
        interval_header = QLabel("Interval:")
        interval_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        interval_header.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-top: 10px;
            margin-bottom: 5px;
        """)
        layout.addWidget(interval_header)
        
        interval_layout = QHBoxLayout()
        interval_layout.setSpacing(15)
        
        interval_label = QLabel("Every:")
        interval_label.setStyleSheet(f"color: {colors['text']};")
        interval_layout.addWidget(interval_label)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setMaximum(365)
        self.interval_spin.setValue(1)
        self.interval_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
            QSpinBox:focus {{
                border: 2px solid {colors['accent']};
            }}
        """)
        interval_layout.addWidget(self.interval_spin)
        
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["Days", "Weeks", "Months"])
        self.interval_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px 30px 8px 12px;
                font-size: 14px;
                min-height: 20px;
            }}
            QComboBox:focus {{
                border: 2px solid {colors['accent']};
            }}
            QComboBox:hover {{
                border: 2px solid {colors['accent_hover']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border: none;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: {colors['card_bg_alt']};
            }}
            QComboBox::drop-down:hover {{
                background-color: {colors['accent']};
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
                background: transparent;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {colors['text']};
                margin-top: 2px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                selection-background-color: {colors['accent']};
                selection-color: {colors['text']};
                outline: none;
            }}
        """)
        interval_layout.addWidget(self.interval_combo)
        
        layout.addLayout(interval_layout)
        
        # Date/Time placement options
        placement_header = QLabel("Date/Time Placement:")
        placement_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        placement_header.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-top: 10px;
            margin-bottom: 5px;
        """)
        layout.addWidget(placement_header)
        
        placement_help = QLabel("Choose where to place date/time relative to PROJECT_NAME:")
        placement_help.setStyleSheet(f"color: {colors['secondary_text']};")
        layout.addWidget(placement_help)
        
        from PyQt6.QtWidgets import QRadioButton, QButtonGroup
        self.datetime_button_group = QButtonGroup()
        
        self.datetime_prefix_radio = QRadioButton("Before PROJECT_NAME (e.g., 20240115_MyProject)")
        self.datetime_suffix_radio = QRadioButton("After PROJECT_NAME (e.g., MyProject_20240115)")
        self.datetime_suffix_radio.setChecked(True)  # Default to suffix
        
        self.datetime_button_group.addButton(self.datetime_prefix_radio, 0)
        self.datetime_button_group.addButton(self.datetime_suffix_radio, 1)
        
        self.datetime_prefix_radio.toggled.connect(self.update_preview)
        self.datetime_suffix_radio.toggled.connect(self.update_preview)
        
        placement_layout = QVBoxLayout()
        placement_layout.addWidget(self.datetime_prefix_radio)
        placement_layout.addWidget(self.datetime_suffix_radio)
        layout.addLayout(placement_layout)
        
        # Preview
        preview_label = QLabel("Preview (first 10 dates):")
        preview_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        preview_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin-top: 10px;
            margin-bottom: 5px;
        """)
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 12px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }}
        """)
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
        button_layout.setSpacing(10)
        button_layout.addStretch()  # Push buttons to the right
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet(BUTTON_STYLE)
        cancel_button.setMinimumSize(100, 35)
        button_layout.addWidget(cancel_button)
        
        apply_button = QPushButton("Apply Date Sequence")
        apply_button.clicked.connect(self.accept)
        apply_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        apply_button.setMinimumSize(150, 35)
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
                if format_text == "YYYY_MM_DD":
                    date_str = current_date.strftime("%Y_%m_%d")
                elif format_text == "YYYYMMDD":
                    date_str = current_date.strftime("%Y%m%d")
                elif format_text == "MM_DD_YYYY":
                    date_str = current_date.strftime("%m_%d_%Y")
                elif format_text == "DD_MM_YYYY":
                    date_str = current_date.strftime("%d_%m_%Y")
                elif format_text == "YYYY-MM-DD":
                    date_str = current_date.strftime("%Y-%m-%d")
                elif format_text == "MM-DD-YYYY":
                    date_str = current_date.strftime("%m-%d-%Y")
                elif format_text == "DD-MM-YYYY":
                    date_str = current_date.strftime("%d-%m-%Y")
                elif format_text == "YYYY.MM.DD":
                    date_str = current_date.strftime("%Y.%m.%d")
                elif format_text == "MM.DD.YYYY":
                    date_str = current_date.strftime("%m.%d.%Y")
                elif format_text == "DD.MM.YYYY":
                    date_str = current_date.strftime("%d.%m.%Y")
                elif format_text == "YYYY MM DD":
                    date_str = current_date.strftime("%Y %m %d")
                elif format_text == "MM DD YYYY":
                    date_str = current_date.strftime("%m %d %Y")
                elif format_text == "DD MM YYYY":
                    date_str = current_date.strftime("%d %m %Y")
                else:
                    date_str = current_date.strftime("%Y_%m_%d")  # Default to underscore
                
                # Create example filename with placement logic
                datetime_prefix = hasattr(self, 'datetime_prefix_radio') and self.datetime_prefix_radio.isChecked()
                
                if datetime_prefix:
                    example_filename = f"{date_str}_{base_name}{extension}"
                else:
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
            'datetime_prefix': hasattr(self, 'datetime_prefix_radio') and self.datetime_prefix_radio.isChecked(),
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
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg']};
                color: {colors['text']};
            }}
            QLabel {{
                color: {colors['text']};
            }}
            QLineEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {colors['accent']};
            }}
            QComboBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px 30px 8px 12px;
                font-size: 14px;
                min-height: 20px;
            }}
            QComboBox:focus {{
                border: 2px solid {colors['accent']};
            }}
            QComboBox:hover {{
                border: 2px solid {colors['accent_hover']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border: none;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: {colors['card_bg_alt']};
            }}
            QComboBox::drop-down:hover {{
                background-color: {colors['accent']};
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
                background: transparent;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {colors['text']};
                margin-top: 2px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                selection-background-color: {colors['accent']};
                selection-color: {colors['text']};
                outline: none;
            }}
            QPushButton {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {colors['accent']};
                border: 2px solid {colors['accent']};
            }}
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
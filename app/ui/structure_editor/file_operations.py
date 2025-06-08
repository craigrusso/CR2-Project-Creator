#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
File Operations Module for Structure Editor
Handles file and folder operations for the structure
"""

import os
import mimetypes
import random
import string
import json
from PyQt6.QtWidgets import (
    QTreeWidgetItem, QInputDialog, QMessageBox, QMenu,
    QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QCheckBox, QApplication, QStyle,
    QListWidget, QListWidgetItem, QScrollArea, QFrame, QWidget
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon, QDrag, QBrush, QColor, QCursor, QAction

from .utils import get_file_icon_for_type

# Import binary file handler
try:
    from app.utils.binary_file_handler import BinaryFileHandler
except ImportError:
    # Simple fallback implementation
    class BinaryFileHandler:
        @staticmethod
        def is_binary_file(file_path):
            # Very basic check
            if not os.path.exists(file_path):
                return False
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            binary_extensions = ['.jpg', '.png', '.gif', '.mp3', '.mp4', '.pdf']
            return ext in binary_extensions
        
        @staticmethod
        def should_embed_binary_file(file_path, max_size_kb=500):
            if not os.path.exists(file_path):
                return False
            return os.path.getsize(file_path) / 1024 <= max_size_kb

# Define file extensions (copied from the original file_types.py)
FILE_EXTENSIONS = {
    'Image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'],
    'Audio': ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'],
    'Video': ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'],
    'Archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
}

FILE_CATEGORIES = {
    'Image': 'Images',
    'Audio': 'Audio',
    'Video': 'Video',
    'Archive': 'Archives',
    'Document': 'Documents',
    'Code': 'Code',
    'Data': 'Data'
}

COMMON_EXTENSIONS = {
    '.jpg': 'Image', 
    '.jpeg': 'Image',
    '.png': 'Image',
    '.mp3': 'Audio',
    '.wav': 'Audio',
    '.mp4': 'Video',
    '.avi': 'Video',
    '.zip': 'Archive',
    '.rar': 'Archive',
    '.txt': 'Text',
    '.md': 'Markdown',
    '.html': 'HTML',
    '.css': 'CSS',
    '.js': 'JavaScript',
    '.py': 'Python',
    '.json': 'JSON',
    '.xml': 'XML'
}

class FileOperations:
    """
    Handles file and folder operations for the structure editor
    
    This class provides methods for adding, removing, and organizing files
    and folders in the structure tree.
    """
    
    def __init__(self, tree_widget=None, editor=None):
        """
        Initialize the file operations
        
        Args:
            tree_widget: Reference to the tree widget (QTreeWidget)
            editor: Reference to the parent editor (optional)
        """
        self.editor = editor
        self.tree = tree_widget
        self.cached_files = {}
        
        # Store reference to cached files if available
        if editor and hasattr(editor, 'files_to_cache'):
            self.cached_files = editor.files_to_cache
    
    def add_file(self, parent_item=None, file_name=None, file_type=None):
        """
        Add a file or files to the structure tree
        
        Args:
            parent_item: Parent tree item to add the file to
            file_name: Name of the file (optional)
            file_type: Type of file (optional)
        
        Returns:
            QTreeWidgetItem or list of QTreeWidgetItems: The created file item(s)
        """
        print(f"🔹 ADD_FILE: Called with parent_item={parent_item}, file_name={file_name}, file_type={file_type}")
        
        # Get reference to the tree widget
        if not hasattr(self, 'tree'):
            if hasattr(self.editor, 'tree'):
                self.tree = self.editor.tree
            elif hasattr(self.editor, 'structure_tree'):
                self.tree = self.editor.structure_tree
            
        if not self.tree:
            print("ERROR: No tree widget available for file operations")
            return None
    
        # If parent is not specified, use root item
        if not parent_item:
            if self.tree.topLevelItemCount() > 0:
                parent_item = self.tree.topLevelItem(0)
                print(f"🔹 ADD_FILE: Using first top level item as parent: {parent_item.text(0)}")
            else:
                parent_item = QTreeWidgetItem(self.tree)
                parent_item.setText(0, "Project Root")
                parent_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "name": "Project Root"})
                print(f"🔹 ADD_FILE: Created new root item as parent: Project Root")
    
        # If file_name is a list or tuple, add multiple files
        if isinstance(file_name, (list, tuple)):
            print(f"🔹 ADD_FILE: Adding multiple files: {file_name}")
            added_items = []
            for name in file_name:
                added_item = self._add_file_item(parent_item, name, file_type)
                if added_item:
                    added_items.append(added_item)
            return added_items
    
        # If file_name is not specified, show file browser
        if not file_name:
            file_path, _ = QFileDialog.getOpenFileName(
                self.editor, 
                "Select File", 
                "", 
                "All Files (*.*)"
            )
            
            if not file_path:
                print("🔹 ADD_FILE: User cancelled file selection")
                return None
            
            # Get file name from path
            file_name = os.path.basename(file_path)
            print(f"🔹 ADD_FILE: User selected file: {file_path}, using name: {file_name}")
            
            # Add file with original path
            file_item = self._add_file_item(parent_item, file_name)
            
            # Store file information for caching but don't cache yet
            # (Caching will happen when template is saved)
            try:
                # Get file data from the tree item
                file_data = file_item.data(0, Qt.ItemDataRole.UserRole)
                
                # Set original path
                file_data['path'] = file_path
                file_data['original_path'] = file_path
                
                # Determine if binary
                from app.utils.binary_file_handler import BinaryFileHandler
                is_binary = BinaryFileHandler.is_binary_file(file_path)
                file_data['is_binary'] = is_binary
                
                # Get template name from the editor if available
                template_name = "Unknown Template"
                if hasattr(self.editor, 'template_name'):
                    template_name = self.editor.template_name
                elif hasattr(self.editor, 'name_input') and hasattr(self.editor.name_input, 'text'):
                    template_name = self.editor.name_input.text()
                
                # Get relative path in the tree structure for later use
                relative_path = self._get_relative_path(file_item)
                file_data['relative_path'] = relative_path
                file_data['template_name'] = template_name
                
                print(f"🔹 ADD_FILE: Created file data: {file_data}")
                
                # Update file data in the tree item
                file_item.setData(0, Qt.ItemDataRole.UserRole, file_data)
                
                # Store reference to the file in the editor's cache tracking if available
                if hasattr(self.editor, 'files_to_cache'):
                    self.editor.files_to_cache[relative_path] = {
                        "original_path": file_path,
                        "relative_path": relative_path,
                        "template_name": template_name
                    }
                    print(f"🔹 ADD_FILE: Added to files_to_cache with key {relative_path}")
                else:
                    print("🔹 ADD_FILE: Warning - editor does not have files_to_cache attribute")
                    
                # Add visual indicator that file is tracked but not yet cached
                from PyQt6.QtGui import QBrush, QColor
                colors = self._get_editor_colors()
                file_item.setForeground(0, QBrush(QColor(colors.get('tracked', '#88AADD'))))
                
            except Exception as e:
                print(f"Error preparing file for caching: {e}")
            
            return file_item
        
        # If file name is provided, just add a single file
        print(f"🔹 ADD_FILE: Adding single file with name: {file_name}")
        return self._add_file_item(parent_item, file_name, file_type)
    
    def _add_file_item(self, parent_item, file_name, file_type=None, original_path=None):
        """
        Add a file item to the structure tree with appropriate icon and data
        
        Args:
            parent_item: Parent tree item
            file_name: Name of the file
            file_type: Type of file (optional)
            original_path: Original path of the file (optional)
        
        Returns:
            QTreeWidgetItem: The created file item
        """
        print(f"🔹 _ADD_FILE_ITEM: Called with parent={parent_item.text(0) if parent_item else 'None'}, file_name={file_name}")
        
        # Ensure tree widget reference is available
        if not self.tree:
            print("🔹 _ADD_FILE_ITEM: No tree widget available")
            return None
            
        # Create file item
        file_item = QTreeWidgetItem(parent_item)
        file_item.setText(0, file_name)
        file_item.setFlags(file_item.flags() | Qt.ItemFlag.ItemIsEditable)
        
        # Determine file type based on extension if not provided
        if not file_type:
            _, ext = os.path.splitext(file_name.lower())
            # Match extension to known file types
            for category, extensions in FILE_EXTENSIONS.items():
                if ext in extensions:
                    file_type = category
                    break
            if not file_type:
                # Use more comprehensive mapping
                file_type = COMMON_EXTENSIONS.get(ext, "Unknown")
        
        # Create item data with file type
        item_data = {
            "type": "file",
            "name": file_name,
            "file_type": file_type,
            "original_path": original_path
        }
        
        # Set item data
        file_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Set appropriate icon based on file type - use icon_utilities for consistency
        try:
            from app.ui.icon_utilities import get_file_icon
            icon = get_file_icon(file_name)
            file_item.setIcon(0, icon)
        except ImportError:
            # Fallback to local icon function if import fails
            icon = get_file_icon_for_type(file_type, file_name)
            file_item.setIcon(0, icon)
        
        print(f"🔹 _ADD_FILE_ITEM: Added file item {file_name} with type {file_type}")
        return file_item
    
    def add_folder(self, parent_item=None, folder_name=None):
        """
        Add a folder to the structure tree
        
        Args:
            parent_item: Parent tree item to add the folder to
            folder_name: Name of the folder (optional)
        
        Returns:
            QTreeWidgetItem: The created folder item
        """
        print(f"🔹 ADD_FOLDER: Called with parent_item={parent_item}, folder_name={folder_name}")
        
        # Get reference to the tree widget
        if not hasattr(self, 'tree'):
            if hasattr(self.editor, 'tree'):
                self.tree = self.editor.tree
            elif hasattr(self.editor, 'structure_tree'):
                self.tree = self.editor.structure_tree
                
        if not self.tree:
            print("ERROR: No tree widget available for file operations")
            return None
        
        # If parent is not specified, use root item
        if not parent_item:
            if self.tree.topLevelItemCount() > 0:
                parent_item = self.tree.topLevelItem(0)
                print(f"🔹 ADD_FOLDER: Using first top level item as parent: {parent_item.text(0)}")
            else:
                parent_item = QTreeWidgetItem(self.tree)
                parent_item.setText(0, "Project Root")
                parent_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "name": "Project Root"})
                print(f"🔹 ADD_FOLDER: Created new root item as parent: Project Root")
        
        # If folder_name is not specified, show input dialog
        if not folder_name:
            # Get folder name from user
            folder_name, ok = QInputDialog.getText(
                self.tree, "New Folder", "Enter folder name:", 
                text="New Folder"
            )
            
            if not ok or not folder_name:
                print("🔹 ADD_FOLDER: User cancelled folder creation")
                return None
        
        # Create folder item
        folder_item = QTreeWidgetItem(parent_item)
        folder_item.setText(0, folder_name)
        folder_item.setFlags(folder_item.flags() | Qt.ItemFlag.ItemIsEditable)
        
        # Set folder data
        folder_data = {
            "type": "folder",
            "name": folder_name
        }
        folder_item.setData(0, Qt.ItemDataRole.UserRole, folder_data)
        
        # Set folder icon - use icon_utilities for Windows folder icons
        try:
            from app.ui.icon_utilities import get_folder_icon
            icon = get_folder_icon(False)  # False = folder is closed initially
            folder_item.setIcon(0, icon)
        except ImportError:
            # Fallback to standard icon if import fails
            folder_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
            folder_item.setIcon(0, folder_icon)
        
        print(f"🔹 ADD_FOLDER: Added folder item: {folder_name}")
        
        # Make the new folder visible
        self.tree.scrollToItem(folder_item)
        
        return folder_item
    
    def delete_selected(self):
        """
        Delete selected items from the structure
        
        Returns:
            bool: True if items were deleted, False otherwise
        """
        try:
            if not self.tree:
                print("DEBUG: delete_selected - tree widget not available")
                return False
            
            # Get selected items
            selected_items = self.tree.selectedItems()
            if not selected_items:
                print("DEBUG: delete_selected - no items selected")
                return False
            
            # Confirm deletion
            count = len(selected_items)
            print(f"DEBUG: delete_selected - {count} items selected for deletion")
            confirm_msg = f"Delete {count} selected item{'s' if count > 1 else ''}?"
            confirm_title = "Confirm Delete"
            
            # Add details about what's being deleted
            if count == 1:
                item = selected_items[0]
                item_data = item.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(item_data, dict):
                    item_type = item_data.get('type', 'item')
                    item_name = item.text(0)
                    confirm_msg = f"Delete {item_type} '{item_name}'?"
            
            # Show confirmation dialog
            reply = QMessageBox.question(
                self.editor, 
                confirm_title,
                confirm_msg, 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                print("DEBUG: delete_selected - user cancelled deletion")
                return False
            
            # Delete items
            deleted_count = 0
            root = self.tree.invisibleRootItem()
            
            for item in selected_items:
                try:
                    # Get the parent of the item
                    parent = item.parent()
                    
                    if parent:
                        # Handle child items (non-top-level)
                        print(f"DEBUG: delete_selected - removing child item '{item.text(0)}' from parent '{parent.text(0)}'")
                        index = parent.indexOfChild(item)
                        if index >= 0:
                            parent.takeChild(index)
                            deleted_count += 1
                            print(f"DEBUG: delete_selected - child item removed successfully")
                        else:
                            print(f"ERROR: delete_selected - failed to find index of child item")
                    else:
                        # Handle top-level items
                        print(f"DEBUG: delete_selected - removing top-level item '{item.text(0)}'")
                        index = root.indexOfChild(item)
                        if index >= 0:
                            root.takeChild(index)
                            deleted_count += 1
                            print(f"DEBUG: delete_selected - top-level item removed successfully")
                        else:
                            print(f"ERROR: delete_selected - failed to find index of top-level item")
                except Exception as item_ex:
                    print(f"ERROR: Exception deleting individual item: {item_ex}")
                    import traceback
                    traceback.print_exc()
            
            # Refresh the tree view
            if deleted_count > 0:
                self.tree.update()
                print(f"DEBUG: delete_selected - {deleted_count} items deleted successfully")
                return True
            else:
                print(f"DEBUG: delete_selected - no items were deleted")
                return False
        except Exception as e:
            print(f"ERROR: Exception in delete_selected: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def rename_item(self, item):
        """
        Rename an item
        
        Args:
            item: The item to rename
            
        Returns:
            bool: True if renamed, False otherwise
        """
        if not item:
            print("ERROR: rename_item - no item provided")
            return False
            
        # Make sure the item is editable
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            
        try:
            # Try in-place editing first
            self.tree.editItem(item, 0)
            
            # Setup timer to check if edit was successful
            # This is needed because editItem is asynchronous
            def check_edit_status():
                # If editor is not visible, the edit may have failed
                if not self.tree.isPersistentEditorOpen(item, 0) and not self.tree.itemWidget(item, 0):
                    print("edit: editing failed")
                    # Use dialog fallback
                    self._rename_with_dialog(item)
            
            # Check status after a short delay
            QTimer.singleShot(200, check_edit_status)
            
            return True
            
        except Exception as e:
            print(f"edit: editing failed with error: {e}")
            # Use dialog fallback
            return self._rename_with_dialog(item)
    
    def _rename_with_dialog(self, item):
        """Fallback for renaming using a dialog"""
        if not item:
            return False
            
        # Get current item name and type
        current_name = item.text(0)
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        item_type = item_data.get('type', 'item') if isinstance(item_data, dict) else 'item'
        
        # Show dialog to get new name
        new_name, ok = QInputDialog.getText(
            self.tree,
            f"Rename {item_type.capitalize()}",
            f"Enter new name for {item_type}:",
            text=current_name
        )
        
        if not ok or not new_name or new_name == current_name:
            return False
            
        # Update item name
        item.setText(0, new_name)
        
        # Update item data
        if isinstance(item_data, dict):
            item_data['name'] = new_name
            item.setData(0, Qt.ItemDataRole.UserRole, item_data)
            
        return True
    
    def import_directory(self, target_item=None):
        """
        Import a directory from the file system
        
        Args:
            target_item: Item to import into (optional)
            
        Returns:
            bool: True if imported, False otherwise
        """
        if not self.tree:
            return False
            
        # Get directory path
        dir_path = QFileDialog.getExistingDirectory(
            self.editor,
            "Select Directory to Import",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not dir_path:
            return False  # User canceled
            
        # If no target specified, use selected item or root
        if not target_item:
            selected_items = self.tree.selectedItems()
            if selected_items:
                target_item = selected_items[0]
                
                # If selected item is a file, use its parent
                item_data = target_item.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(item_data, dict) and item_data.get('type') == 'file':
                    if target_item.parent():
                        target_item = target_item.parent()
                    else:
                        target_item = self.tree.invisibleRootItem()
            else:
                # Use root item
                target_item = self.tree.invisibleRootItem()
        
        # Import the directory
        try:
            # Get directory name from path
            dir_name = os.path.basename(dir_path)
            
            # Create folder item
            folder_item = self.add_folder(target_item, dir_name)
            
            # Import contents
            self._import_directory_contents(dir_path, folder_item)
            
            return True
        except Exception as e:
            QMessageBox.critical(
                self.editor,
                "Import Error",
                f"Error importing directory: {str(e)}"
            )
            return False
    
    def _import_directory_contents(self, dir_path, parent_item):
        """
        Import contents of a directory recursively
        
        Args:
            dir_path: Path to the directory
            parent_item: Parent item to add contents to
        """
        # List all files and subdirectories
        for item_name in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item_name)
            
            # Skip hidden files (like .DS_Store)
            if item_name.startswith('.'):
                continue
                
            if os.path.isdir(item_path):
                # Create subdirectory
                folder_item = self.add_folder(parent_item, item_name)
                
                # Use system folder icon directly
                folder_icon = QIcon.fromTheme("folder", QIcon("icons/folder.png"))
                if not folder_icon.isNull():
                    folder_item.setIcon(0, folder_icon)
                
                # Import contents recursively
                self._import_directory_contents(item_path, folder_item)
            else:
                # Add file
                file_item = self._add_file_item(parent_item, item_name)
                
                # Use system file icon directly
                file_icon = QIcon.fromTheme("document", QIcon("icons/file.png"))
                if not file_icon.isNull():
                    file_item.setIcon(0, file_icon)
                
                # If it's a binary file, cache it
                if self.is_binary_file(item_name):
                    try:
                        with open(item_path, 'rb') as f:
                            content = f.read()
                            cache_key = f"{item_name}_{id(file_item)}"
                            self.cached_files[cache_key] = content
                            
                            # Update file data
                            file_data = file_item.data(0, Qt.ItemDataRole.UserRole)
                            file_data['cached'] = True
                            file_data['cache_key'] = cache_key
                            file_item.setData(0, Qt.ItemDataRole.UserRole, file_data)
                    except Exception as e:
                        print(f"DEBUG: Failed to cache binary file: {e}")
    
    def import_file(self, target_item=None):
        """
        Import a file from the file system
        
        Args:
            target_item: Target tree item to add the file to (optional)
            
        Returns:
            QTreeWidgetItem: The created file item or None if canceled
        """
        # Open file dialog to select file
        file_path, _ = QFileDialog.getOpenFileName(
            self.editor, 
            "Import File", 
            "", 
            "All Files (*.*)"
        )
        
        if not file_path:
            return None
        
        # Use target item or get selected item
        if not target_item:
            selected_items = self.tree.selectedItems()
            if selected_items:
                target_item = selected_items[0]
            else:
                # Use root item
                if self.tree.topLevelItemCount() > 0:
                    target_item = self.tree.topLevelItem(0)
                else:
                    # Create root item if not exists
                    target_item = QTreeWidgetItem(self.tree)
                    target_item.setText(0, "Project Root")
                    target_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "name": "Project Root"})
        
        # Import the file
        try:
            # Get file name from path
            file_name = os.path.basename(file_path)
            
            # Add file with original path
            file_item = self._add_file_item(target_item, file_name, original_path=file_path)
            
            # Store file information for caching but don't cache yet
            # (Caching will happen when template is saved)
            try:
                # Get file data from the tree item
                file_data = file_item.data(0, Qt.ItemDataRole.UserRole)
                
                # Set original path
                file_data['path'] = file_path
                file_data['original_path'] = file_path
                
                # Determine if binary
                from app.utils.binary_file_handler import BinaryFileHandler
                is_binary = BinaryFileHandler.is_binary_file(file_path)
                file_data['is_binary'] = is_binary
                
                # Get template name from the editor if available
                template_name = "Unknown Template"
                if hasattr(self.editor, 'template_name'):
                    template_name = self.editor.template_name
                elif hasattr(self.editor, 'name_input') and hasattr(self.editor.name_input, 'text'):
                    template_name = self.editor.name_input.text()
                
                # Get relative path in the tree structure for later use  
                relative_path = self._get_relative_path(file_item)
                file_data['relative_path'] = relative_path
                file_data['template_name'] = template_name
                
                # Update file data in the tree item
                file_item.setData(0, Qt.ItemDataRole.UserRole, file_data)
                
                # Store reference to the file in the editor's cache tracking if available
                if hasattr(self.editor, 'files_to_cache'):
                    self.editor.files_to_cache[relative_path] = {
                        "original_path": file_path,
                        "relative_path": relative_path,
                        "template_name": template_name
                    }
                    
                # Add visual indicator that file is tracked but not yet cached
                from PyQt6.QtGui import QBrush, QColor
                colors = self._get_editor_colors()
                file_item.setForeground(0, QBrush(QColor(colors.get('tracked', '#88AADD'))))
                
            except Exception as e:
                print(f"Error preparing file for caching: {e}")
                
            return file_item
            
        except Exception as e:
            print(f"Error importing file: {e}")
            return None
    
    def is_binary_file(self, file_path):
        """
        Check if a file is binary based on extension
        
        Args:
            file_path: Path to the file or just the filename
            
        Returns:
            bool: True if binary, False otherwise
        """
        # Use BinaryFileHandler if available
        return BinaryFileHandler.is_binary_file(file_path)
    
    def create_context_menu(self, item, position=None):
        """Create and return a context menu for the given item"""
        print("DEBUG: create_context_menu - creating context menu")
        
        if not self.tree:
            print("ERROR: create_context_menu - tree not available")
            return None
            
        # Create menu
        menu = QMenu(self.tree)
        
        # Apply styling
        try:
            from app.ui.color_scheme_pyqt import CONTEXT_MENU_STYLE
            menu.setStyleSheet(CONTEXT_MENU_STYLE)
        except Exception as e:
            print(f"ERROR: Failed to apply menu styling: {e}")
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
        
        # Process by item type
        if item:
            # Get item data
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(item_data, dict) and 'type' in item_data:
                item_type = item_data['type']
                print(f"DEBUG: create_context_menu - item type: {item_type}")
                
                # Add item-specific actions based on type
                if item_type == 'folder':
                    self._add_folder_context_actions(menu, item)
                elif item_type == 'file':
                    self._add_file_context_actions(menu, item)
                else:
                    # Unknown item type - add basic actions
                    self._add_generic_context_actions(menu, item)
            else:
                # Unknown item type - add basic actions
                self._add_generic_context_actions(menu, item)
        else:
            # Root context menu (no item selected)
            self._add_root_context_actions(menu)
            
        # Make sure all actions are properly added
        menu.ensurePolished()
        
        # Return the menu for display
        return menu

    def _add_file_context_actions(self, menu, item):
        """Add context menu actions for file items"""
        # Add "Add File" and "Add Folder" actions (to add sibling items)
        # These should operate on the parent of the current file item
        parent_for_add = item.parent() if item.parent() else self.tree.invisibleRootItem()

        add_file_action = menu.addAction("Add File")
        add_file_action.triggered.connect(lambda: self.add_file(parent_for_add))
        
        add_folder_action = menu.addAction("Add Folder")
        add_folder_action.triggered.connect(lambda: self.add_folder(parent_for_add))
        
        menu.addSeparator()
        
        # Add rename action
        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(lambda: self.rename_item(item))
        
        # Add delete action
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.delete_selected()) # Assumes delete_selected handles current item
        
        # Add keyboard shortcuts (optional, but good practice)
        # rename_action.setShortcut("F2")
        # delete_action.setShortcut("Delete")
        
        # Project Name Options submenu
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(item_data, dict) and item_data.get('type') == 'file': # Ensure it's a file
            menu.addSeparator()
            
            project_name_menu = menu.addMenu("Project Name Options")
            try:
                from app.ui.color_scheme_pyqt import CONTEXT_MENU_STYLE
                # --- Restoring custom styling for the submenu ---
                project_name_menu.setStyleSheet(CONTEXT_MENU_STYLE) 
            except Exception as e:
                print(f"ERROR: Failed to apply submenu styling: {e}")

            # Get project name mode and usage status from item data
            item_data = self._get_item_data(item)
            name_mode = item_data.get('project_name_mode', 'none') # none, replace, append, prepend
            uses_project_name = item_data.get('uses_project_name', False)
            original_name = item_data.get('original_name', item.text(0))
            
            # Only add these options if the item is renameable and it's a file (not a folder)
            if item.flags() & Qt.ItemFlag.ItemIsEditable and item_data.get('type') == 'file':
                # Action to use project name (replace current name)
                use_action = project_name_menu.addAction("Use Project Name")
                use_action.setCheckable(True)
                # Set checked based on the specific mode being active, or if uses_project_name is true and mode is none (legacy)
                use_action.setChecked(name_mode == 'replace' or (uses_project_name and name_mode == 'none'))
                use_action.triggered.connect(lambda checked, i=item: self._toggle_project_name_for_file(i, mode='replace', is_checked=checked))

                # Action to append project name
                append_action = project_name_menu.addAction("Append Project Name")
                append_action.setCheckable(True)
                append_action.setChecked(name_mode == 'append')
                append_action.triggered.connect(lambda checked, i=item: self._toggle_project_name_for_file(i, mode='append', is_checked=checked))

                # Action to prepend project name
                prepend_action = project_name_menu.addAction("Prepend Project Name")
                prepend_action.setCheckable(True)
                prepend_action.setChecked(name_mode == 'prepend')
                prepend_action.triggered.connect(lambda checked, i=item: self._toggle_project_name_for_file(i, mode='prepend', is_checked=checked))
                
                project_name_menu.addSeparator()

                # Add Custom Pattern and Custom Separator actions
                pattern_action = project_name_menu.addAction("Use Custom Pattern...")
                pattern_action.triggered.connect(
                    lambda checked=False, bound_item=item: (
                        print(f"DEBUG: Lambda for 'Use Custom Pattern...' triggered for item: {bound_item.text(0) if bound_item else 'None'}"),
                        self._configure_naming_pattern(bound_item)
                    )
                )

                separator_action = project_name_menu.addAction("Use Custom Separator...")
                separator_action.triggered.connect(
                    lambda checked=False, bound_item=item: (
                        print(f"DEBUG: Lambda for 'Use Custom Separator...' triggered for item: {bound_item.text(0) if bound_item else 'None'}"),
                        self._configure_custom_separator(bound_item)
                    )
                )

                project_name_menu.addSeparator() # Add another separator before Revert

                # Action to revert to original name
                revert_action = project_name_menu.addAction(f'Reset to "{original_name}"')
                # Enable only if current name differs from original due to project name usage
                revert_action.setEnabled(uses_project_name or name_mode != 'none') 
                revert_action.triggered.connect(lambda checked=False, bound_item=item: self._reset_file_name(bound_item))
            else:
                # If not editable or a folder, add a disabled placeholder
                disabled_action = project_name_menu.addAction("(Options N/A for folders)")
                disabled_action.setEnabled(False)
                
        # Add separator before other actions if project_name_menu was added
        if project_name_menu:
             menu.addSeparator()

    def _add_folder_context_actions(self, menu, item):
        """Add context menu actions for folder items"""
        # Add "Add Folder" and "Add File" actions
        add_folder_action = menu.addAction(QIcon.fromTheme("folder-new"), "Add Folder")
        add_folder_action.triggered.connect(lambda: self.add_folder(item))
        
        add_file_action = menu.addAction(QIcon.fromTheme("document-new"), "Add File")
        add_file_action.triggered.connect(lambda: self.add_file(item))
        
        # Add separator
        menu.addSeparator()
        
        # Add rename action
        rename_action = menu.addAction(QIcon.fromTheme("edit-rename"), "Rename")
        rename_action.triggered.connect(lambda: self.rename_item(item))
        
        # Add delete action
        delete_action = menu.addAction(QIcon.fromTheme("edit-delete"), "Delete")
        delete_action.triggered.connect(lambda: self.delete_selected())
        
        # Add keyboard shortcuts
        rename_action.setShortcut("F2")
        delete_action.setShortcut("Delete")
        
        # Add "Import File" and "Import Directory" actions
        import_menu = menu.addMenu("Import")
        import_file_action = import_menu.addAction(QIcon.fromTheme("document-import"), "Import File")
        import_dir_action = import_menu.addAction(QIcon.fromTheme("folder-import"), "Import Directory")
        
        # Connect actions
        import_file_action.triggered.connect(lambda: self.import_file(item))
        import_dir_action.triggered.connect(lambda: self.import_directory(item))

    def _add_generic_context_actions(self, menu, item):
        """Add context menu actions for generic items"""
        # Add "Add Folder" and "Add File" actions
        add_folder_action = menu.addAction("Add Folder")
        add_folder_action.triggered.connect(lambda: self.add_folder())
        
        add_file_action = menu.addAction("Add File")
        add_file_action.triggered.connect(lambda: self.add_file())
        
        # Add separator
        menu.addSeparator()
        
        # Add "Import Directory" action
        import_dir_action = menu.addAction("Import Directory...")
        import_dir_action.triggered.connect(lambda: self.import_directory())

    def _add_root_context_actions(self, menu):
        """Add context menu actions for the root item"""
        # Add "Add Folder" and "Add File" actions
        add_folder_action = menu.addAction("Add Folder")
        add_folder_action.triggered.connect(lambda: self.add_folder())
        
        add_file_action = menu.addAction("Add File")
        add_file_action.triggered.connect(lambda: self.add_file())
        
        # Add separator
        menu.addSeparator()
        
        # Add "Import Directory" action
        import_dir_action = menu.addAction("Import Directory...")
        import_dir_action.triggered.connect(lambda: self.import_directory())

    def _setup_context_menu(self):
        """Set up the context menu for the tree widget"""
        if not self.tree:
            return
        
        # Do NOT connect the context menu signal here - this is handled by the structure editor.
        # Only set the policy if needed.
        if self.tree.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
            self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        print("DEBUG: Context menu policy set (but not connecting the signal to avoid duplicates)")

    def _show_context_menu(self, position):
        """
        Show a context menu at the given position
        
        Args:
            position: Position to show the menu at
        """
        if not self.tree:
            return
        
        # Get the item at the position
        item = self.tree.itemAt(position)
        
        if item:
            # Get the item data
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            
            # Create menu based on item type
            if isinstance(item_data, dict) and item_data.get('type') == 'folder':
                self._show_folder_context_menu(item, position)
            else:
                self._show_file_context_menu(item, position)
        else:
            # Show the general context menu if no item is selected
            self._show_general_context_menu(position)

    def _show_general_context_menu(self, position):
        """
        Show a general context menu for the tree
        
        Args:
            position: Position to show the menu at
        """
        # Import main app colors
        from app.ui.color_scheme_pyqt import APP_COLORS, CONTEXT_MENU_STYLE
        
        # Create menu
        menu = QMenu(self.tree)
        menu.setStyleSheet(CONTEXT_MENU_STYLE)
        
        # Add actions
        add_folder_action = menu.addAction("Add Folder")
        add_file_action = menu.addAction("Add File")
        menu.addSeparator()
        import_dir_action = menu.addAction("Import Directory...")
        
        # Execute the menu
        action = menu.exec(self.tree.mapToGlobal(position))
        
        # Handle actions
        if action == add_folder_action:
            self.add_folder()
        elif action == add_file_action:
            self.add_file()
        elif action == import_dir_action:
            self.import_directory()

    def _show_folder_context_menu(self, item, position):
        """
        Show a context menu for folder items
        
        Args:
            item: The folder item
            position: Position to show the menu at
        """
        # Import main app colors
        from app.ui.color_scheme_pyqt import APP_COLORS, CONTEXT_MENU_STYLE
        
        # Create menu
        menu = QMenu(self.tree)
        menu.setStyleSheet(CONTEXT_MENU_STYLE)
        
        # Add actions
        add_folder_action = menu.addAction(QIcon.fromTheme("folder-new"), "Add Folder")
        add_file_action = menu.addAction(QIcon.fromTheme("document-new"), "Add File")
        menu.addSeparator()
        
        # Import actions
        import_menu = QMenu("Import", menu)
        import_menu.setStyleSheet(CONTEXT_MENU_STYLE)
        import_file_action = import_menu.addAction(QIcon.fromTheme("document-import"), "Import File")
        import_dir_action = import_menu.addAction(QIcon.fromTheme("folder-import"), "Import Directory")
        menu.addMenu(import_menu)
        
        menu.addSeparator()
        rename_action = menu.addAction(QIcon.fromTheme("edit-rename"), "Rename")
        delete_action = menu.addAction(QIcon.fromTheme("edit-delete"), "Delete")
        
        # Add keyboard shortcuts
        rename_action.setShortcut("F2")
        delete_action.setShortcut("Delete")
        
        # Execute the menu
        action = menu.exec(self.tree.mapToGlobal(position))
        
        # Handle actions
        if action == add_folder_action:
            self.add_folder(item)
        elif action == add_file_action:
            self.add_file(item)
        elif action == import_file_action:
            self.import_file(item)
        elif action == import_dir_action:
            self.import_directory(item)
        elif action == rename_action:
            self.rename_item(item)
        elif action == delete_action:
            self.delete_selected()

    def _show_file_context_menu(self, item, position):
        """
        Show a context menu for file items
        
        Args:
            item: The file item
            position: Position to show the menu at
        """
        # Import main app colors
        from app.ui.color_scheme_pyqt import APP_COLORS, CONTEXT_MENU_STYLE
        
        # Create menu
        menu = QMenu(self.tree)
        menu.setStyleSheet(CONTEXT_MENU_STYLE)
        
        # Add actions
        rename_action = menu.addAction(QIcon.fromTheme("edit-rename"), "Rename")
        menu.addSeparator()
        
        # Get item data
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(item_data, dict):
            item_data = {}
        
        # Create a submenu for project name options
        project_name_menu = menu.addMenu("Project Name Options")
        
        # Determine current state
        name_mode = item_data.get('project_name_mode', 'none')
        uses_project_name = item_data.get('uses_project_name', False)
        
        # Create project name actions
        replace_name_action = project_name_menu.addAction("Replace with Project Name")
        prepend_name_action = project_name_menu.addAction("Prepend Project Name")
        append_name_action = project_name_menu.addAction("Append Project Name")
        pattern_action = project_name_menu.addAction("Use Custom Pattern...")
        separator_action = project_name_menu.addAction("Use Custom Separator...")
        project_name_menu.addSeparator()
        reset_name_action = project_name_menu.addAction("Reset to Original Name")
        
        # Set checkable and check the current mode - but don't make them toggle
        replace_name_action.setCheckable(True)
        prepend_name_action.setCheckable(True)
        append_name_action.setCheckable(True)
        
        # Show which mode is currently active
        replace_name_action.setChecked(name_mode == 'replace')
        prepend_name_action.setChecked(name_mode == 'prepend')
        append_name_action.setChecked(name_mode == 'append')
        
        # Enable/disable reset based on whether a project name option is active
        reset_name_action.setEnabled(uses_project_name or name_mode != 'none')
        
        menu.addSeparator()
        delete_action = menu.addAction(QIcon.fromTheme("edit-delete"), "Delete")
        
        # Add keyboard shortcuts
        rename_action.setShortcut("F2")
        delete_action.setShortcut("Delete")
        
        # Execute the menu
        action = menu.exec(self.tree.mapToGlobal(position))
        
        # Handle actions - Always apply the selected mode, don't toggle
        if action == rename_action:
            self.rename_item(item)
        elif action == replace_name_action:
            # Always apply replace mode, regardless of current state
            self._use_project_name_for_file(item, mode='replace')
        elif action == prepend_name_action:
            # Always apply prepend mode, regardless of current state
            self._use_project_name_for_file(item, mode='prepend')
        elif action == append_name_action:
            # Always apply append mode, regardless of current state
            self._use_project_name_for_file(item, mode='append')
        elif action == pattern_action:
            self._configure_naming_pattern(item)
        elif action == reset_name_action:
            self._reset_file_name(item)
        elif action == separator_action:
            self._configure_custom_separator(item)
        elif action == delete_action:
            self.delete_selected()
            
    def _use_project_name_for_file(self, item, mode):
        """Set a file item to use the project name with a specific mode (replace, append, prepend)."""
        if not item or not self.editor:
            return False
        
        # Get current file data and name
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(item_data, dict) or item_data.get('type') != 'file':
            return False
        
        current_name = item.text(0)
        
        # Store original name if we don't already have it
        # First check if we already have an original_name stored
        if 'original_name' not in item_data:
            # Try to extract original name from current display name if it contains placeholders
            if "${PROJECT_NAME}" in current_name:
                # Try to reconstruct original name from placeholder display
                if mode == 'replace':
                    # For replace mode: ${PROJECT_NAME}.ext -> original would be the extension part
                    parts = current_name.split('${PROJECT_NAME}')
                    if len(parts) == 2 and parts[1].startswith('.'):
                        # This might be from a replace mode, but we can't reliably reconstruct
                        # Use a reasonable fallback
                        item_data['original_name'] = current_name.replace('${PROJECT_NAME}', 'file')
                    else:
                        item_data['original_name'] = current_name.replace('${PROJECT_NAME}', 'file')
                elif mode == 'append':
                    # For append mode: name.${PROJECT_NAME}.ext -> original would be name.ext
                    item_data['original_name'] = current_name.replace('.${PROJECT_NAME}', '')
                elif mode == 'prepend':
                    # For prepend mode: ${PROJECT_NAME}.name.ext -> original would be name.ext
                    item_data['original_name'] = current_name.replace('${PROJECT_NAME}.', '')
                else:
                    item_data['original_name'] = current_name.replace('${PROJECT_NAME}', 'file')
            else:
                # Current name doesn't contain placeholders, so it's the original
                item_data['original_name'] = current_name
        
        # Use original name as the base to work with
        original_name = item_data.get('original_name', current_name)
        
        # Set the project name flags
        item_data['uses_project_name'] = True
        item_data['rename_flag'] = True
        item_data['project_name_mode'] = mode
        
        # Generate the appropriate display name based on mode
        if mode == 'replace':
            # Replace entire name with ${PROJECT_NAME} + extension
            if '.' in original_name:
                extension = '.' + original_name.split('.')[-1]
                display_name = f"${{PROJECT_NAME}}{extension}"
            else:
                display_name = "${PROJECT_NAME}"
        elif mode == 'append':
            # Append ${PROJECT_NAME} before extension
            if '.' in original_name:
                name_part = '.'.join(original_name.split('.')[:-1])
                extension = '.' + original_name.split('.')[-1]
                display_name = f"{name_part}.${{PROJECT_NAME}}{extension}"
            else:
                display_name = f"{original_name}.${{PROJECT_NAME}}"
        elif mode == 'prepend':
            # Prepend ${PROJECT_NAME} to the original name
            display_name = f"${{PROJECT_NAME}}.{original_name}"
        else:
            display_name = f"${{PROJECT_NAME}}"
        
        # Update the item display and data
        item.setText(0, display_name)
        item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Mark editor as modified
        if hasattr(self.editor, 'mark_modified'):
            self.editor.mark_modified()
        
        return True

    def _reset_file_name(self, item):
        """
        Reset file name to the original value
        
        Args:
            item: The file item to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not item:
            print("ERROR: _reset_file_name called with no item")
            return False
        
        # Get current file data
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(item_data, dict) or item_data.get('type') != 'file':
            print("ERROR: _reset_file_name called on non-file item or invalid data")
            return False
        
        # Get original name
        original_name = item_data.get('original_name')
        if not original_name:
            # Try to get original name from original_path as fallback
            original_path = item_data.get('original_path', '')
            if original_path and os.path.exists(original_path):
                original_name = os.path.basename(original_path)
                item_data['original_name'] = original_name  # Store it for future use
                print(f"DEBUG: _reset_file_name - recovered original name from path: {original_name}")
            else:
                print("ERROR: Original name not found and cannot be recovered, cannot reset")
                return False
        
        print(f"DEBUG: _reset_file_name - resetting to original name: {original_name}")
        
        # Update display to show original name
        item.setText(0, original_name)
        
        # Update data - turn off the flags but keep original_name for future use
        item_data['uses_project_name'] = False
        item_data['project_name_mode'] = 'none'
        item_data['rename_flag'] = False
        
        # Clear any custom settings while preserving original_name
        if 'custom_separator' in item_data:
            del item_data['custom_separator']
        if 'custom_pattern' in item_data:
            del item_data['custom_pattern']
        
        # Store updated data
        item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Restore normal styling
        font = item.font(0)
        font.setItalic(False)
        item.setFont(0, font)
        item.setForeground(0, QBrush(QColor("#000000")))  # Reset to default color
        
        # Mark editor as modified
        if hasattr(self.editor, 'mark_modified'):
            self.editor.mark_modified()
        
        return True

    def _configure_custom_separator(self, item):
        """
        Configure a custom separator for project name operations with industry-specific presets
        
        Args:
            item: The file item to update
            
        Returns:
            bool: True if a separator was set, False otherwise
        """
        if not item:
            return False
        
        # Get current file data
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(item_data, dict) or item_data.get('type') != 'file':
            return False
        
        # Get current separator
        current_separator = item_data.get('custom_separator', '.')
        
        # Create a custom dialog with organized separator options
        dialog = SeparatorSelectionDialog(self.tree, current_separator)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            separator = dialog.get_selected_separator()
            
            if separator:
                # Store the separator
                item_data['custom_separator'] = separator
                item.setData(0, Qt.ItemDataRole.UserRole, item_data)
                
                # If already using project name, update the display
                if item_data.get('uses_project_name', False):
                    mode = item_data.get('project_name_mode', 'replace')
                    self._use_project_name_for_file(item, mode=mode)
                
                # Mark editor as modified
                if hasattr(self.editor, 'mark_modified'):
                    self.editor.mark_modified()
                
                return True
        
        return False

    def _toggle_project_name_for_file(self, item, mode, is_checked):
        """Toggle the project name usage for a file item and update item data."""
        if not item:
            return False
        
        # Get current file data
        item_data = self._get_item_data(item)
        if not isinstance(item_data, dict) or item_data.get('type') != 'file':
            return False
        
        # New logic based on is_checked and mode
        if is_checked:
            # If the action is being checked (turned on), apply the specified mode
            return self._use_project_name_for_file(item, mode=mode)
        else:
            # If the action is being unchecked, revert to the original name
            return self._reset_file_name(item)

    def _get_relative_path(self, item):
        """
        Get the relative path of an item in the tree
        
        Args:
            item: Tree item to get path for
            
        Returns:
            str: Relative path of the item
        """
        if not item:
            return ""
            
        # Start with the item's name
        path_parts = [item.text(0)]
        
        # Walk up the tree
        parent = item.parent()
        while parent and parent != self.tree.invisibleRootItem():
            path_parts.insert(0, parent.text(0))
            parent = parent.parent()
        
        # Join parts with platform-independent separator
        return "/".join(path_parts[:-1])  # Exclude the file name itself

    def _get_editor_colors(self):
        """
        Get color scheme from the editor or use defaults
        
        Returns:
            dict: Dictionary of color values
        """
        try:
            # Try to get colors from app's color scheme
            from app.ui.color_scheme_pyqt import APP_COLORS
            return APP_COLORS
        except ImportError:
            # Fallback colors
            return {
                'accent': '#007ACC',            # Blue accent color
                'accent_light': '#338ACC',      # Lighter blue
                'accent_dark': '#005A9C',       # Darker blue
                'tracked': '#88AADD',           # Light blue for tracked files
                'background': '#1E1E1E',        # Dark background
                'text': '#FFFFFF',              # White text
                'text_secondary': '#CCCCCC',    # Light gray secondary text
                'border': '#444444',            # Dark gray borders
                'warning': '#FF9900',           # Orange warning
                'error': '#FF5555',             # Red error
                'success': '#55AA55'            # Green success
            }

    def _configure_naming_pattern(self, item):
        """
        Configure a custom naming pattern for project name operations
        
        Args:
            item: The file item to update
            
        Returns:
            bool: True if a pattern was set, False otherwise
        """
        if not item:
            return False
        
        # Get current file data
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(item_data, dict) or item_data.get('type') != 'file':
            return False
        
        # Get current pattern or default
        current_pattern = item_data.get('custom_pattern', '$project$ext')
        
        # Pattern description
        pattern_desc = """
Available placeholders:
$project - Project name
$base - Original filename without extension
$ext - File extension (with dot)
$sep - Custom separator

Example: $project_$base$ext
"""
        
        # Show input dialog to get the pattern
        pattern, ok = QInputDialog.getText(
            self.tree, 
            "Custom Naming Pattern",
            f"Enter a custom pattern for filename:{pattern_desc}",
            text=current_pattern
        )
        
        if not ok or not pattern:
            return False
        
        # Store the pattern
        item_data['custom_pattern'] = pattern
        item_data['project_name_mode'] = 'pattern'
        item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Update the display
        self._use_project_name_for_file(item, mode='pattern')
        
        return True

    def _get_item_data(self, item):
        """Retrieve the dictionary of data associated with a QTreeWidgetItem."""
        if not item:
            return {}
        try:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            # print(f"Error getting item data for '{item.text(0)}': {e}")
            return {}

    def _update_item_data(self, item, data_dict):
        # Placeholder for actual update logic
        # print(f"DEBUG: Updating data for item: {item.text(0)} with: {data_dict}")
        # This needs to be implemented based on how item data is stored
        pass

class SeparatorSelectionDialog(QDialog):
    """Dialog for selecting file name separators with industry-specific presets"""
    
    def __init__(self, parent, current_separator="."):
        super().__init__(parent)
        self.selected_separator = current_separator
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Choose Project Name Separator")
        self.setFixedWidth(520)
        self.setFixedHeight(650)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title and description
        title = QLabel("Project Name Separator")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)
        
        desc = QLabel("Choose how to separate the project name from the filename:")
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        # Create separator preset sections
        self.create_separator_sections(layout)
        
        # Custom input section
        self.create_custom_section(layout)
        
        # Preview section
        self.create_preview_section(layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        ok_btn = QPushButton("Apply")
        ok_btn.setDefault(True)
        
        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)
        
        # Set initial selection
        self.update_preview()
        
    def create_separator_sections(self, layout):
        """Create organized sections for different separator types"""
        
        # Define separator categories with descriptions and use cases
        separator_categories = {
            "Standard Separators": {
                "description": "Most commonly used across all industries",
                "separators": [
                    (".", "Period", "ProjectName.filename.ext", "Clean, professional, widely compatible"),
                    ("_", "Underscore", "ProjectName_filename.ext", "Very common in programming, technical work"),
                    ("-", "Dash/Hyphen", "ProjectName-filename.ext", "Web-friendly, clean appearance"),
                    (" ", "Space", "ProjectName filename.ext", "Natural reading, may cause issues on some systems")
                ]
            },
            "Video/Film Production": {
                "description": "Optimized for video editing workflows and media management",
                "separators": [
                    ("_", "Underscore", "ProjectName_filename.ext", "Industry standard, NLE-friendly"),
                    ("_v", "Version Underscore", "ProjectName_v01_filename.ext", "Perfect for versioning"),
                    ("-", "Dash", "ProjectName-filename.ext", "Clean, professional"),
                    ("_", "Date Underscore", "ProjectName_20250108_filename.ext", "Great with dates")
                ]
            },
            "Software Development": {
                "description": "Following programming conventions and standards",
                "separators": [
                    ("_", "Snake Case", "project_name_filename.ext", "Python, Ruby style"),
                    ("-", "Kebab Case", "project-name-filename.ext", "Web development, CSS style"),
                    (".", "Dot Notation", "ProjectName.filename.ext", "Clean, namespace-like"),
                    ("_", "Constant Style", "PROJECT_NAME_filename.ext", "All caps, constants")
                ]
            },
            "Design/Creative": {
                "description": "Optimized for creative workflows and client presentations",
                "separators": [
                    ("-", "Dash", "ProjectName-filename.ext", "Clean, professional appearance"),
                    ("_", "Underscore", "ProjectName_filename.ext", "Technical but readable"),
                    (".", "Period", "ProjectName.filename.ext", "Minimalist, clean"),
                    (" ", "Space", "ProjectName filename.ext", "Client-friendly, natural")
                ]
            },
            "Audio Production": {
                "description": "Designed for DAW compatibility and audio workflows",
                "separators": [
                    ("_", "Underscore", "ProjectName_filename.ext", "DAW-friendly, no issues"),
                    ("-", "Dash", "ProjectName-filename.ext", "Clean, professional"),
                    ("_v", "Version Style", "ProjectName_v01_filename.ext", "Perfect for mix versions"),
                    ("_", "Mix Style", "ProjectName_mix01_filename.ext", "Audio industry standard")
                ]
            }
        }
        
        # Create scroll area for the categories
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        for category_name, category_data in separator_categories.items():
            self.create_category_section(scroll_layout, category_name, category_data)
        
        scroll_area.setWidget(scroll_content)
        scroll_area.setFixedHeight(350)
        layout.addWidget(scroll_area)
        
    def create_category_section(self, layout, category_name, category_data):
        """Create a section for a specific category of separators"""
        
        # Category header
        category_frame = QFrame()
        category_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f8f9fa;
                margin: 2px;
            }
        """)
        category_layout = QVBoxLayout(category_frame)
        category_layout.setSpacing(8)
        category_layout.setContentsMargins(12, 12, 12, 12)
        
        # Category title
        title_label = QLabel(category_name)
        title_label.setStyleSheet("font-weight: bold; color: #2c5aa0; font-size: 13px;")
        category_layout.addWidget(title_label)
        
        # Category description
        desc_label = QLabel(category_data["description"])
        desc_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 8px;")
        desc_label.setWordWrap(True)
        category_layout.addWidget(desc_label)
        
        # Separator options
        for separator, name, example, description in category_data["separators"]:
            self.create_separator_option(category_layout, separator, name, example, description)
        
        layout.addWidget(category_frame)
        
    def create_separator_option(self, layout, separator, name, example, description):
        """Create a single separator option"""
        
        option_frame = QFrame()
        option_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
                padding: 6px;
            }
            QFrame:hover {
                border-color: #007ACC;
                background-color: #f0f8ff;
            }
        """)
        option_frame.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        option_layout = QHBoxLayout(option_frame)
        option_layout.setContentsMargins(8, 6, 8, 6)
        
        # Radio button
        radio = QCheckBox()
        radio.setStyleSheet("QCheckBox::indicator { width: 14px; height: 14px; }")
        
        # Option details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(2)
        
        # Name and separator
        name_layout = QHBoxLayout()
        name_label = QLabel(f"{name}")
        name_label.setStyleSheet("font-weight: bold; color: #333;")
        
        sep_label = QLabel(f"'{separator}'")
        sep_label.setStyleSheet("font-family: monospace; background: #f0f0f0; padding: 2px 6px; border-radius: 3px; color: #007ACC;")
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(sep_label)
        name_layout.addStretch()
        
        # Example
        example_label = QLabel(f"Example: {example}")
        example_label.setStyleSheet("font-family: monospace; color: #666; font-size: 11px;")
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #777; font-size: 10px;")
        
        details_layout.addLayout(name_layout)
        details_layout.addWidget(example_label)
        details_layout.addWidget(desc_label)
        
        option_layout.addWidget(radio)
        option_layout.addLayout(details_layout)
        
        layout.addWidget(option_frame)
        
        # Store references and connect signals
        option_frame.separator = separator
        option_frame.radio = radio
        option_frame.mousePressEvent = lambda event, sep=separator: self.select_separator(sep)
        radio.clicked.connect(lambda checked, sep=separator: self.select_separator(sep) if checked else None)
        
        # Check if this is the current separator
        if separator == self.selected_separator:
            radio.setChecked(True)
            
    def create_custom_section(self, layout):
        """Create custom separator input section"""
        
        custom_frame = QFrame()
        custom_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #ffa500;
                border-radius: 6px;
                background-color: #fff8e1;
                margin: 2px;
            }
        """)
        custom_layout = QVBoxLayout(custom_frame)
        custom_layout.setContentsMargins(12, 12, 12, 12)
        
        title_label = QLabel("Custom Separator")
        title_label.setStyleSheet("font-weight: bold; color: #e65100; font-size: 13px;")
        custom_layout.addWidget(title_label)
        
        desc_label = QLabel("Enter any character(s) to use as a separator:")
        desc_label.setStyleSheet("color: #bf360c; font-size: 11px; margin-bottom: 8px;")
        custom_layout.addWidget(desc_label)
        
        input_layout = QHBoxLayout()
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("Enter custom separator...")
        self.custom_input.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-family: monospace;
            }
        """)
        self.custom_input.textChanged.connect(self.on_custom_input_changed)
        
        self.custom_radio = QCheckBox("Use Custom")
        self.custom_radio.clicked.connect(self.on_custom_radio_clicked)
        
        input_layout.addWidget(self.custom_input)
        input_layout.addWidget(self.custom_radio)
        
        custom_layout.addLayout(input_layout)
        layout.addWidget(custom_frame)
        
    def create_preview_section(self, layout):
        """Create preview section"""
        
        preview_frame = QFrame()
        preview_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f5f5f5;
                margin: 2px;
            }
        """)
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(12, 12, 12, 12)
        
        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet("font-weight: bold; color: #333; margin-bottom: 6px;")
        preview_layout.addWidget(preview_label)
        
        self.preview_text = QLabel()
        self.preview_text.setStyleSheet("""
            font-family: monospace;
            background: white;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            color: #007ACC;
            font-size: 12px;
        """)
        preview_layout.addWidget(self.preview_text)
        
        layout.addWidget(preview_frame)
        
    def select_separator(self, separator):
        """Select a separator and update UI"""
        self.selected_separator = separator
        
        # Update all radio buttons
        for frame in self.findChildren(QFrame):
            if hasattr(frame, 'radio') and hasattr(frame, 'separator'):
                frame.radio.setChecked(frame.separator == separator)
        
        # Clear custom radio if not custom
        if separator != self.custom_input.text():
            self.custom_radio.setChecked(False)
        
        self.update_preview()
        
    def on_custom_input_changed(self, text):
        """Handle custom input changes"""
        if text and self.custom_radio.isChecked():
            self.selected_separator = text
            self.update_preview()
            
    def on_custom_radio_clicked(self, checked):
        """Handle custom radio button clicks"""
        if checked and self.custom_input.text():
            self.selected_separator = self.custom_input.text()
            # Uncheck all other radios
            for frame in self.findChildren(QFrame):
                if hasattr(frame, 'radio'):
                    frame.radio.setChecked(False)
            self.update_preview()
        elif checked:
            # Focus on custom input if checked but empty
            self.custom_input.setFocus()
            
    def update_preview(self):
        """Update the preview text"""
        if self.selected_separator:
            example = f"MyProject{self.selected_separator}filename.ext"
            self.preview_text.setText(example)
        else:
            self.preview_text.setText("No separator selected")
            
    def get_selected_separator(self):
        """Get the selected separator"""
        return self.selected_separator

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
        
        # Extensions dropdown
        ext_layout = QHBoxLayout()
        ext_label = QLabel("Extension:")
        ext_layout.addWidget(ext_label)
        
        self.extension_combo = QComboBox()
        self._update_extensions()
        ext_layout.addWidget(self.extension_combo)
        
        # Update file name when extension changes
        self.extension_combo.currentIndexChanged.connect(self._update_file_name)
        
        layout.addLayout(ext_layout)
        
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
            QCheckBox {
                color: #FFFFFF;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                background-color: #3E3E42;
                border: 1px solid #3F3F46;
            }
            QCheckBox::indicator:checked {
                background-color: #007ACC;
            }
        """)
        
        # Connect signals
        self.file_name_edit.textChanged.connect(self._on_file_name_changed)
        
        # Initial update
        self._on_file_name_changed(file_name)
    
    def _on_type_changed(self, index):
        """Handle type selection change"""
        self._update_extensions()
        
        # Update file name based on new extension
        self._update_file_name()
    
    def _update_extensions(self):
        """Update the extensions dropdown based on selected type"""
        self.extension_combo.clear()
        
        # Get current file type
        file_type = self.file_type_combo.currentText()
        
        # Get extensions for this type
        extensions = FILE_EXTENSIONS.get(file_type, [])
        if extensions:
            self.extension_combo.addItems(extensions)
    
    def _update_file_name(self):
        """Update file name based on selected extension"""
        # Get current file name and remove any extension
        file_name = self.file_name_edit.text()
        base_name = os.path.splitext(file_name)[0]
        
        # If base name is empty, generate a random one
        if not base_name:
            # Generate a random file name
            base_name = f"file_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
        
        # Get selected extension
        extension = self.extension_combo.currentText()
        
        # Update file name
        self.file_name_edit.setText(f"{base_name}{extension}")
    
    def _on_file_name_changed(self, text):
        """Handle file name changes"""
        # Extract extension
        _, ext = os.path.splitext(text)
        
        # Update binary checkbox if available
        if self.binary_checkbox:
            # Determine if binary based on extension
            is_binary = False
            for category in ['Image', 'Audio', 'Video', 'Archive']:
                if category in FILE_EXTENSIONS and ext.lower() in FILE_EXTENSIONS[category]:
                    is_binary = True
                    break
                    
            self.binary_checkbox.setChecked(is_binary)
            
        # Try to select matching file type
        for category, extensions in FILE_EXTENSIONS.items():
            if ext.lower() in extensions:
                self.file_type_combo.setCurrentText(category)
                
                # Select the extension in the dropdown
                self.extension_combo.setCurrentText(ext.lower())
                break
    
    def get_file_name(self):
        """Get the entered file name"""
        return self.file_name_edit.text()
    
    def get_file_type(self):
        """Get the selected file type"""
        return self.file_type_combo.currentText()
    
    def is_binary(self):
        """Check if the file is marked as binary"""
        return self.binary_checkbox.isChecked() if self.binary_checkbox else False 
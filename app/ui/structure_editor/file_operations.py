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
from PyQt5.QtWidgets import (
    QTreeWidgetItem, QInputDialog, QMessageBox, QMenu, QAction,
    QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QCheckBox, QApplication, QStyle
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QDrag, QBrush, QColor

from .utils import get_file_icon_for_type

# Common file extensions by category
FILE_EXTENSIONS = {
    "Text": [".txt", ".md", ".csv", ".json", ".xml", ".yaml", ".ini"],
    "Code": [".py", ".js", ".html", ".css", ".cpp", ".h", ".java", ".php", ".go", ".rs"],
    "Image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".tiff"],
    "Audio": [".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"],
    "Video": [".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"],
    "Document": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"],
    "Archive": [".zip", ".rar", ".7z", ".tar", ".gz"]
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
        Add a file to the structure
        
        Args:
            parent_item: Parent item to add the file to (optional)
            file_name: Name of the file (optional, will prompt if None)
            file_type: Type of the file (optional)
            
        Returns:
            QTreeWidgetItem: The new file item
        """
        if not self.tree:
            print("ERROR: Tree widget not available")
            return None
            
        # If no parent specified, use selected item or root
        if not parent_item:
            selected_items = self.tree.selectedItems()
            if selected_items:
                parent_item = selected_items[0]
                
                # If selected item is a file, use its parent
                item_data = parent_item.data(0, Qt.UserRole)
                if isinstance(item_data, dict) and item_data.get('type') == 'file':
                    if parent_item.parent():
                        parent_item = parent_item.parent()
                    else:
                        parent_item = self.tree.invisibleRootItem()
            else:
                # Use root item
                parent_item = self.tree.invisibleRootItem()
        
        # If no file name provided, show file browser dialog to select files
        if not file_name:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self.editor,
                "Select Files to Add",
                os.path.expanduser("~"),
                "All Files (*)"
            )
            
            if not file_paths:
                return None  # User canceled
            
            # Add each selected file
            added_items = []
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                file_item = self._add_file_item(parent_item, file_name, file_type)
                
                # If it's a binary file, cache its contents
                if self.is_binary_file(file_name) and os.path.exists(file_path):
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read()
                            # Generate a unique key for this content
                            cache_key = f"{file_name}_{id(file_item)}"
                            self.cached_files[cache_key] = content
                            
                            # Update file data
                            file_data = file_item.data(0, Qt.UserRole)
                            file_data['cached'] = True
                            file_data['cache_key'] = cache_key
                            file_item.setData(0, Qt.UserRole, file_data)
                    except Exception as e:
                        print(f"DEBUG: Failed to cache binary file: {e}")
                
                added_items.append(file_item)
            
            # Return the last added item
            return added_items[-1] if added_items else None
        
        # If file name is provided, just add a single file
        return self._add_file_item(parent_item, file_name, file_type)
    
    def _add_file_item(self, parent_item, file_name, file_type=None):
        """Helper method to add a file item to the tree"""
        # Create tree item
        file_item = QTreeWidgetItem(parent_item)
        file_item.setText(0, file_name)
        
        # Set icon based on file type
        # First try to get a file type specific icon, fall back to standard file icon
        icon = get_file_icon_for_type(file_name)
        if icon.isNull():
            icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
        file_item.setIcon(0, icon)
        
        # Ensure the item is editable
        file_item.setFlags(file_item.flags() | Qt.ItemIsEditable)
        
        # Determine if binary based on extension
        is_binary = self.is_binary_file(file_name)
        
        # Store file data
        file_data = {
            "type": "file",
            "name": file_name,
            "is_binary": is_binary
        }
        
        # Add file type if provided
        if file_type:
            file_data["file_type"] = file_type
            
        file_item.setData(0, Qt.UserRole, file_data)
        
        # Expand parent and select new item
        parent_item.setExpanded(True)
        self.tree.setCurrentItem(file_item)
        
        return file_item
    
    def add_folder(self, parent_item=None):
        """Add a new folder to the tree under the given parent"""
        folder_name, ok = QInputDialog.getText(
            self.tree, 
            "Add Folder", 
            "Enter folder name:"
        )
        
        if not ok or not folder_name:
            return None
        
        # Create folder item
        if parent_item is None:
            folder_item = QTreeWidgetItem(self.tree)
        else:
            folder_item = QTreeWidgetItem(parent_item)
        
        # Set name and mark as folder
        folder_item.setText(0, folder_name)
        folder_item.setData(0, Qt.UserRole, {"type": "folder"})
        
        # Make the folder editable
        folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
        
        # Set folder icon - use app standard icon instead of theme
        folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
        
        # Apply styles for folders - use bold instead of color
        font = folder_item.font(0)
        font.setBold(True)
        folder_item.setFont(0, font)
        
        # Expand parent to show new folder
        if parent_item:
            parent_item.setExpanded(True)
        
        # Return the created folder item
        return folder_item
    
    def delete_selected(self):
        """
        Delete selected items from the structure
        
        Returns:
            bool: True if items were deleted, False otherwise
        """
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
            item_data = item.data(0, Qt.UserRole)
            if isinstance(item_data, dict):
                item_type = item_data.get('type', 'item')
                item_name = item.text(0)
                confirm_msg = f"Delete {item_type} '{item_name}'?"
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.editor, 
            confirm_title,
            confirm_msg, 
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            print("DEBUG: delete_selected - user cancelled deletion")
            return False
            
        # Delete items
        deleted_count = 0
        root = self.tree.invisibleRootItem()
        
        for item in selected_items:
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
        
        # Refresh the tree view
        if deleted_count > 0:
            self.tree.update()
            print(f"DEBUG: delete_selected - {deleted_count} items deleted successfully")
            return True
        else:
            print(f"DEBUG: delete_selected - no items were deleted")
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
        item.setFlags(item.flags() | Qt.ItemIsEditable)
            
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
        item_data = item.data(0, Qt.UserRole)
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
            item.setData(0, Qt.UserRole, item_data)
            
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
                item_data = target_item.data(0, Qt.UserRole)
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
                            file_data = file_item.data(0, Qt.UserRole)
                            file_data['cached'] = True
                            file_data['cache_key'] = cache_key
                            file_item.setData(0, Qt.UserRole, file_data)
                    except Exception as e:
                        print(f"DEBUG: Failed to cache binary file: {e}")
    
    def import_file(self, target_item=None):
        """
        Import a file from the file system
        
        Args:
            target_item: Item to import into (optional)
            
        Returns:
            bool: True if imported, False otherwise
        """
        if not self.tree:
            return False
            
        # Get file path
        file_path, _ = QFileDialog.getOpenFileName(
            self.editor,
            "Select File to Import",
            os.path.expanduser("~"),
            "All Files (*)"
        )
        
        if not file_path:
            return False  # User canceled
            
        # If no target specified, use selected item or root
        if not target_item:
            selected_items = self.tree.selectedItems()
            if selected_items:
                target_item = selected_items[0]
                
                # If selected item is a file, use its parent
                item_data = target_item.data(0, Qt.UserRole)
                if isinstance(item_data, dict) and item_data.get('type') == 'file':
                    if target_item.parent():
                        target_item = target_item.parent()
                    else:
                        target_item = self.tree.invisibleRootItem()
            else:
                # Use root item
                target_item = self.tree.invisibleRootItem()
        
        # Import the file
        try:
            # Get file name from path
            file_name = os.path.basename(file_path)
            
            # Add file
            file_item = self.add_file(target_item, file_name)
            
            # If it's a binary file, cache it
            if self.is_binary_file(file_name):
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        self.cached_files[file_path] = content
                        
                        # Update file data
                        file_data = file_item.data(0, Qt.UserRole)
                        file_data['cached'] = True
                        file_data['cache_key'] = file_path
                        file_item.setData(0, Qt.UserRole, file_data)
                except Exception as e:
                    print(f"DEBUG: Failed to cache binary file: {e}")
            
            return True
        except Exception as e:
            QMessageBox.critical(
                self.editor,
                "Import Error",
                f"Error importing file: {str(e)}"
            )
            return False
    
    def is_binary_file(self, file_path):
        """
        Check if a file is binary based on extension
        
        Args:
            file_path: Path to the file or just the filename
            
        Returns:
            bool: True if binary, False otherwise
        """
        # Get the file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Common binary file extensions
        binary_extensions = set()
        for extensions in [FILE_EXTENSIONS['Image'], FILE_EXTENSIONS['Audio'], 
                          FILE_EXTENSIONS['Video'], FILE_EXTENSIONS['Archive']]:
            binary_extensions.update(extensions)
        
        # Check if it's a known binary extension
        if ext in binary_extensions:
            return True
            
        # Use mimetypes as fallback
        if ext:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                return mime_type.startswith(('image/', 'audio/', 'video/', 'application/octet-stream'))
                
        # Default to non-binary
        return False
    
    def create_context_menu(self, item, position):
        """
        Create a context menu for a tree item
        
        Args:
            item: The item to create a menu for
            position: Position for the menu
            
        Returns:
            QMenu: The context menu
        """
        print("DEBUG: create_context_menu - creating context menu")
        menu = QMenu(self.tree)
        
        # Import styles for context menu, including destructive action styling
        try:
            from app.ui.color_scheme_pyqt import CONTEXT_MENU_STYLE, DELETE_TEXT_STYLE
            menu.setStyleSheet(CONTEXT_MENU_STYLE)
        except ImportError:
            # Fallback styling
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
        
        # Get item data
        item_data = item.data(0, Qt.UserRole) if item else None
        is_file = isinstance(item_data, dict) and item_data.get('type') == 'file'
        is_folder = isinstance(item_data, dict) and item_data.get('type') == 'folder'
        
        print(f"DEBUG: create_context_menu - item type: {'file' if is_file else 'folder' if is_folder else 'unknown/none'}")
        
        # Add file action
        add_file_action = QAction("Add File", menu)
        add_file_action.triggered.connect(lambda: self.add_file(item if is_folder else item.parent() if item else None))
        menu.addAction(add_file_action)
        
        # Add folder action
        add_folder_action = QAction("Add Folder", menu)
        add_folder_action.triggered.connect(lambda: self.add_folder(item if is_folder else item.parent() if item else None))
        menu.addAction(add_folder_action)
        
        # Import actions
        menu.addSeparator()
        
        import_file_action = QAction("Import File...", menu)
        import_file_action.triggered.connect(lambda: self.import_file(item if is_folder else item.parent() if item else None))
        menu.addAction(import_file_action)
        
        import_dir_action = QAction("Import Directory...", menu)
        import_dir_action.triggered.connect(lambda: self.import_directory(item if is_folder else item.parent() if item else None))
        menu.addAction(import_dir_action)
        
        # Item-specific actions
        if item:
            menu.addSeparator()
            
            # Rename action
            rename_action = QAction("Rename", menu)
            rename_action.triggered.connect(lambda: self.rename_item(item))
            menu.addAction(rename_action)
            
            # Delete action - with destructive styling
            delete_action = QAction("Delete", menu)
            delete_action.triggered.connect(lambda: self.delete_selected())
            
            # Apply destructive styling to delete action
            try:
                from app.ui.color_scheme_pyqt import DELETE_TEXT_STYLE
                delete_action.setProperty("destructive", "true")  # Set property for styling
                
                # Apply direct styling using stylesheet for compatibility
                delete_action.setStyleSheet("color: #FF5555; font-weight: bold;")
            except:
                # Fallback - set color using setData
                print("DEBUG: Using fallback styling for delete action")
                delete_action.setData(QColor("#FF5555"))
                
            menu.addAction(delete_action)
            
            # File-specific actions
            if is_file:
                menu.addSeparator()
                
                # Add "Use Project Name" option 
                use_project_name_action = QAction("Use Project Name", menu)
                use_project_name_action.setEnabled(True)
                
                # Connect to method in editor if available
                if self.editor and hasattr(self.editor, '_use_project_name_for_file'):
                    use_project_name_action.triggered.connect(lambda: self.editor._use_project_name_for_file(item))
                    print("DEBUG: create_context_menu - connected Use Project Name to editor method")
                else:
                    # Fallback to local method
                    use_project_name_action.triggered.connect(lambda: self._use_project_name_for_file(item))
                    print("DEBUG: create_context_menu - connected Use Project Name to local method")
                
                menu.addAction(use_project_name_action)
        
        return menu
    
    def _setup_context_menu(self):
        """Set up the context menu for the tree widget"""
        if not self.tree:
            return
        
        # Make sure tree widget has context menu policy set
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Connect context menu to our handler
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        
        print("DEBUG: Context menu set up")

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
            item_data = item.data(0, Qt.UserRole)
            
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
        add_folder_action = menu.addAction(QIcon.fromTheme("folder-new"), "Add Folder")
        add_file_action = menu.addAction(QIcon.fromTheme("document-new"), "Add File")
        import_action = menu.addAction(QIcon.fromTheme("document-import"), "Import")
        
        # Add submenu for import
        import_menu = QMenu("Import Options", menu)
        import_menu.setStyleSheet(CONTEXT_MENU_STYLE)
        import_menu.addAction(QIcon.fromTheme("document-import"), "Import File")
        import_menu.addAction(QIcon.fromTheme("folder-import"), "Import Directory")
        menu.insertMenu(import_action, import_menu)
        
        # Remove the original import action
        menu.removeAction(import_action)
        
        # Add keyboard shortcuts to actions
        add_folder_action.setShortcut("Ctrl+Shift+N")
        add_file_action.setShortcut("Ctrl+N")
        
        # Execute the menu
        action = menu.exec_(self.tree.mapToGlobal(position))
        
        # Handle actions
        if action == add_folder_action:
            self.add_folder()
        elif action == add_file_action:
            self.add_file()
        elif action == import_file_action:
            self.import_file()
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
        action = menu.exec_(self.tree.mapToGlobal(position))
        
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
        
        # Add "Use Project Name" option
        use_project_name_action = menu.addAction(QIcon.fromTheme("insert-text"), "Use Project Name")
        
        menu.addSeparator()
        delete_action = menu.addAction(QIcon.fromTheme("edit-delete"), "Delete")
        
        # Add keyboard shortcuts
        rename_action.setShortcut("F2")
        delete_action.setShortcut("Delete")
        
        # Execute the menu
        action = menu.exec_(self.tree.mapToGlobal(position))
        
        # Handle actions
        if action == rename_action:
            self.rename_item(item)
        elif action == use_project_name_action:
            self._use_project_name_for_file(item)
        elif action == delete_action:
            self.delete_selected()

    def _use_project_name_for_file(self, item):
        """
        Set a file to use the project name as its name
        
        Args:
            item: The file item to update
        """
        if not item:
            print("DEBUG: FileOperations._use_project_name_for_file - no item provided")
            return
            
        # Get current file data and name
        item_data = item.data(0, Qt.UserRole)
        if not isinstance(item_data, dict) or item_data.get('type') != 'file':
            print(f"DEBUG: FileOperations._use_project_name_for_file - item is not a file: {item.text(0)}")
            return
            
        current_name = item.text(0)
        
        # Use ${PROJECT_NAME} as the placeholder that will be replaced during project creation
        placeholder = "${PROJECT_NAME}"
        
        # For display in the editor, use the template name as an example
        display_name = "Project_Name"
        
        # Try to get the actual template name from the editor for display
        if self.editor:
            # Check if editor has a template_name attribute
            if hasattr(self.editor, 'template_name'):
                temp_name = self.editor.template_name.strip()
                if temp_name:
                    display_name = temp_name
                    print(f"DEBUG: FileOperations._use_project_name_for_file - using template name: {display_name}")
                    
            # Check if editor has a template_name_field in ui_builder as fallback
            elif hasattr(self.editor, 'ui_builder') and hasattr(self.editor.ui_builder, 'template_name_field'):
                temp_name = self.editor.ui_builder.template_name_field.text().strip()
                if temp_name:
                    display_name = temp_name
                    print(f"DEBUG: FileOperations._use_project_name_for_file - using template name from field: {display_name}")
        
        # Get the file extension
        extension = ""
        name_parts = current_name.split('.')
        if len(name_parts) > 1:
            extension = f".{name_parts[-1]}"
            
        # Create new name with template name for display
        new_name = f"{display_name}{extension}"
        
        print(f"DEBUG: FileOperations._use_project_name_for_file - marking file to use project name: '{current_name}' → '{new_name}' (will use '{placeholder}' as placeholder)")
        
        # Set the new name
        item.setText(0, new_name)
        
        # Update the data - store both the display name and the placeholder
        item_data['name'] = new_name
        item_data['uses_project_name'] = True
        item_data['placeholder'] = placeholder  # Store the placeholder that will be replaced
        item_data['original_extension'] = extension
        item.setData(0, Qt.UserRole, item_data)
        
        # Apply styling to indicate this is a dynamic file
        font = item.font(0)
        font.setItalic(True)
        item.setFont(0, font)
        
        # Also use a different color to make it clear
        item.setForeground(0, QBrush(QColor("#4A9BFF")))
        
        print(f"DEBUG: FileOperations._use_project_name_for_file - file marked to use project name: {new_name}")
        
        return True

    def _cut_item(self, item):
        """Cut item to clipboard for moving"""
        self._copy_item(item, is_cut=True)

    def _copy_item(self, item, is_cut=False):
        """Copy item to internal clipboard"""
        if not item:
            return
        
        # Get item data
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return
        
        # Create clipboard data
        is_folder = item_data.get('type') == 'folder'
        name = item.text(0)
        
        # For folders, create a deep copy of the structure
        children = []
        if is_folder:
            for i in range(item.childCount()):
                child_item = item.child(i)
                children.append(self._create_item_data(child_item))
        
        # Store in clipboard
        self._clipboard_item = {
            'name': name,
            'is_folder': is_folder,
            'children': children,
            'is_cut': is_cut,
            'source_item': item if is_cut else None
        }
        
        # Visual indication for cut items
        if is_cut:
            item.setForeground(0, QBrush(QColor(150, 150, 150)))  # Grayed out for cut items
            font = item.font(0)
            font.setItalic(True)
            item.setFont(0, font)

    def _create_item_data(self, item):
        """
        Create a recursive data structure for an item and its children
        
        Args:
            item: The tree item to create data for
            
        Returns:
            dict: Item data with children for folders
        """
        if not item:
            return None
        
        # Get item data
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return None
        
        is_folder = item_data.get('type') == 'folder'
        name = item.text(0)
        
        # Create data structure
        result = {
            'name': name,
            'is_folder': is_folder,
            'children': []
        }
        
        # For folders, add children
        if is_folder:
            for i in range(item.childCount()):
                child_item = item.child(i)
                child_data = self._create_item_data(child_item)
                if child_data:
                    result['children'].append(child_data)
        
        return result

    def _paste_item(self, parent_item):
        """
        Paste item from clipboard to the given parent
        
        Args:
            parent_item: Parent to paste under (or None for root)
        """
        if not hasattr(self, '_clipboard_item') or not self._clipboard_item:
            return
        
        # Get clipboard data
        clipboard_data = self._clipboard_item
        name = clipboard_data.get('name', '')
        is_folder = clipboard_data.get('is_folder', False)
        children = clipboard_data.get('children', [])
        is_cut = clipboard_data.get('is_cut', False)
        source_item = clipboard_data.get('source_item')
        
        # Check for valid name
        if not name:
            return
        
        # Create the new item
        new_item = self._create_item(parent_item, name, is_folder=is_folder)
        
        # For folders, recursively add children
        if is_folder and children:
            for child_data in children:
                self._paste_child_item(new_item, child_data)
        
        # If this was a cut operation, remove the original item
        if is_cut and source_item:
            source_parent = source_item.parent()
            if source_parent:
                source_parent.removeChild(source_item)
            else:
                index = self.tree.indexOfTopLevelItem(source_item)
                if index >= 0:
                    self.tree.takeTopLevelItem(index)
        
        # Expand the parent to show pasted item
        if parent_item:
            parent_item.setExpanded(True)

    def _paste_child_item(self, parent_item, item_data):
        """
        Recursively paste child items from clipboard data
        
        Args:
            parent_item: Parent to paste under
            item_data: Item data structure to create
        """
        if not parent_item or not item_data:
            return
        
        # Get item properties
        name = item_data.get('name', '')
        is_folder = item_data.get('is_folder', False)

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
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Drag and Drop Handler Module for Structure Editor
Handles drag and drop operations for files and folders
"""

import os
import json
from PyQt6.QtWidgets import QTreeWidgetItem, QMessageBox, QApplication, QStyle, QAbstractItemView, QStyleOptionViewItem
from PyQt6.QtCore import Qt, QMimeData, QUrl, QPoint, QRect
from PyQt6.QtGui import QDrag, QIcon, QBrush, QColor, QPixmap, QPainter, QCursor

from .utils import get_file_icon_for_type

# Import binary file handler
try:
    from app.utils.binary_file_handler import BinaryFileHandler
except ImportError:
    # Fallback if not available
    class BinaryFileHandler:
        @staticmethod
        def is_binary_file(file_path):
            # Simple fallback implementation
            return False

class DragDropHandler:
    """
    Handles drag and drop operations for the structure editor
    
    This class manages dragging and dropping files and folders between
    the file system and the structure tree, as well as within the tree.
    """
    
    def __init__(self, tree_widget=None, editor=None):
        """
        Initialize the drag and drop handler
        
        Args:
            tree_widget: Reference to the tree widget (QTreeWidget)
            editor: Reference to the parent editor (optional)
        """
        self.editor = editor
        self.tree = tree_widget
        self.dragged_item_instance = None # To store the item being dragged
        
        # Configure the tree for drag and drop if available
        if self.tree:
            self._configure_tree()
    
    def _configure_tree(self):
        """Configure the tree widget for drag and drop"""
        # Set drag and drop properties
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        
        # Style the drag indicator
        self.tree.setStyleSheet(self.tree.styleSheet() + """
            QTreeWidget::indicator:drop {
                background-color: #007ACC;
                border-radius: 2px;
            }
            QTreeWidget::item:drag {
                background-color: #383838;
                color: #DDDDDD;
                border: 1px solid #007ACC;
            }
        """)
        
        # Override drag and drop methods if not already overridden
        if not hasattr(self.tree, '_old_dragEnterEvent'):
            self.tree._old_dragEnterEvent = self.tree.dragEnterEvent
            self.tree.dragEnterEvent = self._drag_enter_event
            
        if not hasattr(self.tree, '_old_dragMoveEvent'):
            self.tree._old_dragMoveEvent = self.tree.dragMoveEvent
            self.tree.dragMoveEvent = self._drag_move_event
            
        if not hasattr(self.tree, '_old_dropEvent'):
            self.tree._old_dropEvent = self.tree.dropEvent
            self.tree.dropEvent = self._drop_event
        
        # Add mousePressEvent override for custom drag start
        if not hasattr(self.tree, '_old_mousePressEvent'):
            self.tree._old_mousePressEvent = self.tree.mousePressEvent
            self.tree.mousePressEvent = self._mouse_press_event
            
        # Add mouseMoveEvent override for custom drag
        if not hasattr(self.tree, '_old_mouseMoveEvent'):
            self.tree._old_mouseMoveEvent = self.tree.mouseMoveEvent
            self.tree.mouseMoveEvent = self._mouse_move_event
    
    def _drag_enter_event(self, event):
        """
        Handle drag enter events
        
        Args:
            event: Drag enter event
        """
        if event.mimeData().hasFormat("application/x-echelon-template-item"):
            # Handle internal drag of our custom items
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        elif event.mimeData().hasUrls():
            # Handle external file drops
            event.acceptProposedAction()
        else:
            # Fall back to default handler for other types
            self.tree._old_dragEnterEvent(event)
    
    def _drag_move_event(self, event):
        """
        Handle drag move events
        
        Args:
            event: Drag move event
        """
        if event.mimeData().hasFormat("application/x-echelon-template-item"):
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        elif event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            self.tree._old_dragMoveEvent(event)
    
    def _drop_event(self, event):
        """
        Handle drop events
        
        Args:
            event: Drop event
        """
        if event.mimeData().hasFormat("application/x-echelon-template-item") and self.dragged_item_instance:
            source_item = self.dragged_item_instance
            # In PyQt6, event.position() returns QPointF. itemAt expects QPoint.
            drop_point = event.position().toPoint() 
            target_item_at_drop = self.tree.itemAt(drop_point)

            if not source_item:
                event.ignore()
                self.dragged_item_instance = None # Clean up
                return

            target_parent_item = None
            insert_index = -1 # Default to append

            # Determine the actual target parent and insertion index based on drop position
            if target_item_at_drop:
                drop_indicator_pos = self.tree.dropIndicatorPosition()

                if drop_indicator_pos == QAbstractItemView.DropIndicatorPosition.OnItem:
                    # Dropped ON an item. If it's a folder, make source_item a child.
                    # Otherwise (file or non-folder), treat as dropping BELOW the item.
                    item_data = target_item_at_drop.data(0, Qt.ItemDataRole.UserRole)
                    if isinstance(item_data, dict) and item_data.get('type') == 'folder':
                        target_parent_item = target_item_at_drop
                        insert_index = target_parent_item.childCount() # Append to folder
                    else: # Dropped on a file or non-expandable item, treat as BelowItem
                        target_parent_item = target_item_at_drop.parent() or self.tree.invisibleRootItem()
                        insert_index = target_parent_item.indexOfChild(target_item_at_drop) + 1
                
                elif drop_indicator_pos == QAbstractItemView.DropIndicatorPosition.AboveItem:
                    target_parent_item = target_item_at_drop.parent() or self.tree.invisibleRootItem()
                    insert_index = target_parent_item.indexOfChild(target_item_at_drop)
                
                elif drop_indicator_pos == QAbstractItemView.DropIndicatorPosition.BelowItem:
                    target_parent_item = target_item_at_drop.parent() or self.tree.invisibleRootItem()
                    insert_index = target_parent_item.indexOfChild(target_item_at_drop) + 1
                
                else: # Should not happen with valid drop indicator
                    event.ignore()
                    self.dragged_item_instance = None # Clean up
                    return
            else:
                # Dropped in an empty area of the tree, append to the invisible root item
                target_parent_item = self.tree.invisibleRootItem()
                insert_index = target_parent_item.childCount()

            # Prevent dropping an item onto itself or into its own children
            check_item = target_parent_item
            while check_item and check_item != self.tree.invisibleRootItem():
                if check_item == source_item:
                    event.ignore()
                    self.dragged_item_instance = None # Clean up
                    return
                check_item = check_item.parent()
            
            # If target_parent_item ended up being source_item itself (e.g. dropping "on" a folder that is the source_item)
            if target_parent_item == source_item:
                event.ignore()
                self.dragged_item_instance = None # Clean up
                return

            # Perform the move
            original_parent = source_item.parent() or self.tree.invisibleRootItem()
            original_index = original_parent.indexOfChild(source_item)

            if original_parent == target_parent_item and original_index == insert_index:
                # No actual move needed (dropped in the same place)
                event.ignore()
                self.dragged_item_instance = None # Clean up
                return

            # Take the item from its original position
            # takeChild returns the item, so we use source_item directly
            original_parent.takeChild(original_index)

            # Adjust insert_index if moving within the same parent and item was taken from before the insert position
            if original_parent == target_parent_item and original_index < insert_index:
                insert_index -= 1
            
            # Add or insert the item into the new parent
            if insert_index < 0 or insert_index > target_parent_item.childCount(): # Safety check for index
                target_parent_item.addChild(source_item)
            else:
                target_parent_item.insertChild(insert_index, source_item)

            # Ensure the moved item is selected and visible
            source_item.setSelected(True)
            self.tree.setCurrentItem(source_item)
            self.tree.scrollToItem(source_item)

            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
            # self.dragged_item_instance = None # Done in start_drag finally

        elif event.mimeData().hasUrls():
            self._handle_url_drop(event)
        else:
            # Fall back to default handler for other types of internal drags
            self.tree._old_dropEvent(event)
        
        # Clean up dragged_item_instance if drop not handled by our logic or if an error occurred
        # This is primarily handled in start_drag's finally block if drag.exec() completes
        # but good to be defensive. However, start_drag should be the sole clearer.
        # If _drop_event is called, drag.exec() is still in progress.
        # self.dragged_item_instance = None
    
    def _handle_url_drop(self, event):
        """
        Handle dropping URLs (files) onto the tree
        
        Args:
            event: Drop event containing URLs
        """
        from PyQt6.QtWidgets import QMessageBox
        
        # Determine the drop target item
        drop_item = self.tree.itemAt(event.position().toPoint())
        if not drop_item:
            drop_item = self.tree.invisibleRootItem()
            
        # Check if drop target is a file (can only drop into folders)
        item_data = drop_item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(item_data, dict) and item_data.get('type') == 'file':
            # Get the parent (can't drop onto a file)
            parent = drop_item.parent()
            if parent:
                drop_item = parent
            else:
                drop_item = self.tree.invisibleRootItem()
        
        # Provide visual feedback during drop
        self.tree.setProperty("drop-in-progress", True)
        self.tree.style().polish(self.tree)
        
        try:
            # Process each URL
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                
                # Skip if empty
                if not file_path:
                    continue
                    
                # Check if it's a directory or a file
                if os.path.isdir(file_path):
                    self._process_dropped_directory(file_path, drop_item)
                else:
                    self._process_dropped_file(file_path, drop_item)
                    
            # Accept the drop action
            event.acceptProposedAction()
            
            # Force an icon refresh to ensure all icons are properly displayed
            self.refresh_icons()
        except Exception as e:
            print(f"ERROR: Failed to process dropped URLs: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Reset drag feedback
            self.tree.setProperty("drop-in-progress", False)
            self.tree.style().polish(self.tree)
    
    def _process_dropped_file(self, file_path, parent_item):
        """
        Process a dropped file
        
        Args:
            file_path: Path to the dropped file
            parent_item: Parent tree item to add the file to
            
        Returns:
            QTreeWidgetItem: The created file item or None if failed
        """
        try:
            # Ensure file exists
            if not os.path.exists(file_path):
                print(f"DEBUG: File not found: {file_path}")
                return None
            
            # Get just the file name
            file_name = os.path.basename(file_path)
            
            # Skip .DS_Store and hidden files
            if file_name.startswith('.') or file_name == '.DS_Store':
                print(f"DEBUG: Skipping hidden file or .DS_Store: {file_name}")
                return None
            
            # Determine if this is a binary file
            is_binary = BinaryFileHandler.is_binary_file(file_path)
            should_embed = False
            
            if is_binary:
                print(f"DEBUG: Detected binary file: {file_name}")
                should_embed = BinaryFileHandler.should_embed_binary_file(file_path)
                if should_embed:
                    print(f"DEBUG: Binary file {file_name} will be embedded in structure")
                else:
                    print(f"DEBUG: Binary file {file_name} will be cached during template save")
            
            # Create a file hash for identification
            file_hash = None
            try:
                import hashlib
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                print(f"DEBUG: File hash for {file_name}: {file_hash}")
            except Exception as e:
                print(f"ERROR: Failed to create hash for file {file_name}: {e}")
                # Create a default hash from the file path as fallback
                file_hash = hashlib.md5(file_path.encode('utf-8')).hexdigest()
                print(f"DEBUG: Created fallback hash for {file_name}: {file_hash}")
            
            # Create a new tree item for the file
            file_item = QTreeWidgetItem(parent_item)
            file_item.setText(0, file_name)
            
            # Set icon based on file type
            from .utils import get_file_icon_for_type
            file_item.setIcon(0, get_file_icon_for_type(file_name))
            
            # Make the item editable
            file_item.setFlags(file_item.flags() | Qt.ItemFlag.ItemIsEditable)
            
            # Get template name from the editor if available
            template_name = "Unknown Template"
            if hasattr(self.editor, 'template_name'):
                template_name = self.editor.template_name
            elif hasattr(self.editor, 'name_input') and hasattr(self.editor.name_input, 'text'):
                template_name = self.editor.name_input.text()
            
            # Get relative path in the tree structure for later use
            relative_path = ""
            if hasattr(self.editor, 'file_ops') and hasattr(self.editor.file_ops, '_get_relative_path'):
                relative_path = self.editor.file_ops._get_relative_path(file_item)
            
            # Store complete file metadata
            file_data = {
                'type': 'file',
                'name': file_name,
                'path': file_path,
                'original_path': file_path,
                'is_binary': is_binary,
                'should_embed': should_embed,
                'cache_hash': file_hash,
                'relative_path': relative_path,
                'template_name': template_name
            }
            
            # Set special visual indicator for binary files
            if is_binary:
                # Light purple for binary files
                file_item.setForeground(0, QBrush(QColor(180, 120, 220)))
            else:
                # Add visual indicator that file is tracked but not yet cached
                file_item.setForeground(0, QBrush(QColor('#88AADD')))  # Light blue
            
            # Store the data in the tree item
            file_item.setData(0, Qt.ItemDataRole.UserRole, file_data)
            
            # Store reference to the file in the editor's cache tracking if available
            if hasattr(self.editor, 'files_to_cache'):
                self.editor.files_to_cache[relative_path] = {
                    "original_path": file_path,
                    "relative_path": relative_path,
                    "template_name": template_name,
                    "cache_hash": file_hash
                }
            
            return file_item
            
        except Exception as e:
            print(f"ERROR: Failed to process dropped file: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _add_file_to_tree(self, file_path, parent_item=None):
        """
        Add a file to the tree
        
        Args:
            file_path: Path to the file to add
            parent_item: Parent tree item to add to
        
        Returns:
            QTreeWidgetItem: The created file item
        """
        if not parent_item:
            parent_item = self.tree.invisibleRootItem()
        
        # Get file name
        file_name = os.path.basename(file_path)
        
        # Create a file item
        file_item = QTreeWidgetItem(parent_item)
        file_item.setText(0, file_name)
        file_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        
        # Check if it's a binary file
        is_binary = BinaryFileHandler.is_binary_file(file_path)
        
        # Get template name from the editor if available
        template_name = "Unknown Template"
        if hasattr(self.editor, 'template_name'):
            template_name = self.editor.template_name
        elif hasattr(self.editor, 'name_input') and hasattr(self.editor.name_input, 'text'):
            template_name = self.editor.name_input.text()
        
        # Get relative path for later use in caching
        relative_path = ""
        if hasattr(self.editor, 'file_ops') and hasattr(self.editor.file_ops, '_get_relative_path'):
            relative_path = self.editor.file_ops._get_relative_path(file_item)
        
        # Create file hash
        file_hash = None
        try:
            import hashlib
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            print(f"Error calculating file hash: {e}")
            # Fallback to path-based hash
            file_hash = hashlib.md5(file_path.encode('utf-8')).hexdigest()
        
        # Store file data
        file_data = {
            'type': 'file',
            'name': file_name,
            'path': file_path,
            'original_path': file_path,
            'is_binary': is_binary,
            'cache_hash': file_hash,
            'relative_path': relative_path,
            'template_name': template_name
        }
        file_item.setData(0, Qt.ItemDataRole.UserRole, file_data)
        
        # Set visual indicator
        if is_binary:
            # Light purple for binary files
            file_item.setForeground(0, QBrush(QColor(180, 120, 220)))
        else:
            # Light blue for tracked files
            file_item.setForeground(0, QBrush(QColor('#88AADD')))
        
        # Make the item editable
        file_item.setFlags(file_item.flags() | Qt.ItemFlag.ItemIsEditable)
        
        # Store reference to the file in the editor's cache tracking if available
        if hasattr(self.editor, 'files_to_cache'):
            self.editor.files_to_cache[relative_path] = {
                "original_path": file_path,
                "relative_path": relative_path,
                "template_name": template_name,
                "cache_hash": file_hash
            }
        
        return file_item
    
    def _add_directory_to_tree(self, dir_path, parent_item=None, folder_name=None):
        """
        Add a directory to the tree
        
        Args:
            dir_path: Directory path to add
            parent_item: Parent tree item to add to
            folder_name: Optional folder name override
        
        Returns:
            QTreeWidgetItem: The created folder item
        """
        if not parent_item:
            parent_item = self.tree.invisibleRootItem()
        
        # If this is the first call, get just the directory name
        if not folder_name:
            folder_name = os.path.basename(dir_path)
        
        # Create a folder item
        folder_item = QTreeWidgetItem(parent_item)
        folder_item.setText(0, folder_name)
        folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        
        # Store folder data
        folder_data = {
            'type': 'folder',
            'name': folder_name,
            'path': dir_path,
            'children': []  # Initialize empty children array
        }
        folder_item.setData(0, Qt.ItemDataRole.UserRole, folder_data)
        
        # Make the item editable
        folder_item.setFlags(folder_item.flags() | Qt.ItemFlag.ItemIsEditable)
        
        # Process all the contents
        try:
            # Get directory contents, sorted alphabetically with folders first
            dir_contents = []
            try:
                # Get the list of all files and directories
                contents = os.listdir(dir_path)
                # Split into files and dirs
                dirs = []
                files = []
                for item in contents:
                    # Skip hidden files and .DS_Store
                    if item.startswith('.') or item == '.DS_Store':
                        continue
                    
                    full_path = os.path.join(dir_path, item)
                    if os.path.isdir(full_path):
                        dirs.append(item)
                    else:
                        files.append(item)
                
                # Sort both lists and combine with directories first
                dirs.sort()
                files.sort()
                dir_contents = dirs + files
            except Exception as e:
                print(f"Error listing directory contents: {e}")
                return folder_item
            
            # Process each item
            for item_name in dir_contents:
                item_path = os.path.join(dir_path, item_name)
                
                if os.path.isdir(item_path):
                    # Recursively add the directory
                    self._add_directory_to_tree(item_path, folder_item)
                else:
                    # Add the file
                    self._add_file_to_tree(item_path, folder_item)
            
            # Expand the folder
            folder_item.setExpanded(True)
        except Exception as e:
            print(f"Error processing directory: {e}")
        
        return folder_item
    
    def _mouse_press_event(self, event):
        """
        Handle mouse press events for drag detection
        
        Args:
            event: Mouse press event
        """
        # Store the position for drag detection
        if event.button() == Qt.MouseButton.LeftButton:
            self.tree._drag_start_position = event.pos()
        
        # Call the original handler
        self.tree._old_mousePressEvent(event)
    
    def _mouse_move_event(self, event):
        """
        Handle mouse move events for drag start
        
        Args:
            event: Mouse move event
        """
        # Check if we should start a drag
        if (hasattr(self.tree, '_drag_start_position') and
                event.buttons() & Qt.MouseButton.LeftButton and
                (event.pos() - self.tree._drag_start_position).manhattanLength() >= 10):
            
            # Get the item at the drag start position
            item = self.tree.itemAt(self.tree._drag_start_position)
            if item:
                # Start the drag
                self.start_drag(item)
                return  # Don't call the original handler
        
        # Call the original handler
        self.tree._old_mouseMoveEvent(event)
    
    def start_drag(self, item):
        """Start a drag operation"""
        if not item:
            return

        # Store the item instance being dragged
        self.dragged_item_instance = item
            
        # Get item data
        item_name = item.text(0)
        item_type = item.data(0, Qt.ItemDataRole.UserRole).get('type', 'unknown')
            
        # Create mime data
        mime_data = QMimeData()
        drag_data = {
            'name': item_name,
            'type': item_type,
            'source_widget': self.tree.objectName() # Store source widget id
        }
        mime_data.setData("application/x-echelon-template-item", json.dumps(drag_data).encode('utf-8'))
        
        # Create drag object
        drag = QDrag(self.tree)
        drag.setMimeData(mime_data)
        
        # Create a simple pixmap for the drag preview (e.g., from the item itself)
        item_rect = item.treeWidget().visualItemRect(item)
        pixmap = QPixmap(item_rect.size())
        if not pixmap.isNull():
            pixmap.fill(Qt.GlobalColor.transparent) # Fill with transparent to handle item background
            painter = QPainter(pixmap)
            painter.setOpacity(0.7) # Make it slightly transparent
            
            # Setup style options for drawing the item
            option = QStyleOptionViewItem()
            option.rect = QRect(QPoint(0,0), item_rect.size()) # Draw at the pixmap's origin
            option.state = QStyle.StateFlag.State_Enabled # Basic state
            # If the item is selected, you might want to reflect that in the drag pixmap
            if item.isSelected():
                option.state |= QStyle.StateFlag.State_Selected
            # Add other relevant states if necessary, e.g., State_HasFocus
            
            # Get the model index for the item
            model_index = self.tree.indexFromItem(item)
            
            # Ensure the tree has a style before calling initFrom
            if self.tree.style():
                option.initFrom(self.tree) # Initialize with tree's style options

            item.treeWidget().drawRow(painter, option, model_index)
            painter.end()
            drag.setPixmap(pixmap)
            # Set hotspot to the mouse cursor position relative to the pixmap's top-left
            drag.setHotSpot(self.tree.viewport().mapFromGlobal(QCursor.pos()) - item_rect.topLeft())
        else:
            # Fallback if pixmap creation failed (e.g. item not visible)
            # A small default pixmap can be used or just proceed without one
            pass # Or create a default small icon

        print(f"DEBUG: Starting drag for '{item_name}' ('{item_type}')")
        
        # Execute drag operation
        # In PyQt6, these are Qt.DropAction.MoveAction and Qt.DropAction.CopyAction
        try:
            result = drag.exec(Qt.DropAction.MoveAction | Qt.DropAction.CopyAction)
        finally:
            # Clear the stored dragged item instance regardless of drag outcome
            self.dragged_item_instance = None
        
        if result == Qt.DropAction.MoveAction:
            print(f"DEBUG: Drag operation resulted in MoveAction for '{item_name}'")
            # Handle move (e.g., remove from original position if not handled by drop event)
        elif result == Qt.DropAction.CopyAction:
            print(f"DEBUG: Drag operation resulted in CopyAction for '{item_name}'")
        else:
            print(f"DEBUG: Drag operation cancelled or failed for '{item_name}'")
    
    def enable_external_drops(self, enabled=True):
        """
        Enable or disable dropping external files onto the tree
        
        Args:
            enabled: Whether to enable external drops
            
        Returns:
            bool: Previous state
        """
        if not self.tree:
            return False
            
        # Store old state
        old_state = self.tree.acceptDrops()
        
        # Set new state
        self.tree.setAcceptDrops(enabled)
        
        # Update drag drop mode
        if enabled:
            self.tree.setDragDropMode(self.tree.DragDrop)
        else:
            self.tree.setDragDropMode(self.tree.InternalMove)
        
        return old_state
    
    def refresh_icons(self):
        """Refresh all icons in the structure tree"""
        if not self.tree:
            return
        
        try:
            # Use centralized icon refresh utility for consistent icon handling
            from app.ui.icon_utilities import _refresh_widget_item_icons
            
            # Process all top-level items
            root = self.tree.invisibleRootItem()
            for i in range(root.childCount()):
                _refresh_widget_item_icons(root.child(i))
            
            print("DEBUG: Icons refreshed using central icon utility")
        except ImportError:
            # Fallback to old method if import fails
            # Process all top-level items
            root = self.tree.invisibleRootItem()
            for i in range(root.childCount()):
                self._refresh_icons_recursive(root.child(i))
            
            print("DEBUG: Icons refreshed using fallback method")
    
    def _refresh_icons_recursive(self, item):
        """
        Recursively refresh icons for an item and its children
        
        Args:
            item: The tree item to refresh
        """
        if not item:
            return
        
        # Apply icon to this item
        self._apply_icon_to_item(item)
        
        # Process children
        for i in range(item.childCount()):
            self._refresh_icons_recursive(item.child(i))
    
    def apply_item_icons(self):
        """Apply appropriate icons to all items in the tree"""
        if not self.tree:
            return
        
        # Start from root
        root = self.tree.invisibleRootItem()
        
        # Process all top-level items
        for i in range(root.childCount()):
            self._apply_icons_recursive(root.child(i))
        
        print("DEBUG: Icons applied to all items")
    
    def _apply_icons_recursive(self, item):
        """Apply icons recursively to an item and its children"""
        if not item:
            return
        
        # Apply icon to this item
        self._apply_icon_to_item(item)
        
        # Process children
        for i in range(item.childCount()):
            self._apply_icons_recursive(item.child(i))
    
    def _setup_drag_drop(self):
        """Configure the tree widget for drag and drop"""
        # Enable drag and drop
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        
        # Set drag and drop mode
        self.tree.setDragDropMode(self.tree.InternalMove)
        
        # Custom event handlers for drag and drop
        self.tree.dragEnterEvent = self._drag_enter_event
        self.tree.dragMoveEvent = self._drag_move_event
        self.tree.dropEvent = self._drop_event
    
    def _setup_styling(self):
        """Configure styling for drag and drop indicators"""
        # Get colors
        try:
            from app.ui.color_scheme_pyqt import colors
        except ImportError:
            # Default colors if import fails
            colors = {
                'accent': '#007ACC',
                'accent_light': '#338ACC',
                'border': '#444444',
                'text': '#FFFFFF',
                'card_bg': '#2D2D2D'
            }
        
        # Create stylesheet for drop indicators
        drop_indicator_style = f"""
            QTreeWidget::item:selected {{
                background-color: {colors['accent']};
                color: {colors['text']};
            }}
            
            QTreeWidget::item:hover {{
                background-color: {colors['accent_light']};
                color: {colors['text']};
            }}
            
            QTreeWidget::indicator {{
                width: 16px;
                height: 16px;
            }}
        """
        
        # Apply stylesheet
        self.tree.setStyleSheet(drop_indicator_style)
    
    def _apply_icon_to_item(self, item):
        """Apply appropriate icon to an item based on its type"""
        if not item:
            return
            
        # Get item data
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        
        # Validate data
        if not isinstance(item_data, dict) or 'type' not in item_data:
            return
            
        item_type = item_data.get('type')
        item_name = item_data.get('name', item.text(0))
        
        if item_type == 'folder':
            # Use platform-specific folder icons
            import platform
            if platform.system() == "Windows":
                # On Windows, use the standard system folder icon
                try:
                    # Make sure QApplication is initialized
                    app = QApplication.instance()
                    if not app:
                        print("ERROR: QApplication not initialized")
                    else:
                        # Get the icon using standard icon enum
                        folder_icon = app.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
                        
                        # Debug output
                        print(f"DEBUG: Windows folder icon retrieved, null: {folder_icon.isNull()}")
                        
                        if not folder_icon.isNull():
                            # Set the icon to the tree item
                            item.setIcon(0, folder_icon)
                            # Also set a distinctive font to make folders stand out
                            font = item.font(0)
                            font.setBold(True)
                            item.setFont(0, font)
                        else:
                            # Fallback if system icon is null
                            print("WARNING: Windows system folder icon is null, using fallback")
                            # Try a direct system icon as fallback
                            if hasattr(QStyle, "StandardPixmap"):
                                # PyQt6 approach
                                fallback_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)
                            else:
                                # PyQt5 approach
                                fallback_icon = QApplication.style().standardIcon(QStyle.SP_FileDialogNewFolder)
                                
                            item.setIcon(0, fallback_icon)
                except Exception as e:
                    print(f"ERROR: Failed to get Windows system folder icon: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Create a simple folder icon as fallback
                    pixmap = QPixmap(16, 16)
                    pixmap.fill(QColor(255, 255, 255, 0))  # Transparent
                    painter = QPainter(pixmap)
                    painter.setPen(QColor("#FFC107"))  # Yellow
                    painter.setBrush(QColor("#FFC107"))
                    painter.drawRect(2, 3, 12, 10)
                    painter.end()
                    folder_icon = QIcon(pixmap)
                    item.setIcon(0, folder_icon)
            else:
                # For macOS/Linux, use the existing approach
                # 1. Use the provided folders.png icon from assets
                folder_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                            "assets", "icons", "folder.png")
                    
                # 2. Check if the specific icon exists in our assets
                if not os.path.exists(folder_icon_path):
                    folder_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                                "icons", "folder.png")
                    
                # 3. Use system theme icons if file doesn't exist
                if os.path.exists(folder_icon_path):
                    folder_icon = QIcon(folder_icon_path)
                else:
                    # Use system theme icon with fallback
                    folder_icon = QIcon.fromTheme("folder", QIcon())
                    if folder_icon.isNull():
                        # Create a simple folder icon if system theme failed
                        pixmap = QPixmap(16, 16)
                        pixmap.fill(QColor(255, 255, 255, 0))  # Transparent
                        painter = QPainter(pixmap)
                        painter.setPen(QColor("#90CAF9"))  # Light blue
                        painter.setBrush(QColor("#90CAF9"))
                        painter.drawRect(2, 3, 12, 10)
                        painter.end()
                        folder_icon = QIcon(pixmap)
                
                # Apply folder icon
                item.setIcon(0, folder_icon)
            
            # Use bold text for folders instead of blue color
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
        
        elif item_type == 'file':
            # Use file type specific icon
            file_icon = self._get_file_icon(item_name)
            item.setIcon(0, file_icon)
            
            # Style based on file type
            self._style_file_item(item, item_name)
        
        # Recursively apply to children
        for i in range(item.childCount()):
            child_item = item.child(i)
            self._apply_icon_to_item(child_item)
    
    def _get_file_icon(self, filename):
        """
        Get an appropriate icon for a file based on its type
        
        Args:
            filename: Name of the file
            
        Returns:
            QIcon: Icon for the file
        """
        # Check common custom locations first
        file_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                    'assets', 'icons', 'templates', 'file_icon.svg')
                                    
        if os.path.exists(file_icon_path):
            return QIcon(file_icon_path)
        
        # Try to get from utils function
        try:
            icon = get_file_icon_for_type(filename)
            if icon and not icon.isNull():
                return icon
        except Exception as e:
            print(f"Error getting file icon: {e}")
        
        # Try system theme icons
        file_icon = QIcon.fromTheme("text-x-generic", QIcon())
        if not file_icon.isNull():
            return file_icon
        
        # Create a simple file icon as last resort
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(255, 255, 255, 0))  # Transparent
        painter = QPainter(pixmap)
        painter.setPen(QColor("#E0E0E0"))  # Light gray
        painter.setBrush(QColor("#E0E0E0"))
        painter.drawRect(2, 1, 12, 14)
        painter.setPen(QColor("#AAAAAA"))  # Gray lines for text
        painter.drawLine(4, 4, 12, 4)
        painter.drawLine(4, 7, 12, 7)
        painter.drawLine(4, 10, 8, 10)
        painter.end()
        
        return QIcon(pixmap)
    
    def _style_file_item(self, item, filename):
        """Apply styling to a file item based on its type"""
        ext = os.path.splitext(filename)[1].lower()
        
        # Color mappings for file types
        colors = {
            # Code files - blue
            'code': QColor("#42A5F5"),
            # Web files - orange
            'web': QColor("#FF9800"),
            # Documents - green
            'doc': QColor("#66BB6A"),
            # Images - purple
            'image': QColor("#AB47BC"),
            # Config files - yellow
            'config': QColor("#FFC107"),
            # Executables - red
            'executable': QColor("#F44336"),
            # Default - light gray
            'default': QColor("#BDBDBD")
        }
        
        # Determine file type
        file_type = 'default'
        
        if ext in ('.py', '.js', '.java', '.c', '.cpp', '.h', '.cs', '.php', '.rb', '.go', '.swift'):
            file_type = 'code'
        elif ext in ('.html', '.htm', '.css', '.ts', '.jsx', '.tsx'):
            file_type = 'web'
        elif ext in ('.txt', '.md', '.doc', '.docx', '.pdf', '.rtf'):
            file_type = 'doc'
        elif ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg'):
            file_type = 'image'
        elif ext in ('.json', '.yaml', '.yml', '.xml', '.ini', '.conf', '.config', '.toml'):
            file_type = 'config'
        elif ext in ('.exe', '.bat', '.sh', '.app'):
            file_type = 'executable'
        
        # Apply color based on file type
        item.setForeground(0, QBrush(colors[file_type]))
        
        # Apply font styling for certain file types
        font = item.font(0)
        
        # Bold for important files
        if file_type in ('executable', 'config'):
            font.setBold(True)
            
        # Italic for documentation files
        if file_type == 'doc' or filename.lower() in ('readme.md', 'license', 'contributing.md'):
            font.setItalic(True)
        
        item.setFont(0, font)
    
    def _process_dropped_directory(self, dir_path, parent_item):
        """
        Process a dropped directory recursively
        
        Args:
            dir_path: Path to the directory
            parent_item: Parent tree item to add the directory to
        """
        try:
            # Normalize path and get directory name
            dir_path = os.path.normpath(dir_path)
            dir_name = os.path.basename(dir_path)
            
            # Skip hidden directories
            if dir_name.startswith('.'):
                print(f"DEBUG: Skipping hidden directory: {dir_name}")
                return None
            
            # Check for duplicates when dropping at the root level
            if parent_item == self.tree.invisibleRootItem():
                root = self.tree.invisibleRootItem()
                for i in range(root.childCount()):
                    child = root.child(i)
                    child_data = child.data(0, Qt.ItemDataRole.UserRole)
                    
                    if (isinstance(child_data, dict) and 
                        child_data.get('type') == 'folder' and 
                        child.text(0) == dir_name):
                        
                        # Ask if the user wants to replace or add
                        from PyQt6.QtWidgets import QMessageBox
                        reply = QMessageBox.question(
                            self.tree,
                            "Duplicate Folder",
                            f"A folder named '{dir_name}' already exists. What would you like to do?",
                            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                            QMessageBox.Cancel
                        )
                        
                        if reply == QMessageBox.Yes:
                            # Remove existing folder (Replace)
                            root.removeChild(child)
                            break
                        elif reply == QMessageBox.Cancel:
                            # Skip this directory
                            return None
                        # If No (Add), just continue
            
            # Create a folder item
            folder_item = QTreeWidgetItem(parent_item)
            folder_item.setText(0, dir_name)
            
            # Set folder icon
            # Try to get system folder icon
            folder_icon = QIcon.fromTheme("folder")
            if folder_icon.isNull():
                # Fallback to standard icon if available
                folder_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
            
            folder_item.setIcon(0, folder_icon)
            
            # Make the folder editable
            folder_item.setFlags(folder_item.flags() | Qt.ItemFlag.ItemIsEditable)
            
            # Store folder data
            folder_data = {
                'type': 'folder',
                'name': dir_name,
                'path': dir_path
            }
            folder_item.setData(0, Qt.ItemDataRole.UserRole, folder_data)
            
            # Process directory contents
            try:
                # List directory contents
                for item_name in sorted(os.listdir(dir_path)):
                    # Skip hidden files and .DS_Store
                    if item_name.startswith('.') or item_name == '.DS_Store':
                        continue
                    
                    item_path = os.path.join(dir_path, item_name)
                    
                    # Process subdirectories and files
                    if os.path.isdir(item_path):
                        self._process_dropped_directory(item_path, folder_item)
                    else:
                        self._process_dropped_file(item_path, folder_item)
            except Exception as e:
                print(f"ERROR: Failed to process directory contents: {e}")
                import traceback
                traceback.print_exc()
            
            # Expand the folder to show its contents
            folder_item.setExpanded(True)
            
            return folder_item
            
        except Exception as e:
            print(f"ERROR: Failed to process dropped directory: {e}")
            import traceback
            traceback.print_exc()
            return None 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Tree Operations Module
Handles tree widget manipulation, navigation, and state management
"""

from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtCore import Qt


class TreeOperations:
    """Handles tree widget operations and navigation"""
    
    def __init__(self, file_operations):
        """Initialize tree operations handler"""
        self.file_operations = file_operations
        
    def expand_all_items(self, tree_widget):
        """Expand all items in the tree"""
        if not tree_widget:
            return
        
        tree_widget.expandAll()

    def collapse_all_items(self, tree_widget):
        """Collapse all items in the tree"""
        if not tree_widget:
            return
        
        tree_widget.collapseAll()

    def select_all_items(self, tree_widget):
        """Select all items in the tree"""
        if not tree_widget:
            return
        
        tree_widget.selectAll()

    def clear_selection(self, tree_widget):
        """Clear all selections in the tree"""
        if not tree_widget:
            return
        
        tree_widget.clearSelection()

    def get_all_items(self, tree_widget):
        """Get all items in the tree as a flat list"""
        if not tree_widget:
            return []
        
        items = []
        
        def collect_items(item):
            items.append(item)
            for i in range(item.childCount()):
                collect_items(item.child(i))
        
        # Collect from root level
        for i in range(tree_widget.topLevelItemCount()):
            collect_items(tree_widget.topLevelItem(i))
        
        return items

    def get_selected_items(self, tree_widget):
        """Get all currently selected items"""
        if not tree_widget:
            return []
        
        return tree_widget.selectedItems()

    def find_item_by_text(self, tree_widget, text, column=0):
        """Find an item by its text content"""
        if not tree_widget or not text:
            return None
        
        all_items = self.get_all_items(tree_widget)
        for item in all_items:
            if item.text(column) == text:
                return item
        
        return None

    def find_items_by_pattern(self, tree_widget, pattern, column=0):
        """Find items matching a pattern"""
        if not tree_widget or not pattern:
            return []
        
        import re
        matching_items = []
        all_items = self.get_all_items(tree_widget)
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            for item in all_items:
                if regex.search(item.text(column)):
                    matching_items.append(item)
        except re.error:
            # If pattern is invalid regex, do literal search
            pattern_lower = pattern.lower()
            for item in all_items:
                if pattern_lower in item.text(column).lower():
                    matching_items.append(item)
        
        return matching_items

    def get_item_path(self, item):
        """Get the full path of an item from root"""
        if not item:
            return []
        
        path = []
        current = item
        
        while current:
            path.insert(0, current.text(0))
            current = current.parent()
        
        return path

    def get_item_depth(self, item):
        """Get the depth of an item in the tree"""
        if not item:
            return -1
        
        depth = 0
        current = item.parent()
        
        while current:
            depth += 1
            current = current.parent()
        
        return depth

    def is_item_ancestor_of(self, ancestor, descendant):
        """Check if one item is an ancestor of another"""
        if not ancestor or not descendant:
            return False
        
        current = descendant.parent()
        while current:
            if current == ancestor:
                return True
            current = current.parent()
        
        return False

    def get_common_ancestor(self, items):
        """Get the common ancestor of a list of items"""
        if not items:
            return None
        
        if len(items) == 1:
            return items[0].parent()
        
        # Get paths for all items
        paths = [self.get_item_path(item) for item in items]
        
        # Find common prefix
        if not paths:
            return None
        
        common_path = []
        min_length = min(len(path) for path in paths)
        
        for i in range(min_length):
            if all(path[i] == paths[0][i] for path in paths):
                common_path.append(paths[0][i])
            else:
                break
        
        # Find the item with this path
        if not common_path:
            return None
        
        # Navigate to the common ancestor
        tree_widget = items[0].treeWidget()
        if not tree_widget:
            return None
        
        current = None
        for i in range(tree_widget.topLevelItemCount()):
            top_item = tree_widget.topLevelItem(i)
            if top_item.text(0) == common_path[0]:
                current = top_item
                break
        
        if not current:
            return None
        
        # Navigate down the path
        for path_part in common_path[1:]:
            found = False
            for i in range(current.childCount()):
                child = current.child(i)
                if child.text(0) == path_part:
                    current = child
                    found = True
                    break
            if not found:
                return None
        
        return current.parent() if len(common_path) > 1 else None

    def move_item_up(self, tree_widget, item):
        """Move an item up in its parent's children"""
        if not item or not tree_widget:
            return False
        
        parent = item.parent()
        if parent:
            index = parent.indexOfChild(item)
            if index > 0:
                parent.takeChild(index)
                parent.insertChild(index - 1, item)
                tree_widget.setCurrentItem(item)
                return True
        else:
            # Top level item
            index = tree_widget.indexOfTopLevelItem(item)
            if index > 0:
                tree_widget.takeTopLevelItem(index)
                tree_widget.insertTopLevelItem(index - 1, item)
                tree_widget.setCurrentItem(item)
                return True
        
        return False

    def move_item_down(self, tree_widget, item):
        """Move an item down in its parent's children"""
        if not item or not tree_widget:
            return False
        
        parent = item.parent()
        if parent:
            index = parent.indexOfChild(item)
            if index < parent.childCount() - 1:
                parent.takeChild(index)
                parent.insertChild(index + 1, item)
                tree_widget.setCurrentItem(item)
                return True
        else:
            # Top level item
            index = tree_widget.indexOfTopLevelItem(item)
            if index < tree_widget.topLevelItemCount() - 1:
                tree_widget.takeTopLevelItem(index)
                tree_widget.insertTopLevelItem(index + 1, item)
                tree_widget.setCurrentItem(item)
                return True
        
        return False

    def sort_children(self, item, column=0, ascending=True):
        """Sort the children of an item"""
        if not item:
            return
        
        if item.childCount() <= 1:
            return
        
        # Get all children
        children = []
        while item.childCount() > 0:
            children.append(item.takeChild(0))
        
        # Sort children
        children.sort(key=lambda x: x.text(column).lower(), reverse=not ascending)
        
        # Add back sorted children
        for child in children:
            item.addChild(child)

    def sort_tree(self, tree_widget, column=0, ascending=True):
        """Sort the entire tree"""
        if not tree_widget:
            return
        
        # Sort top level items
        tree_widget.sortItems(column, Qt.SortOrder.AscendingOrder if ascending else Qt.SortOrder.DescendingOrder)
        
        # Sort children of each item
        all_items = self.get_all_items(tree_widget)
        for item in all_items:
            if item.childCount() > 0:
                self.sort_children(item, column, ascending)

    def get_tree_statistics(self, tree_widget):
        """Get statistics about the tree"""
        if not tree_widget:
            return {}
        
        all_items = self.get_all_items(tree_widget)
        
        # Count by type
        folders = 0
        files = 0
        
        for item in all_items:
            item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
            if item_data.get('is_folder', False):
                folders += 1
            else:
                files += 1
        
        # Calculate depths
        depths = [self.get_item_depth(item) for item in all_items]
        max_depth = max(depths) if depths else 0
        avg_depth = sum(depths) / len(depths) if depths else 0
        
        return {
            'total_items': len(all_items),
            'folders': folders,
            'files': files,
            'max_depth': max_depth,
            'average_depth': round(avg_depth, 2),
            'top_level_items': tree_widget.topLevelItemCount()
        }

    def validate_tree_structure(self, tree_widget):
        """Validate the tree structure for consistency"""
        if not tree_widget:
            return []
        
        issues = []
        all_items = self.get_all_items(tree_widget)
        
        # Check for duplicate names at same level
        level_names = {}
        for item in all_items:
            parent = item.parent()
            parent_key = id(parent) if parent else 'root'
            
            if parent_key not in level_names:
                level_names[parent_key] = []
            
            name = item.text(0)
            if name in level_names[parent_key]:
                issues.append(f"Duplicate name '{name}' at same level")
            else:
                level_names[parent_key].append(name)
        
        # Check for empty names
        for item in all_items:
            if not item.text(0).strip():
                issues.append("Item with empty name found")
        
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for item in all_items:
            name = item.text(0)
            for char in invalid_chars:
                if char in name:
                    issues.append(f"Invalid character '{char}' in name '{name}'")
        
        return issues

    def backup_tree_state(self, tree_widget):
        """Create a backup of the current tree state"""
        if not tree_widget:
            return None
        
        def serialize_item(item):
            item_data = {
                'text': item.text(0),
                'data': item.data(0, Qt.ItemDataRole.UserRole),
                'expanded': item.isExpanded(),
                'selected': item.isSelected(),
                'children': []
            }
            
            for i in range(item.childCount()):
                item_data['children'].append(serialize_item(item.child(i)))
            
            return item_data
        
        tree_state = {
            'items': [],
            'current_item': None
        }
        
        # Serialize all top-level items
        for i in range(tree_widget.topLevelItemCount()):
            tree_state['items'].append(serialize_item(tree_widget.topLevelItem(i)))
        
        # Store current item
        current = tree_widget.currentItem()
        if current:
            tree_state['current_item'] = self.get_item_path(current)
        
        return tree_state

    def restore_tree_state(self, tree_widget, tree_state):
        """Restore tree from a backup state"""
        if not tree_widget or not tree_state:
            return False
        
        try:
            # Clear current tree
            tree_widget.clear()
            
            def restore_item(item_data, parent=None):
                if parent:
                    item = QTreeWidgetItem(parent)
                else:
                    item = QTreeWidgetItem(tree_widget)
                
                item.setText(0, item_data['text'])
                if item_data['data']:
                    item.setData(0, Qt.ItemDataRole.UserRole, item_data['data'])
                
                # Restore children
                for child_data in item_data['children']:
                    restore_item(child_data, item)
                
                # Restore state
                item.setExpanded(item_data.get('expanded', False))
                item.setSelected(item_data.get('selected', False))
                
                return item
            
            # Restore all items
            for item_data in tree_state['items']:
                restore_item(item_data)
            
            # Restore current item
            if tree_state.get('current_item'):
                path = tree_state['current_item']
                item = self.find_item_by_path(tree_widget, path)
                if item:
                    tree_widget.setCurrentItem(item)
            
            return True
            
        except Exception as e:
            print(f"Error restoring tree state: {e}")
            return False

    def find_item_by_path(self, tree_widget, path):
        """Find an item by its path"""
        if not tree_widget or not path:
            return None
        
        # Start from root
        current = None
        for i in range(tree_widget.topLevelItemCount()):
            item = tree_widget.topLevelItem(i)
            if item.text(0) == path[0]:
                current = item
                break
        
        if not current:
            return None
        
        # Navigate down the path
        for path_part in path[1:]:
            found = False
            for i in range(current.childCount()):
                child = current.child(i)
                if child.text(0) == path_part:
                    current = child
                    found = True
                    break
            if not found:
                return None
        
        return current 
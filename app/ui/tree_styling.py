#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Tree widget styling module
Provides centralized styling for tree widgets
"""

import sys
import os
from PyQt5.QtWidgets import QTreeWidget, QWidget, QAbstractItemView, QApplication, QTreeWidgetItem
from PyQt5.QtCore import Qt, QSize

# Import the application color scheme
from app.ui.color_scheme_pyqt import APP_COLORS
from app.constants import get_resource_path
from app.ui.icon_utilities import get_folder_icon, get_file_icon

def apply_tree_styling(tree_widget):
    """
    Apply consistent styling to a QTreeWidget
    
    Args:
        tree_widget: The QTreeWidget to style
    """
    if not tree_widget or not isinstance(tree_widget, QTreeWidget):
        print(f"WARNING: Cannot style non-tree widget: {type(tree_widget)}")
        return
    
    # Configure basic appearance
    tree_widget.setAlternatingRowColors(True)
    tree_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
    tree_widget.setAllColumnsShowFocus(True)
    tree_widget.setUniformRowHeights(True)
    tree_widget.setAnimated(True)
    
    # Ensure branch indicators are visible
    tree_widget.setRootIsDecorated(True)
    tree_widget.setItemsExpandable(True)
    
    # Set icon size for better visibility
    tree_widget.setIconSize(QSize(20, 20))
    
    # Override indentation to improve visual hierarchy
    tree_widget.setIndentation(24)
    
    # Hide header if it exists (common for structure editors)
    tree_widget.setHeaderHidden(True)
    
    # Apply enhanced styling with visible branch indicators
    apply_enhanced_tree_styling(tree_widget)
    
    # Update icons for all existing items
    update_tree_item_icons(tree_widget)

def apply_enhanced_tree_styling(tree_widget):
    """
    Apply enhanced styling with visible branch indicators and folder styling
    
    Args:
        tree_widget: The QTreeWidget to style
    """
    if not tree_widget or not isinstance(tree_widget, QTreeWidget):
        return
    
    # Get absolute paths to branch indicator SVGs using the resource path helper
    branch_closed_path = get_resource_path('app/assets/css/branch-closed.svg')
    branch_open_path = get_resource_path('app/assets/css/branch-open.svg')
    
    # Apply custom stylesheet for consistent appearance
    # Use the application color scheme for consistency
    tree_widget.setStyleSheet(f"""
        QTreeWidget {{
            background-color: {APP_COLORS['card_bg']};
            color: {APP_COLORS['text']};
            border: 1px solid {APP_COLORS['border']};
            outline: none;
            alternate-background-color: {APP_COLORS['card_bg_alt']};
            font-size: 13px;
        }}
        
        QTreeWidget::item {{
            border: none;
            border-bottom: 1px solid {APP_COLORS['border']};
            padding: 4px 2px;
            min-height: 24px;
        }}
        
        QTreeWidget::item:selected {{
            background-color: {APP_COLORS['highlight_bg']};
            color: {APP_COLORS['highlight_text']};
        }}
        
        QTreeWidget::item:hover:!selected {{
            background-color: {APP_COLORS['hover_bg']};
        }}
        
        /* Ensure branch indicators are visible while maintaining styling */
        QTreeWidget::branch {{
            background-color: transparent;
        }}
        
        /* Style branch when selected for consistent color */
        QTreeWidget::branch:selected {{
            background-color: {APP_COLORS['highlight_bg']};
        }}
        
        /* Style branch indicators to ensure they're visible */
        QTreeWidget::branch:has-children:!has-siblings:closed,
        QTreeWidget::branch:closed:has-children:has-siblings {{
            image: url({branch_closed_path});
            width: 15px;
            height: 15px;
        }}
        
        QTreeWidget::branch:open:has-children:!has-siblings,
        QTreeWidget::branch:open:has-children:has-siblings {{
            image: url({branch_open_path});
            width: 15px;
            height: 15px;
        }}
        
        /* Style for folder items to make them stand out */
        QTreeWidget::item:has-children {{
            font-weight: bold;
        }}
    """)
    
    # Update icons for all existing items after styling
    update_tree_item_icons(tree_widget)

def update_tree_item_icons(tree_widget):
    """
    Update icons for all items in the tree based on whether they are folders or files
    
    Args:
        tree_widget: The QTreeWidget to update icons for
    """
    if not tree_widget or not isinstance(tree_widget, QTreeWidget):
        return
        
    # Process all items starting with the root
    root = tree_widget.invisibleRootItem()
    for i in range(root.childCount()):
        update_item_icon(root.child(i))
        
def update_item_icon(item):
    """
    Update the icon for a tree item based on whether it's a folder or file
    
    Args:
        item: The QTreeWidgetItem to update
    """
    if not item:
        return
        
    # Check if item is a folder or file
    is_folder = False
    
    # First check if there's stored data indicating type
    item_type = item.data(0, Qt.UserRole)
    if item_type == "folder":
        is_folder = True
    elif item_type == "file":
        is_folder = False
    else:
        # If no explicit data, use heuristic checks
        # Items with children are folders
        if item.childCount() > 0:
            is_folder = True
        else:
            # Check the text for file extension
            text = item.text(0)
            if '.' in text and not text.endswith('/'):
                # Has extension, likely a file
                is_folder = False
            else:
                # Assume folder if it has no extension
                is_folder = True
    
    # Set appropriate icon
    if is_folder:
        # For folders, use open folder icon if expanded
        is_expanded = item.isExpanded()
        item.setIcon(0, get_folder_icon(is_expanded))
        
        # Store folder type in data
        if not item_type:
            item.setData(0, Qt.UserRole, "folder")
    else:
        # For files, get icon based on file extension
        item.setIcon(0, get_file_icon(item.text(0)))
        
        # Store file type in data
        if not item_type:
            item.setData(0, Qt.UserRole, "file")
    
    # Process all children recursively
    for i in range(item.childCount()):
        update_item_icon(item.child(i))

def setup_tree_for_structure_editing(tree_widget):
    """Configure a tree widget for structure editing with good user experience"""
    if not tree_widget:
        return
        
    # Make sure the tree widget is set up for editing
    from PyQt5.QtWidgets import QAbstractItemView, QTreeWidgetItem
    from PyQt5.QtCore import Qt
    
    # Import custom delegate
    from app.ui.tree_item_delegate import TreeItemDelegate
    
    # Apply enhanced styling with visible branch indicators
    apply_enhanced_tree_styling(tree_widget)
    
    # Configure edit triggers - essential for editing to work properly
    # Setting all triggers to ensure maximum compatibility
    tree_widget.setEditTriggers(
        QAbstractItemView.DoubleClicked |
        QAbstractItemView.EditKeyPressed |
        QAbstractItemView.SelectedClicked |
        QAbstractItemView.CurrentChanged 
    )
    
    # Enable drag and drop operations
    tree_widget.setDragEnabled(True)
    tree_widget.setAcceptDrops(True)
    tree_widget.setDropIndicatorShown(True)
    tree_widget.setDragDropMode(QAbstractItemView.InternalMove)
    
    # Set selection behavior and mode
    tree_widget.setSelectionBehavior(QAbstractItemView.SelectItems)
    tree_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
    
    # Create and set custom item delegate - enhanced for editing
    delegate = TreeItemDelegate(tree_widget)
    tree_widget.setItemDelegate(delegate)
    
    # Fix a common issue: make sure existing items are editable
    root = tree_widget.invisibleRootItem()
    for i in range(root.childCount()):
        ensure_item_editable(root.child(i))
    
    # Connect to expanded/collapsed signals to update folder icons
    tree_widget.itemExpanded.connect(lambda item: update_folder_icon_on_expand(item, True))
    tree_widget.itemCollapsed.connect(lambda item: update_folder_icon_on_expand(item, False))
    
    print("DEBUG: Tree widget set up for structure editing with enhanced delegate")
    print("DEBUG: Applied enhanced tree styling with folder/file icons")

def update_folder_icon_on_expand(item, expanded):
    """Update folder icon when item is expanded or collapsed"""
    if not item:
        return
        
    # Check if this is a folder item
    item_type = item.data(0, Qt.UserRole)
    if item_type == "folder" or item.childCount() > 0:
        # Update icon based on expanded state
        item.setIcon(0, get_folder_icon(expanded))
        
def ensure_item_editable(item):
    """Make sure an item and all its children are editable"""
    if not item:
        return
        
    from PyQt5.QtCore import Qt
    
    # Make the item editable
    item.setFlags(item.flags() | Qt.ItemIsEditable)
    
    # Process all children recursively
    for i in range(item.childCount()):
        ensure_item_editable(item.child(i))

def apply_styling_to_all_tree_widgets(parent_widget=None):
    """
    Apply styling to all QTreeWidget instances in the application
    
    Args:
        parent_widget: Parent widget to search from (optional)
    
    Returns:
        int: Number of tree widgets styled
    """
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    
    try:
        from app.ui.tree_item_delegate import TreeItemDelegate
    except ImportError:
        # If the custom delegate is not available, we'll continue without it
        print("WARNING: TreeItemDelegate not available, using standard delegate")
        TreeItemDelegate = None
    
    count = 0
    
    # Start with top level widgets if no parent specified
    if parent_widget is None:
        widgets_to_process = QApplication.topLevelWidgets()
    else:
        widgets_to_process = [parent_widget]
    
    # Process all widgets recursively
    for widget in widgets_to_process:
        # If this is a tree widget, style it and set up editing
        if isinstance(widget, QTreeWidget):
            # Apply enhanced styling
            apply_enhanced_tree_styling(widget)
            
            # Apply custom delegate if available
            if TreeItemDelegate:
                delegate = TreeItemDelegate(widget)
                widget.setItemDelegate(delegate)
            
            # Make sure existing items are editable
            root = widget.invisibleRootItem()
            for i in range(root.childCount()):
                ensure_item_editable(root.child(i))
                
            # Connect to expanded/collapsed signals to update folder icons
            widget.itemExpanded.connect(lambda item: update_folder_icon_on_expand(item, True))
            widget.itemCollapsed.connect(lambda item: update_folder_icon_on_expand(item, False))
            
            count += 1
        
        # Process all children recursively
        for child in widget.findChildren(QTreeWidget):
            # Apply enhanced styling
            apply_enhanced_tree_styling(child)
            
            # Apply custom delegate if available
            if TreeItemDelegate:
                delegate = TreeItemDelegate(child)
                child.setItemDelegate(delegate)
            
            # Make sure existing items are editable
            root = child.invisibleRootItem()
            for i in range(root.childCount()):
                ensure_item_editable(root.child(i))
                
            # Connect to expanded/collapsed signals to update folder icons
            child.itemExpanded.connect(lambda item: update_folder_icon_on_expand(item, True))
            child.itemCollapsed.connect(lambda item: update_folder_icon_on_expand(item, False))
                
            count += 1
    
    print(f"DEBUG: Applied styling to {count} tree widgets with platform-specific icons")
    return count 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Tree widget styling module
Provides centralized styling for tree widgets
"""

import sys
import os
from PyQt5.QtWidgets import QTreeWidget, QWidget, QAbstractItemView, QApplication, QTreeWidgetItem, QStyle
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QColor

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
    
    # Set icon size for better visibility - larger size for application icons
    tree_widget.setIconSize(QSize(9, 9))  # Reduced by 50% from 17x17
    
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
            font-size: 13px; /* Reverted from 10px */
        }}
        
        QTreeWidget::item {{
            border: none;
            border-bottom: 1px solid {APP_COLORS['border']};
            padding: 4px 2px; /* Reverted from 3px vertical padding */
            min-height: 24px; /* Reverted from 18px */
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
            width: 5px; /* Reduced by 50% from 10px */
            height: 5px; /* Reduced by 50% from 10px */
        }}
        
        QTreeWidget::branch:open:has-children:!has-siblings,
        QTreeWidget::branch:open:has-children:has-siblings {{
            image: url({branch_open_path});
            width: 5px; /* Reduced by 50% from 10px */
            height: 5px; /* Reduced by 50% from 10px */
        }}
        
        /* Style for folder items to make them stand out */
        QTreeWidget::item:has-children {{
            font-weight: bold;
        }}
        
        /* Ensure icons are displayed properly */
        QTreeWidget::item:has-children:!selected {{
            padding-left: 2px;
        }}
        
        QTreeWidget::item:!has-children:!selected {{
            padding-left: 2px;
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
        # is_expanded = item.isExpanded()
        # item.setIcon(0, get_folder_icon(is_expanded))

        # Directly use QApplication.style().standardIcon like in TemplateDirectoryEditor
        if item.isExpanded():
            folder_icon = QApplication.style().standardIcon(QStyle.SP_DirOpenIcon)
            if folder_icon.isNull(): # Fallback if SP_DirOpenIcon is not available
                folder_icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)
        else:
            folder_icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)
        item.setIcon(0, folder_icon)
        
        # Store folder type in data
        if not item_type:
            item.setData(0, Qt.UserRole, "folder")
    else:
        # For files, get icon based on file extension
        filename = item.text(0)
        
        # Get file extension for color coding
        ext = ''
        if '.' in filename:
            ext = filename.split('.')[-1].lower()
        
        # Use the platform native icon system
        icon = get_file_icon(filename)
        item.setIcon(0, icon)
        
        # Apply appropriate colors based on extension
        apply_color_by_extension(item, ext)
            
    # Update icons for children recursively
    for i in range(item.childCount()):
        update_item_icon(item.child(i))

def apply_color_by_extension(item, ext):
    """
    Apply color coding to tree items based on file extension category
    
    Args:
        item: The QTreeWidgetItem to colorize
        ext: The file extension (without the dot)
    """
    if not ext:
        return
        
    ext = ext.lower()
    
    # Color mapping by extension type
    color_mapping = {
        # Video applications (blue/cyan range)
        'prproj': QColor(0, 180, 255),  # Premiere Pro - Light blue
        'aep': QColor(160, 120, 255),   # After Effects - Purple
        'aepx': QColor(160, 120, 255),  # After Effects - Purple
        'fcpx': QColor(45, 145, 235),   # Final Cut - Blue
        'fcpxml': QColor(45, 145, 235), # Final Cut - Blue
        'drp': QColor(240, 90, 40),     # DaVinci Resolve - Orange
        'dra': QColor(240, 90, 40),     # DaVinci Resolve - Orange
        'avp': QColor(0, 164, 227),     # Avid - Light blue
        'avb': QColor(0, 164, 227),     # Avid - Light blue
        
        # Adobe applications
        'psd': QColor(49, 168, 255),    # Photoshop - Blue
        'ai': QColor(255, 128, 0),      # Illustrator - Orange
        'indd': QColor(236, 0, 140),    # InDesign - Pink
        
        # 3D applications
        'ma': QColor(120, 220, 120),    # Maya - Green
        'mb': QColor(120, 220, 120),    # Maya - Green
        'blend': QColor(242, 103, 34),  # Blender - Orange
        'c4d': QColor(0, 132, 200),     # Cinema 4D - Blue
        
        # Audio applications
        'ptx': QColor(180, 180, 0),     # Pro Tools - Yellow
        'pts': QColor(180, 180, 0),     # Pro Tools - Yellow  
        'logic': QColor(220, 100, 100), # Logic - Red
        
        # Media file formats
        'mov': QColor(80, 180, 80),     # QuickTime - Green
        'mp4': QColor(80, 200, 120),    # MP4 - Green-blue
        'mxf': QColor(100, 230, 100),   # MXF - Bright green
        'wav': QColor(230, 180, 80),    # WAV - Gold
        'mp3': QColor(200, 160, 40),    # MP3 - Light gold
        'aif': QColor(230, 160, 40),    # AIF - Gold
        
        # Document formats
        'pdf': QColor(220, 60, 60),     # PDF - Red
        'docx': QColor(40, 100, 180),   # Word - Blue
        'xlsx': QColor(40, 140, 40),    # Excel - Green
        'pptx': QColor(200, 80, 40),    # PowerPoint - Orange
    }
    
    # Apply color if extension is in the mapping
    if ext in color_mapping:
        item.setForeground(0, color_mapping[ext])

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
    
    # Set icon mode to display icons at highest quality
    tree_widget.setProperty("iconSize", QSize(28, 28))
    
    # Force icon visibility by enabling it explicitly
    tree_widget.viewport().setAttribute(Qt.WA_AlwaysShowToolTips)
    
    # Explicitly update all icons in the tree to ensure proper display
    # This is particularly important for structure editing where icons need to be visible
    update_tree_item_icons(tree_widget)
    
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
            
            # Ensure icons are displayed at a reasonable size
            # widget.setIconSize(QSize(28, 28)) # Removed this override
            
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
            
            # Ensure icons are displayed at a reasonable size
            # child.setIconSize(QSize(28, 28)) # Removed this override
            
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

def refresh_all_tree_icons():
    """Force refresh all tree widget icons to ensure they use the latest icons"""
    from app.ui.icon_utilities import clear_icon_cache
    
    # First, explicitly clear the icon cache to force fresh icon retrieval
    clear_icon_cache()
    
    # Get the application instance
    app = QApplication.instance()
    if not app:
        return 0
        
    # Find all QTreeWidgets in the application
    refresh_count = 0
    for widget in app.allWidgets():
        if isinstance(widget, QTreeWidget):
            # Force icon refresh in this tree widget
            for i in range(widget.topLevelItemCount()):
                item = widget.topLevelItem(i)
                _refresh_tree_item_icons(item)
                refresh_count += 1
                
    return refresh_count

def _refresh_tree_item_icons(item):
    """Recursively refresh icons for a tree item and its children"""
    if not item:
        return
        
    # Get the item's data if it has any
    item_data = item.data(0, Qt.UserRole)
    
    # If the item has data, update its icon based on the data type and content
    if item_data:
        from app.ui.icon_utilities import get_file_icon, get_folder_icon
        
        # Handle different data types - dictionary is most common in the structure editor
        if isinstance(item_data, dict):
            item_type = item_data.get('type', '')
            if item_type == 'folder':
                # It's a folder item
                item.setIcon(0, get_folder_icon(item.isExpanded()))
            elif item_type == 'file':
                # It's a file item
                file_name = item_data.get('name', item.text(0))
                item.setIcon(0, get_file_icon(file_name))
        # Handle string path
        elif isinstance(item_data, str):
            # Check if it's a directory or a file if it exists
            is_dir = os.path.isdir(item_data) if os.path.exists(item_data) else False
            
            if is_dir:
                # Use folder icon
                item.setIcon(0, get_folder_icon(item.isExpanded()))
            else:
                # Use file icon
                item.setIcon(0, get_file_icon(item_data))
        # Default handling for other data types
        else:
            # Use item text and children count to determine icon
            is_folder = item.childCount() > 0
            if is_folder:
                item.setIcon(0, get_folder_icon(item.isExpanded()))
            else:
                item.setIcon(0, get_file_icon(item.text(0)))
    else:
        # No data - use item text and children count to determine icon
        is_folder = item.childCount() > 0
        if is_folder:
            item.setIcon(0, get_folder_icon(item.isExpanded()))
        else:
            item.setIcon(0, get_file_icon(item.text(0)))
    
    # Recursively refresh children's icons
    for i in range(item.childCount()):
        child = item.child(i)
        _refresh_tree_item_icons(child) 
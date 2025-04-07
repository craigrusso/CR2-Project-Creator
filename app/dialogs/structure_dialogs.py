#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Dialog windows for displaying and editing project structures.
"""

import os
import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTreeWidget, QTreeWidgetItem,
                           QApplication, QStyle)
from PyQt5.QtCore import Qt

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.ui.structure_editor_functions import show_enhanced_structure_editor

def preview_structure(app, structure):
    """Show a preview of the project structure"""
    print("PREVIEW_STRUCTURE FUNCTION CALLED WITH:")
    print(json.dumps(structure, indent=2))
    
    dialog = QDialog(app)
    dialog.setWindowTitle("Structure Preview")
    dialog.resize(500, 400)
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(15, 15, 15, 15)
    layout.setSpacing(10)
    
    # Add a header
    header_label = QLabel("Project Structure Preview")
    header_label.setStyleSheet(f"color: {colors['text']}; font-size: 16px; font-weight: bold;")
    layout.addWidget(header_label)
    
    # Create a tree widget to display the structure
    tree = QTreeWidget(dialog)
    tree.setHeaderHidden(True)
    tree.setAlternatingRowColors(True)  # Improves readability
    tree.setExpandsOnDoubleClick(True)  # Enable expand/collapse on double-click
    tree.setAnimated(True)  # Smoother folder expansion
    tree.setVerticalScrollMode(QTreeWidget.ScrollPerPixel)  # Ensures smooth scrolling
    tree.setHorizontalScrollMode(QTreeWidget.ScrollPerPixel)
    tree.setStyleSheet(f"""
        QTreeWidget {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            padding: 5px;
        }}
        QTreeWidget::item {{
            padding: 5px;
        }}
        QTreeWidget::item:selected {{
            background-color: {colors['hover_bg']};
        }}
    """)
    
    # Add root project item
    root_item = QTreeWidgetItem(tree)
    root_item.setText(0, "Project Root")
    root_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
    root_item.setExpanded(True)
    
    # Import needed for file icons
    from PyQt5.QtWidgets import QFileIconProvider
    from PyQt5.QtCore import QFileInfo
    icon_provider = QFileIconProvider()
    
    # Helper function to get file icon by extension
    def get_file_icon(file_name):
        """Get proper system icon for a file based on its extension"""
        from PyQt5.QtGui import QIcon
        import os
        
        # Get file extension
        _, file_ext = os.path.splitext(file_name.lower())
        
        # Try to use custom icons which are more visually distinctive
        try:
            # Import directly for better icons
            from PyQt5.QtWidgets import QStyle
            
            # File type constants - these provide more distinct icons than QFileIconProvider
            VIDEO_ICON = QApplication.style().standardIcon(QStyle.SP_MediaPlay)
            AUDIO_ICON = QApplication.style().standardIcon(QStyle.SP_MediaVolume)
            IMAGE_ICON = QApplication.style().standardIcon(QStyle.SP_DesktopIcon)
            DOC_ICON = QApplication.style().standardIcon(QStyle.SP_FileDialogDetailedView)
            CODE_ICON = QApplication.style().standardIcon(QStyle.SP_FileDialogContentsView)
            ADOBE_ICON = QApplication.style().standardIcon(QStyle.SP_FileLinkIcon)
            
            # More specific file type mapping
            # Video files
            if file_ext in ['.mp4', '.mov', '.avi', '.mkv', '.mxf', '.webm', '.wmv', '.flv']:
                return VIDEO_ICON
                
            # Audio files    
            elif file_ext in ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a', '.aif', '.aiff']:
                return AUDIO_ICON
                
            # Image files
            elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg', '.psd']:
                return IMAGE_ICON
                
            # Document files
            elif file_ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.xls', '.xlsx', '.ppt', '.pptx']:
                return DOC_ICON
                
            # Code files
            elif file_ext in ['.py', '.js', '.html', '.css', '.json', '.xml', '.cpp', '.c', '.h', '.java']:
                return CODE_ICON
                
            # Adobe project files - use different icon than normal files
            elif file_ext in ['.prproj', '.aep', '.aepx', '.psd', '.ai', '.indd']:
                return ADOBE_ICON
                
            # Now try the system icon provider as a fallback
            from PyQt5.QtCore import QFileInfo
            from PyQt5.QtWidgets import QFileIconProvider
            icon_provider = QFileIconProvider()
            
            # For project name placeholders with extension
            if '{PROJECT_NAME}' in file_name and '.' in file_name:
                ext = '.' + file_name.split('.')[-1].split()[0]  # Get extension before any emoji
                
                # Re-use our custom mapping first
                if ext in ['.mp4', '.mov', '.avi', '.mkv', '.mxf', '.webm', '.wmv', '.flv']:
                    return VIDEO_ICON
                elif ext in ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a', '.aif', '.aiff']:
                    return AUDIO_ICON
                elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg', '.psd']:
                    return IMAGE_ICON
                elif ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.xls', '.xlsx', '.ppt', '.pptx']:
                    return DOC_ICON
                elif ext in ['.py', '.js', '.html', '.css', '.json', '.xml', '.cpp', '.c', '.h', '.java']:
                    return CODE_ICON
                elif ext in ['.prproj', '.aep', '.aepx', '.psd', '.ai', '.indd']:
                    return ADOBE_ICON
                    
                # If our mapping failed, try system icon
                temp_file = f"temp{ext}"
                file_info = QFileInfo(temp_file)
                system_icon = icon_provider.icon(file_info)
                if not system_icon.isNull():
                    return system_icon
            
            # For regular files without special handling above
            if not '{PROJECT_NAME}' in file_name:
                file_info = QFileInfo(file_name)
                system_icon = icon_provider.icon(file_info)
                if not system_icon.isNull():
                    return system_icon
                
        except Exception as e:
            print(f"Error getting file icon: {e}")
        
        # Last resort - use generic file icon
        return QApplication.style().standardIcon(QStyle.SP_FileIcon)
    
    # Helper function to add items recursively
    def add_items(parent_item, items):
        print(f"Adding items to {parent_item.text(0)}: {items}")
        for item in items:
            if isinstance(item, dict):
                # It's a directory (either with children or empty)
                for dir_name, children in item.items():
                    dir_item = QTreeWidgetItem(parent_item)
                    dir_item.setText(0, dir_name)
                    dir_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                    dir_item.setExpanded(True)
                    # Mark as folder in data
                    dir_item.setData(0, Qt.UserRole, "folder")
                    # Add children if any exist
                    if children:
                        add_items(dir_item, children)
            elif isinstance(item, list):
                # It's a list of items
                add_items(parent_item, item)
            elif isinstance(item, str):
                # It's a file or legacy empty directory format
                child_item = QTreeWidgetItem(parent_item)
                
                # Check if it's a folder first
                is_folder = False
                
                # Common file extensions that should ALWAYS be files
                file_extensions = ['.prproj', '.aep', '.aepx', '.psd', '.ai', '.mp4', '.mov', '.jpg', '.jpeg', 
                                  '.png', '.txt', '.html', '.css', '.js', '.json', '.xml', '.pdf', '.doc', 
                                  '.docx', '.xls', '.xlsx', '.mp3', '.wav']
                
                # Check for project name placeholder with icon indicator
                is_project_file = '{PROJECT_NAME}' in item and '.' in item
                has_file_emoji = '🔄' in item
                
                # Special check for Adobe project files to ensure they're always files
                is_adobe_file = any(item.lower().endswith(ext) for ext in ['.prproj', '.aep', '.aepx', '.psd', '.ai', '.indd'])
                
                # Check if it has a known file extension - always treat as a file
                has_known_extension = any(item.lower().endswith(ext) for ext in file_extensions)
                
                # If it has a known file extension or is a project name file, it's definitely a file
                if has_known_extension or is_project_file or has_file_emoji or is_adobe_file:
                    is_folder = False
                # Legacy format check  
                elif item.endswith('/'):
                    is_folder = True
                # No file extension (likely a folder)
                elif '.' not in item:
                    is_folder = True
                # Common numeric prefix pattern for folders (01_Footage)
                elif item.startswith(tuple("0123456789")) and '_' in item[:4]:
                    is_folder = True
                # Common folder keywords
                elif any(keyword in item.lower() for keyword in [
                    'folder', 'dir', 'footage', 'audio', 'video', 'gfx', 'exports',
                    'assets', 'renders', 'project', 'images', 'documents'
                ]):
                    is_folder = True
                
                if is_folder:
                    # It's a folder
                    folder_name = item.rstrip('/') if item.endswith('/') else item
                    child_item.setText(0, folder_name)
                    child_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                    # Mark as folder in data
                    child_item.setData(0, Qt.UserRole, "folder")
                else:
                    # It's a file
                    child_item.setText(0, item)
                    # Get proper icon for this file type
                    child_item.setIcon(0, get_file_icon(item))
                    # Mark as file in data
                    child_item.setData(0, Qt.UserRole, "file")
                    
                    # Set special data for project name placeholder files
                    if is_project_file or has_file_emoji:
                        child_item.setData(0, Qt.UserRole + 3, True)  # Mark as using project name
    
    # Add structure items
    add_items(root_item, structure)
    
    # Add tree to layout
    layout.addWidget(tree)
    
    # Close button
    close_button = QPushButton("Close")
    close_button.setStyleSheet(BUTTON_STYLE)
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)
    
    dialog.exec_()

def edit_template_structure(parent, template, structure_tab):
    """Open enhanced structure editor for the template"""
    print("DEBUG: edit_template_structure called")
    
    # Extract the template name from the template
    template_name = template.get('name', '')
    if not template_name and hasattr(template, '_name_input'):
        template_name = template._name_input.text()
    
    # Determine structure name
    structure_name = template.get('structure_name', '')
    if not structure_name and template_name:
        structure_name = f"Template_{template_name}"
    
    print(f"DEBUG: edit_template_structure - template_name={template_name}, structure_name={structure_name}")
    
    # Import needed modules
    from app.ui.structure_editor_functions import show_enhanced_structure_editor
    
    # Get template manager
    template_manager = None
    if hasattr(parent, 'template_manager'):
        template_manager = parent.template_manager
    elif hasattr(parent, 'app') and hasattr(parent.app, 'template_manager'):
        template_manager = parent.app.template_manager
    else:
        from app.templates.template_manager import TemplateManager
        template_manager = TemplateManager()
    
    # Get structure items
    structure_items = template.get('structure', [])
    
    # Dialog reference - store this for access by the callback
    dialog = None
    if hasattr(structure_tab, 'window'):
        dialog = structure_tab.window()
    elif hasattr(parent, 'window'):
        if callable(parent.window):
            dialog = parent.window()
        else:
            dialog = parent.window
    
    # Get tree widget
    tree = None
    if hasattr(structure_tab, 'structure_tree'):
        tree = structure_tab.structure_tree
    
    # Create a callback function to update the template
    def structure_edited_callback(result):
        """Callback for when structure is updated in the editor"""
        print(f"DEBUG: Structure editor callback received result: {result}")
        
        if not result:
            print("DEBUG: Structure editor was cancelled")
            return
        
        success, updated_structure, updated_structure_name = result
        
        if not success:
            print("DEBUG: Structure edit was not successful")
            return
        
        # Update template with new structure
        template['structure'] = updated_structure
        template['structure_name'] = updated_structure_name
        
        print(f"DEBUG: Updated template with new structure. Name: {updated_structure_name}")
        
        # Update the structure tree if available
        if tree and hasattr(template, '_root_item'):
            root_item = template._root_item
            # Clear existing items
            for i in range(root_item.childCount()-1, -1, -1):
                root_item.removeChild(root_item.child(i))
            # Add new items
            populate_structure_tree(root_item, updated_structure)
            print("DEBUG: Updated structure tree view")
    
    # Set focus_name_field if this is a new template
    focus_name_field = template_name == ''
    
    # Open the enhanced structure editor for editing
    show_enhanced_structure_editor(
        parent=parent,
        structure_name=structure_name,
        structure=structure_items,
        is_new=template_name == '',
        template_name=template_name,
        focus_name_field=focus_name_field,
        template_manager=template_manager,
        callback=structure_edited_callback
    )
    
    print("DEBUG: Structure editor opened successfully")

def populate_structure_tree(parent_item, structure_items):
    """Populate a QTreeWidget with structure items"""
    if not structure_items:
        return
        
    for item in structure_items:
        if isinstance(item, dict):
            for folder_name, sub_items in item.items():
                folder_item = QTreeWidgetItem(parent_item)
                folder_item.setText(0, folder_name)
                folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                
                # Recursively add subitems
                populate_structure_tree(folder_item, sub_items)
        elif isinstance(item, str):
            # Determine if this is a folder or file
            is_folder = False
            
            # Common file extensions that should ALWAYS be files
            file_extensions = ['.prproj', '.aep', '.aepx', '.psd', '.ai', '.mp4', '.mov', '.jpg', '.jpeg', 
                              '.png', '.txt', '.html', '.css', '.js', '.json', '.xml', '.pdf', '.doc', 
                              '.docx', '.xls', '.xlsx', '.mp3', '.wav']
            
            # Check if it has a known file extension - always treat as a file
            has_known_extension = any(item.lower().endswith(ext) for ext in file_extensions)
            
            # If it has a known file extension, it's definitely a file
            if has_known_extension:
                is_folder = False
            # Check common folder patterns
            elif item.endswith('/'):
                # Legacy format folder
                is_folder = True
                item = item.rstrip('/')
            elif '.' not in item:
                # No extension - likely a folder
                is_folder = True
            elif item.startswith(tuple("0123456789")) and '_' in item[:4]:
                # Common folder pattern with numeric prefix (01_Footage)
                is_folder = True
            elif any(keyword in item.lower() for keyword in [
                'folder', 'dir', 'footage', 'audio', 'video', 'gfx', 'exports',
                'assets', 'renders', 'project', 'images', 'documents'
            ]):
                # Contains folder keywords
                is_folder = True
            
            # Create the item with appropriate icon
            tree_item = QTreeWidgetItem(parent_item)
            tree_item.setText(0, item)
            
            if is_folder:
                tree_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                # Store that this is a folder in the data
                tree_item.setData(0, Qt.UserRole, "folder")
            else:
                tree_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
                # Store that this is a file in the data
                tree_item.setData(0, Qt.UserRole, "file")

def import_template_structure(parent, template, structure_tab):
    """Import a structure from an existing template"""
    # This is a placeholder for the structure import function
    # The actual implementation would go here
    pass

def preview_template_structure(parent, template, structure_tab):
    """Preview the structure for a template"""
    # Get structure from template
    structure = template.get('structure', [])
    if not structure:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(parent, "No Structure", 
                           "This template has no structure defined yet.")
        return
        
    # Call the preview function
    preview_structure(parent, structure)

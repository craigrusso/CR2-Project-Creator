#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import webbrowser
import json
import copy
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTreeWidget, QTreeWidgetItem,
                           QMessageBox, QScrollArea, QWidget, QTabWidget, 
                           QTextEdit, QCheckBox, QListWidget, QLineEdit,
                           QInputDialog, QFileDialog, QApplication, QStyle,
                           QTabWidget, QGridLayout, QGroupBox, QRadioButton,
                           QButtonGroup, QComboBox, QSplitter, QSizePolicy,
                           QFrame, QSpinBox)
from PyQt5.QtCore import Qt, QSize, QByteArray, QUrl, QRegExp, QCoreApplication, QMimeData
from PyQt5.QtGui import QFont, QPixmap, QMovie, QIcon, QRegExpValidator, QDragEnterEvent, QDragMoveEvent, QDropEvent

from app.core.app_config import APP_NAME, APP_VERSION
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE
from app.utils.utils import get_config_paths, load_config, save_config
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

def show_batch_results(app, results):
    """Show the results of batch project creation"""
    # If results is None or False, don't show the dialog
    if not results:
        return
        
    dialog = QDialog(app)
    dialog.setWindowTitle("Batch Project Creation Results")
    dialog.resize(500, 400)
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(15, 15, 15, 15)
    layout.setSpacing(10)
    
    # Add a header
    header_label = QLabel("Batch Project Creation Results")
    header_label.setStyleSheet(f"color: {colors['text']}; font-size: 16px; font-weight: bold;")
    layout.addWidget(header_label)
    
    # Create a scrollable text area for the results
    results_area = QTextEdit()
    results_area.setReadOnly(True)
    results_area.setStyleSheet(f"""
        QTextEdit {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            padding: 10px;
        }}
    """)
    
    # Format and add the results
    results_text = ""
    success_count = 0
    
    # Check if results is a list of tuples from the project builder
    if isinstance(results, list) and len(results) > 0 and isinstance(results[0], tuple):
        for name, success, path in results:
            if success:
                success_count += 1
                results_text += f"<b style='color: #90EE90;'>✓ {name}</b><br>"
                results_text += f"&nbsp;&nbsp;&nbsp;Created at: {path}<br><br>"
            else:
                results_text += f"<b style='color: #FFA07A;'>✗ {name}</b><br>"
                results_text += f"&nbsp;&nbsp;&nbsp;Error: {path}<br><br>"
    else:
        # Handle legacy format or custom format
        for result in results:
            if isinstance(result, dict):
                project_name = result.get('name', 'Unknown')
                success = result.get('success', False)
                path = result.get('path', 'Not created')
                error = result.get('error', '')
                
                if success:
                    success_count += 1
                    results_text += f"<b style='color: #90EE90;'>✓ {project_name}</b><br>"
                    results_text += f"&nbsp;&nbsp;&nbsp;Created at: {path}<br><br>"
                else:
                    results_text += f"<b style='color: #FFA07A;'>✗ {project_name}</b><br>"
                    results_text += f"&nbsp;&nbsp;&nbsp;Error: {error}<br><br>"
    
    # Add summary
    total_count = len(results)
    summary = f"<b>Summary:</b> {success_count} of {total_count} projects created successfully."
    results_text = f"{summary}<br><br>{results_text}"
    
    results_area.setHtml(results_text)
    layout.addWidget(results_area)
    
    # Add buttons
    button_layout = QHBoxLayout()
    
    # Open folder button - only if at least one project was created
    if success_count > 0:
        from app.utils.utils import open_folder
        
        # Try to get the directory of the first successful project
        output_dir = None
        
        # Check which format we're dealing with
        if isinstance(results[0], tuple):
            for name, success, path in results:
                if success:
                    import os
                    output_dir = os.path.dirname(path)
                    break
        else:
            for result in results:
                if result.get('success', False):
                    path = result.get('path', '')
                    import os
                    output_dir = os.path.dirname(path)
                    break
        
        if output_dir:
            open_folder_btn = QPushButton("Open Folder")
            open_folder_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
            open_folder_btn.clicked.connect(lambda: open_folder(output_dir))
            button_layout.addWidget(open_folder_btn)
    
    # Close button
    close_button = QPushButton("Close")
    close_button.setStyleSheet(BUTTON_STYLE)
    close_button.clicked.connect(dialog.accept)
    button_layout.addWidget(close_button)
    
    layout.addLayout(button_layout)
    
    dialog.exec_()

def show_about(app):
    """Show the about dialog"""
    dialog = QDialog(app)
    dialog.setWindowTitle("About")
    dialog.resize(450, 300)
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(10)
    
    # App name and version
    title_label = QLabel(f"{APP_NAME} {APP_VERSION}")
    font = title_label.font()
    font.setBold(True)
    font.setPointSize(16)
    title_label.setFont(font)
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(title_label)
    
    # Copyright info
    copyright_label = QLabel("© 2023-present Craig P. Russo and CR2 Creative")
    copyright_label.setAlignment(Qt.AlignCenter)
    copyright_label.setStyleSheet(f"color: {colors['secondary_text']};")
    layout.addWidget(copyright_label)
    
    # Description
    description = QLabel(
        "CR2 Creative Pro is a professional project creation tool designed to "
        "streamline your workflow by creating consistent project structures and files "
        "from customizable templates."
    )
    description.setWordWrap(True)
    description.setAlignment(Qt.AlignCenter)
    description.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(description)
    
    # Spacer
    layout.addStretch()
    
    # Close button
    close_button = QPushButton("Close")
    close_button.setStyleSheet(BUTTON_STYLE)
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)
    
    dialog.exec_()

def show_tutorial(app):
    """Show the tutorial dialog"""
    dialog = QDialog(app)
    dialog.setWindowTitle("Tutorial")
    dialog.resize(600, 500)
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(10)
    
    # Title
    title_label = QLabel("Getting Started with CR2 Creative Pro")
    font = title_label.font()
    font.setBold(True)
    font.setPointSize(14)
    title_label.setFont(font)
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(title_label)
    
    # Tutorial content
    tab_widget = QTabWidget()
    tab_widget.setStyleSheet(f"""
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            background-color: {colors['card_bg']};
        }}
        QTabBar::tab {{
            background-color: {colors['bg']};
            color: {colors['text']};
            padding: 8px 12px;
            border: 1px solid {colors['border']};
            border-bottom: none;
        }}
        QTabBar::tab:selected {{
            background-color: {colors['card_bg']};
            border-bottom: none;
            border-top: 2px solid {colors['accent']};
        }}
    """)
    
    # Add tabs
    tabs = ["Templates", "Project Creation", "Customization"]
    
    for tab_name in tabs:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        
        # Placeholder content
        content = QLabel(f"{tab_name} tutorial content will be shown here.")
        content.setWordWrap(True)
        content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        content.setStyleSheet(f"color: {colors['text']};")
        tab_layout.addWidget(content)
        
        tab_widget.addTab(tab, tab_name)
    
    layout.addWidget(tab_widget)
    
    # Close button
    close_button = QPushButton("Close")
    close_button.setStyleSheet(BUTTON_STYLE)
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)
    
    dialog.exec_()

def show_preferences(app):
    """Show the application preferences dialog"""
    dialog = QDialog(app)
    dialog.setWindowTitle("Preferences")
    dialog.resize(600, 450)
    
    main_layout = QVBoxLayout(dialog)
    main_layout.setContentsMargins(15, 15, 15, 15)
    main_layout.setSpacing(10)
    
    # Create tab widget for different preference categories
    tabs = QTabWidget()
    
    # Get current configuration and paths
    config = load_config()
    paths = get_config_paths()
    
    # --- General Tab ---
    general_tab = QWidget()
    general_layout = QVBoxLayout(general_tab)
    
    # User Interface Group
    ui_group = QGroupBox("User Interface")
    ui_layout = QVBoxLayout(ui_group)
    
    # Dark mode option (placeholder for future implementation)
    dark_mode_check = QCheckBox("Use Dark Mode")
    dark_mode_check.setChecked(True)  # Default to checked
    dark_mode_check.setEnabled(False)  # Disabled for now
    ui_layout.addWidget(dark_mode_check)
    
    general_layout.addWidget(ui_group)
    general_layout.addStretch()
    
    # --- Storage Locations Tab ---
    storage_tab = QWidget()
    storage_layout = QGridLayout(storage_tab)
    storage_layout.setColumnStretch(1, 1)  # Make the path column expandable
    
    # Function to create a location row
    def add_location_row(row, label_text, path_key, path_value):
        # Label
        label = QLabel(label_text)
        storage_layout.addWidget(label, row, 0)
        
        # Path field
        path_field = QLineEdit()
        path_field.setText(path_value)
        path_field.setReadOnly(True)
        storage_layout.addWidget(path_field, row, 1)
        
        # Browse button
        browse_btn = QPushButton("Change...")
        
        def browse_for_directory():
            dir_path = QFileDialog.getExistingDirectory(
                dialog, f"Select {label_text} Directory", path_value)
            
            if dir_path:
                path_field.setText(dir_path)
                # Store the new path in the paths dictionary for saving later
                paths[path_key] = dir_path
                
        browse_btn.clicked.connect(browse_for_directory)
        storage_layout.addWidget(browse_btn, row, 2)
        
        # Open button
        open_btn = QPushButton("Open")
        
        def open_directory():
            from app.utils.utils import open_folder
            open_folder(path_value)
            
        open_btn.clicked.connect(open_directory)
        storage_layout.addWidget(open_btn, row, 3)
        
        return path_field
    
    # Add location fields
    row = 0
    config_dir_field = add_location_row(
        row, "Configuration Directory", "config_dir", paths["config_dir"])
    
    row += 1
    templates_dir_field = add_location_row(
        row, "Templates Directory", "templates_dir", paths["templates_dir"])
    
    row += 1
    structures_dir_field = add_location_row(
        row, "Custom Structures Directory", "custom_structures_dir", paths["custom_structures_dir"])
    
    # Add note about restarting
    row += 1
    note_label = QLabel("Note: Some location changes may require restarting the application.")
    note_label.setStyleSheet(f"color: {colors['secondary_text']}; font-style: italic;")
    storage_layout.addWidget(note_label, row, 0, 1, 4)
    
    # Add stretch at the bottom
    row += 1
    storage_layout.setRowStretch(row, 1)
    
    # Add the tabs to the tab widget
    tabs.addTab(general_tab, "General")
    tabs.addTab(storage_tab, "Storage Locations")
    
    # --- Cache Management Tab ---
    cache_tab = QWidget()
    cache_layout = QVBoxLayout(cache_tab)
    
    # Import necessary modules for cache management
    try:
        from app.utils.cache_preferences import CachePreferences
        from app.utils.file_cache_manager import FileCacheManager
        
        # Get current cache preferences
        cache_prefs = CachePreferences()
        
        # Enable file caching group
        caching_group = QGroupBox("File Caching Settings")
        caching_layout = QVBoxLayout(caching_group)
        
        # Enable caching checkbox
        enable_caching_check = QCheckBox("Enable file caching")
        enable_caching_check.setChecked(cache_prefs.should_cache_files())
        enable_caching_check.setToolTip("Cache files used in templates for better performance")
        caching_layout.addWidget(enable_caching_check)
        
        # Auto-clean cache
        auto_clean_check = QCheckBox("Automatically clean cache periodically")
        auto_clean_check.setChecked(cache_prefs.should_clean_cache())
        auto_clean_check.setToolTip("Remove old and unused cached files")
        caching_layout.addWidget(auto_clean_check)
        
        # Cache parameters grid
        params_layout = QGridLayout()
        
        # Cache location
        cache_location_label = QLabel("Cache Location:")
        params_layout.addWidget(cache_location_label, 0, 0)
        
        cache_location_field = QLineEdit()
        cache_location_field.setText(cache_prefs.get_cache_location())
        cache_location_field.setReadOnly(True)
        params_layout.addWidget(cache_location_field, 0, 1)
        
        cache_browse_btn = QPushButton("Change...")
        def browse_cache_location():
            dir_path = QFileDialog.getExistingDirectory(
                dialog, "Select Cache Directory", cache_location_field.text())
            if dir_path:
                cache_location_field.setText(dir_path)
        cache_browse_btn.clicked.connect(browse_cache_location)
        params_layout.addWidget(cache_browse_btn, 0, 2)
        
        cache_open_btn = QPushButton("Open")
        def open_cache_location():
            from app.utils.utils import open_folder
            open_folder(cache_location_field.text())
        cache_open_btn.clicked.connect(open_cache_location)
        params_layout.addWidget(cache_open_btn, 0, 3)
        
        # Maximum cache size
        max_size_label = QLabel("Maximum Cache Size (MB):")
        params_layout.addWidget(max_size_label, 1, 0)
        
        max_size_field = QSpinBox()
        max_size_field.setMinimum(100)  # 100MB minimum
        max_size_field.setMaximum(10000)  # 10GB maximum
        max_size_field.setValue(cache_prefs.get_preference("max_cache_size_mb", 1000))
        max_size_field.setSingleStep(100)
        params_layout.addWidget(max_size_field, 1, 1)
        
        # Maximum cache age
        max_age_label = QLabel("Maximum Cache Age (days):")
        params_layout.addWidget(max_age_label, 2, 0)
        
        max_age_field = QSpinBox()
        max_age_field.setMinimum(1)  # 1 day minimum
        max_age_field.setMaximum(365)  # 1 year maximum
        max_age_field.setValue(cache_prefs.get_preference("max_cache_age_days", 30))
        max_age_field.setSingleStep(1)
        params_layout.addWidget(max_age_field, 2, 1)
        
        caching_layout.addLayout(params_layout)
        
        # Cache statistics group
        stats_group = QGroupBox("Cache Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        # Get cache statistics
        cache_manager = FileCacheManager(cache_prefs.get_cache_location())
        cache_stats = cache_manager.get_cache_stats()
        
        # Display statistics in a grid
        stats_grid = QGridLayout()
        
        stats_grid.addWidget(QLabel("Total Files:"), 0, 0)
        stats_grid.addWidget(QLabel(str(cache_stats.get("cached_files", 0))), 0, 1)
        
        stats_grid.addWidget(QLabel("Total Size:"), 1, 0)
        stats_grid.addWidget(QLabel(cache_manager._human_readable_size(cache_stats.get("total_size", 0))), 1, 1)
        
        stats_grid.addWidget(QLabel("Cache Hits:"), 2, 0)
        stats_grid.addWidget(QLabel(str(cache_stats.get("hits", 0))), 2, 1)
        
        stats_grid.addWidget(QLabel("Cache Misses:"), 3, 0)
        stats_grid.addWidget(QLabel(str(cache_stats.get("misses", 0))), 3, 1)
        
        stats_layout.addLayout(stats_grid)
        
        # Cache maintenance buttons
        maintenance_layout = QHBoxLayout()
        
        clean_cache_btn = QPushButton("Clean Cache Now")
        def clean_cache():
            from PyQt5.QtWidgets import QMessageBox
            result = QMessageBox.question(dialog, "Clean Cache", 
                                         "Are you sure you want to clean the cache? This will remove old and unused files.")
            if result == QMessageBox.Yes:
                try:
                    files_removed = cache_manager.prune_cache(
                        max_age_days=max_age_field.value(),
                        max_size_mb=max_size_field.value()
                    )
                    # Update statistics
                    new_stats = cache_manager.get_cache_stats()
                    QMessageBox.information(dialog, "Cache Cleaned", 
                                         f"Cache cleaned successfully. {files_removed} files removed.")
                    # Refresh the stats display
                    # (This is a simple implementation - in a full version, we'd update the labels)
                except Exception as e:
                    QMessageBox.warning(dialog, "Error", f"Error cleaning cache: {e}")
        clean_cache_btn.clicked.connect(clean_cache)
        maintenance_layout.addWidget(clean_cache_btn)
        
        clear_cache_btn = QPushButton("Clear All Cache")
        def clear_cache():
            from PyQt5.QtWidgets import QMessageBox
            result = QMessageBox.warning(dialog, "Clear Cache", 
                                        "Are you sure you want to clear all cache? This will remove ALL cached files.")
            if result == QMessageBox.Yes:
                try:
                    cache_manager.clear_all_caches()
                    QMessageBox.information(dialog, "Cache Cleared", "All cache files have been removed.")
                    # Update statistics
                    # (This is a simple implementation - in a full version, we'd update the labels)
                except Exception as e:
                    QMessageBox.warning(dialog, "Error", f"Error clearing cache: {e}")
        clear_cache_btn.clicked.connect(clear_cache)
        maintenance_layout.addWidget(clear_cache_btn)
        
        stats_layout.addLayout(maintenance_layout)
        
        # Add the groups to the cache tab
        cache_layout.addWidget(caching_group)
        cache_layout.addWidget(stats_group)
        cache_layout.addStretch()
        
        # Save function for cache preferences
        def save_cache_preferences():
            cache_prefs.set_preference("enable_file_caching", enable_caching_check.isChecked())
            cache_prefs.set_preference("auto_clean_cache", auto_clean_check.isChecked())
            cache_prefs.set_preference("max_cache_size_mb", max_size_field.value())
            cache_prefs.set_preference("max_cache_age_days", max_age_field.value())
            cache_prefs.set_preference("cache_location", cache_location_field.text())
            cache_prefs.save_preferences()
        
    except ImportError as e:
        # If cache modules aren't available, show a message
        warning_label = QLabel("Cache management features are not available.")
        warning_details = QLabel(f"Error: {e}")
        warning_details.setStyleSheet("color: red;")
        cache_layout.addWidget(warning_label)
        cache_layout.addWidget(warning_details)
        cache_layout.addStretch()
        
        def save_cache_preferences():
            # No-op if modules not available
            pass
    
    # Add the cache tab to the tab widget
    tabs.addTab(cache_tab, "File Cache")
    
    # Add the tab widget to the main layout
    main_layout.addWidget(tabs)
    
    # Buttons layout
    buttons_layout = QHBoxLayout()
    
    # Cancel button
    cancel_button = QPushButton("Cancel")
    cancel_button.clicked.connect(dialog.reject)
    
    # Save button
    save_button = QPushButton("Save")
    save_button.setDefault(True)
    
    def save_preferences():
        # Save any changes to configuration
        save_config(config)
        
        # Create directories if they don't exist
        import os
        for dir_path in [paths["config_dir"], paths["templates_dir"], paths["custom_structures_dir"]]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
        
        # Update the config file with new paths if needed
        from app.utils.utils import save_json_file
        paths_file = os.path.join(paths["config_dir"], "paths.json")
        save_json_file(paths_file, paths)
        
        # Save cache preferences
        save_cache_preferences()
        
        # Close the dialog
        dialog.accept()
        
        # Show success message
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(app, "Preferences Saved", 
                             "Your preferences have been saved successfully.")
    
    save_button.clicked.connect(save_preferences)
    
    # Add buttons to layout
    buttons_layout.addStretch()
    buttons_layout.addWidget(cancel_button)
    buttons_layout.addWidget(save_button)
    
    main_layout.addLayout(buttons_layout)
    
    # Execute the dialog
    return dialog.exec_()

def show_edit_template(template, callback=None, app=None, gallery=None):
    """Show a dialog for editing a template
    
    Args:
        template: The template object to edit
        callback: Function to call with updated template if edit succeeds
        app: The main application instance
        gallery: The gallery widget
    
    Returns:
        bool: Whether the edit was successful
    """
    print(f"🔍 EDIT TEMPLATE: Starting template edit for '{template.get('name', '') if isinstance(template, dict) else ''}'")
    
    # Create a working copy to avoid modifying the original until user accepts
    working_template = template.copy() if isinstance(template, dict) else {}
    
    # Extract key information
    template_name = working_template.get('name', '')
    is_new = template_name == ""
    
    # Determine structure name - prioritize structure_name attribute
    structure_name = working_template.get('structure_name', '')
    if not structure_name and template_name:
        # If structure_name not defined, build from template name
        structure_name = f"Template_{template_name}"
    
    # Store original names for reference
    original_name = template_name
    original_structure_name = structure_name
    
    print(f"🔍 EDIT TEMPLATE: Template is_new={is_new}, name='{template_name}', structure_name='{structure_name}'")
    
    # Get structure from the template if it exists
    structure = working_template.get('structure', [])
    
    # Import here to avoid circular imports
    from app.ui.structure_editor_functions import show_enhanced_structure_editor
    from app.templates.template_manager import TemplateManager
    
    # Get template manager instance
    template_manager = None
    if app and hasattr(app, 'template_manager'):
        template_manager = app.template_manager
    else:
        template_manager = TemplateManager()
    
    # Determine parent window for the dialog
    from PyQt5.QtWidgets import QWidget
    parent_window = None
    
    # Try to get a valid QWidget parent
    if gallery and isinstance(gallery, QWidget):
        parent_window = gallery
    elif app:
        if hasattr(app, 'main_window') and isinstance(app.main_window, QWidget):
            parent_window = app.main_window
        elif hasattr(app, 'window') and isinstance(app.window, QWidget):
            parent_window = app.window
        elif hasattr(app, 'parent') and isinstance(app.parent, QWidget):
            parent_window = app.parent
    
    # Show the structure editor
    try:
        success, updated_structure_name = show_enhanced_structure_editor(
            parent=parent_window,
            structure_name=structure_name,
            structure=structure,
            is_new=is_new,
            template_name=template_name,
            focus_name_field=is_new,
            template_manager=template_manager,
            callback=callback
        )
    except ImportError as e:
        print(f"🔍 EDIT TEMPLATE: Error importing structure editor: {e}")
        return False
    except Exception as e:
        print(f"🔍 EDIT TEMPLATE: Error showing structure editor: {e}")
        return False
    
    if success:
        # Get extracted name from structure name
        extracted_name = updated_structure_name
        if updated_structure_name.startswith("Template_"):
            extracted_name = updated_structure_name[9:]  # Remove "Template_" prefix
        
        # Check if this is a rename operation
        is_rename = original_name != "" and extracted_name != original_name
        
        # Update the template with new values
        updated_template = working_template.copy()
        updated_template['name'] = extracted_name
        updated_template['structure_name'] = updated_structure_name
        
        print(f"🔍 EDIT TEMPLATE: Structure editor returned success=True, updated_structure_name='{updated_structure_name}'")
        print(f"🔍 EDIT TEMPLATE: Preserved original_name '{original_name}' and original_structure_name '{original_structure_name}'")
        
        # Call the callback with the updated template if provided
        if callback:
            print(f"🔍 EDIT TEMPLATE: Calling callback with updated template")
            result = callback(updated_template)
            print(f"🔍 EDIT TEMPLATE: Callback returned: {result}")
        
        # If template was renamed and gallery is provided, ensure UI is updated
        if is_rename and gallery:
            print(f"🔍 EDIT TEMPLATE: Template was renamed, updating gallery")
            
            # Force template manager to reload templates
            if template_manager:
                template_manager.load_templates()
                template_manager.load_custom_structures()
                print(f"🔍 EDIT TEMPLATE: Forced reload of templates and structures")
            
            # Force gallery refresh with more thorough approach
            if hasattr(gallery, 'populate_gallery'):
                gallery.populate_gallery(force_refresh=True)
                print(f"🔍 EDIT TEMPLATE: Forced gallery refresh")
        
        return True
    
    return False

def create_basic_info_tab(tabs, template):
    """Create the basic info tab"""
    basic_tab = QWidget()
    basic_layout = QVBoxLayout(basic_tab)
    
    # Basic info explanation
    basic_info_explanation = QLabel("Enter basic information about your template:")
    basic_info_explanation.setWordWrap(True)
    basic_info_explanation.setStyleSheet(f"color: {colors['text_muted']}; font-size: 12px; margin-bottom: 10px;")
    basic_layout.addWidget(basic_info_explanation)
    
    # Template name
    name_layout = QHBoxLayout()
    name_label = QLabel("Template Name:")
    name_label.setStyleSheet(f"color: {colors['text']}; font-weight: bold;")
    name_edit = QLineEdit(template.get('name', ''))
    name_edit.setObjectName("template_name")
    name_edit.setPlaceholderText("Enter a descriptive name for this template")
    name_edit.setStyleSheet(f"background: {colors['input_bg']}; color: {colors['text']}; padding: 8px; border: 1px solid {colors['border']};")
    name_layout.addWidget(name_label)
    name_layout.addWidget(name_edit)
    basic_layout.addLayout(name_layout)
    
    # Add date field (read-only, shows current date or existing date)
    from datetime import datetime
    date_layout = QHBoxLayout()
    date_label = QLabel("Created:")
    date_label.setStyleSheet(f"color: {colors['text']}; font-weight: bold;")
    date_value = template.get('date', datetime.now().strftime('%Y-%m-%d'))
    date_edit = QLineEdit(date_value)
    date_edit.setObjectName("template_date")
    date_edit.setReadOnly(True)
    date_edit.setStyleSheet(f"background: {colors['input_bg']}; color: {colors['text_muted']}; padding: 8px; border: 1px solid {colors['border']};")
    date_layout.addWidget(date_label)
    date_layout.addWidget(date_edit)
    basic_layout.addLayout(date_layout)
    
    # Add spacer
    basic_layout.addStretch()
    
    tabs.addTab(basic_tab, "Basic Info")
    return basic_tab

def create_structure_tab(tabs, template, parent):
    """Create the structure tab"""
    structure_tab = QWidget()
    structure_layout = QVBoxLayout(structure_tab)
    
    # Explanation
    structure_explanation = QLabel("Define the folder structure for your template:")
    structure_explanation.setWordWrap(True)
    structure_explanation.setStyleSheet(f"color: {colors['text_muted']}; font-size: 12px; margin-bottom: 10px;")
    structure_layout.addWidget(structure_explanation)
    
    # Tree widget for structure
    tree = QTreeWidget()
    tree.setHeaderHidden(True)
    tree.setAlternatingRowColors(True)
    tree.setStyleSheet(f"""
        QTreeWidget {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            padding: 5px;
        }}
        QTreeWidget::item {{
            padding: 3px;
        }}
        QTreeWidget::item:selected {{
            background-color: {colors['accent_light']};
        }}
    """)
    tree.setObjectName("structure_tree")
    structure_layout.addWidget(tree)
    
    # Root item
    root = QTreeWidgetItem(tree)
    root.setText(0, "Project Root")
    root.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
    root.setExpanded(True)
    
    # Button layout
    button_layout = QHBoxLayout()
    
    # Add folder button
    add_folder_btn = QPushButton("Add Folder")
    add_folder_btn.setStyleSheet(BUTTON_STYLE)
    add_folder_btn.clicked.connect(lambda: edit_template_structure(parent, template, structure_tab))
    button_layout.addWidget(add_folder_btn)
    
    # Import structure button 
    import_structure_btn = QPushButton("Import Structure")
    import_structure_btn.setStyleSheet(BUTTON_STYLE)
    import_structure_btn.clicked.connect(lambda: import_template_structure(parent, template, structure_tab))
    button_layout.addWidget(import_structure_btn)
    
    # Preview button
    preview_btn = QPushButton("Preview Structure")
    preview_btn.setStyleSheet(BUTTON_STYLE)
    preview_btn.clicked.connect(lambda: preview_template_structure(parent, template, structure_tab))
    button_layout.addWidget(preview_btn)
    
    structure_layout.addLayout(button_layout)
    
    # Populate tree if we have a structure
    if 'structure' in template and template['structure']:
        populate_structure_tree(root, template['structure'])
    
    # Store the root item and tree for later access
    template['_root_item'] = root
    template['_tree'] = tree
    
    tabs.addTab(structure_tab, "Structure")
    return structure_tab

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
                tree_item.setData(0, Qt.UserRole, file_path)  # Store the original path

def show_manage_templates(parent, template_manager, callback=None):
    """Show the template management dialog"""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Manage Templates")
    dialog.resize(600, 500)
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(15, 15, 15, 15)
    layout.setSpacing(10)
    
    # Create tabs
    tabs = QTabWidget()
    
    # Templates tab
    templates_tab = QWidget()
    templates_layout = QVBoxLayout(templates_tab)
    
    templates_label = QLabel("Templates")
    templates_label.setStyleSheet("font-weight: bold; font-size: 14px;")
    templates_layout.addWidget(templates_label)
    
    # Template list
    template_list = QListWidget()
    template_list.setSelectionMode(QListWidget.ExtendedSelection)
    templates_layout.addWidget(template_list)
    
    # Populate template list
    templates = template_manager.get_all_templates()
    for template in templates:
        template_list.addItem(f"{template.get('name', 'Unnamed')}")
    
    # Template buttons
    template_buttons = QHBoxLayout()
    
    edit_btn = QPushButton("Edit")
    edit_btn.clicked.connect(lambda: edit_template(parent, template_manager, template_list, dialog))
    
    delete_btn = QPushButton("Delete")
    delete_btn.clicked.connect(lambda: delete_template(parent, template_manager, template_list, dialog))
    
    import_btn = QPushButton("Import")
    import_btn.clicked.connect(lambda: import_template(parent, template_manager, dialog))
    
    template_buttons.addWidget(edit_btn)
    template_buttons.addWidget(delete_btn)
    template_buttons.addWidget(import_btn)
    templates_layout.addLayout(template_buttons)
    
    # Add templates tab
    tabs.addTab(templates_tab, "Templates")
    
    # Folders tab
    folders_tab = QWidget()
    folders_layout = QVBoxLayout(folders_tab)
    
    folders_label = QLabel("Folders")
    folders_label.setStyleSheet("font-weight: bold; font-size: 14px;")
    folders_layout.addWidget(folders_label)
    
    # Folder list
    folder_list = QListWidget()
    folder_list.setSelectionMode(QListWidget.ExtendedSelection)
    folders_layout.addWidget(folder_list)
    
    # Populate folder list
    folders = template_manager.get_folders()
    for folder in sorted(folders):
        folder_list.addItem(folder)
    
    # Folder buttons
    folder_buttons = QHBoxLayout()
    
    add_folder_btn = QPushButton("Add")
    add_folder_btn.clicked.connect(lambda: create_folder(parent, template_manager, folder_list, dialog))
    
    rename_folder_btn = QPushButton("Rename")
    rename_folder_btn.clicked.connect(lambda: rename_folder(parent, template_manager, folder_list, dialog))
    
    delete_folder_btn = QPushButton("Delete")
    delete_folder_btn.clicked.connect(lambda: delete_folder(parent, template_manager, folder_list, dialog))
    
    folder_buttons.addWidget(add_folder_btn)
    folder_buttons.addWidget(rename_folder_btn)
    folder_buttons.addWidget(delete_folder_btn)
    folders_layout.addLayout(folder_buttons)
    
    # Add folders tab
    tabs.addTab(folders_tab, "Folders")
    
    # Structures tab
    structures_tab = QWidget()
    structures_layout = QVBoxLayout(structures_tab)
    
    structures_label = QLabel("Folder Structures")
    structures_label.setStyleSheet("font-weight: bold; font-size: 14px;")
    structures_layout.addWidget(structures_label)
    
    # Add help text
    structures_help = QLabel("These are the saved folder structures used by templates. Each template uses its own folder structure.")
    structures_help.setWordWrap(True)
    structures_layout.addWidget(structures_help)
    
    # Structure list
    structure_list = QListWidget()
    structure_list.setSelectionMode(QListWidget.ExtendedSelection)
    structures_layout.addWidget(structure_list)
    
    # Populate structure list
    structures = template_manager.get_structures() if hasattr(template_manager, 'get_structures') else []
    for structure in sorted(structures):
        structure_list.addItem(structure)
    
    # Structure buttons
    structure_buttons = QHBoxLayout()
    
    view_structure_btn = QPushButton("View Structure")
    view_structure_btn.clicked.connect(lambda: view_structure(parent, template_manager, structure_list))
    
    delete_structure_btn = QPushButton("Delete")
    delete_structure_btn.clicked.connect(lambda: delete_structure(parent, template_manager, structure_list, dialog))
    
    structure_buttons.addWidget(view_structure_btn)
    structure_buttons.addWidget(delete_structure_btn)
    structures_layout.addLayout(structure_buttons)
    
    # Add structures tab
    tabs.addTab(structures_tab, "Structures")
    
    # Add tabs to main layout
    layout.addWidget(tabs)
    
    # Close button
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    layout.addWidget(close_btn)
    
    # Connect callbacks
    dialog.finished.connect(lambda: callback() if callback else None)
    
    # Show dialog
    dialog.exec_()

def view_structure(parent, template_manager, structure_list):
    """View the selected structure"""
    selected_items = structure_list.selectedItems()
    if not selected_items:
        QMessageBox.warning(parent, "Error", "Please select a structure to view.")
        return
    
    structure_name = selected_items[0].text()
    structure = template_manager.get_structure(structure_name) if hasattr(template_manager, 'get_structure') else None
    
    if not structure:
        QMessageBox.warning(parent, "Error", f"Could not find structure: {structure_name}")
        return
    
    # Show the structure preview
    preview_structure(parent, structure)

def delete_structure(parent, template_manager, structure_list, dialog):
    """Delete the selected structure(s)"""
    selected_items = structure_list.selectedItems()
    if not selected_items:
        QMessageBox.warning(parent, "Error", "Please select at least one structure to delete.")
        return
    
    # Check if any selected structures are in use
    structures_in_use = {}
    for item in selected_items:
        structure_name = item.text()
        # Check if structure is in use by any templates
        templates_using = []
        for template in template_manager.get_all_templates():
            if template.get('structure_name') == structure_name:
                templates_using.append(template.get('name', 'Unnamed'))
        
        if templates_using:
            structures_in_use[structure_name] = templates_using
    
    # If any structures are in use, show warning and abort
    if structures_in_use:
        error_msg = "The following structures cannot be deleted because they are in use:\n\n"
        for structure_name, templates in structures_in_use.items():
            error_msg += f"• {structure_name} - used by: {', '.join(templates)}\n"
        
        QMessageBox.warning(parent, "Cannot Delete", error_msg)
        return
    
    # Confirm deletion
    if len(selected_items) > 1:
        confirm = QMessageBox.question(
            parent,
            "Confirm Delete",
            f"Are you sure you want to delete {len(selected_items)} structures?",
            QMessageBox.Yes | QMessageBox.No
        )
    else:
        structure_name = selected_items[0].text()
        confirm = QMessageBox.question(
            parent,
            "Confirm Delete",
            f"Are you sure you want to delete structure '{structure_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
    
    if confirm == QMessageBox.Yes:
        # Process deletions in reverse order to maintain valid indices
        for i in range(len(selected_items) - 1, -1, -1):
            item = selected_items[i]
            structure_name = item.text()
            
            success = template_manager.delete_structure(structure_name) if hasattr(template_manager, 'delete_structure') else False
            
            if success:
                # Remove from the list
                row = structure_list.row(item)
                structure_list.takeItem(row)
            else:
                QMessageBox.warning(parent, "Error", f"Failed to delete structure '{structure_name}'.")

def edit_template(parent, template_manager, template_list, dialog):
    """Edit the selected template"""
    selected_items = template_list.selectedItems()
    if not selected_items:
        QMessageBox.warning(parent, "Warning", "Please select a template to edit.")
        return
    
    item_text = selected_items[0].text()
    template_name = item_text.split(" (")[0]
    
    # Find the template
    template = None
    for t in template_manager.get_all_templates():
        if t.get("name", "") == template_name:
            template = t
            break
    
    if not template:
        QMessageBox.warning(parent, "Error", f"Template '{template_name}' not found.")
        return
    
    # Show edit dialog
    show_edit_template(parent, template, lambda t: template_manager.update_template(t))

def delete_template(parent, template_manager, template_list, dialog):
    """Delete the selected template(s)"""
    selected_items = template_list.selectedItems()
    if not selected_items:
        QMessageBox.warning(parent, "Warning", "Please select at least one template to delete.")
        return
    
    # If multiple templates selected, confirm with count
    if len(selected_items) > 1:
        confirm = QMessageBox.question(
            parent,
            "Confirm Delete",
            f"Are you sure you want to delete {len(selected_items)} templates?",
            QMessageBox.Yes | QMessageBox.No
        )
    else:
        # Single template selected
        item_text = selected_items[0].text()
        template_name = item_text.split(" (")[0]
        
        confirm = QMessageBox.question(
            parent,
            "Confirm Delete",
            f"Are you sure you want to delete template '{template_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
    
    if confirm == QMessageBox.Yes:
        # Process deletions in reverse order to maintain valid indices
        for i in range(len(selected_items) - 1, -1, -1):
            item = selected_items[i]
            item_text = item.text()
            template_name = item_text.split(" (")[0]
            
            # Delete the template
            success = template_manager.delete_template(template_name)
            
            if success:
                # Remove from list
                row = template_list.row(item)
                template_list.takeItem(row)
            else:
                QMessageBox.warning(parent, "Error", f"Failed to delete template '{template_name}'.")

def import_template(parent, template_manager, dialog):
    """Import a template file"""
    file_dialog = QFileDialog(parent)
    file_dialog.setWindowTitle("Select Template File")
    file_dialog.setFileMode(QFileDialog.ExistingFile)
    file_dialog.setNameFilter("Project Files (*.prproj *.aep *.aepx *.psd *.ai);;All Files (*)")
    
    if file_dialog.exec_():
        selected_files = file_dialog.selectedFiles()
        if selected_files:
            file_path = selected_files[0]
            file_name = os.path.basename(file_path)
            name, _ = os.path.splitext(file_name)
            
            # Get template name
            template_name, ok = QInputDialog.getText(
                parent,
                "Import Template",
                "Template name:",
                text=name
            )
            
            if ok and template_name:
                # Import the template
                success = template_manager.import_template_file(file_path, template_name)
                
                if success:
                    QMessageBox.information(parent, "Success", f"Template '{template_name}' imported successfully.")
                    # Close and refresh
                    dialog.accept()
                else:
                    QMessageBox.warning(parent, "Error", f"Failed to import template '{template_name}'.")

def create_folder(parent, template_manager, folder_list, dialog):
    """Create a new template folder"""
    folder_name, ok = QInputDialog.getText(
        parent,
        "New Folder",
        "Enter folder name:"
    )
    
    if ok and folder_name:
        # Check if folder already exists
        existing_folders = [folder_list.item(i).text() for i in range(folder_list.count())]
        
        if folder_name in existing_folders:
            QMessageBox.warning(parent, "Error", f"Folder '{folder_name}' already exists.")
            return
        
        # Add the folder
        success = template_manager.add_folder(folder_name)
        
        if success:
            # Add to the list
            folder_list.addItem(folder_name)
            
            # Sort the list
            folder_list.sortItems()
        else:
            QMessageBox.warning(parent, "Error", f"Failed to create folder '{folder_name}'.")

def rename_folder(parent, template_manager, folder_list, dialog):
    """Rename a template folder"""
    selected_items = folder_list.selectedItems()
    if not selected_items:
        QMessageBox.warning(parent, "Warning", "Please select a folder to rename.")
        return
    
    old_name = selected_items[0].text()
    
    # Check if this is a default folder that cannot be renamed
    if old_name in ["General", "Development", "Business"]:
        QMessageBox.warning(parent, "Error", f"'{old_name}' is a default folder and cannot be renamed.")
        return
    
    # Get new name
    new_name, ok = QInputDialog.getText(
        parent,
        "Rename Folder",
        "Enter new folder name:",
        text=old_name
    )
    
    if ok and new_name and new_name != old_name:
        # Check if the new name already exists
        existing_folders = [folder_list.item(i).text() for i in range(folder_list.count())]
        
        if new_name in existing_folders:
            QMessageBox.warning(parent, "Error", f"Folder '{new_name}' already exists.")
            return
        
        # Rename the folder
        success = template_manager.rename_folder(old_name, new_name)
        
        if success:
            # Update the list
            selected_items[0].setText(new_name)
            
            # Sort the list
            folder_list.sortItems()
        else:
            QMessageBox.warning(parent, "Error", f"Failed to rename folder '{old_name}'.")

def delete_folder(parent, template_manager, folder_list, dialog):
    """Delete selected template folder(s)"""
    selected_items = folder_list.selectedItems()
    if not selected_items:
        QMessageBox.warning(parent, "Warning", "Please select at least one folder to delete.")
        return
    
    # Check if any default folders are selected
    default_folders = ["General", "Development", "Business"]
    selected_default_folders = [item.text() for item in selected_items if item.text() in default_folders]
    
    if selected_default_folders:
        if len(selected_default_folders) == 1:
            QMessageBox.warning(parent, "Error", f"'{selected_default_folders[0]}' is a default folder and cannot be deleted.")
        else:
            QMessageBox.warning(parent, "Error", f"The following are default folders and cannot be deleted:\n• {', '.join(selected_default_folders)}")
        return
    
    # Confirm deletion
    if len(selected_items) > 1:
        confirm = QMessageBox.question(
            parent,
            "Confirm Delete",
            f"Are you sure you want to delete {len(selected_items)} folders?\n"
            "Templates in these folders will remain available but will be moved to the root.",
            QMessageBox.Yes | QMessageBox.No
        )
    else:
        folder_name = selected_items[0].text()
        confirm = QMessageBox.question(
            parent,
            "Confirm Delete",
            f"Are you sure you want to delete folder '{folder_name}'?\n"
            "Templates in this folder will remain available but will be moved to the root.",
            QMessageBox.Yes | QMessageBox.No
        )
    
    if confirm == QMessageBox.Yes:
        # Process deletions in reverse order to maintain valid indices
        for i in range(len(selected_items) - 1, -1, -1):
            item = selected_items[i]
            folder_name = item.text()
            
            # Delete the folder
            success = template_manager.delete_folder(folder_name)
            
            if success:
                # Remove from list
                row = folder_list.row(item)
                folder_list.takeItem(row)
            else:
                QMessageBox.warning(parent, "Error", f"Failed to delete folder '{folder_name}'.")

def process_dropped_file(file_path, parent_item):
    """Process a file dropped onto the tree"""
    # Get the filename
    file_name = os.path.basename(file_path)
    
    # Skip hidden files on Mac
    if file_name.startswith('.'):
        return None
        
    # Create a file item
    file_item = QTreeWidgetItem(parent_item, [file_name, "File"])
    file_item.setData(0, Qt.UserRole, file_path)  # Store the original path
    
    # Auto-expand the parent
    parent_item.setExpanded(True)
    
    return file_item

# Function to add a dropped directory recursively
def process_dropped_directory(dir_path, parent_item):
    """Process a directory dropped onto the tree"""
    # Create a folder item for this directory
    dir_name = os.path.basename(os.path.normpath(dir_path))
    
    # Skip .DS_Store and other hidden Mac files
    if dir_name.startswith('.'):
        print(f"DEBUG: Skipping hidden Mac directory in recursive function: {dir_name}")
        return None
            
    # Add the directory to the tree
    folder_item = QTreeWidgetItem(parent_item)
    folder_item.setText(0, dir_name)
    folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
    folder_item.setExpanded(True)
    
    # Add all subdirectories and files
    try:
        for item in sorted(os.listdir(dir_path)):
            # Skip hidden files on Mac
            if item.startswith('.'):
                continue
                
            item_path = os.path.join(dir_path, item)
            if os.path.isdir(item_path):
                # Recursively add subdirectory
                process_dropped_directory(item_path, folder_item)
            else:
                # Add file
                add_file_to_tree(item_path, folder_item)
    except Exception as e:
        print(f"DEBUG: Error processing directory contents in recursive function: {e}")
            
    return folder_item

# Function to add a file to the tree
def add_file_to_tree(file_path, parent_item):
    """Add a file to the tree"""
    file_name = os.path.basename(file_path)
    
    # Skip hidden files on Mac
    if file_name.startswith('.'):
        print(f"DEBUG: Skipping hidden Mac file in recursive function: {file_name}")
        return None
            
    # Create a file item
    file_item = QTreeWidgetItem(parent_item)
    file_item.setText(0, file_name)
    file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
    file_item.setData(0, Qt.UserRole, file_path)  # Store the original path
    
    # Auto-expand the parent
    parent_item.setExpanded(True)
    
    return file_item

# No longer needed - batch creation is now handled directly in the UI
# Keeping this as a comment for documentation purposes
# def show_batch_create(app):
#     """Show the batch project creation dialog"""
#     from app.ui.ui_components_pyqt import ProjectNameInput
#     
#     dialog = ProjectNameInput(parent=app, callback=lambda projects: handle_batch_projects(app, projects))
#     dialog.exec_()

def handle_batch_projects(app, projects):
    """Process a list of batch projects"""
    from app.core.project_operations import handle_batch_create
    
    # Convert list of project names to a string for handle_batch_create
    projects_text = "\n".join(projects)
    
    # handle_batch_create may return a boolean to indicate success/failure
    # or it may return the actual results list
    results = handle_batch_create(app, projects_text)
    
    # Only show results if it's not just a boolean success indicator
    if results and not isinstance(results, bool):
        show_batch_results(app, results) 
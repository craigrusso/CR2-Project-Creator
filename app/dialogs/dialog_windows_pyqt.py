#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import webbrowser
import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTreeWidget, QTreeWidgetItem,
                           QMessageBox, QScrollArea, QWidget, QTabWidget, 
                           QTextEdit, QCheckBox, QListWidget, QLineEdit,
                           QInputDialog, QFileDialog, QApplication, QStyle,
                           QTabWidget, QGridLayout, QGroupBox, QRadioButton,
                           QButtonGroup, QComboBox, QSplitter, QSizePolicy,
                           QFrame)
from PyQt5.QtCore import Qt, QSize, QByteArray, QUrl, QRegExp, QCoreApplication, QMimeData
from PyQt5.QtGui import QFont, QPixmap, QMovie, QIcon, QRegExpValidator, QDragEnterEvent, QDragMoveEvent, QDropEvent

from app.core.app_config import APP_NAME, APP_VERSION
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE
from app.utils.utils import get_config_paths, load_config, save_config
from app.ui.structure_editor_enhanced import show_enhanced_structure_editor

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
    root_item.setExpanded(True)
    
    # Helper function to add items recursively
    def add_items(parent_item, items):
        print(f"Adding items to {parent_item.text(0)}: {items}")
        for item in items:
            if isinstance(item, dict):
                # It's a directory (either with children or empty)
                for dir_name, children in item.items():
                    dir_item = QTreeWidgetItem(parent_item)
                    dir_item.setText(0, f"📁 {dir_name}")
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
                # For backward compatibility, check if it has a trailing slash
                if item.endswith('/'):
                    child_item.setText(0, f"📁 {item.rstrip('/')}")
                    # Mark as folder in data
                    child_item.setData(0, Qt.UserRole, "folder")
                else:
                    # It's a file
                    child_item.setText(0, f"📄 {item}")
                    # Mark as file in data
                    child_item.setData(0, Qt.UserRole, "file")
    
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

def show_edit_template(parent, template, callback=None):
    """Show dialog to edit a template"""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Edit Template")
    dialog.resize(700, 550)
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(15, 15, 15, 15)
    layout.setSpacing(10)
    
    # Create tab widget
    tabs = QTabWidget()
    
    # Create the tabs
    create_basic_info_tab(tabs, template)
    create_structure_tab(tabs, template, parent)
    
    # Add the tab widget to the main layout
    layout.addWidget(tabs)
    
    # Buttons
    button_layout = QHBoxLayout()
    
    cancel_btn = QPushButton("Cancel")
    cancel_btn.clicked.connect(dialog.reject)
    
    save_btn = QPushButton("Save")
    save_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
    
    button_layout.addWidget(cancel_btn)
    button_layout.addWidget(save_btn)
    
    layout.addLayout(button_layout)
    
    # Function to convert tree to structure format
    def get_structure_from_tree():
        # Find the structure tree in the second tab
        structure_tab = tabs.widget(1)
        structure_tree = structure_tab.findChild(QTreeWidget)
        root_item = structure_tree.topLevelItem(0)
        
        result = []
        
        def traverse(item, parent_path=""):
            items = []
            for i in range(item.childCount()):
                child = item.child(i)
                child_name = child.text(0)
                has_children = child.childCount() > 0
                
                if has_children:
                    # Directory with children
                    sub_items = traverse(child, os.path.join(parent_path, child_name))
                    items.append({child_name: sub_items})
                else:
                    # Check if it's a folder or file by looking at the user data
                    is_folder = child.data(0, Qt.UserRole) == "folder"
                    
                    if is_folder:
                        # Empty folder - represent as dictionary with empty list
                        items.append({child_name: []})
                    else:
                        # File
                        items.append(child_name)
            
            return items
        
        return traverse(root_item)
    
    def on_save():
        # Find the basic info inputs in the first tab
        basic_tab = tabs.widget(0)
        name_input = basic_tab.findChild(QTextEdit, "name_input")
        desc_input = basic_tab.findChild(QTextEdit, "desc_input")
        
        # Get template name
        template_name = name_input.toPlainText().strip()
        
        # Get structure tab to access the current structure information
        structure_tab = tabs.widget(1)
        
        # Find structure_name from the template's structure_type or get it from project_type
        structure_type = template.get('structure_type')
        
        # If no structure_type specified, try to derive from category/project_type
        if not structure_type:
            project_type = template.get('category', 'Video Editing')
            from app.constants import PROJECT_TYPE_TO_STRUCTURE
            structure_type = PROJECT_TYPE_TO_STRUCTURE.get(project_type)
        
        # Use template name as fallback for structure name
        structure_name = f"Template_{template_name}"
        
        # Get structure from tree
        structure = get_structure_from_tree()
        
        # Update template from form
        updated_template = template.copy()
        updated_template['name'] = template_name
        updated_template['description'] = desc_input.toPlainText().strip()
        # Keep the existing category if it exists, otherwise use 'General'
        if 'category' not in updated_template:
            updated_template['category'] = 'General'
        
        # Update structure information
        updated_template['structure_type'] = structure_type
        updated_template['structure_name'] = structure_name
        updated_template['structure'] = structure  # Add the structure to the template
        
        # Save the structure
        if hasattr(parent, 'template_manager'):
            print(f"DEBUG: Saving structure '{structure_name}' with {len(structure)} items")
            parent.template_manager.save_custom_structure(structure_name, structure)
        
        dialog.accept()
        
        # Call the callback with the updated template
        if callback:
            callback(updated_template)
    
    save_btn.clicked.connect(on_save)
    
    # Show dialog
    dialog.exec_()

def create_basic_info_tab(tabs, template):
    """Create the basic info tab"""
    basic_tab = QWidget()
    basic_layout = QVBoxLayout(basic_tab)
    
    # Basic info explanation
    basic_info_explanation = QLabel("Enter basic information about your template:")
    basic_info_explanation.setWordWrap(True)
    basic_layout.addWidget(basic_info_explanation)
    
    # Template name
    name_label = QLabel("Template Name:")
    name_input = QTextEdit()
    name_input.setObjectName("name_input")
    name_input.setPlainText(template.get('name', 'Unnamed Template'))
    name_input.setMaximumHeight(60)
    
    # Description
    desc_label = QLabel("Description:")
    desc_input = QTextEdit()
    desc_input.setObjectName("desc_input")
    desc_input.setPlainText(template.get('description', ''))
    
    # Add to form
    basic_layout.addWidget(name_label)
    basic_layout.addWidget(name_input)
    basic_layout.addWidget(desc_label)
    basic_layout.addWidget(desc_input)
    
    # Add tab
    tabs.addTab(basic_tab, "Basic Information")
    
def create_structure_tab(tabs, template, parent):
    """Create the structure tab"""
    # Create the tab widget
    structure_tab = QWidget()
    structure_layout = QVBoxLayout(structure_tab)
    
    # Get template info
    template_name = template.get('name', '')
    template_type = template.get('type', '')
    
    # Get project type - use a safe method
    project_type = template.get("project_type", "")
    if not project_type and "config" in template:
        project_type = template["config"].get("project_type", "")
    
    # Info section
    info_label = QLabel("This tab allows you to customize the folder structure that will be created when using this template.")
    info_label.setWordWrap(True)
    structure_layout.addWidget(info_label)
    
    # Get structure from template or default
    template_structure_name = None
    structure_items = []
    
    # If template has a structure_name, use it
    if 'structure_name' in template:
        template_structure_name = template.get('structure_name')
    # For directory templates, check template.json file
    elif template.get('type') == 'directory':
        template_path = template.get('path', '')
        if template_path and os.path.isdir(template_path):
            template_json_path = os.path.join(template_path, "template.json")
            if os.path.exists(template_json_path):
                try:
                    with open(template_json_path, 'r') as f:
                        template_info = json.load(f)
                        if 'structure_name' in template_info:
                            template_structure_name = template_info['structure_name']
                except Exception as e:
                    print(f"Error reading template.json: {e}")
    
    # If we found a structure name, get it
    if template_structure_name and hasattr(parent, 'template_manager'):
        structure_items = parent.template_manager.get_structure(template_structure_name)
    
    # If no structure yet, use default based on category
    if not structure_items and hasattr(parent, 'template_manager'):
        from app.constants import PROJECT_TYPE_TO_STRUCTURE
        
        # Get the structure based on project type
        structure_name = PROJECT_TYPE_TO_STRUCTURE.get(project_type)
        if structure_name:
            structure_items = parent.template_manager.get_structure(structure_name)
        else:
            # Fallback to default structure
            structure_items = parent.template_manager.get_default_structure("Video Editing - Standard")
    
    # Create main structure editor button
    edit_structure_btn = QPushButton("Edit Folder Structure")
    edit_structure_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
    edit_structure_btn.setMinimumHeight(50)  # Make button more prominent
    edit_structure_btn.setFont(QFont("Arial", 12, QFont.Bold))
    edit_structure_btn.clicked.connect(lambda: edit_template_structure(parent, template, structure_tab))
    
    # Add clear instruction
    instruction_label = QLabel("Click the button above to open the structure editor")
    instruction_label.setStyleSheet("color: #666; font-style: italic;")
    instruction_label.setAlignment(Qt.AlignCenter)
    
    # Add the main editor button with clear labeling
    edit_btn_layout = QVBoxLayout()
    edit_btn_layout.addWidget(edit_structure_btn, 0, Qt.AlignCenter)
    edit_btn_layout.addWidget(instruction_label)
    structure_layout.addLayout(edit_btn_layout)
    
    # Add some spacing
    structure_layout.addSpacing(20)
    
    # Create a preview of the structure with clear labeling
    preview_title = QLabel("PREVIEW ONLY (Read-Only)")
    preview_title.setStyleSheet(f"font-weight: bold; color: {colors['text']}; font-size: 14px;")
    preview_title.setAlignment(Qt.AlignCenter)
    structure_layout.addWidget(preview_title)
    
    # Clarification text
    preview_explanation = QLabel("This preview shows the current folder structure. To make changes, use the 'Edit Folder Structure' button above.")
    preview_explanation.setWordWrap(True)
    preview_explanation.setStyleSheet(f"color: {colors['secondary_text']}; font-style: italic;")
    structure_layout.addWidget(preview_explanation)
    
    preview_frame = QFrame()
    preview_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
    preview_frame.setStyleSheet(f"background-color: {colors['card_bg']}; border: 1px solid {colors['border']};")
    preview_layout = QVBoxLayout(preview_frame)
    
    # Create tree widget for structure preview
    structure_tree = QTreeWidget()
    structure_tree.setHeaderLabels(["Folder/File"])
    structure_tree.setIndentation(20)
    structure_tree.setRootIsDecorated(True)
    structure_tree.setAlternatingRowColors(True)
    structure_tree.setEnabled(False)  # Make it visually clear this is read-only
    structure_tree.setStyleSheet(f"""
        QTreeWidget {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: none;
        }}
        QTreeWidget::item {{
            color: {colors['text']};
        }}
        QTreeWidget::item:alternate {{
            background-color: {colors['bg']};
        }}
    """)
    
    # Create root item
    root_item = QTreeWidgetItem(structure_tree)
    root_item.setText(0, "Project Root")
    root_item.setExpanded(True)
    
    # Populate the tree with structure_items
    if structure_items:
        populate_structure_tree(root_item, structure_items)
    
    preview_layout.addWidget(structure_tree)
    structure_layout.addWidget(preview_frame)
    
    # Add the tab
    tabs.addTab(structure_tab, "Folder Structure")
    
    # Store references for later use
    structure_tab.structure_tree = structure_tree
    structure_tab.structure_items = structure_items
    structure_tab.structure_name = template_structure_name
    structure_tab.root_item = root_item

def edit_template_structure(parent, template, structure_tab):
    """Launch the enhanced structure editor for template editing"""
    print("DEBUG: edit_template_structure called")
    
    from app.ui.structure_editor_enhanced import EnhancedStructureEditor
    
    # Get the current structure name and items
    structure_name = getattr(structure_tab, 'structure_name', None)
    structure_items = getattr(structure_tab, 'structure_items', [])
    
    print(f"DEBUG: Current structure_name={structure_name}, items count={len(structure_items) if structure_items else 0}")
    
    # Get project type
    project_type = template.get("project_type", "")
    if not project_type and "config" in template:
        project_type = template["config"].get("project_type", "")
    
    print(f"DEBUG: Project type: {project_type}")
    
    # Show the enhanced structure editor
    print("DEBUG: Calling show_enhanced_structure_editor")
    success, updated_structure, updated_name = show_enhanced_structure_editor(
        parent,
        structure_name=structure_name,
        structure=structure_items,
        project_type=project_type
    )
    
    print(f"DEBUG: Editor returned: success={success}, updated_name={updated_name}, updated_structure={bool(updated_structure)}")
    
    if success and updated_structure:
        print("DEBUG: Processing successful edit")
        # Update the structure name if we got a new one
        if updated_name:
            print(f"DEBUG: Updating structure name to: {updated_name}")
            structure_name = updated_name
            structure_tab.structure_name = structure_name
            template['structure_name'] = structure_name
        # If we still don't have a structure name, create one from the template name
        elif not structure_name and 'name' in template:
            template_name = template.get('name', '')
            structure_name = f"Template_{template_name}"
            print(f"DEBUG: Created structure name from template: {structure_name}")
            structure_tab.structure_name = structure_name
            template['structure_name'] = structure_name
        
        # Update the structure preview with the directly returned structure
        try:
            print(f"DEBUG: Updating structure tree with {len(updated_structure) if updated_structure else 0} items")
            # Update the tree with the structure returned from the editor
            tree = structure_tab.structure_tree
            root = getattr(structure_tab, 'root_item', tree.topLevelItem(0))
            root.takeChildren()  # Clear existing items
            
            # Repopulate with the updated structure
            populate_structure_tree(root, updated_structure)
            
            # Update the stored reference
            structure_tab.structure_items = updated_structure
            
            # Set the template's structure directly
            template['structure'] = updated_structure
            
            # If we have a template manager, make sure the structure is saved
            if hasattr(parent, 'template_manager') and structure_name:
                print(f"DEBUG: Saving to template manager: {structure_name}")
                parent.template_manager.save_custom_structure(structure_name, updated_structure)
                print(f"DEBUG: Saved updated structure '{structure_name}' with {len(updated_structure)} items")
            
            # Show visual feedback that update was successful
            preview_frame = tree.parent()
            if isinstance(preview_frame, QFrame):
                original_style = preview_frame.styleSheet()
                preview_frame.setStyleSheet(f"background-color: #c8e6c9; border: 1px solid {colors['border']};")  # Light green background that works with both light and dark themes
                
                # Reset after 2 seconds
                from PyQt5.QtCore import QTimer
                def reset_style():
                    preview_frame.setStyleSheet(original_style)
                QTimer.singleShot(2000, reset_style)
                
            print(f"DEBUG: Successfully updated structure preview")
        except Exception as e:
            print(f"DEBUG: Error updating structure preview: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("DEBUG: Edit was canceled or no structure returned")

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
            # This is a file
            file_item = QTreeWidgetItem(parent_item)
            file_item.setText(0, item)
            file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))

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
    template_list.setSelectionMode(QListWidget.SingleSelection)
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
    folder_list.setSelectionMode(QListWidget.SingleSelection)
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
    structure_list.setSelectionMode(QListWidget.SingleSelection)
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
    """Delete the selected structure"""
    selected_items = structure_list.selectedItems()
    if not selected_items:
        QMessageBox.warning(parent, "Error", "Please select a structure to delete.")
        return
    
    structure_name = selected_items[0].text()
    
    # Check if structure is in use by any templates
    templates_using = []
    for template in template_manager.get_all_templates():
        if template.get('structure_name') == structure_name:
            templates_using.append(template.get('name', 'Unnamed'))
    
    if templates_using:
        QMessageBox.warning(parent, "Cannot Delete", 
                          f"Structure '{structure_name}' is in use by the following templates:\n\n" + 
                          "\n".join(templates_using))
        return
    
    # Confirm deletion
    confirm = QMessageBox.question(
        parent,
        "Confirm Delete",
        f"Are you sure you want to delete structure '{structure_name}'?",
        QMessageBox.Yes | QMessageBox.No
    )
    
    if confirm == QMessageBox.Yes:
        success = template_manager.delete_structure(structure_name) if hasattr(template_manager, 'delete_structure') else False
        
        if success:
            # Remove from the list
            row = structure_list.row(selected_items[0])
            structure_list.takeItem(row)
            QMessageBox.information(parent, "Success", f"Structure '{structure_name}' deleted successfully.")
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
    """Delete the selected template"""
    selected_items = template_list.selectedItems()
    if not selected_items:
        QMessageBox.warning(parent, "Warning", "Please select a template to delete.")
        return
    
    item_text = selected_items[0].text()
    template_name = item_text.split(" (")[0]
    
    # Confirm deletion
    confirm = QMessageBox.question(
        parent,
        "Confirm Delete",
        f"Are you sure you want to delete template '{template_name}'?",
        QMessageBox.Yes | QMessageBox.No
    )
    
    if confirm == QMessageBox.Yes:
        # Delete the template
        success = template_manager.delete_template(template_name)
        
        if success:
            # Remove from list
            row = template_list.currentRow()
            template_list.takeItem(row)
            QMessageBox.information(parent, "Success", f"Template '{template_name}' deleted successfully.")
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

def create_project_type(parent, template_manager, project_type_list, dialog):
    """Create a new project type"""
    project_type_name, ok = QInputDialog.getText(
        parent,
        "New Project Type",
        "Enter project type name:"
    )
    
    if ok and project_type_name:
        # Check if project type already exists
        existing_project_types = [project_type_list.item(i).text() for i in range(project_type_list.count())]
        
        if project_type_name in existing_project_types:
            QMessageBox.warning(parent, "Error", f"Project type '{project_type_name}' already exists.")
            return
        
        # Add to the list
        project_type_list.addItem(project_type_name)
        
        # Sort the list
        project_type_list.sortItems()
        
        # No need to save as project types are determined by templates

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
    """Delete a template folder"""
    selected_items = folder_list.selectedItems()
    if not selected_items:
        QMessageBox.warning(parent, "Warning", "Please select a folder to delete.")
        return
    
    folder_name = selected_items[0].text()
    
    # Check if this is a default folder that cannot be deleted
    if folder_name in ["General", "Development", "Business"]:
        QMessageBox.warning(parent, "Error", f"'{folder_name}' is a default folder and cannot be deleted.")
        return
    
    # Confirm deletion
    confirm = QMessageBox.question(
        parent,
        "Confirm Delete",
        f"Are you sure you want to delete folder '{folder_name}'?\n"
        "Templates in this folder will remain available but will be moved to the root.",
        QMessageBox.Yes | QMessageBox.No
    )
    
    if confirm == QMessageBox.Yes:
        # Delete the folder
        success = template_manager.delete_folder(folder_name)
        
        if success:
            # Remove from list
            row = folder_list.currentRow()
            folder_list.takeItem(row)
        else:
            QMessageBox.warning(parent, "Error", f"Failed to delete folder '{folder_name}'.")

def show_structure_editor(parent, structure_type=None, callback=None, is_new=False, project_type=None, suggested_name=None):
    """Show structure editor dialog"""
    # Use the enhanced structure editor instead
    from app.ui.structure_editor_enhanced import EnhancedStructureEditor
    
    # Prepare the structure editor with the right parameters
    structure_editor = EnhancedStructureEditor(
        parent, 
        structure_name=structure_type if not suggested_name else suggested_name, 
        structure=None, 
        project_type=project_type,
        is_new=is_new
    )
    
    # Explicitly populate the structure dropdown
    structure_editor.populate_structure_dropdown()
    
    # If we have a suggested name and it's a new structure, set it in the UI
    if is_new and suggested_name:
        structure_editor.name_input.setText(suggested_name)
        structure_editor.name_input.selectAll()
        structure_editor.name_input.setFocus()
    
    # Create a callback wrapper to capture structure name and content
    if callback:
        original_callback = callback
        
        def save_callback(name, structure):
            # Call the original callback with name and structure
            return original_callback(name, structure)
            
        structure_editor.save_callback = save_callback
    
    # Show the dialog modally
    if structure_editor.exec_():
        return True
    return False

def show_enhanced_structure_editor(parent, structure_name=None, structure=None, is_new=False, project_type=None):
    """Show the enhanced structure editor dialog"""
    from app.ui.structure_editor_enhanced import EnhancedStructureEditor
    
    # Create and show the dialog
    structure_editor = EnhancedStructureEditor(
        parent, 
        structure_name=structure_name, 
        structure=structure, 
        project_type=project_type,
        is_new=is_new
    )
    
    # Show the dialog modally
    if structure_editor.exec_():
        return True
    return False

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
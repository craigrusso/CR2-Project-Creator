#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import webbrowser
import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTreeWidget, QTreeWidgetItem,
                           QMessageBox, QScrollArea, QWidget, QTabWidget, 
                           QTextEdit, QCheckBox, QListWidget, QLineEdit,
                           QInputDialog, QFileDialog, QApplication, QStyle)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

from app.core.app_config import APP_NAME, APP_VERSION
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE

def preview_structure(app, structure):
    """Show a preview of the project structure"""
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
        for item in items:
            if isinstance(item, dict):
                # It's a directory with children
                for dir_name, children in item.items():
                    dir_item = QTreeWidgetItem(parent_item)
                    dir_item.setText(0, f"📂 {dir_name}")
                    add_items(dir_item, children)
            elif isinstance(item, list):
                # It's a list of items
                add_items(parent_item, item)
            else:
                # It's a file or simple directory
                child_item = QTreeWidgetItem(parent_item)
                # Use different icon for files vs directories
                if item.endswith('/'):
                    child_item.setText(0, f"📂 {item.rstrip('/')}")
                else:
                    child_item.setText(0, f"📄 {item}")
    
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

def show_batch_create(app):
    """Show the batch project creation dialog"""
    from app.ui.ui_components_pyqt import ProjectNameInput
    
    dialog = ProjectNameInput(parent=app, callback=lambda projects: handle_batch_projects(app, projects))
    dialog.exec_()

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

def show_batch_results(app, results):
    """Show the results of batch project creation"""
    # If results is None or False, don't show the dialog
    if not results:
        return
        
    dialog = QDialog(app)
    dialog.setWindowTitle("Batch Creation Results")
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
    dialog.resize(500, 400)
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(15, 15, 15, 15)
    layout.setSpacing(10)
    
    # Placeholder label
    label = QLabel("Preferences (To Be Implemented)")
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet(f"color: {colors['text']}; font-size: 18px;")
    layout.addWidget(label)
    
    # Close button
    close_button = QPushButton("Close")
    close_button.setStyleSheet(BUTTON_STYLE)
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)
    
    dialog.exec_()

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
                    # Is it a folder or file? Check the icon
                    icon = child.icon(0)
                    if icon.isNull() or child.icon(0).cacheKey() == QApplication.style().standardIcon(QStyle.SP_DirIcon).cacheKey():
                        # It's a folder (empty)
                        items.append(f"{child_name}/")
                    else:
                        # It's a file
                        items.append(child_name)
            
            return items
        
        return traverse(root_item)
    
    def on_save():
        # Find the basic info inputs in the first tab
        basic_tab = tabs.widget(0)
        name_input = basic_tab.findChild(QTextEdit, "name_input")
        desc_input = basic_tab.findChild(QTextEdit, "desc_input")
        cat_input = basic_tab.findChild(QTextEdit, "cat_input")
        
        # Get template name
        template_name = name_input.toPlainText().strip()
        
        # Get structure name
        structure_name = f"Template_{template_name}"
        
        # Get structure from tree
        structure = get_structure_from_tree()
        
        # Update template from form
        updated_template = template.copy()
        updated_template['name'] = template_name
        updated_template['description'] = desc_input.toPlainText().strip()
        updated_template['category'] = cat_input.toPlainText().strip()
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
    
    # Category
    cat_label = QLabel("Category:")
    cat_input = QTextEdit()
    cat_input.setObjectName("cat_input")
    cat_input.setPlainText(template.get('category', 'General'))
    cat_input.setMaximumHeight(60)
    
    # Add to form
    basic_layout.addWidget(name_label)
    basic_layout.addWidget(name_input)
    basic_layout.addWidget(desc_label)
    basic_layout.addWidget(desc_input)
    basic_layout.addWidget(cat_label)
    basic_layout.addWidget(cat_input)
    
    # Add tab
    tabs.addTab(basic_tab, "Basic Information")
    
def create_structure_tab(tabs, template, parent):
    """Create the structure tab"""
    structure_tab = QWidget()
    structure_layout = QVBoxLayout(structure_tab)
    
    # Get dialog reference
    dialog = tabs.parent()
    
    structure_info_label = QLabel("Define the folder structure that will be created when using this template:")
    structure_info_label.setWordWrap(True)
    structure_layout.addWidget(structure_info_label)
    
    # Add drag and drop hint
    drag_drop_hint = QLabel("Tip: You can drag and drop folders directly from your file system to quickly import an existing structure.")
    drag_drop_hint.setWordWrap(True)
    drag_drop_hint.setStyleSheet("color: #666; font-style: italic; font-size: 12px;")
    structure_layout.addWidget(drag_drop_hint)
    
    # Enable drag and drop from OS
    class StructureTreeWithDrop(QTreeWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setAcceptDrops(True)
            
        def dragEnterEvent(self, event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                super().dragEnterEvent(event)
                
        def dragMoveEvent(self, event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                super().dragMoveEvent(event)
                
        def dropEvent(self, event):
            if event.mimeData().hasUrls():
                print("DEBUG: Drop event with URLs detected")
                # Get drop position
                drop_item = self.itemAt(event.pos())
                if not drop_item:
                    drop_item = self.invisibleRootItem().child(0)  # root item
                    print("DEBUG: Drop location is root item")
                else:
                    print(f"DEBUG: Drop location is {drop_item.text(0)}")
                    
                # Process the dropped URLs
                for url in event.mimeData().urls():
                    file_path = url.toLocalFile()
                    print(f"DEBUG: Processing dropped path: {file_path}")
                    
                    # Ensure path exists and is accessible
                    if not os.path.exists(file_path):
                        print(f"DEBUG: Path doesn't exist: {file_path}")
                        continue
                        
                    if os.path.isdir(file_path):
                        print(f"DEBUG: It's a directory: {file_path}")
                        # For macOS, handle folder paths more carefully
                        dir_name = os.path.basename(os.path.normpath(file_path))
                        print(f"DEBUG: Directory name extracted: {dir_name}")
                        
                        # Skip hidden Mac folders
                        if dir_name.startswith('.'):
                            print(f"DEBUG: Skipping hidden Mac directory: {dir_name}")
                            continue
                            
                        # Create folder item directly
                        folder_item = QTreeWidgetItem(drop_item)
                        folder_item.setText(0, dir_name)
                        folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                        folder_item.setExpanded(True)
                        
                        # Recursively process subdirectories
                        try:
                            for item in sorted(os.listdir(file_path)):
                                # Skip hidden Mac files
                                if item.startswith('.'):
                                    continue
                                    
                                item_full_path = os.path.join(file_path, item)
                                if os.path.isdir(item_full_path):
                                    process_dropped_directory(item_full_path, folder_item)
                                else:
                                    add_file_to_tree(item_full_path, folder_item)
                        except Exception as e:
                            print(f"DEBUG: Error processing directory contents: {e}")
                    else:
                        print(f"DEBUG: It's a file: {file_path}")
                        add_file_to_tree(file_path, drop_item)
                
                print("DEBUG: Drop event processing completed")
                event.acceptProposedAction()
            else:
                super().dropEvent(event)
    
    # Create tree with drop support
    structure_tree = StructureTreeWithDrop()
    structure_tree.setHeaderLabels(["Folder/File Name"])
    structure_tree.setSelectionMode(QTreeWidget.SingleSelection)
    structure_tree.setDragEnabled(True)
    structure_tree.setDragDropMode(QTreeWidget.DragDrop)
    structure_tree.setAcceptDrops(True)
    structure_tree.viewport().setAcceptDrops(True)
    structure_tree.setDropIndicatorShown(True)
    structure_layout.addWidget(structure_tree)
    
    # Root item
    root_item = QTreeWidgetItem(structure_tree)
    root_item.setText(0, "Project Root")
    root_item.setExpanded(True)
    
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
    if template_structure_name:
        structure_items = parent.template_manager.get_structure(template_structure_name)
    
    # If no structure yet, use default based on category
    if not structure_items:
        category = template.get('category', 'General')
        if category == "Video Editing":
            structure_type = "video"
        elif category == "Motion Graphics":
            structure_type = "motion"
        elif category == "Design":
            structure_type = "design" 
        else:
            structure_type = "standard"
        
        # Try to get the default structure
        if hasattr(parent, 'template_manager'):
            structure_items = parent.template_manager.get_default_structure(structure_type)
    
    # Populate structure tree recursively
    def add_structure_items(parent_item, items, path=""):
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    # Handle nested dictionary
                    for folder_name, sub_items in item.items():
                        folder_item = QTreeWidgetItem(parent_item)
                        folder_item.setText(0, folder_name)
                        folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                        new_path = os.path.join(path, folder_name)
                        add_structure_items(folder_item, sub_items, new_path)
                else:
                    # Handle string items
                    name = item
                    is_folder = name.endswith('/')
                    if is_folder:
                        name = name[:-1]  # Remove trailing slash
                    
                    item_widget = QTreeWidgetItem(parent_item)
                    item_widget.setText(0, name)
                    if is_folder:
                        # Create empty folder
                        item_widget.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                    else:
                        # Create file
                        item_widget.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
    
    # Add the structure items
    add_structure_items(root_item, structure_items)
    
    # Buttons for tree manipulation
    tree_buttons = QHBoxLayout()
    
    add_folder_btn = QPushButton("Add Folder")
    add_file_btn = QPushButton("Add File")
    remove_btn = QPushButton("Remove")
    rename_btn = QPushButton("Rename")
    
    tree_buttons.addWidget(add_folder_btn)
    tree_buttons.addWidget(add_file_btn)
    tree_buttons.addWidget(remove_btn)
    tree_buttons.addWidget(rename_btn)
    
    structure_layout.addLayout(tree_buttons)
    
    # Add folder action
    def add_folder():
        folder_name, ok = QInputDialog.getText(dialog, "Add Folder", "Folder Name:")
        if ok and folder_name:
            selected_items = structure_tree.selectedItems()
            parent_item = selected_items[0] if selected_items else root_item
            folder_item = QTreeWidgetItem(parent_item)
            folder_item.setText(0, folder_name)
            folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
            parent_item.setExpanded(True)
    
    # Add file action
    def add_file():
        # First, let user select a file
        file_path, _ = QFileDialog.getOpenFileName(
            dialog,
            "Select Template File",
            "",
            "All Files (*);;Project Files (*.prproj *.aep *.aepx *.psd *.ai);;Text Files (*.html *.css *.js *.txt *.md)"
        )
        
        if not file_path or not os.path.exists(file_path):
            return
            
        # Get the filename and suggested name with {{PROJECT_NAME}} placeholder
        original_filename = os.path.basename(file_path)
        filename_base, filename_ext = os.path.splitext(original_filename)
        suggested_name = f"{{{{PROJECT_NAME}}}}{filename_ext}"
        
        # Ask for the filename to use (with the project name placeholder)
        new_filename, ok = QInputDialog.getText(
            dialog,
            "File Name in Template",
            "Enter filename (use {{PROJECT_NAME}} as placeholder):",
            text=suggested_name
        )
        
        if not ok or not new_filename:
            return
            
        # Get selected directory in the structure tree
        selected_items = structure_tree.selectedItems()
        parent_item = selected_items[0] if selected_items else root_item
        
        # If the selected item is a file, use its parent as the directory
        if parent_item != root_item and parent_item.icon(0).cacheKey() == QApplication.style().standardIcon(QStyle.SP_FileIcon).cacheKey():
            parent_item = parent_item.parent() or root_item
        
        # Add the file to the structure tree
        file_item = QTreeWidgetItem(parent_item)
        file_item.setText(0, new_filename)
        file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
        file_item.setData(0, Qt.UserRole, file_path)  # Store original file path
        parent_item.setExpanded(True)
        
        # Notify user
        QMessageBox.information(
            dialog, 
            "File Added", 
            f"File '{new_filename}' added to the template structure.\n\n"
            f"When a project is created, {{PROJECT_NAME}} placeholders will be replaced with the actual project name."
        )
    
    # Remove action
    def remove_item():
        selected_items = structure_tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            if item != root_item:  # Don't remove the root
                parent = item.parent() or structure_tree.invisibleRootItem()
                parent.removeChild(item)
    
    # Rename action
    def rename_item():
        selected_items = structure_tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            if item != root_item:  # Don't rename the root
                name, ok = QInputDialog.getText(dialog, "Rename", "New Name:", text=item.text(0))
                if ok and name:
                    item.setText(0, name)
    
    add_folder_btn.clicked.connect(add_folder)
    add_file_btn.clicked.connect(add_file)
    remove_btn.clicked.connect(remove_item)
    rename_btn.clicked.connect(rename_item)
    
    # Add tab
    tabs.addTab(structure_tab, "Folder Structure")

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
        template_list.addItem(f"{template.get('name', 'Unnamed')} ({template.get('category', 'General')})")
    
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
    
    # Categories tab
    categories_tab = QWidget()
    categories_layout = QVBoxLayout(categories_tab)
    
    categories_label = QLabel("Categories")
    categories_label.setStyleSheet("font-weight: bold; font-size: 14px;")
    categories_layout.addWidget(categories_label)
    
    # Category list
    category_list = QListWidget()
    category_list.setSelectionMode(QListWidget.SingleSelection)
    categories_layout.addWidget(category_list)
    
    # Populate category list
    categories = template_manager.get_categories()
    for category in sorted(categories):
        category_list.addItem(category)
    
    # Category buttons
    category_buttons = QHBoxLayout()
    
    add_category_btn = QPushButton("Add")
    add_category_btn.clicked.connect(lambda: create_category(parent, template_manager, category_list, dialog))
    
    category_buttons.addWidget(add_category_btn)
    categories_layout.addLayout(category_buttons)
    
    # Add categories tab
    tabs.addTab(categories_tab, "Categories")
    
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

def create_category(parent, template_manager, category_list, dialog):
    """Create a new template category"""
    category_name, ok = QInputDialog.getText(
        parent,
        "New Category",
        "Enter category name:"
    )
    
    if ok and category_name:
        # Check if category already exists
        existing_categories = [category_list.item(i).text() for i in range(category_list.count())]
        
        if category_name in existing_categories:
            QMessageBox.warning(parent, "Error", f"Category '{category_name}' already exists.")
            return
        
        # Add to the list
        category_list.addItem(category_name)
        
        # Sort the list
        category_list.sortItems()
        
        # No need to save as categories are determined by templates

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

def show_structure_editor(parent, structure_type=None, callback=None):
    """Show structure editor dialog"""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Edit Structure")
    dialog.resize(700, 500)
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(15, 15, 15, 15)
    layout.setSpacing(10)
    
    # Header
    header_layout = QHBoxLayout()
    
    # Structure name
    name_label = QLabel("Structure Name:")
    name_input = QLineEdit()
    if structure_type:
        name_input.setText(structure_type)
        name_input.setReadOnly(True)  # Don't allow editing existing structure names
    
    header_layout.addWidget(name_label)
    header_layout.addWidget(name_input, 1)  # 1 = stretch factor
    
    layout.addLayout(header_layout)
    
    # Structure tree
    tree_label = QLabel("Directory Structure:")
    tree_label.setStyleSheet("font-weight: bold;")
    layout.addWidget(tree_label)
    
    # Setup the tree
    tree = QTreeWidget()
    tree.setHeaderLabels(["Name", "Type"])
    tree.setColumnWidth(0, 300)
    tree.setSelectionMode(QTreeWidget.SingleSelection)
    tree.setDragEnabled(True)
    tree.setDragDropMode(QTreeWidget.DragDrop)
    tree.setAcceptDrops(True)
    tree.viewport().setAcceptDrops(True)
    tree.setDropIndicatorShown(True)
    
    # Custom drag and drop handling
    original_dragEnterEvent = tree.dragEnterEvent
    original_dragMoveEvent = tree.dragMoveEvent
    original_dropEvent = tree.dropEvent
    
    def custom_dragEnterEvent(event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            original_dragEnterEvent(event)
    
    def custom_dragMoveEvent(event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            original_dragMoveEvent(event)
            
    def custom_dropEvent(event):
        if event.mimeData().hasUrls():
            print("DEBUG: Drop event with URLs detected")
            # Get drop position
            drop_item = tree.itemAt(event.pos())
            if not drop_item:
                drop_item = root_item
                
            # Process the dropped URLs
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                print(f"DEBUG: Processing dropped path: {file_path}")
                
                # Ensure path exists and is accessible
                if not os.path.exists(file_path):
                    print(f"DEBUG: Path doesn't exist: {file_path}")
                    continue
                    
                if os.path.isdir(file_path):
                    print(f"DEBUG: It's a directory: {file_path}")
                    # For macOS, handle folder paths more carefully
                    dir_name = os.path.basename(os.path.normpath(file_path))
                    print(f"DEBUG: Directory name extracted: {dir_name}")
                    
                    # Skip hidden Mac folders
                    if dir_name.startswith('.'):
                        print(f"DEBUG: Skipping hidden Mac directory: {dir_name}")
                        continue
                        
                    # Create folder item directly
                    folder_item = QTreeWidgetItem(drop_item)
                    folder_item.setText(0, dir_name)
                    folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                    folder_item.setExpanded(True)
                    
                    # Recursively process subdirectories
                    try:
                        for item in sorted(os.listdir(file_path)):
                            # Skip hidden Mac files
                            if item.startswith('.'):
                                continue
                                
                            item_full_path = os.path.join(file_path, item)
                            if os.path.isdir(item_full_path):
                                process_dropped_directory(item_full_path, folder_item)
                            else:
                                add_file_to_tree(item_full_path, folder_item)
                    except Exception as e:
                        print(f"DEBUG: Error processing directory contents: {e}")
                else:
                    print(f"DEBUG: It's a file: {file_path}")
                    add_file_to_tree(file_path, drop_item)
            
            print("DEBUG: Drop event processing completed")
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
    
    # Replace the event handlers
    tree.dragEnterEvent = custom_dragEnterEvent
    tree.dragMoveEvent = custom_dragMoveEvent
    tree.dropEvent = custom_dropEvent
    
    # Get structure from template manager
    template_manager = parent.template_manager
    structure_items = []
    
    if structure_type:
        structure_items = template_manager.get_structure(structure_type)
    
    # Root item
    root_item = QTreeWidgetItem(["Project Root", "Directory"])
    root_item.setExpanded(True)
    tree.addTopLevelItem(root_item)
    
    # Helper function to add items recursively
    def add_items(parent_item, items):
        for item in items:
            if isinstance(item, dict):
                # It's a directory with children
                for dir_name, children in item.items():
                    dir_item = QTreeWidgetItem(parent_item, [dir_name, "Directory"])
                    add_items(dir_item, children)
            elif isinstance(item, list):
                # It's a list of items
                add_items(parent_item, item)
            else:
                # It's a file or simple directory
                if item.endswith('/'):
                    name = item.rstrip('/')
                    child_item = QTreeWidgetItem(parent_item, [name, "Directory"])
                else:
                    child_item = QTreeWidgetItem(parent_item, [item, "File"])
    
    # Add structure items
    add_items(root_item, structure_items)
    
    layout.addWidget(tree)
    
    # Button toolbar
    button_toolbar = QHBoxLayout()
    
    add_dir_btn = QPushButton("Add Directory")
    add_file_btn = QPushButton("Add File")
    remove_btn = QPushButton("Remove Item")
    
    button_toolbar.addWidget(add_dir_btn)
    button_toolbar.addWidget(add_file_btn)
    button_toolbar.addWidget(remove_btn)
    button_toolbar.addStretch(1)
    
    layout.addLayout(button_toolbar)
    
    # Add directory function
    def add_directory():
        name, ok = QInputDialog.getText(dialog, "Add Directory", "Directory name:")
        if ok and name:
            selected = tree.selectedItems()
            parent_item = selected[0] if selected else root_item
            
            if parent_item.text(1) != "Directory":
                QMessageBox.warning(dialog, "Error", "Can only add directories to directories")
                return
                
            new_item = QTreeWidgetItem(parent_item, [name, "Directory"])
            parent_item.setExpanded(True)
    
    # Add file function
    def add_file():
        # First, let user select a file
        file_path, _ = QFileDialog.getOpenFileName(
            dialog,
            "Select Template File",
            "",
            "All Files (*);;Project Files (*.prproj *.aep *.aepx *.psd *.ai);;Text Files (*.html *.css *.js *.txt *.md)"
        )
        
        if not file_path or not os.path.exists(file_path):
            return
            
        # Get the filename and suggested name with {{PROJECT_NAME}} placeholder
        original_filename = os.path.basename(file_path)
        filename_base, filename_ext = os.path.splitext(original_filename)
        suggested_name = f"{{{{PROJECT_NAME}}}}{filename_ext}"
        
        # Ask for the filename to use (with the project name placeholder)
        new_filename, ok = QInputDialog.getText(
            dialog,
            "File Name in Template",
            "Enter filename (use {{PROJECT_NAME}} as placeholder):",
            text=suggested_name
        )
        
        if not ok or not new_filename:
            return
            
        # Get selected directory in the structure tree
        selected_items = tree.selectedItems()
        parent_item = selected_items[0] if selected_items else root_item
        
        # If the selected item is a file, use its parent as the directory
        if parent_item != root_item and parent_item.icon(0).cacheKey() == QApplication.style().standardIcon(QStyle.SP_FileIcon).cacheKey():
            parent_item = parent_item.parent() or root_item
        
        # Add the file to the structure tree
        file_item = QTreeWidgetItem(parent_item)
        file_item.setText(0, new_filename)
        file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
        file_item.setData(0, Qt.UserRole, file_path)  # Store original file path
        parent_item.setExpanded(True)
        
        # Notify user
        QMessageBox.information(
            dialog, 
            "File Added", 
            f"File '{new_filename}' added to the template structure.\n\n"
            f"When a project is created, {{PROJECT_NAME}} placeholders will be replaced with the actual project name."
        )
    
    # Remove item function
    def remove_item():
        selected = tree.selectedItems()
        if not selected:
            return
            
        item = selected[0]
        if item == root_item:
            QMessageBox.warning(dialog, "Error", "Cannot remove root item")
            return
            
        parent = item.parent()
        parent.removeChild(item)
    
    # Connect buttons
    add_dir_btn.clicked.connect(add_directory)
    add_file_btn.clicked.connect(add_file)
    remove_btn.clicked.connect(remove_item)
    
    # Dialog buttons
    button_layout = QHBoxLayout()
    
    cancel_btn = QPushButton("Cancel")
    cancel_btn.clicked.connect(dialog.reject)
    
    save_btn = QPushButton("Save")
    save_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
    
    button_layout.addWidget(cancel_btn)
    button_layout.addWidget(save_btn)
    
    layout.addLayout(button_layout)
    
    # Save function
    def save_structure():
        structure_name = name_input.text().strip()
        if not structure_name:
            QMessageBox.warning(dialog, "Error", "Structure name is required")
            return
        
        # Convert tree to structure format
        def get_structure_from_item(item):
            result = []
            for i in range(item.childCount()):
                child = item.child(i)
                child_name = child.text(0)
                child_type = child.text(1)
                
                if child_type == "Directory":
                    if child.childCount() > 0:
                        # Directory with children
                        children = get_structure_from_item(child)
                        result.append({child_name: children})
                    else:
                        # Empty directory
                        result.append(f"{child_name}/")
                else:
                    # File
                    result.append(child_name)
            
            return result
        
        # Get structure from tree
        structure = get_structure_from_item(root_item)
        
        # Save structure
        success = template_manager.save_custom_structure(structure_name, structure)
        
        if success:
            dialog.accept()
            
            # Call callback if provided
            if callback:
                callback()
        else:
            QMessageBox.warning(dialog, "Error", f"Failed to save structure '{structure_name}'")
    
    save_btn.clicked.connect(save_structure)
    
    # Show dialog
    dialog.exec_()

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
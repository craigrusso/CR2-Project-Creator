#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import webbrowser
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTreeWidget, QTreeWidgetItem,
                           QMessageBox, QScrollArea, QWidget, QTabWidget, 
                           QTextEdit, QCheckBox, QListWidget, QLineEdit,
                           QInputDialog)
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
    dialog.resize(500, 400)
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(15, 15, 15, 15)
    layout.setSpacing(10)
    
    # Form layout
    form_layout = QVBoxLayout()
    
    # Template name
    name_label = QLabel("Template Name:")
    name_input = QTextEdit()
    name_input.setPlainText(template.get('name', 'Unnamed Template'))
    name_input.setMaximumHeight(60)
    
    # Description
    desc_label = QLabel("Description:")
    desc_input = QTextEdit()
    desc_input.setPlainText(template.get('description', ''))
    
    # Category
    cat_label = QLabel("Category:")
    cat_input = QTextEdit()
    cat_input.setPlainText(template.get('category', 'General'))
    cat_input.setMaximumHeight(60)
    
    # Add to form
    form_layout.addWidget(name_label)
    form_layout.addWidget(name_input)
    form_layout.addWidget(desc_label)
    form_layout.addWidget(desc_input)
    form_layout.addWidget(cat_label)
    form_layout.addWidget(cat_input)
    
    layout.addLayout(form_layout)
    
    # Buttons
    button_layout = QHBoxLayout()
    
    cancel_btn = QPushButton("Cancel")
    cancel_btn.clicked.connect(dialog.reject)
    
    save_btn = QPushButton("Save")
    save_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
    
    button_layout.addWidget(cancel_btn)
    button_layout.addWidget(save_btn)
    
    layout.addLayout(button_layout)
    
    def on_save():
        # Update template from form
        updated_template = template.copy()
        updated_template['name'] = name_input.toPlainText().strip()
        updated_template['description'] = desc_input.toPlainText().strip()
        updated_template['category'] = cat_input.toPlainText().strip()
        
        dialog.accept()
        
        # Call the callback with the updated template
        if callback:
            callback(updated_template)
    
    save_btn.clicked.connect(on_save)
    
    # Show dialog
    dialog.exec_()

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
    
    tree = QTreeWidget()
    tree.setHeaderLabels(["Name", "Type"])
    tree.setColumnWidth(0, 300)
    
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
        name, ok = QInputDialog.getText(dialog, "Add File", "File name:")
        if ok and name:
            selected = tree.selectedItems()
            parent_item = selected[0] if selected else root_item
            
            if parent_item.text(1) != "Directory":
                QMessageBox.warning(dialog, "Error", "Can only add files to directories")
                return
                
            new_item = QTreeWidgetItem(parent_item, [name, "File"])
            parent_item.setExpanded(True)
    
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
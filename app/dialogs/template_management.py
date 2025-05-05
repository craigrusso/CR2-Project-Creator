#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Dialog windows for managing templates, template folders, and structures.
"""

import os
import copy
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTreeWidget, QTreeWidgetItem,
                           QMessageBox, QTabWidget, QWidget, QListWidget,
                           QInputDialog, QFileDialog, QApplication, QStyle,
                           QLineEdit)
from PyQt5.QtCore import Qt

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE
from app.ui.structure_editor_functions import show_enhanced_structure_editor
from app.dialogs.structure_dialogs import preview_structure

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
        from app.dialogs.structure_dialogs import populate_structure_tree
        populate_structure_tree(root, template['structure'])
    
    # Store the root item and tree for later access
    template['_root_item'] = root
    template['_tree'] = tree
    
    tabs.addTab(structure_tab, "Structure")
    return structure_tab

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
        QMessageBox.warning(parent, "No Structure", 
                           "This template has no structure defined yet.")
        return
        
    # Call the preview function
    preview_structure(parent, structure)

def show_manage_templates(parent, template_manager, callback=None):
    """Show the template management dialog"""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Manage Templates")
    dialog.resize(600, 700)
    
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
    show_edit_template(template, lambda t: template_manager.update_template(t), parent, None)

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
    if not folder_list or not template_manager:
        return
    
    # Get selected items
    selected_items = folder_list.selectedItems()
    if not selected_items:
        return
    
    # Check if any default folders are selected
    default_folders = []
    non_default_folders = []
    for item in selected_items:
        folder_name = item.text()
        if folder_name in ["General", "Development", "Business"]:
            default_folders.append(folder_name)
        else:
            non_default_folders.append(folder_name)
    
    # Show warning if default folders are selected
    if default_folders:
        folder_names = ", ".join([f"'{folder}'" for folder in default_folders])
        QMessageBox.warning(
            parent,
            "Cannot Delete Default Folders",
            f"The following folders cannot be deleted because they are default folders: {folder_names}"
        )
        
        # If only default folders were selected, we're done
        if not non_default_folders:
            return
    
    # Process deletions in reverse order to maintain valid indices
    for i in range(len(selected_items) - 1, -1, -1):
        item = selected_items[i]
        folder_name = item.text()
        
        # Skip default folders
        if folder_name in ["General", "Development", "Business"]:
            continue
        
        # Delete the folder
        success = template_manager.delete_folder(folder_name)
        
        if success:
            # Remove from list
            row = folder_list.row(item)
            folder_list.takeItem(row)
        else:
            QMessageBox.warning(parent, "Error", f"Failed to delete folder '{folder_name}'.")

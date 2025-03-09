#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import datetime
import shutil
import sys

# Using PyQt for the UI framework
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog
from app.ui.ui_components_pyqt import ScrollableFrame
from app.templates.template_card_pyqt import TemplateCard
UI_FRAMEWORK = 'pyqt'

from app.constants import DEFAULT_STRUCTURES, PROJECT_TYPE_TO_STRUCTURE, DEFAULT_TEMPLATE_CATEGORIES
from app.utils.utils import load_json_file, save_json_file, get_config_paths

class TemplateManager:
    """
    Manages project templates and custom structures
    """
    def __init__(self):
        self.paths = get_config_paths()
        self.custom_structures = {}
        self.templates = []
        self.template_directories = []
        
        # Add folder management
        self.folders = {}
        self.current_folder = None
        
        # Create required directories if they don't exist
        self._ensure_directories_exist()
        
        # Load templates and structures
        self.load_templates()
        self.load_custom_structures()
        self.load_template_directories()
        self.load_folders()
    
    def _ensure_directories_exist(self):
        """Ensure all required directories exist"""
        for path_key in ["templates_dir", "custom_structures_dir", "template_directories_dir"]:
            if path_key in self.paths:
                os.makedirs(self.paths[path_key], exist_ok=True)
    
    def load_templates(self):
        """Load all templates from the templates directory"""
        self.templates = []
        
        try:
            template_files = [f for f in os.listdir(self.paths["templates_dir"]) if f.endswith('.json')]
            
            for file in template_files:
                try:
                    with open(os.path.join(self.paths["templates_dir"], file), 'r') as f:
                        template = json.load(f)
                        self.templates.append(template)
                except Exception as e:
                    print(f"Error loading template {file}: {e}")
        except Exception as e:
            print(f"Error loading templates: {e}")
    
    def load_template_directories(self):
        """Load all template directories"""
        self.template_directories = []
        template_directories_dir = self.paths.get("template_directories_dir")
        
        if not template_directories_dir or not os.path.exists(template_directories_dir):
            return
        
        try:
            # Look for directories that contain a template.json file
            for item in os.listdir(template_directories_dir):
                item_path = os.path.join(template_directories_dir, item)
                if os.path.isdir(item_path):
                    template_json = os.path.join(item_path, "template.json")
                    if os.path.exists(template_json):
                        try:
                            with open(template_json, 'r') as f:
                                template_info = json.load(f)
                                template_info['path'] = item_path
                                template_info['type'] = 'directory'
                                self.template_directories.append(template_info)
                        except Exception as e:
                            print(f"Error loading template directory {item}: {e}")
        except Exception as e:
            print(f"Error loading template directories: {e}")
    
    def load_custom_structures(self):
        """Load all custom folder structures"""
        self.custom_structures = {}
        structures_dir = self.paths["custom_structures_dir"]
        
        try:
            structure_files = [f for f in os.listdir(structures_dir) if f.endswith('.json')]
            
            for file in structure_files:
                try:
                    with open(os.path.join(structures_dir, file), 'r') as f:
                        structure = json.load(f)
                        name = structure.get("name", os.path.splitext(file)[0])
                        self.custom_structures[name] = structure
                except Exception as e:
                    print(f"Error loading structure {file}: {e}")
        except Exception as e:
            print(f"Error loading custom structures: {e}")
    
    def get_default_structure(self, project_type):
        """Get the default directory structure for a project type"""
        structure_key = PROJECT_TYPE_TO_STRUCTURE.get(project_type, "Basic")
        
        # If structure_key is not in DEFAULT_STRUCTURES, use "Basic" as fallback
        if structure_key not in DEFAULT_STRUCTURES:
            structure_key = "Basic"
        
        return DEFAULT_STRUCTURES[structure_key]
    
    def get_structure(self, name_or_type):
        """Get a structure by name (custom) or type (default)"""
        # First check if it's a custom structure
        if name_or_type in self.custom_structures:
            return self.custom_structures[name_or_type].get("directories", [])
        
        # Then check if it's a default structure type
        return self.get_default_structure(name_or_type)
    
    def get_categories(self):
        """Get a list of all template categories"""
        # Get categories from existing templates
        categories = set()
        
        # Add from file templates
        for template in self.templates:
            category = template.get("category")
            if category:
                categories.add(category)
        
        # Add from directory templates
        for template in self.template_directories:
            category = template.get("category")
            if category:
                categories.add(category)
        
        # Add default categories
        for category in DEFAULT_TEMPLATE_CATEGORIES:
            categories.add(category)
        
        return sorted(list(categories))
    
    def get_all_templates(self):
        """Get all templates (both file and directory-based)"""
        return self.templates + self.template_directories
    
    def get_template_by_name(self, template_name):
        """Get a template by its name"""
        if not template_name:
            return None
            
        # Look in file templates
        for template in self.templates:
            if template.get('name') == template_name:
                return template
                
        # Look in directory templates
        for template in self.template_directories:
            if template.get('name') == template_name:
                return template
                
        return None
    
    def create_template_directory(self, name, category, source_dir, description=""):
        """Create a template directory from a source directory"""
        if not name or not source_dir or not os.path.isdir(source_dir):
            return False, "Invalid template name or source directory"
        
        # Create a clean directory name
        dir_name = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        template_dir = os.path.join(self.paths["template_directories_dir"], dir_name)
        
        # Check if template directory already exists
        if os.path.exists(template_dir):
            return False, f"Template '{name}' already exists"
        
        try:
            # Create template directory
            os.makedirs(template_dir, exist_ok=True)
            
            # Copy contents from source directory
            for item in os.listdir(source_dir):
                source_item = os.path.join(source_dir, item)
                target_item = os.path.join(template_dir, item)
                
                if os.path.isdir(source_item):
                    shutil.copytree(source_item, target_item)
                else:
                    shutil.copy2(source_item, target_item)
            
            # Create template.json
            template_info = {
                "name": name,
                "category": category,
                "description": description,
                "created": datetime.datetime.now().isoformat(),
                "type": "directory"
            }
            
            with open(os.path.join(template_dir, "template.json"), 'w') as f:
                json.dump(template_info, f, indent=2)
            
            # Update in-memory templates
            template_info["path"] = template_dir
            self.template_directories.append(template_info)
            
            return True, template_dir
            
        except Exception as e:
            error_msg = f"Failed to create template directory: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    def save_custom_structure(self, name, directories):
        """Save a custom folder structure"""
        if not name or not directories:
            return False
        
        structure = {
            "name": name,
            "directories": directories,
            "created": datetime.datetime.now().isoformat()
        }
        
        # Create a clean filename
        filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        file_path = os.path.join(self.paths["custom_structures_dir"], f"{filename}.json")
        
        success = save_json_file(file_path, structure)
        if success:
            # Update in-memory cache
            self.custom_structures[name] = structure
        
        return success
    
    def filter_templates(self, search_term=None, category=None):
        """Filter templates based on search term and category"""
        all_templates = self.get_all_templates()
        filtered = []
        
        for template in all_templates:
            # Filter by category if specified
            if category and category != "All" and template.get("category") != category:
                continue
            
            # Filter by search term if specified
            if search_term:
                search_term = search_term.lower()
                name = template.get("name", "").lower()
                desc = template.get("description", "").lower()
                
                if search_term not in name and search_term not in desc:
                    continue
            
            filtered.append(template)
        
        return filtered
    
    def create_template_list_frame(self, parent):
        """Create a scrollable frame for template list"""
        template_list_frame = ScrollableFrame(parent, bg=parent["bg"])
        template_list_frame.pack(fill="both", expand=True)
        return template_list_frame
    
    def create_template_card(self, parent, template, select_callback=None, **kwargs):
        """Create a card for a template"""
        # Create frame with rounded corners
        card = QFrame(parent, bg=colors["card_bg"], bd=0, **kwargs)
        card.template = template
        
        # Configure rounded corners using border styling
        card.setStyleSheet(f"background-color: {colors['card_bg']}; border: 1px solid {colors['card_bg']};")
        
        # Make entire card clickable
        if select_callback:
            card.mousePressEvent = lambda e: select_callback(template)
            
            # Add hover effects
            card.enterEvent = lambda e: self._on_card_hover_enter(card)
            card.leaveEvent = lambda e: self._on_card_hover_leave(card)
        
        # Icon - use emoji for simplicity
        icon = template.get("icon", "📂")
        icon_label = QLabel(card, text=icon, font=("Segoe UI", 24),
                               bg=colors["card_bg"], fg=colors["text"])
        icon_label.pack(side=Qt.LeftToRight, padx=10, pady=10)
        
        # Make icon clickable too
        if select_callback:
            icon_label.mousePressEvent = lambda e: select_callback(template)
            icon_label.enterEvent = lambda e: self._on_card_hover_enter(card)
            icon_label.leaveEvent = lambda e: self._on_card_hover_leave(card)
        
        # Info section
        info_frame = QFrame(card, bg=colors["card_bg"])
        info_frame.pack(side=Qt.LeftToRight, fill=Qt.Expanding, expand=True, pady=10)
        
        # Name
        name_label = QLabel(info_frame, text=template.get("name", "Unnamed Template"), 
                               font=("Segoe UI", 11, "bold"),
                               bg=colors["card_bg"], fg=colors["text"], anchor="w")
        name_label.pack(fill=Qt.Expanding)
        
        # Category
        category_label = QLabel(info_frame, text=template.get("category", "Custom"), 
                                   font=("Segoe UI", 9),
                                   bg=colors["card_bg"], fg=colors["secondary_text"], anchor="w")
        category_label.pack(fill=Qt.Expanding)
        
        # Description
        desc_label = QLabel(info_frame, text=template.get("description", ""), 
                               font=("Segoe UI", 9),
                               bg=colors["card_bg"], fg=colors["text"], 
                               anchor="w", justify=Qt.Left, wrapLength=350)
        desc_label.pack(fill=Qt.Expanding)
        
        # Make all labels clickable
        if select_callback:
            for label in [name_label, category_label, desc_label]:
                label.mousePressEvent = lambda e: select_callback(template)
                label.enterEvent = lambda e: self._on_card_hover_enter(card)
                label.leaveEvent = lambda e: self._on_card_hover_leave(card)
        
        return card
        
    def _on_card_hover_enter(self, card):
        """Handle hover enter for template card"""
        # Skip if card is already highlighted
        if hasattr(card, 'is_highlighted') and card.is_highlighted:
            return
            
        # Light grey hover effect
        hover_bg = "#303030"  # Slightly lighter than card_bg
        
        # Update the card and all its children - border should match background (no blue outline)
        card.setStyleSheet(f"background-color: {hover_bg}; border: 1px solid {hover_bg};")
        icon_label = card.findChild(QLabel, "icon_label")
        icon_label.setStyleSheet(f"background-color: {hover_bg};")
        info_frame = card.findChild(QFrame, "info_frame")
        info_frame.setStyleSheet(f"background-color: {hover_bg};")
        
        # Update all info frame widgets
        for widget in info_frame.findChildren(QLabel):
            widget.setStyleSheet(f"background-color: {hover_bg};")
        
        # Set cursor
        card.setCursor(Qt.PointingHandCursor)
    
    def _on_card_hover_leave(self, card):
        """Handle hover leave for template card"""
        # Skip if card is highlighted
        if hasattr(card, 'is_highlighted') and card.is_highlighted:
            return
            
        # Reset to card background
        card.setStyleSheet(f"background-color: {colors['card_bg']}; border: 1px solid {colors['card_bg']};")
        icon_label = card.findChild(QLabel, "icon_label")
        icon_label.setStyleSheet(f"background-color: {colors['card_bg']};")
        info_frame = card.findChild(QFrame, "info_frame")
        info_frame.setStyleSheet(f"background-color: {colors['card_bg']};")
        
        # Reset all info frame widgets with appropriate colors
        name_label = info_frame.findChild(QLabel, "name_label")
        name_label.setStyleSheet(f"background-color: {colors['card_bg']}; color: {colors['text']};")
        category_label = info_frame.findChild(QLabel, "category_label")
        category_label.setStyleSheet(f"background-color: {colors['card_bg']}; color: {colors['secondary_text']};")
        desc_label = info_frame.findChild(QLabel, "desc_label")
        desc_label.setStyleSheet(f"background-color: {colors['card_bg']}; color: {colors['text']};")
        
        # Reset cursor
        card.setCursor(Qt.ArrowCursor)
    
    def delete_custom_structure(self, name):
        """Delete a custom folder structure"""
        if name not in self.custom_structures:
            return False
        
        # Create a clean filename
        filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        file_path = os.path.join(self.paths["custom_structures_dir"], f"{filename}.json")
        
        try:
            os.remove(file_path)
            del self.custom_structures[name]
            return True
        except Exception as e:
            print(f"Error deleting structure {name}: {e}")
            return False
    
    def save_template(self, name, category, file_path, structure_type, description=None):
        """Save a template"""
        if not name or not category:
            return False
        
        # Create template info
        template = {
            "name": name,
            "category": category,
            "file": file_path if file_path else "",
            "type": structure_type,
            "description": description or f"{category} template",
            "structure_type": structure_type,
            "created": datetime.datetime.now().isoformat()
        }
        
        # Determine icon based on category
        icons = {
            "Video Editing": "🎬",
            "Motion Graphics": "✨",
            "Design": "📷",
            "Audio": "🎧",
            "Custom": "📂"
        }
        template["icon"] = icons.get(category, "📂")
        
        # Save to file
        filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        file_path = os.path.join(self.paths["templates_dir"], f"{filename}.json")
        
        success = save_json_file(file_path, template)
        if success:
            # Update in-memory cache
            self.templates.append(template)
        
        return success
    
    def save_template_ui(self, app):
        """Show UI for saving a template"""
        from PyQt5.QtWidgets import QDialog, QFrame, QLabel, QLineEdit, QPushButton, QOptionMenu, QStringVar
        
        if not app.template_file_path:
            QMessageBox.warning(app, "Warning", "Please select a template file first")
            return
            
        if not app.project_name.text().strip():
            QMessageBox.warning(app, "Warning", "Please enter a project name to use as template name")
            return
        
        # Create dialog
        dialog = QDialog(app)
        dialog.setWindowTitle("Save as Template")
        dialog.setGeometry(400, 300, 400, 300)
        dialog.setModal(True)
        dialog.exec_()
        
        frame = QFrame(dialog, padx=20, pady=20)
        frame.pack(fill=Qt.Expanding, expand=True)
        
        # Template name
        name_label = QLabel(frame, text="Template Name:", alignment=Qt.AlignLeft)
        name_label.pack(fill=Qt.Expanding, pady=(0, 5))
        
        name_var = QStringVar(value=app.project_name.text().strip())
        name_entry = QLineEdit(frame, textvariable=name_var)
        name_entry.pack(fill=Qt.Expanding, pady=(0, 15))
        
        # Category
        category_label = QLabel(frame, text="Template Category:", alignment=Qt.AlignLeft)
        category_label.pack(fill=Qt.Expanding, pady=(0, 5))
        
        categories = self.get_categories()
        if not categories:
            categories = ["Video Editing", "Motion Graphics", "Design", "Audio", "Custom"]
            
        category_var = QStringVar(value="Standard")
        category_menu = QOptionMenu(frame, category_var, *categories)
        category_menu.pack(fill=Qt.Expanding, pady=(0, 15))
        
        # Description
        desc_label = QLabel(frame, text="Description (optional):", alignment=Qt.AlignLeft)
        desc_label.pack(fill=Qt.Expanding, pady=(0, 5))
        
        desc_var = QStringVar()
        desc_entry = QLineEdit(frame, textvariable=desc_var)
        desc_entry.pack(fill=Qt.Expanding, pady=(0, 20))
        
        # Buttons
        button_frame = QFrame(frame)
        button_frame.pack(fill=Qt.Expanding)
        
        def save_template():
            name = name_var.get().strip()
            category = category_var.get()
            description = desc_var.get().strip()
            
            if not name:
                QMessageBox.warning(app, "Warning", "Template name is required")
                return
                
            # Save template
            success = self.save_template(
                name, 
                category, 
                app.template_file_path,
                "Standard",
                description
            )
            
            if success:
                QMessageBox.information(app, "Success", f"Template '{name}' saved successfully")
                dialog.accept()
                
                # Refresh template gallery
                from app.templates.templates import populate_template_gallery
                populate_template_gallery(app)
            else:
                QMessageBox.warning(app, "Warning", f"Failed to save template '{name}'")
        
        cancel_button = QPushButton(button_frame, text="Cancel", clicked=dialog.reject)
        cancel_button.pack(side=Qt.Left, padx=(0, 5))
        save_button = QPushButton(button_frame, text="Save", clicked=save_template)
        save_button.pack(side=Qt.Right)
        
        # Set focus to name entry
        name_entry.setFocus()
    
    def import_template_ui(self, app):
        """Show UI for importing a template"""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog
        
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            app,
            "Select Template File",
            "",
            "Project Files (*.prproj;*.aep;*.aepx;*.psd;*.ai);;Adobe Premiere (*.prproj);;After Effects (*.aep;*.aepx);;Photoshop (*.psd);;Illustrator (*.ai);;All Files (*.*)"
        )
        
        if not file_path:
            return
            
        # Get filename as default template name
        filename = os.path.basename(file_path)
        name, _ = os.path.splitext(filename)
        
        # Show dialog to confirm name and category
        template_name = QInputDialog.getText(app, "Import Template", "Template name:", text=name)
        
        if not template_name:
            return
            
        # Import the template
        success = self.import_template_file(file_path, template_name)
        
        if success:
            QMessageBox.information(app, "Success", f"Template '{template_name}' imported successfully")
            
            # Refresh template gallery
            from app.templates.templates import populate_template_gallery
            populate_template_gallery(app)
        else:
            QMessageBox.warning(app, "Warning", f"Failed to import template '{template_name}'")
    
    def manage_templates_ui(self, app):
        """Show UI for managing templates"""
        from PyQt5.QtWidgets import QDialog, QFrame, QLabel, QListWidget, QPushButton, QScrollBar, QListWidgetItem
        
        # Create dialog
        dialog = QDialog(app)
        dialog.setWindowTitle("Manage Templates")
        dialog.setGeometry(500, 400, 500, 400)
        dialog.setModal(True)
        dialog.exec_()
        
        frame = QFrame(dialog, padx=20, pady=20)
        frame.pack(fill=Qt.Expanding, expand=True)
        
        Label(frame, text="Templates", font=("Segoe UI", 14, "bold")).pack(anchor=Qt.AlignLeft, pady=(0, 15))
        
        # List with scrollbar
        list_frame = QFrame(frame)
        list_frame.pack(fill=Qt.Expanding, expand=True, pady=(0, 15))
        
        scrollbar = QScrollBar(list_frame)
        scrollbar.setOrientation(Qt.Vertical)
        scrollbar.pack(side=Qt.Right, fill=Qt.Expanding)
        
        template_listbox = QListWidget(list_frame)
        template_listbox.setViewMode(QListWidget.IconMode)
        template_listbox.setIconSize(QSize(64, 64))
        template_listbox.setResizeMode(QListWidget.Adjust)
        template_listbox.setGridSize(QSize(128, 128))
        template_listbox.itemClicked.connect(lambda: delete_template())
        template_listbox.itemDoubleClicked.connect(lambda: rename_template())
        template_listbox.addItems([f"{template['name']} ({template['category']})" for template in self.templates])
        template_listbox.addItems([f"{template['name']} ({template['category']})" for template in self.template_directories])
        
        # Button frame
        button_frame = QFrame(frame)
        button_frame.pack(fill=Qt.Expanding)
        
        def delete_template():
            selected = template_listbox.selectedIndexes()
            if not selected:
                QMessageBox.warning(app, "Warning", "Please select a template to delete")
                return
                
            index = selected[0].row()
            if index < 0 or index >= len(self.templates) + len(self.template_directories):
                return
                
            template = self.templates[index] if index < len(self.templates) else self.template_directories[index - len(self.templates)]
            template_name = template["name"]
            
            # Confirm deletion
            confirm = QMessageBox.question(app, "Confirm Deletion", 
                                        f"Are you sure you want to delete the template '{template_name}'?", QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.No:
                return
                
            # Delete the template
            success = self.delete_template(template_name)
            
            if success:
                QMessageBox.information(app, "Success", f"Template '{template_name}' deleted successfully")
                template_listbox.takeItem(index)
                
                # Refresh template gallery
                from app.templates.templates import populate_template_gallery
                populate_template_gallery(app)
            else:
                QMessageBox.warning(app, "Warning", f"Failed to delete template '{template_name}'")
        
        def rename_template():
            selected = template_listbox.selectedIndexes()
            if not selected:
                QMessageBox.warning(app, "Warning", "Please select a template to rename")
                return
                
            index = selected[0].row()
            if index < 0 or index >= len(self.templates) + len(self.template_directories):
                return
                
            template = self.templates[index] if index < len(self.templates) else self.template_directories[index - len(self.templates)]
            old_name = template["name"]
            
            # Get new name
            new_name = QInputDialog.getText(app, "Rename Template", "Enter new name:", text=old_name)
            
            if not new_name or new_name == old_name:
                return
                
            # Rename the template
            success = self.rename_template(old_name, new_name)
            
            if success:
                QMessageBox.information(app, "Success", f"Template renamed to '{new_name}'")
                template_listbox.takeItem(index)
                template_listbox.insertItem(index, QListWidgetItem(f"{new_name} ({template['category']})"))
                
                # Refresh template gallery
                from app.templates.templates import populate_template_gallery
                populate_template_gallery(app)
            else:
                QMessageBox.warning(app, "Warning", f"Failed to rename template")
        
        Button(button_frame, text="Delete", clicked=delete_template).pack(side=Qt.Left, padx=(0, 5))
        Button(button_frame, text="Rename", clicked=rename_template).pack(side=Qt.Left, padx=(0, 5))
        Button(button_frame, text="Close", clicked=dialog.accept).pack(side=Qt.Right)
    
    def delete_template(self, template_name):
        """Delete a template"""
        template_to_delete = None
        for template in self.templates:
            if template.get("name", "") == template_name:
                template_to_delete = template
                break
        
        if not template_to_delete:
            # Check if it's a directory template
            for template in self.template_directories:
                if template.get("name", "") == template_name:
                    return self.delete_template_directory(template)
            return False
        
        # Create a clean filename
        filename = template_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        file_path = os.path.join(self.paths["templates_dir"], f"{filename}.json")
        
        try:
            os.remove(file_path)
            self.templates.remove(template_to_delete)
            return True
        except Exception as e:
            print(f"Error deleting template {template_name}: {e}")
            return False
    
    def delete_template_directory(self, template):
        """Delete a directory-based template"""
        if not template or template.get('type') != 'directory':
            return False
            
        template_path = template.get('path')
        if not template_path or not os.path.isdir(template_path):
            return False
            
        template_name = template.get('name')
        
        try:
            # Delete the template directory
            shutil.rmtree(template_path)
            
            # Remove from in-memory list
            self.template_directories.remove(template)
            
            # Reload template directories to refresh the list
            self.load_template_directories()
            
            return True
        except Exception as e:
            print(f"Error deleting template directory {template_name}: {e}")
            return False
    
    def import_template_file(self, file_path, name=None, category=None):
        """Import a file as a template"""
        if not file_path or not os.path.exists(file_path):
            return False
        
        # Get filename as default name if not provided
        if not name:
            name = os.path.basename(file_path)
            name = os.path.splitext(name)[0]  # Remove extension
        
        # Determine project type from file extension
        _, ext = os.path.splitext(file_path)
        if not category:
            if ext.lower() in ['.prproj']:
                category = "Video Editing"
                structure_type = "Video Editing"
            elif ext.lower() in ['.aep', '.aepx']:
                category = "Motion Graphics"
                structure_type = "Motion Graphics"
            elif ext.lower() in ['.psd', '.ai']:
                category = "Design"
                structure_type = "Design"
            else:
                category = "Custom"
                structure_type = "Standard"
        else:
            structure_type = category
        
        # Save template
        return self.save_template(name, category, file_path, structure_type)
    
    def filter_templates(self, search_term=None, category=None):
        """Filter templates by search term and/or category"""
        if not search_term and (not category or category == "All"):
            return self.templates
        
        filtered = self.templates
        
        if search_term:
            search_term = search_term.lower()
            filtered = [t for t in filtered if 
                        search_term in t["name"].lower() or 
                        search_term in t.get("description", "").lower()]
        
        if category and category != "All":
            filtered = [t for t in filtered if t["category"] == category]
        
        return filtered
    
    def rename_template(self, old_name, new_name):
        """Rename a template"""
        if old_name == new_name:
            return True
        
        for template in self.templates:
            if template["name"] == old_name:
                # Create a clean filename for both old and new
                old_filename = old_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
                new_filename = new_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
                
                old_path = os.path.join(self.paths["templates_dir"], f"{old_filename}.json")
                new_path = os.path.join(self.paths["templates_dir"], f"{new_filename}.json")
                
                try:
                    # Update the template in memory
                    template["name"] = new_name
                    
                    # Save to new file
                    save_json_file(new_path, template)
                    
                    # Remove old file
                    if os.path.exists(old_path):
                        os.remove(old_path)
                    
                    return True
                except Exception as e:
                    print(f"Error renaming template {old_name} to {new_name}: {e}")
                    return False
        
        return False
    
    def rename_custom_structure(self, old_name, new_name):
        """Rename a custom structure"""
        if old_name == new_name:
            return True
        
        if old_name in self.custom_structures:
            # Create a clean filename for both old and new
            old_filename = old_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
            new_filename = new_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
            
            old_path = os.path.join(self.paths["custom_structures_dir"], f"{old_filename}.json")
            new_path = os.path.join(self.paths["custom_structures_dir"], f"{new_filename}.json")
            
            try:
                # Get the structure
                structure = self.custom_structures[old_name]
                
                # Update the name
                structure["name"] = new_name
                
                # Save to new file
                save_json_file(new_path, structure)
                
                # Remove old file
                if os.path.exists(old_path):
                    os.remove(old_path)
                
                # Update in-memory dictionary
                self.custom_structures[new_name] = structure
                del self.custom_structures[old_name]
                
                return True
            except Exception as e:
                print(f"Error renaming structure {old_name} to {new_name}: {e}")
                return False
        
        return False
    
    # ====== FOLDER MANAGEMENT METHODS ======
    
    def load_folders(self):
        """Load template folders from configuration"""
        # Path to folders configuration file
        folders_path = os.path.join(self.paths["templates_dir"], "folders.json")
        
        # Load folders if file exists
        if os.path.exists(folders_path):
            try:
                with open(folders_path, 'r') as f:
                    self.folders = json.load(f)
            except Exception as e:
                print(f"Error loading folders: {e}")
                self.folders = {}
        else:
            # Create default folders configuration
            self.folders = {
                "Recent": [],
                "Favorites": []
            }
            self.save_folders()
    
    def save_folders(self):
        """Save folder configuration"""
        folders_path = os.path.join(self.paths["templates_dir"], "folders.json")
        
        try:
            with open(folders_path, 'w') as f:
                json.dump(self.folders, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving folders: {e}")
            return False
    
    def get_folders(self):
        """Get list of all folders"""
        return list(self.folders.keys())
        
    def create_folder(self, folder_name):
        """Create a new template folder"""
        if not folder_name or folder_name in self.folders:
            return False
        
        self.folders[folder_name] = []
        return self.save_folders()
    
    # Alias for backwards compatibility
    add_folder = create_folder
    
    def rename_folder(self, old_name, new_name):
        """Rename a template folder"""
        if old_name not in self.folders or new_name in self.folders:
            return False
        
        # Get templates in the folder
        templates = self.folders[old_name]
        
        # Create new folder with same templates
        self.folders[new_name] = templates
        
        # Delete old folder
        del self.folders[old_name]
        
        return self.save_folders()
    
    def delete_folder(self, folder_name):
        """Delete a template folder"""
        if folder_name not in self.folders:
            return False
        
        # Remove folder (templates will still exist, just not in a folder)
        del self.folders[folder_name]
        
        return self.save_folders()
    
    # Alias for backwards compatibility
    remove_folder = delete_folder
    
    def add_to_folder(self, folder_name, template_name):
        """Add a template to a folder"""
        if folder_name not in self.folders:
            return False
        
        # Find the template to verify it exists
        template = None
        for t in self.templates:
            if t.get("name", "") == template_name:
                template = t
                break
                
        # Also check directory templates
        if not template:
            for t in self.template_directories:
                if t.get("name", "") == template_name:
                    template = t
                    break
        
        if not template:
            return False
        
        # Add to folder if not already there
        if template_name not in self.folders[folder_name]:
            self.folders[folder_name].append(template_name)
            return self.save_folders()
        
        return True
    
    def remove_from_folder(self, folder_name, template_name):
        """Remove a template from a folder"""
        if folder_name not in self.folders:
            return False
        
        # Remove from folder if present
        if template_name in self.folders[folder_name]:
            self.folders[folder_name].remove(template_name)
            return self.save_folders()
        
        return True
    
    def get_folder_templates(self, folder_name):
        """Get templates in a folder"""
        if folder_name not in self.folders:
            return []
        
        # Get template names in the folder
        template_names = self.folders[folder_name]
        
        # Get template objects
        templates = []
        for name in template_names:
            for template in self.templates:
                if template.get("name", "") == name:
                    templates.append(template)
                    break
                    
            # Also check directory templates
            for template in self.template_directories:
                if template.get("name", "") == name:
                    templates.append(template)
                    break
        
        return templates
    
    def get_templates_in_folder(self, folder_name):
        """Get templates in a specific folder (or root if None)"""
        if folder_name is None:
            # Return templates not in any folder
            all_template_names = []
            for folder, names in self.folders.items():
                all_template_names.extend(names)
                
            # Filter templates not in any folder
            return [t for t in self.templates if t.get("name", "") not in all_template_names]
        else:
            # Return templates in the specified folder
            return self.get_folder_templates(folder_name)
    
    def update_ui_folder_dropdown(self, app):
        """Update the folder dropdown in the UI to match current folders"""
        if not hasattr(app, 'folder_var'):
            return False
            
        try:
            # Get current folders
            folders = ["All"] + list(self.folders.keys())
            
            # Get the current selection
            current_folder = app.folder_var.currentText()
            
            # Update the dropdown menu
            menu = app.folder_var.model()
            menu.clear()
            
            # Add 'All' option
            menu.addItem("All", "All")
            
            # Add each folder - use a function to create a proper closure to avoid lambda capture issues
            def create_command(folder_name):
                return lambda: (app.folder_var.setCurrentText(folder_name), app.filter_templates())
                
            # Add each folder with proper command
            for folder in folders:
                if folder != "All":
                    menu.addItem(folder, folder)
            
            # If the previously selected folder is no longer available, default to "All"
            if current_folder not in folders:
                app.folder_var.setCurrentText("All")
                
            return True
        except Exception as e:
            print(f"Error updating folder dropdown: {e}")
            return False

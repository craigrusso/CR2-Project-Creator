#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Category Manager for Structure Editor

This module provides a dialog for managing template categories.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton,
                           QHBoxLayout, QLineEdit, QMessageBox, QListWidgetItem, QCheckBox, QInputDialog,
                           QComboBox, QApplication)
from PyQt5.QtCore import Qt
import os
import json

class CategoryManager(QDialog):
    """Dialog for managing template categories"""
    
    def __init__(self, parent=None, categories=None):
        """
        Initialize the category manager
        
        Args:
            parent: Parent widget
            categories: List of existing categories
        """
        super().__init__(parent)
        
        # Get the app instance and template manager if available
        self.app = self._get_app_instance(parent)
        self.template_manager = self._get_template_manager()
        
        # Store categories - use project_type_manager as source of truth
        if self.template_manager and hasattr(self.template_manager, 'get_categories'):
            self.categories = self.template_manager.get_categories()
            print(f"CategoryManager: Loaded {len(self.categories)} categories from template_manager: {self.categories}")
        elif categories:
            self.categories = categories[:]
        else:
            # Fallback default if no template manager
            from app.constants import DEFAULT_TEMPLATE_CATEGORIES
            self.categories = list(DEFAULT_TEMPLATE_CATEGORIES)
            print("CategoryManager: Using default categories from constants")
            
        # Ensure we have at least "Custom" category
        if "Custom" not in self.categories:
            self.categories.append("Custom")
            
        self.result_categories = self.categories.copy()
        
        # Configure dialog
        self.setWindowTitle("Manage Categories")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        # Create layout
        self._init_ui()
        
    def _get_app_instance(self, parent):
        """Get the application instance from the parent widget"""
        if parent is None:
            return None
        
        # Try to get app from parent's app attribute
        if hasattr(parent, 'app'):
            return parent.app
        
        # Try to get app from parent's parent
        if hasattr(parent, 'parent') and callable(parent.parent):
            parent_obj = parent.parent()
            if parent_obj and hasattr(parent_obj, 'app'):
                return parent_obj.app
        
        return None
    
    def _get_template_manager(self):
        """Get the template manager instance"""
        # Try to get from app
        if hasattr(self, 'app') and self.app and hasattr(self.app, 'template_manager'):
            return self.app.template_manager
        
        # If app not available, create a new instance
        try:
            from app.templates.template_manager import TemplateManager
            return TemplateManager()
        except ImportError:
            print("Warning: Could not import TemplateManager")
            return None
        
    def _init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Manage Categories")
        self.resize(400, 300)
        
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Category list
        self.category_list_label = QLabel("Categories:")
        main_layout.addWidget(self.category_list_label)
        
        self.category_list = QListWidget()
        main_layout.addWidget(self.category_list)
        
        # Add the hide defaults checkbox under the list
        self.hide_defaults_checkbox = QCheckBox("Hide Default Categories")
        # Get the current preference
        try:
            from app.core.config_manager import get_hide_default_categories
            hide_defaults = get_hide_default_categories()
            self.hide_defaults_checkbox.setChecked(hide_defaults)
        except ImportError:
            self.hide_defaults_checkbox.setChecked(False)
        
        self.hide_defaults_checkbox.stateChanged.connect(self._on_hide_defaults_changed)
        main_layout.addWidget(self.hide_defaults_checkbox)
        
        # Input for adding new categories
        input_layout = QHBoxLayout()
        main_layout.addLayout(input_layout)
        
        self.new_category_input = QLineEdit()
        self.new_category_input.setPlaceholderText("New Category")
        input_layout.addWidget(self.new_category_input)
        
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self._add_category)
        input_layout.addWidget(self.add_button)
        
        # Buttons for removing and modifying categories
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._remove_category)
        button_layout.addWidget(self.remove_button)
        
        self.rename_button = QPushButton("Rename")
        self.rename_button.clicked.connect(self._rename_category)
        button_layout.addWidget(self.rename_button)
        
        # Dialog buttons
        dialog_buttons = QHBoxLayout()
        main_layout.addLayout(dialog_buttons)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        dialog_buttons.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        dialog_buttons.addWidget(self.cancel_button)
        
        # Initialize the category list
        self._reload_category_list()
        
    def _on_hide_defaults_changed(self, state):
        """Handle the hide defaults checkbox state change"""
        try:
            from app.core.config_manager import set_hide_default_categories
            set_hide_default_categories(state == 2)  # Qt.Checked = 2
        except ImportError:
            pass  # Just use local state if config_manager not available
        
        # Reload the category list to reflect the current preference
        self._reload_category_list()
        
        # Update the app's dropdowns if possible
        self._update_ui_dropdowns()
        
    def _reload_category_list(self):
        """Reload the category list based on current settings"""
        # Clear the list
        self.category_list.clear()
        
        # Get the hide defaults preference
        try:
            from app.core.config_manager import get_hide_default_categories
            hide_defaults = get_hide_default_categories()
        except ImportError:
            hide_defaults = self.hide_defaults_checkbox.isChecked()
            
        # Import default categories
        from app.constants import DEFAULT_TEMPLATE_CATEGORIES
        
        # Get all current categories
        self._update_result()
        
        # Split categories into default and custom
        default_categories = []
        custom_categories = []
        
        for category in self.result_categories:
            if category in DEFAULT_TEMPLATE_CATEGORIES:
                default_categories.append(category)
            else:
                custom_categories.append(category)
        
        # Add default categories if not hiding them
        if not hide_defaults:
            for category in default_categories:
                item = QListWidgetItem(category)
                self.category_list.addItem(item)
            
            # Add a separator if we have custom categories
            if custom_categories:
                divider = QListWidgetItem("─" * 40)  # Use dash characters for visual separator
                divider.setFlags(Qt.NoItemFlags)  # Make it non-selectable
                self.category_list.addItem(divider)
        
        # Always add custom categories
        for category in custom_categories:
            item = QListWidgetItem(category)
            self.category_list.addItem(item)
        
    def _add_category(self):
        """Add a new category to the list"""
        # Get category name
        new_cat = self.new_category_input.text().strip()
        if not new_cat:
            return
            
        # Check if already exists
        existing_items = [self.category_list.item(i).text() for i in range(self.category_list.count()) 
                         if self.category_list.item(i).flags() & Qt.ItemIsSelectable]  # Skip dividers
        if new_cat in existing_items:
            QMessageBox.warning(self, "Duplicate", f"Category '{new_cat}' already exists")
            return
            
        # Determine if a divider already exists
        divider_exists = False
        divider_index = -1
        for i in range(self.category_list.count()):
            if not (self.category_list.item(i).flags() & Qt.ItemIsSelectable):
                divider_exists = True
                divider_index = i
                break
                
        # If no divider exists, add one before adding the custom category
        if not divider_exists:
            # Create and add divider
            divider = QListWidgetItem("─────── Custom Categories ───────")
            divider.setFlags(Qt.NoItemFlags)  # Make non-selectable
            divider.setTextAlignment(Qt.AlignCenter)
            
            # Apply styling to the divider
            divider_font = divider.font()
            divider_font.setBold(True)
            divider.setFont(divider_font)
            divider.setForeground(Qt.darkGray)
            
            self.category_list.addItem(divider)
            divider_index = self.category_list.count() - 1
            
        # Add the new category after the divider
        self.category_list.insertItem(divider_index + 1, new_cat)
        self.new_category_input.clear()
        
        # Update result categories
        self._update_result()
        
        # Save to template category manager
        self._save_to_category_manager()
        
        # Force immediate save to disk and reload
        if self.template_manager and hasattr(self.template_manager, 'project_type_manager'):
            print(f"Force-saving '{new_cat}' to project_type_manager")
            # Add the new category directly to ensure it's saved
            self.template_manager.project_type_manager.create_project_type(new_cat, "Video Editing - Standard")
            # Force reload to make it available immediately
            self.template_manager.project_type_manager.load_custom_project_types()
        
    def _remove_category(self):
        """Remove selected category from the list"""
        # Check if item selected
        selected = self.category_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select a category to remove")
            return
            
        # Don't allow removing "Custom"
        if selected[0].text() == "Custom":
            QMessageBox.warning(self, "Cannot Remove", "The 'Custom' category cannot be removed")
            return
            
        # Remove from list
        row = self.category_list.row(selected[0])
        self.category_list.takeItem(row)
        
        # Update result categories
        self._update_result()
        
        # Save to template category manager
        self._save_to_category_manager()
        
    def _update_result(self):
        """Update the result categories list"""
        # Get all categories from the list that aren't dividers
        self.result_categories = []
        for i in range(self.category_list.count()):
            item = self.category_list.item(i)
            if item.flags() & Qt.ItemIsSelectable:  # Skip dividers which aren't selectable
                category = item.text()
                if category not in self.result_categories:  # Avoid duplicates
                    self.result_categories.append(category)
        
        # Make sure "Custom" is always present
        if "Custom" not in self.result_categories:
            self.result_categories.insert(0, "Custom")
            # Add it to the list view too if not there already
            for i in range(self.category_list.count()):
                if self.category_list.item(i).text() == "Custom":
                    break
            else:  # Not found
                self.category_list.insertItem(0, "Custom")
    
    def _save_to_category_manager(self):
        """Save categories to the project type manager"""
        if not self.template_manager:
            return
        
        # Get updated categories
        self._update_result()
        
        # Use the project type manager to create/save categories
        if hasattr(self.template_manager, 'project_type_manager'):
            # Get existing project types to avoid duplicates
            existing_types = self.template_manager.project_type_manager.get_all_project_types()
            print(f"Existing project types: {existing_types}")
            
            # Get the structure mapping for smart defaults
            structure_mapping = {}
            if hasattr(self.template_manager, 'constants') and hasattr(self.template_manager.constants, 'PROJECT_TYPE_TO_STRUCTURE'):
                structure_mapping = self.template_manager.constants.PROJECT_TYPE_TO_STRUCTURE
            
            # Add each category as a project type if not already present
            for category in self.result_categories:
                if category not in existing_types:
                    # Select an appropriate structure based on category name
                    default_structure = "Video Editing - Standard"  # Default fallback
                    
                    # Map to appropriate structures based on category name
                    category_lower = category.lower()
                    if "video" in category_lower:
                        default_structure = "Video Editing - Standard"
                    elif "motion" in category_lower or "graphics" in category_lower:
                        default_structure = "Motion Graphics - Standard"
                    elif "vfx" in category_lower or "visual effects" in category_lower:
                        default_structure = "VFX - Standard"
                    elif "audio" in category_lower or "sound" in category_lower:
                        default_structure = "Video Editing - Standard"  # No specific audio structure yet
                    elif category in structure_mapping:
                        default_structure = structure_mapping[category]
                        
                    # Create the project type
                    self.template_manager.project_type_manager.create_project_type(category, default_structure)
                    print(f"Added category '{category}' as project type with structure '{default_structure}'")
        else:
            print("Warning: Project type manager not available")
    
    def _update_app_categories(self):
        """Update category dropdowns throughout the app"""
        if not self.app:
            return
            
        # Update template gallery if available
        if hasattr(self.app, 'template_gallery') and self.app.template_gallery:
            if hasattr(self.app.template_gallery, 'populate_gallery'):
                self.app.template_gallery.populate_gallery(force_refresh=True)
            elif hasattr(self.app.template_gallery, '_update_categories'):
                self.app.template_gallery._update_categories()
        
        # Update category combobox in template dialogs
        # This needs to happen in the next event cycle
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self._update_ui_dropdowns)
    
    def _update_ui_dropdowns(self):
        """Update any category dropdowns in the application with the new categories"""
        # Check if we have access to the application instance
        if not hasattr(self, 'app') or not self.app:
            return
        
        # Ensure template_manager has the latest categories
        if hasattr(self.app, 'template_manager'):
            # Get all categories
            if hasattr(self.app.template_manager, 'get_categories'):
                categories = self.app.template_manager.get_categories()
            else:
                # Fall back to local categories if method not available
                categories = self.result_categories
            
            # Check if we should hide default categories
            try:
                from app.core.config_manager import get_hide_default_categories
                hide_defaults = get_hide_default_categories()
            except ImportError:
                hide_defaults = self.hide_defaults_checkbox.isChecked()
            
            # Import default categories
            from app.constants import DEFAULT_TEMPLATE_CATEGORIES
            
            # Split categories into default and custom
            default_categories = []
            custom_categories = []
            
            for category in categories:
                if category in DEFAULT_TEMPLATE_CATEGORIES:
                    default_categories.append(category)
                else:
                    custom_categories.append(category)
            
            # Always include "Custom" even if defaults are hidden
            if hide_defaults and "Custom" not in custom_categories and "Custom" not in default_categories:
                custom_categories.append("Custom")
            
            # Find all QComboBox widgets that might hold categories
            for widget in self.app.findChildren(QComboBox):
                # Check if this looks like a category dropdown (by name or items)
                if hasattr(widget, 'objectName') and ('category' in widget.objectName().lower() or 
                                                     any('Category' in widget.itemText(i) for i in range(widget.count()))):
                    current_text = widget.currentText()
                    widget.clear()
                    
                    # Add the categories based on the hide setting
                    if not hide_defaults:
                        # Add default categories if we're showing them
                        for category in default_categories:
                            widget.addItem(category)
                        
                        # Add a separator if we have custom categories
                        if custom_categories:
                            widget.insertSeparator(widget.count())
                    
                    # Add custom categories
                    for category in custom_categories:
                        widget.addItem(category)
                    
                    # Try to restore the previous selection
                    index = widget.findText(current_text)
                    if index >= 0:
                        widget.setCurrentIndex(index)
                    elif widget.count() > 0:
                        widget.setCurrentIndex(0)
        
        # Force a UI refresh
        QApplication.processEvents()
        
    def get_categories(self):
        """
        Get the resulting categories
        
        Returns:
            list: List of categories
        """
        # Make sure result is up to date
        self._update_result()
        return self.result_categories
    
    def accept(self):
        """Override the accept method to update categories in the app"""
        # Make sure to update the result categories
        self._update_result()
        
        # Force saving all categories to project_type_manager
        if self.template_manager and hasattr(self.template_manager, 'project_type_manager'):
            # Use a default structure for any new categories
            default_structure = "Video Editing - Standard"
            
            # Get existing project types to avoid duplicates
            existing_types = self.template_manager.project_type_manager.get_all_project_types()
            
            # Add each category as a project type if not already saved
            added_count = 0
            for category in self.result_categories:
                if category not in existing_types:
                    success = self.template_manager.project_type_manager.create_project_type(category, default_structure)
                    if success:
                        added_count += 1
                        print(f"Successfully added category '{category}' to project_type_manager")
                    else:
                        print(f"Failed to add category '{category}' to project_type_manager")
            
            if added_count > 0:
                print(f"Added {added_count} new categories to project_type_manager")
        
        # Save categories to template manager
        self._save_to_category_manager()
        
        # Update UI dropdowns
        self._update_app_categories()
        
        # Call the parent method
        super().accept()

    def _rename_category(self):
        """Rename the selected category"""
        current_index = self.category_list.currentRow()
        if current_index < 0:
            QMessageBox.warning(self, "No Selection", "Please select a category to rename.")
            return
        
        # Get the current item text
        current_item = self.category_list.item(current_index)
        current_name = current_item.text()
        
        # Check if this is a default category
        from app.constants import DEFAULT_TEMPLATE_CATEGORIES
        if current_name in DEFAULT_TEMPLATE_CATEGORIES:
            QMessageBox.warning(self, "Cannot Rename", 
                               f"Default category '{current_name}' cannot be renamed.")
            return
        
        # Don't allow renaming of dividers
        if "─" in current_name:
            return
        
        # Get the new name from the user
        new_name, ok = QInputDialog.getText(self, "Rename Category", 
                                          "New Category Name:", 
                                          QLineEdit.Normal, 
                                          current_name)
        
        if not ok or not new_name.strip():
            return
        
        new_name = new_name.strip()
        
        # Check if the new name already exists
        for i in range(self.category_list.count()):
            if i != current_index and self.category_list.item(i).text() == new_name:
                QMessageBox.warning(self, "Duplicate Name", 
                                  f"Category '{new_name}' already exists.")
                return
        
        # Update the item in the list
        current_item.setText(new_name)
        
        # Update our internal list
        self._update_result()
        
        # If we have a reference to the template manager, update it
        if hasattr(self, 'template_manager') and self.template_manager:
            if hasattr(self.template_manager, 'project_type_manager'):
                # Find and update the category in the project_type_manager
                ptm = self.template_manager.project_type_manager
                if hasattr(ptm, 'rename_project_type'):
                    ptm.rename_project_type(current_name, new_name)
                else:
                    # Manual fallback if no dedicated method exists
                    ptm.remove_project_type(current_name)
                    ptm.add_project_type(new_name)
                    ptm.save_custom_project_types()
        
        # Update UI dropdowns
        self._update_ui_dropdowns()

def manage_categories(parent=None, categories=None):
    """
    Show dialog to manage template categories
    
    Args:
        parent: Parent widget
        categories: List of existing categories
        
    Returns:
        list: Updated list of categories, or None if canceled
    """
    # Create and show dialog
    dialog = CategoryManager(parent, categories)
    result = dialog.exec_()
    
    # Return categories if accepted
    if result == QDialog.Accepted:
        return dialog.get_categories()
    
    # Return None if canceled
    return None 
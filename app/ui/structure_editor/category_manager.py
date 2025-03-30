#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Category Manager for Structure Editor

This module provides a dialog for managing template categories.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton,
                           QHBoxLayout, QLineEdit, QMessageBox)
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
        """Initialize the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Add title
        title = QLabel("Template Categories")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Add description
        description = QLabel("Add, edit, or remove template categories.")
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Add list of categories
        self.category_list = QListWidget()
        for category in self.categories:
            self.category_list.addItem(category)
        layout.addWidget(self.category_list)
        
        # Add input for new category
        input_layout = QHBoxLayout()
        self.new_category_input = QLineEdit()
        self.new_category_input.setPlaceholderText("New category name")
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self._add_category)
        input_layout.addWidget(self.new_category_input, 3)
        input_layout.addWidget(self.add_btn, 1)
        layout.addLayout(input_layout)
        
        # Add button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self._remove_category)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.remove_btn)
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)
        
        # Set close button as default
        self.close_btn.setDefault(True)
        
    def _add_category(self):
        """Add a new category to the list"""
        # Get category name
        new_cat = self.new_category_input.text().strip()
        if not new_cat:
            return
            
        # Check if already exists
        existing_items = [self.category_list.item(i).text() for i in range(self.category_list.count())]
        if new_cat in existing_items:
            QMessageBox.warning(self, "Duplicate", f"Category '{new_cat}' already exists")
            return
            
        # Add to list
        self.category_list.addItem(new_cat)
        self.new_category_input.clear()
        
        # Update result categories
        self._update_result()
        
        # Save to template category manager
        self._save_to_category_manager()
        
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
        # Get all categories from the list
        self.result_categories = [self.category_list.item(i).text() for i in range(self.category_list.count())]
        
        # Make sure "Custom" is always present
        if "Custom" not in self.result_categories:
            self.result_categories.insert(0, "Custom")
            # Add it to the list view too
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
        """Update category dropdowns in all UI components"""
        if not self.app:
            return
            
        # Ensure template_manager has the latest categories
        if hasattr(self.app, 'template_manager'):
            # Update project types
            if hasattr(self.app.template_manager, 'project_type_manager'):
                # Force reload of project types
                self.app.template_manager.project_type_manager.load_custom_project_types()
                
        # Get all updated categories from the template manager
        all_categories = []
        if hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'get_categories'):
            all_categories = self.app.template_manager.get_categories()
            print(f"CategoryManager: Updating UI with categories from template_manager: {all_categories}")
        else:
            all_categories = self.result_categories
            print(f"CategoryManager: Updating UI with local categories: {all_categories}")
            
        # Find and update all QComboBox widgets containing categories
        from PyQt5.QtWidgets import QApplication, QComboBox
        updated_widgets = 0
        
        for widget in QApplication.allWidgets():
            if isinstance(widget, QComboBox):
                # Try to identify category dropdowns
                widget_parent = widget.parent()
                widget_name = widget.objectName().lower()
                is_category_dropdown = False
                
                # Method 1: Check if the widget is named appropriately
                if any(term in widget_name for term in ["category", "categories", "type"]):
                    is_category_dropdown = True
                
                # Method 2: Check if the widget has the typical category values
                elif widget.count() > 0:
                    items = [widget.itemText(i) for i in range(widget.count())]
                    if "Custom" in items and any(cat in items for cat in ["Audio", "Video", "Photography", "Graphics"]):
                        is_category_dropdown = True
                
                # Method 3: Check if this widget is used in a structure/template editor
                elif widget_parent:
                    parent_class = widget_parent.__class__.__name__.lower()
                    if any(term in parent_class for term in ["editor", "template", "structure"]):
                        label_text = self._find_associated_label(widget)
                        if label_text and "category" in label_text.lower():
                            is_category_dropdown = True
                
                # Special case: Template gallery filter dropdowns
                is_gallery_dropdown = (widget.count() >= 2 and 
                                      widget.itemText(0) == "All" and 
                                      any(cat in [widget.itemText(i) for i in range(widget.count())] 
                                          for cat in ["Custom", "Video", "Audio"]))
                
                # Update the dropdown if it's identified as a category dropdown
                if is_category_dropdown or is_gallery_dropdown:
                    # Store current selection
                    current = widget.currentText()
                    current_items = [widget.itemText(i) for i in range(widget.count())]
                    
                    print(f"Found category dropdown: {widget_name} with {widget.count()} items: {current_items}")
                    
                    # Update items
                    widget.clear()
                    
                    # If this is a gallery dropdown that needs "All" option first
                    if is_gallery_dropdown or "All" in current_items:
                        widget.addItem("All")
                    
                    # Add all categories
                    widget.addItems(all_categories)
                    
                    # Try to restore the previous selection
                    index = widget.findText(current)
                    if index >= 0:
                        widget.setCurrentIndex(index)
                    elif widget.count() > 0:
                        # Fallback to first item
                        widget.setCurrentIndex(0)
                    
                    updated_widgets += 1
                    print(f"Updated dropdown to {widget.count()} items: {[widget.itemText(i) for i in range(widget.count())]}")
        
        print(f"CategoryManager: Updated {updated_widgets} dropdown widgets with categories")
            
        # Force a UI refresh
        QApplication.processEvents()
        
    def _find_associated_label(self, widget):
        """Find the label text associated with a widget"""
        from PyQt5.QtWidgets import QLabel
        
        # Check siblings in layout
        parent = widget.parent()
        if parent:
            for child in parent.findChildren(QLabel):
                if child.buddy() == widget:
                    return child.text()
        
        return None
    
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
        # Save categories to template manager
        self._save_to_category_manager()
        
        # Update UI dropdowns
        self._update_app_categories()
        
        # Call the parent method
        super().accept()

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
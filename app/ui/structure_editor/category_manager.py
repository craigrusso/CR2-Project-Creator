#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Category Manager for Structure Editor

This module provides a dialog for managing template categories.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton,
                           QHBoxLayout, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt

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
        
        # Store categories
        self.categories = categories or ["Custom"]
        self.result_categories = self.categories.copy()
        
        # Configure dialog
        self.setWindowTitle("Manage Categories")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        # Create layout
        self._init_ui()
        
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
        
    def _update_result(self):
        """Update the result categories list"""
        # Get all categories from the list
        self.result_categories = [self.category_list.item(i).text() for i in range(self.category_list.count())]
        
        # Make sure "Custom" is always present
        if "Custom" not in self.result_categories:
            self.result_categories.insert(0, "Custom")
            # Add it to the list view too
            self.category_list.insertItem(0, "Custom")
            
    def get_categories(self):
        """
        Get the resulting categories
        
        Returns:
            list: List of categories
        """
        # Make sure result is up to date
        self._update_result()
        return self.result_categories

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
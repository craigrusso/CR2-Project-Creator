#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Category Manager for Structure Editor

This module provides a dialog for managing template categories.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton,
                           QHBoxLayout, QLineEdit, QMessageBox, QListWidgetItem, QCheckBox, QComboBox, QListView, QStyledItemDelegate, QInputDialog)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
import os
import json

# Define a user role for the divider item
DIVIDER_ROLE = Qt.ItemDataRole.UserRole + 1

# Import necessary modules
from app.ui.color_scheme_pyqt import APP_COLORS

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
        
        # Initialize QSettings
        self.settings = QSettings()
        
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
        
        # Add checkbox to hide default categories
        self.hide_defaults_checkbox = QCheckBox("Hide Default Categories")
        self.hide_defaults_checkbox.stateChanged.connect(self._toggle_default_categories_visibility)
        self.hide_defaults_checkbox.stateChanged.connect(self._save_hide_defaults_setting)
        layout.addWidget(self.hide_defaults_checkbox)
        
        # Add list of categories
        self.category_list = QListWidget()
        
        # Import default categories
        from app.constants import DEFAULT_TEMPLATE_CATEGORIES
        
        # Get all current categories from template manager (if available)
        if self.template_manager and hasattr(self.template_manager, 'get_categories'):
            self.categories = self.template_manager.get_categories()
        else:
            self.categories = list(DEFAULT_TEMPLATE_CATEGORIES)
        
        # Ensure "Custom" is always present
        if "Custom" not in self.categories:
            self.categories.append("Custom")
        
        # Use a set to remove duplicates and maintain order for display
        unique_categories = list(dict.fromkeys(self.categories))
        
        # Split categories into default and custom
        default_categories = []
        custom_categories = []
        
        for category in unique_categories:
            if category in DEFAULT_TEMPLATE_CATEGORIES:
                default_categories.append(category)
            else:
                custom_categories.append(category)
        
        # Add default categories first
        for category in default_categories:
            self.category_list.addItem(category)
            
        # Add a divider if there are custom categories
        self.divider_item = None # Store reference to the divider item
        if custom_categories:
            divider = QListWidgetItem("─────── Custom Categories ───────")
            divider.setFlags(Qt.ItemFlag(0))  # Make non-selectable
            divider.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            divider.setData(DIVIDER_ROLE, True) # Mark as divider
            
            # Apply styling to the divider
            divider_font = divider.font()
            divider_font.setBold(True)
            divider.setFont(divider_font)
            divider.setForeground(QColor(Qt.GlobalColor.darkGray))
            
            self.category_list.addItem(divider)
            self.divider_item = divider # Store reference
            
            # Add custom categories after divider
            for category in custom_categories:
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
        self.close_btn.setObjectName("closeButtonAccent") # Set object name for styling
        # Also apply style directly for higher specificity
        from app.ui.color_scheme_pyqt import ACCENT_BUTTON_STYLE
        self.close_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        
        button_layout.addWidget(self.remove_btn)
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)
        
        # Set close button as default
        self.close_btn.setDefault(True)
        
        # Load initial checkbox state and apply visibility
        self._load_hide_defaults_setting()
        self._toggle_default_categories_visibility() # Apply initial state
        
    def _add_category(self):
        """Add a new category to the list and save"""
        category_name_from_input = self.new_category_input.text().strip()

        if category_name_from_input:
            category_name = category_name_from_input
            ok = True # Assume ok if text was present in the input field
        else:
            # If the input field was empty, then show the dialog
            category_name, ok = QInputDialog.getText(self, "Add Category", "Category Name:")

        if ok and category_name:
            category_name = category_name.strip()
            if not category_name:
                QMessageBox.warning(self, "Invalid Name", "Category name cannot be empty.")
                return

            # Check for duplicates (case-insensitive)
            existing_categories = [
                self.category_list.item(i).text().lower()
                for i in range(self.category_list.count())
                if self.category_list.item(i).flags() & Qt.ItemFlag.ItemIsSelectable 
            ]
            if category_name.lower() in existing_categories:
                QMessageBox.warning(self, "Duplicate Category", f"The category '{category_name}' already exists.")
                return

            # Add to list widget
            item = QListWidgetItem(category_name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsSelectable) 
            self.category_list.addItem(item)
            self.category_list.setCurrentItem(item)
            self.category_list.sortItems() # Keep the list sorted
            
            # Clear the input field after successful addition
            self.new_category_input.clear()

            # Save and refresh
            self._save_to_category_manager()
            self._update_ui_dropdowns()
            print(f"DEBUG (CategoryManager): Added category '{category_name}'")
        
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
        
        # Call the appropriate method on ProjectTypeManager to remove
        category_name = selected[0].text()
        if self.template_manager and hasattr(self.template_manager, 'project_type_manager'):
            print(f"Attempting to delete project type: {category_name}")
            success = self.template_manager.project_type_manager.delete_project_type(category_name)
            if success:
                print(f"Successfully deleted project type '{category_name}'")
                # Update categories list in memory (might be redundant if reload happens)
                if category_name in self.categories:
                    self.categories.remove(category_name)
                # Update UI dropdowns immediately
                self._update_ui_dropdowns()
            else:
                print(f"Failed to delete project type '{category_name}' via manager (might be default or already removed)")
                # Optionally show a message if deletion fails unexpectedly
                # QMessageBox.warning(self, "Deletion Failed", f"Could not delete category '{category_name}'.")
                # Re-add item to list if deletion failed?
                # self.category_list.insertItem(row, category_name)
                # self._update_result() # Re-update result if re-added
        else:
            print("Project type manager not found, cannot delete from backend.")
            # If no manager, just update internal lists
            if category_name in self.categories:
                 self.categories.remove(category_name)
            self._update_result()
        
        # Reload the list to reflect the changes (including divider removal if needed)
        self._reload_category_list()
        
    def _reload_category_list(self):
        """Reloads the category list preserving the hide defaults state"""
        # Get current state
        hide_defaults = self.hide_defaults_checkbox.isChecked()
        
        # Clear the list
        self.category_list.clear()
        self.divider_item = None # Reset divider reference
        
        # Repopulate based on current self.categories
        from app.constants import DEFAULT_TEMPLATE_CATEGORIES
        
        # Use a set to remove duplicates and maintain order for display
        unique_categories = list(dict.fromkeys(self.categories))
        
        # Split categories into default and custom
        default_categories = []
        custom_categories = []
        
        for category in unique_categories:
            if category in DEFAULT_TEMPLATE_CATEGORIES:
                default_categories.append(category)
            else:
                custom_categories.append(category)
        
        # Add default categories first
        for category in default_categories:
            self.category_list.addItem(category)
            
        # Add a divider if there are custom categories
        if custom_categories:
            divider = QListWidgetItem("─────── Custom Categories ───────")
            divider.setFlags(Qt.ItemFlag(0))  # Make non-selectable
            divider.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            divider.setData(DIVIDER_ROLE, True) # Mark as divider
            
            # Apply styling to the divider
            divider_font = divider.font()
            divider_font.setBold(True)
            divider.setFont(divider_font)
            divider.setForeground(QColor(Qt.GlobalColor.darkGray))
            
            self.category_list.addItem(divider)
            self.divider_item = divider # Store reference
            
            # Add custom categories after divider
            for category in custom_categories:
                self.category_list.addItem(category)
                
        # Re-apply visibility based on checkbox state
        self._toggle_default_categories_visibility()
        
    def _update_result(self):
        """Update the result list based on the current list widget content"""
        # Get all categories from the list that aren't dividers
        self.result_categories = []
        for i in range(self.category_list.count()):
            item = self.category_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsSelectable:  # Only include selectable items
                self.result_categories.append(item.text())
        
        print(f"CategoryManager: Updated result categories: {self.result_categories}")
    
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
            
            # REMOVE this incorrect call - saving is handled by create_project_type
            # self.template_manager.save_categories(self.result_categories)
            # print(f"CategoryManager: Saved {len(self.result_categories)} categories to template manager.")
            
            # Immediately update the UI dropdowns after saving
            self._update_ui_dropdowns()
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
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._update_ui_dropdowns)
    
    def _update_ui_dropdowns(self):
        """Update known category dropdowns in the main UI components"""
        print("CategoryManager: Updating UI dropdowns...")
        if not self.app:
            print("CategoryManager: App instance not found, cannot update dropdowns.")
            return
            
        # Get the latest categories
        all_categories = []
        if hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'get_categories'):
            all_categories = self.app.template_manager.get_categories()
            print(f"Using categories from template_manager: {all_categories}")
        else:
            # Fallback to current result categories if manager isn't available
            self._update_result()
            all_categories = self.result_categories
            print(f"Using local categories fallback: {all_categories}")
            
        # Check the hide defaults setting
        hide_defaults = self.settings.value("CategoryManager/hideDefaultCategories", False, type=bool)
        categories_to_show = all_categories
        
        if hide_defaults:
            from app.constants import DEFAULT_TEMPLATE_CATEGORIES
            categories_to_show = [cat for cat in all_categories if cat not in DEFAULT_TEMPLATE_CATEGORIES]
            print(f"Filtered categories (hide defaults): {categories_to_show}")
        else:
            print(f"Showing all categories (hide defaults is off): {categories_to_show}")

        # Use findChildren on the main app window to be more targeted than allWidgets
        from PyQt6.QtWidgets import QComboBox
        project_type_combos = self.app.findChildren(QComboBox, "project_type_combo_box")
        template_category_combos = self.app.findChildren(QComboBox, "template_category_combo_box")
        
        # Combine the lists
        all_target_combos = project_type_combos + template_category_combos
        updated_widgets = 0
        
        print(f"Found {len(project_type_combos)} widgets with name 'project_type_combo_box'.")
        print(f"Found {len(template_category_combos)} widgets with name 'template_category_combo_box'.")
        print(f"Total target dropdowns: {len(all_target_combos)}")
        
        for combo_box in all_target_combos:
            if combo_box:
                current_text = combo_box.currentText()
                print(f"Updating dropdown: {combo_box.objectName()}, current selection: {current_text}")
                
                # Clear and repopulate with potential separator
                combo_box.clear()
                
                if not hide_defaults:
                    # Separate default and custom
                    from app.constants import DEFAULT_TEMPLATE_CATEGORIES
                    default_cats = sorted([cat for cat in categories_to_show if cat in DEFAULT_TEMPLATE_CATEGORIES])
                    custom_cats = sorted([cat for cat in categories_to_show if cat not in DEFAULT_TEMPLATE_CATEGORIES])
                    
                    # Define labels
                    default_label = "Default Categories"
                    custom_label = "Custom Categories"

                    # --- Add Items with Labels and Separator ---
                    combo_box.blockSignals(True) # Block signals during modification

                    # Add Default Label and Items
                    default_label_item = QStandardItem(default_label)
                    default_label_item.setEnabled(False) # Disable label
                    # Set grey color for the label text
                    default_label_item.setForeground(QColor(APP_COLORS['secondary_text']))
                    model = combo_box.model()
                    if isinstance(model, QStandardItemModel):
                         model.appendRow(default_label_item)
                    else:
                         print("Warning: Could not add default label, model is not QStandardItemModel")

                    for cat in default_cats:
                        combo_box.addItem(cat)

                    # Add Separator and Custom Section (if needed)
                    if custom_cats:
                        # Check if default categories were added before adding separator
                        if default_cats: 
                            combo_box.insertSeparator(combo_box.count()) 

                        # Add Custom Label
                        custom_label_item = QStandardItem(custom_label)
                        custom_label_item.setEnabled(False) # Disable label
                        # Set grey color for the label text
                        custom_label_item.setForeground(QColor(APP_COLORS['secondary_text']))
                        model = combo_box.model()
                        if isinstance(model, QStandardItemModel):
                            model.appendRow(custom_label_item)
                        else:
                            print("Warning: Could not add custom label, model is not QStandardItemModel")

                        # Add Custom Categories
                        for cat in custom_cats:
                            combo_box.addItem(cat)
                    # --- End Add Items ---

                    combo_box.blockSignals(False) # Re-enable signals
                else:
                    # Only custom categories, add them sorted
                    combo_box.addItems(sorted(categories_to_show))
                    
                # Try to restore selection
                index = combo_box.findText(current_text)
                if index != -1:
                    combo_box.setCurrentIndex(index)
                elif combo_box.count() > 0:
                    combo_box.setCurrentIndex(0) # Default to first item
                    
                combo_box.setEnabled(combo_box.count() > 0)
                updated_widgets += 1
                print(f"Dropdown {combo_box.objectName()} updated with {combo_box.count()} items.")
                
        # --- Add logic here to find and update other specific dropdowns if needed ---
        # Example: Update template gallery filter (if its objectName is known)
        # gallery_filter_combo = self.app.findChild(QComboBox, "galleryCategoryFilter")
        # if gallery_filter_combo:
        #     # ... (update logic similar to above, potentially adding "All") ...
        #     pass
        # --------------------------------------------------------------------------

        print(f"CategoryManager: Finished updating {updated_widgets} dropdown widgets.")
            
        # Optional: Force a UI refresh if needed, though often not necessary
        # from PyQt6.QtWidgets import QApplication
        # QApplication.processEvents()
        
    def _find_associated_label(self, widget):
        """Try to find a QLabel associated with this widget"""
        from PyQt6.QtWidgets import QLabel
        
        # Check siblings in layout
        parent = widget.parent()
        if parent:
            for child in parent.findChildren(QLabel):
                if child.buddy() == widget:
                    return child.text()
        
        return None
    
    def get_categories(self):
        """Return the updated list of categories"""
        # Ensure results are updated before returning
        self._update_result()
        return self.result_categories[:]

    # --- Methods for handling checkbox state and visibility ---
    
    def _load_hide_defaults_setting(self):
        """Load the hide default categories setting from QSettings"""
        hide_defaults = self.settings.value("CategoryManager/hideDefaultCategories", False, type=bool)
        self.hide_defaults_checkbox.setChecked(hide_defaults)
        print(f"Loaded hideDefaultCategories setting: {hide_defaults}")
        
    def _save_hide_defaults_setting(self):
        """Save the hide default categories setting to QSettings"""
        state = self.hide_defaults_checkbox.isChecked()
        self.settings.setValue("CategoryManager/hideDefaultCategories", state)
        print(f"Saved hideDefaultCategories setting: {state}")
        # Immediately trigger dropdown updates when the setting changes
        self._update_ui_dropdowns()

    def _toggle_default_categories_visibility(self):
        """Hide or show default categories and the divider in the list"""
        hide = self.hide_defaults_checkbox.isChecked()
        print(f"Toggling default category visibility: {'Hide' if hide else 'Show'}")
        
        from app.constants import DEFAULT_TEMPLATE_CATEGORIES
        
        found_defaults = False
        for i in range(self.category_list.count()):
            item = self.category_list.item(i)
            if item.data(DIVIDER_ROLE):
                # Hide/show divider based on checkbox AND if there are actually defaults to hide
                item.setHidden(hide and found_defaults)
            elif item.text() in DEFAULT_TEMPLATE_CATEGORIES:
                item.setHidden(hide)
                if not hide:
                     found_defaults = True # Mark that we found defaults to show
            else:
                 # Custom items always visible
                 item.setHidden(False)
                 
        # If hiding defaults, and the divider exists but no defaults were found (e.g., all removed), hide divider too
        # This scenario is less likely given defaults can't be removed, but good practice
        if hide and self.divider_item and not any(self.category_list.item(i).text() in DEFAULT_TEMPLATE_CATEGORIES for i in range(self.category_list.count()) if not self.category_list.item(i).data(DIVIDER_ROLE)):
             self.divider_item.setHidden(True)
             
    # --- End checkbox methods ---

    def accept(self):
        """Save changes when closing"""
        print("Category Manager: Accepting changes (Close clicked)")
        # Saving is now handled dynamically on add/remove and checkbox toggle
        # self._save_to_category_manager() # No longer needed here if handled dynamically
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
    result = dialog.exec()
    
    # Return categories if accepted
    if result == QDialog.Accepted:
        return dialog.get_categories()
    
    # Return None if canceled
    return None 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Category Management Dialog

This module provides a dialog for managing template categories.
It interacts with the central CategoryUpdateManager to propagate changes.
"""
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton,
                           QHBoxLayout, QLineEdit, QMessageBox, QListWidgetItem, QCheckBox, QInputDialog)
from PyQt6.QtCore import Qt, QSettings, QTimer
from PyQt6.QtGui import QColor

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE
# from app.templates.category_update_manager import get_instance as get_category_update_manager_instance # Moved into __init__
from app.constants import DEFAULT_TEMPLATE_CATEGORIES

# Define a user role for the divider item
DIVIDER_ROLE = Qt.ItemDataRole.UserRole + 1

log = logging.getLogger(__name__)

class CategoryManagementDialog(QDialog):
    """Dialog for managing template categories"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.app = self._get_app_instance(parent)
        self.template_manager = self._get_template_manager() # For saving/loading categories
        
        from app.templates.category_update_manager import get_instance as get_category_update_manager_instance # Import moved here
        self.category_update_manager = get_category_update_manager_instance(self.app)
        
        self.current_categories = [] # This will hold the categories being edited
        if self.template_manager and hasattr(self.template_manager, 'get_categories'):
            # Load initial categories from the source of truth
            self.current_categories = self.template_manager.get_categories()
            log.debug(f"CategoryManagementDialog: Loaded {len(self.current_categories)} categories from template_manager: {self.current_categories}")
        else:
            self.current_categories = list(DEFAULT_TEMPLATE_CATEGORIES)
            log.warning("CategoryManagementDialog: Using default categories from constants as template_manager was not available or lacked get_categories.")
            
        # Ensure "Custom" is always present as a fallback or default custom category
        if "Custom" not in self.current_categories:
            self.current_categories.append("Custom")
            
        self.settings = QSettings()
        self.hide_defaults_initial_state = self.settings.value("category_manager/hide_defaults", False, type=bool)
        self.hide_defaults_setting_changed_during_session = False
        
        self.setWindowTitle("Manage Categories")
        self.setMinimumWidth(450) # Increased width slightly
        self.setMinimumHeight(350)
        
        self._init_ui()
        self._load_hide_defaults_setting() # Apply after UI is built
        self._reload_category_list() # Populate the list

    def _get_app_instance(self, parent):
        if parent and hasattr(parent, 'app'):
            return parent.app
        current_widget = parent
        while current_widget:
            if hasattr(current_widget, 'app_instance') and current_widget.app_instance:
                 return current_widget.app_instance # Common pattern in my app for main window
            if hasattr(current_widget, 'app') and current_widget.app: # Check for 'app' attribute too
                 return current_widget.app
            if isinstance(current_widget, QDialog) and hasattr(current_widget, 'parent') and callable(current_widget.parent):
                 current_widget = current_widget.parent()
                 if current_widget and hasattr(current_widget, 'app'):
                     return current_widget.app
            else:
                current_widget = current_widget.parentWidget() if hasattr(current_widget, 'parentWidget') else None
        log.warning("Could not automatically determine app instance for CategoryManagementDialog.")
        return None

    def _get_template_manager(self):
        if self.app and hasattr(self.app, 'template_manager'):
            return self.app.template_manager
        log.warning("Could not get template_manager from app instance.")
        # Avoid creating a new one here as it might not be configured
        return None
        
    def _init_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background-color: {colors['bg']}; color: {colors['text']}; }}
            QLabel {{ background-color: transparent; border: none; }}
            QListWidget {{ 
                background-color: {colors['card_bg']}; 
                color: {colors['text']}; 
                border: 1px solid {colors['border']};
                border-radius: 3px; padding: 5px;
            }}
            QListWidget::item {{ padding: 6px; border-radius: 3px; }}
            QListWidget::item:selected {{ background-color: {colors['highlight_bg']}; color: {colors['highlight_text']}; }}
            QListWidget::item:hover {{ background-color: {colors['hover_bg']}; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {colors['border']}; border-radius: 3px; background-color: {colors['card_bg']}; }}
            QCheckBox::indicator:checked {{ background-color: {colors['accent']}; border-color: {colors['accent']}; }}
            QCheckBox::indicator:hover {{ border-color: {colors['highlight_border']}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("Template Categories")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {colors['text']};")
        layout.addWidget(title)
        
        description = QLabel("Add, edit, or remove custom template categories. Default categories cannot be modified directly but can be hidden.")
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {colors['secondary_text']};")
        layout.addWidget(description)
        
        self.hide_defaults_checkbox = QCheckBox("Hide Default Categories")
        self.hide_defaults_checkbox.stateChanged.connect(self._toggle_default_categories_visibility)
        self.hide_defaults_checkbox.stateChanged.connect(self._track_hide_defaults_change)
        layout.addWidget(self.hide_defaults_checkbox)
        
        self.category_list = QListWidget()
        self.category_list.setAlternatingRowColors(True) # Improves readability
        layout.addWidget(self.category_list)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Category")
        self.add_button.setStyleSheet(BUTTON_STYLE)
        self.add_button.clicked.connect(self._add_category)
        button_layout.addWidget(self.add_button)
        
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.setStyleSheet(BUTTON_STYLE)
        self.remove_button.clicked.connect(self._remove_category)
        button_layout.addWidget(self.remove_button)
        
        layout.addLayout(button_layout)
        
        # Dialog buttons
        dialog_button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save and Close")
        self.save_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.save_button.clicked.connect(self.accept)
        dialog_button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(BUTTON_STYLE)
        self.cancel_button.clicked.connect(self.reject)
        dialog_button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(dialog_button_layout)

    def _reload_category_list(self):
        self.category_list.clear()
        
        # Separate into default and custom for display logic
        default_display_categories = []
        custom_display_categories = []

        for category in sorted(list(set(self.current_categories))): # Use current_categories being edited
            if category in DEFAULT_TEMPLATE_CATEGORIES:
                default_display_categories.append(category)
            else:
                custom_display_categories.append(category)

        hide_defaults = self.hide_defaults_checkbox.isChecked()

        if not hide_defaults and default_display_categories:
            default_header = QListWidgetItem("─ Default Categories ─")
            default_header.setFlags(Qt.ItemFlag.NoItemFlags)
            default_header.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            default_header.setForeground(QColor(colors['secondary_text']))
            self.category_list.addItem(default_header)
            for category in default_display_categories:
                item = QListWidgetItem(category)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable) # Default not editable
                self.category_list.addItem(item)
        
        if custom_display_categories:
            if self.category_list.count() > 0: # Add spacer if default were added
                spacer = QListWidgetItem("")
                spacer.setFlags(Qt.ItemFlag.NoItemFlags)
                self.category_list.addItem(spacer)

            custom_header = QListWidgetItem("─ Custom Categories ─")
            custom_header.setFlags(Qt.ItemFlag.NoItemFlags)
            custom_header.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            custom_header.setForeground(QColor(colors['secondary_text']))
            self.category_list.addItem(custom_header)
            for category in custom_display_categories:
                self.category_list.addItem(QListWidgetItem(category))
        
        if self.category_list.count() == 0:
            self.category_list.addItem(QListWidgetItem("No categories to display.")) 

    def _add_category(self):
        text, ok = QInputDialog.getText(self, "Add Category", "Enter category name:")
        if ok and text:
            text = text.strip()
            if not text:
                QMessageBox.warning(self, "Invalid Name", "Category name cannot be empty.")
                return
            if text in self.current_categories:
                QMessageBox.warning(self, "Duplicate Category", f"The category '{text}' already exists.")
                return
            if text in DEFAULT_TEMPLATE_CATEGORIES:
                QMessageBox.information(self, "Default Category", 
                                        f"'{text}' is a default category and cannot be added as a custom category. It can be shown or hidden using the checkbox.")
                return
            self.current_categories.append(text)
            self._reload_category_list()
            # Select the newly added item
            for i in range(self.category_list.count()):
                if self.category_list.item(i).text() == text:
                    self.category_list.setCurrentRow(i)
                    break

    def _remove_category(self):
        selected_item = self.category_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "No Selection", "Please select a category to remove.")
            return
        
        category_name = selected_item.text()
        if category_name in DEFAULT_TEMPLATE_CATEGORIES:
            QMessageBox.information(self, "Cannot Remove", f"'{category_name}' is a default category and cannot be removed. You can hide default categories using the checkbox.")
            return
        
        reply = QMessageBox.question(self, "Confirm Removal", 
                                     f"Are you sure you want to remove the category '{category_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if category_name in self.current_categories:
                self.current_categories.remove(category_name)
            self._reload_category_list()

    def _save_categories_to_source(self):
        if not self.template_manager:
            log.error("Cannot save categories: TemplateManager is not available.")
            QMessageBox.critical(self, "Error", "Failed to save categories: Template manager not found.")
            return False
        
        # The project_type_manager is typically the source of truth for categories
        if hasattr(self.template_manager, 'project_type_manager') and \
           hasattr(self.template_manager.project_type_manager, 'save_custom_project_types'):
            
            # We need to distinguish between what project_type_manager considers "project types"
            # and the broader list of "categories" this dialog manages.
            # For now, assume all non-default categories are "custom project types".
            custom_categories_to_save = [cat for cat in self.current_categories if cat not in DEFAULT_TEMPLATE_CATEGORIES]
            
            # The project_type_manager might have its own internal list of defaults.
            # We need to be careful not to overwrite those if they are not part of DEFAULT_TEMPLATE_CATEGORIES.
            # Best approach: get existing custom types, merge, then save.
            
            # This part needs careful implementation based on how ProjectTypeManager truly works.
            # For this refactor, we'll simplify: save the custom ones we have.
            # A more robust solution would involve TemplateManager providing a dedicated
            # `save_categories(all_categories)` method.
            
            # At this point, 'updated_custom_types' is a list of strings for custom categories,
            # and 'default_categories_to_keep' is a list of strings for default categories.
            # The ProjectTypeManager expects a dictionary for custom_project_types.
            # We need to reconstruct this dictionary. For simplicity, we'll assign a default
            # structure or an empty dict if no structure is known.
            
            final_custom_types_dict = {}
            for cat_name in custom_categories_to_save:
                # Try to preserve existing structure if this category was already custom
                existing_custom_data = self.template_manager.project_type_manager.custom_project_types.get(cat_name)
                if existing_custom_data:
                    final_custom_types_dict[cat_name] = existing_custom_data
                else:
                    # New custom category, add with default empty structure or marker
                    final_custom_types_dict[cat_name] = {"structure_name": None, "icon": "🆕"}

            # Update the project_type_manager's internal dictionary
            self.template_manager.project_type_manager.custom_project_types = final_custom_types_dict
            
            # Now save the (modified) custom project types stored within the manager
            success = self.template_manager.project_type_manager.save_custom_project_types()

            if success:
                log.info(f"Successfully saved {len(final_custom_types_dict)} custom categories.")
                return True
            else:
                log.error("Failed to save categories via project_type_manager.")
                QMessageBox.critical(self, "Save Error", "Could not save category changes to project types.")
                return False
        else:
            log.error("TemplateManager or ProjectTypeManager lacks capability to save custom types/categories.")
            QMessageBox.critical(self, "Configuration Error", "Application is not configured to save category changes.")
            return False

    def _load_hide_defaults_setting(self):
        hide = self.settings.value("category_manager/hide_defaults", False, type=bool)
        self.hide_defaults_checkbox.setChecked(hide)
        self.hide_defaults_initial_state = hide # Update initial state after loading

    def _save_hide_defaults_setting(self):
        self.settings.setValue("category_manager/hide_defaults", self.hide_defaults_checkbox.isChecked())

    def _toggle_default_categories_visibility(self):
        self._reload_category_list()
        self._save_hide_defaults_setting() # Save immediately on change

    def _track_hide_defaults_change(self, state):
        if state != self.hide_defaults_initial_state:
            self.hide_defaults_setting_changed_during_session = True

    def accept(self):
        log.debug("Accept called on CategoryManagementDialog")
        saved_ok = self._save_categories_to_source()
        if saved_ok:
            log.info(f"Categories saved. Notifying manager with: {self.current_categories}")
            # Notify the central manager that categories might have changed.
            # It will then fetch the definitive list from the source.
            if self.category_update_manager:
                self.category_update_manager.notify_categories_changed(self.current_categories) # Pass the working list
            super().accept()
        # If save failed, the dialog remains open due to error messages shown in _save_categories_to_source

    def reject(self):
        log.debug("Reject called on CategoryManagementDialog")
        # If hide defaults was changed, but dialog is cancelled, revert the setting
        if self.hide_defaults_setting_changed_during_session and \
           self.hide_defaults_checkbox.isChecked() != self.hide_defaults_initial_state:
            self.settings.setValue("category_manager/hide_defaults", self.hide_defaults_initial_state)
            log.info(f"Reverted 'hide_defaults' setting to initial state: {self.hide_defaults_initial_state}")
            # If this change needs to trigger UI updates elsewhere immediately, it would require a notify.
            # However, for a cancel operation, usually no widespread notification is desired.
        super().reject()

# Global function to launch the dialog (if needed from menus etc.)
def manage_categories_dialog(parent=None):
    dialog = CategoryManagementDialog(parent)
    return dialog.exec()
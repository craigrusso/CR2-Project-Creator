#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Category Management Dialog

This module provides a dialog for managing template categories.
It interacts with the central CategoryUpdateManager to propagate changes.
"""
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton,
    QHBoxLayout, QLineEdit, QMessageBox, QListWidgetItem, 
    QCheckBox, QInputDialog, QWidget, QApplication
)
from PyQt6.QtCore import Qt, QSettings, QTimer, QObject, pyqtSignal
from PyQt6.QtGui import QColor

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE
# from app.templates.category_update_manager import get_instance as get_category_update_manager_instance # Moved into __init__
from app.constants import DEFAULT_TEMPLATE_CATEGORIES

# Define a user role for the divider item
DIVIDER_ROLE = Qt.ItemDataRole.UserRole + 1

log = logging.getLogger("app.dialogs.category_management_dialog")

class RenameDialog(QDialog):
    """Custom dialog for renaming categories with consistent styling"""
    
    def __init__(self, parent=None, category_name="", title="Rename Category"):
        super().__init__(parent)
        
        # Set window properties
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(350, 180)
        
        # Import here to avoid circular imports
        from app.ui.color_scheme_pyqt import colors, ACCENT_BUTTON_STYLE, BUTTON_STYLE
        
        # Set dialog styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg']};
                color: {colors['text']};
            }}
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title label
        title_label = QLabel("Enter new category name:")
        title_label.setStyleSheet(f"""
            font-size: 14px;
            color: {colors['text']};
            background-color: transparent;
            border: none;
        """)
        layout.addWidget(title_label)
        
        # Text input
        self.text_input = QLineEdit(category_name)
        self.text_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 8px;
                selection-background-color: {colors['highlight_bg']};
                selection-color: {colors['highlight_text']};
            }}
            QLineEdit:focus {{
                border: 1px solid {colors['accent']};
            }}
        """)
        self.text_input.selectAll()
        layout.addWidget(self.text_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(BUTTON_STYLE)
        self.cancel_button.clicked.connect(self.reject)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # Connect Enter key to accept
        self.text_input.returnPressed.connect(self.accept)
        
    def get_text(self):
        """Get the entered text"""
        return self.text_input.text().strip()
        
    @staticmethod
    def get_name(parent=None, title="Rename Category", label="Enter new name:", text=""):
        """Static method to create the dialog and return the entered text"""
        dialog = RenameDialog(parent, text, title)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            return dialog.get_text(), True
        return "", False

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
        # Direct parent check
        if parent and hasattr(parent, 'app'):
            log.debug(f"Found app directly on parent widget")
            return parent.app
            
        # Check parent's editor attribute (structure editor case)
        if parent and hasattr(parent, 'editor'):
            if hasattr(parent.editor, 'app'):
                log.debug(f"Found app via parent.editor.app")
                return parent.editor.app
        
        # Check parent's template_manager (for structure editor case)
        if parent and hasattr(parent, 'template_manager'):
            log.debug(f"Parent has template_manager but no direct app reference")
            # We'll handle this in _get_template_manager instead
            pass
            
        # Walk up the widget hierarchy
        current_widget = parent
        while current_widget:
            if hasattr(current_widget, 'app_instance') and current_widget.app_instance:
                log.debug(f"Found app_instance via widget hierarchy")
                return current_widget.app_instance
                
            if hasattr(current_widget, 'app') and current_widget.app:
                log.debug(f"Found app via widget hierarchy")
                return current_widget.app
                
            # Special case for structure editor
            if hasattr(current_widget, 'editor') and hasattr(current_widget.editor, 'app'):
                log.debug(f"Found app via editor in widget hierarchy")
                return current_widget.editor.app
                
            # Special case for UIBuilder
            if hasattr(current_widget, 'ui_builder') and hasattr(current_widget.ui_builder, 'editor') and hasattr(current_widget.ui_builder.editor, 'app'):
                log.debug(f"Found app via ui_builder.editor in widget hierarchy")
                return current_widget.ui_builder.editor.app
                
            if isinstance(current_widget, QDialog) and hasattr(current_widget, 'parent') and callable(current_widget.parent):
                current_widget = current_widget.parent()
                if current_widget and hasattr(current_widget, 'app'):
                    log.debug(f"Found app via parent() method")
                    return current_widget.app
            else:
                current_widget = current_widget.parentWidget() if hasattr(current_widget, 'parentWidget') else None
                
        # Try to get QApplication instance as last resort
        try:
            from PyQt6.QtWidgets import QApplication
            app_instance = QApplication.instance()
            if app_instance and hasattr(app_instance, 'template_manager'):
                log.debug(f"Found app via QApplication.instance()")
                return app_instance
        except:
            pass
                
        log.warning("Could not automatically determine app instance for CategoryManagementDialog.")
        return None

    def _get_template_manager(self):
        # First check if app has template_manager
        if self.app and hasattr(self.app, 'template_manager'):
            log.debug(f"Found template_manager via app")
            return self.app.template_manager
            
        # Check parent directly if available
        parent = self.parent()
        if parent:
            # Direct template_manager on parent (structure editor case)
            if hasattr(parent, 'template_manager'):
                log.debug(f"Found template_manager directly on parent")
                return parent.template_manager
                
            # Check editor attribute (common in structure editor)
            if hasattr(parent, 'editor'):
                if hasattr(parent.editor, 'template_manager'):
                    log.debug(f"Found template_manager via parent.editor")
                    return parent.editor.template_manager
                if hasattr(parent.editor, 'app') and hasattr(parent.editor.app, 'template_manager'):
                    log.debug(f"Found template_manager via parent.editor.app")
                    return parent.editor.app.template_manager
                    
            # Check for UIBuilder (structure editor case)
            if hasattr(parent, 'ui_builder'):
                if hasattr(parent.ui_builder, 'template_manager'):
                    log.debug(f"Found template_manager via parent.ui_builder")
                    return parent.ui_builder.template_manager
        
        # Try to get QApplication instance as last resort
        try:
            from PyQt6.QtWidgets import QApplication
            app_instance = QApplication.instance()
            if app_instance and hasattr(app_instance, 'template_manager'):
                log.debug(f"Found template_manager via QApplication.instance()")
                return app_instance.template_manager
        except:
            pass
            
        log.warning("Could not get template_manager from app instance or any parent widget.")
        
        # Last resort - create a new instance if we have direct import
        try:
            from app.templates.template_manager import TemplateManager
            log.warning("Creating new TemplateManager instance - this is a fallback and may not have full context!")
            return TemplateManager()
        except ImportError:
            log.error("Could not import TemplateManager for fallback instance")
            
        return None
        
    def _init_ui(self):
        """Initialize the UI components"""
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QCheckBox, QPushButton, QLineEdit, QMessageBox, QDialog
        from PyQt6.QtCore import Qt
        from app.ui.color_scheme_pyqt import colors, ACCENT_BUTTON_STYLE, BUTTON_STYLE
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Set overall dialog styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg']};
                color: {colors['text']};
            }}
        """)
        
        # Header with title and description
        header = QLabel("Manage Template Categories")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 10px 0px;
        """)
        main_layout.addWidget(header)
        
        description = QLabel("Add, remove, and organize categories for your templates.")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet(f"""
            color: {colors['secondary_text']};
            background-color: transparent;
            border: none;
            padding: 0px 0px 10px 0px;
            font-size: 13px;
        """)
        main_layout.addWidget(description)
        
        # Checkbox for hiding default categories
        self.hide_defaults_checkbox = QCheckBox("Hide default categories in dropdowns")
        self.hide_defaults_checkbox.setChecked(self.hide_defaults_initial_state)
        self.hide_defaults_checkbox.stateChanged.connect(self._toggle_default_categories_visibility)
        self.hide_defaults_checkbox.stateChanged.connect(self._track_hide_defaults_change)
        self.hide_defaults_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {colors['text']};
                background-color: transparent;
                border: none;
                padding: 5px 0px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {colors['border']};
                border-radius: 3px;
                background-color: {colors['card_bg']};
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {colors['accent']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors['accent']};
                border: 1px solid {colors['accent']};
                image: url("app/assets/css/check.svg");
            }}
        """)
        main_layout.addWidget(self.hide_defaults_checkbox)
        
        # Category list
        self.category_list = QListWidget()
        self.category_list.setSelectionMode(self.category_list.SelectionMode.SingleSelection)
        self.category_list.setMinimumHeight(150)
        # Style the list widget
        self.category_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
            }}
            QListWidget::item {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                padding: 5px;
                margin: 2px 0px;
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: {colors['highlight_bg']};
                color: {colors['highlight_text']};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {colors['hover_bg']};
            }}
        """)
        main_layout.addWidget(self.category_list)
        
        # Add new category section
        add_layout = QHBoxLayout()
        add_layout.setContentsMargins(0, 5, 0, 5)
        add_layout.setSpacing(10)
        
        self.new_category_edit = QLineEdit()
        self.new_category_edit.setPlaceholderText("New category name...")
        # Style the line edit
        self.new_category_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
            }}
            QLineEdit:focus {{
                border: 1px solid {colors['accent']};
            }}
        """)
        # Connect Enter key to add category
        self.new_category_edit.returnPressed.connect(self._add_category)
        add_layout.addWidget(self.new_category_edit, 1)  # 1 = stretch factor
        
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self._add_category)
        # Style the add button using ACCENT_BUTTON_STYLE
        self.add_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        add_layout.addWidget(self.add_button)
        
        main_layout.addLayout(add_layout)
        
        # Buttons for editing categories
        edit_layout = QHBoxLayout()
        edit_layout.setContentsMargins(0, 5, 0, 10)
        edit_layout.setSpacing(10)
        
        self.rename_button = QPushButton("Rename")
        self.rename_button.clicked.connect(self._rename_category)
        # Style the rename button
        self.rename_button.setStyleSheet(BUTTON_STYLE)
        edit_layout.addWidget(self.rename_button)
        
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._remove_category)
        # Style the remove button
        self.remove_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #902A2A;
                color: white;
                border: 1px solid #732121;
                border-radius: 3px;
                padding: 5px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #A33030;
                border: 1px solid #8A2727;
            }}
            QPushButton:pressed {{
                background-color: #7D2525;
            }}
        """)
        edit_layout.addWidget(self.remove_button)
        
        main_layout.addLayout(edit_layout)
        
        # Save and Cancel buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        # Style the cancel button
        self.cancel_button.setStyleSheet(BUTTON_STYLE)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch(1)  # Add stretch to push buttons to opposite sides
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._save_categories)
        # Style the save button
        self.save_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        button_layout.addWidget(self.save_button)
        
        main_layout.addLayout(button_layout)
        
        # Set default button (responds to Enter key)
        self.save_button.setDefault(True)

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
        """Add a new category from the input field"""
        text = self.new_category_edit.text().strip()
        
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
        
        # Clear the input field after successful addition
        self.new_category_edit.clear()
        
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

    def _save_categories_to_source(self, categories):
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
            custom_categories_to_save = [cat for cat in categories if cat not in DEFAULT_TEMPLATE_CATEGORIES]
            
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

    def _save_categories(self):
        """Save categories to the project type manager"""
        try:
            # Get categories from the list
            categories = [self.category_list.item(i).text() for i in range(self.category_list.count())]
            
            # Save to project type manager
            success = self._save_categories_to_source(categories)
            
            if success:
                log.debug(f"Successfully saved {len(categories)} categories")
                
                # Notify that categories have changed so all dropdowns can update
                if self.category_update_manager:
                    log.debug("Notifying category update manager that categories have changed")
                    self.category_update_manager.notify_categories_changed(categories)
                
                # Accept the dialog (will close it)
                self.accept()
            else:
                log.error("Failed to save categories")
                QMessageBox.warning(self, "Save Error", "Failed to save categories. Please try again.")
        except Exception as e:
            log.exception(f"Error saving categories: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while saving categories: {str(e)}")
            # Don't close the dialog on error

    def accept(self):
        log.debug("Accept called on CategoryManagementDialog")
        saved_ok = self._save_categories_to_source(self.current_categories)
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

    def _rename_category(self):
        """Rename the selected category"""
        # Get the selected category
        selected_items = self.category_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a category to rename.")
            return
            
        selected_item = selected_items[0]
        old_name = selected_item.text()
        
        # Check if this is a default category
        if old_name in DEFAULT_TEMPLATE_CATEGORIES:
            QMessageBox.warning(self, "Cannot Rename", f"Cannot rename default category '{old_name}'.")
            return
        
        # Use our custom rename dialog instead of QInputDialog
        new_name, ok = RenameDialog.get_name(
            parent=self,
            title="Rename Category",
            text=old_name
        )
        
        if ok and new_name and new_name != old_name:
            # Check for duplicates
            for i in range(self.category_list.count()):
                if self.category_list.item(i).text() == new_name:
                    QMessageBox.warning(self, "Duplicate Name", f"Category '{new_name}' already exists.")
                    return
            
            # Update the item text
            selected_item.setText(new_name)
            
            # Update in our local list
            index = self.current_categories.index(old_name)
            self.current_categories[index] = new_name
            
            log.debug(f"Renamed category '{old_name}' to '{new_name}'")
            
        # Indicate that we need to save
        self.setWindowModified(True)

def manage_categories_dialog(parent=None):
    """
    Show the category management dialog
    
    Args:
        parent: The parent widget
        
    Returns:
        bool: True if the dialog was accepted, False otherwise
    """
    try:
        # Create the dialog
        dialog = CategoryManagementDialog(parent)
        
        # Pass template_manager directly if parent has it
        if parent and hasattr(parent, 'template_manager'):
            dialog.template_manager = parent.template_manager
        
        # Show the dialog
        result = dialog.exec()
        
        # Return whether the dialog was accepted
        return result == QDialog.DialogCode.Accepted
    except Exception as e:
        log.exception(f"Error showing category management dialog: {e}")
        if parent:
            QMessageBox.critical(parent, "Error", f"An error occurred while showing the category management dialog: {str(e)}")
        return False
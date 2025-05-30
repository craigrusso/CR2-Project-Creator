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
from app.ui.color_scheme_pyqt import APP_COLORS, colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE

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
        
        # Get the category update manager
        from app.templates.category_update_manager import get_instance
        self.category_update_manager = get_instance(self.app)
        
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
        # Apply dialog styling to match app theme
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
        
        # Add title
        title = QLabel("Template Categories")
        title.setStyleSheet(f"""
            font-size: 16px; 
            font-weight: bold;
            color: {colors['text']};
            background-color: transparent;
            border: none;
        """)
        layout.addWidget(title)
        
        # Add description
        description = QLabel("Add, edit, or remove template categories.")
        description.setWordWrap(True)
        description.setStyleSheet(f"""
            color: {colors['secondary_text']};
            background-color: transparent;
            border: none;
        """)
        layout.addWidget(description)
        
        # Add checkbox to hide default categories
        self.hide_defaults_checkbox = QCheckBox("Hide Default Categories")
        self.hide_defaults_checkbox.stateChanged.connect(self._toggle_default_categories_visibility)
        self.hide_defaults_checkbox.stateChanged.connect(self._save_hide_defaults_setting)
        self.hide_defaults_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {colors['text']};
                background-color: transparent;
                spacing: 5px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {colors['border']};
                border-radius: 3px;
                background-color: {colors['card_bg']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors['accent']};
                border-color: {colors['accent']};
            }}
            QCheckBox::indicator:hover {{
                border-color: {colors['highlight_border']};
            }}
        """)
        layout.addWidget(self.hide_defaults_checkbox)
        
        # Add list of categories
        self.category_list = QListWidget()
        self.category_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 5px;
                border-radius: 2px;
            }}
            QListWidget::item:selected {{
                background-color: {colors['highlight_bg']};
                color: {colors['highlight_text']};
            }}
            QListWidget::item:hover {{
                background-color: {colors['hover_bg']};
            }}
        """)
        
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
        self.new_category_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
                min-height: 25px;
            }}
            QLineEdit:focus {{
                border: 1px solid {colors['accent']};
            }}
        """)
        
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self._add_category)
        self.add_btn.setStyleSheet(BUTTON_STYLE)
        
        input_layout.addWidget(self.new_category_input, 3)
        input_layout.addWidget(self.add_btn, 1)
        layout.addLayout(input_layout)
        
        # Add button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self._remove_category)
        self.remove_btn.setStyleSheet(BUTTON_STYLE)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setObjectName("closeButtonAccent") # Set object name for styling
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
            
            # Add item to the correct location - after default categories but before the divider
            # or at the end if no divider exists
            divider_index = -1
            for i in range(self.category_list.count()):
                if self.category_list.item(i).data(DIVIDER_ROLE):
                    divider_index = i
                    break
            
            if divider_index >= 0:
                # Add after the divider
                self.category_list.insertItem(divider_index + 1, item)
            else:
                # No divider, add to the end
                self.category_list.addItem(item)
                
            self.category_list.setCurrentItem(item)
            
            # Clear the input field after successful addition
            self.new_category_input.clear()

            # Update the internal result categories
            self._update_result()
            
            # Save the category using the project_type_manager
            if self.template_manager and hasattr(self.template_manager, 'project_type_manager'):
                # Choose an appropriate default structure based on category name
                default_structure = "Video Editing - Standard"  # Default fallback
                
                # Map to appropriate structures based on category name
                category_lower = category_name.lower()
                if "video" in category_lower:
                    default_structure = "Video Editing - Standard"
                elif "motion" in category_lower or "graphics" in category_lower:
                    default_structure = "Motion Graphics - Standard"
                elif "vfx" in category_lower or "visual effects" in category_lower:
                    default_structure = "VFX - Standard"
                elif "audio" in category_lower or "sound" in category_lower:
                    default_structure = "Video Editing - Standard"  # No specific audio structure yet
                
                # Save the new category to the project_type_manager
                success = self.template_manager.project_type_manager.create_project_type(category_name, default_structure)
                if success:
                    print(f"DEBUG (CategoryManager): Successfully added category '{category_name}' to project_type_manager")
                    # Make sure our categories list is updated
                    if category_name not in self.categories:
                        self.categories.append(category_name)
                else:
                    print(f"DEBUG (CategoryManager): Failed to add category '{category_name}' to project_type_manager")
            
            # Force reload the list to ensure correct ordering and display
            self._reload_category_list()
            
            # Notify CategoryUpdateManager about the category change
            if hasattr(self, 'category_update_manager'):
                self.category_update_manager.notify_categories_changed(self.result_categories)
                print(f"DEBUG (CategoryManager): Notified CategoryUpdateManager about adding category '{category_name}'")
            
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
                # self._update_ui_dropdowns() # REMOVED - Redundant due to notify_categories_changed later
            else:
                print(f"Failed to delete project type '{category_name}' via manager (might be a default or already removed)")
        else:
            print("Project type manager not found, cannot delete from backend.")
            # If no manager, just update internal lists
            if category_name in self.categories:
                 self.categories.remove(category_name)
            self._update_result()
        
        # Reload the list to reflect the changes (including divider removal if needed)
        self._reload_category_list()
        
        # Notify CategoryUpdateManager about the category change
        if hasattr(self, 'category_update_manager'):
            self.category_update_manager.notify_categories_changed(self.result_categories)
            print(f"DEBUG (CategoryManager): Notified CategoryUpdateManager about removing category '{category_name}'")
            
        # Process events to ensure UI updates
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        
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
            
        # Get the latest categories from the template manager to ensure we have the most recent list
        if hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'get_categories'):
            # Force reload categories from project_type_manager first to ensure we have fresh data
            if hasattr(self.app.template_manager, 'project_type_manager'):
                self.app.template_manager.project_type_manager.load_custom_project_types()
            
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
        from PyQt6.QtWidgets import QComboBox, QWidget, QDialog, QApplication
        from PyQt6.QtCore import Qt
        
        # Find all relevant comboboxes in the application
        # Search for named comboboxes first
        project_type_combos = self.app.findChildren(QComboBox, "project_type_combo_box")
        template_category_combos = self.app.findChildren(QComboBox, "template_category_combo_box")
        
        # Additionally, find template editor comboboxes that might be in dialogs
        # Try to find open dialogs that might have category comboboxes
        open_dialogs = [w for w in QApplication.topLevelWidgets() if isinstance(w, QDialog)]
        additional_combos = []
        
        for dialog in open_dialogs:
            # Find category comboboxes in dialogs
            dialog_combos = dialog.findChildren(QComboBox)
            for combo in dialog_combos:
                # Check if this looks like a category combobox based on object name or parent widget name
                if (combo.objectName() and ("category" in combo.objectName().lower() or 
                                           "type" in combo.objectName().lower())):
                    additional_combos.append(combo)
                    print(f"Found additional combobox in dialog: {combo.objectName()}")
        
        # Combine the lists
        all_target_combos = project_type_combos + template_category_combos + additional_combos
        updated_widgets = 0
        
        print(f"Found {len(project_type_combos)} widgets with name 'project_type_combo_box'.")
        print(f"Found {len(template_category_combos)} widgets with name 'template_category_combo_box'.")
        print(f"Found {len(additional_combos)} additional comboboxes in dialogs.")
        print(f"Total target dropdowns: {len(all_target_combos)}")
        
        for combo_box in all_target_combos:
            if not combo_box:
                continue
                
            # Remember current selection
            current_text = combo_box.currentText()
            print(f"Updating dropdown: {combo_box.objectName()}, current selection: {current_text}")
            
            # Block signals during update
            combo_box.blockSignals(True)
            
            # Clear the combobox
            combo_box.clear()
            
            # Simple approach - just add all categories directly
            if not hide_defaults:
                # Separate into default and custom
                from app.constants import DEFAULT_TEMPLATE_CATEGORIES
                default_cats = [cat for cat in all_categories if cat in DEFAULT_TEMPLATE_CATEGORIES]
                custom_cats = [cat for cat in all_categories if cat not in DEFAULT_TEMPLATE_CATEGORIES]
                
                # Add default categories section if we have any
                if default_cats:
                    # Add the header item
                    header_index = combo_box.count()
                    combo_box.addItem("Default Categories")
                    combo_box.setItemData(header_index, False, Qt.ItemDataRole.UserRole)
                    combo_box.setItemData(header_index, QColor(colors['secondary_text']), Qt.ItemDataRole.ForegroundRole)
                    
                    # Explicitly make the header non-selectable by setting its flags
                    model = combo_box.model()
                    if model:
                        item = model.item(header_index)
                        if item:
                            item.setFlags(Qt.ItemFlag.NoItemFlags)
                    
                    # Add default categories
                    for cat in sorted(default_cats):
                        combo_box.addItem(cat)
                
                # Add custom categories section if we have any
                if custom_cats:
                    # Add separator if we have default categories
                    if default_cats:
                        combo_box.insertSeparator(combo_box.count())
                    
                    # Add the header item
                    header_index = combo_box.count()
                    combo_box.addItem("Custom Categories")
                    combo_box.setItemData(header_index, False, Qt.ItemDataRole.UserRole)
                    combo_box.setItemData(header_index, QColor(colors['secondary_text']), Qt.ItemDataRole.ForegroundRole)
                    
                    # Explicitly make the header non-selectable by setting its flags
                    model = combo_box.model()
                    if model:
                        item = model.item(header_index)
                        if item:
                            item.setFlags(Qt.ItemFlag.NoItemFlags)
                    
                    # Add custom categories
                    for cat in sorted(custom_cats):
                        combo_box.addItem(cat)
            else:
                # Simple flat list of categories when hiding defaults
                for cat in sorted(categories_to_show):
                    combo_box.addItem(cat)
            
            # Try to restore selection or select first selectable item
            index = combo_box.findText(current_text)
            if index != -1 and combo_box.itemData(index, Qt.ItemDataRole.UserRole) != False:
                combo_box.setCurrentIndex(index)
            else:
                # Find first selectable item
                for i in range(combo_box.count()):
                    if combo_box.itemData(i, Qt.ItemDataRole.UserRole) != False:
                        combo_box.setCurrentIndex(i)
                        break
            
            # Enable if we have items
            combo_box.setEnabled(combo_box.count() > 0)
            
            # Re-enable signals
            combo_box.blockSignals(False)
            
            updated_widgets += 1
            print(f"Dropdown {combo_box.objectName()} updated with {combo_box.count()} items.")
        
        print(f"CategoryManager: Finished updating {updated_widgets} dropdown widgets.")
        
        # Force UI refresh
        QApplication.processEvents()
        
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
        """Save the hide default categories setting"""
        state = self.hide_defaults_checkbox.isChecked()
        self.settings.setValue("CategoryManager/hideDefaultCategories", state)
        print(f"Saved hideDefaultCategories setting: {state}")
        # Immediately trigger dropdown updates when the setting changes
        # self._update_ui_dropdowns() # REMOVED - Setting change should not force app-wide UI update directly

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
        
        # Ensure categories are saved
        self._update_result()
        
        # Instead of just calling _save_to_category_manager, make sure any
        # missing categories are explicitly created in the project_type_manager
        if self.template_manager and hasattr(self.template_manager, 'project_type_manager'):
            existing_types = self.template_manager.project_type_manager.get_all_project_types()
            
            # Add any missing categories
            for category in self.result_categories:
                if category not in existing_types:
                    # Choose an appropriate default structure
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
                    
                    # Save the category to project_type_manager
                    success = self.template_manager.project_type_manager.create_project_type(category, default_structure)
                    print(f"Adding missing category '{category}' with structure '{default_structure}': {'Success' if success else 'Failed'}")
        
        # Notify the category update manager that categories have changed
        if hasattr(self, 'category_update_manager'):
            self.category_update_manager.notify_categories_changed(self.result_categories)
            print("Category Manager: Notified CategoryUpdateManager of category changes")
        
        # Directly find and update all template forms that are currently open
        # self._directly_update_template_forms() # REMOVED
        
        # Update all UI dropdowns before closing - for backwards compatibility
        # self._update_ui_dropdowns() # REMOVED
        
        # More comprehensive update of all possible category dropdowns - for backwards compatibility
        # self._update_all_category_combos() # REMOVED
        
        # Force immediate UI refresh before closing
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Call super's accept method directly - don't use a timer/lambda which loses 'self' context
        super().accept()

    def _update_all_category_combos(self):
        """Update all combo boxes in the application that might contain categories"""
        from PyQt6.QtWidgets import QComboBox, QApplication
        
        # Get all widgets in the application
        all_widgets = QApplication.allWidgets()
        
        # Get all categories
        all_categories = []
        if self.template_manager and hasattr(self.template_manager, 'get_categories'):
            # Force reload categories first
            if hasattr(self.template_manager, 'project_type_manager'):
                self.template_manager.project_type_manager.load_custom_project_types()
            
            all_categories = self.template_manager.get_categories()
            print(f"Updating all combos with {len(all_categories)} categories from template_manager")
        else:
            # Fallback to our internal list
            self._update_result()
            all_categories = self.result_categories
            print(f"Updating all combos with {len(all_categories)} categories from internal list")
        
        # Count how many were updated
        updated_count = 0
        
        # Check each widget
        for widget in all_widgets:
            if isinstance(widget, QComboBox):
                # Skip if this is our own category list widget
                if widget == self.category_list:
                    continue
                    
                # Check if this looks like a category combo box
                name = widget.objectName().lower()
                if "category" in name or "type" in name or name.endswith("combo"):
                    # Remember current selection
                    current_text = widget.currentText()
                    
                    # Block signals during update
                    widget.blockSignals(True)
                    
                    # Check if this combo already has at least one category item
                    has_categories = False
                    for i in range(widget.count()):
                        item_text = widget.itemText(i)
                        if item_text in all_categories:
                            has_categories = True
                            break
                    
                    # If it's empty or contains categories, update it
                    if widget.count() == 0 or has_categories:
                        # Clear and repopulate
                        widget.clear()
                        
                        # Add all categories
                        for category in sorted(all_categories):
                            widget.addItem(category)
                        
                        # Try to restore previous selection or select first item
                        index = widget.findText(current_text)
                        if index != -1:
                            widget.setCurrentIndex(index)
                        elif widget.count() > 0:
                            widget.setCurrentIndex(0)
                        
                        updated_count += 1
                    
                    # Re-enable signals
                    widget.blockSignals(False)
        
        print(f"Updated {updated_count} combo boxes with categories")
        
        # Force UI refresh
        QApplication.processEvents()

    def _directly_update_template_forms(self):
        """Directly find and update all template forms that are currently open"""
        print("Category Manager: Directly updating all open template forms")
        
        # Get the updated categories
        categories = self.result_categories
        print(f"Category Manager: Using {len(categories)} categories for update: {categories}")
        
        # Find all open dialogs that might be template creation forms
        from PyQt6.QtWidgets import QApplication, QDialog, QComboBox
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QColor
        from app.ui.color_scheme_pyqt import colors
        
        # Import necessary modules for formatted dropdowns
        from app.constants import DEFAULT_TEMPLATE_CATEGORIES
        
        # Split categories into default and custom
        default_cats = [cat for cat in categories if cat in DEFAULT_TEMPLATE_CATEGORIES]
        custom_cats = [cat for cat in categories if cat not in DEFAULT_TEMPLATE_CATEGORIES]
        
        # Get all top-level widgets
        all_top_widgets = QApplication.topLevelWidgets()
        updated_forms = 0
        
        for widget in all_top_widgets:
            # Check if it's a dialog and has a title related to templates
            if isinstance(widget, QDialog) and ("template" in widget.windowTitle().lower() or "edit" in widget.windowTitle().lower()):
                print(f"Category Manager: Found template form dialog: {widget.windowTitle()}")
                
                # Try to find the type_combo directly
                type_combos = []
                
                # First, look for combobox with specific object name
                combos = widget.findChildren(QComboBox, "template_category_combo_box")
                if combos:
                    type_combos.extend(combos)
                
                # Also look for any combobox that might contain categories
                all_combos = widget.findChildren(QComboBox)
                for combo in all_combos:
                    # Skip if already added
                    if combo in type_combos:
                        continue
                    
                    # Check if object name suggests it's a category combobox
                    obj_name = combo.objectName().lower()
                    if "category" in obj_name or "type" in obj_name:
                        type_combos.append(combo)
                        continue
                    
                    # Check if current items match any of our categories
                    for i in range(combo.count()):
                        if combo.itemText(i) in categories:
                            type_combos.append(combo)
                            break
                
                # Update all found category comboboxes
                for combo in type_combos:
                    # Check if this dropdown uses the special format with headers
                    has_headers = False
                    for i in range(combo.count()):
                        if combo.itemData(i, Qt.ItemDataRole.UserRole) == False:  # Headers have UserRole=False
                            has_headers = True
                            break
                    
                    # Remember current selection
                    current_selection = combo.currentText()
                    print(f"Category Manager: Updating combobox in {widget.windowTitle()}, current selection: '{current_selection}'")
                    
                    # Block signals during update
                    combo.blockSignals(True)
                    
                    # Use the special formatted update if needed
                    if has_headers:
                        print(f"Category Manager: Using formatted update with headers for {combo.objectName()}")
                        
                        # Clear and rebuild
                        combo.clear()
                        
                        # Add default categories section if we have any
                        if default_cats:
                            # Add the header item
                            header_index = combo.count()
                            combo.addItem("Default Categories")
                            combo.setItemData(header_index, False, Qt.ItemDataRole.UserRole)
                            combo.setItemData(header_index, QColor(colors['secondary_text']), Qt.ItemDataRole.ForegroundRole)
                            
                            # Explicitly make the header non-selectable by setting its flags
                            model = combo.model()
                            if model:
                                item = model.item(header_index)
                                if item:
                                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                            
                            # Add default categories
                            for cat in sorted(default_cats):
                                combo.addItem(cat)
                        
                        # Add custom categories section if we have any
                        if custom_cats:
                            # Add separator if we have default categories
                            if default_cats:
                                combo.insertSeparator(combo.count())
                            
                            # Add the header item
                            header_index = combo.count()
                            combo.addItem("Custom Categories")
                            combo.setItemData(header_index, False, Qt.ItemDataRole.UserRole)
                            combo.setItemData(header_index, QColor(colors['secondary_text']), Qt.ItemDataRole.ForegroundRole)
                            
                            # Explicitly make the header non-selectable by setting its flags
                            model = combo.model()
                            if model:
                                item = model.item(header_index)
                                if item:
                                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                            
                            # Add custom categories
                            for cat in sorted(custom_cats):
                                combo.addItem(cat)
                        
                        # Try to restore selection or select first selectable item
                        index = combo.findText(current_selection)
                        if index != -1 and combo.itemData(index, Qt.ItemDataRole.UserRole) != False:
                            combo.setCurrentIndex(index)
                        else:
                            # Find first selectable item
                            for i in range(combo.count()):
                                if combo.itemData(i, Qt.ItemDataRole.UserRole) != False:
                                    combo.setCurrentIndex(i)
                                    break
                    else:
                        print(f"Category Manager: Using standard update for {combo.objectName()}")
                        
                        # Clear and repopulate
                        combo.clear()
                        
                        # Add categories
                        for category in sorted(categories):
                            combo.addItem(category)
                        
                        # Try to restore selection
                        index = combo.findText(current_selection)
                        if index >= 0:
                            combo.setCurrentIndex(index)
                        elif combo.count() > 0:
                            combo.setCurrentIndex(0)
                    
                    # Re-enable signals
                    combo.blockSignals(False)
                    
                    updated_forms += 1
                    print(f"Category Manager: Updated combobox with {combo.count()} items, current selection: '{combo.currentText()}'")
        
        # Process events to ensure UI updates
        QApplication.processEvents()
        
        print(f"Category Manager: Updated {updated_forms} comboboxes in template forms")

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
        # Get the updated categories
        updated_categories = dialog.get_categories()
        
        # Make sure the CategoryUpdateManager gets notified after the dialog is fully closed
        from app.templates.category_update_manager import get_instance
        
        # Get app instance from parent if available
        app = None
        if parent and hasattr(parent, 'app'):
            app = parent.app
        elif parent and hasattr(parent, 'parent') and callable(parent.parent):
            parent_obj = parent.parent()
            if parent_obj and hasattr(parent_obj, 'app'):
                app = parent_obj.app
        
        # Get category update manager with app instance
        category_manager = get_instance(app)
        
        # Schedule multiple notifications with increasing delays to ensure all UI components are updated
        from PyQt6.QtCore import QTimer
        
        def notify_categories_changed():
            category_manager.notify_categories_changed(updated_categories)
            print(f"Delayed notification: CategoryUpdateManager notified of {len(updated_categories)} categories")
        
        # Directly update any open template forms right after dialog closes
        from PyQt6.QtWidgets import QApplication, QDialog, QComboBox
        
        def directly_update_template_forms():
            """Helper function to update template forms directly"""
            print("manage_categories: Directly updating all template forms after dialog close")
            
            # Find all dialogs that might be template forms
            all_top_widgets = QApplication.topLevelWidgets()
            for widget in all_top_widgets:
                if isinstance(widget, QDialog) and ("template" in widget.windowTitle().lower() or "edit" in widget.windowTitle().lower()):
                    print(f"manage_categories: Found template dialog: {widget.windowTitle()}")
                    
                    # Look for comboboxes that might contain categories
                    category_combos = []
                    
                    # First, look for combobox with specific object name
                    combos = widget.findChildren(QComboBox, "template_category_combo_box")
                    if combos:
                        category_combos.extend(combos)
                    
                    # Also look for other comboboxes by name or content
                    all_combos = widget.findChildren(QComboBox)
                    for combo in all_combos:
                        if combo in category_combos:
                            continue
                            
                        obj_name = combo.objectName().lower()
                        if "category" in obj_name or "type" in obj_name:
                            category_combos.append(combo)
                    
                    # Import necessary modules for formatted dropdowns
                    from app.constants import DEFAULT_TEMPLATE_CATEGORIES
                    from PyQt6.QtGui import QColor
                    from app.ui.color_scheme_pyqt import colors
                    
                    # Split categories into default and custom
                    default_cats = [cat for cat in updated_categories if cat in DEFAULT_TEMPLATE_CATEGORIES]
                    custom_cats = [cat for cat in updated_categories if cat not in DEFAULT_TEMPLATE_CATEGORIES]
                    
                    # Update all found comboboxes
                    for combo in category_combos:
                        current_text = combo.currentText()
                        
                        # Check if this dropdown uses the special format with headers
                        has_headers = False
                        for i in range(combo.count()):
                            if combo.itemData(i, Qt.ItemDataRole.UserRole) == False:  # Headers have UserRole=False
                                has_headers = True
                                break
                        
                        # Block signals during update
                        combo.blockSignals(True)
                        combo.clear()
                        
                        # Use the formatted update for all comboboxes to ensure consistency
                        # Add default categories section if we have any
                        if default_cats:
                            # Add the header item
                            header_index = combo.count()
                            combo.addItem("Default Categories")
                            combo.setItemData(header_index, False, Qt.ItemDataRole.UserRole)
                            combo.setItemData(header_index, QColor(colors['secondary_text']), Qt.ItemDataRole.ForegroundRole)
                            
                            # Explicitly make the header non-selectable by setting its flags
                            model = combo.model()
                            if model:
                                item = model.item(header_index)
                                if item:
                                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                            
                            # Add default categories
                            for cat in sorted(default_cats):
                                combo.addItem(cat)
                        
                        # Add custom categories section if we have any
                        if custom_cats:
                            # Add separator if we have default categories
                            if default_cats:
                                combo.insertSeparator(combo.count())
                            
                            # Add the header item
                            header_index = combo.count()
                            combo.addItem("Custom Categories")
                            combo.setItemData(header_index, False, Qt.ItemDataRole.UserRole)
                            combo.setItemData(header_index, QColor(colors['secondary_text']), Qt.ItemDataRole.ForegroundRole)
                            
                            # Explicitly make the header non-selectable by setting its flags
                            model = combo.model()
                            if model:
                                item = model.item(header_index)
                                if item:
                                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                            
                            # Add custom categories
                            for cat in sorted(custom_cats):
                                combo.addItem(cat)
                        
                        # Try to restore previous selection or select first selectable item
                        index = combo.findText(current_text)
                        if index >= 0 and combo.itemData(index, Qt.ItemDataRole.UserRole) != False:
                            combo.setCurrentIndex(index)
                        else:
                            # Find first selectable item
                            for i in range(combo.count()):
                                if combo.itemData(i, Qt.ItemDataRole.UserRole) != False:
                                    combo.setCurrentIndex(i)
                                    break
                        
                        combo.blockSignals(False)
                        print(f"manage_categories: Updated combobox in {widget.windowTitle()} with {combo.count()} items, current: '{combo.currentText()}'")
            
            # Process events to ensure UI updates
            QApplication.processEvents()
        
        # Run direct update immediately
        directly_update_template_forms()
        
        # Notify immediately
        notify_categories_changed()
        
        # Schedule additional notifications to catch all UI states
        QTimer.singleShot(100, notify_categories_changed)
        QTimer.singleShot(300, notify_categories_changed)
        QTimer.singleShot(500, notify_categories_changed)
        
        # Schedule additional direct updates as well
        QTimer.singleShot(200, directly_update_template_forms)
        QTimer.singleShot(400, directly_update_template_forms)
        
        return updated_categories
    
    # Return None if canceled
    return None 
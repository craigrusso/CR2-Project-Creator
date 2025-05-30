#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Category Update Manager

This module provides centralized management of template categories 
and ensures all UI components are updated when categories change.
"""

import logging
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt
from PyQt6.QtWidgets import QApplication, QComboBox, QDialog
from PyQt6.QtGui import QColor
from app.ui.color_scheme_pyqt import colors

# Singleton instance
_instance = None

class CategoryUpdateManager(QObject):
    """
    Centralized manager for category updates throughout the application.
    
    This class ensures that when categories are added, removed, or changed,
    all relevant UI components are updated properly.
    """
    
    # Signal emitted when categories change
    categories_changed = pyqtSignal(list)
    
    def __init__(self, app=None):
        """Initialize the category update manager"""
        super().__init__()
        self.app = app
        self.debug = True  # Set to False in production
        
        # Connect our signal to our scheduling method
        self.categories_changed.connect(self._schedule_update_all_category_combos)
        
        # The initial update will be triggered from main.py after UI is stable
        # QTimer.singleShot(100, self.force_update_all_category_combos)
    
    def log(self, message):
        """Log messages if debug is enabled"""
        if self.debug:
            print(f"[CategoryUpdateManager] {message}")
            logging.debug(f"[CategoryUpdateManager] {message}")
    
    def set_app(self, app):
        """Set the application instance for this manager"""
        self.app = app
        self.log(f"Application instance set: {app}")
    
    def notify_categories_changed(self, categories=None):
        """
        Notify the system that categories have changed.
        
        Args:
            categories (list, optional): The new categories list. If None,
                                       categories will be retrieved from the template manager.
        """
        self.log("Categories changed notification received")
        
        # If categories weren't provided, try to get them from the template manager
        if categories is None and self.app:
            if hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'get_categories'):
                # Force reload project types first
                if hasattr(self.app.template_manager, 'project_type_manager'):
                    self.app.template_manager.project_type_manager.load_custom_project_types()
                
                categories = self.app.template_manager.get_categories()
                self.log(f"Retrieved {len(categories)} categories from template_manager")
        
        # Emit signal with the categories
        if categories:
            self.log(f"Emitting categories_changed signal with {len(categories)} categories")
            self.categories_changed.emit(categories)
        else:
            self.log("No categories available to emit")
    
    def force_update_all_category_combos(self):
        """Force an update of all category comboboxes in the application"""
        if self.app:
            if hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'get_categories'):
                # Force reload project types first
                if hasattr(self.app.template_manager, 'project_type_manager'):
                    self.app.template_manager.project_type_manager.load_custom_project_types()
                
                categories = self.app.template_manager.get_categories()
                self.log(f"Forced update with {len(categories)} categories from template_manager")
                self.update_all_category_combos(categories)
            else:
                self.log("No template_manager available for forced update")
        else:
            self.log("No app instance set for forced update")
    
    def update_all_category_combos(self, categories):
        """
        Update all category comboboxes in the application with the given categories.
        
        Args:
            categories (list): The list of categories to update comboboxes with.
        """
        if not categories:
            self.log("UPDATE_ALL_COMBOS: No categories provided, skipping update.")
            return
        
        self.log(f"UPDATE_ALL_COMBOS: Starting update with {len(categories)} categories: {categories}")
        
        # Find all combo boxes in the application
        all_widgets = QApplication.allWidgets()
        updated_count = 0
        
        # First pass: update all known category dropdowns by object name
        known_category_names = ["template_category_combo_box", "project_type_combo_box", "category_combo"]
        
        # Track which combos we've updated in the first pass
        updated_combos = set()
        
        # First, focus on known category combos by object name
        for widget in all_widgets:
            if isinstance(widget, QComboBox):
                obj_name = widget.objectName()
                
                # Check if this is a known category combo box by name
                is_known_category_combo = any(name in obj_name.lower() for name in known_category_names)
                
                if is_known_category_combo:
                    self.update_single_combobox(widget, categories)
                    updated_combos.add(widget)
                    updated_count += 1
        
        # Second pass: focus on all comboboxes in dialogs that might be template-related
        for widget in all_widgets:
            if isinstance(widget, QDialog):
                dialog_title = widget.windowTitle().lower()
                if "template" in dialog_title or "category" in dialog_title:
                    self.log(f"UPDATE_ALL_COMBOS: Found relevant dialog: {dialog_title}")
                    
                    # Look for all comboboxes in this dialog
                    for combo_in_dialog in widget.findChildren(QComboBox):
                        if combo_in_dialog not in updated_combos:
                            obj_name_in_dialog = combo_in_dialog.objectName()
                            parent_name_in_dialog = combo_in_dialog.parent().objectName() if combo_in_dialog.parent() else "None"
                            self.log(f"UPDATE_ALL_COMBOS:   Updating QComboBox '{obj_name_in_dialog}' (Parent: '{parent_name_in_dialog}') within dialog '{dialog_title}'")
                            self.update_single_combobox(combo_in_dialog, categories)
                            updated_combos.add(combo_in_dialog)
                            updated_count += 1
        
        # Third pass: look for empty or category-like comboboxes we missed
        for widget in all_widgets:
            if isinstance(widget, QComboBox) and widget not in updated_combos:
                obj_name = widget.objectName().lower()
                
                # Check if this looks like a category combo by name or if it's empty
                if "category" in obj_name or "type" in obj_name or widget.count() == 0:
                    # Check if this combo already contains any of our categories
                    contains_categories = False
                    for i in range(widget.count()):
                        if widget.itemText(i) in categories:
                            contains_categories = True
                            break
                    
                    # Get parent and dialog info for logging
                    parent_name = widget.parent().objectName() if widget.parent() else "None"
                    dialog_title = "None"
                    parent_dialog = widget.parentWidget()
                    while parent_dialog is not None and not isinstance(parent_dialog, QDialog):
                        parent_dialog = parent_dialog.parentWidget()
                    if isinstance(parent_dialog, QDialog):
                        dialog_title = parent_dialog.windowTitle()
                    
                    # Update if it's empty or already contains categories
                    if widget.count() == 0 or contains_categories:
                        self.log(f"UPDATE_ALL_COMBOS: Updating QComboBox '{obj_name}' (Parent: '{parent_name}', Dialog: '{dialog_title}') based on third pass criteria.")
                        self.update_single_combobox(widget, categories)
                        updated_count += 1
        
        self.log(f"UPDATE_ALL_COMBOS: Finished. Updated {updated_count} comboboxes.")
        
        # Process events to ensure UI updates
        QApplication.processEvents()
    
    def update_single_combobox(self, combo, categories):
        """
        Update a single combobox with the given categories.
        
        Args:
            combo (QComboBox): The combobox to update
            categories (list): The list of categories to update with
        """
        if not combo or not categories:
            self.log(f"UPDATE_SINGLE_COMBO: Invalid combo or no categories. Combo: {combo}, Categories: {categories}")
            return
        
        # Get combo properties for logging
        obj_name = combo.objectName()
        parent_name = combo.parent().objectName() if combo.parent() else "None"
        self.log(f"UPDATE_SINGLE_COMBO: Updating '{obj_name}' (Parent: '{parent_name}')")
        
        # Remember current selection and initial item count
        current_text = combo.currentText()
        initial_item_count = combo.count()
        self.log(f"UPDATE_SINGLE_COMBO: '{obj_name}' initial state - Items: {initial_item_count}, Current selection: '{current_text}'")
        
        # Block signals during update
        combo.blockSignals(True)
        
        # Determine if this combobox should always be formatted
        # Check if it's within a QDialog and if the dialog title suggests it's a template form
        parent_dialog = combo.parentWidget()
        while parent_dialog is not None and not isinstance(parent_dialog, QDialog):
            parent_dialog = parent_dialog.parentWidget()
        
        should_force_format = False
        if isinstance(parent_dialog, QDialog):
            dialog_title = parent_dialog.windowTitle().lower()
            if "template" in dialog_title or "edit" in dialog_title or "create" in dialog_title:
                if "category" in obj_name.lower(): # e.g., template_category_combo_box
                    should_force_format = True

        # Check for existing headers or if we should force format
        has_headers = False
        if not should_force_format:
            for i in range(combo.count()):
                # Headers have UserRole set to False (the boolean value)
                if combo.itemData(i, Qt.ItemDataRole.UserRole) is False:
                    has_headers = True
                    break
        
        # If dropdown should be formatted or already has headers, use the formatted update
        if should_force_format or has_headers:
            self.log(f"UPDATE_SINGLE_COMBO: '{obj_name}' using formatted update (Forced: {should_force_format}, Detected Headers: {has_headers})")
            self._update_formatted_combobox(combo, categories, current_text)
        else:
            # Standard update for simple dropdown
            self.log(f"UPDATE_SINGLE_COMBO: '{obj_name}' using standard update for flat dropdown")
            
            # Clear the combobox
            combo.clear()
            
            # Add all categories
            for category in sorted(categories):
                combo.addItem(category)
            
            # Try to restore selection or select first item
            index = combo.findText(current_text)
            if index >= 0:
                combo.setCurrentIndex(index)
                self.log(f"UPDATE_SINGLE_COMBO: '{obj_name}' Restored selection to '{current_text}'")
            elif combo.count() > 0:
                combo.setCurrentIndex(0)
                self.log(f"UPDATE_SINGLE_COMBO: '{obj_name}' Set selection to first item: '{combo.currentText()}'")
        
        # Re-enable signals
        combo.blockSignals(False)
        
        self.log(f"UPDATE_SINGLE_COMBO: '{obj_name}' finished update - Items: {combo.count()}, Final selection: '{combo.currentText()}'")
        
    def _update_formatted_combobox(self, combo, categories, current_text):
        """
        Update a combobox that uses the formatted layout with headers and separators.
        
        Args:
            combo (QComboBox): The combobox to update
            categories (list): The list of categories to update with
            current_text (str): The current selection text to restore
        """
        obj_name = combo.objectName()
        self.log(f"_UPDATE_FORMATTED_COMBO: Updating '{obj_name}' with {len(categories)} categories. Attempting to restore '{current_text}'")

        from PyQt6.QtGui import QColor
        from app.ui.color_scheme_pyqt import colors
        
        # Import default categories
        from app.constants import DEFAULT_TEMPLATE_CATEGORIES
        
        # Split categories into default and custom
        default_cats = [cat for cat in categories if cat in DEFAULT_TEMPLATE_CATEGORIES]
        custom_cats = [cat for cat in categories if cat not in DEFAULT_TEMPLATE_CATEGORIES]
        
        # Remember items to preserve
        old_items = []
        for i in range(combo.count()):
            text = combo.itemText(i)
            data = combo.itemData(i, Qt.ItemDataRole.UserRole)
            foreground = combo.itemData(i, Qt.ItemDataRole.ForegroundRole)
            flags = combo.model().item(i).flags() if combo.model() and combo.model().item(i) else None
            old_items.append((text, data, foreground, flags))
        
        # Now clear and rebuild
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
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable & ~Qt.ItemFlag.ItemIsEnabled)
            
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
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable & ~Qt.ItemFlag.ItemIsEnabled)
            
            # Add custom categories
            for cat in sorted(custom_cats):
                combo.addItem(cat)
        
        # Try to restore selection or select first selectable item
        index = combo.findText(current_text)
        if index != -1:
            # Check if the item at this index is actually selectable
            is_selectable = True
            model = combo.model()
            if model and model.item(index):
                flags = model.item(index).flags()
                if not (flags & Qt.ItemFlag.ItemIsSelectable and flags & Qt.ItemFlag.ItemIsEnabled):
                    is_selectable = False
            
            if is_selectable:
                combo.setCurrentIndex(index)
                self.log(f"_UPDATE_FORMATTED_COMBO: '{obj_name}' - Restored selection to '{current_text}'")
            else:
                self.log(f"_UPDATE_FORMATTED_COMBO: '{obj_name}' - Found '{current_text}' but it's a non-selectable header. Finding first selectable.")
                # Find first selectable item if restored item was a header
                for i in range(combo.count()):
                    is_item_selectable = True
                    if model and model.item(i):
                        flags = model.item(i).flags()
                        if not (flags & Qt.ItemFlag.ItemIsSelectable and flags & Qt.ItemFlag.ItemIsEnabled):
                            is_item_selectable = False
                    if is_item_selectable:
                        combo.setCurrentIndex(i)
                        self.log(f"_UPDATE_FORMATTED_COMBO: '{obj_name}' - Set selection to first selectable item: '{combo.itemText(i)}'")
                        break
        else:
            # Find first selectable item if current_text was not found or was a header
            model = combo.model() # Ensure model is available
            found_selectable = False
            for i in range(combo.count()):
                is_item_selectable = True
                if model and model.item(i):
                    flags = model.item(i).flags()
                    if not (flags & Qt.ItemFlag.ItemIsSelectable and flags & Qt.ItemFlag.ItemIsEnabled):
                        is_item_selectable = False
                if is_item_selectable:
                    combo.setCurrentIndex(i)
                    self.log(f"_UPDATE_FORMATTED_COMBO: '{obj_name}' - Current text '{current_text}' not valid or not found. Set selection to first selectable item: '{combo.itemText(i)}'")
                    found_selectable = True
                    break
            if not found_selectable:
                self.log(f"_UPDATE_FORMATTED_COMBO: '{obj_name}' - No selectable items found after populating.")

    def test_category_updates(self):
        """Test method to verify the CategoryUpdateManager works correctly"""
        print("\n===== CATEGORY UPDATE MANAGER TEST =====")
        print("Testing CategoryUpdateManager functionality...")
        
        # Get all categories from template manager
        categories = []
        if self.app and hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'get_categories'):
            # Force reload project types first
            if hasattr(self.app.template_manager, 'project_type_manager'):
                self.app.template_manager.project_type_manager.load_custom_project_types()
            
            categories = self.app.template_manager.get_categories()
            print(f"Found {len(categories)} categories from template_manager: {categories}")
        else:
            print("No app or template_manager available, test failed")
            return False
        
        # Count combos before update
        all_widgets = QApplication.allWidgets()
        combo_count = 0
        empty_combo_count = 0
        
        for widget in all_widgets:
            if isinstance(widget, QComboBox):
                combo_count += 1
                if widget.count() == 0:
                    empty_combo_count += 1
        
        print(f"Found {combo_count} total comboboxes, {empty_combo_count} are empty")
        
        # Update all comboboxes
        self.update_all_category_combos(categories)
        
        # Count combos after update
        updated_count = 0
        still_empty_count = 0
        
        for widget in all_widgets:
            if isinstance(widget, QComboBox):
                if widget.count() > 0:
                    updated_count += 1
                else:
                    still_empty_count += 1
        
        print(f"After update: {updated_count} comboboxes populated, {still_empty_count} still empty")
        print("===== TEST COMPLETE =====\n")
        
        return updated_count > 0

    def _schedule_update_all_category_combos(self, categories):
        """Schedules the update of all category comboboxes via a QTimer."""
        self.log(f"Scheduling update for all category combos with {len(categories)} categories via QTimer.")
        # Use a more substantial delay to allow other synchronous/asynchronous operations to complete
        QTimer.singleShot(250, lambda: self.update_all_category_combos(categories))

def get_instance(app=None):
    """Get the singleton instance of the CategoryUpdateManager"""
    global _instance
    if _instance is None:
        _instance = CategoryUpdateManager(app)
    elif app is not None and _instance.app is None:
        _instance.set_app(app)
    return _instance 

def test_category_update_manager(app=None):
    """Run a test of the CategoryUpdateManager"""
    manager = get_instance(app)
    return manager.test_category_updates() 
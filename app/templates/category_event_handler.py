#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Category Update Manager - Event Handling and Coordination

This module provides the centralized CategoryUpdateManager class that handles
events related to category changes and coordinates UI updates across the application.
"""

import logging
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication, QComboBox, QDialog

from app.templates.category_combobox_updater import (
    update_single_combobox, 
    ensure_all_combos_have_hover_delegates,
    log_updater as log_combobox_updater # Alias for clarity if needed
)

# Singleton instance for CategoryUpdateManager
_manager_instance = None

# Debug flag for this module
DEBUG_EVENT_HANDLER = True # Set to False in production

def log_event_handler(message):
    """Log messages if debug is enabled for this module"""
    if DEBUG_EVENT_HANDLER:
        print(f"[CategoryEventHandler] {message}")
        logging.debug(f"[CategoryEventHandler] {message}")

class CategoryUpdateManager(QObject):
    """
    Centralized manager for category updates throughout the application.
    Coordinates updates to UI elements when categories change.
    """
    categories_changed_signal = pyqtSignal(list)
    
    def __init__(self, app=None):
        super().__init__()
        self.app = app
        # Timer for debouncing updates
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._perform_scheduled_update)
        self.pending_categories_update = None

        self.categories_changed_signal.connect(self._schedule_global_combobox_update)
        log_event_handler("CategoryUpdateManager initialized.")

    def set_app(self, app):
        self.app = app
        log_event_handler(f"Application instance set: {app}")

    def get_current_categories_from_source(self):
        """Retrieves the current list of categories from the primary source (e.g., TemplateManager)."""
        if self.app and hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'get_categories'):
            # Ensure project types (which can be categories) are loaded/reloaded
            if hasattr(self.app.template_manager, 'project_type_manager') and hasattr(self.app.template_manager.project_type_manager, 'load_custom_project_types'):
                self.app.template_manager.project_type_manager.load_custom_project_types()
                log_event_handler("Reloaded custom project types before getting categories.")
            
            categories = self.app.template_manager.get_categories()
            log_event_handler(f"Retrieved {len(categories)} categories from template_manager: {categories}")
            return categories
        log_event_handler("Could not retrieve categories from template_manager.")
        return []

    def notify_categories_changed(self, categories: list = None):
        """
        Public method to call when categories have changed externally (e.g., from Category Management Dialog).
        If categories list is provided, it's used. Otherwise, it fetches from the source.
        """
        log_event_handler("notify_categories_changed called.")
        if categories is not None:
            log_event_handler(f"External categories provided: {categories}")
            self.categories_changed_signal.emit(categories)
        else:
            log_event_handler("No external categories provided, will fetch from source.")
            # Emit with empty list to trigger fetch in the slot, or fetch directly
            # Forcing a fetch here ensures the signal carries the most current data if possible
            current_cats = self.get_current_categories_from_source()
            self.categories_changed_signal.emit(current_cats) 

    def _schedule_global_combobox_update(self, categories: list):
        """
        Schedules an update of all category comboboxes. 
        This debounces rapid changes.
        """
        log_event_handler(f"_schedule_global_combobox_update triggered with {len(categories)} categories.")
        self.pending_categories_update = categories
        # Debounce: wait 50ms before actually updating to catch rapid successive calls
        self.update_timer.start(50) 

    def _perform_scheduled_update(self):
        """
        Actually performs the update of all comboboxes after the debounce timer.
        """
        if self.pending_categories_update is None:
            log_event_handler("Scheduled update triggered, but no pending categories. Fetching fresh.")
            self.pending_categories_update = self.get_current_categories_from_source()
            if not self.pending_categories_update:
                log_event_handler("No categories found even after fetching. Aborting update.")
                return
        
        categories_to_update = self.pending_categories_update
        self.pending_categories_update = None # Clear pending state

        log_event_handler(f"Performing scheduled update for {len(categories_to_update)} categories: {categories_to_update}")
        self.update_all_category_combos_globally(categories_to_update)
        ensure_all_combos_have_hover_delegates(self.app)

    def force_immediate_global_update(self):
        """
        Forces an immediate update of all category comboboxes, bypassing the debounce timer.
        Useful for initial setup or after explicit user actions.
        """
        log_event_handler("force_immediate_global_update called.")
        self.update_timer.stop() # Cancel any pending scheduled update
        self.pending_categories_update = None # Clear any pending data
        
        categories = self.get_current_categories_from_source()
        if categories:
            self.update_all_category_combos_globally(categories)
            ensure_all_combos_have_hover_delegates(self.app)
        else:
            log_event_handler("No categories found for forced immediate update.")

    def update_all_category_combos_globally(self, categories: list):
        """
        Updates all relevant QComboBoxes across the application.
        Iterates through widgets and uses update_single_combobox.
        """
        if not categories:
            log_event_handler("UPDATE_ALL_GLOBALLY: No categories provided, skipping.")
            return
        
        log_event_handler(f"UPDATE_ALL_GLOBALLY: Starting update with {len(categories)} categories: {categories}")
        
        app_instance = self.app if self.app else QApplication.instance()
        if not app_instance:
            log_event_handler("UPDATE_ALL_GLOBALLY: No QApplication instance found.")
            return

        all_widgets = QApplication.allWidgets()
        updated_count = 0

        # Define known names for comboboxes that should be updated
        # This list should be comprehensive based on observed names in the project
        known_category_combo_names = [
            "template_category_combo_box", # Common name in structure editor / forms
            "project_type_combo_box",      # Also common
            "category_combo",              # Generic category combo
            "type_combo",                  # Used in template_creation_form
            "gallerycategoryfilter",       # Gallery specific
            "category_filter",             # Another gallery filter possibility
            # Add other specific names if discovered
        ]

        for widget in all_widgets:
            if isinstance(widget, QComboBox):
                obj_name = widget.objectName().lower()
                # Check if the combobox is one of the known types or if it's in a relevant dialog
                is_known_target = any(known_name in obj_name for known_name in known_category_combo_names)
                
                # More sophisticated check: if it's in a dialog related to templates or categories
                # This helps catch unnamed or generically named comboboxes in specific contexts.
                parent_dialog = widget
                is_in_relevant_dialog = False
                while parent_dialog is not None:
                    if isinstance(parent_dialog, QDialog):
                        dialog_title = parent_dialog.windowTitle().lower()
                        if "template" in dialog_title or "category" in dialog_title or "filter" in dialog_title:
                            is_in_relevant_dialog = True
                        break
                    parent_dialog = parent_dialog.parentWidget()

                if is_known_target or is_in_relevant_dialog:
                    log_event_handler(f"UPDATE_ALL_GLOBALLY: Updating QComboBox '{widget.objectName()}' (Known: {is_known_target}, In Dialog: {is_in_relevant_dialog})")
                    # Pass current text to preserve selection if item still exists
                    update_single_combobox(widget, categories, current_category=widget.currentText(), force_default_style=True)
                    updated_count += 1
                # else:
                #     log_event_handler(f"UPDATE_ALL_GLOBALLY: Skipping QComboBox '{widget.objectName()}' - not a known target.")
        
        log_event_handler(f"UPDATE_ALL_GLOBALLY: Finished. Updated {updated_count} comboboxes.")
        QApplication.processEvents() # Ensure UI updates propagate


# Singleton accessor
def get_category_update_manager(app=None):
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = CategoryUpdateManager(app)
    elif app and not _manager_instance.app:
        _manager_instance.set_app(app) # Ensure app instance is set if provided later
    return _manager_instance 
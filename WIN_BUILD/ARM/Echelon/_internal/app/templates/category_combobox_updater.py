#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Module for updating and styling category-related QComboBoxes.
"""

import logging
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWidgets import QApplication, QComboBox, QListView
from PyQt6.QtGui import QStandardItem, QStandardItemModel, QColor

from app.ui.color_scheme_pyqt import colors, COMBOBOX_STYLE, LISTVIEW_POPUP_STYLE
from app.ui.custom_delegates import apply_hover_delegate
from app.ui.app_theme_pyqt import ComboBoxItemDelegate
from app.constants import DEFAULT_TEMPLATE_CATEGORIES

# Debug flag
DEBUG_UPDATER = True # Set to False in production

def log_updater(message):
    """Log messages if debug is enabled"""
    if DEBUG_UPDATER:
        print(f"[CategoryComboboxUpdater] {message}")
        logging.debug(f"[CategoryComboboxUpdater] {message}")

def update_single_combobox(combo: QComboBox, categories: list, current_category: str = None, force_default_style: bool = False):
    """
    Update a single combobox with the given categories, preserving selection and applying styles.

    Args:
        combo (QComboBox): The combobox to update.
        categories (list): The list of category strings.
        current_category (str, optional): The category to pre-select. Defaults to None.
        force_default_style (bool, optional): If True, forces the application of default styling.
    """
    log_updater(f"UPDATE_SINGLE_COMBO: Received combo: {combo}, type: {type(combo)}")
    if combo is None:
        log_updater(f"UPDATE_SINGLE_COMBO: Combo is None.")
        return
    if not isinstance(combo, QComboBox):
        log_updater(f"UPDATE_SINGLE_COMBO: Combo is not a QComboBox instance. Type: {type(combo)}")
        return
    if not categories:
        log_updater(f"UPDATE_SINGLE_COMBO: No categories provided for combo: {combo.objectName()}.")
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("✓ No Category") # Use addItem directly
        combo.setCurrentIndex(0)
        combo.blockSignals(False)
        log_updater(f"UPDATE_SINGLE_COMBO: Added only 'No Category' to {combo.objectName()} as no other categories were provided.")
        if force_default_style:
            current_style = combo.styleSheet()
            if not current_style or COMBOBOX_STYLE not in current_style:
                combo.setStyleSheet(COMBOBOX_STYLE)
                log_updater(f"UPDATE_SINGLE_COMBO: Applied COMBOBOX_STYLE to \'{combo.objectName()}\' (only No Category).")
        return

    obj_name = combo.objectName()
    parent = combo.parent()
    parent_name = parent.objectName() if parent else "None"
    log_updater(f"UPDATE_SINGLE_COMBO: Updating '{obj_name}' (Parent: '{parent_name}') with {len(categories)} categories.")

    current_text_to_restore = current_category if current_category else combo.currentText()
    # Store current index as a fallback if text isn't found later due to model changes
    current_index_to_restore = combo.currentIndex() 
    initial_item_count = combo.count()
    log_updater(f"UPDATE_SINGLE_COMBO: '{obj_name}' initial state - Items: {initial_item_count}, Current selection to restore: '{current_text_to_restore}' (index: {current_index_to_restore})")

    combo.blockSignals(True)

    # Use QStandardItemModel to allow for non-selectable headers
    model = QStandardItemModel(combo)

    settings = QSettings()
    hide_defaults = settings.value("category_manager/hide_defaults", False, type=bool)

    # Always add "No Category" first
    no_category_item = QStandardItem("✓ No Category")
    no_category_item.setData(True, Qt.ItemDataRole.UserRole + 1) # Mark as special
    model.appendRow(no_category_item)

    default_display_categories = []
    custom_display_categories = []

    # Ensure "No Category" itself isn't processed as a regular category
    # Also handle the case where current_category might be "No Category" (with or without tick)
    unique_categories = sorted(list(set(c for c in categories if c and c.strip() and c.lower() not in ["no category", "✓ no category"])))

    for category_name in unique_categories:
        if category_name in DEFAULT_TEMPLATE_CATEGORIES:
            default_display_categories.append(category_name)
        else:
            custom_display_categories.append(category_name)
    
    if not hide_defaults and default_display_categories:
        default_header = QStandardItem("─ Default Categories ─")
        default_header.setEnabled(False)
        default_header.setData(True, Qt.ItemDataRole.UserRole + 2) # Mark as header
        # Set font for header (optional, for visual distinction)
        font = default_header.font()
        font.setBold(True)
        default_header.setFont(font)
        model.appendRow(default_header)
        for category_name in default_display_categories:
            item = QStandardItem(category_name)
            model.appendRow(item)

    if custom_display_categories:
        custom_header = QStandardItem("─ Custom Categories ─")
        custom_header.setEnabled(False)
        custom_header.setData(True, Qt.ItemDataRole.UserRole + 2) # Mark as header
        font = custom_header.font()
        font.setBold(True)
        custom_header.setFont(font)
        model.appendRow(custom_header)
        for category_name in custom_display_categories:
            item = QStandardItem(category_name)
            model.appendRow(item)
            
    combo.setModel(model)
    # --- End of new model-based logic ---

    # Restore selection
    if current_text_to_restore:
        index_to_select = combo.findText(current_text_to_restore)
        if index_to_select != -1:
            combo.setCurrentIndex(index_to_select)
            log_updater(f"UPDATE_SINGLE_COMBO: Restored selection to '{current_text_to_restore}' at index {index_to_select} for '{obj_name}'.")
        else:
            log_updater(f"UPDATE_SINGLE_COMBO: Could not find text '{current_text_to_restore}' to restore selection for '{obj_name}'. Current items: {[combo.itemText(i) for i in range(combo.count())]}")
            if combo.count() > 0:
                combo.setCurrentIndex(0) # Select first item if previous not found
    elif combo.count() > 0:
        combo.setCurrentIndex(0) # Default to first item if no specific selection to restore

    combo.blockSignals(False)

    # Apply styling
    # The main application theme (app_theme_pyqt.py) is expected to handle
    # the QListView popup styling and item delegate (for hover/selection) globally
    # via ComboBoxPopupFilter and ComboBoxItemDelegate.
    
    # The COMBOBOX_STYLE is for the QComboBox widget (the button) itself.
    if force_default_style:
        # Check if the base style is already present or if the stylesheet is empty.
        # Avoid appending if the exact style is already there to prevent duplicate properties.
        current_style = combo.styleSheet()
        if not current_style or COMBOBOX_STYLE not in current_style:
            # It's generally safer to set it rather than append, 
            # unless specifically managing layered stylesheets.
            combo.setStyleSheet(COMBOBOX_STYLE)
            log_updater(f"UPDATE_SINGLE_COMBO: Applied COMBOBOX_STYLE to '{obj_name}'.")

    log_updater(f"UPDATE_SINGLE_COMBO: Finished updating '{obj_name}'. Items: {combo.count()}, Current: '{combo.currentText()}'")

    # --- NEW DIRECT VIEW CONFIGURATION ---
    view = combo.view()
    if view and isinstance(view, QListView):
        log_updater(f"UPDATE_SINGLE_COMBO: Configuring view for '{obj_name}'")
        
        view.setStyleSheet(LISTVIEW_POPUP_STYLE)
        log_updater(f"UPDATE_SINGLE_COMBO: Applied LISTVIEW_POPUP_STYLE to view of '{obj_name}'")

        # Set Item Delegate
        current_delegate = view.itemDelegate()
        if not isinstance(current_delegate, ComboBoxItemDelegate):
            delegate = ComboBoxItemDelegate(view) # Pass view as parent
            view.setItemDelegate(delegate)
            log_updater(f"UPDATE_SINGLE_COMBO: Applied ComboBoxItemDelegate to view of '{obj_name}'")
        else:
            log_updater(f"UPDATE_SINGLE_COMBO: View of '{obj_name}' already has ComboBoxItemDelegate.")

        # Set Mouse Tracking
        view.setMouseTracking(True)
        log_updater(f"UPDATE_SINGLE_COMBO: View mouseTracking for '{obj_name}': {view.hasMouseTracking()}")
        if hasattr(view, 'viewport'):
            view.viewport().setMouseTracking(True)
            log_updater(f"UPDATE_SINGLE_COMBO: Viewport mouseTracking for '{obj_name}': {view.viewport().hasMouseTracking()}")
    elif view:
        log_updater(f"UPDATE_SINGLE_COMBO: View for '{obj_name}' is not QListView, it is {type(view)}. Skipping delegate/mouseTracking setup.")
    else:
        log_updater(f"UPDATE_SINGLE_COMBO: No view found for '{obj_name}'.")
    # --- END NEW DIRECT VIEW CONFIGURATION ---

    QApplication.processEvents() # Process events to ensure UI updates if called mid-operation


def ensure_all_combos_have_hover_delegates(app_instance=None):
    """
    Ensure all relevant QComboBoxes in the application have hover delegates applied.
    This is crucial for consistent item highlighting.
    
    NOTE: This function's body is commented out as of [Date of refactor]
    The global theme in app_theme_pyqt.py (specifically ComboBoxPopupFilter 
    applying ComboBoxItemDelegate) is expected to handle hover effects for 
    QComboBox popups globally. This function is preserved as a stub in case
    that assumption proves incorrect or specific overrides are needed later.
    """
    # log_updater("Skipping ensure_all_combos_have_hover_delegates; relying on global theme.")
    if app_instance is None:
        app_instance = QApplication.instance()
    if not app_instance:
        log_updater("No QApplication instance found for delegate application.")
        return

    all_widgets = QApplication.allWidgets()
    delegate_count = 0
    
    # Known category-related combo box names (can be expanded)
    known_category_combo_names = [
        "template_category_combo_box", 
        "project_type_combo_box", 
        "category_combo",
        "type_combo" # From template_creation_form
    ] 
    # Also include general gallery filters if they behave like category dropdowns
    gallery_filter_names = ["gallerycategoryfilter", "category_filter"]

    for widget in all_widgets:
        if isinstance(widget, QComboBox):
            obj_name = widget.objectName().lower()
            
            is_target_combo = (any(name in obj_name for name in known_category_combo_names) or
                              any(name in obj_name for name in gallery_filter_names))
            
            if is_target_combo:
                apply_hover_delegate(widget) # This was the line applying the local delegate
                delegate_count += 1
    
    log_updater(f"Applied/Ensured hover delegates for {delegate_count} targeted QComboBoxes.")
    QApplication.processEvents()


def style_category_combobox(combo: QComboBox):
    """
    Applies a standardized style to a category QComboBox.
    
    NOTE: This function's body is commented out as of [Date of refactor]
    The main application theme (app_theme_pyqt.py) should handle styling.
    The COMBOBOX_STYLE constant defines the style for the QComboBox button.
    The hover/selection effects for popup items are expected to be handled
    by the global theme's ComboBoxItemDelegate applied via ComboBoxPopupFilter.
    This function is preserved as a stub.
    """
    log_updater(f"Skipping style_category_combobox for '{combo.objectName()}'; relying on global theme and update_single_combobox.")
    # if not combo:
    #     return

    # # Core style for the button is COMBOBOX_STYLE from app.ui.color_scheme_pyqt
    # # update_single_combobox can apply this using force_default_style=True.
    # # Example: combo.setStyleSheet(COMBOBOX_STYLE)

    # # The popup (QListView) styling (LISTVIEW_POPUP_STYLE) and item delegate
    # # are expected to be handled by the global theme.
    # # Example: apply_hover_delegate(combo)

    # log_updater(f"Styled and applied hover delegate to QComboBox: {combo.objectName()}") 
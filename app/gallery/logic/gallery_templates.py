#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template gallery and associated UI components
"""

import os
import sys
import time
import re
import copy
from datetime import datetime
from functools import partial
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QGridLayout, 
    QLabel, QPushButton, QComboBox, QSizePolicy, QApplication,
    QFrame, QMenu, QMessageBox, QAction, QButtonGroup, QToolButton, QTableWidget, 
    QTableWidgetItem, QAbstractItemView, QHeaderView, QSpacerItem, QLineEdit, QCompleter,
    QListWidget, QListWidgetItem, QStyle, QStyledItemDelegate, QStyleOptionViewItem,
    QStyleOptionFrame, QCheckBox, QDialog, QTreeWidget, QTreeWidgetItem, QSplitter
)
from PyQt6.QtGui import QIcon, QColor, QFont, QPixmap, QCursor, QPainter, QPalette, QPen, QBrush
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint, QRect, QBuffer, QTimer, QEvent, QItemSelectionModel
import traceback # Import the traceback module

from app.ui.color_scheme_pyqt import colors, ACCENT_BUTTON_STYLE
from app.templates.components.utils import get_system_font
from app.ui.gallery.components.template_card import TemplateCard
from app.gallery.logic.gallery_events import GalleryEvents # MODIFIED: Update import path
from app.constants import get_resource_path
from app.ui.views.template_table_view import TemplateTableView # Import the new TableView

def sort_templates(templates, sort_field='name', sort_order='asc'):
    """Sort templates by the given field and order, while respecting folder hierarchy"""
    # If templates is a dictionary, convert to list of tuples or dicts
    if isinstance(templates, dict):
        template_list = []
        for name, data in templates.items():
            if isinstance(data, dict):
                # Make sure 'name' is in the data
                template_data = dict(data)
                template_data['name'] = name
                template_list.append(template_data)
            else:
                template_list.append({'name': name})
    else:
        template_list = templates

    # Now sort based on field and order
    reverse = sort_order.lower() != 'asc'
    
    # Make sure the sort is stable by using a tuple with name as secondary sort
    def sort_key(template):
        if isinstance(template, str):
            # This case might not be hit if input is always list of dicts now
            return (1, template.lower(), '') # Treat as non-folder, sort by name
        
        is_folder = template.get('is_folder', False)
        
        # Primary sort key: 0 for folders, 1 for templates (for ascending sort)
        folder_priority = 0 if is_folder else 1
        
        name_val = template.get('name', '').lower()
        
        # Handle different sort fields
        if sort_field == 'name':
            return (folder_priority, name_val)
        elif sort_field == 'category':
            category_val = template.get('category', '').lower()
            if is_folder:
                category_val = "Folder" # Special category for folders 
            return (folder_priority, category_val, name_val)
        elif sort_field == 'created':
            created_val = template.get('created', 0)
            if is_folder:
                # Keep folders at the top regardless of sort field
                created_val = 0 if not reverse else float('inf')
            return (folder_priority, created_val, name_val)
        elif sort_field == 'modified':
            modified_val = template.get('modified', 0)
            if is_folder:
                # Keep folders at the top regardless of sort field
                modified_val = 0 if not reverse else float('inf')
            return (folder_priority, modified_val, name_val)
        else:
            # Default to name sorting for unknown fields
            return (folder_priority, name_val)

    # If sorting templates in a way that would separate folders by category,
    # ensure folders still come before templates
    if reverse and sort_field in ['category', 'created', 'modified']:
        # Process folders and templates separately to maintain hierarchy
        folders = [t for t in template_list if t.get('is_folder', False)]
        templates_only = [t for t in template_list if not t.get('is_folder', False)]
        
        # Sort folders by name or specified field
        sorted_folders = sorted(folders, key=sort_key, reverse=reverse)
        
        # Sort templates by specified field
        sorted_templates = sorted(templates_only, key=sort_key, reverse=reverse)
        
        # Combine with folders first, then templates
        return sorted_folders + sorted_templates
    else:
        # Regular sort works fine for ascending order or name-based sorts
        return sorted(template_list, key=sort_key, reverse=reverse)

def handle_template_edit(gallery, template=None, selected_template=None, name=None, **kwargs):
    """
    Handle template edit operation
    
    Args:
        gallery: The gallery widget
        template: Template to edit (can be name, dict, or object)
        selected_template: Name of the currently selected template
        name: Name of the template (if template is not an object)
        **kwargs: Additional parameters
        
    Returns:
        bool: True if successful, False if canceled
    """
    try:
        print(f"🔷 GALLERY LISTENER: Starting edit of template: {template}")
        
        # Log gallery state before edit
        print(f"🔷 GALLERY LISTENER: Gallery state BEFORE edit:")
        print(f"🔷 GALLERY LISTENER: - selected_template: {getattr(gallery, 'selected_template', None)}")
        print(f"🔷 GALLERY LISTENER: - template cards count: {len(getattr(gallery, 'template_cards', []))}")
        print(f"🔷 GALLERY LISTENER: - template card names: {[getattr(card, 'template', {}).get('name', card.template) for card in getattr(gallery, 'template_cards', [])]}")
        
        from app.ui.structure_editor_functions import show_enhanced_structure_editor
        
        # Track original template name for rename detection
        original_template_name = None
        
        # Handle different template types
        if template is None and selected_template:
            # Try to get template by name
            template = selected_template
            
        # If template is a string (just the template name)
        if isinstance(template, str):
            # Get the actual template object by name
            clean_name = template.strip()
            original_template_name = clean_name
            
            # If name already has Template_ prefix, extract it
            if clean_name.startswith("Template_"):
                clean_name = clean_name[9:]  # Remove Template_ prefix
            else:
                structure_name = f"Template_{clean_name}"
            
            print(f"🔷 GALLERY LISTENER: Structure name: {structure_name}, Clean name: {clean_name}")
            
            # Try to find template by name
            print(f"🔷 GALLERY LISTENER: Searching for template with name '{clean_name}'")
            # Find the template data using the TemplateManager
            # MODIFIED: Access get_template via template_io instance
            template = gallery.app.template_manager.template_io.get_template(clean_name)

            if not template:
                QMessageBox.warning(gallery, "Template Not Found", f"Could not find template data for '{clean_name}'")
            
            # If still not found, create a new template with this name
            if template is None:
                print(f"🔷 GALLERY LISTENER: Template not found, creating new one with name '{clean_name}'")
                template = {
                    'name': clean_name,
                    'structure_name': structure_name,
                    'structure': []
                }
        
        # If we still don't have a template, create a new one
        if template is None:
            print(f"🔷 GALLERY LISTENER: No template found, creating a new empty template")
            template = {
                'name': '',
                'structure_name': '',
                'structure': []
            }
        
        # Make sure template is a dict
        if not isinstance(template, dict):
            print(f"🔷 GALLERY LISTENER: Template is not a dict, converting: {template}")
            template = {
                'name': str(template),
                'structure_name': f"Template_{template}",
                'structure': []
            }
        
        # Get structure from template manager or disk if available
        if 'structure' not in template or not template['structure']:
            structure_name = template.get('structure_name')
            if not structure_name and 'name' in template:
                structure_name = f"Template_{template['name']}"
            
            structure = None
            
            # Try to load structure using various name formats
            for name_to_try in [structure_name, template.get('name'), f"Template_{template.get('name')}"]:
                if not name_to_try:
                    continue
                    
                print(f"🔷 GALLERY LISTENER: Trying to get structure for name '{name_to_try}'")
                
                # Try to get structure from template manager
                if hasattr(gallery, 'app') and hasattr(gallery.app, 'template_manager'):
                    structure = gallery.app.template_manager.get_structure(name_to_try)
                    if structure:
                        print(f"🔷 GALLERY LISTENER: Found structure for name '{name_to_try}'")
                        break
            
            # If structure was found, add it to the template
            if structure:
                template['structure'] = structure
        
        # Check if this is a new template
        is_new = template.get('is_new', False) or not template.get('name')
        
        # Show the structure editor
        print(f"🔷 GALLERY LISTENER: Opening structure editor - structure_name: {template.get('structure_name') or template.get('name')}, is_new: {is_new}")
        
        # Use the enhanced structure editor - Capture category and description
        success, updated_structure, updated_structure_name, _, updated_template_name, saved_category, saved_description = show_enhanced_structure_editor(
            parent=gallery if isinstance(gallery, QWidget) else None,
            structure_name=template.get('structure_name', f"Template_{template.get('name', '')}"),
            structure=template.get('structure', []),
            is_new=is_new,
            template_name=template.get('name'), # Pass current template name
            template_manager=gallery.app.template_manager if hasattr(gallery, 'app') else None # Pass template manager
        )
        
        # Check if the editor was successful and returned valid data
        if success and updated_template_name:
            print(f"🔷 GALLERY LISTENER: Editor returned success. Template='{updated_template_name}', Category='{saved_category}', Desc='{saved_description}'")
            
            # Determine if it was a rename operation
            is_rename = original_template_name and updated_template_name != original_template_name
            
            # Get the template manager instance
            template_manager = gallery.app.template_manager if hasattr(gallery, 'app') else None
            if not template_manager:
                print("❌ GALLERY LISTENER: Template manager not available")
                return False
            
            # --- Save structure (using save_custom_structure) ---
            # Ensure structure name always starts with Template_
            if not updated_structure_name.startswith("Template_"):
                updated_structure_name = f"Template_{updated_template_name}"
                
            print(f"🔷 GALLERY LISTENER: Saving structure: Name='{updated_structure_name}', Category='{saved_category}'")
            structure_save_success = template_manager.save_custom_structure(updated_structure_name, updated_structure, saved_category, saved_description)
            
            if not structure_save_success:
                print(f"❌ GALLERY LISTENER: Failed to save structure for template '{updated_template_name}'")
                QMessageBox.warning(gallery, "Save Error", f"Could not save the template structure for {updated_template_name}. The structure might be saved, but the template list may be inconsistent.")
                return False
            
            # --- Save main template file (using save_template) ---
            print(f"🔷 GALLERY LISTENER: Saving main template file: Name='{updated_template_name}', Category='{saved_category}'")
            
            # Create a template_data dictionary with all required fields
            template_data = {
                "name": updated_template_name,
                "structure": updated_structure,
                "category": saved_category,
                "description": saved_description,
                "tags": template.get('tags', []),
                "type": template.get('type', 'Standard')
            }
            
            # If this is a rename operation, include the original name
            if is_rename:
                template_data["original_name"] = original_template_name
            
            # Call save_template with the template_data dictionary
            template_save_success = template_manager.template_io.save_template(template_data)
            if template_save_success:
                save_message = "Template saved successfully"
            else:
                save_message = "Failed to save template"
            
            if template_save_success:
                print(f"🔷 GALLERY LISTENER: Successfully saved template '{updated_template_name}'")
                
                # Refresh gallery to show changes
                if hasattr(gallery, 'refresh_gallery'):
                    gallery.refresh_gallery()
                else:
                    # Fallback to populate_gallery if refresh_gallery doesn't exist
                    gallery.populate_gallery(force_refresh=True)
                
                # Select the newly created/updated template
                gallery.select_template(updated_template_name)
                
                return True # Return success
            else:
                print(f"❌ GALLERY LISTENER: Failed to save template '{updated_template_name}'")
                QMessageBox.warning(gallery, "Save Error", f"Could not save the template file for {updated_template_name}. Error: {save_message}")
                return False
        else:
            print(f"🔷 GALLERY LISTENER: Structure editor was cancelled or returned no template data.")
            return False # Return failure/cancel
    except Exception as e:
        print(f"Error in handle_template_edit: {e}")
        traceback.print_exc() # Use traceback for full error info
        QMessageBox.warning(gallery, "Edit Error", f"An error occurred during template edit: {e}")
        return False

# Function to select template after a rename operation
def select_template_after_rename(gallery, new_name, old_name):
    """Selects a template in the gallery after a rename operation, handling UI updates."""
    print(f"🔍 GALLERY SELECT: Attempting to select renamed template: '{new_name}' (was '{old_name}')")

    if not hasattr(gallery, 'selection_manager'):
        print("[ERROR] Gallery select_template_after_rename: gallery has no selection_manager!")
        return

    # It's possible the gallery hasn't fully repopulated with the new name yet.
    # Give it a moment, then try to find the template data for the new name.

    def _find_and_select():
        # Attempt to get the template data for the new name from the TemplateManager
        # This assumes TemplateManager has the latest data after rename and gallery refresh.
        template_data_new = None
        if hasattr(gallery, 'app') and hasattr(gallery.app, 'template_manager'):
            template_data_new = gallery.app.template_manager.get_template_by_name(new_name)
        
        if template_data_new:
            print(f"🔍 GALLERY SELECT: Found data for '{new_name}'. Setting as primary selection.")
            gallery.selection_manager.clear_multi_selection_list(emit_signal=False)
            gallery.selection_manager.set_primary_selection(template_data_new, emit_signal=True)
        else:
            print(f"⚠️ GALLERY SELECT: Could not find data for renamed template '{new_name}' in TemplateManager after delay. Selection may not occur.")
            # As a fallback, if the old_name is still somehow selected, clear it.
            current_primary = gallery.selection_manager.selected_template
            if current_primary and current_primary.get('name') == old_name:
                gallery.selection_manager.clear_all_selections(emit_signal=True)

    # Use QTimer to delay the selection attempt slightly, allowing UI to update.
    QTimer.singleShot(200, _find_and_select) # 200ms delay

# --- TEMPORARY TEST FUNCTIONS --- (To be removed or moved to test suite)
# Test renaming a template
# Example:
# gallery = self.app.template_gallery  # Assuming `gallery` is accessible
# test_template_rename(gallery, "My Template", "My Renamed Template")
def test_template_rename(gallery, template_name, new_name):
    """Test function for renaming a template"""
    try:
        print(f"\n--- Starting Template Rename Test ---")
        print(f"Renaming: '{template_name}' -> '{new_name}'")
        
        if not hasattr(gallery, 'app') or not hasattr(gallery.app, 'template_manager'):
            print("Template manager not found. Cannot perform rename.")
            return
        
        # Use template_manager to rename the template
        template_manager = gallery.app.template_manager
        if hasattr(template_manager, 'rename_template'):
            success = template_manager.rename_template(template_name, new_name)
            if success:
                print(f"Rename successful via template_manager: '{template_name}' -> '{new_name}'")
                
                # Refresh gallery and re-select
                gallery.populate_gallery(force_refresh=True)
                gallery.select_template(new_name) # Ensure new template is selected
                
                print(f"Selected template after rename: {gallery.selected_template.get('name') if gallery.selected_template else 'None'}")
                
                # Now, try to edit the renamed template
                QTimer.singleShot(100, lambda: GalleryEvents.on_edit_template(gallery, new_name))
                
            else:
                print(f"Rename failed via template_manager: '{template_name}' -> '{new_name}'")
        else:
            print("template_manager has no 'rename_template' method.")
            
        print(f"--- End Template Rename Test ---\n")
    except Exception as e:
        print(f"Error during rename test: {e}")
        traceback.print_exc()

# Example usage:
# gallery = self.app.template_gallery  # Assuming `gallery` is accessible
# test_template_rename_workflow(gallery, "My Template", "My Renamed Template")
def test_template_rename_workflow(gallery, template_name, new_name):
    """Tests the full rename workflow, including editing the renamed template"""
    try:
        print(f"\n--- Starting Full Template Rename Workflow Test ---")
        print(f"Renaming: '{template_name}' -> '{new_name}'")
        
        if not hasattr(gallery, 'app') or not hasattr(gallery.app, 'template_manager'):
            print("Template manager not found. Cannot perform rename.")
            return
        
        template_manager = gallery.app.template_manager
        
        # --- 1. Initial state --- (Optional)
        initial_template = template_manager.get_template_by_name(template_name)
        if not initial_template:
            print(f"Template '{template_name}' not found. Aborting test.")
            return
        print(f"Initial template data for '{template_name}': {initial_template}")
        
        # --- 2. Simulate rename request from UI --- (e.g., GalleryEvents.on_rename_template)
        GalleryEvents.on_rename_template(gallery, template_name) # This will pop up a dialog
        
        # NOTE: This test is interactive due to QInputDialog. To automate, mock QInputDialog.
        # For manual testing, enter `new_name` in the dialog.
        
        # --- 3. Verify rename in TemplateManager and on disk ---
        # This check needs to happen *after* the dialog is closed and rename is processed.
        # We'll use a QTimer to delay the check.
        def verify_rename():
            renamed_template = template_manager.get_template_by_name(new_name)
            old_template_exists = template_manager.get_template_by_name(template_name) is not None
            
            if renamed_template and not old_template_exists:
                print(f"VERIFIED: Template renamed successfully. '{new_name}' exists, '{template_name}' does not.")
                
                # --- 4. Ensure gallery is updated and new template is selected ---
                # This should be handled by populate_gallery and select_template in on_rename_template
                # We can check gallery.selected_template here
                if gallery.selected_template and gallery.selected_template.get('name') == new_name:
                    print(f"VERIFIED: Gallery updated and '{new_name}' is selected.")
                    
                    # --- 5. Try to edit the renamed template ---
                    print(f"Attempting to edit the renamed template: '{new_name}'")
                    GalleryEvents.on_edit_template(gallery, new_name) # This will open the structure editor
                    # For manual testing, make a change and save, or cancel.
                    
                    # Further verification after editor closes would require another callback/timer
                else:
                    print(f"FAILED VERIFICATION: Gallery did not select '{new_name}' after rename. Selected: {gallery.selected_template.get('name') if gallery.selected_template else 'None'}")
            else:
                print(f"FAILED VERIFICATION: Rename did not complete as expected.")
                print(f" - '{new_name}' exists: {renamed_template is not None}")
                print(f" - '{template_name}' still exists: {old_template_exists}")
                
            print(f"--- End Full Template Rename Workflow Test ---\n")
            
        # Wait a bit for the rename dialog and processing to complete
        QTimer.singleShot(3000, verify_rename) # 3 second delay, adjust if needed
        
    except Exception as e:
        print(f"Error during full rename workflow test: {e}")
        traceback.print_exc()

class GalleryTemplatesSetup:
    """Templates-related functionality for the Template Gallery"""
    
    @staticmethod
    def connect_template_signals(gallery, item, template_data):
        """Connect signals for a template item (card or list view item)."""
        if not template_data or not isinstance(template_data, dict):
            print(f"[ERROR] connect_template_signals: Invalid template_data: {template_data}")
            return

        template_name = template_data.get('name')
        if not template_name:
            print(f"[ERROR] connect_template_signals: Template data missing 'name': {template_data}")
            return

        # --- Selection Handling (Primary Signal) ---
        # This is the main signal for simple selection (single click without modifiers)
        if hasattr(item, 'clicked'):
            # Disconnect any existing connections to avoid duplicates
            try:
                item.clicked.disconnect()
            except TypeError:
                pass # No connections to disconnect
            item.clicked.connect(lambda td=template_data: gallery._on_template_select(td))

        # --- Multi-Selection Handling (Secondary Signal) ---
        # This signal is typically emitted by cards when a modifier key is used during a click.
        if hasattr(item, 'multiSelected'):
            try:
                item.multiSelected.disconnect()
            except TypeError:
                pass
            item.multiSelected.connect(lambda td=template_data, add=True: gallery.on_template_multi_select(td, add))

        # --- Double-Click for Editing ---
        if hasattr(item, 'doubleClicked'):
            try:
                item.doubleClicked.disconnect()
            except TypeError:
                pass
            # Use GalleryEvents.on_edit_template which expects the gallery and template_name
            item.doubleClicked.connect(lambda name=template_name: GalleryEvents.on_edit_template(gallery, name))

    @staticmethod
    def setup_templates_section(gallery):
        """Setup the templates section of the gallery"""
        
        # Templates section
        gallery.templates_section = QWidget()
        gallery.templates_section.setStyleSheet("background: transparent;")
        gallery.templates_section_layout = QVBoxLayout(gallery.templates_section)
        gallery.templates_section_layout.setContentsMargins(10, 0, 10, 10) # Reduced from 15,0,15,15
        
        # Templates header with search, filter, view controls
        GalleryTemplatesSetup.setup_templates_header(gallery)
        gallery.templates_section_layout.addWidget(gallery.templates_header)
        
        # Add a small margin between header and content
        spacer = QWidget()
        spacer.setFixedHeight(5)
        spacer.setStyleSheet("background: transparent;")
        gallery.templates_section_layout.addWidget(spacer)
        
        # Main content area (scrollable for cards, or table view)
        gallery.templates_content_area = QWidget()
        gallery.templates_content_area.setStyleSheet("background: transparent;")
        gallery.templates_content_layout = QVBoxLayout(gallery.templates_content_area)
        gallery.templates_content_layout.setContentsMargins(0, 0, 0, 0)
        gallery.templates_content_layout.setSpacing(0)
        
        # Scrollable container for template cards (Grid View)
        gallery.templates_scroll = QScrollArea()
        gallery.templates_scroll.setWidgetResizable(True)
        gallery.templates_scroll.setFrameShape(QFrame.NoFrame) # No border for scroll area
        gallery.templates_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        gallery.templates_scroll.setStyleSheet("background: transparent; border: none;")
        gallery.templates_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Container for template cards
        gallery.templates_container = QWidget()
        gallery.templates_container.setStyleSheet("background: transparent;")
        gallery.templates_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred) # Let it grow vertically
        
        gallery.templates_grid = QGridLayout(gallery.templates_container)
        gallery.templates_grid.setContentsMargins(0, 0, 0, 0) # No margins for the grid itself
        gallery.templates_grid.setSpacing(10)  # Space between cards
        gallery.templates_grid.setAlignment(Qt.AlignmentFlagFlagFlagFlagFlag.AlignTop | Qt.AlignmentFlagFlagFlagFlagFlag.AlignLeft)
        
        gallery.templates_scroll.setWidget(gallery.templates_container)
        gallery.templates_content_layout.addWidget(gallery.templates_scroll)
        
        # --- Table View for Templates (List View) ---
        gallery.template_table_view = TemplateTableView(gallery)
        gallery.template_table_view.setObjectName("templateGalleryTableView")
        gallery.template_table_view.selectionModel().selectionChanged.connect(gallery._on_table_selection_changed)
        gallery.template_table_view.doubleClicked.connect(gallery._on_table_item_double_clicked)
        gallery.template_table_view.templateRenamed.connect(gallery._on_template_renamed_in_table)
        gallery.template_table_view.itemDropped.connect(gallery._on_table_item_dropped)
        gallery.templates_content_layout.addWidget(gallery.template_table_view)
        
        # Add content area to section layout
        gallery.templates_section_layout.addWidget(gallery.templates_content_area)
        
        # Initially hide one of the views
        if gallery.template_view_mode == "grid":
            gallery.template_table_view.hide()
            gallery.templates_scroll.show()
        else:
            gallery.templates_scroll.hide()
            gallery.template_table_view.show()

    @staticmethod
    def setup_templates_header(gallery):
        """Setup the header for the templates section"""
        gallery.templates_header = QWidget()
        gallery.templates_header.setStyleSheet(f"background-color: {colors['card_bg']}; border: none;")
        gallery.templates_header_layout = QHBoxLayout(gallery.templates_header)
        gallery.templates_header_layout.setContentsMargins(15, 10, 15, 10)

        # Templates section header
        gallery.header_label = QLabel("Templates")
        gallery.header_label.setFont(QFont(get_system_font(), 14, QFont.Weight.Bold))
        gallery.header_label.setStyleSheet(f"color: {colors['text']}; font-weight: bold; background: transparent;")
        gallery.templates_header_layout.addWidget(gallery.header_label)

        # Search bar
        gallery.search_bar = QLineEdit()
        gallery.search_bar.setPlaceholderText("Search templates...")
        gallery.search_bar.textChanged.connect(gallery._on_search)
        gallery.search_bar.setClearButtonEnabled(True)
        gallery.search_bar.setFixedWidth(200) # Keep search bar width fixed
        gallery.templates_header_layout.addWidget(gallery.search_bar)

        # Category filter dropdown
        gallery.category_filter = QComboBox()
        gallery.category_filter.setFixedWidth(150)
        gallery.category_filter.currentIndexChanged.connect(gallery._on_category_select)
        gallery.templates_header_layout.addWidget(gallery.category_filter)
        
        # Sort dropdown
        gallery.sort_dropdown = QComboBox()
        gallery.sort_dropdown.setFixedWidth(120)
        gallery.sort_dropdown.addItems(["Name (A-Z)", "Name (Z-A)", "Date Created (Newest)", "Date Created (Oldest)", "Date Modified (Newest)", "Date Modified (Oldest)", "Category"])
        gallery.sort_dropdown.currentIndexChanged.connect(gallery._on_sort_change)
        gallery.templates_header_layout.addWidget(gallery.sort_dropdown)

        # Stretch to push controls to the right
        gallery.templates_header_layout.addStretch(1)

        # Folder label (shows current folder)
        gallery.folder_label = QLabel("")
        gallery.folder_label.setFont(QFont(get_system_font(), 11, QFont.Weight.Bold))
        gallery.folder_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
        gallery.folder_label.hide()
        gallery.templates_header_layout.addWidget(gallery.folder_label)

        # Back button (to navigate out of folders)
        gallery.back_button = QPushButton("Back")
        gallery.back_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        gallery.back_button.clicked.connect(gallery._on_back_to_all)
        gallery.back_button.setVisible(False) # Initially hidden
        gallery.back_button.setFixedSize(80, 30)
        gallery.templates_header_layout.addWidget(gallery.back_button)
        
        # Add Template button
        gallery.add_template_button = QPushButton("New Template")
        gallery.add_template_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        gallery.add_template_button.clicked.connect(gallery._on_add_template)
        gallery.add_template_button.setFixedSize(120, 30)
        gallery.templates_header_layout.addWidget(gallery.add_template_button)
        
        # Create view toggle buttons
        gallery.template_grid_view_btn = QToolButton()
        gallery.template_grid_view_btn.setCheckable(True)
        gallery.template_grid_view_btn.setToolTip("Grid View")
        gallery.template_grid_view_btn.setText("Grid")
        gallery.template_grid_view_btn.setChecked(gallery.template_view_mode == "grid")
        gallery.template_grid_view_btn.clicked.connect(lambda: gallery._set_template_view_mode("grid"))
        gallery.template_grid_view_btn.setFixedSize(65, 24) # Match folder view buttons
        
        gallery.template_grid_view_btn.setStyleSheet("""
            QToolButton {
                background-color: #2A2A2A;
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                border-top-left-radius: 3px;
                border-bottom-left-radius: 3px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 3px 8px;
                min-width: 50px;
            }
            QToolButton:checked {
                background-color: #3E3E3E;
                color: white;
                border-color: #585858;
            }
            QToolButton:hover:!checked {
                background-color: #323232;
                border-color: #585858;
            }
        """)
        
        gallery.template_list_view_btn = QToolButton()
        gallery.template_list_view_btn.setCheckable(True)
        gallery.template_list_view_btn.setToolTip("List View")
        gallery.template_list_view_btn.setText("List")
        gallery.template_list_view_btn.setChecked(gallery.template_view_mode == "list")
        gallery.template_list_view_btn.clicked.connect(lambda: gallery._set_template_view_mode("list"))
        gallery.template_list_view_btn.setFixedSize(65, 24) # Match folder view buttons
        
        gallery.template_list_view_btn.setStyleSheet("""
            QToolButton {
                background-color: #2A2A2A;
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                border-left: none; /* Important for joining with grid button */
                padding: 3px 8px;
                min-width: 50px;
            }
            QToolButton:checked {
                background-color: #3E3E3E;
                color: white;
                border-color: #585858;
            }
            QToolButton:hover:!checked {
                background-color: #323232;
                border-color: #585858;
            }
        """)
        
        # Create a button group to manage selection
        gallery.template_view_toggle_group = QButtonGroup(gallery)
        gallery.template_view_toggle_group.addButton(gallery.template_grid_view_btn)
        gallery.template_view_toggle_group.addButton(gallery.template_list_view_btn)
        
        # Add view toggle buttons to header layout
        gallery.templates_header_layout.addWidget(gallery.template_grid_view_btn)
        gallery.templates_header_layout.addWidget(gallery.template_list_view_btn)

    @staticmethod
    def populate_templates_list(gallery, items_to_populate):
        """Populate the list view (QTableView) with templates only (no folders)."""
        print(f"[DEBUG] List View (TableView): Starting population")
        
        try:
            # Ensure the table view instance exists
            if not hasattr(gallery, 'template_table_view') or gallery.template_table_view is None:
                print("[ERROR] TemplateTableView instance not found during population.")
                return # Cannot proceed without table view
                
            # Ensure table view is visible in the proper container
            if hasattr(gallery, 'templates_list_container'):
                gallery.templates_list_container.setVisible(True)
            gallery.template_table_view.setVisible(True)

            # Get items to show - make a copy to avoid modifying original
            items_data = items_to_populate.copy() if items_to_populate else []
            
            # If items_data is a dict, get values
            if isinstance(items_data, dict):
                items_data = list(items_data.values())
                 
            print(f"[DEBUG] List View (TableView): Processing {len(items_data)} items")
            
            # Filter out any folder items here explicitly as an extra precaution
            template_items_only = [item for item in items_data if isinstance(item, dict) and not item.get('is_folder', False)]
            print(f"[DEBUG] List View (TableView): Filtered out folders, processing {len(template_items_only)} template items only")
            
            # Verify each template item has proper structure and keys
            validated_items = []
            for item in template_items_only:
                # Every item must have 'name' attribute at minimum
                if 'name' not in item:
                    print(f"[WARNING] List View: Skipping item without name: {item}")
                    continue
                
                # Ensure all required attributes are present
                validated_item = {
                    'name': item.get('name', ''),
                    'is_folder': False,  # Always false for templates in list view
                    'parent_folder': item.get('parent_folder', 'ROOT'),
                    'category': item.get('category', 'Uncategorized'),
                    'created': item.get('created', None),
                    'modified': item.get('modified', None)
                }
                validated_items.append(validated_item)
                
            print(f"[DEBUG] List View (TableView): Validated {len(validated_items)} template items")

            # --- Sorting Logic ---
            current_sort_field = getattr(gallery, 'current_sort_field', 'name')
            current_sort_order = getattr(gallery, 'current_sort_order', 'asc')
            
            print(f"[DEBUG] List View (TableView): Sorting by {current_sort_field} ({current_sort_order})")
            
            # Sort items using the existing helper function
            try:
                sorted_items = sort_templates(validated_items, current_sort_field, current_sort_order)
                print(f"[DEBUG] List View (TableView): Sorted {len(sorted_items)} items")
            except Exception as sort_e:
                print(f"[ERROR] Failed to sort templates for table view: {sort_e}")
                traceback.print_exc()
                sorted_items = validated_items # Use unsorted data as fallback

            # --- Populate Table View ---
            print(f"[DEBUG] Populating TemplateTableView with {len(sorted_items)} template items")
            gallery.template_table_view.populate_data(sorted_items)
            
            # Ensure the proxy model has the correct filter
            proxy_model = gallery.template_table_view.model()
            if hasattr(proxy_model, 'set_current_filter_folder'):
                proxy_model.set_current_filter_folder(gallery.current_folder)
                
            print(f"[DEBUG] List View (TableView): Population complete.")
            
        except Exception as e:
            print(f"[ERROR] Error populating templates list (TableView): {e}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def _update_column_widths(gallery, position, index):
        # This method is now obsolete as QTableView/QHeaderView handles widths internally
        # Kept temporarily to avoid breaking calls, should be removed later.
        # print(f"[DEBUG] (Obsolete) _update_column_widths called for splitter: pos={position}, index={index}")
        # if hasattr(gallery, 'header_splitter'):
        #     gallery.header_sizes = gallery.header_splitter.sizes()
        #     print(f"[DEBUG] (Obsolete) Splitter sizes: {gallery.header_sizes}")
        pass

    @staticmethod
    def populate_templates_grid(gallery, templates_to_show):
        """Populate templates in grid view"""
        # print(f"Populating grid view with {len(templates_to_show)} templates.")
        # print(f"Templates data: {templates_to_show}")
        
        # Make sure the grid view is visible if this mode is active
        if gallery.template_view_mode == "grid":
            gallery.templates_scroll.show()
            gallery.template_table_view.hide()

        # Clear existing items from the grid
        for i in reversed(range(gallery.templates_grid.count())):
            widget = gallery.templates_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        gallery.template_cards.clear()

        col = 0
        row = 0
        container_width = gallery.templates_container.width()
        
        # Default card width (can be adjusted based on scale)
        # Use gallery.icon_size if available, otherwise default to 150
        card_width = getattr(gallery, 'icon_size', 150) 
        card_width_with_spacing = card_width + gallery.templates_grid.spacing()
        
        min_cols = 2 # Minimum number of columns
        
        # Calculate max columns based on container width and card size
        # Default to 4 columns if container width is not yet available
        if container_width <= 0 or card_width_with_spacing <= 0:
            max_cols = 4 
        else:
            # Ensure calculated_cols is at least min_cols
            calculated_cols = max(min_cols, container_width // card_width_with_spacing)
            # Cap max_cols at a reasonable number (e.g., 8)
            max_cols = min(8, calculated_cols) 

        # print(f"Calculated max_cols: {max_cols} (container_width: {container_width}, card_width_with_spacing: {card_width_with_spacing})")
        
        # Sort templates based on current sort settings
        sorted_templates = sort_templates(templates_to_show, gallery.current_sort_field, gallery.current_sort_order)

        for template_data in sorted_templates:
            if not isinstance(template_data, dict):
                print(f"[WARN] populate_templates_grid: Skipping non-dict template_data: {template_data}")
                continue
            
            template_card = GalleryTemplatesSetup.create_template_card(gallery, template_data)
            if template_card:
                gallery.templates_grid.addWidget(template_card, row, col)
                gallery.template_cards.append(template_card)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            else:
                print(f"[WARN] Failed to create template card for: {template_data.get('name', 'Unknown')}")
        
        # Add a stretch at the end of the grid to push items to the top-left
        # gallery.templates_grid.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding), row + 1, 0, 1, max_cols)
        # gallery.templates_grid.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum), 0, max_cols, row + 1, 1)

        # Update selection state after populating
        GalleryTemplatesSetup.update_template_selection_state(gallery)
        
        # Force UI update
        gallery.templates_container.updateGeometry()
        gallery.templates_container.update()
        gallery.templates_scroll.update()
        gallery.templates_scroll.viewport().update()
        QApplication.processEvents() # Force UI update

    @staticmethod
    def set_template_view_mode(gallery, mode):
        """Set the template view mode (grid or list)"""
        print(f"DEBUG: Setting template view mode to: {mode}")
        old_mode = gallery.template_view_mode
        gallery.template_view_mode = mode
        
        # Toggle buttons
        gallery.template_grid_view_btn.setChecked(mode == "grid")
        gallery.template_list_view_btn.setChecked(mode == "list")
        
        # Show/hide the appropriate view container for templates
        if mode == "grid":
            gallery.templates_scroll.show()
            gallery.template_table_view.hide()
        else: # List view
            gallery.templates_scroll.hide()
            gallery.template_table_view.show()
            # Ensure the table view header is correctly sized after showing
            if hasattr(gallery.template_table_view, 'horizontalHeader'):
                gallery.template_table_view.horizontalHeader().resizeSections(QHeaderView.ResizeMode.ResizeToContents)

        # Ensure folders section remains visible in both modes when appropriate
        # This is a critical fix - we don't hide the folders section just because we switch to list view
        # The folders section should only be hidden based on navigation state (in a folder) or filter state
        if gallery.current_folder is None and gallery.current_category == "All" and not gallery.current_search:
            # At root with no category or search filters, folders should be visible
            if hasattr(gallery, 'folders_section') and not gallery.folders_section.isVisible():
                gallery.folders_section.setVisible(True)
        
        # Repopulate with current templates - pass force_refresh=True to ensure proper folder visibility
        gallery.populate_gallery(force_refresh=True)

        # Update settings
        if gallery.app and gallery.app.settings_manager:
            gallery.app.settings_manager.update_setting("template_view_mode", mode)
            
        # After switching view, ensure selection UI is consistent
        gallery._update_selection_ui()
        
        print(f"[DEBUG] View mode set to '{mode}'.")
        print(f"[DEBUG] Grid visible: {gallery.templates_scroll.isVisible()}")
        print(f"[DEBUG] List visible: {gallery.template_table_view.isVisible()}")

    @staticmethod
    def update_template_selection_state(gallery):
        """Updates the visual selection state of template cards based on GallerySelectionManager."""
        # print("Updating template card selection states from manager...")
        if not hasattr(gallery, 'selection_manager'):
            # print("[WARN] GalleryTemplatesSetup.update_template_selection_state: gallery has no selection_manager!")
            return

        primary_selected = gallery.selection_manager.selected_template
        multi_selected_list = gallery.selection_manager.multi_selected_templates
        # print(f"  Primary: {primary_selected.get('name') if primary_selected else 'None'}, Multi: {[t.get('name') for t in multi_selected_list]}")

        def is_template_selected(template_name, selected_template):
            return selected_template and selected_template.get('name') == template_name

        def is_template_multi_selected(template_name, multi_selected_templates):
            return any(t.get('name') == template_name for t in multi_selected_templates if isinstance(t, dict))

        # This function will be applied to items in both grid (TemplateCard) and list (QTableWidgetItem via delegate)
        def update_item_selection(item, is_selected, is_multi_selected):
            # Store current state to see if we actually need to update
            current_is_selected = False
            current_is_multi_selected = False

            if hasattr(item, 'is_selected'): # For TemplateCard
                current_is_selected = item.is_selected()
            if hasattr(item, 'is_multi_selected'): # For TemplateCard
                current_is_multi_selected = item.is_multi_selected()
            
            # For QTableWidgetItems, selection is handled by the view itself, but we might need to
            # trigger a repaint if a custom delegate relies on properties that we might set here.
            # This part primarily targets TemplateCard.

            needs_update = False
            if hasattr(item, 'set_selected') and current_is_selected != is_selected:
                item.set_selected(is_selected)
                needs_update = True
            
            if hasattr(item, 'set_multi_selected') and current_is_multi_selected != is_multi_selected:
                item.set_multi_selected(is_multi_selected)
                needs_update = True
            
            if needs_update and hasattr(item, 'update'):
                item.update() # Trigger repaint for the card

        # Grid View (Template Cards)
        if gallery.template_view_mode == "grid":
            for card in gallery.template_cards:
                if hasattr(card, 'template_data') and isinstance(card.template_data, dict):
                    template_name = card.template_data.get('name')
                    if template_name:
                        is_primary = is_template_selected(template_name, primary_selected)
                        is_multi = is_template_multi_selected(template_name, multi_selected_list)
                        
                        # If it's the primary selection, it shouldn't also be marked as multi-selected visually
                        # (unless the primary is the *only* thing in a multi-select list, which is an edge case)
                        if is_primary and len(multi_selected_list) <= 1:
                            actual_multi_for_card = False
                        else:
                            actual_multi_for_card = is_multi
                            
                        update_item_selection(card, is_primary, actual_multi_for_card)
        
        # List View (QTableView)
        # The QTableView's selection model should ideally be the source of truth when in list view.
        # The GallerySelectionManager should be updated BY the table view's selection changes.
        # And when the manager's state changes (e.g., programmatically), it should SYNC the table view.
        # This method is more about ensuring VISUAL consistency of cards if they were somehow visible
        # or if other UI elements depend on this explicit call.
        # The table view itself uses its selection model to draw selections.
        # However, if we need to force a visual update based on the manager, we might do it here.
        if gallery.template_view_mode == "list" and hasattr(gallery, 'template_table_view'):
            gallery.template_table_view.sync_selection_from_manager(primary_selected, multi_selected_list)
            # The sync_selection_from_manager should handle selecting rows in the table.
            # If a custom delegate for drawing cells needs to know about multi-select beyond the standard
            # QItemSelectionModel, that logic would be in the delegate's paint method, potentially
            # checking properties on the QModelIndex (e.g., set via setData in the model).

    @staticmethod
    def get_templates_in_folder(gallery, folder_name):
        """Get templates associated with a specific folder"""
        if not hasattr(gallery, 'app') or not hasattr(gallery.app, 'template_manager'):
            print("Template manager not available in get_templates_in_folder")
            return []

        template_manager = gallery.app.template_manager
        templates_in_folder = []

        # Check if template_manager has folders attribute and if it's a dictionary
        if not hasattr(template_manager, 'folders') or not isinstance(template_manager.folders, dict):
            print(f"Error: template_manager.folders is not a valid dictionary. Found: {template_manager.folders}")
            # Try to load folders if they seem to be missing or invalid
            if hasattr(template_manager, 'load_folders'):
                print("Attempting to reload folders...")
                template_manager.load_folders()
                # Check again after loading
                if not hasattr(template_manager, 'folders') or not isinstance(template_manager.folders, dict):
                    print("Error: Folders are still invalid after reload.")
                    return [] # Return empty if folders are still not valid
            else:
                return [] # Return empty if cannot load folders

        # Get the list of template names for the given folder
        template_names_in_folder = template_manager.folders.get(folder_name, [])
        # print(f"Template names in folder '{folder_name}': {template_names_in_folder}")

        # Retrieve full template data for each template name
        # Ensure template_manager.templates is a list of dicts
        all_templates = []
        if hasattr(template_manager, 'templates') and isinstance(template_manager.templates, list):
            all_templates = template_manager.templates
        elif hasattr(template_manager, 'templates') and isinstance(template_manager.templates, dict):
            # Convert dict of templates to list of dicts if needed (older format)
            all_templates = list(template_manager.templates.values())
        else:
            print(f"Error: template_manager.templates is not a valid list or dictionary. Found: {template_manager.templates}")
            # Try to load templates if they seem to be missing or invalid
            if hasattr(template_manager, 'load_templates'):
                print("Attempting to reload templates...")
                template_manager.load_templates()
                # Check again after loading
                if hasattr(template_manager, 'templates') and isinstance(template_manager.templates, list):
                    all_templates = template_manager.templates
                elif hasattr(template_manager, 'templates') and isinstance(template_manager.templates, dict):
                    all_templates = list(template_manager.templates.values())
                else:
                    print("Error: Templates are still invalid after reload.")
                    return [] # Return empty if templates are still not valid
            else:
                return [] # Return empty if cannot load templates
        
        # Create a mapping of template names to their data for quick lookup
        name_to_template_map = {t.get('name'): t for t in all_templates if isinstance(t, dict) and t.get('name')}

        for name in template_names_in_folder:
            template_data = name_to_template_map.get(name)
            if template_data:
                templates_in_folder.append(template_data)
            else:
                print(f"Warning: Template '{name}' listed in folder '{folder_name}' but not found in main template list.")
        
        # print(f"Retrieved {len(templates_in_folder)} templates for folder '{folder_name}'")
        return templates_in_folder

    @staticmethod
    def create_template_card(gallery, template_data):
        """Create a template card widget based on the current view mode"""
        from app.ui.gallery.components.template_card import TemplateCard
        
        # Create card for grid view
        template_card = TemplateCard(gallery, template=template_data, app=gallery.app)
        
        # Connect all signals using the common helper
        GalleryTemplatesSetup.connect_template_signals(gallery, template_card, template_data)
        
        return template_card

    @staticmethod
    def set_template_sort(gallery, sort_field):
        """Set the sort field and order for templates"""
        if not hasattr(gallery, 'current_sort_field'):
            gallery.current_sort_field = 'name'
        if not hasattr(gallery, 'current_sort_order'):
            gallery.current_sort_order = 'asc'
        
        # Toggle sort order if same field clicked again
        if gallery.current_sort_field == sort_field:
            gallery.current_sort_order = 'desc' if gallery.current_sort_order == 'asc' else 'asc'
        else:
            # New field, default to ascending
            gallery.current_sort_field = sort_field
            gallery.current_sort_order = 'asc'
        
        print(f"[DEBUG] Setting template sort: Field='{sort_field}', Order='{gallery.current_sort_order}'")
        
        # Critical bug fix: Don't use current_templates_to_display here as it might include ALL templates
        # Instead, refresh the gallery which will apply proper filtering
        
        # We don't need to call populate_gallery with ALL templates here - that's causing the bug
        # where subfolder templates appear after sorting. Just call populate_gallery and it will
        # correctly reapply filtering and sorting.
        gallery.populate_gallery(force_refresh=True)

    @staticmethod
    def clear_selections_with_ui_refresh(gallery):
        """Clears all selections (primary and multi) and ensures UI reflects this.
           Uses GallerySelectionManager.
        """
        if not hasattr(gallery, 'selection_manager'):
            print("[ERROR] clear_selections_with_ui_refresh: gallery has no selection_manager!")
            return

        # print("Clearing all selections via manager and refreshing UI...")
        gallery.selection_manager.clear_all_selections(emit_signal=True)
        
        # The selection_manager.selection_changed signal should trigger 
        # gallery._handle_selection_manager_update, which in turn calls
        # gallery._update_selection_ui() and gallery._update_button_state().
        # So, direct calls to _update_selection_ui or _update_button_state here
        # might be redundant if the signal system is working correctly.
        
        # However, to be absolutely sure the UI is clean, especially if there are edge cases
        # or if the signal isn't processed immediately, a direct call can be a safeguard.
        # Consider if this is needed after testing the signal flow thoroughly.
        # gallery._update_selection_ui() # Potentially redundant
        # gallery._update_button_state()   # Potentially redundant

    # This method might be part of TemplateGallery or a helper class for TableView interactions
    def _handle_list_view_blank_space_click(self, event):
        # This might need adjustment. Clicking blank space in QTableView doesn't typically
        # emit a signal from a specific container widget like the old implementation.
        # We might need to handle clicks on the QTableView's viewport() background.
        
        # Assuming `self` is the TemplateGallery instance
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click was on an item or blank space
            index = self.template_table_view.indexAt(event.pos())
            if not index.isValid(): # Click was on blank space
                self.clear_selections_with_ui_refresh()
                event.accept()
            else:
                event.ignore() # Click was on an item, let default handling proceed

    # Slot for delayed population of list view
    def _delayed_populate_list(self):
        print("Executing delayed list population...")
        
        # Ensure this is the TemplateGallery instance
        gallery = self 
        
        # Get current templates to show (this might need to be fetched again if data changed)
        # This logic assumes `gallery.current_templates_to_display` is up-to-date
        templates_to_show = gallery.current_templates_to_display
        
        # Call the static method to populate the list
        GalleryTemplatesSetup.populate_templates_list(gallery, templates_to_show)
        
        # Adjust column widths after populating
        gallery.template_table_view.resize_columns_to_contents()
        # gallery.template_table_view.adjust_column_widths() # If you have a custom method
        
        # Ensure the view is updated
        gallery.template_table_view.update()
        gallery.template_table_view.viewport().update()
        
        print("Delayed list population complete.")
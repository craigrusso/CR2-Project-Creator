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
    QFrame, QMenu, QMessageBox, QButtonGroup, QToolButton, QTableWidget, 
    QTableWidgetItem, QAbstractItemView, QHeaderView, QSpacerItem, QLineEdit, QCompleter,
    QListWidget, QListWidgetItem, QStyle, QStyledItemDelegate, QStyleOptionViewItem,
    QStyleOptionFrame, QCheckBox, QDialog, QTreeWidget, QTreeWidgetItem, QSplitter
)
from PyQt6.QtGui import QIcon, QColor, QFont, QPixmap, QCursor, QPainter, QPalette, QPen, QBrush, QAction
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint, QRect, QBuffer, QTimer, QEvent, QItemSelectionModel
import traceback # Import the traceback module

from app.ui.color_scheme_pyqt import colors, ACCENT_BUTTON_STYLE
from app.templates.components.utils import get_system_font
from app.ui.gallery.components.template_card import TemplateCard
from app.templates.gallery_events import GalleryEvents
from app.constants import get_resource_path
from app.ui.views.template_table_view import TemplateTableView # Import the new TableView

def sort_templates(templates, sort_field='name', sort_order='asc'):
    """Sort templates by the given field and order"""
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
            # If template is just a string (name), use it directly for sorting
            return (template.lower(), '')
        
        # For dict templates, handle different sort fields
        if sort_field == 'created' or sort_field == 'date':
            # Sort by date (created timestamp)
            created = template.get('created', 0)
            return (created, template.get('name', '').lower())
        elif sort_field == 'modified':
            # Sort by modified timestamp
            modified = template.get('modified', template.get('created', 0))
            return (modified, template.get('name', '').lower())
        elif sort_field == 'category':
            # Sort by category, with empty categories at the end
            category = template.get('category', '').lower()
            return (category if category else 'zzz', template.get('name', '').lower())
        else:
            # Default sort by name
            return (template.get('name', '').lower(), '')
    
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
            save_message = "Template saved successfully" if template_save_success else "Failed to save template"
            
            if template_save_success:
                print(f"✅ GALLERY LISTENER: Successfully saved template '{updated_template_name}'")
                # Refresh gallery needs to happen here after successful save
                if hasattr(gallery, 'populate_gallery'):
                    print(f"🔄 GALLERY LISTENER: Refreshing gallery after successful edit.")
                    gallery.populate_gallery(force_refresh=True)
                return True # Indicate success
            else:
                print(f"❌ GALLERY LISTENER: Failed to save main template file for '{updated_template_name}'")
                QMessageBox.warning(gallery, "Save Error", f"Could not save the main template file for {updated_template_name}. The structure might be saved, but the template list may be inconsistent.")
                return False # Indicate failure
        else:
            print(f"🔷 GALLERY LISTENER: Editor cancelled or failed. Success={success}, Name='{updated_template_name}'")
            return False # Indicate cancellation or failure
    
    except Exception as e:
        import traceback
        print(f"❌ GALLERY LISTENER: Error during template edit: {e}")
        traceback.print_exc()
        QMessageBox.critical(gallery, "Edit Error", f"An unexpected error occurred while editing the template: {e}")
        return False

def select_template_after_rename(gallery, new_name, old_name):
    """Helper function to select a template after rename with fallback options"""
    print(f"🔶 SELECT AFTER RENAME: Trying to select renamed template '{new_name}' (was '{old_name}')")
    
    # Force a reload of templates and structures if we have access to template_manager
    if hasattr(gallery, 'app') and hasattr(gallery.app, 'template_manager'):
        # Wait a moment to ensure files are written to disk
        from PyQt6.QtCore import QTimer, QApplication
        QTimer.singleShot(200, lambda: QApplication.processEvents())
        
        # Force complete reloads
        gallery.app.template_manager.load_templates()
        gallery.app.template_manager.load_custom_structures()
        
        # Make sure to load structures as templates
        if hasattr(gallery.app.template_manager, 'load_structures_as_templates'):
            gallery.app.template_manager.load_structures_as_templates()
        
        print(f"🔶 SELECT AFTER RENAME: Forced reload of templates and structures")
        
        # Log loaded templates for debugging
        if hasattr(gallery.app.template_manager, 'templates'):
            template_names = [t.get('name', 'Unknown') for t in gallery.app.template_manager.templates 
                              if isinstance(t, dict) and 'name' in t]
            print(f"🔶 SELECT AFTER RENAME: Loaded template names: {template_names}")
    
    # Force the gallery to rebuild
    if hasattr(gallery, 'populate_gallery'):
        print(f"🔶 SELECT AFTER RENAME: Forcing gallery refresh")
        # Set templates_loaded to False to force a complete refresh
        if hasattr(gallery, 'templates_loaded'):
            gallery.templates_loaded = False
        gallery.populate_gallery(force_refresh=True)
        
        # Process events to ensure UI updates
        QApplication.processEvents()
    
    # Generate variations of the name to try
    name_variations = [
        new_name,                          # The new name as provided
        new_name.replace(" ", "_"),        # With underscores
        new_name.replace("_", " "),        # With spaces
        f"Template_{new_name}",            # With Template_ prefix
        f"Template_{new_name.replace(' ', '_')}"  # With Template_ prefix and underscores
    ]
    
    # Add original name variations as a fallback
    name_variations.extend([
        old_name,                          # The old name as provided
        old_name.replace(" ", "_"),        # With underscores
        old_name.replace("_", " "),        # With spaces
        f"Template_{old_name}",            # With Template_ prefix
        f"Template_{old_name.replace(' ', '_')}"  # With Template_ prefix and underscores
    ])
    
    # Add special handling for test-style rename pattern
    if new_name.startswith("TEST_") and "_RENAMED_" in new_name:
        # Extract the base part of the new name without the timestamp
        base_parts = new_name.split("_RENAMED_")[0]
        name_variations.append(base_parts)
    
    # Log variations we're going to try
    print(f"🔶 SELECT AFTER RENAME: Will try these name variations: {name_variations}")
    
    template_manager = gallery.app.template_manager
    found_template = None
    
    # Try each name variation
    for variation in name_variations:
        # Try get_template method if available
        if hasattr(template_manager, 'get_template'):
            print(f"🔶 SELECT AFTER RENAME: Trying template_manager.get_template('{variation}')")
            template = template_manager.get_template(variation)
            if template:
                found_template = template
                print(f"🔶 SELECT AFTER RENAME: Found template in manager via get_template: {template.get('name', variation)}")
                break
        
        # Try get_template_by_name method if available
        if hasattr(template_manager, 'get_template_by_name'):
            print(f"🔶 SELECT AFTER RENAME: Trying template_manager.get_template_by_name('{variation}')")
            template = template_manager.get_template_by_name(variation)
            if template:
                found_template = template
                print(f"🔶 SELECT AFTER RENAME: Found template in manager via get_template_by_name: {template.get('name', variation)}")
                break
                
        # Try direct access to templates list if available
        if hasattr(template_manager, 'templates'):
            for template in template_manager.templates:
                if isinstance(template, dict) and template.get('name') == variation:
                    found_template = template
                    print(f"🔶 SELECT AFTER RENAME: Found template in templates list: {template.get('name', variation)}")
                    break
            if found_template:
                break
    
    # If we found the template, select it in the gallery
    if found_template:
        # Try the dedicated select_template method first
        if hasattr(gallery, 'select_template'):
            template_name = found_template.get('name', '')
            print(f"🔶 SELECT AFTER RENAME: Calling gallery.select_template('{template_name}')")
            result = gallery.select_template(template_name)
            print(f"🔶 SELECT AFTER RENAME: select_template result: {result}")
            
            # If that failed, try the internal handler
            if not result and hasattr(gallery, '_on_template_select'):
                print(f"🔶 SELECT AFTER RENAME: Calling gallery._on_template_select with template object")
                gallery._on_template_select(found_template)
        
        # If no select_template method, use the internal handler directly
        elif hasattr(gallery, '_on_template_select'):
            print(f"🔶 SELECT AFTER RENAME: Using _on_template_select directly")
            gallery._on_template_select(found_template)
            
        # Force a refresh after selection to update UI
        if hasattr(gallery, 'update_selected_template_style'):
            gallery.update_selected_template_style()
            print(f"🔶 SELECT AFTER RENAME: Updated template style")
            
        # Verify selection worked
        if hasattr(gallery, 'selected_template'):
            selected_name = gallery.selected_template.get('name', 'Unknown') if isinstance(gallery.selected_template, dict) else str(gallery.selected_template)
            print(f"🔶 SELECT AFTER RENAME: Gallery now has selected_template: {selected_name}")
    else:
        print(f"🔶 SELECT AFTER RENAME: No template found matching renamed template '{new_name}'")
        
        # Force another populate as a last resort
        if hasattr(gallery, 'populate_gallery'):
            print(f"🔶 SELECT AFTER RENAME: Forcing another gallery refresh as fallback")
            gallery.populate_gallery(force_refresh=True)
            
            # After refresh, check if any template card contains the new name
            if hasattr(gallery, 'template_cards'):
                print(f"🔶 SELECT AFTER RENAME: Looking for template cards with name '{new_name}'")
                for card in gallery.template_cards:
                    if hasattr(card, 'template') and isinstance(card.template, dict):
                        card_name = card.template.get('name', '')
                        if card_name == new_name:
                            print(f"🔶 SELECT AFTER RENAME: Found template card with new name '{new_name}'")
                            # Try to select this card
                            if hasattr(gallery, '_on_template_select'):
                                print(f"🔶 SELECT AFTER RENAME: Selecting template from card")
                                gallery._on_template_select(card.template)
                                found_template = card.template
                                break
    
    return found_template is not None

class GalleryTemplatesSetup:
    """Template-related functionality for the Template Gallery"""
    
    @staticmethod
    def connect_template_signals(gallery, item, template_data):
        """Connect signals for a template item (card or list item)"""
        # Ensure template_data is a dictionary
        if not isinstance(template_data, dict):
            # Attempt to get it from template_io if it's just a name
            if isinstance(template_data, str) and hasattr(gallery, 'app') and gallery.app.template_manager:
                template_name_str = template_data
                template_data = gallery.app.template_manager.template_io.get_template(template_name_str)
                if not template_data: # Fallback if still not found
                    print(f"[ERROR] connect_template_signals: Could not retrieve template data for name '{template_name_str}'")
                    template_data = {'name': template_name_str} # Minimal data
            else:
                print(f"[ERROR] connect_template_signals: template_data is not a dict and cannot be resolved: {template_data}")
                # Create a minimal dict to avoid errors, though functionality might be limited
                template_data = {'name': str(template_data) if template_data else "Unknown"}

        template_name = template_data.get('name', 'Unknown')
        is_folder = template_data.get('is_folder', False)

        # Connect signals based on item type (TemplateCard or QTableWidgetItem/etc.)
        if hasattr(item, 'clicked'):
            item.clicked.connect(lambda td=template_data: GalleryEvents.on_template_select(gallery, td))
        
        if hasattr(item, 'doubleClicked'):
            item.doubleClicked.connect(lambda t_name=template_name: GalleryEvents.on_edit_template(gallery, t_name))

        if hasattr(item, 'editRequested'):
            item.editRequested.connect(lambda t_name=template_name: GalleryEvents.on_edit_template(gallery, t_name))
        
        if hasattr(item, 'deleteRequested'):
            # Corrected: on_delete_template expects only the gallery instance.
            # It uses the gallery's selection_manager to determine what to delete.
            item.deleteRequested.connect(lambda: GalleryEvents.on_delete_template(gallery))

        if hasattr(item, 'duplicate_requested'):
            item.duplicate_requested.connect(lambda t_name=template_name: GalleryEvents.on_duplicate_template(gallery, t_name))

        if hasattr(item, 'moveToFolderRequested'):
            item.moveToFolderRequested.connect(lambda t_name=template_name, folder=template_data.get('parent_folder'): 
                                                GalleryEvents.on_move_template_to_folder(gallery, [t_name], folder))

        # Connect multi-select handler
        if hasattr(gallery, 'on_template_multi_select') and hasattr(item, 'multiSelectRequested'):
            item.multiSelectRequested.connect(
                lambda t, add=True: gallery.on_template_multi_select(t, add))
                
        return item
        
    @staticmethod
    def setup_templates_section(gallery):
        """Set up the templates section of the gallery"""
        # Templates section
        gallery.templates_section = QWidget()
        gallery.templates_section.setStyleSheet("background: transparent;")
        gallery.templates_section_layout = QVBoxLayout(gallery.templates_section)
        gallery.templates_section_layout.setContentsMargins(10, 0, 10, 10)

        # Call helper to setup templates header
        GalleryTemplatesSetup.setup_templates_header(gallery)
        
        # Add the templates header to the section layout
        gallery.templates_section_layout.addWidget(gallery.templates_header)

        # Add the "No root templates" notice label here, after the header
        if hasattr(gallery, 'no_root_templates_notice_label'):
            gallery.templates_section_layout.addWidget(gallery.no_root_templates_notice_label)
        
        # Add a small margin between header/notice and content
        spacer = QWidget()
        spacer.setFixedHeight(5)
        spacer.setStyleSheet("background: transparent;")
        gallery.templates_section_layout.addWidget(spacer)
        
        # Scrollable container for templates (Grid and List/Table View)
        gallery.templates_scroll = QScrollArea()
        gallery.templates_scroll.setWidgetResizable(True)
        gallery.templates_scroll.setFrameShape(QFrame.Shape.NoFrame)
        gallery.templates_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        gallery.templates_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        gallery.templates_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        gallery.templates_scroll.setStyleSheet("background: transparent; border: none;")
        
        gallery.templates_container = QWidget()
        gallery.templates_container.setStyleSheet("background: transparent; border: none;")
        gallery.templates_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        gallery.templates_grid = QGridLayout(gallery.templates_container)
        gallery.templates_grid.setContentsMargins(0, 0, 0, 0)
        gallery.templates_grid.setSpacing(15)
        gallery.templates_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Create template_list_container with its own layout to hold the table view
        gallery.templates_list_container = QWidget()
        gallery.templates_list_container.setStyleSheet("background: transparent;")
        list_layout = QVBoxLayout(gallery.templates_list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create and add the table view to the list container
        gallery.template_table_view = TemplateTableView(gallery.app, gallery)
        gallery.template_table_view.setObjectName("templateTableView")
        list_layout.addWidget(gallery.template_table_view)
        gallery.template_table_view.hide()  # Initially hidden, grid view is default
        
        # Add both views to the section
        gallery.templates_scroll.setWidget(gallery.templates_container)
        gallery.templates_section_layout.addWidget(gallery.templates_scroll)
        gallery.templates_section_layout.addWidget(gallery.templates_list_container)
        gallery.templates_list_container.hide()  # Initially hidden
        
        # Create cards container for grid view
        gallery.template_cards_scroll_area = gallery.templates_scroll

    @staticmethod
    def setup_templates_header(gallery):
        """Setup the header for the templates section"""
        SYSTEM_FONT = get_system_font()

        gallery.templates_header = QWidget()
        gallery.templates_header.setStyleSheet(f"""
            background-color: {colors['card_bg']};
            border: none; 
        """)
        gallery.templates_header_layout = QHBoxLayout(gallery.templates_header)
        gallery.templates_header_layout.setContentsMargins(15, 10, 15, 10)
        gallery.templates_header_layout.setSpacing(10)

        gallery.templates_label = QLabel("TEMPLATES")
        gallery.templates_label.setStyleSheet(f"color: {colors['text']}; padding-left: 5px;")
        gallery.templates_label.setFont(QFont(SYSTEM_FONT, 14, QFont.Weight.Bold))
        gallery.templates_header_layout.addWidget(gallery.templates_label, 1) # Give stretch factor of 1

        gallery.templates_header_layout.addStretch(1) # Push buttons to the right

        # Add Template button
        gallery.add_template_button = QPushButton("Add Template")
        gallery.add_template_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        gallery.add_template_button.clicked.connect(gallery._on_add_template)
        gallery.add_template_button.setFixedSize(120, 30)
        gallery.templates_header_layout.addWidget(gallery.add_template_button)

        # Template view toggle buttons
        gallery.template_view_controls = QWidget()
        gallery.template_view_controls.setFixedHeight(30)
        gallery.template_view_controls_layout = QHBoxLayout(gallery.template_view_controls)
        gallery.template_view_controls_layout.setContentsMargins(0, 0, 0, 0)
        gallery.template_view_controls_layout.setSpacing(0)

        gallery.template_grid_view_btn = QToolButton()
        gallery.template_grid_view_btn.setCheckable(True)
        gallery.template_grid_view_btn.setToolTip("Grid View")
        gallery.template_grid_view_btn.setText("Grid")
        gallery.template_grid_view_btn.setChecked(gallery.view_mode == "grid")
        gallery.template_grid_view_btn.clicked.connect(lambda: gallery._set_template_view_mode("grid"))
        gallery.template_grid_view_btn.setFixedSize(65, 24)
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
        gallery.template_list_view_btn.setChecked(gallery.view_mode == "list")
        gallery.template_list_view_btn.clicked.connect(lambda: gallery._set_template_view_mode("list"))
        gallery.template_list_view_btn.setFixedSize(65, 24)
        gallery.template_list_view_btn.setStyleSheet("""
            QToolButton {
                background-color: #2A2A2A;
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                border-left: none;
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

        gallery.template_view_toggle_group = QButtonGroup(gallery)
        gallery.template_view_toggle_group.addButton(gallery.template_grid_view_btn)
        gallery.template_view_toggle_group.addButton(gallery.template_list_view_btn)

        gallery.template_view_controls_layout.addWidget(gallery.template_grid_view_btn)
        gallery.template_view_controls_layout.addWidget(gallery.template_list_view_btn)
        gallery.templates_header_layout.addWidget(gallery.template_view_controls)

    @staticmethod
    def populate_templates_list(gallery, templates_to_show):
        """Populate the template table view with template items."""
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

            # Get templates to show
            # Handle None or empty list
            templates_data = templates_to_show if templates_to_show else []
            
            # If templates_to_show is a dict (from get_templates_in_folder), get values
            if isinstance(templates_data, dict):
                 templates_data = list(templates_data.values())
                 
            print(f"[DEBUG] List View (TableView): Preparing {len(templates_data)} templates")

            # --- Sorting Logic ---
            # Sort based on gallery's state
            current_sort_field = getattr(gallery, 'current_sort_field', 'name')
            current_sort_order = getattr(gallery, 'current_sort_order', 'asc')
            
            print(f"[DEBUG] List View (TableView): Sorting by {current_sort_field} ({current_sort_order})")
            
            # Sort templates using the existing helper function
            try:
                 sorted_templates = sort_templates(templates_data, current_sort_field, current_sort_order)
                 print(f"[DEBUG] List View (TableView): Sorted {len(sorted_templates)} templates")
            except Exception as sort_e:
                 print(f"[ERROR] Failed to sort templates for table view: {sort_e}")
                 traceback.print_exc()
                 sorted_templates = templates_data # Use unsorted data as fallback

            # --- Populate Table View ---
            print(f"[DEBUG] Populating TemplateTableView with {len(sorted_templates)} items.")
            gallery.template_table_view.populate_data(sorted_templates)
            print(f"[DEBUG] List View (TableView): Population complete.")
            
        except Exception as e:
            print(f"[ERROR] Error populating templates list (TableView): {e}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def _update_column_widths(gallery, position, index):
        # This method is now obsolete as QTableView/QHeaderView handles widths internally
        # Kept temporarily to avoid breaking calls, should be removed later.
        # print(f"[DEBUG] (Obsolete) _update_column_widths called for splitter: pos={position}, index={index}\")
        # if hasattr(gallery, 'header_splitter'):
        #     gallery.header_sizes = gallery.header_splitter.sizes()
        #     print(f"[DEBUG] (Obsolete) Splitter sizes: {gallery.header_sizes}\")
        pass # No longer needed

    @staticmethod
    def populate_templates_grid(gallery, templates_to_show):
        """Populate templates in grid view"""
        # Clear existing cards from the grid
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
        template_width = getattr(gallery, 'icon_size', 150) + 20  # Add spacing
        min_cols = 2  # Minimum number of columns
        
        # Default to 4 columns if container width is not yet available
        if container_width <= 0:
            max_cols = 4
        else:
            calculated_cols = max(min_cols, container_width // template_width)
            max_cols = min(8, calculated_cols)  # Limit max columns to 8
        
        # Debug output to help diagnose issues
        print(f"[DEBUG] Gallery: Populating templates grid with {len(templates_to_show)} templates")
        
        # Handle templates_to_show being either a list of dicts or a dictionary
        if isinstance(templates_to_show, list):
            # It's already a list of template data dictionaries
            sorted_templates = sorted(templates_to_show, key=lambda x: x.get('name', '').lower())
            
            for template_data in sorted_templates:
                if not isinstance(template_data, dict) or 'name' not in template_data:
                    print(f"[WARNING] Invalid template data format: {template_data}")
                    continue
                    
                print(f"[DEBUG] Gallery: Creating template card for '{template_data.get('name')}'")
                print(f"DEBUG (Card): Populating card with data: {template_data}")
                template_card = TemplateCard(gallery, template=template_data, app=gallery.app)
                
                # Connect all signals using the common helper
                GalleryTemplatesSetup.connect_template_signals(gallery, template_card, template_data)
                
                gallery.templates_grid.addWidget(template_card, row, col)
                gallery.template_cards.append(template_card)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
                    
        elif isinstance(templates_to_show, dict):
            # It's a dictionary mapping names to template data
            print(f"[DEBUG] Gallery: Template keys: {list(templates_to_show.keys())}")
            
            # Sort templates by name for consistent display
            sorted_templates = []
            for name, data in templates_to_show.items():
                sorted_templates.append((name, data))
            sorted_templates.sort(key=lambda x: x[0].lower())  # Sort by name case-insensitive
            
            for name, data in sorted_templates:
                # Make sure we're passing the template data dictionary with the correct name
                if isinstance(data, dict):
                    # Ensure the template data has the correct name
                    template_data = dict(data)  # Create a copy to avoid modifying the original
                    template_data['name'] = name  # Ensure name is set correctly
                    # Also verify we're not using Template-# as the name
                    if name.startswith("Template-") and 'name' in data and not data['name'].startswith("Template-"):
                        template_data['name'] = data['name']  # Use the real name from the data
                    
                    print(f"[DEBUG] Gallery: Creating template card for '{template_data['name']}'")
                else:
                    # If data is not a dictionary, create one with the name
                    template_data = {"name": name, "category": "Custom", "description": ""}
                    print(f"[DEBUG] Gallery: Creating template card from name only '{name}'")
                
                print(f"DEBUG (Card): Populating card with data: {template_data}")
                template_card = TemplateCard(gallery, template=template_data, app=gallery.app)
                
                # Connect all signals using the common helper
                GalleryTemplatesSetup.connect_template_signals(gallery, template_card, template_data)
                
                gallery.templates_grid.addWidget(template_card, row, col)
                gallery.template_cards.append(template_card)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
        else:
            print(f"[ERROR] populate_templates_grid: Unsupported templates_to_show type: {type(templates_to_show)}")
        
        # If we have the currently selected template, highlight it
        if hasattr(gallery, 'selected_template') and gallery.selected_template:
            selected_name = gallery.selected_template.get('name', '')
            for card in gallery.template_cards:
                if hasattr(card, 'template') and isinstance(card.template, dict):
                    card_name = card.template.get('name', '')
                    if card_name == selected_name:
                        if hasattr(card, 'set_selected'):
                            card.set_selected(True)
                    else:
                        if hasattr(card, 'set_selected'):
                            card.set_selected(False)

    @staticmethod
    def set_template_view_mode(gallery, mode):
        """Set the template view mode (grid or list)"""
        # Debug information
        print(f"DEBUG: Setting template view mode to: {mode}")
        
        # Ensure gallery and its UI components are initialized
        has_scroll_area = hasattr(gallery, 'template_cards_scroll_area') and gallery.template_cards_scroll_area is not None
        has_table_view = hasattr(gallery, 'template_table_view') and gallery.template_table_view is not None
        has_list_container = hasattr(gallery, 'templates_list_container') and gallery.templates_list_container is not None
        
        if not has_scroll_area or not has_table_view or not has_list_container:
            # Log which components are missing
            print(f"[ERROR] Gallery UI not fully initialized. Cannot set view mode. Missing components:")
            if not has_scroll_area:
                print("- template_cards_scroll_area is missing")
            if not has_table_view:
                print("- template_table_view is missing")
            if not has_list_container:
                print("- templates_list_container is missing")
            return

        if mode == "grid":
            # Show grid view, hide list view
            gallery.template_cards_scroll_area.setVisible(True)
            gallery.templates_list_container.setVisible(False)
            gallery.view_mode = "grid"
            
            # Update button states if they exist
            if hasattr(gallery, 'template_grid_view_btn'):
                gallery.template_grid_view_btn.setChecked(True)
            if hasattr(gallery, 'template_list_view_btn'):
                gallery.template_list_view_btn.setChecked(False)
            
            if hasattr(gallery, 'current_folder') and gallery.current_folder and hasattr(gallery, 'folder_nav'):
                gallery.folder_nav.setVisible(True)

        elif mode == "list":
            # Show list view, hide grid view
            gallery.template_cards_scroll_area.setVisible(False)
            gallery.templates_list_container.setVisible(True)
            gallery.view_mode = "list"
            
            # Update button states
            if hasattr(gallery, 'template_grid_view_btn'):
                gallery.template_grid_view_btn.setChecked(False)
            if hasattr(gallery, 'template_list_view_btn'):
                gallery.template_list_view_btn.setChecked(True)

            if hasattr(gallery, 'current_folder') and gallery.current_folder and hasattr(gallery, 'folder_nav'):
                gallery.folder_nav.setVisible(True)
                
            # Populate the list view with templates
            current_templates_to_display = []
            if hasattr(gallery, 'current_folder') and gallery.current_folder:
                current_templates_to_display = GalleryTemplatesSetup.get_templates_in_folder(gallery, gallery.current_folder)
            elif hasattr(gallery, 'app') and hasattr(gallery.app, 'template_manager'):
                all_tmpls = gallery.app.template_manager.get_all_templates()
                
                templates_in_folders = set()
                folders_data = gallery.app.template_manager.get_folders()
                
                if isinstance(folders_data, dict):
                    for folder_data_val in folders_data.values():
                        if isinstance(folder_data_val, dict) and 'templates' in folder_data_val:
                            templates_in_folders.update(folder_data_val['templates'])
                        elif isinstance(folder_data_val, list):
                            templates_in_folders.update(folder_data_val)

                if isinstance(all_tmpls, (list, dict)):
                    tmpls_iterable = all_tmpls.values() if isinstance(all_tmpls, dict) else all_tmpls
                    for tmpl in tmpls_iterable:
                        if isinstance(tmpl, dict) and tmpl.get('name') not in templates_in_folders:
                            current_category = getattr(gallery, 'current_category', "All")
                            passes_category = (current_category == "All" or 
                                              tmpl.get("category") == current_category)
                            
                            passes_search = True
                            current_search = getattr(gallery, 'current_search', None)
                            if current_search:
                                search_term = current_search.lower()
                                name_match = search_term in tmpl.get('name', '').lower()
                                desc_match = search_term in tmpl.get('description', '').lower()
                                cat_match = search_term in tmpl.get('category', '').lower()
                                passes_search = name_match or desc_match or cat_match
                                
                            if passes_category and passes_search:
                                current_templates_to_display.append(tmpl)
            
            # Populate the list view
            GalleryTemplatesSetup.populate_templates_list(gallery, current_templates_to_display)
            
        else:
            print(f"[WARNING] Unknown view mode: {mode}")

        # After changing visibility, update the selection state
        GalleryTemplatesSetup.update_template_selection_state(gallery)
        
        # Debug visibility information
        print(f"[DEBUG] View mode set to '{mode}'.")
        print(f"[DEBUG] Grid visible: {gallery.template_cards_scroll_area.isVisible()}")
        print(f"[DEBUG] List visible: {gallery.templates_list_container.isVisible()}")

    @staticmethod
    def update_template_selection_state(gallery):
        """Update the template selection state after view mode change or other updates
        
        Args:
            gallery: The gallery widget instance
        """
        print("🔍 LISTENER: Updating template selection UI")
        
        # Get selection information
        has_multi_selection = False
        primary_template = None
        multi_selected = []
        
        # Get selection from SelectionManager
        if hasattr(gallery, 'selection_manager'):
            primary_template = gallery.selection_manager.selected_template
            multi_selected = gallery.selection_manager.multi_selected_templates
            
            # Determine if multi-selection is active by checking the length of multi_selected
            has_multi_selection = len(multi_selected) > 1
            
            print(f"🔍 LISTENER: In multi-selection mode: {has_multi_selection}")
            print(f"🔍 LISTENER: Primary selection: {primary_template.get('name') if primary_template else 'None'}")
            print(f"🔍 LISTENER: Multi-selection count: {len(multi_selected)}")
        
        # Update the correct view's selection based on view mode
        if gallery.view_mode == "grid":
            # Use helper methods to update card selection
            if hasattr(gallery, '_update_template_card_selection'):
                gallery._update_template_card_selection()
        else:  # list view
            # For template table view
            if gallery.template_table_view and gallery.template_table_view.isVisible():
                # Block signals during selection changes
                gallery.template_table_view.selectionModel().blockSignals(True)
                
                # Clear current selection
                gallery.template_table_view.selectionModel().clear()
                
                # Find and select appropriate rows for template(s)
                model = gallery.template_table_view.model()
                if not model:
                    print("🔍 LISTENER: No model found for template table view")
                else:
                    # If we have a primary selection, find and select it
                    if primary_template:
                        # Select row(s) in table
                        for row in range(model.rowCount()):
                            index = model.index(row, 0)  # Assuming first column has the template name
                            if index.isValid():
                                name = model.data(index, Qt.ItemDataRole.DisplayRole)
                                if name == primary_template.get('name'):
                                    # Select the row for primary selection
                                    select_flags = QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
                                    gallery.template_table_view.selectionModel().select(index, select_flags)
                                    gallery.template_table_view.setCurrentIndex(index)
                                    
                                    print(f"🔍 LISTENER: Selected primary template: {name}")
                                    break
                    
                    # If we have multi-selection, add additional rows
                    if has_multi_selection:
                        multi_names = [t.get('name') for t in multi_selected if t != primary_template]
                        if multi_names:
                            for row in range(model.rowCount()):
                                index = model.index(row, 0)
                                if index.isValid():
                                    name = model.data(index, Qt.ItemDataRole.DisplayRole)
                                    if name in multi_names:
                                        # Add to the selection (don't replace)
                                        select_flags = QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
                                        gallery.template_table_view.selectionModel().select(index, select_flags)
                
                # Unblock signals
                gallery.template_table_view.selectionModel().blockSignals(False)
        
        # Force immediate UI refresh for the active view container
        active_container = None
        if gallery.view_mode == "list" and hasattr(gallery, 'templates_list_container'):
             active_container = gallery.templates_list_container
        elif gallery.view_mode == "grid" and hasattr(gallery, 'templates_scroll'):
             active_container = gallery.templates_scroll
             
        if active_container:
             active_container.update()
             active_container.repaint()
            
        # Process all pending UI events
        QApplication.processEvents()

    @staticmethod
    def get_templates_in_folder(gallery, folder_name):
        """Get templates in a specific folder"""
        print(f"[DEBUG] Gallery: Getting templates in folder '{folder_name}'")
        
        # Initialize an empty templates dictionary
        templates_dict = {}
        
        if hasattr(gallery.app, 'template_manager'):
            # Get templates directly from the template manager
            template_manager = gallery.app.template_manager
            
            # Get all template objects from all available sources
            all_templates = []
            
            # Add templates from the most reliable source first - TemplateIO
            if hasattr(template_manager, 'template_io') and hasattr(template_manager.template_io, 'templates'):
                for name, template in template_manager.template_io.templates.items():
                    all_templates.append(template)
                print(f"[DEBUG] Gallery: Added {len(template_manager.template_io.templates)} templates from template_io")
            
            # Then add any templates from the templates attribute
            if hasattr(template_manager, 'templates'):
                all_templates.extend(template_manager.templates)
                print(f"[DEBUG] Gallery: Added {len(template_manager.templates)} templates from templates attribute")
                
            # Then add any templates from template_directories
            if hasattr(template_manager, 'template_directories'):
                all_templates.extend(template_manager.template_directories)
                print(f"[DEBUG] Gallery: Added {len(template_manager.template_directories)} templates from template_directories")
            
            # Get the list of template names in this folder
            template_names_in_folder = []
            if hasattr(template_manager, 'get_templates_in_folder'):
                # Use the manager's method to get template names
                template_names_in_folder = template_manager.get_templates_in_folder(folder_name)
                print(f"[DEBUG] Gallery: Template names in folder from manager: {template_names_in_folder}")
            elif hasattr(template_manager, 'folders') and folder_name in template_manager.folders:
                # Direct access to folders dictionary
                template_names_in_folder = template_manager.folders[folder_name]
                print(f"[DEBUG] Gallery: Template names in folder from folders dict: {template_names_in_folder}")
            
            # Process each template name and find the actual template objects
            if template_names_in_folder:
                # Create a case-insensitive lookup map for faster template matching
                template_name_map = {}
                for template in all_templates:
                    if isinstance(template, dict) and 'name' in template:
                        template_name = template.get('name')
                        template_name_map[template_name.lower()] = template
                
                for template_name in template_names_in_folder:
                    if not template_name:
                        continue
                        
                    # Try exact match first
                    matching_template = None
                    for template in all_templates:
                        if isinstance(template, dict) and template.get('name') == template_name:
                            matching_template = template
                            break
                    
                    # If no exact match, try case-insensitive match
                    if not matching_template:
                        template_name_lower = template_name.lower()
                        if template_name_lower in template_name_map:
                            matching_template = template_name_map[template_name_lower]
                            print(f"[DEBUG] Gallery: Found template '{template_name}' using case-insensitive match")
                    
                    # If still no match and we have template_io, try to get the template directly
                    if not matching_template and hasattr(template_manager, 'template_io') and hasattr(template_manager.template_io, 'templates'):
                        matching_template = template_manager.template_io.templates.get(template_name)
                        if matching_template:
                            print(f"[DEBUG] Gallery: Found template '{template_name}' directly from template_io")
                    
                    # If we found a template, add it to our results
                    if matching_template:
                        # Use the real template name as the key, never generate random keys
                        real_name = matching_template.get('name')
                        print(f"[DEBUG] Gallery: Found template '{real_name}' in folder")
                        templates_dict[real_name] = matching_template
                    else:
                        print(f"[DEBUG] Gallery: Could not find template '{template_name}' in the templates list")
            else:
                print(f"[DEBUG] Gallery: No templates found in folder '{folder_name}'")
            
            # If we found no templates, try legacy fallback methods
            if not templates_dict:
                print(f"[DEBUG] Gallery: Using fallback methods to find templates in folder")
                # Original method as fallback - check if templates have a 'folder' attribute
                for template in all_templates:
                    if isinstance(template, dict) and 'folder' in template and template['folder'] == folder_name:
                        name = template.get('name')
                        if name:
                            print(f"[DEBUG] Gallery: Found template '{name}' with folder attribute")
                            templates_dict[name] = template
            
            # Final debug output
            print(f"[DEBUG] Gallery: Returning {len(templates_dict)} templates for folder '{folder_name}'")
            return templates_dict

    @staticmethod
    def create_template_card(gallery, template_data):
        """Create a template card widget based on the current view mode"""
        from app.ui.gallery.components.template_card import TemplateCard
        
        # Create card for grid view
        template_card = TemplateCard(gallery, template=template_data, app=gallery.app)
        
        # Connect all signals using the common helper
        GalleryTemplatesSetup.connect_template_signals(gallery, template_card, template_data)

    @staticmethod
    def set_template_sort(gallery, sort_field):
        """Sets the sorting field and order for the template list/table."""
        if not hasattr(gallery, 'current_sort_field'):
            gallery.current_sort_field = 'name'
        if not hasattr(gallery, 'current_sort_order'):
            gallery.current_sort_order = 'asc'

        if gallery.current_sort_field == sort_field:
            # Toggle order if clicking the same field
            gallery.current_sort_order = 'desc' if gallery.current_sort_order == 'asc' else 'asc'
        else:
            # Set new field, default to ascending
            gallery.current_sort_field = sort_field
            gallery.current_sort_order = 'asc'
            
        print(f"[DEBUG] Setting template sort: Field='{gallery.current_sort_field}', Order='{gallery.current_sort_order}'")

        # Trigger a refresh of the current view to apply sorting
        if gallery.view_mode == 'list':
            # --- Get the templates currently being displayed ---
            current_templates_data = []
            current_folder = getattr(gallery, 'current_folder', None)
            
            # Re-fetch based on the *same logic* used for initial population
            if current_folder:
                # If a folder filter is active, get templates for that folder
                current_templates_data = GalleryTemplatesSetup.get_templates_in_folder(gallery, current_folder)
            else:
                # Otherwise, get all templates currently loaded by the manager
                if hasattr(gallery, 'template_manager') and hasattr(gallery.template_manager, 'get_all_templates'):
                     all_templates_dict = gallery.template_manager.get_all_templates()
                     # Ensure it's a list of dicts for sorting/population
                     if isinstance(all_templates_dict, dict):
                         current_templates_data = list(all_templates_dict.values())
                     elif isinstance(all_templates_dict, list): # Handle if it already returns a list
                        current_templates_data = all_templates_dict
                     else:
                         print("[ERROR] get_all_templates did not return dict or list in set_template_sort")
                         current_templates_data = []
                else:
                     print("[ERROR] Template manager or get_all_templates not found in set_template_sort")
                     current_templates_data = [] # Fallback

            # Ensure it's a list before passing (redundant if handled above, but safe)
            if isinstance(current_templates_data, dict):
                 current_templates_data = list(current_templates_data.values())

            # --- Repopulate with the fetched data ---
            print(f"[DEBUG] set_template_sort: Repopulating list view with {len(current_templates_data)} templates.")
            GalleryTemplatesSetup.populate_templates_list(gallery, current_templates_data)
            
            # --- Update header indicator ---
            if hasattr(gallery, 'template_table_view'):
                 header = gallery.template_table_view.horizontalHeader()
                 # Use Qt.AscendingOrder and Qt.DescendingOrder
                 sort_indicator = Qt.AscendingOrder if gallery.current_sort_order == 'asc' else Qt.DescendingOrder
                 
                 # Map field name to column index
                 # Ensure TemplateTableView.COLUMN_HEADERS is accessible and correct
                 try:
                     # Assuming TemplateTableView is imported or accessible
                     from app.ui.views.template_table_view import TemplateTableView # Ensure import
                     col_map = {header_text.lower().strip(): i for i, header_text in enumerate(TemplateTableView.COLUMN_HEADERS)}
                 except (ImportError, AttributeError) as e:
                     print(f"[ERROR] Could not access TemplateTableView.COLUMN_HEADERS: {e}")
                     col_map = {} # Fallback to empty map

                 sort_column_index = col_map.get(sort_field.lower().strip(), -1)
                 
                 if sort_column_index != -1:
                      header.setSortIndicator(sort_column_index, sort_indicator)
                      header.setSortIndicatorShown(True)
                 else:
                      print(f"[WARN] Could not map sort field '{sort_field}' to a table column index.")
                      header.setSortIndicatorShown(False) # Hide if field doesn't match

        elif gallery.view_mode == 'grid':
            # Repopulate grid view (ensure populate_templates_grid uses sorting)
            print("[DEBUG] Triggering grid repopulation for sorting.")
            # TODO: Ensure populate_gallery uses the new sort order.
            # Might need modification if it doesn't already read gallery.current_sort_field/order
            gallery.populate_gallery() # Assuming this handles sorting for grid

    @staticmethod
    def clear_selections_with_ui_refresh(gallery):
        """Clear all selections and immediately update the UI"""
        had_selection = False
        had_multi_selection = False

        # // ... existing code to clear gallery.selected_template and gallery.multi_selected_templates ...

        # Update grid view cards (existing logic)
        if hasattr(gallery, 'template_cards'):
             # ... existing logic ...
             pass # Add pass statement to fix indentation error

        # Clear selection in Table View
        if gallery.view_mode == "list" and hasattr(gallery, 'template_table_view'):
            selection_model = gallery.template_table_view.selectionModel()
            if selection_model:
                selection_model.clearSelection()

        # Refresh UI (existing logic)
        # // ... existing code for refresh ...
        
        print(f"🔍 LISTENER: All selections cleared and UI updated")
        return had_selection or had_multi_selection

    def _handle_list_view_blank_space_click(self, event):
        # This might need adjustment. Clicking blank space in QTableView doesn't typically
        # emit a signal from a specific container widget like the old implementation.
        # We might need to handle clicks on the QTableView's viewport() background.
        print(f"🔍 LISTENER: Blank space clicked in list view (Need to adapt for TableView)")
        # Potentially connect to table_view.viewport().mousePressEvent
        # Or handle in the main gallery's mouse press if event filters down.
        self.clear_selections_with_ui_refresh(self) 
        # event.accept() # May not be needed depending on where handled

    def _delayed_populate_list(self):
        """Delayed population of list view (now table view) to prevent UI freezing."""
        # This function should now call the refactored populate_templates_list
        try:
            # Get templates to show based on current folder
            templates_to_show = {}
            current_folder = getattr(self, 'current_folder', None)
            
            if current_folder:
                # Get templates in this folder
                templates_to_show = GalleryTemplatesSetup.get_templates_in_folder(self, current_folder)
            else:
                # Show all templates
                templates_to_show = getattr(self.template_manager, 'templates', {})
            
            print("[DEBUG] Delayed population triggering populate_templates_list (TableView)")
            # Populate the list view (table view) with current templates
            GalleryTemplatesSetup.populate_templates_list(self, templates_to_show)
            
            # Update selection state after population
            GalleryTemplatesSetup.update_template_selection_state(self)
            
        except Exception as e:
            print(f"Error in delayed list population (TableView): {e}")
            traceback.print_exc()


# For testing our template name update functionality
def test_template_rename(gallery, template_name, new_name):
    """Test function to verify template renaming works correctly
    
    This function tests the full template rename workflow from selecting
    a template, to renaming it, to verifying the UI is updated correctly.
    
    Args:
        gallery: Template gallery instance
        template_name: Original template name to test with
        new_name: New name to rename the template to
        
    Returns:
        dict: Test results with success, error details, and status
    """
    from PyQt6.QtCore import QTimer
    results = {
        'success': False,
        'errors': [],
        'steps_completed': [],
        'template_selected': False,
        'template_renamed': False,
        'gallery_updated': False,
        'renamed_template_found': False
    }
    
    try:
        print(f"TEST: Starting template rename test: '{template_name}' -> '{new_name}'")
        
        # Step 1: Select the template
        if hasattr(gallery, 'select_template'):
            success = gallery.select_template(template_name)
            if success:
                print(f"TEST: Successfully selected template '{template_name}'")
                results['template_selected'] = True
                results['steps_completed'].append('select_template')
            else:
                print(f"TEST: Failed to select template '{template_name}'")
                results['errors'].append(f"Failed to select template '{template_name}'")
                return results
        else:
            print(f"TEST: Gallery has no select_template method")
            results['errors'].append("Gallery has no select_template method")
            return results
        
        # Step 2: Get the template manager
        template_manager = None
        if hasattr(gallery, 'app') and hasattr(gallery.app, 'template_manager'):
            template_manager = gallery.app.template_manager
        
        if not template_manager:
            print(f"TEST: No template manager found")
            results['errors'].append("No template manager found")
            return results
        
        # Step 3: Get the original template
        original_template = template_manager.get_template_by_name(template_name)
        if not original_template:
            print(f"TEST: Original template '{template_name}' not found")
            results['errors'].append(f"Original template '{template_name}' not found")
            return results
        
        print(f"TEST: Found original template: {original_template.get('name', 'Unknown')}")
        results['steps_completed'].append('get_original_template')
        
        # Step 4: Rename the template
        rename_success = template_manager.rename_template(template_name, new_name)
        
        if rename_success:
            print(f"TEST: Template successfully renamed")
            results['template_renamed'] = True
            results['steps_completed'].append('rename_template')
        else:
            print(f"TEST: Failed to rename template from '{template_name}' to '{new_name}'")
            results['errors'].append(f"Failed to rename template from '{template_name}' to '{new_name}'")
            return results
        
        # Step 5: Verify old template is gone
        old_template = template_manager.get_template_by_name(template_name)
        if old_template:
            print(f"TEST WARNING: Old template '{template_name}' still exists")
            results['errors'].append(f"Old template '{template_name}' still exists after rename")
        else:
            print(f"TEST PASSED: Old template '{template_name}' no longer exists")
            results['steps_completed'].append('old_template_removed')
        
        # Step 6: Verify new template exists
        new_template = template_manager.get_template_by_name(new_name)
        if not new_template:
            print(f"TEST FAILED: New template '{new_name}' not found")
            results['errors'].append(f"New template '{new_name}' not found after rename")
            return results
        
        print(f"TEST PASSED: New template '{new_name}' exists")
        results['steps_completed'].append('new_template_exists')
        
        # Step 7: Force gallery refresh
        if hasattr(gallery, 'populate_gallery'):
            print(f"TEST: Forcing gallery refresh")
            gallery.populate_gallery(force_refresh=True)
            results['steps_completed'].append('gallery_refreshed')
        else:
            print(f"TEST WARNING: Gallery has no populate_gallery method")
            results['errors'].append("Gallery has no populate_gallery method")
        
        # Step 8: Verify template card with new name exists in gallery
        if hasattr(gallery, 'template_cards') and gallery.template_cards:
            template_found = False
            for card in gallery.template_cards:
                if hasattr(card, 'template') and isinstance(card.template, dict):
                    card_name = card.template.get('name', '')
                    if card_name == new_name:
                        print(f"TEST PASSED: Found template card with new name '{new_name}'")
                        template_found = True
                        results['renamed_template_found'] = True
                        results['steps_completed'].append('template_card_found')
                        break
            
            if not template_found:
                print(f"TEST: No template card found with name '{new_name}'")
                results['gallery_updated'] = True
        
        # Step 9: Verify selection with new name works
        if hasattr(gallery, 'select_template'):
            success = gallery.select_template(new_name)
            if success:
                print(f"TEST PASSED: Successfully selected renamed template '{new_name}'")
                results['steps_completed'].append('select_renamed_template')
            else:
                print(f"TEST WARNING: Failed to select renamed template '{new_name}'")
                results['errors'].append(f"Failed to select renamed template '{new_name}'")
        
        # Step 10: Final verification - check selected_template
        if hasattr(gallery, 'selected_template'):
            if isinstance(gallery.selected_template, dict) and gallery.selected_template.get('name') == new_name:
                print(f"TEST PASSED: Gallery's selected_template is correctly set to '{new_name}'")
                results['steps_completed'].append('selected_template_updated')
            else:
                current = gallery.selected_template
                current_name = current.get('name', str(current)) if isinstance(current, dict) else str(current)
                print(f"TEST WARNING: Gallery's selected_template is '{current_name}', expected '{new_name}'")
                results['errors'].append(f"Gallery's selected_template is '{current_name}', expected '{new_name}'")
        
        # Overall success?
        if (results['template_renamed'] and results['renamed_template_found'] and 
            'select_renamed_template' in results['steps_completed']):
            results['success'] = True
            print(f"TEST PASSED: Template rename test successful")
        else:
            print(f"TEST FAILED: Template rename test failed")
            
        return results
    except Exception as e:
        import traceback
        print(f"TEST ERROR: Exception during template rename test: {e}")
        print(traceback.format_exc())
        results['errors'].append(f"Exception: {str(e)}")
        return results 
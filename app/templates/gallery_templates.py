#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template gallery and associated UI components
"""

import os
import time
import re
import copy
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QGridLayout, 
    QLabel, QPushButton, QComboBox, QSizePolicy, QApplication,
    QFrame, QMenu, QMessageBox, QAction, QButtonGroup, QToolButton, QTableWidget, 
    QTableWidgetItem, QAbstractItemView, QHeaderView
)
from PyQt5.QtGui import QIcon, QColor, QFont, QPixmap, QCursor, QPainter, QPalette
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint, QRect, QBuffer, QTimer

from app.ui.color_scheme_pyqt import colors
from app.ui.app_theme_pyqt import ACCENT_BUTTON_STYLE, BUTTON_STYLE
from .components.utils import SYSTEM_FONT
from .components.template_card import TemplateCard, TemplateListItem
from .gallery_events import GalleryEvents
from app.templates.components.template_list_item import TemplateListItem

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
            return template.lower()
        elif sort_field == 'date' or sort_field == 'created':
            # Sort by date (created or modified)
            date_value = template.get('date_modified', template.get('created', ''))
            return (date_value, template.get('name', '').lower())
        elif sort_field == 'category':
            # Sort by category
            return (template.get('category', '').lower(), template.get('name', '').lower())
        else:
            # Default sort by name
            return template.get('name', '').lower()
    
    return sorted(template_list, key=sort_key, reverse=reverse)

def handle_template_edit(gallery, template_name):
    """
    Handle template editing bypassing gallery._on_edit_template to avoid None issues.
    This function is called from the template double-click and edit actions.
    """
    try:
        print(f"Direct edit of template: {template_name}")
        # Import the dialog directly
        from app.dialogs.dialog_windows_pyqt import show_edit_template
        
        # Get the template directly from the app's template manager
        if hasattr(gallery, 'app') and hasattr(gallery.app, 'template_manager'):
            template_manager = gallery.app.template_manager
            template = template_manager.get_template_by_name(template_name)
            if template:
                # Open the template editor directly
                show_edit_template(gallery, template, lambda t: template_manager.update_template(t))
                gallery.populate_gallery()
                return
        
        print(f"Could not edit template {template_name}: app or template_manager not available")
    except Exception as e:
        import traceback
        print(f"Error in direct template edit: {e}")
        print(traceback.format_exc())

class GalleryTemplatesSetup:
    """Template-related functionality for the Template Gallery"""
    
    @staticmethod
    def connect_template_signals(gallery, item, template_data):
        """Connect signals consistently for both grid and list view items"""
        template_name = template_data.get('name', '') if isinstance(template_data, dict) else str(template_data)
        
        # Connect click handler for selection
        if hasattr(gallery, '_on_template_select') and hasattr(item, 'clicked'):
            item.clicked.connect(lambda checked=False, t=template_data: gallery._on_template_select(t))
        
        # Connect double-click handler for editing
        if hasattr(item, 'doubleClicked'):
            item.doubleClicked.connect(lambda t_name=template_name: handle_template_edit(gallery, t_name))
        
        # Connect context menu actions
        if hasattr(item, 'editRequested'):
            item.editRequested.connect(lambda t_name=template_name: handle_template_edit(gallery, t_name))
        
        if hasattr(item, 'deleteRequested'):
            item.deleteRequested.connect(lambda t_name=template_name: 
                GalleryEvents.on_delete_template(gallery, t_name))
        
        # Connect move to folder signal
        if hasattr(item, 'moveToFolderRequested'):
            item.moveToFolderRequested.connect(lambda t_name, folder_name: 
                GalleryEvents.on_move_template_to_folder(gallery, t_name, folder_name))
        
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
        gallery.templates_section_layout.setContentsMargins(15, 0, 15, 15)  # Add padding on sides for consistent layout
        gallery.templates_section_layout.setSpacing(5)
        
        # Configure size policy to allow expansion to fill available space
        gallery.templates_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Templates header with view controls
        GalleryTemplatesSetup.setup_templates_header(gallery)
        
        # Add a small margin between header and content
        spacer = QWidget()
        spacer.setFixedHeight(5)
        spacer.setStyleSheet("background: transparent;")
        gallery.templates_section_layout.addWidget(spacer)
        
        # Scrollable area for templates
        gallery.templates_scroll = QScrollArea()
        gallery.templates_scroll.setWidgetResizable(True)
        gallery.templates_scroll.setFrameShape(QFrame.NoFrame)
        gallery.templates_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        gallery.templates_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        gallery.templates_scroll.setStyleSheet("background: transparent; border: none;")
        
        # Configure scroll area to expand horizontally and vertically
        gallery.templates_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Container for templates
        gallery.templates_container = QWidget()
        gallery.templates_container.setStyleSheet("background: transparent;")
        
        # Configure container to expand horizontally
        gallery.templates_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Use a grid layout for flexible positioning
        gallery.templates_grid = QGridLayout(gallery.templates_container)
        gallery.templates_grid.setContentsMargins(0, 0, 0, 0)
        gallery.templates_grid.setHorizontalSpacing(6)
        gallery.templates_grid.setVerticalSpacing(12)
        gallery.templates_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        # Set the templates container as the widget for the scroll area
        gallery.templates_scroll.setWidget(gallery.templates_container)
        
        # Add the scroll area to the templates section layout
        gallery.templates_section_layout.addWidget(gallery.templates_scroll)
        
        # List view widget - will be initialized when switching to list view
        gallery.templates_list_widget = QScrollArea()
        gallery.templates_list_widget.setWidgetResizable(True)
        gallery.templates_list_widget.setFrameShape(QFrame.NoFrame)
        gallery.templates_list_widget.setStyleSheet("background: transparent; border: none;")
        gallery.templates_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        gallery.templates_section_layout.addWidget(gallery.templates_list_widget)
        
        # Initially hide the list widget (default to grid view)
        gallery.templates_list_widget.setVisible(False)
    
    @staticmethod
    def setup_templates_header(gallery):
        """Set up the templates header with view controls"""
        # Templates header with view controls
        gallery.templates_header_container = QWidget()
        # Apply a subtle background to the header that spans the full width
        gallery.templates_header_container.setStyleSheet(f"""
            background-color: {colors['card_bg']};
            border: none;
        """)
        gallery.templates_header_container.setFixedHeight(50)  # Slightly taller for better proportions
        gallery.templates_header_layout = QHBoxLayout(gallery.templates_header_container)
        gallery.templates_header_layout.setContentsMargins(15, 10, 15, 10)  # Increase padding for better spacing
        gallery.templates_header_layout.setSpacing(10)
        
        # Template title - should stretch
        gallery.templates_header = QLabel("Templates")
        gallery.templates_header.setFont(QFont(SYSTEM_FONT, 14, QFont.Bold))
        gallery.templates_header.setStyleSheet(f"color: {colors['text']}; padding: 5px 0; background-color: transparent;")
        gallery.templates_header.setAlignment(Qt.AlignLeft)
        gallery.templates_header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        gallery.templates_header_layout.addWidget(gallery.templates_header, 1)  # Give stretch factor of 1
        
        # Add template button - fixed size, right aligned
        gallery.add_button = QPushButton("Add Template")
        gallery.add_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        gallery.add_button.clicked.connect(gallery._on_add_template)
        gallery.add_button.setFixedSize(120, 30)
        gallery.templates_header_layout.addWidget(gallery.add_button)
        
        # Add structure editor button - fixed size, right aligned
        gallery.new_structure_button = QPushButton("Add | Edit Structures")
        gallery.new_structure_button.setStyleSheet(BUTTON_STYLE)
        gallery.new_structure_button.setFixedSize(180, 30)
        gallery.templates_header_layout.addWidget(gallery.new_structure_button)
        
        # Template view toggle buttons - fixed size, right aligned
        gallery.template_view_controls = QWidget()
        gallery.template_view_controls.setFixedHeight(30)
        gallery.template_view_controls_layout = QHBoxLayout(gallery.template_view_controls)
        gallery.template_view_controls_layout.setContentsMargins(0, 0, 0, 0)
        gallery.template_view_controls_layout.setSpacing(0)
        
        # Grid view button
        gallery.template_grid_view_btn = QToolButton()
        gallery.template_grid_view_btn.setCheckable(True)
        gallery.template_grid_view_btn.setToolTip("Grid View")
        gallery.template_grid_view_btn.setText("Grid")
        gallery.template_grid_view_btn.setChecked(gallery.template_view_mode == "grid")
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
        
        # List view button
        gallery.template_list_view_btn = QToolButton()
        gallery.template_list_view_btn.setCheckable(True)
        gallery.template_list_view_btn.setToolTip("List View")
        gallery.template_list_view_btn.setText("List")
        gallery.template_list_view_btn.setChecked(gallery.template_view_mode == "list")
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
        
        # Create button group to manage toggle buttons
        gallery.template_view_toggle_group = QButtonGroup(gallery)
        gallery.template_view_toggle_group.addButton(gallery.template_grid_view_btn)
        gallery.template_view_toggle_group.addButton(gallery.template_list_view_btn)
        
        # Add buttons to layout
        gallery.template_view_controls_layout.addWidget(gallery.template_grid_view_btn)
        gallery.template_view_controls_layout.addWidget(gallery.template_list_view_btn)
        
        # Add the view controls widget to the header layout
        gallery.templates_header_layout.addWidget(gallery.template_view_controls)
        
        # Add header container to section layout
        gallery.templates_section_layout.addWidget(gallery.templates_header_container)

    @staticmethod
    def populate_templates_list(gallery, templates_to_show):
        """Populate the templates list with template items from the given templates list"""
        print(f"[DEBUG] List View: Starting population")
        
        try:
            # Clear existing items and widget if it exists
            if hasattr(gallery, 'template_item_map'):
                gallery.template_item_map.clear()
            if hasattr(gallery, 'templates_list_widget') and gallery.templates_list_widget:
                if gallery.templates_list_widget.widget():
                    old_widget = gallery.templates_list_widget.takeWidget()
                    if old_widget:
                        old_widget.setParent(None)
                        old_widget.deleteLater()
                
            # Create a new container widget and layout for the entire list view
            container = ListViewContainer(gallery)
            main_layout = QVBoxLayout(container)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(5)
            
            # Create a header row with sortable columns
            header_container = QWidget()
            header_container.setFixedHeight(30)
            header_container.setStyleSheet(f"""
                background-color: {colors['card_bg']};
                border-bottom: 1px solid {colors['border']};
            """)
            header_layout = QHBoxLayout(header_container)
            header_layout.setContentsMargins(10, 5, 10, 5)
            header_layout.setSpacing(5)
            
            # Determine sort indicators
            name_sort_indicator = ""
            created_sort_indicator = ""
            modified_sort_indicator = ""
            
            if hasattr(gallery, 'current_sort_field') and hasattr(gallery, 'current_sort_order'):
                sort_arrow = "▼" if gallery.current_sort_order == "desc" else "▲"
                
                if gallery.current_sort_field == "name":
                    name_sort_indicator = f" {sort_arrow}"
                elif gallery.current_sort_field == "created":
                    created_sort_indicator = f" {sort_arrow}"
                elif gallery.current_sort_field == "modified":
                    modified_sort_indicator = f" {sort_arrow}"
            
            # Column headers with click-to-sort functionality
            name_header = QLabel(f"Name{name_sort_indicator}")
            name_header.setStyleSheet(f"font-weight: bold; color: {'#4A86E8' if name_sort_indicator else colors['text']};")
            name_header.setCursor(Qt.PointingHandCursor)
            name_header.mousePressEvent = lambda e: GalleryTemplatesSetup.set_template_sort(gallery, 'name')
            header_layout.addWidget(name_header)
            
            # Add spacer
            header_layout.addStretch(1)
            
            # Created date header
            created_header = QLabel(f"Created{created_sort_indicator}")
            created_header.setStyleSheet(f"font-weight: bold; color: {'#4A86E8' if created_sort_indicator else colors['text']};")
            created_header.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            created_header.setFixedWidth(130)
            created_header.setCursor(Qt.PointingHandCursor)
            created_header.mousePressEvent = lambda e: GalleryTemplatesSetup.set_template_sort(gallery, 'created')
            header_layout.addWidget(created_header)
            
            # Modified date header
            modified_header = QLabel(f"Modified{modified_sort_indicator}")
            modified_header.setStyleSheet(f"font-weight: bold; color: {'#4A86E8' if modified_sort_indicator else colors['text']};")
            modified_header.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            modified_header.setFixedWidth(130)
            modified_header.setCursor(Qt.PointingHandCursor)
            modified_header.mousePressEvent = lambda e: GalleryTemplatesSetup.set_template_sort(gallery, 'modified')
            header_layout.addWidget(modified_header)
            
            # Add header to main layout
            main_layout.addWidget(header_container)
            
            # Create items container
            items_container = QWidget()
            items_container.setObjectName("ItemsContainer")
            gallery.list_container_layout = QVBoxLayout(items_container)
            gallery.list_container_layout.setContentsMargins(0, 0, 0, 0)
            gallery.list_container_layout.setSpacing(1)  # Minimal spacing between items
            
            # Get templates to show
            templates = templates_to_show if templates_to_show else []
            print(f"[DEBUG] List View: Working with {len(templates)} templates")
            
            # Initialize/clear template item map
            if not hasattr(gallery, 'template_item_map'):
                gallery.template_item_map = {}
            else:
                gallery.template_item_map.clear()
            
            # Default sort by name
            if not hasattr(gallery, 'current_sort_field'):
                gallery.current_sort_field = 'name'
            if not hasattr(gallery, 'current_sort_order'):
                gallery.current_sort_order = 'asc'
            
            print(f"[DEBUG] List View: Current sort - {gallery.current_sort_field} ({gallery.current_sort_order})")
            
            # Sort templates
            sorted_templates = sort_templates(templates, gallery.current_sort_field, gallery.current_sort_order)
            print(f"[DEBUG] List View: Sorted {len(sorted_templates)} templates")
            
            # Temporarily block signals to prevent recursive updates
            gallery.templates_list_widget.blockSignals(True)
            
            # Create a template list item for each template
            for i, template in enumerate(sorted_templates):
                # Handle both string templates and dictionary templates
                if isinstance(template, str):
                    template_name = template
                    template_data = {"name": template_name}
                    print(f"[DEBUG] List View: Creating item {i+1} - {template_name}")
                else:
                    template_name = template.get('name', 'Unknown')
                    template_data = template
                    print(f"[DEBUG] List View: Creating item {i+1} - {template_name}")
                
                list_item = TemplateListItem(template_data, gallery=gallery, row_index=i)
                
                # Connect all signals using the common helper
                GalleryTemplatesSetup.connect_template_signals(gallery, list_item, template_data)
                
                # Store in template item map for later access
                gallery.template_item_map[template_name] = list_item
                
                # Set initial selection state
                if hasattr(gallery, 'selected_template') and gallery.selected_template:
                    selected_name = gallery.selected_template.get('name', '') if isinstance(gallery.selected_template, dict) else gallery.selected_template
                    if selected_name == template_name:
                        list_item.setSelected(True)
                        print(f"[DEBUG] Setting {template_name} as initially selected")
                
                # Set initial multi-selection state
                if hasattr(gallery, 'multi_selected_templates') and gallery.multi_selected_templates:
                    for sel_template in gallery.multi_selected_templates:
                        sel_name = sel_template.get('name', '') if isinstance(sel_template, dict) else sel_template
                        if sel_name == template_name:
                            list_item.setMultiSelected(True)
                            print(f"[DEBUG] Setting {template_name} as initially multi-selected")
                            break
                
                # Add to layout
                gallery.list_container_layout.addWidget(list_item)
            
            # Set stretch factor to push items to the top
            gallery.list_container_layout.addStretch()
            
            # Add the items container to the main layout
            main_layout.addWidget(items_container)
            
            # Set the container as the widget for the templates list
            gallery.templates_list_widget.setWidget(container)
            
            # Unblock signals after setting up the widget
            gallery.templates_list_widget.blockSignals(False)
            
            # Do a single update for the container
            container.update()
            
            print(f"[DEBUG] List View: Added main container to list view")
            
        except Exception as e:
            import traceback
            print(f"Error populating templates list: {e}")
            traceback.print_exc()

    @staticmethod
    def populate_templates_grid(gallery, templates_to_show):
        """Populate templates in grid view"""
        gallery.template_cards = []
        
        # Grid layout parameters
        col = 0
        row = 0
        
        # Calculate max columns based on container width
        container_width = gallery.templates_container.width()
        template_width = 150  # Template card width + spacing
        min_cols = 2  # Minimum number of columns
        
        # Default to 4 columns if container width is not yet available
        if container_width <= 0:
            max_cols = 4
        else:
            calculated_cols = max(min_cols, container_width // template_width)
            max_cols = min(8, calculated_cols)  # Limit max columns to 8
        
        # Debug output to help diagnose issues
        print(f"[DEBUG] Gallery: Populating templates grid with {len(templates_to_show)} templates")
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
            
            template_card = TemplateCard(gallery, template=template_data, app=gallery.app)
            
            # Connect all signals using the common helper
            GalleryTemplatesSetup.connect_template_signals(gallery, template_card, template_data)
            
            gallery.templates_grid.addWidget(template_card, row, col)
            gallery.template_cards.append(template_card)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
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
        if mode != gallery.template_view_mode:
            # Update button states
            gallery.template_grid_view_btn.setChecked(mode == "grid")
            gallery.template_list_view_btn.setChecked(mode == "list")
            
            # Store the new mode
            gallery.template_view_mode = mode
            
            # Show the appropriate view
            if mode == "grid":
                # Show grid view
                gallery.templates_scroll.setVisible(True)
                gallery.templates_list_widget.setVisible(False)
                
                # Force refresh if the grid is empty
                if not hasattr(gallery, 'template_cards') or not gallery.template_cards:
                    gallery.populate_gallery()
            else:
                # Show list view
                gallery.templates_scroll.setVisible(False)
                gallery.templates_list_widget.setVisible(True)
                
                # Show loading indicator
                # TODO: Add loading indicator
                
                # Safely clear the list widget
                if hasattr(gallery, 'templates_list_widget') and gallery.templates_list_widget:
                    if gallery.templates_list_widget.widget():
                        old_widget = gallery.templates_list_widget.takeWidget()
                        if old_widget:
                            old_widget.deleteLater()
                
                # Clear list items to avoid stale references
                if hasattr(gallery, 'template_item_map'):
                    gallery.template_item_map.clear()
                
                # Block signals during populate to prevent recursive updates
                gallery.templates_list_widget.blockSignals(True)
                
                # Create and schedule a delayed population function
                def delayed_populate():
                    try:
                        # Get templates to show based on current folder
                        templates_to_show = {}
                        current_folder = gallery.current_folder if hasattr(gallery, 'current_folder') else None
                        
                        if current_folder:
                            # Get templates in this folder
                            templates_to_show = GalleryTemplatesSetup.get_templates_in_folder(gallery, current_folder)
                        else:
                            # Show all templates
                            templates_to_show = gallery.template_manager.templates if hasattr(gallery, 'template_manager') and hasattr(gallery.template_manager, 'templates') else {}
                        
                        # Populate the list view with current templates
                        GalleryTemplatesSetup.populate_templates_list(gallery, templates_to_show)
                        
                        # Unblock signals after population is complete
                        gallery.templates_list_widget.blockSignals(False)
                        
                        # Update selection state after population
                        GalleryTemplatesSetup.update_template_selection_state(gallery)
                        
                    except Exception as e:
                        import traceback
                        print(f"Error in delayed list population: {e}")
                        traceback.print_exc()
                        
                        # Make sure signals are unblocked even on error
                        if hasattr(gallery, 'templates_list_widget'):
                            gallery.templates_list_widget.blockSignals(False)
                
                # Schedule the delayed population
                QTimer.singleShot(50, delayed_populate)
            
            # Save preference
            if hasattr(gallery, 'app') and hasattr(gallery.app, 'preferences'):
                gallery.app.preferences.set('template_view_mode', mode)
            
            # Update the UI to reflect selection state
            GalleryTemplatesSetup.update_template_selection_state(gallery)
            
            print(f"🔍 LISTENER: Switched to {mode} view, preserved selection state")
            if gallery.selected_template:
                print(f"🔍 LISTENER: Preserved primary selection: {gallery.selected_template}")
            if gallery.multi_selected_templates:
                print(f"🔍 LISTENER: Preserved multi-selection count: {len(gallery.multi_selected_templates)}")

    @staticmethod
    def update_template_selection_state(gallery):
        """Update the selection state of all templates in the gallery"""
        print(f"🔍 LISTENER: Updating template selection UI")
        
        # Debug output
        print(f"🔍 LISTENER: In multi-selection mode: {hasattr(gallery, 'is_multi_selecting') and gallery.is_multi_selecting}")
        print(f"🔍 LISTENER: Primary selection: {gallery.selected_template if hasattr(gallery, 'selected_template') else None}")
        print(f"🔍 LISTENER: Multi-selection count: {len(gallery.multi_selected_templates) if hasattr(gallery, 'multi_selected_templates') else 0}")
        
        # Helper function to determine if a template is selected
        def is_template_selected(template_name, selected_template):
            if not selected_template:
                return False
                
            if isinstance(selected_template, dict):
                return selected_template.get('name', '') == template_name
            return selected_template == template_name
            
        # Helper function to determine if a template is multi-selected
        def is_template_multi_selected(template_name, multi_selected_templates):
            if not multi_selected_templates:
                return False
                
            for t in multi_selected_templates:
                if isinstance(t, dict) and t.get('name', '') == template_name:
                    return True
                elif t == template_name:
                    return True
            return False
            
        # Helper function to set template item selection state and update UI
        def update_item_selection(item, is_selected, is_multi_selected):
            # Store current state to see if we actually need to update
            current_selected = item.selected if hasattr(item, 'selected') else False
            current_multi_selected = item.multi_selected if hasattr(item, 'multi_selected') else False
            
            # Skip update if no change is needed
            if current_selected == is_selected and current_multi_selected == is_multi_selected:
                return
                
            # Temporarily block signals during update
            item.blockSignals(True)
            
            # Set primary selection
            if hasattr(item, 'set_selected'):
                item.set_selected(is_selected)
            elif hasattr(item, 'setSelected'):
                item.setSelected(is_selected)
                
            # Set multi-selection
            if hasattr(item, 'set_multi_selected'):
                item.set_multi_selected(is_multi_selected)
            elif hasattr(item, 'setMultiSelected'):
                item.setMultiSelected(is_multi_selected)
                
            # Unblock signals
            item.blockSignals(False)
            
            # Update visual appearance
            if hasattr(item, '_update_styling'):
                item._update_styling()
        
        # For grid view - update template cards
        if gallery.template_view_mode == "grid" and hasattr(gallery, 'template_cards'):
            for card in gallery.template_cards:
                if not card or not hasattr(card, 'template'):
                    continue
                    
                template_name = card.template.get('name', '') if isinstance(card.template, dict) else str(card.template)
                
                # Determine selection state
                is_selected = is_template_selected(template_name, gallery.selected_template if hasattr(gallery, 'selected_template') else None)
                is_multi = is_template_multi_selected(template_name, gallery.multi_selected_templates if hasattr(gallery, 'multi_selected_templates') else [])
                
                # Update card state
                update_item_selection(card, is_selected, is_multi)
        
        # For list view - update list items
        if gallery.template_view_mode == "list" and hasattr(gallery, 'template_item_map'):
            for template_name, list_item in list(gallery.template_item_map.items()):
                try:
                    # Check if item is still valid
                    _ = list_item.size()
                    
                    # Determine selection state
                    is_selected = is_template_selected(template_name, gallery.selected_template if hasattr(gallery, 'selected_template') else None)
                    is_multi = is_template_multi_selected(template_name, gallery.multi_selected_templates if hasattr(gallery, 'multi_selected_templates') else [])
                    
                    # Update list item state
                    update_item_selection(list_item, is_selected, is_multi)
                    
                except RuntimeError as e:
                    print(f"Skipping deleted list item for {template_name}: {e}")
                except Exception as e:
                    print(f"Error updating item {template_name}: {e}")
        
        # Force immediate UI refresh for the active view container
        if gallery.template_view_mode == "list" and hasattr(gallery, 'templates_list_widget'):
            gallery.templates_list_widget.update()
            gallery.templates_list_widget.repaint()
        elif gallery.template_view_mode == "grid" and hasattr(gallery, 'templates_scroll'):
            gallery.templates_scroll.update()
            gallery.templates_scroll.repaint()
            
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
            
            # Get all template objects first
            all_templates = []
            if hasattr(template_manager, 'templates'):
                all_templates.extend(template_manager.templates)
            if hasattr(template_manager, 'template_directories'):
                all_templates.extend(template_manager.template_directories)
            
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
                for template_name in template_names_in_folder:
                    # Find the actual template object by name
                    matching_template = None
                    for template in all_templates:
                        if template.get('name') == template_name:
                            matching_template = template
                            break
                    
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
            template_names = list(templates_dict.keys())
            print(f"[DEBUG] Gallery: Template names: {template_names}")
        
        return templates_dict 

    @staticmethod
    def create_template_card(gallery, template_data):
        """Create a template card widget based on the current view mode"""
        from app.templates.components import TemplateCard
        
        # Create card for grid view
        template_card = TemplateCard(gallery, template=template_data, app=gallery.app)
        
        # Connect all signals using the common helper
        GalleryTemplatesSetup.connect_template_signals(gallery, template_card, template_data)

    @staticmethod
    def create_template_list_item(gallery, template_data):
        """Create a template list item for the given template data"""
        try:
            # Import directly from the components folder
            from app.templates.components.template_list_item import TemplateListItem
            
            # Create the list item
            list_item = TemplateListItem(template_data, gallery)
            
            # Connect basic signals if gallery has the handlers
            if hasattr(gallery, '_on_template_select'):
                list_item.clicked.connect(lambda checked=False, t=template_data: 
                    gallery._on_template_select(t))
            
            # Also connect double-click handler if available
            if hasattr(gallery, '_on_template_double_click'):
                list_item.doubleClicked.connect(lambda t_name=template_data.get('name', ''): 
                    handle_template_edit(gallery, t_name))
            
            # Connect multi-select handler if the gallery has the method
            if hasattr(gallery, 'on_template_multi_select') and hasattr(list_item, 'multiSelectRequested'):
                list_item.multiSelectRequested.connect(
                    lambda t: gallery.on_template_multi_select(t, True))
            
            return list_item
        except Exception as e:
            # Provide a fallback in case of import errors
            print(f"Error creating template list item: {e}")
            from PyQt5.QtWidgets import QLabel
            return QLabel(f"Template: {template_data.get('name', 'Unknown')}") 

    @staticmethod
    def set_template_sort(gallery, sort_field):
        """Set the template sort field and order"""
        # Toggle sort order if the same field is clicked again
        if hasattr(gallery, 'current_sort_field') and gallery.current_sort_field == sort_field:
            if hasattr(gallery, 'current_sort_order'):
                gallery.current_sort_order = 'desc' if gallery.current_sort_order == 'asc' else 'asc'
            else:
                gallery.current_sort_order = 'desc'  # Default to desc if toggled
        else:
            gallery.current_sort_field = sort_field
            gallery.current_sort_order = 'asc'  # Default to ascending
            
        # Print debug information
        print(f"[DEBUG] List View: Sorting by {gallery.current_sort_field} ({gallery.current_sort_order})")

        # Refresh the current view
        if gallery.template_view_mode == "list":
            gallery.populate_gallery(force_refresh=True) 

    @staticmethod
    def clear_selections_with_ui_refresh(gallery):
        """Clear all selections and immediately update the UI"""
        # Clear selection state
        had_selection = False
        if hasattr(gallery, 'selected_template') and gallery.selected_template:
            had_selection = True
            gallery.selected_template = None
            if hasattr(gallery, 'app') and hasattr(gallery.app, 'selected_template'):
                gallery.app.selected_template = None
            print(f"🔍 LISTENER: Cleared primary selection")
            
        # Clear multi-selection
        had_multi_selection = False
        if hasattr(gallery, 'multi_selected_templates') and gallery.multi_selected_templates:
            had_multi_selection = True
            gallery.multi_selected_templates.clear()
            print(f"🔍 LISTENER: Cleared multi-selection")
            
        # Turn off multi-selection mode
        if hasattr(gallery, 'is_multi_selecting'):
            gallery.is_multi_selecting = False
            
        # Update grid view if active
        if gallery.template_view_mode == "grid" and hasattr(gallery, 'template_cards'):
            for card in gallery.template_cards:
                if not card:
                    continue
                    
                # Handle different possible interfaces
                if hasattr(card, 'set_selected'):
                    card.set_selected(False)
                elif hasattr(card, 'setSelected'):
                    card.setSelected(False)
                    
                if hasattr(card, 'set_multi_selected'):
                    card.set_multi_selected(False)
                elif hasattr(card, 'setMultiSelected'):
                    card.setMultiSelected(False)
                    
                # Force style update
                if hasattr(card, '_update_styling'):
                    card._update_styling()
                    
        # Update list view if active
        if hasattr(gallery, 'template_item_map'):
            for item_name, list_item in list(gallery.template_item_map.items()):
                try:
                    # Skip deleted items
                    _ = list_item.size()
                    
                    # Update item state
                    if hasattr(list_item, 'setSelected'):
                        list_item.setSelected(False)
                    if hasattr(list_item, 'setMultiSelected'):
                        list_item.setMultiSelected(False)
                        
                    # Force styling update
                    if hasattr(list_item, '_update_styling'):
                        list_item._update_styling()
                        
                except Exception as e:
                    print(f"Error updating item {item_name}: {e}")
        
        # Force immediate UI refresh
        if gallery.template_view_mode == "list" and hasattr(gallery, 'templates_list_widget'):
            gallery.templates_list_widget.update()
            gallery.templates_list_widget.repaint()
        elif gallery.template_view_mode == "grid" and hasattr(gallery, 'templates_scroll'):
            gallery.templates_scroll.update()
            gallery.templates_scroll.repaint()
            
        # Process pending UI events
        QApplication.processEvents()
        
        print(f"🔍 LISTENER: All selections cleared and UI updated")
        return had_selection or had_multi_selection

    def _handle_list_view_blank_space_click(self, event):
        """Handle click on blank space in the list view by clearing selections"""
        print(f"🔍 LISTENER: Blank space clicked in list view")
        self.clear_selections_with_ui_refresh(self)
        event.accept() 

    def _delayed_populate_list(self):
        """Delayed population of list view to prevent UI freezing and recursive repaints"""
        try:
            # Get templates to show based on current folder
            templates_to_show = {}
            current_folder = self.current_folder if hasattr(self, 'current_folder') else None
            
            if current_folder:
                # Get templates in this folder
                templates_to_show = GalleryTemplatesSetup.get_templates_in_folder(self, current_folder)
            else:
                # Show all templates
                templates_to_show = self.template_manager.templates if hasattr(self, 'template_manager') and hasattr(self.template_manager, 'templates') else {}
            
            # Populate the list view with current templates
            GalleryTemplatesSetup.populate_templates_list(self, templates_to_show)
            
            # Unblock signals after population is complete
            self.templates_list_widget.blockSignals(False)
            
            # Update selection state after population
            GalleryTemplatesSetup.update_template_selection_state(self)
            
        except Exception as e:
            import traceback
            print(f"Error in delayed list population: {e}")
            traceback.print_exc()
            
            # Make sure signals are unblocked even on error
            if hasattr(self, 'templates_list_widget'):
                self.templates_list_widget.blockSignals(False)

class ListViewContainer(QWidget):
    """Widget container for the list view to handle blank space clicks"""
    def __init__(self, gallery, parent=None):
        super().__init__(parent)
        self.gallery = gallery
        self.setMouseTracking(True)
        self.setObjectName("ListViewContainer")
        
        # Force visual styling update
        self.setStyleSheet("QWidget#ListViewContainer { background-color: transparent; }")
        
    def mousePressEvent(self, event):
        """Handle mouse press events on blank areas of the list view"""
        # Check if this is a click directly on the container and not on a child widget
        child = self.childAt(event.pos())
        if child is None or child == self:
            print(f"🔍 LISTENER: Blank space clicked in list container")
            
            # Call the gallery's clear selections function if available
            if hasattr(self.gallery, 'clear_selections_with_ui_refresh'):
                self.gallery.clear_selections_with_ui_refresh(self.gallery)
                print("🔍 LISTENER: Used gallery's clear_selections_with_ui_refresh")
            else:
                # Fall back to our direct implementation
                # Simply clear the selection state in the gallery
                if hasattr(self.gallery, 'selected_template'):
                    self.gallery.selected_template = None
                    if hasattr(self.gallery, 'app') and hasattr(self.gallery.app, 'selected_template'):
                        self.gallery.app.selected_template = None
                    
                # Clear multi-selection
                if hasattr(self.gallery, 'multi_selected_templates'):
                    self.gallery.multi_selected_templates.clear()
                    
                # Turn off multi-selection mode
                if hasattr(self.gallery, 'is_multi_selecting'):
                    self.gallery.is_multi_selecting = False
                
                # Update all list items and force visual refresh
                if hasattr(self.gallery, 'template_item_map'):
                    for template_name, list_item in list(self.gallery.template_item_map.items()):
                        try:
                            list_item.setSelected(False)
                            list_item.setMultiSelected(False)
                            # Explicitly call _update_styling to force visual update
                            list_item._update_styling()
                        except Exception as e:
                            print(f"Error updating item {template_name}: {e}")
                
                # Force complete UI refresh
                self.updateUI()
            
            # Accept the event
            event.accept()
        
        # Call parent handler
        super().mousePressEvent(event)
    
    def updateUI(self):
        """Comprehensive UI refresh that ensures all template items update visually"""
        # First update this container
        self.update()
        
        # If we have an items container, update each widget in it
        if hasattr(self.gallery, 'list_container_layout'):
            for i in range(self.gallery.list_container_layout.count()):
                item = self.gallery.list_container_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    # Force update on the widget
                    widget.update()
        
        # Update the scroll area and viewport
        if hasattr(self.gallery, 'templates_list_widget'):
            # Update viewport first
            viewport = self.gallery.templates_list_widget.viewport()
            if viewport:
                viewport.update()
            
            # Update scroll area itself
            self.gallery.templates_list_widget.update()
        
        # Process events to make updates visible
        QApplication.processEvents()
        
        print(f"🔍 LISTENER: UI refreshed after blank space click") 
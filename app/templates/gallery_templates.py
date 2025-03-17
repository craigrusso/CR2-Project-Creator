#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QFrame, QScrollArea, QGridLayout, QButtonGroup, 
                            QToolButton, QSizePolicy, QPushButton, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import os
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
    """Handle template editing bypassing gallery._on_edit_template to avoid None issues"""
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
            # Create a new container widget and layout for the entire list view
            container = QWidget()
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
            
            # Column headers with click-to-sort functionality
            name_header = QPushButton("Name")
            name_header.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {colors['text']};
                    font-weight: bold;
                    border: none;
                    text-align: left;
                    padding-left: 5px;
                }}
                QPushButton:hover {{
                    color: {colors['accent']};
                }}
            """)
            name_header.clicked.connect(lambda: gallery._on_sort_column('name'))
            
            category_header = QPushButton("Category")
            category_header.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {colors['text']};
                    font-weight: bold;
                    border: none;
                    text-align: left;
                    padding-left: 5px;
                }}
                QPushButton:hover {{
                    color: {colors['accent']};
                }}
            """)
            category_header.clicked.connect(lambda: gallery._on_sort_column('category'))
            
            date_header = QPushButton("Date")
            date_header.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {colors['text']};
                    font-weight: bold;
                    border: none;
                    text-align: left;
                    padding-left: 5px;
                }}
                QPushButton:hover {{
                    color: {colors['accent']};
                }}
            """)
            date_header.clicked.connect(lambda: gallery._on_sort_column('date'))
            
            # Add sort indicators based on current sort field and order
            sort_field = getattr(gallery, 'current_sort_field', 'name')
            sort_order = getattr(gallery, 'current_sort_order', 'asc')
            
            if sort_field == 'name':
                name_header.setText(f"Name {'↓' if sort_order == 'asc' else '↑'}")
            elif sort_field == 'category':
                category_header.setText(f"Category {'↓' if sort_order == 'asc' else '↑'}")
            elif sort_field == 'date':
                date_header.setText(f"Date {'↓' if sort_order == 'asc' else '↑'}")
            
            # Add headers to layout with correct proportions
            header_layout.addWidget(name_header, 4)  # Name gets more space
            header_layout.addWidget(category_header, 2)
            header_layout.addWidget(date_header, 2)
            
            # Add headers to main layout
            main_layout.addWidget(header_container)
            
            # Create a container for the list items
            items_container = QWidget()
            gallery.list_container_layout = QVBoxLayout(items_container)
            gallery.list_container_layout.setContentsMargins(0, 0, 0, 0)
            gallery.list_container_layout.setSpacing(0)
            
            # Get sorted templates based on current sort settings
            templates = list(templates_to_show)
            print(f"[DEBUG] List View: Working with {len(templates)} templates")
            
            # Default sort by name
            if not hasattr(gallery, 'current_sort_field'):
                gallery.current_sort_field = 'name'
            if not hasattr(gallery, 'current_sort_order'):
                gallery.current_sort_order = 'asc'
            
            print(f"[DEBUG] List View: Current sort - {gallery.current_sort_field} ({gallery.current_sort_order})")
            
            # Sort templates
            sorted_templates = sort_templates(templates, gallery.current_sort_field, gallery.current_sort_order)
            print(f"[DEBUG] List View: Sorted {len(sorted_templates)} templates")
            
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
                
                # Connect signals
                list_item.clicked.connect(lambda checked=False, t=template_data: gallery._on_template_select(t))
                list_item.doubleClicked.connect(lambda t=template_data: gallery._on_template_double_click(t))
                
                # Connect delete signal
                list_item.deleteRequested.connect(lambda t_name=template_name: 
                    GalleryEvents.on_delete_template(gallery, t_name))
                
                # Add to layout
                gallery.list_container_layout.addWidget(list_item)
            
            # Set stretch factor to push items to the top
            gallery.list_container_layout.addStretch()
            
            # Add the items container to the main layout
            main_layout.addWidget(items_container)
            
            # Add the main container to the list widget area
            gallery.templates_list_widget.setWidget(container)
            print(f"[DEBUG] List View: Added main container to grid")
            
        except Exception as e:
            import traceback
            print(f"Error populating templates list: {e}")
            print(traceback.format_exc())

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
            
            # Connect the click handler with the template data
            template_card.clicked.connect(lambda checked=False, t=template_data: gallery._on_template_select(t))
            
            # Connect double-click handler to edit template
            template_card.doubleClicked.connect(lambda t_name=template_data.get('name', ''): 
                handle_template_edit(gallery, t_name))
            
            # Connect context menu actions 
            template_card.editRequested.connect(lambda t_name=template_data.get('name', ''): 
                handle_template_edit(gallery, t_name))
            template_card.deleteRequested.connect(lambda t_name=template_data.get('name', ''): 
                GalleryEvents.on_delete_template(gallery, t_name))
            
            # Connect move to folder signal
            template_card.moveToFolderRequested.connect(lambda t_name, folder_name, 
                template_name=template_data.get('name', ''): 
                GalleryEvents.on_move_template_to_folder(gallery, template_name, folder_name))
            
            # Connect multi-select handler if the gallery has the method
            if hasattr(gallery, 'on_template_multi_select') and hasattr(template_card, 'multiSelectRequested'):
                template_card.multiSelectRequested.connect(
                    lambda template, add: gallery.on_template_multi_select(template, add))
            
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
        """Set the template view mode"""
        old_mode = gallery.template_view_mode
        gallery.template_view_mode = mode
        
        # Update button checked states
        gallery.template_grid_view_btn.setChecked(mode == "grid")
        gallery.template_list_view_btn.setChecked(mode == "list")
        
        # Toggle visibility of the view widgets
        if hasattr(gallery, 'templates_scroll'):
            gallery.templates_scroll.setVisible(mode == "grid")
        if hasattr(gallery, 'templates_list_widget'):
            gallery.templates_list_widget.setVisible(mode == "list")
        
        # Always force refresh the view when toggle button is pressed
        gallery.populate_gallery(force_refresh=True)
        
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
        
        # Connect click handler
        template_card.clicked.connect(lambda checked=False, t=template_data: 
            gallery._on_template_select(t))
            
        # Connect multi-select handler if the gallery has the method
        if hasattr(gallery, 'on_template_multi_select') and hasattr(template_card, 'multiSelectRequested'):
            template_card.multiSelectRequested.connect(
                lambda template, add: gallery.on_template_multi_select(template, add))

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
                list_item.doubleClicked.connect(lambda t=template_data: 
                    gallery._on_template_double_click(t))
            
            return list_item
        except Exception as e:
            # Provide a fallback in case of import errors
            print(f"Error creating template list item: {e}")
            from PyQt5.QtWidgets import QLabel
            return QLabel(f"Template: {template_data.get('name', 'Unknown')}") 
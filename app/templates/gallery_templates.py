#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QFrame, QScrollArea, QGridLayout, QButtonGroup, 
                            QToolButton, QSizePolicy, QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import os
from app.ui.color_scheme_pyqt import colors
from app.ui.app_theme_pyqt import ACCENT_BUTTON_STYLE, BUTTON_STYLE
from .components.utils import SYSTEM_FONT
from .components.template_card import TemplateCard, TemplateListItem
from .gallery_events import GalleryEvents

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
        
        # Template title
        gallery.templates_header = QLabel("Templates")
        gallery.templates_header.setFont(QFont(SYSTEM_FONT, 14, QFont.Bold))
        gallery.templates_header.setStyleSheet(f"color: {colors['text']}; padding: 5px 0; background-color: transparent;")
        gallery.templates_header.setAlignment(Qt.AlignLeft)
        gallery.templates_header.setFixedHeight(30)
        gallery.templates_header.setFixedWidth(120)
        gallery.templates_header.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        gallery.templates_header_layout.addWidget(gallery.templates_header)
        
        # Add spacer to push buttons to the right
        gallery.templates_header_layout.addStretch(1)
        
        # Add template button to the left of view controls for consistency with folder section
        gallery.add_button = QPushButton("Add Template")
        # Use accent style to make it stand out
        gallery.add_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        gallery.add_button.clicked.connect(gallery._on_add_template)
        gallery.add_button.setFixedHeight(30)
        gallery.add_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        gallery.templates_header_layout.addWidget(gallery.add_button)
        
        # Add the structure editor button next to Add Template button
        gallery.new_structure_button = QPushButton("Add | Edit Structures")
        gallery.new_structure_button.setStyleSheet(BUTTON_STYLE)
        gallery.new_structure_button.setFixedHeight(30)
        gallery.new_structure_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # We need to connect this to the structure editor handler in the main gallery class
        # The actual connection will be done in the main gallery init
        gallery.templates_header_layout.addWidget(gallery.new_structure_button)
        
        # Template view controls - similar layout to folder view controls
        gallery.template_view_controls = QWidget()
        gallery.template_view_controls.setStyleSheet("background: transparent;")
        gallery.template_view_controls_layout = QHBoxLayout(gallery.template_view_controls)
        gallery.template_view_controls_layout.setContentsMargins(0, 0, 0, 0)
        gallery.template_view_controls_layout.setSpacing(10)
        
        # Create a button group for view toggle
        gallery.template_view_buttons = QWidget()
        gallery.template_view_buttons.setStyleSheet("background: transparent;")
        gallery.template_view_buttons_layout = QHBoxLayout(gallery.template_view_buttons)
        gallery.template_view_buttons_layout.setContentsMargins(0, 0, 0, 0)
        gallery.template_view_buttons_layout.setSpacing(0)  # No spacing between buttons
        
        gallery.template_view_toggle_group = QButtonGroup(gallery)
        
        # Grid view button
        gallery.template_grid_view_btn = QToolButton()
        gallery.template_grid_view_btn.setCheckable(True)
        gallery.template_grid_view_btn.setToolTip("Grid View")
        gallery.template_grid_view_btn.setText("Grid")
        gallery.template_grid_view_btn.setChecked(gallery.template_view_mode == "grid")
        gallery.template_grid_view_btn.clicked.connect(lambda: gallery._set_template_view_mode("grid"))
        gallery.template_grid_view_btn.setFixedSize(65, 24)
        
        # Apply same styling as folder buttons
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
        gallery.template_view_toggle_group.addButton(gallery.template_grid_view_btn)
        gallery.template_view_buttons_layout.addWidget(gallery.template_grid_view_btn)
        
        # List view button
        gallery.template_list_view_btn = QToolButton()
        gallery.template_list_view_btn.setCheckable(True)
        gallery.template_list_view_btn.setToolTip("List View")
        gallery.template_list_view_btn.setText("List")
        gallery.template_list_view_btn.setChecked(gallery.template_view_mode == "list")
        gallery.template_list_view_btn.clicked.connect(lambda: gallery._set_template_view_mode("list"))
        gallery.template_list_view_btn.setFixedSize(65, 24)
        
        # Apply same styling as folder buttons
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
        gallery.template_view_toggle_group.addButton(gallery.template_list_view_btn)
        gallery.template_view_buttons_layout.addWidget(gallery.template_list_view_btn)
        
        # Add buttons widget to controls
        gallery.template_view_controls_layout.addWidget(gallery.template_view_buttons)
        
        # Set fixed size for controls to prevent layout shifting
        gallery.template_view_controls.setFixedHeight(30)
        gallery.template_view_controls.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Add template view controls to the header layout
        gallery.templates_header_layout.addWidget(gallery.template_view_controls)
        
        # Add header container to section layout
        gallery.templates_section_layout.addWidget(gallery.templates_header_container)

    @staticmethod
    def populate_templates_list(gallery, templates_to_show):
        """Populate templates in list view"""
        gallery.template_cards = []
        
        # First, clear any existing widgets from the grid
        if hasattr(gallery, 'templates_grid'):
            try:
                # Remove all items from grid
                while gallery.templates_grid.count():
                    item = gallery.templates_grid.takeAt(0)
                    if item and item.widget():
                        item.widget().deleteLater()
            except Exception as e:
                print(f"Error clearing grid: {e}")
        
        # Debug output to help diagnose issues
        print(f"[DEBUG] Gallery: Populating templates list with {len(templates_to_show)} templates")
        print(f"[DEBUG] Gallery: Template keys: {list(templates_to_show.keys())}")
        
        # Sort templates for consistent display
        sorted_templates = []
        for name, data in templates_to_show.items():
            sorted_templates.append((name, data))
        sorted_templates.sort(key=lambda x: x[0].lower())  # Sort by name case-insensitive
        
        # Create a container for list view that spans the entire width
        list_container = QFrame()
        list_container.setFrameShape(QFrame.NoFrame)
        list_container.setStyleSheet("background-color: transparent; border: none;")
        
        # Make the container expand to fill all available width immediately
        list_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        list_container.setMinimumWidth(gallery.width() - 40)  # Force initial width
        
        # Create a layout that will hug the container to the edges
        list_container_layout = QVBoxLayout(list_container)
        list_container_layout.setContentsMargins(0, 0, 0, 0)
        list_container_layout.setSpacing(0)
        
        # Create an inner scroll area to ensure consistent width
        scroll_area = QScrollArea()
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background-color: transparent; border: none;")
        
        # Make scroll area expand to fill container
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Create the actual list widget that will contain the items
        list_widget = QWidget()
        list_widget.setStyleSheet("background-color: transparent; border: none;")
        list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)  # No spacing between items
        
        # Important: Add vertical alignment to top to prevent centering
        list_layout.setAlignment(Qt.AlignTop)
        
        # Add each template to the list
        for i, (name, data) in enumerate(sorted_templates):
            # Make sure we're passing the template data dictionary with the correct name
            if isinstance(data, dict):
                # Ensure the template data has the correct name
                template_data = dict(data)  # Create a copy to avoid modifying the original
                template_data['name'] = name  # Ensure name is set correctly
                # Also verify we're not using Template-# as the name
                if name.startswith("Template-") and 'name' in data and not data['name'].startswith("Template-"):
                    template_data['name'] = data['name']  # Use the real name from the data
                
                print(f"[DEBUG] Gallery: Creating template list item for '{template_data['name']}'")
            else:
                # If data is not a dictionary, create one with the name
                template_data = {"name": name, "category": "Custom", "description": ""}
                print(f"[DEBUG] Gallery: Creating template list item from name only '{name}'")
            
            # Create a list item using our enhanced TemplateListItem class
            template_item = TemplateListItem(parent=list_widget, template=template_data, app=gallery.app)
            
            # Ensure the item stretches to fill the full width
            template_item.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            # Set alternating row color property
            template_item.setProperty("row_type", "odd" if i % 2 else "even")
            
            # Force style update to apply the alternate row colors
            template_item.style().unpolish(template_item)
            template_item.style().polish(template_item)
            
            # Update styling if the item has a method for it
            if hasattr(template_item, '_update_styling'):
                template_item._update_styling()
            
            # Connect click handlers
            template_item.clicked.connect(lambda checked=False, t=template_data: gallery._on_template_select(t))
            
            # Connect double-click handler to edit template
            template_item.doubleClicked.connect(lambda t=template_data: 
                handle_template_edit(gallery, t.get('name', '')))
            
            # Connect context menu actions if the signals exist
            if hasattr(template_item, 'editRequested'):
                template_item.editRequested.connect(lambda t_name=template_data.get('name', ''): 
                    handle_template_edit(gallery, t_name))
            
            if hasattr(template_item, 'deleteRequested'):
                template_item.deleteRequested.connect(lambda t_name=template_data.get('name', ''): 
                    GalleryEvents.on_delete_template(gallery, t_name))
            
            # Connect move to folder signal if it exists
            if hasattr(template_item, 'moveToFolderRequested'):
                template_item.moveToFolderRequested.connect(lambda t_name, folder_name, 
                    template_name=template_data.get('name', ''): 
                    GalleryEvents.on_move_template_to_folder(gallery, template_name, folder_name))
            
            # Add item to the list layout
            list_layout.addWidget(template_item)
            gallery.template_cards.append(template_item)
        
        # Set up the scroll area with our list widget
        scroll_area.setWidget(list_widget)
        list_container_layout.addWidget(scroll_area)
        
        # Make the container fill the entire available grid space
        # Use a span of 12 columns to make sure it's wider than needed
        gallery.templates_grid.addWidget(list_container, 0, 0, 1, 12)
        
        # Force the container to take the full width of its parent
        list_container.setMinimumWidth(gallery.templates_container.width())
        
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
                            
        # Force immediate layout update to avoid the delay in resizing
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
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
        
        # Only repopulate if the mode actually changed
        if old_mode != mode:
            # Update the gallery
            gallery.populate_gallery()
        
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
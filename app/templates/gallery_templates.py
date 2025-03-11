#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QFrame, QScrollArea, QGridLayout, QButtonGroup, 
                            QToolButton, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from app.ui.color_scheme_pyqt import colors
from .components.utils import SYSTEM_FONT
from .components.template_card import TemplateCard, TemplateListItem

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
        # Set a maximum width and policy to prevent excessive expansion
        gallery.templates_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        gallery.templates_section.setMaximumWidth(1200)
        
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
        # Ensure scroll area fills available space
        gallery.templates_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Container for templates
        gallery.templates_container = QWidget()
        gallery.templates_container.setStyleSheet("background: transparent;")
        gallery.templates_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        gallery.templates_grid = QGridLayout(gallery.templates_container)
        gallery.templates_grid.setContentsMargins(0, 0, 0, 0)
        gallery.templates_grid.setHorizontalSpacing(6)
        gallery.templates_grid.setVerticalSpacing(12)
        gallery.templates_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        gallery.templates_scroll.setWidget(gallery.templates_container)
        gallery.templates_section_layout.addWidget(gallery.templates_scroll)
        
        # Add templates section to main layout
        gallery.main_layout.addWidget(gallery.templates_section)
    
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
    def populate_templates_grid(gallery, templates_to_show):
        """Populate templates in grid view"""
        gallery.template_cards = []
        
        # Grid layout parameters
        col = 0
        row = 0
        max_cols = 4  # Default number of columns
        
        for name, data in templates_to_show.items():
            template_card = TemplateCard(gallery, template=data, app=gallery.app)
            
            # Make sure we're passing the template data dictionary, not just the name
            if isinstance(data, dict):
                template_data = data
            else:
                # If data is not a dictionary, create one with the name
                template_data = {"name": name}
                
            # Connect the click handler with the template data
            template_card.clicked.connect(lambda checked=False, t=template_data: gallery._on_template_select(t))
            
            gallery.templates_grid.addWidget(template_card, row, col)
            gallery.template_cards.append(template_card)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    @staticmethod
    def populate_templates_list(gallery, templates_to_show):
        """Populate templates in list view"""
        gallery.template_cards = []
        
        # List layout - one column
        row = 0
        
        # Sort templates alphabetically for consistent ordering
        sorted_templates = []
        for name, data in templates_to_show.items():
            sorted_templates.append((name, data))
        sorted_templates.sort(key=lambda x: x[0].lower())  # Sort by name case-insensitive
        
        # Create list items with alternating colors
        for i, (name, data) in enumerate(sorted_templates):
            template_item = TemplateListItem(gallery, template=data, app=gallery.app)
            
            # Make sure we're passing the template data dictionary, not just the name
            if isinstance(data, dict):
                template_data = data
            else:
                # If data is not a dictionary, create one with the name
                template_data = {"name": name}
                
            # Set alternating row color property
            template_item.setProperty("row_type", "odd" if i % 2 else "even")
            
            # Force style update
            template_item.style().unpolish(template_item)
            template_item.style().polish(template_item)
            template_item._update_styling()
                
            # Connect the click handler with the template data
            template_item.clicked.connect(lambda checked=False, t=template_data: gallery._on_template_select(t))
            
            gallery.templates_grid.addWidget(template_item, row, 0)
            gallery.template_cards.append(template_item)
            row += 1
            
    @staticmethod
    def set_template_view_mode(gallery, mode):
        """Set the template view mode"""
        old_mode = gallery.template_view_mode
        gallery.template_view_mode = mode
        
        # Update button checked states
        gallery.template_grid_view_btn.setChecked(mode == "grid")
        gallery.template_list_view_btn.setChecked(mode == "list")
        
        # Only repopulate if the mode actually changed and we have a populated gallery
        if old_mode != mode and hasattr(gallery, 'templates_grid'):
            # Update the gallery
            gallery.populate_gallery()
            
    @staticmethod
    def get_templates_in_folder(gallery, folder_name):
        """Get templates in a specific folder"""
        if hasattr(gallery.app, 'template_manager'):
            # First, check if the template manager has a method for this
            if hasattr(gallery.app.template_manager, 'get_templates_in_folder'):
                # Use the template manager's method to get templates in the folder
                templates_list = gallery.app.template_manager.get_templates_in_folder(folder_name)
                
                # Convert list to dict for consistency with the rest of the gallery code
                templates_dict = {}
                for template in templates_list:
                    if isinstance(template, dict) and 'name' in template:
                        templates_dict[template['name']] = template
                    else:
                        # Generate a unique key for templates without names
                        templates_dict[f"Template-{len(templates_dict)}"] = template
                
                return templates_dict
            
            # Fallback: Try checking the folders dictionary directly
            if hasattr(gallery.app.template_manager, 'folders') and folder_name in gallery.app.template_manager.folders:
                # Get template names in the folder
                template_names = gallery.app.template_manager.folders[folder_name]
                templates = gallery.app.template_manager.templates
                
                # Convert to dictionary format
                templates_dict = {}
                
                # Handle templates as dict or list
                if isinstance(templates, dict):
                    for name in template_names:
                        if name in templates:
                            templates_dict[name] = templates[name]
                elif isinstance(templates, list):
                    for name in template_names:
                        for template in templates:
                            if template.get('name') == name:
                                templates_dict[name] = template
                                break
                
                return templates_dict
                
            # Original method as fallback
            templates = gallery.app.template_manager.templates
            folder_templates = {}
            
            # Handle templates as dict or list
            if isinstance(templates, dict):
                for name, data in templates.items():
                    if isinstance(data, dict) and 'folder' in data and data['folder'] == folder_name:
                        folder_templates[name] = data
            elif isinstance(templates, list):
                for template in templates:
                    if isinstance(template, dict) and 'folder' in template and template['folder'] == folder_name:
                        # Use the name as the key if available, otherwise generate a unique key
                        name = template.get('name', f"Template-{len(folder_templates)}")
                        folder_templates[name] = template
                
            return folder_templates
        
        return {} 
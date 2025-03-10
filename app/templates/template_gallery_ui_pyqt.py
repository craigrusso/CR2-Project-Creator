#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import platform
import time
import random
import shutil
import sys
import sip
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QFrame, QScrollArea, QGridLayout, QFileDialog, QMessageBox,
                           QInputDialog, QMenu, QAction, QApplication, QComboBox, QSizePolicy,
                           QSlider, QButtonGroup, QToolButton, QLineEdit)
from PyQt5.QtCore import (Qt, pyqtSignal, QSize, QPoint, QEvent, QMimeData, 
                        QByteArray, QTimer)
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QCursor, QDrag, QPixmap

from app.ui.color_scheme_pyqt import colors, get_color, BUTTON_STYLE, ACCENT_BUTTON_STYLE, LABEL_STYLE, COMBOBOX_STYLE, LINEEDIT_STYLE
from app.ui.ui_components_pyqt import ScrollableFrame, CardFrame, ToolTip, SearchBox, FlowLayout
from app.templates.template_manager import TemplateManager
from app.templates.template_card_pyqt import TemplateCard, CARD_NORMAL, CARD_HOVER, CARD_SELECTED, get_system_font, SYSTEM_FONT
from app.dialogs.dialog_windows_pyqt import show_edit_template, show_manage_templates
from app.templates.template_folder_cards import TemplateFolderCard, TemplateFolderListItem

# Constants for styling
BLUE_HIGHLIGHT = colors["highlight_bg"]
CARD_NORMAL = colors["card_bg"]
CARD_HOVER = colors["hover_bg"]
CARD_SELECTED = colors["highlight_bg"]

# Import the TemplateListItem class from the template_list_item module
from app.templates.template_list_item import TemplateListItem

class TemplateGallery(QWidget):
    """Main widget for displaying and managing templates"""
    
    template_selected = pyqtSignal(dict)
    folder_selected = pyqtSignal(str)
    
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        
        # Get template manager from model in the new MVC architecture
        if app:
            if hasattr(app, 'model'):
                # New MVC architecture
                self.template_manager = app.model.template_manager
            elif hasattr(app, 'template_manager'):
                # Legacy architecture
                self.template_manager = app.template_manager
            else:
                self.template_manager = None
                print("Warning: No template manager found in app. Template gallery may not function correctly.")
        else:
            self.template_manager = None
        
        # UI state tracking
        self.current_category = "All"
        self.current_folder = None
        self.current_search = ""
        self.selected_template = None
        self.selected_folder = None
        self.folder_cards = []
        self.template_cards = []
        self.icon_scale = 100  # Default scale in percentage
        self.folder_view_mode = "grid"  # Default to grid view for folders
        self.template_view_mode = "grid"  # Default to grid view for templates
        self.templates_loaded = False  # Track if templates have been loaded
        
        # Resize handling
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.setInterval(200)  # 200ms debounce
        self.resize_timer.timeout.connect(self._handle_resize_timeout)
        
        # Create main layout - split into two columns
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)  # No spacing between elements

        # Header container at the top
        self.header_container = QWidget()
        self.header_container.setFixedHeight(50)  # Fixed height header
        self.header_layout = QHBoxLayout(self.header_container)
        self.header_layout.setContentsMargins(10, 5, 10, 5)

        # Add header to main layout
        self.layout.addWidget(self.header_container)

        # Create the folders section with fixed header
        self.folders_section = QWidget()
        self.folders_section_layout = QVBoxLayout(self.folders_section)
        self.folders_section_layout.setContentsMargins(0, 0, 0, 0)
        self.folders_section_layout.setSpacing(0)

        # Folders header with view controls
        self.folders_header_container = QWidget()
        self.folders_header_container.setFixedHeight(40)  # Fixed height instead of minimum
        self.folders_header_layout = QHBoxLayout(self.folders_header_container)
        self.folders_header_layout.setContentsMargins(10, 5, 10, 5)  # Add some padding
        self.folders_header_layout.setSpacing(10)

        # Add solid background color to header
        self.folders_header_container.setStyleSheet(f"background-color: {colors['card_bg']};")

        # Folder title
        self.folders_header = QLabel("Folders")
        self.folders_header.setFont(QFont(SYSTEM_FONT, 14, QFont.Bold))
        self.folders_header.setStyleSheet(f"color: {colors['text']}; padding: 5px 0; background-color: transparent;")
        self.folders_header.setAlignment(Qt.AlignLeft)
        # Set fixed height and prevent vertical expansion
        self.folders_header.setFixedHeight(30)
        # Set a fixed width to prevent expanding
        self.folders_header.setFixedWidth(100)
        self.folders_header.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.folders_header_layout.addWidget(self.folders_header)
        
        # Folders section with its own scroll area
        self.folders_scroll = QScrollArea()
        self.folders_scroll.setWidgetResizable(True)
        self.folders_scroll.setFrameShape(QFrame.NoFrame)
        self.folders_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Never allow horizontal scrolling
        self.folders_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Set minimum and maximum height constraints
        self.folders_scroll.setMinimumHeight(150)
        self.folders_scroll.setMaximumHeight(300)  # Limit height to force scrolling
        
        # Container for folder grid - use a flow layout instead of grid
        self.folders_container = QWidget()
        self.folders_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.folders_container.setStyleSheet(f"background-color: {colors['bg']}; border: none;")
        self.folders_grid = QGridLayout(self.folders_container)
        self.folders_grid.setContentsMargins(0, 0, 0, 0)
        self.folders_grid.setHorizontalSpacing(15)  # Increase horizontal spacing for better readability
        self.folders_grid.setVerticalSpacing(15)  # Increase vertical spacing for better separation
        self.folders_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.folders_scroll.setWidget(self.folders_container)
        self.folders_section_layout.addWidget(self.folders_scroll)
        
        # Templates section
        self.templates_section = QWidget()
        self.templates_section_layout = QVBoxLayout(self.templates_section)
        self.templates_section_layout.setContentsMargins(0, 0, 0, 0)
        self.templates_section_layout.setSpacing(5)
        # Set a maximum width and policy to prevent excessive expansion
        self.templates_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.templates_section.setMaximumWidth(1200)
        
        # Templates header with view controls
        self.templates_header_container = QWidget()
        self.templates_header_container.setFixedHeight(40)  # Fixed height instead of minimum
        self.templates_header_layout = QHBoxLayout(self.templates_header_container)
        self.templates_header_layout.setContentsMargins(10, 5, 10, 5)  # Add some padding
        self.templates_header_layout.setSpacing(10)
        # Add solid background color to header
        self.templates_header_container.setStyleSheet(f"background-color: {colors['card_bg']};")
        
        # Template title
        self.templates_header = QLabel("Templates")
        self.templates_header.setFont(QFont(SYSTEM_FONT, 14, QFont.Bold))
        self.templates_header.setStyleSheet(f"color: {colors['text']}; padding: 5px 0; background-color: transparent;")
        self.templates_header.setAlignment(Qt.AlignLeft)
        # Set fixed height and prevent vertical expansion
        self.templates_header.setFixedHeight(30)
        # Set a fixed width to prevent expanding
        self.templates_header.setFixedWidth(120)
        self.templates_header.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.templates_header_layout.addWidget(self.templates_header)
        
        # Add spacer to push buttons to the right
        self.templates_header_layout.addStretch(1)
        
        # Create template view toggle buttons
        self.template_view_toggle_group = QButtonGroup(self)
        
        self.template_view_controls = QWidget()
        self.template_view_controls_layout = QHBoxLayout(self.template_view_controls)
        self.template_view_controls_layout.setContentsMargins(0, 0, 0, 0)
        self.template_view_controls_layout.setSpacing(0)  # No spacing between buttons for a joined appearance
        self.template_view_controls.setStyleSheet("background-color: transparent;")
        
        # Create a widget to hold just the buttons in a group
        self.template_view_buttons = QWidget()
        self.template_view_buttons_layout = QHBoxLayout(self.template_view_buttons)
        self.template_view_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.template_view_buttons_layout.setSpacing(0)  # No spacing between buttons
        
        # Create view buttons that look like a segmented control
        self.template_icon_view_btn = QToolButton()
        self.template_icon_view_btn.setText("Icons")
        self.template_icon_view_btn.setCheckable(True)
        self.template_icon_view_btn.setChecked(True)  # Default is icon view
        self.template_icon_view_btn.clicked.connect(lambda: self._set_template_view_mode("icon"))
        self.template_icon_view_btn.setStyleSheet("""
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
        self.template_view_toggle_group.addButton(self.template_icon_view_btn)
        self.template_view_buttons_layout.addWidget(self.template_icon_view_btn)
        
        self.template_list_view_btn = QToolButton()
        self.template_list_view_btn.setText("List")
        self.template_list_view_btn.setCheckable(True)
        self.template_list_view_btn.clicked.connect(lambda: self._set_template_view_mode("list"))
        self.template_list_view_btn.setStyleSheet("""
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
        self.template_view_toggle_group.addButton(self.template_list_view_btn)
        self.template_view_buttons_layout.addWidget(self.template_list_view_btn)
        
        # Add the button group to the controls layout
        self.template_view_controls_layout.addWidget(self.template_view_buttons)
        
        # Make sure template view controls maintain their size
        self.template_view_controls.setMinimumWidth(135)  # Increased width to prevent cutoff
        self.template_view_controls.setMaximumWidth(135)
        self.template_view_controls.setFixedHeight(30)  # Fixed height to prevent vertical changes
        self.template_view_controls.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Also set fixed size for buttons to prevent layout changes
        self.template_icon_view_btn.setFixedSize(65, 24)
        self.template_list_view_btn.setFixedSize(65, 24)
        
        # Add view controls to header layout
        self.templates_header_layout.addWidget(self.template_view_controls)
        
        # Add header container to section layout
        self.templates_section_layout.addWidget(self.templates_header_container)
        
        # Container for templates grid
        self.templates_container = QWidget()
        self.templates_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.templates_grid = QGridLayout(self.templates_container)
        self.templates_grid.setContentsMargins(0, 0, 0, 0)
        self.templates_grid.setHorizontalSpacing(5)
        self.templates_grid.setVerticalSpacing(5)
        self.templates_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.templates_section_layout.addWidget(self.templates_container)
        
        # Add sections to the main layout
        self.layout.addWidget(self.folders_section)
        self.layout.addWidget(self.templates_section)
        
        # Set up the main scroll area
        # These variables don't exist in this version of the app
        # self.gallery_scroll.setWidget(self.gallery_widget)
        # self.layout.addWidget(self.gallery_scroll)
        
        # Hide sections by default
        self.folders_section.hide()
        self.templates_section.hide()
        
        # Populate gallery
        self.populate_gallery()
    
    def populate_gallery(self, force_refresh=False):
        """Populate the gallery with templates or folders"""
        try:
            print("Starting populate_gallery")
            # Check if we need to refresh templates data
            if force_refresh or not self.templates_loaded:
                # No need to call refresh if it doesn't exist
                self.templates_loaded = True
                
            # Clear the gallery
            print("Clearing gallery")
            self._clear_gallery()
            
            # Update category controls
            print("Updating categories")
            self._update_categories()
            
            # Update folder UI
            print("Updating folder UI")
            self._update_folder_ui()
            
            # Add structure legend below folder navigation if it doesn't exist
            if not hasattr(self, 'structure_legend'):
                self.structure_legend = QWidget()
                legend_layout = QHBoxLayout(self.structure_legend)
                legend_layout.setContentsMargins(15, 5, 15, 5)
                
                folder_icon = QLabel("📂")
                folder_icon.setStyleSheet("color: #4CAF50; font-size: 16px;")
                legend_layout.addWidget(folder_icon)
                
                legend_text = QLabel("Templates with this icon have a custom folder structure")
                legend_text.setStyleSheet("color: #666; font-size: 12px; font-style: italic;")
                legend_layout.addWidget(legend_text)
                
                legend_layout.addStretch(1)  # Push content to left
                
                # Add to gallery layout before the content area
                self.templates_section_layout.insertWidget(0, self.structure_legend)

            print(f"Current folder: {self.current_folder}")
            # Get templates or folders based on current view
            if self.current_folder is None:
                print("Root level - showing folders")
                # Root level - show folders
                QApplication.setOverrideCursor(Qt.WaitCursor)
                try:
                    # Get folder list
                    print("Getting folders")
                    folders = self.template_manager.get_folders()
                    print(f"Folders: {folders}")
                    
                    # Handle either a list of folder names or a dictionary
                    folders_list = []
                    if isinstance(folders, list):
                        folders_list = folders
                    elif isinstance(folders, dict):
                        folders_list = sorted(folders.keys())
                    print(f"Folders list: {folders_list}")
                    
                    # Make sure the folders section is visible if we have folders
                    if folders_list:
                        print("Making folders section visible")
                        self.folders_section.setVisible(True)
                    
                    # Display using either grid or list
                    print(f"Folder view mode: {self.folder_view_mode}")
                    if self.folder_view_mode == "grid" or self.folder_view_mode == "icon":
                        print("Using grid view for folders")
                        # Grid view for folders
                        row, col = 0, 0  # Initialize row and column counters
                        
                        # Calculate available width for better responsive layout
                        available_width = self.folders_container.width()
                        if available_width > 0:
                            # Each folder card is 120px wide plus spacing
                            folder_width = 120 + 15  # Card width + margin
                            # Recalculate number of columns based on available width
                            max_cols = max(1, int((available_width - 30) // folder_width))
                            print(f"Available width: {available_width}px, max columns: {max_cols}")
                        else:
                            max_cols = 3  # Default number of columns
                        
                        # Clear existing grid first to ensure proper layout
                        for card in self.folder_cards:
                            self.folders_grid.removeWidget(card)
                            card.setParent(None)
                        self.folder_cards = []
                        
                        for folder_name in sorted(folders_list):
                            print(f"Creating folder card for: {folder_name}")
                            folder_card = TemplateFolderCard(self, folder_name, self.app)
                            folder_card.clicked.connect(self._on_folder_select)
                            folder_card.doubleClicked.connect(self._on_folder_enter)
                            folder_card.renameRequested.connect(self._on_rename_folder_requested)
                            folder_card.renameDone.connect(self._on_rename_folder_done)
                            self.folders_grid.addWidget(folder_card, row, col)
                            self.folder_cards.append(folder_card)  # Track cards for cleanup
                            
                            # Update grid position
                            col += 1
                            if col >= max_cols:
                                col = 0
                                row += 1
                    else:
                        print("Using list view for folders")
                        # List view for folders
                        # Create a container for list view
                        list_container = QFrame()
                        list_container.setFrameShape(QFrame.NoFrame)
                        list_container.setStyleSheet("background-color: transparent; border: none;")
                        list_layout = QVBoxLayout(list_container)
                        list_layout.setContentsMargins(0, 0, 0, 0)
                        list_layout.setSpacing(0)  # No spacing between items
                        
                        # Add the list container to the grid
                        self.folders_grid.addWidget(list_container, 0, 0, 1, 1)
                        
                        for i, folder_name in enumerate(sorted(folders_list)):
                            print(f"Creating folder list item for: {folder_name}")
                            folder_item = TemplateFolderListItem(self, folder_name, self.app)
                            # Height is already set in the TemplateFolderListItem class
                            folder_item.clicked.connect(self._on_folder_select)
                            folder_item.doubleClicked.connect(self._on_folder_enter)
                            folder_item.renameRequested.connect(self._on_rename_folder_requested)
                            folder_item.renameDone.connect(self._on_rename_folder_done)
                            
                            # Set alternate row color
                            folder_item.set_row_type("odd" if i % 2 else "even")
                            
                            list_layout.addWidget(folder_item)
                            self.folder_cards.append(folder_item)  # Track cards for cleanup
                    
                    # Also load templates not in folders for the root view
                    print("Getting all templates")
                    templates = self.template_manager.get_all_templates()
                    print(f"Templates: {len(templates)}")
                    
                    # Use template_manager to get templates not in any folder
                    root_templates = self.template_manager.get_templates_in_folder(None)
                    print(f"Root templates: {len(root_templates)}")

                    # Make templates section visible if we have templates
                    if root_templates:
                        print("Making templates section visible")
                        self.templates_section.setVisible(True)
                        
                    # Now add template cards to the template section
                    print("Displaying templates")
                    self._display_templates(root_templates)
                    
                    # Update folder management UI visibility
                    print("Updating folder UI")
                    self._update_folder_ui()
                finally:
                    QApplication.restoreOverrideCursor()
            else:
                print(f"Showing templates for folder: {self.current_folder}")
                # Viewing a specific folder
                # Get templates in the folder
                templates = self.get_templates_in_folder(self.current_folder)
                print(f"Templates in folder: {len(templates)}")
                
                # Hide the folders section when inside a folder
                self.folders_section.setVisible(False)
                
                # Update the templates header to show we're in a folder
                self.templates_header.setText(f"Templates in '{self.current_folder}'")
                
                # Make templates section visible if we have templates
                if templates:
                    print("Making templates section visible")
                    self.templates_section.setVisible(True)
                    
                # Display templates
                print("Displaying templates")
                self._display_templates(templates)
                
                # Update folder management UI visibility
                print("Updating folder UI")
                self._update_folder_ui()
                
            print("Populate gallery complete")
        except Exception as e:
            print(f"Error populating gallery: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _display_templates(self, templates):
        """Display templates in the template section"""
        try:
            print(f"_display_templates called with {len(templates)} templates")
            
            if not templates:
                print("No templates to display")
                return
                
            # Calculate available width for templates
            available_width = self.templates_container.width()
            if available_width <= 0:
                available_width = self.width() - 40  # Use widget width with margin
                
            # Limit to a reasonable maximum width
            available_width = min(available_width, 1200)
            
            # Calculate columns for templates
            template_width = 200 + 10  # Template card width + spacing
            max_cols = max(1, (available_width - 30) // template_width)
            
            row, col = 0, 0  # Reset row and column counters
            
            # Display templates based on view mode
            print(f"Template view mode: {self.template_view_mode}")
            if self.template_view_mode == "grid" or self.template_view_mode == "icon":
                print("Using grid view for templates")
                # Grid view
                for template in templates:
                    try:
                        # Use a safer import approach
                        template_name = template.get('name', 'Unknown')
                        print(f"Creating template card for: {template_name}")
                        
                        # Import here to avoid circular imports, use a try-except block
                        try:
                            from app.templates.template_card_pyqt import TemplateCard
                        except ImportError as e:
                            print(f"Error importing TemplateCard: {e}")
                            # Create a simple placeholder frame instead
                            temp_frame = QFrame()
                            temp_layout = QVBoxLayout(temp_frame)
                            temp_label = QLabel(f"Template: {template_name}")
                            temp_label.setStyleSheet("color: white; background: transparent;")
                            temp_layout.addWidget(temp_label)
                            temp_frame.setStyleSheet("background-color: #333; padding: 10px; border-radius: 5px;")
                            temp_frame.setMinimumSize(150, 100)
                            template_card = temp_frame
                            # Create a mousePressEvent for the frame
                            def mousePressEvent(event, t=template):
                                self._on_template_select(t)
                            template_card.mousePressEvent = mousePressEvent.__get__(template_card, QFrame)
                        else:
                            template_card = TemplateCard(parent=self, template=template, app=self.app)
                            # Connect the click signal directly to our selection handler
                            template_card.clicked.connect(self._on_template_select)
                            
                        self.templates_grid.addWidget(template_card, row, col)
                        self.template_cards.append(template_card)
                        
                        # Update grid position
                        col += 1
                        if col >= max_cols:
                            col = 0
                            row += 1
                            
                    except Exception as e:
                        print(f"Error creating template card for {template.get('name', 'Unknown')}: {e}")
            else:
                print("Using list view for templates")
                # List view
                # Create a container for list view
                list_container = QFrame()
                list_container.setFrameShape(QFrame.NoFrame)
                list_container.setStyleSheet("background-color: transparent; border: none;")
                list_layout = QVBoxLayout(list_container)
                list_layout.setContentsMargins(0, 0, 0, 0)
                list_layout.setSpacing(0)  # No spacing between items
                
                # Add the list container to the grid
                self.templates_grid.addWidget(list_container, 0, 0, 1, 1)
                
                for i, template in enumerate(templates):
                    try:
                        template_name = template.get('name', 'Unknown')
                        template_desc = template.get('description', '')
                        print(f"Creating template list item for: {template_name}")
                        
                        # Use the TemplateListItem class from template_list_item.py
                        from app.templates.template_list_item import TemplateListItem
                        list_item = TemplateListItem(self, template, self.app)
                        
                        # Set row type for alternating colors
                        list_item.setProperty("row_type", "odd" if i % 2 else "even")
                        
                        # Connect signals
                        list_item.clicked.connect(lambda t=template: self._on_template_select(t))
                        
                        # Add to layout
                        self.templates_grid.addWidget(list_item, i, 0)
                        self.template_cards.append(list_item)  # Track for cleanup
                    except Exception as e:
                        print(f"Error creating template list item for {template.get('name', 'Unknown')}: {e}")
                        
            print("Templates displayed successfully")
        except Exception as e:
            print(f"Error in _display_templates: {e}")
            import traceback
            traceback.print_exc()
    
    def _clear_gallery(self):
        """Clear all cards from the gallery"""
        # First, delete all folder cards
        for card in self.folder_cards:
            try:
                card.deleteLater()
            except RuntimeError:
                pass
        self.folder_cards = []
        
        # Delete all template cards
        for card in self.template_cards:
            try:
                card.deleteLater()
            except RuntimeError:
                pass
        self.template_cards = []
        
        # Completely remove and recreate the folders container with a new grid layout
        if self.folders_container:
            self.folders_container.deleteLater()
        
        self.folders_container = QWidget()
        self.folders_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.folders_grid = QGridLayout(self.folders_container)
        self.folders_grid.setContentsMargins(0, 0, 0, 0)
        self.folders_grid.setHorizontalSpacing(15)  # Increase horizontal spacing for better readability
        self.folders_grid.setVerticalSpacing(15)  # Increase vertical spacing for better separation
        self.folders_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.folders_scroll.setWidget(self.folders_container)
        
        # Completely remove and recreate the templates container with a new grid layout
        if self.templates_container:
            self.templates_container.deleteLater()
        
        self.templates_container = QWidget()
        self.templates_grid = QGridLayout(self.templates_container)
        self.templates_grid.setContentsMargins(0, 0, 0, 0)
        self.templates_grid.setHorizontalSpacing(5)
        self.templates_grid.setVerticalSpacing(5)
        self.templates_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.templates_section_layout.addWidget(self.templates_container)

    def _update_categories(self):
        """Update category dropdown with available categories"""
        # Skip if category_combo doesn't exist
        if not hasattr(self, 'category_combo'):
            print("Category combo not found, skipping update")
            return
            
        # Get unique categories
        templates = self.template_manager.get_all_templates()
        categories = sorted(set(t.get('category', 'General') for t in templates))
        
        # Remember current category
        current_category = self.current_category
        
        # Clear and repopulate the combo box
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        
        # Always add "All" as the first option
        self.category_combo.addItem("All")
        
        # Add categories
        for category in categories:
            self.category_combo.addItem(category)
        
        # Set to current category if it exists, otherwise default to "All"
        index = self.category_combo.findText(current_category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        else:
            self.category_combo.setCurrentIndex(0)
            self.current_category = "All"
        
        self.category_combo.blockSignals(False)

    def _on_category_select(self, category):
        """Handle category selection"""
        self.current_category = category
        self.populate_gallery()
    
    def _on_search(self, search_text):
        """Handle search input"""
        # Handle both SearchBox (which passes the text) and LineEdit (which doesn't)
        if isinstance(search_text, bool) or search_text is None:
            # This is from the LineEdit
            search_text = self.search_input.text()
            
        self.current_search = search_text
        self.populate_gallery(force_refresh=True)
    
    def _on_template_select(self, template):
        """Handle template selection from gallery"""
        print(f"Template selected: {template.get('name', 'Unknown')}")
        
        # Clear selection from all templates first
        for card in self.template_cards:
            try:
                # Different cards might have different ways to set selected
                if hasattr(card, 'set_selected'):
                    card.set_selected(False)
                elif hasattr(card, 'setProperty'):
                    card.setProperty('selected', False)
                    # Force style refresh
                    card.style().unpolish(card)
                    card.style().polish(card)
            except Exception as e:
                print(f"Error in template selection: {e}")
        
        # Now set the selected template
        self.selected_template = template
        
        # Emit the selected template signal
        self.template_selected.emit(template)
        
        # Update UI feedback
        for card in self.template_cards:
            if not hasattr(card, 'template'):
                continue
                
            if card.template == template:
                try:
                    # Different cards might have different ways to set selected
                    if hasattr(card, 'set_selected'):
                        card.set_selected(True)
                    elif hasattr(card, 'setProperty'):
                        card.setProperty('selected', True)
                        # Force style refresh
                        card.style().unpolish(card)
                        card.style().polish(card)
                except Exception as e:
                    print(f"Error setting template selected state: {e}")
    
    def _on_add_template(self):
        """Handle add template button click"""
        # Get template name from user
        template_name, ok = QInputDialog.getText(
            self,
            "New Template",
            "Enter template name:"
        )
        
        if not ok or not template_name:
            return
            
        # Get category
        category, ok = QInputDialog.getItem(
            self,
            "Template Category",
            "Select category:",
            self.template_manager.get_categories(),
            0,
            False
        )
        
        if not ok or not category:
            return
        
        # Create an empty template - no file association yet
        success = self.template_manager.save_template(
            template_name,
            category,
            "",  # No file yet - user will add files in the editor
            "Standard"
        )
        
        if not success:
            QMessageBox.warning(self, "Error", f"Failed to create template '{template_name}'.")
            return
            
        # If we're in a folder, add the template to it
        if self.current_folder:
            print(f"Adding new template '{template_name}' to current folder '{self.current_folder}'")
            self.template_manager.add_to_folder(self.current_folder, template_name)
        
        # Get the newly created template
        new_template = self.template_manager.get_template_by_name(template_name)
        
        if not new_template:
            QMessageBox.warning(self, "Error", f"Failed to retrieve template '{template_name}' after creation.")
            self.populate_gallery()
            return
            
        # Open the editor immediately so user can add files and set up structure
        from app.dialogs.dialog_windows_pyqt import show_edit_template
        show_edit_template(self, new_template, self._on_template_edited)
        
        # Refresh the gallery to show the new template
        self.populate_gallery()
    
    def _on_edit_template(self):
        """Handle edit template button click"""
        if self.selected_template:
            show_edit_template(self, self.selected_template, self._on_template_edited)
    
    def _on_template_edited(self, template):
        """Handle template edit completion"""
        if template:
            print(f"DEBUG: Template edited: {template.get('name')}")
            
            # Check if the template has a structure
            if 'structure' in template:
                print(f"DEBUG: Template has structure data")
                structure_name = f"Template_{template.get('name')}"
                print(f"DEBUG: Saving structure as {structure_name}")
                
                # Save the structure first
                self.template_manager.save_custom_structure(structure_name, template.get('structure', []))
                
                # Make sure structure_name is set in the template
                template['structure_name'] = structure_name
            
            # Check if update_template exists, otherwise use save_template as fallback
            if hasattr(self.template_manager, 'update_template'):
                print(f"DEBUG: Using update_template method")
                self.template_manager.update_template(template)
            else:
                # Fallback to save_template if update_template doesn't exist
                print(f"DEBUG: Using save_template fallback")
                template_name = template.get('name', '')
                category = template.get('category', '')
                path = template.get('path', '')
                template_type = template.get('type', 'Standard')
                self.template_manager.save_template(template_name, category, path, template_type)
            
            self.populate_gallery()
    
    def _on_delete_template(self):
        """Handle delete template button click"""
        if self.selected_template:
            template_name = self.selected_template.get('name', 'Unnamed Template')
            
            confirm = QMessageBox.question(
                self, 
                "Confirm Delete", 
                f"Are you sure you want to delete template '{template_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                success = self.template_manager.delete_template(template_name)
                if success:
                    QMessageBox.information(self, "Success", f"Template '{template_name}' deleted successfully.")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to delete template '{template_name}'.")
                
                self.selected_template = None
                self.populate_gallery()
    
    def _on_manage_templates(self):
        """Handle manage templates button click"""
        show_manage_templates(self, self.template_manager, self.populate_gallery)
    
    def _on_folder_select(self, folder_name):
        """Handle folder selection - updates UI but doesn't navigate into the folder"""
        try:
            # Update tracking of selected folder
            self.selected_folder = folder_name
            
            # Update folder button states if they exist
            if hasattr(self, 'delete_folder_button'):
                self.delete_folder_button.setEnabled(True)
            
            # Deselect any selected template
            self.selected_template = None
            
            # Update button states (template buttons)
            self._update_button_state()
            
            # Update folder selection in UI
            for card in self.folder_cards:
                if hasattr(card, 'set_selected') and callable(card.set_selected):
                    if hasattr(card, 'folder_name'):
                        card.set_selected(card.folder_name == folder_name)
                    
            # Emit the folder selected signal
            self.folder_selected.emit(folder_name)
        except Exception as e:
            print(f"Error in _on_folder_select: {e}")

    def _on_folder_enter(self, folder_name):
        """Handle folder navigation - actually enter the folder"""
        try:
            # Validate input
            if not folder_name or not isinstance(folder_name, str):
                print(f"Invalid folder name: {folder_name}")
                return
                
            # Get valid folders 
            folders = self.template_manager.get_folders()
            
            # Check if folder exists - handle both list and dict
            folder_exists = False
            if isinstance(folders, list):
                folder_exists = folder_name in folders
            elif isinstance(folders, dict):
                folder_exists = folder_name in folders.keys()
                
            if not folder_exists:
                print(f"Folder not found: {folder_name}")
                return
                
            # Update the current folder
            self.current_folder = folder_name
            self.folder_label.setText(f"Current Folder: {folder_name}")
            
            # Refresh the gallery with the folder contents
            QApplication.processEvents()  # Process pending events to avoid UI freezes
            self.populate_gallery()
        except Exception as e:
            print(f"Error in _on_folder_enter: {e}")
            import traceback
            traceback.print_exc()
            
    def get_templates_in_folder(self, folder_name):
        """Get templates in a specific folder - fallback implementation"""
        # If template manager has its own implementation, use that
        if hasattr(self.template_manager, 'get_templates_in_folder'):
            return self.template_manager.get_templates_in_folder(folder_name)
            
        # Otherwise use our fallback implementation
        templates = self.template_manager.get_all_templates()
        
        # Check if folders are stored as a dict with folder contents
        folders = self.template_manager.get_folders()
        if isinstance(folders, dict) and folder_name in folders:
            # Get the templates in this folder
            folder_templates = []
            for template_name in folders[folder_name]:
                # Find the template with this name
                for template in templates:
                    if template.get('name') == template_name:
                        folder_templates.append(template)
                        break
            return folder_templates
        
        # If folders are not a dict or don't contain this folder,
        # look for templates that have this folder in their 'folder' attribute
        return [t for t in templates if t.get('folder') == folder_name]
    
    def _on_back_to_all(self):
        """Handle clicking the "Back to All" button"""
        # Clear current folder
        self.current_folder = None
        
        # Clear folder label
        self.folder_label.setText("")
        
        # Reset templates header
        self.templates_header.setText("Templates")
        
        # Make sure the folders section is visible again
        self.folders_section.setVisible(True)
        
        # Refresh the gallery
        self.populate_gallery()
    
    def _update_folder_ui(self):
        """Update folder navigation UI based on current folder"""
        print("Updating folder UI")
        
        # Update navigation based on current folder
        if self.current_folder:
            print(f"Current folder: {self.current_folder}")
            # Update label text
            self.folder_label.setText(f"Current Folder: {self.current_folder}")
            # Show navigation controls
            self.folder_nav.show()
            self.folder_label.show()
            
            # Update folder management buttons
            self.add_folder_button.show()
            # Hide delete button by default (we use context menu instead)
            self.delete_folder_button.hide()
        else:
            print("Root level - showing folders")
            # Hide folder navigation
            self.folder_nav.hide()
            self.folder_label.hide()
            
            # Update folder management buttons    
            self.add_folder_button.show()
            self.delete_folder_button.hide()
    
    def _on_add_folder(self):
        """Handle add folder button click"""
        folder_name, ok = QInputDialog.getText(
            self,
            "New Folder",
            "Enter folder name:"
        )
        
        if ok and folder_name:
            # Check if folder already exists
            folders = self.template_manager.get_folders()
            if folder_name in folders:
                QMessageBox.warning(self, "Error", f"Folder '{folder_name}' already exists.")
                return
                
            # Create folder
            self.template_manager.add_folder(folder_name)
            
            # If we're in a folder, move to new folder
            if self.current_folder is not None:
                self.current_folder = folder_name
                
            self.populate_gallery()
            
    def _on_rename_folder(self):
        """Handle rename folder button click - kept for compatibility"""
        if self.current_folder is None:
            return
            
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Folder",
            "Enter new folder name:",
            text=self.current_folder
        )
        
        if ok and new_name and new_name != self.current_folder:
            # Check if new folder name already exists
            folders = self.template_manager.get_folders()
            if new_name in folders:
                QMessageBox.warning(self, "Error", f"Folder '{new_name}' already exists.")
                return
                
            # Rename folder
            self.template_manager.rename_folder(self.current_folder, new_name)
            self.current_folder = new_name
            self.populate_gallery()
    
    def _on_rename_folder_requested(self, folder_name):
        """Handle rename folder request from folder card - kept for compatibility"""
        # We're now using inline editing, so this method is just a fallback
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Folder",
            "Enter new folder name:",
            text=folder_name
        )
        
        if ok and new_name and new_name != folder_name:
            self._rename_folder(folder_name, new_name)
    
    def _on_rename_folder_done(self, old_name, new_name):
        """Handle folder rename completion from inline editing"""
        try:
            print(f"Folder rename requested from '{old_name}' to '{new_name}'")
            
            # Check if new folder name already exists
            folders = self.template_manager.get_folders()
            print(f"Current folders: {folders}")
            
            # Check if the folder already exists
            folder_exists = False
            if isinstance(folders, list):
                folder_exists = new_name in folders
            elif isinstance(folders, dict):
                folder_exists = new_name in folders.keys()
                
            if folder_exists:
                print(f"Folder '{new_name}' already exists, cancelling rename")
                QMessageBox.warning(self, "Error", f"Folder '{new_name}' already exists.")
                return
                
            # Proceed with renaming
            print(f"Proceeding with rename '{old_name}' to '{new_name}'")
            self._rename_folder(old_name, new_name)
        except Exception as e:
            print(f"Error in _on_rename_folder_done: {e}")
            import traceback
            traceback.print_exc()
            
    def _rename_folder(self, old_name, new_name):
        """Common method to handle folder renaming"""
        try:
            print(f"Renaming folder from '{old_name}' to '{new_name}'")
            
            # Rename folder
            success = self.template_manager.rename_folder(old_name, new_name)
            print(f"Rename result: {success}")
            
            if success:
                # Update current folder if needed
                if self.current_folder == old_name:
                    print(f"Updating current folder from '{old_name}' to '{new_name}'")
                    self.current_folder = new_name
                    self.folder_label.setText(f"Current Folder: {new_name}")
                
                # Refresh the gallery
                print("Refreshing gallery after rename")
                self.populate_gallery()
            else:
                print(f"Failed to rename folder '{old_name}'")
                QMessageBox.warning(self, "Error", f"Failed to rename folder '{old_name}'.")
        except Exception as e:
            print(f"Error in _rename_folder: {e}")
            import traceback
            traceback.print_exc()

    def _on_delete_folder(self):
        """Handle delete folder button click"""
        if self.current_folder is None:
            return
            
        # Check if this is a default folder
        if self.current_folder in ["General", "Development", "Business"]:
            QMessageBox.warning(self, "Error", f"'{self.current_folder}' is a default folder and cannot be deleted.")
            return
            
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete folder '{self.current_folder}'?\n"
            "Templates in this folder will remain available but will be moved to the root.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Delete folder
            self.template_manager.delete_folder(self.current_folder)
            self.current_folder = None
            self.populate_gallery()
    
    def _update_button_state(self):
        """Update button states based on selection"""
        has_selection = self.selected_template is not None
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        # Handle delete or backspace key when a folder is selected
        if self.selected_folder and (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace):
            # Don't allow deleting default folders
            if self.selected_folder in ["General", "Development", "Business"]:
                QMessageBox.warning(self, "Error", f"'{self.selected_folder}' is a default folder and cannot be deleted.")
                return
                
            # Show confirmation dialog
            confirm = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete folder '{self.selected_folder}'?\n"
                "Templates in this folder will remain available but will be moved to the root.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                # Delete folder
                self.template_manager.delete_folder(self.selected_folder)
                self.selected_folder = None
                self.populate_gallery()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        """Override resize event to adjust layout dynamically but prevent excessive redraws"""
        super().resizeEvent(event)
        
        # Instead of updating immediately, use a timer to prevent excessive redraws
        if self.resize_timer.isActive():
            self.resize_timer.stop()
        
        # Schedule a single update after the user has stopped resizing for a short time
        self.resize_timer.start(50)  # 50ms debounce
    
    def _handle_resize_timeout(self):
        """Handle the resize timeout after resizing has stopped"""
        # Calculate minimum width needed for controls
        min_width_needed = self._calculate_min_width_needed()
        
        # If window is too small, enforce minimum size
        current_width = self.width()
        if current_width < min_width_needed:
            self.setMinimumWidth(min_width_needed)
        
        # Update layouts now that resizing has stopped
        self._update_layout_after_resize()
    
    def _calculate_min_width_needed(self):
        """Calculate minimum width needed to display all controls properly"""
        # Use fixed values instead of calculating sizeHints which can cause repaints
        min_width = 400  # Base minimum width
        
        # Add container margins
        min_width += 60  # Side margins with some extra padding
        
        return min_width
        
    def _update_layout_after_resize(self):
        """Update layout after resize with proper timing"""
        try:
            # Block signals to prevent repainting cascade
            self.blockSignals(True)
            
            # Force recalculation of container widths
            parent_width = self.width()
            available_width = min(parent_width - 40, 1200)
            
            viewport_width = self.folders_scroll.viewport().width()
            if viewport_width > 0:
                available_width = viewport_width
            
            # Set the width without triggering layout
            self.folders_container.setMinimumWidth(available_width)
            self.folders_container.setMaximumWidth(available_width)
        
            # Force layout recalculation for folder wrapping if we're in grid mode
            if self.folder_view_mode in ["grid", "icon"]:
                self._recalculate_folder_grid(available_width)
        
            # Also update templates container width
            parent_width = self.width()
            available_width = min(parent_width - 40, 1200)
            
            # Set the width without triggering layout
            self.templates_container.setMinimumWidth(available_width)
            self.templates_container.setMaximumWidth(available_width)
        finally:
            # Always unblock signals
            self.blockSignals(False)

    def _recalculate_folder_grid(self, available_width):
        """Recalculate folder grid layout without repopulating"""
        try:
            # Only proceed if we're in grid view
            if self.folder_view_mode not in ["grid", "icon"]:
                return
            
            # Calculate max columns based on available width
            folder_width = 120 + 15  # Card width + margin
            max_cols = max(1, int((available_width - 30) // folder_width))
            
            # Get all existing folder cards
            cards = list(self.folder_cards)
            
            # Skip if no cards
            if not cards:
                return
            
            # Remove widgets from grid
            for card in cards:
                self.folders_grid.removeWidget(card)
            
            # Re-add widgets in new arrangement
            row, col = 0, 0
            for card in cards:
                if card and not sip.isdeleted(card):
                    self.folders_grid.addWidget(card, row, col)
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
        except Exception as e:
            print(f"Error recalculating folder grid: {e}")

    def _on_icon_scale_changed(self, value):
        """Handle icon scale slider changes"""
        print(f"[DEBUG] Icon scale changed to {value}")
        
        # Update the icon_scale property for all sizing
        self.icon_scale = value
        
        # Only update folder card sizes, not template card sizes
        self._update_folder_card_sizes(value)

    def _update_folder_card_sizes(self, value):
        """Update folder card sizes based on icon scale"""
        print(f"[DEBUG] Updating folder card sizes with scale value: {value}")
        print(f"[DEBUG] Current folder view mode: {self.folder_view_mode}")
        print(f"[DEBUG] Number of folder cards: {len(self.folder_cards)}")
        
        # Default sizes should match the sizes we use in initialization
        folder_base_width = 120
        folder_base_height = 120
        
        # Calculate new sizes
        scale_factor = value / 100.0
        
        # New folder sizes
        new_folder_width = int(folder_base_width * scale_factor)
        new_folder_height = int(folder_base_height * scale_factor)
        print(f"[DEBUG] New folder size: {new_folder_width}x{new_folder_height}")
        
        # Update folder cards in grid or icon view (any mode that's not list)
        if self.folder_view_mode != "list":
            resized_count = 0
            for card in self.folder_cards:
                if isinstance(card, TemplateFolderCard):  # Only scale icon/grid view cards
                    card.setFixedSize(new_folder_width, new_folder_height)
                    # Adjust font size of icon - use 40 to match the default in TemplateFolderCard
                    icon_font_size = int(40 * scale_factor)
                    card.icon_label.setFont(QFont(SYSTEM_FONT, icon_font_size))
                    resized_count += 1
            print(f"[DEBUG] Resized {resized_count} folder cards")
        else:
            print(f"[DEBUG] Not resizing folders in list view mode")
        
        # Update layout but don't repopulate to avoid recursive loops
        self.folders_grid.update()
        if hasattr(self, 'folders_container'):
            self.folders_container.updateGeometry()
            self.folders_container.update()
    
    def _update_template_card_sizes(self, value):
        """Update template card sizes based on icon scale"""
        print(f"[DEBUG] Updating template card sizes with scale value: {value}")
        
        # Default sizes should match the sizes we use in initialization
        template_base_width = 200
        template_base_height = 250  # Adjusted to match typical card height
        
        # Calculate new sizes
        scale_factor = value / 100.0
        
        # New template sizes
        new_template_width = int(template_base_width * scale_factor)
        new_template_height = int(template_base_height * scale_factor)
        
        # Update template cards if in icon/grid view
        if self.template_view_mode != "list":
            resized_count = 0
            for card in self.template_cards:
                if hasattr(card, 'setFixedSize'):  # Check for the required method
                    # Set the size on the card
                    card.setFixedSize(new_template_width, new_template_height)
                    resized_count += 1
            print(f"[DEBUG] Resized {resized_count} template cards")
        else:
            print(f"[DEBUG] Not resizing templates in list view mode")
            
        # Update layout but don't repopulate to avoid recursive loops
        self.templates_grid.update()
        if hasattr(self, 'templates_container'):
            self.templates_container.updateGeometry()
            self.templates_container.update()

    def _set_folder_view_mode(self, mode):
        """Set the folder view mode"""
        print(f"Changing folder view mode to: {mode}")
        if mode in ["icon", "grid", "list"]:
            prev_mode = self.folder_view_mode
            self.folder_view_mode = mode
            
            # Update button states
            self.folder_icon_view_btn.setChecked(mode in ["icon", "grid"])
            self.folder_list_view_btn.setChecked(mode == "list")
            
            # When in list mode, hide the slider but keep the container visible
            # This prevents layout shifts when toggling between modes
            if hasattr(self, 'folder_size_control'):
                if mode == "list":
                    self.folder_size_slider.setVisible(False)
                else:
                    self.folder_size_slider.setVisible(True)
            
            # Only refresh if the view mode actually changed
            if prev_mode != mode:
                print(f"Folder view mode changed from {prev_mode} to {mode}, refreshing...")
                self.populate_gallery(force_refresh=True)
        else:
            print(f"Invalid folder view mode: {mode}")

    def _set_template_view_mode(self, mode):
        """Set the template view mode"""
        print(f"Changing template view mode to: {mode}")
        if mode in ["icon", "grid", "list"]:
            prev_mode = self.template_view_mode
            self.template_view_mode = mode
            
            # Update button states
            self.template_icon_view_btn.setChecked(mode in ["icon", "grid"])
            self.template_list_view_btn.setChecked(mode == "list")
            
            # Only refresh if the view mode actually changed
            if prev_mode != mode:
                print(f"View mode changed from {prev_mode} to {mode}, refreshing...")
                self.populate_gallery(force_refresh=True)
        else:
            print(f"Invalid template view mode: {mode}")

    def _update_card_sizes(self):
        """Legacy method to update all card sizes - kept for backward compatibility"""
        # Forward to the specific method using current slider value
        self._update_folder_card_sizes(self.folder_size_slider.value())
        # We no longer update template cards with the folder size slider

    def _create_templates_section(self):
        """Create the templates section"""
        self.templates_section = QFrame()
        self.templates_section.setObjectName("templatesSection")
        self.templates_section_layout = QVBoxLayout(self.templates_section)
        self.templates_section_layout.setContentsMargins(0, 0, 0, 0)
        self.templates_section_layout.setSpacing(0)
        
        # Templates header with legend and controls

def create_template_gallery(app):
    """
    Create and return a new template gallery widget
    
    Args:
        app: The main application instance, which can be either the legacy architecture
             or the new MVC architecture with model and controller properties
    
    Returns:
        A configured TemplateGallery widget
    """
    try:
        gallery = TemplateGallery(app=app)
        
        # Connect template selection signal
        gallery.template_selected.connect(lambda template: select_template_from_gallery(app, template))
        
        # Populate the gallery
        gallery.populate_gallery()
        
        # Connect to app's template updated signal
        if hasattr(app, 'controller') and hasattr(app.controller, 'template_updated'):
            # New MVC architecture
            app.controller.template_updated.connect(lambda: gallery.populate_gallery(True))
        elif hasattr(app, 'template_updated'):
            # Legacy architecture
            app.template_updated.connect(lambda: gallery.populate_gallery(True))
        
        return gallery
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error creating template gallery: {e}")
        # Return an empty widget as fallback
        return QWidget()

def select_template_from_gallery(app, template):
    """Select a template from the gallery by ID or template object"""
    # Handle different types of template identifiers
    template_id = None
    if isinstance(template, str):
        # Template ID directly
        template_id = template
    elif isinstance(template, dict) and 'id' in template:
        # Template object
        template_id = template['id']

    # Select in the gallery
    if hasattr(app, 'template_gallery') and template_id:
        if hasattr(app.template_gallery, 'select_template_by_id'):
            app.template_gallery.select_template_by_id(template_id)
        elif hasattr(app.template_gallery, '_on_template_select'):
            app.template_gallery._on_template_select(template)

# Add unit test section at the end of the file
if __name__ == "__main__":
    """Unit test section for testing gallery components"""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test template list item
    template = {
        "name": "Test Template",
        "description": "This is a test template for verifying the UI",
        "category": "Test",
        "icon": "📄"
    }
    
    # Create a simple test window
    window = QWidget()
    layout = QVBoxLayout()
    window.setLayout(layout)
    
    # Add a folder list item
    folder_item = TemplateFolderListItem(window, "Test Folder")
    layout.addWidget(folder_item)
    
    # Add a template list item
    template_item = TemplateListItem(window, template)
    layout.addWidget(template_item)
    
    # Show the window
    window.setGeometry(100, 100, 800, 600)
    window.setWindowTitle("Gallery Component Test")
    window.show()
    
    sys.exit(app.exec_()) 
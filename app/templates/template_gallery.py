#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QFrame, QScrollArea, QGridLayout, QComboBox, QButtonGroup, 
                           QToolButton, QSlider, QSizePolicy, QMessageBox, QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap
import os
import platform

from app.ui.color_scheme_pyqt import colors, get_color, BUTTON_STYLE, ACCENT_BUTTON_STYLE, LABEL_STYLE

from .components.template_folder_card import TemplateFolderCard, TemplateFolderListItem
from .components.template_card import TemplateCard, TemplateListItem
from .components.utils import SYSTEM_FONT
from .components.common_styles import CARD_NORMAL, CARD_HOVER, CARD_SELECTED
from .components.components import SearchBox

class TemplateGallery(QWidget):
    """Main widget for displaying and managing templates"""
    
    template_selected = pyqtSignal(dict)
    folder_selected = pyqtSignal(str)
    
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.parent = parent
        self.template_manager = app.template_manager if app else None
        
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
        
        # Initialize grid layouts to avoid AttributeError
        self.folders_grid = None
        self.templates_grid = None
        
        # Resize handling
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.setInterval(200)  # 200ms debounce
        self.resize_timer.timeout.connect(self._handle_resize_timeout)
        
        # Set up the UI
        self._setup_ui()
        
        # Populate the gallery initially - do this after UI setup
        self.populate_gallery()
    
    def _setup_ui(self):
        """Set up the UI components"""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)  # No space between components
        
        # Top bar with category filter and search
        self._setup_top_bar()
        
        # Action bar with buttons
        self._setup_action_bar()
        
        # Add a fixed margin frame between action bar and content
        self.margin_frame = QFrame()
        self.margin_frame.setFixedHeight(10)  # Fixed spacing
        self.margin_frame.setStyleSheet("background-color: transparent;")
        self.layout.addWidget(self.margin_frame)
        
        # Set up the gallery containers
        self._setup_gallery_containers()
    
    def _setup_top_bar(self):
        """Set up the top bar with category filter and search"""
        # Top bar for search, filter and actions
        self.top_bar = QWidget()
        self.top_bar.setStyleSheet("background: transparent;")
        self.top_bar_layout = QHBoxLayout(self.top_bar)
        self.top_bar_layout.setContentsMargins(10, 5, 10, 5)
        
        # Category filter with horizontal layout
        self.category_layout = QHBoxLayout()
        self.category_layout.setContentsMargins(0, 0, 0, 0)
        self.category_layout.setSpacing(5)  # Small spacing between label and dropdown
        
        # Clean, minimal category label
        self.category_label = QLabel("Category:")
        self.category_label.setStyleSheet("color: #CCCCCC; background: transparent; font-weight: 500;")
        self.category_layout.addWidget(self.category_label)
        
        # Container for dropdown and arrow
        self.dropdown_container = QWidget()
        self.dropdown_layout = QHBoxLayout(self.dropdown_container)
        self.dropdown_layout.setContentsMargins(0, 0, 0, 0)
        self.dropdown_layout.setSpacing(0)
        
        # Clean, minimal dropdown with no border
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: rgba(60, 60, 60, 0.5);
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 5px 10px 5px 10px;
                min-width: 120px;
                selection-background-color: {colors['accent']};
            }}
            QComboBox:hover {{
                background-color: rgba(70, 70, 70, 0.7);
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border: none;
                padding-right: 5px;
            }}
            QComboBox::down-arrow {{
                image: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: #333333;
                color: #FFFFFF;
                selection-background-color: {colors['accent']};
                selection-color: {colors['highlight_text']};
                border: 1px solid #555555;
                border-radius: 4px;
            }}
        """)
        self.category_combo.currentTextChanged.connect(self._on_category_select)
        self.dropdown_layout.addWidget(self.category_combo)
        
        # Visible down arrow label
        self.arrow_label = QLabel("▼")
        self.arrow_label.setStyleSheet("color: #CCCCCC; margin-left: -18px; background: transparent;")
        self.dropdown_layout.addWidget(self.arrow_label)
        
        # Populate initial categories
        self._update_categories()
        
        self.category_layout.addWidget(self.dropdown_container)
        self.top_bar_layout.addLayout(self.category_layout, 1)
        
        # Search box - import locally to avoid circular imports
        from .components import SearchBox
        self.search_box = SearchBox(self, "Search templates...")
        self.search_box.textChanged.connect(self._on_search)
        self.top_bar_layout.addWidget(self.search_box, 2)
        
        self.layout.addWidget(self.top_bar)

    def _setup_action_bar(self):
        """Set up the action bar with buttons for templates and folders"""
        # Action buttons - folders, templates, etc.
        self.action_bar = QWidget()
        self.action_bar.setStyleSheet("background: transparent;")
        self.action_bar_layout = QHBoxLayout(self.action_bar)
        self.action_bar_layout.setContentsMargins(10, 0, 10, 0)
        
        # Folder navigation (shown when in a folder)
        self.folder_nav = QWidget()
        self.folder_nav.setStyleSheet("background: transparent;")
        self.folder_nav_layout = QHBoxLayout(self.folder_nav)
        self.folder_nav_layout.setContentsMargins(0, 0, 0, 0)
        
        self.back_button = QPushButton("« Back to All")
        self.back_button.setStyleSheet(BUTTON_STYLE)
        self.back_button.clicked.connect(self._on_back_to_all)
        self.folder_nav_layout.addWidget(self.back_button)
        
        self.folder_label = QLabel("Current Folder: None")
        self.folder_label.setStyleSheet(f"color: {colors['text']}; font-weight: bold; background: transparent;")
        self.folder_nav_layout.addWidget(self.folder_label)
        
        self.folder_nav_layout.addStretch()
        self.folder_nav.setVisible(False)  # Hidden by default
        
        self.action_bar_layout.addWidget(self.folder_nav)
        
        # Template/folder buttons
        self.button_frame = QWidget()
        self.button_frame.setStyleSheet("background: transparent;")
        self.button_layout = QHBoxLayout(self.button_frame)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(10)
        
        self.button_layout.addStretch(1)  # Push buttons to the right
        
        # Folder management buttons
        self.add_folder_button = QPushButton("New Folder")
        self.add_folder_button.setStyleSheet(BUTTON_STYLE)
        self.add_folder_button.clicked.connect(self._on_add_folder)
        self.button_layout.addWidget(self.add_folder_button)
        
        # We're removing the rename folder button as requested
        # Keep the variable for compatibility but don't add to layout
        self.rename_folder_button = QPushButton("Rename Folder")
        self.rename_folder_button.setStyleSheet(BUTTON_STYLE)
        self.rename_folder_button.clicked.connect(self._on_rename_folder)
        self.rename_folder_button.setEnabled(False)
        # Don't add to layout: self.button_layout.addWidget(self.rename_folder_button)
        
        self.delete_folder_button = QPushButton("Delete Folder")
        self.delete_folder_button.setStyleSheet(BUTTON_STYLE)
        self.delete_folder_button.clicked.connect(self._on_delete_folder)
        self.delete_folder_button.setEnabled(False)
        self.button_layout.addWidget(self.delete_folder_button)
        
        self.button_layout.addStretch()
        
        # Template buttons
        self.add_button = QPushButton("Add Template")
        self.add_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.add_button.clicked.connect(self._on_add_template)
        self.button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Edit")
        self.edit_button.setStyleSheet(BUTTON_STYLE)
        self.edit_button.clicked.connect(self._on_edit_template)
        self.edit_button.setEnabled(False)
        self.button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.setStyleSheet(BUTTON_STYLE)
        self.delete_button.clicked.connect(self._on_delete_template)
        self.delete_button.setEnabled(False)
        self.button_layout.addWidget(self.delete_button)
        
        self.manage_button = QPushButton("Manage All")
        self.manage_button.setStyleSheet(BUTTON_STYLE)
        self.manage_button.clicked.connect(self._on_manage_templates)
        self.button_layout.addWidget(self.manage_button)
        
        self.action_bar_layout.addWidget(self.button_frame)
        self.layout.addWidget(self.action_bar)

    def _setup_gallery_containers(self):
        """Set up the gallery containers for folders and templates"""
        # Template gallery - use a main vertical layout
        self.gallery_scroll = QScrollArea()
        self.gallery_scroll.setWidgetResizable(True)
        self.gallery_scroll.setFrameShape(QFrame.NoFrame)
        self.gallery_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.gallery_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Ensure scroll area fills available space
        self.gallery_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.gallery_scroll.setStyleSheet("background: transparent; border: none;")
        
        # Main container widget with vertical layout and fixed spacing
        self.gallery_widget = QWidget()
        self.gallery_widget.setStyleSheet("background: transparent; border: none;")
        self.gallery_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.main_layout = QVBoxLayout(self.gallery_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # No margins on the main layout
        self.main_layout.setSpacing(15)  # Space between sections
        
        # Set up folders section
        self._setup_folders_section()
        
        # Set up templates section
        self._setup_templates_section()
        
        # Add the gallery widget to the scroll area
        self.gallery_scroll.setWidget(self.gallery_widget)
        
        # Add the scroll area to the main layout
        self.layout.addWidget(self.gallery_scroll)
    
    def _setup_folders_section(self):
        """Set up the folders section of the gallery"""
        # Folders section
        self.folders_section = QWidget()
        self.folders_section.setStyleSheet("background: transparent;")
        self.folders_section_layout = QVBoxLayout(self.folders_section)
        self.folders_section_layout.setContentsMargins(15, 0, 15, 15)
        
        # Folders header with view controls
        self.folders_header = QWidget()
        # Apply a subtle background to the header that spans the full width
        self.folders_header.setStyleSheet(f"""
            background-color: {colors['card_bg']};
            border: none;
        """)
        self.folders_header_layout = QHBoxLayout(self.folders_header)
        self.folders_header_layout.setContentsMargins(15, 10, 15, 10)  # Increase padding for better spacing
        
        # Folders section header
        self.folders_label = QLabel("Folders")
        self.folders_label.setFont(QFont(SYSTEM_FONT, 14, QFont.Bold))
        self.folders_label.setStyleSheet(f"color: {colors['text']}; font-weight: bold; background: transparent;")
        self.folders_header_layout.addWidget(self.folders_label)
        
        # Setup view controls
        self._setup_folder_view_controls()
        
        self.folders_section_layout.addWidget(self.folders_header)
        
        # Add a small margin between header and content
        spacer = QWidget()
        spacer.setFixedHeight(5)
        spacer.setStyleSheet("background: transparent;")
        self.folders_section_layout.addWidget(spacer)
        
        # Scrollable container for folders
        self.folders_scroll = QScrollArea()
        self.folders_scroll.setWidgetResizable(True)
        self.folders_scroll.setFrameShape(QFrame.NoFrame)
        self.folders_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.folders_scroll.setStyleSheet("background: transparent; border: none;")
        
        # Container for folder cards
        self.folders_container = QWidget()
        self.folders_container.setStyleSheet("background: transparent;")
        
        # Create a grid layout for folders
        self.folders_grid = QGridLayout(self.folders_container)
        self.folders_grid.setContentsMargins(0, 0, 0, 0)
        self.folders_grid.setSpacing(10)  # Space between cards
        
        # Set the container as the scroll area widget
        self.folders_scroll.setWidget(self.folders_container)
        self.folders_section_layout.addWidget(self.folders_scroll)
        
        # Add to main layout
        self.main_layout.addWidget(self.folders_section)

    def _setup_folder_view_controls(self):
        """Set up the folder view controls"""
        # View controls
        self.folder_view_controls = QWidget()
        self.folder_view_controls_layout = QHBoxLayout(self.folder_view_controls)
        self.folder_view_controls_layout.setContentsMargins(0, 0, 0, 0)
        self.folder_view_controls_layout.setSpacing(10)
        
        # Size control with minimal styling (no borders or backgrounds)
        self.folder_size_control = QWidget()
        self.folder_size_control.setStyleSheet("background: transparent;")
        self.folder_size_layout = QHBoxLayout(self.folder_size_control)
        self.folder_size_layout.setContentsMargins(0, 0, 0, 0)
        self.folder_size_layout.setSpacing(5)
        
        # Add small label for folder size
        self.folder_size_label = QLabel("Folder Size:")
        self.folder_size_label.setStyleSheet("color: #AAAAAA; background: transparent;")
        self.folder_size_layout.addWidget(self.folder_size_label)
        
        # Size slider
        self.folder_size_slider = QSlider(Qt.Horizontal)
        self.folder_size_slider.setRange(50, 150)  # 50% to 150% scaling
        self.folder_size_slider.setValue(self.icon_scale)  # Use current scale value
        self.folder_size_slider.setFixedWidth(100)
        self.folder_size_slider.setTickPosition(QSlider.TicksBelow)
        self.folder_size_slider.setTickInterval(25)
        self.folder_size_slider.valueChanged.connect(self._on_icon_scale_changed)
        self.folder_size_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #3C3C3C;
                height: 8px;
                background: #2A2A2A;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #909090;
                border: 1px solid #5A5A5A;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #AAAAAA;
            }
        """)
        
        # Add to layout
        self.folder_size_layout.addWidget(self.folder_size_slider)
        
        # Create an invisible placeholder with the same size as the size control
        # This will be shown when the size control is hidden to keep the layout stable
        self.size_control_placeholder = QWidget()
        self.size_control_placeholder.setFixedSize(self.folder_size_control.sizeHint())
        self.size_control_placeholder.setStyleSheet("background: transparent;")
        self.size_control_placeholder.setVisible(False)  # Hidden by default
        
        # Create a container to hold either the size control or the placeholder
        self.size_control_container = QWidget()
        self.size_control_container.setStyleSheet("background: transparent;")
        self.size_container_layout = QHBoxLayout(self.size_control_container)
        self.size_container_layout.setContentsMargins(0, 0, 0, 0)
        self.size_container_layout.setSpacing(0)
        
        # Add both controls to the container
        self.size_container_layout.addWidget(self.folder_size_control)
        self.size_container_layout.addWidget(self.size_control_placeholder)
        
        # Add the container to the view controls
        self.folder_view_controls_layout.addWidget(self.size_control_container)
        
        # Create a horizontal button group for toggling between grid and list views
        self.folder_view_buttons = QWidget()
        self.folder_view_buttons.setStyleSheet("background: transparent;")
        self.folder_view_buttons_layout = QHBoxLayout(self.folder_view_buttons)
        self.folder_view_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.folder_view_buttons_layout.setSpacing(0)
        
        self.folder_view_toggle_group = QButtonGroup(self)
        
        # Grid view button (replacing icon view)
        self.folder_grid_view_btn = QToolButton()
        self.folder_grid_view_btn.setCheckable(True)
        self.folder_grid_view_btn.setToolTip("Grid View")
        self.folder_grid_view_btn.setText("Grid")
        self.folder_grid_view_btn.setChecked(self.folder_view_mode == "grid")
        self.folder_grid_view_btn.clicked.connect(lambda: self._set_folder_view_mode("grid"))
        self.folder_grid_view_btn.setFixedSize(65, 24)
        
        # Apply styling
        self.folder_grid_view_btn.setStyleSheet("""
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
        self.folder_view_toggle_group.addButton(self.folder_grid_view_btn)
        self.folder_view_buttons_layout.addWidget(self.folder_grid_view_btn)
        
        # List view button
        self.folder_list_view_btn = QToolButton()
        self.folder_list_view_btn.setCheckable(True)
        self.folder_list_view_btn.setToolTip("List View")
        self.folder_list_view_btn.setText("List")
        self.folder_list_view_btn.setChecked(self.folder_view_mode == "list")
        self.folder_list_view_btn.clicked.connect(lambda: self._set_folder_view_mode("list"))
        self.folder_list_view_btn.setFixedSize(65, 24)  # Fixed size to prevent layout shifts
        
        # Apply the same styling as the template list view button
        self.folder_list_view_btn.setStyleSheet("""
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
        self.folder_view_toggle_group.addButton(self.folder_list_view_btn)
        self.folder_view_buttons_layout.addWidget(self.folder_list_view_btn)
        
        # Add buttons to controls
        self.folder_view_controls_layout.addWidget(self.folder_view_buttons)
        
        # Make sure folder view controls maintain their size
        self.folder_view_controls.setMinimumWidth(320)  # Increased to accommodate slider
        self.folder_view_controls.setMaximumWidth(320)
        self.folder_view_controls.setFixedHeight(30)
        self.folder_view_controls.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Add folder view controls to the header layout
        self.folders_header_layout.addWidget(self.folder_view_controls)
    
    def _setup_templates_section(self):
        """Set up the templates section of the gallery"""
        # Templates section
        self.templates_section = QWidget()
        self.templates_section.setStyleSheet("background: transparent;")
        self.templates_section_layout = QVBoxLayout(self.templates_section)
        self.templates_section_layout.setContentsMargins(15, 0, 15, 15)  # Add padding on sides for consistent layout
        self.templates_section_layout.setSpacing(5)
        # Set a maximum width and policy to prevent excessive expansion
        self.templates_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.templates_section.setMaximumWidth(1200)
        
        # Templates header with view controls
        self._setup_templates_header()
        
        # Add a small margin between header and content
        spacer = QWidget()
        spacer.setFixedHeight(5)
        spacer.setStyleSheet("background: transparent;")
        self.templates_section_layout.addWidget(spacer)
        
        # Scrollable area for templates
        self.templates_scroll = QScrollArea()
        self.templates_scroll.setWidgetResizable(True)
        self.templates_scroll.setFrameShape(QFrame.NoFrame)
        self.templates_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.templates_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.templates_scroll.setStyleSheet("background: transparent; border: none;")
        # Ensure scroll area fills available space
        self.templates_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Container for templates
        self.templates_container = QWidget()
        self.templates_container.setStyleSheet("background: transparent;")
        self.templates_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.templates_grid = QGridLayout(self.templates_container)
        self.templates_grid.setContentsMargins(0, 0, 0, 0)
        self.templates_grid.setHorizontalSpacing(6)
        self.templates_grid.setVerticalSpacing(12)
        self.templates_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.templates_scroll.setWidget(self.templates_container)
        self.templates_section_layout.addWidget(self.templates_scroll)
        
        # Add templates section to main layout
        self.main_layout.addWidget(self.templates_section)
    
    def _setup_templates_header(self):
        """Set up the templates header with view controls"""
        # Templates header with view controls
        self.templates_header_container = QWidget()
        # Apply a subtle background to the header that spans the full width
        self.templates_header_container.setStyleSheet(f"""
            background-color: {colors['card_bg']};
            border: none;
        """)
        self.templates_header_container.setFixedHeight(50)  # Slightly taller for better proportions
        self.templates_header_layout = QHBoxLayout(self.templates_header_container)
        self.templates_header_layout.setContentsMargins(15, 10, 15, 10)  # Increase padding for better spacing
        self.templates_header_layout.setSpacing(10)
        
        # Template title
        self.templates_header = QLabel("Templates")
        self.templates_header.setFont(QFont(SYSTEM_FONT, 14, QFont.Bold))
        self.templates_header.setStyleSheet(f"color: {colors['text']}; padding: 5px 0; background-color: transparent;")
        self.templates_header.setAlignment(Qt.AlignLeft)
        self.templates_header.setFixedHeight(30)
        self.templates_header.setFixedWidth(120)
        self.templates_header.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.templates_header_layout.addWidget(self.templates_header)
        
        # Add spacer to push buttons to the right
        self.templates_header_layout.addStretch(1)
        
        # Template view controls - similar layout to folder view controls
        self.template_view_controls = QWidget()
        self.template_view_controls.setStyleSheet("background: transparent;")
        self.template_view_controls_layout = QHBoxLayout(self.template_view_controls)
        self.template_view_controls_layout.setContentsMargins(0, 0, 0, 0)
        self.template_view_controls_layout.setSpacing(10)
        
        # Create a button group for view toggle
        self.template_view_buttons = QWidget()
        self.template_view_buttons.setStyleSheet("background: transparent;")
        self.template_view_buttons_layout = QHBoxLayout(self.template_view_buttons)
        self.template_view_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.template_view_buttons_layout.setSpacing(0)  # No spacing between buttons
        
        self.template_view_toggle_group = QButtonGroup(self)
        
        # Grid view button
        self.template_grid_view_btn = QToolButton()
        self.template_grid_view_btn.setCheckable(True)
        self.template_grid_view_btn.setToolTip("Grid View")
        self.template_grid_view_btn.setText("Grid")
        self.template_grid_view_btn.setChecked(self.template_view_mode == "grid")
        self.template_grid_view_btn.clicked.connect(lambda: self._set_template_view_mode("grid"))
        self.template_grid_view_btn.setFixedSize(65, 24)
        
        # Apply same styling as folder buttons
        self.template_grid_view_btn.setStyleSheet("""
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
        self.template_view_toggle_group.addButton(self.template_grid_view_btn)
        self.template_view_buttons_layout.addWidget(self.template_grid_view_btn)
        
        # List view button
        self.template_list_view_btn = QToolButton()
        self.template_list_view_btn.setCheckable(True)
        self.template_list_view_btn.setToolTip("List View")
        self.template_list_view_btn.setText("List")
        self.template_list_view_btn.setChecked(self.template_view_mode == "list")
        self.template_list_view_btn.clicked.connect(lambda: self._set_template_view_mode("list"))
        self.template_list_view_btn.setFixedSize(65, 24)
        
        # Apply same styling as folder buttons
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
        
        # Add buttons widget to controls
        self.template_view_controls_layout.addWidget(self.template_view_buttons)
        
        # Set fixed size for controls to prevent layout shifting
        self.template_view_controls.setFixedHeight(30)
        self.template_view_controls.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Add template view controls to the header layout
        self.templates_header_layout.addWidget(self.template_view_controls)
        
        # Add header container to section layout
        self.templates_section_layout.addWidget(self.templates_header_container)

    def populate_gallery(self, force_refresh=False):
        """Populate the gallery with templates and folders"""
        # Make sure UI is set up before populating
        if not hasattr(self, 'folders_grid') or self.folders_grid is None or not hasattr(self, 'templates_grid') or self.templates_grid is None:
            # UI not fully set up yet, defer population
            return
            
        self.clear_gallery()
        
        # Check if we have a template_manager attribute in the app
        if hasattr(self.app, 'template_manager'):
            # Use template_manager if available
            if hasattr(self.app.template_manager, 'templates'):
                templates = self.app.template_manager.templates
            else:
                templates = {}
                
            if hasattr(self.app.template_manager, 'get_folders'):
                folders = self.app.template_manager.get_folders()
            else:
                folders = []
            
            # Set visibility based on current context
            if self.current_folder:
                # Inside a folder - hide folders section, show only templates
                self.folders_section.setVisible(False)
                self.folder_nav.setVisible(True)
                
                # Update templates header to indicate folder context
                if hasattr(self, 'templates_header'):
                    self.templates_header.setText(f"Templates in '{self.current_folder}'")
            else:
                # Root view - show both folders and templates
                self.folders_section.setVisible(True)
                self.folder_nav.setVisible(False)
                
                # Reset templates header to default
                if hasattr(self, 'templates_header'):
                    self.templates_header.setText("Templates")
                
                # Populate folders section based on view mode
                if self.folder_view_mode == "grid":
                    self._populate_folders_grid(folders)
                else:
                    self._populate_folders_list(folders)
            
            # Populate templates section based on current context
            if self.current_folder:
                # Show templates in the current folder
                templates_to_show = self.get_templates_in_folder(self.current_folder)
            else:
                # Show templates not in any folder
                templates_to_show = {}
                if isinstance(templates, dict):
                    # Check which folder approach is being used
                    if hasattr(self.app.template_manager, 'folders'):
                        # Using the folders dictionary approach (original approach)
                        # Get all template names that are in any folder
                        templates_in_folders = set()
                        for folder_name, template_list in self.app.template_manager.folders.items():
                            templates_in_folders.update(template_list)
                        
                        # Only show templates not in any folder
                        for name, data in templates.items():
                            if name not in templates_in_folders:
                                templates_to_show[name] = data
                    else:
                        # Using the direct folder property approach
                        for name, data in templates.items():
                            if not data.get("folder"):
                                templates_to_show[name] = data
                elif isinstance(templates, list):
                    # Check which folder approach is being used
                    if hasattr(self.app.template_manager, 'folders'):
                        # Using the folders dictionary approach
                        templates_in_folders = set()
                        for folder_name, template_list in self.app.template_manager.folders.items():
                            templates_in_folders.update(template_list)
                        
                        # Only show templates not in any folder
                        templates_to_show = {t.get('name', f"Template-{i}"): t for i, t in enumerate(templates) 
                                            if t.get('name') not in templates_in_folders}
                    else:
                        # Using the direct folder property approach
                        templates_to_show = {t.get('name', f"Template-{i}"): t for i, t in enumerate(templates) 
                                          if not t.get("folder")}
            
            # Populate templates based on view mode
            if self.template_view_mode == "grid":
                self._populate_templates_grid(templates_to_show)
            else:
                self._populate_templates_list(templates_to_show)
            
            # Update button states
            self._update_button_state()
            
            # Mark templates as loaded
            self.templates_loaded = True
        else:
            print("DEBUG: app.template_manager not found!")
    
    def clear_gallery(self):
        """Clear the gallery containers"""
        # Clear folders grid
        if hasattr(self, 'folders_grid') and self.folders_grid is not None:
            for i in reversed(range(self.folders_grid.count())):
                widget = self.folders_grid.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
        
        # Clear templates grid
        if hasattr(self, 'templates_grid') and self.templates_grid is not None:
            for i in reversed(range(self.templates_grid.count())):
                widget = self.templates_grid.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
    
    def on_template_clicked(self, template_name):
        """Legacy method for compatibility"""
        print(f"Template clicked: {template_name}")
        # Find the template data and emit the signal
        if hasattr(self.app, 'template_manager'):
            templates = self.app.template_manager.templates
            if isinstance(templates, dict) and template_name in templates:
                self._on_template_select(templates[template_name])
    
    def on_folder_clicked(self, folder_name):
        """Legacy method for compatibility"""
        print(f"Folder clicked: {folder_name}")
        self._on_folder_select(folder_name)
    
    # Event handlers
    def _on_category_select(self, category):
        """Handle category selection"""
        self.current_category = category
        self.populate_gallery()
    
    def _on_search(self, search_text):
        """Handle search text changes"""
        self.current_search = search_text
        self.populate_gallery()
    
    def _on_template_select(self, template):
        """Handle template selection"""
        self.selected_template = template
        
        # Update selection state of all template cards
        for card in self.template_cards:
            if hasattr(card, 'template') and card.template == template:
                card.set_selected(True)
            else:
                card.set_selected(False)
        
        # Update button states
        self.edit_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        
        # Ensure template is a dictionary before emitting
        if isinstance(template, str):
            # Convert string to dictionary
            template_dict = {"name": template}
            self.template_selected.emit(template_dict)
        elif isinstance(template, dict):
            # Already a dictionary, emit as is
            self.template_selected.emit(template)
        else:
            # Try to convert to dictionary
            try:
                template_dict = dict(template)
                self.template_selected.emit(template_dict)
            except (TypeError, ValueError):
                # Last resort: create a new dictionary with the template as name
                template_dict = {"name": str(template)}
                self.template_selected.emit(template_dict)
    
    def _on_folder_select(self, folder_name):
        """Handle folder selection"""
        self.selected_folder = folder_name
        
        # Update selection state of all folder cards
        for card in self.folder_cards:
            if hasattr(card, 'folder_name') and card.folder_name == folder_name:
                card.set_selected(True)
            else:
                card.set_selected(False)
        
        # Update button states
        self.delete_folder_button.setEnabled(True)
        self.rename_folder_button.setEnabled(True)
        
        # Emit signal
        self.folder_selected.emit(folder_name)
    
    def _on_folder_enter(self, folder_name):
        """Handle entering a folder"""
        if folder_name in self.app.template_manager.get_folders():
            # Update UI to reflect we're in a folder
            self.current_folder = folder_name
            
            # Update folder label
            self.folder_label.setText(f"Current Folder: {folder_name}")
            
            # Show folder navigation
            self.folder_nav.setVisible(True)
            
            # Hide the folders section when inside a folder
            self.folders_section.setVisible(False)
            
            # Update the templates header to indicate folder context
            if hasattr(self, 'templates_header'):
                self.templates_header.setText(f"Templates in '{folder_name}'")
            
            # Refresh gallery to show templates in the folder
            self.populate_gallery()
            
            # Emit folder selected signal
            self.folder_selected.emit(folder_name)
    
    def _on_back_to_all(self):
        """Handle going back to the main view"""
        # Clear current folder
        self.current_folder = None
        
        # Update folder label
        self.folder_label.setText("Current Folder: None")
        
        # Hide folder navigation
        self.folder_nav.setVisible(False)
        
        # Show the folders section when back at root
        self.folders_section.setVisible(True)
        
        # Reset the templates header
        if hasattr(self, 'templates_header'):
            self.templates_header.setText("Templates")
        
        # Reset selection
        self.selected_folder = None
        
        # Refresh gallery
        self.populate_gallery()
    
    def get_templates_in_folder(self, folder_name):
        """Get templates in the specified folder"""
        result = {}
        if hasattr(self.app, 'template_manager'):
            # Check which approach the template manager is using
            
            # First try the 'folders' dictionary approach (original approach)
            if hasattr(self.app.template_manager, 'folders') and folder_name in self.app.template_manager.folders:
                template_names = self.app.template_manager.folders[folder_name]
                if template_names:
                    templates = self.app.template_manager.templates
                    for name in template_names:
                        # Try to find template in both dictionary and list formats
                        if isinstance(templates, dict):
                            if name in templates:
                                result[name] = templates[name]
                        elif isinstance(templates, list):
                            for t in templates:
                                if t.get('name') == name:
                                    result[name] = t
                                    break
                return result
            
            # If that doesn't work, try the direct 'folder' property approach (TEST_REFACT approach)
            templates = self.app.template_manager.templates
            if isinstance(templates, dict):
                for name, data in templates.items():
                    if data.get("folder") == folder_name:
                        result[name] = data
        return result
    
    def _update_categories(self):
        """Update the category dropdown with available categories"""
        if hasattr(self.app, 'template_manager'):
            categories = ["All"]
            if hasattr(self.app.template_manager, 'get_categories'):
                categories.extend(self.app.template_manager.get_categories())
            
            self.category_combo.clear()
            for category in categories:
                self.category_combo.addItem(category)

    def _update_button_state(self):
        """Update button states based on selection"""
        has_template_selected = self.selected_template is not None
        has_folder_selected = self.selected_folder is not None
        
        self.edit_button.setEnabled(has_template_selected)
        self.delete_button.setEnabled(has_template_selected)
        self.delete_folder_button.setEnabled(has_folder_selected)
        self.rename_folder_button.setEnabled(has_folder_selected)
    
    def _handle_resize_timeout(self):
        """Handle resize events after a timeout to prevent excessive updates"""
        self._update_layout_after_resize()
    
    def _update_layout_after_resize(self):
        """Update layout after resize"""
        # Recalculate grid columns based on available width
        self._update_card_sizes()
    
    def _on_icon_scale_changed(self, value):
        """Handle icon scale change"""
        self.icon_scale = value
        # Only update folder card sizes, not templates
        self._update_folder_card_sizes(value)
        
    def _update_card_sizes(self):
        """Update card sizes based on current scale"""
        # Only update folder sizes, not templates
        self._update_folder_card_sizes(self.icon_scale)
    
    def _update_folder_card_sizes(self, scale_percent):
        """Update folder card sizes based on scale percentage"""
        if self.folder_view_mode == "list":
            # List view has fixed height, no resizing needed
            return
            
        # Grid view - resize just the icons, not the entire card
        for card in self.folder_cards:
            if hasattr(card, 'resize_icon'):
                card.resize_icon(scale_percent)
            # No need to resize the card itself
    
    def _set_folder_view_mode(self, mode):
        """Set the folder view mode (grid or list)"""
        if self.folder_view_mode == mode:
            return
            
        self.folder_view_mode = mode
        
        # Update button states
        self.folder_grid_view_btn.setChecked(mode == "grid")
        self.folder_list_view_btn.setChecked(mode == "list")
        
        # Swap between the size control and placeholder to keep buttons in position
        if hasattr(self, 'folder_size_control') and hasattr(self, 'size_control_placeholder'):
            if mode == "grid":
                # In grid view, show size control, hide placeholder
                self.folder_size_control.setVisible(True)
                self.size_control_placeholder.setVisible(False)
            else:
                # In list view, hide size control, show placeholder
                self.folder_size_control.setVisible(False)
                self.size_control_placeholder.setVisible(True)
        
        # Clear current layouts
        self.clear_gallery()
        
        # Recreate with new view mode
        self.populate_gallery()
    
    def _set_template_view_mode(self, mode):
        """Set the template view mode (grid or list)"""
        if self.template_view_mode == mode:
            return
            
        self.template_view_mode = mode
        
        # Update button states
        self.template_grid_view_btn.setChecked(mode == "grid")
        self.template_list_view_btn.setChecked(mode == "list")
        
        # Clear current layouts
        self.clear_gallery()
        
        # Recreate with new view mode
        self.populate_gallery()
    
    # Template and folder management methods
    def _on_add_template(self):
        """Handle add template button click"""
        if hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'add_template'):
            self.app.template_manager.add_template()
            self.populate_gallery()
    
    def _on_edit_template(self):
        """Handle edit template button click"""
        if self.selected_template and hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'edit_template'):
            self.app.template_manager.edit_template(self.selected_template)
            self.populate_gallery()
    
    def _on_delete_template(self):
        """Handle delete template button click"""
        if self.selected_template and hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'delete_template'):
            self.app.template_manager.delete_template(self.selected_template)
            self.selected_template = None
            self.populate_gallery()
    
    def _on_manage_templates(self):
        """Handle manage templates button click"""
        if hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'manage_templates'):
            self.app.template_manager.manage_templates()
            self.populate_gallery()
    
    def _on_add_folder(self):
        """Handle add folder button click"""
        if hasattr(self.app, 'template_manager'):
            # Get folder name from dialog
            folder_name, ok = QInputDialog.getText(None, "Add Folder", "Folder Name:")
            if ok and folder_name:
                self.app.template_manager.create_folder(folder_name)
                self.populate_gallery()
    
    def _on_rename_folder(self):
        """Handle rename folder button click"""
        if self.selected_folder:
            # Find the selected folder card and trigger rename
            for card in self.folder_cards:
                if hasattr(card, '_start_rename'):
                    card._start_rename()
                    break
    
    def _on_rename_folder_requested(self, folder_name):
        """Handle rename folder requested signal"""
        self.selected_folder = folder_name
    
    def _on_rename_folder_done(self, old_name, new_name):
        """Handle rename folder done signal"""
        if hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'rename_folder'):
            self.app.template_manager.rename_folder(old_name, new_name)
            self.selected_folder = new_name
            self.populate_gallery()
    
    def _on_delete_folder(self):
        """Handle delete folder button click"""
        if self.selected_folder and hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'delete_folder'):
            self.app.template_manager.delete_folder(self.selected_folder)
            self.selected_folder = None
            self.populate_gallery()

    def _populate_folders_grid(self, folders):
        """Populate folders in grid view"""
        self.folder_cards = []
        
        # Grid layout parameters
        col = 0
        row = 0
        max_cols = 4  # Default number of columns
        
        # Import the folder card class
        from .components.template_folder_card import TemplateFolderCard
        
        for folder in folders:
            folder_card = TemplateFolderCard(self, folder_name=folder, app=self.app)
            folder_card.clicked.connect(self._on_folder_select)
            folder_card.doubleClicked.connect(self._on_folder_enter)
            folder_card.renameRequested.connect(self._on_rename_folder_requested)
            folder_card.renameDone.connect(self._on_rename_folder_done)
            
            self.folders_grid.addWidget(folder_card, row, col)
            self.folder_cards.append(folder_card)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def _populate_folders_list(self, folders):
        """Populate folders in list view"""
        self.folder_cards = []
        
        # List layout - one column
        row = 0
        
        # Import the folder list item class
        from .components.template_folder_card import TemplateFolderListItem
        
        # Sort folders alphabetically
        for i, folder in enumerate(sorted(folders)):
            folder_item = TemplateFolderListItem(self, folder_name=folder, app=self.app)
            folder_item.clicked.connect(self._on_folder_select)
            folder_item.doubleClicked.connect(self._on_folder_enter)
            folder_item.renameRequested.connect(self._on_rename_folder_requested)
            folder_item.renameDone.connect(self._on_rename_folder_done)
            
            # Set alternate row color property
            folder_item.setProperty("row_type", "odd" if i % 2 else "even")
            
            # Force style update
            folder_item.style().unpolish(folder_item)
            folder_item.style().polish(folder_item)
            folder_item._update_styling()
            
            self.folders_grid.addWidget(folder_item, row, 0)
            self.folder_cards.append(folder_item)
            row += 1
    
    def _populate_templates_grid(self, templates_to_show):
        """Populate templates in grid view"""
        self.template_cards = []
        
        # Grid layout parameters
        col = 0
        row = 0
        max_cols = 4  # Default number of columns
        
        # Import the template card class
        from .components.template_card import TemplateCard
        
        for name, data in templates_to_show.items():
            template_card = TemplateCard(self, template=data, app=self.app)
            
            # Make sure we're passing the template data dictionary, not just the name
            if isinstance(data, dict):
                template_data = data
            else:
                # If data is not a dictionary, create one with the name
                template_data = {"name": name}
                
            # Connect the click handler with the template data
            template_card.clicked.connect(lambda checked=False, t=template_data: self._on_template_select(t))
            
            self.templates_grid.addWidget(template_card, row, col)
            self.template_cards.append(template_card)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def _populate_templates_list(self, templates_to_show):
        """Populate templates in list view"""
        self.template_cards = []
        
        # List layout - one column
        row = 0
        
        # Import the template list item class from the template_card module
        from .components.template_card import TemplateListItem
        
        # Sort templates alphabetically for consistent ordering
        sorted_templates = []
        for name, data in templates_to_show.items():
            sorted_templates.append((name, data))
        sorted_templates.sort(key=lambda x: x[0].lower())  # Sort by name case-insensitive
        
        # Create list items with alternating colors
        for i, (name, data) in enumerate(sorted_templates):
            template_item = TemplateListItem(self, template=data, app=self.app)
            
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
            template_item.clicked.connect(lambda checked=False, t=template_data: self._on_template_select(t))
            
            self.templates_grid.addWidget(template_item, row, 0)
            self.template_cards.append(template_item)
            row += 1

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
                if hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'delete_folder'):
                    self.app.template_manager.delete_folder(self.selected_folder)
                    self.selected_folder = None
                    self.populate_gallery(force_refresh=True)
        else:
            super().keyPressEvent(event)

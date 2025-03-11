#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QFrame, QScrollArea, QGridLayout, QComboBox, QButtonGroup, 
                           QToolButton, QSlider, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from app.ui.color_scheme_pyqt import colors, get_color, BUTTON_STYLE, ACCENT_BUTTON_STYLE
from .components.utils import SYSTEM_FONT
from .components.components import SearchBox

class GalleryUISetup:
    """UI setup methods for the Template Gallery"""
    
    @staticmethod
    def setup_ui(gallery):
        """Set up the UI components"""
        # Main layout
        gallery.layout = QVBoxLayout(gallery)
        gallery.layout.setContentsMargins(0, 0, 0, 0)
        gallery.layout.setSpacing(0)  # No space between components
        
        # Top bar with category filter and search
        GalleryUISetup.setup_top_bar(gallery)
        
        # Action bar with buttons
        GalleryUISetup.setup_action_bar(gallery)
        
        # Add a fixed margin frame between action bar and content
        gallery.margin_frame = QFrame()
        gallery.margin_frame.setFixedHeight(10)  # Fixed spacing
        gallery.margin_frame.setStyleSheet("background-color: transparent;")
        gallery.layout.addWidget(gallery.margin_frame)
        
        # Set up the gallery containers
        GalleryUISetup.setup_gallery_containers(gallery)
    
    @staticmethod
    def setup_top_bar(gallery):
        """Set up the top bar with category filter and search"""
        # Top bar for search, filter and actions
        gallery.top_bar = QWidget()
        gallery.top_bar.setStyleSheet("background: transparent;")
        gallery.top_bar_layout = QHBoxLayout(gallery.top_bar)
        gallery.top_bar_layout.setContentsMargins(10, 5, 10, 5)
        
        # Category filter with horizontal layout
        gallery.category_layout = QHBoxLayout()
        gallery.category_layout.setContentsMargins(0, 0, 0, 0)
        gallery.category_layout.setSpacing(5)  # Small spacing between label and dropdown
        
        # Clean, minimal category label
        gallery.category_label = QLabel("Category:")
        gallery.category_label.setStyleSheet("color: #CCCCCC; background: transparent; font-weight: 500;")
        gallery.category_layout.addWidget(gallery.category_label)
        
        # Container for dropdown and arrow
        gallery.dropdown_container = QWidget()
        gallery.dropdown_layout = QHBoxLayout(gallery.dropdown_container)
        gallery.dropdown_layout.setContentsMargins(0, 0, 0, 0)
        gallery.dropdown_layout.setSpacing(0)
        
        # Clean, minimal dropdown with no border
        gallery.category_combo = QComboBox()
        gallery.category_combo.setStyleSheet(f"""
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
        gallery.category_combo.currentTextChanged.connect(gallery._on_category_select)
        gallery.dropdown_layout.addWidget(gallery.category_combo)
        
        # Visible down arrow label
        gallery.arrow_label = QLabel("▼")
        gallery.arrow_label.setStyleSheet("color: #CCCCCC; margin-left: -18px; background: transparent;")
        gallery.dropdown_layout.addWidget(gallery.arrow_label)
        
        # Populate initial categories
        gallery._update_categories()
        
        gallery.category_layout.addWidget(gallery.dropdown_container)
        gallery.top_bar_layout.addLayout(gallery.category_layout, 1)
        
        # Search box
        gallery.search_box = SearchBox(gallery, "Search templates...")
        gallery.search_box.textChanged.connect(gallery._on_search)
        gallery.top_bar_layout.addWidget(gallery.search_box, 2)
        
        gallery.layout.addWidget(gallery.top_bar)

    @staticmethod
    def setup_action_bar(gallery):
        """Set up the action bar with buttons for templates and folders"""
        # Action buttons - folders, templates, etc.
        gallery.action_bar = QWidget()
        gallery.action_bar.setStyleSheet("background: transparent;")
        gallery.action_bar_layout = QHBoxLayout(gallery.action_bar)
        gallery.action_bar_layout.setContentsMargins(10, 0, 10, 0)
        
        # Folder navigation (shown when in a folder)
        gallery.folder_nav = QWidget()
        gallery.folder_nav.setStyleSheet("background: transparent;")
        gallery.folder_nav_layout = QHBoxLayout(gallery.folder_nav)
        gallery.folder_nav_layout.setContentsMargins(0, 0, 0, 0)
        
        gallery.back_button = QPushButton("« Back to All")
        gallery.back_button.setStyleSheet(BUTTON_STYLE)
        gallery.back_button.clicked.connect(gallery._on_back_to_all)
        gallery.folder_nav_layout.addWidget(gallery.back_button)
        
        gallery.folder_label = QLabel("Current Folder: None")
        gallery.folder_label.setStyleSheet(f"color: {colors['text']}; font-weight: bold; background: transparent;")
        gallery.folder_nav_layout.addWidget(gallery.folder_label)
        
        gallery.folder_nav_layout.addStretch()
        gallery.folder_nav.setVisible(False)  # Hidden by default
        
        gallery.action_bar_layout.addWidget(gallery.folder_nav)
        
        # Template/folder buttons
        gallery.button_frame = QWidget()
        gallery.button_frame.setStyleSheet("background: transparent;")
        gallery.button_layout = QHBoxLayout(gallery.button_frame)
        gallery.button_layout.setContentsMargins(0, 0, 0, 0)
        gallery.button_layout.setSpacing(10)
        
        gallery.button_layout.addStretch(1)  # Push buttons to the right
        
        # Folder management buttons
        gallery.add_folder_button = QPushButton("New Folder")
        gallery.add_folder_button.setStyleSheet(BUTTON_STYLE)
        gallery.add_folder_button.clicked.connect(gallery._on_add_folder)
        gallery.button_layout.addWidget(gallery.add_folder_button)
        
        gallery.rename_folder_button = QPushButton("Rename Folder")
        gallery.rename_folder_button.setStyleSheet(BUTTON_STYLE)
        gallery.rename_folder_button.clicked.connect(gallery._on_rename_folder)
        gallery.rename_folder_button.setEnabled(False)
        # Not adding to layout as per original code
        
        gallery.delete_folder_button = QPushButton("Delete Folder")
        gallery.delete_folder_button.setStyleSheet(BUTTON_STYLE)
        gallery.delete_folder_button.clicked.connect(gallery._on_delete_folder)
        gallery.delete_folder_button.setEnabled(False)
        gallery.button_layout.addWidget(gallery.delete_folder_button)
        
        gallery.button_layout.addStretch()
        
        # Template buttons
        gallery.add_button = QPushButton("Add Template")
        gallery.add_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        gallery.add_button.clicked.connect(gallery._on_add_template)
        gallery.button_layout.addWidget(gallery.add_button)
        
        gallery.edit_button = QPushButton("Edit")
        gallery.edit_button.setStyleSheet(BUTTON_STYLE)
        gallery.edit_button.clicked.connect(gallery._on_edit_template)
        gallery.edit_button.setEnabled(False)
        gallery.button_layout.addWidget(gallery.edit_button)
        
        gallery.delete_button = QPushButton("Delete")
        gallery.delete_button.setStyleSheet(BUTTON_STYLE)
        gallery.delete_button.clicked.connect(gallery._on_delete_template)
        gallery.delete_button.setEnabled(False)
        gallery.button_layout.addWidget(gallery.delete_button)
        
        gallery.manage_button = QPushButton("Manage All")
        gallery.manage_button.setStyleSheet(BUTTON_STYLE)
        gallery.manage_button.clicked.connect(gallery._on_manage_templates)
        gallery.button_layout.addWidget(gallery.manage_button)
        
        gallery.action_bar_layout.addWidget(gallery.button_frame)
        gallery.layout.addWidget(gallery.action_bar)

    @staticmethod
    def setup_gallery_containers(gallery):
        """Set up the gallery containers for folders and templates"""
        # Template gallery - use a main vertical layout
        gallery.gallery_scroll = QScrollArea()
        gallery.gallery_scroll.setWidgetResizable(True)
        gallery.gallery_scroll.setFrameShape(QFrame.NoFrame)
        gallery.gallery_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        gallery.gallery_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Ensure scroll area fills available space
        gallery.gallery_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        gallery.gallery_scroll.setStyleSheet("background: transparent; border: none;")
        
        # Main container widget with vertical layout and fixed spacing
        gallery.gallery_widget = QWidget()
        gallery.gallery_widget.setStyleSheet("background: transparent; border: none;")
        gallery.gallery_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        gallery.main_layout = QVBoxLayout(gallery.gallery_widget)
        gallery.main_layout.setContentsMargins(0, 0, 0, 0)  # No margins on the main layout
        gallery.main_layout.setSpacing(15)  # Space between sections
        
        # Import the setup classes here to avoid circular imports
        from .gallery_folders import GalleryFoldersSetup
        from .gallery_templates import GalleryTemplatesSetup
        
        # Set up folders section
        GalleryFoldersSetup.setup_folders_section(gallery)
        
        # Set up templates section
        GalleryTemplatesSetup.setup_templates_section(gallery)
        
        # Add the gallery widget to the scroll area
        gallery.gallery_scroll.setWidget(gallery.gallery_widget)
        
        # Add the scroll area to the main layout
        gallery.layout.addWidget(gallery.gallery_scroll)

    # Note: Additional setup methods will be defined in gallery_folders.py and gallery_templates.py 
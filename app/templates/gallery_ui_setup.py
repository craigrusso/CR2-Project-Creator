#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QFrame, QScrollArea, QGridLayout, QComboBox, QButtonGroup, 
                           QToolButton, QSlider, QSizePolicy, QSplitter)
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
        
        # Top bar with project type filter and search
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
        """Set up the top bar with search box"""
        # Create top bar container with layout
        gallery.top_bar_container = QWidget()
        gallery.top_bar_container.setObjectName("topBarContainer")
        gallery.top_bar_container.setStyleSheet("""
            QWidget#topBarContainer {
                background-color: #2d2d2d;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        # Create layout for the top bar container
        gallery.top_bar_layout = QHBoxLayout(gallery.top_bar_container)
        gallery.top_bar_layout.setContentsMargins(10, 5, 10, 5)
        gallery.top_bar_layout.setSpacing(10)
        
        # Create New Structure button - moved to templates section
        # gallery.new_structure_button = QPushButton("Create New Structure")
        # gallery.new_structure_button.setStyleSheet(BUTTON_STYLE)
        
        # Fix the structure editor call by using a callback to the main app
        from app.dialogs.dialog_windows_pyqt import show_structure_editor
        
        # Define a safer handler that checks for app availability
        def show_structure_editor_handler():
            # Get the parent app if available
            parent_app = None
            if hasattr(gallery, 'app') and gallery.app is not None:
                parent_app = gallery.app
            elif hasattr(gallery, 'parent') and callable(gallery.parent) and gallery.parent() is not None:
                parent_app = gallery.parent()
            
            if parent_app is not None:
                # Create a custom implementation of show_enhanced_structure_editor
                # that handles missing template_manager
                from app.constants import DEFAULT_STRUCTURES
                from app.ui.structure_editor_enhanced import EnhancedStructureEditor
                
                # Create a modified editor with fallback for template_manager
                class EnhancedStructureEditorWithFallback(EnhancedStructureEditor):
                    def __init__(self, parent, **kwargs):
                        # First ensure the parent has a template_manager attribute
                        if not hasattr(parent, 'template_manager') or parent.template_manager is None:
                            # Create a basic template_manager with just what we need for the dropdown
                            class BasicTemplateManager:
                                def __init__(self):
                                    self.custom_structures = {}
                                
                                def get_structure(self, name):
                                    print(f"BasicTemplateManager: get_structure called with name={name}")
                                    if not name:
                                        return []
                                    
                                    # Check if it's a built-in structure (case-insensitive)
                                    name_lower = name.lower()
                                    for key in DEFAULT_STRUCTURES:
                                        if key.lower() == name_lower:
                                            print(f"BasicTemplateManager: Found built-in structure: {key}")
                                            return DEFAULT_STRUCTURES[key]
                                    
                                    print(f"BasicTemplateManager: Structure not found: {name}")
                                    return []
                            
                            parent.template_manager = BasicTemplateManager()
                        
                        # Call the original constructor
                        super().__init__(parent, **kwargs)
                        
                        # Ensure dropdown is populated with built-in structures
                        self.populate_structure_dropdown()
                
                # Create and show the editor
                editor = EnhancedStructureEditorWithFallback(
                    parent_app,
                    structure_name=None,
                    is_new=True,
                    project_type=None
                )
                editor.exec_()
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(gallery, "Error", "Could not access application context.")
        
        # Button moved to templates section, so don't connect event handler here
        # gallery.new_structure_button.clicked.connect(show_structure_editor_handler)
        # gallery.top_bar_layout.addWidget(gallery.new_structure_button)
        
        # No need for stretcher since we don't have the button anymore
        # gallery.top_bar_layout.addStretch(1)
        
        # Add search box to top bar
        GalleryUISetup.add_search_box(gallery)
        
        # Add the top bar container to the main layout
        gallery.layout.addWidget(gallery.top_bar_container)

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
        gallery.add_folder_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        gallery.add_folder_button.clicked.connect(gallery._on_add_folder)
        gallery.button_layout.addWidget(gallery.add_folder_button)
        
        gallery.rename_folder_button = QPushButton("Rename Folder")
        gallery.rename_folder_button.setStyleSheet(BUTTON_STYLE)
        gallery.rename_folder_button.clicked.connect(gallery._on_rename_folder)
        gallery.rename_folder_button.setEnabled(False)
        # Not adding to layout as per original code
        
        # Delete folder button removed as it's not needed - we can delete with keystroke and context menu
        
        gallery.button_layout.addStretch()
        
        # Template buttons
        # Moved to templates header area for better UX
        # gallery.add_button = QPushButton("Add Template")
        # gallery.add_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        # gallery.add_button.clicked.connect(gallery._on_add_template)
        # gallery.button_layout.addWidget(gallery.add_button)
        
        # Removing the "Manage All" button as it's redundant with other functionality
        # gallery.manage_button = QPushButton("Manage All")
        # gallery.manage_button.setStyleSheet(BUTTON_STYLE)
        # gallery.manage_button.clicked.connect(gallery._on_manage_templates)
        # gallery.button_layout.addWidget(gallery.manage_button)
        
        gallery.action_bar_layout.addWidget(gallery.button_frame)
        gallery.layout.addWidget(gallery.action_bar)

    @staticmethod
    def setup_gallery_containers(gallery):
        """Set up the gallery containers for folders and templates"""
        # Add QSplitter import
        from PyQt5.QtWidgets import QSplitter
        
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
        
        # Create a splitter widget
        gallery.content_splitter = QSplitter(Qt.Vertical)  # Vertical splitter for top/bottom sections
        gallery.content_splitter.setChildrenCollapsible(False)  # Don't allow sections to be collapsed
        gallery.content_splitter.setHandleWidth(5)  # Slightly wider handle for easier grabbing
        gallery.content_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555555;
                border: 1px solid #666666;
            }
            QSplitter::handle:hover {
                background-color: #777777;
            }
        """)
        
        # Set up folders section
        GalleryFoldersSetup.setup_folders_section(gallery)
        
        # Set up templates section
        GalleryTemplatesSetup.setup_templates_section(gallery)
        
        # Add sections to the splitter
        gallery.content_splitter.addWidget(gallery.folders_section)
        gallery.content_splitter.addWidget(gallery.templates_section)
        
        # Set the initial sizes (40% folders, 60% templates)
        gallery.content_splitter.setSizes([400, 600])  # Use actual pixel values, not percentages
        
        # Add the splitter to the main layout
        gallery.main_layout.addWidget(gallery.content_splitter)
        
        # Add the gallery widget to the scroll area
        gallery.gallery_scroll.setWidget(gallery.gallery_widget)
        
        # Add the scroll area to the main layout
        gallery.layout.addWidget(gallery.gallery_scroll)

    @staticmethod
    def add_search_box(gallery):
        """Add a search box to the top bar"""
        # Search box
        gallery.search_box = SearchBox(gallery, "Search templates...")
        gallery.search_box.textChanged.connect(gallery._on_search)
        gallery.top_bar_layout.addWidget(gallery.search_box, 2)

    # Note: Additional setup methods will be defined in gallery_folders.py and gallery_templates.py 
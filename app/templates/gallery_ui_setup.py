#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QFrame, QScrollArea, QGridLayout, QComboBox, QButtonGroup, 
                           QToolButton, QSlider, QSizePolicy, QSplitter, QMenu)
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
        
        # Add spacing between search bar and folder header
        spacer = QWidget()
        spacer.setFixedHeight(15)  # Match the spacing between sections
        spacer.setStyleSheet("background: transparent;")
        gallery.layout.addWidget(spacer)
        
        # Action bar with buttons
        GalleryUISetup.setup_action_bar(gallery)
        
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
        from app.dialogs.dialog_windows_pyqt import show_edit_template
        
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
                                
                                def save_custom_structure(self, name, structure, category="General"):
                                    """Save a custom structure in memory (doesn't persist to disk)"""
                                    print(f"BasicTemplateManager: Saving structure {name} with {len(structure)} items")
                                    self.custom_structures[name] = structure
                                    return True
                                    
                                def get_categories(self):
                                    """Return available categories"""
                                    return ["General", "Custom", "Web Development", "Motion Graphics", "Video Editing", "VFX"]
                            
                            parent.template_manager = BasicTemplateManager()
                        
                        # Call the original constructor
                        super().__init__(parent, **kwargs)
                        
                        # Ensure dropdown is populated with built-in structures
                        self.populate_structure_dropdown()
                        
                        # Store the parent's template manager in the editor
                        self.template_manager = parent.template_manager
                    
                    def accept(self):
                        """Override accept to ensure template_manager is available"""
                        try:
                            # Ensure template_manager is accessible in the parent class accept method
                            if not hasattr(self, 'template_manager') or self.template_manager is None:
                                print("EnhancedStructureEditorWithFallback.accept: template_manager not found, getting from parent")
                                if hasattr(self.parent(), 'template_manager'):
                                    self.template_manager = self.parent().template_manager
                                else:
                                    # No template_manager available in parent
                                    from PyQt5.QtWidgets import QMessageBox
                                    QMessageBox.warning(self, "Save Error", 
                                        "Cannot save structure: Template manager is not available in the parent application. Changes will be lost.")
                                    # Just close the dialog without saving
                                    super(EnhancedStructureEditor, self).accept()
                                    return
                            
                            # Call parent class accept method
                            super().accept()
                            
                        except AttributeError as e:
                            if "Template manager instance is not available" in str(e):
                                # Show a user-friendly message
                                from PyQt5.QtWidgets import QMessageBox
                                QMessageBox.warning(self, "Save Error", 
                                    "Cannot save structure: Template manager is not available. Changes will be lost.")
                                # Just close the dialog without saving
                                super(EnhancedStructureEditor, self).accept()
                            else:
                                # Re-raise any other AttributeError
                                raise e
                
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
        from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QSizePolicy, QComboBox, QLineEdit, QMenu, QToolButton
        from PyQt5.QtCore import Qt
        from app.ui.color_scheme_pyqt import BUTTON_STYLE, ACCENT_BUTTON_STYLE
        
        # Create the action bar
        gallery.action_bar = QFrame()
        gallery.action_bar.setFrameShape(QFrame.NoFrame)
        gallery.action_bar.setFrameShadow(QFrame.Plain)
        gallery.action_bar.setLineWidth(0)
        
        # Action bar layout
        gallery.action_bar_layout = QVBoxLayout(gallery.action_bar)
        gallery.action_bar_layout.setContentsMargins(10, 5, 10, 5)
        
        # Filtering and search
        gallery.filter_frame = QFrame()
        gallery.filter_frame.setFrameShape(QFrame.NoFrame)
        gallery.filter_frame.setFrameShadow(QFrame.Plain)
        
        gallery.filter_layout = QHBoxLayout(gallery.filter_frame)
        gallery.filter_layout.setContentsMargins(0, 0, 0, 0)
        
        gallery.category_filter_label = QLabel("Category:")
        gallery.category_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        gallery.filter_layout.addWidget(gallery.category_filter_label)
        
        gallery.category_filter = QComboBox()
        gallery.category_filter.addItem("All")
        gallery.category_filter.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        gallery.category_filter.setMinimumWidth(150)
        gallery.category_filter.currentIndexChanged.connect(gallery._filter_templates)
        gallery.filter_layout.addWidget(gallery.category_filter)
        
        gallery.filter_layout.addSpacing(15)
        
        gallery.search_label = QLabel("Search:")
        gallery.search_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        gallery.filter_layout.addWidget(gallery.search_label)
        
        gallery.search_box = QLineEdit()
        gallery.search_box.setPlaceholderText("Search templates...")
        gallery.search_box.textChanged.connect(gallery._filter_templates)
        gallery.filter_layout.addWidget(gallery.search_box)
        
        gallery.action_bar_layout.addWidget(gallery.filter_frame)
        
        # Button row
        gallery.button_frame = QFrame()
        gallery.button_frame.setFrameShape(QFrame.NoFrame)
        gallery.button_frame.setFrameShadow(QFrame.Plain)
        gallery.button_layout = QHBoxLayout(gallery.button_frame)
        gallery.button_layout.setContentsMargins(0, 0, 0, 0)
        
        # View mode button
        gallery.view_mode_button = QToolButton()
        gallery.view_mode_button.setText("View")
        gallery.view_mode_button.setPopupMode(QToolButton.InstantPopup)
        gallery.view_mode_button.setStyleSheet(BUTTON_STYLE)
        gallery.view_mode_menu = QMenu(gallery.view_mode_button)
        
        # Set up view mode menu actions
        gallery.card_view_action = gallery.view_mode_menu.addAction("Card View")
        gallery.card_view_action.setCheckable(True)
        gallery.card_view_action.triggered.connect(lambda: gallery._set_view_mode("card"))
        
        gallery.list_view_action = gallery.view_mode_menu.addAction("List View")
        gallery.list_view_action.setCheckable(True)
        gallery.list_view_action.triggered.connect(lambda: gallery._set_view_mode("list"))
        
        gallery.table_view_action = gallery.view_mode_menu.addAction("Table View")
        gallery.table_view_action.setCheckable(True)
        gallery.table_view_action.triggered.connect(lambda: gallery._set_view_mode("table"))
        
        # Add separator
        gallery.view_mode_menu.addSeparator()
        
        # Add animation toggle option
        gallery.animations_action = gallery.view_mode_menu.addAction("Enable Animations")
        gallery.animations_action.setCheckable(True)
        gallery.animations_action.triggered.connect(gallery._toggle_animations)
        
        gallery.view_mode_button.setMenu(gallery.view_mode_menu)
        gallery.button_layout.addWidget(gallery.view_mode_button)
        
        # Add a Cache Management button with dropdown menu
        gallery.cache_management_button = QToolButton()
        gallery.cache_management_button.setText("Cache Management")
        gallery.cache_management_button.setPopupMode(QToolButton.InstantPopup)
        gallery.cache_management_button.setStyleSheet(BUTTON_STYLE)
        gallery.cache_management_menu = QMenu(gallery.cache_management_button)
        
        # Add cache management menu actions
        gallery.recache_all_action = gallery.cache_management_menu.addAction("Recache All Templates")
        gallery.recache_all_action.triggered.connect(gallery._on_recache_all_templates)
        
        gallery.clear_all_caches_action = gallery.cache_management_menu.addAction("Clear All Caches")
        gallery.clear_all_caches_action.triggered.connect(gallery._on_clear_all_caches)
        
        gallery.cache_management_menu.addSeparator()
        
        gallery.check_missing_originals_action = gallery.cache_management_menu.addAction("Check for Missing Originals")
        gallery.check_missing_originals_action.triggered.connect(gallery._on_check_missing_originals)
        
        gallery.cache_management_button.setMenu(gallery.cache_management_menu)
        gallery.button_layout.addWidget(gallery.cache_management_button)
        
        # Push buttons to the right
        
        # Folder management buttons - moved to folders header
        # Rename folder button is kept for context menu/keyboard shortcut functionality
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
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QFrame, QScrollArea, QGridLayout, QComboBox, QButtonGroup, 
                           QToolButton, QSlider, QSizePolicy, QSplitter, QMenu, QStyle)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from app.ui.color_scheme_pyqt import colors, get_color, BUTTON_STYLE, ACCENT_BUTTON_STYLE
from .components.utils import SYSTEM_FONT
from .components.components import SearchBox
from .gallery_folders import GalleryFoldersSetup
from .gallery_templates import GalleryTemplatesSetup

class GalleryUISetup:
    """UI setup methods for the Template Gallery"""
    
    @staticmethod
    def setup_ui(gallery):
        """Set up the UI components"""
        # Main layout
        gallery.layout = QVBoxLayout(gallery)
        gallery.layout.setContentsMargins(0, 0, 0, 0)
        gallery.layout.setSpacing(0)  # No space between components
        
        # Top bar with search
        GalleryUISetup.setup_top_bar(gallery)
        
        # Add spacing between search bar and folder header
        spacer = QWidget()
        spacer.setFixedHeight(15)  # Match the spacing between sections
        spacer.setStyleSheet("background: transparent;")
        gallery.layout.addWidget(spacer)
        
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
                                    from PyQt6.QtWidgets import QMessageBox
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
                                from PyQt6.QtWidgets import QMessageBox
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
                editor.exec()
            else:
                from PyQt6.QtWidgets import QMessageBox
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
        from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QSizePolicy, QComboBox, QLineEdit, QMenu, QToolButton
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QAction
        from app.ui.color_scheme_pyqt import BUTTON_STYLE, ACCENT_BUTTON_STYLE
        
        # Create the action bar - KEEPING THIS CODE BUT NOT USING IT
        # This allows backward compatibility with code that might expect these objects
        gallery.action_bar = QFrame()
        gallery.action_bar.setFrameShape(QFrame.NoFrame)
        gallery.action_bar.setFrameShadow(QFrame.Plain)
        gallery.action_bar.setLineWidth(0)
        
        # Action bar layout
        gallery.action_bar_layout = QVBoxLayout(gallery.action_bar)
        gallery.action_bar_layout.setContentsMargins(10, 5, 10, 5)
        
        # Create empty frames for backward compatibility
        gallery.filter_frame = QFrame()
        gallery.button_frame = QFrame()
        
        # Create hidden button for keyboard shortcut functionality
        gallery.rename_folder_button = QPushButton("Rename Folder")
        gallery.rename_folder_button.setStyleSheet(BUTTON_STYLE)
        gallery.rename_folder_button.clicked.connect(gallery._on_rename_folder)
        gallery.rename_folder_button.setEnabled(False)
        gallery.rename_folder_button.setVisible(False)
        
        # Set up view mode actions for compatibility
        gallery.card_view_action = QAction("Card View")
        gallery.card_view_action.setCheckable(True)
        gallery.card_view_action.triggered.connect(lambda: gallery._set_view_mode("card"))
        
        gallery.list_view_action = QAction("List View")
        gallery.list_view_action.setCheckable(True)
        gallery.list_view_action.triggered.connect(lambda: gallery._set_view_mode("list"))
        
        gallery.table_view_action = QAction("Table View")
        gallery.table_view_action.setCheckable(True)
        gallery.table_view_action.triggered.connect(lambda: gallery._set_view_mode("table"))
        
        gallery.animations_action = QAction("Enable Animations")
        gallery.animations_action.setCheckable(True)
        gallery.animations_action.triggered.connect(gallery._toggle_animations)
        
        # Set up cache management actions for compatibility
        gallery.recache_all_action = QAction("Recache All Templates")
        gallery.recache_all_action.triggered.connect(gallery._on_recache_all_templates)
        
        gallery.clear_all_caches_action = QAction("Clear All Caches")
        gallery.clear_all_caches_action.triggered.connect(gallery._on_clear_all_caches)
        
        gallery.check_missing_originals_action = QAction("Check for Missing Originals")
        gallery.check_missing_originals_action.triggered.connect(gallery._on_check_missing_originals)
        
        # Note: We're not adding the action_bar to the layout anymore

    @staticmethod
    def setup_gallery_containers(gallery):
        """Set up the gallery containers"""
        # Main container for folders and templates (everything below search bar)
        gallery.gallery_content_area = QWidget()
        gallery.gallery_content_layout = QVBoxLayout(gallery.gallery_content_area)
        gallery.gallery_content_layout.setContentsMargins(0, 0, 0, 0)
        gallery.gallery_content_layout.setSpacing(0)

        # --- Folder Navigation Bar (Initially hidden) ---
        gallery.folder_nav = QWidget()
        gallery.folder_nav.setObjectName("folderNav")
        gallery.folder_nav.setStyleSheet(f"""
            QWidget#folderNav {{
                background-color: {colors.get('dark_header_bg', '#252525')};
                padding: 5px 10px;
                border-bottom: 1px solid {colors.get('border', '#444444')};
            }}
        """)
        gallery.folder_nav_layout = QHBoxLayout(gallery.folder_nav)
        gallery.folder_nav_layout.setContentsMargins(0, 5, 0, 5) # Top/bottom padding
        gallery.folder_nav_layout.setSpacing(10)

        gallery.back_button = QPushButton("〈 Back to All") # Using a fancier back arrow
        gallery.back_button.setStyleSheet(BUTTON_STYLE + "padding: 5px 10px;") # Add some padding
        gallery.back_button.clicked.connect(gallery._on_back_to_all)
        gallery.folder_nav_layout.addWidget(gallery.back_button)

        # Breadcrumb layout
        breadcrumb_layout = QHBoxLayout()
        breadcrumb_layout.setSpacing(5) # Spacing between elements

        # Icon for "Template Collections"
        collections_icon_label = QLabel()
        collections_icon_label.setPixmap(gallery.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon).pixmap(QSize(16, 16)))
        collections_icon_label.setStyleSheet("border: none; background-color: transparent;")
        breadcrumb_layout.addWidget(collections_icon_label)

        breadcrumb_static_label = QLabel("Template Collections >")
        breadcrumb_static_label.setStyleSheet(f"color: {colors['secondary_text']}; font-size: 13px; border: none; background: transparent;")
        breadcrumb_layout.addWidget(breadcrumb_static_label)

        # Icon for the current folder name
        current_folder_icon_label = QLabel()
        current_folder_icon_label.setPixmap(gallery.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon).pixmap(QSize(16, 16)))
        current_folder_icon_label.setStyleSheet("border: none; background-color: transparent;")
        breadcrumb_layout.addWidget(current_folder_icon_label)

        gallery.folder_label = QLabel("") # Will be filled with current folder name
        gallery.folder_label.setStyleSheet(f"color: {colors['text']}; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        breadcrumb_layout.addWidget(gallery.folder_label)
        
        breadcrumb_layout.addStretch(1) # Push to the left

        gallery.folder_nav_layout.addLayout(breadcrumb_layout)
        gallery.folder_nav_layout.addStretch(1) # Ensure back button and breadcrumb are on left
        gallery.folder_nav.setVisible(False) # Initially hidden
        gallery.gallery_content_layout.addWidget(gallery.folder_nav)
        # --- End Folder Navigation Bar ---

        # --- Folder Content Notice ---
        gallery.folder_notice_label = QLabel("")
        gallery.folder_notice_label.setObjectName("folderNoticeLabel")
        gallery.folder_notice_label.setStyleSheet(f"""
            QLabel#folderNoticeLabel {{
                color: {colors['secondary_text']};
                font-size: 12px;
                padding: 8px 12px;
                background-color: {colors.get('content_bg', '#2A2A2A')}; 
                border-bottom: 1px solid {colors.get('border', '#444444')};
                text-align: center; 
            }}
        """)
        gallery.folder_notice_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gallery.folder_notice_label.setWordWrap(True)
        gallery.folder_notice_label.setVisible(False) # Initially hidden
        gallery.gallery_content_layout.addWidget(gallery.folder_notice_label)
        # --- End Folder Content Notice ---

        # --- No Root Templates Notice ---
        gallery.no_root_templates_notice_label = QLabel("")
        gallery.no_root_templates_notice_label.setObjectName("noRootTemplatesNoticeLabel")
        gallery.no_root_templates_notice_label.setStyleSheet(f"""
            QLabel#noRootTemplatesNoticeLabel {{
                color: {colors['text_info'] if 'text_info' in colors else colors['secondary_text']}; 
                font-size: 12px;
                padding: 8px 12px;
                background-color: {colors.get('info_bg', '#2E3B4E')}; 
                border: 1px solid {colors.get('info_border', '#4A5F7A')};
                border-radius: 4px;
                margin: 10px; 
            }}
        """)
        gallery.no_root_templates_notice_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gallery.no_root_templates_notice_label.setWordWrap(True)
        gallery.no_root_templates_notice_label.setVisible(False) # Initially hidden
        # --- End No Root Templates Notice ---

        # Folders section (for displaying folder cards or list)
        GalleryFoldersSetup.setup_folders_section(gallery)
        gallery.gallery_content_layout.addWidget(gallery.folders_section, 2)  # 20% less space (reduced stretch factor)
        
        # Templates section (for displaying template cards or list)
        GalleryTemplatesSetup.setup_templates_section(gallery)
        gallery.gallery_content_layout.addWidget(gallery.templates_section, 3)  # 20% more space (increased stretch factor)

        gallery.layout.addWidget(gallery.gallery_content_area)

    @staticmethod
    def add_search_box(gallery):
        """Add a search box to the top bar"""
        # Search box
        gallery.search_box = SearchBox(gallery, "Search templates...")
        gallery.search_box.textChanged.connect(gallery._on_search)
        gallery.top_bar_layout.addWidget(gallery.search_box, 2)

    # Note: Additional setup methods will be defined in gallery_folders.py and gallery_templates.py 
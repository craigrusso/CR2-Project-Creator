#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QFrame, QScrollArea, QGridLayout, QButtonGroup, 
                            QToolButton, QSlider, QSizePolicy, QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from app.ui.color_scheme_pyqt import colors, ACCENT_BUTTON_STYLE
from .components.utils import SYSTEM_FONT
from .components.template_folder_card import TemplateFolderCard, TemplateFolderListItem

class GalleryFoldersSetup:
    """Folder-related functionality for the Template Gallery"""
    
    @staticmethod
    def setup_folders_section(gallery):
        """Set up the folders section of the gallery"""
        # Folders section
        gallery.folders_section = QWidget()
        gallery.folders_section.setStyleSheet("background: transparent;")
        gallery.folders_section_layout = QVBoxLayout(gallery.folders_section)
        gallery.folders_section_layout.setContentsMargins(10, 0, 10, 10)  # Reduced from 15,0,15,15
        
        # Folders header with view controls
        gallery.folders_header = QWidget()
        # Apply a subtle background to the header that spans the full width
        gallery.folders_header.setStyleSheet(f"""
            background-color: {colors['card_bg']};
            border: none;
        """)
        gallery.folders_header_layout = QHBoxLayout(gallery.folders_header)
        gallery.folders_header_layout.setContentsMargins(15, 10, 15, 10)  # Increase padding for better spacing
        
        # Folders section header - should stretch
        gallery.folders_label = QLabel("Folders")
        gallery.folders_label.setFont(QFont(SYSTEM_FONT, 14, QFont.Bold))
        gallery.folders_label.setStyleSheet(f"color: {colors['text']}; font-weight: bold; background: transparent;")
        gallery.folders_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Changed back to Expanding
        gallery.folders_header_layout.addWidget(gallery.folders_label, 1)  # Give stretch factor of 1
        
        # Folder size label and slider
        gallery.folder_size_label = QLabel("Size:")
        gallery.folder_size_label.setStyleSheet("color: #AAAAAA; background: transparent;")
        gallery.folders_header_layout.addWidget(gallery.folder_size_label)
        
        # Size slider
        gallery.folder_size_slider = QSlider(Qt.Horizontal)
        gallery.folder_size_slider.setRange(50, 300)  # 50% to 300% scaling
        gallery.folder_size_slider.setValue(gallery.icon_scale)  # Use current scale value
        gallery.folder_size_slider.setFixedWidth(100)
        gallery.folder_size_slider.setTickPosition(QSlider.TicksBelow)
        gallery.folder_size_slider.setTickInterval(50)
        gallery.folder_size_slider.valueChanged.connect(gallery._on_icon_scale_changed)
        gallery.folder_size_slider.setStyleSheet("""
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
        gallery.folders_header_layout.addWidget(gallery.folder_size_slider)
        
        # Add New Folder button to the right side
        gallery.add_folder_button = QPushButton("New Folder")
        gallery.add_folder_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        gallery.add_folder_button.clicked.connect(gallery._on_add_folder)
        gallery.add_folder_button.setFixedSize(120, 30)  # Match size with Add Template button
        gallery.folders_header_layout.addWidget(gallery.add_folder_button)
        
        # Create view toggle buttons
        gallery.folder_grid_view_btn = QToolButton()
        gallery.folder_grid_view_btn.setCheckable(True)
        gallery.folder_grid_view_btn.setToolTip("Grid View")
        gallery.folder_grid_view_btn.setText("Grid")
        gallery.folder_grid_view_btn.setChecked(gallery.folder_view_mode == "grid")
        gallery.folder_grid_view_btn.clicked.connect(lambda: gallery._set_folder_view_mode("grid"))
        gallery.folder_grid_view_btn.setFixedSize(65, 24)
        
        gallery.folder_grid_view_btn.setStyleSheet("""
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
        
        gallery.folder_list_view_btn = QToolButton()
        gallery.folder_list_view_btn.setCheckable(True)
        gallery.folder_list_view_btn.setToolTip("List View")
        gallery.folder_list_view_btn.setText("List")
        gallery.folder_list_view_btn.setChecked(gallery.folder_view_mode == "list")
        gallery.folder_list_view_btn.clicked.connect(lambda: gallery._set_folder_view_mode("list"))
        gallery.folder_list_view_btn.setFixedSize(65, 24)
        
        gallery.folder_list_view_btn.setStyleSheet("""
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
        
        # Create a button group to manage selection
        gallery.folder_view_toggle_group = QButtonGroup(gallery)
        gallery.folder_view_toggle_group.addButton(gallery.folder_grid_view_btn)
        gallery.folder_view_toggle_group.addButton(gallery.folder_list_view_btn)
        
        # Add view toggle buttons to header layout
        gallery.folders_header_layout.addWidget(gallery.folder_grid_view_btn)
        gallery.folders_header_layout.addWidget(gallery.folder_list_view_btn)
        
        # Add the header to the section layout
        gallery.folders_section_layout.addWidget(gallery.folders_header)
        
        # Add a small margin between header and content
        spacer = QWidget()
        spacer.setFixedHeight(5)
        spacer.setStyleSheet("background: transparent;")
        gallery.folders_section_layout.addWidget(spacer)
        
        # Scrollable container for folders
        gallery.folders_scroll = QScrollArea()
        gallery.folders_scroll.setWidgetResizable(True)
        gallery.folders_scroll.setFrameShape(QFrame.NoFrame)
        gallery.folders_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        gallery.folders_scroll.setStyleSheet("background: transparent; border: none;")
        # Ensure scroll area fills available space
        gallery.folders_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Container for folder cards
        gallery.folders_container = QWidget()
        gallery.folders_container.setStyleSheet("background: transparent;")
        gallery.folders_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Match templates container policy
        
        # Create a grid layout for folders
        gallery.folders_grid = QGridLayout(gallery.folders_container)
        gallery.folders_grid.setContentsMargins(0, 0, 0, 0)
        gallery.folders_grid.setSpacing(10)  # Space between cards
        gallery.folders_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # Align to top-left like templates
        
        # Set the container as the scroll area widget
        gallery.folders_scroll.setWidget(gallery.folders_container)
        gallery.folders_section_layout.addWidget(gallery.folders_scroll)

    @staticmethod
    def populate_folders_grid(gallery, folders):
        """Populate folders in grid view"""
        gallery.folder_cards = []
        
        # Grid layout parameters
        col = 0
        row = 0
        
        # Calculate max columns based on container width
        container_width = gallery.folders_container.width()
        folder_width = 130  # Folder card width + spacing
        min_cols = 2  # Minimum number of columns
        
        # Default to 4 columns if container width is not yet available
        if container_width <= 0:
            max_cols = 4
        else:
            calculated_cols = max(min_cols, container_width // folder_width)
            max_cols = min(8, calculated_cols)  # Increased max columns to 8 (was 6)
        
        for folder in folders:
            folder_card = TemplateFolderCard(gallery, folder_name=folder, app=gallery.app)
            folder_card.clicked.connect(gallery._on_folder_select)
            folder_card.doubleClicked.connect(gallery._on_folder_enter)
            folder_card.renameRequested.connect(gallery._on_rename_folder_requested)
            folder_card.renameDone.connect(gallery._on_rename_folder_done)
            
            gallery.folders_grid.addWidget(folder_card, row, col)
            gallery.folder_cards.append(folder_card)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    @staticmethod
    def populate_folders_list(gallery, folders):
        """Populate folders in list view"""
        gallery.folder_cards = []
        
        # List layout - one column
        row = 0
        
        # Sort folders alphabetically
        for i, folder in enumerate(sorted(folders)):
            folder_item = TemplateFolderListItem(gallery, folder_name=folder, app=gallery.app)
            folder_item.clicked.connect(gallery._on_folder_select)
            folder_item.doubleClicked.connect(gallery._on_folder_enter)
            folder_item.renameRequested.connect(gallery._on_rename_folder_requested)
            folder_item.renameDone.connect(gallery._on_rename_folder_done)
            
            # Set alternate row color property
            folder_item.setProperty("row_type", "odd" if i % 2 else "even")
            
            # Force style update
            folder_item.style().unpolish(folder_item)
            folder_item.style().polish(folder_item)
            folder_item._update_styling()
            
            gallery.folders_grid.addWidget(folder_item, row, 0)
            gallery.folder_cards.append(folder_item)
            row += 1
        
        # Force the folders section to update and repaint
        # QGridLayout doesn't have update/repaint methods
        gallery.folders_section.update()
        gallery.folders_section.repaint()
        
        # Process events to make UI changes immediately visible
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
    
    @staticmethod
    def set_folder_view_mode(gallery, mode):
        """Set the folder view mode"""
        old_mode = gallery.folder_view_mode
        gallery.folder_view_mode = mode
        
        # Update button checked states
        gallery.folder_grid_view_btn.setChecked(mode == "grid")
        gallery.folder_list_view_btn.setChecked(mode == "list")
        
        # Only repopulate if the mode actually changed and we have a template manager
        if old_mode != mode and hasattr(gallery, 'folders_grid') and gallery.folders_grid:
            # Clear existing layout
            while gallery.folders_grid.count():
                item = gallery.folders_grid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            if hasattr(gallery.app, 'template_manager') and hasattr(gallery.app.template_manager, 'get_folders'):
                folders = gallery.app.template_manager.get_folders()
                
                # Clear existing cards
                gallery.folder_cards = []
                
                # Adjust layout spacing based on mode
                if mode == "grid":
                    gallery.folders_grid.setSpacing(10)
                    GalleryFoldersSetup.populate_folders_grid(gallery, folders)
                else:  # list mode
                    gallery.folders_grid.setSpacing(0)
                    GalleryFoldersSetup.populate_folders_list(gallery, folders)
            
            # Show or hide size slider based on mode (visible only in grid mode)
            gallery.folder_size_label.setVisible(mode == "grid")
            gallery.folder_size_slider.setVisible(mode == "grid")
            
            # Update card sizes for the new view mode
            gallery._update_folder_card_sizes(gallery.icon_scale)
    
    @staticmethod
    def update_folder_card_sizes(gallery, scale_percent):
        """Update the sizes of folder cards based on the scale percentage"""
        # Apply to all folder cards
        for card in gallery.folder_cards:
            # Only resize the icon, not the entire card
            if hasattr(card, 'resize_icon'):
                card.resize_icon(scale_percent)
                
        # We don't need to re-layout the grid since we're not changing card sizes anymore 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Layout management component for UI setup
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QSplitter, QTextEdit, QCheckBox, QPushButton,
                           QComboBox, QDateEdit, QSpinBox, QSizePolicy)
from PyQt6.QtCore import Qt, QDate

from app.ui.color_scheme_pyqt import colors, COMBOBOX_STYLE, ACCENT_BUTTON_STYLE
from app.ui.ui_components_pyqt import CardFrame, UI_FONT


class LayoutManager:
    """Handles the main UI layout setup and management"""
    
    def __init__(self, app_instance):
        """Initialize the layout manager"""
        self.app = app_instance
    
    def setup_main_layout(self):
        """Set up the main application layout"""
        print("DEBUG: Setting up main layout...")
        
        # Create central widget and main layout
        self.app.central_widget = QWidget()
        self.app.setCentralWidget(self.app.central_widget)
        self.app.main_layout = QVBoxLayout(self.app.central_widget)
        self.app.main_layout.setContentsMargins(10, 10, 10, 10)
        self.app.main_layout.setSpacing(10)
        
        # Create main splitter
        self.app.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.app.main_layout.addWidget(self.app.main_splitter)
        
        print("DEBUG: Main layout created")
        
    def setup_left_panel(self):
        """Set up the left panel with project settings"""
        print("DEBUG: Setting up left panel...")
        
        # Create left panel
        self.app.left_panel = CardFrame()
        self.app.left_layout = self.app.left_panel.main_layout
        
        # Project settings header
        self.app.settings_header = QLabel("Project Settings")
        self.app.settings_header.setStyleSheet(
            f"font-weight: bold; font-size: 14px; border: none; "
            f"color: {colors.get('text_subtle', '#A0A0A0')};"
        )
        self.app.left_layout.addWidget(self.app.settings_header)
        
        # Set up batch project section
        self._setup_batch_project_section()
        
        # Set up custom options section
        self._setup_custom_options_section()
        
        # Set up versioning section
        self._setup_versioning_section()
        
        # Set up action buttons
        self._setup_action_buttons()
        
        print("DEBUG: Left panel setup complete")
    
    def _setup_batch_project_section(self):
        """Set up the batch project input section"""
        # Batch projects header
        self.app.batch_projects_header = QLabel("Enter Project Names")
        self.app.batch_projects_header.setStyleSheet(
            f"font-weight: bold; font-size: 13px; border: none; "
            f"color: {colors.get('text_focus', '#FFFFFF')};"
        )
        self.app.left_layout.addWidget(self.app.batch_projects_header)
        
        # Instructions
        instruction_base_color = colors.get('text', '#CCCCCC')
        highlight_color = colors.get('text_focus', '#FFFFFF')
        
        instruction_html = (
            f"<span style='color: {instruction_base_color};'>"
            f"Select a <span style='color: {highlight_color}; font-weight: bold;'>template</span> "
            f"on the right to use for project creation.</span><br>"
            f"<span style='color: {instruction_base_color};'>"
            f"Enter one project name per line. You can also separate names with commas or semicolons.</span><br>"
            f"<span style='color: {instruction_base_color};'>"
            f"All projects will be created using the selected "
            f"<span style='color: {highlight_color}; font-weight: bold;'>template</span> and output location.</span>"
        )
        
        self.app.batch_instructions = QLabel(instruction_html)
        self.app.batch_instructions.setTextFormat(Qt.TextFormat.RichText)
        self.app.batch_instructions.setWordWrap(True)
        self.app.batch_instructions.setStyleSheet(
            f"background-color: {colors.get('info_bg_transparent', 'rgba(46, 59, 78, 0.7)')}; "
            f"border: none; border-radius: 4px; padding: 8px; "
            f"color: {instruction_base_color};"
        )
        self.app.left_layout.addWidget(self.app.batch_instructions)
        
        # Text input area
        middle_container = QWidget()
        middle_layout = QVBoxLayout(middle_container)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        
        self.app.batch_text_edit = QTextEdit()
        try:
            # Enforce plain-text paste to avoid styled content from web clients
            self.app.batch_text_edit.setAcceptRichText(False)
        except Exception:
            pass
        self.app.batch_text_edit.setPlaceholderText("Project 1\nProject 2\nProject 3")
        self.app.batch_text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 8px;
                font-family: '{UI_FONT}';
                font-size: 13px;
            }}
        """)
        self.app.batch_text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        middle_layout.addWidget(self.app.batch_text_edit)
        
        self.app.left_layout.addWidget(middle_container, 1)
    
    def _setup_custom_options_section(self):
        """Set up the custom options section"""
        print("DEBUG: Creating AnimatedCustomOptionsWidget...")
        from app.ui.custom_options_widgets import AnimatedCustomOptionsWidget
        self.app.custom_options_widget = AnimatedCustomOptionsWidget(self.app)
        self.app.custom_options_widget.hide()
        self.app.left_layout.addWidget(self.app.custom_options_widget)
        print("DEBUG: AnimatedCustomOptionsWidget created")
    
    def _setup_versioning_section(self):
        """Set up the versioning options section"""
        versioning_container = QWidget()
        versioning_layout = QVBoxLayout(versioning_container)
        versioning_layout.setContentsMargins(0, 10, 0, 0)
        
        # Enable versioning checkbox
        self.app.enable_versioning = QCheckBox("Create sequence variations for each project")
        self.app.enable_versioning.setStyleSheet(f"""
            QCheckBox {{
                color: {colors['text']};
                font-weight: bold;
                spacing: 8px;
                padding: 8px 4px;
                min-height: 20px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {colors['border']};
                border-radius: 3px;
                background-color: {colors['card_bg']};
                margin-right: 4px;
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {colors['accent']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors['accent']};
                border: 1px solid {colors['accent']};
            }}
        """)
        if hasattr(self.app, '_toggle_versioning_options'):
            self.app.enable_versioning.toggled.connect(self.app._toggle_versioning_options)
        versioning_layout.addWidget(self.app.enable_versioning)
        
        # Versioning options (initially hidden)
        self.app.versioning_options = QWidget()
        self.app.versioning_options.hide()
        versioning_options_layout = QVBoxLayout(self.app.versioning_options)
        versioning_options_layout.setContentsMargins(20, 8, 0, 0)
        versioning_options_layout.setSpacing(8)
        
        # Type and position row
        type_position_row = QWidget()
        type_position_layout = QHBoxLayout(type_position_row)
        type_position_layout.setContentsMargins(0, 0, 0, 0)
        type_position_layout.setSpacing(16)
        
        # Sequence type
        type_container = QWidget()
        type_layout = QVBoxLayout(type_container)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(4)
        
        type_label = QLabel("Type:")
        type_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
            font-weight: normal;
        """)
        type_layout.addWidget(type_label)
        
        self.app.sequence_type = QComboBox()
        self.app.sequence_type.addItems(["Date Sequences", "Version Numbers", "Sequential Numbers"])
        self.app.sequence_type.setMinimumWidth(180)
        self.app.sequence_type.setMinimumHeight(32)
        self.app.sequence_type.setStyleSheet(COMBOBOX_STYLE)
        if hasattr(self.app, '_update_versioning_options'):
            self.app.sequence_type.currentTextChanged.connect(self.app._update_versioning_options)
        
        type_layout.addWidget(self.app.sequence_type)
        type_position_layout.addWidget(type_container)
        
        # Position
        position_container = QWidget()
        position_layout = QVBoxLayout(position_container)
        position_layout.setContentsMargins(0, 0, 0, 0)
        position_layout.setSpacing(4)
        
        position_label = QLabel("Position:")
        position_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;  
            font-weight: normal;
        """)
        position_layout.addWidget(position_label)
        
        self.app.name_position = QComboBox()
        self.app.name_position.addItems(["Suffix", "Prefix"])
        self.app.name_position.setMinimumWidth(100)
        self.app.name_position.setMinimumHeight(32)
        self.app.name_position.setStyleSheet(COMBOBOX_STYLE)
        
        position_layout.addWidget(self.app.name_position)
        type_position_layout.addWidget(position_container)
        type_position_layout.addStretch()
        
        versioning_options_layout.addWidget(type_position_row)
        versioning_layout.addWidget(self.app.versioning_options)
        
        self.app.left_layout.addWidget(versioning_container)
    
    def _setup_action_buttons(self):
        """Set up the action buttons"""
        # Create Project button
        self.app.create_project_button = QPushButton("Create Projects")
        self.app.create_project_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        if hasattr(self.app, 'batch_manager'):
            self.app.create_project_button.clicked.connect(self.app.batch_manager.process_batch_projects)
        self.app.left_layout.addWidget(self.app.create_project_button)
    
    def setup_right_panel(self):
        """Set up the right panel with template gallery"""
        print("DEBUG: Setting up right panel...")
        
        from app.gallery.gallery_widget import TemplateGallery
        self.app.template_gallery = TemplateGallery(self.app)
        
        print("DEBUG: Right panel setup complete")
    
    def finalize_layout(self):
        """Finalize the layout by adding panels to splitter"""
        print("DEBUG: Finalizing layout...")
        
        # Add panels to splitter
        self.app.main_splitter.addWidget(self.app.left_panel)
        self.app.main_splitter.addWidget(self.app.template_gallery)
        
        # Set splitter sizes (30% left, 70% right)
        self.app.main_splitter.setSizes([400, 900])
        
        print("DEBUG: Layout finalized") 
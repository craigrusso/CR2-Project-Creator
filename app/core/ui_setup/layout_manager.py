#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QComboBox, QLineEdit, QTextEdit, QSizePolicy, QLayout)
from PyQt6.QtCore import Qt
from app.ui.color_scheme_pyqt import APP_COLORS, ACCENT_BUTTON_STYLE


class LayoutManager:
    """Handles main layout creation and management"""
    
    def __init__(self, main_window):
        """Initialize with reference to main window"""
        self.main_window = main_window
    
    def create_left_panel(self):
        """Create the left panel with batch text input and versioning options"""
        # Create left panel
        left_panel = QWidget()
        left_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)
        
        # Add title
        title_label = QLabel("Batch Project Creation")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {APP_COLORS['text']};
                font-size: 16px;
                font-weight: bold;
                padding: 10px 0px;
            }}
        """)
        left_layout.addWidget(title_label)
        
        # Add text edit for project names
        text_label = QLabel("Enter project names (one per line):")
        text_label.setStyleSheet(f"color: {APP_COLORS['text']};")
        left_layout.addWidget(text_label)
        
        self.main_window.batch_text_edit = QTextEdit()
        try:
            self.main_window.batch_text_edit.setAcceptRichText(False)
        except Exception:
            pass
        self.main_window.batch_text_edit.setPlaceholderText("Project One\nProject Two\nProject Three")
        self.main_window.batch_text_edit.setMaximumHeight(150)
        self.main_window.batch_text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {APP_COLORS['card_bg']};
                color: {APP_COLORS['text']};
                border: 1px solid {APP_COLORS['border']};
                padding: 8px;
                font-family: monospace;
            }}
        """)
        left_layout.addWidget(self.main_window.batch_text_edit)
        
        # Add versioning options (placeholder)
        versioning_widget = self.main_window.versioning_ui.create_versioning_widget()
        left_layout.addWidget(versioning_widget)
        
        # Add output directory section
        self._create_output_directory_section(left_layout)
        
        # Add create button
        self.main_window.batch_create_btn = QPushButton("Create Project(s)")
        self.main_window.batch_create_btn.clicked.connect(self.main_window.process_batch_projects)
        self.main_window.batch_create_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.main_window.batch_create_btn.setMinimumHeight(40)
        left_layout.addWidget(self.main_window.batch_create_btn)
        
        # Add navigation button to switch between Templates and Transfer
        left_layout.addSpacing(20)  # Add some spacing
        
        self.main_window.toggle_btn = QPushButton("Switch to Transfer")
        self.main_window.toggle_btn.clicked.connect(self.main_window._toggle_transfer_view)
        self.main_window.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
                margin: 8px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.main_window.toggle_btn.setMinimumHeight(40)
        left_layout.addWidget(self.main_window.toggle_btn)
        
        # Store reference for access from main window
        self.main_window.left_layout = left_layout
        
        return left_panel
    
    def _create_output_directory_section(self, parent_layout):
        """Create the output directory selection section"""
        # Output directory
        output_dir_layout = QHBoxLayout()
        output_dir_layout.setContentsMargins(10, 0, 10, 0)
        output_dir_layout.setSpacing(5)
        
        output_dir_label = QLabel("Output Directory:")
        output_dir_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        output_dir_label.setStyleSheet(f"""
            QLabel {{
                background-color: {APP_COLORS['bg']};
                border: none;
                padding-left: 5px;
            }}
        """)
        
        self.main_window.output_dir_input = QLineEdit()
        self.main_window.output_dir_input.setPlaceholderText("Select output directory...")
        self.main_window.output_dir_input.setReadOnly(True)
        self.main_window.output_dir_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {APP_COLORS['bg']};
                color: {APP_COLORS['text']};
                border: 1px solid {APP_COLORS['border']};
                padding: 5px;
                min-height: 22px;
            }}
        """)
        
        self.main_window.output_dir_btn = QPushButton("Browse...")
        self.main_window.output_dir_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.main_window.output_dir_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #383838;
                color: #CCCCCC;
                border: 1px solid {APP_COLORS['border']};
                padding: 5px 10px;
                border-radius: 3px;
                min-height: 22px;
                margin-right: 5px;
            }}
            QPushButton:hover {{
                background-color: #454545;
                border: 1px solid #2C4F76;
                color: white;
            }}
            QPushButton:pressed {{
                background-color: #2C4F76;
                color: white;
            }}
        """)
        
        output_dir_layout.addWidget(output_dir_label)
        output_dir_layout.addWidget(self.main_window.output_dir_input, 1)
        output_dir_layout.addWidget(self.main_window.output_dir_btn)
        
        parent_layout.addLayout(output_dir_layout) 
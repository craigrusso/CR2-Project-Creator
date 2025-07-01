#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Dialog windows for displaying information and tutorials.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTabWidget, QWidget,
                           QScrollArea, QFrame, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QDesktopServices, QFont

# Import from the same place as APP_NAME and APP_VERSION for consistency
from app.config.app_config import APP_NAME, APP_VERSION_NUMBER
from app.constants import APP_BUILD_NUMBER, APP_RELEASE_STAGE
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, TAB_STYLE, SCROLL_AREA_STYLE, FRAME_STYLE
from app.constants import get_resource_path
from app.ui.ui_utils import get_styled_app_name

def show_about(app):
    """Show the about dialog"""
    dialog = QDialog(app)
    dialog.setWindowTitle(f"About {APP_NAME}")
    dialog.resize(450, 320)
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(10)
    
    # App Icon and Name
    icon_layout = QVBoxLayout()
    icon_label = QLabel()
    pixmap = QApplication.instance().windowIcon().pixmap(64, 64)
    icon_label.setPixmap(pixmap)
    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    title_label = QLabel(get_styled_app_name())
    title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_label.setStyleSheet(f"color: {colors['text']};")
    
    version_label = QLabel(f"Version {APP_VERSION_NUMBER} (Build {APP_BUILD_NUMBER}, {APP_RELEASE_STAGE})")
    version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    version_label.setStyleSheet(f"color: {colors['secondary_text']};")
    
    icon_layout.addWidget(icon_label)
    icon_layout.addWidget(title_label)
    icon_layout.addWidget(version_label)
    layout.addLayout(icon_layout)
    
    # Copyright info
    copyright_label = QLabel("© 2023-present Craig P. Russo and CR2 Creative")
    copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    copyright_label.setStyleSheet(f"color: {colors['secondary_text']};")
    layout.addWidget(copyright_label)
    
    # Description
    description = QLabel(
        f"{APP_NAME} is a professional project creation tool designed to "
        "streamline your workflow by creating consistent project structures and files "
        "from customizable templates."
    )
    description.setWordWrap(True)
    description.setAlignment(Qt.AlignmentFlag.AlignCenter)
    description.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(description)
    
    # Spacer
    layout.addStretch()
    
    # Close button
    close_button = QPushButton("Close")
    close_button.setStyleSheet(BUTTON_STYLE)
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)
    
    dialog.exec()

def show_tutorial(app):
    """Show the comprehensive user guide dialog"""
    dialog = QDialog(app)
    dialog.setWindowTitle(f"{APP_NAME} User Guide")
    dialog.resize(800, 650)  # Larger for better readability
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(16)
    
    # Title
    title_label = QLabel(f"{get_styled_app_name()} User Guide")
    title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_label.setStyleSheet(f"color: {colors['text']}; margin-bottom: 10px;")
    layout.addWidget(title_label)
    
    # Subtitle
    subtitle_label = QLabel("Complete reference for all features and advanced workflows")
    subtitle_font = subtitle_label.font()
    subtitle_font.setPointSize(11)
    subtitle_label.setFont(subtitle_font)
    subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    subtitle_label.setStyleSheet(f"color: {colors['secondary_text']}; margin-bottom: 16px;")
    layout.addWidget(subtitle_label)
    
    # --- Introduction Tab ---
    intro_tab = QWidget()
    intro_layout = QVBoxLayout(intro_tab)
    intro_text = QLabel(
        f"<p>New to {get_styled_app_name()}? This quick overview will have you creating projects in minutes.</p>"
        "<h3>1. Create or Select a Template</h3>"
        "<p>Templates are blueprints for your projects. You can create your own or use the examples provided. "
        "A template defines the folder structure and files that will be generated.</p>"
        "<h3>2. Customize the Structure</h3>"
        "<p>Use the structure editor to add folders, files, and smart naming patterns. "
        "You can use variables like <code>{date}</code>, <code>{project_name}</code>, or create your own custom inputs.</p>"
        "<h3>3. Create Your Project</h3>"
        "<p>Select your template, enter a project name, choose an output location, and click 'Create'. "
        f"{get_styled_app_name()} will build the entire project directory for you instantly.</p>"
    )
    intro_text.setWordWrap(True)
    intro_text.setOpenExternalLinks(True)
    intro_text.setStyleSheet(f"color: {colors['text']};")
    intro_layout.addWidget(intro_text)
    
    # --- Templates Tab ---
    templates_tab = QWidget()
    templates_layout = QVBoxLayout(templates_tab)
    templates_text = QLabel(
        "<h3>Managing Templates</h3>"
        "<p><b>Create New:</b> Click the 'Add Template' button to create a new, empty template.</p>"
        "<p><b>Edit:</b> Right-click any template and choose 'Edit' to open the structure editor.</p>"
        "<p><b>Duplicate:</b> Right-click and select 'Duplicate' to make a copy of an existing template.</p>"
        "<p><b>Export/Import:</b> You can export templates to a <code>.json</code> file to share them or back them up. "
        f"Use <code>File > Import Template</code> to bring them into {get_styled_app_name()}.</p>"
    )
    templates_text.setWordWrap(True)
    templates_text.setStyleSheet(f"color: {colors['text']};")
    templates_layout.addWidget(templates_text)
    
    # --- Structures Tab ---
    structures_tab = QWidget()
    structures_layout = QVBoxLayout(structures_tab)
    structures_text = QLabel(
        "<h3>Template Structure</h3>"
        "<p>Templates are organized into a hierarchical structure. You can create folders and subfolders to organize your project files.</p>"
        "<h4>Creating New Templates</h4>"
        "<p>To add a new template, click the 'Add Template' button or use the 'File > New Template...' menu option.</p>"
        "<h4>Template Actions</h4>"
        "<p>You can edit, duplicate, or delete templates using right-click menu options.</p>"
    )
    structures_text.setWordWrap(True)
    structures_text.setStyleSheet(f"color: {colors['text']};")
    structures_layout.addWidget(structures_text)
    
    # --- Advanced Tab ---
    advanced_tab = QWidget()
    advanced_layout = QVBoxLayout(advanced_tab)
    advanced_text = QLabel(
        "<h3>Advanced Features</h3>"
        "<p><b>Custom Options:</b> In the structure editor, you can add custom input fields (text, numbers, dates) "
        "that will appear in the main window when you select the template. This allows for dynamic, per-project customization.</p>"
        "<p><b>Sequence Variations:</b> When creating projects in batch, you can use the 'Sequence' option to generate numbered variations "
        "(e.g., Project_01, Project_02).</p>"
        f"<p><b>Batch Creation:</b> Create multiple projects at once. {get_styled_app_name()} intelligently handles naming conflicts and organization.</p>"
    )
    advanced_text.setWordWrap(True)
    advanced_text.setStyleSheet(f"color: {colors['text']};")
    advanced_layout.addWidget(advanced_text)
    
    # Create modern tab widget with enhanced styling
    tab_widget = QTabWidget()
    tab_widget.setStyleSheet(TAB_STYLE)
    
    # Add tabs
    tab_widget.addTab(intro_tab, "Getting Started")
    tab_widget.addTab(templates_tab, "Templates")
    tab_widget.addTab(structures_tab, "Structures")
    tab_widget.addTab(advanced_tab, "Advanced")
    layout.addWidget(tab_widget)
    
    # Close button
    close_button = QPushButton("Close")
    close_button.setStyleSheet(BUTTON_STYLE)
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)
    
    dialog.exec()

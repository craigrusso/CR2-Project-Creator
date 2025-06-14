#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Refactored main application class that delegates to modular components
This file maintains the same interface as the original while using smaller, focused modules
"""

import os
import platform
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QComboBox, QLineEdit, 
                           QFileDialog, QMessageBox, QMenu,
                           QStatusBar, QFrame, QSplitter, QScrollArea, QSizePolicy,
                           QApplication, QGroupBox, QListView, QTextEdit, QLayout, QGridLayout,
                           QWIDGETSIZE_MAX, QCheckBox, QDateEdit, QSpinBox, QToolButton)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QEvent, QModelIndex, QPoint, QUrl, QMimeData, QSettings, QObject, QThread, QDate, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor, QPainter, QPen, QBrush, QPixmap, QDesktopServices, QCursor, QDragEnterEvent, QDropEvent, QFontMetrics, QStandardItemModel, QStandardItem, QAction, QTextCharFormat

# Import component modules
from .workers import UpdateWorker
from .components import (
    MainWindow, LayoutManager, MenuBuilder, StatusManager, 
    BatchManager, VersioningUI, CustomOptionsManager, 
    UpdateManager, RecentFilesManager, ImportExportManager
)

# Import existing modules that are already well-structured
from app.core.app_config import APP_NAME, RECENT_TEMPLATES_MAX
from app.ui.color_scheme_pyqt import get_color, colors, BUTTON_STYLE, COMBOBOX_STYLE, ACCENT_BUTTON_STYLE, LISTVIEW_POPUP_STYLE, APP_COLORS, ACTION_LINK_STYLE
from app.utils.utils import load_config, save_config, truncate_path, normalize_path_for_storage
from app.ui.ui_components_pyqt import ToolTip, CardFrame, SearchBox, TemplateFileCard, ScrollableFrame, UI_FONT, UpdateNotificationBanner
from app.templates.template_manager import TemplateManager
from app.templates.template_manager_core import TemplateManagerCore
from app.core.project_builder import ProjectBuilder
from app.dialogs.dialog_windows_pyqt import (preview_structure, show_about, 
                                show_tutorial, show_preferences_dialog, show_edit_template,
                                show_batch_results)
from app.templates.template_utils import (get_template_file, clear_template_file, clear_structure_template,
                       rename_current_template, rename_template_file)
from app.gallery.gallery_widget import TemplateGallery
from app.ui.app_theme_pyqt import apply_dark_theme_to_template_gallery
from app.core.structures_pyqt import (create_custom_structure, edit_structure, update_structure_dropdown,
                     manage_structures, _update_structure_combo, _preview_structure, _edit_structure)
from app.core.project_operations import (handle_batch_create, 
                             open_recent_project, clear_recent_projects,
                             use_recent_template, clear_recent_templates,
                             add_to_recent_templates, update_card_highlighting,
                             remove_from_recent_templates)
from app.utils.utils import (load_recent_projects, save_recent_projects, 
                 open_folder, load_recent_templates,
                 save_recent_templates, add_to_recent_projects)
from app.dialogs.template_creation_form import show_template_creation_form
from app.templates.components.utils import get_system_font, SYSTEM_FONT
from app.core.import_export_manager import import_template
from app.dialogs.license_management import LicenseManagementDialog
from app.config.app_config import UPDATE_CHECK_INTERVAL_SECONDS
from app.utils.update_checker import get_latest_version_info, natural_sort_key
from packaging.version import parse as parse_version
import time
from app.constants import (
    APP_VERSION_NUMBER, 
    APP_BUILD_NUMBER as CURRENT_BUILD_NUMBER_CONST,
    APP_RELEASE_STAGE as CURRENT_RELEASE_STAGE_CONST,
    USER_UPDATE_CHANNEL_PREFERENCE
)


class ProjectCreatorApp(QMainWindow):
    """Main application class for CR2 Creative Pro using PyQt - Refactored Version
    
    This class maintains the same interface as the original but delegates functionality
    to smaller, focused component modules for better maintainability.
    """
    
    # Signals for template updates
    template_updated = pyqtSignal()
    gallery_preference_changed = pyqtSignal(str)
    manual_check_complete = pyqtSignal(bool, object)  # bool: update_found, object: version_info or None
    
    # Class variables to hold the instance and app icon
    _instance = None
    _app_icon = None
    
    def __init__(self):
        """Initialize the application with modular components"""
        print("DEBUG: ProjectCreatorApp.__init__() started")
        super().__init__()
        
        # Initialize component managers
        self.main_window = MainWindow(self)
        self.status_manager = StatusManager(self)
        self.batch_manager = BatchManager(self)
        # self.layout_manager = LayoutManager(self)
        # self.menu_builder = MenuBuilder(self)
        # self.versioning_ui = VersioningUI(self)
        # self.custom_options_manager = CustomOptionsManager(self)
        # self.update_manager = UpdateManager(self)
        # self.recent_files_manager = RecentFilesManager(self)
        # self.import_export_manager = ImportExportManager(self)
        
        # Set up basic window properties through main_window component
        self.main_window.setup_debug_info()
        self.main_window.setup_window_properties()
        self.main_window.initialize_core_components()
        self.main_window.load_saved_data()
        
        # Set up UI components
        self._setup_ui()
        self._update_ui_from_config()
        
        # Connect signals
        self.template_updated.connect(self.main_window.trigger_template_updated)
        
        print("DEBUG: ProjectCreatorApp initialization complete")
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of the app"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_app_icon(cls):
        """Get the application icon as a QIcon object"""
        if cls._app_icon is None:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               "app", "assets", "icon.png")
            if os.path.exists(icon_path):
                cls._app_icon = QIcon(icon_path)
            else:
                print(f"WARNING: Application icon not found at {icon_path}")
                cls._app_icon = QIcon()  # Empty icon to avoid None checks
        return cls._app_icon
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.main_window.handle_close_event(event)
    
    def _setup_ui(self):
        """Set up the main application UI - Simplified version"""
        print("DEBUG: Setting up UI...")
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Set up status bar through status manager
        self.status_manager.setup_status_bar()
        
        # Create a basic layout for now - full layout implementation would be in LayoutManager
        self._setup_basic_layout()
        
        print("DEBUG: UI setup complete")
    
    def _setup_basic_layout(self):
        """Set up a basic layout structure"""
        # Main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        
        # Left panel for project settings
        self.left_panel = CardFrame()
        self.left_layout = self.left_panel.main_layout
        
        # Basic project settings
        self.settings_header = QLabel("Project Settings")
        self.settings_header.setStyleSheet(f"font-weight: bold; font-size: 14px; border: none; color: {colors.get('text_subtle', '#A0A0A0')};")
        self.left_layout.addWidget(self.settings_header)
        
        # Batch project input
        self.batch_projects_header = QLabel("Enter Project Names")
        self.batch_projects_header.setStyleSheet(f"font-weight: bold; font-size: 13px; border: none; color: {colors.get('text_focus', '#FFFFFF')};")
        self.left_layout.addWidget(self.batch_projects_header)
        
        # Text input for batch projects
        self.batch_text_edit = QTextEdit()
        self.batch_text_edit.setPlaceholderText("Project 1\nProject 2\nProject 3")
        self.batch_text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 8px;
                font-family: '{UI_FONT}';
                font-size: 13px;
            }}
        """)
        self.left_layout.addWidget(self.batch_text_edit, 1)
        
        # Custom options widget placeholder
        from app.ui.custom_options_widgets import AnimatedCustomOptionsWidget
        self.custom_options_widget = AnimatedCustomOptionsWidget(self)
        self.custom_options_widget.hide()
        self.left_layout.addWidget(self.custom_options_widget)
        
        # Versioning options placeholder
        self.enable_versioning = QCheckBox("Create sequence variations for each project")
        self.enable_versioning.setStyleSheet(f"""
            QCheckBox {{
                color: {colors['text']};
                font-weight: bold;
                spacing: 8px;
                padding: 8px 4px;
                min-height: 20px;
            }}
        """)
        self.left_layout.addWidget(self.enable_versioning)
        
        # Create Project button
        self.create_project_button = QPushButton("Create Projects")
        self.create_project_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.create_project_button.clicked.connect(self.batch_manager.process_batch_projects)
        self.left_layout.addWidget(self.create_project_button)
        
        # Template gallery placeholder
        self.template_gallery = TemplateGallery(self)
        
        # Add panels to splitter
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.template_gallery)
        
        # Set splitter sizes (30% left, 70% right)
        self.main_splitter.setSizes([400, 900])
    
    def _update_ui_from_config(self):
        """Update UI elements based on loaded configuration"""
        # Load last output directory if available
        last_output_dir = self.config.get("last_output_dir", "")
        
        # Load other UI elements from config as needed
        # This would be expanded with more configuration options
    
    # Delegate methods to component managers
    def show_status_message(self, message, message_type="info", duration=5000):
        """Show a status message"""
        self.status_manager.show_status_message(message, message_type, duration)
    
    def _reset_status_bar(self):
        """Reset the status bar"""
        self.status_manager._reset_status_bar()
    
    def process_batch_projects(self):
        """Process batch project creation"""
        self.batch_manager.process_batch_projects()
    
    def show_error(self, message):
        """Show an error message"""
        self.main_window.show_error(message)
    
    def show_about_dialog(self):
        """Show the about dialog"""
        self.main_window.show_about_dialog()
    
    def trigger_template_updated(self):
        """Handle template update signal"""
        self.main_window.trigger_template_updated()
    
    def notify_gallery_preference_changed(self, preference_key):
        """Notify that a gallery preference has changed"""
        self.main_window.notify_gallery_preference_changed(preference_key)
    
    # Placeholder methods for functionality that would be implemented in other components
    def get_output_dir(self):
        """Get output directory - placeholder"""
        return QFileDialog.getExistingDirectory(self, "Select Output Directory")
    
    def get_current_output_dir(self, use_fallbacks=True):
        """Get current output directory - placeholder"""
        return self.get_output_dir()
    
    def check_template_for_custom_options(self, template_data):
        """Check template for custom options - placeholder"""
        # This would be implemented in CustomOptionsManager
        pass
    
    def reset_custom_options_widget(self):
        """Reset custom options widget - placeholder"""
        if hasattr(self, 'custom_options_widget'):
            self.custom_options_widget.slide_down()
    
    # Additional methods would be added here or delegated to appropriate components
    # The key is maintaining the same public interface while organizing the implementation 
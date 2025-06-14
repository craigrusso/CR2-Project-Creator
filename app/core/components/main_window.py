#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Main window component for basic window setup and management
"""

import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon

from app.core.app_config import APP_NAME, APP_VERSION_NUMBER
from app.utils.utils import load_config, load_recent_projects, load_recent_templates
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder


class MainWindow:
    """Handles main window setup, properties, and basic initialization"""
    
    def __init__(self, app_instance):
        """Initialize the main window component"""
        self.app = app_instance
        
        # Class variables for singleton pattern
        self._instance = None
        self._app_icon = None
        
    def setup_window_properties(self):
        """Set up basic window properties"""
        print("DEBUG: Setting up window properties...")
        
        # Set window title
        self.app.setWindowTitle(f"{APP_NAME} {APP_VERSION_NUMBER}")
        
        # Set window size and position
        self.app.resize(1300, 850)
        self.center_window()
        
        # Set up app icon
        self.set_app_icon()
        
        # Set minimum window size
        self.app.setMinimumSize(1000, 600)
        
        print("DEBUG: Window properties set up successfully")
    
    def initialize_core_components(self):
        """Initialize core application components"""
        print("DEBUG: Initializing core components...")
        
        # Initialize template manager
        print("DEBUG: Initializing TemplateManager...")
        self.app.template_manager = TemplateManager()
        print("DEBUG: TemplateManager initialized")
        
        # Initialize project builder
        print("DEBUG: Initializing ProjectBuilder...")
        self.app.project_builder = ProjectBuilder(self.app.template_manager)
        print("DEBUG: ProjectBuilder initialized")
        
        # Initialize status message timer
        self.app.status_message_timer = QTimer()
        self.app.status_message_timer.timeout.connect(self.app._reset_status_bar)
        
        # Initialize batch results
        self.app.batch_results = None
        
        print("DEBUG: Core components initialized successfully")
    
    def load_saved_data(self):
        """Load saved configuration and data"""
        print("DEBUG: Loading saved data...")
        
        # Load configuration
        self.app.config = load_config()
        
        # Load recent files
        self.app.recent_projects = load_recent_projects()
        self.app.recent_templates = load_recent_templates()
        
        # Store app version
        self.app.app_version = APP_VERSION_NUMBER
        
        print("DEBUG: Saved data loaded successfully")
    
    def set_app_icon(self):
        """Set the application icon for this window"""
        app_icon = self.get_app_icon()
        if not app_icon.isNull():
            self.app.setWindowIcon(app_icon)
    
    def get_app_icon(self):
        """Get the application icon as a QIcon object"""
        if self._app_icon is None:
            # Load the icon if it hasn't been loaded before
            icon_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                "app", "assets", "icon.png"
            )
            if os.path.exists(icon_path):
                self._app_icon = QIcon(icon_path)
            else:
                print(f"WARNING: Application icon not found at {icon_path}")
                self._app_icon = QIcon()  # Empty icon to avoid None checks
                
        return self._app_icon
    
    def center_window(self):
        """Center the window on the screen"""
        qr = self.app.frameGeometry()
        screen = QApplication.primaryScreen()
        cp = screen.availableGeometry().center()
        qr.moveCenter(cp)
        self.app.move(qr.topLeft())
    
    def handle_close_event(self, event):
        """Handle window close event"""
        # Save any unsaved data before closing
        try:
            # Save configuration if needed
            if hasattr(self.app, 'config') and self.app.config:
                self.app.config.save()
        except Exception as e:
            print(f"Warning: Error saving configuration on close: {e}")
        
        # Accept the close event
        event.accept()
    
    def get_instance(self):
        """Get the singleton instance of the app"""
        if self._instance is None:
            self._instance = self.app
        return self._instance
    
    def setup_debug_info(self):
        """Set up debug information and logging"""
        print("DEBUG: ProjectCreatorApp component initialization started")
        
        # Debug: Print unique identifiers for all created CardFrames if needed
        from app.ui.ui_components_pyqt import CardFrame
        self.app._orig_cardframe_init = CardFrame.__init__
        
        def debug_cardframe_init(self, *args, **kwargs):
            # print(f"Creating CardFrame with ID: {id(self)}") # DEBUG
            self.app._orig_cardframe_init(*args, **kwargs)
        
        # Temporarily uncomment this to debug CardFrame issues
        # CardFrame.__init__ = debug_cardframe_init
        
        print("DEBUG: Debug setup complete")
    
    def trigger_template_updated(self):
        """Handle template update signal"""
        # Refresh template gallery and related UI elements
        if hasattr(self.app, 'template_gallery'):
            self.app.template_gallery.refresh()
        
        # Refresh other UI components that depend on templates
        if hasattr(self.app, 'recent_files_manager'):
            self.app.recent_files_manager.update_recent_templates_menu()
    
    def show_error(self, message):
        """Show an error message to the user"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self.app, "Error", message)
    
    def show_about_dialog(self):
        """Show the about dialog"""
        from app.dialogs.dialog_windows_pyqt import show_about
        show_about(self.app)
    
    def notify_gallery_preference_changed(self, preference_key):
        """Notify that a gallery preference has changed"""
        if hasattr(self.app, 'gallery_preference_changed'):
            self.app.gallery_preference_changed.emit(preference_key) 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
import logging
from typing import Dict, List, Any, Optional, Union, Callable

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QComboBox, QLineEdit, 
                           QFileDialog, QMessageBox, QAction, QMenu, 
                           QStatusBar, QFrame, QSplitter, QScrollArea, QSizePolicy,
                           QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont

from app.core.app_config import APP_NAME, APP_VERSION, RECENT_TEMPLATES_MAX
from app.core.app_model import AppModel
from app.core.app_controller import AppController
from app.ui.color_scheme_pyqt import get_color, colors
from app.utils.utils import load_config, save_config, truncate_path
from app.ui.ui_components_pyqt import ToolTip, CardFrame, SearchBox, TemplateFileCard
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder
from app.dialogs.dialog_windows_pyqt import (preview_structure, show_batch_create, show_about, 
                                show_tutorial, show_preferences, show_structure_editor)
from app.templates.templates import (get_template_file, clear_template_file, clear_structure_template,
                       rename_current_template, rename_template_file)
from app.templates.template_gallery_ui_pyqt import create_template_gallery, select_template_from_gallery
from app.ui.app_theme_pyqt import apply_dark_theme_to_template_gallery
from app.core.structures_pyqt import (create_custom_structure, edit_structure, update_structure_dropdown,
                     manage_structures, _update_structure_combo, _preview_structure, _edit_structure)
from app.core.project_operations import (create_project, handle_batch_create, 
                             open_recent_project, clear_recent_projects,
                             use_recent_template, clear_recent_templates,
                             add_to_recent_templates, update_card_highlighting,
                             remove_from_recent_templates)
from app.utils.utils import (load_recent_projects, save_recent_projects, 
                 open_folder, create_sample_templates, load_recent_templates,
                 save_recent_templates)

# Set up logging
logger = logging.getLogger(__name__)

class ProjectCreatorApp(QMainWindow):
    """Main application class for CR2 Creative Pro using PyQt (View component in MVC)"""
    
    def __init__(self, model: AppModel, controller: AppController):
        """Initialize the application with MVC dependencies"""
        super().__init__()
        
        # Store references to model and controller
        self.model = model
        self.controller = controller
        
        # Connect controller signals
        self.controller.template_updated.connect(self.trigger_template_updated)
        self.controller.status_update.connect(self.show_status_message)
        self.controller.batch_results_ready.connect(self.check_batch_results)
        
        # Debug: Print unique identifiers for all created CardFrames
        self._orig_cardframe_init = CardFrame.__init__
        
        def debug_cardframe_init(self, *args, **kwargs):
            logger.debug(f"Creating CardFrame with ID: {id(self)}")
            self._orig_cardframe_init(*args, **kwargs)
        
        # Temporarily uncomment this to debug CardFrame issues
        # CardFrame.__init__ = debug_cardframe_init
        
        # Set window properties
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        
        # Set window size and position
        self.resize(1200, 800)
        self.center_window()
        
        # Set up app icon
        self.set_app_icon()
        
        # Initialize status bar timer
        self.status_message_timer = QTimer()
        self.status_message_timer.timeout.connect(self._reset_status_bar)
        
        # Setup UI components
        self._setup_ui()
        self._update_ui_from_config()
        
        # Update UI elements
        self.update_recent_menu()
        self.update_recent_templates_menu()
        
        # Set up a timer to check for batch results
        self.batch_check_timer = QTimer(self)
        self.batch_check_timer.timeout.connect(self.check_batch_results)
        self.batch_check_timer.start(500)  # Check every 500ms
        
        # Show app (make visible)
        self.show()
        
        logger.info("Application UI initialized")
        
    def _setup_ui(self):
        """Set up the main application UI"""
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Create menu bar
        self.create_menu()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_message = QLabel("")
        self.status_bar.addWidget(self.status_message)
        
        # Add main horizontal splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        
        # Create left panel with project settings
        self.left_panel = CardFrame()
        self.left_layout = self.left_panel.main_layout
        
        # Project settings header
        self.settings_header = QLabel("Project Settings")
        self.settings_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.left_layout.addWidget(self.settings_header)
        
        # Project name input
        self.project_name_layout = QHBoxLayout()
        self.project_name_label = QLabel("Project Name:")
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Enter project name...")
        self.project_name_layout.addWidget(self.project_name_label)
        self.project_name_layout.addWidget(self.project_name_input)
        self.left_layout.addLayout(self.project_name_layout)
        
        # Output directory
        self.output_dir_layout = QHBoxLayout()
        self.output_dir_label = QLabel("Output Directory:")
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("Select output directory...")
        self.output_dir_input.setReadOnly(True)
        self.output_dir_btn = QPushButton("Browse...")
        self.output_dir_btn.clicked.connect(self.get_output_dir)
        self.output_dir_layout.addWidget(self.output_dir_label)
        self.output_dir_layout.addWidget(self.output_dir_input)
        self.output_dir_layout.addWidget(self.output_dir_btn)
        self.left_layout.addLayout(self.output_dir_layout)
        
        # Template file selection
        self.template_file_layout = QHBoxLayout()
        self.template_file_label = QLabel("Template File:")
        self.template_file_input = QLineEdit()
        self.template_file_input.setPlaceholderText("Select template file...")
        self.template_file_input.setReadOnly(True)
        self.template_file_btn = QPushButton("Browse...")
        self.template_file_btn.clicked.connect(self._select_template_file)
        self.template_file_layout.addWidget(self.template_file_label)
        self.template_file_layout.addWidget(self.template_file_input)
        self.template_file_layout.addWidget(self.template_file_btn)
        self.left_layout.addLayout(self.template_file_layout)
        
        # Structure selection
        self.structure_layout = QHBoxLayout()
        self.structure_label = QLabel("Folder Structure:")
        self.structure_combo = QComboBox()
        self.structure_btn = QPushButton("Edit...")
        self.structure_btn.clicked.connect(self._edit_structure)
        self.structure_layout.addWidget(self.structure_label)
        self.structure_layout.addWidget(self.structure_combo)
        self.structure_layout.addWidget(self.structure_btn)
        self.left_layout.addLayout(self.structure_layout)
        
        # Populate structure combo
        self._update_structure_combo()
        
        # Preview button
        self.preview_btn = QPushButton("Preview Structure")
        self.preview_btn.clicked.connect(self._preview_structure)
        self.left_layout.addWidget(self.preview_btn)
        
        # Create project button
        self.create_btn = QPushButton("Create Project")
        self.create_btn.clicked.connect(lambda: create_project(self))
        self.left_layout.addWidget(self.create_btn)
        
        # Batch create project button
        self.batch_create_btn = QPushButton("Batch Create Projects")
        self.batch_create_btn.clicked.connect(lambda: show_batch_create(self))
        self.left_layout.addWidget(self.batch_create_btn)
        
        # Add spacing
        self.left_layout.addStretch(1)
        
        # Create right panel with template gallery
        self.right_panel = QWidget()
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create template gallery
        self.template_gallery = create_template_gallery(self)
        self.right_layout.addWidget(self.template_gallery)
        
        # Apply theme to template gallery
        apply_dark_theme_to_template_gallery(self.template_gallery)
        
        # Add panels to splitter
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.right_panel)
        self.main_splitter.setSizes([300, 500])  # Initial sizes
        
        # Apply initial config
        self._update_ui_from_config()
        
    def _update_ui_from_config(self):
        """Update UI elements based on loaded configuration"""
        # Load last output directory if available
        last_output_dir = self.model.config.get("last_output_dir", "")
        if last_output_dir and hasattr(self, 'output_dir_input'):
            self.output_dir_input.setText(last_output_dir)
            
        # Load other UI elements from config as needed
        # (like structure selection, template location, etc.)
        if hasattr(self, 'structure_combo'):
            # Attempt to set the last used structure if available
            last_structure = self.model.config.get("last_structure", "Default")
            idx = self.structure_combo.findText(last_structure)
            if idx >= 0:
                self.structure_combo.setCurrentIndex(idx)
        
    def set_app_icon(self):
        """Set the application icon"""
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               "app", "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
    def center_window(self):
        """Center the window on the screen"""
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def create_menu(self):
        """Create application menus"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Save template action
        save_template_action = QAction("Save Template...", self)
        save_template_action.triggered.connect(lambda: self.model.template_manager.save_template_ui(self))
        file_menu.addAction(save_template_action)
        
        # Import template action
        import_template_action = QAction("Import Template...", self)
        import_template_action.triggered.connect(lambda: self.model.template_manager.import_template_ui(self))
        file_menu.addAction(import_template_action)
        
        # Manage templates action
        manage_templates_action = QAction("Manage Templates...", self)
        manage_templates_action.triggered.connect(lambda: self.model.template_manager.manage_templates_ui(self))
        file_menu.addAction(manage_templates_action)
        
        file_menu.addSeparator()
        
        # Recent projects menu
        self.recent_menu = QMenu("Recent Projects", self)
        file_menu.addMenu(self.recent_menu)
        self.update_recent_menu()
        
        # Clear Recent Projects action
        clear_recent_action = QAction("Clear Recent Projects", self)
        clear_recent_action.triggered.connect(lambda: clear_recent_projects(self))
        file_menu.addAction(clear_recent_action)
        
        file_menu.addSeparator()
        
        # Recent templates menu
        self.recent_templates_menu = QMenu("Recent Templates", self)
        file_menu.addMenu(self.recent_templates_menu)
        self.update_recent_templates_menu()
        
        # Clear Recent Templates action
        clear_recent_templates_action = QAction("Clear Recent Templates", self)
        clear_recent_templates_action.triggered.connect(lambda: clear_recent_templates(self))
        file_menu.addAction(clear_recent_templates_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        # Preferences action
        preferences_action = QAction("Preferences...", self)
        preferences_action.triggered.connect(lambda: show_preferences(self))
        edit_menu.addAction(preferences_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # Refresh Template Gallery
        refresh_gallery_action = QAction("Refresh Template Gallery", self)
        refresh_gallery_action.triggered.connect(lambda: self.template_gallery.populate_gallery())
        view_menu.addAction(refresh_gallery_action)
        
        # Refresh Structure List
        refresh_structure_action = QAction("Refresh Structure List", self)
        refresh_structure_action.triggered.connect(self._update_structure_combo)
        view_menu.addAction(refresh_structure_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        # Batch Create action
        batch_create_action = QAction("Batch Create...", self)
        batch_create_action.triggered.connect(lambda: show_batch_create(self))
        tools_menu.addAction(batch_create_action)
        
        # Create Custom Structure action
        custom_structure_action = QAction("Create Custom Structure...", self)
        custom_structure_action.triggered.connect(self._create_custom_structure)
        tools_menu.addAction(custom_structure_action)
        
        # Manage Custom Structures action
        manage_structures_action = QAction("Manage Custom Structures...", self)
        manage_structures_action.triggered.connect(self._manage_structures)
        tools_menu.addAction(manage_structures_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        # Tutorial action
        tutorial_action = QAction("Tutorial", self)
        tutorial_action.triggered.connect(lambda: show_tutorial(self))
        help_menu.addAction(tutorial_action)
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(lambda: show_about(self))
        help_menu.addAction(about_action)
        
        # Check for Updates action
        updates_action = QAction("Check for Updates", self)
        updates_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(updates_action)
    
    def filter_templates(self, search_text):
        """Filter templates based on search text"""
        if hasattr(self, 'template_gallery'):
            self.template_gallery.filter_templates(search_text)

    def update_recent_templates_gallery(self):
        """Update the recent templates gallery"""
        if hasattr(self, 'recent_templates_gallery'):
            self.recent_templates_gallery.update_templates(self.model.template_manager.get_folder_templates("Recent"))

    def get_output_dir(self):
        """Get output directory from user"""
        starting_dir = self.get_current_output_dir() or os.path.expanduser("~")
        
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            starting_dir,
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            self.output_dir_input.setText(directory)
            
            # Save to config
            self.model.config["last_output_dir"] = directory
            self.model.save_config()
            
        return directory  # Return the selected directory so it can be used by callers

    def get_current_output_dir(self):
        """Get the current output directory from the UI"""
        if hasattr(self, 'output_dir_input'):
            return self.output_dir_input.text().strip()
        return ""

    def update_recent_menu(self):
        """Update the recent projects menu"""
        if hasattr(self, 'recent_menu'):
            self.recent_menu.clear()
            
            # Add recent projects
            if not self.model.recent_projects:
                no_recent_action = QAction("No Recent Projects", self)
                no_recent_action.setEnabled(False)
                self.recent_menu.addAction(no_recent_action)
            else:
                # Process recent projects
                projects_list = []
                
                # Check the type of recent_projects and convert to a list of strings
                if isinstance(self.model.recent_projects, list):
                    # Filter out non-string items
                    projects_list = [p for p in self.model.recent_projects if isinstance(p, str)]
                elif isinstance(self.model.recent_projects, dict):
                    # Extract paths from dict values if they are strings
                    projects_list = [v for v in self.model.recent_projects.values() if isinstance(v, str)]
                
                # If we have no valid projects after filtering
                if not projects_list:
                    no_recent_action = QAction("No Recent Projects", self)
                    no_recent_action.setEnabled(False)
                    self.recent_menu.addAction(no_recent_action)
                else:
                    # Add each valid project path
                    for project_path in projects_list[:10]:  # Limit to 10 items
                        try:
                            # Create action with truncated path
                            name = os.path.basename(project_path)
                            truncated_path = truncate_path(project_path, 50)
                            action = QAction(f"{name} ({truncated_path})", self)
                            action.triggered.connect(lambda checked, p=project_path: self.controller.open_recent_project(p))
                            self.recent_menu.addAction(action)
                        except TypeError as e:
                            logger.error(f"Error processing project path: {project_path}, error: {e}")
            
            # Add separator
            self.recent_menu.addSeparator()
            
            # Add clear recent projects action
            clear_action = QAction("Clear Recent Projects", self)
            clear_action.triggered.connect(self.controller.clear_recent_projects)
            self.recent_menu.addAction(clear_action)

    def update_recent_templates_menu(self):
        """Update the recent templates menu"""
        if hasattr(self, 'recent_templates_menu'):
            self.recent_templates_menu.clear()
            
            # Add recent templates
            if not self.model.recent_templates:
                no_recent_action = QAction("No Recent Templates", self)
                no_recent_action.setEnabled(False)
                self.recent_templates_menu.addAction(no_recent_action)
            else:
                # Process recent templates
                templates_list = []
                
                # Check the type of recent_templates and convert to a list of strings
                if isinstance(self.model.recent_templates, list):
                    # Filter out non-string items
                    templates_list = [t for t in self.model.recent_templates if isinstance(t, str)]
                elif isinstance(self.model.recent_templates, dict):
                    # Extract templates from dict values if they are strings
                    templates_list = [v for v in self.model.recent_templates.values() if isinstance(v, str)]
                
                # If we have no valid templates after filtering
                if not templates_list:
                    no_recent_action = QAction("No Recent Templates", self)
                    no_recent_action.setEnabled(False)
                    self.recent_templates_menu.addAction(no_recent_action)
                else:
                    # Add each valid template
                    max_recent = RECENT_TEMPLATES_MAX
                    for template_name in templates_list[:max_recent]:  # Limit to configured max
                        try:
                            if not template_name:
                                continue
                                
                            # Create action
                            action = QAction(template_name, self)
                            action.triggered.connect(lambda checked, t=template_name: self.controller.use_recent_template(t))
                            self.recent_templates_menu.addAction(action)
                        except Exception as e:
                            logger.error(f"Error processing template: {template_name}, error: {e}")
            
            # Add separator
            self.recent_templates_menu.addSeparator()
            
            # Add clear recent templates action
            clear_action = QAction("Clear Recent Templates", self)
            clear_action.triggered.connect(self.controller.clear_recent_templates)
            self.recent_templates_menu.addAction(clear_action)

    def trigger_template_updated(self):
        """Handle template updated signal"""
        # Update UI elements
        self.update_recent_templates_menu()
        self.update_recent_menu()
        if hasattr(self, 'template_gallery'):
            self.template_gallery.update_templates()
        
        logger.debug("Template updated event triggered")

    def show_status_message(self, message, message_type="info", duration=5000):
        """Display a status message"""
        if not hasattr(self, 'statusBar'):
            return
            
        # Clear any existing message and timer
        if self.status_message_timer.isActive():
            self.status_message_timer.stop()
            
        # Set message color based on type
        color = {
            "info": "#FFFFFF",     # White for info
            "success": "#4CAF50",  # Green for success
            "warning": "#FFC107",  # Yellow/amber for warning
            "error": "#F44336"     # Red for error
        }.get(message_type.lower(), "#FFFFFF")
        
        # Display message with color
        self.statusBar().showMessage(message)
        self.statusBar().setStyleSheet(f"color: {color};")
        
        # Set timer to clear message
        if duration > 0:
            self.status_message_timer.start(duration)
            
        # Log status
        log_level = {
            "info": logging.INFO,
            "success": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR
        }.get(message_type.lower(), logging.INFO)
        logger.log(log_level, f"Status: {message}")

    def _reset_status_bar(self):
        """Reset the status bar to default state"""
        if hasattr(self, 'statusBar'):
            self.statusBar().clearMessage()
            self.statusBar().setStyleSheet("") # Reset to default style
            
        # Stop the timer
        self.status_message_timer.stop()

    def check_for_updates(self):
        """Check for application updates"""
        # Background task to check for updates
        self.show_status_message("Checking for updates...", "info")
        
        # Use the controller to run this asynchronously
        self.controller.run_async(
            self._perform_update_check,
            self.update_check_complete
        )

    def update_check_complete(self):
        """Handle update check completion"""
        self.show_status_message("You are running the latest version", "success", 5000)

    def _perform_update_check(self):
        """
        Perform the actual update check (async)
        This would connect to a remote service to check for updates.
        Currently just simulates the check with a delay.
        """
        import time
        
        logger.info("Performing update check")
        
        # Simulate network delay
        time.sleep(2)
        
        # In a real implementation, this would check against a remote server
        latest_version = APP_VERSION
        
        # Return True if update available, False otherwise
        current_version_parts = APP_VERSION.split('.')
        latest_version_parts = latest_version.split('.')
        
        # Compare version parts
        for i in range(min(len(current_version_parts), len(latest_version_parts))):
            if int(latest_version_parts[i]) > int(current_version_parts[i]):
                logger.info(f"Update available: {latest_version}")
                return True
            elif int(latest_version_parts[i]) < int(current_version_parts[i]):
                logger.info(f"Current version is newer than latest release: {APP_VERSION} > {latest_version}")
                return False
                
        # If we get here, versions are equal or couldn't be compared
        logger.info(f"Application is up to date: {APP_VERSION}")
        return False

    def _update_structure_combo(self):
        """Update the structure dropdown with available structures"""
        if not hasattr(self, 'structure_combo'):
            return
            
        # Remember current selection if any
        current_selection = self.structure_combo.currentText()
        
        # Clear current items
        self.structure_combo.clear()
        
        # Add default structures
        DEFAULT_STRUCTURES = ["Empty", "Basic", "Standard", "Advanced", "Video Editing", "Motion Graphics", "Audio"]
        for structure in DEFAULT_STRUCTURES:
            self.structure_combo.addItem(structure)
            
        # Add custom structures
        for name in sorted(self.model.template_manager.custom_structures.keys()):
            self.structure_combo.addItem(name)
        
        # Restore previous selection or set default
        index = self.structure_combo.findText(current_selection) 
        if index >= 0:
            self.structure_combo.setCurrentIndex(index)
        else:
            # Set to Default structure if available, otherwise first item
            default_index = self.structure_combo.findText("Standard")
            if default_index >= 0:
                self.structure_combo.setCurrentIndex(default_index)
            elif self.structure_combo.count() > 0:
                self.structure_combo.setCurrentIndex(0)

    def _select_template_file(self):
        """Open file dialog to select template file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Template File",
            "",
            "Project Files (*.prproj *.aep *.aepx *.psd *.ai *.blend *.c4d);;Adobe Premiere (*.prproj);;After Effects (*.aep;*.aepx);;Photoshop (*.psd);;Illustrator (*.ai);;Blender (*.blend);;Cinema 4D (*.c4d);;All Files (*.*)"
        )
        
        if file_path:
            # Update template file input
            get_template_file(self, file_path)
            
        return file_path

    def _edit_structure(self):
        """Open dialog to edit the current structure"""
        if not hasattr(self, 'structure_combo'):
            return
            
        structure_name = self.structure_combo.currentText()
        structure = self.model.template_manager.get_structure(structure_name)
        
        edit_structure(self, structure_name, structure)

    def _preview_structure(self):
        """Preview the current structure"""
        if not hasattr(self, 'structure_combo'):
            return
            
        structure_type = self.structure_combo.currentText()
        
        # Get structure
        structure = self.model.template_manager.get_structure(structure_type)
        
        # Show preview dialog
        preview_structure(self, structure)

    def _create_custom_structure(self):
        """Create a new custom structure"""
        create_custom_structure(self)

    def _manage_structures(self):
        """Manage custom structures"""
        manage_structures(self)

    def check_batch_results(self):
        """Check if batch creation results are available and show summary"""
        batch_results = self.model.batch_results
        if batch_results:
            # Clear results from model
            self.model.batch_results = None
            self.batch_check_timer.stop()
            
            # Show results summary
            total = batch_results.get("total", 0)
            successful = batch_results.get("successful", 0)
            failed = batch_results.get("failed", 0)
            
            if failed > 0:
                self.show_status_message(f"Batch creation completed: {successful} successful, {failed} failed", "warning", 10000)
            else:
                self.show_status_message(f"Successfully created {successful} projects", "success", 10000)
                
            # Enable batch creation button if it exists
            if hasattr(self, 'batch_button'):
                self.batch_button.setEnabled(True) 
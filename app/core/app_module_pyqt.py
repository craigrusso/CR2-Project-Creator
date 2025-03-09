#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QComboBox, QLineEdit, 
                           QFileDialog, QMessageBox, QAction, QMenu, 
                           QStatusBar, QFrame, QSplitter, QScrollArea, QSizePolicy,
                           QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont

from app.core.app_config import APP_NAME, APP_VERSION, RECENT_TEMPLATES_MAX
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

class ProjectCreatorApp(QMainWindow):
    """Main application class for CR2 Creative Pro using PyQt"""
    
    # Signal for template updates
    template_updated = pyqtSignal()
    
    def __init__(self):
        """Initialize the application"""
        super().__init__()
        
        # Debug: Print unique identifiers for all created CardFrames
        self._orig_cardframe_init = CardFrame.__init__
        
        def debug_cardframe_init(self, *args, **kwargs):
            print(f"Creating CardFrame with ID: {id(self)}")
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
        
        # Initialize instance variables
        self.template_manager = TemplateManager()
        self.project_builder = ProjectBuilder(self.template_manager)
        self.status_message_timer = QTimer()
        self.status_message_timer.timeout.connect(self._reset_status_bar)
        
        # Batch project creation results
        self.batch_results = None
        
        # Load saved data
        self.config = load_config()
        self.recent_projects = load_recent_projects()
        self.recent_templates = load_recent_templates()
        
        # Setup UI components
        self._setup_ui()
        self._update_ui_from_config()
        
        # Connect signals
        self.template_updated.connect(self.trigger_template_updated)
        
        # Update UI elements
        self.update_recent_menu()
        self.update_recent_templates_menu()
        
        # Set up a timer to check for batch results
        self.batch_check_timer = QTimer(self)
        self.batch_check_timer.timeout.connect(self.check_batch_results)
        self.batch_check_timer.start(500)  # Check every 500ms
        
        # Show app (make visible)
        self.show()
        
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
        last_output_dir = self.config.get("last_output_dir", "")
        if last_output_dir and hasattr(self, 'output_dir_input'):
            self.output_dir_input.setText(last_output_dir)
            
        # Load other UI elements from config as needed
        # (like structure selection, template location, etc.)
        if hasattr(self, 'structure_combo'):
            # Attempt to set the last used structure if available
            last_structure = self.config.get("last_structure", "Default")
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
        save_template_action.triggered.connect(lambda: self.template_manager.save_template_ui(self))
        file_menu.addAction(save_template_action)
        
        # Import template action
        import_template_action = QAction("Import Template...", self)
        import_template_action.triggered.connect(lambda: self.template_manager.import_template_ui(self))
        file_menu.addAction(import_template_action)
        
        # Manage templates action
        manage_templates_action = QAction("Manage Templates...", self)
        manage_templates_action.triggered.connect(lambda: self.template_manager.manage_templates_ui(self))
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
        # Template gallery handles its own filtering
        pass
        
    def update_recent_templates_gallery(self):
        """Update the recent templates gallery section"""
        # Trigger template gallery to update
        if hasattr(self, 'template_gallery'):
            self.template_gallery.populate_gallery()
        
    def get_output_dir(self):
        """Open file dialog to select output directory"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Output Directory",
            self.output_dir_input.text() if hasattr(self, 'output_dir_input') else "",
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            # Update the output directory entry
            if hasattr(self, 'output_dir_input'):
                self.output_dir_input.setText(directory)
            
            # Save to config
            self.config["last_output_dir"] = directory
            save_config(self.config)
            
        return directory  # Return the selected directory so it can be used by callers
    
    def get_current_output_dir(self):
        """Get the current output directory from the entry field"""
        if hasattr(self, 'output_dir_input'):
            return self.output_dir_input.text()
        return ""
        
    def update_recent_menu(self):
        """Update the recent projects menu"""
        # Clear existing items
        self.recent_menu.clear()
        
        # Add recent projects
        if not self.recent_projects:
            no_recent_action = QAction("No Recent Projects", self)
            no_recent_action.setEnabled(False)
            self.recent_menu.addAction(no_recent_action)
        else:
            # Check if recent_projects is a list or dict
            if isinstance(self.recent_projects, list):
                projects_list = self.recent_projects
            elif isinstance(self.recent_projects, dict):
                # If it's a dict, we'll extract the paths
                projects_list = list(self.recent_projects.values()) if self.recent_projects else []
            else:
                # Default empty list for any other type
                projects_list = []
            
            # Add each recent project
            for project_path in projects_list:
                if isinstance(project_path, str):
                    project_name = os.path.basename(project_path)
                    action = QAction(f"{project_name} ({truncate_path(project_path)})", self)
                    action.triggered.connect(lambda checked=False, p=project_path: open_recent_project(self, p))
                    self.recent_menu.addAction(action)
    
    def update_recent_templates_menu(self):
        """Update the recent templates menu"""
        # Clear existing items
        self.recent_templates_menu.clear()
        
        # Add recent templates
        if not self.recent_templates:
            no_recent_action = QAction("No Recent Templates", self)
            no_recent_action.setEnabled(False)
            self.recent_templates_menu.addAction(no_recent_action)
        else:
            # Check if recent_templates is a list or dict
            if isinstance(self.recent_templates, list):
                templates_list = self.recent_templates
            elif isinstance(self.recent_templates, dict):
                # If it's a dict, we'll extract the paths
                templates_list = list(self.recent_templates.values()) if self.recent_templates else []
            else:
                # Default empty list for any other type
                templates_list = []
            
            # Add each recent template
            for template_path in templates_list:
                if isinstance(template_path, str):
                    template_name = os.path.basename(template_path)
                    action = QAction(f"{template_name} ({truncate_path(template_path)})", self)
                    action.triggered.connect(lambda checked=False, t=template_path: use_recent_template(self, t))
                    self.recent_templates_menu.addAction(action)
    
    def trigger_template_updated(self):
        """Handle template updated signal"""
        # Update UI elements that depend on template data
        pass
    
    def show_status_message(self, message, message_type="info", duration=5000):
        """Show a status message in the status bar"""
        # Stop any existing timer
        self.status_message_timer.stop()
        
        # Set message style based on type
        style = ""
        if message_type == "success":
            style = f"background-color: {colors['success']}; color: {colors['success_text']}; padding: 5px;"
        elif message_type == "error":
            style = f"background-color: {colors['error']}; color: white; padding: 5px;"
        elif message_type == "warning":
            style = f"background-color: {colors['warning']}; color: black; padding: 5px;"
        else:  # info
            style = f"background-color: {colors['accent']}; color: white; padding: 5px;"
        
        # Set status bar message and style
        self.status_bar.setStyleSheet(style)
        self.status_bar.showMessage(message)
        
        # Start timer to clear message after duration
        if duration > 0:
            self.status_message_timer.start(duration)
    
    def _reset_status_bar(self):
        """Reset the status bar to its default state"""
        # Stop the timer
        self.status_message_timer.stop()
        
        # Clear message and reset style
        self.status_bar.clearMessage()
        self.status_bar.setStyleSheet(f"background-color: {colors['card_bg']}; color: {colors['text']}")
    
    def check_for_updates(self):
        """Check for application updates"""
        # This would connect to a service to check for updates
        self.show_status_message("Checking for updates...", "info", 2000)
        
        # Simulate checking for updates
        QTimer.singleShot(2000, self.update_check_complete)
    
    def update_check_complete(self):
        """Called when update check is complete"""
        # For now, just show a message that we're up to date
        self.show_status_message("Your application is up to date!", "success", 5000)
    
    def _update_structure_combo(self):
        """Update the structure dropdown with available structures"""
        self.structure_combo.clear()
        
        # Add default structures
        self.structure_combo.addItem("Standard")
        self.structure_combo.addItem("Video Editing")
        self.structure_combo.addItem("Motion Graphics")
        self.structure_combo.addItem("Design")
        self.structure_combo.addItem("Audio")
        
        # Add custom structures
        for name in sorted(self.template_manager.custom_structures.keys()):
            self.structure_combo.addItem(name)
    
    def _select_template_file(self):
        """Open file dialog to select a template file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Template File",
            "",
            "All Files (*);;Project Files (*.prproj *.aep *.aepx *.psd *.ai)"
        )
        
        if file_path:
            self.template_file_input.setText(file_path)
            self.template_file_path = file_path
    
    def _edit_structure(self):
        """Open structure editor dialog"""
        # Get current structure type
        structure_type = self.structure_combo.currentText()
        
        # Show structure editor dialog
        from app.dialogs.dialog_windows_pyqt import show_structure_editor
        show_structure_editor(self, structure_type, self._update_structure_combo)
    
    def _preview_structure(self):
        """Preview the selected structure"""
        # Get current structure type
        structure_type = self.structure_combo.currentText()
        
        # Get structure
        structure = self.template_manager.get_structure(structure_type)
        
        # Show preview dialog
        from app.dialogs.dialog_windows_pyqt import preview_structure
        preview_structure(self, structure)
    
    def _create_custom_structure(self):
        """Create a new custom structure"""
        from app.dialogs.dialog_windows_pyqt import show_structure_editor
        show_structure_editor(self, None, self._update_structure_combo)
    
    def _manage_structures(self):
        """Manage custom structures"""
        # TODO: Implement manage structures dialog
        QMessageBox.information(self, "Not Implemented", "Structure management dialog not yet implemented in PyQt version.")
    
    def check_batch_results(self):
        """Check for batch results and display them if available"""
        if hasattr(self, 'batch_results') and self.batch_results:
            from app.dialogs.dialog_windows_pyqt import show_batch_results
            results = self.batch_results
            self.batch_results = None  # Clear results to avoid showing them again
            show_batch_results(self, results) 
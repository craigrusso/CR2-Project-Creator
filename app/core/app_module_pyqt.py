#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QComboBox, QLineEdit, 
                           QFileDialog, QMessageBox, QAction, QMenu, 
                           QStatusBar, QFrame, QSplitter, QScrollArea, QSizePolicy,
                           QApplication, QGroupBox, QListView, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QEvent, QModelIndex
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QPainter, QPen, QBrush, QPixmap, QDesktopServices

from app.core.app_config import APP_NAME, APP_VERSION, RECENT_TEMPLATES_MAX
from app.ui.color_scheme_pyqt import get_color, colors, BUTTON_STYLE, COMBOBOX_STYLE, ACCENT_BUTTON_STYLE, LISTVIEW_POPUP_STYLE, APP_COLORS
from app.utils.utils import load_config, save_config, truncate_path
from app.ui.ui_components_pyqt import ToolTip, CardFrame, SearchBox, TemplateFileCard, ScrollableFrame, UI_FONT
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder
from app.dialogs.dialog_windows_pyqt import (preview_structure, show_about, 
                                show_tutorial, show_preferences, show_edit_template,
                                show_batch_results)
from app.templates.template_utils import (get_template_file, clear_template_file, clear_structure_template,
                       rename_current_template, rename_template_file)
from app.templates.refactored_template_gallery import create_template_gallery, select_template_from_gallery
from app.ui.app_theme_pyqt import apply_dark_theme_to_template_gallery
from app.core.structures_pyqt import (create_custom_structure, edit_structure, update_structure_dropdown,
                     manage_structures, _update_structure_combo, _preview_structure, _edit_structure)
from app.core.project_operations import (handle_batch_create, 
                             open_recent_project, clear_recent_projects,
                             use_recent_template, clear_recent_templates,
                             add_to_recent_templates, update_card_highlighting,
                             remove_from_recent_templates)
from app.utils.utils import (load_recent_projects, save_recent_projects, 
                 open_folder, create_sample_templates, load_recent_templates,
                 save_recent_templates)
from app.templates.template_gallery_ui_pyqt import create_template_gallery
from app.dialogs.template_creation_form import show_template_creation_form
from app.templates.components.utils import get_system_font, SYSTEM_FONT

class ProjectCreatorApp(QMainWindow):
    """Main application class for CR2 Creative Pro using PyQt"""
    
    # Signal for template updates
    template_updated = pyqtSignal()
    
    # Class variable to hold the instance
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of the app"""
        # Return existing instance or create a new one if needed
        if cls._instance is None:
            print("Creating new ProjectCreatorApp instance")
            cls._instance = cls()
        return cls._instance
    
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
        
        # Store the app version
        self.app_version = APP_VERSION
        
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
        
        # Configure status bar for proper text display
        self.status_bar.setStyleSheet("""
            QStatusBar { 
                padding-left: 8px; 
                min-height: 24px;
            }
            QStatusBar::item {
                border: none;
                padding-left: 8px;
            }
        """)
        
        # Set minimum window size to ensure all elements are visible
        self.setMinimumSize(1000, 600)
        
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
        
        # Batch project input area - integrated directly into the main UI
        self.batch_projects_header = QLabel("Enter Project Names")
        self.batch_projects_header.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.left_layout.addWidget(self.batch_projects_header)
        
        # Instructions for batch projects
        self.batch_instructions = QLabel(
            "Enter one project name per line. You can also separate names with commas or semicolons.\n"
            "All projects will be created using the selected template and output location."
        )
        self.batch_instructions.setWordWrap(True)
        self.batch_instructions.setStyleSheet(f"color: {colors['secondary_text']};")
        self.left_layout.addWidget(self.batch_instructions)
        
        # Create dummy structure_combo property for compatibility
        # This ensures other parts of the code that reference it will still work
        self.structure_combo = QComboBox()
        self.structure_combo.hide()  # Hide it from view
        
        # Create a stretching middle section for the batch text edit
        middle_container = QWidget()
        middle_layout = QVBoxLayout(middle_container)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        
        # Text input area for batch projects - this should expand
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
        # Set size policy to make text edit expand
        self.batch_text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        middle_layout.addWidget(self.batch_text_edit)
        
        # Add the expandable middle section
        self.left_layout.addWidget(middle_container, 1)  # Use stretch factor of 1
        
        # Create a fixed bottom section for output directory and create button
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 10, 0, 0)  # Add some top margin for separation
        
        # Output directory
        self.output_dir_layout = QHBoxLayout()
        self.output_dir_label = QLabel("Output Directory:")
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("Select output directory...")
        self.output_dir_input.setReadOnly(True)
        self.output_dir_btn = QPushButton("Browse...")
        self.output_dir_btn.clicked.connect(self.get_output_dir)
        # Custom style for the browse button - lighter grey with distinct hover state
        self.output_dir_btn.setStyleSheet("""
            QPushButton {
                background-color: #383838;  /* Lighter grey than default */
                color: #CCCCCC;
                border: 1px solid #3C3C3C;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #454545;
                border: 1px solid #2C4F76;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2C4F76;
                color: white;
            }
        """)
        self.output_dir_layout.addWidget(self.output_dir_label)
        self.output_dir_layout.addWidget(self.output_dir_input)
        self.output_dir_layout.addWidget(self.output_dir_btn)
        bottom_layout.addLayout(self.output_dir_layout)
        
        # Add some spacing before the create button
        bottom_layout.addSpacing(10)
        
        # Batch create project button
        self.batch_create_btn = QPushButton("Create Projects")
        self.batch_create_btn.clicked.connect(self.process_batch_projects)
        self.batch_create_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        # Set minimum height for the button to make it more prominent
        self.batch_create_btn.setMinimumHeight(40)
        bottom_layout.addWidget(self.batch_create_btn)
        
        # Add the bottom container to the main layout (fixed size, won't stretch)
        self.left_layout.addWidget(bottom_container, 0)  # Use stretch factor of 0
        
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
        
        # Set minimum widths for panels to ensure they're always usable
        self.left_panel.setMinimumWidth(280)
        self.right_panel.setMinimumWidth(450)  # Ensure right panel buttons remain visible
        
        # Initial sizes
        self.main_splitter.setSizes([300, 700])  
        self.main_splitter.setHandleWidth(6)  # Standard handle width
        
        # Allow panels to be collapsed to their minimum size but not further
        self.main_splitter.setCollapsible(0, True)
        self.main_splitter.setCollapsible(1, True)
        
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
        """Create application menus that are OS-aware (macOS vs Windows)"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # New Template action (new)
        new_template_action = QAction("New Template...", self)
        new_template_action.triggered.connect(self._create_template)
        file_menu.addAction(new_template_action)
        
        file_menu.addSeparator()
        
        # Import template action
        import_template_action = QAction("Import Template...", self)
        import_template_action.triggered.connect(lambda: self.template_manager.import_template_ui(self))
        file_menu.addAction(import_template_action)
        
        # Export/Import Settings section
        file_menu.addSeparator()
        
        # Export submenu
        export_menu = QMenu("Export", self)
        
        # Export all settings and templates
        export_all_action = QAction("All Settings and Templates...", self)
        export_all_action.triggered.connect(self._export_all)
        export_menu.addAction(export_all_action)
        
        # Export templates only
        export_templates_action = QAction("Templates Only...", self)
        export_templates_action.triggered.connect(self._export_templates)
        export_menu.addAction(export_templates_action)
        
        # Export settings only
        export_settings_action = QAction("Settings Only...", self)
        export_settings_action.triggered.connect(self._export_settings)
        export_menu.addAction(export_settings_action)
        
        # Add export menu to file menu
        file_menu.addMenu(export_menu)
        
        # Import submenu
        import_menu = QMenu("Import", self)
        
        # Import all settings and templates
        import_all_action = QAction("All Settings and Templates...", self)
        import_all_action.triggered.connect(self._import_all)
        import_menu.addAction(import_all_action)
        
        # Import templates only
        import_templates_action = QAction("Templates Only...", self)
        import_templates_action.triggered.connect(self._import_templates)
        import_menu.addAction(import_templates_action)
        
        # Import settings only
        import_settings_action = QAction("Settings Only...", self)
        import_settings_action.triggered.connect(self._import_settings)
        import_menu.addAction(import_settings_action)
        
        # Add import menu to file menu
        file_menu.addMenu(import_menu)
        
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
        
        # Don't show Exit on macOS as it's handled by the system
        if platform.system() != "Darwin":  # Not macOS
            file_menu.addSeparator()
            
            # Exit action
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        # Preferences action - use standard macOS naming convention on Mac
        if platform.system() == "Darwin":  # macOS
            preferences_action = QAction("Preferences...", self)
            # Set shortcut for macOS (Command+,)
            preferences_action.setShortcut("Ctrl+,")
        else:
            preferences_action = QAction("Settings...", self)
            # Set shortcut for Windows/Linux
            preferences_action.setShortcut("Ctrl+P") 
            
        preferences_action.triggered.connect(lambda: show_preferences(self))
        edit_menu.addAction(preferences_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # Refresh Template Gallery
        refresh_gallery_action = QAction("Refresh Template Gallery", self)
        refresh_gallery_action.triggered.connect(lambda: self.template_gallery.populate_gallery())
        view_menu.addAction(refresh_gallery_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        # Batch Create action
        batch_create_action = QAction("Batch Create...", self)
        batch_create_action.triggered.connect(self.process_batch_projects)
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
        
        # About action - should be in app menu on macOS, but we'll add it here for completeness
        if platform.system() != "Darwin":  # Not macOS
            about_action = QAction("About", self)
        else:
            about_action = QAction("About CR2 Creative Pro", self)
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
        base_style = """
            QStatusBar { 
                padding-left: 8px; 
                min-height: 24px;
            }
            QStatusBar::item {
                border: none;
                padding-left: 8px;
            }
        """
        
        if message_type == "success":
            style = base_style + f"QStatusBar {{ background-color: {colors['success']}; color: {colors['success_text']}; }}"
        elif message_type == "error":
            style = base_style + f"QStatusBar {{ background-color: {colors['error']}; color: white; }}"
        elif message_type == "warning":
            style = base_style + f"QStatusBar {{ background-color: {colors['warning']}; color: black; }}"
        else:  # info
            style = base_style + f"QStatusBar {{ background-color: {colors['accent']}; color: white; }}"
        
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
        
        # Reset to default style while maintaining proper padding
        base_style = """
            QStatusBar { 
                padding-left: 8px; 
                min-height: 24px;
                background-color: """ + colors['card_bg'] + """; 
                color: """ + colors['text'] + """;
            }
            QStatusBar::item {
                border: none;
                padding-left: 8px;
            }
        """
        self.status_bar.setStyleSheet(base_style)
    
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
        """Update the structure dropdown with available structures
        
        Note: The UI element has been removed, but we keep this method for compatibility.
        We still populate the hidden combo box to ensure the structure selection works properly.
        """
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
            
        # Select the default structure
        self.structure_combo.setCurrentIndex(0)
    
    def _select_template_file(self):
        """This method is no longer needed as templates contain their files"""
        pass  # Keeping the method as a stub for compatibility
    
    def _edit_structure(self):
        """Open structure editor dialog
        
        Note: The UI element for this has been removed. This method is kept
        for compatibility with other parts of the code.
        """
        # Use Standard as the default structure type
        structure_type = "Standard"
        
        # Show structure editor dialog
        from app.dialogs.dialog_windows_pyqt import show_structure_editor
        show_structure_editor(self, structure_type, self._update_structure_combo)
    
    def _preview_structure(self):
        """Preview the selected structure
        
        Note: The UI element for this has been removed. This method is kept
        for compatibility with other parts of the code.
        """
        # Use Standard as the default structure type
        structure_type = "Standard"
        
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
    
    def _create_template(self):
        """Create a new template"""
        try:
            # Use the template manager to create a new template
            success = self.template_manager.create_new_template(self)
            if success:
                self._refresh_ui()
        except Exception as e:
            print(f"Error creating template: {e}")
            import traceback
            traceback.print_exc()

    def _refresh_ui(self):
        """Refresh the UI after creating a new template"""
        # Update UI elements that depend on template data
        pass
        
        # Update recent templates gallery
        self.update_recent_templates_gallery()
        
        # Show status message
        self.show_status_message("Template created successfully!", "success", 5000)

    def eventFilter(self, obj, event):
        """Filter for specific events"""
        # Handle hover effects for structure_combo dropdown - no longer needed as the UI has been removed
        # if hasattr(self, 'structure_combo') and self.structure_combo.view() and obj == self.structure_combo.view().viewport():
        #     if event.type() == QEvent.MouseMove:
        #         # Get the item under the mouse
        #         pos = event.pos()
        #         index = self.structure_combo.view().indexAt(pos)
        #         
        #         if index.isValid():
        #             # Set hover style directly
        #             for i in range(self.structure_combo.view().model().rowCount()):
        #                 item_index = self.structure_combo.view().model().index(i, 0)
        #                 rect = self.structure_combo.view().visualRect(item_index)
        #                 
        #                 # Apply style to the item under cursor
        #                 if rect.contains(pos):
        #                     # Force a repaint of the view
        #                     self.structure_combo.view().update(item_index)
                            
        # Pass the event to the parent class
        return super().eventFilter(obj, event) 

    def process_batch_projects(self):
        """Process the entered project names for batch creation"""
        import re
        from PyQt5.QtWidgets import QMessageBox
        from app.core.project_operations import handle_batch_create
        from app.dialogs.dialog_windows_pyqt import show_batch_results
        
        # Get text from the batch input area
        text = self.batch_text_edit.toPlainText().strip()
        
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter at least one project name.")
            return
        
        # Split by newlines, commas, or semicolons
        project_names = re.split(r'[\n,;]+', text)
        project_names = [name.strip() for name in project_names if name.strip()]
        
        if not project_names:
            QMessageBox.warning(self, "Warning", "No valid project names found.")
            return
        
        # Check for duplicate names
        if len(project_names) != len(set(project_names)):
            duplicates = [name for name in project_names if project_names.count(name) > 1]
            if QMessageBox.question(
                self, 
                "Duplicate Names", 
                f"The following names appear more than once: {', '.join(set(duplicates))}\n\nDo you want to continue anyway?",
                QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.No:
                return
        
        # Validate requirements for project creation
        missing_requirements = []
        
        # Check for a template
        has_template = False
        
        # Check for selected template from gallery first
        if hasattr(self, 'selected_template') and self.selected_template:
            has_template = True
        # Then check for template file path as fallback
        elif hasattr(self, 'template_file_path') and self.template_file_path:
            has_template = True
        # Finally check if there's a template gallery with selected template
        elif hasattr(self, 'template_gallery') and hasattr(self.template_gallery, 'get_selected_template'):
            try:
                selected_template = self.template_gallery.get_selected_template()
                if selected_template:
                    has_template = True
            except Exception as e:
                print(f"Error checking gallery template: {e}")
        
        if not has_template:
            missing_requirements.append("No template selected")
        
        output_dir = self.get_current_output_dir()
        if not output_dir:
            # Instead of adding it to missing requirements, directly prompt for selection
            output_dir = self.get_output_dir()
            if not output_dir:  # User cancelled the directory selection
                self.show_status_message("Project creation cancelled - no output location selected", message_type="warning")
                return
        
        # Check if there's still any missing requirements
        if missing_requirements:
            QMessageBox.critical(
                self, 
                "Missing Requirements", 
                "Cannot create projects due to the following issues:\n\n" + 
                "\n".join([f"• {item}" for item in missing_requirements])
            )
            return
        
        # Removed confirmation dialog - directly create projects
        
        # Convert list of project names to a string for handle_batch_create
        projects_text = "\n".join(project_names)
        
        # Show creating message in status bar
        self.show_status_message(f"Creating {len(project_names)} projects...", message_type="info")
        
        # Execute batch creation
        results = handle_batch_create(self, projects_text)
        
        # Display the results if it's not just a boolean success indicator
        if results and not isinstance(results, bool):
            show_batch_results(self, results)

    def _export_all(self):
        """Export all settings and templates"""
        from app.core.import_export_manager import export_package
        export_package(self, include_settings=True, include_templates=True)
    
    def _export_templates(self):
        """Export templates only"""
        from app.core.import_export_manager import export_package
        export_package(self, include_settings=False, include_templates=True)
    
    def _export_settings(self):
        """Export settings only"""
        from app.core.import_export_manager import export_package
        export_package(self, include_settings=True, include_templates=False)
    
    def _import_all(self):
        """Import all settings and templates"""
        from app.core.import_export_manager import import_package
        import_package(self, import_settings=True, import_templates=True)
    
    def _import_templates(self):
        """Import templates only"""
        from app.core.import_export_manager import import_package
        import_package(self, import_settings=False, import_templates=True)
    
    def _import_settings(self):
        """Import settings only"""
        from app.core.import_export_manager import import_package
        import_package(self, import_settings=True, import_templates=False) 
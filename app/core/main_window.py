#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QApplication, QTabWidget, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSettings
from PyQt6.QtGui import QIcon

from app.core.app_config import APP_NAME, RECENT_TEMPLATES_MAX
from app.ui.color_scheme_pyqt import APP_COLORS
from app.utils.utils import load_config, save_config, load_recent_projects, save_recent_projects, load_recent_templates, save_recent_templates
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder
from app.gallery.gallery_widget import TemplateGallery
from app.ui.app_theme_pyqt import apply_dark_theme_to_template_gallery
from app.ui.ui_components_pyqt import UpdateNotificationBanner
from app.ui.ui_utils import get_styled_app_name

# Import refactored modules
from .update_system.update_worker import UpdateWorker
from .project_creation.batch_creation import BatchCreationManager
from .ui_setup.menu_builder import MenuBuilder
from .ui_setup.layout_manager import LayoutManager
from .ui_setup.versioning_ui import VersioningUI
from .file_operations.recent_files import RecentFilesManager
from .file_operations.import_export import ImportExportManager

from app.constants import APP_VERSION_NUMBER


class ForwardFlowApp(QMainWindow):
    """Main application class for ForwardFlow using PyQt"""
    
    # Signals
    template_updated = pyqtSignal()
    gallery_preference_changed = pyqtSignal(str)
    manual_check_complete = pyqtSignal(bool, object)  # bool: update_found, object: version_info or None
    
    # Class variables
    _instance = None
    _app_icon = None
    
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
    
    def __init__(self):
        """Initialize the application"""
        super().__init__()
        
        # Set window properties
        self.setWindowTitle(f"{get_styled_app_name()} {APP_VERSION_NUMBER}")
        self.resize(1300, 850)
        self.center_window()
        self.set_app_icon()
        
        # Initialize core components
        self.template_manager = TemplateManager()
        self.project_builder = ProjectBuilder(self.template_manager)
        
        # Initialize status message timer
        self.status_message_timer = QTimer()
        self.status_message_timer.timeout.connect(self._reset_status_bar)
        
        # Batch project creation results
        self.batch_results = None
        
        # Load saved data
        self.config = load_config()
        self.recent_projects = load_recent_projects()
        self.recent_templates = load_recent_templates()
        self.app_version = APP_VERSION_NUMBER
        
        # Initialize managers
        self.batch_manager = BatchCreationManager(self)
        self.menu_builder = MenuBuilder(self)
        self.layout_manager = LayoutManager(self)
        self.versioning_ui = VersioningUI(self)
        self.recent_files_manager = RecentFilesManager(self)
        self.import_export_manager = ImportExportManager(self)
        
        # Setup UI
        self._setup_ui()
        self._update_ui_from_config()
        
        # Connect signals
        self.template_updated.connect(self.trigger_template_updated)
        
        # Update UI elements
        self.recent_files_manager.update_recent_menu()
        self.recent_files_manager.update_recent_templates_menu()
    
    def _setup_ui(self):
        """Setup the main UI layout"""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create and setup menu
        self.menu_builder.create_menu()
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        
        # Setup left panel using layout manager
        self.left_panel = self.layout_manager.create_left_panel()
        
        # Create right panel with tab system
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.right_layout.addWidget(self.tab_widget)
        
        # Create Templates tab
        # Create the template gallery
        try:
            print("DEBUG: Creating TemplateGallery...")
            self.template_gallery = TemplateGallery(self.template_manager, self)
            print("DEBUG: TemplateGallery created successfully")
        except Exception as e:
            print(f"DEBUG: Error creating TemplateGallery: {e}")
            import traceback
            traceback.print_exc()
            # Create a simple placeholder instead
            from PyQt6.QtWidgets import QLabel
            self.template_gallery = QLabel("Template Gallery temporarily disabled")
            self.template_gallery.setStyleSheet("color: red; padding: 20px;")
        self.tab_widget.addTab(self.template_gallery, "Templates")
        apply_dark_theme_to_template_gallery(self.template_gallery)
        
        # Create Transfer tab
        try:
            # Check if ingest module is enabled
            from forwardflow.ingest.config import FF_INGEST_ENABLED
            if not FF_INGEST_ENABLED:
                print("Ingest module disabled by configuration")
                # Create a placeholder tab
                self.transfer_tab = QWidget()
                placeholder_layout = QVBoxLayout(self.transfer_tab)
                placeholder_label = QLabel("Transfer module disabled")
                placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder_layout.addWidget(placeholder_label)
                self.tab_widget.addTab(self.transfer_tab, "Transfer")
            else:
                from forwardflow.ingest.ui.ingest_tab import build_ingest_tab
                self.transfer_tab = build_ingest_tab()
                self.tab_widget.addTab(self.transfer_tab, "Transfer")
        except ImportError as e:
            print(f"Warning: Could not import ingest module: {e}")
            # Create a placeholder tab
            self.transfer_tab = QWidget()
            placeholder_layout = QVBoxLayout(self.transfer_tab)
            placeholder_label = QLabel("Transfer module not available")
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_layout.addWidget(placeholder_label)
            self.tab_widget.addTab(self.transfer_tab, "Transfer")
        except Exception as e:
            print(f"Error creating ingest tab: {e}")
            import traceback
            traceback.print_exc()
            # Create a placeholder tab
            self.transfer_tab = QWidget()
            placeholder_layout = QVBoxLayout(self.transfer_tab)
            placeholder_label = QLabel("Transfer module error occurred")
            placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_layout.addWidget(placeholder_label)
            self.tab_widget.addTab(self.transfer_tab, "Transfer")
        
        # Add panels to splitter
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.right_panel)
        
        # Set panel properties
        self.left_panel.setMinimumWidth(280)
        self.right_panel.setMinimumWidth(450)
        self.main_splitter.setSizes([400, 900])
        self.main_splitter.setHandleWidth(6)
        self.main_splitter.setCollapsible(0, True)
        self.main_splitter.setCollapsible(1, True)
        
        # Add Update Notification Banner (initially hidden)
        self.update_banner = UpdateNotificationBanner()
        self.main_layout.insertWidget(0, self.update_banner)
    
    def _update_ui_from_config(self):
        """Update UI elements based on loaded configuration"""
        # Load last output directory if available
        last_output_dir = self.config.get("last_output_dir", "")
        if last_output_dir and hasattr(self, 'output_dir_input'):
            self.output_dir_input.setText(last_output_dir)
            
        # Load other UI elements from config as needed
        if hasattr(self, 'structure_combo'):
            last_structure = self.config.get("last_structure", "Default")
            idx = self.structure_combo.findText(last_structure)
            if idx >= 0:
                self.structure_combo.setCurrentIndex(idx)
    
    def set_app_icon(self):
        """Set the application icon for this window"""
        app_icon = self.get_app_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)
    
    def center_window(self):
        """Center the window on the screen"""
        qr = self.frameGeometry()
        screen = QApplication.primaryScreen()
        cp = screen.availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def trigger_template_updated(self):
        """Handle template update signal"""
        # Refresh template gallery and related UI elements
        if hasattr(self, 'template_gallery'):
            self.template_gallery.refresh()
    
    def show_status_message(self, message, message_type="info", duration=5000):
        """Show a status message in the status bar"""
        if not hasattr(self, 'statusBar'):
            return
            
        status_bar = self.statusBar()
        if message_type == "error":
            status_bar.setStyleSheet(f"color: {APP_COLORS['error']};")
        elif message_type == "success":
            status_bar.setStyleSheet(f"color: {APP_COLORS['success']};")
        else:
            status_bar.setStyleSheet(f"color: {APP_COLORS['text']};")
        
        status_bar.showMessage(message, duration)
        
        # Reset status bar after duration
        self.status_message_timer.stop()
        self.status_message_timer.start(duration)
    
    def _reset_status_bar(self):
        """Reset status bar to default state"""
        if hasattr(self, 'statusBar'):
            self.statusBar().clearMessage()
            self.statusBar().setStyleSheet("")
        self.status_message_timer.stop()
    
    def show_error(self, message):
        """Show an error message"""
        self.show_status_message(message, message_type="error")
    
    def filter_templates(self, search_text):
        """Filter templates based on search text"""
        if hasattr(self, 'template_gallery'):
            self.template_gallery.filter_templates(search_text)
    
    def notify_gallery_preference_changed(self, preference_key):
        """Notify that a gallery preference has changed"""
        self.gallery_preference_changed.emit(preference_key)
    
    # Delegation methods to managers
    def process_batch_projects(self):
        """Delegate to batch creation manager"""
        return self.batch_manager.process_batch_projects()
    
    def _handle_enhanced_batch_creation(self, project_names):
        """Delegate to batch creation manager"""
        return self.batch_manager.handle_enhanced_batch_creation(project_names)
    
    def _generate_sequence_names(self, base_name):
        """Delegate to batch creation manager"""
        return self.batch_manager._generate_sequence_names(base_name)
    
    def update_recent_menu(self):
        """Delegate to recent files manager"""
        return self.recent_files_manager.update_recent_menu()
    
    def update_recent_templates_menu(self):
        """Delegate to recent files manager"""
        return self.recent_files_manager.update_recent_templates_menu()
    
    def _export_all(self):
        """Delegate to import/export manager"""
        return self.import_export_manager.export_all()
    
    def _export_settings(self):
        """Delegate to import/export manager"""
        return self.import_export_manager.export_settings()
    
    def _import_all(self):
        """Delegate to import/export manager"""
        return self.import_export_manager.import_all()
    
    def _import_settings(self):
        """Delegate to import/export manager"""
        return self.import_export_manager.import_settings()
    
    def _toggle_versioning_options(self, enabled):
        """Delegate to versioning UI"""
        return self.versioning_ui.toggle_versioning_options(enabled)
    
    def _update_versioning_options(self):
        """Delegate to versioning UI"""
        return self.versioning_ui.update_versioning_options() 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import platform
import sys
import logging
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from app.core.app_config import APP_NAME, APP_VERSION, setup_dpi_awareness
from app.core.app_model import AppModel
from app.core.app_controller import AppController
from app.core.app_module_pyqt import ProjectCreatorApp
from app.ui.app_theme_pyqt import apply_dark_theme_to_template_section
from app.templates.template_manager_migration import TemplateManagerMigration
from app.core.performance_optimizations import optimize_template_loading, optimize_file_io
from app.utils.utils import get_config_paths

# This is the PyQt version of the application
UI_FRAMEWORK = 'pyqt'

# Set up logging
logger = logging.getLogger(__name__)

def setup_logging():
    """Configure application logging"""
    try:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.expanduser("~"), ".cr2projectcreator", "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Log file path
        log_file = os.path.join(logs_dir, "app.log")
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        logger.info("Logging initialized")
    except Exception as e:
        print(f"Error setting up logging: {e}")

def main():
    """Main entry point for the CR2 Creative Pro application"""
    try:
        # Setup logging
        setup_logging()
        
        # Setup DPI awareness for Windows
        setup_dpi_awareness()
        
        # Set app ID for Windows taskbar
        if platform.system() == "Windows":
            try:
                import ctypes
                myappid = 'cr2creative.projectcreator.pro.2.1'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception as e:
                logger.warning(f"Could not set app ID: {e}")

        # Enable High DPI scaling
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Initialize the PyQt application
        app = QApplication(sys.argv)
        app.setApplicationName(f"{APP_NAME}")
        app.setApplicationVersion(APP_VERSION)
        
        # Initialize MVC components
        model = AppModel()
        controller = AppController(model)
        
        # Apply performance optimizations
        config_paths = get_config_paths()
        optimize_file_io(config_paths.get("templates_dir", ""))
        optimize_template_loading(model.template_manager)
        
        # Create and show the main window
        main_window = ProjectCreatorApp(model, controller)
        main_window.show()
        
        # Apply template migration if needed
        TemplateManagerMigration.apply_migration(main_window)
        
        # Apply dark theme to template section
        apply_dark_theme_to_template_section(main_window)
        
        logger.info(f"Application {APP_NAME} {APP_VERSION} started successfully")
        
        # Start the application main loop
        return app.exec_()
    except Exception as e:
        logger.critical(f"Critical error starting application: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
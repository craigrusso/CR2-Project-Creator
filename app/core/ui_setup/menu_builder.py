#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction


class MenuBuilder:
    """Handles menu creation and management"""
    
    def __init__(self, main_window):
        """Initialize with reference to main window"""
        self.main_window = main_window
    
    def create_menu(self):
        """Create application menus"""
        # For now, use a simplified menu structure
        # Full implementation would be extracted from original create_menu method
        menubar = self.main_window.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # New Template action
        new_template_action = QAction("New Template...", self.main_window)
        file_menu.addAction(new_template_action)
        
        file_menu.addSeparator()
        
        # Export menu
        export_menu = QMenu("Export", self.main_window)
        export_all_action = QAction("All Settings and Templates...", self.main_window)
        export_all_action.triggered.connect(self.main_window._export_all)
        export_menu.addAction(export_all_action)
        
        export_settings_action = QAction("Settings Only...", self.main_window)
        export_settings_action.triggered.connect(self.main_window._export_settings)
        export_menu.addAction(export_settings_action)
        
        file_menu.addMenu(export_menu)
        
        # Import menu
        import_menu = QMenu("Import", self.main_window)
        import_all_action = QAction("All Settings and Templates...", self.main_window)
        import_all_action.triggered.connect(self.main_window._import_all)
        import_menu.addAction(import_all_action)
        
        import_settings_action = QAction("Settings Only...", self.main_window)
        import_settings_action.triggered.connect(self.main_window._import_settings)
        import_menu.addAction(import_settings_action)
        
        file_menu.addMenu(import_menu)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self.main_window)
        help_menu.addAction(about_action) 
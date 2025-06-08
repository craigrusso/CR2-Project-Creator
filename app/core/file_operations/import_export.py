#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from app.core.import_export_manager import export_package, import_package


class ImportExportManager:
    """Handles import/export functionality"""
    
    def __init__(self, main_window):
        """Initialize with reference to main window"""
        self.main_window = main_window
    
    def export_all(self):
        """Export all settings and templates"""
        export_package(self.main_window, include_settings=True, include_templates=True)
    
    def export_settings(self):
        """Export settings only"""
        export_package(self.main_window, include_settings=True, include_templates=False)
    
    def import_all(self):
        """Import all settings and templates"""
        import_package(self.main_window, import_settings=True, import_templates=True)
    
    def import_settings(self):
        """Import settings only"""
        import_package(self.main_window, import_settings=True, import_templates=False) 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction
from app.core.project_operations import (open_recent_project, clear_recent_projects,
                                       use_recent_template, clear_recent_templates,
                                       remove_from_recent_templates)
from app.utils.utils import truncate_path


class RecentFilesManager:
    """Handles recent files and templates management"""
    
    def __init__(self, main_window):
        """Initialize with reference to main window"""
        self.main_window = main_window
    
    def update_recent_menu(self):
        """Update the recent projects menu"""
        # This would need to be called after menu is created
        # Placeholder implementation
        pass
    
    def update_recent_templates_menu(self):
        """Update the recent templates menu"""
        # This would need to be called after menu is created
        # Placeholder implementation  
        pass
    
    def add_recent_project(self, project_path):
        """Add a project to recent projects list"""
        # Implementation would go here
        pass
    
    def add_recent_template(self, template_path):
        """Add a template to recent templates list"""
        # Implementation would go here
        pass
    
    def clear_recent_projects(self):
        """Clear all recent projects"""
        clear_recent_projects(self.main_window)
    
    def clear_recent_templates(self):
        """Clear all recent templates"""
        clear_recent_templates(self.main_window) 
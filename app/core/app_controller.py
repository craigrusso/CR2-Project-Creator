#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from typing import Dict, List, Any, Optional, Tuple, Union, Callable
import logging
import os
import threading
from PyQt5.QtCore import QObject, pyqtSignal

from app.core.app_model import AppModel
from app.dialogs.dialog_windows_pyqt import preview_structure, show_batch_create, show_about
from app.utils.utils import open_folder

# Set up logging
logger = logging.getLogger(__name__)

class AppController(QObject):
    """
    Controller class for the application following MVC pattern.
    Responsible for coordinating interactions between model and view.
    """
    
    # Define signals for view updates
    template_updated = pyqtSignal()
    status_update = pyqtSignal(str, str, int)  # message, type, duration
    batch_results_ready = pyqtSignal()
    
    def __init__(self, model: AppModel) -> None:
        """Initialize the application controller with model reference"""
        super().__init__()
        self.model = model
        logger.info("Application controller initialized")
    
    def create_project(self, project_name: str, output_dir: str, template_file: str,
                      structure: Union[Dict, List], settings: Dict[str, Any]) -> Tuple[bool, str]:
        """Create a new project with the given parameters"""
        success, message = self.model.create_project(
            project_name, output_dir, template_file, structure, settings
        )
        
        if success:
            self.status_update.emit(message, "success", 5000)
            # Emit template updated signal to refresh UI
            self.template_updated.emit()
        else:
            self.status_update.emit(message, "error", 5000)
            
        return success, message
    
    def handle_batch_create(self, view, base_dir: str, template_file: str, structure: Union[Dict, List]) -> None:
        """Handle batch project creation dialog"""
        # Use PyQt dialog to get batch project parameters
        self.model.batch_results = show_batch_create(view, base_dir, template_file, structure)
        
        # Signal that batch results are ready
        if self.model.batch_results is not None:
            self.batch_results_ready.emit()
    
    def get_current_batch_results(self) -> Dict[str, Any]:
        """Get the current batch creation results"""
        return self.model.batch_results
    
    def clear_batch_results(self) -> None:
        """Clear the batch creation results"""
        self.model.batch_results = None
    
    def preview_structure(self, view, structure: Union[Dict, List]) -> None:
        """Preview the directory structure"""
        preview_structure(view, structure)
    
    def show_about_dialog(self, view) -> None:
        """Show the about dialog"""
        show_about(view)
    
    def open_folder(self, path: str) -> bool:
        """Open a folder in the file explorer"""
        try:
            open_folder(path)
            return True
        except Exception as e:
            logger.error(f"Error opening folder {path}: {e}")
            self.status_update.emit(f"Error opening folder: {str(e)}", "error", 5000)
            return False
    
    def open_recent_project(self, project_path: str) -> bool:
        """Open a recent project"""
        if not project_path or not os.path.exists(project_path):
            self.status_update.emit(f"Project folder not found: {project_path}", "error", 5000)
            # Remove from recent projects if it doesn't exist
            if project_path in self.model.recent_projects:
                self.model.recent_projects.remove(project_path)
                self.model.save_recent_projects()
            return False
        
        return self.open_folder(project_path)
    
    def use_recent_template(self, template_name: str) -> bool:
        """Use a recent template"""
        # Find the template in the template manager
        template = self.model.template_manager.get_template_by_name(template_name)
        if not template:
            self.status_update.emit(f"Template not found: {template_name}", "error", 5000)
            # Remove from recent templates if it doesn't exist
            self.model.remove_recent_template(template_name)
            return False
        
        # Add to recent templates (moves to top of list)
        self.model.add_recent_template(template_name)
        self.template_updated.emit()
        return True
    
    def get_template_by_name(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get a template by name"""
        try:
            if not template_name:
                logger.warning("Empty template name provided to get_template_by_name")
                return None
                
            return self.model.template_manager.get_template_by_name(template_name)
        except Exception as e:
            logger.error(f"Error getting template {template_name}: {e}")
            self.status_update.emit(f"Error loading template: {str(e)}", "error", 5000)
            return None
    
    def filter_templates(self, search_term: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filter templates by search term and category"""
        return self.model.template_manager.filter_templates(search_term, category)
    
    def get_structure(self, structure_name: str) -> Union[Dict, List]:
        """Get a directory structure by name"""
        return self.model.template_manager.get_structure(structure_name)
    
    def get_categories(self) -> List[str]:
        """Get all template categories"""
        return self.model.template_manager.get_categories()
    
    def clear_recent_templates(self) -> None:
        """Clear the recent templates list"""
        self.model.clear_recent_templates()
        self.template_updated.emit()
        self.status_update.emit("Recent templates cleared", "info", 3000)
    
    def clear_recent_projects(self) -> None:
        """Clear the recent projects list"""
        self.model.clear_recent_projects()
        self.status_update.emit("Recent projects cleared", "info", 3000)
    
    def add_to_favorites(self, template_name: str) -> bool:
        """Add a template to favorites"""
        result = self.model.template_manager.add_to_folder("Favorites", template_name)
        if result:
            self.template_updated.emit()
            self.status_update.emit(f"Added '{template_name}' to Favorites", "info", 3000)
        return result
    
    def remove_from_favorites(self, template_name: str) -> bool:
        """Remove a template from favorites"""
        result = self.model.template_manager.remove_from_folder("Favorites", template_name)
        if result:
            self.template_updated.emit()
            self.status_update.emit(f"Removed '{template_name}' from Favorites", "info", 3000)
        return result
    
    def run_async(self, func: Callable, callback: Optional[Callable] = None, *args, **kwargs) -> None:
        """Run a function asynchronously in a separate thread"""
        def _async_wrapper():
            try:
                result = func(*args, **kwargs)
                if callback:
                    callback(result)
            except Exception as e:
                logger.exception(f"Error in async operation: {str(e)}")
                self.status_update.emit(f"Operation failed: {str(e)}", "error", 5000)
        
        thread = threading.Thread(target=_async_wrapper)
        thread.daemon = True
        thread.start() 
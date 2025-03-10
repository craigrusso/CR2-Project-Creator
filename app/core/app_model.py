#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from typing import Dict, List, Any, Optional, Tuple, Union
import logging
import os
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder
from app.utils.utils import load_config, save_config, load_recent_projects, save_recent_projects, load_recent_templates, save_recent_templates

# Set up logging
logger = logging.getLogger(__name__)

class AppModel:
    """
    Model class for the application following MVC pattern.
    Responsible for handling business logic and data management.
    """
    
    def __init__(self) -> None:
        """Initialize the application model with all data dependencies"""
        # Set up logging
        self._configure_logging()
        
        # Initialize core components
        self.template_manager = TemplateManager()
        self.project_builder = ProjectBuilder(self.template_manager)
        
        # Load saved data
        self.config = load_config()
        self.recent_projects = load_recent_projects()
        self.recent_templates = load_recent_templates()
        
        # Batch project creation results
        self.batch_results = None
        
        logger.info("Application model initialized")
    
    def _configure_logging(self) -> None:
        """Set up application logging"""
        log_dir = os.path.join(os.path.expanduser("~"), ".cr2projectcreator", "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, "app.log")
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def save_config(self) -> bool:
        """Save application configuration"""
        try:
            save_config(self.config)
            logger.info("Configuration saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def save_recent_projects(self) -> bool:
        """Save recent projects list"""
        try:
            save_recent_projects(self.recent_projects)
            logger.info("Recent projects saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving recent projects: {e}")
            return False
    
    def save_recent_templates(self) -> bool:
        """Save recent templates list"""
        try:
            save_recent_templates(self.recent_templates)
            logger.info("Recent templates saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving recent templates: {e}")
            return False
    
    def add_recent_project(self, project_path: str) -> bool:
        """Add a project to the recent projects list"""
        if not project_path:
            logger.warning("Cannot add empty project path to recent projects")
            return False
            
        # Remove if already exists (to move to top)
        if project_path in self.recent_projects:
            self.recent_projects.remove(project_path)
            
        # Add to beginning of list
        self.recent_projects.insert(0, project_path)
        
        # Limit to 10 recent projects
        self.recent_projects = self.recent_projects[:10]
        
        # Save updated list
        return self.save_recent_projects()
    
    def add_recent_template(self, template_name: str) -> bool:
        """Add a template to the recent templates list"""
        if not template_name:
            logger.warning("Cannot add empty template name to recent templates")
            return False
            
        # Remove if already exists (to move to top)
        if template_name in self.recent_templates:
            self.recent_templates.remove(template_name)
            
        # Add to beginning of list
        self.recent_templates.insert(0, template_name)
        
        # Limit to configured max recent templates
        max_recent = self.config.get("max_recent_templates", 5)
        self.recent_templates = self.recent_templates[:max_recent]
        
        # Save updated list
        self.save_recent_templates()
        
        # Also add to Recent folder
        self.template_manager.add_to_folder("Recent", template_name)
        
        return True
    
    def remove_recent_template(self, template_name: str) -> bool:
        """Remove a template from the recent templates list"""
        if template_name in self.recent_templates:
            self.recent_templates.remove(template_name)
            self.save_recent_templates()
            
            # Also remove from Recent folder
            self.template_manager.remove_from_folder("Recent", template_name)
            return True
        return False
    
    def clear_recent_templates(self) -> bool:
        """Clear the recent templates list"""
        self.recent_templates = []
        self.save_recent_templates()
        
        # Also clear Recent folder
        if "Recent" in self.template_manager.folders:
            self.template_manager.folders["Recent"] = []
            self.template_manager.save_folders()
        
        return True
    
    def clear_recent_projects(self) -> bool:
        """Clear the recent projects list"""
        self.recent_projects = []
        return self.save_recent_projects()
    
    def create_project(self, project_name: str, output_dir: str, template_file: str, 
                      structure: Union[Dict, List], settings: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a new project using the provided parameters
        
        Args:
            project_name: Name of the project
            output_dir: Output directory for the project
            template_file: Path to the template file
            structure: Directory structure for the project
            settings: Additional project settings
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Log project creation
            logger.info(f"Creating project: {project_name} in {output_dir}")
            
            # Use project builder to create the project
            result = self.project_builder.create_project(
                project_name,
                output_dir,
                template_file,
                structure,
                settings
            )
            
            if result:
                # Add to recent projects
                project_path = os.path.join(output_dir, project_name)
                self.add_recent_project(project_path)
                
                # Add template to recent templates if applicable
                if settings.get("template_name"):
                    self.add_recent_template(settings["template_name"])
                
                logger.info(f"Project created successfully: {project_path}")
                return True, f"Project '{project_name}' created successfully"
            else:
                logger.error(f"Failed to create project: {project_name}")
                return False, f"Failed to create project: {project_name}"
                
        except Exception as e:
            error_msg = f"Error creating project: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg 
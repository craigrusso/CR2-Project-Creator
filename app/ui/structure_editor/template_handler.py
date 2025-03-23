#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template Handler Module for Structure Editor
Handles template loading, saving, and management
"""

import os
import json
from PyQt5.QtWidgets import QMessageBox

from .utils import is_built_in_structure

class TemplateHandler:
    """
    Handles template operations for the structure editor
    
    This class manages loading, saving, and categorizing templates,
    interfacing with the application's template management system.
    """
    
    def __init__(self, editor):
        """
        Initialize the template handler
        
        Args:
            editor: Reference to the parent editor
        """
        self.editor = editor
        
        # Get references to important components
        self.template_manager = self._get_template_manager()
        self.ui_builder = getattr(editor, 'ui_builder', None)
        
        # Template properties
        self.structure_name = getattr(editor, 'structure_name', None)
        self.original_template_name = getattr(editor, 'original_template_name', None)
        self.project_type = getattr(editor, 'project_type', None)
        
    def _get_template_manager(self):
        """
        Get the template manager instance
        
        Returns:
            object: The template manager instance
        """
        # Try to get from editor
        if hasattr(self.editor, 'template_manager') and self.editor.template_manager:
            return self.editor.template_manager
            
        # Try to get from parent
        if hasattr(self.editor, 'parent') and hasattr(self.editor.parent, 'template_manager'):
            return self.editor.parent.template_manager
            
        # Try to get from app
        if hasattr(self.editor, 'app') and hasattr(self.editor.app, 'template_manager'):
            return self.editor.app.template_manager
            
        return None
    
    def load_template(self, template_name):
        """
        Load a template by name
        
        Args:
            template_name: Name of the template to load
            
        Returns:
            dict: The loaded template data or None if not found
        """
        if not self.template_manager or not template_name:
            return None
            
        # Try to get the structure from the template manager
        if hasattr(self.template_manager, 'get_structure'):
            return self.template_manager.get_structure(template_name)
            
        return None
    
    def save_structure(self, structure_name=None):
        """
        Save the current structure
        
        Args:
            structure_name: Optional name for the structure.
                           If not provided, gets from UI.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        # Use provided structure name or get from UI
        if not structure_name:
            if self.ui_builder and hasattr(self.ui_builder, 'get_ui_values'):
                template_info = self.ui_builder.get_ui_values()
                structure_name = template_info.get('template_name')
            else:
                structure_name = self.structure_name
        
        # If still no name, error
        if not structure_name:
            print("ERROR: Cannot save structure without a name")
            return False
        
        # Get the structure from the tree
        if hasattr(self.editor, 'structure_converter') and hasattr(self.editor.structure_converter, 'create_structure_from_tree'):
            structure = self.editor.structure_converter.create_structure_from_tree()
        else:
            print("ERROR: Cannot convert tree to structure (converter not available)")
            return False
        
        # If we got here and have a structure, save it
        if structure:
            # Check if we're renaming
            is_rename = (self.original_template_name and 
                         structure_name != self.original_template_name)
                         
            try:
                # Save to template manager if available
                if self.template_manager:
                    success = self.template_manager.save_structure(structure_name, structure)
                    
                    if success:
                        print(f"Successfully saved structure '{structure_name}'")
                        
                        # If this was a rename, delete the old structure
                        if is_rename and hasattr(self.template_manager, 'delete_structure'):
                            self.template_manager.delete_structure(self.original_template_name)
                            print(f"Renamed structure from '{self.original_template_name}' to '{structure_name}'")
                            
                        # Update the current structure name
                        self.structure_name = structure_name
                        
                        # Set the project type if available
                        self._set_structure_project_type(structure_name)
                        
                        return True
                    else:
                        print(f"ERROR: Failed to save structure '{structure_name}'")
                else:
                    # Direct file saving fallback if no template manager
                    success = self._save_to_file(structure_name, structure)
                    
                    if success:
                        # Update the current structure name
                        self.structure_name = structure_name
                        return True
                        
                return False
            except Exception as e:
                import traceback
                print(f"ERROR saving structure: {e}")
                traceback.print_exc()
                return False
        else:
            print("ERROR: No structure data to save")
            return False
    
    def _save_to_file(self, template_name, structure):
        """
        Save a structure to a file
        
        Args:
            template_name: Name of the template
            structure: Structure data to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        # Generate a filename
        template_filename = template_name.replace(' ', '_') + '.json'
        
        # Get templates directory
        templates_dir = os.path.join(os.path.dirname(__file__), '../../../templates')
        if not os.path.exists(templates_dir):
            templates_dir = os.path.expanduser('~')
            
        # Full path
        file_path = os.path.join(templates_dir, template_filename)
        
        try:
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(structure, f, indent=2)
                
            QMessageBox.information(
                self.editor,
                "Template Saved",
                f"Template saved to {file_path}"
            )
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self.editor,
                "Save Error",
                f"Failed to save template: {str(e)}"
            )
            return False
    
    def get_template_info(self):
        """
        Get template information from UI
        
        Returns:
            dict: Dictionary containing template information
        """
        # Try to get from UI builder
        if self.ui_builder and hasattr(self.ui_builder, 'get_ui_values'):
            return self.ui_builder.get_ui_values()
            
        # Fallback to basic information
        return {
            'template_name': self.structure_name or '',
            'template_category': 'Custom',
            'template_info': ''
        }
    
    def set_template_info(self, template_info):
        """
        Set template information in UI
        
        Args:
            template_info: Dictionary containing template information
        """
        # Try to set in UI builder
        if self.ui_builder and hasattr(self.ui_builder, 'set_ui_values'):
            self.ui_builder.set_ui_values(template_info)
            
    def get_template_categories(self):
        """
        Get available template categories
        
        Returns:
            list: List of available categories
        """
        # Try to get from template manager
        if self.template_manager and hasattr(self.template_manager, 'get_categories'):
            return self.template_manager.get_categories()
            
        # Default categories
        return ["Custom", "Audio", "Video", "Photography", "Graphics", "Writing", "Development", "Other"]
        
    def get_template_by_category(self, category):
        """
        Get templates by category
        
        Args:
            category: Category to filter by
            
        Returns:
            list: List of template names in the category
        """
        # Try to get from template manager
        if self.template_manager and hasattr(self.template_manager, 'get_templates_by_category'):
            return self.template_manager.get_templates_by_category(category)
            
        return []
    
    def duplicate_template(self, template_name, new_name):
        """
        Duplicate a template
        
        Args:
            template_name: Name of the template to duplicate
            new_name: New name for the duplicated template
            
        Returns:
            bool: True if duplicated successfully, False otherwise
        """
        # Load the original template
        structure = self.load_template(template_name)
        if not structure:
            return False
            
        # Save with the new name
        if self.template_manager and hasattr(self.template_manager, 'save_structure'):
            return self.template_manager.save_structure(new_name, structure)
            
        return False
    
    def _set_structure_project_type(self, structure_name):
        """
        Set project type for the structure if available
        
        Args:
            structure_name: Name of the structure
            
        Returns:
            bool: True if set successfully, False otherwise
        """
        if not self.project_type or not self.template_manager:
            return False
        
        try:
            # Try to set project type directly
            if hasattr(self.template_manager, 'set_structure_project_type'):
                self.template_manager.set_structure_project_type(
                    structure_name, 
                    self.project_type
                )
                return True
            
            # Alternative: set category based on project type
            if hasattr(self.template_manager, 'set_structure_category'):
                # Determine category from project type
                category = "Custom"
                if self.project_type.lower() in ["audio", "video", "photo", "graphics", "writing", "development"]:
                    category = self.project_type.capitalize()
                elif self.project_type.lower() == "photography":
                    category = "Photography"
                
                self.template_manager.set_structure_category(structure_name, category)
                return True
            
            return False
        except Exception as e:
            print(f"ERROR setting project type: {e}")
            return False 
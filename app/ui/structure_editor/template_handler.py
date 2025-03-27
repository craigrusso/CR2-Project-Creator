#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template Handler Module for Structure Editor
Handles template loading, saving, and management
"""

import os
import json
from PyQt5.QtWidgets import QMessageBox
import datetime

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
            
        # Try to get the template from the template manager
        template_data = None
        if hasattr(self.template_manager, 'get_template_by_name'):
            template_data = self.template_manager.get_template_by_name(template_name)
            if template_data:
                print(f"Loaded template '{template_name}' with category '{template_data.get('category', template_data.get('type', 'Custom'))}'")
                return template_data
                
        # If not found or no get_template_by_name, try get_structure
        if hasattr(self.template_manager, 'get_structure'):
            structure = self.template_manager.get_structure(template_name)
            if structure:
                # For backward compatibility, if structure is just an array, 
                # wrap it in a dictionary with metadata
                if isinstance(structure, list):
                    category = 'Custom'  # Default category
                    # Try to get category from project type manager
                    if hasattr(self.template_manager, 'project_type_manager'):
                        types = self.template_manager.project_type_manager.get_all_project_types()
                        if template_name in types:
                            category = template_name
                            
                    structure = {
                        'name': template_name,
                        'structure': structure,
                        'category': category
                    }
                    print(f"Created metadata wrapper for structure '{template_name}' with category '{category}'")
                
                return structure
                
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
        template_info = {}
        if self.ui_builder and hasattr(self.ui_builder, 'get_ui_values'):
            template_info = self.ui_builder.get_ui_values()
            structure_name = template_info.get('template_name') if not structure_name else structure_name
        else:
            structure_name = structure_name or self.structure_name
        
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
            
            # Get category from UI or fallback to "Custom"
            category = template_info.get('template_category', template_info.get('category', 'Custom'))
            print(f"Saving template '{structure_name}' with category '{category}'")
                         
            try:
                # Save to template manager if available
                if self.template_manager:
                    # First, process any files that need to be cached
                    self._process_files_for_caching(structure_name, structure)
                    
                    # Add template metadata
                    if isinstance(structure, list):
                        # Convert to dictionary with metadata
                        structure_dict = {
                            'name': structure_name,
                            'structure': structure,
                            'category': category,
                            'description': template_info.get('template_info', ''),
                            'modified': datetime.datetime.now().timestamp()
                        }
                        # If we have an existing template, preserve its metadata
                        if self.original_template_name:
                            existing_template = self.get_template(self.original_template_name)
                            if existing_template and isinstance(existing_template, dict):
                                # Preserve created timestamp and other metadata
                                for field in ['created', 'files']:
                                    if field in existing_template:
                                        structure_dict[field] = existing_template[field]
                        structure = structure_dict
                    elif isinstance(structure, dict):
                        # Update metadata in dictionary
                        structure['name'] = structure_name
                        structure['category'] = category
                        structure['modified'] = datetime.datetime.now().timestamp()
                        if 'template_info' in template_info:
                            structure['description'] = template_info.get('template_info', '')
                        elif 'description' in template_info:
                            structure['description'] = template_info.get('description', '')
                    
                    # Now save the structure with the updated file paths
                    success = self.template_manager.save_structure(structure_name, structure)
                    
                    if success:
                        print(f"Successfully saved structure '{structure_name}' with category '{category}'")
                        
                        # If this was a rename, delete the old structure
                        if is_rename and hasattr(self.template_manager, 'delete_structure'):
                            self.template_manager.delete_structure(self.original_template_name)
                            print(f"Renamed structure from '{self.original_template_name}' to '{structure_name}'")
                            
                        # Update the current structure name
                        self.structure_name = structure_name
                        
                        # Set the project type if available
                        if category and category != 'Custom':
                            self.project_type = category
                            self._set_structure_project_type(structure_name)
                        
                        return True
                    else:
                        print(f"ERROR: Failed to save structure '{structure_name}'")
                else:
                    # Direct file saving fallback if no template manager
                    # Add metadata to structure before saving
                    if isinstance(structure, list):
                        structure = {
                            'name': structure_name,
                            'structure': structure,
                            'category': category, 
                            'description': template_info.get('template_info', '')
                        }
                    
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
        if hasattr(self, 'app') and hasattr(self.app, 'template_manager'):
            categories = self.app.template_manager.get_categories()
            print(f"template_handler.get_template_categories: Retrieved {len(categories)} categories from template_manager: {categories}")
            return categories
        
        # Fallback to default categories
        fallback_categories = ["Custom", "Audio", "Video", "Photography", "Graphics", "Writing", "Development", "Other"]
        print(f"template_handler.get_template_categories: Using fallback categories: {fallback_categories}")
        return fallback_categories
        
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
    
    def _process_files_for_caching(self, template_name, structure):
        """
        Process files in the structure to ensure they are cached
        
        Args:
            template_name: Name of the template
            structure: Structure data to update with cache paths
            
        Returns:
            None (modifies structure in place)
        """
        print(f"🔄 FILE_CACHING: Processing files for '{template_name}'")
        
        # Check if files_to_cache is available in editor
        if hasattr(self.editor, 'files_to_cache'):
            print(f"🔄 FILE_CACHING: Editor has {len(self.editor.files_to_cache)} files in files_to_cache")
            for rel_path, file_data in self.editor.files_to_cache.items():
                print(f"🔄 FILE_CACHING: files_to_cache entry: {rel_path} -> {file_data.get('original_path')}")
        else:
            print("🔄 FILE_CACHING: Editor does not have files_to_cache attribute")
        
        try:
            # Import cache manager if needed
            from app.utils.file_cache_manager import FileCacheManager
            from app.utils.cache_preferences import CachePreferences
            
            # Check if caching is enabled
            cache_prefs = CachePreferences()
            if not cache_prefs.should_cache_files():
                print("🔄 FILE_CACHING: File caching is disabled in preferences")
                return
            
            # Initialize cache manager
            cache_manager = FileCacheManager(cache_prefs.get_cache_location())
            print(f"🔄 FILE_CACHING: Using cache location: {cache_prefs.get_cache_location()}")
            
            # Process the structure recursively
            self._process_structure_for_caching(structure, template_name, cache_manager)
            
        except ImportError:
            print("🔄 FILE_CACHING: Cache manager not available, skipping file caching")
        except Exception as e:
            import traceback
            print(f"🔄 FILE_CACHING ERROR: {e}")
            traceback.print_exc()
    
    def _process_structure_for_caching(self, structure_item, template_name, cache_manager, path=""):
        """
        Recursively process a structure item to cache files
        
        Args:
            structure_item: Structure item to process (can be dict, list, or string)
            template_name: Name of the template
            cache_manager: Cache manager instance
            path: Current path in the structure (for relative paths)
            
        Returns:
            None (modifies structure_item in place)
        """
        # Check structure type
        if isinstance(structure_item, list):
            print(f"🔄 STRUCTURE_CACHING: Processing list with {len(structure_item)} items at path '{path}'")
            
            # Look for string items (directly added files)
            string_items = [item for item in structure_item if isinstance(item, str)]
            if string_items:
                print(f"🔄 STRUCTURE_CACHING: Found {len(string_items)} string items at path '{path}': {string_items}")
                
                # Check if we have files_to_cache to resolve these string items
                if hasattr(self.editor, 'files_to_cache'):
                    for string_item in string_items:
                        # Try to find this file in files_to_cache
                        found = False
                        for rel_path, file_data in self.editor.files_to_cache.items():
                            if os.path.basename(rel_path) == string_item or os.path.basename(file_data.get('original_path', '')) == string_item:
                                print(f"🔄 STRUCTURE_CACHING: Found matching file for '{string_item}' in files_to_cache: {file_data}")
                                found = True
                                
                                # We found a match, now we need to create a proper file entry
                                original_path = file_data.get('original_path')
                                if original_path and os.path.exists(original_path):
                                    print(f"🔄 STRUCTURE_CACHING: Caching file '{string_item}' from '{original_path}'")
                                    
                                    # Cache the file
                                    cache_info = cache_manager.cache_file(
                                        original_path,
                                        template_name,
                                        os.path.join(path, string_item)
                                    )
                                    
                                    if cache_info:
                                        print(f"🔄 STRUCTURE_CACHING: Successfully cached: {cache_info}")
                                        
                                        # Replace the string item with a proper file object
                                        idx = structure_item.index(string_item)
                                        structure_item[idx] = {
                                            'type': 'file',
                                            'name': string_item,
                                            'original_path': original_path,
                                            'cache_path': cache_info['cache_path'],
                                            'file_hash': cache_info.get('file_hash', '')
                                        }
                                        print(f"🔄 STRUCTURE_CACHING: Replaced string item with file object at index {idx}")
                                break
                        
                        if not found:
                            print(f"🔄 STRUCTURE_CACHING: Could not find original path for '{string_item}' in files_to_cache")
            
            # Process all items in the list
            for item in structure_item:
                self._process_structure_for_caching(item, template_name, cache_manager, path)
            
        # Check if this is a dictionary (folder or normalized item)
        elif isinstance(structure_item, dict):
            # Check if this is a normalized format item
            if 'type' in structure_item and 'name' in structure_item:
                item_type = structure_item.get('type')
                item_name = structure_item.get('name')
                
                print(f"🔄 STRUCTURE_CACHING: Processing {item_type} item '{item_name}' at path '{path}'")
                
                # Handle folder
                if item_type == 'folder' or item_type == 'directory':
                    # Process children recursively with updated path
                    if 'children' in structure_item and isinstance(structure_item['children'], list):
                        new_path = os.path.join(path, item_name)
                        self._process_structure_for_caching(structure_item['children'], template_name, cache_manager, new_path)
                
                # Handle file
                elif item_type == 'file':
                    # Check if we have an original path and need to cache
                    if 'original_path' in structure_item and os.path.exists(structure_item['original_path']):
                        # Determine the relative path in template
                        relative_path = os.path.join(path, item_name)
                        
                        print(f"🔄 STRUCTURE_CACHING: Caching file '{item_name}' from '{structure_item['original_path']}'")
                        
                        # Cache the file
                        file_info = cache_manager.cache_file(
                            structure_item['original_path'], 
                            template_name,
                            relative_path
                        )
                        
                        if file_info:
                            # Update structure with cache info
                            structure_item['cache_path'] = file_info['cache_path']
                            structure_item['file_hash'] = file_info['file_hash']
                            print(f"🔄 STRUCTURE_CACHING: Cached file: {item_name} -> {file_info['cache_path']}")
                    else:
                        print(f"🔄 STRUCTURE_CACHING: File '{item_name}' has no original_path or path doesn't exist")
            
            # Check if it's a traditional folder structure {folder_name: [children]}
            else:
                for key, value in structure_item.items():
                    print(f"🔄 STRUCTURE_CACHING: Processing folder '{key}' with {len(value) if isinstance(value, list) else 'non-list'} children")
                    # The key is the folder name and value should be a list of children
                    if isinstance(value, list):
                        new_path = os.path.join(path, key)
                        self._process_structure_for_caching(value, template_name, cache_manager, new_path)
        elif isinstance(structure_item, str):
            print(f"🔄 STRUCTURE_CACHING: Found direct string item '{structure_item}' at path '{path}'")
            
            # Try to find this string in files_to_cache
            if hasattr(self.editor, 'files_to_cache'):
                for rel_path, file_data in self.editor.files_to_cache.items():
                    if (os.path.basename(rel_path) == structure_item or 
                        os.path.basename(file_data.get('original_path', '')) == structure_item):
                        print(f"🔄 STRUCTURE_CACHING: Found matching file for '{structure_item}' in files_to_cache: {file_data}")
                        
                        # We found a match, cache the file
                        original_path = file_data.get('original_path')
                        if original_path and os.path.exists(original_path):
                            cache_info = cache_manager.cache_file(
                                original_path,
                                template_name,
                                os.path.join(path, structure_item)
                            )
                            if cache_info:
                                print(f"🔄 STRUCTURE_CACHING: Cached direct string file: {structure_item} -> {cache_info['cache_path']}")
                        break 
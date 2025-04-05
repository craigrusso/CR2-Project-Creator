#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Project Builder Module

This module handles creating projects from templates or structures.
"""

import os
import threading
import datetime
import shutil
import sys
import json
import platform
import re  # Add import for regex
from pathlib import Path

# Using PyQt for the UI framework
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt5.QtCore import Qt, QTimer
UI_FRAMEWORK = 'pyqt'

# Import binary file handler
try:
    from app.utils.binary_file_handler import BinaryFileHandler
except ImportError:
    # Fallback implementation if not available
    class BinaryFileHandler:
        @staticmethod
        def decode_binary_file(encoded_data, output_path):
            print(f"WARNING: BinaryFileHandler not available, can't decode file to {output_path}")
            return False

# Define PyQt version of progress window
class BatchProgressWindowPyQt(QDialog):
    """PyQt version of the batch progress window"""
    
    def __init__(self, total_projects):
        super().__init__()
        self.total_projects = total_projects
        self.results = None
        
        # Set window properties
        self.setWindowTitle("Creating Projects")
        self.setFixedSize(400, 150)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Status label
        self.status_label = QLabel("Preparing...")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(total_projects)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Spacer
        layout.addSpacing(10)
        
        # Cancel button (disabled for now since we don't have cancellation logic)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        layout.addWidget(self.cancel_button, alignment=Qt.AlignRight)
    
    def update_status(self, text):
        """Update the status text"""
        self.status_label.setText(text)
    
    def update_progress(self, current):
        """Update the progress bar"""
        self.progress_bar.setValue(current)
    
    def set_results(self, results):
        """Store the results for potential display"""
        self.results = results
        # Change status to complete
        self.status_label.setText(f"Completed: {len(results)} projects processed")
        self.progress_bar.setValue(self.total_projects)

# Set the BatchProgressWindow class to use PyQt version
BatchProgressWindow = BatchProgressWindowPyQt

from app.utils.utils import add_to_recent_projects, create_readme_file

class ProjectBuilder:
    """
    Creates project directories and handles batch project creation
    """
    def __init__(self, template_manager):
        self.template_manager = template_manager
        self.project_queue = []
        self.is_building = False
    
    def _handle_dollar_placeholder(self, input_string, project_name):
        """
        Specialized handling for dollar sign placeholders (${PROJECT_NAME})
        
        Args:
            input_string: String that may contain the ${PROJECT_NAME} placeholder
            project_name: Project name to replace the placeholder with
            
        Returns:
            String with placeholder replaced
        """
        # Define all placeholder formats we need to handle
        placeholder_dollar = "${PROJECT_NAME}"
        
        # Debug logging
        print(f"🔍 DOLLAR HANDLING DEBUG: Processing string: '{input_string}'")
        print(f"🔍 DOLLAR HANDLING DEBUG: String length: {len(input_string)}")
        print(f"🔍 DOLLAR HANDLING DEBUG: String as bytes: {input_string.encode('utf-8')}")
        print(f"🔍 DOLLAR HANDLING DEBUG: Project name: '{project_name}'")
        
        # Initialize result with input string
        result = input_string
        
        # Case 1: Input contains the full placeholder "${PROJECT_NAME}"
        if placeholder_dollar in input_string:
            # Create a new string with the placeholder replaced
            # We need to be careful with this replacement to ensure no $ artifacts remain
            parts = input_string.split(placeholder_dollar)
            result = project_name.join(parts)
            print(f"🔍 DOLLAR HANDLING DEBUG: Full placeholder replacement: '{result}'")
        
        # Case 2: Input starts with $ but doesn't contain the full placeholder
        # This likely means the display is showing $ but internally it's not matching correctly
        elif input_string.startswith("$"):
            # Extract the part after $ 
            remaining = input_string[1:]
            
            # If it looks like it might be a malformed PROJECT_NAME placeholder
            if remaining.startswith("{PROJECT_NAME}") or remaining.startswith("PROJECT_NAME"):
                # In these cases, we want to just use the project name with any suffix
                name_index = remaining.find("PROJECT_NAME")
                if name_index >= 0:
                    suffix_index = name_index + len("PROJECT_NAME")
                    suffix = remaining[suffix_index:] if suffix_index < len(remaining) else ""
                    result = f"{project_name}{suffix}"
                    print(f"🔍 DOLLAR HANDLING DEBUG: Malformed placeholder handling: '{result}'")
                    
            # If it's another kind of file that just happens to start with $
            elif "." in remaining:
                # It has an extension - preserve the extension
                parts = remaining.split(".")
                ext = "." + ".".join(parts[1:])  # Handle multiple dots in filename
                result = f"{project_name}{ext}"
                print(f"🔍 DOLLAR HANDLING DEBUG: $ prefix with extension: '{result}'")
                
            # Any other $ prefix case
            else:
                # Just replace the $ with the project name
                result = f"{project_name}{remaining}"
                print(f"🔍 DOLLAR HANDLING DEBUG: Simple $ prefix handling: '{result}'")
                
        # Log the final result for debugging
        print(f"🔍 DOLLAR HANDLING DEBUG: Final result: '{result}'")
        return result
    
    def _apply_structure_flags_to_files(self, structure_data, files_array):
        """
        Apply rename and project name flags from structure to files array
        
        Args:
            structure_data: Structure data that might contain file flags
            files_array: Array of files to update with flags
            
        Returns:
            list: Updated files array
        """
        if not structure_data or not files_array:
            return files_array
            
        print(f"DEBUG: Applying structure flags to {len(files_array)} files")
        
        # Create lookup dictionary for files by name
        files_by_name = {}
        for file_data in files_array:
            file_name = file_data.get('file_name')
            if file_name:
                files_by_name[file_name] = file_data
                
        # Function to search for files in structure recursively
        def process_structure_items(items, path=""):
            if not items or not isinstance(items, list):
                return
                
            for item in items:
                if not isinstance(item, dict):
                    continue
                    
                if item.get('type') == 'file':
                    file_name = item.get('name')
                    if not file_name:
                        continue
                        
                    # Check if this file is in our files_array
                    if file_name in files_by_name:
                        # Check for rename flags
                        rename_flag = item.get('rename_flag', False)
                        uses_project_name = item.get('uses_project_name', False)
                        
                        if rename_flag or uses_project_name:
                            print(f"DEBUG: Found flag in structure for file '{file_name}': rename_flag={rename_flag}, uses_project_name={uses_project_name}")
                            
                            # Apply flags to the file data
                            file_data = files_by_name[file_name]
                            if rename_flag and not file_data.get('rename_flag'):
                                file_data['rename_flag'] = True
                                print(f"DEBUG: Applied rename_flag to file: {file_name}")
                                
                            if uses_project_name and not file_data.get('uses_project_name'):
                                file_data['uses_project_name'] = True
                                print(f"DEBUG: Applied uses_project_name to file: {file_name}")
                
                # Process children if this is a folder
                if item.get('type') == 'folder' and 'children' in item:
                    new_path = path
                    if item.get('name'):
                        if new_path:
                            new_path += '/'
                        new_path += item.get('name')
                    process_structure_items(item.get('children', []), new_path)
        
        # Process the structure
        if isinstance(structure_data, list):
            process_structure_items(structure_data)
        elif isinstance(structure_data, dict) and 'root' in structure_data:
            process_structure_items(structure_data['root'])
            
        return files_array

    def create_project(self, project_name, output_dir=None, template_file=None, project_type="Standard", 
                   structure_name=None, create_backup=True, use_cached_files=True):
        """Create a new project based on a template.
        
        Args:
            project_name (str): Name of the project
            output_dir (str, optional): Directory where the project should be created
            template_file (str, optional): Path to template file or template data
            project_type (str, optional): Type of project (Standard, etc.)
            structure_name (str, optional): Name of the structure to use
            create_backup (bool, optional): Whether to create a backup if the directory exists
            use_cached_files (bool, optional): Whether to use cached files
            
        Returns:
            tuple: (success, result) where result is either the project path or an error message
                   success is True if project was created, False otherwise
        """
        # Log parameters for debugging
        print(f"DEBUG: Creating project '{project_name}' in directory: '{output_dir}'")
        print(f"DEBUG: Using template: '{template_file}', structure: '{structure_name}'")
        
        # Validate project name
        if not project_name:
            return False, "No project name provided"
            
        # Validate output directory
        if not output_dir:
            return False, "No output directory provided"
            
        # Create output directory if it doesn't exist
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating output directory: {e}")
            return False, f"Failed to create output directory: {e}"
            
        # Create project directory path
        project_dir = os.path.join(output_dir, project_name)
        print(f"DEBUG: Project will be created at: {project_dir}")
        
        # Check if project directory exists
        if os.path.exists(project_dir):
            if create_backup:
                # Create backup of existing directory
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = f"{project_dir}_backup_{timestamp}"
                try:
                    shutil.copytree(project_dir, backup_dir)
                    # Also try to copy hidden files which might be missed by copytree
                    os.system(f'cp -r "{project_dir}/."* "{backup_dir}" 2>/dev/null || true')
                    print(f"Created backup at {backup_dir}")
                except Exception as e:
                    print(f"Failed to create backup: {e}")
                    return False, f"Failed to create backup: {e}"
                    
                # Remove old directory contents but keep the directory
                try:
                    for item in os.listdir(project_dir):
                        item_path = os.path.join(project_dir, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                except Exception as e:
                    print(f"Failed to clean project directory: {e}")
                    return False, f"Failed to clean project directory: {e}"
            else:
                # If we're not creating a backup, fail
                return False, f"Project directory '{project_dir}' already exists"
        else:
            # Create project directory if it doesn't exist
            try:
                os.makedirs(project_dir, exist_ok=True)
            except Exception as e:
                print(f"Error creating project directory: {e}")
                return False, f"Failed to create project directory: {e}"
                
        # Get template data
        template_data = None
        files_to_process = []
        
        # If template_file is a dict, use it directly
        if isinstance(template_file, dict):
            template_data = template_file
            print(f"DEBUG: Direct template_data has structure: {template_data.get('structure', [])}")
        elif template_file and os.path.isfile(template_file):
            # Load template from file
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
            except Exception as e:
                print(f"Error loading template file: {e}")
                return False, f"Failed to load template file: {e}"
                
        # Get structure data
        structure_data = self._get_structure_data(structure_name, template_data.get('name') if template_data else None)
        
        # Check for valid structure - crucial step to validate structure exists
        if not structure_data:
            print(f"DEBUG: No valid structure found for '{structure_name}'")
            # Create the project directory but return a message that there's no structure
            try:
                os.makedirs(project_dir, exist_ok=True)
            except Exception as e:
                print(f"Error creating project directory: {e}")
                return False, f"Failed to create project directory: {e}"
                
            # Instead of failing, return success with no_structure flag
            return True, {"project_dir": project_dir, "no_structure": True}
            
        # Create placeholders for template processing
        placeholders = {
            "PROJECT_NAME": project_name,
            "project_name": project_name.lower(),
            "Project_Name": project_name.title(),
            "ProjectName": self._camel_case(project_name),
            "PROJECT_DIR": project_dir,
            "PROJECT_TYPE": project_type,
            # Additional placeholders can be added here
        }
        
        # Create folders based on structure
        print(f"DEBUG: Creating folders with structure: {structure_data}")
        created_folders_count = self._create_folders_from_structure(project_dir, structure_data)
        print(f"DEBUG: Created {created_folders_count} folders from structure")
        
        # Process files if available in template
        if template_data and 'files' in template_data and template_data['files']:
            files_array = template_data['files']
            
            # Apply structure flags to files if needed
            if structure_data:
                files_array = self._apply_structure_flags_to_files(structure_data, files_array)
                
            # Process files
            files_result = self._process_files_array(
                project_dir, 
                files_array, 
                placeholders,
                use_cached_files,
                template_data.get('name')
            )
            print(f"DEBUG: Processed {len(files_array)} files")
            
            if not files_result[0]:
                # If file processing failed, return warning
                return True, {"project_dir": project_dir, "warning": files_result[1]}
        
        # Return success and project directory
        return True, {"project_dir": project_dir}
        
    def _get_structure_data(self, structure_name=None, template_name=None):
        """
        Get structure data for creating project folders
        
        Args:
            structure_name (str, optional): Name of structure to use
            template_name (str, optional): Name of template for finding matching structure
            
        Returns:
            dict/list: The structure data if found, None otherwise
        """
        print(f"DEBUG: get_structure called with structure_name='{structure_name}'")
        
        # If a template name is provided but no structure name, try to construct the structure name
        if template_name and not structure_name:
            structure_name = f"Template_{template_name}"
            print(f"DEBUG: Using template name to create structure name: {structure_name}")
        
        # Try different variations of the structure name
        variations = []
        if structure_name:
            variations.append(structure_name)
            # Try with and without "Template_" prefix
            if structure_name.startswith("Template_"):
                variations.append(structure_name[9:])  # Remove "Template_"
            else:
                variations.append(f"Template_{structure_name}")
                variations.append(f"Template {structure_name}")
                
        print(f"DEBUG: Trying structure names: {variations}")
        
        # Process the structure
        structure_data = None
        
        # Check if we already have the template loaded with embedded structure
        if hasattr(self, 'template_manager') and template_name:
            try:
                template_data = self.template_manager.get_template_by_name(template_name)
                if template_data and 'structure' in template_data and template_data['structure']:
                    print(f"DEBUG: Found structure embedded in template '{template_name}'")
                    # Validate the embedded structure first
                    if self._ensure_valid_structure(template_data['structure']):
                        return template_data['structure']
            except Exception as e:
                print(f"ERROR: Failed to extract structure from template: {e}")
        
        # First check if we have custom structures directory
        config_manager = None
        if hasattr(self, 'template_manager') and hasattr(self.template_manager, 'config_manager'):
            config_manager = self.template_manager.config_manager
        else:
            print("WARNING: ProjectBuilder cannot access ConfigManager via template_manager.")
        
        structures_dir = config_manager.get_structures_path() if config_manager else "~/.echelon/structures"
        if os.path.exists(structures_dir):
            for variation in variations:
                structure_path = os.path.join(structures_dir, f"{variation}.json")
                if os.path.exists(structure_path):
                    print(f"DEBUG: Found custom structure on disk: {variation}")
                    try:
                        with open(structure_path, 'r', encoding='utf-8') as f:
                            structure_data = json.load(f)
                            
                            # If structure is in 'directories' key, extract it
                            if isinstance(structure_data, dict) and 'directories' in structure_data:
                                structure_data = structure_data['directories']
                            
                            # Validate structure
                            if self._ensure_valid_structure(structure_data):
                                return structure_data
                            else:
                                print(f"DEBUG: Structure from file {variation} is not valid")
                    except Exception as e:
                        print(f"ERROR: Failed to load structure file {structure_path}: {e}")
                        
        # If we reach here, no structure was found or loaded successfully
        # Check if template name was provided, try to get default structure
        if not structure_data:
            default_structure = self._get_default_structure()
            if default_structure:
                print(f"DEBUG: Using default structure")
                return default_structure
        
        # No valid structure found
        print(f"DEBUG: No valid structure found, skipping folder creation")
        return None
    
    def _ensure_valid_structure(self, structure_data):
        """
        Ensure that a structure is valid and can be used for folder creation.
        
        Args:
            structure_data: The structure data to validate
            
        Returns:
            bool: True if the structure is valid, False otherwise
        """
        if not structure_data:
            print("DEBUG: Structure data is empty or None")
            return False
            
        # Check for dict format with folders key
        if isinstance(structure_data, dict):
            if 'folders' in structure_data and structure_data['folders']:
                # Old format with folders key
                print("DEBUG: Structure is valid (dict with folders key)")
                return True
            elif any(isinstance(value, dict) for value in structure_data.values()):
                # Dict format with folder objects as values
                print("DEBUG: Structure is valid (dict with folder objects)")
                return True
            # Check for 'directories' key used in template editor
            elif 'directories' in structure_data and structure_data['directories']:
                print("DEBUG: Structure is valid (dict with directories key)")
                return True
                
        # Check for list format with folder items
        elif isinstance(structure_data, list) and structure_data:
            # Check if any item has a type of 'folder'
            has_folders = any(
                isinstance(item, dict) and item.get('type') == 'folder' for item in structure_data 
            )
            
            # Check for folder dictionaries in the list (common format)
            has_folder_dicts = any(
                isinstance(item, dict) and len(item) == 1 and 
                isinstance(list(item.values())[0], list)
                for item in structure_data
            )
            
            # Check for valid template UI structure format
            template_ui_format = len(structure_data) > 0 and all(
                isinstance(item, dict) and ('name' in item) 
                for item in structure_data if isinstance(item, dict)
            )
            
            if has_folders or has_folder_dicts or template_ui_format:
                print("DEBUG: Structure is valid (list with folder items)")
                return True
                
        print("DEBUG: Structure is not valid")
        return False
    
    def _get_default_structure(self):
        """
        Get a default empty structure
        
        Returns:
            dict: Empty structure with root folder
        """
        return {
            "folders": {
                "src": {},
                "docs": {},
                "resources": {}
            }
        }
        
    def _create_folders_from_structure(self, base_path, structure_data):
        """
        Create folder structure from a structure dictionary or list
        
        Args:
            base_path (str): Base directory to create folders in
            structure_data (dict or list): Structure data with folders
            
        Returns:
            list: List of created paths
        """
        created_paths = []
        
        # Check if structure_data is None
        if not structure_data:
            print(f"WARNING: Empty structure data")
            return created_paths
            
        # Handle dictionary-based structure format
        if isinstance(structure_data, dict):
            # Create folders from structure
            if 'folders' in structure_data and isinstance(structure_data['folders'], dict):
                folders = structure_data['folders']
                created_paths.extend(self._create_folders_recursive(base_path, folders))
            else:
                print(f"WARNING: Dictionary structure data missing 'folders' key or not in expected format")
        
        # Handle list-based structure format (like in the template structure)
        elif isinstance(structure_data, list):
            print(f"DEBUG: Processing list-based structure with {len(structure_data)} items")
            
            # Process each item in the list
            for item in structure_data:
                # Only process folder items
                if isinstance(item, dict) and item.get('type') == 'folder':
                    folder_name = item.get('name')
                    if folder_name:
                        # Create the folder
                        folder_path = os.path.join(base_path, folder_name)
                        try:
                            os.makedirs(folder_path, exist_ok=True)
                            created_paths.append(folder_path)
                            print(f"Created folder: {folder_path}")
                            
                            # Process children recursively if they exist
                            children = item.get('children', [])
                            if children and isinstance(children, list):
                                for child in children:
                                    if isinstance(child, dict) and child.get('type') == 'folder':
                                        child_name = child.get('name')
                                        if child_name:
                                            child_path = os.path.join(folder_path, child_name)
                                            try:
                                                os.makedirs(child_path, exist_ok=True)
                                                created_paths.append(child_path)
                                                print(f"Created subfolder: {child_path}")
                                                
                                                # Process grandchildren if they exist
                                                grandchildren = child.get('children', [])
                                                if grandchildren and isinstance(grandchildren, list):
                                                    for grandchild in grandchildren:
                                                        if isinstance(grandchild, dict) and grandchild.get('type') == 'folder':
                                                            grandchild_name = grandchild.get('name')
                                                            if grandchild_name:
                                                                grandchild_path = os.path.join(child_path, grandchild_name)
                                                                try:
                                                                    os.makedirs(grandchild_path, exist_ok=True)
                                                                    created_paths.append(grandchild_path)
                                                                    print(f"Created grandchild folder: {grandchild_path}")
                                                                except Exception as e:
                                                                    error_message = f"Failed to create grandchild folder {grandchild_path}: {str(e)}"
                                                                    print(f"ERROR: {error_message}")
                                                                    self._add_error(error_message)
                                            except Exception as e:
                                                error_message = f"Failed to create subfolder {child_path}: {str(e)}"
                                                print(f"ERROR: {error_message}")
                                                self._add_error(error_message)
                        except Exception as e:
                            error_message = f"Failed to create folder {folder_path}: {str(e)}"
                            print(f"ERROR: {error_message}")
                            self._add_error(error_message)
        else:
            print(f"WARNING: Invalid structure data type: {type(structure_data)}")
            
        return created_paths
    
    def _create_folders_recursive(self, base_path, folders_dict, parent_path=''):
        """
        Recursively create folders from a nested dictionary
        
        Args:
            base_path (str): Base directory
            folders_dict (dict): Dictionary of folders
            parent_path (str): Current parent path
            
        Returns:
            list: List of created paths
        """
        created_paths = []
        
        if not isinstance(folders_dict, dict):
            return created_paths
            
        for folder_name, sub_folders in folders_dict.items():
            # Skip folders starting with "." to avoid creating hidden folders
            if folder_name.startswith('.'):
                continue
                
            # Create folder path
            folder_path = os.path.join(base_path, parent_path, folder_name)
            
            try:
                # Create the folder
                os.makedirs(folder_path, exist_ok=True)
                created_paths.append(folder_path)
                print(f"Created folder: {folder_path}")
                
                # Process subfolders recursively
                if isinstance(sub_folders, dict):
                    sub_path = os.path.join(parent_path, folder_name)
                    sub_created = self._create_folders_recursive(base_path, sub_folders, sub_path)
                    created_paths.extend(sub_created)
            except Exception as e:
                error_message = f"Failed to create folder {folder_path}: {str(e)}"
                print(f"ERROR: {error_message}")
                self._add_error(error_message)
                
        return created_paths
    
    def _camel_case(self, s):
        """
        Convert a string to CamelCase
        
        Args:
            s: String to convert
            
        Returns:
            str: Camel case string
        """
        if not s:
            return ""
        
        # Split on non-alphanumeric characters
        words = re.split(r'[^a-zA-Z0-9]', s)
        # Join with first letter of each word capitalized
        return ''.join(word.title() for word in words if word)
    
    def _create_folder_structure(self, output_path, structure_data, placeholders=None, dry_run=False):
        """
        Create folder structure from a structure dictionary or list
        
        Args:
            output_path (str): Base directory to create folders in
            structure_data (dict or list): Structure data with folders
            placeholders (dict, optional): Dictionary of placeholders to replace
            dry_run (bool, optional): If True, don't actually create directories/files
            
        Returns:
            list: List of created paths
        """
        created_paths = []
        
        if not placeholders:
            placeholders = {}
        
        # Check if structure data is valid - accept both dict and list formats
        if not structure_data:
            print(f"WARNING: Empty structure data")
            return created_paths
        
        # For list-based structures, process using _process_template directly
        if isinstance(structure_data, list):
            print(f"DEBUG: Processing list-based structure with {len(structure_data)} items")
            return self._process_template(output_path, structure_data, placeholders, created_paths, dry_run)
        
        # Handle dictionary-based structures
        print(f"DEBUG: Processing dictionary-based structure")
        
        # Handle the root dictionary format - common in newer structures
        if 'root' in structure_data:
            # Don't create an actual 'root' directory, just process the contents
            if isinstance(structure_data['root'], list):
                # Process each item in the root list
                return self._process_template(output_path, structure_data['root'], placeholders, created_paths, dry_run)
        
        # Handle structure as a dictionary with named folders
        # Convert to a list of dictionaries for consistent processing
        structure_to_process = []
        for key, value in structure_data.items():
            if key != 'root':  # Skip the root key to avoid duplication
                if isinstance(value, list) or isinstance(value, dict):
                    folder_item = {
                        'type': 'folder',
                        'name': key,
                        'children': value if isinstance(value, list) else []
                    }
                    structure_to_process.append(folder_item)
                else:
                    folder_item = {
                        'type': 'folder',
                        'name': key
                    }
                    structure_to_process.append(folder_item)
        
        # Process the normalized structure list
        if structure_to_process:
            return self._process_template(output_path, structure_to_process, placeholders, created_paths, dry_run)
        else:
            print("WARNING: Invalid or empty structure format")
            return created_paths

    def _process_item(self, parent_path, item, placeholders, created_paths, dry_run):
        """
        Process a single item (file or folder) in the structure
        
        Args:
            parent_path: Path to the parent directory
            item: Item to process (dictionary with name, type, etc.)
            placeholders: Placeholders for variable substitution
            created_paths: List to add created paths to
            dry_run: If True, don't actually create anything
            
        Returns:
            None
        """
        if not isinstance(item, dict) or 'name' not in item or 'type' not in item:
            print(f"WARNING: Invalid item format: {item}")
            return
            
        item_name = self._replace_placeholders(item['name'], placeholders)
        item_path = os.path.join(parent_path, item_name)
        
        if item['type'] == 'folder':
            # Skip creating 'root' folders to avoid unnecessary nesting
            if item_name.lower() == 'root':
                # Process children directly in the parent_path
                if 'children' in item and item['children']:
                    for child in item['children']:
                        self._process_item(parent_path, child, placeholders, created_paths, dry_run)
            else:
                # Create the directory
                print(f"DEBUG: Creating directory from custom structure: {item_path}")
                if not dry_run:
                    os.makedirs(item_path, exist_ok=True)
                created_paths.append(item_path)
                
                # Process children
                if 'children' in item and item['children']:
                    for child in item['children']:
                        self._process_item(item_path, child, placeholders, created_paths, dry_run)
        
        elif item['type'] == 'file':
            # Create the file
            self._process_file(parent_path, item, placeholders, dry_run)
            if not dry_run:
                created_paths.append(item_path)

    def _process_template(self, output_path, structure, placeholders=None, created_paths=None, dry_run=False):
        """
        Process a template structure
        
        Args:
            output_path: Path where to create the structure
            structure: Structure data (list or dict)
            placeholders: Placeholders for variable substitution
            created_paths: List to store created paths
            dry_run: If True, don't actually create anything
            
        Returns:
            list: List of created paths
        """
        if not created_paths:
            created_paths = []
        
        if not placeholders:
            placeholders = {}
        
        if not structure:
            return created_paths
        
        # Log the structure details for debugging
        print(f"DEBUG: Processing template structure of type {type(structure)} with {len(structure) if isinstance(structure, list) else 'unknown'} items")
        
        # Normalize structure format to ensure consistent processing
        normalized_structure = self._normalize_structure_format(structure)
        
        # Process each item in the normalized structure
        for item in normalized_structure:
            # All items should be dictionaries with 'type' and 'name' at this point
            if not isinstance(item, dict) or 'type' not in item or 'name' not in item:
                print(f"WARNING: Skipping invalid item format after normalization: {item}")
                continue
            
            item_type = item.get('type')
            item_name = item.get('name')
            
            # Apply placeholders to the name
            if placeholders and isinstance(item_name, str):
                item_name = self._replace_placeholders(item_name, placeholders)
                item['name'] = item_name  # Update the item with the processed name
            
            # Final validation of name
            if not item_name or item_name == '[]' or item_name == 'name':
                print(f"WARNING: Skipping item with empty/invalid name after normalization: {item}")
                continue
            
            print(f"DEBUG: Processing item: {item_name} of type {item_type}")
            
            if item_type == 'folder':
                # Skip root folders to avoid unnecessary nesting
                if item_name.lower() == 'root':
                    # Process children of root folder directly in the parent path
                    if 'children' in item and item['children']:
                        self._process_template(output_path, item['children'], placeholders, created_paths, dry_run)
                else:
                    # Process as a directory
                    folder_path = os.path.join(output_path, item_name)
                    
                    # Create the directory
                    print(f"DEBUG: Creating directory: {folder_path}")
                    if not dry_run:
                        os.makedirs(folder_path, exist_ok=True)
                    
                    # Add to created paths
                    created_paths.append(folder_path)
                    
                    # Process children if any
                    if 'children' in item and item['children']:
                        self._process_template(folder_path, item['children'], placeholders, created_paths, dry_run)
            
            elif item_type == 'file':
                # Process as a file
                try:
                    file_path = self._process_file(output_path, item, placeholders, dry_run)
                    if file_path:
                        created_paths.append(file_path)
                except Exception as e:
                    print(f"ERROR: Failed to process file {item_name}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"WARNING: Unknown item type: {item_type} for {item_name}")
        
        return created_paths
    
    def _normalize_structure_format(self, structure):
        """
        Normalize structure format to ensure consistent processing
        
        Args:
            structure: Structure data in any supported format
            
        Returns:
            list: Normalized structure list with consistent format
        """
        normalized = []
        
        # Handle different structure formats
        
        # Already normalized format (list of dicts with type and name)
        if isinstance(structure, list):
            print(f"DEBUG: Normalizing structure list with {len(structure)} items")
            for item in structure:
                if isinstance(item, dict) and 'type' in item and 'name' in item:
                    # Already in normalized format, just copy it including any children
                    normalized_item = dict(item)  # Create a copy to avoid modifying original
                    
                    # Process children recursively if they exist
                    if 'children' in normalized_item and isinstance(normalized_item['children'], list):
                        normalized_item['children'] = self._normalize_structure_format(normalized_item['children'])
                        
                    normalized.append(normalized_item)
                elif isinstance(item, dict) and len(item) == 1:
                    # Old format: {folder_name: [children]}
                    for folder_name, children in item.items():
                        folder_item = {
                            'type': 'folder',
                            'name': folder_name
                        }
                        
                        # Add children if any
                        if isinstance(children, list) and children:
                            folder_item['children'] = self._normalize_structure_format(children)
                            
                        normalized.append(folder_item)
                elif isinstance(item, str):
                    # Simple string item (treat as file)
                    normalized.append({
                        'type': 'file',
                        'name': item
                    })
                else:
                    print(f"WARNING: Unsupported item format in structure: {item}")
                    if isinstance(item, dict):
                        print(f"Item keys: {list(item.keys())}")
                        # Try to interpret as folder or file based on available keys
                        if 'name' in item:
                            item_type = item.get('type', 'file')  # Default to file if type is missing
                            normalized_item = {
                                'type': item_type,
                                'name': item['name']
                            }
                            
                            # Handle children if this is a folder
                            if item_type == 'folder' and 'children' in item:
                                normalized_item['children'] = self._normalize_structure_format(item['children'])
                                
                            normalized.append(normalized_item)
        
            return normalized
        
        # Newer format with root array
        elif isinstance(structure, dict) and 'root' in structure and isinstance(structure['root'], list):
            # Process root items
            print(f"DEBUG: Normalizing structure with 'root' key containing {len(structure['root'])} items")
            for item in structure['root']:
                if isinstance(item, dict) and 'type' in item and 'name' in item:
                    # Already in normalized format, just copy it including any children
                    normalized_item = dict(item)  # Create a copy to avoid modifying original
                    
                    # Process children recursively if they exist
                    if 'children' in normalized_item and isinstance(normalized_item['children'], list):
                        normalized_item['children'] = self._normalize_structure_format(normalized_item['children'])
                        
                    normalized.append(normalized_item)
                elif isinstance(item, dict) and len(item) == 1:
                    # Old format: {folder_name: [children]}
                    for folder_name, children in item.items():
                        folder_item = {
                            'type': 'folder',
                            'name': folder_name
                        }
                        
                        # Add children if any
                        if isinstance(children, list) and children:
                            folder_item['children'] = self._normalize_structure_format(children)
                            
                        normalized.append(folder_item)
                elif isinstance(item, str):
                    # Simple string item (treat as file)
                    normalized.append({
                        'type': 'file',
                        'name': item
                    })
                else:
                    print(f"WARNING: Unsupported item format in structure root: {item}")
                    if isinstance(item, dict) and 'name' in item:
                        item_type = item.get('type', 'file')  # Default to file if type is missing
                        normalized_item = {
                            'type': item_type,
                            'name': item['name']
                        }
                        
                        # Handle children if this is a folder
                        if item_type == 'folder' and 'children' in item:
                            normalized_item['children'] = self._normalize_structure_format(item['children'])
                            
                        normalized.append(normalized_item)
        
        # Old format: dictionary of {folder_name: [children]}
        elif isinstance(structure, dict):
            print(f"DEBUG: Normalizing dictionary structure with {len(structure)} keys")
            for key, value in structure.items():
                if key != 'root':  # Skip 'root' key to avoid duplication
                    folder_item = {
                        'type': 'folder',
                        'name': key
                    }
                    
                    # Add children if any
                    if isinstance(value, list) and value:
                        folder_item['children'] = self._normalize_structure_format(value)
                    elif isinstance(value, dict):
                        # Nested dictionary structure
                        folder_item['children'] = self._normalize_structure_format(value)
                        
                    normalized.append(folder_item)
        
        print(f"DEBUG: Normalized structure has {len(normalized)} items")
        return normalized
        
    def _process_directory(self, output_path, contents, directory_name, placeholders, created_paths, dry_run=False):
        """
        Process a directory item in the structure
        
        Args:
            output_path: Base path for the directory
            contents: List of child items
            directory_name: Name of the directory
            placeholders: Placeholders to replace
            created_paths: List to store created paths
            dry_run: If True, don't actually create the directory
        """
        # Skip invalid directory names
        if not directory_name or directory_name == '[]' or directory_name == 'name':
            print(f"WARNING: Skipping directory with invalid name: {directory_name}")
            return
        
        # Convert to string if it's not already
        if not isinstance(directory_name, str):
            directory_name = str(directory_name)
        
        # If placeholders present, apply them to the directory name
        if placeholders:
            directory_name = self._replace_placeholders(directory_name, placeholders)
        
        # Create directory path
        directory_path = os.path.join(output_path, directory_name)
        
        # Create the directory if it doesn't exist
        print(f"DEBUG: Creating directory from custom structure: {directory_path}")
        if not dry_run:
            os.makedirs(directory_path, exist_ok=True)
        
        # Add to created paths
        created_paths.append(directory_path)
        
        # Process children if any
        if contents:
            # Normalize children to ensure consistent format
            normalized_children = self._normalize_structure_format(contents)
            self._process_template(directory_path, normalized_children, placeholders, created_paths, dry_run)
        
    def _process_file(self, parent_output_path, item, placeholders=None, dry_run=False):
        """
        Process a file item from the structure, copying it to the output path with placeholders applied
        
        Args:
            parent_output_path: The output path for the parent directory
            item: The file item to process
            placeholders: Dictionary of placeholder replacements
            dry_run: If True, don't actually create files, just check structure
            
        Returns:
            str or None: The output file path if successful, None if failed
        """
        # Default placeholders to empty dict if None
        if placeholders is None:
            placeholders = {}
        
        # Get file name from item
        if isinstance(item, dict):
            # Get the original name from the name field
            item_name = item.get('name')
            
            print(f"🔍 DEBUG FILE RENAMING: Processing file item {item_name}")
            print(f"🔍 DEBUG FILE RENAMING: Full item data: {item}")
            print(f"🔍 DEBUG FILE RENAMING: Placeholders: {placeholders}")
            
            # Normalize name if it's an array
            if isinstance(item_name, list):
                if item_name and item_name[0]:
                    item_name = str(item_name[0])
                else:
                    print(f"WARNING: Skipping file with empty name array: {item}")
                    return None
                
            # Skip files with empty or placeholder names
            if not item_name or item_name == '[]' or item_name == 'name':
                print(f"WARNING: Skipping file with empty/invalid name: {item}")
                return None
            
            # Initialize output_name with item_name as a fallback
            output_name = item_name
            
            # Check if this file should use the project name based on the flag
            # Prefer rename_flag, but fall back to uses_project_name for backward compatibility
            rename_flag = item.get('rename_flag', False)
            uses_project_name = item.get('uses_project_name', False)
            
            print(f"DEBUG: Processing file '{item_name}' with rename_flag={rename_flag}, uses_project_name={uses_project_name}")
            
            # First check if the filename contains a placeholder
            if "${PROJECT_NAME}" in item_name:
                # Apply placeholder replacement directly
                output_name = self._replace_placeholders(item_name, placeholders)
                print(f"Applied placeholder to filename: {item_name} -> {output_name}")
            elif rename_flag or uses_project_name:
                # Get the project name
                project_name = placeholders.get("PROJECT_NAME", "Unknown")
                
                # Extract file extension
                name_parts = os.path.splitext(item_name)
                if len(name_parts) == 2:
                    base_name, ext = name_parts
                    # Replace base name with project name
                    output_name = f"{project_name}{ext}"
                else:
                    # No extension, use project name directly
                    output_name = project_name
                
                print(f"Renamed file: {item_name} -> {output_name}")
            else:
                # For files not using project name, apply normal placeholder replacement
                print(f"DEBUG: Applying normal placeholder replacement to: '{item_name}'")
                output_name = self._replace_placeholders(item_name, placeholders) if placeholders else item_name
                print(f"DEBUG: After placeholder replacement: '{output_name}'")
                
                # Handle special case for ${PROJECT_NAME} in the name (legacy support)
                if "${PROJECT_NAME}" in output_name:
                    project_name = placeholders.get("PROJECT_NAME", "Unknown")
                    output_name = output_name.replace("${PROJECT_NAME}", project_name)
                    print(f"DEBUG: After legacy placeholder replacement: '{output_name}'")
            
            # Get output file path
            file_path = os.path.join(parent_output_path, output_name)
            
            # Print final paths
            print(f"🔍 DEBUG FILE RENAMING: Original name: {item_name}")
            print(f"🔍 DEBUG FILE RENAMING: Output name: {output_name}")
            print(f"🔍 DEBUG FILE RENAMING: Full output path: {file_path}")
            
            # Handle string items
            source_path = None
            content = None
            
            # Check if we have path or cached_path for the file
            if 'original_path' in item:
                source_path = item['original_path']
                print(f"🔍 DEBUG FILE RENAMING: Using original_path: {source_path}")
            elif 'path' in item:
                source_path = item['path']
                print(f"🔍 DEBUG FILE RENAMING: Using path: {source_path}")
            elif 'cached_path' in item:
                source_path = item['cached_path']
                print(f"🔍 DEBUG FILE RENAMING: Using cached_path: {source_path}")
                
            # Skip if we're in dry run mode
            if dry_run:
                return file_path
                
            # If the file already exists, verify overwrite
            if os.path.exists(file_path) and not self._verify_overwrite(file_path):
                print(f"WARNING: Not overwriting existing file: {file_path}")
                return None
                
            # Create parent directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Process file content
            if source_path and os.path.exists(source_path):
                # Binary files are copied directly
                is_binary = item.get('is_binary', False)
                
                if is_binary:
                    # For binary files, just copy the file
                    try:
                        # Use shutil.copy2 to copy file with metadata
                        shutil.copy2(source_path, file_path)
                        print(f"Copied binary file to {file_path}")
                        
                        # Log the renaming operation for debugging
                        if output_name != item_name:
                            print(f"✅ Successfully renamed binary file: {item_name} -> {output_name}")
                            
                        return file_path
                    except Exception as e:
                        error_message = f"Failed to copy binary file {source_path} to {file_path}: {str(e)}"
                        print(f"ERROR: {error_message}")
                        self._add_error(error_message)
                        return None
                else:
                    # For text files, replace placeholders
                    try:
                        # Read the file
                        with open(source_path, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                            
                        # Replace placeholders if they exist
                        if placeholders and self._might_contain_placeholders(source_path):
                            content = self._replace_placeholders(content, placeholders)
                            
                        # Write the file
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                            
                        # Log the renaming operation for debugging
                        if output_name != item_name:
                            print(f"✅ Successfully renamed text file: {item_name} -> {output_name}")
                            
                        print(f"Created file with placeholders: {file_path}")
                        return file_path
                    except UnicodeDecodeError:
                        # If Unicode decoding fails, treat as binary and copy directly
                        try:
                            shutil.copy2(source_path, file_path)
                            print(f"Copied file (binary after Unicode decode error) to {file_path}")
                            
                            # Log the renaming operation for debugging
                            if output_name != item_name:
                                print(f"✅ Successfully renamed file after Unicode decode error: {item_name} -> {output_name}")
                                
                            return file_path
                        except Exception as e:
                            error_message = f"Failed to copy file {source_path} to {file_path}: {str(e)}"
                            print(f"ERROR: {error_message}")
                            self._add_error(error_message)
                            return None
                    except Exception as e:
                        error_message = f"Failed to process file {source_path} to {file_path}: {str(e)}"
                        print(f"ERROR: {error_message}")
                        self._add_error(error_message)
                        return None
            elif 'content' in item or content:
                # Direct file content provided
                file_content = content or item.get('content', '')
                
                # Apply placeholders
                if placeholders:
                    file_content = self._replace_placeholders(file_content, placeholders)
                    
                # Write the content to the file
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_content)
                        
                    # Log the renaming operation for debugging
                    if output_name != item_name:
                        print(f"✅ Successfully renamed file with direct content: {item_name} -> {output_name}")
                        
                    print(f"Created file with content: {file_path}")
                    return file_path
                except Exception as e:
                    error_message = f"Failed to write content to {file_path}: {str(e)}"
                    print(f"ERROR: {error_message}")
                    self._add_error(error_message)
                    return None
            else:
                # No content or source path, create an empty file
                try:
                    with open(file_path, 'w') as f:
                        pass
                        
                    # Log the renaming operation for debugging
                    if output_name != item_name:
                        print(f"✅ Successfully renamed empty file: {item_name} -> {output_name}")
                        
                    print(f"Created empty file: {file_path}")
                    return file_path
                except Exception as e:
                    error_message = f"Failed to create empty file {file_path}: {str(e)}"
                    print(f"ERROR: {error_message}")
                    self._add_error(error_message)
                    return None
        elif isinstance(item, str):
            # Simple string item - just create an empty file with the name
            file_path = os.path.join(parent_output_path, item)
            
            # Skip if we're in dry run mode
            if dry_run:
                return file_path
                
            # Create parent directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Create the file
            try:
                with open(file_path, 'w') as f:
                    pass
                    
                # Log the renaming operation for debugging
                if output_name != item:
                    print(f"✅ Successfully renamed empty file: {item} -> {output_name}")
                    
                print(f"Created empty file: {file_path}")
                return file_path
            except Exception as e:
                error_message = f"Failed to create empty file {file_path}: {str(e)}"
                print(f"ERROR: {error_message}")
                self._add_error(error_message)
                return None
        else:
            print(f"WARNING: Unrecognized file item format: {item}")
            return None
    
    def start_batch_creation(self, project_names, output_dir, template_file=None, project_type="Standard", 
                            structure_name=None, use_version_control=False, create_backup=True, callback=None,
                            selected_template=None):
        """
        Set up a batch creation of multiple projects
        
        Args:
            project_names: List of project names to create
            output_dir: Directory to create projects in
            template_file: Optional template file to use
            project_type: Type of project
            structure_name: Custom structure to use (optional)
            use_version_control: Whether to use version control
            create_backup: Whether to create backups
            callback: Function to call when batch process completes
            selected_template: The selected template object (used for gallery templates)
        """
        if not project_names or not output_dir:
            return False
        
        # Create queue of projects to create
        self.project_queue = [(name.strip(), output_dir, template_file, project_type, 
                             use_version_control, create_backup, structure_name, selected_template) 
                             for name in project_names if name.strip()]
        
        # Start batch processing thread
        self.is_building = True
        
        # Use threading to prevent UI freeze
        thread = threading.Thread(target=self._process_batch_queue, args=(callback,))
        thread.daemon = True  # Make thread daemon so it doesn't block application exit
        thread.start()
        
        return True
    
    def _process_batch_queue(self, callback=None):
        """Process the batch queue of projects to create"""
        results = []
        
        # Progress indicator for CLI usage
        print(f"Starting batch processing of {len(self.project_queue)} projects...")
        
        # Process all projects in the queue
        for i, (name, output_dir, template_file, project_type, 
               use_version_control, create_backup, structure_name, selected_template) in enumerate(self.project_queue):
            
            # Log progress
            print(f"Creating project {i+1}/{len(self.project_queue)}: {name}")
            
            # Add debug info about the template being used
            if template_file == "gallery_template":
                print(f"Using gallery template with structure: {structure_name}")
                print(f"Project name: {name}, Output dir: {output_dir}")
                
                # Special handling for gallery template - use the actual template name
                # instead of the generic "gallery_template" string
                if selected_template and isinstance(selected_template, dict) and 'name' in selected_template:
                    actual_template_name = selected_template['name']
                    print(f"Using actual template name '{actual_template_name}' instead of 'gallery_template'")
                    template_file = actual_template_name
            else:
                print(f"Using template file: {template_file}")
                if template_file and not os.path.exists(template_file):
                    print(f"Warning: Template file does not exist: {template_file}")
            
            # Create project
            print(f"Creating project: {name} in {output_dir}")

            # Run the create_project method
            success, result = self.create_project(
                project_name=name,
                output_dir=output_dir,
                template_file=template_file if template_file else structure_name,
                structure_name=structure_name,
                use_cached_files=True
            )
            
            results.append((name, success, result))
        
        # Completed
        self.is_building = False
        self.project_queue = []
        
        print("Batch processing completed.")
        
        # Call callback with results - this will happen in the main thread
        if callback:
            callback(results)

        # Return results for potential direct use
        return results

    def _replace_placeholders(self, text, placeholders):
        """
        Replace placeholders in text with values
        
        Args:
            text: Text with placeholders
            placeholders: Dictionary of placeholder values
            
        Returns:
            str: Text with placeholders replaced
        """
        if not text or not isinstance(text, str):
            return text
            
        result = text
        
        # Replace ${PLACEHOLDER} format
        for key, value in placeholders.items():
            placeholder = f"${{{key}}}"
            result = result.replace(placeholder, value)
            
        # Replace $PLACEHOLDER format
        for key, value in placeholders.items():
            placeholder = f"${key}"
            result = result.replace(placeholder, value)
            
        return result
        
    def _add_error(self, error_message):
        """
        Add an error message to the error log
        
        Args:
            error_message: Error message to add
        """
        if not hasattr(self, '_errors'):
            self._errors = []
            
        self._errors.append(error_message)
        print(f"ERROR: {error_message}")

    def _verify_overwrite(self, file_path):
        """
        Verify if an existing file should be overwritten
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if the file should be overwritten, False otherwise
        """
        # By default, allow overwriting files during project creation
        # This is a simple implementation; in the real app UI, 
        # this could prompt the user or check preferences
        return True
        
    def batch_create_projects(self, project_names, template_name=None, structure_name=None, output_dir=None, use_cached_files=True, template_data=None):
        """
        Create multiple projects from a list of project names
        
        Args:
            project_names (list): List of project names to create
            template_name (str, optional): Template to use for projects
            structure_name (str, optional): Structure to use for projects
            output_dir (str, optional): Directory to create projects in
            use_cached_files (bool, optional): Whether to use cached files
            template_data (dict, optional): Template data to use instead of loading from file
            
        Returns:
            dict: Results dictionary with success/failure information
        """
        # Validate input
        if not isinstance(project_names, list):
            error_msg = "Project names must be provided as a list"
            print(f"ERROR: {error_msg}")
            return {
                "error": error_msg,
                "successful_count": 0,
                "total_count": 0,
                "success_rate": "0/0 (0%)"
            }
            
        # Ensure output directory is provided
        if not output_dir:
            error_msg = "Output directory must be provided for batch creation"
            print(f"ERROR: {error_msg}")
            return {
                "error": error_msg,
                "successful_count": 0,
                "total_count": 0,
                "success_rate": "0/0 (0%)"
            }
        
        # Ensure the output directory exists
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            error_msg = f"Failed to create output directory: {e}"
            print(f"ERROR: {error_msg}")
            return {
                "error": error_msg,
                "successful_count": 0,
                "total_count": 0,
                "success_rate": "0/0 (0%)"
            }
            
        # Initialize results
        results = {
            "results": [],  # List of tuples (project_name, success, message)
            "successful_count": 0,
            "total_count": len(project_names),
            "success_rate": "0/0 (0%)",
            "no_structure": True  # Default to True, will set to False if any project has a structure
        }
        
        # Track if all projects were created without structure
        all_no_structure = True
        
        # Process each project name
        for project_name in project_names:
            print(f"Creating project: {project_name} in {output_dir}")
            
            # Create project directory
            project_dir = os.path.join(output_dir, project_name)
            try:
                # Run the create_project method
                success, result = self.create_project(
                    project_name=project_name,
                    output_dir=output_dir,
                    template_file=template_data if template_data else template_name,
                    structure_name=structure_name,
                    use_cached_files=use_cached_files
                )
                
                # Check if the result is a dictionary with a no_structure flag
                if success:
                    results["successful_count"] += 1
                    if isinstance(result, dict):
                        if result.get("no_structure", False):
                            # Project was created without structure
                            results["results"].append((project_name, True, result))
                        else:
                            # Project was created with structure
                            results["results"].append((project_name, True, result["project_dir"]))
                            # At least one project had a structure
                            all_no_structure = False
                    else:
                        # Result is just a string (project directory)
                        results["results"].append((project_name, True, result))
                        # Assume it has a structure
                        all_no_structure = False
                else:
                    # Failed to create project
                    results["results"].append((project_name, False, result))
                    
            except Exception as e:
                print(f"ERROR creating project {project_name}: {e}")
                import traceback
                traceback.print_exc()
                results["results"].append((project_name, False, str(e)))
        
        # Update no_structure flag based on results
        results["no_structure"] = all_no_structure
        
        # Calculate success rate
        if results["total_count"] > 0:
            success_rate = results["successful_count"] / results["total_count"] * 100
            results["success_rate"] = f"{results['successful_count']}/{results['total_count']} ({success_rate:.0f}%)"
        
        return results

    def _process_files_array(self, project_dir, files_array, placeholders, use_cached_files=True, template_name=None):
        """
        Process the files array and copy files to the project
        
        Args:
            project_dir: Base project directory
            files_array: Array of file objects
            placeholders: Dictionary of placeholders for variable substitution
            use_cached_files: Whether to use cached files when available
            template_name: Name of the template (used for cache lookup)
            
        Returns:
            list: Paths of copied files
        """
        copied_files = []
        # --- ADDED --- Access Cache Manager
        cache_manager = None
        if hasattr(self, 'template_manager') and hasattr(self.template_manager, 'file_cache_manager'):
             cache_manager = self.template_manager.file_cache_manager
        else:
            print("WARNING: ProjectBuilder cannot access FileCacheManager via template_manager.")
        # --- END ADDED ---

        if not files_array:
            return copied_files

        print(f"Processing {len(files_array)} files from files array for template: {template_name}")

        for file_data in files_array:
            source_path_used = "None" # Debugging
            source_path = None      # Reset for each file
            cached_path_attempted = None # Debugging
            original_path_attempted = None # Debugging

            try:
                # Get file info
                file_name = file_data.get('file_name')
                original_path = file_data.get('original_path')
                folder = file_data.get('folder', '')
                rename_flag = file_data.get('rename_flag', False)
                uses_project_name = file_data.get('uses_project_name', False)
                file_type = file_data.get('file_type', 'other')

                if not file_name:
                    print(f"WARNING: File data missing file_name: {file_data}")
                    continue
                
                original_filename_for_debug = file_name # Store before potential rename

                # Print debug info for renaming
                # print(f"🔍 RENAMING DEBUG: Processing file '{file_name}' with rename_flag={rename_flag}, uses_project_name={uses_project_name}")

                # First check if the filename contains a placeholder
                if "${PROJECT_NAME}" in file_name:
                    # Apply placeholder replacement directly
                    file_name = self._replace_placeholders(file_name, placeholders)
                    # print(f"Applied placeholder to filename: {original_filename_for_debug} -> {file_name}")
                # Apply placeholders to file name if either flag is set
                elif rename_flag or uses_project_name:
                    project_name = placeholders.get("PROJECT_NAME", "Unknown")
                    name_parts = os.path.splitext(file_name)
                    if len(name_parts) == 2:
                        base_name, ext = name_parts
                        file_name = f"{project_name}{ext}"
                    else:
                        file_name = project_name
                    # print(f"Renamed file: {original_filename_for_debug} -> {file_name}")

                # Apply placeholders to folder path
                folder = self._replace_placeholders(folder, placeholders)

                # Create folder structure if it doesn't exist
                folder_path = os.path.join(project_dir, folder)
                os.makedirs(folder_path, exist_ok=True)

                # Determine destination path
                dest_path = os.path.join(folder_path, file_name)

                # --- MODIFIED --- Source Path Determination Logic
                print(f"DEBUG: Determining source path for: {original_filename_for_debug} (output: {file_name})")

                # 1. Try cache first
                if use_cached_files and template_name and cache_manager:
                    try:
                        # Use original_path as the key to find the file in the specific template's cache metadata
                        # --- MODIFIED --- get_cached_file returns a dict, not just a path
                        file_info_from_cache = cache_manager.get_cached_file(template_name, file_path=original_path)
                        cached_path = None
                        if file_info_from_cache:
                            cached_path = file_info_from_cache.get('cached_path')
                        # --- END MODIFIED ---
                        
                        cached_path_attempted = cached_path # Store for logging
                        
                        # --- MODIFIED --- Check if the extracted cached_path exists
                        if cached_path and os.path.exists(cached_path):
                        # --- END MODIFIED ---
                            source_path = cached_path
                            source_path_used = "Cache"
                            print(f"  ✅ Using CACHED file: {source_path}")
                            if hasattr(cache_manager, 'cache_stats'): cache_manager.cache_stats['hits'] += 1
                        elif cached_path:
                            print(f"  ⚠️ Cache path found ({cached_path}) but file does not exist.")
                        # else:
                            # print(f"  ℹ️ File not found in cache metadata for template '{template_name}' using original_path '{original_path}'.")
                    except Exception as cache_err:
                        print(f"  ⚠️ Error looking up file in cache: {cache_err}")
                        cached_path_attempted = f"Error: {cache_err}" # Store error for logging

                # 2. Fall back to original path
                if not source_path and original_path:
                    original_path_attempted = original_path # Store for logging
                    if os.path.exists(original_path):
                        source_path = original_path
                        source_path_used = "Original"
                        print(f"  ✅ Using ORIGINAL file: {source_path}")
                        if cache_manager and hasattr(cache_manager, 'cache_stats'): cache_manager.cache_stats['misses'] += 1
                    else:
                        print(f"  ⚠️ Original path ({original_path}) does not exist.")
                elif not source_path:
                    print(f"  ℹ️ Original path was not provided in template data.")
                    

                # 3. Skip if no valid source path found
                if not source_path:
                    print(f"  ❌ ERROR: No valid source path found for file '{original_filename_for_debug}'.")
                    print(f"      Attempted Cache Path: {cached_path_attempted}")
                    print(f"      Attempted Original Path: {original_path_attempted}")
                    continue

                # --- END MODIFIED ---

                # Copy the file
                print(f"  ⚙️ Attempting copy: '{source_path}' ({source_path_used}) -> '{dest_path}'")
                try:
                    shutil.copy2(source_path, dest_path)
                    copied_files.append(dest_path)
                    print(f"  ✅ Copied file successfully.")

                    # Log successful renaming
                    if file_name != original_filename_for_debug:
                        print(f"  ℹ️ File renamed during copy: '{original_filename_for_debug}' -> '{file_name}'")

                    # Replace placeholders in text files only, not in binary files
                    is_binary = file_data.get('is_binary', False)

                    if not is_binary and placeholders and self._might_contain_placeholders(source_path):
                        try:
                            with open(dest_path, 'r', encoding='utf-8', errors='replace') as f:
                                content = f.read()
                            content = self._replace_placeholders(content, placeholders)
                            with open(dest_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            print(f"  ✅ Replaced placeholders in: {dest_path}")
                        except Exception as e:
                            print(f"  ⚠️ WARNING: Error replacing placeholders in {dest_path}: {str(e)}")
                except Exception as e:
                    # --- MODIFIED --- More specific copy error logging
                    print(f"  ❌ ERROR: Failed to copy file using {source_path_used} path.")
                    print(f"      Source: {source_path}")
                    print(f"      Destination: {dest_path}")
                    print(f"      Error Details: {str(e)}") # THIS IS WHERE USER'S ERROR MESSAGE IS NEEDED FOR CONTEXT
                    import traceback
                    traceback.print_exc() # Keep traceback for detailed debugging if needed
                    # --- END MODIFIED ---

            except Exception as e:
                print(f"ERROR processing file data block: {file_data}. Error: {str(e)}")
                import traceback
                traceback.print_exc()

        # --- ADDED --- Save cache stats after processing
        if cache_manager:
            cache_manager._save_stats()
        # --- END ADDED ---

        return copied_files
        
    def _might_contain_placeholders(self, file_path):
        """
        Check if a file might contain placeholders by reading the first few KB
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if the file might contain placeholders
        """
        try:
            # First check if the file is likely binary based on extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # Common binary extensions - shortlist for quick check
            binary_extensions = {
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp', 
                '.mp3', '.wav', '.mp4', '.mov', '.zip', '.exe', '.pdf'
            }
            
            # If it's a common binary extension, assume it doesn't have placeholders
            if ext in binary_extensions:
                return False
                
            # Read the first 8KB of the file
            with open(file_path, 'rb') as f:
                data = f.read(8192)
                
            # If contains null bytes, likely binary
            if b'\0' in data:
                return False
            
            # Convert to string with errors ignored
            text = data.decode('utf-8', errors='ignore')
            
            # Check for common placeholder patterns
            return '${' in text or '$PROJECT_NAME' in text or '$project_name' in text
        except Exception as e:
            print(f"Error checking for placeholders: {e}")
            return False
            
    def _process_binary_file(self, source_path, dest_path, placeholders):
        """
        Process a binary file that might contain placeholder text
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
            placeholders: Dictionary of placeholders
            
        Returns:
            bool: Success status
        """
        try:
            # For binary files, simply copy - don't attempt to replace placeholders
            # This ensures binary file integrity is maintained
            print(f"Processing binary file: using direct copy method")
            shutil.copy2(source_path, dest_path)
            return True
        except Exception as e:
            print(f"Error copying binary file: {e}")
            import traceback
            traceback.print_exc()
            return False

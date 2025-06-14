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
import tempfile
import base64
from pathlib import Path

# Using PyQt for the UI framework
from PyQt6.QtWidgets import QMessageBox, QApplication, QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QProgressDialog
from PyQt6.QtCore import Qt, QTimer
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

# Import the normalize_path_for_storage function for cross-platform compatibility
try:
    from app.utils.utils import normalize_path_for_storage, safe_path_join
except ImportError:
    # Fallback if not available
    def normalize_path_for_storage(path):
        """Normalize a path for storage with forward slashes"""
        if not path:
            return ""
        norm_path = os.path.normpath(path)
        return norm_path.replace('\\', '/')
    
    def safe_path_join(*paths):
        """Join paths in a safe, cross-platform way"""
        joined_path = os.path.join(*paths)
        return os.path.normpath(joined_path)

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
        layout.addWidget(self.cancel_button, alignment=Qt.AlignmentFlagFlagFlagFlagFlag.AlignRight)
    
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
        
        # Initialize result with input string
        result = input_string
        
        # Case 1: Input contains the full placeholder "${PROJECT_NAME}"
        if placeholder_dollar in input_string:
            # Create a new string with the placeholder replaced
            # We need to be careful with this replacement to ensure no $ artifacts remain
            parts = input_string.split(placeholder_dollar)
            result = project_name.join(parts)
        
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
            # If it's another kind of file that just happens to start with $
            elif "." in remaining:
                # It has an extension - preserve the extension
                parts = remaining.split(".")
                ext = "." + ".".join(parts[1:])  # Handle multiple dots in filename
                result = f"{project_name}{ext}"
            # Any other $ prefix case
            else:
                # Just replace the $ with the project name
                result = f"{project_name}{remaining}"
        
        # Log the final result for debugging
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
                            # Apply flags to the file data
                            file_data = files_by_name[file_name]
                            if rename_flag and not file_data.get('rename_flag'):
                                file_data['rename_flag'] = True
                                
                            if uses_project_name and not file_data.get('uses_project_name'):
                                file_data['uses_project_name'] = True
                
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
        # print(f"DEBUG: Creating project '{project_name}' in directory: '{output_dir}'")
        # print(f"DEBUG: Using template: '{template_file}', structure: '{structure_name}'")
            
        # Validate project name
        if not project_name:
            return False, "No project name provided"
            
        # Validate output directory
        if not output_dir:
            return False, "No output directory provided"
            
        # Check if we can use security bookmarks - requires macOS and objc modules
        use_bookmark = False
        bookmarks_available = False
        
        # Only try to import security bookmarks if we're on macOS
        if platform.system() == "Darwin":
            try:
                # Check if Foundation module is actually available (not just importable)
                import importlib
                foundation_spec = importlib.util.find_spec("Foundation")
                objc_spec = importlib.util.find_spec("objc")
                
                if foundation_spec is not None and objc_spec is not None:
                    # Now import the actual BookmarkAccessContext
                    from app.utils.security_bookmarks import BookmarkAccessContext
                    # print("DEBUG: Security bookmarks are available.")
                    bookmarks_available = True
                else:
                    print("WARNING: Foundation/objc modules not available. Security bookmarks disabled.")
            except (ImportError, ModuleNotFoundError) as e:
                print(f"WARNING: Could not import security_bookmarks module: {e}")
        
        # Skip security bookmarks if we can't access them
        if not bookmarks_available:
            print("INFO: Creating project without security bookmarks.")
            return self._create_project_internal(
                project_name, output_dir, template_file, project_type,
                structure_name, create_backup, use_cached_files
            )
            
        # Try with security bookmarks since we have confirmed they're available
        try:
            # Skip security bookmark if output_dir is a dict or not a valid path
            if not isinstance(output_dir, str) or not os.path.exists(os.path.dirname(output_dir)):
                print(f"WARNING: Skipping security bookmark for invalid output directory: {output_dir}")
                use_bookmark = False
            else:
                # print(f"DEBUG: Using security bookmark for output directory: {output_dir}")
                use_bookmark = True
                with BookmarkAccessContext(output_dir):
                    return self._create_project_internal(
                        project_name, output_dir, template_file, project_type,
                        structure_name, create_backup, use_cached_files
                    )
        except Exception as e:
            print(f"ERROR: Failed to access directory with security bookmark: {e}")
            print("Falling back to standard directory access...")
            use_bookmark = False
        
        # If we're not using a bookmark or fell back, use standard project creation
        if not use_bookmark:
            return self._create_project_internal(
                project_name, output_dir, template_file, project_type,
                structure_name, create_backup, use_cached_files
            )
            
    def _create_project_internal(self, project_name, output_dir=None, template_file=None, project_type="Standard", 
                        structure_name=None, create_backup=True, use_cached_files=True):
        """Create a new project based on a template - internal implementation.
        
        Args:
            project_name (str): Name of the project
            output_dir (str, optional): Directory where the project should be created
            template_file (str or dict, optional): Path to template file or template data dictionary
            project_type (str, optional): Type of project (Standard, etc.)
            structure_name (str, optional): Name of structure to use
            create_backup (bool, optional): Whether to create a backup of the project directory if it exists
            use_cached_files (bool, optional): Whether to use cached files when available
            
        Returns:
            tuple: (success, result) where result is the project path or error message
        """
        # print(f"DEBUG: Creating project '{project_name}' in directory: '{output_dir}'")
        # print(f"DEBUG: Using template: '{template_file}', structure: '{structure_name}'")
        
        # Validate project name
        if not project_name:
            return False, "Project name is required"
        
        # Input validation
        if not output_dir:
            return False, "Output directory is required"
            
        # Create the project directory
        project_dir = os.path.join(output_dir, project_name)
        try:
            os.makedirs(project_dir, exist_ok=True)
            # print(f"Created project directory: {project_dir}")
        except Exception as e:
            return False, f"Failed to create project directory: {str(e)}"
            
        # Template handling
        template_data = None
        template_file_path = None
        template_name = None
        
        # Handle different template_file input types
        if template_file:
            if isinstance(template_file, dict):
                # Direct template data provided
                template_data = template_file
                template_name = template_data.get('name', 'Unknown')
                template_file_path = template_data.get('file_path', None)
            elif isinstance(template_file, str) and os.path.exists(template_file):
                # Template file path provided
                template_file_path = template_file
                # Load the template data from the file
                try:
                    with open(template_file, 'r') as f:
                        template_data = json.load(f)
                        template_name = template_data.get('name', os.path.basename(template_file))
                        # print(f"Loaded template from file: {template_file}")
                except Exception as e:
                    return False, f"Failed to load template file: {str(e)}"
            else:
                print(f"Warning: Template file not found or invalid: {template_file}")
                # Will fall back to empty template
        
        # Set default template data if none provided
        if not template_data:
            template_data = {"name": "Empty", "structure": [], "type": project_type}
            template_name = "Empty"
            # print("Using empty template")
        
        # Collect custom options from template if needed
        custom_values = self._collect_custom_options(template_data)
        if custom_values is None:
            # User cancelled custom options dialog
            return False, "Project creation cancelled by user"
        
        # Extract date and time formats from template
        date_format, time_format = self._extract_datetime_formats(template_data)
        
        # Check if this project name contains sequence date information
        sequence_date_info = self._extract_sequence_date_from_project_name(project_name)
        
        # Create placeholders with custom values and date/time formats
        placeholders = self._create_placeholders(
            project_name, 
            custom_values=custom_values,
            date_format=date_format,
            time_format=time_format,
            sequence_date_info=sequence_date_info
        )
        
        # Get structure data
        structure_data = self._get_structure_data(template_data, structure_name)
        
        # Handle backup of existing directory if needed
        if os.path.exists(project_dir) and os.listdir(project_dir):
            if create_backup:
                # Create backup of existing directory
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = f"{project_dir}_backup_{timestamp}"
                try:
                    # print(f"Creating backup at {backup_dir}")
                    shutil.copytree(project_dir, backup_dir)
                    # Also try to copy hidden files which might be missed by copytree
                    if platform.system() != "Windows":
                        # Unix-like systems
                        os.system(f'cp -r "{project_dir}/."* "{backup_dir}" 2>/dev/null || true')
                    # print(f"Created backup at {backup_dir}")
                    
                    # Remove old directory completely instead of just emptying it
                    shutil.rmtree(project_dir)
                    # print(f"Removed old project directory: {project_dir}")
                    
                    # Create a fresh empty directory
                    os.makedirs(project_dir, exist_ok=True)
                    # print(f"Created fresh project directory: {project_dir}")
                    
                except Exception as e:
                    print(f"Failed to create backup or prepare project directory: {e}")
                    return False, f"Failed to create backup: {str(e)}"
            else:
                # Simply empty the directory
                # print(f"Emptying existing project directory: {project_dir}")
                for item in os.listdir(project_dir):
                    item_path = os.path.join(project_dir, item)
                    try:
                        if os.path.isfile(item_path) or os.path.islink(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except Exception as e:
                        print(f"Failed to remove item {item_path}: {e}")
                        return False, f"Failed to empty project directory: {str(e)}"
        
        # Check for valid structure - crucial step to validate structure exists
        if not structure_data:
            # print(f"DEBUG: No valid structure found for structure_name: '{structure_name}'")
            # Create the project directory but return a message that there's no structure
            try:
                os.makedirs(project_dir, exist_ok=True)
            except Exception as e:
                print(f"Error creating project directory: {e}")
                return False, f"Failed to create project directory: {str(e)}"
                
            # Instead of failing, return success with no_structure flag
            return True, {"project_dir": project_dir, "no_structure": True}
        
        # Process the template
        # print(f"Processing template for project: {project_name}")
        
        # Track created paths for reporting
        created_paths = []
        
        # Process the template structure
        # print(f"Creating project structure with {len(structure_data)} top-level items")
        try:
            # Process the template - check if we should process files separately
            has_files_array = template_data and 'files' in template_data and template_data['files']
            has_structure_with_files = self._structure_contains_files(structure_data)
            
            if has_files_array and not has_structure_with_files:
                # Only process files array if structure doesn't contain files (avoid duplication)
                # Apply flags from structure to files if applicable
                template_data['files'] = self._apply_structure_flags_to_files(
                    structure_data, template_data['files']
                )
                
                # Process files array - copy files with placeholders
                success, copied_files = self._process_files_array(
                    project_dir, 
                    template_data['files'], 
                    placeholders,
                    use_cached_files=use_cached_files,
                    template_name=template_name
                )
                
                if success:
                    # Add to created paths for reporting
                    if copied_files:
                        created_paths.extend(copied_files)
                else:
                    return False, f"Failed to copy files: {copied_files}"
            
            # Process structure (folders and embedded files)
            self._process_template(project_dir, structure_data, placeholders, created_paths)
            
            # Return success with project directory
            # print(f"Project '{project_name}' created successfully at: {project_dir}")
            
            # Create readme file if it doesn't exist
            readme_path = os.path.join(project_dir, "README.md")
            if not os.path.exists(readme_path):
                try:
                    from app.utils.utils import create_readme_file
                    readme_content = create_readme_file(project_name, template_name)
                    with open(readme_path, 'w', encoding='utf-8') as f:
                        f.write(readme_content)
                    # print(f"Created README.md file")
                except Exception as e:
                    print(f"Failed to create README.md: {e}")
                    # Non-critical, continue without failing
            
            return True, project_dir
            
        except Exception as e:
            print(f"Error creating project: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Error creating project: {str(e)}"
    
    def _get_structure_data(self, template_data=None, structure_name=None):
        """
        Get the structure data to use for project creation.
        
        Args:
            template_data (dict, optional): The template data dictionary
            structure_name (str, optional): Name of structure to use
            
        Returns:
            list or dict: Structure data
        """
        # print(f"🔍 _get_structure_data: structure_name={structure_name}")
        
        # First try using structure directly from template_data
        if template_data and 'structure' in template_data:
            structure = template_data.get('structure')
            # print(f"Using structure from template data")
            
            # Check if we have a valid structure
            if structure and (isinstance(structure, list) or isinstance(structure, dict)):
                # Convert dict form to list form if needed for consistency
                if isinstance(structure, dict) and 'folders' in structure:
                    structure = structure['folders']
                    
                return structure
            
        # If we get here, try to find structure by name
        if structure_name:
            # print(f"Looking for structure with name: {structure_name}")
            
            # Try to get the structure data
            if hasattr(self, 'template_manager'):
                structure_data = self.template_manager.get_structure(structure_name)
                if structure_data:
                    return structure_data
        
        # If no structure found, check if we have a fallback in template
        template_name = template_data.get('name') if template_data else None
        if template_name:
            # Try to get a structure with a name based on the template
            fallback_names = [
                f"Template_{template_name}",
                template_name
            ]
            
            for fallback_name in fallback_names:
                if hasattr(self, 'template_manager'):
                    structure_data = self.template_manager.get_structure(fallback_name)
                    if structure_data:
                        return structure_data
        
        # If we get here, no structure was found
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
            # print("DEBUG: Structure data is empty or None")
            return False
            
        # Check for dict format with folders key
        if isinstance(structure_data, dict):
            if 'folders' in structure_data and structure_data['folders']:
                # Old format with folders key
                # print("DEBUG: Structure is valid (dict with folders key)")
                return True
            elif any(isinstance(value, dict) for value in structure_data.values()):
                # Dict format with folder objects as values
                # print("DEBUG: Structure is valid (dict with folder objects)")
                return True
            # Check for 'directories' key used in template editor
            elif 'directories' in structure_data and structure_data['directories']:
                # print("DEBUG: Structure is valid (dict with directories key)")
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
                # print("DEBUG: Structure is valid (list with folder items)")
                return True
                
        # print("DEBUG: Structure is not valid")
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
            # print(f"WARNING: Empty structure data")
            return created_paths
            
        # Handle dictionary-based structure format
        if isinstance(structure_data, dict):
            # Create folders from structure
            if 'folders' in structure_data and isinstance(structure_data['folders'], dict):
                folders = structure_data['folders']
                created_paths.extend(self._create_folders_recursive(base_path, folders))
            else:
                # print(f"WARNING: Dictionary structure data missing 'folders' key or not in expected format")
                pass
        
        # Handle list-based structure format (like in the template structure)
        elif isinstance(structure_data, list):
            # print(f"DEBUG: Processing list-based structure with {len(structure_data)} items")
            
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
                            # print(f"Created folder: {folder_path}")
                            
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
                                                # print(f"Created subfolder: {child_path}")
                                                
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
                                                                    # print(f"Created grandchild folder: {grandchild_path}")
                                                                except Exception as e:
                                                                    error_message = f"Failed to create grandchild folder {grandchild_path}: {str(e)}"
                                                                    # print(f"ERROR: {error_message}")
                                                                    self._add_error(error_message)
                                            except Exception as e:
                                                error_message = f"Failed to create subfolder {child_path}: {str(e)}"
                                                # print(f"ERROR: {error_message}")
                                                self._add_error(error_message)
                        except Exception as e:
                            error_message = f"Failed to create folder {folder_path}: {str(e)}"
                            # print(f"ERROR: {error_message}")
                            self._add_error(error_message)
        else:
            # print(f"WARNING: Invalid structure data type: {type(structure_data)}")
            pass
            
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
                # print(f"Created folder: {folder_path}")
                
                # Process subfolders recursively
                if isinstance(sub_folders, dict):
                    sub_path = os.path.join(parent_path, folder_name)
                    sub_created = self._create_folders_recursive(base_path, sub_folders, sub_path)
                    created_paths.extend(sub_created)
            except Exception as e:
                error_message = f"Failed to create folder {folder_path}: {str(e)}"
                # print(f"ERROR: {error_message}")
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
            # print(f"WARNING: Empty structure data")
            return created_paths
        
        # For list-based structures, process using _process_template directly
        if isinstance(structure_data, list):
            # print(f"DEBUG: Processing list-based structure with {len(structure_data)} items")
            return self._process_template(output_path, structure_data, placeholders, created_paths, dry_run)
        
        # Handle dictionary-based structures
        # print(f"DEBUG: Processing dictionary-based structure")
        
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
            # print("WARNING: Invalid or empty structure format")
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
                # print(f"DEBUG: Creating directory from custom structure: {item_path}")
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
        # print(f"DEBUG: Processing template structure of type {type(structure)} with {len(structure) if isinstance(structure, list) else 'unknown'} items")
        
        # Normalize structure format to ensure consistent processing
        normalized_structure = self._normalize_structure_format(structure)
        
        # Process each item in the normalized structure
        for item in normalized_structure:
            # All items should be dictionaries with 'type' and 'name' at this point
            if not isinstance(item, dict) or 'type' not in item or 'name' not in item:
                # print(f"WARNING: Skipping invalid item format after normalization: {item}")
                continue
            
            item_type = item.get('type')
            item_name = item.get('name')
            
            # Apply placeholders to the name
            if placeholders and isinstance(item_name, str):
                item_name = self._replace_placeholders(item_name, placeholders)
                item['name'] = item_name  # Update the item with the processed name
            
            # Final validation of name
            if not item_name or item_name == '[]' or item_name == 'name':
                # print(f"WARNING: Skipping item with empty/invalid name after normalization: {item}")
                continue
            
            # print(f"DEBUG: Processing item: {item_name} of type {item_type}")
            
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
                    # print(f"DEBUG: Creating directory: {folder_path}")
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
                    # print(f"ERROR: Failed to process file {item_name}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                # print(f"WARNING: Unknown item type: {item_type} for {item_name}")
                pass
        
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
            # print(f"DEBUG: Normalizing structure list with {len(structure)} items")
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
                    # print(f"WARNING: Unsupported item format in structure: {item}")
                    if isinstance(item, dict):
                        # print(f"Item keys: {list(item.keys())}")
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
            # print(f"DEBUG: Normalizing structure with 'root' key containing {len(structure['root'])} items")
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
                    # print(f"WARNING: Unsupported item format in structure root: {item}")
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
            # print(f"DEBUG: Normalizing dictionary structure with {len(structure)} keys")
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
        
        # print(f"DEBUG: Normalized structure has {len(normalized)} items")
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
            # print(f"WARNING: Skipping directory with invalid name: {directory_name}")
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
        # print(f"DEBUG: Creating directory from custom structure: {directory_path}")
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
        if placeholders is None:
            placeholders = {}

        if isinstance(item, dict):
            item_name = item.get('name')
            if isinstance(item_name, list):
                if item_name and item_name[0]:
                    item_name = str(item_name[0])
                else:
                    return None
            if not item_name or item_name == '[]' or item_name == 'name':
                return None

            output_name = item_name
            rename_flag = item.get('rename_flag', False)
            uses_project_name = item.get('uses_project_name', False)
            pattern = item.get('pattern', None)
            sequence = item.get('sequence', None)

            # --- Sequence support ---
            if pattern and sequence and "${COUNTER}" in pattern:
                created_paths = []
                for i in range(sequence['start'], sequence['start'] + sequence['count']):
                    local_placeholders = placeholders.copy()
                    local_placeholders['COUNTER'] = str(i).zfill(sequence['padding'])
                    
                    # Handle custom options for this specific item (using nested extraction)
                    def extract_pattern_data(data, depth=0, max_depth=5):
                        """Recursively extract pattern and custom options from nested data"""
                        if depth > max_depth or not isinstance(data, dict):
                            return [], ''
                        
                        found_options = data.get('custom_options', [])
                        found_pattern = data.get('pattern', '')
                        
                        # If we found both, return them
                        if found_options and found_pattern:
                            return found_options, found_pattern
                        
                        # Otherwise, check user_data recursively
                        if 'user_data' in data and isinstance(data['user_data'], dict):
                            nested_options, nested_pattern = extract_pattern_data(data['user_data'], depth + 1, max_depth)
                            if not found_options and nested_options:
                                found_options = nested_options
                            if not found_pattern and nested_pattern:
                                found_pattern = nested_pattern
                        
                        return found_options, found_pattern
                    
                    custom_options, _ = extract_pattern_data(item)
                    if custom_options and "${CUSTOM}" in pattern:
                        # Find the custom value for this specific item
                        item_path = self._get_item_path(parent_output_path, item, placeholders)
                        custom_key = f"{item_path}_CUSTOM"
                        if custom_key in placeholders:
                            local_placeholders['CUSTOM'] = placeholders[custom_key]
                    
                    output_name = self._process_custom_pattern(pattern, local_placeholders, item)
                    file_path = os.path.join(parent_output_path, output_name)
                    
                    if dry_run:
                        created_paths.append(file_path)
                        continue
                    
                    if os.path.exists(file_path) and not self._verify_overwrite(file_path):
                        continue
                    
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    if source_path and os.path.exists(source_path):
                        is_binary = item.get('is_binary', False)
                        if is_binary:
                            try:
                                shutil.copy2(source_path, file_path)
                            except Exception as e:
                                self.logger.error(f"Error copying binary file {source_path} to {file_path}: {e}")
                                continue
                        else:
                            try:
                                with open(source_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                processed_content = self._replace_placeholders(content, local_placeholders)
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(processed_content)
                            except Exception as e:
                                self.logger.error(f"Error processing file {source_path} to {file_path}: {e}")
                                continue
                    else:
                        try:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write("")
                        except Exception as e:
                            self.logger.error(f"Error creating empty file {file_path}: {e}")
                            continue
                    
                    created_paths.append(file_path)
                
                return created_paths
            
            # --- End sequence support ---

            # Original single-file logic (for non-sequence files)
            # Handle custom options for single files/folders
            local_placeholders = placeholders.copy()
            
            # Helper function to recursively search for pattern data
            def extract_pattern_data(data, depth=0, max_depth=5):
                """Recursively extract pattern and custom options from nested data"""
                if depth > max_depth or not isinstance(data, dict):
                    return [], ''
                
                found_options = data.get('custom_options', [])
                found_pattern = data.get('pattern', '')
                
                # If we found both, return them
                if found_options and found_pattern:
                    return found_options, found_pattern
                
                # Otherwise, check user_data recursively
                if 'user_data' in data and isinstance(data['user_data'], dict):
                    nested_options, nested_pattern = extract_pattern_data(data['user_data'], depth + 1, max_depth)
                    if not found_options and nested_options:
                        found_options = nested_options
                    if not found_pattern and nested_pattern:
                        found_pattern = nested_pattern
                
                return found_options, found_pattern
            
            # Extract pattern data from the item (override previous pattern if found)
            custom_options, nested_pattern = extract_pattern_data(item)
            if nested_pattern:
                pattern = nested_pattern
            
            if custom_options and pattern and "${CUSTOM}" in pattern:
                # Find the custom value for this specific item
                item_path = self._get_item_path(parent_output_path, item, placeholders)
                custom_key = f"{item_path}_CUSTOM"
                print(f"DEBUG: Looking for custom value with key: '{custom_key}'")
                print(f"DEBUG: Available placeholders: {list(placeholders.keys())}")
                if custom_key in placeholders:
                    local_placeholders['CUSTOM'] = placeholders[custom_key]
                    print(f"DEBUG: Set local_placeholders['CUSTOM'] = '{placeholders[custom_key]}'")
                elif 'CUSTOM' in placeholders:
                    local_placeholders['CUSTOM'] = placeholders['CUSTOM']
                    print(f"DEBUG: Using global CUSTOM value: '{placeholders['CUSTOM']}'")
                else:
                    print(f"DEBUG: No CUSTOM value found for key '{custom_key}' or global 'CUSTOM'")
            
            # Determine output name - prioritize custom patterns
            if pattern:
                # Use custom pattern with enhanced features (highest priority)
                output_name = self._process_custom_pattern(pattern, local_placeholders, item)
                print(f"DEBUG: Used custom pattern processing, result: '{output_name}'")
            elif "${PROJECT_NAME}" in item_name:
                # Check if the filename contains a placeholder
                output_name = self._replace_placeholders(item_name, local_placeholders)
            elif rename_flag or uses_project_name:
                project_name = local_placeholders.get("PROJECT_NAME", "Unknown")
                name_parts = os.path.splitext(item_name)
                if len(name_parts) == 2:
                    base_name, ext = name_parts
                    if uses_project_name:
                        output_name = f"{project_name}_{base_name}{ext}"
                    else:
                        output_name = f"{base_name}_{project_name}{ext}"
                else:
                    if uses_project_name:
                        output_name = f"{project_name}_{item_name}"
                    else:
                        output_name = f"{item_name}_{project_name}"
            else:
                output_name = item_name

            file_path = os.path.join(parent_output_path, output_name)
            source_path = None
            content = None
            if 'original_path' in item:
                source_path = item['original_path']
            elif 'path' in item:
                source_path = item['path']
            elif 'cached_path' in item:
                source_path = item['cached_path']

            if dry_run:
                return file_path
            if os.path.exists(file_path) and not self._verify_overwrite(file_path):
                return None
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if source_path and os.path.exists(source_path):
                is_binary = item.get('is_binary', False)
                if is_binary:
                    try:
                        shutil.copy2(source_path, file_path)
                        return file_path
                    except Exception as e:
                        self.logger.error(f"Error copying binary file {source_path} to {file_path}: {e}")
                        return None
                else:
                    try:
                        with open(source_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        processed_content = self._replace_placeholders(content, local_placeholders)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(processed_content)
                        return file_path
                    except Exception as e:
                        self.logger.error(f"Error processing file {source_path} to {file_path}: {e}")
                        return None
            elif 'content' in item or content:
                file_content = content or item.get('content', '')
                if placeholders:
                    file_content = self._replace_placeholders(file_content, placeholders)
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_content)
                    return file_path
                except Exception as e:
                    self.logger.error(f"Error writing content to {file_path}: {e}")
                    return None
            else:
                try:
                    with open(file_path, 'w') as f:
                        pass
                    return file_path
                except Exception as e:
                    self.logger.error(f"Error creating empty file {file_path}: {e}")
                    return None
        elif isinstance(item, str):
            file_path = os.path.join(parent_output_path, item)
            if dry_run:
                return file_path
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            try:
                with open(file_path, 'w') as f:
                    pass
                return file_path
            except Exception as e:
                self.logger.error(f"Error creating empty file {file_path}: {e}")
                return None
        else:
            return None

    def _might_contain_placeholders(self, file_path):
        """
        Check if a file might contain placeholders by reading the first few KB.
        Handles both ${PROJECT_NAME} and {{PROJECT_NAME}} formats.
        
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
            
            # Check for common placeholder patterns - both ${NAME} and {{NAME}} formats
            return ('${' in text or 
                   '$PROJECT_NAME' in text or 
                   '$project_name' in text or 
                   '{{' in text or 
                   '{{PROJECT_NAME}}' in text or 
                   '{{project_name}}' in text)
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



    def _extract_sequence_date_from_project_name(self, project_name):
        """
        Extract sequence date information from project name if it contains date sequences.
        
        Args:
            project_name (str): The project name that may contain date sequences
            
        Returns:
            dict or None: Dictionary with date info if found, None otherwise
                {
                    'date': datetime.date object,
                    'date_format': format string used,
                    'position': 'prefix' or 'suffix'
                }
        """
        import re
        import datetime
        
        # Common date patterns to look for in project names
        date_patterns = [
            # YYYY-MM-DD formats
            (r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),
            # YYYYMMDD formats  
            (r'(\d{8})', '%Y%m%d'),
            # MM-DD-YYYY formats
            (r'(\d{2}-\d{2}-\d{4})', '%m-%d-%Y'),
            # DD-MM-YYYY formats
            (r'(\d{2}-\d{2}-\d{4})', '%d-%m-%Y'),
            # YYYY_MM_DD formats
            (r'(\d{4}_\d{2}_\d{2})', '%Y_%m_%d'),
            # MM_DD_YYYY formats
            (r'(\d{2}_\d{2}_\d{4})', '%m_%d_%Y'),
            # DD_MM_YYYY formats
            (r'(\d{2}_\d{2}_\d{4})', '%d_%m_%Y'),
            # YYYY.MM.DD formats
            (r'(\d{4}\.\d{2}\.\d{2})', '%Y.%m.%d'),
            # MM.DD.YYYY formats
            (r'(\d{2}\.\d{2}\.\d{4})', '%m.%d.%Y'),
            # DD.MM.YYYY formats
            (r'(\d{2}\.\d{2}\.\d{4})', '%d.%m.%Y'),
        ]
        
        for pattern, date_format in date_patterns:
            # Check for date at the beginning (prefix)
            prefix_match = re.match(f'^{pattern}_', project_name)
            if prefix_match:
                try:
                    date_str = prefix_match.group(1)
                    parsed_date = datetime.datetime.strptime(date_str, date_format).date()
                    return {
                        'date': parsed_date,
                        'date_format': date_format,
                        'position': 'prefix',
                        'date_string': date_str
                    }
                except ValueError:
                    continue
            
            # Check for date at the end (suffix)
            suffix_match = re.search(f'_{pattern}$', project_name)
            if suffix_match:
                try:
                    date_str = suffix_match.group(1)
                    parsed_date = datetime.datetime.strptime(date_str, date_format).date()
                    return {
                        'date': parsed_date,
                        'date_format': date_format,
                        'position': 'suffix',
                        'date_string': date_str
                    }
                except ValueError:
                    continue
        
        return None

    def _extract_datetime_formats(self, template_data):
        """
        Extract date and time format preferences from template structure
        
        Args:
            template_data: The template data dictionary
            
        Returns:
            tuple: (date_format, time_format) or (None, None) if not found
        """
        def search_structure(structure):
            """Recursively search for date/time formats in structure"""
            for item in structure:
                if isinstance(item, dict):
                    # Check for date_format and time_format in item
                    date_format = item.get('date_format')
                    time_format = item.get('time_format')
                    
                    if date_format or time_format:
                        return date_format, time_format
                    
                    # Check in user_data (nested structures)
                    user_data = item.get('user_data', {})
                    if isinstance(user_data, dict):
                        date_format = user_data.get('date_format')
                        time_format = user_data.get('time_format')
                        
                        if date_format or time_format:
                            return date_format, time_format
                        
                        # Check double-nested user_data
                        nested_user_data = user_data.get('user_data', {})
                        if isinstance(nested_user_data, dict):
                            date_format = nested_user_data.get('date_format')
                            time_format = nested_user_data.get('time_format')
                            
                            if date_format or time_format:
                                return date_format, time_format
                    
                    # Recursively check children
                    children = item.get('children', [])
                    if children:
                        result = search_structure(children)
                        if result != (None, None):
                            return result
            
            return None, None
        
        structure = template_data.get('structure', [])
        return search_structure(structure)

    def _collect_custom_options(self, template_data):
        """
        Collect all custom options needed for this project creation
        
        Args:
            template_data: The template data dictionary
            
        Returns:
            dict: Dictionary mapping custom variable names to selected values, or None if cancelled
        """
        # Try to get custom values from the main app's animated widget first
        try:
            from app.core.app_module_pyqt import ProjectCreatorApp
            app_instance = ProjectCreatorApp.get_instance()
            print(f"DEBUG: ProjectBuilder._collect_custom_options - app_instance found: {app_instance is not None}")
            if app_instance and hasattr(app_instance, 'get_custom_values_from_widget'):
                print(f"DEBUG: ProjectBuilder._collect_custom_options - calling get_custom_values_from_widget()")
                custom_values = app_instance.get_custom_values_from_widget()
                print(f"DEBUG: ProjectBuilder._collect_custom_options - received custom_values: {custom_values}")
                if custom_values:
                    print(f"DEBUG: ProjectBuilder._collect_custom_options - returning custom values from widget: {custom_values}")
                    return custom_values
                else:
                    print(f"DEBUG: ProjectBuilder._collect_custom_options - no custom values from widget, falling back to dialog")
        except Exception as e:
            print(f"Warning: Could not get custom values from animated widget: {e}")
        
        # Fallback to collecting custom options and showing dialog (for compatibility)
        custom_prompts = {}
        
        def collect_from_structure(structure, path=""):
            """Recursively collect custom options from structure"""
            for item in structure:
                if isinstance(item, dict):
                    item_name = item.get('name', '')
                    item_path = f"{path}/{item_name}" if path else item_name
                    
                    # Helper function to recursively search for pattern data
                    def extract_pattern_data(data, depth=0, max_depth=5):
                        """Recursively extract pattern and custom options from nested data"""
                        if depth > max_depth or not isinstance(data, dict):
                            return [], ''
                        
                        found_options = data.get('custom_options', [])
                        found_pattern = data.get('pattern', '')
                        
                        # If we found both, return them
                        if found_options and found_pattern:
                            return found_options, found_pattern
                        
                        # Otherwise, check user_data recursively
                        if 'user_data' in data and isinstance(data['user_data'], dict):
                            nested_options, nested_pattern = extract_pattern_data(data['user_data'], depth + 1, max_depth)
                            if not found_options and nested_options:
                                found_options = nested_options
                            if not found_pattern and nested_pattern:
                                found_pattern = nested_pattern
                        
                        return found_options, found_pattern
                    
                    # Extract pattern data from the item
                    custom_options, pattern = extract_pattern_data(item)
                    
                    # Check for any CUSTOM placeholders in the pattern
                    if custom_options and pattern:
                        import re
                        custom_matches = re.findall(r'\$\{(CUSTOM\d*)\}', pattern)
                        if custom_matches:
                            # Handle both old format (list) and new format (dict)
                            if isinstance(custom_options, dict):
                                # New format - each placeholder has its own options
                                for custom_placeholder in custom_matches:
                                    if custom_placeholder in custom_options:
                                        custom_key = f"{item_path}_{custom_placeholder}"
                                        if custom_key not in custom_prompts:
                                            custom_prompts[custom_key] = {
                                                'item_path': item_path,
                                                'item_name': item_name,
                                                'options': custom_options[custom_placeholder],
                                                'pattern': pattern,
                                                'placeholder': custom_placeholder
                                            }
                            else:
                                # Old format - single list of options, create entries for each placeholder
                                for i, custom_placeholder in enumerate(custom_matches):
                                    custom_key = f"{item_path}_{custom_placeholder}"
                                    if custom_key not in custom_prompts:
                                        # Use different option based on placeholder index
                                        if i < len(custom_options):
                                            option_list = [custom_options[i]]
                                        else:
                                            # If we don't have enough options, use all options for this placeholder
                                            option_list = custom_options
                                        
                                        custom_prompts[custom_key] = {
                                            'item_path': item_path,
                                            'item_name': item_name,
                                            'options': option_list if len(option_list) > 1 else custom_options,
                                            'pattern': pattern,
                                            'placeholder': custom_placeholder
                                        }
                    
                    # Recursively check children
                    children = item.get('children', [])
                    if children:
                        collect_from_structure(children, item_path)
        
        # Collect all custom options needed
        structure = template_data.get('structure', [])
        collect_from_structure(structure)
        
        # If no custom options needed, return empty dict
        if not custom_prompts:
            return {}
        
        # If we reach here, show the fallback dialog
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout
        from PyQt6.QtCore import Qt
        
        class CustomOptionsDialog(QDialog):
            def __init__(self, parent, custom_prompts):
                super().__init__(parent)
                self.custom_prompts = custom_prompts
                self.selected_values = {}
                self.init_ui()
            
            def init_ui(self):
                from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE
                self.setWindowTitle("Custom Options")
                self.setMinimumSize(400, 300)
                self.setStyleSheet(f"""
                    QDialog {{
                        background-color: {colors['bg']};
                        color: {colors['text']};
                    }}
                """)
                
                layout = QVBoxLayout(self)
                layout.setContentsMargins(20, 20, 20, 20)
                layout.setSpacing(15)
                
                title = QLabel("Select Custom Options for Project Creation")
                title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {colors['text']};")
                layout.addWidget(title)
                
                self.combos = {}
                for key, prompt_data in self.custom_prompts.items():
                    item_label = QLabel(f"For '{prompt_data['item_path']}':")
                    item_label.setStyleSheet(f"color: {colors['text']};")
                    layout.addWidget(item_label)
                    
                    combo = QComboBox()
                    combo.addItems(prompt_data['options'])
                    # Use the standard combo box styling for consistency
                    from app.ui.color_scheme_pyqt import COMBOBOX_STYLE
                    combo.setStyleSheet(COMBOBOX_STYLE)
                    
                    # Apply hover delegate for proper blue hover effects
                    try:
                        from app.ui.custom_delegates import apply_hover_delegate
                        apply_hover_delegate(combo)
                    except ImportError:
                        pass
                    
                    self.combos[key] = combo
                    layout.addWidget(combo)
                
                # Buttons
                button_layout = QHBoxLayout()
                cancel_btn = QPushButton("Cancel")
                cancel_btn.clicked.connect(self.reject)
                cancel_btn.setStyleSheet(BUTTON_STYLE)
                
                ok_btn = QPushButton("OK")
                ok_btn.clicked.connect(self.accept)
                ok_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
                ok_btn.setDefault(True)
                
                button_layout.addWidget(cancel_btn)
                button_layout.addStretch()
                button_layout.addWidget(ok_btn)
                layout.addLayout(button_layout)
            
            def get_selected_values(self):
                return {key: combo.currentText() for key, combo in self.combos.items()}
        
        # Show dialog to collect custom values
        dialog = CustomOptionsDialog(None, custom_prompts)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_selected_values()
        else:
            return None  # User cancelled

    def _create_placeholders(self, project_name, custom_values=None, date_format=None, time_format=None, sequence_date_info=None):
        """
        Create placeholders dictionary for variable replacement
        
        Args:
            project_name: Name of the project
            custom_values: Dictionary of custom values selected by user
            date_format: Custom date format string (e.g., "YYYY_MM_DD (2024_01_15)")
            time_format: Custom time format string (e.g., "HH_MM_SS (14_30_22)")
            sequence_date_info: Dictionary with sequence date info if project name contains date sequences
            
        Returns:
            dict: Dictionary of placeholder replacements
        """
        import datetime
        
        # Determine which date/time to use
        if sequence_date_info and sequence_date_info.get('date'):
            # Use the sequence date for both date and time placeholders
            sequence_date = sequence_date_info['date']
            # Create datetime object from date (use current time for time component)
            current_time = datetime.datetime.now().time()
            now = datetime.datetime.combine(sequence_date, current_time)
            print(f"DEBUG: Using sequence date for placeholders: {sequence_date}")
        else:
            # Use current date/time as normal
            now = datetime.datetime.now()
        
        # Format date based on custom format
        if date_format:
            if "YYYYMMDD" in date_format:
                date_str = now.strftime('%Y%m%d')
            elif "YYYY_MM_DD" in date_format:
                date_str = now.strftime('%Y_%m_%d')
            elif "YYYY-MM-DD" in date_format:
                date_str = now.strftime('%Y-%m-%d')
            elif "YYYY.MM.DD" in date_format:
                date_str = now.strftime('%Y.%m.%d')
            elif "YYYY MM DD" in date_format:
                date_str = now.strftime('%Y %m %d')
            elif "MM_DD_YYYY" in date_format:
                date_str = now.strftime('%m_%d_%Y')
            elif "MM-DD-YYYY" in date_format:
                date_str = now.strftime('%m-%d-%Y')
            elif "MM.DD.YYYY" in date_format:
                date_str = now.strftime('%m.%d.%Y')
            elif "MM DD YYYY" in date_format:
                date_str = now.strftime('%m %d %Y')
            elif "DD_MM_YYYY" in date_format:
                date_str = now.strftime('%d_%m_%Y')
            elif "DD-MM-YYYY" in date_format:
                date_str = now.strftime('%d-%m-%Y')
            elif "DD.MM.YYYY" in date_format:
                date_str = now.strftime('%d.%m.%Y')
            elif "DD MM YYYY" in date_format:
                date_str = now.strftime('%d %m %Y')
            else:
                date_str = now.strftime('%Y%m%d')  # Default
        else:
            date_str = now.strftime('%Y%m%d')  # Default
        
        # Format time based on custom format
        if time_format:
            if "HHMMSS" in time_format:
                time_str = now.strftime('%H%M%S')
            elif "HH_MM_SS" in time_format:
                time_str = now.strftime('%H_%M_%S')
            elif "HH-MM-SS" in time_format:
                time_str = now.strftime('%H-%M-%S')
            elif "HH.MM.SS" in time_format:
                time_str = now.strftime('%H.%M.%S')
            elif "HH MM SS" in time_format:
                time_str = now.strftime('%H %M %S')
            elif "HHMM" in time_format:
                time_str = now.strftime('%H%M')
            elif "HH_MM" in time_format:
                time_str = now.strftime('%H_%M')
            elif "HH-MM" in time_format:
                time_str = now.strftime('%H-%M')
            elif "HH.MM" in time_format:
                time_str = now.strftime('%H.%M')
            elif "HH MM" in time_format:
                time_str = now.strftime('%H %M')
            else:
                time_str = now.strftime('%H%M%S')  # Default
        else:
            time_str = now.strftime('%H%M%S')  # Default
        
        placeholders = {
            'PROJECT_NAME': project_name,
            'DATE': date_str,
            'TIME': time_str,
            'COUNTER': '001'  # Default counter value
        }
        
        # Add custom values if provided
        if custom_values:
            print(f"DEBUG: Processing custom_values in _create_placeholders: {custom_values}")
            for key, value in custom_values.items():
                print(f"DEBUG: Processing custom value - key: '{key}', value: '{value}'")
                # Extract the placeholder type from the key
                if '_CUSTOM' in key:
                    # Handle both legacy CUSTOM and new CUSTOM1, CUSTOM2, etc.
                    placeholder_part = key.split('_')[-1]  # Gets 'CUSTOM', 'CUSTOM1', etc.
                    
                    # Set the specific placeholder
                    placeholders[placeholder_part] = value
                    print(f"DEBUG: Set placeholders['{placeholder_part}'] = '{value}'")
                    
                    # For backwards compatibility, also set generic CUSTOM if it's the base CUSTOM
                    if placeholder_part == 'CUSTOM':
                        placeholders['CUSTOM'] = value
                        print(f"DEBUG: Set placeholders['CUSTOM'] = '{value}' (backwards compatibility)")
                    
                    # Also store with the full key for specific replacements
                    placeholders[key] = value
                    print(f"DEBUG: Set placeholders['{key}'] = '{value}'")
        
        print(f"DEBUG: Final placeholders in _create_placeholders: {placeholders}")
        return placeholders

    def _replace_placeholders(self, text, placeholders):
        """
        Replace placeholders in text with actual values
        
        Args:
            text: Text containing placeholders
            placeholders: Dictionary of placeholder replacements
            
        Returns:
            str: Text with placeholders replaced
        """
        if not text or not placeholders:
            return text
        
        result = text
        for key, value in placeholders.items():
            placeholder = f"${{{key}}}"
            result = result.replace(placeholder, str(value))
        
        return result

    def _process_custom_pattern(self, pattern, placeholders, item):
        """
        Process custom pattern with enhanced features:
        - Automatic extension preservation for files
        - Date/time placement options
        - Separator-aware formatting
        
        Args:
            pattern: The pattern string
            placeholders: Dictionary of placeholder replacements
            item: The item dictionary containing metadata
            
        Returns:
            str: Processed filename/foldername
        """
        print(f"DEBUG: _process_custom_pattern called with pattern: '{pattern}'")
        print(f"DEBUG: _process_custom_pattern placeholders: {placeholders}")
        print(f"DEBUG: _process_custom_pattern item type: {item.get('type')}")
        print(f"DEBUG: _process_custom_pattern item name: {item.get('name')}")
        print(f"DEBUG: _process_custom_pattern item original_name: {item.get('original_name')}")
        
        result = pattern
        
        # Get separator information from item
        separator = item.get('separator', '_')  # Default to underscore
        print(f"DEBUG: _process_custom_pattern - using separator: '{separator}'")
        
        # Check if user manually added separators in pattern
        manual_separators = self._detect_manual_separators_in_pattern(pattern)
        print(f"DEBUG: _process_custom_pattern - manual separators detected: {manual_separators}")
        
        # Auto-adjust date/time formats to match separator if not manually set
        if not manual_separators and separator != "_":
            # Update placeholders with separator-adjusted formats
            if 'DATE' in placeholders:
                placeholders = placeholders.copy()  # Don't modify original
                if separator == "-":
                    # Convert date to dash format
                    date_val = placeholders['DATE']
                    if len(date_val) == 8 and date_val.isdigit():  # YYYYMMDD format
                        placeholders['DATE'] = f"{date_val[:4]}-{date_val[4:6]}-{date_val[6:]}"
                elif separator == ".":
                    # Convert date to dot format
                    date_val = placeholders['DATE']
                    if len(date_val) == 8 and date_val.isdigit():  # YYYYMMDD format
                        placeholders['DATE'] = f"{date_val[:4]}.{date_val[4:6]}.{date_val[6:]}"
                elif separator == " ":
                    # Convert date to space format
                    date_val = placeholders['DATE']
                    if len(date_val) == 8 and date_val.isdigit():  # YYYYMMDD format
                        placeholders['DATE'] = f"{date_val[:4]} {date_val[4:6]} {date_val[6:]}"
            
            if 'TIME' in placeholders:
                if 'DATE' not in placeholders:  # Only copy if not already copied above
                    placeholders = placeholders.copy()
                if separator == "-":
                    # Convert time to dash format
                    time_val = placeholders['TIME']
                    if len(time_val) == 6 and time_val.isdigit():  # HHMMSS format
                        placeholders['TIME'] = f"{time_val[:2]}-{time_val[2:4]}-{time_val[4:]}"
                elif separator == ".":
                    # Convert time to dot format
                    time_val = placeholders['TIME']
                    if len(time_val) == 6 and time_val.isdigit():  # HHMMSS format
                        placeholders['TIME'] = f"{time_val[:2]}.{time_val[2:4]}.{time_val[4:]}"
                elif separator == " ":
                    # Convert time to space format
                    time_val = placeholders['TIME']
                    if len(time_val) == 6 and time_val.isdigit():  # HHMMSS format
                        placeholders['TIME'] = f"{time_val[:2]} {time_val[2:4]} {time_val[4:]}"
        
        # Handle date/time placement
        datetime_prefix = item.get('datetime_prefix', False)
        
        if datetime_prefix and ('${DATE}' in result or '${TIME}' in result):
            # Extract date/time and place at beginning
            date_str = placeholders.get('DATE', '')
            time_str = placeholders.get('TIME', '')
            
            datetime_part = ""
            if '${DATE}' in result:
                datetime_part += date_str
            if '${TIME}' in result:
                if datetime_part:
                    datetime_part += separator
                datetime_part += time_str
            
            # Remove date/time placeholders from pattern
            result = result.replace('${DATE}', '').replace('${TIME}', '')
            # Clean up multiple consecutive separators
            while f'{separator}{separator}' in result:
                result = result.replace(f'{separator}{separator}', separator)
            # Clean up leading/trailing separators
            result = result.strip(separator)
            # Add datetime at the beginning
            result = f"{datetime_part}{separator}{result}" if result else datetime_part
        
        # Add BASE placeholder if it's used in the pattern
        if '${BASE}' in result:
            placeholders = placeholders.copy()  # Don't modify original
            
            # Get the base name (original filename without extension)
            original_name = item.get('original_name') or item.get('name', '')
            if original_name:
                if '.' in original_name:
                    base_name, _ = os.path.splitext(original_name)
                    placeholders['BASE'] = base_name
                    print(f"DEBUG: _process_custom_pattern - Added BASE placeholder: '{base_name}' from '{original_name}'")
                else:
                    # No extension, use the whole name as base
                    placeholders['BASE'] = original_name
                    print(f"DEBUG: _process_custom_pattern - Added BASE placeholder: '{original_name}' (no extension)")
            else:
                # Fallback if no original name available
                placeholders['BASE'] = 'filename'
                print(f"DEBUG: _process_custom_pattern - Added fallback BASE placeholder: 'filename'")
        
        # Replace remaining placeholders
        result = self._replace_placeholders(result, placeholders)
        
        # Handle automatic extension preservation for files
        if item.get('type') == 'file':
            original_name = item.get('original_name') or item.get('name', '')
            print(f"DEBUG: _process_custom_pattern - file processing, original_name: '{original_name}'")
            if '.' in original_name:
                _, ext = os.path.splitext(original_name)
                print(f"DEBUG: _process_custom_pattern - extracted extension: '{ext}'")
                print(f"DEBUG: _process_custom_pattern - result before extension: '{result}'")
                # Only add extension if not already present
                if not result.endswith(ext):
                    result += ext
                    print(f"DEBUG: _process_custom_pattern - added extension, result: '{result}'")
                else:
                    print(f"DEBUG: _process_custom_pattern - extension already present")
            else:
                print(f"DEBUG: _process_custom_pattern - no extension found in original_name")
        
        print(f"DEBUG: _process_custom_pattern - final result: '{result}'")
        return result
    
    def _detect_manual_separators_in_pattern(self, pattern):
        """Detect if user has manually added separators in the pattern"""
        import re
        variables = re.findall(r'\$\{[A-Z_]+\}', pattern)
        if len(variables) < 2:
            return False
        
        # Check for separators between consecutive variables
        for i in range(len(variables) - 1):
            var1_end = pattern.find(variables[i]) + len(variables[i])
            var2_start = pattern.find(variables[i + 1], var1_end)
            between_text = pattern[var1_end:var2_start]
            if between_text.strip():  # If there's text between variables
                return True
        return False

    def _get_item_path(self, parent_path, item, placeholders):
        """
        Get the item path for custom option lookup
        
        Args:
            parent_path: The parent directory path
            item: The item dictionary
            placeholders: Dictionary of placeholder replacements
            
        Returns:
            str: The item path for custom option lookup
        """
        item_name = item.get('name', '')
        if isinstance(item_name, list):
            if item_name and item_name[0]:
                item_name = item_name[0]
            else:
                item_name = 'unnamed'
        
        # Replace placeholders in the item name for path construction
        if placeholders:
            item_name = self._replace_placeholders(item_name, placeholders)
        
        # Get relative path from project root
        # This is a simplified version - in practice you might need more sophisticated path tracking
        return item_name

    def _structure_contains_files(self, structure_data):
        """
        Check if structure contains embedded files (to avoid duplication)
        
        Args:
            structure_data: The structure data to check
            
        Returns:
            bool: True if structure contains files, False otherwise
        """
        if not structure_data:
            return False
            
        def check_items(items):
            """Recursively check items for files"""
            if not items:
                return False
                
            for item in items:
                if isinstance(item, dict):
                    # Check if this item is a file
                    if item.get('type') == 'file':
                        return True
                    
                    # Check children recursively
                    children = item.get('children', [])
                    if children and check_items(children):
                        return True
            
            return False
        
        # Handle different structure formats
        if isinstance(structure_data, list):
            return check_items(structure_data)
        elif isinstance(structure_data, dict):
            if 'folders' in structure_data:
                return check_items(structure_data['folders'])
            else:
                return check_items(list(structure_data.values()))
        
        return False

    def _process_files_array(self, project_dir, files_array, placeholders, use_cached_files=True, template_name=None):
        """
        Process an array of files, copying them to the project directory with placeholders applied
        
        Args:
            project_dir: The project directory to copy files to
            files_array: Array of file information dictionaries
            placeholders: Dictionary of placeholder replacements
            use_cached_files: Whether to use cached files if available
            template_name: Name of the template (for caching)
            
        Returns:
            tuple: (success, copied_files_list)
        """
        if not files_array:
            return True, []
            
        copied_files = []
        
        try:
            for file_info in files_array:
                if not isinstance(file_info, dict):
                    continue
                    
                file_name = file_info.get('file_name', '')
                folder = file_info.get('folder', '')
                original_path = file_info.get('original_path', '')
                cached_path = file_info.get('cached_path', '')
                is_binary = file_info.get('is_binary', False)
                rename_flag = file_info.get('rename_flag', False)
                uses_project_name = file_info.get('uses_project_name', False)
                
                if not file_name:
                    continue
                
                # Determine source path - prefer cached if available and use_cached_files is True
                source_path = None
                if use_cached_files and cached_path and os.path.exists(cached_path):
                    source_path = cached_path
                elif original_path and os.path.exists(original_path):
                    source_path = original_path
                
                if not source_path:
                    # print(f"Warning: Could not find source file for {file_name}")
                    continue
                
                # Build destination path
                folder_path = folder.rstrip('/') if folder else ''
                dest_dir = os.path.join(project_dir, folder_path) if folder_path else project_dir
                
                # Apply placeholders to filename if needed
                final_filename = file_name
                if rename_flag or uses_project_name or '${' in file_name:
                    final_filename = self._replace_placeholders(file_name, placeholders)
                
                dest_path = os.path.join(dest_dir, final_filename)
                
                # Create destination directory
                os.makedirs(dest_dir, exist_ok=True)
                
                # Copy the file
                try:
                    if is_binary:
                        # Binary file - direct copy
                        shutil.copy2(source_path, dest_path)
                    else:
                        # Text file - process placeholders in content
                        with open(source_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Apply placeholders to content
                        processed_content = self._replace_placeholders(content, placeholders)
                        
                        with open(dest_path, 'w', encoding='utf-8') as f:
                            f.write(processed_content)
                    
                    copied_files.append(dest_path)
                    
                except Exception as e:
                    # print(f"Error copying file {file_name}: {e}")
                    continue
            
            return True, copied_files
            
        except Exception as e:
            return False, f"Error processing files array: {str(e)}"

    def batch_create_projects(self, project_names, template_name=None, structure_name=None, 
                            output_dir=None, template_data=None, use_cached_files=True):
        """
        Create multiple projects in batch from a template
        
        Args:
            project_names (list): List of project names to create
            template_name (str, optional): Name of the template to use
            structure_name (str, optional): Name of the structure to use
            output_dir (str): Directory where projects should be created
            template_data (dict, optional): Template data dictionary
            use_cached_files (bool, optional): Whether to use cached files
            
        Returns:
            dict: Results of batch creation with format:
                {
                    "successful_count": int,
                    "total_count": int,
                    "results": [(project_name, success, path_or_error), ...]
                }
        """
        if not project_names:
            return {"error": "No project names provided", "successful_count": 0, "total_count": 0}
        
        if not output_dir:
            return {"error": "No output directory provided", "successful_count": 0, "total_count": 0}
        
        # Initialize results tracking
        results = []
        successful_count = 0
        total_count = len(project_names)
        
        # Show progress window if we have many projects
        progress_window = None
        if total_count > 1:
            try:
                progress_window = BatchProgressWindow(total_count)
                progress_window.show()
                QApplication.processEvents()
            except Exception as e:
                print(f"Warning: Could not create progress window: {e}")
        
        # Create each project
        for i, project_name in enumerate(project_names):
            try:
                # Update progress
                if progress_window:
                    progress_window.update_status(f"Creating project '{project_name}'...")
                    progress_window.update_progress(i)
                    QApplication.processEvents()
                
                # Create the individual project
                success, result = self.create_project(
                    project_name=project_name,
                    output_dir=output_dir,
                    template_file=template_data,
                    project_type="Standard",
                    structure_name=structure_name,
                    create_backup=True,
                    use_cached_files=use_cached_files
                )
                
                if success:
                    successful_count += 1
                    # Handle different result formats
                    if isinstance(result, dict):
                        project_path = result.get("project_dir", output_dir)
                        results.append((project_name, True, result))
                    else:
                        # Result is a path string
                        results.append((project_name, True, result))
                else:
                    # Failed to create project
                    results.append((project_name, False, result))
                    
            except Exception as e:
                # Exception during project creation
                error_msg = f"Exception during creation: {str(e)}"
                results.append((project_name, False, error_msg))
                print(f"Error creating project '{project_name}': {e}")
        
        # Update final progress
        if progress_window:
            progress_window.update_progress(total_count)
            progress_window.update_status(f"Completed: {successful_count}/{total_count} projects created")
            QApplication.processEvents()
            
            # Close progress window after a short delay
            QTimer.singleShot(1000, progress_window.close)
        
        # Return results in the expected format
        return {
            "successful_count": successful_count,
            "total_count": total_count,
            "results": results
        }

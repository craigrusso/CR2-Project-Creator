#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import datetime
import shutil
import time
import hashlib

from app.utils.utils import save_json_file, get_config_paths
from app.constants import PROJECT_TYPE_TO_STRUCTURE

class TemplateOperations:
    """
    Operations for managing templates (create, read, update, delete)
    """
    
    def __init__(self):
        """Initialize template operations"""
        self.paths = get_config_paths()
        
        # Initialize templates list
        self.templates = {}
        
        # Add flag for auto-creating structure files (default to false)
        self.auto_create_structure = False
        
        # Try to load templates if needed
        try:
            self.load_templates()
        except Exception as e:
            print(f"Warning: Could not load templates: {e}")
        
        self.preferences = getattr(self, 'preferences', {})
        
        # Ensure we have a valid template cache directory
        if 'templates_cache_dir' not in self.paths or not self.paths.get('templates_cache_dir'):
            try:
                # Try to get cache location from preferences first
                from app.utils.cache_preferences import CachePreferences
                import os  # Import os module here
                cache_prefs = CachePreferences()
                self.paths['templates_cache_dir'] = cache_prefs.get_cache_location()
                print(f"DEBUG: Set templates_cache_dir from cache preferences: {self.paths['templates_cache_dir']}")
            except Exception as e:
                print(f"WARNING: Failed to get cache location from preferences: {e}")
                # Fallback to a default location in user's home directory
                import os  # Import os module here
                default_cache_dir = os.path.join(os.path.expanduser("~"), ".echelon", "template_cache")
                self.paths['templates_cache_dir'] = default_cache_dir
                print(f"DEBUG: Set templates_cache_dir to default location: {default_cache_dir}")
            
            # Ensure the cache directory exists
            os.makedirs(self.paths['templates_cache_dir'], exist_ok=True)
        
        # Initialize file cache manager
        from app.utils.file_cache_manager import FileCacheManager
        cache_dir = self.paths.get('templates_cache_dir')
        if cache_dir:
            self.file_cache_manager = FileCacheManager(cache_dir)
        else:
            print("Warning: No template cache directory specified in paths")
            self.file_cache_manager = None
    
    def get_default_structure(self, project_type):
        """Get the default directory structure for a project type"""
        from app.constants import DEFAULT_STRUCTURES
        structure_key = PROJECT_TYPE_TO_STRUCTURE.get(project_type, "Video Editing - Basic")
        
        # If structure_key is not in DEFAULT_STRUCTURES, use a fallback
        if structure_key not in DEFAULT_STRUCTURES:
            # Try different fallback keys based on common values
            if structure_key == "Basic":
                structure_key = "Video Editing - Basic"
            elif structure_key == "Standard":
                structure_key = "Video Editing - Standard"
            else:
                # Default fallback to a structure that definitely exists
                structure_key = "Video Editing - Basic"
        
        # Return the structure or an empty list as last resort
        return DEFAULT_STRUCTURES.get(structure_key, [])
    
    def get_structure(self, structure_name):
        """Get the folder structure for a template."""
        from app.constants import DEFAULT_STRUCTURES
        print(f"DEBUG: get_structure called with structure_name='{structure_name}'")
        
        if not structure_name:
            print("DEBUG: No structure name provided, returning empty structure")
            return []
        
        # Check if it's a built-in structure
        structure_name_lower = structure_name.lower()
        for default_name in DEFAULT_STRUCTURES.keys():
            if structure_name_lower == default_name.lower():
                print(f"DEBUG: Found built-in structure: {default_name}")
                return DEFAULT_STRUCTURES[default_name]
        
        # Try with and without the Template_ prefix, and with spaces replaced by underscores
        structure_names_to_try = [structure_name]
        
        # If the name starts with Template_, try also without it
        if structure_name.startswith('Template_'):
            structure_names_to_try.append(structure_name[9:])  # Remove Template_ prefix
        # If the name doesn't start with Template_, try also with it
        else:
            structure_names_to_try.append(f'Template_{structure_name}')
        
        # Add versions with spaces replaced by underscores
        space_versions = []
        for name in structure_names_to_try:
            if ' ' in name:
                space_versions.append(name.replace(' ', '_'))
            elif '_' in name:
                space_versions.append(name.replace('_', ' '))
        structure_names_to_try.extend(space_versions)
        
        print(f"DEBUG: Trying structure names: {structure_names_to_try}")
        
        # Check custom structures for all variations
        for name_to_try in structure_names_to_try:
            # Check in self.custom_structures first (in-memory cache)
            if name_to_try in self.custom_structures:
                print(f"DEBUG: Found custom structure in memory: {name_to_try}")
                # Return the 'directories' field if it exists, otherwise the whole structure
                if 'directories' in self.custom_structures[name_to_try]:
                    return self.custom_structures[name_to_try]['directories']
                return self.custom_structures[name_to_try]
            
            # Check on disk
            custom_structure_path = os.path.join(self.paths["custom_structures_dir"], f"{name_to_try}.json")
            if os.path.exists(custom_structure_path):
                try:
                    with open(custom_structure_path, 'r') as f:
                        structure_data = json.load(f)
                        print(f"DEBUG: Found custom structure on disk: {name_to_try}")
                        # Return the 'directories' field if it exists, otherwise the whole structure
                        if 'directories' in structure_data:
                            return structure_data['directories']
                        return structure_data
                except Exception as e:
                    print(f"Error loading structure {name_to_try}: {e}")
        
        print(f"DEBUG: Structure not found: {structure_name}")
        return []
    
    def filter_templates(self, search_term=None, category=None):
        """Filter templates based on search term and category"""
        filtered_templates = []
        
        for template in self.templates:
            # Filter by search term if specified
            if search_term and search_term.lower() not in template.get("name", "").lower():
                continue
                
            filtered_templates.append(template)
            
        return filtered_templates
    
    def get_template(self, template_name):
        """Get a template by name"""
        if not template_name:
            print(f"DEBUG: get_template called with empty name")
            return None
            
        # Ensure templates is a list
        if not isinstance(self.templates, list):
            print(f"WARNING: self.templates is not a list, it's a {type(self.templates)}")
            return None
            
        # Try to find the template by exact name
        for template in self.templates:
            # Make sure template is a dict before using get()
            if not isinstance(template, dict):
                print(f"WARNING: Template item is not a dict, it's a {type(template)}: {template}")
                continue
                
            if template.get("name") == template_name:
                return template
                
        # If not found with exact match, try case-insensitive match
        for template in self.templates:
            # Make sure template is a dict before using get()
            if not isinstance(template, dict):
                continue
                
            if template.get("name", "").lower() == template_name.lower():
                return template
                
        print(f"DEBUG: Template not found: {template_name}")
        return None
        
    def sanitize_filename(self, filename):
        """
        Sanitize a filename for cross-platform compatibility.
        Replaces unsafe characters with safe ones.
        """
        # Replace characters not allowed in filenames across platforms
        unsafe_chars = [":", "/", "\\", "?", "*", "\"", "<", ">", "|", "'"]
        safe_filename = filename
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, "-")
        
        # Replace spaces with underscores
        safe_filename = safe_filename.replace(" ", "_")
        
        # Trim to a reasonable length
        if len(safe_filename) > 180:
            # Keep extension if any
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:175] + ext
        
        return safe_filename

    def create_template_directory(self, name, source_dir, description=""):
        """Create a template directory structure from a source directory"""
        # Create readable directory name from template name
        dirname = self.sanitize_filename(name)
        
        # Generate the template directory path
        template_dir = os.path.join(self.paths["templates_dir"], dirname)
        
        # Create the directory if it doesn't exist
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)
        
        # Create the template JSON file
        template_file = os.path.join(template_dir, "template.json")
        
        # Create the template data
        template_data = {
            "name": name,
            "description": description or f"Template based on {os.path.basename(source_dir)}",
            "type": "template",
            "path": source_dir
        }
        
        # Write the template JSON file
        try:
            with open(template_file, 'w') as f:
                json.dump(template_data, f, indent=2)
        except Exception as e:
            print(f"Error creating template directory: {e}")
            return False
            
        return True
    
    def _validate_template(self, template):
        """Validate template data"""
        # Check for required fields
        required_fields = ["name", "path", "type"]
        
        for field in required_fields:
            if field not in template:
                print(f"Error: Missing required field '{field}' in template")
                return False
                
        # Check that name and path are not empty
        if not template.get("name") or not template.get("path"):
            print("Error: Template name or path cannot be empty")
            return False
            
        # Check if structure is present and log its status
        if "structure" in template:
            print(f"INFO: Template '{template['name']}' has a folder structure attached")
            structure_count = self._count_structure_items(template["structure"])
            print(f"INFO: Structure contains {structure_count} items")
        else:
            print(f"INFO: Template '{template['name']}' has no folder structure attached")
            
        return True
        
    def _count_structure_items(self, structure):
        """Count items in a structure to help with debugging"""
        if not structure or not isinstance(structure, list):
            return 0
            
        count = 0
        for item in structure:
            if isinstance(item, dict):
                count += len(item)
                # Count nested items
                for key, value in item.items():
                    if isinstance(value, list):
                        count += self._count_structure_items(value)
        
        return count
        
    def save_folders(self):
        """Save template folders to disk"""
        # This is a dummy implementation to avoid errors when called
        # The actual folder saving is implemented in the TemplateManager class
        print("[DEBUG] TemplateOperations.save_folders called - this is a stub implementation")
        
        # If we have a folders attribute, try to save it
        if hasattr(self, 'folders') and self.folders:
            try:
                folders_path = os.path.join(self.paths["templates_dir"], "folders.json")
                with open(folders_path, 'w') as f:
                    json.dump(self.folders, f, indent=2)
                print(f"[DEBUG] Saved {len(self.folders)} folders to {folders_path}")
                return True
            except Exception as e:
                print(f"[ERROR] Failed to save folders: {e}")
                return False
        
        return False
        
    def save_template(self, template_name, structure=None, template_data=None, source_files=None, category=None, 
                       description=None, cache_files=True, is_update=False, original_name=None):
        """
        Save a template with structure
        
        Args:
            template_name: Name of the template
            structure: Structure data (dictionary)
            template_data: Optional additional template data
            source_files: Optional list of source files to include
            category: Optional category for the template
            description: Optional description
            cache_files: Whether to cache files
            is_update: Whether this is an update to an existing template
            original_name: Original name of the template if being renamed
            
        Returns:
            bool: Success status
        """
        # Import required modules
        import os
        
        print(f"[DEBUG] TemplateOperations: save_template called with name={template_name}, structure={type(structure)}")
        
        # Normalize template name (use underscores instead of spaces)
        template_file_name = template_name.replace(' ', '_')
        
        # If this is an update and we have an original name, use that for the file path
        # to maintain the same file name unless explicitly renamed
        original_file_name = None
        if is_update and original_name:
            original_file_name = original_name.replace(' ', '_')
            
        # Create the template dictionary
        template = {}
        
        # If template_data is provided, use it as the base
        if template_data and isinstance(template_data, dict):
            template = template_data.copy()
        
        # Ensure template has required fields
        template['name'] = template_name
        template['description'] = template.get('description', description or 'Template created with structure editor')
        template['category'] = template.get('category', category or 'Custom')
        template['type'] = template.get('type', 'Standard')
        
        # Add creation and modification dates
        current_time = time.time()
        template['created'] = template.get('created', current_time)
        template['modified'] = current_time
        template['tags'] = template.get('tags', [])
        template['date_created'] = template.get('date_created', datetime.datetime.now().isoformat())
        template['date_modified'] = datetime.datetime.now().isoformat()
        
        # Add structure to template
        template['structure'] = structure
        
        # Ensure file_cache_manager is initialized
        if cache_files and not self.file_cache_manager:
            # Try to initialize file_cache_manager
            from app.utils.file_cache_manager import FileCacheManager
            import os  # Import os module here
            cache_dir = self.paths.get('templates_cache_dir')
            if cache_dir:
                self.file_cache_manager = FileCacheManager(cache_dir)
                print(f"[DEBUG] TemplateOperations: Initialized file_cache_manager with cache_dir={cache_dir}")
            else:
                print("[WARNING] TemplateOperations: No template cache directory specified in paths")
                cache_files = False
        
        # Extract files from the structure and add them to the files array
        template['files'] = template.get('files', [])
        if structure:
            # Create a files array to collect all files from the structure
            files_array = []
            self._extract_files_from_structure(structure, files_array)
            
            # If the structure contains files, add them to the files array after removing duplicates
            if files_array:
                print(f"[DEBUG] TemplateOperations: Extracted {len(files_array)} files from structure")
                
                # Create a set of file names to avoid duplicates
                existing_file_names = {f.get('file_name') for f in template['files']}
                
                # Add files from the structure to the template's files array if not already there
                for file_info in files_array:
                    if file_info.get('file_name') not in existing_file_names:
                        template['files'].append(file_info)
                        existing_file_names.add(file_info.get('file_name'))
                
                # Cache the files if needed
                if cache_files and self.file_cache_manager:
                    print(f"[DEBUG] TemplateOperations: Caching {len(files_array)} files from structure")
                    for file_data in files_array:
                        original_path = file_data.get('original_path')
                        if original_path and os.path.exists(original_path):
                            # Cache the file
                            cached_path = self.file_cache_manager.cache_file(
                                original_path,
                                template_file_name,
                                folder_path=file_data.get('folder', ''),
                                rename_flag=file_data.get('rename_flag', False),
                                file_metadata=file_data
                            )
                            # Update the file_data with cached_path
                            if cached_path:
                                file_data['cached_path'] = cached_path
        
        # Clean up the structure to remove unnecessary file details
        if structure:
            self._clean_structure_files(structure)
        
        # Process source files if provided
        if source_files and isinstance(source_files, list):
            # Create a cache for template files if caching is enabled
            if cache_files and self.file_cache_manager:
                if template_name:
                    # Normalize cache name
                    cache_name = template_file_name.strip()
                    
                    for file_data in source_files:
                        if isinstance(file_data, str):
                            # For simple string paths
                            cached_path = self.file_cache_manager.cache_file(file_data, cache_name)
                            if cached_path:
                                template['files'].append({
                                    'file_name': os.path.basename(file_data),
                                    'original_path': file_data,
                                    'cached_path': cached_path
                                })
                        else:
                            # For file data dictionaries
                            original_path = file_data.get('original_path') or file_data.get('path')
                            if original_path and os.path.exists(original_path):
                                # Cache the file
                                cached_path = self.file_cache_manager.cache_file(
                                    original_path,
                                    cache_name,
                                    folder_path=file_data.get('folder', ''),
                                    rename_flag=file_data.get('rename_flag', False),
                                    file_metadata=file_data
                                )
                                # Update the cached_path in the file_data
                                if cached_path:
                                    file_data['cached_path'] = cached_path
                                # Add to template's files array
                                template['files'].append(file_data)
                else:
                    print("WARNING: Cannot cache files without a template name")
            else:
                # Just add the files to the template without caching
                template['files'] = template.get('files', []) + source_files
                
        # Save the template JSON
        templates_dir = self.paths.get('templates_dir')
        if not templates_dir:
            print("ERROR: Templates directory not found")
            return False
            
        # Create templates directory if it doesn't exist
        os.makedirs(templates_dir, exist_ok=True)
        
        # Determine the file path to use
        # For updates where template was renamed, keep the original file
        if is_update and original_file_name:
            file_name_to_use = original_file_name
            print(f"[DEBUG] TemplateOperations: Using original file name for update: {file_name_to_use}")
        else:
            file_name_to_use = template_file_name
        
        # Full path to template file
        template_path = os.path.join(templates_dir, f"{file_name_to_use}.json")
        print(f"[DEBUG] TemplateOperations: Saving template to {template_path}")
        
        # Add the file path to the template data for reference
        template['file_path'] = template_path
        
        try:
            with open(template_path, 'w') as f:
                json.dump(template, f, indent=2)
                
            print(f"Saved template to {template_path}")
            
            # Skip structure file creation as we're including the structure in the template
            print(f"[DEBUG] TemplateOperations: Skipping separate structure file creation")
            
            # Reload templates
            if hasattr(self, 'reload_templates'):
                self.reload_templates()
            elif hasattr(self, 'load_templates'):
                self.load_templates()
            
            return True
        except Exception as e:
            print(f"ERROR: Failed to save template: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _extract_files_from_structure(self, structure, files_array, current_folder=""):
        """
        Recursively extract file information from the structure and add to files_array
        
        Args:
            structure: The structure dictionary or list
            files_array: The array to add file information to
            current_folder: The current folder path
        """
        if not structure:
            return
        
        # Handle different structure formats
        items = []
        
        # Case 1: Dictionary with 'root' key (common format)
        if isinstance(structure, dict) and 'root' in structure:
            items = structure['root']
        # Case 2: List of items (array format)
        elif isinstance(structure, list):
            items = structure
        # Case 3: Dictionary with folder keys mapping to children (legacy format)
        elif isinstance(structure, dict) and not any(k in structure for k in ['type', 'name']):
            # Convert to items
            for folder_name, children in structure.items():
                items.append({
                    'name': folder_name,
                    'type': 'folder',
                    'children': children if isinstance(children, list) else []
                })
        # Case 4: Single item dictionary with type/name fields
        elif isinstance(structure, dict) and 'type' in structure and 'name' in structure:
            items = [structure]
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            item_name = item.get('name', '')
            item_type = item.get('type', '')
            
            # Handle different folder formats
            if item_type == 'folder':
                # Format 1: Modern format with explicit 'children' field
                folder_path = f"{current_folder}{item_name}/"
                if 'children' in item and item['children']:
                    self._extract_files_from_structure(item['children'], files_array, folder_path)
            
            # Handle different file formats
            elif item_type == 'file':
                # Extract file information - collect all relevant fields
                file_info = {
                    'file_name': item_name,
                    'original_path': item.get('original_path', item.get('path', '')),
                    'cached_path': item.get('cached_path', ''),
                    'rename_flag': item.get('rename_flag', '${PROJECT_NAME}' in item_name),
                    'folder': current_folder,
                    'file_type': item.get('file_type', self._guess_file_type(item_name)),
                    'size': item.get('size', 0),
                    'is_binary': item.get('is_binary', False),
                    'last_modified': item.get('last_modified', datetime.datetime.now().isoformat())
                }
                
                # Only add files with original_path (actual files) to the files array
                if file_info['original_path'] and file_info['file_name']:
                    files_array.append(file_info)
            
            # Handle legacy format where item might be a single-key dictionary representing a folder
            elif len(item) == 1 and not item_type and not item_name:
                folder_name = list(item.keys())[0]
                children = list(item.values())[0]
                if isinstance(children, list):
                    folder_path = f"{current_folder}{folder_name}/"
                    self._extract_files_from_structure(children, files_array, folder_path)

    def _clean_structure_files(self, structure):
        """
        Clean up file details in the structure, leaving only essential information
        
        Args:
            structure: The structure dictionary or list
        """
        if not structure:
            return
        
        # Handle different structure formats
        items = []
        
        # Case 1: Dictionary with 'root' key (common format)
        if isinstance(structure, dict) and 'root' in structure:
            items = structure['root']
        # Case 2: List of items (array format)
        elif isinstance(structure, list):
            items = structure
        # Case 3: Dictionary with folder keys mapping to children (legacy format)
        elif isinstance(structure, dict) and not any(k in structure for k in ['type', 'name']):
            # Convert to items
            for folder_name, children in structure.items():
                items.append({
                    'name': folder_name,
                    'type': 'folder',
                    'children': children if isinstance(children, list) else []
                })
        # Case 4: Single item dictionary with type/name fields
        elif isinstance(structure, dict) and 'type' in structure and 'name' in structure:
            items = [structure]
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            item_type = item.get('type', '')
            
            # Handle different folder formats
            if item_type == 'folder' and 'children' in item and item['children']:
                # Recursively process child folders
                self._clean_structure_files(item['children'])
                
            # Handle different file formats
            elif item_type == 'file':
                # Remove unnecessary file details but keep essential ones
                # Keep name, type, and optionally rename_flag
                keys_to_keep = ['name', 'type', 'rename_flag']
                keys_to_remove = [k for k in list(item.keys()) if k not in keys_to_keep]
                
                for key in keys_to_remove:
                    if key in item:
                        del item[key]
            
            # Handle legacy format where item might be a single-key dictionary representing a folder
            elif len(item) == 1 and not item_type:
                folder_name = list(item.keys())[0]
                children = list(item.values())[0]
                if isinstance(children, list):
                    self._clean_structure_files(children)

    def _guess_file_type(self, file_name):
        """
        Guess the file type based on the file extension
        
        Args:
            file_name: The file name
        
        Returns:
            str: The file type
        """
        _, ext = os.path.splitext(file_name)
        ext = ext.lower()
        
        # Video extensions
        if ext in ['.mp4', '.mov', '.avi', '.mkv', '.prproj', '.aep']:
            return 'video'
        # Audio extensions
        elif ext in ['.mp3', '.wav', '.aac', '.flac']:
            return 'audio'
        # Image extensions
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.psd']:
            return 'image'
        # Document extensions
        elif ext in ['.doc', '.docx', '.pdf', '.txt', '.rtf', '.csv', '.xls', '.xlsx']:
            return 'document'
        # Code extensions
        elif ext in ['.py', '.js', '.html', '.css', '.json', '.xml']:
            return 'code'
        else:
            return 'other'

    def _sanitize_template_name(self, template_name):
        """Sanitize a template name for use in filenames"""
        # Replace characters not allowed in filenames across platforms
        unsafe_chars = [":", "/", "\\", "?", "*", "\"", "<", ">", "|", "'"]
        safe_name = template_name
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, "-")
        
        # Replace spaces with underscores
        safe_name = safe_name.replace(" ", "_")
        
        # Trim to a reasonable length
        if len(safe_name) > 180:
            # Keep extension if any
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:175] + ext
        
        return safe_name
    
    def _clean_structure_data(self, structure):
        """
        Clean structure data to remove empty arrays and ensure all item names are strings
        
        Args:
            structure (dict): Structure data
            
        Returns:
            dict: Cleaned structure data
        """
        if not isinstance(structure, dict):
            return structure
            
        cleaned = {}
        for key, value in structure.items():
            # Skip empty arrays
            if isinstance(value, list) and not value:
                continue
                
            # Convert arrays to strings
            if isinstance(key, list):
                if not key:  # Skip empty arrays as keys
                    continue
                key = str(key)
            
            # Skip empty keys
            if not key or key.strip() == "" or key == "[]":
                continue
                
            # Clean nested structures recursively
            if isinstance(value, dict):
                cleaned_value = self._clean_structure_data(value)
                if cleaned_value:  # Only add if the cleaned value is not empty
                    cleaned[key] = cleaned_value
            elif isinstance(value, list):
                # Handle list values - typically for directories with children
                if value:  # Only process non-empty lists
                    cleaned_list = []
                    for item in value:
                        if isinstance(item, dict):
                            cleaned_item = self._clean_structure_data(item)
                            if cleaned_item:  # Only add if the cleaned item is not empty
                                cleaned_list.append(cleaned_item)
                        else:
                            # For non-dict items in lists (string, etc), keep them if not empty
                            if item:
                                cleaned_list.append(item)
                    
                    if cleaned_list:  # Only add if the cleaned list is not empty
                        cleaned[key] = cleaned_list
            else:
                # For non-dict, non-list values (string, bool, etc), keep them
                cleaned[key] = value
                
        return cleaned
    
    def _cache_template_files(self, template_name, template_path, structure_data, save_to_storage=True):
        """Cache all template files in the structure data"""
        # Cache all files in the structure data
        # This will be called when the template is loaded/updated
        
        import time
        start_time = time.time()
        
        if not template_name or not template_path:
            return structure_data
        
        # Ensure cache paths exist
        if "templates_cache_dir" not in self.paths:
            from app.utils.cache_preferences import CachePreferences
            cache_prefs = CachePreferences()
            self.paths["templates_cache_dir"] = cache_prefs.get_cache_location()
            print(f"DEBUG: Missing templates_cache_dir, setting to: {self.paths['templates_cache_dir']}")
            
        cache_dir = os.path.join(self.paths["templates_cache_dir"], template_name)
        print(f"DEBUG: Using cache directory: {cache_dir}")
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        files_dir = os.path.join(cache_dir, "files")
        os.makedirs(files_dir, exist_ok=True)
        
        # Initialize files array to store file metadata
        files_array = []
        
        # Update all cache paths in the structure data and collect file metadata
        structure_data, new_files = self._update_cache_paths_and_collect_files(
            template_name, template_path, structure_data, files_dir, files_array
        )
        
        # Save the updated structure data if requested
        if save_to_storage:
            template_data = self.get_template(template_name)
            
            # Check if template_data is valid (not None or a string)
            if template_data and isinstance(template_data, dict):
                # Update the cache_path in the template data
                template_data["cache_path"] = cache_dir
                
                # Add files array to template data
                if new_files:
                    template_data["files"] = new_files
                
                # Save the metadata
                metadata_path = os.path.join(cache_dir, "metadata.json")
                metadata = {
                    "cached_at": datetime.datetime.now().isoformat(),
                    "template_name": template_name,
                    "template_path": template_path,
                    "files_count": len(new_files) if new_files else self._count_files_in_structure(structure_data),
                }
                save_json_file(metadata_path, metadata)
                print(f"DEBUG: Saved cache metadata to {metadata_path}")
                
                # Save the template with updated cache path
                self.save_template(template_name, template_data)
            else:
                print(f"WARNING: Cannot update template cache - invalid template data for {template_name}")
            
        # Calculate and log the time taken
        end_time = time.time()
        print(f"DEBUG: Template caching took {end_time - start_time:.2f} seconds")
        
        return structure_data
        
    def _update_cache_paths_and_collect_files(self, template_name, template_path, structure_data, files_dir, files_array=None, current_folder=""):
        """
        Update cache paths in a structure and collect file metadata
        
        Args:
            template_name: Template name
            template_path: Path to the template
            structure_data: Structure data
            files_dir: Cache directory for files
            files_array: List to collect file metadata
            current_folder: Current folder path within the structure
            
        Returns:
            Tuple of (structure_data with updated cache paths, files array)
        """
        if files_array is None:
            files_array = []
            
        # Handle string (file path)
        if isinstance(structure_data, str):
            # Check if it's a file path
            if os.path.isabs(structure_data) and os.path.exists(structure_data):
                # Cache the file and return the cache path
                cache_path = self._cache_file(structure_data, files_dir)
                if cache_path:
                    # Add file metadata to files array
                    file_name = os.path.basename(structure_data)
                    files_array.append({
                        "file_name": file_name,
                        "original_path": structure_data,
                        "cached_path": cache_path,
                        "rename_flag": False,
                        "folder": current_folder,
                        "file_type": self._get_file_type(structure_data),
                        "size": os.path.getsize(structure_data),
                        "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(structure_data)).isoformat()
                    })
                    return cache_path, files_array
            # If caching failed, keep original string
        
        # Handle file dictionary format
        elif isinstance(structure_data, dict) and structure_data.get('type') == 'file' and 'path' in structure_data:
            file_path = structure_data['path']
            if os.path.exists(file_path):
                # Cache the file
                cache_path = self._cache_file(file_path, files_dir)
                if cache_path:
                    # Update cache_path but preserve the original path
                    structure_data['cache_path'] = cache_path
                    
                    # Add file metadata to files array
                    file_name = structure_data.get('name', os.path.basename(file_path))
                    rename_flag = '$' in file_name or '${' in file_name  # Check if file should be renamed with project name
                    
                    files_array.append({
                        "file_name": file_name,
                        "original_path": file_path,
                        "cached_path": cache_path,
                        "rename_flag": rename_flag,
                        "folder": current_folder,
                        "file_type": self._get_file_type(file_path),
                        "size": os.path.getsize(file_path),
                        "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
            return structure_data, files_array
        
        # Handle folder format
        elif isinstance(structure_data, dict) and structure_data.get('type') == 'folder' and 'name' in structure_data:
            folder_name = structure_data['name']
            new_current_folder = os.path.join(current_folder, folder_name) if current_folder else folder_name
            
            # Process children if any
            if 'children' in structure_data and isinstance(structure_data['children'], list):
                for i, child in enumerate(structure_data['children']):
                    result, files_array = self._update_cache_paths_and_collect_files(
                        template_name, template_path, child, files_dir, files_array, new_current_folder
                    )
                    structure_data['children'][i] = result
                    
            return structure_data, files_array
        
        elif isinstance(structure_data, list):
            # Process a list of items
            for i, item in enumerate(structure_data):
                result, files_array = self._update_cache_paths_and_collect_files(
                    template_name, template_path, item, files_dir, files_array, current_folder
                )
                structure_data[i] = result
                
            return structure_data, files_array
        
        return structure_data, files_array
    
    def _get_file_type(self, file_path):
        """Determine the file type based on extension"""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Video extensions
        if ext in ['.mp4', '.mov', '.avi', '.mkv', '.prproj', '.aep']:
            return 'video'
        # Audio extensions
        elif ext in ['.mp3', '.wav', '.aac', '.flac']:
            return 'audio'
        # Image extensions
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.psd']:
            return 'image'
        # Document extensions
        elif ext in ['.doc', '.docx', '.pdf', '.txt', '.rtf', '.csv', '.xls', '.xlsx']:
            return 'document'
        # Code extensions
        elif ext in ['.py', '.js', '.html', '.css', '.json', '.xml']:
            return 'code'
        else:
            return 'other'

    def _cache_file(self, file_path, files_dir):
        """
        Cache a file and return the cache path
        
        Args:
            file_path: Path to the file to cache
            files_dir: Directory to cache the file in
            
        Returns:
            str: Path to the cached file, or None if caching failed
        """
        if not file_path or not os.path.exists(file_path):
            print(f"ERROR: Cannot cache file - path does not exist: {file_path}")
            return None
        
        try:
            # Get the file name and extension
            file_name = os.path.basename(file_path)
            
            # Create a unique file hash based on path and modification time
            file_stats = os.stat(file_path)
            file_hash = f"{hash(file_path)}_{file_stats.st_mtime}"
            
            # Cache the file with its original name
            cache_path = os.path.join(files_dir, file_name)
            
            # Create the cache directory if it doesn't exist
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            
            # Check if the file is already cached and up to date
            if os.path.exists(cache_path):
                # If the file is already cached, check if it's the same
                try:
                    cached_stats = os.stat(cache_path)
                    if cached_stats.st_size == file_stats.st_size and cached_stats.st_mtime >= file_stats.st_mtime:
                        print(f"DEBUG: File already cached and up to date: {file_name}")
                        return cache_path
                except Exception as e:
                    print(f"ERROR: Failed to check cached file stats: {str(e)}")
            
            # Copy the file to the cache
            try:
                shutil.copy2(file_path, cache_path)
                print(f"DEBUG: Cached file {file_path} to {cache_path}")
                
                # Get the metadata file path - store it at the template level, not in each directory
                root_cache_dir = os.path.dirname(files_dir)
                metadata_path = os.path.join(root_cache_dir, "metadata.json")
                
                # Load existing metadata if it exists
                metadata = {}
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                    except Exception as e:
                        print(f"ERROR: Failed to load metadata: {str(e)}")
                        metadata = {}
                
                # Ensure files dictionary exists
                if "files" not in metadata:
                    metadata["files"] = {}
                
                # Get relative path from files_dir to cache_path
                relative_to_cache = os.path.relpath(cache_path, os.path.dirname(files_dir))
                
                # Store file metadata
                metadata["files"][relative_to_cache] = {
                    "original_path": file_path,
                    "cache_path": cache_path,
                    "relative_path": os.path.dirname(relative_to_cache),
                    "file_name": file_name,
                    "size": file_stats.st_size,
                    "hash": hashlib.sha256(file_path.encode()).hexdigest(),
                    "cached_date": time.time()
                }
                
                # Update last_updated timestamp
                metadata["last_updated"] = time.time()
                
                # Create created timestamp if it doesn't exist
                if "created" not in metadata:
                    metadata["created"] = time.time()
                
                # Save the metadata
                try:
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2)
                except Exception as e:
                    print(f"ERROR: Failed to save metadata: {str(e)}")
                
                return cache_path
            except Exception as e:
                print(f"Error caching file: {str(e)}")
                return None
        except Exception as e:
            print(f"Error caching file: {str(e)}")
            return None
            
    def _count_files_in_structure(self, structure_data):
        """Count the number of files in a structure"""
        count = 0
        
        if isinstance(structure_data, dict):
            if structure_data.get("type") == "file":
                count += 1
            else:
                # Process all children
                for key, value in structure_data.items():
                    if isinstance(value, (dict, list)):
                        count += self._count_files_in_structure(value)
        elif isinstance(structure_data, list):
            for item in structure_data:
                count += self._count_files_in_structure(item)
                
        return count
    
    def _contains_template_variables(self, file_path, filename):
        """
        Check if a file contains template variables like {{PROJECT_NAME}}
        
        Args:
            file_path: Path to the file
            filename: Name of the file
            
        Returns:
            bool: True if file contains template variables, False otherwise
        """
        print(f"DEBUG: Checking for template variables in file: {filename}")
        
        # Check if filename contains template variables
        if "{{" in filename and "}}" in filename:
            print(f"DEBUG: Filename contains template variables: {filename}")
            return True
            
        # Check if it's a text file that might contain template variables
        if self._is_text_file(file_path):
            print(f"DEBUG: File appears to be a text file, checking content: {filename}")
            try:
                # Only check the first portion of the file (for large files)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(10240)  # Read first 10KB
                    has_variables = "{{" in content and "}}" in content
                    
                    if has_variables:
                        print(f"DEBUG: File content contains template variables: {filename}")
                        
                        # Find and log the template variables for debugging
                        import re
                        template_vars = re.findall(r"{{(.*?)}}", content)
                        if template_vars:
                            print(f"DEBUG: Found template variables: {', '.join(template_vars)}")
                    else:
                        print(f"DEBUG: File content does not contain template variables: {filename}")
                        
                    return has_variables
            except Exception as e:
                print(f"ERROR: Failed to check file content for template variables: {e}")
                
        print(f"DEBUG: File is not a text file or doesn't contain template variables: {filename}")
        return False
        
    def _is_text_file(self, file_path):
        """Check if a file is a text file"""
        text_extensions = ['.txt', '.html', '.css', '.js', '.json', '.xml', '.md', '.csv', '.yml', '.yaml', 
                          '.ini', '.cfg', '.conf', '.py', '.sh', '.bat', '.ps1', '.php', '.rb', '.java', 
                          '.c', '.cpp', '.h', '.cs', '.swift', '.go', '.ts', '.jsx', '.tsx']
        
        # Get the file extension                  
        _, ext = os.path.splitext(file_path.lower())
        
        print(f"DEBUG: Checking if file is text file: {file_path}, extension: {ext}")
        
        # Known text extensions
        if ext in text_extensions:
            print(f"DEBUG: File has a known text extension: {ext}")
            return True
            
        # Try to detect text files without extensions
        if os.path.exists(file_path):
            print(f"DEBUG: File doesn't have a known text extension, testing content...")
            try:
                # Try to open and read a few bytes
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    sample = f.read(1024)
                    # If we can read it as text, it's likely a text file
                    is_text = '\0' not in sample  # Binary files often contain null bytes
                    print(f"DEBUG: Content-based detection result: {'text file' if is_text else 'binary file'}")
                    return is_text
            except Exception as e:
                print(f"DEBUG: Failed to read file for text detection: {e}")
                
        print(f"DEBUG: File is not a text file: {file_path}")
        return False
    
    def import_template_file(self, file_path, name=None, structure_type=None):
        """Import a template from a file"""
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"Error: Template file does not exist: {file_path}")
            return False
            
        # Determine name from file path if not provided
        if not name:
            name = os.path.splitext(os.path.basename(file_path))[0].replace("_", " ")
            
        # Determine structure type from file extension if not provided
        if not structure_type:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in (".prproj", ".xml"):
                structure_type = "Video Editing"
            elif ext in (".aep", ".aet"):
                structure_type = "Motion Graphics"
            elif ext in (".psd", ".ai", ".indd"):
                structure_type = "Design"
            else:
                structure_type = "Custom"
            
        # Save the template
        return self.save_template(name, file_path, structure_type)
    
    def delete_template(self, template_name):
        """
        Delete a template and all associated files
        
        Args:
            template_name: Name of the template to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not template_name:
            return False
        
        # Normalize template name for file and directory names
        normalized_name = template_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        
        # Check if template exists in memory
        template_index = None
        template_data = None
        
        for i, template in enumerate(self.templates):
            if template.get('name') == template_name:
                template_index = i
                template_data = template
                break
            
        # Get template path and structure name
        template_path = None
        structure_name = None
        structured_format = False
        
        if template_data:
            template_path = template_data.get('path')
            structure_name = template_data.get('structure_name')
            structured_format = 'structure' in template_data or structure_name
            
            # Print debug info on what we're deleting
            print(f"[DEBUG] TemplateOps: Deleting template '{template_name}'")
            print(f"[DEBUG] TemplateOps: Template path: {template_path}")
            print(f"[DEBUG] TemplateOps: Structure name: {structure_name}")
            print(f"[DEBUG] TemplateOps: Structured format: {structured_format}")
            
        # Delete from filesystem if template file exists
        if template_path and os.path.exists(template_path):
            try:
                # Don't try to delete the entire directory
                if os.path.isdir(template_path):
                    # Only delete json file if it exists
                    json_path = os.path.join(template_path, f"{template_name}.json")
                    if os.path.exists(json_path):
                        os.remove(json_path)
                        print(f"[DEBUG] TemplateOps: Deleted template file '{json_path}'")
                else:
                    # Delete the file directly
                    os.remove(template_path)
                    print(f"[DEBUG] TemplateOps: Deleted template file '{template_path}'")
            
            except Exception as e:
                print(f"[ERROR] TemplateOps: Failed to delete template file '{template_path}': {e}")
            
        # Check if structures_dir exists in paths and is valid before trying to delete structure files
        if 'structures_dir' in self.paths and self.paths['structures_dir'] and os.path.exists(self.paths['structures_dir']):
            # Delete associated structure files
            # Try different possible structure names
            structure_paths = [
                # Direct matching
                os.path.join(self.paths['structures_dir'], f"{template_name}.json"),
                # Template_ prefix
                os.path.join(self.paths['structures_dir'], f"Template_{template_name}.json"),
                # Normalized name (spaces to underscores)
                os.path.join(self.paths['structures_dir'], f"{normalized_name}.json"),
                # Template_ prefix with normalized name
                os.path.join(self.paths['structures_dir'], f"Template_{normalized_name}.json")
            ]
            
            # If we know the structure name, add it
            if structured_format and structure_name:
                structure_paths.append(os.path.join(self.paths['structures_dir'], f"{structure_name}.json"))
            
            # Try deleting each possible structure file
            structure_deleted = False
            for structure_path in structure_paths:
                if os.path.exists(structure_path):
                    try:
                        os.remove(structure_path)
                        print(f"DEBUG: Successfully deleted structure file for '{template_name}': {structure_path}")
                        structure_deleted = True
                    except Exception as e:
                        print(f"ERROR: Failed to delete structure file: {e}")
            
            # If no structure was deleted, log it
            if not structure_deleted:
                print(f"DEBUG: No structure file found for '{template_name}'")
        else:
            print(f"DEBUG: Skipping structure file deletion - structures_dir not found or invalid")
        
        # Ensure we have a templates_cache_dir in paths
        if 'templates_cache_dir' not in self.paths:
            try:
                from app.utils.cache_preferences import CachePreferences
                cache_prefs = CachePreferences()
                self.paths['templates_cache_dir'] = cache_prefs.get_cache_location()
                print(f"[DEBUG] TemplateOps: Setting templates_cache_dir to {self.paths['templates_cache_dir']}")
            except Exception as e:
                print(f"[WARNING] TemplateOps: Failed to get cache location: {e}")
                # Fallback to a default location
                self.paths['templates_cache_dir'] = os.path.join(os.path.expanduser("~"), ".echelon", "template_cache")
        
        # Delete template cache directory - check all possible cache locations
        cache_paths = []
        
        # Only add paths if we have a valid templates_cache_dir
        if 'templates_cache_dir' in self.paths and self.paths['templates_cache_dir']:
            cache_paths = [
                # Original name
                os.path.join(self.paths['templates_cache_dir'], template_name),
                # Normalized name
                os.path.join(self.paths['templates_cache_dir'], normalized_name),
            ]
        
        # Check the cached_path from template if available
        if template_data and 'cached_path' in template_data:
            cached_path = template_data['cached_path']
            if cached_path:
                if os.path.isdir(cached_path):
                    cache_paths.append(cached_path)
                
                # Also check parent directory (in case cached_path points to a file)
                parent_dir = os.path.dirname(cached_path)
                if os.path.isdir(parent_dir):
                    cache_paths.append(parent_dir)
        
        # Try to delete each cache directory
        cache_deleted = False
        import shutil
        for cache_path in cache_paths:
            if cache_path and os.path.exists(cache_path) and os.path.isdir(cache_path):
                try:
                    shutil.rmtree(cache_path)
                    print(f"[DEBUG] TemplateOps: Deleted template cache directory: {cache_path}")
                    cache_deleted = True
                except Exception as e:
                    print(f"[WARNING] TemplateOps: Failed to delete template cache: {e}")
        
        if not cache_deleted:
            print(f"[INFO] TemplateOps: No cache directory found for '{template_name}'")
        
        # Also check template cache patterns under different locations
        try:
            from app.utils.cache_preferences import CachePreferences
            cache_prefs = CachePreferences()
            cache_base = cache_prefs.get_cache_location()
            
            # Check for template cache
            template_cache_dir = os.path.join(cache_base, 'template_cache', template_name)
            if os.path.exists(template_cache_dir) and os.path.isdir(template_cache_dir):
                try:
                    shutil.rmtree(template_cache_dir)
                    print(f"[DEBUG] TemplateOps: Deleted template cache directory: {template_cache_dir}")
                    cache_deleted = True
                except Exception as e:
                    print(f"[WARNING] TemplateOps: Failed to delete template cache: {e}")
        except Exception as e:
            print(f"[WARNING] TemplateOps: Error checking additional cache locations: {e}")
        
        # Remove from templates list if found
        if template_index is not None:
            del self.templates[template_index]
            print(f"[DEBUG] TemplateOps: Removed template '{template_name}' from templates list")
        
        # Force refresh of the template gallery
        if hasattr(self, 'refresh_template_gallery'):
            self.app.refresh_template_gallery()
            print(f"[DEBUG] TemplateOps: Forced gallery refresh after template deletion")
        
        # Mark as successful even if we couldn't find the template in memory
        # Since we still attempted to delete from filesystem
        print(f"[INFO] TemplateOps: Successfully deleted template '{template_name}'")
        return True
    
    def delete_template_directory(self, template):
        """Delete a directory-based template"""
        if not template or template.get('type') != 'directory':
            return False
            
        template_path = template.get('path')
        if not template_path or not os.path.isdir(template_path):
            return False
            
        template_name = template.get('name')
        
        try:
            # Delete the template directory
            shutil.rmtree(template_path)
            
            # Remove from in-memory list
            self.template_directories.remove(template)
            
            # Reload template directories to refresh the list
            self.load_template_directories()
            
            return True
        except Exception as e:
            print(f"Error deleting template directory {template_name}: {e}")
            return False
    
    def rename_template(self, old_name, new_name):
        """
        Rename a template and its associated structure.
        
        Args:
            old_name (str): The current name of the template
            new_name (str): The new name for the template
            
        Returns:
            bool: True if the template was successfully renamed, False otherwise
        """
        print(f"DEBUG: rename_template called - old_name='{old_name}', new_name='{new_name}'")
        
        # If the names are identical, return success
        if old_name == new_name:
            return True
            
        try:
            # Normalize names - strip any extra whitespace
            old_name = old_name.strip()
            new_name = new_name.strip()
            
            # Find the template by the old name
            template = None
            for t in self.templates:
                # Use case-insensitive comparison for better matching
                if t.get('name', '').strip().lower() == old_name.lower():
                    template = t
                    break
                    
            if not template:
                print(f"WARNING: Template not found with name '{old_name}' for renaming")
                return False
                
            # Save the old and new file paths
            old_file_path = os.path.join(self.paths.get('templates_dir', ''), self.sanitize_filename(old_name) + ".json")
            new_file_path = os.path.join(self.paths.get('templates_dir', ''), self.sanitize_filename(new_name) + ".json")
            
            # Look for any associated structure files
            structure_name = template.get('structure_name')
            if not structure_name:
                # Try to find structure using various naming patterns
                possible_structure_names = [
                    f"Template_{old_name}",
                    old_name,
                    f"Template_{old_name.replace(' ', '_')}",
                    old_name.replace(' ', '_')
                ]
                
                # Remove duplicates while preserving order
                seen = set()
                structure_names_to_try = [name for name in possible_structure_names 
                                        if not (name.lower() in seen or seen.add(name.lower()))]
                
                print(f"DEBUG: Looking for associated structures with names: {structure_names_to_try}")
                
                # Try each name variation
                for name in structure_names_to_try:
                    structure = self.get_structure(name)
                    if structure:
                        structure_name = name
                        print(f"DEBUG: Found associated structure with name '{name}'")
                        break
            
            # Update the template in memory
            old_template_data = template.copy()
            template['name'] = new_name
            
            # If there's a structure associated with this template, update its name too
            if structure_name:
                print(f"DEBUG: Updating associated structure from '{structure_name}' to '{new_name}'")
                
                # Create the new structure name
                if structure_name.startswith("Template_"):
                    new_structure_name = f"Template_{new_name}"
                else:
                    new_structure_name = new_name
                    
                # Update structure name in the template
                template['structure_name'] = new_structure_name
                
                # Get the structure data
                structure = self.get_structure(structure_name)
                if structure:
                    # Copy the structure with the new name 
                    if isinstance(structure, dict) and 'name' in structure:
                        structure['name'] = new_structure_name
                    
                    # Save the structure with the new name
                    from app.templates.structure_operations import StructureOperations
                    structure_ops = StructureOperations()
                    saved = structure_ops.save_custom_structure(new_structure_name, structure)
                    
                    if saved:
                        print(f"DEBUG: Successfully saved structure with new name '{new_structure_name}'")
                        
                        # Try to delete the old structure file if it exists
                        if structure_name != new_structure_name:
                            structure_ops.delete_custom_structure(structure_name)
                    else:
                        print(f"WARNING: Failed to save structure with new name '{new_structure_name}'")
            
            # Save the template with the new name and delete the old one
            save_result = self.save_template_to_file(template, new_file_path)
            if not save_result:
                print(f"ERROR: Failed to save template with new name to {new_file_path}")
                return False
                
            # Update the template in the templates list - first remove the old one, then add the new one
            # Find and remove the old template
            for i in range(len(self.templates) - 1, -1, -1):  # Iterate backwards to safely remove
                t = self.templates[i]
                if isinstance(t, dict) and t.get('name', '').strip().lower() == old_name.lower():
                    print(f"DEBUG: Removing old template '{old_name}' from templates list at index {i}")
                    self.templates.pop(i)
            
            # Add the new template
            self.templates.append(template.copy())
            print(f"DEBUG: Added new template '{new_name}' to templates list")
            
            # Remove the old template file
            if os.path.exists(old_file_path) and old_file_path != new_file_path:
                try:
                    os.remove(old_file_path)
                    print(f"DEBUG: Removed old template file: {old_file_path}")
                except Exception as e:
                    print(f"WARNING: Failed to remove old template file: {e}")
            
            # Update any references in folders
            for folder in self.folders:
                if 'templates' in folder:
                    # Update template references in the folder
                    for i, tmpl_name in enumerate(folder['templates']):
                        if tmpl_name.strip() == old_name:
                            folder['templates'][i] = new_name
                            print(f"DEBUG: Updated template reference in folder '{folder.get('name', 'Unknown')}'")
            
            # Save the updated folders
            self.save_folders()
            
            # Force reload of templates
            self.reload_templates()
            
            # Refresh UI if possible
            if hasattr(self, 'refresh_ui') and callable(self.refresh_ui):
                self.refresh_ui()
                
            # Try to select the renamed template in the UI
            if hasattr(self, 'gallery') and getattr(self, 'gallery', None):
                print(f"🔶 SELECT AFTER RENAME: Trying gallery.select_template('{new_name}')")
                # Make multiple attempts with different variations of the name
                success = self.gallery.select_template(new_name)
                
                if not success:
                    print("🔶 SELECT AFTER RENAME: Direct selection failed for all name variations")
                    print("🔶 SELECT AFTER RENAME: Direct selection failed, trying fallbacks")
                    
                    # Try different variations of the name
                    variations = [
                        new_name,
                        new_name.strip(),
                        f"Template_{new_name}",
                        new_name.replace(' ', '_'),
                        new_name.replace('_', ' ')
                    ]
                    
                    # Try to find the template in the template manager
                    template_found = False
                    for variation in variations:
                        print(f"🔶 SELECT AFTER RENAME: Looking for template '{variation}' in template manager")
                        for template in self.templates:
                            if template.get('name', '').strip() == variation.strip():
                                template_found = True
                                break
                                
                        if template_found:
                            break
                            
                    if not template_found:
                        print("🔶 SELECT AFTER RENAME: Template not found in template manager with any name variation")
                        
                        # Last resort - try to manually select from visible cards
                        print(f"🔶 SELECT AFTER RENAME: Attempting manual selection from {len(self.gallery.template_cards)} template cards")
                        for card in self.gallery.template_cards:
                            card_name = getattr(card, 'template_name', None) or card.template.get('name', '')
                            print(f"🔶 SELECT AFTER RENAME: Checking card '{card_name}' against '{new_name}'")
                            # Fuzzy match - check if one name contains the other or vice versa
                            if (card_name.strip().lower() in new_name.lower() or 
                                new_name.lower() in card_name.strip().lower()):
                                if hasattr(card, 'select') and callable(card.select):
                                    card.select()
                                    print(f"🔶 SELECT AFTER RENAME: Selected card '{card_name}' as a fallback")
                                    return True
                    
                    print(f"🔶 SELECT AFTER RENAME: All selection methods failed for '{new_name}'")
            
            return True
            
        except Exception as e:
            print(f"ERROR renaming template: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_template(self, template):
        """Update a template's metadata"""
        if not template or not template.get('name'):
            return False
            
        template_name = template.get('name')
        
        # Different handling based on template type
        if template.get('type') == 'directory':
            return self.update_directory_template(template)
        else:
            # For file templates, use the save_template method to ensure consistent handling
            # Extract the structure from the template
            structure = template.get('structure')
            
            # Any files that are part of the template
            source_files = template.get('files', [])
            
            # Get the original template name from the file path if available
            original_name = template_name
            file_path = template.get('file_path', '')
            if file_path:
                import os
                # Extract original name from file path
                file_name = os.path.basename(file_path)
                if file_name.endswith('.json'):
                    original_name = file_name[:-5]  # Remove .json extension
                print(f"[DEBUG] TemplateOperations: Updating template {template_name}, original file: {original_name}")
            
            # Use save_template to ensure consistent handling of file caching
            return self.save_template(
                template_name=template_name,
                structure=structure,
                template_data=template,
                source_files=source_files,
                cache_files=True,  # Always cache files during update
                is_update=True,    # Mark this as an update
                original_name=original_name  # Pass the original name for file path consistency
            )
    
    def update_directory_template(self, template):
        """Update a directory-based template's metadata"""
        if not template or not template.get('name') or template.get('type') != 'directory':
            return False
            
        template_name = template.get('name')
        template_path = template.get('path', '')
        
        if not template_path or not os.path.isdir(template_path):
            return False
            
        try:
            # Update template.json inside the directory
            template_json_path = os.path.join(template_path, "template.json")
            
            # Create a copy without the 'path' attribute for saving
            template_copy = dict(template)
            if 'path' in template_copy:
                del template_copy['path']
            
            save_json_file(template_json_path, template_copy)
            
            # Update in-memory copy
            for i, t in enumerate(self.template_directories):
                if t.get('name') == template_name:
                    self.template_directories[i] = template
                    break
            
            return True
        except Exception as e:
            print(f"Error updating directory template {template_name}: {e}")
            return False
    
    def save_custom_structure(self, name, structure):
        """Save a custom folder structure"""
        if not name or not structure:
            print(f"ERROR: Cannot save custom structure. Invalid name or structure.")
            return False
            
        print(f"INFO: Saving custom structure '{name}'")
        
        # Initialize custom structures if needed
        if not hasattr(self, 'custom_structures'):
            self.custom_structures = {}
            
        # Prepare a safe structure by converting to string and back
        try:
            # Use json.dumps/loads to ensure it's serializable
            safe_structure_str = json.dumps(structure)
            safe_structure = json.loads(safe_structure_str)
            
            # Sanitize the filename for disk operations
            sanitized_name = name.replace(' ', '_').replace('/', '-').replace('\\', '-')
            
            # Check if we already have this structure loaded
            existing_creation_time = None
            existing_found = False
            
            # First check if it exists in our in-memory structures
            for i, s in enumerate(self.custom_structures):
                if isinstance(s, dict) and s.get("name") == name:
                    existing_creation_time = s.get("created", time.time())
                    existing_found = True
                    # Update the in-memory structure
                    self.custom_structures[i] = {
                        "name": name,
                        "structure": safe_structure,
                        "modified": time.time(),
                        "created": existing_creation_time
                    }
                    print(f"INFO: Updated existing in-memory custom structure '{name}'")
                    break
                
            # If not found in memory, check if file exists on disk
            if not existing_found:
                file_path = os.path.join(self.paths["custom_structures_dir"], f"{sanitized_name}.json")
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            existing_data = json.load(f)
                            existing_creation_time = existing_data.get("created", time.time())
                            existing_found = True
                            print(f"INFO: Found existing on-disk custom structure '{name}'")
                    except Exception as e:
                        print(f"WARNING: Error reading existing structure file: {e}")
                        # Continue with creation time of now
                        existing_creation_time = time.time()
                else:
                    # No existing structure, use current time
                    existing_creation_time = time.time()
                    
                # Add to our in-memory structures
                structure_data = {
                    "name": name,
                    "structure": safe_structure,
                    "modified": time.time(),
                    "created": existing_creation_time
                }
                self.custom_structures.append(structure_data)
                    
            # Save to disk
            try:
                os.makedirs(self.paths["custom_structures_dir"], exist_ok=True)
                file_path = os.path.join(self.paths["custom_structures_dir"], f"{sanitized_name}.json")
                
                # Write file
                with open(file_path, 'w') as f:
                    json.dump({
                        "name": name,
                        "structure": safe_structure,
                        "modified": time.time(),
                        "created": existing_creation_time
                    }, indent=2)
                    
                status = "Updated" if existing_found else "Created"
                print(f"INFO: Successfully {status.lower()} custom structure '{name}' to {file_path}")
                
                # If this was an update and name differs from sanitized name, clean up old file
                if existing_found and name != sanitized_name:
                    old_path = os.path.join(self.paths["custom_structures_dir"], f"{name}.json")
                    if os.path.exists(old_path) and old_path != file_path:
                        try:
                            os.remove(old_path)
                            print(f"INFO: Removed old structure file at {old_path}")
                        except Exception as e:
                            print(f"WARNING: Failed to remove old structure file: {e}")
                
                return True
            except Exception as e:
                print(f"ERROR: Failed to save custom structure '{name}' to disk: {e}")
                return False
                
        except RecursionError:
            print(f"ERROR: Failed to save custom structure '{name}': Recursion detected in structure")
            return False
        except Exception as e:
            print(f"ERROR: Failed to process custom structure '{name}': {e}")
            return False
    
    def get_custom_structure(self, name):
        """
        Get a custom structure by name
        
        Args:
            name (str): Name of the custom structure
            
        Returns:
            dict: The structure data, or None if not found
        """
        if not hasattr(self, 'custom_structures') or not self.custom_structures:
            self.load_custom_structures()
            
        # Find the structure in the custom structures list
        for structure in self.custom_structures:
            if structure.get("name") == name:
                print(f"INFO: Found custom structure '{name}'")
                return structure.get("structure")
                
        print(f"INFO: Custom structure '{name}' not found")
        return None
        
    def save_structure(self, name, structure):
        """
        Save a structure (alias for save_custom_structure)
        
        Args:
            name (str): Name of the structure
            structure (list): The structure data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First attempt to save normally
            result = self.save_custom_structure(name, structure)
            if result:
                return True
                
            # If that failed, try a more robust approach
            print(f"INFO: First save attempt failed, trying with simplified approach")
            
            # Create a safe serializable structure
            safe_structure = self._create_safe_structure(structure)
            return self.save_custom_structure(name, safe_structure)
            
        except Exception as e:
            print(f"ERROR: Failed to save structure: {e}")
            return False
            
    def _create_safe_structure(self, structure):
        """Convert structure to a safely serializable format"""
        if not structure:
            return []
            
        # Handle both list and dict formats safely
        if isinstance(structure, dict):
            result = {}
            # Copy basic fields that are definitely serializable
            for key in ['name', 'type']:
                if key in structure:
                    result[key] = structure[key]
                    
            # Handle children separately
            if 'children' in structure and structure['children']:
                result['children'] = self._create_safe_structure(structure['children'])
            return result
            
        elif isinstance(structure, list):
            result = []
            # Process each item
            for item in structure:
                if isinstance(item, (dict, list)):
                    result.append(self._create_safe_structure(item))
                else:
                    result.append(item)
            return result
            
        # For any other type, return as is
        return structure
        
    def save_template_info(self, template_name, template_info):
        """
        Save template information
        
        Args:
            template_name (str): Name of the template
            template_info (dict): Dictionary containing template information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the template if it exists
            existing_template = self.get_template(template_name)
            
            if existing_template:
                # Update existing template with new info
                for key, value in template_info.items():
                    existing_template[key] = value
                    
                # Save the updated template
                self.update_template(existing_template)
                print(f"INFO: Updated template info for '{template_name}'")
                return True
            else:
                # Create a new template entry
                template_info['name'] = template_name
                template_info['created'] = time.time()
                template_info['modified'] = time.time()
                
                # Save as a new template
                self.templates.append(template_info)
                
                # Save to disk
                template_file = os.path.join(self.paths["templates_dir"], f"{template_name.replace(' ', '_')}.json")
                with open(template_file, 'w') as f:
                    json.dump(template_info, f, indent=2)
                    
                print(f"INFO: Created new template info for '{template_name}'")
                return True
        except Exception as e:
            print(f"ERROR: Failed to save template info for '{template_name}': {e}")
            return False
        
    def load_custom_structures(self):
        """Load custom structures from disk"""
        if not hasattr(self, 'custom_structures'):
            self.custom_structures = []
            
        if not os.path.exists(self.paths["custom_structures_dir"]):
            os.makedirs(self.paths["custom_structures_dir"], exist_ok=True)
            return
            
        # Load all structure files
        for filename in os.listdir(self.paths["custom_structures_dir"]):
            if filename.endswith(".json"):
                filepath = os.path.join(self.paths["custom_structures_dir"], filename)
                try:
                    with open(filepath, 'r') as f:
                        structure_data = json.load(f)
                        
                    # Check if this structure already exists
                    exists = False
                    for i, s in enumerate(self.custom_structures):
                        if s.get("name") == structure_data.get("name"):
                            self.custom_structures[i] = structure_data
                            exists = True
                            break
                            
                    if not exists:
                        self.custom_structures.append(structure_data)
                        
                    print(f"INFO: Loaded custom structure '{structure_data.get('name')}' from {filename}")
                except Exception as e:
                    print(f"ERROR: Failed to load custom structure from {filename}: {e}")
                    
        print(f"INFO: Loaded {len(self.custom_structures)} custom structures")
        return self.custom_structures
    
    def delete_custom_structure(self, name):
        """Delete a custom folder structure"""
        if name not in self.custom_structures:
            return False
        
        # Create a clean filename
        filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        file_path = os.path.join(self.paths["custom_structures_dir"], f"{filename}.json")
        
        try:
            # Delete the structure JSON file
            os.remove(file_path)
            
            # Delete all cached files associated with this structure
            cache_dir = os.path.join(self.paths["templates_dir"], "cache", filename)
            if os.path.exists(cache_dir):
                print(f"DEBUG: Deleting cache directory for structure '{name}': {cache_dir}")
                shutil.rmtree(cache_dir)
                print(f"DEBUG: Successfully deleted cache directory for structure '{name}'")
            
            # Remove from in-memory cache
            del self.custom_structures[name]
            
            return True
        except Exception as e:
            print(f"Error deleting structure {name}: {e}")
            return False
    
    def load_templates(self):
        """Load all templates from template directory"""
        self.templates = {}
        
        # Get template directory
        template_dir = self.paths.get("templates_dir", "")
        if not template_dir or not os.path.exists(template_dir):
            print(f"Warning: Template directory does not exist: {template_dir}")
            return
            
        # Find all template files
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith(".json") and file != "folders.json" and file != "preferences.json":
                    try:
                        # Load template file
                        template_path = os.path.join(root, file)
                        with open(template_path, 'r') as f:
                            template_data = json.load(f)
                            
                        # Add template to list if it has required fields
                        if 'name' in template_data:
                            self.templates[template_data['name']] = template_data
                    except Exception as e:
                        print(f"Error loading template file {file}: {e}")
                        
        print(f"Loaded {len(self.templates)} templates from {template_dir}")

    def _normalize_structure_format(self, structure_items):
        """Normalize the structure format to ensure consistency.
        
        This method ensures folders are represented as dictionaries with empty arrays 
        for consistency with the rest of the application: {"folder_name": []}
        
        Args:
            structure_items (list): List of structure items to normalize
            
        Returns:
            list: Normalized structure items
        """
        if not structure_items:
            return []
            
        normalized = []
        
        for item in structure_items:
            # Handle dictionaries (folders with possible children)
            if isinstance(item, dict):
                # If the item is already a dictionary with a key and a list value,
                # we can use it directly or process its children
                if list(item.keys()) == 1 and isinstance(list(item.values())[0], list):
                    folder_name = list(item.keys())[0]
                    children = list(item.values())[0]
                    normalized.append({folder_name: self._normalize_structure_format(children)})
                # Handle the {"name": "folder_name", "type": "folder"} format
                elif "name" in item and "type" in item and item["type"] == "folder":
                    folder_name = item["name"]
                    children = []
                    if "children" in item and isinstance(item["children"], list):
                        children = self._normalize_structure_format(item["children"])
                    normalized.append({folder_name: children})
                # Handle the {"folder_name": []} format
                else:
                    processed_dict = {}
                    for folder_name, children in item.items():
                        if isinstance(children, list):
                            processed_dict[folder_name] = self._normalize_structure_format(children)
                        else:
                            # Ensure empty folders are represented as empty lists
                            processed_dict[folder_name] = []
                    normalized.append(processed_dict)
            # Handle string items (files or folders without format)
            elif isinstance(item, str):
                # String items are treated as file names
                normalized.append(item)
                
        return normalized 

    def save_template_to_file(self, template, file_path):
        """
        Save a template object to a specific file path
        
        Args:
            template (dict): The template object to save
            file_path (str): The file path where the template should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the template to the file
            with open(file_path, 'w') as f:
                json.dump(template, f, indent=2)
                
            print(f"DEBUG: Successfully saved template to file: {file_path}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to save template to file {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return False 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Structure Operations
Handles management of folder structures
"""

import os
import json
import copy
import shutil
from pathlib import Path

# Import StructureUtils
try:
    from app.utils.structure_utils import StructureUtils
except ImportError:
    # Fallback if not available
    class StructureUtils:
        @staticmethod
        def normalize_structure(structure):
            return structure
            
        @staticmethod
        def save_structure(structure, file_path, pretty=True):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(structure, f, indent=2 if pretty else None)
                return True
            except Exception as e:
                print(f"Error saving structure: {e}")
                return False

from app.utils.utils import save_json_file, load_json_file

class StructureOperations:
    """
    Operations for managing custom folder structures
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize custom_structures as a dictionary
        self.custom_structures = {}
        # Initialize paths if not provided
        if not hasattr(self, 'paths'):
            self.paths = {}
        
        # Ensure consistent naming of directories
        if "custom_structures_dir" in self.paths and "structures_dir" not in self.paths:
            self.paths["structures_dir"] = self.paths["custom_structures_dir"]
        elif "structures_dir" in self.paths and "custom_structures_dir" not in self.paths:
            self.paths["custom_structures_dir"] = self.paths["structures_dir"]
    
    def save_custom_structure(self, name, structure_data):
        """
        Save a custom folder structure to disk
        
        Args:
            name: Structure name
            structure_data: Structure data
        """
        try:
            # Make sure we have the structures directory
            structures_dir = self.paths.get('structures_dir', './structures')
            if not os.path.exists(structures_dir):
                os.makedirs(structures_dir, exist_ok=True)
                
            # Normalize the name for file saving
            file_name = name.replace(' ', '_')
            if not file_name.endswith('.json'):
                file_name += '.json'
                
            # If structure_data doesn't have a name, add it
            if isinstance(structure_data, dict) and 'name' not in structure_data:
                structure_data['name'] = name
                
            # Save the structure to the structures directory
            structure_path = os.path.join(structures_dir, file_name)
            with open(structure_path, 'w', encoding='utf-8') as f:
                json.dump(structure_data, f, indent=4)
                
            # Store the structure data in memory
            if not hasattr(self, 'custom_structures') or self.custom_structures is None:
                self.custom_structures = {}
                
            self.custom_structures[name] = structure_data
            
            print(f"[DEBUG] Saved custom structure {name} to {structure_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to save custom structure {name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _validate_structure_format(self, structure_data):
        """
        Validate and ensure a structure can be properly serialized
        
        Args:
            structure_data: The structure data dictionary
            
        Returns:
            dict: Validated structure data or None if validation fails
        """
        try:
            # Basic schema validation
            required_fields = ["name", "directories"]
            for field in required_fields:
                if field not in structure_data:
                    print(f"[ERROR] StructureOps: Missing required field '{field}' in structure data")
                    return None
                    
            # Ensure directories is a list
            if not isinstance(structure_data["directories"], list):
                print(f"[ERROR] StructureOps: 'directories' must be a list, got {type(structure_data['directories'])}")
                if structure_data["directories"] is None:
                    structure_data["directories"] = []
                else:
                    structure_data["directories"] = [structure_data["directories"]]
            
            # Simple serialization test to make sure the structure can be converted to JSON
            try:
                json_str = json.dumps(structure_data)
                # Try to decode back to ensure it's valid
                test_decode = json.loads(json_str)
                return structure_data
            except Exception as e:
                print(f"[ERROR] StructureOps: Structure data is not serializable: {e}")
                
                # Attempt to create a safe serializable version
                safe_structure = self._create_safe_structure(structure_data)
                if safe_structure:
                    print(f"[DEBUG] StructureOps: Created safe serializable version of structure")
                    return safe_structure
                
                return None
                
        except Exception as e:
            print(f"[ERROR] StructureOps: Validation error: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    def _create_safe_structure(self, structure_data):
        """
        Create a safely serializable version of a structure.
        
        Args:
            structure_data (dict): The structure data to sanitize
            
        Returns:
            dict: Sanitized structure data that can be serialized to JSON
        """
        if not structure_data:
            # Return a minimal valid structure
            return {
                "name": "Empty",
                "display_name": "Empty Structure",
                "type": "custom",
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                "directories": []
            }
            
        try:
            # If it's already a dict, use it as the base
            if isinstance(structure_data, dict):
                safe_structure = structure_data.copy()
            else:
                # Convert non-dict to a dict
                safe_structure = {"directories": structure_data if isinstance(structure_data, list) else []}
                
            # Ensure required fields exist
            if "name" not in safe_structure:
                safe_structure["name"] = "Unknown"
                
            if "display_name" not in safe_structure:
                safe_structure["display_name"] = safe_structure["name"]
                
            if "type" not in safe_structure:
                safe_structure["type"] = "custom"
                
            if "version" not in safe_structure:
                safe_structure["version"] = "1.0"
                
            if "created" not in safe_structure:
                safe_structure["created"] = datetime.now().isoformat()
                
            if "modified" not in safe_structure:
                safe_structure["modified"] = datetime.now().isoformat()
                
            # Convert datetime objects to strings
            for key in ["created", "modified"]:
                if key in safe_structure and isinstance(safe_structure[key], datetime):
                    safe_structure[key] = safe_structure[key].isoformat()
                    
            # Ensure directories is a list
            if "directories" not in safe_structure:
                safe_structure["directories"] = []
            elif not isinstance(safe_structure["directories"], list):
                if isinstance(safe_structure["directories"], dict):
                    safe_structure["directories"] = [safe_structure["directories"]]
                else:
                    safe_structure["directories"] = []
                    
            # Test serialization to ensure it works
            json.dumps(safe_structure)
            return safe_structure
            
        except Exception as e:
            print(f"[ERROR] StructureOps: Error creating safe structure: {e}")
            # Return a minimal valid structure as a fallback
            return {
                "name": "Error",
                "display_name": "Error Structure",
                "type": "custom",
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                "directories": []
            }
    
    def get_structure(self, structure_name):
        """
        Get a structure by name. Handles various naming formats.
        
        Args:
            structure_name (str): The name of the structure to retrieve
            
        Returns:
            dict or list: The structure data or None if not found
        """
        print(f"DEBUG: get_structure called with structure_name='{structure_name}'")
        
        if not structure_name:
            print("WARNING: Empty structure name provided to get_structure")
            return None
            
        # Normalize the structure name to handle trailing spaces and other issues
        structure_name = structure_name.strip()
        
        # Generate a list of name variants to try
        name_variations = self._get_name_variations(structure_name)
        
        print(f"DEBUG: Trying structure names: {name_variations[:3]}{'...' if len(name_variations) > 3 else ''}")
        
        # First check if already in memory
        for name in name_variations:
            # Check custom_structures
            if name in self.custom_structures:
                print(f"DEBUG: Found custom structure in memory: {name}")
                structure_data = self.custom_structures[name]
                
                # Check if this is a complete structure with directories field
                if isinstance(structure_data, dict) and 'directories' in structure_data:
                    print(f"DEBUG: Found complete structure data with directories field")
                    return structure_data['directories']
                    
                # Return the structure data as is
                return structure_data
                
        # Not found in memory, try looking in the template data first
        # This is a more direct approach since template data contains structured folder hierarchy
        if hasattr(self, 'templates'):
            for template in self.templates:
                if not isinstance(template, dict):
                    continue
                    
                # Check if template matches any of our name variations
                template_name = template.get('name', '')
                structure_name_in_template = template.get('structure_name', '')
                
                if template_name in name_variations or structure_name_in_template in name_variations:
                    # Check if the template has a structure field
                    if 'structure' in template and template['structure']:
                        print(f"DEBUG: Found structure in template data for {structure_name}")
                        return template['structure']
        
        # Not found in memory or templates, try loading from file system
        for name in name_variations:
            # Create sanitized filename
            filename = self.sanitize_filename(name)
            
            # First try the custom structures directory
            structure_path = os.path.join(
                self.paths.get('custom_structures_dir', self.paths.get('structures_dir', '')), 
                f"{filename}.json"
            )
            
            if os.path.exists(structure_path):
                try:
                    with open(structure_path, 'r') as f:
                        structure_data = json.load(f)
                        
                    # Check if we have a dictionary with directories
                    if isinstance(structure_data, dict) and 'directories' in structure_data:
                        # Log the structure data format
                        print(f"DEBUG: Structure data has directories field with {len(structure_data['directories'])} entries")
                        
                        # Cache the structure in memory for future lookups
                        self.custom_structures[name] = structure_data
                        
                        # Return the directories list, which is the actual structure
                        return structure_data['directories']
                    else:
                        # Store in memory cache and return as is
                        self.custom_structures[name] = structure_data
                        print(f"DEBUG: Found custom structure on disk: {name}")
                        return structure_data
                except json.JSONDecodeError:
                    print(f"ERROR: Invalid JSON in structure file: {structure_path}")
                except Exception as e:
                    print(f"ERROR: Failed to load structure file {structure_path}: {e}")
            
            # If not found in custom structures dir, try main structures dir if different
            if ('custom_structures_dir' in self.paths and 'structures_dir' in self.paths and
                self.paths['custom_structures_dir'] != self.paths['structures_dir']):
                
                structure_path = os.path.join(
                    self.paths['structures_dir'], 
                    f"{filename}.json"
                )
                
                if os.path.exists(structure_path):
                    try:
                        with open(structure_path, 'r') as f:
                            structure_data = json.load(f)
                        
                        # Check for directories field
                        if isinstance(structure_data, dict) and 'directories' in structure_data:
                            # Cache and return directories list
                            self.custom_structures[name] = structure_data
                            print(f"DEBUG: Found structure with directories in main structures dir: {name}")
                            return structure_data['directories']
                        else:
                            # Store and return as is
                            self.custom_structures[name] = structure_data
                            print(f"DEBUG: Found structure in main structures dir: {name}")
                            return structure_data
                    except json.JSONDecodeError:
                        print(f"ERROR: Invalid JSON in structure file: {structure_path}")
                    except Exception as e:
                        print(f"ERROR: Failed to load structure file {structure_path}: {e}")
        
        # If we got here, the structure wasn't found
        print(f"DEBUG: Structure not found: {structure_name}")
        return None
    
    def _get_name_variations(self, structure_name):
        """Generate variations of a structure name for robust lookup
        
        Args:
            structure_name (str): Base structure name
            
        Returns:
            list: List of name variations to try
        """
        # Original name first (after normalization)
        name_variations = [structure_name]
        
        # Add variant with Template_ prefix if not already present
        if not structure_name.startswith("Template_"):
            name_variations.append(f"Template_{structure_name}")
        else:
            # Also try without the prefix
            name_variations.append(structure_name[9:])
        
        # Add variants with spaces converted to underscores and vice versa
        if " " in structure_name:
            name_variations.append(structure_name.replace(" ", "_"))
            if not structure_name.startswith("Template_"):
                name_variations.append(f"Template_{structure_name.replace(' ', '_')}")
        elif "_" in structure_name:
            name_variations.append(structure_name.replace("_", " "))
            if not structure_name.startswith("Template_"):
                name_variations.append(f"Template_{structure_name.replace('_', ' ')}")
                
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = [name for name in name_variations 
                          if not (name.lower() in seen or seen.add(name.lower()))]
        
        return unique_variations
    
    def load_custom_structures(self):
        """Load custom folder structures from disk"""
        try:
            # Make sure we have the structures directory
            structures_dir = self.paths.get('structures_dir', './structures')
            if not os.path.exists(structures_dir):
                os.makedirs(structures_dir, exist_ok=True)
                
            # Reset the custom structures
            self.custom_structures = {}
            
            # Get all JSON files in the structures directory
            structure_files = [f for f in os.listdir(structures_dir) if f.endswith('.json')]
            
            for structure_file in structure_files:
                try:
                    structure_path = os.path.join(structures_dir, structure_file)
                    with open(structure_path, 'r', encoding='utf-8') as f:
                        structure_data = json.load(f)
                    
                    # Get the name from the file name (without the .json extension)
                    structure_name = os.path.splitext(structure_file)[0]
                    
                    # Store the structure data with the name as the key
                    if isinstance(structure_data, dict):
                        # Add name to the structure data if missing
                        if 'name' not in structure_data:
                            structure_data['name'] = structure_name
                        self.custom_structures[structure_name] = structure_data
                    else:
                        print(f"[WARNING] Structure file {structure_file} has invalid format (not a dictionary)")
                        
                except Exception as e:
                    print(f"[ERROR] Failed to load structure file {structure_file}: {e}")
            
            print(f"[DEBUG] Loaded {len(self.custom_structures)} custom structures")
            
            # If custom_structures is empty after load, attempt to force-load the structures
            if not self.custom_structures:
                print("[WARNING] custom_structures is empty after load, attempting force load")
                self._force_load_structures()
                
        except Exception as e:
            print(f"[ERROR] Failed to load custom structures: {e}")
            import traceback
            traceback.print_exc()
    
    def _force_load_structures(self):
        """Attempt to force-load structures using alternative methods"""
        try:
            # First try looking for structures in the predefined templates
            structures_dir = self.paths.get('structures_dir', './structures')
            template_dir = self.paths.get('templates_dir', './templates')
            
            # Check if there are any structure files in the templates directory
            if os.path.exists(template_dir):
                template_files = [f for f in os.listdir(template_dir) if f.endswith('.json')]
                
                for template_file in template_files:
                    try:
                        template_path = os.path.join(template_dir, template_file)
                        with open(template_path, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                        
                        # If this is a template with a structure, add it to custom structures
                        if isinstance(template_data, dict) and 'structure' in template_data:
                            structure_name = f"Template_{template_data.get('name', os.path.splitext(template_file)[0])}"
                            self.custom_structures[structure_name] = template_data
                    except Exception as e:
                        print(f"[ERROR] Failed to force-load template file {template_file}: {e}")
            
            print(f"[DEBUG] Force-loaded {len(self.custom_structures)} custom structures")
            
        except Exception as e:
            print(f"[ERROR] Failed to force-load structures: {e}")
            import traceback
            traceback.print_exc()
    
    def delete_custom_structure(self, name):
        """Delete a custom folder structure"""
        if not name:
            print(f"DEBUG: Cannot delete structure with empty name")
            return False
            
        # Create different variations of the filename to check
        name_variants = [name]
        if name.startswith("Template_"):
            name_variants.append(name[9:])  # Without Template_ prefix
        else:
            name_variants.append(f"Template_{name}")
            
        # With spaces replaced by underscores
        for variant in list(name_variants):  # Make a copy of the list for iteration
            if " " in variant:
                name_variants.append(variant.replace(" ", "_"))
            elif "_" in variant:
                name_variants.append(variant.replace("_", " "))
        
        deleted = False
        for variant in name_variants:
            # Create a clean filename
            filename = variant.replace(" ", "_").replace("/", "-").replace("\\", "-")
            file_path = os.path.join(self.paths["custom_structures_dir"], f"{filename}.json")
            
            if os.path.exists(file_path):
                try:
                    # Delete the structure file
                    os.remove(file_path)
                    print(f"DEBUG: Successfully deleted structure file for '{variant}': {file_path}")
                    
                    # Delete associated cache directory
                    cache_dir = os.path.join(self.paths["templates_dir"], "cache", filename)
                    if os.path.exists(cache_dir):
                        print(f"DEBUG: Deleting cache directory for structure '{variant}': {cache_dir}")
                        import shutil
                        shutil.rmtree(cache_dir)
                        print(f"DEBUG: Successfully deleted cache directory for structure '{variant}'")
                    
                    deleted = True
                except Exception as e:
                    print(f"ERROR: Failed to delete structure file for '{variant}': {e}")
            else:
                print(f"DEBUG: Structure file not found for '{variant}': {file_path}")
        
        return deleted
    
    def get_structures(self):
        """Get a list of all available folder structures"""
        # Return the names of all custom structures
        custom_structures = list(self.custom_structures.keys())
        
        # Add built-in structures from constants
        from app.constants import DEFAULT_STRUCTURES
        all_structures = list(DEFAULT_STRUCTURES.keys()) + custom_structures
        
        # Filter out duplicates and sort
        return sorted(list(set(all_structures)))
    
    def delete_structure(self, structure_name):
        """Delete a folder structure by name"""
        # Check if it's a built-in structure (which can't be deleted)
        from app.constants import DEFAULT_STRUCTURES
        if structure_name.lower() in DEFAULT_STRUCTURES:
            print(f"Cannot delete built-in structure: {structure_name}")
            return False
        
        # Try to delete as a custom structure
        return self.delete_custom_structure(structure_name)
    
    def rename_custom_structure(self, old_name, new_name):
        """Rename a custom structure"""
        if old_name == new_name:
            return True
        
        if old_name in self.custom_structures:
            # Create a clean filename for both old and new
            old_filename = old_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
            new_filename = new_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
            
            old_path = os.path.join(self.paths["custom_structures_dir"], f"{old_filename}.json")
            new_path = os.path.join(self.paths["custom_structures_dir"], f"{new_filename}.json")
            
            # Cache directory paths
            old_cache_dir = os.path.join(self.paths["templates_dir"], "cache", old_filename)
            new_cache_dir = os.path.join(self.paths["templates_dir"], "cache", new_filename)
            
            try:
                # Get the structure
                structure = self.custom_structures[old_name]
                
                # Update the name
                structure["name"] = new_name
                
                # Save to new file
                save_json_file(new_path, structure)
                
                # Remove old file
                if os.path.exists(old_path):
                    os.remove(old_path)
                
                # Rename cache directory if it exists
                import shutil
                if os.path.exists(old_cache_dir):
                    print(f"DEBUG: Renaming cache directory from '{old_cache_dir}' to '{new_cache_dir}'")
                    
                    # Create parent directory if needed
                    os.makedirs(os.path.dirname(new_cache_dir), exist_ok=True)
                    
                    # If new directory already exists, remove it first
                    if os.path.exists(new_cache_dir):
                        print(f"DEBUG: Removing existing cache directory: {new_cache_dir}")
                        shutil.rmtree(new_cache_dir)
                    
                    # Rename directory
                    shutil.move(old_cache_dir, new_cache_dir)
                    print(f"DEBUG: Successfully renamed cache directory to {new_cache_dir}")
                
                # Update in-memory dictionary
                self.custom_structures[new_name] = structure
                del self.custom_structures[old_name]
                
                return True
            except Exception as e:
                print(f"Error renaming structure {old_name} to {new_name}: {e}")
                return False
        
        return False
    
    def save_structure_from_folders(self, template_name, folder_list):
        """Save a folder structure from a list of folder names"""
        if not template_name or not folder_list:
            return False
            
        # Process folder list to remove duplicates and sort
        unique_folders = sorted(list(set(folder_list)))
        
        # Create structure with directories
        structure = {
            "name": f"Template_{template_name}",
            "directories": unique_folders,
            "created": datetime.now().isoformat()
        }
        
        # Save to file
        return self.save_custom_structure(structure["name"], unique_folders)
    
    def get_structure_for_project_type(self, project_type):
        """Get the appropriate structure for a given project type"""
        from app.constants import PROJECT_TYPE_TO_STRUCTURE
        
        # Get the structure name for this project type
        structure_name = PROJECT_TYPE_TO_STRUCTURE.get(project_type)
        
        if structure_name:
            # Get the structure
            return self.get_structure(structure_name)
        
        # Fallback to a default structure
        return self.get_structure("Video Editing - Standard")
    
    def get_default_structure(self, structure_type="standard"):
        """Get a default structure by type"""
        from app.constants import DEFAULT_STRUCTURES
        
        # Map common structure type keywords to our structure names in constants.py
        structure_mapping = {
            "standard": "Video Editing - Standard",
            "basic": "Video Editing - Basic",
            "video": "Video Editing - Standard",
            "motion": "Motion Graphics - Standard",
            "design": "Video Editing - Basic",
            "vfx": "VFX - Standard",
            "audio": "Video Editing - Basic"
        }
        
        # Convert to lowercase for case-insensitive matching
        structure_type_lower = structure_type.lower()
        
        # Check if we have a direct mapping
        if structure_type_lower in structure_mapping:
            structure_key = structure_mapping[structure_type_lower]
        else:
            # Default to basic structure
            structure_key = "Video Editing - Basic"
        
        # Return the structure or an empty list as last resort
        return DEFAULT_STRUCTURES.get(structure_key, [])
    
    def sanitize_filename(self, name):
        """
        Sanitize a name for use as a filename.
        
        Args:
            name (str): The name to sanitize
            
        Returns:
            str: A sanitized filename that is safe to use on the filesystem
        """
        if not name:
            return "untitled"
            
        # Normalize the name - remove extra whitespace
        name = name.strip()
        
        # Replace spaces with underscores
        name = name.replace(' ', '_')
        
        # Remove invalid filename characters
        import re
        name = re.sub(r'[\\/*?:"<>|]', '', name)
        
        # Ensure we don't have consecutive underscores
        name = re.sub(r'_+', '_', name)
        
        # Limit length (optional)
        if len(name) > 100:
            name = name[:100]
            
        # Ensure we don't end with an underscore or period
        name = name.rstrip('_').rstrip('.')
        
        # Provide a fallback name if we end up with an empty string
        if not name:
            return "untitled"
            
        return name 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import datetime
import json

from app.utils.utils import save_json_file

class StructureOperations:
    """
    Operations for managing custom folder structures
    """
    
    def save_custom_structure(self, name, directories):
        """Save a custom folder structure"""
        if not name or not directories:
            return False
        
        # Ensure directories are properly formatted
        directories = self._normalize_structure_format(directories)
        
        structure = {
            "name": name,
            "directories": directories,
            "created": datetime.datetime.now().isoformat()
        }
        
        # Create a clean filename - always replace spaces with underscores
        filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        file_path = os.path.join(self.paths["custom_structures_dir"], f"{filename}.json")
        
        print(f"DEBUG: Saving structure '{name}' to file '{file_path}'")
        
        success = save_json_file(file_path, structure)
        if success:
            # Update in-memory cache
            self.custom_structures[name] = structure
        
        return success
    
    def delete_custom_structure(self, name):
        """Delete a custom folder structure"""
        if name not in self.custom_structures:
            return False
        
        # Create a clean filename
        filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        file_path = os.path.join(self.paths["custom_structures_dir"], f"{filename}.json")
        
        try:
            os.remove(file_path)
            del self.custom_structures[name]
            return True
        except Exception as e:
            print(f"Error deleting structure {name}: {e}")
            return False
    
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
            "created": datetime.datetime.now().isoformat()
        }
        
        # Save to file
        return self.save_custom_structure(structure["name"], unique_folders)
    
    def get_structure(self, structure_name):
        """Get a folder structure by name"""
        structure = []
        
        # Check if it's a built-in structure
        from app.constants import DEFAULT_STRUCTURES
        if structure_name in DEFAULT_STRUCTURES:
            structure = DEFAULT_STRUCTURES[structure_name]
        
        # Check if it's a custom structure
        elif structure_name in self.custom_structures:
            structure = self.custom_structures[structure_name].get("directories", [])
        
        # For compatbility with older format, ensure empty folders are dictionaries with empty lists
        if structure:
            structure = self._normalize_structure_format(structure)
        
        return structure
    
    def _normalize_structure_format(self, structure_items):
        """
        Ensure the structure items are properly formatted.
        - Folders should be dictionaries with arrays: {"folder_name": []}
        - Files should be simple strings
        """
        if not structure_items:
            return []
            
        normalized = []
        
        for item in structure_items:
            # If it's already a dictionary, process its children
            if isinstance(item, dict):
                processed_dict = {}
                
                # Get the single folder name and its children
                for folder_name, children in item.items():
                    # Process children recursively if they exist
                    if children:
                        processed_dict[folder_name] = self._normalize_structure_format(children)
                    else:
                        # Make sure empty folders are represented as empty lists
                        processed_dict[folder_name] = []
                        
                normalized.append(processed_dict)
            # If it's a string that ends with a slash (legacy format), convert to dict
            elif isinstance(item, str) and item.endswith('/'):
                folder_name = item[:-1]  # Remove the trailing slash
                normalized.append({folder_name: []})
            # If it's a regular string (file or single folder from older format)
            elif isinstance(item, str):
                # Check for revision folders (REV01, REV02, etc.)
                if item.upper().startswith('REV') and len(item) >= 4 and item[3:].isdigit():
                    print(f"Converting revision folder '{item}' to folder format during structure save")
                    normalized.append({item: []})
                # Try to detect if this is a folder based on naming convention
                elif ('.' not in item or item.startswith('_')) and not item.startswith('{{PROJECT_NAME}}'):
                    # Folders often have numeric prefixes like "1_Footage"
                    if (item.startswith(tuple("0123456789")) and '_' in item) or \
                       any(folder_keyword in item.lower() for folder_keyword in ['folder', 'dir', 'footage', 'audio', 'video', 'gfx', 'exports']):
                        print(f"Converting string '{item}' to folder format during structure save")
                        normalized.append({item: []})
                    else:
                        # It's a file or we can't be sure, leave it as is
                        normalized.append(item)
                else:
                    # It's likely a file, leave it as is
                    normalized.append(item)
            else:
                # Unknown type, add as is (though this shouldn't happen)
                normalized.append(item)
                
        return normalized
    
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
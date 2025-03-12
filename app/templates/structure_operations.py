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
    
    def _normalize_structure_format(self, structure):
        """Convert any string folder names to dictionary format with empty lists"""
        result = []
        
        if isinstance(structure, list):
            for item in structure:
                if isinstance(item, str):
                    # Convert string to dict with empty list
                    if item.endswith('/'): 
                        # Old format with trailing slash
                        folder_name = item[:-1]  # Remove trailing slash
                        result.append({folder_name: []})
                    else:
                        # Assume it's a folder if it doesn't contain a period (simple heuristic)
                        if '.' not in item:
                            result.append({item: []})
                        else:
                            # Keep files as strings
                            result.append(item)
                elif isinstance(item, dict):
                    # Process nested dictionaries recursively
                    processed_dict = {}
                    for key, value in item.items():
                        if isinstance(value, list) or isinstance(value, dict):
                            processed_dict[key] = self._normalize_structure_format(value)
                        else:
                            processed_dict[key] = []
                    result.append(processed_dict)
                else:
                    # Pass through other types
                    result.append(item)
        elif isinstance(structure, dict):
            # Convert dict to list of dicts (for compatibility with various formats)
            for key, value in structure.items():
                if isinstance(value, dict) or isinstance(value, list):
                    result.append({key: self._normalize_structure_format(value)})
                else:
                    result.append({key: []})
        
        return result
    
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
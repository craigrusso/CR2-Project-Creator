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
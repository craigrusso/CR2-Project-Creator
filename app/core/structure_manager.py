#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import datetime
import shutil
from copy import deepcopy
from app.utils.utils import get_config_paths

class StructureManager:
    """
    Manages project structures for the application.
    """
    
    def __init__(self, structures_dir=None):
        """
        Initialize the structure manager.
        
        Args:
            structures_dir: Optional directory for storing structures. If not provided,
                            the default from config will be used.
        """
        paths = get_config_paths()
        self.structures_dir = structures_dir or paths.get("custom_structures_dir")
        
        # Make sure the structures directory exists
        os.makedirs(self.structures_dir, exist_ok=True)
        
        # Dictionary to hold loaded structures
        self.structures = {}
        
        # Load all structures
        self.load_structures()
    
    def load_structures(self):
        """Load all structures from the structures directory."""
        self.structures = {}
        
        try:
            structure_files = [f for f in os.listdir(self.structures_dir) if f.endswith('.json')]
            
            for file in structure_files:
                try:
                    with open(os.path.join(self.structures_dir, file), 'r') as f:
                        structure = json.load(f)
                        
                        # Ensure structure has a name (use filename if not)
                        name = structure.get("name", os.path.splitext(file)[0])
                        
                        # Store the structure
                        self.structures[name] = structure
                except Exception as e:
                    print(f"Error loading structure {file}: {e}")
        except Exception as e:
            print(f"Error loading structures: {e}")
    
    def get_all_structures(self):
        """Get all structures as a list."""
        return list(self.structures.values())
    
    def get_structure_names(self):
        """Get a list of all structure names."""
        return list(self.structures.keys())
    
    def get_structure_by_name(self, name):
        """
        Get a structure by its name.
        
        Args:
            name: The name of the structure to retrieve.
            
        Returns:
            The structure dict if found, None otherwise.
        """
        return self.structures.get(name)
    
    def structure_exists(self, name):
        """
        Check if a structure with the given name exists.
        
        Args:
            name: The name to check.
            
        Returns:
            True if the structure exists, False otherwise.
        """
        return name in self.structures
    
    def add_structure(self, structure):
        """
        Add a new structure.
        
        Args:
            structure: The structure to add. Must be a dict with at least 'name' and 'items' keys.
            
        Returns:
            True if successful, False otherwise.
        """
        if not isinstance(structure, dict) or 'name' not in structure or 'items' not in structure:
            print("Invalid structure format")
            return False
        
        name = structure['name']
        
        # Don't overwrite existing structures without explicit update
        if name in self.structures:
            print(f"Structure '{name}' already exists")
            return False
        
        # Add to in-memory dict
        self.structures[name] = structure
        
        # Save to file
        try:
            # Create a clean filename
            filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
            file_path = os.path.join(self.structures_dir, f"{filename}.json")
            
            with open(file_path, 'w') as f:
                json.dump(structure, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving structure '{name}': {e}")
            # Roll back in-memory change
            if name in self.structures:
                del self.structures[name]
            return False
    
    def update_structure(self, structure):
        """
        Update an existing structure.
        
        Args:
            structure: The updated structure. Must have the same 'name' as an existing structure.
            
        Returns:
            True if successful, False otherwise.
        """
        if not isinstance(structure, dict) or 'name' not in structure:
            print("Invalid structure format")
            return False
        
        name = structure['name']
        
        # Structure must exist to be updated
        if name not in self.structures:
            print(f"Structure '{name}' does not exist")
            return False
        
        # Update in-memory dict
        self.structures[name] = structure
        
        # Save to file
        try:
            # Create a clean filename
            filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
            file_path = os.path.join(self.structures_dir, f"{filename}.json")
            
            with open(file_path, 'w') as f:
                json.dump(structure, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error updating structure '{name}': {e}")
            return False
    
    def delete_structure(self, name):
        """
        Delete a structure by name.
        
        Args:
            name: The name of the structure to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        if name not in self.structures:
            print(f"Structure '{name}' does not exist")
            return False
        
        # Remove from in-memory dict
        structure = self.structures.pop(name)
        
        # Delete file
        try:
            # Create a clean filename
            filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
            file_path = os.path.join(self.structures_dir, f"{filename}.json")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                
            return True
        except Exception as e:
            print(f"Error deleting structure '{name}': {e}")
            # Roll back in-memory change
            self.structures[name] = structure
            return False
    
    def duplicate_structure(self, name, new_name):
        """
        Duplicate a structure with a new name.
        
        Args:
            name: The name of the structure to duplicate.
            new_name: The name for the duplicated structure.
            
        Returns:
            True if successful, False otherwise.
        """
        if name not in self.structures:
            print(f"Structure '{name}' does not exist")
            return False
            
        if new_name in self.structures:
            print(f"Structure '{new_name}' already exists")
            return False
        
        # Create a deep copy of the structure
        structure = deepcopy(self.structures[name])
        
        # Update the name
        structure['name'] = new_name
        
        # Add creation timestamp if not present
        if 'created' not in structure:
            structure['created'] = datetime.datetime.now().isoformat()
            
        # Add as a new structure
        return self.add_structure(structure) 
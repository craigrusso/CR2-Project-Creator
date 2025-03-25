#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import importlib
import json
import datetime
import time

from app.templates.template_manager_core import TemplateManagerCore
from app.templates.template_operations import TemplateOperations
from app.templates.structure_operations import StructureOperations
from app.templates.folder_operations import FolderOperations
from app.templates.ui_operations import UIOperations
from app.utils.utils import get_config_paths

class TemplateManager(TemplateManagerCore, StructureOperations, FolderOperations, UIOperations):
    """
    Manages project templates and custom structures.
    
    This class combines functionality from:
    - TemplateManagerCore: Core initialization and basic operations
    - StructureOperations: Custom structure operations
    - FolderOperations: Folder management operations
    - UIOperations: UI-related operations
    
    The inheritance order is important for proper initialization.
    """
    def __init__(self):
        """Initialize the template manager"""
        # Initialize core first to set up paths and basic attributes
        TemplateManagerCore.__init__(self)
        
        # Initialize mixins after core initialization
        StructureOperations.__init__(self)
        FolderOperations.__init__(self)
        UIOperations.__init__(self)
        
        # Initialize additional attributes for multi-selection
        self.multi_selected_templates = []

    def move_template_to_folder(self, template_name, folder_name):
        """Move a template to a folder, ensuring it's removed from other folders first"""
        print(f"[DEBUG] FolderOps: Moving template '{template_name}' to folder '{folder_name}'")
        
        # Validate input
        if not template_name or not folder_name:
            print(f"[DEBUG] FolderOps: Invalid template or folder name: '{template_name}', '{folder_name}'")
            return False
        
        try:
            # Make sure the template exists
            template = None
            for t in self.templates + self.template_directories:
                if isinstance(t, dict) and t.get('name') == template_name:
                    template = t
                    break
            
            if not template:
                print(f"[DEBUG] FolderOps: Template '{template_name}' not found")
                return False
            
            # Make sure the folder exists
            if folder_name not in self.folders:
                print(f"[DEBUG] FolderOps: Folder '{folder_name}' not found")
                return False
            
            # First, remove the template from all folders to avoid duplicates
            for f in self.folders:
                if template_name in self.folders[f]:
                    print(f"[DEBUG] FolderOps: Removing '{template_name}' from folder '{f}'")
                    self.folders[f].remove(template_name)
            
            # Now add the template to the target folder
            print(f"[DEBUG] FolderOps: Adding '{template_name}' to folder '{folder_name}'")
            if template_name not in self.folders[folder_name]:
                self.folders[folder_name].append(template_name)
            
            # Save the folders to disk
            print(f"[DEBUG] FolderOps: Saving folders after move")
            self.save_folders()
            
            # Return a list of templates actually in the folder after cleaning
            cleaned_list = self.get_templates_in_folder(folder_name)
            print(f"[DEBUG] FolderOps: Returning cleaned template list: {cleaned_list}")
            
            return True
        except Exception as e:
            import traceback
            print(f"[DEBUG] FolderOps: Error moving template to folder: {e}")
            traceback.print_exc()
            return False

    def create_folder(self, folder_name):
        """Create a new folder with the given name.
        
        Args:
            folder_name (str): Name of the folder to create
            
        Returns:
            bool: True if folder was created successfully, False otherwise
        """
        print(f"[DEBUG] FolderOps: Creating folder '{folder_name}'")
        
        # Validate input
        if not folder_name or not isinstance(folder_name, str):
            print(f"[DEBUG] FolderOps: Invalid folder name: '{folder_name}'")
            return False
        
        # Trim whitespace
        folder_name = folder_name.strip()
        
        if not folder_name:
            print(f"[DEBUG] FolderOps: Empty folder name after trimming")
            return False
        
        # Check if folder already exists
        if folder_name in self.folders:
            print(f"[DEBUG] FolderOps: Folder '{folder_name}' already exists")
            return False
        
        try:
            # Create the new folder
            self.folders[folder_name] = []
            
            # Save the folders to disk
            print(f"[DEBUG] FolderOps: Saving folders after creation")
            self.save_folders()
            
            # Update UI if we have a template gallery
            if hasattr(self, 'app') and hasattr(self.app, 'template_gallery'):
                # Schedule a UI update on the main thread
                from PyQt5.QtCore import QTimer
                from PyQt5.QtWidgets import QApplication
                
                def update_ui():
                    self.app.template_gallery.populate_gallery(force_refresh=True)
                    self.app.template_gallery.update()
                    
                    # Process events to ensure UI updates
                    QApplication.processEvents()
                
                # Use a very short timer to ensure this happens after current event processing
                QTimer.singleShot(10, update_ui)
            
            return True
        except Exception as e:
            import traceback
            print(f"[DEBUG] FolderOps: Error creating folder: {e}")
            traceback.print_exc()
            return False

    def save_custom_structure(self, name, structure):
        """Save a custom structure to disk"""
        print(f"\n[DEBUG] TemplateManager.save_custom_structure: Starting save for '{name}'")
        
        try:
            # Ensure the custom structures directory exists
            os.makedirs(self.paths["custom_structures_dir"], exist_ok=True)
            
            # Check if we're updating an existing structure
            existing_path = None
            is_update = False
            
            # Look for existing file with this name
            for filename in os.listdir(self.paths["custom_structures_dir"]):
                if filename.startswith(name.replace(" ", "_")) and filename.endswith(".json"):
                    existing_path = os.path.join(self.paths["custom_structures_dir"], filename)
                    is_update = True
                    print(f"[DEBUG] Found existing structure file: {existing_path}")
                    break
            
            # Create structure data
            structure_data = {
                "name": name,
                "type": "custom",
                "directories": structure,
                "created": datetime.datetime.now().isoformat()
            }
            
            print(f"[DEBUG] Structure data prepared: {structure_data}")
            
            # If we're updating an existing file, read it to preserve metadata
            if is_update and existing_path:
                try:
                    print("[DEBUG] Reading existing structure to preserve metadata")
                    with open(existing_path, 'r') as f:
                        existing_data = json.load(f)
                        
                    # Preserve creation timestamp and other metadata
                    if 'created' in existing_data:
                        structure_data['created'] = existing_data['created']
                    
                    # Preserve any other metadata fields that aren't being explicitly updated
                    for key, value in existing_data.items():
                        if key not in structure_data and key != 'directories':
                            structure_data[key] = value
                            
                    # Add modified timestamp
                    structure_data['modified'] = datetime.datetime.now().isoformat()
                    
                    print("[DEBUG] Preserved metadata from existing structure")
                except Exception as e:
                    print(f"[ERROR] Error reading existing structure: {e}")
                    # Continue with saving as new if read fails
            
            # Store in memory - important to store the whole structure_data object
            self.custom_structures[name] = structure_data
            print(f"[DEBUG] Updated in-memory structure cache")
            
            # Determine file path - use existing path if updating, otherwise create new
            if is_update and existing_path:
                file_path = existing_path
            else:
                # Create a clean filename
                filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
                file_path = os.path.join(self.paths["custom_structures_dir"], f"{filename}.json")
            
            print(f"[DEBUG] Saving structure to: {file_path}")
            
            # Make sure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the structure file
            with open(file_path, 'w') as f:
                json.dump(structure_data, f, indent=2)
                
            print("[DEBUG] Structure saved successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to save structure: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

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

    def get_template_info(self, template_name):
        """
        Get template information for a given template name.
        This is a compatibility method that works with both older and newer APIs.
        
        Args:
            template_name (str): Name of the template
            
        Returns:
            dict: Template information including name, description, tags, etc.
        """
        if not template_name:
            print(f"DEBUG: get_template_info called with empty name")
            return None
        
        # First try using the get_template method if available
        template = self.get_template(template_name)
        if template:
            return template
        
        # If template not found, try to look for it in custom structures
        if hasattr(self, 'custom_structures') and template_name in self.custom_structures:
            structure_data = self.custom_structures[template_name]
            # Convert structure data to template info format
            template_info = {
                "name": template_name,
                "description": structure_data.get("description", f"Structure for {template_name}"),
                "tags": structure_data.get("tags", []),
                "structure_name": template_name
            }
            return template_info
        
        # Try to find a structure file with this name
        try:
            structure_path = os.path.join(self.paths["custom_structures_dir"], 
                                         f"{template_name.replace(' ', '_')}.json")
            if os.path.exists(structure_path):
                with open(structure_path, 'r') as f:
                    structure_data = json.load(f)
                    # Convert structure data to template info format
                    template_info = {
                        "name": template_name,
                        "description": structure_data.get("description", f"Structure for {template_name}"),
                        "tags": structure_data.get("tags", []),
                        "structure_name": template_name
                    }
                    return template_info
        except Exception as e:
            print(f"DEBUG: Error loading structure file for template info: {e}")
        
        # If nothing found, return a basic template info with default values
        print(f"DEBUG: Template info not found for {template_name}, returning default")
        return {
            "name": template_name,
            "description": f"Template {template_name}",
            "tags": [],
            "category": "General"
        }

    def rename_template(self, oldname, newname):
        """Rename a template and update its references, but keep structure files intact."""
        print(f"🔄 TEMPLATE MANAGER: Renaming template '{oldname}' to '{newname}'")
        
        # Get current timestamp for file operations
        timestamp = datetime.datetime.now().isoformat()
        print(f"🔄 TEMPLATE MANAGER: Current timestamp: {timestamp}")
        
        # Make sure we have valid names
        if not oldname or not newname:
            print(f"❌ TEMPLATE MANAGER: Invalid template names for rename: old='{oldname}', new='{newname}'")
            return False
        
        # Get the template object by name
        template = self.get_template_by_name(oldname)
        if not template:
            print(f"❌ TEMPLATE MANAGER: Template '{oldname}' not found for renaming")
            return False
            
        # Keep a reference to the original template for file handling
        original_template = template.copy()
        
        # Find the actual template file path before we update the name
        old_template_path = None
        template_path_variants = [
            os.path.join(self.paths["templates_dir"], f"{oldname.replace(' ', '_')}.json"),
            os.path.join(self.paths["templates_dir"], f"{oldname}.json")
        ]
        for path in template_path_variants:
            if os.path.exists(path):
                old_template_path = path
                print(f"🔄 TEMPLATE MANAGER: Found original template file at: {old_template_path}")
                break
        
        if not old_template_path:
            print(f"⚠️ TEMPLATE MANAGER: Could not find original template file for '{oldname}'")
            # Fall back to the standard path format
            old_template_path = os.path.join(self.paths["templates_dir"], f"{oldname.replace(' ', '_')}.json")
        
        # Keep track of the structure name - we won't rename it
        structure_name = original_template.get('structure_name', None)
        if not structure_name:
            # If no structure name is explicitly set, it might use the default convention
            structure_name = f"Template_{oldname}"
            print(f"🔄 TEMPLATE MANAGER: Using default structure name: '{structure_name}'")
        
        # Update template name in the object
        template['name'] = newname
        
        # IMPORTANT: Keep the structure name reference unchanged
        # This ensures the template continues to point to the same structure
        # Only update the template's name, not its linked structure
        
        # Determine where the new template file should be saved
        new_template_path = os.path.join(self.paths["templates_dir"], f"{newname.replace(' ', '_')}.json")
        print(f"🔄 TEMPLATE MANAGER: Will save template to new location: {new_template_path}")
        
        # Save the updated template to disk
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(new_template_path), exist_ok=True)
            
            # Update cached_path field if it exists and templates_cache_dir is available
            if 'cached_path' in template and 'templates_cache_dir' in self.paths:
                template['cached_path'] = os.path.join(self.paths["templates_cache_dir"], f"{newname.replace(' ', '_')}")
            elif 'cached_path' in template:
                # Remove the cached_path if we can't update it properly
                template.pop('cached_path', None)
                print(f"⚠️ TEMPLATE MANAGER: Removed cached_path from template because templates_cache_dir is not available")
            
            # Write the template file
            with open(new_template_path, 'w') as f:
                json.dump(template, f, indent=2)
                
            print(f"✅ TEMPLATE MANAGER: Successfully saved template file to {new_template_path}")
        except Exception as e:
            print(f"❌ TEMPLATE MANAGER: Error saving template file: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        # If the old and new paths are different, delete the old template file
        if old_template_path != new_template_path and os.path.exists(old_template_path):
            try:
                os.remove(old_template_path)
                print(f"✅ TEMPLATE MANAGER: Deleted old template file: {old_template_path}")
            except Exception as e:
                print(f"⚠️ TEMPLATE MANAGER: Error deleting old template file: {e}")
        
        # Update references in templates list
        if hasattr(self, 'templates'):
            updated_in_list = False
            for i, t in enumerate(self.templates):
                if isinstance(t, dict) and t.get('name') == oldname:
                    # Update with our modified template object that has the new name
                    self.templates[i] = template
                    updated_in_list = True
                    print(f"🔄 TEMPLATE MANAGER: Updated template entry in templates list")
                    break
                
            if not updated_in_list:
                # If not found, add it
                print(f"🔄 TEMPLATE MANAGER: Template not found in templates list, adding it")
                self.templates.append(template)
        
        # Update references in folders
        if hasattr(self, 'folders'):
            for folder_name in self.folders:
                if isinstance(self.folders[folder_name], list) and oldname in self.folders[folder_name]:
                    self.folders[folder_name].remove(oldname)
                    self.folders[folder_name].append(newname)
                    print(f"🔄 TEMPLATE MANAGER: Updated template reference in folder '{folder_name}'")
            
            # Save the updated folders
            self.save_folders()
        
        # Force a reload of templates to ensure everything is up to date
        self.load_templates()
        
        # Notify any listeners that templates have been updated
        if hasattr(self, 'on_templates_updated') and callable(self.on_templates_updated):
            self.on_templates_updated()
        
        print(f"✅ TEMPLATE MANAGER: Successfully renamed template '{oldname}' to '{newname}'")
        return True

    def update_references(self, old_name, new_name):
        """Update all references to a template name in the template manager
        
        Args:
            old_name: Old template name
            new_name: New template name
        """
        # Update template references in internal lists
        updated = False
        for i, template in enumerate(self.templates):
            if template.get('name') == old_name:
                self.templates[i]['name'] = new_name
                updated = True
                print(f"DEBUG: TemplateManager updated template reference from '{old_name}' to '{new_name}'")
        
        # Update template name in folders
        if hasattr(self, 'template_folders'):
            for folder_name, templates in self.template_folders.items():
                if old_name in templates:
                    templates.remove(old_name)
                    templates.append(new_name)
                    updated = True
                    print(f"DEBUG: TemplateManager updated template reference in folder '{folder_name}'")
        
        # Save folders if any references were updated
        if updated and hasattr(self, 'save_folders'):
            self.save_folders()
        
        return updated

    def _get_structure_path(self, structure_name):
        """
        Helper method to get the file path for a structure by name.
        Handles various name formats and returns the path if the file exists.
        
        Args:
            structure_name (str): The name of the structure (with or without Template_ prefix)
        
        Returns:
            str: The full path to the structure file if it exists, otherwise None
        """
        if not structure_name:
            return None
        
        # Generate all possible filename variations
        variations = [
            structure_name,                             # Original name
            structure_name.replace(' ', '_'),           # With underscores
            structure_name.replace('_', ' '),           # With spaces
        ]
        
        # If it doesn't start with Template_, add variations with the prefix
        if not structure_name.startswith("Template_"):
            variations.extend([
                f"Template_{structure_name}",                   # With Template_ prefix
                f"Template_{structure_name.replace(' ', '_')}"  # With Template_ prefix and underscores
            ])
        
        # Try each variation
        for variant in variations:
            # Clean up any potentially problematic characters for filenames
            safe_variant = variant.replace("/", "-").replace("\\", "-").replace("'", "")
            path = os.path.join(self.paths["custom_structures_dir"], f"{safe_variant}.json")
            if os.path.exists(path):
                return path
        
        return None

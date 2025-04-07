#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Structure Utilities
Provides tools for working with structure data, including validation,
normalization, and conversion between different structure formats.
"""

import os
import json
from pathlib import Path

class StructureUtils:
    """
    Utilities for working with structure data
    
    This class provides methods for validating, normalizing, and converting
    structure data to ensure it's in a consistent format for storage and retrieval.
    """
    
    @staticmethod
    def normalize_structure(structure):
        """
        Normalize a structure to ensure consistent format
        
        Args:
            structure: The structure data to normalize
            
        Returns:
            dict: Normalized structure data
        """
        if not structure:
            return []
            
        # If it's already a list (most common case)
        if isinstance(structure, list):
            return [StructureUtils.normalize_item(item) for item in structure]
            
        # If it's a dictionary with 'directories' key (old format)
        if isinstance(structure, dict) and 'directories' in structure:
            return [StructureUtils.normalize_item(item) for item in structure['directories']]
            
        # If it's a dictionary but not in the expected format
        if isinstance(structure, dict) and not any(k in structure for k in ['type', 'name']):
            # It might be a dictionary with folder names as keys
            result = []
            for folder_name, children in structure.items():
                folder_item = {'type': 'folder', 'name': folder_name}
                if children:
                    folder_item['children'] = StructureUtils.normalize_structure(children)
                result.append(folder_item)
            return result
            
        # Single item case
        return [StructureUtils.normalize_item(structure)]
    
    @staticmethod
    def normalize_item(item):
        """
        Normalize a single structure item
        
        Args:
            item: The item to normalize
            
        Returns:
            dict: Normalized item data
        """
        # String case (simple file or folder name)
        if isinstance(item, str):
            # If it ends with a slash, it's a folder
            if item.endswith('/'):
                return {'type': 'folder', 'name': item.rstrip('/')}
            else:
                return {'type': 'file', 'name': item}
                
        # Dictionary case with one key (folder with children)
        if isinstance(item, dict) and len(item) == 1 and not any(k in item for k in ['type', 'name']):
            folder_name = list(item.keys())[0]
            children = item[folder_name]
            
            return {
                'type': 'folder',
                'name': folder_name,
                'children': StructureUtils.normalize_structure(children)
            }
            
        # Dictionary with explicit type
        if isinstance(item, dict) and 'type' in item:
            # Start with a copy of the item
            normalized = item.copy()
            
            # Ensure 'name' is a string
            if 'name' in normalized:
                if isinstance(normalized['name'], list):
                    if normalized['name']:
                        normalized['name'] = str(normalized['name'][0])
                    else:
                        normalized['name'] = ""
                elif not isinstance(normalized['name'], str):
                    normalized['name'] = str(normalized['name'])
                    
            # Ensure 'type' is a string
            if 'type' in normalized and not isinstance(normalized['type'], str):
                if isinstance(normalized['type'], list) and normalized['type']:
                    normalized['type'] = str(normalized['type'][0])
                else:
                    normalized['type'] = 'file'  # Default to file
                    
            # Ensure 'is_binary' is a boolean
            if 'is_binary' in normalized:
                if isinstance(normalized['is_binary'], list):
                    normalized['is_binary'] = bool(normalized['is_binary'][0]) if normalized['is_binary'] else False
                else:
                    normalized['is_binary'] = bool(normalized['is_binary'])
                    
            # Process children if it's a folder
            if normalized.get('type') == 'folder' and 'children' in normalized:
                normalized['children'] = StructureUtils.normalize_structure(normalized['children'])
                
            return normalized
            
        # Unknown format, default to file
        return {'type': 'file', 'name': str(item)}
    
    @staticmethod
    def validate_structure(structure):
        """
        Validate a structure to ensure it's in the correct format
        
        Args:
            structure: The structure data to validate
            
        Returns:
            tuple: (is_valid, errors)
        """
        errors = []
        
        if not structure:
            return True, []
            
        # Structure must be a list or dictionary
        if not isinstance(structure, (list, dict)):
            errors.append(f"Structure must be a list or dictionary, got {type(structure)}")
            return False, errors
            
        # If it's a list, validate each item
        if isinstance(structure, list):
            for i, item in enumerate(structure):
                is_valid, item_errors = StructureUtils.validate_item(item, f"item[{i}]")
                if not is_valid:
                    errors.extend(item_errors)
            return len(errors) == 0, errors
            
        # If it's a dictionary with 'directories' key (old format)
        if isinstance(structure, dict) and 'directories' in structure:
            directories = structure['directories']
            if not isinstance(directories, list):
                errors.append(f"'directories' must be a list, got {type(directories)}")
                return False, errors
                
            for i, item in enumerate(directories):
                is_valid, item_errors = StructureUtils.validate_item(item, f"directories[{i}]")
                if not is_valid:
                    errors.extend(item_errors)
            return len(errors) == 0, errors
            
        # If it's a single item, validate it
        is_valid, item_errors = StructureUtils.validate_item(structure, "structure")
        if not is_valid:
            errors.extend(item_errors)
            
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_item(item, path=""):
        """
        Validate a single structure item
        
        Args:
            item: The item to validate
            path: Path to the item for error reporting
            
        Returns:
            tuple: (is_valid, errors)
        """
        errors = []
        
        # String case (simple file or folder name)
        if isinstance(item, str):
            return True, []
            
        # Dictionary case
        if isinstance(item, dict):
            # Dictionary with one key (folder with children)
            if len(item) == 1 and not any(k in item for k in ['type', 'name']):
                folder_name = list(item.keys())[0]
                children = item[folder_name]
                
                if not isinstance(children, list):
                    errors.append(f"{path}: Folder '{folder_name}' children must be a list, got {type(children)}")
                    return False, errors
                    
                for i, child in enumerate(children):
                    is_valid, child_errors = StructureUtils.validate_item(child, f"{path}.{folder_name}[{i}]")
                    if not is_valid:
                        errors.extend(child_errors)
                        
                return len(errors) == 0, errors
                
            # Dictionary with explicit type
            if 'type' in item:
                item_type = item['type']
                
                # Convert list to string if needed
                if isinstance(item_type, list):
                    if item_type:
                        item_type = str(item_type[0])
                    else:
                        errors.append(f"{path}: Empty type list")
                        return False, errors
                        
                # Type must be a string
                if not isinstance(item_type, str):
                    errors.append(f"{path}: Type must be a string, got {type(item_type)}")
                    return False, errors
                    
                # Name is required
                if 'name' not in item:
                    errors.append(f"{path}: Name is required for items with type")
                    return False, errors
                    
                # Name must be a string (or convertible to string)
                item_name = item['name']
                if isinstance(item_name, list):
                    if not item_name:
                        errors.append(f"{path}: Empty name list")
                        return False, errors
                        
                # Check for folders with children
                if item_type == 'folder' and 'children' in item:
                    children = item['children']
                    
                    if not isinstance(children, list):
                        errors.append(f"{path}: Folder children must be a list, got {type(children)}")
                        return False, errors
                        
                    for i, child in enumerate(children):
                        is_valid, child_errors = StructureUtils.validate_item(child, f"{path}.children[{i}]")
                        if not is_valid:
                            errors.extend(child_errors)
                            
                return len(errors) == 0, errors
                
            # Dictionary without type - legacy format?
            if 'name' in item:
                return True, []
                
            # Unknown dictionary format
            errors.append(f"{path}: Unknown dictionary format: {item.keys()}")
            return False, errors
            
        # Unknown type
        errors.append(f"{path}: Unknown item type: {type(item)}")
        return False, errors
    
    @staticmethod
    def structure_to_json(structure, pretty=True):
        """
        Convert a structure to a JSON string
        
        Args:
            structure: The structure data to convert
            pretty: Whether to format the JSON with indentation
            
        Returns:
            str: JSON string representation of the structure
        """
        # Normalize the structure first
        normalized = StructureUtils.normalize_structure(structure)
        
        # Convert to JSON
        if pretty:
            return json.dumps(normalized, indent=2)
        else:
            return json.dumps(normalized)
    
    @staticmethod
    def json_to_structure(json_str):
        """
        Convert a JSON string to a structure
        
        Args:
            json_str: JSON string to convert
            
        Returns:
            list: Normalized structure data
        """
        try:
            data = json.loads(json_str)
            return StructureUtils.normalize_structure(data)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return []
    
    @staticmethod
    def save_structure(structure, file_path, pretty=True):
        """
        Save a structure to a JSON file
        
        Args:
            structure: The structure data to save
            file_path: Path to save the file
            pretty: Whether to format the JSON with indentation
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Normalize the structure
            normalized = StructureUtils.normalize_structure(structure)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(normalized, f, indent=2)
                else:
                    json.dump(normalized, f)
                    
            return True
        except Exception as e:
            print(f"Error saving structure: {e}")
            return False
    
    @staticmethod
    def load_structure(file_path):
        """
        Load a structure from a JSON file
        
        Args:
            file_path: Path to the file
            
        Returns:
            list: Normalized structure data
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return StructureUtils.normalize_structure(data)
        except Exception as e:
            print(f"Error loading structure: {e}")
            return [] 
#!/usr/bin/env python3
"""
Template Sanitizer Utility

This utility cleans up corrupted template files that have infinite nesting
of user_data structures, which was causing JSON files to grow exponentially.
"""

import os
import json
import shutil
from typing import Dict, List, Any, Union


class TemplateSanitizer:
    """Utility class to clean up corrupted template structures"""
    
    def __init__(self):
        self.cleaned_count = 0
        self.error_count = 0
        self.backup_suffix = ".backup"
    
    def sanitize_template_file(self, file_path: str, create_backup: bool = True) -> bool:
        """
        Sanitize a single template file
        
        Args:
            file_path: Path to the template JSON file
            create_backup: Whether to create a backup before modifying
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read the original file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if sanitization is needed
            if not self._needs_sanitization(data):
                print(f"✓ {os.path.basename(file_path)} - Already clean")
                return True
            
            # Create backup if requested
            if create_backup:
                backup_path = file_path + self.backup_suffix
                shutil.copy2(file_path, backup_path)
                print(f"📁 Created backup: {backup_path}")
            
            # Sanitize the data
            sanitized_data = self._sanitize_structure(data)
            
            # Write the cleaned data back
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sanitized_data, f, indent=4)
            
            self.cleaned_count += 1
            print(f"🧹 Cleaned: {os.path.basename(file_path)}")
            return True
            
        except Exception as e:
            self.error_count += 1
            print(f"❌ Error processing {file_path}: {e}")
            return False
    
    def sanitize_directory(self, directory_path: str, create_backup: bool = True) -> Dict[str, int]:
        """
        Sanitize all template files in a directory
        
        Args:
            directory_path: Path to directory containing template files
            create_backup: Whether to create backups before modifying
            
        Returns:
            dict: Statistics about the operation
        """
        if not os.path.isdir(directory_path):
            print(f"❌ Directory not found: {directory_path}")
            return {"processed": 0, "cleaned": 0, "errors": 0}
        
        self.cleaned_count = 0
        self.error_count = 0
        processed_count = 0
        
        print(f"🔍 Scanning directory: {directory_path}")
        
        for filename in os.listdir(directory_path):
            if filename.endswith('.json') and not filename.endswith(self.backup_suffix):
                file_path = os.path.join(directory_path, filename)
                if os.path.isfile(file_path):
                    processed_count += 1
                    self.sanitize_template_file(file_path, create_backup)
        
        return {
            "processed": processed_count,
            "cleaned": self.cleaned_count,
            "errors": self.error_count
        }
    
    def _needs_sanitization(self, data: Any) -> bool:
        """Check if data structure needs sanitization"""
        return self._has_nested_user_data(data)
    
    def _has_nested_user_data(self, data: Any, depth: int = 0) -> bool:
        """Check for nested user_data structures"""
        if depth > 20:  # Prevent infinite recursion
            return True
        
        if isinstance(data, dict):
            if 'user_data' in data:
                user_data = data['user_data']
                if isinstance(user_data, dict) and 'user_data' in user_data:
                    return True  # Found nested user_data
            
            for value in data.values():
                if self._has_nested_user_data(value, depth + 1):
                    return True
                    
        elif isinstance(data, list):
            for item in data:
                if self._has_nested_user_data(item, depth + 1):
                    return True
        
        return False
    
    def _sanitize_structure(self, data: Any) -> Any:
        """Recursively sanitize data structure"""
        if isinstance(data, dict):
            sanitized = {}
            
            for key, value in data.items():
                if key == 'structure' and isinstance(value, list):
                    # Special handling for structure arrays
                    sanitized[key] = [self._sanitize_structure_item(item) for item in value]
                elif key == 'user_data':
                    # Flatten user_data - extract only essential keys
                    sanitized.update(self._extract_essential_data(value))
                else:
                    sanitized[key] = self._sanitize_structure(value)
            
            return sanitized
            
        elif isinstance(data, list):
            return [self._sanitize_structure(item) for item in data]
        
        return data
    
    def _sanitize_structure_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize a single structure item"""
        if not isinstance(item, dict):
            return item
        
        sanitized = {}
        
        # Essential keys to preserve
        essential_keys = [
            'name', 'type', 'original_path', 'path', 'rename_flag', 
            'uses_project_name', 'is_binary', 'pattern', 'separator',
            'custom_separator', 'date_format_text', 'time_format_text',
            'uses_custom_pattern', 'original_name'
        ]
        
        # Copy essential keys
        for key in essential_keys:
            if key in item:
                sanitized[key] = item[key]
        
        # Handle children recursively
        if 'children' in item and isinstance(item['children'], list):
            sanitized['children'] = [
                self._sanitize_structure_item(child) for child in item['children']
            ]
        
        # Extract data from nested user_data if present
        if 'user_data' in item:
            essential_data = self._extract_essential_data(item['user_data'])
            # Only add keys that aren't already present
            for key, value in essential_data.items():
                if key not in sanitized:
                    sanitized[key] = value
        
        return sanitized
    
    def _extract_essential_data(self, user_data: Any, depth: int = 0) -> Dict[str, Any]:
        """Extract essential data from potentially nested user_data"""
        if depth > 10 or not isinstance(user_data, dict):
            return {}
        
        essential = {}
        essential_keys = [
            'pattern', 'separator', 'custom_separator', 'date_format_text',
            'time_format_text', 'uses_custom_pattern', 'custom_options'
        ]
        
        for key in essential_keys:
            if key in user_data and not isinstance(user_data[key], dict):
                essential[key] = user_data[key]
        
        # If there's nested user_data, extract from it too
        if 'user_data' in user_data:
            nested_essential = self._extract_essential_data(user_data['user_data'], depth + 1)
            # Only add keys that aren't already present
            for key, value in nested_essential.items():
                if key not in essential:
                    essential[key] = value
        
        return essential


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up corrupted template files')
    parser.add_argument('path', help='Path to template file or directory')
    parser.add_argument('--no-backup', action='store_true', 
                       help='Skip creating backup files')
    
    args = parser.parse_args()
    
    sanitizer = TemplateSanitizer()
    
    if os.path.isfile(args.path):
        # Single file
        success = sanitizer.sanitize_template_file(args.path, not args.no_backup)
        if success:
            print("✅ Template sanitization completed successfully")
        else:
            print("❌ Template sanitization failed")
            return 1
    elif os.path.isdir(args.path):
        # Directory
        stats = sanitizer.sanitize_directory(args.path, not args.no_backup)
        print(f"\n📊 Sanitization Summary:")
        print(f"   Processed: {stats['processed']} files")
        print(f"   Cleaned: {stats['cleaned']} files")
        print(f"   Errors: {stats['errors']} files")
        
        if stats['errors'] > 0:
            return 1
    else:
        print(f"❌ Path not found: {args.path}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main()) 
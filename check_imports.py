#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
This script checks for any problematic imports in the codebase after our 
folder management system unification.
"""

import os
import re
import sys

# Files we've deleted or want to check for references to
PROBLEMATIC_IMPORTS = [
    'enhanced_template_manager',
    'TemplateManagerEnhanced',
    'enhanced_template_card',
    'TemplateCardEnhanced',
]

def search_file(file_path, patterns):
    """Search a file for any of the given patterns"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    return [(pattern, match) for match in matches]
        return []
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def search_directory(dir_path, patterns, exclude_dirs=None):
    """Recursively search a directory for files that contain any of the patterns"""
    results = {}
    
    if exclude_dirs is None:
        exclude_dirs = ['.git', '__pycache__', '.cursor']
    
    for root, dirs, files in os.walk(dir_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                matches = search_file(file_path, patterns)
                if matches:
                    results[file_path] = matches
    
    return results

def main():
    """Main function"""
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Create search patterns for imports
    patterns = [
        f'import.*{pattern}' for pattern in PROBLEMATIC_IMPORTS
    ] + [
        f'from.*{pattern}' for pattern in PROBLEMATIC_IMPORTS
    ]
    
    print(f"Searching for problematic imports in {project_root}...")
    print(f"Patterns: {patterns}")
    
    # Search for problematic imports
    results = search_directory(project_root, patterns)
    
    # Print results
    if results:
        print("\nFound problematic imports in the following files:")
        for file_path, matches in results.items():
            rel_path = os.path.relpath(file_path, project_root)
            print(f"\n{rel_path}:")
            for pattern, match in matches:
                print(f"  - {match}")
        
        print("\nPlease fix these imports before running the app.")
        return 1
    else:
        print("\nNo problematic imports found.")
        return 0

if __name__ == '__main__':
    sys.exit(main()) 
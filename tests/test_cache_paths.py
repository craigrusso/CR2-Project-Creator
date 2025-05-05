#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to verify template cache paths and structure
"""

import os
import json
from app.utils.file_cache_manager import FileCacheManager
from app.utils.cache_preferences import CachePreferences
from app.templates.template_manager import TemplateManager

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 50)
    print(f" {title}")
    print("=" * 50)

def main():
    # Check cache preferences
    print_section("Cache Preferences")
    cache_prefs = CachePreferences()
    cache_enabled = cache_prefs.should_cache_files()
    cache_location = cache_prefs.get_cache_location()
    
    print(f"Cache enabled: {cache_enabled}")
    print(f"Cache location: {cache_location}")
    
    # Check if cache location exists
    if cache_location and os.path.exists(cache_location):
        print(f"Cache directory exists: {os.path.exists(cache_location)}")
    else:
        print(f"Cache directory does not exist: {cache_location}")
        os.makedirs(cache_location, exist_ok=True)
        print(f"Created cache directory: {cache_location}")
    
    # Initialize cache manager
    print_section("Cache Manager")
    cache_manager = FileCacheManager(cache_location)
    cache_stats = cache_manager.get_cache_stats()
    print(f"Cache stats: {json.dumps(cache_stats, indent=2)}")
    
    # List all template caches
    print_section("Template Caches")
    for item in os.listdir(cache_location):
        item_path = os.path.join(cache_location, item)
        if os.path.isdir(item_path) and item != "cache_stats.json":
            print(f"\nTemplate: {item}")
            
            # Check for metadata.json
            metadata_path = os.path.join(item_path, "metadata.json")
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    print(f"  Last updated: {metadata.get('last_updated', 'unknown')}")
                    print(f"  Files count: {len(metadata.get('files', {}))}")
                    
                    # List all files in metadata
                    for file_key, file_info in metadata.get('files', {}).items():
                        print(f"  - {file_key}")
                        print(f"    Cache path: {file_info.get('cache_path', 'unknown')}")
                        cache_path_exists = os.path.exists(file_info.get('cache_path', ''))
                        print(f"    Cache file exists: {cache_path_exists}")
                except Exception as e:
                    print(f"  Error reading metadata: {e}")
            else:
                print("  No metadata.json found")
            
            # List actual files in cache directory
            files_dir = os.path.join(item_path, "files")
            if os.path.exists(files_dir):
                print("\n  Files in cache directory:")
                for root, dirs, files in os.walk(files_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, files_dir)
                        print(f"  - {rel_path} ({os.path.getsize(file_path)} bytes)")
            else:
                print("  No files directory found")
    
    # Check echelon cache directory
    echelon_dir = os.path.expanduser("~/.echelon")
    print_section("Echelon Directories")
    if os.path.exists(echelon_dir):
        print(f"Echelon directory: {echelon_dir}")
        
        # Check templates dir
        templates_dir = os.path.join(echelon_dir, "templates")
        if os.path.exists(templates_dir):
            print(f"Templates directory: {templates_dir}")
            
            # List template files
            print("\nTemplate files:")
            for item in os.listdir(templates_dir):
                if item.endswith(".json"):
                    print(f"- {item}")
            
            # Check template cache
            templates_cache_dir = os.path.join(templates_dir, "cache")
            if os.path.exists(templates_cache_dir):
                print(f"\nTemplates cache directory: {templates_cache_dir}")
                print("Contents:")
                for item in os.listdir(templates_cache_dir):
                    item_path = os.path.join(templates_cache_dir, item)
                    if os.path.isdir(item_path):
                        print(f"- {item} (dir)")
                        # List contents 
                        files = os.listdir(item_path)
                        if files:
                            for file in files:
                                file_path = os.path.join(item_path, file)
                                print(f"  - {file} ({os.path.getsize(file_path)} bytes)")
                        else:
                            print("  (empty directory)")
        
        # Check structures dir
        structures_dir = os.path.join(echelon_dir, "structures")
        if os.path.exists(structures_dir):
            print(f"\nStructures directory: {structures_dir}")
            
            # List structure files
            print("Structure files:")
            for item in os.listdir(structures_dir):
                if item.endswith(".json"):
                    print(f"- {item}")
    else:
        print(f"Echelon directory does not exist: {echelon_dir}")
    
    # Initialize TemplateManager to check paths
    print_section("Template Manager Paths")
    template_manager = TemplateManager()
    for key, path in template_manager.paths.items():
        print(f"{key}: {path}")
    
    # Check template paths match cache locations
    print_section("Path Consistency Check")
    print(f"Cache path from preferences: {cache_location}")
    templates_cache_dir = template_manager.paths.get("templates_cache_dir", "unknown")
    print(f"Cache path from template manager: {templates_cache_dir}")
    
    path_match = cache_location == templates_cache_dir
    print(f"Paths match: {path_match}")
    
    if not path_match:
        print("\nWARNING: Cache paths do not match between preferences and template manager!")
        print("This could cause files to be cached in one location but searched for in another.")
    
    print_section("Summary")
    print(f"Cache enabled: {cache_enabled}")
    print(f"Cache location from preferences: {cache_location}")
    print(f"Cache location from template manager: {templates_cache_dir}")
    print(f"Paths match: {path_match}")

if __name__ == "__main__":
    main() 
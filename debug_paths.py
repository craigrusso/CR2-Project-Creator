#!/usr/bin/env python3

import os
import sys

def check_paths():
    """Check all possible paths for the icon files"""
    print("=== PATH DEBUG INFO ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {os.path.abspath(__file__)}")
    print(f"Python executable: {sys.executable}")
    
    # Check if app directory exists
    app_dir = os.path.join(os.getcwd(), "app")
    print(f"App directory exists: {os.path.exists(app_dir)}")
    
    # Try to find project root by traversing up
    current_dir = os.getcwd()
    project_root = current_dir
    for _ in range(10):  # Limit directory traversal
        if os.path.exists(os.path.join(project_root, "app")) and os.path.isdir(os.path.join(project_root, "app")):
            print(f"Found project root at: {project_root}")
            break
        parent = os.path.dirname(project_root)
        if parent == project_root:  # Reached filesystem root
            break
        project_root = parent
    
    # List of possible icon paths to check
    icon_paths = [
        os.path.join(os.getcwd(), "app", "assets", "icons", "templates", "template_structure_icon.svg"),
        os.path.join(project_root, "app", "assets", "icons", "templates", "template_structure_icon.svg"),
        os.path.join(os.getcwd(), "assets", "icons", "templates", "template_structure_icon.svg"),
        os.path.join(project_root, "assets", "icons", "templates", "template_structure_icon.svg"),
    ]
    
    # Check each path
    print("\nChecking possible icon paths:")
    for i, path in enumerate(icon_paths):
        print(f"{i+1}. {path} - Exists: {os.path.exists(path)}")
    
    # Check specific directories
    print("\nChecking directory contents:")
    dirs_to_check = [
        os.path.join(os.getcwd(), "app", "assets", "icons", "templates"),
        os.path.join(project_root, "app", "assets", "icons", "templates"),
        os.path.join(os.getcwd(), "app", "assets", "icons"),
        os.path.join(project_root, "app", "assets", "icons"),
    ]
    
    for directory in dirs_to_check:
        if os.path.exists(directory) and os.path.isdir(directory):
            print(f"\nContents of {directory}:")
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                print(f"  - {file} ({os.path.getsize(file_path)} bytes)")
        else:
            print(f"\nDirectory not found: {directory}")
    
    # Try to import app.constants and use get_resource_path
    print("\nTrying to use get_resource_path:")
    try:
        sys.path.insert(0, os.getcwd())
        from app.constants import get_resource_path
        
        icon_path = get_resource_path(os.path.join("app", "assets", "icons", "templates", "template_structure_icon.svg"))
        print(f"Path from get_resource_path: {icon_path}")
        print(f"Path exists: {os.path.exists(icon_path)}")
    except ImportError as e:
        print(f"ImportError: {e}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("=== END PATH DEBUG INFO ===")

if __name__ == "__main__":
    check_paths() 
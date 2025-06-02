#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import pickle
import platform
import datetime
import subprocess
import sys

# Using PyQt for the UI framework
from PyQt6.QtWidgets import QMessageBox
from app.ui.color_scheme_pyqt import colors
UI_FRAMEWORK = 'pyqt'

from app.constants import RECENT_PROJECTS_MAX, RECENT_TEMPLATES_MAX
from app.core import config_manager

# Import defaults from app_config
from app.config.app_config import DEFAULT_GET_PUBLIC_DOWNLOADS_URL

def load_json_file(file_path, default=None):
    """Load data from a JSON file, returning default if file doesn't exist or has errors"""
    if default is None:
        default = {}
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
    
    return default

def save_json_file(file_path, data):
    """Save data to a JSON file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        # print(f"DEBUG: Saved {os.path.basename(file_path)} to {file_path}")
        return True
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to save JSON file {file_path}")
        import traceback
        traceback.print_exc()
        return False

def load_pickle_file(file_path, default_value=None):
    """Load a pickle file with error handling"""
    if not file_path or not os.path.exists(file_path):
        return default_value
    
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading pickle file {file_path}: {e}")
        # If there's an error, return the default value and create a fresh file
        try:
            # Rename the problematic file for backup
            if os.path.exists(file_path):
                backup_path = f"{file_path}.bak"
                os.rename(file_path, backup_path)
                print(f"Renamed problematic file to {backup_path}")
            
            # Create a new file with the default value
            with open(file_path, 'wb') as f:
                pickle.dump(default_value, f)
            
            print(f"Created new file with default value")
        except Exception as backup_error:
            print(f"Error creating backup: {backup_error}")
        
        return default_value

def save_pickle_file(file_path, data):
    """Save data to a pickle file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
        return True
    except Exception as e:
        print(f"Error saving pickle file {file_path}: {e}")
        return False

def load_config():
    """Load the application configuration from a JSON file."""
    # Use config_manager to get the correct path
    settings_dir = config_manager.get_settings_path()
    config_path = os.path.join(settings_dir, "config.json")
    default_config = {
        # --- Update the default URL here --- 
        # --- API Endpoint Configuration ---
        "api_urls": {
            # !!! IMPORTANT: Default set to TEST endpoint for development. !!!
            # !!! MUST be changed to /prod/versions for PRODUCTION builds. !!!
            "get_public_downloads": "https://zryss80ntj.execute-api.us-west-1.amazonaws.com/test/versions" # TEST Endpoint
        },
        # --------------------------------------
        "last_output_dir": "",
        "last_structure": "Standard",
        "theme": "dark", # default theme
        "last_directory": "",
        "template_file_path": "",
        "structure_template": "Default",
        "show_advanced_options": False
    }
    return load_json_file(config_path, default_config)

def save_config(config):
    """Save application configuration to the settings directory."""
    settings_dir = config_manager.get_settings_path()
    config_file = os.path.join(settings_dir, "config.json")
    return save_json_file(config_file, config)

def load_recent_projects():
    """Load list of recent projects from the settings directory."""
    settings_dir = config_manager.get_settings_path()
    recent_projects_file = os.path.join(settings_dir, "recent_projects.json")
    return load_json_file(recent_projects_file, [])

def save_recent_projects(projects):
    """Save list of recent projects to the settings directory."""
    settings_dir = config_manager.get_settings_path()
    recent_projects_file = os.path.join(settings_dir, "recent_projects.json")
    return save_json_file(recent_projects_file, projects)

def load_recent_templates():
    """Load list of recent templates from the settings directory."""
    settings_dir = config_manager.get_settings_path()
    recent_templates_file = os.path.join(settings_dir, "recent_templates.json")
    return load_json_file(recent_templates_file, [])

def save_recent_templates(templates):
    """Save list of recent templates to the settings directory."""
    settings_dir = config_manager.get_settings_path()
    recent_templates_file = os.path.join(settings_dir, "recent_templates.json")
    return save_json_file(recent_templates_file, templates)

def add_to_recent_projects(project_path):
    """Add a project to the recent projects list"""
    recent_projects = load_recent_projects()
    
    # Create project entry
    project_entry = {
        'path': project_path,
        'name': os.path.basename(project_path),
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    # Remove if already exists
    recent_projects = [p for p in recent_projects if p['path'] != project_path]
    
    # Add to beginning
    recent_projects.insert(0, project_entry)
    
    # Limit to max items
    recent_projects = recent_projects[:RECENT_PROJECTS_MAX]
    
    # Save
    return save_recent_projects(recent_projects)

def open_folder(path):
    """Open a folder in the system file explorer"""
    try:
        # Handle paths with spaces or special characters
        if platform.system() == "Windows":
            os.startfile(os.path.normpath(path))
        elif platform.system() == "Darwin":
            # Use security-scoped bookmarks on macOS if available
            try:
                from app.utils.security_bookmarks import BookmarkAccessContext
                # Use a context manager to access the bookmark
                with BookmarkAccessContext(path):
                    # Use subprocess instead of os.system to avoid shell escaping issues
                    subprocess.run(['open', path], check=True)
            except ImportError:
                # Fall back to regular folder access
                # print("WARNING: Could not import security_bookmarks module. Falling back to standard access.")
                subprocess.run(['open', path], check=True)
            except Exception as e:
                # print(f"WARNING: Failed to use bookmark for {path}: {e}")
                # Try regular access as fallback
                subprocess.run(['open', path], check=True)
        else:
            # Use subprocess for Linux as well
            subprocess.run(['xdg-open', path], check=True)
        return True
    except Exception as e:
        print(f"Failed to open folder: {str(e)}")
        return False

def open_in_explorer(path):
    """Open folder in file explorer and select the folder"""
    try:
        path = os.path.normpath(path)
        if platform.system() == "Windows":
            subprocess.run(['explorer', '/select,', path], check=True)
        elif platform.system() == "Darwin":
            # Use security-scoped bookmarks on macOS if available
            try:
                from app.utils.security_bookmarks import BookmarkAccessContext
                # Use a context manager to access the bookmark
                with BookmarkAccessContext(path):
                    subprocess.run(['open', '-R', path], check=True)
            except ImportError:
                # Fall back to regular folder access
                # print("WARNING: Could not import security_bookmarks module. Falling back to standard access.")
                subprocess.run(['open', '-R', path], check=True)
            except Exception as e:
                # print(f"WARNING: Failed to use bookmark for {path}: {e}")
                # Try regular access as fallback
                subprocess.run(['open', '-R', path], check=True)
        else:
            # Fallback to regular open on Linux
            open_folder(path)
        return True
    except Exception as e:
        print(f"Failed to open in explorer: {str(e)}")
        return False

def create_readme_file(project_path, project_name, project_type, directories=None):
    """Create a README.txt file in the project folder"""
    if directories is None:
        directories = []
        
    readme_path = os.path.join(project_path, "README.txt")
    try:
        with open(readme_path, "w") as f:
            f.write(f"Project: {project_name}\n")
            f.write(f"Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Type: {project_type}\n\n")
            f.write("Created with CR2 Creative Pro Tools\n")
            f.write("----------------------------------\n\n")
            f.write("Project Structure Overview:\n")
            
            # List directories
            for root, dirs, files in os.walk(project_path):
                level = root.replace(project_path, '').count(os.sep)
                indent = ' ' * 4 * level
                subpath = os.path.basename(root)
                if root != project_path:
                    f.write(f"{indent}{subpath}/\n")
                    
                # List files (excluding README.txt itself)
                for file in files:
                    if file != "README.txt":
                        indent_file = ' ' * 4 * (level + 1)
                        f.write(f"{indent_file}{file}\n")
        
        return True
    except Exception as e:
        print(f"Error creating README file: {e}")
        return False

def parse_project_names(text):
    """
    Parse a list of project names from text, handling copy-pasted lists
    from emails with carriage returns
    """
    if not text:
        return []
    
    # Split by newlines and handle various formats
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    
    # Remove empty lines and strip whitespace
    project_names = [line.strip() for line in lines if line.strip()]
    
    return project_names

def truncate_path(path, max_length=40):
    """Truncate a path for display if it's too long"""
    if not path:
        return "No location selected"
        
    if len(path) <= max_length:
        return path
    
    # Split the path to get the directory and filename
    dirname, basename = os.path.split(path)
    
    # Keep the last part (filename or last directory) intact if possible
    if len(basename) < max_length - 5:  # Allow space for ".../"
        # Calculate remaining space for the first part
        first_part_len = max_length - len(basename) - 5  # 5 chars for ".../+"
        return dirname[:first_part_len] + ".../" + basename
    else:
        # No room for basename, just truncate middle
        return path[:max_length//2-2] + "..." + path[-max_length//2+1:]

def safe_path_join(*paths):
    """
    Join paths in a safe, cross-platform way.
    Normalizes the result to ensure consistent directory separators.
    """
    joined_path = os.path.join(*paths)
    return os.path.normpath(joined_path)

def normalize_path_for_storage(path):
    """
    Normalizes a path for storage in a platform-independent way.
    Converts Windows backslashes to forward slashes for consistency.
    
    Args:
        path (str): The path to normalize
        
    Returns:
        str: Normalized path with forward slashes
    """
    if not path:
        return ""
    
    # Normalize the path according to OS conventions
    norm_path = os.path.normpath(path)
    
    # Convert backslashes to forward slashes for storage
    # This ensures paths are stored consistently across platforms
    return norm_path.replace('\\', '/')

def ensure_directory_exists(directory):
    """
    Ensure a directory exists, creating it if necessary.
    Uses normalized paths for cross-platform compatibility.
    """
    directory = os.path.normpath(directory)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {directory}: {e}")
            return False
    return True

def resource_path(relative_path):
    """
    Get the absolute path to a resource file.
    This function is used to locate resources such as images or other files.
    """
    # This is a placeholder implementation. You might want to implement this
    # function based on your application's structure.
    # For example, you could use os.path.join(os.path.dirname(__file__), relative_path)
    # or a more robust resource management system.
    return relative_path

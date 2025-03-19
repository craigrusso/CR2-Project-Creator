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
from PyQt5.QtWidgets import QMessageBox
from app.ui.color_scheme_pyqt import colors
UI_FRAMEWORK = 'pyqt'

from app.constants import RECENT_PROJECTS_MAX

def get_config_paths():
    """Get paths for configuration files and directories"""
    # Default config directory
    default_config_dir = os.path.join(os.path.expanduser("~"), ".echelon")
    
    # Create the default config dir if it doesn't exist
    if not os.path.exists(default_config_dir):
        os.makedirs(default_config_dir)
    
    # First, check if we have a custom paths.json file
    paths_file = os.path.join(default_config_dir, "paths.json")
    custom_paths = {}
    
    if os.path.exists(paths_file):
        try:
            with open(paths_file, 'r') as f:
                custom_paths = json.load(f)
        except Exception as e:
            print(f"Error loading custom paths: {e}")
    
    # Use the config_dir from custom_paths if it exists, otherwise use default
    config_dir = custom_paths.get("config_dir", default_config_dir)
    
    # Define default paths
    default_paths = {
        "config_dir": config_dir,
        "config_file": os.path.join(config_dir, "config.json"),
        "recent_projects_file": os.path.join(config_dir, "recent_projects.json"),
        "recent_templates_file": os.path.join(config_dir, "recent_templates.json"),
        "templates_dir": os.path.join(config_dir, "templates"),
        "template_directories_dir": os.path.join(config_dir, "template_directories"),
        "custom_structures_dir": os.path.join(config_dir, "structures")
    }
    
    # Merge default paths with custom paths, prioritizing custom paths
    paths = {**default_paths, **custom_paths}
    
    # Ensure all directory paths exist
    for dir_key in ["config_dir", "templates_dir", "custom_structures_dir", "template_directories_dir"]:
        dir_path = paths[dir_key]
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
            except Exception as e:
                print(f"Error creating directory {dir_path}: {e}")
                # Fall back to default if custom directory can't be created
                if dir_key in custom_paths:
                    paths[dir_key] = default_paths[dir_key]
                    if not os.path.exists(default_paths[dir_key]):
                        os.makedirs(default_paths[dir_key])
    
    return paths

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
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving file {file_path}: {e}")
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
    """Load application configuration"""
    paths = get_config_paths()
    config_file = paths["config_file"]
    
    # Default configuration
    default_config = {
        "last_directory": "",
        "template_file_path": "",
        "structure_template": "Default",
        "show_advanced_options": False
    }
    
    # Load configuration using JSON instead of Pickle for better cross-platform compatibility
    config = load_json_file(config_file, default_config)
    
    return config

def save_config(config):
    """Save application configuration"""
    paths = get_config_paths()
    return save_json_file(paths["config_file"], config)

def load_recent_projects():
    """Load list of recent projects"""
    paths = get_config_paths()
    return load_json_file(paths["recent_projects_file"], [])

def save_recent_projects(projects):
    """Save list of recent projects"""
    paths = get_config_paths()
    return save_json_file(paths["recent_projects_file"], projects)

def load_recent_templates():
    """Load list of recent templates"""
    paths = get_config_paths()
    return load_json_file(paths["recent_templates_file"], [])

def save_recent_templates(templates):
    """Save list of recent templates"""
    paths = get_config_paths()
    return save_json_file(paths["recent_templates_file"], templates)

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
            # Use subprocess instead of os.system to avoid shell escaping issues
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

def create_sample_directory_template():
    """Create a sample directory template if none exists"""
    paths = get_config_paths()
    template_directories_dir = paths.get("template_directories_dir")
    
    # Check if any template directories exist
    if os.path.exists(template_directories_dir) and os.listdir(template_directories_dir):
        return  # Templates already exist
    
    # Sample template directory structure
    sample_dir = os.path.join(template_directories_dir, "Web_Project_Template")
    os.makedirs(sample_dir, exist_ok=True)
    
    # Create directory structure
    for folder in ["css", "js", "images", "fonts"]:
        os.makedirs(os.path.join(sample_dir, folder), exist_ok=True)
    
    # Create a sample index.html file
    index_html = os.path.join(sample_dir, "index.html")
    with open(index_html, 'w') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{PROJECT_NAME}}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <h1>{{PROJECT_NAME}}</h1>
    </header>
    <main>
        <p>Welcome to {{PROJECT_NAME}}!</p>
        <p>Created on {{DATE}}</p>
    </main>
    <footer>
        <p>&copy; {{YEAR}} - {{PROJECT_NAME}}</p>
    </footer>
    <script src="js/main.js"></script>
</body>
</html>""")
    
    # Create a sample CSS file
    css_dir = os.path.join(sample_dir, "css")
    with open(os.path.join(css_dir, "style.css"), 'w') as f:
        f.write("""/* 
 * {{PROJECT_NAME}} Styles
 * Created: {{DATE}}
 */

body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    color: #333;
}

header {
    background-color: #4682B4;
    color: white;
    text-align: center;
    padding: 1rem;
}

main {
    max-width: 800px;
    margin: 0 auto;
    padding: 1rem;
}

footer {
    text-align: center;
    padding: 1rem;
    background-color: #f4f4f4;
    margin-top: 2rem;
}
""")
    
    # Create a sample JS file
    js_dir = os.path.join(sample_dir, "js")
    with open(os.path.join(js_dir, "main.js"), 'w') as f:
        f.write("""/*
 * {{PROJECT_NAME}} - Main JavaScript
 * Created: {{DATE}}
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('{{PROJECT_NAME}} loaded successfully!');
    
    // Your code here
});
""")
    
    # Create a sample README with project name placeholder
    with open(os.path.join(sample_dir, "README.md"), 'w') as f:
        f.write("""# {{PROJECT_NAME}}

## Description
This is a sample web project template with basic structure.

## Structure
- css/: Stylesheets
- js/: JavaScript files
- images/: Image files
- fonts/: Font files

## Getting Started
1. Edit the index.html file
2. Modify the CSS in css/style.css
3. Add your JavaScript in js/main.js

## Created
{{DATE}}
""")
    
    # Create a template.json file to describe the template
    with open(os.path.join(sample_dir, "template.json"), 'w') as f:
        json.dump({
            "name": "Web Project Template",
            "category": "Web Development",
            "description": "A basic web project template with HTML, CSS, and JavaScript files",
            "created": datetime.datetime.now().isoformat(),
            "type": "directory"
        }, f, indent=2)

def create_sample_templates():
    """Create sample templates if none exist"""
    # Create regular file templates
    paths = get_config_paths()
    templates_dir = paths.get("templates_dir")
    
    # Check if any templates exist
    if not os.path.exists(templates_dir) or not os.listdir(templates_dir):
        # Create templates directory
        os.makedirs(templates_dir, exist_ok=True)
        
        # Create sample templates
        sample_templates = [
            {
                "name": "Basic Website",
                "category": "Web Development",
                "description": "A basic website template with HTML, CSS, and JavaScript",
                "type": "Web"
            },
            {
                "name": "Python Application",
                "category": "Desktop Applications",
                "description": "A Python application template with basic structure",
                "type": "Python"
            },
            {
                "name": "React App",
                "category": "Web Development",
                "description": "A React.js application template",
                "type": "Web"
            },
            {
                "name": "Mobile App",
                "category": "Mobile Apps",
                "description": "A mobile application template",
                "type": "Mobile"
            }
        ]
        
        # Save sample templates
        for i, template in enumerate(sample_templates):
            filename = f"sample_template_{i+1}.json"
            with open(os.path.join(templates_dir, filename), 'w') as f:
                json.dump(template, f, indent=2)
    
    # Create directory templates
    create_sample_directory_template()

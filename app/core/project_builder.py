#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Project Builder Module

This module handles creating projects from templates or structures.
"""

import os
import threading
import datetime
import shutil
import sys
import json
import platform
import re  # Add import for regex

# Using PyQt for the UI framework
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt5.QtCore import Qt, QTimer
UI_FRAMEWORK = 'pyqt'

# Define PyQt version of progress window
class BatchProgressWindowPyQt(QDialog):
    """PyQt version of the batch progress window"""
    
    def __init__(self, total_projects):
        super().__init__()
        self.total_projects = total_projects
        self.results = None
        
        # Set window properties
        self.setWindowTitle("Creating Projects")
        self.setFixedSize(400, 150)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Status label
        self.status_label = QLabel("Preparing...")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(total_projects)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Spacer
        layout.addSpacing(10)
        
        # Cancel button (disabled for now since we don't have cancellation logic)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        layout.addWidget(self.cancel_button, alignment=Qt.AlignRight)
    
    def update_status(self, text):
        """Update the status text"""
        self.status_label.setText(text)
    
    def update_progress(self, current):
        """Update the progress bar"""
        self.progress_bar.setValue(current)
    
    def set_results(self, results):
        """Store the results for potential display"""
        self.results = results
        # Change status to complete
        self.status_label.setText(f"Completed: {len(results)} projects processed")
        self.progress_bar.setValue(self.total_projects)

# Set the BatchProgressWindow class to use PyQt version
BatchProgressWindow = BatchProgressWindowPyQt

from app.utils.utils import add_to_recent_projects, create_readme_file

class ProjectBuilder:
    """
    Creates project directories and handles batch project creation
    """
    def __init__(self, template_manager):
        self.template_manager = template_manager
        self.project_queue = []
        self.is_building = False
    
    def _handle_dollar_placeholder(self, input_string, project_name):
        """
        Specialized handling for dollar sign placeholders (${PROJECT_NAME})
        
        Args:
            input_string: String that may contain the ${PROJECT_NAME} placeholder
            project_name: Project name to replace the placeholder with
            
        Returns:
            String with placeholder replaced
        """
        # Define all placeholder formats we need to handle
        placeholder_dollar = "${PROJECT_NAME}"
        
        # Debug logging
        print(f"🔍 DOLLAR HANDLING DEBUG: Processing string: '{input_string}'")
        print(f"🔍 DOLLAR HANDLING DEBUG: String length: {len(input_string)}")
        print(f"🔍 DOLLAR HANDLING DEBUG: String as bytes: {input_string.encode('utf-8')}")
        print(f"🔍 DOLLAR HANDLING DEBUG: Project name: '{project_name}'")
        
        # Initialize result with input string
        result = input_string
        
        # Case 1: Input contains the full placeholder "${PROJECT_NAME}"
        if placeholder_dollar in input_string:
            # Create a new string with the placeholder replaced
            # We need to be careful with this replacement to ensure no $ artifacts remain
            parts = input_string.split(placeholder_dollar)
            result = project_name.join(parts)
            print(f"🔍 DOLLAR HANDLING DEBUG: Full placeholder replacement: '{result}'")
        
        # Case 2: Input starts with $ but doesn't contain the full placeholder
        # This likely means the display is showing $ but internally it's not matching correctly
        elif input_string.startswith("$"):
            # Extract the part after $ 
            remaining = input_string[1:]
            
            # If it looks like it might be a malformed PROJECT_NAME placeholder
            if remaining.startswith("{PROJECT_NAME}") or remaining.startswith("PROJECT_NAME"):
                # In these cases, we want to just use the project name with any suffix
                name_index = remaining.find("PROJECT_NAME")
                if name_index >= 0:
                    suffix_index = name_index + len("PROJECT_NAME")
                    suffix = remaining[suffix_index:] if suffix_index < len(remaining) else ""
                    result = f"{project_name}{suffix}"
                    print(f"🔍 DOLLAR HANDLING DEBUG: Malformed placeholder handling: '{result}'")
                    
            # If it's another kind of file that just happens to start with $
            elif "." in remaining:
                # It has an extension - preserve the extension
                parts = remaining.split(".")
                ext = "." + ".".join(parts[1:])  # Handle multiple dots in filename
                result = f"{project_name}{ext}"
                print(f"🔍 DOLLAR HANDLING DEBUG: $ prefix with extension: '{result}'")
                
            # Any other $ prefix case
            else:
                # Just replace the $ with the project name
                result = f"{project_name}{remaining}"
                print(f"🔍 DOLLAR HANDLING DEBUG: Simple $ prefix handling: '{result}'")
                
        # Log the final result for debugging
        print(f"🔍 DOLLAR HANDLING DEBUG: Final result: '{result}'")
        return result
    
    def create_project(self, project_name, output_dir, template_file=None, project_type="Standard", 
                      use_version_control=True, create_backup=True, structure_name=None,
                      batch_mode=False, callback=None):
        """Create a single project with the specified settings"""
        if not project_name or not output_dir:
            return False, "Project name and output directory are required"
        
        # Debug information
        print(f"DEBUG: Creating project '{project_name}' in '{output_dir}'")
        print(f"DEBUG: template_file={template_file}, structure_name={structure_name}")
        
        # Base project path
        project_path = os.path.join(output_dir, project_name)
        version = 1
        
        # Check if project folder already exists
        while os.path.exists(project_path):
            project_path = os.path.join(output_dir, f"{project_name}_{version}")
            version += 1
        
        try:
            # Create base directory
            os.makedirs(project_path)
            
            # Make sure template_file is actually a valid path before processing it
            # Process template first (if provided and it's not our dummy gallery template)
            if template_file and template_file != "gallery_template":
                print(f"DEBUG: Processing template file: {template_file}")
                # Only process the template if it's a valid directory or file that exists
                # This prevents copying from the application root directory unintentionally
                if os.path.exists(template_file):
                    if os.path.isdir(template_file):
                        # Make sure we're not copying from the app's root directory
                        app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        print(f"DEBUG: App root directory: {app_root}")
                        print(f"DEBUG: Template directory: {os.path.abspath(template_file)}")
                        
                        if os.path.abspath(template_file) == app_root:
                            print(f"Warning: Attempting to copy from application root directory, skipping template copy")
                        else:
                            # Directory-based template
                            self._copy_template_directory(template_file, project_path, project_name)
                    elif os.path.isfile(template_file):
                        # File-based template
                        self._copy_template_file(template_file, project_path, project_name, project_type)
                    else:
                        print(f"Warning: Template file does not exist: {template_file}")
                else:
                    print(f"Warning: Template path does not exist: {template_file}")
            
            # Create directory structure - get structure from name if provided
            if structure_name:
                # Store the current structure name for use in file copying
                if hasattr(self.template_manager, 'current_structure_name'):
                    print(f"DEBUG: Setting current_structure_name to {structure_name}")
                    self.template_manager.current_structure_name = structure_name
                else:
                    print(f"DEBUG: Adding current_structure_name attribute with value {structure_name}")
                    setattr(self.template_manager, 'current_structure_name', structure_name)
                
                # Get the structure by name
                directories = self.template_manager.get_structure(structure_name)
                # Debug the structure data
                print(f"DEBUG: Retrieved structure data from template_manager.get_structure({structure_name})")
                print(f"DEBUG: Structure data type: {type(directories)}")
                print(f"DEBUG: Structure data content: {directories}")
                
                # Create the structure - pass the original project name
                self._create_folder_structure(project_path, directories, original_project_name=project_name)
            else:
                # Try to get the structure from the selected template
                print("DEBUG: No structure_name provided, checking if template has embedded structure")
                directories = None
                
                if hasattr(self.template_manager, 'selected_template') and self.template_manager.selected_template:
                    selected_template = self.template_manager.selected_template
                    print(f"DEBUG: Found selected_template: {selected_template}")
                    
                    if isinstance(selected_template, dict) and 'structure' in selected_template:
                        directories = selected_template['structure']
                        print(f"DEBUG: Found structure in selected_template: {directories}")
                    
                    # If no structure in template, try to load it using template name
                    if directories is None and isinstance(selected_template, dict) and 'name' in selected_template:
                        template_name = selected_template['name']
                        print(f"DEBUG: Attempting to load structure for template name: {template_name}")
                        
                        # Try with Template_ prefix
                        structure_name = f"Template_{template_name}"
                        directories = self.template_manager.get_structure(structure_name)
                        
                        if directories:
                            print(f"DEBUG: Successfully loaded structure using Template_ prefix: {directories}")
                        else:
                            # Try with the plain template name
                            directories = self.template_manager.get_structure(template_name)
                            if directories:
                                print(f"DEBUG: Successfully loaded structure using plain template name: {directories}")
                
                # Use an empty list for directories if none provided
                if not directories:
                    directories = []
                    print("DEBUG: Using empty directories list")
                
                # Create the structure
                if directories:
                    print(f"DEBUG: Creating folder structure with directories: {directories}")
                    self._create_folder_structure(project_path, directories, original_project_name=project_name)
            
            # Add to recent projects
            add_to_recent_projects(project_path)
            
            # Return success
            return True, project_path
            
        except Exception as e:
            import traceback
            print(f"Error creating project: {e}")
            traceback.print_exc()
            return False, f"Error: {e}"
    
    def _create_folder_structure(self, project_path, directories, original_project_name=None):
        """Create folder structure with improved handling of nested directories and files"""
        # Use the original project name if provided, otherwise get from the path
        # This ensures we use the correct project name in nested folders
        if original_project_name is None:
            project_name = os.path.basename(project_path)
        else:
            project_name = original_project_name
            
        print(f"Creating folder structure at {project_path} with project name: {project_name}")
        print(f"DEBUG: Structure format type: {type(directories)}")
        print(f"DEBUG: Structure content: {directories}")
            
        # Cache project name placeholder formats for faster replacement
        project_name_placeholder_double = "{{PROJECT_NAME}}"
        project_name_placeholder_single = "{PROJECT_NAME}"
        project_name_placeholder_dollar = "${PROJECT_NAME}"
        
        # Check if directories is a list or dictionary
        if isinstance(directories, list):
            print(f"DEBUG: Processing list structure with {len(directories)} items")
            
            # Process each item in the list
            for item in directories:
                print(f"DEBUG: Processing item type: {type(item)}, content: {item}")
                original_item = item  # Store for logging
                
                # Handle string item - could be a file or folder name
                if isinstance(item, str):
                    print(f"DEBUG: Processing file: {item}")
                    
                    # Process item name - check for placeholders that need replacement
                    if project_name_placeholder_dollar in item:
                        # Split the string on the placeholder and join with the project name
                        parts = item.split(project_name_placeholder_dollar)
                        item = project_name.join(parts)
                        print(f"DEBUG: Dollar placeholder replaced: '{original_item}' -> '{item}'")
                    elif project_name_placeholder_double in item:
                        parts = item.split(project_name_placeholder_double)
                        item = project_name.join(parts)
                        print(f"DEBUG: Double placeholder replaced: '{original_item}' -> '{item}'")
                    elif project_name_placeholder_single in item:
                        parts = item.split(project_name_placeholder_single)
                        item = project_name.join(parts)
                        print(f"DEBUG: Single placeholder replaced: '{original_item}' -> '{item}'")
                    elif item.startswith("$"):
                        # For items that just start with $ but don't have the full placeholder format
                        item = self._handle_dollar_placeholder(item, project_name)
                        print(f"DEBUG: $ sign at start handled: '{original_item}' -> '{item}'")
                    
                    # Create the file (or folder, depending on whether it has an extension)
                    file_path = os.path.join(project_path, item)
                    if '.' in os.path.basename(item):
                        # It's a file - create an empty file
                        with open(file_path, 'w') as f:
                            pass
                    else:
                        # No extension - treat as directory
                        os.makedirs(file_path, exist_ok=True)
                        
                # Handle normalized structure format
                elif isinstance(item, dict) and 'name' in item and 'type' in item:
                    print(f"DEBUG: Processing normalized item: {item}")
                    name = item['name']
                    original_name = name  # Store for logging
                    item_type = item['type']
                    
                    # Replace placeholders in name
                    if isinstance(name, str):
                        if project_name_placeholder_dollar in name:
                            # Split the string on the placeholder and join with the project name
                            parts = name.split(project_name_placeholder_dollar)
                            name = project_name.join(parts)
                            print(f"DEBUG: Dollar placeholder replaced in item: '{original_name}' -> '{name}'")
                        elif project_name_placeholder_double in name:
                            parts = name.split(project_name_placeholder_double)
                            name = project_name.join(parts)
                            print(f"DEBUG: Double placeholder replaced in item: '{original_name}' -> '{name}'")
                        elif project_name_placeholder_single in name:
                            parts = name.split(project_name_placeholder_single)
                            name = project_name.join(parts)
                            print(f"DEBUG: Single placeholder replaced in item: '{original_name}' -> '{name}'")
                        elif name.startswith("$"):
                            # For items that just start with $ but don't have the full placeholder format
                            name = self._handle_dollar_placeholder(name, project_name)
                            print(f"DEBUG: $ sign at start handled in item: '{original_name}' -> '{name}'")
                    
                    # Check if this is a folder or file
                    is_folder = (item_type == "folder" or item_type == "directory")
                    
                    # Create file or folder
                    if is_folder:
                        folder_path = os.path.join(project_path, name)
                        os.makedirs(folder_path, exist_ok=True)
                        
                        # Process children recursively if they exist
                        if 'children' in item and item['children']:
                            # Pass the original project name to keep consistent naming
                            self._create_folder_structure(folder_path, item['children'], original_project_name)
                    else:
                        # Create empty file
                        file_path = os.path.join(project_path, name)
                        with open(file_path, 'w') as f:
                            pass
                            
                elif isinstance(item, dict) and len(item) == 1:
                    # Handle simplified folder format {folder_name: [children]}
                    for folder_name, children in item.items():
                        original_folder = folder_name  # Store for logging
                        
                        # Handle placeholder replacement in folder name
                        if isinstance(folder_name, str):
                            if project_name_placeholder_dollar in folder_name:
                                # Split the string on the placeholder and join with the project name
                                parts = folder_name.split(project_name_placeholder_dollar)
                                folder_name = project_name.join(parts)
                                print(f"DEBUG: Dollar placeholder replaced in folder: '{original_folder}' -> '{folder_name}'")
                            elif project_name_placeholder_double in folder_name:
                                parts = folder_name.split(project_name_placeholder_double)
                                folder_name = project_name.join(parts)
                                print(f"DEBUG: Double placeholder replaced in folder: '{original_folder}' -> '{folder_name}'")
                            elif project_name_placeholder_single in folder_name:
                                parts = folder_name.split(project_name_placeholder_single)
                                folder_name = project_name.join(parts)
                                print(f"DEBUG: Single placeholder replaced in folder: '{original_folder}' -> '{folder_name}'")
                            elif folder_name.startswith("$"):
                                # For folders that just start with $ but don't have the full placeholder format
                                folder_name = self._handle_dollar_placeholder(folder_name, project_name)
                                print(f"DEBUG: $ sign at start handled in folder: '{original_folder}' -> '{folder_name}'")
                        
                        # Create the parent folder
                        folder_path = os.path.join(project_path, folder_name)
                        os.makedirs(folder_path, exist_ok=True)
                        
                        # Process children recursively
                        if children:
                            # Pass the original project name to keep consistent naming
                            self._create_folder_structure(folder_path, children, original_project_name)
        else:
            print(f"WARNING: Unhandled structure format: {type(directories)}")
    
    def _process_template(self, template_file, project_path, project_name, project_type):
        """Process template files with improved handling for different template types"""
        # Determine if this is a single file or a template directory
        if os.path.isdir(template_file):
            self._copy_template_directory(template_file, project_path, project_name)
        else:
            self._copy_template_file(template_file, project_path, project_name, project_type)
    
    def _copy_template_directory(self, template_dir, project_path, project_name):
        """Copy a directory template, renaming files that match specific patterns"""
        print(f"Copying template directory: {template_dir} to {project_path}")
        
        # Safety check: make sure we're not copying from system directories
        template_abs_path = os.path.abspath(template_dir)
        app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Define system directories based on platform
        system_dirs = [app_root]
        if platform.system() == "Windows":
            # Add Windows system directories
            system_roots = [os.path.splitdrive(sys.executable)[0] + '\\']
            system_dirs.extend([
                os.path.join(root, folder) 
                for root in system_roots
                for folder in ['Windows', 'Program Files', 'Program Files (x86)']
            ])
        else:
            # Unix-like system directories (Linux and macOS)
            system_dirs.extend(["/", "/usr", "/etc", "/var", "/bin", "/sbin", "/lib"])
            
            # Add macOS specific system directories
            if platform.system() == "Darwin":
                system_dirs.extend(["/System", "/Library", "/Applications"])
        
        if any(template_abs_path == os.path.abspath(d) or 
               template_abs_path.startswith(os.path.abspath(d) + os.sep) 
               for d in system_dirs):
            print(f"WARNING: Refusing to copy from system directory or app root: {template_abs_path}")
            print(f"This is likely unintentional and could copy unwanted files.")
            return
        
        # Skip if the directory doesn't exist
        if not os.path.exists(template_dir) or not os.path.isdir(template_dir):
            print(f"WARNING: Template directory does not exist: {template_dir}")
            return
        
        # Define placeholder formats we need to replace
        double_brace_placeholder = "{{PROJECT_NAME}}"
        single_brace_placeholder = "{PROJECT_NAME}"
        dollar_placeholder = "${PROJECT_NAME}"
        
        for root, dirs, files in os.walk(template_dir):
            # Skip template.json file
            if "template.json" in files:
                files.remove("template.json")
                
            # Get relative path from template dir
            rel_path = os.path.relpath(root, template_dir)
            if rel_path == '.':  # Root directory
                target_dir = project_path
            else:
                # Replace PROJECT_NAME in directory names if needed
                rel_path_parts = []
                for part in rel_path.split(os.sep):
                    if double_brace_placeholder in part:
                        new_part = part.replace(double_brace_placeholder, project_name)
                        print(f"Renamed directory: {part} -> {new_part}")
                        part = new_part
                    elif single_brace_placeholder in part:
                        new_part = part.replace(single_brace_placeholder, project_name)
                        print(f"Renamed directory: {part} -> {new_part}")
                        part = new_part
                    elif dollar_placeholder in part:
                        new_part = part.replace(dollar_placeholder, project_name)
                        print(f"Renamed directory: {part} -> {new_part}")
                        part = new_part
                    rel_path_parts.append(part)
                rel_path = os.path.join(*rel_path_parts)
                target_dir = os.path.join(project_path, rel_path)
            
            # Create target directory
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy files, renaming any with placeholder in them
            for file in files:
                source_file = os.path.join(root, file)
                
                # Handle file renaming if needed
                target_file_name = file
                if double_brace_placeholder in file:
                    target_file_name = file.replace(double_brace_placeholder, project_name)
                    print(f"Renamed file: {file} -> {target_file_name}")
                elif single_brace_placeholder in file:
                    target_file_name = file.replace(single_brace_placeholder, project_name)
                    print(f"Renamed file: {file} -> {target_file_name}")
                elif dollar_placeholder in file:
                    target_file_name = file.replace(dollar_placeholder, project_name)
                    print(f"Renamed file: {file} -> {target_file_name}")
                
                # Remove the emoji indicator if present
                if '🔄' in target_file_name:
                    target_file_name = target_file_name.replace('🔄', '').strip()
                    print(f"Removed emoji from file name: {target_file_name}")
                
                target_file = os.path.join(target_dir, target_file_name)
                
                # Copy the file
                shutil.copy2(source_file, target_file)
                
                # If it's a text file that might need content replacement
                if self._is_text_file(source_file):
                    self._replace_template_placeholders(target_file, project_name)
    
    def _is_text_file(self, file_path):
        """Check if a file is likely a text file that can have placeholders replaced"""
        # Basic check based on extension
        text_extensions = [
            '.txt', '.md', '.json', '.xml', '.html', '.css', '.js', '.jsx', '.ts', '.tsx',
            '.py', '.c', '.cpp', '.h', '.hpp', '.java', '.config', '.yaml', '.yml', '.toml',
            '.sh', '.bash', '.bat', '.ps1', '.sql', '.php', '.rb', '.swift', '.dart',
            '.gitignore', '.env', '.ini', '.cfg', '.conf', '.properties'
        ]
        _, ext = os.path.splitext(file_path.lower())
        
        # Try to detect text files without extensions
        if not ext and os.path.exists(file_path):
            try:
                # Try to open and read a few bytes
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    sample = f.read(1024)
                    # If we can read it as text, it's likely a text file
                    return '\0' not in sample  # Binary files often contain null bytes
            except:
                # If we can't read it as text, assume it's not a text file
                return False
                
        return ext in text_extensions
    
    def _replace_template_placeholders(self, file_path, project_name):
        """Replace template placeholders in file content with improved formatting support"""
        try:
            # Check if file exists and is a file (not a directory)
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                print(f"WARNING: Can't replace placeholders - file doesn't exist: {file_path}")
                return False
            
            # Only process files we recognize as text files
            if not self._is_text_file(file_path):
                print(f"DEBUG: Skipping binary file for placeholder replacement: {file_path}")
                return False
            
            # Read the file content
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                print(f"WARNING: Error reading file for placeholder replacement: {e}")
                return False
            
            # Define all possible placeholder formats
            double_brace_placeholder = "{{PROJECT_NAME}}"  # Double braces
            single_brace_placeholder = "{PROJECT_NAME}"    # Single braces
            dollar_placeholder = "${PROJECT_NAME}"         # Dollar sign with braces
            
            # Track if any replacements were made
            replacements_made = False
            
            # Replace placeholders in the content
            if double_brace_placeholder in content:
                content = content.replace(double_brace_placeholder, project_name)
                print(f"Replaced double brace placeholder in {os.path.basename(file_path)}")
                replacements_made = True
                
            if single_brace_placeholder in content:
                content = content.replace(single_brace_placeholder, project_name)
                print(f"Replaced single brace placeholder in {os.path.basename(file_path)}")
                replacements_made = True

            if dollar_placeholder in content:
                content = content.replace(dollar_placeholder, project_name)
                print(f"Replaced dollar placeholder in {os.path.basename(file_path)}")
                replacements_made = True
            
            # Write the modified content back to the file if any changes were made
            if replacements_made:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Updated template placeholders in {os.path.basename(file_path)}")
                    return True
                except Exception as e:
                    print(f"WARNING: Error writing file after placeholder replacement: {e}")
                    return False
            
            # No changes were made to the content
            print(f"No placeholders found in {os.path.basename(file_path)}")
            return False
            
        except Exception as e:
            print(f"ERROR replacing template placeholders: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _copy_template_file(self, template_file, project_path, project_name, project_type):
        """Copy the template file to the appropriate location in the project"""
        filename = os.path.basename(template_file)
        _, ext = os.path.splitext(filename)
        
        # Check if filename contains placeholders (both formats)
        if "{{PROJECT_NAME}}" in filename:
            print(f"Template filename contains placeholder: {filename}")
            # Replace placeholder but keep the extension
            filename = filename.replace("{{PROJECT_NAME}}", project_name)
            print(f"Renamed template file to: {filename}")
        elif "{PROJECT_NAME}" in filename:
            print(f"Template filename contains placeholder: {filename}")
            # Replace placeholder but keep the extension
            filename = filename.replace("{PROJECT_NAME}", project_name)
            print(f"Renamed template file to: {filename}")
        
        # Remove emoji indicator if present
        if '🔄' in filename:
            filename = filename.replace('🔄', '').strip()
            print(f"Removed emoji from file name: {filename}")
        
        # Determine destination subfolder based on file type
        if ext.lower() in ['.prproj']:
            dest_folder = os.path.join(project_path, "01_PREMIER_PROJECT")
        elif ext.lower() in ['.aep', '.aepx']:
            if project_type == "Motion Graphics":
                dest_folder = os.path.join(project_path, "01_AE_PROJECTS")
            else:
                dest_folder = os.path.join(project_path, "02_AE_PROJECTS")
        elif ext.lower() in ['.psd']:
            dest_folder = os.path.join(project_path, "01_PHOTOSHOP_PROJECTS")
        elif ext.lower() in ['.ai']:
            dest_folder = os.path.join(project_path, "02_ILLUSTRATOR_PROJECTS")
        else:
            dest_folder = project_path
        
        # Make sure destination folder exists
        os.makedirs(dest_folder, exist_ok=True)
        
        # Copy the template file
        dest_path = os.path.join(dest_folder, filename)
        shutil.copy2(template_file, dest_path)
        
        # If it's a text file, replace placeholders in content
        if self._is_text_file(template_file):
            self._replace_template_placeholders(dest_path, project_name)
    
    def batch_create_projects(self, project_names, output_dir, template_file=None, 
                             project_type="Standard", structure_name=None,
                             use_version_control=True, create_backup=True,
                             callback=None):
        """
        Set up a batch creation of multiple projects
        
        Args:
            project_names: List of project names to create
            output_dir: Directory to create projects in
            template_file: Optional template file to use
            project_type: Type of project
            structure_name: Custom structure to use (optional)
            use_version_control: Whether to use version control
            create_backup: Whether to create backups
            callback: Function to call when batch process completes
        """
        if not project_names or not output_dir:
            return False
        
        # Create queue of projects to create
        self.project_queue = [(name.strip(), output_dir, template_file, project_type, 
                             use_version_control, create_backup, structure_name) 
                             for name in project_names if name.strip()]
        
        # Start batch processing thread
        self.is_building = True
        
        # Use threading to prevent UI freeze
        thread = threading.Thread(target=self._process_batch_queue, args=(callback,))
        thread.daemon = True  # Make thread daemon so it doesn't block application exit
        thread.start()
        
        return True
    
    def _process_batch_queue(self, callback=None):
        """Process the batch queue of projects to create"""
        results = []
        
        # Progress indicator for CLI usage
        print(f"Starting batch processing of {len(self.project_queue)} projects...")
        
        # Process all projects in the queue
        for i, (name, output_dir, template_file, project_type, 
               use_version_control, create_backup, structure_name) in enumerate(self.project_queue):
            
            # Log progress
            print(f"Creating project {i+1}/{len(self.project_queue)}: {name}")
            
            # Add debug info about the template being used
            if template_file == "gallery_template":
                print(f"Using gallery template with structure: {structure_name}")
                print(f"Project name: {name}, Output dir: {output_dir}")
            else:
                print(f"Using template file: {template_file}")
                if not os.path.exists(template_file):
                    print(f"Warning: Template file does not exist: {template_file}")
            
            # Create project
            success, result = self.create_project(
                name, output_dir, template_file, project_type,
                use_version_control, create_backup, structure_name,
                batch_mode=True
            )
            
            results.append((name, success, result))
        
        # Completed
        self.is_building = False
        self.project_queue = []
        
        print("Batch processing completed.")
        
        # Call callback with results - this will happen in the main thread
        if callback:
            callback(results)

        # Return results for potential direct use
        return results

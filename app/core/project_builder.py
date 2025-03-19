#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import threading
import datetime
import shutil
import sys
import json
import platform

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
                # Create the structure - pass the original project name
                self._create_folder_structure(project_path, directories, original_project_name=project_name)
            else:
                # Use an empty list for directories if none provided
                directories = []
            
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
            
        # Cache project name placeholder formats for faster replacement
        project_name_placeholder_double = "{{PROJECT_NAME}}"
        project_name_placeholder_single = "{PROJECT_NAME}"
        
        # Handle different types of directories input
        if isinstance(directories, list):
            for item in directories:
                # Handle nested dict - this covers both folders with children and empty folders
                if isinstance(item, dict):
                    for folder_name, sub_items in item.items():
                        # Replace placeholders in folder_name if needed
                        if isinstance(folder_name, str):
                            if project_name_placeholder_double in folder_name:
                                new_folder_name = folder_name.replace(project_name_placeholder_double, project_name)
                                print(f"Renamed folder in structure: {folder_name} -> {new_folder_name}")
                                folder_name = new_folder_name
                            elif project_name_placeholder_single in folder_name:
                                new_folder_name = folder_name.replace(project_name_placeholder_single, project_name)
                                print(f"Renamed folder in structure: {folder_name} -> {new_folder_name}")
                                folder_name = new_folder_name
                        
                        # Create the parent folder
                        folder_path = os.path.join(project_path, folder_name)
                        os.makedirs(folder_path, exist_ok=True)
                        
                        # Process subfolders recursively - pass the original project name
                        # Only process if there are subitems
                        if sub_items:
                            self._create_folder_structure(folder_path, sub_items, original_project_name=project_name)
                # Handle string items (files or legacy format with trailing slash)
                elif isinstance(item, str):
                    name = item
                    original_name = item  # Keep the original name for cache lookup
                    
                    # FIXED: Better detection of folder vs file
                    # Check if this is a folder (using various signals)
                    is_folder = False
                    
                    # Check if this item has a project name placeholder - these are always files when they have extensions
                    has_project_name_placeholder = (project_name_placeholder_double in name) or (project_name_placeholder_single in name)
                    has_file_emoji = '🔄' in name
                    
                    # Legacy format - folder ending with slash
                    if name.endswith('/'):
                        is_folder = True
                        name = name[:-1]  # Remove the trailing slash
                    
                    # Check for revision folders (REV01, REV02, etc.)
                    elif name.upper().startswith('REV') and len(name) >= 4 and name[3:].isdigit():
                        is_folder = True
                        print(f"Detected '{name}' as a revision folder")
                    
                    # Check for folder naming conventions 
                    # e.g., folders typically don't have extensions, or have specific numeric prefixes
                    elif ('.' not in name or name.startswith('_')) and not has_project_name_placeholder:
                        # Folders often have numeric prefixes like "1_Footage" or other folder-like naming
                        if (name.startswith(tuple("0123456789")) and '_' in name) or \
                           any(folder_keyword in name.lower() for folder_keyword in ['folder', 'dir', 'footage', 'audio', 'video', 'gfx', 'exports']):
                            is_folder = True
                            print(f"Detected '{name}' as a folder based on naming convention")
                    
                    # Handle placeholder replacement in the name - do this efficiently
                    # First check double braces format
                    if project_name_placeholder_double in name:
                        # Replace the placeholder with the project name
                        name = name.replace(project_name_placeholder_double, project_name)
                        print(f"Renamed item in structure: {item} -> {name}")
                        is_folder = False  # If it has a project name placeholder, it's a file
                    # Then check single braces format
                    elif project_name_placeholder_single in name:
                        # Replace the placeholder with the project name
                        name = name.replace(project_name_placeholder_single, project_name)
                        print(f"Renamed item in structure: {item} -> {name}")
                        is_folder = False  # If it has a project name placeholder, it's a file
                    
                    # Special case - if it has the file emoji, it's definitely a file
                    if has_file_emoji:
                        is_folder = False
                        # Remove the emoji from the name
                        name = name.replace('🔄', '').strip()
                        print(f"Removed emoji indicator from file name: {name}")
                    
                    if is_folder:
                        # It's a folder - create directory
                        folder_path = os.path.join(project_path, name)
                        print(f"Creating folder: {folder_path}")
                        os.makedirs(folder_path, exist_ok=True)
                    else:
                        # It's a file, create placeholder or empty file
                        if '/' in name:
                            # Handle file in subfolder
                            file_dir, filename = os.path.split(name)
                            file_dir_path = os.path.join(project_path, file_dir)
                            os.makedirs(file_dir_path, exist_ok=True)
                            file_path = os.path.join(file_dir_path, filename)
                        else:
                            file_path = os.path.join(project_path, name)
                        
                        # Check if this is a file that should be copied from the cache
                        source_file = None
                        
                        # For files with project name placeholders and emoji, try to find them in the cache
                        if has_project_name_placeholder or has_file_emoji:
                            # Get the original file name (without emoji) for cache lookup
                            lookup_name = original_name.replace('🔄', '').strip()
                            
                            # Extract just the filename part if it has a path
                            if '/' in lookup_name:
                                _, lookup_filename = os.path.split(lookup_name)
                            else:
                                lookup_filename = lookup_name
                                
                            # 1. First try finding the file in the structure cache directory
                            # The cache should be in templates/cache/structure_name
                            structure_name = None
                            if hasattr(self.template_manager, 'current_structure_name'):
                                structure_name = self.template_manager.current_structure_name
                            elif hasattr(self.template_manager, 'last_structure_name'):
                                structure_name = self.template_manager.last_structure_name
                            
                            if structure_name:
                                # Clean up structure name for file system
                                safe_name = structure_name.replace(" ", "_").replace("/", "-").replace("\\", "-").replace("'", "")
                                cache_dir = os.path.join(self.template_manager.paths["templates_dir"], "cache", safe_name)
                                
                                # Try to find the file in the cache (both with the placeholder and without)
                                # Check with the exact filename first
                                if os.path.exists(os.path.join(cache_dir, lookup_filename)):
                                    source_file = os.path.join(cache_dir, lookup_filename)
                                    print(f"Found source file in cache: {source_file}")
                                else:
                                    # For files with placeholders, we need to look for the original file
                                    # Extract the base name and extension
                                    filename_parts = os.path.splitext(lookup_filename)
                                    if len(filename_parts) > 1:
                                        base_name, ext = filename_parts
                                        
                                        # Go through all files in the cache directory
                                        if os.path.exists(cache_dir):
                                            for cached_file in os.listdir(cache_dir):
                                                # Check if it has the same extension
                                                if cached_file.endswith(ext):
                                                    source_file = os.path.join(cache_dir, cached_file)
                                                    print(f"Found source file with matching extension in cache: {source_file}")
                                                    break
                    
                        # Create the file
                        if source_file and os.path.exists(source_file):
                            # Copy the source file to the destination
                            print(f"Copying file from cache: {source_file} -> {file_path}")
                            shutil.copy2(source_file, file_path)
                            
                            # If it's a text file, replace any placeholders in the content
                            if self._is_text_file(source_file):
                                self._replace_template_placeholders(file_path, project_name)
                        else:
                            # Create an empty file if no source file was found
                            print(f"Creating empty file (no source found in cache): {file_path}")
                            open(file_path, 'a').close()
        
        # Handle case where directories is a dict (may happen in recursive calls)
        elif isinstance(directories, dict):
            for folder_name, sub_items in directories.items():
                # Replace placeholders in folder_name if needed
                if isinstance(folder_name, str):
                    if project_name_placeholder_double in folder_name:
                        new_folder_name = folder_name.replace(project_name_placeholder_double, project_name)
                        print(f"Renamed folder in structure: {folder_name} -> {new_folder_name}")
                        folder_name = new_folder_name
                    elif project_name_placeholder_single in folder_name:
                        new_folder_name = folder_name.replace(project_name_placeholder_single, project_name)
                        print(f"Renamed folder in structure: {folder_name} -> {new_folder_name}")
                        folder_name = new_folder_name
                
                # Create the parent folder
                folder_path = os.path.join(project_path, folder_name)
                os.makedirs(folder_path, exist_ok=True)
                
                # Process subfolders recursively - pass the original project name
                # Only process if there are subitems
                if sub_items:
                    self._create_folder_structure(folder_path, sub_items, original_project_name=project_name)
    
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
        """Replace placeholder content in a file with project-specific values"""
        file_path = os.path.normpath(file_path)  # Normalize path for cross-platform compatibility
        
        try:
            # Skip very large files to avoid performance issues
            if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10 MB
                print(f"Skipping placeholder replacement in large file: {file_path}")
                return
            
            # Use a safe reading approach with explicit encoding
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with a different encoding
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                except:
                    print(f"Skipping placeholder replacement in non-text file: {file_path}")
                    return
            
            # Check if there are any placeholders to replace
            original_content = content
            
            # Create a dict of replacements
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            current_year = datetime.datetime.now().strftime("%Y")
            
            replacements = {
                "{{PROJECT_NAME}}": project_name,
                "{PROJECT_NAME}": project_name,
                "{{PROJECT NAME}}": project_name,
                "{PROJECT NAME}": project_name,
                "{{PROJECTNAME}}": project_name,
                "{PROJECTNAME}": project_name,
                "{{project_name}}": project_name.lower(),
                "{project_name}": project_name.lower(),
                "{{Project_Name}}": project_name.title(),
                "{Project_Name}": project_name.title(),
                "{{DATE}}": current_date,
                "{DATE}": current_date,
                "{{YEAR}}": current_year,
                "{YEAR}": current_year
            }
            
            # Apply all replacements
            placeholders_found = False
            for placeholder, value in replacements.items():
                if placeholder in content:
                    placeholders_found = True
                    content = content.replace(placeholder, value)
            
            if placeholders_found:
                print(f"Replaced placeholders in file: {file_path}")
                # Use a safe writing approach
                temp_file = file_path + ".tmp"
                try:
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    # On Windows, we need to remove the destination file first
                    if platform.system() == "Windows" and os.path.exists(file_path):
                        os.remove(file_path)
                    os.rename(temp_file, file_path)
                except Exception as e:
                    print(f"Error writing to temp file, trying direct write: {e}")
                    # Fall back to direct write
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
            
        except UnicodeDecodeError:
            # Not a text file or uses a different encoding
            print(f"Skipping placeholder replacement in non-text file: {file_path}")
        except Exception as e:
            print(f"Error replacing placeholders in {file_path}: {e}")
    
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

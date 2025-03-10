#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import threading
import datetime
import shutil
import sys
import json

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
            
            # If template_file is a template name, look it up
            template_obj = None
            if template_file and not os.path.exists(template_file):
                # It might be a template name, try to find it
                template_obj = self.template_manager.get_template_by_name(template_file)
                if template_obj:
                    if template_obj.get('type') == 'directory':
                        template_file = template_obj.get('path')
                    else:
                        template_file = template_obj.get('file', '')
            
            # Check if we need to get structure name from the template
            if template_obj and not structure_name:
                # Check if template has a structure_name
                if 'structure_name' in template_obj:
                    structure_name = template_obj.get('structure_name')
                # For directory templates, check the template.json file
                elif template_obj.get('type') == 'directory' and os.path.exists(template_file):
                    template_json_path = os.path.join(template_file, "template.json")
                    if os.path.exists(template_json_path):
                        try:
                            with open(template_json_path, 'r') as f:
                                template_info = json.load(f)
                                if 'structure_name' in template_info:
                                    structure_name = template_info['structure_name']
                        except Exception as e:
                            print(f"Error reading template.json: {e}")
            
            # Create folder structure based on template or type
            if structure_name and structure_name in self.template_manager.custom_structures:
                # Use custom structure
                directories = self.template_manager.get_structure(structure_name)
            else:
                # Use default structure for project type
                directories = self.template_manager.get_default_structure(project_type)
            
            # Create all directories
            self._create_folder_structure(project_path, directories)
            
            # Copy template file if selected
            if template_file and os.path.exists(template_file):
                self._process_template(template_file, project_path, project_name, project_type)
            
            # Create README file
            create_readme_file(project_path, project_name, project_type, directories)
            
            # Add to recent projects
            add_to_recent_projects(project_path)
            
            return True, project_path
            
        except Exception as e:
            error_msg = f"Failed to create project: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    def _create_folder_structure(self, project_path, directories):
        """Create folder structure with improved handling of nested directories and files"""
        if isinstance(directories, list):
            for item in directories:
                if isinstance(item, dict):
                    # Handle nested dictionary
                    for folder_name, sub_items in item.items():
                        # Create the parent folder
                        folder_path = os.path.join(project_path, folder_name)
                        os.makedirs(folder_path, exist_ok=True)
                        
                        # Process subfolders recursively
                        self._create_folder_structure(folder_path, sub_items)
                else:
                    # Handle string items (files or simple folders)
                    name = item
                    is_folder = name.endswith('/')
                    
                    if is_folder:
                        # It's a folder (ending with slash)
                        name = name[:-1]  # Remove the trailing slash
                        folder_path = os.path.join(project_path, name)
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
                        
                        # Create an empty file
                        open(file_path, 'a').close()
    
    def _process_template(self, template_file, project_path, project_name, project_type):
        """Process template files with improved handling for different template types"""
        # Determine if this is a single file or a template directory
        if os.path.isdir(template_file):
            self._copy_template_directory(template_file, project_path, project_name)
        else:
            self._copy_template_file(template_file, project_path, project_name, project_type)
    
    def _copy_template_directory(self, template_dir, project_path, project_name):
        """Copy a directory template, renaming files that match specific patterns"""
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
                    part = part.replace("{{PROJECT_NAME}}", project_name)
                    rel_path_parts.append(part)
                rel_path = os.path.join(*rel_path_parts)
                target_dir = os.path.join(project_path, rel_path)
            
            # Create target directory
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy files, renaming any with {{PROJECT_NAME}} in them
            for file in files:
                source_file = os.path.join(root, file)
                
                # Handle file renaming if needed
                target_file_name = file.replace("{{PROJECT_NAME}}", project_name)
                target_file = os.path.join(target_dir, target_file_name)
                
                # Copy the file
                shutil.copy2(source_file, target_file)
                
                # If it's a text file that might need content replacement
                if self._is_text_file(source_file):
                    self._replace_template_placeholders(target_file, project_name)
    
    def _is_text_file(self, file_path):
        """Check if a file is likely a text file that can have placeholders replaced"""
        # Basic check based on extension
        text_extensions = ['.txt', '.md', '.json', '.xml', '.html', '.css', '.js', '.py', '.c', '.cpp', '.h', '.java', '.config']
        _, ext = os.path.splitext(file_path.lower())
        return ext in text_extensions
    
    def _replace_template_placeholders(self, file_path, project_name):
        """Replace placeholder content in a file with project-specific values"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Create a dict of replacements
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            current_year = datetime.datetime.now().strftime("%Y")
            
            replacements = {
                "{{PROJECT_NAME}}": project_name,
                "{{PROJECT NAME}}": project_name,
                "{{PROJECTNAME}}": project_name,
                "{{project_name}}": project_name.lower(),
                "{{DATE}}": current_date,
                "{{YEAR}}": current_year
            }
            
            # Apply all replacements
            for placeholder, value in replacements.items():
                content = content.replace(placeholder, value)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except UnicodeDecodeError:
            # Not a text file or uses a different encoding
            pass
        except Exception as e:
            print(f"Error replacing placeholders in {file_path}: {e}")
    
    def _copy_template_file(self, template_file, project_path, project_name, project_type):
        """Copy the template file to the appropriate location in the project"""
        filename = os.path.basename(template_file)
        _, ext = os.path.splitext(filename)
        
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
        
        # Copy and rename the template file
        new_filename = f"{project_name}{ext}"
        dest_path = os.path.join(dest_folder, new_filename)
        shutil.copy2(template_file, dest_path)
    
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

#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import threading
import datetime
import shutil
from tkinter import Toplevel, Label, Frame, messagebox, ttk
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
        """Create folder structure with improved handling of nested directories"""
        for directory in directories:
            # Support for nested directories using forward slashes
            dir_path = os.path.join(project_path, directory.replace('/', os.sep))
            os.makedirs(dir_path, exist_ok=True)
    
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
            # Get relative path from template dir
            rel_path = os.path.relpath(root, template_dir)
            if rel_path == '.':  # Root directory
                target_dir = project_path
            else:
                target_dir = os.path.join(project_path, rel_path)
            
            # Create target directory
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy files, renaming any with {{PROJECT_NAME}} in them
            for file in files:
                source_file = os.path.join(root, file)
                
                # Handle file renaming if needed
                target_file_name = file.replace('{{PROJECT_NAME}}', project_name)
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
        """Replace placeholders in text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace placeholders
            content = content.replace('{{PROJECT_NAME}}', project_name)
            content = content.replace('{{DATE}}', datetime.datetime.now().strftime('%Y-%m-%d'))
            content = content.replace('{{YEAR}}', datetime.datetime.now().strftime('%Y'))
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except (UnicodeDecodeError, IOError):
            # Not a text file or can't read it - just skip placeholder replacement
            pass
    
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
        
        # Create progress window
        progress_window = self._create_progress_window(len(self.project_queue))
        
        for i, (name, output_dir, template_file, project_type, 
               use_version_control, create_backup, structure_name) in enumerate(self.project_queue):
            
            # Update progress
            if progress_window:
                progress_window.update_status(f"Creating project: {name}")
                progress_window.update_progress(i + 1)
            
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
        
        # Close progress window
        if progress_window and progress_window.winfo_exists():
            progress_window.destroy()
        
        # Call callback with results
        if callback:
            # Safer way to handle callback to the main thread
            import tkinter as tk
            if tk._default_root:
                tk._default_root.after(100, lambda: callback(results))
            else:
                # Fallback if no root exists
                callback(results)
    
    def _create_progress_window(self, total_projects):
        """Create a progress window for batch processing"""
        return BatchProgressWindow(total_projects)


class BatchProgressWindow(Toplevel):
    """Progress window for batch project creation"""
    def __init__(self, total_projects):
        super().__init__()
        self.title("Creating Projects")
        self.geometry("400x150")
        self.resizable(False, False)
        self.total_projects = total_projects
        
        self.transient()  # Make window appear on top
        self.grab_set()   # Make window modal
        
        self.main_frame = Frame(self, padx=20, pady=20)
        self.main_frame.pack(fill="both", expand=True)
        
        # Status label
        self.status_var = Label(self.main_frame, text="Initializing...", anchor="w")
        self.status_var.pack(fill="x", pady=(0, 10))
        
        # Progress counter
        self.counter_frame = Frame(self.main_frame)
        self.counter_frame.pack(fill="x", pady=(0, 10))
        
        self.counter_label = Label(self.counter_frame, 
                                 text=f"Creating project 0 of {self.total_projects}")
        self.counter_label.pack(side="left")
        
        # Progress bar
        self.progress = ttk.Progressbar(self.main_frame, orient="horizontal", 
                                      length=360, mode="determinate", maximum=self.total_projects)
        self.progress.pack(fill="x")
        
        # Center window on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    def update_status(self, text):
        """Update the status text"""
        self.status_var.config(text=text)
        self.update_idletasks()
    
    def update_progress(self, current):
        """Update the progress bar and counter"""
        self.counter_label.config(text=f"Creating project {current} of {self.total_projects}")
        self.progress["value"] = current
        self.update_idletasks()

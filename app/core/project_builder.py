#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import threading
import datetime
import shutil
import sys

# Detect which UI framework is being used
if 'PyQt5' in sys.modules:
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
    from PyQt5.QtCore import Qt, QTimer
    UI_FRAMEWORK = 'pyqt'
    
    # Define PyQt version of progress window here to avoid NameError
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
    
else:
    from tkinter import Toplevel, Label, Frame, messagebox, ttk
    UI_FRAMEWORK = 'tkinter'
    
    # Define Tkinter version of progress window
    class BatchProgressWindow(Toplevel):
        """Tkinter version of the batch progress window"""
        
        def __init__(self, total_projects):
            super().__init__()
            self.title("Creating Projects")
            self.geometry("400x150")
            self.resizable(False, False)
            self.protocol("WM_DELETE_WINDOW", lambda: None)  # Prevent closing
            
            # Create a frame for the content
            main_frame = Frame(self, padx=20, pady=20)
            main_frame.pack(fill="both", expand=True)
            
            # Status label
            self.status_var = Label(main_frame, text="Preparing...")
            self.status_var.pack(anchor="w", pady=(0, 10))
            
            # Progress bar
            self.progress = ttk.Progressbar(main_frame, orient="horizontal", length=360, mode="determinate")
            self.progress["maximum"] = total_projects
            self.progress["value"] = 0
            self.progress.pack(fill="x", pady=(0, 10))
            
            # Cancel button (disabled for now)
            self.cancel_btn = ttk.Button(main_frame, text="Cancel", state="disabled")
            self.cancel_btn.pack(side="right")
            
            # Center the window
            self.update_idletasks()
            width = self.winfo_width()
            height = self.winfo_height()
            x = (self.winfo_screenwidth() // 2) - (width // 2)
            y = (self.winfo_screenheight() // 2) - (height // 2)
            self.geometry(f"+{x}+{y}")
        
        def update_status(self, text):
            """Update the status text"""
            self.status_var.config(text=text)
            self.update_idletasks()
        
        def update_progress(self, current):
            """Update the progress bar"""
            self.progress["value"] = current
            self.update_idletasks()

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

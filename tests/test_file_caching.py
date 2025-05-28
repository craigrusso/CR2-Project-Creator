#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test file for verifying file caching functionality
"""

import os
import sys
import shutil
import tempfile
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QPushButton, QLabel, QFileDialog, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt

# Import our modules
from app.utils.file_cache_manager import FileCacheManager
from app.utils.cache_preferences import CachePreferences
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder

class FileCachingTestWindow(QMainWindow):
    """Test window for file caching functionality"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Caching Test")
        self.setMinimumSize(800, 600)
        
        # Test paths
        self.test_dir = tempfile.mkdtemp()
        self.test_files_dir = os.path.join(self.test_dir, "test_files")
        self.template_dir = os.path.join(self.test_dir, "template")
        self.cache_dir = os.path.join(self.test_dir, "cache")
        self.output_dir = os.path.join(self.test_dir, "output")
        
        # Create directories
        os.makedirs(self.test_files_dir, exist_ok=True)
        os.makedirs(self.template_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("File Caching Test")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title)
        
        # Add test paths information
        paths_label = QLabel(f"Test Directory: {self.test_dir}")
        layout.addWidget(paths_label)
        
        # Add cache manager
        self.cache_manager = FileCacheManager(self.cache_dir)
        
        # Add test tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File Structure"])
        layout.addWidget(self.tree)
        
        # Add buttons
        self.add_button(layout, "Create Test Files", self.create_test_files)
        self.add_button(layout, "Cache Files", self.cache_files)
        self.add_button(layout, "Show Cache Stats", self.show_cache_stats)
        self.add_button(layout, "Create Project from Cache", self.create_project)
        self.add_button(layout, "Clean Up", self.clean_up)
        
        # Create test files after UI is set up
        self.create_test_files()
    
    def add_button(self, layout, text, callback):
        """Helper to add a button to the layout"""
        button = QPushButton(text)
        button.clicked.connect(callback)
        layout.addWidget(button)
        return button
    
    def create_test_files(self):
        """Create test files for caching"""
        # Clear existing files
        if os.path.exists(self.test_files_dir):
            shutil.rmtree(self.test_files_dir)
        os.makedirs(self.test_files_dir, exist_ok=True)
        
        # Copy our existing test files instead of creating new ones
        
        # Copy the README file
        readme_src = os.path.join(os.getcwd(), "project_readme.txt")
        readme_dst = os.path.join(self.test_files_dir, "README.txt")
        if os.path.exists(readme_src):
            shutil.copy2(readme_src, readme_dst)
            self.log(f"Copied README file to test directory")
        else:
            # Fallback to creating a simple text file
            text_file = os.path.join(self.test_files_dir, "README.txt")
            with open(text_file, "w") as f:
                f.write("This is a test file with {{PROJECT_NAME}} placeholder\n")
            self.log(f"Created fallback README file")
        
        # Copy the binary file
        binary_src = os.path.join(os.getcwd(), "test_binary.bin")
        binary_dst = os.path.join(self.test_files_dir, "binary.bin")
        if os.path.exists(binary_src):
            shutil.copy2(binary_src, binary_dst)
            self.log(f"Copied binary file to test directory")
        else:
            # Fallback to creating a simple binary file
            binary_file = os.path.join(self.test_files_dir, "binary.bin")
            with open(binary_file, "wb") as f:
                f.write(os.urandom(1024))  # 1KB of random data
            self.log(f"Created fallback binary file")
        
        # Copy nested directory structure
        test_data_src = os.path.join(os.getcwd(), "test_data")
        test_data_dst = os.path.join(self.test_files_dir, "data")
        if os.path.exists(test_data_src):
            shutil.copytree(test_data_src, test_data_dst)
            self.log(f"Copied nested directory structure to test directory")
        else:
            # Fallback to creating a simple nested structure
            nested_dir = os.path.join(self.test_files_dir, "nested")
            os.makedirs(nested_dir, exist_ok=True)
            nested_file = os.path.join(nested_dir, "nested.txt")
            with open(nested_file, "w") as f:
                f.write("This is a nested file\n")
            self.log(f"Created fallback nested directory structure")
        
        # Update tree view
        self.update_tree()
        
        # Log
        self.log(f"Created test files in {self.test_files_dir}")
    
    def update_tree(self):
        """Update the tree view with the current structure"""
        self.tree.clear()
        
        # Add test files directory
        root_item = QTreeWidgetItem(self.tree, ["Test Files"])
        self.add_directory_to_tree(self.test_files_dir, root_item)
        
        # Add cache directory if it exists
        if os.path.exists(self.cache_dir):
            cache_item = QTreeWidgetItem(self.tree, ["Cache"])
            self.add_directory_to_tree(self.cache_dir, cache_item)
        
        # Add output directory if it exists
        if os.path.exists(self.output_dir) and os.listdir(self.output_dir):
            output_item = QTreeWidgetItem(self.tree, ["Output"])
            self.add_directory_to_tree(self.output_dir, output_item)
        
        # Expand all items
        self.tree.expandAll()
    
    def add_directory_to_tree(self, directory, parent_item):
        """Add a directory and its contents to the tree"""
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            
            if os.path.isdir(item_path):
                # Add directory
                dir_item = QTreeWidgetItem(parent_item, [item])
                self.add_directory_to_tree(item_path, dir_item)
            else:
                # Add file
                QTreeWidgetItem(parent_item, [item])
    
    def cache_files(self):
        """Cache the test files"""
        # Cache the files
        template_name = "TestTemplate"
        
        # Cache files from the test directory
        for root, dirs, files in os.walk(self.test_files_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, self.test_files_dir)
                if relative_path == ".":
                    relative_path = None
                    
                # Cache file
                result = self.cache_manager.cache_file(file_path, template_name, relative_path)
                
                # Log result
                if result:
                    self.log(f"Cached file: {file_path} -> {result['cache_path']}")
                else:
                    self.log(f"Failed to cache file: {file_path}")
        
        # Update tree
        self.update_tree()
    
    def show_cache_stats(self):
        """Show cache statistics"""
        stats = self.cache_manager.get_cache_stats()
        
        self.log(f"Cache Statistics:")
        self.log(f"  Files: {stats['cached_files']}")
        self.log(f"  Size: {stats['total_size_human']}")
        self.log(f"  Templates: {stats['template_count']}")
        self.log(f"  Hits: {stats['hits']}")
        self.log(f"  Misses: {stats['misses']}")
    
    def create_project(self):
        """Create a project from cached files"""
        template_name = "TestTemplate"
        project_name = "TestProject"
        project_path = os.path.join(self.output_dir, project_name)
        
        # Clear existing project
        if os.path.exists(project_path):
            shutil.rmtree(project_path)
        os.makedirs(project_path, exist_ok=True)
        
        # Get all cached files
        cached_files = self.cache_manager.get_all_cached_files(template_name)
        
        # Copy files to project
        for file_key, file_info in cached_files.items():
            # Determine destination path
            if file_info.get("relative_path"):
                rel_dir = os.path.join(project_path, file_info["relative_path"])
                os.makedirs(rel_dir, exist_ok=True)
                dest_path = os.path.join(rel_dir, file_info["file_name"])
            else:
                dest_path = os.path.join(project_path, file_info["file_name"])
            
            # Copy file
            try:
                shutil.copy2(file_info["cache_path"], dest_path)
                self.log(f"Copied file to project: {file_info['cache_path']} -> {dest_path}")
                
                # Replace placeholders if it's a text file
                if self.is_text_file(dest_path):
                    self.replace_placeholders(dest_path, project_name)
                    self.log(f"Replaced placeholders in {dest_path}")
            except Exception as e:
                self.log(f"Error copying file: {e}")
        
        # Update tree
        self.update_tree()
    
    def is_text_file(self, file_path):
        """Check if a file is a text file"""
        text_extensions = [".txt", ".md", ".json", ".xml", ".html", ".css", ".js", ".py"]
        _, ext = os.path.splitext(file_path.lower())
        return ext in text_extensions
    
    def replace_placeholders(self, file_path, project_name):
        """Replace placeholders in a text file"""
        try:
            with open(file_path, "r") as f:
                content = f.read()
            
            # Replace placeholders
            content = content.replace("{{PROJECT_NAME}}", project_name)
            content = content.replace("${PROJECT_NAME}", project_name)
            
            with open(file_path, "w") as f:
                f.write(content)
                
            return True
        except Exception as e:
            self.log(f"Error replacing placeholders: {e}")
            return False
    
    def clean_up(self):
        """Clean up test files"""
        try:
            shutil.rmtree(self.test_dir)
            self.log(f"Cleaned up test directory: {self.test_dir}")
        except Exception as e:
            self.log(f"Error cleaning up: {e}")
    
    def log(self, message):
        """Log a message to the console"""
        print(message)

# Main function
def main():
    """Test file caching and project creation with cached files"""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    cache_test_dir = os.path.join(temp_dir, "cache_test")
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(cache_test_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Temporary directory: {temp_dir}")
    print(f"Cache test directory: {cache_test_dir}")
    print(f"Output directory: {output_dir}")
    
    try:
        # Create a test file to cache
        test_file_path = os.path.join(cache_test_dir, "test_file.txt")
        with open(test_file_path, 'w') as f:
            f.write("This is a test file with {{PROJECT_NAME}} placeholder")
            
        # Create a test Premier Pro file (just a text file for testing)
        test_prproj_path = os.path.join(cache_test_dir, "Test_Project.prproj")
        with open(test_prproj_path, 'w') as f:
            f.write("This is a fake Premier Pro file for {{PROJECT_NAME}}")
        
        # Create an instance of TemplateManager
        print("\n=== Initializing Template Manager ===")
        template_manager = TemplateManager()
        
        # Check if template_manager has cache path
        if not hasattr(template_manager, 'paths') or 'templates_cache_dir' not in template_manager.paths:
            print("Adding templates_cache_dir to template_manager.paths")
            if not hasattr(template_manager, 'paths'):
                template_manager.paths = {}
                
            # Use a cache directory in our temporary directory
            template_manager.paths['templates_cache_dir'] = os.path.join(temp_dir, "cache")
        
        # Get a structure to modify
        print("\n=== Getting structure ===")
        structure_name = "Template_THIS IS TEST"
        
        # First check if the structure exists
        if hasattr(template_manager, 'structures') and structure_name in template_manager.structures:
            structure_data = template_manager.structures[structure_name]
        else:
            print(f"Structure {structure_name} not found, creating a new one")
            # Create a simple structure
            structure_data = []
            print("Creating a new structure")

        # Modify the structure to include our test files
        print("\n=== Modifying structure to include test files ===")
        if isinstance(structure_data, list) and len(structure_data) > 0:
            # Structure data is a list of directories - use the first one
            first_item = structure_data[0]
            if isinstance(first_item, dict):
                # Add type and name if not present
                if 'type' not in first_item:
                    first_item['type'] = 'directory'
                if 'name' not in first_item:
                    first_item['name'] = '01_PROJECT_FILES'
                
                # Add children if not present
                if 'children' not in first_item:
                    first_item['children'] = []
                
                # Add our test files to the children
                first_item['children'].append({
                    'type': 'file',
                    'name': 'test_file.txt',
                    'path': test_file_path,
                    'is_binary': False
                })
                
                first_item['children'].append({
                    'type': 'file',
                    'name': '{{PROJECT_NAME}}.prproj',
                    'path': test_prproj_path,
                    'is_binary': False
                })
                
                print(f"Added test files to structure")
        else:
            # Create a simple structure with our test files
            structure_data = [
                {
                    'type': 'directory',
                    'name': '01_PROJECT_FILES',
                    'children': [
                        {
                            'type': 'file',
                            'name': 'test_file.txt',
                            'path': test_file_path,
                            'is_binary': False
                        },
                        {
                            'type': 'file',
                            'name': '{{PROJECT_NAME}}.prproj',
                            'path': test_prproj_path,
                            'is_binary': False
                        }
                    ]
                }
            ]
            
            # Add to structures if it exists
            if hasattr(template_manager, 'structures'):
                template_manager.structures[structure_name] = structure_data
                print(f"Created new structure with test files")
            
        # Cache the files
        print("\n=== Caching files ===")
        # Use a simple file caching function to avoid dependencies
        def cache_files(structure, cache_dir):
            """Simple function to cache files in a structure"""
            os.makedirs(cache_dir, exist_ok=True)
            
            def process_item(item):
                """Process a structure item and cache files"""
                if isinstance(item, dict):
                    if item.get('type') == 'file' and 'path' in item:
                        path = item['path']
                        if os.path.exists(path):
                            # Cache the file
                            filename = os.path.basename(path)
                            cache_path = os.path.join(cache_dir, filename)
                            shutil.copy2(path, cache_path)
                            print(f"Cached file: {path} -> {cache_path}")
                            
                            # Add cache path to the item
                            item['cache_path'] = cache_path
                    
                    # Process children if present
                    if 'children' in item and isinstance(item['children'], list):
                        for child in item['children']:
                            process_item(child)
                            
                elif isinstance(item, list):
                    for child in item:
                        process_item(child)
                        
            # Process the structure
            process_item(structure)
            return structure
            
        # Create cache directory
        cache_dir = os.path.join(template_manager.paths['templates_cache_dir'], "TEST_CACHE")
        print(f"Caching files to: {cache_dir}")
        
        # Cache the files
        updated_structure = cache_files(structure_data, cache_dir)
        
        # Print cache paths
        if isinstance(updated_structure, list) and len(updated_structure) > 0:
            first_item = updated_structure[0]
            if isinstance(first_item, dict) and 'children' in first_item:
                print("Cache paths in updated structure:")
                for child in first_item['children']:
                    if isinstance(child, dict) and 'cache_path' in child:
                        print(f"  {child.get('name', 'unnamed')}: {child['cache_path']}")
            
        # Create ProjectBuilder
        print("\n=== Creating ProjectBuilder ===")
        project_builder = ProjectBuilder(template_manager)
        
        # Create project with the updated structure
        print("\n=== Creating project with updated structure ===")
        project_name = "CACHE_TEST_PROJECT"
        project_path = os.path.join(output_dir, project_name)
        
        # Create the project
        success, message = project_builder.create_project(
            project_name=project_name,
            output_path=output_dir,
            structure_data=updated_structure  # Use the updated structure directly
        )
        
        # Check result
        if success:
            print(f"Project creation successful: {message}")
            
            # List created files
            print("\n=== Files created ===")
            for root, dirs, files in os.walk(project_path):
                rel_path = os.path.relpath(root, project_path)
                if rel_path == ".":
                    print(f"Files in project root:")
                else:
                    print(f"Files in {rel_path}:")
                    
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    print(f"  - {file} ({file_size} bytes)")
                    
                    # Print content for small text files
                    if file_size < 1000 and (file.endswith(".txt") or file.endswith(".prproj")):
                        with open(file_path, 'r') as f:
                            content = f.read()
                            print(f"    Content: {content}")
        else:
            print(f"Project creation failed: {message}")
    
    finally:
        # Clean up
        print(f"\nCleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main() 
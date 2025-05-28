#!/usr/bin/env python3
# Test script for diagnosing template lifecycle issues

import os
import sys
import json
import time
import shutil
import tempfile
from pprint import pprint

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import PyQt modules
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget, QTextEdit, QScrollArea
from PyQt6.QtCore import Qt

# Import template modules
from app.templates.template_manager import TemplateManager
from app.templates.template_operations import TemplateOperations
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
import app.constants as constants

class TemplateLifecycleTest(QMainWindow):
    """Test class for diagnosing template lifecycle issues"""
    
    def __init__(self):
        super().__init__()
        
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.custom_structures_dir = os.path.join(self.test_dir, 'custom_structures')
        self.templates_dir = os.path.join(self.test_dir, 'templates')
        
        # Create test directories
        os.makedirs(self.custom_structures_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Set up UI
        self.setWindowTitle("Template Lifecycle Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Debug log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("font-family: monospace; font-size: 10pt;")
        
        # Scroll area for log
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.log_area)
        
        # Create test control buttons
        self.create_simple_btn = QPushButton("Step 1: Create Simple Template")
        self.create_complex_btn = QPushButton("Step 2: Create Complex Template")
        self.verify_storage_btn = QPushButton("Step 3: Verify Template Storage")
        self.edit_template_btn = QPushButton("Step 4: Edit Template")
        self.verify_updates_btn = QPushButton("Step 5: Verify Template Updates")
        
        # Connect buttons to functions
        self.create_simple_btn.clicked.connect(self.create_simple_template)
        self.create_complex_btn.clicked.connect(self.create_complex_template)
        self.verify_storage_btn.clicked.connect(self.verify_template_storage)
        self.edit_template_btn.clicked.connect(self.edit_template)
        self.verify_updates_btn.clicked.connect(self.verify_template_updates)
        
        # Add widgets to layout
        self.layout.addWidget(QLabel("<h2>Template Lifecycle Test</h2>"))
        self.layout.addWidget(self.create_simple_btn)
        self.layout.addWidget(self.create_complex_btn)
        self.layout.addWidget(self.verify_storage_btn)
        self.layout.addWidget(self.edit_template_btn)
        self.layout.addWidget(self.verify_updates_btn)
        self.layout.addWidget(scroll_area)
        
        # Initialize template manager
        self.log("Initializing test environment...")
        self.initialize_template_manager()
        
    def log(self, message):
        """Log a message to the UI"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        print(f"[{timestamp}] {message}")
        
    def initialize_template_manager(self):
        """Initialize the template manager with test directories"""
        # Patch the config paths function to use our test directories
        original_get_config_paths = None
        
        # Import and patch the config paths
        try:
            from app.utils.utils import get_config_paths
            original_get_config_paths = get_config_paths
            
            def patched_get_config_paths():
                """Return test paths instead of real paths"""
                paths = original_get_config_paths()
                paths["templates_dir"] = self.templates_dir
                paths["custom_structures_dir"] = self.custom_structures_dir
                paths["template_directories_dir"] = os.path.join(self.test_dir, 'template_directories')
                return paths
                
            # Apply the patch
            import app.utils.utils
            app.utils.utils.get_config_paths = patched_get_config_paths
            
            # Create template manager with patched paths
            self.template_manager = TemplateManager()
            
            # Save a reference so we can access it as parent.template_manager 
            # (required for compatibility with EnhancedStructureEditor)
            self.template_manager = self.template_manager
            
            self.log(f"Template manager initialized with test paths")
            self.log(f"Templates dir: {self.templates_dir}")
            self.log(f"Custom structures dir: {self.custom_structures_dir}")
            
        except Exception as e:
            self.log(f"ERROR initializing template manager: {e}")
    
    def create_simple_template(self):
        """Step 1: Create a simple template with basic structure"""
        self.log("\n=== STEP 1: Creating Simple Template ===")
        
        try:
            # Create a basic template structure
            simple_structure = [
                {"Footage": []},
                {"Assets": []},
                {"Output": []}
            ]
            
            # Create template metadata
            template_name = "Test_Simple_Template"
            template_info = {
                "name": template_name,
                "description": "A simple test template",
                "tags": ["test", "simple"],
                "type": "Standard",
                "structure_name": template_name
            }
            
            # Save the structure
            self.log(f"Saving structure '{template_name}'...")
            success = self.template_manager.save_custom_structure(template_name, simple_structure)
            
            if success:
                self.log(f"✅ Structure saved successfully")
                
                # Save the template info
                template_path = os.path.join(self.templates_dir, f"{template_name}.json")
                with open(template_path, 'w') as f:
                    json.dump(template_info, f, indent=2)
                self.log(f"✅ Template info saved to {template_path}")
                
                # Reload templates to ensure it's loaded
                self.template_manager.load_templates()
                self.template_manager.load_custom_structures()
                self.log("Reloaded templates and structures")
                
                # Verify the template exists
                template = self.template_manager.get_template_by_name(template_name)
                if template:
                    self.log(f"✅ Template '{template_name}' found in template manager")
                    self.log(f"Template info: {json.dumps(template, indent=2)}")
                else:
                    self.log(f"❌ Template '{template_name}' NOT found in template manager")
                    
                # Verify the structure exists
                structure = self.template_manager.get_structure(template_name)
                if structure:
                    self.log(f"✅ Structure '{template_name}' found in template manager")
                    self.log(f"Structure content: {json.dumps(structure, indent=2)}")
                else:
                    self.log(f"❌ Structure '{template_name}' NOT found in template manager")
            else:
                self.log(f"❌ Failed to save structure '{template_name}'")
                
        except Exception as e:
            self.log(f"ERROR creating simple template: {e}")
    
    def create_complex_template(self):
        """Step 2: Create a more complex template with nested structure"""
        self.log("\n=== STEP 2: Creating Complex Template ===")
        
        try:
            # Create a complex template structure with nested folders
            complex_structure = [
                {"Footage": [
                    {"RAW": []},
                    {"Proxies": []}
                ]},
                {"Audio": [
                    {"Music": []},
                    {"SFX": []},
                    {"VO": []}
                ]},
                {"Graphics": [
                    {"Titles": []},
                    {"Animations": []}
                ]},
                {"Project_Files": []},
                {"Exports": [
                    {"Drafts": []},
                    {"Finals": []},
                    {"Archives": []}
                ]}
            ]
            
            # Create template metadata
            template_name = "Test_Complex_Template"
            template_info = {
                "name": template_name,
                "description": "A complex test template with nested folders",
                "tags": ["test", "complex", "nested"],
                "type": "Standard",
                "structure_name": template_name
            }
            
            # Save the structure
            self.log(f"Saving structure '{template_name}'...")
            success = self.template_manager.save_custom_structure(template_name, complex_structure)
            
            if success:
                self.log(f"✅ Structure saved successfully")
                
                # Save the template info
                template_path = os.path.join(self.templates_dir, f"{template_name}.json")
                with open(template_path, 'w') as f:
                    json.dump(template_info, f, indent=2)
                self.log(f"✅ Template info saved to {template_path}")
                
                # Reload templates to ensure it's loaded
                self.template_manager.load_templates()
                self.template_manager.load_custom_structures()
                self.log("Reloaded templates and structures")
                
                # Verify the template exists
                template = self.template_manager.get_template_by_name(template_name)
                if template:
                    self.log(f"✅ Template '{template_name}' found in template manager")
                else:
                    self.log(f"❌ Template '{template_name}' NOT found in template manager")
            else:
                self.log(f"❌ Failed to save structure '{template_name}'")
                
        except Exception as e:
            self.log(f"ERROR creating complex template: {e}")
    
    def verify_template_storage(self):
        """Step 3: Verify template storage format on disk"""
        self.log("\n=== STEP 3: Verifying Template Storage ===")
        
        try:
            # Verify structure files exist in the custom_structures_dir
            structure_files = [f for f in os.listdir(self.custom_structures_dir) if f.endswith('.json')]
            self.log(f"Found {len(structure_files)} structure files in custom structures directory:")
            for filename in structure_files:
                # Read and display the file content
                file_path = os.path.join(self.custom_structures_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        structure_data = json.load(f)
                    
                    self.log(f"✅ Structure file: {filename}")
                    self.log(f"  Name: {structure_data.get('name', 'N/A')}")
                    directories = structure_data.get('directories', [])
                    self.log(f"  Contains {len(directories)} root directories")
                    
                    # Show the first level of directories for verification
                    dirs_str = []
                    for item in directories:
                        if isinstance(item, dict):
                            for dir_name in item.keys():
                                dirs_str.append(dir_name)
                    self.log(f"  Folders: {', '.join(dirs_str)}")
                    
                except Exception as e:
                    self.log(f"❌ Error reading structure file {filename}: {e}")
            
            # Verify template files exist in the templates_dir
            template_files = [f for f in os.listdir(self.templates_dir) if f.endswith('.json')]
            self.log(f"\nFound {len(template_files)} template files in templates directory:")
            for filename in template_files:
                # Read and display the file content
                file_path = os.path.join(self.templates_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        template_data = json.load(f)
                    
                    self.log(f"✅ Template file: {filename}")
                    self.log(f"  Name: {template_data.get('name', 'N/A')}")
                    self.log(f"  Description: {template_data.get('description', 'N/A')}")
                    self.log(f"  Structure name: {template_data.get('structure_name', 'N/A')}")
                    
                except Exception as e:
                    self.log(f"❌ Error reading template file {filename}: {e}")
                    
        except Exception as e:
            self.log(f"ERROR verifying template storage: {e}")
    
    def edit_template(self):
        """Step 4: Edit a template structure using the enhanced structure editor"""
        self.log("\n=== STEP 4: Editing Template ===")
        
        try:
            # Select the simple template for editing
            template_name = "Test_Simple_Template"
            self.log(f"Attempting to edit template '{template_name}'")
            
            # Get the template structure
            structure = self.template_manager.get_structure(template_name)
            if not structure:
                self.log(f"❌ Could not find structure for '{template_name}'")
                return
                
            self.log(f"Structure before editing: {json.dumps(structure, indent=2)}")
            
            # Create the structure editor
            editor = EnhancedStructureEditor(
                self, 
                structure_name=template_name,
                structure=structure
            )
            
            # Instead of showing the editor (which would block the test),
            # we'll simulate editing the structure programmatically
            
            # 1. Update the template name
            new_template_name = f"{template_name}_Edited"
            self.log(f"Changing template name to '{new_template_name}'")
            editor.name_input.setText(new_template_name)
            
            # 2. Add a new folder to the structure
            self.log("Adding a new 'Documentation' folder to the structure")
            structure.append({"Documentation": []})
            
            # 3. Update the structure in the editor
            editor.load_structure(structure)
            
            # 4. Save the edited structure
            self.log("Saving edited structure...")
            success = editor.save_structure()
            
            if success:
                self.log(f"✅ Edited structure saved successfully")
                # Store the new name for verification in the next step
                self.edited_template_name = new_template_name
            else:
                self.log(f"❌ Failed to save edited structure")
                
        except Exception as e:
            self.log(f"ERROR editing template: {e}")
    
    def verify_template_updates(self):
        """Step 5: Verify that template updates were saved correctly"""
        self.log("\n=== STEP 5: Verifying Template Updates ===")
        
        try:
            # Check if we have an edited template name from previous step
            if not hasattr(self, 'edited_template_name'):
                self.log(f"❌ No edited template name found, cannot verify updates")
                return
                
            template_name = self.edited_template_name
            self.log(f"Verifying updates for template '{template_name}'")
            
            # Reload templates and structures to ensure we're getting the latest data
            self.template_manager.load_templates()
            self.template_manager.load_custom_structures()
            self.log("Reloaded templates and structures from disk")
            
            # Check if the structure file exists
            structure_filename = f"{template_name.replace(' ', '_')}.json"
            structure_path = os.path.join(self.custom_structures_dir, structure_filename)
            
            if os.path.exists(structure_path):
                self.log(f"✅ Structure file exists at {structure_path}")
                
                # Read and display the structure
                with open(structure_path, 'r') as f:
                    structure_data = json.load(f)
                
                self.log(f"Structure name in file: {structure_data.get('name', 'N/A')}")
                directories = structure_data.get('directories', [])
                self.log(f"Root directories ({len(directories)}):")
                
                # Show all directories for verification
                for item in directories:
                    if isinstance(item, dict):
                        for dir_name, children in item.items():
                            self.log(f"  - {dir_name} ({len(children)} children)")
                
                # Verify that our added 'Documentation' folder exists
                has_documentation = False
                for item in directories:
                    if isinstance(item, dict) and "Documentation" in item:
                        has_documentation = True
                        break
                        
                if has_documentation:
                    self.log(f"✅ 'Documentation' folder found in structure")
                else:
                    self.log(f"❌ 'Documentation' folder NOT found in structure")
                
            else:
                self.log(f"❌ Structure file does not exist at {structure_path}")
            
            # Check if the template was updated or if a new one was created
            template = self.template_manager.get_template_by_name(template_name)
            if template:
                self.log(f"✅ Updated template '{template_name}' found in template manager")
                self.log(f"Template info: {json.dumps(template, indent=2)}")
            else:
                self.log(f"❌ Updated template '{template_name}' NOT found in template manager")
                
            # Also check if the original template still exists
            original_name = "Test_Simple_Template"
            original_template = self.template_manager.get_template_by_name(original_name)
            if original_template:
                self.log(f"⚠️ Original template '{original_name}' still exists in template manager")
                self.log(f"Original template info: {json.dumps(original_template, indent=2)}")
            else:
                self.log(f"✅ Original template '{original_name}' no longer exists in template manager")
                
        except Exception as e:
            self.log(f"ERROR verifying template updates: {e}")
    
    def closeEvent(self, event):
        """Clean up temporary directory when the window is closed"""
        try:
            shutil.rmtree(self.test_dir)
            print(f"Removed temporary directory: {self.test_dir}")
        except Exception as e:
            print(f"Error removing temporary directory: {e}")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_window = TemplateLifecycleTest()
    test_window.show()
    sys.exit(app.exec()) 
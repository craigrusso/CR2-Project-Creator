import os
import sys
import time
from app.templates.template_operations import TemplateOperations

def main():
    print("Starting selective caching test...")
    
    # Initialize the template operations
    template_ops = TemplateOperations()
    # The templates are loaded automatically in the constructor
    
    # Print available templates
    templates = template_ops.templates
    print(f"Loaded {len(templates)} templates from {template_ops.paths['templates_dir']}")
    print("Available templates:")
    for template in templates:
        print(f" - {template.get('name')} (Type: {template.get('type')})")
    
    # Files to cache
    selected_files = [
        "main.py",
        "app/templates/template_operations.py",
        "test_caching.py"
    ]
    
    # Check if files exist
    for file in selected_files:
        print(f"File exists: {file} - {os.path.exists(file)}")
    
    # Find template by name
    template_name = "yyyy"  # Updated to use the correct template name
    template = None
    for t in template_ops.templates:
        if t.get("name") == template_name:
            template = t
            break
    
    if template:
        print(f"Found template: {template.get('name')}")
        print(f"Selected files before update: {template.get('selected_files', 'None')}")
        
        # Update template with selected files
        result = template_ops.update_template(template_name, {"selected_files": selected_files})
        if result:
            print(f"Successfully updated template {template_name} with {len(selected_files)} selected files: {selected_files}")
        else:
            print(f"Failed to update template {template_name}")
        
        # Wait a moment for file operations to complete
        time.sleep(2)
        
        # Check updated template details
        updated_template = None
        for t in template_ops.templates:
            if t.get("name") == template_name:
                updated_template = t
                break
                
        if updated_template:
            print(f"Updated template details:")
            print(f" - Name: {updated_template.get('name')}")
            print(f" - Type: {updated_template.get('type')}")
            print(f" - Selected files: {updated_template.get('selected_files', 'None')}")
            
            # Check if cache directory exists
            cache_dir = os.path.join(template_ops.paths["templates_dir"], "cache", template_ops.sanitize_filename(template_name))
            print(f"Cache directory path: {cache_dir}")
            print(f"Cache directory exists: {os.path.exists(cache_dir)}")
            
            if os.path.exists(cache_dir):
                cached_files = os.listdir(cache_dir)
                print(f"Found {len(cached_files)} files in cache directory:")
                for file in cached_files:
                    print(f" - {file}")
                
                # Check if all selected files are cached
                cached_file_count = 0
                for file in selected_files:
                    base_name = os.path.basename(file)
                    if base_name in cached_files:
                        print(f"File cached: {file} ✓")
                        cached_file_count += 1
                    else:
                        print(f"File not cached: {file} ✗")
                
                print(f"Cached {cached_file_count} of {len(selected_files)} selected files")
            else:
                print("Cache directory does not exist!")
                
                # Check parent directory
                parent_dir = os.path.dirname(cache_dir)
                print(f"Parent directory exists: {os.path.exists(parent_dir)}")
                
                if os.path.exists(parent_dir):
                    print(f"Parent directory contents: {os.listdir(parent_dir)}")
        else:
            print(f"Template {template_name} not found after update!")
    else:
        print(f"Template {template_name} not found!")

if __name__ == "__main__":
    main() 
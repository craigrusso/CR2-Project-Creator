import os
import sys
import json

# Set up paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our classes
from app.templates.template_manager import TemplateManager
from app.utils.utils import load_json_file

def main():
    """Debug the structure loading process"""
    # Create an instance of TemplateManager
    template_manager = TemplateManager()
    
    # Print paths information
    print("\n=== Paths Configuration ===")
    if hasattr(template_manager, 'paths'):
        for key, path in template_manager.paths.items():
            print(f"{key}: {path}")
            if os.path.exists(path):
                print(f"  - Path exists")
                if os.path.isdir(path):
                    files = os.listdir(path)
                    print(f"  - Contains {len(files)} items: {files[:5]}")
            else:
                print(f"  - Path does not exist")
    
    # Check structure files
    print("\n=== Structure Files ===")
    structures_dir = template_manager.paths.get('custom_structures_dir')
    if structures_dir and os.path.exists(structures_dir):
        structure_files = [f for f in os.listdir(structures_dir) if f.endswith('.json')]
        print(f"Found {len(structure_files)} structure files in {structures_dir}:")
        for file in structure_files:
            print(f"  - {file}")
            
            # Try loading the file
            try:
                file_path = os.path.join(structures_dir, file)
                structure_data = load_json_file(file_path)
                if structure_data:
                    print(f"    - Loaded successfully")
                    if 'name' in structure_data:
                        print(f"    - Structure name: {structure_data['name']}")
                    if 'display_name' in structure_data:
                        print(f"    - Display name: {structure_data['display_name']}")
            except Exception as e:
                print(f"    - Error loading: {e}")
                
    # Check custom_structures attribute
    print("\n=== Custom Structures ===")
    if hasattr(template_manager, 'custom_structures'):
        print(f"custom_structures dictionary has {len(template_manager.custom_structures)} items")
        for key, value in template_manager.custom_structures.items():
            print(f"  - {key}")
    else:
        print("No custom_structures attribute found")
        
    # Force loading of custom structures
    print("\n=== Forcing custom structure load ===")
    if hasattr(template_manager, 'load_custom_structures'):
        print("Calling load_custom_structures() directly...")
        template_manager.load_custom_structures()
        
        # Check again after forced loading
        if hasattr(template_manager, 'custom_structures'):
            print(f"After direct load: custom_structures has {len(template_manager.custom_structures)} items")
            for key, value in template_manager.custom_structures.items():
                print(f"  - {key}")
        else:
            print("Still no custom_structures attribute found")
            
    # Check for templates
    print("\n=== Templates ===")
    if hasattr(template_manager, 'templates'):
        print(f"templates list has {len(template_manager.templates)} items")
        for template in template_manager.templates:
            name = template.get('name', 'unnamed')
            print(f"  - {name}")
            if 'folder_structure' in template:
                print(f"    - Has folder_structure")
    else:
        print("No templates attribute found")
        
    # Debug structure retrieval function
    print("\n=== Structure Retrieval ===")
    if hasattr(template_manager, 'get_structure'):
        test_name = "Template_THIS IS TEST"
        print(f"Calling get_structure('{test_name}')...")
        result = template_manager.get_structure(test_name)
        if result:
            print(f"  - Structure found, type: {type(result)}")
            if isinstance(result, dict):
                print(f"  - Keys: {list(result.keys())}")
        else:
            print(f"  - No structure found for '{test_name}'")
    else:
        print("No get_structure method found")
    
    # Test if reference issue
    print("\n=== Testing Reference Issue ===")
    print("Creating a fresh copy of custom_structures...")
    
    # Try loading all structures directly from files
    direct_structures = {}
    if structures_dir and os.path.exists(structures_dir):
        for file in os.listdir(structures_dir):
            if file.endswith('.json'):
                try:
                    file_path = os.path.join(structures_dir, file)
                    structure_data = load_json_file(file_path)
                    if structure_data:
                        structure_name = file.replace('.json', '')
                        direct_structures[structure_name] = structure_data
                        print(f"  - Added {structure_name} to direct structures")
                except Exception as e:
                    print(f"  - Error loading {file}: {e}")
    
    print(f"Direct structures has {len(direct_structures)} items")
    
    # Try to attach directly to template_manager
    template_manager.direct_structures = direct_structures
    print("Attached direct_structures to template_manager")
    
if __name__ == "__main__":
    main() 
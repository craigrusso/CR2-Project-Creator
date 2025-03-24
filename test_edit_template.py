#!/usr/bin/env python3
# Simple test for template editing and file caching

import os
import json
import time
from app.templates.template_operations import TemplateOperations

# Create a test file
test_file_path = "test_edit_file.txt"
with open(test_file_path, "w") as f:
    f.write("Test file content for caching test")

print(f"Created test file: {test_file_path}")

# Initialize template operations
ops = TemplateOperations()
print(f"Template cache directory: {ops.paths.get('templates_cache_dir')}")

# Create a simple template
template_name = "TEST_EDIT_TEMPLATE"
template = {
    "name": template_name,
    "description": "Test template for edit testing",
    "category": "Test",
    "type": "Standard",
    "structure": {
        "name": "root",
        "type": "folder",
        "children": [
            {
                "name": "folder1",
                "type": "folder", 
                "children": []
            }
        ]
    }
}

# Save the template initially without files
template_path = os.path.join(ops.paths["templates_dir"], f"{template_name}.json")
print(f"\nSaving initial template to {template_path}...")
ops.save_template(
    template_name=template_name,
    structure=template["structure"],
    template_data=template,
    cache_files=True
)

# Verify template was saved
print(f"Checking if template exists at {template_path}...")
if os.path.exists(template_path):
    print("✅ Template saved successfully")
else:
    print("❌ Template not saved")
    exit(1)

# Load the template
with open(template_path, "r") as f:
    saved_template = json.load(f)
    
print(f"\nInitial template has {len(saved_template.get('files', []))} files")

# Now edit the template to add a file
print(f"\nAdding file {test_file_path} to template structure...")
saved_template["structure"]["children"].append({
    "name": os.path.basename(test_file_path),
    "type": "file",
    "original_path": os.path.abspath(test_file_path)
})

# Update the template
print("Updating template...")
success = ops.update_template(saved_template)
print(f"Update successful: {success}")

# Load the updated template
with open(template_path, "r") as f:
    updated_template = json.load(f)

# Check if files were properly cached
files = updated_template.get("files", [])
print(f"\nUpdated template has {len(files)} files")
print("Files in template:")
for f in files:
    print(f"  - {f.get('file_name')}: {f.get('cached_path', 'None')}")

# Now test renaming the template but keeping the same file
print("\n=== Testing template rename ===")
renamed_template = updated_template.copy()
new_name = "RENAMED_TEMPLATE"
renamed_template["name"] = new_name
print(f"Renaming template from '{updated_template['name']}' to '{new_name}'...")

# Update the renamed template
success = ops.update_template(renamed_template)
print(f"Rename update successful: {success}")

# Check that the original file path was used
if os.path.exists(template_path):
    print(f"✅ Original template file still exists at: {template_path}")
    
    # Verify the content has the new name
    with open(template_path, "r") as f:
        content = json.load(f)
    if content.get("name") == new_name:
        print(f"✅ Template file contains new name: {new_name}")
    else:
        print(f"❌ Template file has incorrect name: {content.get('name')}")
else:
    print(f"❌ Original template file no longer exists!")

# Check if a new file was mistakenly created
new_path = os.path.join(ops.paths["templates_dir"], f"{new_name}.json")
if os.path.exists(new_path) and template_path != new_path:
    print(f"❌ NEW FILE was incorrectly created at: {new_path}")
else:
    print(f"✅ No duplicate file was created")

# Check if cache directory exists
cache_dir = ops.paths.get("templates_cache_dir")
if cache_dir:
    template_cache_dir = os.path.join(cache_dir, template_name)
    print(f"\nTemplate cache directory: {template_cache_dir}")
    if os.path.exists(template_cache_dir):
        print("✅ Cache directory exists")
        print("Files in cache directory:")
        for root, dirs, files in os.walk(template_cache_dir):
            for file in files:
                file_path = os.path.join(root, file)
                print(f"  - {file_path}")
                # Verify file content
                if file.endswith(".txt"):
                    with open(file_path, "r") as f:
                        content = f.read()
                    print(f"    Content: {content[:30]}...")
    else:
        print("❌ Cache directory does not exist")
else:
    print("❌ No cache directory specified")

print("\nTest completed.") 
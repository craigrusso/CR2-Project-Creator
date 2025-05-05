# Project Folder Creation Fix

## Issue Fixed
Fixed project creation process to properly use folder names from custom structures. Previously, folders were being created with generic names like "unnamed_item_1", "unnamed_item_2", etc., instead of using the actual folder names defined in the structure.

## Root Cause
The `_process_template` method in `ProjectBuilder` wasn't handling the structure format correctly. The structure JSON file uses a format where each folder is represented as a dictionary with a single key (the folder name) and a list value (the children). The method was expecting a different format with explicit 'name' fields.

## Implementation Details

### Step 1: Updated `_process_template`
Added specific handling for the custom structure format in the `_process_template` method of `ProjectBuilder`. When a dictionary with a single key is encountered in a list of items, the key is treated as the folder name and the value as children.

```python
# Handle custom structure format: dict with single key as folder name
if isinstance(item, dict) and len(item.keys()) == 1:
    folder_name = list(item.keys())[0]  # Get the folder name (dict key)
    children = item.get(folder_name, [])  # Get the children (value)
    
    # Replace placeholders in the name if needed
    if placeholders:
        folder_name = self._replace_placeholders(folder_name, placeholders)
    
    # Create the directory
    dir_path = os.path.join(output_path, folder_name)
    print(f"DEBUG: Creating directory from structure: {dir_path}")
    
    if not dry_run:
        os.makedirs(dir_path, exist_ok=True)
    
    created_paths.append(dir_path)
    
    # Process children recursively
    if children:
        self._process_template(dir_path, children, placeholders, created_paths, dry_run)
```

### Step 2: Updated `_create_folder_structure`
Enhanced the `_create_folder_structure` method to directly handle the 'directories' field in the structure JSON:

```python
# Handle case where structure is a dict with 'directories' field
# (this is the format from our structure JSON files)
if isinstance(structure, dict) and 'directories' in structure:
    print(f"DEBUG: Found 'directories' field, processing that instead")
    self._process_template(output_path, structure['directories'], placeholders, created_paths, dry_run)
```

## Testing
Created test scripts to verify the fix:
- `test_fix_structure_processor.py`: Compares the original behavior with the enhanced behavior
- `test_verify_structure_fix.py`: Verifies the fix in a full project creation scenario

Testing confirmed that the fix correctly processes both the 'directories' field in the structure JSON and the individual folder dictionaries to create properly named directories.

## Results
When creating a project from the `sixth one` template:

Before:
```
unnamed_item_1
unnamed_item_2
unnamed_item_3
unnamed_item_4
unnamed_item_5
unnamed_item_6
unnamed_item_7
unnamed_item_8
```

After:
```
01_PREMIER_PROJECT
  01_FOOTAGE
02_AE_PROJECTS
03_AE_RENDERS
04_DELIVERY
05_MUSIC
06_AAFs
07_VOs
08_AUDITION_FILES
  01_AUDITION_SESSIONS
  02_AUDITION_FILES
  03_MIX_PRINTS
```

The fix correctly handles both top-level directories and nested subdirectories, preserving the proper structure defined in the template. 
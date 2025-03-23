#!/usr/bin/env python3
# Test script to verify module imports

import os
import sys

# Add the parent directory to Python path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try importing the module directly
print("Testing direct import...")
try:
    from app.ui.enhanced_structure_editor import EnhancedStructureEditor
    print("✅ Direct import successful")
except Exception as e:
    print(f"❌ Direct import failed: {e}")
    print(f"Exception type: {type(e)}")
    import traceback
    traceback.print_exc()

# Try importing through the package
print("\nTesting package import...")
try:
    from app.ui import EnhancedStructureEditor
    print("✅ Package import successful")
except Exception as e:
    print(f"❌ Package import failed: {e}")
    print(f"Exception type: {type(e)}")
    import traceback
    traceback.print_exc()

# Test if we can import and use show_enhanced_structure_editor
print("\nTesting structure_editor_functions import...")
try:
    from app.ui.structure_editor_functions import show_enhanced_structure_editor
    print("✅ structure_editor_functions import successful")
    print(f"Function signature: {show_enhanced_structure_editor.__code__.co_varnames[:show_enhanced_structure_editor.__code__.co_argcount]}")
except Exception as e:
    print(f"❌ structure_editor_functions import failed: {e}")
    print(f"Exception type: {type(e)}")
    import traceback
    traceback.print_exc()

# Print the import path for diagnostics
print("\nPython path:")
for p in sys.path:
    print(f"- {p}")

# Print module files
print("\nModule files:")
import app
print(f"app: {app.__file__}")
print(f"app.ui: {app.ui.__file__}")

# List all modules in app.ui
print("\nModules in app.ui:")
for item in dir(app.ui):
    if not item.startswith('__'):
        print(f"- {item}")

print("\nTest complete.") 
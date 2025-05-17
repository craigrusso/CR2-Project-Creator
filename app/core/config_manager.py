#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
from PyQt5.QtCore import QSettings, QStandardPaths, QCoreApplication
# Removed direct import of APP_NAME to break circular dependency
# from .app_config import APP_NAME 

# Ensure QCoreApplication attributes are set before QSettings is used heavily
# These should match what's in main.py
if not QCoreApplication.organizationName():
    QCoreApplication.setOrganizationName("CR2 Creative")
if not QCoreApplication.organizationDomain():
    QCoreApplication.setOrganizationDomain("cr2creative.com")
if not QCoreApplication.applicationName():
    # Use a generic name if main hasn't set it yet, though ideally it should be
    # set before this module is imported heavily.
    QCoreApplication.setApplicationName("Echelon")


SETTINGS_KEY_USER_DATA_ROOT = "UserDataRoot"

# Store the resolved root path in memory to avoid repeated QSettings lookups/default checks
_resolved_user_data_root = None

def get_default_data_root():
    """
    Determines the default root directory for application data based on
    platform conventions.
    """
    system = platform.system()
    app_name = QCoreApplication.applicationName() # Get app name from QCoreApplication
    if not app_name:
        # Fallback if not set, though it should be by main.py
        app_name = "Echelon_Fallback"
        print(f"WARN: QCoreApplication.applicationName() was not set. Using fallback: {app_name}")

    if system == "Darwin":  # macOS
        # ~/Library/Application Support/APP_NAME
        home_dir = os.path.expanduser("~")
        default_path = os.path.join(home_dir, "Library", "Application Support", app_name)
    elif system == "Windows":
        # %APPDATA%\APP_NAME (e.g., C:\Users\<user>\AppData\Roaming\APP_NAME)
        appdata = os.getenv('APPDATA')
        if not appdata: # Fallback if APPDATA is not set
             home_dir = os.path.expanduser("~")
             # A less standard but usable fallback
             appdata = os.path.join(home_dir, 'AppData', 'Roaming') 
        default_path = os.path.join(appdata, app_name)
    else:  # Linux and other Unix-like systems
        # Use XDG Base Directory Specification
        # Data files -> $XDG_DATA_HOME or default to ~/.local/share
        xdg_data_home = os.getenv('XDG_DATA_HOME', os.path.join(os.path.expanduser("~"), ".local", "share"))
        default_path = os.path.join(xdg_data_home, app_name)
        
    # Note: Directory creation is handled by the caller (get_user_data_root)
    return default_path

def get_user_data_root(force_reload=False):
    """
    Gets the user-defined data root path from QSettings, or the default.
    Ensures the directory exists. Caches the result in memory.

    Args:
        force_reload (bool): If True, bypass the memory cache and reload from QSettings.

    Returns:
        str: The absolute path to the user data root directory.
    """
    global _resolved_user_data_root
    if _resolved_user_data_root and not force_reload:
        # Ensure it still exists, create if not (might be deleted externally)
        os.makedirs(_resolved_user_data_root, exist_ok=True)
        return _resolved_user_data_root

    settings = QSettings()
    user_path = settings.value(SETTINGS_KEY_USER_DATA_ROOT, None)

    if user_path and isinstance(user_path, str) and os.path.isdir(os.path.dirname(user_path)):
        # Check if the *directory* containing the potential path exists and is writable
        # This avoids issues if the user selects a root drive like C:\ directly
        # We also need write permissions to create subdirs
         try:
             # Test writability by trying to create the dir itself
             os.makedirs(user_path, exist_ok=True)
             # Check if we can actually write a test file (more robust)
             test_file = os.path.join(user_path, ".writetest")
             with open(test_file, "w") as f:
                 f.write("test")
             os.remove(test_file)
             _resolved_user_data_root = user_path
             return user_path
         except Exception as e:
             default_path_for_error_msg = get_default_data_root() # Recalculate for message
             print(f"WARN: User-defined path '{user_path}' exists but is not valid or writable ({e}). Falling back to default '{default_path_for_error_msg}'.")
             # Fall through to default logic
    elif user_path:
        default_path_for_error_msg = get_default_data_root() # Recalculate for message
        print(f"WARN: User-defined path '{user_path}' is invalid or parent doesn't exist. Falling back to default '{default_path_for_error_msg}'.")
        # Fall through to default logic

    # If no valid user path, use default
    default_path = get_default_data_root()
    try:
        os.makedirs(default_path, exist_ok=True)
        _resolved_user_data_root = default_path
        return default_path
    except Exception as e:
        print(f"CRITICAL: Could not create default data directory '{default_path}': {e}")
        # Fallback to a very basic temp dir as last resort?
        # Or maybe just raise the exception? For now, return the path anyway.
        _resolved_user_data_root = default_path # Store even if creation failed
        return default_path


def set_user_data_root(path):
    """
    Sets and saves the user-defined data root path to QSettings.
    Also updates the in-memory cache.

    Args:
        path (str): The absolute path to the new user data root directory.

    Returns:
        bool: True if successful, False otherwise.
    """
    global _resolved_user_data_root
    if not path or not isinstance(path, str):
        print("ERROR: Invalid path provided to set_user_data_root.")
        return False

    # Basic validation: check if it's an absolute path and seems plausible
    if not os.path.isabs(path):
         print(f"ERROR: Path must be absolute: {path}")
         return False

    # Check if the parent directory exists and is writable
    parent_dir = os.path.dirname(path)
    if not os.path.isdir(parent_dir) or not os.access(parent_dir, os.W_OK):
        print(f"ERROR: Parent directory does not exist or is not writable: {parent_dir}")
        # Optionally, try to create the parent? Safer not to by default.
        return False

    # Try creating the directory itself to ensure writability at the target location
    try:
        os.makedirs(path, exist_ok=True)
        # Test writability by trying to create a test file
        test_file = os.path.join(path, ".writetest")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        print(f"ERROR: Cannot create or write to the specified path '{path}': {e}")
        return False

    settings = QSettings()
    settings.setValue(SETTINGS_KEY_USER_DATA_ROOT, path)
    settings.sync() # Ensure it's written immediately
    _resolved_user_data_root = path # Update cache
    # Ensure the new directory exists after setting
    os.makedirs(_resolved_user_data_root, exist_ok=True)
    return True


def get_path(subdirectory_name, ensure_exists=True):
    """
    Gets the full path for a specific subdirectory within the data root.

    Args:
        subdirectory_name (str): The name of the subdirectory (e.g., "Templates", "Cache").
        ensure_exists (bool): If True, create the directory if it doesn't exist.

    Returns:
        str: The absolute path to the subdirectory.
    """
    if not subdirectory_name or not isinstance(subdirectory_name, str):
        raise ValueError("subdirectory_name must be a non-empty string")

    base_path = get_user_data_root() # Gets user or default path
    full_path = os.path.join(base_path, subdirectory_name)

    if ensure_exists:
        try:
            # exist_ok=True prevents error if dir already exists
            os.makedirs(full_path, exist_ok=True)
        except Exception as e:
            print(f"ERROR: Could not create directory '{full_path}': {e}")
            # Decide how to handle: raise error, return None, or return path anyway?
            # Returning path allows caller to potentially handle/log
            pass # Fall through and return the path even if creation failed

    return full_path

# --- Specific Path Getters ---

def get_templates_path():
    """Returns the path to the Templates directory."""
    return get_path("Templates")

def get_cache_path():
    """Returns the path to the Cache directory."""
    return get_path("Cache") # Changed from 'template_cache' for consistency

def get_structures_path():
    """Returns the path to the Structures directory (for custom structures)."""
    # Maintain consistency with old 'structures' name if needed, or use 'CustomStructures'
    return get_path("Structures")

def get_settings_path():
    """Returns the path to the Settings directory (for JSON configs like preferences.json)."""
    # This is where non-QSettings files could live, like the cache preferences
    return get_path("Settings")

def get_template_directories_path():
    """Returns the path for storing template directory organization (folders.json)."""
    # Matches old name from get_config_paths
    return get_path("TemplateDirectories")

def get_log_path():
    """Returns the path to the Logs directory."""
    return get_path("Logs")


# Example Usage (for testing when run directly)
if __name__ == "__main__":
    # Make sure App Info is set for QSettings
    QCoreApplication.setOrganizationName("TestOrg")
    QCoreApplication.setOrganizationDomain("test.org")
    # Use the actual APP_NAME for testing consistency - Need to import it here
    # Since this block is only run when executed directly, the import is safe here.
    try:
        from app.core.app_config import APP_NAME
        QCoreApplication.setApplicationName(APP_NAME) 
    except ImportError:
        # Fallback if running standalone without full package structure
        print("WARN: Could not import APP_NAME from app_config for testing. Using default.")
        QCoreApplication.setApplicationName("EchelonTest")

    print("--- Testing Config Manager ---")
    settings = QSettings()
    print(f"QSettings path: {settings.fileName()}")

    # Clear existing setting for clean test
    print("Clearing previous user setting (if any)...")
    settings.remove(SETTINGS_KEY_USER_DATA_ROOT)
    settings.sync()
    _resolved_user_data_root = None # Clear cache

    print("\n1. Getting default root path:")
    # Temporarily override platform for testing different OS defaults
    original_system = platform.system
    try:
        print("   Testing macOS default:")
        platform.system = lambda: "Darwin"
        print(f"      -> {get_default_data_root()}")
        _resolved_user_data_root = None # Clear cache between tests
        
        print("   Testing Windows default:")
        platform.system = lambda: "Windows"
        # Mock APPDATA if needed for consistency in tests
        original_appdata = os.environ.get('APPDATA')
        # Use raw string for Windows path to avoid unicode escape errors
        os.environ['APPDATA'] = r'C:\Users\TestUser\AppData\Roaming'
        print(f"      -> {get_default_data_root()}")
        if original_appdata is None:
            del os.environ['APPDATA']
        _resolved_user_data_root = None # Clear cache

        print("   Testing Linux default:")
        platform.system = lambda: "Linux"
        print(f"      -> {get_default_data_root()}")
        _resolved_user_data_root = None # Clear cache
    finally:
        platform.system = original_system # Restore original platform function

    # Get the actual default root for the current system for the rest of the test
    print("\n   Getting actual default root for this system:")
    default_root = get_user_data_root() # This will use the *actual* system's default
    print(f"   Resolved Root: {default_root}")
    print(f"   Templates Path: {get_templates_path()}")
    print(f"   Cache Path: {get_cache_path()}")
    print(f"   Settings Path: {get_settings_path()}")

    print("\n2. Setting a new user path:")
    # Create a temporary directory for the test user path
    import tempfile
    temp_dir = tempfile.mkdtemp()
    new_user_path = os.path.join(temp_dir, "MyAppCustomData")
    print(f"   Attempting to set path to: {new_user_path}")
    success = set_user_data_root(new_user_path)
    print(f"   Set successful: {success}")

    if success:
        print("\n3. Getting path after setting user path:")
        current_root = get_user_data_root() # Should use cache now
        print(f"   Resolved Root (cached): {current_root}")
        reloaded_root = get_user_data_root(force_reload=True) # Force read from QSettings
        print(f"   Resolved Root (reloaded): {reloaded_root}")
        print(f"   Templates Path: {get_templates_path()}")
        print(f"   Cache Path: {get_cache_path()}")
        print(f"   Settings Path: {get_settings_path()}")
        if current_root != new_user_path or reloaded_root != new_user_path:
             print("   ERROR: Path mismatch after setting!")

    print("\n4. Testing invalid path setting:")
    success_invalid = set_user_data_root("/non/existent/path/for/sure")
    print(f"   Set invalid path successful: {success_invalid}")
    if not success_invalid:
        current_root_after_fail = get_user_data_root()
        print(f"   Root path after failed set: {current_root_after_fail}")
        if current_root_after_fail != new_user_path:
             print("   ERROR: Path changed after failed set!")

    # Clean up the temporary directory
    import shutil
    try:
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up temp directory: {temp_dir}")
    except Exception as e:
        print(f"\nError cleaning up temp directory {temp_dir}: {e}")

    print("\n--- Test Complete ---") 
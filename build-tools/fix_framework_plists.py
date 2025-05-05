import os
import plistlib
import sys

def find_executable_in_framework(framework_path):
    """Tries to find the executable file within a framework bundle."""
    framework_name = os.path.splitext(os.path.basename(framework_path))[0]
    # Common locations and naming conventions (e.g., QtCore.framework/Versions/5/QtCore)
    possible_paths = [
        os.path.join(framework_path, 'Versions', '5', framework_name),
        os.path.join(framework_path, 'Versions', 'A', framework_name),
        os.path.join(framework_path, framework_name) # Less common, but check root
    ]

    for loc in possible_paths:
        if os.path.exists(loc) and not os.path.isdir(loc) and os.access(loc, os.X_OK):
            # Return path relative to the framework's root directory
            executable_relative_path = os.path.relpath(loc, framework_path)
            print(f"   - Found executable: {executable_relative_path}")
            return executable_relative_path

    print(f"   - Warning: Could not automatically find executable for {framework_name} in standard locations.")
    return None # Could not find it

def fix_framework_plist(framework_path):
    """Checks and potentially adds the CFBundleExecutable key to a framework's Info.plist."""
    plist_path = None
    # Prefer Resources/Info.plist, fallback to root Info.plist
    plist_locations = [
        os.path.join(framework_path, 'Resources', 'Info.plist'),
        os.path.join(framework_path, 'Info.plist')
    ]

    for loc in plist_locations:
        if os.path.exists(loc):
            plist_path = loc
            break

    if not plist_path:
        # Frameworks without plists are usually okay (e.g., simple resource bundles)
        # print(f" - Info.plist not found in standard locations within {framework_path}. Skipping.")
        return False

    print(f" - Checking plist: {os.path.relpath(plist_path)}") # More concise path in output
    try:
        with open(plist_path, 'rb') as fp:
            try:
                # Use fmt=None to preserve existing format if possible on load
                # Though we force XML on dump for consistency
                plist_data = plistlib.load(fp)
            except plistlib.InvalidFileException:
                 print(f"   - Invalid plist file. Skipping.")
                 return False
            except Exception as e:
                 # Catch other potential load errors (e.g., permission denied)
                 print(f"   - Error loading plist: {e}. Skipping.")
                 return False

    except Exception as e:
        print(f"   - Error opening plist file {plist_path}: {e}. Skipping.")
        return False

    # Check if CFBundleExecutable is missing, empty, or points to a non-existent/non-executable file
    needs_fix = False
    existing_executable_valid = False
    if 'CFBundleExecutable' in plist_data and plist_data['CFBundleExecutable']:
        executable_path_relative = plist_data['CFBundleExecutable']
        # Construct absolute path for checking existence and permissions
        full_executable_path = os.path.normpath(os.path.join(framework_path, executable_path_relative))
        if os.path.exists(full_executable_path) and not os.path.isdir(full_executable_path) and os.access(full_executable_path, os.X_OK):
            existing_executable_valid = True
            # print(f"   - Existing CFBundleExecutable '{executable_path_relative}' seems valid.")
        else:
             print(f"   - Existing CFBundleExecutable '{executable_path_relative}' is invalid (missing/not executable).")
             needs_fix = True # Mark for fixing even if key exists but is wrong
    else:
        print(f"   - CFBundleExecutable missing or empty.")
        needs_fix = True

    if needs_fix:
        print(f"   - Attempting to find and set correct executable path.")
        executable_relative_path = find_executable_in_framework(framework_path)
        if executable_relative_path:
            # Only update if the found path is different from an existing (but invalid) one
            # Or if the key was missing entirely
            if 'CFBundleExecutable' not in plist_data or plist_data.get('CFBundleExecutable') != executable_relative_path:
                plist_data['CFBundleExecutable'] = executable_relative_path
                print(f" + Fixing {os.path.relpath(plist_path)}: Setting CFBundleExecutable={executable_relative_path}")
                try:
                    # Ensure plist is written back in standard XML format
                    with open(plist_path, 'wb') as fp:
                        plistlib.dump(plist_data, fp, fmt=plistlib.FMT_XML)
                    return True # Fixed
                except Exception as e:
                    print(f"   - Error writing fixed plist {plist_path}: {e}. Skipping fix.")
                    return False
            else:
                 print(f"   - Found executable '{executable_relative_path}', but it matches existing invalid entry? Skipping write.")
                 return False # No change needed or possible
        else:
            print(f" - Cannot fix {os.path.relpath(plist_path)}: Could not find executable for framework {os.path.basename(framework_path)}.")
            return False
    # elif not existing_executable_valid: # This case is covered by needs_fix = True above
        # print(f"   - Existing CFBundleExecutable was invalid, but couldn't find a replacement.")
        # return False
    else:
        # print(f"   = CFBundleExecutable okay in {os.path.relpath(plist_path)}.")
        return False # Already okay


def main(app_bundle_path):
    # Prioritize the Qt Frameworks path based on previous errors
    frameworks_dirs_to_check = [
        os.path.join(app_bundle_path, 'Contents', 'Resources', 'lib', 'python3.12', 'PyQt5', 'Qt5', 'lib'),
        os.path.join(app_bundle_path, 'Contents', 'Frameworks') # Standard location
    ]

    frameworks_dir = None
    for d in frameworks_dirs_to_check:
        if os.path.isdir(d):
            frameworks_dir = d
            print(f"Found frameworks directory: {frameworks_dir}")
            break

    if not frameworks_dir:
        print(f"Error: Could not find frameworks directory in standard locations:")
        for d in frameworks_dirs_to_check:
             print(f"  - {d}")
        sys.exit(1)


    print(f"Scanning for frameworks in: {frameworks_dir}")
    fixed_count = 0
    total_frameworks = 0
    processed_count = 0 # Count only those we attempt to process (have Info.plist)

    items = sorted(os.listdir(frameworks_dir)) # Sort for consistent order

    for item in items:
        item_path = os.path.join(frameworks_dir, item)
        if item.endswith('.framework') and os.path.isdir(item_path):
            total_frameworks += 1
            if fix_framework_plist(item_path):
                fixed_count += 1


    print(f"Finished fixing framework plists. Checked {total_frameworks} frameworks, fixed {fixed_count}.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fix_framework_plists.py <path_to_app_bundle>")
        sys.exit(1)

    app_path = sys.argv[1]
    if not app_path.endswith('.app'):
        print(f"Error: Provided path '{app_path}' does not end with .app")
        sys.exit(1)
    if not os.path.isdir(app_path):
        print(f"Error: Provided path '{app_path}' is not a valid directory.")
        sys.exit(1)

    main(app_path) 
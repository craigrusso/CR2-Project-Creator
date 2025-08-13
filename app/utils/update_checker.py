# app/utils/update_checker.py
import requests
import platform
import json
from packaging.version import parse
import re # Added for natural sort

# Map platform.system() output to expected API platform strings
PLATFORM_MAP = {
    "Darwin": "macos",
    "Windows": "windows",
    "Linux": "linux" 
}

def natural_sort_key(s):
    """
    Create a key for natural sorting (handles numbers in strings).
    None or empty strings are treated as lowest.
    """
    if s is None:
        return [] # Will compare lower than any list with content
    s_str = str(s).strip()
    if not s_str:
        return []
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s_str)]

def _as_bool(value):
    """Coerce common truthy values to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    if isinstance(value, (int, float)):
        return value == 1
    return False


def get_latest_version_info(api_url):
    """
    Fetches version info from the public API and returns the latest 
    available version dictionary for the current platform, considering
    versionNumber and then buildNumber.
    
    Args:
        api_url (str): The URL of the public downloads API endpoint.
        
    Returns:
        dict or None: The latest version_info dictionary if an update is found,
                     or None if no update is available, no matching platform 
                     is found, or an error occurs.
    """
    current_platform_system = platform.system()
    target_platform_api = PLATFORM_MAP.get(current_platform_system)

    if not target_platform_api:
        print(f"ERROR: Update check - Unsupported platform: {current_platform_system}")
        return None

    # print(f"DEBUG: Checking for updates at {api_url} for platform '{target_platform_api}'")

    try:
        response = requests.get(api_url, timeout=10) # 10 second timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        versions_data = response.json()
        
        if not isinstance(versions_data, list):
            print("ERROR: Update check - Invalid API response format (expected a list).")
            return None
            
        latest_version_obj = None
        highest_parsed_v_num = parse("0.0.0") # Initialize with a very old version

        for version_info in versions_data:
            # Check required fields are present (versionNumber, platform, isAvailable are key)
            # buildNumber and releaseStage are also expected as per new requirements.
            if not all(k in version_info for k in ('platform', 'versionNumber', 'isAvailable')):
                # print(f"WARN: Skipping invalid version entry (missing core fields): {version_info}")
                continue
                
            api_platform = version_info.get('platform')
            is_available = _as_bool(version_info.get('isAvailable'))
            if not (api_platform and api_platform.lower() == target_platform_api and is_available):
                continue

            current_entry_v_num_str = version_info.get('versionNumber')
            if not current_entry_v_num_str:
                # print(f"WARN: Skipping entry with missing versionNumber: {version_info}")
                continue
            
            try:
                current_entry_parsed_v_num = parse(current_entry_v_num_str)
                current_entry_build_num = version_info.get('buildNumber') # Can be None, str, or number if JSON has it

                if latest_version_obj is None or current_entry_parsed_v_num > highest_parsed_v_num:
                    highest_parsed_v_num = current_entry_parsed_v_num
                    latest_version_obj = version_info
                elif current_entry_parsed_v_num == highest_parsed_v_num:
                    # Semantic versions are identical, compare buildNumber
                    latest_obj_build_num = latest_version_obj.get('buildNumber')
                    
                    current_build_key = natural_sort_key(current_entry_build_num)
                    latest_obj_build_key = natural_sort_key(latest_obj_build_num)

                    if current_build_key > latest_obj_build_key:
                        latest_version_obj = version_info
                        # highest_parsed_v_num remains the same

            except Exception as e:
                 # print(f"WARN: Could not parse/compare version or build for entry '{version_info.get('versionNumber')}': {e}")
                 pass # Skip this entry if parsing/comparison fails

        if latest_version_obj:
            # print(f"DEBUG: Latest version selected for {target_platform_api}: {latest_version_obj.get('versionNumber')} Build: {latest_version_obj.get('buildNumber')}")
            return latest_version_obj
        else:
            # print(f"DEBUG: No suitable newer versions found for platform {target_platform_api}.")
            return None

    except requests.exceptions.Timeout:
        print("ERROR: Update check - Request timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Update check - Network request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Update check - Failed to parse JSON response: {e}")
        return None
    except Exception as e:
        # Catch any other unexpected errors
        print(f"ERROR: Update check - An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return None 
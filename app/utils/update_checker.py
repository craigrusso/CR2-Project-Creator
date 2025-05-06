# app/utils/update_checker.py
import requests
import platform
import json
from packaging.version import parse

# Map platform.system() output to expected API platform strings
PLATFORM_MAP = {
    "Darwin": "macos",
    "Windows": "windows",
    "Linux": "linux" 
}

def get_latest_version_info(api_url):
    """
    Fetches version info from the public API and returns the latest 
    available version string for the current platform.
    
    Args:
        api_url (str): The URL of the public downloads API endpoint.
        
    Returns:
        str or None: The latest version string (e.g., "1.0.1") if found and newer,
                     or None if no update is available, no matching platform 
                     is found, or an error occurs.
    """
    current_platform_system = platform.system()
    target_platform_api = PLATFORM_MAP.get(current_platform_system)

    if not target_platform_api:
        print(f"ERROR: Update check - Unsupported platform: {current_platform_system}")
        return None

    print(f"DEBUG: Checking for updates at {api_url} for platform '{target_platform_api}'")

    try:
        response = requests.get(api_url, timeout=10) # 10 second timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        versions_data = response.json()
        
        if not isinstance(versions_data, list):
            print("ERROR: Update check - Invalid API response format (expected a list).")
            return None
            
        latest_version = None
        latest_version_str = "0.0.0" # Start comparison from 0

        for version_info in versions_data:
            # Check required fields are present
            if not all(k in version_info for k in ('platform', 'versionNumber', 'isAvailable')):
                print(f"WARN: Skipping invalid version entry: {version_info}")
                continue
                
            # Check platform match and availability
            if version_info.get('platform') == target_platform_api and version_info.get('isAvailable') is True:
                current_entry_version_str = version_info.get('versionNumber')
                if not current_entry_version_str:
                    print(f"WARN: Skipping entry with missing versionNumber: {version_info}")
                    continue
                    
                try:
                    # Compare versions using packaging.version
                    if parse(current_entry_version_str) > parse(latest_version_str):
                        latest_version_str = current_entry_version_str
                        latest_version = version_info # Store the whole dict
                except Exception as e:
                     print(f"WARN: Could not parse version '{current_entry_version_str}': {e}")

        if latest_version:
            print(f"DEBUG: Latest available version found for {target_platform_api}: {latest_version_str}")
            # Return only the version string
            return latest_version_str 
        else:
            print(f"DEBUG: No available versions found for platform {target_platform_api}.")
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
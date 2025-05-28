#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Cache Preferences Manager
Manages preferences for the file caching system
"""

import os
import json

class CachePreferences:
    """
    Manages preferences for the file caching system.
    
    Preferences include settings like:
    - Whether to cache files
    - Maximum cache size
    - Maximum cache age
    - Location of cache
    """
    
    DEFAULT_PREFERENCES = {
        "enable_file_caching": True,
        "max_cache_size_mb": 1000,  # 1GB
        "max_cache_age_days": 30,   # 1 month
        "auto_clean_cache": True,
        "cache_check_frequency_days": 7  # Check cache weekly
    }
    
    def __init__(self, preferences_path=None):
        """
        Initialize the cache preferences
        
        Args:
            preferences_path: Path to the preferences file. If None, use default location
        """
        if preferences_path is None:
            # Store preferences file inside the centralized settings directory
            try:
                # Import late to avoid circular dependencies if config_manager imports this
                from app.core.config_manager import get_settings_path
                settings_dir = get_settings_path() 
                self.preferences_path = os.path.join(settings_dir, "cache_preferences.json")
            except ImportError as e:
                print(f"CRITICAL ERROR: Could not import config_manager to determine settings path: {e}")
                # Fallback to old location as a last resort? Or raise error?
                # Using a fallback might hide the underlying issue. Let's log and maybe use a temp name
                home_dir = os.path.expanduser("~")
                self.preferences_path = os.path.join(home_dir, ".echelon", "cache_preferences.json.error_fallback")
                print(f"WARNING: Using fallback preferences path: {self.preferences_path}")
        else:
            self.preferences_path = preferences_path
            
        # Ensure directory exists (get_settings_path in config_manager should already do this)
        # os.makedirs(os.path.dirname(self.preferences_path), exist_ok=True) # Likely redundant now
        
        # Load preferences
        self.preferences = self.load_preferences()
        
    def load_preferences(self):
        """
        Load preferences from file
        
        Returns:
            dict: Preferences dictionary
        """
        if os.path.exists(self.preferences_path):
            try:
                with open(self.preferences_path, 'r') as f:
                    preferences = json.load(f)
                    
                # Merge with defaults to ensure all keys exist
                # Also remove obsolete keys like cache_location if found
                final_preferences = {}
                for key, value in self.DEFAULT_PREFERENCES.items():
                    final_preferences[key] = preferences.get(key, value) # Use default if missing in file
                    
                # Optional: Clean up keys present in file but not in defaults
                # obsolete_keys = [k for k in preferences if k not in self.DEFAULT_PREFERENCES]
                # if obsolete_keys:
                #    print(f"DEBUG: Removing obsolete keys from loaded preferences: {obsolete_keys}")
                        
                return final_preferences
            except Exception as e:
                print(f"Error loading cache preferences from {self.preferences_path}: {e}")
                # Fallback to defaults, ensure cache_location is NOT included
                return {k: v for k, v in self.DEFAULT_PREFERENCES.items()}
        else:
            # If no preferences file exists, return defaults (without cache_location)
             return {k: v for k, v in self.DEFAULT_PREFERENCES.items()}
    
    def save_preferences(self):
        """
        Save preferences to file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure directory exists before writing
            pref_dir = os.path.dirname(self.preferences_path)
            os.makedirs(pref_dir, exist_ok=True)
            with open(self.preferences_path, 'w') as f:
                json.dump(self.preferences, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving cache preferences: {e}")
            return False
    
    def get_preference(self, key, default=None):
        """
        Get a preference value
        
        Args:
            key: Preference key
            default: Default value if key doesn't exist
            
        Returns:
            Value of the preference
        """
        return self.preferences.get(key, default)
    
    def set_preference(self, key, value):
        """
        Set a preference value
        
        Args:
            key: Preference key
            value: New value
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.preferences[key] = value
        return self.save_preferences()
    
    def reset_to_defaults(self):
        """
        Reset preferences to default values
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Ensure cache_location is not part of the reset defaults
        self.preferences = {k: v for k, v in self.DEFAULT_PREFERENCES.items()}
        return self.save_preferences()
    
    def should_cache_files(self):
        """
        Check if file caching is enabled
        
        Returns:
            bool: True if caching is enabled, False otherwise
        """
        return self.get_preference("enable_file_caching", True)
    
    def should_clean_cache(self):
        """
        Check if automatic cache cleaning is enabled
        
        Returns:
            bool: True if automatic cleaning is enabled, False otherwise
        """
        return self.get_preference("auto_clean_cache", True)
    
    def get_clean_parameters(self):
        """
        Get parameters for cache cleaning
        
        Returns:
            tuple: (max_age_days, max_size_mb)
        """
        max_age = self.get_preference("max_cache_age_days", 30)
        max_size = self.get_preference("max_cache_size_mb", 1000)
        
        return max_age, max_size 
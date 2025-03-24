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
        "cache_location": "",       # Empty = use default
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
            # Use default location in user's home directory
            home_dir = os.path.expanduser("~")
            self.preferences_path = os.path.join(home_dir, ".echelon", "cache_preferences.json")
        else:
            self.preferences_path = preferences_path
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.preferences_path), exist_ok=True)
        
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
                for key, value in self.DEFAULT_PREFERENCES.items():
                    if key not in preferences:
                        preferences[key] = value
                        
                return preferences
            except Exception as e:
                print(f"Error loading cache preferences: {e}")
                return self.DEFAULT_PREFERENCES.copy()
        else:
            # If no preferences file exists, return defaults
            return self.DEFAULT_PREFERENCES.copy()
    
    def save_preferences(self):
        """
        Save preferences to file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
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
        self.preferences = self.DEFAULT_PREFERENCES.copy()
        return self.save_preferences()
    
    def get_cache_location(self):
        """
        Get the cache location
        
        Returns:
            str: Path to the cache directory
        """
        # Use specified location or default
        location = self.get_preference("cache_location", "")
        
        if not location:
            # Use default location
            home_dir = os.path.expanduser("~")
            location = os.path.join(home_dir, ".echelon", "template_cache")
            
        return location
    
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
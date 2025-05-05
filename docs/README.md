# Template File Caching System

This module provides a robust file caching system for template files, ensuring that template files remain accessible even if the original source is removed or changed.

## Features

- Caches template files in a central location
- Maintains metadata about cached files including original paths
- Provides statistics about cache usage
- Configurable cache settings (size limits, age limits, etc.)
- Automatic cache pruning to remove old or unused files
- Supports binary and text files
- Handles nested directory structures

## Components

### FileCacheManager

The `FileCacheManager` class provides the core functionality for caching files:

- Caching files with their original paths
- Retrieving cached files
- Managing cache metadata
- Providing cache statistics
- Pruning the cache based on age and size

### CachePreferences

The `CachePreferences` class manages user preferences for the caching system:

- Enable/disable caching
- Maximum cache size
- Maximum cache age
- Cache location
- Automatic cache cleaning

## Integration

The file caching system is integrated with:

1. **Structure Editor** - When adding files to the template structure, the original file paths are stored and files are cached
2. **Structure Converter** - When exporting the structure to JSON, file paths are included
3. **Project Builder** - When creating a project, actual files are copied from the cache instead of creating empty files

## Testing

Use the `test_file_caching.py` script to test the file caching functionality:

```bash
python test_file_caching.py
```

The test script provides a GUI for testing various aspects of the file caching system:

- Creating test files
- Caching files
- Viewing cache statistics
- Creating a project from cached files
- Cleaning up test files

## Usage Example

```python
from app.utils.file_cache_manager import FileCacheManager
from app.utils.cache_preferences import CachePreferences

# Check if caching is enabled
prefs = CachePreferences()
if prefs.should_cache_files():
    # Get cache location
    cache_location = prefs.get_cache_location()
    
    # Create cache manager
    cache_manager = FileCacheManager(cache_location)
    
    # Cache a file
    result = cache_manager.cache_file(
        file_path="/path/to/file.txt",
        template_name="MyTemplate",
        relative_path="folder"
    )
    
    # Get cached file path
    cached_file = cache_manager.get_cached_file(
        template_name="MyTemplate",
        original_path="/path/to/file.txt"
    )
    
    # Use cached file path
    if cached_file:
        print(f"Cached file: {cached_file['cache_path']}")
``` 
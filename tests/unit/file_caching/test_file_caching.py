#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import shutil
import pytest
import json
import time
from pathlib import Path

class MockFileCacheManager:
    """Mock version of FileCacheManager for testing"""
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
    def cache_file(self, file_path, template_name, folder_path='', rename_flag=False):
        """Cache a file and return cache info"""
        if not os.path.exists(file_path):
            return None
            
        # Create cache directory for this template
        template_cache_dir = os.path.join(self.cache_dir, template_name)
        template_files_dir = os.path.join(template_cache_dir, 'files')
        os.makedirs(template_files_dir, exist_ok=True)
        
        # Get filename and determine destination path
        file_name = os.path.basename(file_path)
        folder_cache_path = template_files_dir
        if folder_path:
            folder_cache_path = os.path.join(template_files_dir, folder_path)
            os.makedirs(folder_cache_path, exist_ok=True)
            
        # Destination path in cache
        cache_path = os.path.join(folder_cache_path, file_name)
        
        # Copy file to cache location
        try:
            shutil.copy2(file_path, cache_path)
            return {
                'cached_path': cache_path,
                'file_hash': 'test_hash',
                'original_path': file_path,
                'file_type': 'text',
                'file_size': os.path.getsize(file_path),
                'is_binary': False,
                'folder_path': folder_path,
                'file_name': file_name,
                'extension': os.path.splitext(file_name)[1],
                'rename_flag': rename_flag,
                'cache_time': time.time()
            }
        except Exception as e:
            print(f"Error caching file: {e}")
            return None
            
    def get_file_path_with_fallback(self, file_info):
        """Get the best available path for a file"""
        original_path = file_info.get('original_path')
        if original_path and os.path.exists(original_path):
            return original_path
            
        cached_path = file_info.get('cached_path')
        if cached_path and os.path.exists(cached_path):
            return cached_path
            
        return None

class MockTemplateOperations:
    """Mock version of TemplateOperations for testing"""
    def __init__(self, cache_dir):
        self.paths = {
            'templates_cache_dir': cache_dir
        }
        self.file_cache_manager = MockFileCacheManager(cache_dir)
        
    def process_template_files(self, template_name, files, cache_files=True):
        """Process and cache template files"""
        if not files:
            return []
            
        processed_files = []
        for file_info in files:
            if not isinstance(file_info, dict):
                continue
                
            file_name = file_info.get('file_name', '')
            file_path = file_info.get('original_path', '')
            
            if not file_name or not file_path:
                continue
                
            if cache_files and os.path.exists(file_path):
                try:
                    rel_path = file_info.get('folder', '') + file_name
                    cache_info = self.file_cache_manager.cache_file(
                        file_path,
                        template_name,
                        rel_path,
                        file_info.get('rename_flag', False)
                    )
                    
                    if cache_info:
                        file_info.update(cache_info)
                except Exception as e:
                    print(f"Error processing file {file_name}: {e}")
                    
            processed_files.append(file_info)
            
        return processed_files
        
    def get_file_path(self, file_info):
        """Get the best available path for a file"""
        return self.file_cache_manager.get_file_path_with_fallback(file_info)

def test_file_caching(temp_dir, test_file):
    """Test that files are properly cached"""
    # Set up cache directory
    cache_dir = temp_dir / 'cache'
    template_dir = temp_dir / 'templates'
    os.makedirs(cache_dir)
    os.makedirs(template_dir)
    
    # Initialize template operations
    template_ops = MockTemplateOperations(str(cache_dir))
    
    # Create a test template with a file
    template_name = 'test_template'
    file_info = {
        'file_name': test_file.name,
        'original_path': str(test_file),
        'folder': ''
    }
    
    # Process the file
    processed_files = template_ops.process_template_files(
        template_name, [file_info], cache_files=True
    )
    
    # Verify file was cached
    assert len(processed_files) == 1
    processed_file = processed_files[0]
    assert 'cached_path' in processed_file
    assert os.path.exists(processed_file['cached_path'])
    
    # Verify content matches
    with open(processed_file['cached_path'], 'r') as f:
        cached_content = f.read()
    assert cached_content == "Test content"
    
def test_fallback_to_cache(temp_dir, test_file):
    """Test that system falls back to cached file when original is unavailable"""
    # Set up cache directory
    cache_dir = temp_dir / 'cache'
    template_dir = temp_dir / 'templates'
    os.makedirs(cache_dir)
    os.makedirs(template_dir)
    
    # Initialize template operations
    template_ops = MockTemplateOperations(str(cache_dir))
    
    # First cache the file
    template_name = 'test_template'
    file_info = {
        'file_name': test_file.name,
        'original_path': str(test_file),
        'folder': ''
    }
    
    processed_files = template_ops.process_template_files(
        template_name, [file_info], cache_files=True
    )
    
    # Store the cached path
    cached_path = processed_files[0]['cached_path']
    
    # Delete the original file
    os.remove(test_file)
    
    # Try to get the file path
    file_path = template_ops.get_file_path(processed_files[0])
    
    # Verify we got the cached path
    assert file_path == cached_path
    
    # Verify the content is still accessible
    with open(file_path, 'r') as f:
        content = f.read()
    assert content == "Test content"
    
def test_cache_updates(temp_dir, test_file):
    """Test that cache is updated when original file changes"""
    # Set up cache directory
    cache_dir = temp_dir / 'cache'
    template_dir = temp_dir / 'templates'
    os.makedirs(cache_dir)
    os.makedirs(template_dir)
    
    # Initialize template operations
    template_ops = MockTemplateOperations(str(cache_dir))
    
    # First cache the file
    template_name = 'test_template'
    file_info = {
        'file_name': test_file.name,
        'original_path': str(test_file),
        'folder': ''
    }
    
    processed_files = template_ops.process_template_files(
        template_name, [file_info], cache_files=True
    )
    
    # Modify the original file
    test_file.write_text("Updated content")
    
    # Process the file again
    updated_files = template_ops.process_template_files(
        template_name, [processed_files[0]], cache_files=True
    )
    
    # Verify the cache was updated
    with open(updated_files[0]['cached_path'], 'r') as f:
        cached_content = f.read()
    assert cached_content == "Updated content" 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
import tempfile
import unittest
import platform
from unittest.mock import patch, MagicMock

# Skip tests on non-macOS platforms
IS_MACOS = platform.system() == "Darwin"

# Skip import errors if macOS-specific modules are not available
if IS_MACOS:
    try:
        # We need to use objc directly for this functionality
        import objc
        from Foundation import NSURL, NSData, NSError
        OBJC_AVAILABLE = True
    except ImportError:
        OBJC_AVAILABLE = False
else:
    OBJC_AVAILABLE = False


class TestSecurityBookmarks(unittest.TestCase):
    """Test the security-scoped bookmarks functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        # Create a temporary directory for testing
        cls.temp_dir = tempfile.mkdtemp()
        print(f"Created temporary directory for testing: {cls.temp_dir}")

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment after all tests"""
        # Remove the temporary directory
        import shutil
        shutil.rmtree(cls.temp_dir)
        print(f"Removed temporary directory: {cls.temp_dir}")

    def setUp(self):
        """Set up test environment before each test"""
        # Create bookmark storage file in temp directory
        self.storage_file = os.path.join(self.temp_dir, "test_bookmarks.json")

    def tearDown(self):
        """Clean up test environment after each test"""
        # Delete the bookmark storage file if it exists
        if os.path.exists(self.storage_file):
            os.unlink(self.storage_file)

    @unittest.skipIf(not IS_MACOS or not OBJC_AVAILABLE, "Test requires macOS with objc/Foundation modules")
    def test_create_and_access_bookmark(self):
        """Test creating and accessing a security-scoped bookmark"""
        from app.utils.security_bookmarks import BookmarkManager

        # Create a mock NSURL for testing
        mock_url = MagicMock()
        mock_data = MagicMock()
        mock_data.bytes.return_value.tobytes.return_value = b'test_bookmark_data'
        mock_url.bookmarkDataWithOptions_includingResourceValuesForKeys_relativeToURL_error_.return_value = (mock_data, None)
        mock_url.startAccessingSecurityScopedResource.return_value = True

        # Create a mock for NSURL.fileURLWithPath_
        with patch('app.utils.security_bookmarks.NSURL') as mock_nsurl:
            mock_nsurl.fileURLWithPath_.return_value = mock_url
            
            # Create a mock for NSData
            with patch('app.utils.security_bookmarks.NSData') as mock_nsdata:
                mock_nsdata.dataWithBytes_length_.return_value = mock_data
                
                # Create a mock for URL resolution
                mock_nsurl.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_.return_value = (mock_url, False, None)
                
                # Create a bookmark manager with our test storage file
                manager = BookmarkManager(storage_path=os.path.dirname(self.storage_file))
                manager.bookmark_file = self.storage_file
                
                # Test creating a bookmark
                test_path = "/test/path"
                result = manager.create_bookmark(test_path)
                self.assertTrue(result)
                self.assertTrue(manager.has_bookmark(test_path))
                
                # Test accessing the bookmark
                result = manager.access_bookmark(test_path)
                self.assertTrue(result)
                
                # Test stopping access
                result = manager.stop_accessing_bookmark(test_path)
                self.assertTrue(result)
                
                # Test removing the bookmark
                result = manager.remove_bookmark(test_path)
                self.assertTrue(result)
                self.assertFalse(manager.has_bookmark(test_path))

    def test_non_macos_stubs(self):
        """Test the stub implementations on non-macOS platforms"""
        # Force non-macOS behavior
        with patch('app.utils.security_bookmarks.IS_MACOS', False):
            from app.utils.security_bookmarks import BookmarkManager
            
            # Create a bookmark manager with our test storage file
            manager = BookmarkManager(storage_path=os.path.dirname(self.storage_file))
            manager.bookmark_file = self.storage_file
            
            # Test creating a bookmark
            test_path = "/test/path"
            result = manager.create_bookmark(test_path)
            self.assertTrue(result)  # Should succeed even though it's a stub
            
            # Test accessing the bookmark
            result = manager.access_bookmark(test_path)
            self.assertTrue(result)  # Should succeed even though it's a stub
            
            # Test stopping access
            result = manager.stop_accessing_bookmark(test_path)
            self.assertTrue(result)  # Should succeed even though it's a stub
            
            # Test removing the bookmark
            result = manager.remove_bookmark(test_path)
            self.assertTrue(result)  # Should succeed even though it's a stub

    def test_context_manager(self):
        """Test the context manager for bookmark access"""
        # Force non-macOS behavior for testing
        with patch('app.utils.security_bookmarks.IS_MACOS', False):
            from app.utils.security_bookmarks import BookmarkAccessContext
            
            # Test context manager with mocked manager
            mock_manager = MagicMock()
            mock_manager.access_bookmark.return_value = True
            mock_manager.stop_accessing_bookmark.return_value = True
            
            with patch('app.utils.security_bookmarks.get_bookmark_manager', return_value=mock_manager):
                test_path = "/test/path"
                
                # Use the context manager
                with BookmarkAccessContext(test_path) as ctx:
                    self.assertTrue(ctx.accessed)
                
                # Verify methods were called
                mock_manager.access_bookmark.assert_called_once_with(test_path)
                mock_manager.stop_accessing_bookmark.assert_called_once_with(test_path)

    def test_helper_functions(self):
        """Test the helper functions for bookmark management"""
        # Force non-macOS behavior for testing
        with patch('app.utils.security_bookmarks.IS_MACOS', False):
            from app.utils.security_bookmarks import (
                create_bookmark, access_bookmark, 
                stop_accessing_bookmark, with_bookmark_access
            )
            
            # Mock the BookmarkManager
            mock_manager = MagicMock()
            mock_manager.create_bookmark.return_value = True
            mock_manager.access_bookmark.return_value = True
            mock_manager.stop_accessing_bookmark.return_value = True
            
            with patch('app.utils.security_bookmarks.get_bookmark_manager', return_value=mock_manager):
                test_path = "/test/path"
                
                # Test create_bookmark
                result = create_bookmark(test_path)
                self.assertTrue(result)
                mock_manager.create_bookmark.assert_called_once_with(test_path)
                
                # Test access_bookmark
                result = access_bookmark(test_path)
                self.assertTrue(result)
                mock_manager.access_bookmark.assert_called_once_with(test_path)
                
                # Test stop_accessing_bookmark
                result = stop_accessing_bookmark(test_path)
                self.assertTrue(result)
                mock_manager.stop_accessing_bookmark.assert_called_once_with(test_path)
                
                # Test with_bookmark_access decorator
                mock_manager.reset_mock()
                
                @with_bookmark_access(test_path)
                def test_func():
                    return True
                
                # Call the decorated function
                result = test_func()
                self.assertTrue(result)
                
                # Decorator should have used the context manager
                mock_manager.access_bookmark.assert_called_once_with(test_path)
                mock_manager.stop_accessing_bookmark.assert_called_once_with(test_path)


if __name__ == "__main__":
    unittest.main() 
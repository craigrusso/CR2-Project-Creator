#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
import tempfile
import unittest
import platform
import shutil
from unittest.mock import patch, MagicMock

# Skip tests on non-macOS platforms for detailed integration tests
IS_MACOS = platform.system() == "Darwin"

class TestSecurityBookmarksIntegration(unittest.TestCase):
    """Test the integration of security-scoped bookmarks with ProjectBuilder"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        # Create a temporary directory for testing
        cls.temp_dir = tempfile.mkdtemp()
        print(f"Created temporary directory for testing: {cls.temp_dir}")
        
        # Create output directory
        cls.output_dir = os.path.join(cls.temp_dir, "output")
        os.makedirs(cls.output_dir, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment after all tests"""
        # Remove the temporary directory
        shutil.rmtree(cls.temp_dir)
        print(f"Removed temporary directory: {cls.temp_dir}")

    def test_project_creation_with_bookmarks(self):
        """Test creating a project with security-scoped bookmarks"""
        from app.core.project_builder import ProjectBuilder
        from app.templates.template_manager import TemplateManager
        
        # Create a project builder
        template_manager = TemplateManager()
        project_builder = ProjectBuilder(template_manager)
        
        # Create a simple project - this should use security-scoped bookmarks on macOS
        project_name = "TestProject"
        
        # Mock the BookmarkAccessContext to simulate macOS behavior regardless of platform
        with patch('platform.system', return_value="Darwin"):
            if IS_MACOS:
                # On macOS, we'll check for real Foundation imports and potentially skip
                try:
                    import objc
                    from Foundation import NSURL, NSData, NSError
                    # If we got here, we have real Foundation support
                except ImportError:
                    # Skip test if we can't import real Foundation on macOS
                    print("Skipping real macOS test due to missing Foundation modules")
                    return
                
                # Use the real behavior on macOS
                success, result = project_builder.create_project(
                    project_name=project_name,
                    output_dir=self.output_dir,
                    project_type="Test"
                )
                self.assertTrue(success)
                self.assertTrue(os.path.exists(os.path.join(self.output_dir, project_name)))
            else:
                # On non-macOS, mock everything
                mock_context = MagicMock()
                mock_context.__enter__ = MagicMock(return_value=None)
                mock_context.__exit__ = MagicMock(return_value=None)
                
                # Mock the BookmarkAccessContext constructor
                with patch('app.utils.security_bookmarks.BookmarkAccessContext', return_value=mock_context):
                    # Mock the Foundation imports
                    with patch.dict('sys.modules', {'Foundation': MagicMock(), 'objc': MagicMock()}):
                        # Patch IS_MACOS in the security_bookmarks module
                        with patch('app.utils.security_bookmarks.IS_MACOS', True):
                            success, result = project_builder.create_project(
                                project_name=project_name,
                                output_dir=self.output_dir,
                                project_type="Test"
                            )
                            self.assertTrue(success)
                            self.assertTrue(os.path.exists(os.path.join(self.output_dir, project_name)))
                            
                            # Verify that BookmarkAccessContext was used
                            from app.utils.security_bookmarks import BookmarkAccessContext
                            BookmarkAccessContext.assert_called_once_with(self.output_dir)

    def test_batch_project_creation_with_bookmarks(self):
        """Test batch creating projects with security-scoped bookmarks"""
        from app.core.project_builder import ProjectBuilder
        from app.templates.template_manager import TemplateManager
        
        # Create a project builder
        template_manager = TemplateManager()
        project_builder = ProjectBuilder(template_manager)
        
        # Create a list of project names
        project_names = ["TestProject1", "TestProject2", "TestProject3"]
        
        # Mock the BookmarkAccessContext to simulate macOS behavior
        with patch('platform.system', return_value="Darwin"):
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=None)
            mock_context.__exit__ = MagicMock(return_value=None)
            
            # Mock the BookmarkAccessContext constructor
            with patch('app.utils.security_bookmarks.BookmarkAccessContext', return_value=mock_context):
                # Patch IS_MACOS in the security_bookmarks module
                with patch('app.utils.security_bookmarks.IS_MACOS', True):
                    # Create batch projects
                    results = project_builder.batch_create_projects(
                        project_names=project_names,
                        output_dir=self.output_dir
                    )
                    
                    # Verify results
                    self.assertEqual(results["successful_count"], len(project_names))
                    self.assertEqual(results["total_count"], len(project_names))
                    
                    # Verify all projects were created
                    for project_name in project_names:
                        self.assertTrue(os.path.exists(os.path.join(self.output_dir, project_name)))

    def test_fallback_behavior(self):
        """Test fallback behavior when security-scoped bookmarks fail"""
        from app.core.project_builder import ProjectBuilder
        from app.templates.template_manager import TemplateManager
        
        # Create a project builder
        template_manager = TemplateManager()
        project_builder = ProjectBuilder(template_manager)
        
        # Create a project name
        project_name = "FallbackProject"
        
        # Mock the BookmarkAccessContext to simulate macOS behavior that fails
        with patch('platform.system', return_value="Darwin"):
            # Create a mock context that raises an exception when entered
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(side_effect=Exception("Simulated bookmark access failure"))
            mock_context.__exit__ = MagicMock(return_value=None)
            
            # Mock the BookmarkAccessContext constructor
            with patch('app.utils.security_bookmarks.BookmarkAccessContext', return_value=mock_context):
                # Patch IS_MACOS in the security_bookmarks module
                with patch('app.utils.security_bookmarks.IS_MACOS', True):
                    # Create a project - should fall back to standard behavior
                    success, result = project_builder.create_project(
                        project_name=project_name,
                        output_dir=self.output_dir,
                        project_type="Test"
                    )
                    
                    # Verify the project was still created despite the bookmark failure
                    self.assertTrue(success)
                    self.assertTrue(os.path.exists(os.path.join(self.output_dir, project_name)))


if __name__ == "__main__":
    unittest.main() 
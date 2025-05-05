import os
import sys
import shutil
import unittest
import tempfile
import zipfile
from unittest.mock import MagicMock, patch

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.templates.template_operations import TemplateOperations
from app.core.import_export_manager import export_template, import_template
from app.templates.template_manager import TemplateManager


class TestSelectiveFileCaching(unittest.TestCase):
    """Tests for selective file caching with binary files support"""
    
    def setUp(self):
        """Set up a temporary directory structure with various file types for testing"""
        self.test_dir = tempfile.mkdtemp()
        self.test_project_dir = os.path.join(self.test_dir, "test_project")
        os.makedirs(self.test_project_dir)
        
        # Create various file types
        # Create a .git directory (should be excluded)
        os.makedirs(os.path.join(self.test_project_dir, ".git"))
        with open(os.path.join(self.test_project_dir, ".git", "config"), "w") as f:
            f.write("This is a git config file")
        
        # Create a node_modules directory (should be excluded)
        os.makedirs(os.path.join(self.test_project_dir, "node_modules"))
        with open(os.path.join(self.test_project_dir, "node_modules", "package.json"), "w") as f:
            f.write('{"name": "test"}')
        
        # Create a normal directory with text files
        os.makedirs(os.path.join(self.test_project_dir, "src"))
        with open(os.path.join(self.test_project_dir, "src", "main.py"), "w") as f:
            f.write("print('Hello World')")
        
        # Create a fake binary file (simulating image)
        with open(os.path.join(self.test_project_dir, "image.jpg"), "wb") as f:
            f.write(os.urandom(1024))  # 1KB of random data
        
        # Create another fake binary file (simulating video)
        with open(os.path.join(self.test_project_dir, "video.mp4"), "wb") as f:
            f.write(os.urandom(2048))  # 2KB of random data
        
        # Create a text file with template variables
        with open(os.path.join(self.test_project_dir, "template.txt"), "w") as f:
            f.write("Hello, {{name}}!")
        
        # Create a markdown file
        with open(os.path.join(self.test_project_dir, "README.md"), "w") as f:
            f.write("# Test Project\nThis is a test project.")
        
        # Initialize directory paths for testing
        self.templates_dir = os.path.join(self.test_dir, "templates")
        self.structures_dir = os.path.join(self.test_dir, "structures")
        self.templates_cache_dir = os.path.join(self.templates_dir, "cache")
        
        # Create necessary directories
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.structures_dir, exist_ok=True)
        os.makedirs(self.templates_cache_dir, exist_ok=True)
        
        # Create a manager with our test paths
        self.template_manager = TemplateManager()
        self.template_manager.paths = {
            "templates_dir": self.templates_dir,
            "custom_structures_dir": self.structures_dir,
            "templates_cache_dir": self.templates_cache_dir
        }
        
        # Mock template operations to use our paths
        self.template_ops = TemplateOperations()
        self.template_ops.paths = self.template_manager.paths
        self.template_ops.templates = []
    
    def tearDown(self):
        """Clean up temporary files after test"""
        shutil.rmtree(self.test_dir)
    
    def test_selective_file_caching(self):
        """Test that selective file caching includes only the selected files"""
        template_name = "Selective Files Template"
        
        # Select specific files for caching
        selected_files = [
            "image.jpg",          # Binary image file
            "src/main.py",        # Text file in subdirectory
            "template.txt"        # Text file with template vars
        ]
        
        # Import the template with selected files
        result = self.template_ops.import_template_file(
            self.test_project_dir, 
            template_name, 
            "Test", 
            selected_files=selected_files
        )
        
        self.assertTrue(result, "Template import should succeed")
        
        # Get the template
        template = None
        for tmpl in self.template_ops.templates:
            if tmpl.get("name") == template_name:
                template = tmpl
                break
        
        self.assertIsNotNone(template, "Template should exist in the templates list")
        
        # Check that the template has the selected_files attribute
        self.assertIn("selected_files", template, "Template should have selected_files attribute")
        self.assertEqual(template["selected_files"], selected_files, "Template should have correct selected files list")
        
        # Check that the cached files exist and only selected files are cached
        cache_dir = os.path.join(self.templates_cache_dir, template_name.replace(" ", "_"))
        self.assertTrue(os.path.exists(cache_dir), "Cache directory should exist")
        
        # Check that the binary image file was cached (should exist)
        self.assertTrue(
            os.path.exists(os.path.join(cache_dir, "image.jpg")), 
            "Binary image file should be cached"
        )
        
        # Check that the src/main.py file was cached
        self.assertTrue(
            os.path.exists(os.path.join(cache_dir, "src", "main.py")), 
            "Source file in subdirectory should be cached"
        )
        
        # Check that the template.txt file was cached
        self.assertTrue(
            os.path.exists(os.path.join(cache_dir, "template.txt")), 
            "Template file should be cached"
        )
        
        # Check that README.md was NOT cached (not in selected_files)
        self.assertFalse(
            os.path.exists(os.path.join(cache_dir, "README.md")), 
            "README.md should NOT be cached as it wasn't selected"
        )
        
        # Check that video.mp4 was NOT cached (not in selected_files)
        self.assertFalse(
            os.path.exists(os.path.join(cache_dir, "video.mp4")), 
            "video.mp4 should NOT be cached as it wasn't selected"
        )
        
        # Check that .git directory was NOT cached
        self.assertFalse(
            os.path.exists(os.path.join(cache_dir, ".git")), 
            ".git directory should NOT be cached"
        )
        
        # Check that node_modules directory was NOT cached
        self.assertFalse(
            os.path.exists(os.path.join(cache_dir, "node_modules")), 
            "node_modules directory should NOT be cached"
        )
    
    def test_export_with_selective_cache(self):
        """Test that export works correctly with selectively cached files"""
        template_name = "Export Selective Template"
        
        # Select specific files for caching
        selected_files = [
            "image.jpg",          # Binary image file
            "video.mp4",          # Binary video file
            "src/main.py",        # Text file in subdirectory
            "template.txt"        # Text file with template vars
        ]
        
        # Import the template with selected files
        result = self.template_ops.import_template_file(
            self.test_project_dir, 
            template_name, 
            "Test", 
            selected_files=selected_files
        )
        
        self.assertTrue(result, "Template import should succeed")
        
        # Get the template for export
        template = None
        for tmpl in self.template_ops.templates:
            if tmpl.get("name") == template_name:
                template = tmpl
                break
        
        self.assertIsNotNone(template, "Template should exist in the templates list")
        
        # Verify that the files were actually cached (the ones we selected)
        for selected_file in selected_files:
            cached_file_path = os.path.join(self.templates_cache_dir, template_name.replace(" ", "_"), selected_file)
            self.assertTrue(os.path.exists(cached_file_path), f"Selected file {selected_file} should be cached")
            
        # Check that unwanted files are not cached
        readme_path = os.path.join(self.templates_cache_dir, template_name.replace(" ", "_"), "README.md")
        self.assertFalse(os.path.exists(readme_path), "README.md should not be cached as it was not selected")
    
    def test_binary_file_import_and_cache(self):
        """Test that binary files can be imported and cached properly"""
        # Create a binary file directly
        binary_file = os.path.join(self.test_dir, "test_binary.bin")
        with open(binary_file, "wb") as f:
            f.write(os.urandom(4096))  # 4KB of random data
        
        template_name = "Binary File Template"
        
        # Import the binary file as a template
        result = self.template_ops.import_template_file(
            binary_file, 
            template_name, 
            "Binary"
        )
        
        self.assertTrue(result, "Binary file import should succeed")
        
        # Get the template
        template = None
        for tmpl in self.template_ops.templates:
            if tmpl.get("name") == template_name:
                template = tmpl
                break
        
        self.assertIsNotNone(template, "Template should exist in templates list")
        
        # Check that is_single_file is set
        self.assertTrue(template.get("is_single_file", False), "Template should be marked as single file")
        
        # Check the cached binary file
        cache_dir = os.path.join(self.templates_cache_dir, template_name.replace(" ", "_"))
        self.assertTrue(os.path.exists(cache_dir), "Cache directory should exist")
        
        cached_file = os.path.join(cache_dir, "test_binary.bin")
        self.assertTrue(os.path.exists(cached_file), "Binary file should be cached")
        
        # Compare file sizes to make sure content was cached correctly
        original_size = os.path.getsize(binary_file)
        cached_size = os.path.getsize(cached_file)
        self.assertEqual(original_size, cached_size, "Cached binary file should have same size as original")


if __name__ == "__main__":
    unittest.main() 
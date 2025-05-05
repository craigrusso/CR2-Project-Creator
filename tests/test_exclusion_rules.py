import os
import sys
import shutil
import unittest
import tempfile
from unittest.mock import MagicMock, patch

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.templates.template_operations import TemplateOperations
from app.templates.template_manager import TemplateManager


class TestExclusionRules(unittest.TestCase):
    """Tests for verifying exclusion rules work properly"""
    
    def setUp(self):
        """Set up a temporary directory structure with development directories for testing"""
        self.test_dir = tempfile.mkdtemp()
        self.test_project_dir = os.path.join(self.test_dir, "test_project")
        os.makedirs(self.test_project_dir)
        
        # Create a regular source file
        os.makedirs(os.path.join(self.test_project_dir, "src"))
        with open(os.path.join(self.test_project_dir, "src", "main.py"), "w") as f:
            f.write("print('Hello World')")
        
        # Create a README file
        with open(os.path.join(self.test_project_dir, "README.md"), "w") as f:
            f.write("# Test Project\nThis is a test project.")

        # Create development directories that should ALWAYS be excluded
        
        # Create a .git directory with some files
        os.makedirs(os.path.join(self.test_project_dir, ".git", "objects"))
        with open(os.path.join(self.test_project_dir, ".git", "config"), "w") as f:
            f.write("[core]\n\trepositoryformatversion = 0\n\tfilemode = true")
        with open(os.path.join(self.test_project_dir, ".git", "objects", "info"), "w") as f:
            f.write("dummy git object")
            
        # Create a node_modules directory
        os.makedirs(os.path.join(self.test_project_dir, "node_modules"))
        with open(os.path.join(self.test_project_dir, "node_modules", "package.json"), "w") as f:
            f.write('{"name": "test-package"}')
            
        # Create a .vscode directory
        os.makedirs(os.path.join(self.test_project_dir, ".vscode"))
        with open(os.path.join(self.test_project_dir, ".vscode", "settings.json"), "w") as f:
            f.write('{"editor.formatOnSave": true}')
            
        # Create a __pycache__ directory
        os.makedirs(os.path.join(self.test_project_dir, "__pycache__"))
        with open(os.path.join(self.test_project_dir, "__pycache__", "main.cpython-39.pyc"), "wb") as f:
            f.write(b'\x01\x02\x03\x04')  # Dummy binary content
        
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
    
    def test_excluded_directories_never_cached(self):
        """Test that excluded directories are never cached, even with no selection"""
        template_name = "Full Directory Template"
        
        # Import the entire directory - this should exclude dev directories
        result = self.template_ops.import_template_file(
            self.test_project_dir, 
            template_name, 
            "Test"
        )
        
        self.assertTrue(result, "Template import should succeed")
        
        # Get the template
        template = None
        for tmpl in self.template_ops.templates:
            if tmpl.get("name") == template_name:
                template = tmpl
                break
        
        self.assertIsNotNone(template, "Template should exist in the templates list")
        
        # Check that the cache directory was created
        cache_dir = os.path.join(self.templates_cache_dir, template_name.replace(" ", "_"))
        self.assertTrue(os.path.exists(cache_dir), "Cache directory should exist")
        
        # Check that normal files were cached
        self.assertTrue(
            os.path.exists(os.path.join(cache_dir, "README.md")), 
            "README.md should be cached"
        )
        self.assertTrue(
            os.path.exists(os.path.join(cache_dir, "src", "main.py")), 
            "src/main.py should be cached"
        )
        
        # Check that NONE of the excluded directories were cached
        excluded_dirs = ['.git', 'node_modules', '.vscode', '__pycache__']
        for excluded_dir in excluded_dirs:
            self.assertFalse(
                os.path.exists(os.path.join(cache_dir, excluded_dir)), 
                f"{excluded_dir} directory should NEVER be cached"
            )
    
    def test_excluded_directories_not_in_selected_files(self):
        """Test that files within excluded directories can't be selected for caching"""
        template_name = "Selected Files Template"
        
        # Try to select files that include some in excluded directories
        selected_files = [
            "src/main.py",               # Valid file that should be cached
            "README.md",                 # Valid file that should be cached
            ".git/config",               # In excluded directory - should be ignored
            "node_modules/package.json", # In excluded directory - should be ignored
            ".vscode/settings.json"      # In excluded directory - should be ignored
        ]
        
        # Import with selected files - files in excluded directories should be ignored
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
        
        # Check that the cache directory was created
        cache_dir = os.path.join(self.templates_cache_dir, template_name.replace(" ", "_"))
        self.assertTrue(os.path.exists(cache_dir), "Cache directory should exist")
        
        # Check that normal files were cached
        self.assertTrue(
            os.path.exists(os.path.join(cache_dir, "README.md")), 
            "README.md should be cached"
        )
        self.assertTrue(
            os.path.exists(os.path.join(cache_dir, "src", "main.py")), 
            "src/main.py should be cached"
        )
        
        # Check that NONE of the excluded directories were cached
        excluded_dirs = ['.git', 'node_modules', '.vscode', '__pycache__']
        for excluded_dir in excluded_dirs:
            self.assertFalse(
                os.path.exists(os.path.join(cache_dir, excluded_dir)), 
                f"{excluded_dir} directory should NEVER be cached"
            )
            
        # Check that individual files from excluded directories weren't cached
        self.assertFalse(
            os.path.exists(os.path.join(cache_dir, ".git", "config")), 
            ".git/config should NOT be cached"
        )
        self.assertFalse(
            os.path.exists(os.path.join(cache_dir, "node_modules", "package.json")), 
            "node_modules/package.json should NOT be cached"
        )
        self.assertFalse(
            os.path.exists(os.path.join(cache_dir, ".vscode", "settings.json")), 
            ".vscode/settings.json should NOT be cached"
        )


if __name__ == "__main__":
    unittest.main() 
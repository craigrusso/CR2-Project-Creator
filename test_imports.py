#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to verify imports are working properly after reorganization
"""

import sys
import traceback

def test_imports():
    """Test all critical imports to ensure they still work after reorganization"""
    
    print("Testing imports after reorganization...")
    
    try:
        # 1. Test config imports
        print("Testing config imports...")
        from app.config import APP_NAME, APP_VERSION, get_resource_path
        from app.config import get_user_data_root, get_templates_path
        print(f"App Name: {APP_NAME}, Version: {APP_VERSION}")
        
        # 2. Test core imports
        print("\nTesting core imports...")
        from app.core import ProjectCreatorApp, ProjectBuilder
        
        # 3. Test utils imports
        print("\nTesting utils imports...")
        from app.utils import (
            load_json_file, save_json_file, 
            FileOperationsHandler, BinaryFileHandler,
            validate_template_name, format_template_name
        )
        
        # 4. Test UI imports
        print("\nTesting UI imports...")
        from app.ui import apply_dark_theme_to_template_section, force_app_palette, configure_styles
        
        # 5. Test templates imports
        print("\nTesting templates imports...")
        from app.templates import TemplateManager, TemplateManagerMigration
        
        print("\nAll imports successful!")
        return True
        
    except ImportError as e:
        print(f"\nIMPORT ERROR: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1) 
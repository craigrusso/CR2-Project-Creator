#!/usr/bin/env python3
"""
Test script to verify tutorial slideshow functionality specifically in the built app context
This script will be run inside the built app environment to test resource loading
"""

import sys
import os

# Add the built app's framework path to Python path
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    bundle_dir = sys._MEIPASS
    app_path = os.path.join(bundle_dir, 'app')
    sys.path.insert(0, bundle_dir)
    sys.path.insert(0, app_path)
    print(f"Running in PyInstaller bundle: {bundle_dir}")
else:
    # Running in development
    project_root = '/Users/craigrusso/SynologyDrive/SCRIPTS/CLAUDE_PROJECT_CREATOR/V4'
    sys.path.insert(0, project_root)
    print(f"Running in development mode: {project_root}")

def test_imports():
    """Test if all required modules can be imported"""
    print("\n=== Testing Imports ===")
    try:
        from app.constants import get_resource_path
        print("✓ app.constants imported successfully")
        
        from app.onboarding.slideshow import TutorialSlideshow
        print("✓ TutorialSlideshow imported successfully")
        
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        print("✓ PyQt6 modules imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_resource_paths():
    """Test if tutorial resources can be found"""
    print("\n=== Testing Resource Paths ===")
    try:
        from app.constants import get_resource_path
        
        # Test slide images
        test_resources = [
            "slides/SLIDE_01.png",
            "slides/SLIDE_02_BG.png", 
            "slides/DOT EMPTY.png",
            "slides/DOT FILL.png"
        ]
        
        all_found = True
        for resource in test_resources:
            path = get_resource_path(resource)
            exists = os.path.exists(path)
            print(f"{'✓' if exists else '❌'} {resource}: {path} {'(exists)' if exists else '(NOT FOUND)'}")
            if not exists:
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"❌ Resource path test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_slideshow_creation():
    """Test if the slideshow can be created"""
    print("\n=== Testing Slideshow Creation ===")
    try:
        from PyQt6.QtWidgets import QApplication
        from app.onboarding.slideshow import TutorialSlideshow
        
        # Create minimal QApplication if needed
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            print("✓ Created QApplication")
        else:
            print("✓ Using existing QApplication")
        
        # Try to create the slideshow
        slideshow = TutorialSlideshow()
        print("✓ TutorialSlideshow created successfully")
        
        # Try to show it briefly
        slideshow.show()
        print("✓ Slideshow shown successfully")
        
        # Close it quickly
        slideshow.close()
        print("✓ Slideshow closed successfully")
        
        return True
    except Exception as e:
        print(f"❌ Slideshow creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("TUTORIAL SLIDESHOW TEST IN BUILT APP")
    print("=" * 60)
    
    # Run all tests
    imports_ok = test_imports()
    resources_ok = test_resource_paths() 
    slideshow_ok = test_slideshow_creation()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print(f"Imports:   {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"Resources: {'✅ PASS' if resources_ok else '❌ FAIL'}")
    print(f"Slideshow: {'✅ PASS' if slideshow_ok else '❌ FAIL'}")
    
    if imports_ok and resources_ok and slideshow_ok:
        print("🎉 ALL TESTS PASSED - Tutorial should work!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Tutorial may not work")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
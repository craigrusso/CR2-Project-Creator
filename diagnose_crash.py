#!/usr/bin/env python3
"""
Diagnostic script to help identify ForwardFlow crash issues.
"""

import os
import sys
import platform
import traceback
from pathlib import Path

def check_environment():
    """Check the environment for potential issues"""
    print("=== Environment Check ===")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Script location: {os.path.abspath(__file__)}")
    
    # Check for required directories
    required_dirs = [
        "app",
        "app/core",
        "app/ui",
        "app/templates",
        "forwardflow"
    ]
    
    print("\n=== Directory Check ===")
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✓ {dir_path} exists")
        else:
            print(f"✗ {dir_path} missing")
    
    # Check for critical files
    critical_files = [
        "main.py",
        "app/core/app_module_pyqt.py",
        "app/config/app_config.py"
    ]
    
    print("\n=== Critical Files Check ===")
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")

def check_imports():
    """Test critical imports"""
    print("\n=== Import Test ===")
    
    try:
        import PyQt6
        from PyQt6.QtCore import QT_VERSION_STR
        print(f"✓ PyQt6 version: {QT_VERSION_STR}")
    except ImportError as e:
        print(f"✗ PyQt6 import failed: {e}")
        return False
    except AttributeError as e:
        print(f"✗ PyQt6 version check failed: {e}")
        return False
    
    try:
        from PyQt6.QtWidgets import QApplication
        print("✓ PyQt6.QtWidgets import successful")
    except ImportError as e:
        print(f"✗ PyQt6.QtWidgets import failed: {e}")
        return False
    
    try:
        from app.config.app_config import APP_NAME, APP_VERSION_NUMBER
        print(f"✓ App config import successful: {APP_NAME} v{APP_VERSION_NUMBER}")
    except ImportError as e:
        print(f"✗ App config import failed: {e}")
        return False
    
    try:
        from app.core.app_module_pyqt import ForwardFlowApp
        print("✓ Main app class import successful")
    except ImportError as e:
        print(f"✗ Main app class import failed: {e}")
        return False
    
    return True

def test_ingest_module():
    """Test ingest module specifically"""
    print("\n=== Ingest Module Test ===")
    
    try:
        from forwardflow.ingest.config import FF_INGEST_ENABLED
        print(f"✓ Ingest module config import successful: FF_INGEST_ENABLED = {FF_INGEST_ENABLED}")
    except ImportError as e:
        print(f"✗ Ingest module config import failed: {e}")
        return False
    
    try:
        from forwardflow.ingest.engines.python_engine import PythonCopyEngine
        print("✓ Python copy engine import successful")
    except ImportError as e:
        print(f"✗ Python copy engine import failed: {e}")
        return False
    
    try:
        from forwardflow.ingest.ui.ingest_tab import build_ingest_tab
        print("✓ Ingest tab builder import successful")
    except ImportError as e:
        print(f"✗ Ingest tab builder import failed: {e}")
        return False
    
    return True

def main():
    """Main diagnostic function"""
    print("ForwardFlow Crash Diagnostic Tool")
    print("=" * 50)
    
    # Check environment
    check_environment()
    
    # Test imports
    imports_ok = check_imports()
    
    # Test ingest module
    ingest_ok = test_ingest_module()
    
    print("\n=== Summary ===")
    if imports_ok:
        print("✓ Basic imports successful")
    else:
        print("✗ Basic imports failed")
    
    if ingest_ok:
        print("✓ Ingest module imports successful")
    else:
        print("✗ Ingest module imports failed")
    
    if imports_ok and ingest_ok:
        print("\n✓ All checks passed - the app should start normally")
        print("If it still crashes, the issue may be runtime-related")
    else:
        print("\n✗ Some checks failed - fix the import issues first")
    
    print("\n=== Recommendations ===")
    if not imports_ok:
        print("1. Check that PyQt6 is properly installed")
        print("2. Verify all app modules are present")
        print("3. Check Python path and virtual environment")
    
    if not ingest_ok:
        print("4. The ingest module may be causing crashes")
        print("5. Try running with FF_INGEST_ENABLED=False")
        print("6. Check forwardflow module installation")
    
    print("\nTo test without ingest module, run: python test_app_safe.py")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Safe test script for ForwardFlow that disables the ingest module
to test if crashes are ingest-specific.
"""

import os
import sys
import platform

# Temporarily disable the ingest module
os.environ['FF_INGEST_ENABLED'] = 'False'

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for the safe test"""
    print("=== ForwardFlow Safe Test Mode ===")
    print("Ingest module disabled for testing")
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    
    try:
        # Import and run the main application
        from main import main as app_main
        print("Starting ForwardFlow in safe test mode...")
        return app_main()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

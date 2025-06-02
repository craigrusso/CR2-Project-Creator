import platform
import os
import logging
import sys

def clear_icon_cache():
    if platform.system() == "Windows":
        try:
            os.system('ie4uinit.exe -ClearIconCache')
        except Exception as e:
            logging.error(f"Error clearing icon cache: {e}")

if __name__ == "__main__":
    clear_icon_cache()
    sys.exit(main()) 
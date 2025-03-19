# utils.py

import platform

def get_system_font():
    """Return an appropriate system font based on platform."""
    system = platform.system()
    if system == "Windows":
        return "Segoe UI, Arial, sans-serif"
    elif system == "Darwin":  # macOS
        return "Helvetica"
    else:  # Linux and others
        return "Ubuntu, DejaVu Sans, Liberation Sans, Arial, sans-serif"

SYSTEM_FONT = get_system_font()

def is_mac():
    return platform.system() == "Darwin"

def is_windows():
    return platform.system() == "Windows"

def is_linux():
    return platform.system() == "Linux"
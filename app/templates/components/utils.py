# utils.py

import platform

def get_system_font():
    """Return an appropriate system font based on platform."""
    system = platform.system()
    if system == "Windows":
        return "Segoe UI"
    elif system == "Darwin":  # macOS
        return "Helvetica Neue"
    else:
        return "Ubuntu, DejaVu Sans, Liberation Sans, Arial"

SYSTEM_FONT = get_system_font()

def is_mac():
    return platform.system() == "Darwin"

def is_windows():
    return platform.system() == "Windows"

def is_linux():
    return platform.system() == "Linux"
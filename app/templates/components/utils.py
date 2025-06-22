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

def get_platform_font_size(base_size):
    """
    Return platform-adjusted font size to ensure consistent appearance across platforms.
    Windows tends to render fonts larger, so we use smaller sizes there.
    macOS and Linux need larger sizes for the same visual appearance.
    """
    system = platform.system()
    if system == "Windows":
        # Windows fonts render larger, so use smaller sizes
        return base_size
    elif system == "Darwin":  # macOS
        # macOS needs larger font sizes for equivalent visual appearance
        return int(base_size * 1.3)  # 30% larger
    else:  # Linux and others
        # Linux generally needs slightly larger fonts too
        return int(base_size * 1.2)  # 20% larger

def get_platform_css_font_size(base_size):
    """
    Return platform-adjusted CSS font size string for consistent appearance across platforms.
    """
    adjusted_size = get_platform_font_size(base_size)
    return f"{adjusted_size}px"

def get_slideshow_title_font_size():
    """Get the appropriate font size for slideshow titles across platforms"""
    return get_platform_font_size(22)

def get_slideshow_description_font_size():
    """Get the appropriate font size for slideshow descriptions across platforms"""
    return get_platform_font_size(11)

SYSTEM_FONT = get_system_font()

def is_mac():
    return platform.system() == "Darwin"

def is_windows():
    return platform.system() == "Windows"

def is_linux():
    return platform.system() == "Linux"
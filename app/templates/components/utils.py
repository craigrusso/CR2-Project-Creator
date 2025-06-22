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

def get_display_info():
    """
    Get display information including DPI and scaling factor.
    Returns dict with 'dpi', 'scale_factor', and 'logical_dpi'.
    """
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QGuiApplication
        
        app = QApplication.instance() or QGuiApplication.instance()
        if not app:
            # Fallback if no app instance
            return {"dpi": 96, "scale_factor": 1.0, "logical_dpi": 96}
        
        screen = app.primaryScreen()
        if not screen:
            return {"dpi": 96, "scale_factor": 1.0, "logical_dpi": 96}
        
        # Get physical DPI
        physical_dpi = screen.physicalDotsPerInch()
        
        # Get logical DPI (after OS scaling)
        logical_dpi = screen.logicalDotsPerInch()
        
        # Calculate scale factor
        scale_factor = logical_dpi / 96.0  # 96 DPI is the standard baseline
        
        return {
            "dpi": physical_dpi,
            "scale_factor": scale_factor,
            "logical_dpi": logical_dpi
        }
    except Exception as e:
        # Fallback for any import or detection issues
        return {"dpi": 96, "scale_factor": 1.0, "logical_dpi": 96}

def calculate_optimal_font_size(base_size, container_width, text_length, max_lines=3, scale_adjustment=1.0):
    """
    Calculate optimal font size that fits within container without overflow.
    
    Args:
        base_size: Base font size to start from
        container_width: Available width in pixels
        text_length: Approximate character count of text
        max_lines: Maximum lines before text should wrap
        scale_adjustment: Additional scaling factor (1.0 = no change)
        
    Returns:
        Optimal font size as integer
    """
    display = get_display_info()
    scale_factor = display["scale_factor"]
    
    # Platform-specific baseline adjustments
    system = platform.system()
    if system == "Windows":
        platform_factor = 0.95  # Slightly smaller on Windows
    elif system == "Darwin":  # macOS
        platform_factor = 1.15  # Larger on Mac
    else:  # Linux
        platform_factor = 1.05  # Slightly larger on Linux
    
    # Estimate character width (rough approximation)
    # Typical character width is about 0.6 * font_size for most fonts
    char_width_ratio = 0.6
    
    # Account for container padding/margins (estimate 40px total)
    effective_width = container_width - 40
    
    # Calculate how many characters can fit per line
    chars_per_line = effective_width / (base_size * char_width_ratio * scale_factor * platform_factor)
    
    # Calculate required lines
    required_lines = text_length / chars_per_line if chars_per_line > 0 else max_lines
    
    # If text would exceed max_lines, reduce font size
    size_adjustment = 1.0
    if required_lines > max_lines:
        size_adjustment = max_lines / required_lines
        size_adjustment = max(0.7, size_adjustment)  # Don't go below 70% of original
    
    # Apply all factors
    final_size = int(base_size * platform_factor * scale_adjustment * size_adjustment)
    
    # Ensure reasonable bounds
    min_size = max(8, int(base_size * 0.6))  # Never below 60% of base or 8px
    max_size = int(base_size * 1.8)  # Never above 180% of base
    
    return max(min_size, min(max_size, final_size))

def get_slideshow_title_font_size(text="Sample Title", container_width=430):
    """Get optimal font size for slideshow titles based on content and container"""
    base_size = 28  # Larger base size
    text_length = len(text) if text else 50
    
    # Special handling for different platforms
    system = platform.system()
    if system == "Darwin":  # macOS
        # Mac needs larger fonts but not cartoonishly large
        min_size = 24  # Minimum 24px on Mac (reduced from 32px)
        max_size = 32  # Maximum 32px on Mac to prevent huge titles
        calculated_size = calculate_optimal_font_size(base_size, container_width, text_length, max_lines=2, scale_adjustment=1.2)
        return min(max_size, max(min_size, calculated_size))
    elif system == "Windows":
        # Windows headers tend to render large, so use smaller base with limits
        min_size = 18  # Minimum 18px on Windows
        max_size = 26  # Maximum 26px on Windows to prevent giant headers
        calculated_size = calculate_optimal_font_size(22, container_width, text_length, max_lines=2, scale_adjustment=1.0)
        return min(max_size, max(min_size, calculated_size))
    else:
        # Linux and others
        return calculate_optimal_font_size(base_size, container_width, text_length, max_lines=2, scale_adjustment=1.2)

def get_slideshow_description_font_size(text="Sample description text", container_width=430):
    """Get optimal font size for slideshow descriptions based on content and container"""
    base_size = 14  # Larger base size
    text_length = len(text) if text else 200
    
    # Special handling for different platforms
    system = platform.system()
    if system == "Darwin":  # macOS
        # Mac needs larger fonts
        min_size = 16  # Minimum 16px on Mac
        calculated_size = calculate_optimal_font_size(base_size, container_width, text_length, max_lines=6, scale_adjustment=1.3)
        return max(min_size, calculated_size)
    elif system == "Windows":
        # Windows description text tends to render small, so boost it
        min_size = 13  # Minimum 13px on Windows (larger than before)
        max_size = 18  # Maximum 18px to keep it readable but not huge
        calculated_size = calculate_optimal_font_size(15, container_width, text_length, max_lines=6, scale_adjustment=1.2)
        return min(max_size, max(min_size, calculated_size))
    else:
        # Linux and others
        return calculate_optimal_font_size(base_size, container_width, text_length, max_lines=6, scale_adjustment=1.0)

def get_dynamic_font_size(base_size, scale_adjustment=1.0):
    """
    Get dynamically adjusted font size based on display characteristics.
    Simpler version for general UI elements.
    """
    display = get_display_info()
    scale_factor = display["scale_factor"]
    
    # Platform-specific adjustments
    system = platform.system()
    if system == "Windows":
        platform_factor = 0.95
    elif system == "Darwin":  # macOS
        platform_factor = 1.15
    else:  # Linux
        platform_factor = 1.05
    
    final_size = int(base_size * platform_factor * scale_adjustment * min(1.5, scale_factor))
    return max(8, min(72, final_size))  # Reasonable bounds

def get_platform_css_font_size(base_size, scale_adjustment=1.0):
    """
    Return platform and DPI adjusted CSS font size string.
    """
    adjusted_size = get_dynamic_font_size(base_size, scale_adjustment)
    return f"{adjusted_size}px"

# Legacy function for backward compatibility
def get_platform_font_size(base_size):
    """Legacy function - use get_dynamic_font_size instead"""
    return get_dynamic_font_size(base_size)

SYSTEM_FONT = get_system_font()

def is_mac():
    return platform.system() == "Darwin"

def is_windows():
    return platform.system() == "Windows"

def is_linux():
    return platform.system() == "Linux"
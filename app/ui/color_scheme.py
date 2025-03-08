#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Color Scheme File for CR2 Project Creator
This file provides a centralized place for all color definitions
to ensure consistency across the application.
"""

# Main application colors
APP_COLORS = {
    # Main background colors
    "bg": "#1E1E1E",              # Main application background
    "card_bg": "#252526",         # Card background (darker than bg)
    
    # Text colors
    "text": "#CCCCCC",            # Primary text color
    "secondary_text": "#858585",  # Secondary/dimmed text
    
    # Accent colors
    "accent": "#007ACC",          # Blue accent color
    "accent_hover": "#0066B3",    # Darker blue for hover states
    
    # Status/notification colors
    "success": "#4CAF50",         # Success (green)
    "success_text": "#003300",    # Text on success backgrounds
    "warning": "#F1AE3C",         # Warning (yellow/amber)
    "error": "#E8574C",           # Error (red)
    
    # Selection/highlight colors
    "highlight_bg": "#4682B4",    # Steel Blue for highlights (selected items)
    "highlight_darker": "#36648B", # Darker blue for hover on highlighted items
    "highlight_text": "#FFFFFF",  # White text for highlighted items
    
    # Hover effect colors
    "hover_bg": "#303030",        # Light grey hover effect for cards
    
    # Border colors
    "border": "#3C3C3C",          # Border for cards and sections
    "highlight_border": "#4682B4" # Border for highlighted elements
}

# Function to get a specific color by name
def get_color(name):
    """Get a color by name from the color scheme"""
    return APP_COLORS.get(name, APP_COLORS["text"])  # Default to text color if not found

# For backward compatibility with existing 'colors' dictionary
colors = APP_COLORS

# Export specific color combinations for different UI elements
CARD_NORMAL = {
    "bg": APP_COLORS["card_bg"],
    "border": APP_COLORS["card_bg"],
    "text": APP_COLORS["text"],
    "secondary_text": APP_COLORS["secondary_text"]
}

CARD_HOVER = {
    "bg": APP_COLORS["hover_bg"],
    "border": APP_COLORS["hover_bg"],
    "text": APP_COLORS["text"],
    "secondary_text": APP_COLORS["secondary_text"]
}

CARD_SELECTED = {
    "bg": APP_COLORS["highlight_bg"],
    "border": APP_COLORS["highlight_bg"],
    "text": APP_COLORS["highlight_text"],
    "secondary_text": APP_COLORS["highlight_text"]
} 
"""
Custom Patterns Dialog Package

This package contains all components of the custom patterns functionality,
broken down into focused, manageable modules.
"""

# Import all the component modules
from .pattern_ui_components import PatternUIComponents
from .custom_options_manager import CustomOptionsManager
from .format_managers import FormatManagers
from .pattern_logic import PatternLogic
from .pattern_data_handler import PatternDataHandler

__all__ = [
    'PatternUIComponents',
    'CustomOptionsManager', 
    'FormatManagers',
    'PatternLogic',
    'PatternDataHandler'
] 
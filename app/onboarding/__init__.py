#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Onboarding Tutorial System

A modular, self-contained tutorial system that provides:
- Interactive slideshow tutorials for first-time users
- Tutorial state management and preferences
- Easy integration with existing PyQt6 applications

The system is designed to be non-intrusive and easily removable if needed.
"""

from .tutorial_manager import TutorialManager
from .slideshow import TutorialSlideshow
from .tutorial_state import TutorialState

__all__ = [
    'TutorialManager',
    'TutorialSlideshow', 
    'TutorialState'
]

# Version info for the onboarding system
__version__ = "1.0.0"
__author__ = "CR2 Creative" 
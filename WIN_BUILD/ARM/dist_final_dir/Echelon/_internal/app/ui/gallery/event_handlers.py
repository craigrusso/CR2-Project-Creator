#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Event handler bridge module for the gallery UI components.
This module imports the actual gallery event handlers from app.templates.gallery_events
and re-exports them to keep backward compatibility with UI components.
"""

# Import the actual implementation
from app.templates.gallery_events import GalleryEvents

# This module serves as a bridge to maintain compatibility with UI components
# that import GalleryEvents from app.ui.gallery.event_handlers 
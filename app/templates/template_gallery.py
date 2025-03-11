#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

# Re-export the refactored TemplateGallery class
from .template_gallery_refactored import TemplateGallery

# This file is now just a compatibility layer to maintain backwards compatibility.
# All implementation details have been moved to separate modules:
# - template_gallery_refactored.py - Main class with core functionality
# - gallery_ui_setup.py - UI setup methods
# - gallery_folders.py - Folder related functionality
# - gallery_templates.py - Template related functionality
# - gallery_events.py - Event handlers

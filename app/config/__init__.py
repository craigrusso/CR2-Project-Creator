#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Configuration module for the application
"""

# Import core configuration
from app.config.app_config import APP_NAME, APP_VERSION
from app.config.constants import get_resource_path
from app.config.config_manager import (
    get_user_data_root,
    set_user_data_root,
    get_templates_path,
    get_cache_path,
    get_settings_path
) 
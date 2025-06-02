#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Security utility module
"""

# Import the BookmarkManager as SecurityBookmarkManager for clarity
from app.utils.security.security_bookmarks import BookmarkManager as SecurityBookmarkManager
from app.utils.security.security_bookmarks import (
    get_bookmark_manager,
    create_bookmark as save_security_bookmarks,
    access_bookmark as load_security_bookmarks,
    with_bookmark_access
)

# Import the license manager components
from app.utils.security.license_manager import (
    LicenseManager,
    LicenseActivationDialog,
    TrialNagDialog,
    LICENSE_TYPE_PERMANENT,
    LICENSE_TYPE_ENTERPRISE,
    LICENSE_TYPE_SUBSCRIPTION
) 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys

# Use PyQt structures module
from app.core.structures_pyqt import (
    create_custom_structure, save_custom_structure,
    edit_structure, update_custom_structure,
    manage_structures, rename_structure,
    delete_structure, update_structure_dropdown,
    highlight_current_structure, _update_structure_combo,
    _preview_structure, _edit_structure
)
UI_FRAMEWORK = 'pyqt'

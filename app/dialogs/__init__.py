# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Dialog window modules - PyQt version
"""

# Using PyQt for the UI framework
from PyQt5.QtWidgets import QApplication
UI_FRAMEWORK = 'pyqt'

# PyQt dialogs are implemented in dialog_windows_pyqt.py
from app.dialogs.dialog_windows_pyqt import (
    show_about,
    show_preferences,
    show_tutorial,
    show_batch_create,
    show_batch_results,
    preview_structure,
    show_structure_editor
)

"""
Structure Editor Dialogs Package

This package contains all dialog classes that were previously in the monolithic
file_operations.py file. Each dialog is now in its own focused module.
"""

from .versioning_dialog import VersioningDialog
from .date_sequence_dialog import DateSequenceDialog
from .file_details_dialog import FileDetailsDialog

__all__ = [
    'VersioningDialog', 
    'DateSequenceDialog',
    'FileDetailsDialog'
] 
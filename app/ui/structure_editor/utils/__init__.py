"""
Structure Editor Utilities Package

Small utility modules for common functionality.
"""

from .file_type_detector import FileTypeDetector
from .tree_item_helpers import TreeItemHelpers
from .structure_utils import _count_structure_items, get_file_icon_for_type, is_built_in_structure

__all__ = [
    'FileTypeDetector',
    'TreeItemHelpers',
    '_count_structure_items',
    'get_file_icon_for_type',
    'is_built_in_structure'
] 
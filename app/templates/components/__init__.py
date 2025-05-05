#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Components module for the template gallery system.
Contains the UI components used in the template gallery interface.
"""

from PyQt5.QtCore import QObject
from .template_card import TemplateCard
from .template_list_item import TemplateListItem
from .template_folder_card import TemplateFolderCard
from .template_folder_list_item import TemplateFolderListItem
from .components import SearchBox, ScrollableFrame, CardFrame, ToolTip
from .common_styles import CARD_NORMAL, CARD_HOVER, CARD_SELECTED, colors
from .utils import SYSTEM_FONT, get_system_font
from .menu_actions import ContextMenu

__all__ = [
    "TemplateCard", 
    "TemplateListItem", 
    "TemplateFolderCard",
    "TemplateFolderListItem",
    "SYSTEM_FONT",
    "get_system_font",
    "CARD_NORMAL",
    "CARD_HOVER", 
    "CARD_SELECTED",
    "ContextMenu"
] 
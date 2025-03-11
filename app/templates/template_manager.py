#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import importlib

from app.templates.template_manager_core import TemplateManagerCore
from app.templates.template_operations import TemplateOperations
from app.templates.structure_operations import StructureOperations
from app.templates.folder_operations import FolderOperations
from app.templates.ui_operations import UIOperations

class TemplateManager(TemplateManagerCore, TemplateOperations, StructureOperations, FolderOperations, UIOperations):
    """
    Manages project templates and custom structures
    
    This class combines functionality from:
    - TemplateManagerCore: Core initialization and basic operations
    - TemplateOperations: Template CRUD operations
    - StructureOperations: Custom structure operations
    - FolderOperations: Folder management operations
    - UIOperations: UI-related operations
    """
    def __init__(self):
        # Initialize the core functionality
        TemplateManagerCore.__init__(self)

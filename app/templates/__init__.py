# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template management modules
"""

# Import key template modules - PyQt version
from app.templates.template_manager import TemplateManager
from app.templates.templates import (
    populate_template_gallery,
    select_template_from_gallery,
    get_template_file,
    clear_template_file,
    clear_structure_template,
    rename_current_template,
    rename_template_file
)
# Migration helper for upgrade path
from app.templates.template_manager_migration import TemplateManagerMigration
from app.templates.template_category_manager import TemplateCategoryManager
from app.templates.template_card_pyqt import TemplateCard

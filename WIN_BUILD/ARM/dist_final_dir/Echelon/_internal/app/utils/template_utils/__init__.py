#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template utilities module
"""

from app.utils.template_utils.template_validator import TemplateValidator
from app.utils.template_utils.template_name_utils import TemplateNameGenerator
from app.utils.template_utils.structure_utils import StructureUtils

# Define the exported functions
# Use the actual functions directly from their respective classes
validate_template_name = TemplateNameGenerator.validate_and_fix_name
format_template_name = TemplateNameGenerator.sanitize_name

# Define the structure utility functions
get_structure_file_extension = lambda ext: f".{ext}" if not ext.startswith(".") else ext
get_structure_file_extensions = lambda: [".json", ".yaml", ".yml"]
parse_structure_data = StructureUtils.normalize_structure 
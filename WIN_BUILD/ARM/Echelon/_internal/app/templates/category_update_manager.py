#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Category Update Manager (Facade)

This module now acts as a facade, re-exporting the primary CategoryUpdateManager 
and related functionalities from their new, refactored locations.

Primary logic is now in:
- app.templates.category_event_handler.py (for the manager class and event handling)
- app.templates.category_combobox_updater.py (for combobox population and styling utilities)
"""

import logging

# Re-export the main manager instance getter from the event handler module
from app.templates.category_event_handler import get_category_update_manager as get_instance
from app.templates.category_event_handler import CategoryUpdateManager # For type hinting or direct instantiation if ever needed

# Re-export key functions from the combobox updater module if they were previously accessed directly
# (or if they are intended for broader utility)
from app.templates.category_combobox_updater import (
    update_single_combobox,
    ensure_all_combos_have_hover_delegates,
    style_category_combobox
)

# Deprecated test functions - these should be moved or managed within a proper test suite
# or adapted if still needed for diagnostics.

def test_category_update_manager(app=None):
    logging.warning("'test_category_update_manager' is deprecated and its functionality should be verified via new structure.")
    # manager = get_instance(app)
    # if manager:
    #     manager.force_immediate_global_update() # Example of calling the new manager
    pass

def diagnose_category_dropdown_issue(app=None):
    logging.warning("'diagnose_category_dropdown_issue' is deprecated. Use logging and direct checks on the new components.")
    # Example: You might call ensure_all_combos_have_hover_delegates() and check logs
    # if app:
    #     ensure_all_combos_have_hover_delegates(app)
    pass

# Make the primary get_instance available for existing code that uses it.
# This maintains backward compatibility for imports like:
# from app.templates.category_update_manager import get_instance
__all__ = [
    "get_instance", 
    "CategoryUpdateManager",
    "update_single_combobox",
    "ensure_all_combos_have_hover_delegates",
    "style_category_combobox",
    "test_category_update_manager",
    "diagnose_category_dropdown_issue"
]

log = logging.getLogger(__name__)
log.info("app.templates.category_update_manager is now a facade for refactored category management.") 
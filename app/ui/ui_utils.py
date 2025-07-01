#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
UI utility functions.
"""

from app.ui.color_scheme_pyqt import colors

def get_styled_app_name():
    """
    Returns the styled application name using HTML.
    """
    flow_color = colors.get("styled_flow_blue", "#2d7096")
    return f"Forward<i style='color:{flow_color}'>Flow</i>" 
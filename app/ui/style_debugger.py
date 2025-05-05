#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import logging
from PyQt5.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, QApplication
from PyQt5.QtCore import Qt, QEvent, QObject

# Set up logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class StyleDebugger(QObject):
    """
    Utility class for debugging styling issues with Qt widgets
    
    This class helps diagnose styling conflicts by monitoring and reporting
    the active styles on widgets at runtime.
    """
    
    def __init__(self, target_widget):
        """
        Initialize the style debugger with a target widget to monitor
        
        Args:
            target_widget: The widget to monitor for style changes
        """
        super().__init__()
        self.target_widget = target_widget
        self.widget_type = type(target_widget).__name__
        
        # If it's a tree widget, install event filter to monitor item events
        if isinstance(target_widget, QTreeWidget):
            target_widget.installEventFilter(self)
            target_widget.viewport().installEventFilter(self)
            logger.debug(f"Style debugger attached to {self.widget_type}")
    
    def eventFilter(self, obj, event):
        """
        Filter events to monitor style-related changes
        
        Args:
            obj: The object receiving the event
            event: The event being processed
        
        Returns:
            False to allow the event to be processed further
        """
        # Monitor hover events on the viewport
        if event.type() == QEvent.HoverEnter or event.type() == QEvent.HoverLeave:
            logger.debug(f"Hover event on {type(obj).__name__}")
            
        # Monitor style changes
        elif event.type() == QEvent.StyleChange:
            logger.debug(f"Style changed on {type(obj).__name__}")
            self.log_current_style()
            
        # Monitor mouse events for tree items
        elif isinstance(obj, QTreeWidget) and event.type() in [QEvent.MouseButtonPress, QEvent.MouseButtonRelease]:
            item = obj.itemAt(event.pos())
            if item:
                logger.debug(f"Mouse event on item: {item.text(0)}")
                self.log_item_properties(item)
                
        return False
    
    def log_current_style(self):
        """Log the current style information for the target widget"""
        logger.debug("=== STYLE INFORMATION ===")
        logger.debug(f"Widget: {self.widget_type}")
        logger.debug(f"Style sheet: {self.target_widget.styleSheet()}")
        
        # For tree widgets, also log items and their properties
        if isinstance(self.target_widget, QTreeWidget):
            logger.debug("Tree widget properties:")
            logger.debug(f"- Frame shape: {self.target_widget.frameShape()}")
            logger.debug(f"- Frame shadow: {self.target_widget.frameShadow()}")
            logger.debug(f"- Edit triggers: {self.target_widget.editTriggers()}")
            
            # Log root items
            root_count = self.target_widget.topLevelItemCount()
            logger.debug(f"Root items: {root_count}")
            for i in range(root_count):
                item = self.target_widget.topLevelItem(i)
                self.log_item_properties(item, depth=0)
    
    def log_item_properties(self, item, depth=0):
        """
        Log properties of a tree widget item
        
        Args:
            item: The QTreeWidgetItem to inspect
            depth: The depth in the tree hierarchy
        """
        indent = "  " * depth
        logger.debug(f"{indent}Item: {item.text(0)}")
        logger.debug(f"{indent}- Flags: {item.flags()}")
        logger.debug(f"{indent}- Is selected: {item.isSelected()}")
        logger.debug(f"{indent}- Background: {item.background(0).color().name()}")
        logger.debug(f"{indent}- Foreground: {item.foreground(0).color().name()}")
        
        # Log children recursively
        for i in range(item.childCount()):
            self.log_item_properties(item.child(i), depth + 1)
    
    def compare_styles(self, style1, style2):
        """
        Compare two style sheets and highlight differences
        
        Args:
            style1: First style sheet string
            style2: Second style sheet string
        """
        style1_parts = self._parse_style(style1)
        style2_parts = self._parse_style(style2)
        
        # Find differences
        all_selectors = set(style1_parts.keys()) | set(style2_parts.keys())
        
        logger.debug("=== STYLE DIFFERENCES ===")
        for selector in sorted(all_selectors):
            if selector not in style1_parts:
                logger.debug(f"Only in style2: {selector} {style2_parts[selector]}")
            elif selector not in style2_parts:
                logger.debug(f"Only in style1: {selector} {style1_parts[selector]}")
            elif style1_parts[selector] != style2_parts[selector]:
                logger.debug(f"Different for {selector}:")
                logger.debug(f"  Style1: {style1_parts[selector]}")
                logger.debug(f"  Style2: {style2_parts[selector]}")
    
    def _parse_style(self, style_sheet):
        """
        Parse a style sheet into a dictionary of selectors and properties
        
        Args:
            style_sheet: The style sheet string to parse
        
        Returns:
            A dictionary mapping selectors to property strings
        """
        result = {}
        parts = style_sheet.split('}')
        
        for part in parts:
            if not part.strip():
                continue
                
            selector_end = part.find('{')
            if selector_end > 0:
                selector = part[:selector_end].strip()
                properties = part[selector_end+1:].strip()
                result[selector] = properties
                
        return result
    
    def get_effective_styles(self, widget=None):
        """
        Get the effective styles for a widget, considering inheritance
        
        Args:
            widget: The widget to inspect, or the target widget if None
        
        Returns:
            A string representing the effective style sheet
        """
        widget = widget or self.target_widget
        effective_style = widget.styleSheet()
        
        # Add parent styles that might be inherited
        parent = widget.parent()
        while parent:
            if parent.styleSheet():
                effective_style = parent.styleSheet() + "\n" + effective_style
            parent = parent.parent()
            
        return effective_style

def create_style_report(widget, output_file=None):
    """
    Create a comprehensive style report for a widget and its children
    
    Args:
        widget: The root widget to analyze
        output_file: Optional path to write the report to
    
    Returns:
        A string containing the report
    """
    debugger = StyleDebugger(widget)
    report = ["=== STYLE REPORT ==="]
    report.append(f"Widget: {type(widget).__name__}")
    report.append(f"Style sheet: {widget.styleSheet()}")
    
    # Add effective styles
    report.append("Effective styles:")
    report.append(debugger.get_effective_styles())
    
    # Add child widget styles if applicable
    if hasattr(widget, 'children'):
        for child in widget.children():
            if isinstance(child, QWidget) and child.styleSheet():
                report.append(f"\nChild widget: {type(child).__name__}")
                report.append(f"Style sheet: {child.styleSheet()}")
    
    # Write to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            f.write('\n'.join(report))
    
    return '\n'.join(report) 
#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import sys
import inspect
import os
import traceback
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, 
                            QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel, 
                            QStyle, QStyledItemDelegate)
from PyQt5.QtCore import Qt, QObject, QEvent

# This script intercepts PyQt edit events to find where "edit: editing failed"
# is being printed or where editing is failing.

# Track all print statements
original_print = print

def print_tracer(*args, **kwargs):
    """Trace print statements to find the culprit"""
    # Only inspect prints about editing
    text = " ".join(str(arg) for arg in args)
    if "edit" in text.lower() and "fail" in text.lower():
        stack = traceback.extract_stack()
        caller = stack[-2]  # The caller of print_tracer
        original_print(f"TRACED: {text}")
        original_print(f"Called from: {caller.filename}:{caller.lineno}")
        original_print(f"Function: {caller.name}")
        original_print(f"Context: {caller.line}")
        original_print("Stack trace:")
        for frame in reversed(stack[:-1]):
            original_print(f"  {frame.filename}:{frame.lineno} - {frame.name}")
    
    # Pass through to the original print
    return original_print(*args, **kwargs)

# Replace built-in print
sys.modules['builtins'].print = print_tracer

# Event filter to catch QEvent.Edit events
class EditEventFilter(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def eventFilter(self, obj, event):
        # Track any edit-related events
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                original_print(f"EDIT KEY PRESS: Enter/Return in {obj.__class__.__name__}")
        elif event.type() == QEvent.FocusOut:
            original_print(f"EDIT FOCUS OUT: {obj.__class__.__name__}")
        
        return super().eventFilter(obj, event)

# Custom delegate to track editing events
class TraceEditDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        original_print("TraceEditDelegate created")
        
    def createEditor(self, parent, option, index):
        original_print(f"createEditor called for {index.data()}")
        editor = super().createEditor(parent, option, index)
        if editor:
            editor.installEventFilter(EditEventFilter(editor))
            original_print(f"Created editor: {editor.__class__.__name__}")
        return editor
    
    def setEditorData(self, editor, index):
        original_print(f"setEditorData called for {index.data()}")
        super().setEditorData(editor, index)
        
    def setModelData(self, editor, model, index):
        original_print(f"setModelData called - about to commit edit for {index.data()}")
        try:
            super().setModelData(editor, model, index)
            original_print(f"setModelData succeeded for {index.data()}")
        except Exception as e:
            original_print(f"setModelData FAILED: {e}")
            traceback.print_exc()
            
    def closeEditor(self, editor, hint):
        original_print(f"closeEditor called with hint: {hint}")
        super().closeEditor(editor, hint)

# Monkey patch QTreeWidget.editItem method
original_editItem = QTreeWidget.editItem

def traced_editItem(self, item, column):
    original_print(f"editItem called for '{item.text(column)}' at column {column}")
    try:
        return original_editItem(self, item, column)
    except Exception as e:
        original_print(f"editItem FAILED: {e}")
        traceback.print_exc()

QTreeWidget.editItem = traced_editItem

# Run the main application with our debug hooks
if __name__ == "__main__":
    # Execute the main script
    original_print("Starting main.py with debug hooks...")
    
    # Find the main.py in the current directory
    main_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    
    # Execute the original main script
    if os.path.exists(main_script):
        original_print(f"Executing main script: {main_script}")
        exec(open(main_script).read())
    else:
        original_print(f"Could not find main script: {main_script}") 
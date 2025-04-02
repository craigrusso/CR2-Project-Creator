#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem,
                            QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel,
                            QStyle, QSplitter, QTextEdit)
from PyQt5.QtCore import Qt, QEvent

from app.ui.style_debugger import StyleDebugger, create_style_report
from app.ui.tree_styling import apply_tree_styling, setup_tree_for_structure_editing

class StyleListenerWindow(QMainWindow):
    """Test window with tree widget and style monitor for diagnostics"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Style Listener Test")
        self.resize(1200, 800)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Instructions
        instructions = QLabel(
            "Create a template and add folders/files to the tree view. "
            "The style debugger will monitor and log styling information to help diagnose the blue border issue."
        )
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)
        
        # Create splitter for tree and log
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side - Tree widget with our fixed styling
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        
        # Add tree label
        tree_label = QLabel("Template Structure Tree:")
        tree_label.setStyleSheet("font-weight: bold;")
        tree_layout.addWidget(tree_label)
        
        # Create tree widget
        self.tree = QTreeWidget()
        
        # Set object name for debugging
        self.tree.setObjectName("TestStyleListenerTree")
        
        # Apply centralized styling to ensure consistent appearance
        setup_tree_for_structure_editing(self.tree)
        
        # Add a root item
        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, "Template Root")
        root_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
        root_item.setData(0, Qt.UserRole, {"type": "folder"})
        root_item.setFlags(root_item.flags() | Qt.ItemIsEditable)
        
        # Expand root
        self.tree.expandItem(root_item)
        
        tree_layout.addWidget(self.tree)
        
        # Add buttons for testing
        button_layout = QHBoxLayout()
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.add_folder)
        button_layout.addWidget(add_folder_btn)
        
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self.add_file)
        button_layout.addWidget(add_file_btn)
        
        generate_report_btn = QPushButton("Generate Style Report")
        generate_report_btn.clicked.connect(self.generate_report)
        button_layout.addWidget(generate_report_btn)
        
        tree_layout.addLayout(button_layout)
        splitter.addWidget(tree_container)
        
        # Right side - Log output
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        
        log_label = QLabel("Style Debug Log:")
        log_label.setStyleSheet("font-weight: bold;")
        log_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: monospace;")
        log_layout.addWidget(self.log_text)
        
        splitter.addWidget(log_container)
        
        # Set splitter proportions
        splitter.setSizes([400, 800])
        
        # Attach style debugger
        self.style_debugger = StyleDebugger(self.tree)
        self.log("Style debugger attached to tree widget")
        
        # Install event filter for additional event tracking
        self.tree.viewport().installEventFilter(self)
        self.tree.installEventFilter(self)
        
        # Write initial report
        self.generate_report()
    
    def log(self, message):
        """Add a log message to the log text area"""
        self.log_text.append(message)
    
    def add_folder(self):
        """Add a test folder to the tree"""
        selected_items = self.tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.tree.topLevelItem(0)
        
        # Create a new folder item
        folder_item = QTreeWidgetItem(parent_item)
        folder_item.setText(0, "New Folder")
        folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
        folder_item.setData(0, Qt.UserRole, {"type": "folder"})
        folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
        
        # Expand parent to show new item
        parent_item.setExpanded(True)
        
        # Select the new item
        self.tree.clearSelection()
        folder_item.setSelected(True)
        
        self.log(f"Added new folder item: {folder_item.text(0)}")
        
        # Analyze the item styling
        self.analyze_item_styling(folder_item)
    
    def add_file(self):
        """Add a test file to the tree"""
        selected_items = self.tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.tree.topLevelItem(0)
        
        # Create a new file item
        file_item = QTreeWidgetItem(parent_item)
        file_item.setText(0, "new_file.txt")
        file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
        file_item.setData(0, Qt.UserRole, {"type": "file", "source_path": ""})
        file_item.setFlags(file_item.flags() | Qt.ItemIsEditable)
        
        # Expand parent to show new item
        parent_item.setExpanded(True)
        
        # Select the new item
        self.tree.clearSelection()
        file_item.setSelected(True)
        
        self.log(f"Added new file item: {file_item.text(0)}")
        
        # Analyze the item styling
        self.analyze_item_styling(file_item)
    
    def eventFilter(self, obj, event):
        """Filter events to track hover and selection events"""
        if obj == self.tree.viewport():
            if event.type() == QEvent.MouseMove:
                item = self.tree.itemAt(event.pos())
                if item:
                    self.log(f"Mouse over item: {item.text(0)}")
            
            elif event.type() == QEvent.MouseButtonPress:
                item = self.tree.itemAt(event.pos())
                if item:
                    self.log(f"Clicked on item: {item.text(0)}")
                    self.analyze_item_styling(item)
        
        if obj == self.tree:
            if event.type() == QEvent.StyleChange:
                self.log("Tree style changed")
            
            # Track when items are being edited
            elif event.type() == QEvent.FocusIn:
                self.log("Tree received focus")
                for i in range(self.tree.topLevelItemCount()):
                    item = self.tree.topLevelItem(i)
                    self.check_editing_status(item)
            
            elif event.type() == QEvent.FocusOut:
                self.log("Tree lost focus")
        
        return super().eventFilter(obj, event)
    
    def check_editing_status(self, item):
        """Recursively check if any item is being edited"""
        if self.tree.isPersistentEditorOpen(item, 0):
            self.log(f"Item is being edited: {item.text(0)}")
        
        for i in range(item.childCount()):
            self.check_editing_status(item.child(i))
    
    def analyze_item_styling(self, item):
        """Analyze the styling of a specific item"""
        self.log(f"\n=== ITEM STYLING ANALYSIS ===")
        self.log(f"Item text: {item.text(0)}")
        self.log(f"Item flags: {item.flags()}")
        self.log(f"Is editable: {bool(item.flags() & Qt.ItemIsEditable)}")
        self.log(f"Is selected: {item.isSelected()}")
        
        # Get background and foreground colors
        bg_color = item.background(0).color()
        fg_color = item.foreground(0).color()
        self.log(f"Background color: {bg_color.name()} (alpha: {bg_color.alpha()})")
        self.log(f"Foreground color: {fg_color.name()} (alpha: {fg_color.alpha()})")
        
        # Check if the item has its own style sheet
        self.log(f"Tree style sheet contains:")
        style = self.tree.styleSheet()
        self.log(f"- Border in default state: {'border: none' in style}")
        self.log(f"- Hover state styling: {'QTreeWidget::item:hover' in style}")
        self.log(f"- Selected state styling: {'QTreeWidget::item:selected' in style}")
    
    def generate_report(self):
        """Generate a full style report"""
        report = create_style_report(self.tree)
        self.log("\n=== FULL STYLE REPORT ===")
        self.log(report)
        
        # Check for any dynamic styles that might be applied
        self.log("\n=== DYNAMIC STYLE CHECK ===")
        
        # Check if selection styling is properly applied
        selected_items = self.tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            self.log(f"Selected item: {item.text(0)}")
            self.analyze_item_styling(item)
        else:
            self.log("No items are currently selected")
        
        # Validate there are no borders on any items
        self.check_all_items_for_borders(self.tree.topLevelItem(0))
    
    def check_all_items_for_borders(self, item, depth=0):
        """Recursively check all items for unwanted borders"""
        if depth == 0:
            self.log("\n=== CHECKING ALL ITEMS FOR BORDERS ===")
        
        # We can't directly access the rendered style, but we can check
        # if any item has custom styles that might override our tree styles
        indent = "  " * depth
        self.log(f"{indent}Item: {item.text(0)}")
        
        # Check children recursively
        for i in range(item.childCount()):
            self.check_all_items_for_borders(item.child(i), depth + 1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StyleListenerWindow()
    window.show()
    sys.exit(app.exec_()) 
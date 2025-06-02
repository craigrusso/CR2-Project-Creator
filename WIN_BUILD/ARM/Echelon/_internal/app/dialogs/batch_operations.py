#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Dialog windows for handling batch operations.
"""

import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QTextEdit, QSpacerItem, 
                             QSizePolicy)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE

def show_batch_results(app, results):
    """
    Show a dialog with batch creation results.
    
    Args:
        app: The main application instance
        results: Results from batch creation
            This can be:
            - None or False: No dialog shown
            - A list of tuples: (project_name, success, path_or_error)
            - A dictionary with 'results' key containing the list of tuples
    """
    if not results:
        return
    
    # Avoid duplicating dialogs if this was already shown
    if hasattr(app, '_current_batch_dialog') and app._current_batch_dialog:
        try:
            app._current_batch_dialog.close()
        except:
            pass
        
    # Create dialog
    dialog = QDialog(app)
    dialog.setWindowTitle("Batch Project Creation Results")
    dialog.setMinimumWidth(600)
    dialog.setMinimumHeight(400)
    
    # Store reference to prevent duplication
    app._current_batch_dialog = dialog
    
    # Create layout
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(15)
    
    # Create results text area
    successful_projects = []
    total_success_count = 0
    total_count = 0
    
    # Check for dictionary format with results key (new format)
    if isinstance(results, dict) and "results" in results:
        # Get the list of results from the dictionary
        result_list = results["results"]
        
        # Check for summary information in the dictionary
        if "successful_count" in results and "total_count" in results:
            total_success_count = results["successful_count"]
            total_count = results["total_count"]
    # Handle list of tuples format
    elif isinstance(results, list):
        result_list = results
    else:
        # Unknown format - just display error
        result_list = []
    
    # Process the result list
    for result in result_list:
        if len(result) >= 3:  # Tuple with at least 3 elements
            project_name, success, path_or_message = result
            
            if success:
                # For successful creations, get the path
                if isinstance(path_or_message, dict):
                    # Path is a dictionary with project_dir key
                    path = path_or_message.get("project_dir", "Unknown path")
                else:
                    # Path is a string
                    path = path_or_message
                
                # Store successful project for opening
                successful_projects.append(path)
                total_success_count += 1
            
            total_count += 1
    
    # Create colorful summary header
    summary_frame = QFrame(dialog)
    summary_frame.setStyleSheet(f"""
        QFrame {{
            background-color: #2C4F76;
            border-radius: 8px;
            padding: 10px;
        }}
    """)
    summary_layout = QVBoxLayout(summary_frame)
    
    # Summary label with green checkmark for success
    summary_text = f"SUMMARY: {total_success_count} of {total_count} projects created successfully "
    summary_label = QLabel(summary_text + "✓")
    summary_label.setStyleSheet("""
        QLabel {
            color: white;
            font-size: 16px;
            font-weight: bold;
        }
    """)
    summary_layout.addWidget(summary_label)
    
    # If there are successful projects, show the first one's path
    if successful_projects:
        first_project = successful_projects[0]
        project_path_label = QLabel(f"Project '{os.path.basename(first_project)}' created successfully at: {first_project}")
        project_path_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
            }
        """)
        project_path_label.setWordWrap(True)
        summary_layout.addWidget(project_path_label)
    
    layout.addWidget(summary_frame)
    
    # Add detailed results text display
    results_text = ""
    
    # Process the result list again for detailed text
    for result in result_list:
        if len(result) >= 3:  # Tuple with at least 3 elements
            project_name, success, path_or_message = result
            
            if success:
                # For successful creations, get the path
                if isinstance(path_or_message, dict):
                    # Path is a dictionary with project_dir key
                    path = path_or_message.get("project_dir", "Unknown path")
                    has_warning = path_or_message.get("warning", False)
                    no_structure = path_or_message.get("no_structure", False)
                    
                    # Format success message with possible warning
                    results_text += f"✅ Project '{project_name}' created successfully at:\n   {path}\n"
                    
                    if no_structure:
                        results_text += f"   ⚠️ WARNING: Template has no structure, project created without folders\n"
                    elif has_warning:
                        results_text += f"   ⚠️ WARNING: {has_warning}\n"
                else:
                    # Path is a string
                    path = path_or_message
                    results_text += f"✅ Project '{project_name}' created successfully at:\n   {path}\n"
            else:
                # For failures, display the error message
                error_msg = path_or_message
                results_text += f"❌ Failed to create project '{project_name}':\n   {error_msg}\n"
            
            results_text += "\n"
    
    if result_list:
        # Show detailed results only if there are items to display
        results_display = QTextEdit(dialog)
        results_display.setReadOnly(True)
        results_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        results_display.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 10px;
                font-family: "Menlo", "Consolas", monospace;
                font-size: 13px;
            }
        """)
        results_display.setHtml(results_text.replace("✅", "<span style='color:#4CAF50'>✅</span>")
                                        .replace("❌", "<span style='color:#F44336'>❌</span>")
                                        .replace("⚠️", "<span style='color:#FF9800'>⚠️</span>")
                                        .replace("**", "<b>").replace("**", "</b>"))
        layout.addWidget(results_display, 1)  # Give this widget a stretch factor
    
    # Create button container with enhanced styling
    button_container = QFrame(dialog)
    button_container.setStyleSheet("""
        QFrame {
            background-color: #252525;
            border-radius: 4px;
            padding: 8px;
        }
    """)
    button_layout = QHBoxLayout(button_container)
    button_layout.setContentsMargins(10, 10, 10, 10)
    
    # Add Open Output Directory button if there were successful projects
    if successful_projects:
        open_button = QPushButton("Open Output Directory", dialog)
        open_button.setStyleSheet("""
            QPushButton {
                background-color: #2C4F76;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3A639A;
            }
            QPushButton:pressed {
                background-color: #1F3C5C;
            }
        """)
        # Add folder icon if possible
        try:
            # Set icon if we can find it
            open_button.setIcon(QIcon.fromTheme("folder-open"))
        except:
            pass
        open_button.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl.fromLocalFile(os.path.dirname(successful_projects[0]))))
        button_layout.addWidget(open_button)
    
    # Add spacer
    button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
    
    # Add Close button
    close_button = QPushButton("Close", dialog)
    close_button.setStyleSheet("""
        QPushButton {
            background-color: #444444;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #555555;
        }
        QPushButton:pressed {
            background-color: #333333;
        }
    """)
    close_button.clicked.connect(dialog.accept)
    button_layout.addWidget(close_button)
    
    layout.addWidget(button_container)
    
    # Clean up dialog when closing
    def cleanup_on_close():
        if hasattr(app, '_current_batch_dialog'):
            app._current_batch_dialog = None
    
    dialog.finished.connect(cleanup_on_close)
    
    # Show dialog
    dialog.exec()

def handle_batch_projects(app, projects):
    """Process a list of batch projects"""
    from app.core.project_operations import handle_batch_create
    
    # Convert list of project names to a string for handle_batch_create
    projects_text = "\n".join(projects)
    
    # handle_batch_create may return a boolean to indicate success/failure
    # or it may return the actual results list
    results = handle_batch_create(app, projects_text)
    
    # Only show results if it's not just a boolean success indicator
    if results and not isinstance(results, bool):
        show_batch_results(app, results)

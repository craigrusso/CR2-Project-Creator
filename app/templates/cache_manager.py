#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template Cache Manager
Provides additional cache management features for templates
"""

import os
import time
import json
from typing import Dict, List, Tuple, Set, Optional, Any, Union

from PyQt5.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QProgressBar, QCheckBox, QListWidget, QListWidgetItem,
    QGroupBox, QFrame, QApplication, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont

from app.ui.color_scheme_pyqt import colors
from app.utils.file_cache_manager import FileCacheManager


class TemplateCacheManager(QObject):
    """
    Extended cache management for templates
    Provides template-specific cache operations and UI
    """

    # Signal emitted when recache operations complete
    recache_completed = pyqtSignal(dict)
    
    def __init__(self, template_manager, parent=None):
        """
        Initialize the template cache manager
        
        Args:
            template_manager: Reference to the template manager
            parent: Parent QObject
        """
        super().__init__(parent)
        self.template_manager = template_manager
        self.file_cache_manager = template_manager.file_cache_manager if hasattr(template_manager, 'file_cache_manager') else None
        self.template_io = template_manager.template_io if hasattr(template_manager, 'template_io') else None
        
        # If we have no FileCacheManager, try to create one
        if not self.file_cache_manager:
            # Check if we can get cache_dir from paths
            cache_dir = None
            if hasattr(template_manager, 'paths') and 'cache_dir' in template_manager.paths:
                cache_dir = template_manager.paths['cache_dir']
                self.file_cache_manager = FileCacheManager(cache_dir)
                print(f"[DEBUG] Created FileCacheManager with cache_dir: {cache_dir}")
        
        # Stats tracking
        self.stats = {
            "templates_checked": 0,
            "files_checked": 0,
            "files_recached": 0,
            "files_missing_original": 0,
            "templates_missing_original": set()
        }

    def check_template_original_files(self, template_name: str) -> Tuple[bool, Dict]:
        """
        Check if a template has all its original files available
        
        Args:
            template_name: Name of the template to check
            
        Returns:
            Tuple containing:
                - bool: True if all original files exist, False otherwise
                - dict: Details about missing files
        """
        if not self.file_cache_manager:
            print(f"[ERROR] No FileCacheManager available")
            return False, {"error": "No cache manager available"}
            
        # Get all cached files for this template
        cached_files = self.file_cache_manager.get_all_cached_files(template_name)
        
        missing_files = {}
        all_originals_exist = True
        
        # Check each cached file for its original
        for file_key, file_info in cached_files.items():
            original_path = file_info.get('original_path', '')
            cached_path = file_info.get('cached_path', '')
            
            # Skip if this is an imported file
            if isinstance(original_path, str) and original_path.startswith("Imported from:"):
                continue
                
            # Check if original file exists
            if not original_path or not os.path.exists(original_path):
                all_originals_exist = False
                missing_files[file_key] = {
                    "cached_path": cached_path,
                    "original_path": original_path,
                    "file_name": os.path.basename(cached_path),
                    "folder": file_info.get('folder', '')
                }
        
        return all_originals_exist, missing_files
    
    def find_all_templates_with_missing_originals(self) -> Dict[str, Dict]:
        """
        Find all templates that have cached files without original sources
        
        Returns:
            Dict mapping template names to their missing file info
        """
        result = {}
        
        if not self.file_cache_manager or not self.template_io:
            print(f"[ERROR] Required managers not available")
            return result
            
        # Reset stats
        self.stats = {
            "templates_checked": 0,
            "files_checked": 0,
            "files_missing_original": 0,
            "templates_missing_original": set()
        }
        
        # Get all templates from template_io
        all_templates = self.template_io.templates
        self.stats["templates_checked"] = len(all_templates)
        
        # Check each template
        for template_name, template_data in all_templates.items():
            all_originals_exist, missing_files = self.check_template_original_files(template_name)
            
            if not all_originals_exist:
                result[template_name] = missing_files
                self.stats["templates_missing_original"].add(template_name)
                self.stats["files_missing_original"] += len(missing_files)
            
            # Update total file count
            cached_files = self.file_cache_manager.get_all_cached_files(template_name)
            self.stats["files_checked"] += len(cached_files)
        
        # Convert set to list for easier serialization
        self.stats["templates_missing_original"] = list(self.stats["templates_missing_original"])
        
        return result
    
    def recache_template(self, template_name: str) -> Tuple[bool, Dict]:
        """
        Recache a template by finding and caching original files again
        
        Args:
            template_name: Name of the template to recache
            
        Returns:
            Tuple containing:
                - bool: True if successful, False otherwise
                - dict: Stats about the recaching operation
        """
        if not self.file_cache_manager:
            print(f"[ERROR] No FileCacheManager available")
            return False, {"error": "No cache manager available"}
            
        # Get the template data
        template_data = None
        if self.template_io:
            template_data = self.template_io.get_template(template_name)
        
        if not template_data:
            print(f"[ERROR] Template '{template_name}' not found")
            return False, {"error": f"Template '{template_name}' not found"}
            
        # Clear the existing cache
        self.file_cache_manager.clear_template_cache(template_name)
        
        # Get cached files from template data
        files_to_cache = []
        if 'files' in template_data:
            files_to_cache = template_data['files']
        
        # Stats for this operation
        stats = {
            "files_total": len(files_to_cache),
            "files_recached": 0,
            "files_failed": 0,
            "files_missing_original": 0
        }
        
        # Recache each file
        for file_info in files_to_cache:
            original_path = file_info.get('original_path', '')
            folder_path = file_info.get('folder', '')
            
            # Skip imported files
            if isinstance(original_path, str) and original_path.startswith("Imported from:"):
                continue
                
            # Check if original file exists
            if original_path and os.path.exists(original_path):
                # Recache the file
                new_cached_path = self.file_cache_manager.cache_file(
                    file_path=original_path,
                    template_name=template_name,
                    folder_path=folder_path,
                    rename_flag=file_info.get('rename_flag', False)
                )
                
                if new_cached_path:
                    stats["files_recached"] += 1
                else:
                    stats["files_failed"] += 1
            else:
                stats["files_missing_original"] += 1
        
        return True, stats
    
    def recache_all_templates(self) -> Tuple[bool, Dict]:
        """
        Recache all templates
        
        Returns:
            Tuple containing:
                - bool: True if operation completed, False if failed to start
                - dict: Stats about the recaching operation
        """
        if not self.file_cache_manager or not self.template_io:
            print(f"[ERROR] Required managers not available")
            return False, {"error": "Required managers not available"}
            
        # Get all templates
        all_templates = self.template_io.templates
        
        # Overall stats
        stats = {
            "templates_total": len(all_templates),
            "templates_processed": 0,
            "templates_failed": 0,
            "files_recached": 0,
            "files_failed": 0,
            "files_missing_original": 0
        }
        
        # Recache each template
        for template_name in all_templates:
            success, template_stats = self.recache_template(template_name)
            
            if success:
                stats["templates_processed"] += 1
                stats["files_recached"] += template_stats["files_recached"]
                stats["files_failed"] += template_stats["files_failed"]
                stats["files_missing_original"] += template_stats["files_missing_original"]
            else:
                stats["templates_failed"] += 1
        
        # Emit completion signal 
        self.recache_completed.emit(stats)
        
        return True, stats
    
    def safe_clear_template_cache(self, template_name: str) -> Tuple[bool, Dict]:
        """
        Safely clear a template's cache by checking for original files first
        
        Args:
            template_name: Name of the template to clear cache for
            
        Returns:
            Tuple containing:
                - bool: True if cache cleared or user confirmed, False if operation canceled
                - dict: Information about the operation
        """
        if not self.file_cache_manager:
            return False, {"error": "No cache manager available"}
            
        # Check if all original files exist
        all_originals_exist, missing_files = self.check_template_original_files(template_name)
        
        # If all originals exist, we can safely clear the cache
        if all_originals_exist:
            self.file_cache_manager.clear_template_cache(template_name)
            return True, {"cleared": True, "warning_shown": False}
            
        # Some originals are missing, we need to warn the user
        num_missing = len(missing_files)
        cached_files = self.file_cache_manager.get_all_cached_files(template_name)
        num_total = len(cached_files)
        
        # Prepare a list of missing file details for the dialog
        missing_file_list = ""
        missing_count = 0
        # Limit the list to prevent excessive dialog height
        max_files_to_show = 10
        
        for _, file_info in sorted(missing_files.items(), key=lambda x: x[1].get('file_name', '')):
            if missing_count < max_files_to_show:
                file_name = file_info.get('file_name', '')
                folder = file_info.get('folder', '')
                original_path = file_info.get('original_path', '')
                display_path = f"{folder}/{file_name}" if folder else file_name
                missing_file_list += f"• {display_path} (original: {original_path})\n"
            missing_count += 1
            
        # Add a note if we didn't show all files
        if missing_count > max_files_to_show:
            missing_file_list += f"• ... and {missing_count - max_files_to_show} more files\n"
        
        # Show warning dialog with file details
        message = (
            f"Warning: {num_missing} out of {num_total} files in template '{template_name}' "
            f"have no original source files. If you clear the cache, these files will be permanently lost.\n\n"
            f"The following files will be permanently deleted:\n{missing_file_list}\n"
            f"This often happens when original files are renamed, moved, or deleted.\n\n"
            f"Do you want to proceed with clearing the cache?"
        )
        
        result = QMessageBox.warning(
            None,
            "Warning: Missing Original Files",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            # User confirmed, clear the cache
            self.file_cache_manager.clear_template_cache(template_name)
            return True, {"cleared": True, "warning_shown": True, "missing_files": missing_files}
        else:
            # User canceled
            return False, {"cleared": False, "warning_shown": True, "missing_files": missing_files}

    def safe_clear_all_caches(self) -> Tuple[bool, Dict]:
        """
        Safely clear all caches by checking for templates with missing originals first
        
        Returns:
            Tuple containing:
                - bool: True if caches cleared or user confirmed, False if operation canceled
                - dict: Information about the operation
        """
        if not self.file_cache_manager or not self.template_io:
            return False, {"error": "Required managers not available"}
            
        # Find all templates with missing originals
        templates_with_missing = self.find_all_templates_with_missing_originals()
        
        # If no templates have missing originals, we can safely clear all caches
        if not templates_with_missing:
            self.file_cache_manager.clear_all_caches()
            return True, {"cleared": True, "warning_shown": False}
            
        # Show warning dialog
        num_templates = len(templates_with_missing)
        num_files = sum(len(missing) for missing in templates_with_missing.values())
        
        # Prepare a detailed list of affected templates and files
        template_details = ""
        max_templates_to_show = 5
        max_files_per_template = 3
        
        for idx, (template_name, missing_files) in enumerate(sorted(templates_with_missing.items())):
            if idx < max_templates_to_show:
                template_details += f"\n• Template: {template_name} ({len(missing_files)} files)\n"
                
                # Show a sample of files for this template
                file_count = 0
                for _, file_info in sorted(missing_files.items(), key=lambda x: x[1].get('file_name', ''))[:max_files_per_template]:
                    file_name = file_info.get('file_name', '')
                    folder = file_info.get('folder', '')
                    display_path = f"{folder}/{file_name}" if folder else file_name
                    template_details += f"  - {display_path}\n"
                    file_count += 1
                    
                # Note if there are more files not shown
                if len(missing_files) > max_files_per_template:
                    template_details += f"  - ... and {len(missing_files) - max_files_per_template} more files\n"
        
        # Note if there are more templates not shown
        if num_templates > max_templates_to_show:
            template_details += f"\n• ... and {num_templates - max_templates_to_show} more templates\n"
        
        message = (
            f"Warning: {num_templates} templates have a total of {num_files} cached files "
            f"without original source files. If you clear all caches, these files will be permanently lost.\n\n"
            f"Affected templates and files:{template_details}\n"
            f"This often happens when original files are renamed, moved, or deleted.\n\n"
            f"Do you want to proceed with clearing all caches?"
        )
        
        result = QMessageBox.warning(
            None,
            "Warning: Missing Original Files",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            # User confirmed, clear all caches
            self.file_cache_manager.clear_all_caches()
            return True, {"cleared": True, "warning_shown": True, "templates_with_missing": templates_with_missing}
        else:
            # User canceled
            return False, {"cleared": False, "warning_shown": True, "templates_with_missing": templates_with_missing}


class RecacheProgressDialog(QDialog):
    """Dialog to show recaching progress"""
    
    def __init__(self, template_cache_manager, templates_to_recache=None, parent=None):
        """
        Initialize the recache progress dialog
        
        Args:
            template_cache_manager: Reference to the template cache manager
            templates_to_recache: List of template names to recache. If None, recache all.
            parent: Parent widget
        """
        super().__init__(parent)
        self.template_cache_manager = template_cache_manager
        self.templates_to_recache = templates_to_recache
        self.is_all_templates = templates_to_recache is None
        
        self.setWindowTitle("Recaching Templates")
        self.setMinimumWidth(450)
        self.setMinimumHeight(200)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Info label
        if self.is_all_templates:
            self.info_label = QLabel("Recaching all templates...")
        else:
            template_names = ", ".join(templates_to_recache)
            self.info_label = QLabel(f"Recaching templates: {template_names}")
        layout.addWidget(self.info_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Starting...")
        layout.addWidget(self.status_label)
        
        # Results frame (hidden initially)
        self.results_frame = QFrame()
        self.results_frame.setVisible(False)
        results_layout = QVBoxLayout(self.results_frame)
        
        self.results_label = QLabel("Recaching complete")
        results_layout.addWidget(self.results_label)
        
        # Stats labels
        self.templates_processed_label = QLabel("Templates processed: 0")
        self.files_recached_label = QLabel("Files recached: 0")
        self.files_failed_label = QLabel("Files failed: 0")
        self.files_missing_label = QLabel("Files with missing originals: 0")
        
        results_layout.addWidget(self.templates_processed_label)
        results_layout.addWidget(self.files_recached_label)
        results_layout.addWidget(self.files_failed_label)
        results_layout.addWidget(self.files_missing_label)
        
        layout.addWidget(self.results_frame)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        template_cache_manager.recache_completed.connect(self.on_recache_completed)
        
        # Use timer to start operation after dialog is shown
        QTimer.singleShot(100, self.start_recaching)
    
    def start_recaching(self):
        """Start the recaching operation"""
        self.status_label.setText("Recaching in progress...")
        
        # Initialize progress bar animation
        self.progress_value = 0
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress_animation)
        self.progress_timer.start(50)
        
        # Start the actual recaching operation
        if self.is_all_templates:
            # Recache all templates
            QTimer.singleShot(0, self.template_cache_manager.recache_all_templates)
        elif self.templates_to_recache:
            # Recache specific templates
            def recache_selected():
                total_stats = {
                    "templates_total": len(self.templates_to_recache),
                    "templates_processed": 0,
                    "templates_failed": 0,
                    "files_recached": 0,
                    "files_failed": 0,
                    "files_missing_original": 0
                }
                
                for template_name in self.templates_to_recache:
                    success, stats = self.template_cache_manager.recache_template(template_name)
                    
                    if success:
                        total_stats["templates_processed"] += 1
                        total_stats["files_recached"] += stats.get("files_recached", 0)
                        total_stats["files_failed"] += stats.get("files_failed", 0)
                        total_stats["files_missing_original"] += stats.get("files_missing_original", 0)
                    else:
                        total_stats["templates_failed"] += 1
                
                # Emit completion signal with aggregated stats
                self.template_cache_manager.recache_completed.emit(total_stats)
            
            QTimer.singleShot(0, recache_selected)
    
    def update_progress_animation(self):
        """Update the progress bar animation"""
        self.progress_value = (self.progress_value + 1) % 101
        self.progress_bar.setValue(self.progress_value)
    
    def on_recache_completed(self, stats):
        """Handle recache completion"""
        # Stop progress animation
        if hasattr(self, 'progress_timer') and self.progress_timer.isActive():
            self.progress_timer.stop()
        
        # Set progress to 100%
        self.progress_bar.setValue(100)
        
        # Update status
        self.status_label.setText("Recaching complete")
        
        # Update results
        self.templates_processed_label.setText(f"Templates processed: {stats.get('templates_processed', 0)}/{stats.get('templates_total', 0)}")
        self.files_recached_label.setText(f"Files recached: {stats.get('files_recached', 0)}")
        self.files_failed_label.setText(f"Files failed: {stats.get('files_failed', 0)}")
        self.files_missing_label.setText(f"Files with missing originals: {stats.get('files_missing_original', 0)}")
        
        # Show results frame
        self.results_frame.setVisible(True)
        
        # Change buttons
        self.cancel_button.setVisible(False)
        self.close_button.setText("Close")
        
        # Adjust size
        self.adjustSize()


class MissingOriginalsDialog(QDialog):
    """Dialog to show templates with missing original files"""
    
    def __init__(self, template_cache_manager, templates_with_missing, parent=None):
        """
        Initialize the missing originals dialog
        
        Args:
            template_cache_manager: Reference to the template cache manager
            templates_with_missing: Dict mapping template names to their missing file info
            parent: Parent widget
        """
        super().__init__(parent)
        self.template_cache_manager = template_cache_manager
        self.templates_with_missing = templates_with_missing
        
        self.setWindowTitle("Templates with Missing Original Files")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Info label
        num_templates = len(templates_with_missing)
        num_files = sum(len(missing) for missing in templates_with_missing.values())
        self.info_label = QLabel(
            f"{num_templates} templates have a total of {num_files} cached files without original source files. "
            f"These files exist only in the cache."
        )
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Tree widget to show templates and their missing files
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Template / File", "Cached Path", "Original Path (Missing)"])
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree)
        
        # Populate tree
        for template_name, missing_files in templates_with_missing.items():
            template_item = QTreeWidgetItem(self.tree, [template_name])
            template_item.setExpanded(True)
            
            for file_key, file_info in missing_files.items():
                file_name = file_info.get("file_name", "")
                cached_path = file_info.get("cached_path", "")
                original_path = file_info.get("original_path", "")
                
                file_item = QTreeWidgetItem(template_item, [file_name, cached_path, original_path])
        
        # Resize columns to content
        for i in range(3):
            self.tree.resizeColumnToContents(i)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Export Report...")
        self.export_button.clicked.connect(self.export_report)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def export_report(self):
        """Export a report of missing original files"""
        # Create a formatted report
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "templates_with_missing": len(self.templates_with_missing),
                "total_missing_files": sum(len(missing) for missing in self.templates_with_missing.values())
            },
            "templates": {}
        }
        
        # Add detailed template information
        for template_name, missing_files in self.templates_with_missing.items():
            template_entry = {
                "name": template_name,
                "missing_files_count": len(missing_files),
                "missing_files": list(missing_files.values())
            }
            report["templates"][template_name] = template_entry
        
        # Save to file dialog
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Missing Originals Report",
            os.path.expanduser("~/missing_originals_report.json"),
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(report, f, indent=2)
                    
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Report successfully exported to {file_path}",
                    QMessageBox.Ok
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    f"Failed to export report: {str(e)}",
                    QMessageBox.Ok
                ) 
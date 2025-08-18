#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative
"""
File Operations Handler

Provides utilities for handling file operations in the application
"""

import os
import json
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal

# Import enhanced copy functionality - try C++ first, then Python
try:
    from app.utils.cpp_enhanced_copy import (
        CppEnhancedCopyEngine, CopyOptions, CopyStats, 
        copy_files, copy_file, copy_directory,
        CPP_ENGINE_AVAILABLE
    )
    ENHANCED_COPY_AVAILABLE = True
    print(f"✓ Enhanced copy available: C++ engine {'✓' if CPP_ENGINE_AVAILABLE else '✗'}, Python fallback ✓")
except ImportError:
    try:
        from app.utils.enhanced_file_copy import (
            EnhancedFileCopy, CopyOptions, CopyStats, 
            copy_files, copy_file, copy_directory
        )
        ENHANCED_COPY_AVAILABLE = True
        CPP_ENGINE_AVAILABLE = False
        print("✓ Enhanced copy available: Python engine only")
    except ImportError:
        ENHANCED_COPY_AVAILABLE = False
        CPP_ENGINE_AVAILABLE = False
        print("✗ Enhanced copy not available")


class FileOperationsHandler(QObject):
    """Handler for file operations with signal support"""
    
    # Signals
    file_loaded = pyqtSignal(str, object)  # file_path, content
    file_saved = pyqtSignal(str)  # file_path
    
    def __init__(self, parent=None, debug=False):
        """Initialize the file operations handler"""
        super().__init__(parent)
        self.parent = parent
        self.debug = debug
        
        # Initialize enhanced copy engine if available
        if ENHANCED_COPY_AVAILABLE:
            try:
                self.enhanced_engine = CppEnhancedCopyEngine() if CPP_ENGINE_AVAILABLE else EnhancedFileCopy()
                print(f"✓ Enhanced copy engine initialized: {'C++' if CPP_ENGINE_AVAILABLE else 'Python'}")
            except Exception as e:
                print(f"Warning: Failed to initialize enhanced copy engine: {e}")
                self.enhanced_engine = None
        else:
            self.enhanced_engine = None
    
    def load_json_file(self, file_path=None, show_dialog=True):
        """
        Load a JSON file and emit a signal with the content
        
        Args:
            file_path: Path to the file to load (optional)
            show_dialog: Whether to show a file dialog if no path is provided
            
        Returns:
            tuple: (success, content)
        """
        try:
            # If no file path and show_dialog is True, show a file dialog
            if not file_path and show_dialog:
                file_path, _ = QFileDialog.getOpenFileName(
                    self.parent,
                    "Load JSON File",
                    "",
                    "JSON Files (*.json);;All Files (*)"
                )
                
                if not file_path:
                    return False, None
            
            # if self.debug:
            #     print(f"FileOperationsHandler: Loading file from {file_path}")
            
            # Load the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            # Emit signal
            self.file_loaded.emit(file_path, content)
            
            return True, content
        except Exception as e:
            print(f"Error loading file: {e}")
            if self.parent:
                QMessageBox.warning(
                    self.parent,
                    "Error",
                    f"Failed to load file: {e}"
                )
            return False, None
    
    def save_json_file(self, data, file_path=None, show_dialog=True):
        """
        Save JSON data to a file
        
        Args:
            data: The data to save
            file_path: Path to save the file to (optional)
            show_dialog: Whether to show a file dialog if no path is provided
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # If no file path and show_dialog is True, show a file dialog
            if not file_path and show_dialog:
                file_path, _ = QFileDialog.getSaveFileName(
                    self.parent,
                    "Save JSON File",
                    "",
                    "JSON Files (*.json);;All Files (*)"
                )
                
                if not file_path:
                    return False
            
            # if self.debug:
            #     print(f"FileOperationsHandler: Saving file to {file_path}")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Save the file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Emit signal
            self.file_saved.emit(file_path)
            
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            if self.parent:
                QMessageBox.warning(
                    self.parent,
                    "Error",
                    f"Failed to save file: {e}"
                )
            return False
    
    def import_file(self, target_dir, file_path=None, show_dialog=True, use_enhanced_copy=True):
        """
        Import a file to a target directory
        
        Args:
            target_dir: Directory to import the file to
            file_path: Path of the file to import (optional)
            show_dialog: Whether to show a file dialog if no path is provided
            use_enhanced_copy: Whether to use enhanced copy engine (if available)
            
        Returns:
            tuple: (success, imported_file_path)
        """
        try:
            # If no file path and show_dialog is True, show a file dialog
            if not file_path and show_dialog:
                file_path, _ = QFileDialog.getOpenFileName(
                    self.parent,
                    "Import File",
                    "",
                    "All Files (*)"
                )
                
                if not file_path:
                    return False, None
            
            # Ensure target directory exists
            os.makedirs(target_dir, exist_ok=True)
            
            # Get the file name
            file_name = os.path.basename(file_path)
            target_path = os.path.join(target_dir, file_name)
            
            # Use enhanced copy if available and requested
            if use_enhanced_copy and ENHANCED_COPY_AVAILABLE and self.enhanced_engine:
                try:
                    stats = copy_file(file_path, target_path, verify_integrity=True)
                    if stats.copied_files > 0:
                        return True, target_path
                    else:
                        # Fallback to standard copy if enhanced copy fails
                        import shutil
                        shutil.copy2(file_path, target_path)
                        return True, target_path
                except Exception as e:
                    print(f"Enhanced copy failed, falling back to standard copy: {e}")
                    # Fallback to standard copy
                    import shutil
                    shutil.copy2(file_path, target_path)
                    return True, target_path
            else:
                # Use standard copy
                import shutil
                shutil.copy2(file_path, target_path)
                return True, target_path
            
        except Exception as e:
            print(f"Error importing file: {e}")
            if self.parent:
                QMessageBox.warning(
                    self.parent,
                    "Error",
                    f"Failed to import file: {e}"
                )
            return False, None
    
    def import_file_enhanced(self, target_dir, file_path=None, show_dialog=True, **copy_options):
        """
        Import a file using the enhanced copy engine with full options
        
        Args:
            target_dir: Directory to import the file to
            file_path: Path of the file to import (optional)
            show_dialog: Whether to show a file dialog if no path is provided
            **copy_options: Additional options for enhanced copy engine
            
        Returns:
            tuple: (success, imported_file_path, copy_stats)
        """
        if not ENHANCED_COPY_AVAILABLE:
            # Fallback to standard import
            success, imported_path = self.import_file(target_dir, file_path, show_dialog, use_enhanced_copy=False)
            return success, imported_path, None
        
        try:
            # If no file path and show_dialog is True, show a file dialog
            if not file_path and show_dialog:
                file_path, _ = QFileDialog.getOpenFileName(
                    self.parent,
                    "Import File",
                    "",
                    "All Files (*)"
                )
                
                if not file_path:
                    return False, None, None
            
            # Ensure target directory exists
            os.makedirs(target_dir, exist_ok=True)
            
            # Get the file name
            file_name = os.path.basename(file_path)
            target_path = os.path.join(target_dir, file_name)
            
            # Use enhanced copy with options
            options = CopyOptions(**copy_options)
            stats = copy_file(file_path, target_path, **options.__dict__)
            
            if stats.copied_files > 0:
                return True, target_path, stats
            else:
                return False, None, stats
            
        except Exception as e:
            print(f"Error importing file with enhanced copy: {e}")
            if self.parent:
                QMessageBox.warning(
                    self.parent,
                    "Error",
                    f"Failed to import file: {e}"
                )
            return False, None, None
    
    def copy_files_enhanced(self, source_paths, destination_paths, **copy_options):
        """
        Copy multiple files using the enhanced copy engine
        
        Args:
            source_paths: List of source file/directory paths
            destination_paths: List of destination paths
            **copy_options: Additional options for enhanced copy engine
            
        Returns:
            CopyStats: Statistics from the copy operation
        """
        if not ENHANCED_COPY_AVAILABLE:
            raise RuntimeError("Enhanced copy engine not available")
        
        try:
            options = CopyOptions(**copy_options)
            stats = copy_files(source_paths, destination_paths, **options.__dict__)
            return stats
        except Exception as e:
            print(f"Error in enhanced file copy: {e}")
            raise
    
    def test_enhanced_copy_performance(self):
        """
        Test the performance of the enhanced copy engine
        
        Returns:
            dict: Performance test results
        """
        if not ENHANCED_COPY_AVAILABLE:
            return {"error": "Enhanced copy engine not available"}
        
        try:
            # Test bandwidth
            bandwidth = self.enhanced_engine.test_bandwidth()
            
            # Test optimal parameters
            optimal_params = self.enhanced_engine.get_optimal_parameters()
            
            return {
                "engine_type": "C++" if CPP_ENGINE_AVAILABLE else "Python",
                "bandwidth_mbps": bandwidth.get("avg_speed", 0),
                "write_speed_mbps": bandwidth.get("write_speed", 0),
                "read_speed_mbps": bandwidth.get("read_speed", 0),
                "optimal_block_size": optimal_params.get("block_size", 1024 * 1024),
                "optimal_thread_count": optimal_params.get("thread_count", 4),
                "use_direct_io": optimal_params.get("use_direct_io", True),
                "large_file_threshold": optimal_params.get("large_file_threshold", 100 * 1024 * 1024)
            }
        except Exception as e:
            return {"error": f"Performance test failed: {e}"} 
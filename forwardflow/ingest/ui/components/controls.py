"""Control Section for Ingest Tab"""

import os
import time
import threading
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer

try:
    from app.ui.color_scheme_pyqt import (
        colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, DANGER_BUTTON_STYLE
    )
    STYLING_AVAILABLE = True
except ImportError as e:
    print(f"DEBUG: Failed to import centralized styles: {e}")
    raise ImportError("Centralized styles are required for the ingest tab")


class ControlSection(QWidget):
    """Control Section with exact original design"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the control buttons UI"""
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 5, 0, 10)  # Reduced margin around buttons
        
        # Start button
        self.start_btn = QPushButton("Start Transfer")
        self.start_btn.setObjectName("start_btn")
        self.start_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.start_btn.setFixedHeight(45)
        self.start_btn.setEnabled(False)
        
        # Pause button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setObjectName("pause_btn")
        self.pause_btn.setStyleSheet(BUTTON_STYLE)
        self.pause_btn.setFixedHeight(45)
        self.pause_btn.setEnabled(False)
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.setStyleSheet(DANGER_BUTTON_STYLE)
        self.cancel_btn.setFixedHeight(45)
        self.cancel_btn.setEnabled(False)
        
        layout.addWidget(self.start_btn)
        layout.addWidget(self.pause_btn)
        layout.addWidget(self.cancel_btn)
        layout.addStretch()
    
    def setup_button_handlers(self, root, source_dest_section, options_section, progress_section):
        """Setup button event handlers"""
        print("DEBUG: Setting up button handlers...")
        
        # Store references for button state checking
        self.root = root
        self.source_dest_section = source_dest_section
        self.options_section = options_section
        self.progress_section = progress_section
        
        # Connect button handlers
        self.start_btn.clicked.connect(lambda: self.on_start(root, source_dest_section, options_section))
        self.pause_btn.clicked.connect(lambda: self.on_pause(root))
        self.cancel_btn.clicked.connect(lambda: self.on_cancel(root))
        
        # Connect signals for button state checking
        source_dest_section.src_combo.currentTextChanged.connect(self.check_button_states)
        source_dest_section.dest_combo.currentTextChanged.connect(self.check_button_states)
        source_dest_section.destinations_changed.connect(self.check_button_states)
        
        # Initial button state check
        self.check_button_states()
        
        print("DEBUG: Button handlers connected")
    
    def check_button_states(self):
        """Check if buttons should be enabled based on current state"""
        try:
            source_path = self.source_dest_section.src_combo.currentText().strip()
            destinations = self.source_dest_section.get_destinations()
            
            if source_path and len(destinations) > 0:
                self.start_btn.setEnabled(True)
                print("DEBUG: Source and destinations selected, enabling start button")
            else:
                self.start_btn.setEnabled(False)
                print("DEBUG: Source or destinations not complete, disabling start button")
        except Exception as e:
            print(f"DEBUG: Error in check_button_states: {e}")
            self.start_btn.setEnabled(False)
    
    def on_start(self, root, source_dest_section, options_section):
        """Handle start button click - implement C++ engine transfer"""
        print("DEBUG: ===== START BUTTON CLICKED =====")
        print(f"DEBUG: Current job state: {getattr(root, 'current_job', 'None')}")
        print(f"DEBUG: Start button enabled: {self.start_btn.isEnabled()}")
        print(f"DEBUG: Start button text: {self.start_btn.text()}")
        
        try:
            # Get source and destinations from the source_dest_section
            source_path = source_dest_section.src_combo.currentText().strip()
            destinations = source_dest_section.get_destinations()
            
            if not source_path or not destinations:
                print("DEBUG: Source path is empty or no destinations added")
                return

            print("DEBUG: Starting ingest job...")
            
            # Generate unique job ID
            job_id = f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"DEBUG: Generated job ID: {job_id}")
            
            # Get destination paths (destinations is already a list of paths)
            dest_paths = destinations
            print(f"DEBUG: Source: {source_path}")
            print(f"DEBUG: Destinations: {dest_paths}")
            
            # Get options from options_section
            verify_mode = options_section.verify_combo.currentText()
            global_preset = options_section.preset_combo.currentText()
            per_file_concurrency = options_section.conc_slider.value()
            stream_concurrency = options_section.stream_slider.value()
            generate_report = options_section.report_checkbox.isChecked()
            
            print(f"DEBUG: Verify Mode: {verify_mode}")
            print(f"DEBUG: Global Preset: {global_preset}")
            print(f"DEBUG: Per-file concurrency: {per_file_concurrency}")
            print(f"DEBUG: Stream concurrency: {stream_concurrency}")
            print(f"DEBUG: Generate report: {generate_report}")
            
            # Import JobSpec and JobOptions
            print("DEBUG: Importing JobSpec and JobOptions...")
            try:
                from forwardflow.ingest.api.models import JobSpec, JobOptions
                print("DEBUG: JobSpec and JobOptions imported successfully")
            except ImportError as e:
                print(f"DEBUG: Failed to import JobSpec/JobOptions: {e}")
                return
            
            # Create JobSpec with UI-configured parameters
            print("DEBUG: Creating JobSpec...")
            try:
                job = JobSpec(
                    job_id=job_id,
                    source_root=source_path,
                    destination_roots=dest_paths,
                    options=JobOptions(
                        mode='FAST' if verify_mode == 'FAST' else 'BALANCED',
                        per_file_concurrency=per_file_concurrency,
                        stream_concurrency=stream_concurrency,
                        verify_algorithm='xxh64',
                        verify_mode=verify_mode,
                        preset=global_preset,
                        generate_verification_report=generate_report
                    )
                )
                print(f"DEBUG: Created JobSpec: {job}")
            except Exception as e:
                print(f"DEBUG: Failed to create JobSpec: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # Store job reference
            root.current_job = job
            print(f"DEBUG: Job stored in root.current_job: {root.current_job}")
            
            # Freeze controls
            print("DEBUG: Freezing controls...")
            self.start_btn.setEnabled(False)
            source_dest_section.src_combo.setEnabled(False)
            source_dest_section.src_btn.setEnabled(False)
            source_dest_section.dest_combo.setEnabled(False)
            options_section.verify_combo.setEnabled(False)
            options_section.preset_combo.setEnabled(False)
            options_section.conc_slider.setEnabled(False)
            options_section.stream_slider.setEnabled(False)
            options_section.report_checkbox.setEnabled(False)
            print("DEBUG: Controls frozen")
            
            # Enable pause and cancel buttons
            self.pause_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            print("DEBUG: Pause and cancel buttons enabled")
            
            # Start the job in a background thread
            print("DEBUG: Starting job in background thread...")
            print(f"DEBUG: Target function: {self._run_job_with_cpp_engine}")
            print(f"DEBUG: Target function name: {self._run_job_with_cpp_engine.__name__}")
            print(f"DEBUG: Target function type: {type(self._run_job_with_cpp_engine)}")
            print(f"DEBUG: Target function module: {self._run_job_with_cpp_engine.__module__}")
            job_thread = threading.Thread(
                target=self._run_job_with_cpp_engine,
                args=(job, root),
                daemon=True
            )
            job_thread.start()
            print("DEBUG: Job thread started")
            
        except Exception as e:
            print(f"DEBUG: Error in on_start: {e}")
            import traceback
            traceback.print_exc()
            self.reenable_controls()
    
    def _run_job_with_cpp_engine(self, job, root):
        """Run the job in a background thread with C++ engine"""
        print(f"DEBUG: ===== RUN_JOB STARTED =====")
        print(f"DEBUG: Job ID: {job.job_id}")
        print(f"DEBUG: Thread ID: {threading.current_thread().ident}")
        
        try:
            # Get the C++ engine instance with proper event sink
            print("DEBUG: Getting C++ engine instance...")
            try:
                from ..engine_manager import get_engine
                from ..cpp_event_sink import CppEventSink
                
                # Create event sink first
                event_sink = CppEventSink()
                
                # Get engine with event sink
                engine = get_engine(sink=event_sink)
                print(f"DEBUG: C++ engine retrieved: {engine}")
                
                # Store event sink reference in root for report generation
                root._cpp_event_sink = event_sink
                print("DEBUG: Event sink stored in root for report generation")
                
            except Exception as e:
                print(f"DEBUG: Failed to get C++ engine: {e}")
                raise
            
            print("DEBUG: C++ engine is being used")
            
            # Store the engine reference and job spec
            root.current_job = engine
            root.current_job_spec = job
            print("DEBUG: Engine stored in root.current_job")
            print("DEBUG: Job spec stored in root.current_job_spec")
            
            print("DEBUG: Starting engine with job...")
            try:
                # Import C++ engine module to access CopyJob class
                import sys
                import os
                
                # Add the build/lib path to sys.path if not already there
                current_dir = os.path.dirname(os.path.abspath(__file__))
                build_lib_path = os.path.join(current_dir, "..", "..", "engines", "High_perf")
                if build_lib_path not in sys.path:
                    sys.path.insert(0, build_lib_path)
                
                import enhanced_high_perf_engine as cpp_engine
                print("DEBUG: C++ engine module imported successfully")
                
                # Create CopyJob object for the C++ engine
                copy_job = cpp_engine.CopyJob()
                copy_job.source_paths = [job.source_root]
                copy_job.destination_paths = job.destination_roots
                copy_job.job_id = job.job_id
                copy_job.files_in_flight = job.options.per_file_concurrency
                copy_job.ranges_per_file = job.options.stream_concurrency
                copy_job.verify_integrity = job.options.verify_mode != 'NONE'
                copy_job.hash_algorithm = job.options.verify_algorithm
                copy_job.generate_verification_report = job.options.generate_verification_report
                
                # Set preset-specific parameters
                if job.options.preset == 'FAST':
                    copy_job.use_direct_io = True
                    copy_job.block_size = 4 * 1024 * 1024  # 4MB blocks
                elif job.options.preset == 'BALANCED':
                    copy_job.use_direct_io = True
                    copy_job.block_size = 2 * 1024 * 1024  # 2MB blocks
                else:  # STRICT
                    copy_job.use_direct_io = True
                    copy_job.block_size = 1 * 1024 * 1024  # 1MB blocks
                
                print(f"DEBUG: CopyJob created: {copy_job}")
                print(f"DEBUG: Source paths: {copy_job.source_paths}")
                print(f"DEBUG: Destination paths: {copy_job.destination_paths}")
                print(f"DEBUG: Job ID: {copy_job.job_id}")
                print(f"DEBUG: Files in flight: {copy_job.files_in_flight}")
                print(f"DEBUG: Ranges per file: {copy_job.ranges_per_file}")
                print(f"DEBUG: Verify integrity: {copy_job.verify_integrity}")
                print(f"DEBUG: Hash algorithm: {copy_job.hash_algorithm}")
                print(f"DEBUG: Generate verification report: {copy_job.generate_verification_report}")
                print(f"DEBUG: Use direct I/O: {copy_job.use_direct_io}")
                print(f"DEBUG: Block size: {copy_job.block_size}")
                
                # Start the copy operation
                print("DEBUG: Starting copy operation...")
                stats = engine.copy_files(copy_job)
                print(f"DEBUG: Copy operation completed with stats: {stats}")
                
                # Generate completion report
                self._generate_completion_report(root, "completed", stats, job)
                
            except Exception as e:
                print(f"DEBUG: Error in copy operation: {e}")
                import traceback
                traceback.print_exc()
                
                # Generate error report
                self._generate_error_report(root, str(e), job)
                raise
                
        except Exception as e:
            print(f"DEBUG: Error in run_job: {e}")
            import traceback
            traceback.print_exc()
            
            # Generate error report
            self._generate_error_report(root, str(e), job)
            
            # Re-enable controls on error
            QTimer.singleShot(0, self.reenable_controls)
    
    def _generate_completion_report(self, root, status, stats, job):
        """Generate completion report using the report generator"""
        try:
            from ...utils.report_generator import TransferReportGenerator
            
            # Create report generator
            report_gen = TransferReportGenerator()
            
            # Get stats from the C++ event sink instead of the C++ engine
            from ..cpp_event_sink import CppEventSink
            event_sink = getattr(root, '_cpp_event_sink', None)
            
            if event_sink and hasattr(event_sink, 'get_current_stats'):
                current_stats = event_sink.get_current_stats()
                total_bytes = current_stats.get('total_bytes', 0)
                copied_bytes = current_stats.get('bytes_copied', 0)
                elapsed_time = time.time() - current_stats.get('start_time', time.time()) if current_stats.get('start_time') else 0.0
            else:
                # Fallback to stats parameter
                total_bytes = getattr(stats, 'total_bytes', 0)
                copied_bytes = getattr(stats, 'copied_bytes', 0)
                elapsed_time = getattr(stats, 'duration', lambda: 0.0)()
            
            # Generate report
            if status == "completed":
                report_path = report_gen.generate_completed_report(
                    job_id=job.job_id,
                    copied_bytes=copied_bytes,
                    total_bytes=total_bytes,
                    elapsed_time=elapsed_time,
                    destinations=job.destination_roots
                )
            else:
                report_path = report_gen.generate_cancelled_report(
                    job_id=job.job_id,
                    copied_bytes=copied_bytes,
                    total_bytes=total_bytes,
                    elapsed_time=elapsed_time,
                    destinations=job.destination_roots
                )
            
            if report_path:
                print(f"DEBUG: Report generated successfully: {report_path}")
            else:
                print("DEBUG: Failed to generate report")
                
        except Exception as e:
            print(f"DEBUG: Error generating completion report: {e}")
            import traceback
            traceback.print_exc()
    
    def _generate_error_report(self, root, error_message, job):
        """Generate error report using the report generator"""
        try:
            from ...utils.report_generator import TransferReportGenerator
            
            # Create report generator
            report_gen = TransferReportGenerator()
            
            # Generate error report
            report_path = report_gen.generate_error_report(
                job_id=job.job_id,
                error_message=error_message
            )
            
            if report_path:
                print(f"DEBUG: Error report generated: {report_path}")
            else:
                print("DEBUG: Failed to generate error report")
                
        except Exception as e:
            print(f"DEBUG: Error generating error report: {e}")
            import traceback
            traceback.print_exc()
    
    def _generate_detailed_report(self, root, status, error_message, comprehensive_stats=None):
        """Generate detailed transfer report with enhanced stats from C++ engine"""
        print(f"DEBUG: Generating detailed report for status: {status}")
        print(f"DEBUG: Comprehensive stats: {comprehensive_stats}")
        
        # Import the transfer log writer at the top of the method
        from forwardflow.ingest.utils.transfer_log_writer import write_transfer_log
        import os
        import time
        
        try:
            # Get job information from root
            job_id = getattr(root, 'current_job_id', f"job_{int(time.time())}")
            source_path = getattr(root, 'source_path', "Unknown")
            
            # Get destinations from the current job instead of root.destinations
            destinations = []
            if hasattr(root, 'current_job') and root.current_job and hasattr(root.current_job, 'destination_roots'):
                destinations = root.current_job.destination_roots
                print(f"DEBUG: Got destinations from current job: {destinations}")
            else:
                # Fallback to source_dest_section if available
                if hasattr(root, 'source_dest_section') and root.source_dest_section:
                    try:
                        destinations = root.source_dest_section.get_destinations()
                        print(f"DEBUG: Got destinations from source_dest_section: {destinations}")
                    except Exception as e:
                        print(f"DEBUG: Error getting destinations from source_dest_section: {e}")
                
                if not destinations:
                    print("DEBUG: No destinations found, using fallback")
                    destinations = ["Unknown"]
            
            # Use comprehensive stats if available, otherwise fall back to basic stats
            if comprehensive_stats:
                # Use the comprehensive stats from the C++ engine
                stats = comprehensive_stats
                print(f"DEBUG: Using comprehensive stats from C++ engine: {stats}")
            else:
                # Fallback to basic stats (for backward compatibility)
                stats = {
                    "total_bytes": getattr(root, 'total_bytes', 0),
                    "copied_bytes": getattr(root, 'copied_bytes', 0),
                    "duration": getattr(root, 'elapsed_time', 0),
                    "avg_speed": getattr(root, 'avg_speed', 0),
                    "total_files": getattr(root, 'total_files', 0),
                    "completed_files": getattr(root, 'completed_files', 0),
                    "cancelled_files": getattr(root, 'cancelled_files', 0),
                    "error_files": getattr(root, 'error_files', 0),
                    "files": []  # Placeholder for individual file records
                }
                print(f"DEBUG: Using fallback basic stats: {stats}")
            
            # Write the comprehensive transfer log
            log_path = write_transfer_log(
                job_id=job_id,
                source_path=source_path,
                destinations=destinations,
                status=status,
                error_message=error_message,
                stats=stats
            )
            
            print(f"DEBUG: Transfer log written to: {log_path}")
            
            # Update UI to show report completion
            if hasattr(root, 'progress_section') and root.progress_section:
                if hasattr(root.progress_section, 'status_label'):
                    root.progress_section.status_label.setText(f"Report written: {os.path.basename(log_path)}")
            
            # Re-enable controls after successful report generation
            self.reenable_controls()
            print("DEBUG: Controls re-enabled after successful report generation")
            
        except Exception as e:
            print(f"DEBUG: Error generating detailed report: {e}")
            import traceback
            traceback.print_exc()
            
            # Re-enable controls on error
            self.reenable_controls()
    
    def on_pause(self, root):
        """Handle pause button click"""
        print("DEBUG: Pause button clicked")
        # Implementation will be added here
        pass
    
    def on_cancel(self, root):
        """Handle cancel button click - immediately kill UI and stop copy"""
        print("DEBUG: Cancel button clicked - immediately stopping transfer")
        
        try:
            # Cancel the C++ engine immediately
            if hasattr(root, 'current_job') and root.current_job:
                print("DEBUG: Cancelling C++ engine...")
                try:
                    # Call the cancel method on the C++ engine
                    if hasattr(root.current_job, 'cancel'):
                        root.current_job.cancel()
                        print("DEBUG: C++ engine cancelled successfully")
                    else:
                        print("DEBUG: C++ engine has no cancel method")
                except Exception as e:
                    print(f"DEBUG: Error cancelling C++ engine: {e}")
            
            # Show "Writing report" message in progress section
            if hasattr(root, 'progress_section'):
                try:
                    # Update progress bar to show "Writing report"
                    if hasattr(root.progress_section, 'total_progress'):
                        root.progress_section.total_progress.setFormat("Writing report...")
                        root.progress_section.total_progress.setValue(0)
                    
                    # Update status label
                    if hasattr(root.progress_section, 'status_label'):
                        root.progress_section.status_label.setText("Writing transfer log...")
                except Exception as e:
                    print(f"DEBUG: Error updating progress section: {e}")
            
            # CRITICAL FIX: Re-enable controls immediately after cancellation
            # This prevents the app from freezing
            print("DEBUG: Re-enabling controls immediately after cancellation")
            self.reenable_controls()
            
            # Write transfer log immediately (simple and working)
            try:
                print("DEBUG: Writing transfer log immediately...")
                # Use the simple working method
                self._generate_detailed_report(root, "CANCELLED", "Transfer cancelled by user")
                print("DEBUG: Transfer log written successfully")
            except Exception as e:
                print(f"DEBUG: Error writing transfer log: {e}")
                import traceback
                traceback.print_exc()
            
        except Exception as e:
            print(f"DEBUG: Error in on_cancel: {e}")
            import traceback
            traceback.print_exc()
            # Ensure controls are re-enabled even if there's an error
            self.reenable_controls()
    
    def reenable_controls(self):
        """Re-enable controls after error or completion"""
        print("DEBUG: Re-enabling controls")
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        # Re-enable other controls as needed

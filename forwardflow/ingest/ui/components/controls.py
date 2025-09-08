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
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject

try:
    from app.ui.color_scheme_pyqt import (
        colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, DANGER_BUTTON_STYLE
    )
    STYLING_AVAILABLE = True
except ImportError as e:
    print(f"DEBUG: Failed to import centralized styles: {e}")
    raise ImportError("Centralized styles are required for the ingest tab")


class TransferWorker(QObject):
    """Worker class for running transfer operations in a separate thread"""
    
    # Signals for communication with main thread
    progress_update = pyqtSignal(dict)
    transfer_completed = pyqtSignal(dict)
    transfer_failed = pyqtSignal(str)
    transfer_cancelled = pyqtSignal()
    
    def __init__(self, job, root):
        super().__init__()
        self.job = job
        self.root = root
        self.engine = None
        self.event_sink = None
        self._cancelled = False
        
    def run_transfer(self):
        """Run the transfer operation in the worker thread"""
        import threading
        print(f"DEBUG: ===== TRANSFER WORKER STARTED =====")
        print(f"DEBUG: Job ID: {self.job.job_id}")
        print(f"DEBUG: Thread ID: {threading.current_thread().ident}")
        
        try:
            # Get the Rust engine instance
            print("DEBUG: Getting engine instance...")
            try:
                from ..engine_manager import get_engine, get_engine_type
                
                # Get engine with appropriate event sink
                self.engine = get_engine()
                engine_type = get_engine_type()
                print(f"DEBUG: {engine_type} engine retrieved: {self.engine}")
                
                # Store Rust event sink reference in root for report generation
                from ..rust_event_sink import RustEventSink
                self.event_sink = RustEventSink()
                self.root._rust_event_sink = self.event_sink
                print("DEBUG: Rust event sink stored in root for report generation")
                
                # Connect Rust event sink to progress updates
                self.event_sink.progress_update.connect(self.progress_update.emit)
                print("DEBUG: Rust event sink connected to progress updates")
                
            except Exception as e:
                print(f"DEBUG: Failed to get engine: {e}")
                raise
            
            print(f"DEBUG: {engine_type} engine is being used")
            
            # Set the event sink on the engine
            if hasattr(self.engine, 'set_event_sink'):
                self.engine.set_event_sink(self.event_sink)
                print("DEBUG: Event sink set on engine")
            
            # Store the engine reference and job spec
            self.root.current_job = self.engine
            self.root.current_job_spec = self.job
            print("DEBUG: Engine stored in root.current_job")
            print("DEBUG: Job spec stored in root.current_job_spec")
            
            print("DEBUG: Starting engine with job...")
            try:
                # Create CopyJob object for Rust engine
                print("DEBUG: Creating CopyJob object for Rust engine...")
                from rust_high_perf_engine import CopyJob
                
                copy_job = CopyJob()
                copy_job.source_paths = [self.job.source_root]
                copy_job.destination_paths = self.job.destination_roots
                copy_job.job_id = self.job.job_id
                copy_job.files_in_flight = self.job.options.per_file_concurrency
                copy_job.ranges_per_file = self.job.options.stream_concurrency
                copy_job.verify_integrity = self.job.options.verify_mode != 'NONE'
                copy_job.hash_algorithm = self.job.options.verify_algorithm
                copy_job.generate_verification_report = self.job.options.generate_verification_report
                copy_job.use_direct_io = True
                copy_job.block_size = self._get_block_size_for_preset(self.job.options.preset)
                
                print(f"DEBUG: CopyJob object created for Rust engine")
                
                # Start the copy operation - this should be non-blocking
                print("DEBUG: Starting Rust copy operation...")
                
                # Start the copy operation in a separate thread to avoid blocking
                import threading
                self.copy_result = None
                self.copy_completed = False
                self.copy_thread = None
                
                def run_copy():
                    try:
                        print("DEBUG: Calling Rust engine copy_files...")
                        self.copy_result = self.engine.copy_files(copy_job)
                        self.copy_completed = True
                        print(f"DEBUG: Rust copy operation completed with stats: {self.copy_result}")
                    except Exception as e:
                        print(f"DEBUG: Error in copy operation: {e}")
                        import traceback
                        traceback.print_exc()
                        self.copy_completed = True
                        self.copy_result = {'error': str(e)}
                
                self.copy_thread = threading.Thread(target=run_copy, daemon=True)
                self.copy_thread.start()
                
                # Use a timer to periodically check for completion
                from PyQt6.QtCore import QTimer
                self.copy_timer = QTimer()
                self.copy_timer.timeout.connect(self._check_copy_progress)
                self.copy_timer.start(100)  # Check every 100ms
                
            except Exception as e:
                print(f"DEBUG: Error in copy operation: {e}")
                import traceback
                traceback.print_exc()
                self.transfer_failed.emit(str(e))
                
        except Exception as e:
            print(f"DEBUG: Critical error in transfer worker: {e}")
            import traceback
            traceback.print_exc()
            self.transfer_failed.emit(str(e))
    
    def cancel_transfer(self):
        """Cancel the current transfer operation"""
        print("DEBUG: Transfer worker received cancel request")
        self._cancelled = True
        
        # Stop the copy timer
        if hasattr(self, 'copy_timer'):
            self.copy_timer.stop()
        
        # Cancel the engine
        if self.engine and hasattr(self.engine, 'cancel'):
            try:
                self.engine.cancel()
                print("DEBUG: Engine cancelled successfully")
            except Exception as e:
                print(f"DEBUG: Error cancelling engine: {e}")
        
        # Mark as completed with cancellation
        self.copy_completed = True
        self.copy_result = {'error': 'Transfer cancelled by user'}
        
        self.transfer_cancelled.emit()
    
    def _check_copy_progress(self):
        """Check if the copy operation has completed"""
        if hasattr(self, 'copy_completed') and self.copy_completed:
            # Stop the timer
            if hasattr(self, 'copy_timer'):
                self.copy_timer.stop()
            
            # Handle completion
            if self.copy_result and 'error' not in self.copy_result:
                # Store the engine stats in root for report generation
                self.root.engine_stats = self.copy_result
                print(f"DEBUG: Engine stats stored in root: {self.copy_result}")
                
                # Emit completion signal
                self.transfer_completed.emit(self.copy_result)
            else:
                # Handle error
                error_msg = self.copy_result.get('error', 'Unknown error') if self.copy_result else 'Copy operation failed'
                print(f"DEBUG: Copy operation failed: {error_msg}")
                self.transfer_failed.emit(error_msg)
    
    def _get_block_size_for_preset(self, preset):
        """Get block size for preset"""
        preset_sizes = {
            'FAST': 1024 * 1024,      # 1MB
            'BALANCED': 4 * 1024 * 1024,  # 4MB
            'STRICT': 8 * 1024 * 1024     # 8MB
        }
        return preset_sizes.get(preset, 4 * 1024 * 1024)


class ControlSection(QWidget):
    """Control Section with exact original design"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # Transfer worker and thread
        self.transfer_worker = None
        self.transfer_thread = None
        
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
        """Handle start button click - implement Rust engine transfer"""
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
            
            # Start the job using QThread for proper UI responsiveness
            print("DEBUG: Starting job using QThread...")
            
            # Create transfer worker and thread
            self.transfer_worker = TransferWorker(job, root)
            self.transfer_thread = QThread()
            
            # Move worker to thread
            self.transfer_worker.moveToThread(self.transfer_thread)
            
            # Connect signals
            self.transfer_thread.started.connect(self.transfer_worker.run_transfer)
            self.transfer_worker.progress_update.connect(self._handle_progress_update)
            self.transfer_worker.transfer_completed.connect(self._handle_transfer_completed)
            self.transfer_worker.transfer_failed.connect(self._handle_transfer_failed)
            self.transfer_worker.transfer_cancelled.connect(self._handle_transfer_cancelled)
            
            # Connect progress updates to progress section
            if hasattr(root, 'progress_section') and root.progress_section:
                self.transfer_worker.progress_update.connect(root.progress_section.handle_progress_update)
                print("DEBUG: Progress updates connected to progress section")
            
            # Start the thread
            self.transfer_thread.start()
            print("DEBUG: Transfer thread started")
            
        except Exception as e:
            print(f"DEBUG: Error in on_start: {e}")
            import traceback
            traceback.print_exc()
            self.reenable_controls()
    
    def _handle_progress_update(self, payload):
        """Handle progress updates from transfer worker"""
        print(f"DEBUG: Progress update received: {payload}")
        # Progress updates are already connected to progress section
        # This method can be used for additional processing if needed
    
    def _handle_transfer_completed(self, stats):
        """Handle transfer completion"""
        print(f"DEBUG: Transfer completed with stats: {stats}")
        try:
            # Mark progress as completed with green styling
            if hasattr(self.root, 'progress_section') and self.root.progress_section:
                self.root.progress_section.mark_transfer_completed()
            
            # Generate completion report
            self._generate_completion_report(self.root, "completed", stats, self.transfer_worker.job)
            
            # Re-enable controls
            self.reenable_controls()
            
            # Clean up thread
            self._cleanup_transfer_thread()
            
        except Exception as e:
            print(f"DEBUG: Error handling transfer completion: {e}")
            import traceback
            traceback.print_exc()
            self.reenable_controls()
    
    def _handle_transfer_failed(self, error_message):
        """Handle transfer failure"""
        print(f"DEBUG: Transfer failed: {error_message}")
        try:
            # Generate failure report
            self._generate_completion_report(self.root, "failed", None, self.transfer_worker.job, error_message)
            
            # Re-enable controls
            self.reenable_controls()
            
            # Clean up thread
            self._cleanup_transfer_thread()
            
        except Exception as e:
            print(f"DEBUG: Error handling transfer failure: {e}")
            import traceback
            traceback.print_exc()
            self.reenable_controls()
    
    def _handle_transfer_cancelled(self):
        """Handle transfer cancellation"""
        print("DEBUG: Transfer cancelled")
        try:
            # Generate cancellation report
            self._generate_completion_report(self.root, "cancelled", None, self.transfer_worker.job)
            
            # Re-enable controls
            self.reenable_controls()
            
            # Clean up thread
            self._cleanup_transfer_thread()
            
        except Exception as e:
            print(f"DEBUG: Error handling transfer cancellation: {e}")
            import traceback
            traceback.print_exc()
            self.reenable_controls()
    
    def _cleanup_transfer_thread(self):
        """Clean up transfer thread and worker"""
        try:
            if self.transfer_thread and self.transfer_thread.isRunning():
                self.transfer_thread.quit()
                self.transfer_thread.wait(5000)  # Wait up to 5 seconds
                if self.transfer_thread.isRunning():
                    print("DEBUG: Force terminating transfer thread")
                    self.transfer_thread.terminate()
                    self.transfer_thread.wait(1000)
            
            self.transfer_worker = None
            self.transfer_thread = None
            print("DEBUG: Transfer thread cleaned up")
            
        except Exception as e:
            print(f"DEBUG: Error cleaning up transfer thread: {e}")
    
    def _run_job_with_rust_engine(self, job, root):
        """Run the job in a background thread with Rust engine"""
        import threading
        print(f"DEBUG: ===== RUN_JOB STARTED =====")
        print(f"DEBUG: Job ID: {job.job_id}")
        print(f"DEBUG: Thread ID: {threading.current_thread().ident}")
        
        try:
            # Get the Rust engine instance
            print("DEBUG: Getting engine instance...")
            try:
                from ..engine_manager import get_engine, get_engine_type
                
                # Get engine with appropriate event sink
                engine = get_engine()
                engine_type = get_engine_type()
                print(f"DEBUG: {engine_type} engine retrieved: {engine}")
                
                # Store Rust event sink reference in root for report generation
                from ..rust_event_sink import RustEventSink
                event_sink = RustEventSink()
                root._rust_event_sink = event_sink
                print("DEBUG: Rust event sink stored in root for report generation")
                
                # Connect Rust event sink to progress section for simple UI updates
                if hasattr(root, 'progress_section') and root.progress_section:
                    event_sink.progress_update.connect(root.progress_section.handle_progress_update)
                    print("DEBUG: Rust event sink connected to progress section for simple updates")
                
            except Exception as e:
                print(f"DEBUG: Failed to get engine: {e}")
                raise
            
            print(f"DEBUG: {engine_type} engine is being used")
            
            # Set the event sink on the engine
            if hasattr(engine, 'set_event_sink'):
                engine.set_event_sink(event_sink)
                print("DEBUG: Event sink set on engine")
            
            # Store the engine reference and job spec
            root.current_job = engine
            root.current_job_spec = job
            print("DEBUG: Engine stored in root.current_job")
            print("DEBUG: Job spec stored in root.current_job_spec")
            
            print("DEBUG: Starting engine with job...")
            try:
                # Create CopyJob object for Rust engine
                print("DEBUG: Creating CopyJob object for Rust engine...")
                from rust_high_perf_engine import CopyJob
                
                copy_job = CopyJob()
                copy_job.source_paths = [job.source_root]
                copy_job.destination_paths = job.destination_roots
                copy_job.job_id = job.job_id
                copy_job.files_in_flight = job.options.per_file_concurrency
                copy_job.ranges_per_file = job.options.stream_concurrency
                copy_job.verify_integrity = job.options.verify_mode != 'NONE'
                copy_job.hash_algorithm = job.options.verify_algorithm
                copy_job.generate_verification_report = job.options.generate_verification_report
                copy_job.use_direct_io = True
                copy_job.block_size = self._get_block_size_for_preset(job.options.preset)
                
                print(f"DEBUG: CopyJob object created for Rust engine")
                
                # Start the copy operation
                print("DEBUG: Starting Rust copy operation...")
                stats = engine.copy_files(copy_job)
                print(f"DEBUG: Rust copy operation completed with stats: {stats}")
                
                # Store the engine stats in root for report generation
                root.engine_stats = stats
                print(f"DEBUG: Engine stats stored in root: {stats}")
                
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
    
    def _get_block_size_for_preset(self, preset: str) -> int:
        """Get block size in bytes for the given preset"""
        if preset == 'FAST':
            return 4 * 1024 * 1024  # 4MB blocks
        elif preset == 'BALANCED':
            return 2 * 1024 * 1024  # 2MB blocks
        else:  # STRICT
            return 1 * 1024 * 1024  # 1MB blocks
    
    def _generate_completion_report(self, root, status, stats, job, error_message=None):
        """Generate completion report using the report generator"""
        try:
            from ...utils.report_generator import TransferReportGenerator
            
            # Create report generator
            report_gen = TransferReportGenerator()
            
            # Get stats from the Rust event sink
            event_sink = None
            if hasattr(root, '_rust_event_sink'):
                event_sink = root._rust_event_sink
                print("DEBUG: Using Rust event sink for report generation")
            
            if event_sink and hasattr(event_sink, 'get_progress'):
                # Get stats from Rust event sink
                current_stats = event_sink.get_progress()
                total_bytes = getattr(current_stats, 'total_bytes', 0)
                copied_bytes = getattr(current_stats, 'copied_bytes', 0)
                elapsed_time = getattr(current_stats, 'elapsed_time', 0.0)
                print(f"DEBUG: Rust event sink stats - total: {total_bytes}, copied: {copied_bytes}, elapsed: {elapsed_time}")
            else:
                # Use stats parameter from Rust engine (stats is a CopyStats object)
                total_bytes = getattr(stats, 'total_bytes', 0)
                copied_bytes = getattr(stats, 'copied_bytes', 0)
                elapsed_time = getattr(stats, 'elapsed_time', 0.0)
                print(f"DEBUG: Using Rust engine stats - total: {total_bytes}, copied: {copied_bytes}, elapsed: {elapsed_time}")
            
            # Extract file records from stats or engine
            file_records = []
            if stats and hasattr(stats, 'file_records'):
                file_records = getattr(stats, 'file_records', [])
            elif stats and hasattr(stats, 'files'):
                file_records = getattr(stats, 'files', [])
            
            # Convert file records to the format expected by the report generator
            processed_file_records = []
            for record in file_records:
                if isinstance(record, dict):
                    processed_file_records.append(record)
                else:
                    # Convert from object to dict if needed
                    processed_file_records.append({
                        'source_path': getattr(record, 'source_path', ''),
                        'dest_path': getattr(record, 'dest_path', ''),
                        'size_bytes': getattr(record, 'size_bytes', 0),
                        'status': getattr(record, 'status', 'unknown'),
                        'checksum': getattr(record, 'checksum', ''),
                        'transfer_time': getattr(record, 'transfer_time', 0.0)
                    })
            
            print(f"DEBUG: Extracted {len(processed_file_records)} file records for report")
            
            # Generate report with file records
            if status == "completed":
                report_path = report_gen.generate_completed_report(
                    job_id=job.job_id,
                    copied_bytes=copied_bytes,
                    total_bytes=total_bytes,
                    elapsed_time=elapsed_time,
                    destinations=job.destination_roots,
                    file_records=processed_file_records
                )
            else:
                report_path = report_gen.generate_cancelled_report(
                    job_id=job.job_id,
                    copied_bytes=copied_bytes,
                    total_bytes=total_bytes,
                    elapsed_time=elapsed_time,
                    destinations=job.destination_roots,
                    file_records=processed_file_records
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
        """Generate detailed transfer report with enhanced stats from Rust engine"""
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
                # Use the comprehensive stats from the engine
                stats = comprehensive_stats
                print(f"DEBUG: Using comprehensive stats from engine: {stats}")
            else:
                # Try to get stats from the current job (Rust engine stats)
                engine_stats = getattr(root, 'engine_stats', None)
                if engine_stats:
                    # Handle CopyStats object (has attributes) vs dictionary
                    if hasattr(engine_stats, 'total_bytes'):
                        # CopyStats object
                        stats = {
                            "total_bytes": getattr(engine_stats, 'total_bytes', 0),
                            "copied_bytes": getattr(engine_stats, 'copied_bytes', 0),
                            "duration": getattr(engine_stats, 'end_time', 0) - getattr(engine_stats, 'start_time', 0),
                            "avg_speed": getattr(engine_stats, 'speed_mbps', 0),
                            "total_files": getattr(engine_stats, 'total_files', 0),
                            "completed_files": getattr(engine_stats, 'copied_files', 0),
                            "cancelled_files": 0,
                            "error_files": len(getattr(engine_stats, 'errors', [])),
                            "files": getattr(engine_stats, 'file_records', [])
                        }
                    else:
                        # Dictionary
                        stats = {
                            "total_bytes": getattr(engine_stats, 'total_bytes', 0),
                            "copied_bytes": getattr(engine_stats, 'copied_bytes', 0),
                            "duration": getattr(engine_stats, 'elapsed_time', 0),
                            "avg_speed": getattr(engine_stats, 'average_speed_mbps', 0),
                            "total_files": getattr(engine_stats, 'total_files', 0),
                            "completed_files": getattr(engine_stats, 'copied_files', 0),
                            "cancelled_files": 0,
                            "error_files": len(getattr(engine_stats, 'errors', [])),
                            "files": getattr(engine_stats, 'file_records', [])
                        }
                    print(f"DEBUG: Using engine stats: {stats}")
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
                
                # CRITICAL FIX: If stats are empty, try to get them from the job spec
                if stats["total_files"] == 0 and hasattr(root, 'current_job_spec'):
                    job_spec = root.current_job_spec
                    if job_spec and hasattr(job_spec, 'source_root'):
                        try:
                            from pathlib import Path
                            source_path = Path(job_spec.source_root)
                            if source_path.exists():
                                # Count files and calculate total size
                                source_files = []
                                if source_path.is_file():
                                    source_files = [source_path]
                                elif source_path.is_dir():
                                    source_files = list(source_path.rglob('*'))
                                    source_files = [f for f in source_files if f.is_file()]
                                
                                stats["total_files"] = len(source_files)
                                stats["total_bytes"] = sum(f.stat().st_size for f in source_files)
                                print(f"DEBUG: Recalculated stats from source: {stats['total_files']} files, {stats['total_bytes']} bytes")
                        except Exception as e:
                            print(f"DEBUG: Error recalculating stats: {e}")
            
            # Write the comprehensive transfer log
            log_path = write_transfer_log(
                job_id=job_id,
                source_path=source_path,
                destinations=destinations,
                status=status,
                error_message=error_message,
                stats=stats
            )
            
            # Generate DIT-compliant verification report with file details
            if hasattr(root, 'engine_stats') and root.engine_stats:
                self._generate_dit_compliant_reports(root, job_id, source_path, destinations, status, root.engine_stats)
            
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
        """Handle cancel button click - immediately stop transfer and show writing report"""
        print("DEBUG: Cancel button clicked - immediately stopping transfer")
        
        try:
            # Show "Writing report" message in progress section immediately
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
            
            # Cancel the transfer worker if it exists
            if self.transfer_worker:
                print("DEBUG: Cancelling transfer worker...")
                try:
                    self.transfer_worker.cancel_transfer()
                    print("DEBUG: Transfer worker cancelled successfully")
                except Exception as e:
                    print(f"DEBUG: Error cancelling transfer worker: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Also try to cancel the engine directly as backup
            if hasattr(root, 'current_job') and root.current_job:
                print("DEBUG: Cancelling Rust engine directly...")
                try:
                    if hasattr(root.current_job, 'cancel'):
                        root.current_job.cancel()
                        print("DEBUG: Rust engine cancelled successfully")
                except Exception as e:
                    print(f"DEBUG: Error cancelling Rust engine: {e}")
                    import traceback
                    traceback.print_exc()
            
            # CRITICAL FIX: Re-enable controls immediately after cancellation
            # This prevents the app from freezing
            print("DEBUG: Re-enabling controls immediately after cancellation")
            self.reenable_controls()
            
            # Write transfer log with a delay to allow engine stats to be available
            try:
                print("DEBUG: Writing transfer log with delay to allow engine stats...")
                # Use a timer to delay report generation until engine stats are available
                QTimer.singleShot(1000, lambda: self._generate_detailed_report_with_progress(root, "CANCELLED", "Transfer cancelled by user"))
                print("DEBUG: Transfer log generation scheduled")
            except Exception as e:
                print(f"DEBUG: Error scheduling transfer log: {e}")
                import traceback
                traceback.print_exc()
            
        except Exception as e:
            print(f"DEBUG: Error in on_cancel: {e}")
            import traceback
            traceback.print_exc()
    
    def _generate_dit_compliant_reports(self, root, job_id, source_path, destinations, status, engine_stats):
        """Generate DIT-compliant reports in multiple formats (TXT, CSV, JSON)"""
        try:
            import os
            import json
            import csv
            from datetime import datetime
            
            # Get the first destination for report storage
            if destinations and len(destinations) > 0:
                dest_path = destinations[0]
                report_dir = os.path.join(dest_path, "_CR2_CREATIVE_REPORTS")
                os.makedirs(report_dir, exist_ok=True)
                
                # Generate timestamp for filename
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
                
                # Extract stats from engine_stats (handle both CopyStats object and dictionary)
                if hasattr(engine_stats, 'total_files'):
                    # CopyStats object
                    total_files = getattr(engine_stats, 'total_files', 0)
                    files_copied = getattr(engine_stats, 'copied_files', 0)
                    bytes_copied = getattr(engine_stats, 'copied_bytes', 0)
                    total_bytes = getattr(engine_stats, 'total_bytes', 0)
                    elapsed_time = getattr(engine_stats, 'end_time', 0) - getattr(engine_stats, 'start_time', 0)
                    avg_speed = getattr(engine_stats, 'speed_mbps', 0) * 1024 * 1024  # Convert MB/s to bytes/sec
                    errors = getattr(engine_stats, 'errors', [])
                    file_records = getattr(engine_stats, 'file_records', [])
                    engine = "Rust Engine"
                else:
                    # Dictionary
                    total_files = getattr(engine_stats, 'total_files', 0)
                    files_copied = getattr(engine_stats, 'copied_files', 0)
                    bytes_copied = getattr(engine_stats, 'copied_bytes', 0)
                    total_bytes = getattr(engine_stats, 'total_bytes', 0)
                    elapsed_time = getattr(engine_stats, 'elapsed_time', 0)
                    avg_speed = getattr(engine_stats, 'average_speed_mbps', 0)
                    errors = getattr(engine_stats, 'errors', [])
                    file_records = getattr(engine_stats, 'file_records', [])
                    engine = 'Rust Engine'
                
                verification_passed = len(errors) == 0
                
                # Create comprehensive report data
                report_data = {
                    'job_id': job_id,
                    'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': status.upper(),
                    'source': source_path,
                    'destination': dest_path,
                    'total_files': total_files,
                    'files_copied': files_copied,
                    'bytes_copied': bytes_copied,
                    'total_bytes': total_bytes,
                    'elapsed_time': elapsed_time,
                    'avg_speed': avg_speed,
                    'engine': engine,
                    'verification_passed': verification_passed,
                    'errors': errors,
                    'file_records': file_records
                }
                
                # Generate TXT report (DIT-compliant format)
                txt_filename = f"dit_verification_report_{timestamp}.txt"
                txt_path = os.path.join(report_dir, txt_filename)
                self._write_dit_txt_report(txt_path, report_data)
                
                # Generate CSV report
                csv_filename = f"dit_verification_report_{timestamp}.csv"
                csv_path = os.path.join(report_dir, csv_filename)
                self._write_dit_csv_report(csv_path, report_data)
                
                # Generate JSON report
                json_filename = f"dit_verification_report_{timestamp}.json"
                json_path = os.path.join(report_dir, json_filename)
                self._write_dit_json_report(json_path, report_data)
                
                print(f"DEBUG: DIT-compliant reports generated:")
                print(f"  TXT: {txt_path}")
                print(f"  CSV: {csv_path}")
                print(f"  JSON: {json_path}")
                
        except Exception as e:
            print(f"DEBUG: Error generating DIT-compliant reports: {e}")
            import traceback
            traceback.print_exc()
    
    def _write_dit_txt_report(self, file_path, data):
        """Write DIT-compliant TXT report"""
        with open(file_path, 'w') as f:
            f.write("ForwardFlow DIT Verification Report\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Job ID: {data['job_id']}\n")
            f.write(f"Generated: {data['generated']}\n")
            f.write(f"Status: {data['status']}\n\n")
            
            f.write("=== TRANSFER SUMMARY ===\n")
            f.write(f"Source: {data['source']}\n")
            f.write(f"Destination: {data['destination']}\n")
            f.write(f"Total Files: {data['total_files']:,}\n")
            f.write(f"Files Copied: {data['files_copied']:,}\n")
            f.write(f"Bytes Copied: {data['bytes_copied']:,}\n")
            f.write(f"Total Bytes: {data['total_bytes']:,}\n")
            f.write(f"Elapsed Time: {data['elapsed_time']:.2f} seconds\n")
            f.write(f"Average Speed: {data['avg_speed']:,.0f} bytes/sec\n")
            f.write(f"Engine: {data['engine']}\n\n")
            
            f.write("=== FILE VERIFICATION DETAILS ===\n")
            if data['file_records']:
                f.write("File-by-file verification results:\n")
                for i, record in enumerate(data['file_records'], 1):
                    f.write(f"{i:3d}. {record.get('source', 'Unknown')}\n")
                    f.write(f"     Destination: {record.get('destination', 'Unknown')}\n")
                    f.write(f"     Size: {record.get('size', 0):,} bytes\n")
                    f.write(f"     Status: {record.get('status', 'Unknown')}\n")
                    if 'error' in record:
                        f.write(f"     Error: {record['error']}\n")
                    f.write("\n")
            else:
                f.write("No individual file records available.\n\n")
            
            f.write("=== VERIFICATION RESULTS ===\n")
            f.write(f"Verification Passed: {data['verification_passed']}\n")
            f.write(f"Errors: {len(data['errors'])}\n")
            if data['errors']:
                for error in data['errors']:
                    f.write(f"  - {error}\n")
            
            f.write(f"\nReport saved to: {file_path}\n")
    
    def _write_dit_csv_report(self, file_path, data):
        """Write DIT-compliant CSV report"""
        import csv
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['ForwardFlow DIT Verification Report'])
            writer.writerow(['Job ID', data['job_id']])
            writer.writerow(['Generated', data['generated']])
            writer.writerow(['Status', data['status']])
            writer.writerow(['Source', data['source']])
            writer.writerow(['Destination', data['destination']])
            writer.writerow(['Total Files', data['total_files']])
            writer.writerow(['Files Copied', data['files_copied']])
            writer.writerow(['Bytes Copied', data['bytes_copied']])
            writer.writerow(['Total Bytes', data['total_bytes']])
            writer.writerow(['Elapsed Time', f"{data['elapsed_time']:.2f} seconds"])
            writer.writerow(['Average Speed', f"{data['avg_speed']:,.0f} bytes/sec"])
            writer.writerow(['Engine', data['engine']])
            writer.writerow(['Verification Passed', data['verification_passed']])
            writer.writerow(['Errors', len(data['errors'])])
            writer.writerow([])
            
            # Write file records
            if data['file_records']:
                writer.writerow(['File Records'])
                writer.writerow(['Source', 'Destination', 'Size (bytes)', 'Status', 'Error'])
                for record in data['file_records']:
                    writer.writerow([
                        record.get('source', 'Unknown'),
                        record.get('destination', 'Unknown'),
                        record.get('size', 0),
                        record.get('status', 'Unknown'),
                        record.get('error', '')
                    ])
    
    def _write_dit_json_report(self, file_path, data):
        """Write DIT-compliant JSON report"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _generate_detailed_report_with_progress(self, root, status, error_message):
        """Generate detailed report with progress bar updates"""
        try:
            # Update progress bar to show report generation progress
            if hasattr(root, 'progress_section'):
                try:
                    if hasattr(root.progress_section, 'total_progress'):
                        root.progress_section.total_progress.setFormat("Generating report... 25%")
                        root.progress_section.total_progress.setValue(25)
                    
                    if hasattr(root.progress_section, 'status_label'):
                        root.progress_section.status_label.setText("Generating transfer report...")
                except Exception as e:
                    print(f"DEBUG: Error updating progress section: {e}")
            
            # Generate the detailed report
            self._generate_detailed_report(root, status, error_message)
            
            # Update progress bar to show completion
            if hasattr(root, 'progress_section'):
                try:
                    if hasattr(root.progress_section, 'total_progress'):
                        root.progress_section.total_progress.setFormat("Report complete!")
                        root.progress_section.total_progress.setValue(100)
                    
                    if hasattr(root.progress_section, 'status_label'):
                        root.progress_section.status_label.setText("Transfer report generated successfully")
                    
                    # Clear the progress bar after a delay
                    QTimer.singleShot(2000, lambda: self._clear_progress_bar(root))
                except Exception as e:
                    print(f"DEBUG: Error updating progress section: {e}")
                    
        except Exception as e:
            print(f"DEBUG: Error in report generation with progress: {e}")
            import traceback
            traceback.print_exc()
    
    def _clear_progress_bar(self, root):
        """Clear the progress bar and reset status"""
        try:
            if hasattr(root, 'progress_section'):
                if hasattr(root.progress_section, 'total_progress'):
                    root.progress_section.total_progress.setFormat("Ready for next transfer")
                    root.progress_section.total_progress.setValue(0)
                
                if hasattr(root.progress_section, 'status_label'):
                    root.progress_section.status_label.setText("Ready for next transfer")
        except Exception as e:
            print(f"DEBUG: Error clearing progress bar: {e}")
            # Ensure controls are re-enabled even if there's an error
            self.reenable_controls()
    
    def reenable_controls(self):
        """Re-enable controls after error or completion"""
        print("DEBUG: Re-enabling controls")
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        
        # Clean up transfer thread if it exists
        self._cleanup_transfer_thread()
        
        # Re-enable other controls as needed

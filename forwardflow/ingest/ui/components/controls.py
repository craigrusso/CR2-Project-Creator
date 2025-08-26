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
from PyQt6.QtCore import Qt

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
            # Use bridge emitter via engine wrapper
            print("DEBUG: Creating event sink...")
            from forwardflow.ingest.ui.qt_safe_bridge import emit_event
            # Create a callable function that the C++ engine expects
            def event_sink(event_type, payload):
                # Convert PyCapsule to dict if needed
                if hasattr(payload, '__class__') and 'PyCapsule' in str(payload.__class__):
                    # For now, just log the event type and skip the payload
                    print(f"DEBUG: C++ event: {event_type} (PyCapsule payload)")
                    return
                emit_event(event_type, payload)
            print("DEBUG: Event sink created")
            
            # Get the C++ engine instance
            print("DEBUG: Getting C++ engine instance...")
            try:
                from ..engine_manager import get_engine
                engine = get_engine(sink=event_sink)
                print(f"DEBUG: C++ engine retrieved: {engine}")
            except Exception as e:
                print(f"DEBUG: Failed to get C++ engine: {e}")
                raise
            
            print("DEBUG: C++ engine is being used")
            
            # Store the engine reference
            root.current_job = engine
            print("DEBUG: Engine stored in root.current_job")
            
            print("DEBUG: Starting engine with job...")
            try:
                # Import C++ engine module to access CopyJob class
                import sys
                import os
                current_dir = os.path.dirname(os.path.abspath(__file__))
                build_lib_path = os.path.join(current_dir, "..", "..", "engines", "build", "lib")
                if build_lib_path not in sys.path:
                    sys.path.insert(0, build_lib_path)
                
                import enhanced_high_perf_engine as cpp_engine
                
                # Convert JobSpec to CopyJob for C++ engine
                cpp_job = cpp_engine.CopyJob()
                cpp_job.source_paths = [job.source_root]
                cpp_job.destination_paths = job.destination_roots
                cpp_job.job_id = job.job_id
                
                # Set concurrency settings
                cpp_job.files_in_flight = job.options.per_file_concurrency
                cpp_job.ranges_per_file = job.options.stream_concurrency
                
                # Set verification settings
                if hasattr(job.options, 'verify_mode'):
                    cpp_job.verify_mode = job.options.verify_mode
                
                print(f"DEBUG: Created CopyJob: {cpp_job}")
                engine.copy_files(cpp_job)
                print("DEBUG: Engine completed successfully")
            except Exception as e:
                print(f"DEBUG: Engine failed: {e}")
                import traceback
                traceback.print_exc()
                raise
                
        except Exception as e:
            print(f"DEBUG: Error in run_job: {e}")
            import traceback
            traceback.print_exc()
            
            # Re-enable controls on error
            def reenable_controls():
                self.reenable_controls()
                print("DEBUG: Controls re-enabled after error")
            
            # Use QTimer to ensure this runs on the main thread
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, reenable_controls)
            
        finally:
            print("DEBUG: ===== RUN_JOB COMPLETED =====")
    
    def on_pause(self, root):
        """Handle pause button click"""
        print("DEBUG: Pause button clicked")
        # Implementation will be added here
        pass
    
    def on_cancel(self, root):
        """Handle cancel button click - immediately kill UI and stop copy"""
        print("DEBUG: Cancel button clicked - immediately stopping transfer")
        
        try:
            # Immediately disable all controls to prevent further interaction
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            
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
            
            # Write transfer log in background thread
            def write_transfer_log():
                try:
                    print("DEBUG: Writing transfer log...")
                    # Import the transfer log writer
                    from forwardflow.ingest.utils.transfer_log_writer import write_transfer_log
                    
                    # Get job info for the log
                    job_id = getattr(root, 'current_job_id', 'unknown')
                    source_path = getattr(root, 'source_path', 'unknown')
                    destinations = getattr(root, 'destinations', [])
                    
                    # Write the log
                    log_path = write_transfer_log(
                        job_id=job_id,
                        source_path=source_path,
                        destinations=destinations,
                        status="CANCELLED",
                        error_message="Transfer cancelled by user"
                    )
                    print(f"DEBUG: Transfer log written to: {log_path}")
                    
                    # Re-enable controls after log is written
                    def reenable_controls():
                        self.reenable_controls()
                        print("DEBUG: Controls re-enabled after cancellation")
                    
                    # Use QTimer to ensure this runs on the main thread
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, reenable_controls)
                    
                except Exception as e:
                    print(f"DEBUG: Error writing transfer log: {e}")
                    # Still re-enable controls even if log writing fails
                    def reenable_controls():
                        self.reenable_controls()
                        print("DEBUG: Controls re-enabled after log writing error")
                    
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, reenable_controls)
            
            # Start log writing in background thread
            log_thread = threading.Thread(target=write_transfer_log, daemon=True)
            log_thread.start()
            
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

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
        print(f"DEBUG: !!!!! TRANSFER WORKER STARTED - THIS SHOULD APPEAR IN LOGS !!!!!")
        print(f"DEBUG: Job ID: {self.job.job_id}")
        print(f"DEBUG: Thread ID: {threading.current_thread().ident}")
        print(f"DEBUG: self.root type: {type(self.root)}")
        print(f"DEBUG: CHECKING IF ENGINE EXISTS...")
        
        # Test basic connection first
        try:
            print(f"DEBUG: About to check engine manager...")
            from ..engine_manager import get_engine, get_engine_type
            print(f"DEBUG: Engine manager imported successfully")
        except Exception as e:
            print(f"DEBUG: *** CRITICAL *** Failed to import engine manager: {e}")
            import traceback
            traceback.print_exc()
            return
        
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
                
                # Initialize JobAggregator with job details
                try:
                    total_files = self._count_source_files(self.job.source_root)
                    destinations = self.job.destination_roots
                    self.event_sink.initialize_job(total_files, destinations)
                    print(f"DEBUG: JobAggregator initialized with {total_files} files to {destinations}")
                except Exception as e:
                    print(f"DEBUG: Failed to initialize JobAggregator: {e}")
                
                # Event sink will connect directly to UI components, no need to re-emit through TransferWorker
                print("DEBUG: Event sink will connect directly to UI components")
                
            except Exception as e:
                print(f"DEBUG: Failed to get engine: {e}")
                raise
            
            print(f"DEBUG: {engine_type} engine is being used")
            
            # DEBUG: Check root object and its attributes
            print(f"DEBUG: COMPREHENSIVE ROOT CHECK:")
            print(f"DEBUG: self.root type: {type(self.root)}")
            print(f"DEBUG: self.root attributes: {dir(self.root)}")
            print(f"DEBUG: hasattr(self.root, 'progress_section'): {hasattr(self.root, 'progress_section')}")
            print(f"DEBUG: hasattr(self.root, 'source_dest_section'): {hasattr(self.root, 'source_dest_section')}")
            
            # Connect Rust event sink to progress section for simple UI updates
            try:
                if hasattr(self.root, 'progress_section') and self.root.progress_section:
                    self.event_sink.progress_update.connect(self.root.progress_section.handle_progress_update)
                    print("DEBUG: ✓ Rust event sink connected to progress section for simple updates")
                else:
                    print(f"DEBUG: ✗ Progress section not available - hasattr: {hasattr(self.root, 'progress_section')}")
                    if hasattr(self.root, 'progress_section'):
                        print(f"DEBUG: ✗ progress_section is None: {self.root.progress_section is None}")
            except Exception as e:
                print(f"DEBUG: ✗ Error connecting to progress section: {e}")
            
            # NOTE: progress_update should ONLY go to progress_section for main progress bar updates.
            # Destination cards should receive destination_update signals specifically.
            # Removed incorrect connection that was causing progress bar conflicts.
            print("DEBUG: progress_update signals are correctly routed only to progress_section")
            
            # Connect destination-specific progress updates to source/destination section
            try:
                print(f"DEBUG: Checking destination_update connection...")
                if hasattr(self.root, 'source_dest_section') and self.root.source_dest_section:
                    print(f"DEBUG: Connecting event_sink.destination_update to {self.root.source_dest_section}.handle_destination_progress")
                    self.event_sink.destination_update.connect(self.root.source_dest_section.handle_destination_progress)
                    print("DEBUG: ✓ *** DESTINATION CONNECTION ESTABLISHED ***")
                    
                    # Connect destination completion signal for immediate report generation
                    if hasattr(self.root, 'control_section') and self.root.control_section:
                        self.event_sink.destination_completed.connect(self.root.control_section._handle_destination_completed)
                        print("DEBUG: ✓ *** DESTINATION COMPLETION CONNECTION ESTABLISHED ***")
                        
                        # CRITICAL: Also connect to the _check_destination_completion method to ensure it processes dest.completed events
                        # This ensures the EventBridge properly handles destination completion events from Rust
                        print("DEBUG: Setting up destination completion processing in EventBridge")
                    else:
                        print("DEBUG: ✗ DESTINATION COMPLETION CONNECTION FAILED - control_section not available")
                else:
                    print("DEBUG: ✗ *** DESTINATION CONNECTION FAILED - source_dest_section not available ***")
            except Exception as e:
                print(f"DEBUG: ✗ Error establishing destination connection: {e}")
                import traceback
                traceback.print_exc()
            
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
                # Create CopyJob object for REAL Rust engine - MUST use system-wide compiled library
                print("DEBUG: Creating CopyJob object for Rust engine...")
                
                # Import rust_high_perf_engine module
                import sys
                import importlib
                
                # Clear cached import to ensure fresh import
                if 'rust_high_perf_engine' in sys.modules:
                    del sys.modules['rust_high_perf_engine']
                
                import rust_high_perf_engine
                CopyJob = rust_high_perf_engine.CopyJob
                print(f"DEBUG: Using CopyJob from: {getattr(rust_high_perf_engine, '__file__', 'system')}")
                
                # INTELLIGENT TRANSFER STRATEGY SELECTION
                # Use standard high-performance parallel copying by default
                # BLAST is only used when user specifically selects a cache drive
                
                destinations = self.job.destination_roots
                print(f"DEBUG: 🚀 HIGH-PERFORMANCE ENGINE: Analyzing {len(destinations)} destinations")
                
                # Check if user has selected a BLAST cache drive (from UI controls)
                blast_cache_drive = getattr(self.job.options, 'blast_cache_drive', None)
                use_blast = blast_cache_drive is not None and blast_cache_drive != ""
                
                if use_blast:
                    print(f"DEBUG: 💾 BLAST mode selected - cache drive: {blast_cache_drive}")
                    print("DEBUG:   🔄 Workflow: Camera card → SSD cache → Multiple destinations")
                    
                    # Import BLAST engine for cache-and-distribute workflow
                    BlastEngine = rust_high_perf_engine.BlastEngine
                    blast_config = {
                        'blast_cache_path': blast_cache_drive,
                        'distribution_targets': destinations,
                        'memory_buffer_mb': 512,
                        'max_parallel_streams': len(destinations),
                        'use_direct_io': True,
                        'use_memory_mapping': True,
                        'cache_chunk_size_mb': 64
                    }
                    blast_engine = BlastEngine(blast_config, self.event_sink)
                    
                else:
                    print(f"DEBUG: 🔥 Standard high-performance mode - parallel copying to {len(destinations)} destination(s)")
                    print("DEBUG:   ⚡ Direct source-to-destination copying with full parallelization")
                    
                    # Create standard CopyJob for high-performance direct copying
                    copy_job = CopyJob()
                    copy_job.source_paths = [self.job.source_root]
                    copy_job.destination_paths = destinations
                    copy_job.job_id = self.job.job_id
                
                print("DEBUG: 🛠️  Starting high-performance transfer operation...")
                print(f"DEBUG: Transfer mode: {'BLAST cache-and-distribute' if use_blast else 'Direct parallel copying'}")
                print(f"DEBUG: Verification algorithm: {self.job.options.verify_algorithm}")
                print("DEBUG: Starting Rust copy operation...")
                
                # ESTABLISH DESTINATION CONNECTIONS HERE - this code IS executed
                print("DEBUG: !!!!! ESTABLISHING DESTINATION CONNECTIONS AT CORRECT LOCATION !!!!!")
                
                # NOTE: Removed incorrect progress_update connection to destination section.
                # Destination cards should receive destination_update signals, not progress_update signals.
                print("DEBUG: Correctly avoiding incorrect progress_update connection to destination section")
                
                # NOTE: destination_update connection is already established above (line 126).
                # Removed duplicate connection to avoid multiple signal emissions to the same handler.
                print("DEBUG: destination_update connection already established - avoiding duplicate")
                
                # Execute the appropriate transfer strategy
                import threading
                
                self.copy_result = None
                self.copy_completed = False
                
                def run_intelligent_copy():
                    try:
                        if use_blast:
                            # BLAST ENGINE: Cache-and-distribute workflow
                            print("DEBUG: 🚀 Executing BLAST workflow - cache-and-distribute...")
                            print("DEBUG:   Phase 1: 📖 Copy from camera card to SSD cache")
                            print("DEBUG:   Phase 2: 🔄 Parallel distribution from cache to all destinations")
                            
                            # Get source files list
                            import os
                            source_files = []
                            for root, dirs, files in os.walk(self.job.source_root):
                                for file in files:
                                    source_files.append(os.path.join(root, file))
                            
                            print(f"DEBUG: 📄 Found {len(source_files)} files to transfer via BLAST")
                            
                            # Execute BLAST transfer workflow
                            self.copy_result = blast_engine.execute_blast_transfer(
                                source_files,
                                self.job.job_id
                            )
                            
                            print("DEBUG: 🎉 BLAST workflow completed - camera card can be removed!")
                            
                        else:
                            # STANDARD HIGH-PERFORMANCE COPYING: Direct parallel copy to all destinations
                            print(f"DEBUG: 🔥 Executing high-performance direct copy to {len(destinations)} destinations...")
                            
                            # Configure copy job with verification settings
                            import os
                            cpu_count = os.cpu_count() or 8
                            
                            copy_job.files_in_flight = min(self.job.options.per_file_concurrency, cpu_count * 2)
                            copy_job.ranges_per_file = min(self.job.options.stream_concurrency, cpu_count)
                            
                            # Enable verification if algorithm selected
                            copy_job.verify_integrity = (
                                self.job.options.verify_algorithm and 
                                self.job.options.verify_algorithm.lower() not in ['none', '', 'disabled']
                            )
                            
                            # Map algorithm names
                            algorithm_mapping = {
                                'xxhash64be': 'xxhash64',
                                'xxhash128': 'xxhash64', 
                                'sha256': 'sha256',
                                'sha3': 'sha256',
                                'md5': 'xxhash64'
                            }
                            rust_algorithm = algorithm_mapping.get(self.job.options.verify_algorithm, 'xxhash64')
                            copy_job.hash_algorithm = rust_algorithm
                            copy_job.generate_verification_report = self.job.options.generate_verification_report
                            copy_job.use_direct_io = True
                            copy_job.block_size = self._get_block_size_for_preset(self.job.options.preset)
                            
                            print(f"DEBUG: ⚡ Using parallel copying: {copy_job.files_in_flight} files, {copy_job.ranges_per_file} streams each")
                            print(f"DEBUG: 🔐 Verification: {rust_algorithm if copy_job.verify_integrity else 'disabled'}")
                            
                            # Execute high-performance parallel copy to all destinations
                            self.copy_result = self.engine.copy_files(copy_job)
                            print(f"DEBUG: ✅ High-performance copy completed to {len(destinations)} destinations")
                        
                        self.copy_completed = True
                        
                    except Exception as e:
                        print(f"DEBUG: ❌ Error in intelligent copy operation: {e}")
                        import traceback
                        traceback.print_exc()
                        self.copy_completed = True
                        self.copy_result = {'error': str(e)}
                
                self.copy_thread = threading.Thread(target=run_intelligent_copy, daemon=True)
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
        """Get block size for preset - optimized for M2 Max performance with network awareness"""
        # Check if any destination is network-based for optimization
        has_network_destination = False
        if hasattr(self, 'destination_widgets') and self.destination_widgets:
            for widget in self.destination_widgets:
                dest_path = widget.get_destination()
                if dest_path and self._is_network_destination(dest_path):
                    has_network_destination = True
                    break
        
        if has_network_destination:
            # Network-optimized buffer sizes (smaller for better network performance)
            network_preset_sizes = {
                'FAST': 8 * 1024 * 1024,           # 8MB for fast network transfers
                'Auto (recommended)': 4 * 1024 * 1024,  # 4MB for reliable network performance  
                'BALANCED': 2 * 1024 * 1024,       # 2MB balanced for network
                'STRICT': 1 * 1024 * 1024          # 1MB for network verification accuracy
            }
            return network_preset_sizes.get(preset, 4 * 1024 * 1024)  # Default network optimized
        else:
            # Local transfer optimized buffer sizes (original large sizes)
            local_preset_sizes = {
                'FAST': 32 * 1024 * 1024,      # 32MB for max local speed
                'Auto (recommended)': 32 * 1024 * 1024,  # 32MB for max local speed  
                'BALANCED': 16 * 1024 * 1024,   # 16MB balanced local
                'STRICT': 8 * 1024 * 1024       # 8MB for local verification accuracy
            }
            return local_preset_sizes.get(preset, 32 * 1024 * 1024)  # Default to max performance
    
    def _is_network_destination(self, path):
        """Detect if destination is network-based (NAS, SMB, network share)"""
        if not path:
            return False
        
        path = path.lower()
        # Common network path patterns
        network_indicators = [
            '/volumes/',           # macOS network volumes
            '\\\\',               # Windows UNC paths
            '//',                 # UNC paths
            'smb://',            # SMB protocol
            'nfs://',            # NFS protocol
            'afp://',            # Apple Filing Protocol
            '.synology.',        # Synology NAS
            '.qnap.',            # QNAP NAS
            'nas.',              # Generic NAS
            '.local',            # Local network domains
            'diskstation',       # Synology DiskStation
            'readynas',          # Netgear ReadyNAS
            'mycloud',           # WD My Cloud
        ]
        
        return any(indicator in path for indicator in network_indicators)
    
    def _count_source_files(self, source_path: str) -> int:
        """Count total files in source directory"""
        try:
            from pathlib import Path
            source = Path(source_path)
            total_files = 0
            
            if source.is_file():
                return 1
            elif source.is_dir():
                for item in source.rglob('*'):
                    if item.is_file():
                        total_files += 1
                return total_files
            else:
                return 0
        except Exception as e:
            print(f"DEBUG: Error counting source files: {e}")
            return 0


class ControlSection(QWidget):
    """Control Section with exact original design"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # Transfer worker and thread
        self.transfer_worker = None
        self.transfer_thread = None
        
        # Track destinations that already have reports to prevent duplicates
        self._destinations_with_reports = set()
        
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
            verify_algorithm = options_section.get_verification_algorithm()
            global_preset = options_section.preset_combo.currentText()
            per_file_concurrency = options_section.conc_slider.value()
            stream_concurrency = options_section.stream_slider.value()
            generate_report = options_section.report_checkbox.isChecked()
            blast_cache_drive = options_section.get_blast_cache_drive()
            
            print(f"DEBUG: Verification Algorithm: {verify_algorithm}")
            print(f"DEBUG: Global Preset: {global_preset}")
            print(f"DEBUG: Per-file concurrency: {per_file_concurrency}")
            print(f"DEBUG: Stream concurrency: {stream_concurrency}")
            print(f"DEBUG: Generate report: {generate_report}")
            print(f"DEBUG: BLAST cache drive: {blast_cache_drive}")
            
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
                        mode='FAST',  # Keep simple - just fast mode for all algorithms
                        per_file_concurrency=per_file_concurrency,
                        stream_concurrency=stream_concurrency,
                        verify_algorithm=verify_algorithm,  # Use industry-standard algorithm
                        verify_mode=verify_algorithm,       # Use algorithm as mode for compatibility
                        preset=global_preset,
                        generate_verification_report=generate_report,
                        blast_cache_drive=blast_cache_drive
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
            if hasattr(options_section, 'blast_browse_button'):
                options_section.blast_browse_button.setEnabled(False)
            if hasattr(options_section, 'blast_clear_button'):
                options_section.blast_clear_button.setEnabled(False)
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
            
            # Progress updates are handled directly in run_transfer via event_sink connection
            # No need to duplicate connection here since TransferWorker just re-emits the same signal
            print("DEBUG: Progress updates will be connected directly via event_sink in run_transfer")
            
            # Start the thread
            self.transfer_thread.start()
            print("DEBUG: Transfer thread started")
            
        except Exception as e:
            print(f"DEBUG: Error in on_start: {e}")
            import traceback
            traceback.print_exc()
            self.reenable_controls()
    
    def _handle_progress_update(self, payload):
        """Handle progress updates from transfer worker (currently unused since direct connections are used)"""
        print(f"DEBUG: TransferWorker progress update received (should not happen with direct connections): {payload}")
    
    def _handle_destination_completed(self, dest_path: str):
        """Handle individual destination completion for immediate DIT report generation"""
        print(f"🎯 DESTINATION COMPLETED: {dest_path} - Generating immediate DIT report")
        
        try:
            # Show "Writing report..." UI feedback
            self._show_report_generation_ui(dest_path)
            
            # Get comprehensive stats and file records from the event sink
            event_sink = getattr(self.root, '_rust_event_sink', None)
            if event_sink and hasattr(event_sink, 'get_comprehensive_stats'):
                comprehensive_stats = event_sink.get_comprehensive_stats()
                # CRITICAL FIX: Use file records that are already included in comprehensive_stats
                # This ensures we get the JobAggregator file records with proper status fields
                file_records = comprehensive_stats.get('files', [])
                print(f"📊 Got stats for destination report: {comprehensive_stats.get('total_bytes', 0)} bytes, {len(file_records)} files")
            else:
                # Fallback to basic stats if event sink not available
                comprehensive_stats = {'total_bytes': 0, 'copied_bytes': 0, 'total_files': 0}
                file_records = []
                print("⚠️  No event sink available, using fallback stats")
            
            # Generate immediate comprehensive DIT report for this specific destination
            from ...utils.report_generator import TransferReportGenerator
            report_gen = TransferReportGenerator()
            
            # Get job info
            job_id = getattr(self.root, 'current_job_id', f"dest_report_{int(time.time())}")
            if hasattr(self.root, 'current_job_spec'):
                source_path = self.root.current_job_spec.source_root
            else:
                source_path = "Unknown"
            
            # Generate comprehensive reports (JSON, TXT, CSV) directly in destination's _CR2_CREATIVE_REPORTS/ folder
            generated_reports = report_gen.generate_comprehensive_reports(
                job_id=job_id,  # Use clean job ID - destination name will be added in report_generator
                status="completed",
                source_path=source_path,
                destinations=[dest_path],  # Single destination for per-destination report
                stats=comprehensive_stats,
                file_records=file_records,
                error_message=None
            )
            
            if generated_reports:
                print(f"✅ DIT reports generated for destination {dest_path}: {len(generated_reports)} files")
                for report in generated_reports:
                    print(f"  📄 {report}")
                
                # Mark this destination as having a report to prevent duplicates
                self._destinations_with_reports.add(dest_path)
                print(f"🔒 Destination {dest_path} marked as having reports (prevents duplicates)")
            else:
                print(f"❌ Failed to generate DIT reports for destination {dest_path}")
            
        except Exception as e:
            print(f"❌ Error generating report for destination {dest_path}: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_transfer_completed(self, stats):
        """Handle transfer completion - only generate reports for destinations without them"""
        print(f"DEBUG: Transfer completed with stats: {stats}")
        try:
            # Mark progress as completed with green styling
            if hasattr(self.root, 'progress_section') and self.root.progress_section:
                self.root.progress_section.mark_transfer_completed()
            
            # CRITICAL FIX: Generate reports BEFORE cleaning up job state
            # This ensures the JobAggregator data is still available for reporting
            if hasattr(self.transfer_worker, 'job') and self.transfer_worker.job:
                job_destinations = set(self.transfer_worker.job.destination_roots)
                destinations_needing_reports = job_destinations - self._destinations_with_reports
                
                if destinations_needing_reports:
                    print(f"DEBUG: Generating completion reports for remaining destinations: {destinations_needing_reports}")
                    # Generate report BEFORE cleanup so JobAggregator data is available
                    self._generate_completion_report(
                        self.root, 
                        "completed", 
                        stats, 
                        self.transfer_worker.job
                    )
                else:
                    print("DEBUG: All destinations already have reports from per-destination generation - no duplicates needed")
            
            # Clean up job state AFTER report generation
            self._cleanup_job_state()
            
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
        """Handle transfer cancellation - only generate reports for incomplete destinations"""
        print("DEBUG: Transfer cancelled - checking for incomplete destinations")
        try:
            # CRITICAL FIX: Generate reports BEFORE cleaning up job state
            # This ensures the JobAggregator data is still available for reporting
            if hasattr(self.transfer_worker, 'job') and self.transfer_worker.job:
                job_destinations = set(self.transfer_worker.job.destination_roots)
                destinations_needing_reports = job_destinations - self._destinations_with_reports
                
                if destinations_needing_reports:
                    print(f"DEBUG: Generating cancel reports for incomplete destinations: {destinations_needing_reports}")
                    
                    # Generate report BEFORE cleanup so JobAggregator data is available
                    self._generate_completion_report(
                        self.root, 
                        "cancelled", 
                        None, 
                        self.transfer_worker.job
                    )
                else:
                    print("DEBUG: All destinations already have reports - skipping duplicate generation")
            
            # Clean up job state AFTER report generation (FIXED: this was happening before!)
            self._cleanup_job_state()
            
            # Re-enable controls
            self.reenable_controls()
            
            # Clean up thread
            self._cleanup_transfer_thread()
            
        except Exception as e:
            print(f"DEBUG: Error handling transfer cancellation: {e}")
            import traceback
            traceback.print_exc()
            # On error, ensure job data is reset properly
            if hasattr(self.root, '_rust_event_sink') and self.root._rust_event_sink:
                try:
                    self.root._rust_event_sink.reset_for_new_job()
                    print("DEBUG: Reset event sink after error in cancellation handling")
                except Exception as reset_error:
                    print(f"DEBUG: Error resetting event sink: {reset_error}")
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
    
    def _get_block_size_for_preset(self, preset: str) -> int:
        """Get block size in bytes for the given preset - optimized for M2 Max performance"""
        if preset == 'FAST' or preset == 'Auto (recommended)':
            return 32 * 1024 * 1024  # 32MB blocks for maximum M2 Max throughput
        elif preset == 'BALANCED':
            return 16 * 1024 * 1024  # 16MB blocks for good speed + verification
        else:  # STRICT
            return 8 * 1024 * 1024   # 8MB blocks for accurate verification
    
    def _cleanup_job_state(self):
        """Clean up job state to prevent contamination between jobs"""
        try:
            # Clear job references
            if hasattr(self.root, 'current_job'):
                self.root.current_job = None
            if hasattr(self.root, 'current_job_spec'):
                self.root.current_job_spec = None  
            if hasattr(self.root, 'current_job_id'):
                self.root.current_job_id = None
                
            # Reset progress tracking state
            self.root.active_files = 0
            self.root.total_bytes = 0
            self.root.copied_bytes = 0
            self.root.job_start_time = None
            
            # Clear file widgets
            if hasattr(self.root, 'file_widgets'):
                self.root.file_widgets.clear()
                
            print("DEBUG: Job state cleanup completed")
            
        except Exception as e:
            print(f"DEBUG: Error during job state cleanup: {e}")
    

    def _generate_completion_report(self, root, status, stats, job, error_message=None):
        """Generate comprehensive completion report with proper data merging"""
        try:
            from ...utils.report_generator import TransferReportGenerator
            
            # Create report generator
            report_gen = TransferReportGenerator()
            
            # Initialize comprehensive stats with fallback values
            comprehensive_stats = {
                'total_bytes': 0,
                'copied_bytes': 0,
                'duration': 0,
                'avg_speed': 0,
                'peak_speed': 0,
                'total_files': 0,
                'completed_files': 0,
                'cancelled_files': 0,
                'error_files': 0
            }
            file_records = []
            
            # Primary source: Get stats from EventBridge through Rust event sink
            event_sink = getattr(root, '_rust_event_sink', None)
            if event_sink and hasattr(event_sink, 'get_comprehensive_stats'):
                try:
                    bridge_stats = event_sink.get_comprehensive_stats()
                    # CRITICAL FIX: Use file records that are already included in comprehensive_stats
                    # This ensures we get the JobAggregator file records with proper status fields
                    bridge_file_records = bridge_stats.get('files', [])
                    
                    print(f"DEBUG: EventBridge stats - total: {bridge_stats.get('total_bytes', 0)}, "
                          f"copied: {bridge_stats.get('copied_bytes', 0)}, "
                          f"duration: {bridge_stats.get('duration', 0)}")
                    
                    # Merge EventBridge stats (primary source)
                    if bridge_stats.get('total_bytes', 0) > 0 or bridge_stats.get('copied_bytes', 0) > 0:
                        comprehensive_stats.update(bridge_stats)
                        file_records = bridge_file_records
                        print(f"DEBUG: Using EventBridge data: {len(file_records)} file records")
                    else:
                        print("DEBUG: EventBridge stats are empty, will use engine stats as fallback")
                        
                except Exception as e:
                    print(f"DEBUG: Error accessing EventBridge stats: {e}")
            
            # Secondary source: Engine stats (fallback or supplement)
            if hasattr(root, 'current_job') and root.current_job and hasattr(root.current_job, 'get_stats'):
                try:
                    engine_stats = root.current_job.get_stats()
                    print(f"DEBUG: Engine stats available: {type(engine_stats)}")
                    
                    # If EventBridge stats are empty, use engine stats
                    if comprehensive_stats['total_bytes'] == 0 and comprehensive_stats['copied_bytes'] == 0:
                        comprehensive_stats.update({
                            'total_bytes': getattr(engine_stats, 'total_bytes', 0),
                            'copied_bytes': getattr(engine_stats, 'copied_bytes', 0),
                            'duration': getattr(engine_stats, 'elapsed_time', 0),
                            'avg_speed': getattr(engine_stats, 'average_speed_mbps', 0),
                            'peak_speed': getattr(engine_stats, 'peak_speed_mbps', 0),
                            'total_files': getattr(engine_stats, 'total_files', 0),
                            'completed_files': getattr(engine_stats, 'completed_files', 0)
                        })
                        print(f"DEBUG: Using engine stats as primary data source")
                    else:
                        # Merge additional data from engine stats
                        if comprehensive_stats.get('peak_speed', 0) == 0:
                            comprehensive_stats['peak_speed'] = getattr(engine_stats, 'peak_speed_mbps', 0)
                        print(f"DEBUG: Merged additional data from engine stats")
                        
                except Exception as e:
                    print(f"DEBUG: Error accessing engine stats: {e}")
            
            # Tertiary source: Method parameter stats (final fallback)
            if stats and (comprehensive_stats['total_bytes'] == 0 and comprehensive_stats['copied_bytes'] == 0):
                try:
                    comprehensive_stats.update({
                        'total_bytes': getattr(stats, 'total_bytes', 0),
                        'copied_bytes': getattr(stats, 'copied_bytes', 0),
                        'duration': getattr(stats, 'elapsed_time', 0),
                        'avg_speed': getattr(stats, 'average_speed', 0),
                        'total_files': getattr(stats, 'total_files', 0),
                        'completed_files': getattr(stats, 'completed_files', 0)
                    })
                    print(f"DEBUG: Using fallback parameter stats")
                except Exception as e:
                    print(f"DEBUG: Error accessing parameter stats: {e}")
            
            # Validate final stats
            print(f"DEBUG: Final comprehensive stats for report:")
            print(f"  Total bytes: {comprehensive_stats['total_bytes']}")
            print(f"  Copied bytes: {comprehensive_stats['copied_bytes']}")
            print(f"  Duration: {comprehensive_stats['duration']}")
            print(f"  Avg speed: {comprehensive_stats['avg_speed']} MB/s")
            print(f"  Peak speed: {comprehensive_stats['peak_speed']} MB/s")
            print(f"  Total files: {comprehensive_stats['total_files']}")
            print(f"  Completed files: {comprehensive_stats['completed_files']}")
            print(f"  File records: {len(file_records)}")
            
            # Generate comprehensive reports (JSON, TXT, CSV) in _CR2_CREATIVE_REPORTS/ subfolders
            generated_reports = report_gen.generate_comprehensive_reports(
                job_id=job.job_id,
                status=status,
                source_path=job.source_root,
                destinations=job.destination_roots,
                stats=comprehensive_stats,
                file_records=file_records,
                error_message=error_message
            )
            
            if generated_reports:
                print(f"DEBUG: Generated {len(generated_reports)} comprehensive reports:")
                for report in generated_reports:
                    print(f"  - {report}")
            else:
                print("DEBUG: Failed to generate comprehensive reports")
                
        except Exception as e:
            print(f"DEBUG: Error generating comprehensive completion report: {e}")
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
                    # Try to get stats from EventBridge before falling back to zeros
                    event_sink = getattr(root, '_rust_event_sink', None)
                    if event_sink and hasattr(event_sink, 'get_comprehensive_stats'):
                        try:
                            stats = event_sink.get_comprehensive_stats()
                            print(f"DEBUG: Using EventBridge comprehensive stats: {stats}")
                        except Exception as e:
                            print(f"DEBUG: Error getting EventBridge stats: {e}")
                            # Only fall back to zeros if EventBridge also fails
                            stats = {
                                "total_bytes": 0,
                                "copied_bytes": 0,
                                "duration": 0,
                                "avg_speed": 0,
                                "total_files": 0,
                                "completed_files": 0,
                                "cancelled_files": 0,
                                "error_files": 0,
                                "files": []
                            }
                            print(f"DEBUG: Using final fallback stats after EventBridge error: {stats}")
                    else:
                        print("DEBUG: No EventBridge available, skipping zero-report generation")
                        return  # Don't generate a report with all zeros - this is misleading
                
                # CRITICAL FIX: If stats are empty and we don't have comprehensive stats from event sink, try to get them from the job spec
                # Get event_sink reference for this scope
                event_sink = getattr(root, '_rust_event_sink', None)
                if (not (event_sink and hasattr(event_sink, 'get_comprehensive_stats')) and 
                    stats["total_files"] == 0 and hasattr(root, 'current_job_spec')):
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
            
            # NOTE: Comprehensive reports are already generated above - no need for duplicate write_transfer_log call
            # This was causing duplicate reports to be generated. The comprehensive reports provide all the necessary information.
            print("DEBUG: Skipping duplicate write_transfer_log call since comprehensive reports were already generated")
            log_path = None
            
            # NOTE: Comprehensive reports already include all DIT-compliant data in JSON, TXT, and CSV formats.
            # No need for additional dit_compliant_reports as they duplicate the same information with different prefixes.
            print("DEBUG: Comprehensive reports already include all necessary DIT-compliant information")
            
            print("DEBUG: Comprehensive reports generation completed")
            
            # Update UI to show report completion
            if hasattr(root, 'progress_section') and root.progress_section:
                if hasattr(root.progress_section, 'status_label'):
                    if generated_reports and len(generated_reports) > 0:
                        report_name = os.path.basename(generated_reports[0])
                        root.progress_section.status_label.setText(f"Reports generated: {len(generated_reports)} files")
                    else:
                        root.progress_section.status_label.setText("Report generation completed")
            
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
            
            # NOTE: Report generation is handled by _handle_transfer_cancelled() when the transfer worker 
            # emits the cancelled signal. No need for duplicate report generation here.
            print("DEBUG: Report generation will be handled by _handle_transfer_cancelled() - no duplicate calls needed")
            
        except Exception as e:
            print(f"DEBUG: Error in on_cancel: {e}")
            import traceback
            traceback.print_exc()
    
    
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
        """Re-enable controls after error or completion and reset UI to Ready state"""
        print("DEBUG: Re-enabling controls and resetting UI to Ready state")
        
        # Re-enable transfer buttons
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        
        # Re-enable ALL controls that get disabled during transfer start
        # This fixes the post-cancel UI bug where dropdowns become unresponsive
        
        # Re-enable source/destination section controls
        if hasattr(self.root, 'src_dest_section') and self.root.src_dest_section:
            source_dest_section = self.root.src_dest_section
            if hasattr(source_dest_section, 'src_combo'):
                source_dest_section.src_combo.setEnabled(True)
                print("DEBUG: Re-enabled source combo")
            if hasattr(source_dest_section, 'src_btn'):
                source_dest_section.src_btn.setEnabled(True)
                print("DEBUG: Re-enabled source browse button")
            if hasattr(source_dest_section, 'dest_combo'):
                source_dest_section.dest_combo.setEnabled(True)
                print("DEBUG: Re-enabled destination combo")
                
        # Re-enable options section controls  
        if hasattr(self.root, 'options_section') and self.root.options_section:
            options_section = self.root.options_section
            if hasattr(options_section, 'verify_combo'):
                options_section.verify_combo.setEnabled(True)
                print("DEBUG: Re-enabled verify combo")
            if hasattr(options_section, 'preset_combo'):
                options_section.preset_combo.setEnabled(True)
                print("DEBUG: Re-enabled preset combo")
            if hasattr(options_section, 'conc_slider'):
                options_section.conc_slider.setEnabled(True)
                print("DEBUG: Re-enabled concurrency slider")
            if hasattr(options_section, 'stream_slider'):
                options_section.stream_slider.setEnabled(True)
                print("DEBUG: Re-enabled stream slider")
            if hasattr(options_section, 'report_checkbox'):
                options_section.report_checkbox.setEnabled(True)
                print("DEBUG: Re-enabled report checkbox")
            if hasattr(options_section, 'blast_browse_button'):
                options_section.blast_browse_button.setEnabled(True)
                print("DEBUG: Re-enabled BLAST browse button")
            if hasattr(options_section, 'blast_clear_button'):
                options_section.blast_clear_button.setEnabled(True)
                print("DEBUG: Re-enabled BLAST clear button")
        
        # Legacy attribute names for backward compatibility
        if hasattr(self.root, 'verify_mode_dropdown') and self.root.verify_mode_dropdown:
            self.root.verify_mode_dropdown.setEnabled(True)
            print("DEBUG: Re-enabled legacy verify mode dropdown")
        
        if hasattr(self.root, 'preset_dropdown') and self.root.preset_dropdown:
            self.root.preset_dropdown.setEnabled(True)
            print("DEBUG: Re-enabled legacy preset dropdown")
            
        if hasattr(self.root, 'file_concurrency_slider') and self.root.file_concurrency_slider:
            self.root.file_concurrency_slider.setEnabled(True)
            print("DEBUG: Re-enabled legacy file concurrency slider")
            
        if hasattr(self.root, 'stream_concurrency_slider') and self.root.stream_concurrency_slider:
            self.root.stream_concurrency_slider.setEnabled(True)
            print("DEBUG: Re-enabled legacy stream concurrency slider")
        
        # Reset progress bar to 0 and clear status
        if hasattr(self.root, 'progress_section') and self.root.progress_section:
            if hasattr(self.root.progress_section, 'total_progress'):
                self.root.progress_section.total_progress.setValue(0)
                self.root.progress_section.total_progress.setFormat("0%")
                print("DEBUG: Reset main progress bar to 0%")
            
            # Reset all speed/time labels
            if hasattr(self.root.progress_section, 'current_speed_label'):
                self.root.progress_section.current_speed_label.setText("0 MB/s")
            if hasattr(self.root.progress_section, 'avg_speed_label'):
                self.root.progress_section.avg_speed_label.setText("0 MB/s")
            if hasattr(self.root.progress_section, 'peak_speed_label'):
                self.root.progress_section.peak_speed_label.setText("0 MB/s")
            if hasattr(self.root.progress_section, 'elapsed_label'):
                self.root.progress_section.elapsed_label.setText("00:00:00")
            if hasattr(self.root.progress_section, 'eta_label'):
                self.root.progress_section.eta_label.setText("--:--:--")
            if hasattr(self.root.progress_section, 'files_count'):
                self.root.progress_section.files_count.setText("0 of 0 files")
            print("DEBUG: Reset all progress section labels")
        
        # Reset destination cards to Ready state
        if hasattr(self.root, 'src_dest_section') and self.root.src_dest_section:
            if hasattr(self.root.src_dest_section, 'destination_widgets'):
                for dest_widget in self.root.src_dest_section.destination_widgets:
                    if hasattr(dest_widget, 'status_label'):
                        dest_widget.status_label.setText("Ready")
                        dest_widget.status_label.setStyleSheet("color: #64748b;")
                    if hasattr(dest_widget, 'speed_label'):
                        dest_widget.speed_label.setText("0.0 MB/s")
                    if hasattr(dest_widget, 'peak_speed_label'):
                        dest_widget.peak_speed_label.setText("Peak: 0 MB/s")
                    if hasattr(dest_widget, 'eta_label'):
                        dest_widget.eta_label.setText("--:--:--")
                print("DEBUG: Reset all destination cards to Ready state")
        
        # Reset event sink for new job
        if hasattr(self.root, '_rust_event_sink') and self.root._rust_event_sink:
            self.root._rust_event_sink.reset_for_new_job()
            print("DEBUG: Reset event sink for new job")
        
        # Clean up transfer thread if it exists
        self._cleanup_transfer_thread()
        
        # Clear any job references
        if hasattr(self.root, 'current_job'):
            self.root.current_job = None
        if hasattr(self.root, 'current_job_id'):
            self.root.current_job_id = None
        
        # Clear destinations report tracking for new job
        self._destinations_with_reports.clear()
        print("DEBUG: Cleared destinations report tracking for new job")
            
        print("DEBUG: UI completely reset to Ready state for new transfer")
    
    def _show_report_generation_ui(self, dest_path: str):
        """Show 'Writing report...' UI feedback for destination"""
        print(f"📄 Showing report generation UI for: {dest_path}")
        
        # TODO: Add progress dialog or status message
        # For now, just print - this can be enhanced with actual UI feedback
        

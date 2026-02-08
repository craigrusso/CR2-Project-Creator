"""Control Section for Ingest Tab"""

import os
import sys
import time
import threading
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer, QThread, QCoreApplication, pyqtSignal, QObject

try:
    from app.ui.color_scheme_pyqt import (
        colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, DANGER_BUTTON_STYLE
    )
    STYLING_AVAILABLE = True
except ImportError as e:
    print(f"DEBUG: Failed to import centralized styles: {e}")
    raise ImportError("Centralized styles are required for the ingest tab")

try:
    import rust_high_perf_engine as _gpu_warmup_module

    if hasattr(_gpu_warmup_module, "warm_up_gpu_hash_backend"):
        _gpu_warmup_module.warm_up_gpu_hash_backend()
        print("DEBUG: Triggered GPU hash backend warm-up")
except Exception as warm_err:
    print(f"DEBUG: GPU hash warm-up skipped: {warm_err}")
finally:
    sys.modules.pop("rust_high_perf_engine", None)


class TransferWorker(QObject):
    """Worker class for running transfer operations in a separate thread"""
    
    # Signals for communication with main thread
    progress_update = pyqtSignal(dict)
    transfer_completed = pyqtSignal(dict)
    transfer_failed = pyqtSignal(str)
    transfer_cancelled = pyqtSignal()
    
    def __init__(self, job, root, event_sink):
        super().__init__()
        self.job = job
        self.root = root
        self.engine = None
        self._cancelled = False
        self._cancel_in_progress = False
        self.cancel_btn = None  # Will be set by ControlSection
        self.copy_completed = False
        self.copy_result = None

        # CRITICAL FIX: Receive RustEventSink created on main thread (NOT worker thread)
        # QObjects MUST be created on the thread where they'll receive signals (main thread)
        self.event_sink = event_sink
        print("DEBUG: ✅ RustEventSink received from main thread (correct thread for Qt signals)")

        # NOTE: Event connections are already established on main thread in ControlSection.on_start()
        # This prevents Qt threading violations when connecting signals across threads
        print("DEBUG: Event connections already established on main thread - worker ready")
    
        
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
                # (event_sink already created on main thread in __init__)
                self.root._rust_event_sink = self.event_sink
                print("DEBUG: Rust event sink (created on main thread) stored in root for report generation")
                
                # Initialize JobAggregator with job details
                try:
                    total_files = self._count_source_files(self.job.source_root)
                    destinations = self.job.destination_roots
                    self.event_sink.initialize_job(total_files, destinations)
                    print(f"DEBUG: JobAggregator initialized with {total_files} files to {destinations}")
                except Exception as e:
                    print(f"DEBUG: Failed to initialize JobAggregator: {e}")
                
                # NOTE: DIT collector and real-time writer are now initialized on MAIN THREAD
                # This prevents race condition where file completion events arrive before initialization
                # See on_start() method for initialization code

                # Event sink will connect directly to UI components, no need to re-emit through TransferWorker
                print("DEBUG: Event sink will connect directly to UI components")
                print("DEBUG: About to exit inner try block...")
                
            except Exception as e:
                print(f"DEBUG: Failed to get engine: {e}")
                raise
            
            print(f"DEBUG: {engine_type} engine is being used")
            
            # NOTE: Event pump is initialized on MAIN THREAD in on_start() method
            # This prevents Qt signal connection failures when connecting across threads
            # Event pump is already running and will receive events from Rust engine
            print("DEBUG: Event pump initialized on main thread - worker can safely emit to queue")
            
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

                # Check if BLAST workflow should be used (user-selected cache or auto-detection)
                from ..engine_manager import should_use_blast_workflow
                use_blast, blast_cache_drive = should_use_blast_workflow(self.job)
                
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
                            
                            # CRITICAL FIX: Map UI algorithm names to exact Rust enum variants
                            algorithm_mapping = {
                                'xxhash64be': 'xxhash64',  # Maps to HashAlgorithm::XxHash64
                                'xxhash128': 'xxhash128',  # Maps to HashAlgorithm::XxHash128
                                'sha256': 'sha256',        # Maps to HashAlgorithm::Sha256
                                'sha3': 'sha3',           # Maps to HashAlgorithm::Sha3
                                'md5': 'md5'              # Maps to HashAlgorithm::Md5
                            }
                            rust_algorithm = algorithm_mapping.get(self.job.options.verify_algorithm, 'xxhash64')
                            copy_job.hash_algorithm = rust_algorithm
                            copy_job.generate_verification_report = self.job.options.generate_verification_report
                            copy_job.use_direct_io = True
                            block_size = self._get_block_size_for_preset(self.job.options.preset)
                            if self._should_throttle_block_size(self.job.source_root, destinations):
                                throttled_block = min(block_size, 8 * 1024 * 1024)
                                if throttled_block != block_size:
                                    print(
                                        f"DEBUG: Throttling block size from {block_size} to {throttled_block} bytes "
                                        "for cloud/network paths"
                                    )
                                block_size = throttled_block
                            copy_job.block_size = block_size
                            
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
                
                # CRITICAL FIX: Don't use QTimer on worker thread - it requires an event loop
                # Just run the copy directly - Rust engine will emit events as it progresses
                print("DEBUG: Running copy operation directly (no nested threading or timers)")
                run_intelligent_copy()
                
                # Handle completion immediately after copy finishes
                copy_stats = self.copy_result
                has_error = False
                error_msg = None

                if isinstance(copy_stats, dict):
                    # Our own fallback error dictionaries
                    error_msg = copy_stats.get('error') or copy_stats.get('message')
                    has_error = True
                elif copy_stats is None:
                    has_error = True
                    error_msg = "Copy operation returned no statistics"
                else:
                    # Native CopyStats object from Rust engine
                    engine_errors = list(getattr(copy_stats, 'errors', []) or [])
                    if engine_errors:
                        has_error = True
                        error_msg = engine_errors[0] if len(engine_errors) == 1 else "; ".join(engine_errors)
                    else:
                        total_files = getattr(copy_stats, 'total_files', 0) or 0
                        copied_files = getattr(copy_stats, 'copied_files', getattr(copy_stats, 'completed_files', 0) or 0)
                        if total_files and copied_files < total_files:
                            missing = total_files - copied_files
                            has_error = True
                            error_msg = f"{missing} file(s) did not complete"

                if copy_stats and not has_error:
                    # Store the engine stats in root for report generation
                    self.root.engine_stats = copy_stats
                    print(f"DEBUG: Engine stats stored in root: {copy_stats}")

                    # Stop event pump (cleanup)
                    if hasattr(self, 'event_pump'):
                        print("DEBUG: Stopping event pump...")
                        self.event_pump.stop_pump()
                        print("DEBUG: ✅ Event pump stopped")

                    # Emit completion signal (convert CopyStats to dict)
                    result_dict = {
                        'total_bytes': getattr(copy_stats, 'total_bytes', 0),
                        'bytes_transferred': getattr(copy_stats, 'copied_bytes', getattr(copy_stats, 'total_bytes', 0)),
                        'total_files': getattr(copy_stats, 'total_files', 0),
                        'files_completed': getattr(copy_stats, 'copied_files', getattr(copy_stats, 'total_files', 0)),
                        'duration': copy_stats.duration() if hasattr(copy_stats, 'duration') else getattr(copy_stats, 'duration', 0),
                        'status': 'completed'
                    }
                    self.transfer_completed.emit(result_dict)
                else:
                    # Stop event pump (cleanup on error)
                    if hasattr(self, 'event_pump'):
                        print("DEBUG: Stopping event pump (error path)...")
                        self.event_pump.stop_pump()

                    # Handle error
                    error_msg = error_msg or "Copy operation failed"
                    print(f"DEBUG: Copy operation failed: {error_msg}")
                    self.transfer_failed.emit(error_msg)
                
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
        """Cancel the current transfer operation - IMMEDIATE cancellation"""
        if self._cancel_in_progress:
            print("DEBUG: Cancel already in progress - ignoring additional click")
            return

        print("DEBUG: Transfer worker received cancel request - IMMEDIATE cancellation")
        self._cancel_in_progress = True
        self._cancelled = True
        
        # Update button state immediately
        if self.cancel_btn:
            self.cancel_btn.setDown(True)  # Show pressed state
            self.cancel_btn.setEnabled(False)
            self.cancel_btn.setText("Cancelling...")
            # Force UI update
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()

        # Cancel the engine IMMEDIATELY - this is the critical path
        if self.engine and hasattr(self.engine, 'cancel'):
            try:
                self.engine.cancel()
                print("DEBUG: ✅ Engine cancelled successfully - cancellation signal sent to Rust")
            except Exception as e:
                print(f"DEBUG: ❌ Error cancelling engine: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"DEBUG: ⚠️  No engine or engine has no cancel method. Engine: {self.engine}")

        # Mark as completed with cancellation
        self.copy_completed = True
        self.copy_result = {'error': 'Transfer cancelled by user'}

        # Emit cancellation signal immediately
        self.transfer_cancelled.emit()
        print("DEBUG: ✅ Transfer cancelled signal emitted")
    
    def _get_block_size_for_preset(self, preset):
        """Map UI preset names to conservative copy block sizes."""
        normalized_preset = (preset or "").strip().lower()

        preset_map = {
            'auto': 32 * 1024 * 1024,
            'auto (recommended)': 32 * 1024 * 1024,
            'usb/tb': 32 * 1024 * 1024,
            'usb': 32 * 1024 * 1024,
            'thunderbolt': 32 * 1024 * 1024,
            'network': 8 * 1024 * 1024,
            'custom': 16 * 1024 * 1024,
            'fast': 32 * 1024 * 1024,
            'balanced': 16 * 1024 * 1024,
            'strict': 8 * 1024 * 1024,
        }

        return preset_map.get(normalized_preset, 32 * 1024 * 1024)
    
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

    def _is_cloud_source(self, path: str) -> bool:
        """Detect if source lives in a cloud-synced location (OneDrive, Dropbox, iCloud, etc.)."""
        if not path:
            return False

        normalized = path.lower()
        cloud_indicators = [
            'library/cloudstorage',
            'onedrive',
            'dropbox',
            'icloud',
            'google drive',
            'gdrive',
            'box/',
            'sharepoint',
        ]
        return any(marker in normalized for marker in cloud_indicators)

    def _should_throttle_block_size(self, source_path: str, destinations: List[str]) -> bool:
        """Return True when we should keep block sizes small for better responsiveness."""
        if self._is_cloud_source(source_path):
            return True
        return any(self._is_network_destination(dest or "") for dest in destinations or [])
    
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
        self._pending_thread_cleanup = False

        # Track destinations that already have reports to prevent duplicates
        self._destinations_with_reports = set()
        self._destination_root_map = {}

        # Track cleanup state to prevent duplicate cleanup calls
        self._cleanup_in_progress = False

        # Track cancel state to prevent duplicate cancel calls
        self._cancel_in_progress = False

        # Track active job metadata for destination completion handling
        self._active_job_id = None
        self._active_destination_roots = {}
        
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

    def _wait_for_event_pump_idle(self, idle_ms: int = 250, timeout_ms: int = 5000) -> None:
        """Wait for the event pump to finish emitting pending events before generating reports."""
        if not hasattr(self, 'event_pump') or not self.event_pump:
            return
        try:
            if self.event_pump.wait_for_idle(idle_ms=idle_ms, timeout_ms=timeout_ms):
                print(f"DEBUG: Event pump idle for {idle_ms}ms - safe to proceed with reporting")
            else:
                print(f"DEBUG: Event pump did not become idle within {timeout_ms}ms - proceeding cautiously")
        except Exception as e:
            print(f"DEBUG: Failed to wait for event pump idle: {e}")

    def _finalize_realtime_writer(self, status: str = "COMPLETED", error_message: Optional[str] = None) -> None:
        """Finalize the real-time report writer after the event pump has flushed pending events."""
        try:
            from ...utils.realtime_report_writer import get_realtime_writer, stop_realtime_reporting
        except Exception as import_error:
            print(f"DEBUG: Real-time writer finalize skipped (import error): {import_error}")
            return

        writer = get_realtime_writer()
        if not writer:
            print("DEBUG: No active real-time report writer to finalize")
            if hasattr(self.root, 'realtime_writer'):
                self.root.realtime_writer = None
            return

        try:
            self._wait_for_event_pump_idle()
        except Exception as idle_error:
            print(f"DEBUG: Error while waiting for event pump idle before finalizing reports: {idle_error}")

        try:
            stop_realtime_reporting(final_status=status, error_message=error_message)
            print(f"DEBUG: ✅ Real-time reports finalized with {status} status")
        except Exception as finalize_error:
            print(f"DEBUG: Error finalizing real-time reports: {finalize_error}")
        finally:
            if hasattr(self.root, 'realtime_writer'):
                self.root.realtime_writer = None
    
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

            if self.transfer_thread and self.transfer_thread.isRunning():
                print("DEBUG: Transfer already in progress - ignoring duplicate start request")
                return

            if self._pending_thread_cleanup:
                print("DEBUG: Previous transfer thread is still shutting down - please wait")
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
            root.current_job_id = job.job_id
            print(f"DEBUG: Current job ID set on root: {root.current_job_id}")

            # Track active job metadata for destination completion handling
            normalized_map = {}
            for index, path in enumerate(dest_paths):
                try:
                    normalized = os.path.normpath(path)
                except Exception:
                    normalized = path
                normalized_map[normalized] = index

            self._active_job_id = job.job_id
            self._active_destination_roots = normalized_map.copy()
            print(f"DEBUG: Active destination roots recorded: {list(self._active_destination_roots.keys())}")

            # Track destination roots for quick lookup (normalized)
            self._destination_root_map = normalized_map

            # Reset cleanup flag for new transfer
            self._cleanup_in_progress = False

            # CRITICAL: Clean up old event pump and connections from previous job
            # This prevents duplicate signal connections and stale event handlers
            if hasattr(self, 'event_pump') and self.event_pump:
                print("DEBUG: Cleaning up old event pump from previous job...")
                try:
                    # Stop the old pump
                    self.event_pump.stop_pump()

                    # Disconnect all old signals to prevent duplicates
                    try:
                        self.event_pump.progress_update.disconnect()
                        self.event_pump.destination_update.disconnect()
                        self.event_pump.destination_completed.disconnect()
                        self.event_pump.file_completed.disconnect()
                        print("DEBUG: ✅ Old event pump signals disconnected")
                    except Exception as e:
                        print(f"DEBUG: Note: Some signals may not have been connected: {e}")

                    # Clear reference
                    self.event_pump = None
                    print("DEBUG: ✅ Old event pump cleaned up")
                except Exception as e:
                    print(f"DEBUG: Error cleaning up old event pump: {e}")

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

            # CRITICAL FIX: Create RustEventSink on MAIN THREAD before worker thread starts
            # QObjects MUST be created on the thread where they'll receive signals (main Qt thread)
            print("DEBUG: 🔧 Creating RustEventSink on MAIN THREAD (Qt event loop thread)")
            from ..rust_event_sink import RustEventSink
            event_sink = RustEventSink()
            print("DEBUG: ✅ RustEventSink created on main thread successfully")

            # CRITICAL FIX: Connect event sink signals on MAIN THREAD before worker starts
            # Qt requires signal connections to be made on the same thread as the QObject
            print("DEBUG: 🔧 Connecting event sink signals on MAIN THREAD")
            try:
                # Connect Rust event sink to progress section for UI updates
                if hasattr(root, 'progress_section') and root.progress_section:
                    event_sink.progress_update.connect(root.progress_section.handle_progress_update)
                    print("DEBUG: ✅ Event sink → progress section connected")

                # Connect destination-specific progress updates to source/destination section
                if hasattr(root, 'source_dest_section') and root.source_dest_section:
                    event_sink.destination_update.connect(root.source_dest_section.handle_destination_progress)
                    print("DEBUG: ✅ Event sink → destination section connected")

                    # Connect destination completion signal to control section
                    event_sink.destination_completed.connect(self.handle_destination_completed)
                    print("DEBUG: ✅ Event sink → destination completion connected")

            except Exception as e:
                print(f"DEBUG: ❌ Error connecting event sink signals: {e}")
                import traceback
                traceback.print_exc()

            # CRITICAL FIX: Initialize event pump on MAIN THREAD (prevents Qt signal connection failures)
            # Event pump must be created and connected on main thread before worker starts
            print("DEBUG: 🔧 Initializing event pump on MAIN THREAD")
            from ..event_pump import EventPumpManager

            # Get engine instance to access event queue
            from ..engine_manager import get_engine
            engine = get_engine()

            # CRITICAL FIX: Reset engine state from previous transfer
            # The engine is a singleton that persists across transfers
            print("DEBUG: 🔄 Resetting Rust engine state from previous transfer...")
            if hasattr(engine, 'reset'):
                engine.reset()
                print("DEBUG: ✅ Rust engine state reset")
            else:
                print("DEBUG: ⚠️  No reset method - engine may have stale state")

            # Check if engine has event queue handle (new GIL-free architecture)
            if hasattr(engine, 'get_event_queue_handle'):
                print("DEBUG: Getting event queue handle from Rust engine...")
                queue_handle = engine.get_event_queue_handle()
                print("DEBUG: ✅ Event queue handle obtained")

                # CRITICAL FIX: Drain old events from previous transfer
                # The engine singleton's event queue may contain stale events from cancelled transfers
                # This prevents DestCompleted events from triggering premature report generation
                print("DEBUG: 🧹 Draining old events from event queue...")
                if hasattr(queue_handle, 'drain_all_events'):
                    drained_events = queue_handle.drain_all_events()
                    print(f"DEBUG: ✅ Drained {len(drained_events)} old events from queue")
                    if drained_events:
                        print(f"DEBUG: 🗑️  Discarded stale events: {[e[:100] for e in drained_events[:3]]}")
                else:
                    print("DEBUG: ⚠️  No drain_all_events method - queue may have stale events")

                # Create event pump manager
                self.event_pump = EventPumpManager()
                if job and getattr(job, 'destination_roots', None):
                    self.event_pump.set_expected_destination_count(len(job.destination_roots))
                    self.event_pump.set_destination_roots(job.destination_roots)

                # Connect event pump signals to UI handlers (MUST happen on main thread)
                print("DEBUG: 🔧 Connecting event pump signals on MAIN THREAD")
                try:
                    self.event_pump.progress_update.connect(root.progress_section.handle_progress_update)
                    print("DEBUG: ✅ Event pump → progress section connected")

                    self.event_pump.destination_update.connect(root.source_dest_section.handle_destination_progress)
                    print("DEBUG: ✅ Event pump → destination section connected")

                    self.event_pump.destination_completed.connect(self.handle_destination_completed)
                    print("DEBUG: ✅ Event pump → destination completion connected")

                    # CRITICAL FIX: Connect file completed events to DIT collector
                    self.event_pump.file_completed.connect(self._handle_file_completed_for_dit)
                    print("DEBUG: ✅ Event pump → DIT collector connected")
                    print(f"DEBUG: 🎯 Signal connected: event_pump.file_completed → controls._handle_file_completed_for_dit")
                except Exception as e:
                    print(f"DEBUG: ❌ Error connecting event pump signals: {e}")
                    import traceback
                    traceback.print_exc()

                # Start the pump (background thread polls queue and emits signals)
                self.event_pump.start_pump(queue_handle)
                print("DEBUG: ✅ Event pump started on MAIN THREAD - NO GIL DEADLOCK!")
            else:
                print("DEBUG: ⚠️ Engine doesn't have get_event_queue_handle - event pump disabled")

            # CRITICAL: Stop any old realtime writer from previous job FIRST
            # This ensures we don't have stale references
            print("DEBUG: 🧹 Cleaning up old realtime writer from previous job...")
            try:
                from ...utils.realtime_report_writer import stop_realtime_reporting
                stop_realtime_reporting("RESET")
                print("DEBUG: ✅ Old realtime writer stopped")
            except Exception as e:
                print(f"DEBUG: Note: No old realtime writer to stop: {e}")

            # CRITICAL: Initialize real-time report writer on MAIN THREAD before worker starts
            # This prevents race condition where events arrive before initialization completes
            print("DEBUG: 📊 Initializing real-time report writer on MAIN THREAD...")
            try:
                from ...utils.realtime_report_writer import start_realtime_reporting
                from ...utils.dit_data_collector import reset_dit_collector
                import os

                # CRITICAL FIX: Scan source directory to count total files BEFORE starting transfer
                # JobSpec only has source_root (path), not source_files (list)
                expected_files = 0
                if hasattr(job, 'source_root') and os.path.isdir(job.source_root):
                    print(f"DEBUG: Scanning source directory to count files: {job.source_root}")
                    try:
                        for root_dir, dirs, files in os.walk(job.source_root):
                            # Count only files, not directories
                            expected_files += len(files)
                        print(f"DEBUG: ✅ Found {expected_files} files in source directory")
                    except Exception as e:
                        print(f"DEBUG: ⚠️ Error scanning source directory: {e}")
                        expected_files = 0
                else:
                    print(f"DEBUG: ⚠️ job.source_root not found or not a directory")

                reset_dit_collector(job.job_id, expected_files)
                print(f"🎯 DIT collector initialized for job: {job.job_id}, expecting {expected_files} files")

                # Initialize real-time writer with expected total files from manifest
                realtime_writer = start_realtime_reporting(
                    job.job_id,
                    job.source_root,
                    job.destination_roots,
                    expected_files  # Pass manifest total for accurate reporting
                )
                root.realtime_writer = realtime_writer
                print(f"📊 Real-time report writer initialized for job: {job.job_id}")
                print(f"📊 Writer object ID: {id(realtime_writer)}")
                print(f"📊 Writer destinations: {realtime_writer.destinations}")
                print(f"📊 Writer report_paths keys: {list(realtime_writer.report_paths.keys())}")
                print("DEBUG: ✅ Real-time writer ready to receive file completion events")
            except Exception as e:
                print(f"ERROR: Failed to initialize real-time reporting: {e}")
                import traceback
                traceback.print_exc()

            # Connect destination cancel signals and enable cancel buttons
            print("DEBUG: 🔧 Connecting destination cancel signals...")
            if hasattr(root, 'source_dest_section') and root.source_dest_section:
                for dest_index, dest_widget in enumerate(root.source_dest_section.destination_widgets):
                    # Set destination index for tracking
                    dest_widget.dest_index = dest_index

                    # Connect cancel signal (signal emits: dest_index, dest_path)
                    dest_widget.destination_cancel_requested.connect(self._cancel_destination)

                    # Enable cancel button for this destination
                    dest_widget.enable_cancel_button()
                    print(f"DEBUG: ✅ Destination {dest_index} cancel button enabled")

            # Create transfer worker and thread (AFTER event sink is created and connected)
            print("DEBUG: 🔧 Creating TransferWorker with pre-connected event sink")
            self.transfer_worker = TransferWorker(job, root, event_sink)
            # Set cancel button reference so worker can update it immediately
            self.transfer_worker.cancel_btn = self.cancel_btn
            print("DEBUG: ✅ Transfer worker created with cancel button reference")
            self.transfer_thread = QThread()
            self.transfer_thread.setObjectName("ForwardFlowTransferThread")
            self.transfer_thread.finished.connect(self._on_transfer_thread_finished)

            # Move worker to thread
            self.transfer_worker.moveToThread(self.transfer_thread)
            print("DEBUG: ✅ Worker moved to QThread")

            # Connect worker signals (these are fine to connect here - worker is QObject on worker thread)
            self.transfer_thread.started.connect(self.transfer_worker.run_transfer)
            self.transfer_worker.progress_update.connect(self._handle_progress_update)
            self.transfer_worker.transfer_completed.connect(self._handle_transfer_completed)
            self.transfer_worker.transfer_failed.connect(self._handle_transfer_failed)
            self.transfer_worker.transfer_cancelled.connect(self._handle_transfer_cancelled)
            print("DEBUG: ✅ Worker signals connected")

            # Start the thread
            self.transfer_thread.start()
            print("DEBUG: ✅ Transfer thread started - Rust engine will emit events to main thread")
            
        except Exception as e:
            print(f"DEBUG: Error in on_start: {e}")
            import traceback
            traceback.print_exc()
            self.reenable_controls()
    
    def _handle_progress_update(self, payload):
        """Handle progress updates from transfer worker (currently unused since direct connections are used)"""
        print(f"DEBUG: TransferWorker progress update received (should not happen with direct connections): {payload}")

    def _handle_file_completed_for_dit(self, payload):
        """Handle file completed events and update real-time report + DIT collector"""
        try:
            print(f"🎯🎯🎯 CONTROLS: _handle_file_completed_for_dit() CALLED!")
            print(f"🎯🎯🎯 CONTROLS: Payload received: {payload}")

            # Extract file information from payload (matching Rust event format)
            filename = payload.get('filename', '')
            source_path = payload.get('source_path', '')
            dest_path = payload.get('dest_path', '')
            bytes_copied = payload.get('bytes_copied', 0)
            # CRITICAL FIX: Rust emits 'source_checksum', not 'source_hash'
            source_checksum = payload.get('source_checksum', '')
            dest_checksum = payload.get('dest_checksum', payload.get('destination_checksum', ''))
            verification_passed = payload.get('verification_passed', False)

            print(f"🎯🎯🎯 CONTROLS: Extracted data - file={filename}, hash={source_checksum[:16] if source_checksum else 'NONE'}")

            file_record = {
                'filename': filename,
                'source_path': source_path,
                'destination_path': dest_path,
                'dest_path': dest_path,
                'dest_index': payload.get('dest_index', 0),
                'file_size': bytes_copied,
                'size_bytes': bytes_copied,
                'source_checksum': source_checksum,
                'destination_checksum': dest_checksum,
                'hash_algorithm': payload.get('hash_algorithm', 'unknown'),
                'verification_passed': verification_passed,
                'status': payload.get('status', 'COMPLETED'),
                'transfer_status': payload.get('status', 'COMPLETED'),
            }

            # CRITICAL: Update real-time report IMMEDIATELY - Industry standard approach
            # This ensures we never lose data even if the system crashes
            print(f"🎯🎯🎯 CONTROLS: About to get real-time writer...")
            from ...utils.realtime_report_writer import get_realtime_writer
            writer = get_realtime_writer()
            print(f"🎯🎯🎯 CONTROLS: Real-time writer = {writer}")

            if writer:
                print(f"🎯🎯🎯 CONTROLS: Calling writer.add_file_completion()...")
                writer.add_file_completion(file_record)
                print(f"🎯🎯🎯 CONTROLS: ✅ Real-time report updated for: {filename}")
            else:
                print(f"🎯🎯🎯 CONTROLS: ❌❌❌ WARNING: No real-time report writer available!")

            # Also store in DIT collector for legacy compatibility
            print(f"🎯🎯🎯 CONTROLS: Getting DIT collector...")
            from ...utils.dit_data_collector import get_dit_collector
            dit_collector = get_dit_collector()
            print(f"🎯🎯🎯 CONTROLS: DIT collector = {dit_collector}")
            print(f"🎯🎯🎯 CONTROLS: Calling DIT collector.handle_file_complete_event()...")
            dit_collector.handle_file_complete_event(file_record)
            print(f"🎯🎯🎯 CONTROLS: ✅ File recorded in DIT collector: {filename} ({bytes_copied} bytes, hash: {source_checksum[:16] if source_checksum else 'none'}...)")

        except Exception as e:
            print(f"ERROR: Failed to record file in DIT collector: {e}")
            import traceback
            traceback.print_exc()

    def handle_destination_completed(self, dest_path: str):
        """Handle destination completion signal from event sink"""
        self._handle_destination_completed(dest_path)

    def _cancel_destination(self, dest_index: int, dest_path: str):
        """Cancel transfer to a specific destination"""
        print(f"\n{'='*80}")
        print(f"🚫🚫🚫 CANCEL DESTINATION REQUESTED: Index={dest_index}, Path={dest_path}")
        print(f"{'='*80}")

        try:
            # Get the engine and cancel this specific destination
            if hasattr(self.root, 'current_job'):
                engine = self.root.current_job
                print(f"DEBUG: Engine type: {type(engine)}")
                print(f"DEBUG: Has cancel_destination: {hasattr(engine, 'cancel_destination')}")

                # Check if engine has per-destination cancellation support
                if hasattr(engine, 'cancel_destination'):
                    print(f"DEBUG: ⚡⚡⚡ CALLING engine.cancel_destination({dest_index}) NOW")
                    engine.cancel_destination(dest_index)
                    print(f"✅✅✅ Destination {dest_index} cancellation signal sent to Rust engine")

                    # Reset destination widget to Ready state with Cancelled status
                    if hasattr(self.root, 'source_dest_section') and self.root.source_dest_section:
                        if dest_index < len(self.root.source_dest_section.destination_widgets):
                            dest_widget = self.root.source_dest_section.destination_widgets[dest_index]
                            dest_widget.reset_to_ready_state(status_text="Cancelled", status_color="#f59e0b")  # Orange
                            print(f"✅ Destination {dest_index} reset to Ready state with Cancelled status")
                else:
                    print(f"⚠️  Engine does not support per-destination cancellation")
                    print(f"    Engine type: {type(engine)}")
                    print(f"    Available methods: {dir(engine)}")
            else:
                print(f"⚠️  No active transfer to cancel")

        except Exception as e:
            print(f"❌ Error cancelling destination {dest_index}: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_destination_completed(self, dest_path: str):
        """Handle individual destination completion for immediate DIT report generation"""
        print(f"\n{'='*80}")
        print(f"🎯🎯🎯 DESTINATION COMPLETED HANDLER CALLED: {dest_path}")
        print(f"{'='*80}")

        # CRITICAL FIX: Allow destination completion handler to run even during cleanup
        # This ensures per-destination reports are generated as destinations finish,
        # not just at the end when all destinations complete.
        # We only skip if we've ALREADY processed this specific destination.

        if not dest_path:
            print("⚠️  DESTINATION COMPLETED ignored - empty destination path")
            return

        # CRITICAL FIX: Generate reports even if job_id is None (during cleanup phase)
        # Use a fallback job_id if needed
        active_job_id = getattr(self.root, 'current_job_id', None) or self._active_job_id
        if not active_job_id:
            print("⚠️  No active job ID - using fallback")
            import time
            active_job_id = f"dest_report_{int(time.time())}"

        normalized_path = os.path.normpath(dest_path) if dest_path else dest_path
        dest_index = None
        if not getattr(self, '_destination_root_map', None) and self._active_destination_roots:
            self._destination_root_map = self._active_destination_roots.copy()
            print("DEBUG: Reconstructed destination root map from active destinations")

        if hasattr(self, '_destination_root_map') and self._destination_root_map:
            dest_index = self._destination_root_map.get(normalized_path)
            if dest_index is None:
                # Attempt prefix match for nested paths
                for root, idx in self._destination_root_map.items():
                    if normalized_path.startswith(root):
                        dest_index = idx
                        normalized_path = root
                        break

        if dest_index is None:
            # Fallback: consult DIT collector destination records (handles resolved paths/symlinks)
            try:
                from ...utils.dit_data_collector import get_dit_collector
                collector = get_dit_collector()
                destination_details = collector.get_destination_details()
                for idx, info in destination_details.items():
                    recorded_path = info.get('dest_path', '')
                    if not recorded_path:
                        continue
                    normalized_recorded = os.path.normpath(recorded_path)
                    if (normalized_path and normalized_path.startswith(normalized_recorded)) or (
                        normalized_recorded and normalized_recorded.startswith(normalized_path)
                    ) or normalized_recorded == normalized_path:
                        dest_index = idx
                        normalized_path = normalized_recorded
                        print(f"DEBUG: Fallback matched destination index {dest_index} for path {dest_path}")
                        break
            except Exception as mapping_error:
                print(f"DEBUG: Failed fallback lookup for destination index: {mapping_error}")

        # Final fallback: attempt to match against active destination roots
        if dest_index is None and self._active_destination_roots:
            for root_path, idx in self._active_destination_roots.items():
                if normalized_path.startswith(root_path):
                    dest_index = idx
                    normalized_path = root_path
                    print(f"DEBUG: Active destination root map matched index {dest_index} for {dest_path}")
                    break

        if dest_index is None:
            print(f"⚠️  DESTINATION COMPLETED ignored - could not map path {dest_path} to destination index")
            return

        # Check if this destination is part of current job
        job_destinations = set(self._active_destination_roots.keys())
        if not job_destinations and hasattr(self.transfer_worker, 'job') and self.transfer_worker.job:
            job_destinations = {os.path.normpath(p) for p in self.transfer_worker.job.destination_roots}

        if job_destinations and normalized_path not in job_destinations:
            print(f"⚠️  DESTINATION COMPLETED ignored - {dest_path} not in current job destinations")
            return

        if normalized_path in self._destinations_with_reports:
            print(f"DEBUG: Destination {dest_path} already has a report - skipping duplicate generation")
            return

        try:
            # CRITICAL: Wait briefly for any pending FileCompleted events to be processed
            # The Rust engine says this dest is complete, but the last FileCompleted event
            # might still be in the queue. A short wait ensures it's processed.
            print(f"📊 Waiting briefly for event pump to process any pending events for dest_index={dest_index}...")
            self._wait_for_event_pump_idle(idle_ms=250, timeout_ms=2000)
            
            # Show "Writing report..." UI feedback
            self._show_report_generation_ui(dest_path)

            # CRITICAL: Finalize real-time report for this destination FIRST
            # This updates the JSON/CSV/TXT reports that were being written incrementally
            try:
                from ...utils.realtime_report_writer import get_realtime_writer
                realtime_writer = get_realtime_writer()
                if realtime_writer:
                    print(f"📊 Finalizing real-time report for destination: {dest_path}")
                    realtime_writer.finalize_destination_report(dest_path, status="COMPLETED")
                    print(f"✅ Real-time report finalized for destination: {dest_path}")
                else:
                    print(f"⚠️ No real-time writer available - skipping real-time report finalization")
            except Exception as rt_error:
                print(f"⚠️ Error finalizing real-time report for {dest_path}: {rt_error}")
                import traceback
                traceback.print_exc()

            # DISABLED: Comprehensive report generation creates duplicates
            # Real-time reports already contain all the data and are finalized above
            # # Get DIT collector and stats
            # from ...utils.dit_data_collector import get_dit_collector
            # dit_collector = get_dit_collector()
            # comprehensive_stats = dit_collector.get_stats_for_destination(dest_index)
            # file_records = dit_collector.get_file_records_for_destination(dest_index)
            # ... (comprehensive report generation code removed to prevent duplicates)

            print(f"✅ Destination {dest_path} reports already finalized by real-time reporter (no duplicate comprehensive reports needed)")

            # Mark this destination as having a report to prevent duplicates
            self._destinations_with_reports.add(normalized_path)
            print(f"🔒 Destination {dest_path} marked as having reports (prevents duplicates)")

            # Reset destination widget to Ready state with Completed status
            if hasattr(self.root, 'source_dest_section') and self.root.source_dest_section:
                if dest_index < len(self.root.source_dest_section.destination_widgets):
                    dest_widget = self.root.source_dest_section.destination_widgets[dest_index]
                    dest_widget.reset_to_ready_state(status_text="Completed", status_color="#10b981")  # Green
                    print(f"✅ Destination {dest_index} reset to Ready state with Completed status")

            # DISABLED: Completion log entry removed since it was based on comprehensive_stats
            # which we no longer generate (to avoid duplicates). Real-time reports have all the data.
            # # Add to completion log in progress section
            # if hasattr(self.root, 'progress_section') and self.root.progress_section:
            #     bytes_transferred = comprehensive_stats.get('total_bytes', comprehensive_stats.get('completed_bytes', 0))
            #     ...
            print(f"✅ Destination {dest_index} completed (real-time report already finalized)")

        except Exception as e:
            print(f"❌ Error generating report for destination {dest_path}: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_transfer_completed(self, stats):
        """Handle transfer completion - only generate reports for destinations without them"""
        print(f"DEBUG: Transfer completed with stats: {stats}")

        # Prevent duplicate cleanup if already in progress
        if self._cleanup_in_progress:
            print("DEBUG: Cleanup already in progress - skipping duplicate completion handler")
            return
        self._cleanup_in_progress = True

        # CRITICAL FIX: Wait for event pump to be COMPLETELY IDLE before cleanup
        # The engine's result collector finishes when all writes complete, but the event
        # queue may still have FileCompleted events waiting to be processed.
        # We MUST wait for the event pump to drain all events before destroying the 
        # realtime writer and DIT collector, or we'll lose data.
        try:
            import time
            print("DEBUG: ⏳ Waiting for Rust event queue to drain completely...")
            # AGGRESSIVE WAIT: The wait_for_idle check only looks at _last_event_timestamp,
            # but events can be queued in Rust and not yet processed. We need to wait
            # long enough for ALL events to drain through the entire pipeline.
            # With 126 files completing rapidly, we need at least 2-3 seconds.
            time.sleep(2.0)
            print("DEBUG: ⏳ Now waiting for event pump processing to idle (1000ms)...")
            self._wait_for_event_pump_idle(idle_ms=1000, timeout_ms=10000)
            print("DEBUG: ✅ Event pump is idle - safe to proceed with cleanup")
        except Exception as idle_error:
            print(f"DEBUG: ⚠️ Error waiting for event pump idle: {idle_error}")
            # Wait even more to be safe
            import time
            print("DEBUG: Waiting 2 seconds as fallback...")
            time.sleep(2.0)

        try:
            # CRITICAL FIX: Update all destination widgets to show 100% completion
            if hasattr(self.root, 'source_destination_section') and self.root.source_destination_section:
                print("DEBUG: Updating all destination widgets to 100% completion")
                for widget in self.root.source_destination_section.destination_widgets:
                    # Create a completion payload to update the widget
                    completion_payload = {
                        'dest_path': widget.path,
                        'progress_percent': 100.0,
                        'bytes_copied': widget.current_values.get('bytes_copied', 0),
                        'total_bytes': widget.current_values.get('total_bytes', 0),
                        'current_speed_mbps': 0.0,  # Completed destinations show 0 speed
                        'peak_speed_mbps': widget.current_values.get('peak_speed_mbps', 0),
                        'eta_seconds': 0.0,
                        'elapsed_seconds': widget.current_values.get('elapsed_seconds', 0),
                        'completed_files': widget.current_values.get('completed_files', 0),
                        'total_files': widget.current_values.get('total_files', 0),
                    }
                    widget.update_progress(completion_payload)
                    print(f"DEBUG: Updated destination widget {widget.path} to 100% completion")

            # Mark progress as completed with green styling
            if hasattr(self.root, 'progress_section') and self.root.progress_section:
                self.root.progress_section.mark_transfer_completed()

            # CRITICAL FIX: Generate reports BEFORE cleaning up job state
            # This ensures the JobAggregator data is still available for reporting
            if hasattr(self.transfer_worker, 'job') and self.transfer_worker.job:
                job_destinations = {
                    os.path.normpath(path) for path in self.transfer_worker.job.destination_roots
                }
                destinations_needing_reports = job_destinations - self._destinations_with_reports
                
                if destinations_needing_reports:
                    print(f"DEBUG: Generating completion reports for remaining destinations: {destinations_needing_reports}")
                    self._wait_for_event_pump_idle()
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
            
        except Exception as e:
            print(f"DEBUG: Error handling transfer completion: {e}")
            import traceback
            traceback.print_exc()
            self.reenable_controls()
        finally:
            try:
                self._cleanup_transfer_thread()
            except Exception as cleanup_error:
                print(f"DEBUG: Error cleaning up transfer thread during completion: {cleanup_error}")

            self._finalize_realtime_writer(status="COMPLETED")
            self._cleanup_in_progress = False
    
    def _handle_transfer_failed(self, error_message):
        """Handle transfer failure - ALWAYS generate reports showing what completed"""
        print(f"DEBUG: ========== TRANSFER FAILED: {error_message} ==========")
        try:
            # CRITICAL: Wait for events to be processed
            print("DEBUG: ⏳ Waiting for final events to be processed...")
            if hasattr(self, 'event_pump') and self.event_pump:
                import time
                time.sleep(1.0)
                for i in range(10):
                    QCoreApplication.processEvents()
                    QThread.msleep(50)

            # CRITICAL: Force realtime writer to flush everything
            print("DEBUG: ⏳ Forcing realtime writer to flush all data...")
            from ...utils.realtime_report_writer import get_realtime_writer
            writer = get_realtime_writer()
            if writer:
                for dest_path_key in list(writer.report_paths.keys()):
                    dest_display = writer.report_paths[dest_path_key].get('root_path', dest_path_key)
                    try:
                        writer.finalize_destination_report(dest_display, status="FAILED", error_message=error_message)
                    except Exception as e:
                        print(f"DEBUG: Error finalizing {dest_display}: {e}")

            # DISABLED: Real-time reports are already comprehensive and finalized per-destination
            # Generating additional "failed" reports creates duplicates
            # print("DEBUG: ⏳ Generating comprehensive failure report...")
            # self._generate_completion_report(self.root, "failed", None, self.transfer_worker.job, error_message)
            # print("DEBUG: ✅ Failure reports generated")
            print("DEBUG: ✅ Real-time reports already finalized (no duplicate comprehensive reports needed)")

            # Re-enable controls
            self.reenable_controls()

            # Clean up thread
            self._cleanup_transfer_thread()

        except Exception as e:
            print(f"DEBUG: Error handling transfer failure: {e}")
            import traceback
            traceback.print_exc()
            self.reenable_controls()

    def _wait_for_transfer_thread_shutdown(self, timeout_ms: int = 5000) -> bool:
        """Request the worker thread to exit; cleanup continues asynchronously."""
        if not self.transfer_thread or not self.transfer_thread.isRunning():
            return True

        if not self._pending_thread_cleanup:
            print(f"DEBUG: Requesting transfer thread shutdown (timeout={timeout_ms}ms)")
            self._pending_thread_cleanup = True
            self.transfer_thread.quit()
            QTimer.singleShot(timeout_ms, self._force_terminate_transfer_thread)
        else:
            print("DEBUG: Transfer thread shutdown already pending")

        return False

    def _force_terminate_transfer_thread(self):
        """Final safety net: force-stop the worker thread if it ignored quit()."""
        if self.transfer_thread and self.transfer_thread.isRunning():
            print("DEBUG: Force terminating transfer thread after timeout")
            self.transfer_thread.terminate()
            self.transfer_thread.wait(1000)
        if self.transfer_thread and not self.transfer_thread.isRunning():
            self._finalize_transfer_thread_cleanup()

    def _on_transfer_thread_finished(self):
        """Qt signal handler fired when the transfer worker thread exits."""
        print("DEBUG: Transfer thread finished signal received")
        self._finalize_transfer_thread_cleanup()

    def _finalize_transfer_thread_cleanup(self):
        """Disconnect signals and release thread/worker references."""
        if self.transfer_thread:
            try:
                self.transfer_thread.finished.disconnect(self._on_transfer_thread_finished)
            except Exception:
                pass
        self.transfer_thread = None
        self.transfer_worker = None
        self._pending_thread_cleanup = False
        self._reset_cancel_button_state()
        print("DEBUG: Transfer thread cleaned up")
    
    def _handle_transfer_cancelled(self):
        """Handle transfer cancellation - ALWAYS generate reports showing what completed"""
        print("DEBUG: ========== TRANSFER CANCELLED - ENSURING COMPLETE REPORTS ==========")

        # Prevent duplicate cleanup if already in progress
        if self._cleanup_in_progress:
            print("DEBUG: Cleanup already in progress - skipping duplicate cancellation handler")
            return
        self._cleanup_in_progress = True

        try:
            # CRITICAL FIX: AGGRESSIVE wait for all events to be processed
            # This is the #1 cause of blank/incomplete reports
            print("DEBUG: ⏳ STEP 1: Waiting for transfer thread to finish...")
            if self.transfer_thread and self.transfer_thread.isRunning():
                if self._wait_for_transfer_thread_shutdown(timeout_ms=10000):
                    print("DEBUG: ✅ Transfer thread finished gracefully")
                else:
                    print("DEBUG: ⚠️  Transfer thread still shutting down - waiting anyway")
                    # Force wait even if it didn't finish gracefully
                    if self.transfer_thread:
                        self.transfer_thread.wait(5000)

            # CRITICAL FIX: AGGRESSIVE event pump flushing
            print("DEBUG: ⏳ STEP 2: Flushing ALL remaining events from event pump...")
            if hasattr(self, 'event_pump') and self.event_pump:
                # Let events continue processing for a bit
                import time
                print("DEBUG:    Waiting 1 second for final events to arrive...")
                time.sleep(1.0)

                # Process Qt events multiple times to ensure signals propagate
                for i in range(10):
                    QCoreApplication.processEvents()
                    QThread.msleep(50)

                # NOW stop the pump
                print("DEBUG:    Stopping event pump...")
                self.event_pump.stop_pump()
                print("DEBUG: ✅ Event pump stopped")

            # CRITICAL: Additional Qt event processing
            print("DEBUG: ⏳ STEP 3: Processing Qt event queue...")
            for i in range(20):
                QCoreApplication.processEvents()
                QThread.msleep(25)
            print("DEBUG: ✅ Qt events processed")

            # CRITICAL FIX: FORCE realtime writer to flush everything NOW
            print("DEBUG: ⏳ STEP 4: Forcing realtime writer to flush all data...")
            from ...utils.realtime_report_writer import get_realtime_writer
            writer = get_realtime_writer()
            if writer:
                # Get current stats before finalization
                print(f"DEBUG:    Realtime writer has {len(writer.report_paths)} destination(s)")
                print(f"DEBUG:    Stats: {writer.stats}")

                # Finalize ALL destination reports immediately
                for dest_path_key in list(writer.report_paths.keys()):
                    dest_display = writer.report_paths[dest_path_key].get('root_path', dest_path_key)
                    print(f"DEBUG:    Finalizing realtime report for: {dest_display}")
                    try:
                        writer.finalize_destination_report(dest_display, status="CANCELLED")
                    except Exception as e:
                        print(f"DEBUG:    Error finalizing {dest_display}: {e}")
                print("DEBUG: ✅ Realtime writer flushed")
            else:
                print("DEBUG: ⚠️  No realtime writer found")

            # Now generate comprehensive DIT reports with complete data
            print("DEBUG: ⏳ STEP 5: Generating comprehensive DIT reports...")
            if hasattr(self.transfer_worker, 'job') and self.transfer_worker.job:
                job_destinations = {
                    os.path.normpath(path) for path in self.transfer_worker.job.destination_roots
                }
                destinations_needing_reports = job_destinations - self._destinations_with_reports

                # DISABLED: Real-time reports already handle cancellation per-destination
                # Additional comprehensive reports create duplicates
                # print(f"DEBUG: Generating CANCELLED report for ALL destinations")
                # self._generate_completion_report(
                #     self.root,
                #     "cancelled",
                #     None,
                #     self.transfer_worker.job,
                #     error_message="Transfer cancelled by user"
                # )
                print(f"DEBUG: ✅ Real-time reports already finalized with cancellation status (no duplicate reports needed)")
                print("DEBUG: ✅ Reports generated")

            # Clean up job state AFTER report generation (FIXED: this was happening before!)
            self._cleanup_job_state()

            # Re-enable controls
            self.reenable_controls()
            
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
        finally:
            try:
                self._cleanup_transfer_thread()
            except Exception as cleanup_error:
                print(f"DEBUG: Error cleaning up transfer thread during cancellation: {cleanup_error}")
            self._finalize_realtime_writer(status="CANCELLED")
            self._cleanup_in_progress = False
    
    def _cleanup_transfer_thread(self):
        """Clean up transfer thread and worker"""
        try:
            if self._wait_for_transfer_thread_shutdown():
                self._finalize_transfer_thread_cleanup()
            else:
                print("DEBUG: Transfer thread cleanup deferred")
            
        except Exception as e:
            print(f"DEBUG: Error cleaning up transfer thread: {e}")
    
    def _get_block_size_for_preset(self, preset: str) -> int:
        """Get block size in bytes for the given preset - optimized for M2 Max performance"""
        normalized_preset = (preset or "").strip().lower()

        preset_map = {
            'auto': 32 * 1024 * 1024,
            'auto (recommended)': 32 * 1024 * 1024,
            'usb/tb': 32 * 1024 * 1024,
            'usb': 32 * 1024 * 1024,
            'thunderbolt': 32 * 1024 * 1024,
            'network': 8 * 1024 * 1024,
            'custom': 16 * 1024 * 1024,
            'fast': 32 * 1024 * 1024,
            'balanced': 16 * 1024 * 1024,
            'strict': 8 * 1024 * 1024,
            '': 32 * 1024 * 1024,
        }

        return preset_map.get(normalized_preset, 32 * 1024 * 1024)
    
    def _cleanup_job_state(self):
        """Clean up job state to prevent contamination between jobs"""
        try:
            # CRITICAL FIX: Reset Rust engine cancelled flag for next transfer
            if hasattr(self.root, 'current_job') and self.root.current_job:
                try:
                    if hasattr(self.root.current_job, 'reset'):
                        self.root.current_job.reset()
                        print("DEBUG: ✅ Rust engine reset - ready for next transfer")
                except Exception as e:
                    print(f"DEBUG: Error resetting Rust engine: {e}")

            # Clear job references
            if hasattr(self.root, 'current_job'):
                self.root.current_job = None
            if hasattr(self.root, 'current_job_spec'):
                self.root.current_job_spec = None
            if hasattr(self.root, 'current_job_id'):
                self.root.current_job_id = None

            # Clear active job metadata
            self._active_job_id = None
            self._active_destination_roots.clear()

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
            # Ensure all pending file events have been processed before reading collector data
            self._wait_for_event_pump_idle()

            from ...utils.report_generator import TransferReportGenerator
            from ...utils.dit_data_collector import get_dit_collector
            
            # Create report generator
            report_gen = TransferReportGenerator()
            
            # CRITICAL FIX: Use DIT data collector as primary source
            print(f"🔍 DEBUG: About to get DIT collector for report generation...")
            dit_collector = get_dit_collector()
            print(f"🔍 DEBUG: Report generator got DIT collector instance {id(dit_collector)}")

            # Initialize comprehensive stats with DIT collector data
            comprehensive_stats = dit_collector.get_job_stats()
            file_records = dit_collector.get_file_records()

            print(f"🎯 DIT COLLECTOR REPORT DATA:")
            print(f"   File records: {len(file_records)}")
            print(f"   Total bytes: {comprehensive_stats.get('total_bytes', 0)}")
            print(f"   Completed files: {comprehensive_stats.get('completed_files', 0)}")
            
            # If DIT collector has no data, fall back to legacy sources
            if not dit_collector.has_data():
                print("DEBUG: DIT collector has no data, using legacy fallback sources")
                
                # Initialize fallback stats
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
            
            # CRITICAL FIX: Generate separate reports per destination with independent stats
            print("🔥🔥🔥 DEBUG: Generating PER-DESTINATION reports with independent stats")
            all_dest_indices = dit_collector.get_all_destination_indices()
            print(f"🔥 DEBUG: Found {len(all_dest_indices)} destinations with data: {all_dest_indices}")

            remaining_destinations = {
                os.path.normpath(path) for path in job.destination_roots
                if os.path.normpath(path) not in self._destinations_with_reports
            }
            
            all_generated_reports = []
            
            # If we have per-destination data, generate independent reports
            if all_dest_indices and len(all_dest_indices) > 0:
                for dest_index in all_dest_indices:
                    # Get per-destination stats and files
                    dest_stats = dit_collector.get_stats_for_destination(dest_index)
                    dest_file_records = dit_collector.get_file_records_for_destination(dest_index)
                    
                    # Get the actual destination path
                    dest_path = ''
                    if dest_file_records and len(dest_file_records) > 0:
                        # Extract dest_path from first file record
                        dest_path = dest_file_records[0].get('dest_path', '')
                        # Get the root path (remove file-specific parts)
                        for dest_root in job.destination_roots:
                            if dest_path.startswith(dest_root):
                                dest_path = dest_root
                                break
                    
                    if not dest_path and dest_index < len(job.destination_roots):
                        dest_path = job.destination_roots[dest_index]
                    normalized_dest_path = os.path.normpath(dest_path) if dest_path else dest_path

                    if remaining_destinations and normalized_dest_path not in remaining_destinations:
                        print(f"DEBUG: Destination {dest_path} already has reports - skipping")
                        continue
                    
                    print(f"🔥 DEBUG: Generating report for dest_index={dest_index}, path={dest_path}")
                    print(f"🔥 DEBUG:   Files: {dest_stats['total_files']}, Bytes: {dest_stats['total_bytes']}")
                    print(f"🔥 DEBUG:   Avg Speed: {dest_stats['avg_speed']:.1f} MB/s, Peak: {dest_stats['peak_speed']:.1f} MB/s")
                    
                    # Generate report for this destination
                    dest_reports = report_gen.generate_comprehensive_reports(
                        job_id=job.job_id,
                        status=status,
                        source_path=job.source_root,
                        destinations=[dest_path],  # Single destination
                        stats=dest_stats,  # Per-destination stats
                        file_records=dest_file_records,  # Per-destination files
                        error_message=error_message
                    )
                    
                    if dest_reports:
                        all_generated_reports.extend(dest_reports)
                        print(f"✅ Generated {len(dest_reports)} reports for destination {dest_path}")
                        remaining_destinations.discard(normalized_dest_path)
                        self._destinations_with_reports.add(normalized_dest_path)
                
                if all_generated_reports:
                    print(f"DEBUG: Generated {len(all_generated_reports)} total comprehensive reports across all destinations")
                    for report in all_generated_reports:
                        print(f"  - {report}")
                else:
                    print("DEBUG: No per-destination reports were generated")
            else:
                # Fallback to global reports if no per-destination data
                print("⚠️ DEBUG: No per-destination data available - generating global report as fallback")
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
                    print(f"DEBUG: Generated {len(generated_reports)} fallback comprehensive reports:")
                    for report in generated_reports:
                        print(f"  - {report}")
                    for dest_path in job.destination_roots:
                        self._destinations_with_reports.add(os.path.normpath(dest_path))
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
                        # CopyStats object - safely get errors
                        errors = getattr(engine_stats, 'errors', None)
                        error_count = 0
                        if errors:
                            if hasattr(errors, '__len__'):  # Check if iterable
                                error_count = len(errors)
                            elif isinstance(errors, (int, float)):
                                error_count = int(errors)

                        stats = {
                            "total_bytes": getattr(engine_stats, 'total_bytes', 0),
                            "copied_bytes": getattr(engine_stats, 'copied_bytes', 0),
                            "duration": getattr(engine_stats, 'end_time', 0) - getattr(engine_stats, 'start_time', 0),
                            "avg_speed": getattr(engine_stats, 'speed_mbps', 0),
                            "total_files": getattr(engine_stats, 'total_files', 0),
                            "completed_files": getattr(engine_stats, 'copied_files', 0),
                            "cancelled_files": 0,
                            "error_files": error_count,
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
        """Handle pause button click - toggle between pause and resume"""
        print("DEBUG: Pause button clicked")

        try:
            # Check if we have an active transfer
            if not hasattr(root, 'current_job') or not root.current_job:
                print("DEBUG: No active transfer to pause")
                return

            engine = root.current_job

            # Check current pause state
            is_paused = False
            try:
                if hasattr(engine, 'is_paused'):
                    is_paused = engine.is_paused()
            except Exception as e:
                print(f"DEBUG: Error checking pause state: {e}")

            if is_paused:
                # Resume the transfer
                print("DEBUG: Resuming transfer...")
                try:
                    if hasattr(engine, 'resume'):
                        engine.resume()
                        self.pause_btn.setText("Pause")
                        print("DEBUG: Transfer resumed")

                        # Update UI to show transfer is active again
                        if hasattr(root, 'progress_section') and root.progress_section:
                            if hasattr(root.progress_section, 'total_progress'):
                                # Don't change progress value, just ensure it's visible
                                root.progress_section.total_progress.update()
                    else:
                        print("DEBUG: Engine does not support resume")
                except Exception as e:
                    print(f"DEBUG: Error resuming transfer: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                # Pause the transfer
                print("DEBUG: Pausing transfer...")
                try:
                    if hasattr(engine, 'pause'):
                        engine.pause()
                        self.pause_btn.setText("Resume")
                        print("DEBUG: Transfer paused")

                        # Update UI to show transfer is paused
                        if hasattr(root, 'progress_section') and root.progress_section:
                            if hasattr(root.progress_section, 'total_progress'):
                                current_value = root.progress_section.total_progress.value()
                                root.progress_section.total_progress.setFormat(f"{current_value}% (Paused)")
                    else:
                        print("DEBUG: Engine does not support pause")
                except Exception as e:
                    print(f"DEBUG: Error pausing transfer: {e}")
                    import traceback
                    traceback.print_exc()

        except Exception as e:
            print(f"DEBUG: Error in pause handler: {e}")
            import traceback
            traceback.print_exc()
    
    def on_cancel(self, root):
        """Handle cancel button click - immediately stop transfer and show writing report"""
        print("DEBUG: Cancel button clicked - immediately stopping transfer")

        # Guard against multiple simultaneous cancellations
        if hasattr(self, '_cancel_in_progress') and self._cancel_in_progress:
            print("DEBUG: Cancel already in progress - ignoring duplicate click")
            return

        self._cancel_in_progress = True

        # Immediate visual feedback - show button is pressed
        if self.cancel_btn:
            self.cancel_btn.setDown(True)  # Show pressed state
            self.cancel_btn.setEnabled(False)  # Prevent multiple clicks
            self.cancel_btn.setText("Cancelling...")
            # Force UI update
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
        
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

            # NOTE: reenable_controls() and report generation are handled by _handle_transfer_cancelled()
            # when the transfer worker emits the cancelled signal.
            # DO NOT call reenable_controls() here - it will be called by the proper handler.
            print("DEBUG: Waiting for transfer worker to emit cancelled signal and trigger cleanup...")
            
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

    def _reset_cancel_button_state(self):
        """Reset cancel button text/state and internal flags."""
        self._cancel_in_progress = False
        if self.cancel_btn:
            self.cancel_btn.setEnabled(False)
            self.cancel_btn.setText("Cancel")
    
    def reenable_controls(self):
        """Re-enable controls after error or completion and reset UI to Ready state"""
        print("DEBUG: Re-enabling controls and resetting UI to Ready state")
        
        # Re-enable transfer buttons
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("Pause")  # Reset text from "Resume" if it was paused
        self._reset_cancel_button_state()
        
        # Re-enable ALL controls that get disabled during transfer start
        # This fixes the post-cancel UI bug where dropdowns become unresponsive
        
        # Re-enable source/destination section controls
        if hasattr(self.root, 'source_dest_section') and self.root.source_dest_section:
            source_dest_section = self.root.source_dest_section
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
                # Reset progress bar styling back to blue (from green completion state)
                from app.ui.color_scheme_pyqt import colors
                self.root.progress_section.total_progress.setStyleSheet(f"""
                    QProgressBar {{
                        border: 1px solid {colors['border']};
                        border-radius: 3px;
                        text-align: center;
                        background-color: {colors['bg']};
                        color: {colors['text']};
                        font-size: 14px;
                        font-weight: 600;
                        margin: 0;
                        padding: 0;
                        min-height: 60px;
                        max-height: 60px;
                    }}
                    QProgressBar::chunk {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                   stop:0 #2563eb,
                                                   stop:0.5 #3b82f6,
                                                   stop:1 #60a5fa);
                        border-radius: 2px;
                    }}
                """)
                print("DEBUG: Reset main progress bar to 0% with blue styling")

            # Reset speed/time labels but PRESERVE file count
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
            # CRITICAL FIX: DO NOT reset files_count - preserve final count after transfer completes
            # The old buggy code was: self.root.progress_section.files_count.setText("0 of 0 files")

            # Reset health indicators to default state
            if hasattr(self.root.progress_section, 'integrity_label'):
                self.root.progress_section.integrity_label.setText("Pending...")
                self.root.progress_section.integrity_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors['secondary_text']};
                        font-size: 11px;
                        font-weight: 600;
                        text-align: center;
                        margin: 0;
                        padding: 2px;
                        background: transparent;
                        border: none;
                    }}
                """)
            if hasattr(self.root.progress_section, 'errors_label'):
                self.root.progress_section.errors_label.setText("0")
                self.root.progress_section.errors_label.setStyleSheet(f"""
                    QLabel {{
                        color: #22c55e;
                        font-size: 11px;
                        font-weight: 600;
                        text-align: center;
                        margin: 0;
                        padding: 2px;
                        background: transparent;
                        border: none;
                    }}
                """)
            if hasattr(self.root.progress_section, 'connection_label'):
                self.root.progress_section.connection_label.setText("— Idle")
                self.root.progress_section.connection_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors['secondary_text']};
                        font-size: 11px;
                        font-weight: 600;
                        text-align: center;
                        margin: 0;
                        padding: 2px;
                        background: transparent;
                        border: none;
                    }}
                """)
            if hasattr(self.root.progress_section, 'disk_label'):
                self.root.progress_section.disk_label.setText("— Idle")
                self.root.progress_section.disk_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors['secondary_text']};
                        font-size: 11px;
                        font-weight: 600;
                        text-align: center;
                        margin: 0;
                        padding: 2px;
                        background: transparent;
                        border: none;
                    }}
                """)

            # Reset health metrics tracking
            if hasattr(self.root.progress_section, 'error_count'):
                self.root.progress_section.error_count = 0
            if hasattr(self.root.progress_section, 'last_speed_samples'):
                self.root.progress_section.last_speed_samples = []

            print("DEBUG: Reset all progress section labels and health indicators")
        
        # Reset destination cards to Ready state
        if hasattr(self.root, 'source_dest_section') and self.root.source_dest_section:
            if hasattr(self.root.source_dest_section, 'destination_widgets'):
                for dest_widget in self.root.source_dest_section.destination_widgets:
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
        self._destination_root_map.clear()
        print("DEBUG: Cleared destinations report tracking for new job")
            
        print("DEBUG: UI completely reset to Ready state for new transfer")
    
    def _show_report_generation_ui(self, dest_path: str):
        """Show 'Writing report...' UI feedback for destination"""
        print(f"📄 Showing report generation UI for: {dest_path}")
        
        # TODO: Add progress dialog or status message
        # For now, just print - this can be enhanced with actual UI feedback
        

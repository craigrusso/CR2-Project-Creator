"""Progress Section for Ingest Tab"""

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt

try:
    from app.ui.color_scheme_pyqt import (
        colors, PROGRESS_BAR_STYLE, FIELD_LABEL_STYLE, SCROLL_AREA_STYLE,
        CARD_FRAME_STYLE, SECTION_HEADER_STYLE, SUMMARY_METRIC_STYLE
    )
    STYLING_AVAILABLE = True
except ImportError as e:
    print(f"DEBUG: Failed to import centralized styles: {e}")
    raise ImportError("Centralized styles are required for the ingest tab")


class DestinationProgressWidget(QWidget):
    """Individual destination progress widget"""
    
    def __init__(self, dest_index, dest_path, parent=None):
        super().__init__(parent)
        self.dest_index = dest_index
        self.dest_path = dest_path
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the destination progress UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 6, 8, 6)
        
        # Destination header with path and status
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Destination label (truncated path)
        path_label = QLabel(self._truncate_path(self.dest_path))
        path_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                font-size: 11px;
                font-weight: 600;
                margin: 0;
                padding: 0;
            }}
        """)
        path_label.setToolTip(self.dest_path)  # Full path on hover
        
        # Status indicator
        self.status_label = QLabel("Waiting...")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['secondary_text']};
                font-size: 10px;
                font-weight: 500;
                margin: 0;
                padding: 0;
            }}
        """)
        
        header_layout.addWidget(path_label, 1)
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Progress bar for this destination
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {colors['border']};
                border-radius: 2px;
                text-align: center;
                background-color: {colors['bg']};
                color: {colors['text']};
                font-size: 10px;
                font-weight: 500;
                margin: 0;
                padding: 0;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                           stop:0 #2563eb, 
                                           stop:0.5 #3b82f6, 
                                           stop:1 #60a5fa);
                border-radius: 1px;
            }}
        """)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setTextVisible(True)
        
        layout.addWidget(self.progress_bar)
        
        # Destination stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        
        # Speed indicator
        self.speed_label = QLabel("0 MB/s")
        self.speed_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                font-size: 10px;
                font-weight: 600;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
                margin: 0;
                padding: 0;
            }}
        """)
        
        # Files completed
        self.files_label = QLabel("0/0 files")
        self.files_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['secondary_text']};
                font-size: 9px;
                font-weight: 500;
                margin: 0;
                padding: 0;
            }}
        """)
        
        # ETA
        self.eta_label = QLabel("--:--:--")
        self.eta_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['secondary_text']};
                font-size: 9px;
                font-weight: 500;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
                margin: 0;
                padding: 0;
            }}
        """)
        
        stats_layout.addWidget(self.speed_label)
        stats_layout.addWidget(self.files_label)
        stats_layout.addWidget(self.eta_label)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        # Set fixed height for compact display
        self.setFixedHeight(80)
    
    def _truncate_path(self, path, max_length=40):
        """Truncate long paths for display"""
        if len(path) <= max_length:
            return path
        
        # Try to keep the end of the path
        parts = path.split('/')
        if len(parts) <= 2:
            return path[:max_length-3] + "..."
        
        # Keep first and last parts
        result = parts[0] + "/.../" + parts[-1]
        if len(result) > max_length:
            result = "..." + result[-(max_length-3):]
        return result
    
    def update_progress(self, bytes_copied, total_bytes, completed_files, total_files, current_speed_mbps, elapsed_time):
        """Update destination progress"""
        # Update progress bar
        if total_bytes > 0:
            progress_percent = int((bytes_copied / total_bytes) * 100)
            self.progress_bar.setValue(progress_percent)
            self.progress_bar.setFormat(f"{progress_percent}%")
        
        # Update speed
        self.speed_label.setText(f"{current_speed_mbps:.1f} MB/s")
        
        # Update files count
        self.files_label.setText(f"{completed_files}/{total_files} files")
        
        # Update ETA if we have speed data
        if current_speed_mbps > 0 and bytes_copied < total_bytes:
            remaining_bytes = total_bytes - bytes_copied
            eta_seconds = remaining_bytes / (current_speed_mbps * 1024 * 1024)
            if eta_seconds > 0:
                eta_str = f"{int(eta_seconds//3600):02d}:{int((eta_seconds%3600)//60):02d}:{int(eta_seconds%60):02d}"
                self.eta_label.setText(eta_str)
            else:
                self.eta_label.setText("--:--:--")
        else:
            self.eta_label.setText("--:--:--")
        
        # Update status
        if completed_files == total_files:
            self.status_label.setText("Complete")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: #4a7c4a;
                    font-size: 10px;
                    font-weight: 600;
                    margin: 0;
                    padding: 0;
                }}
            """)
        elif completed_files > 0:
            self.status_label.setText("Transferring...")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: #2d5a2d;
                    font-size: 10px;
                    font-weight: 600;
                    margin: 0;
                    padding: 0;
                }}
            """)
        else:
            self.status_label.setText("Waiting...")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors['secondary_text']};
                    font-size: 10px;
                    font-weight: 500;
                    margin: 0;
                    padding: 0;
                }}
            """)


class ProgressSection(QWidget):
    """Progress Section with exact original design"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize job data tracking
        self.job_data = None
        # Destination progress is now handled in destination cards
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the progress UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main progress display (clean, compact)
        progress_frame = QFrame()
        progress_frame.setStyleSheet(CARD_FRAME_STYLE)
        progress_frame.setMinimumHeight(120)  # Increased to accommodate stats
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setSpacing(8)
        progress_layout.setContentsMargins(12, 12, 12, 12)
        
        # Total progress with integrated label - prominently sized for visibility
        self.total_progress = QProgressBar()
        self.total_progress.setRange(0, 100)
        self.total_progress.setValue(0)
        self.total_progress.setFixedHeight(60)  # 2.5x taller for prominence
        # Custom style to override min-height constraint and make progress bar prominent
        self.total_progress.setStyleSheet(f"""
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
        self.total_progress.setVisible(True)
        self.total_progress.setEnabled(True)
        self.total_progress.setFormat("%p%")
        self.total_progress.setTextVisible(True)
        
        # Add progress bar with normal layout
        progress_layout.addWidget(self.total_progress)

        # Close the progress frame here
        layout.addWidget(progress_frame)

        # Add spacing between progress bar and stats card
        spacer = QWidget()
        spacer.setFixedHeight(8)  # 8px spacing for visual separation
        layout.addWidget(spacer)

        # Create a separate CARD for stats to prevent overlap with progress bar title
        stats_card = QFrame()
        stats_card.setStyleSheet(CARD_FRAME_STYLE)
        stats_card.setMinimumHeight(80)  # Ensure sufficient height for two rows
        stats_container_layout = QVBoxLayout(stats_card)
        stats_container_layout.setSpacing(2)
        stats_container_layout.setContentsMargins(12, 8, 12, 8)
        
        # Create compact, direct labels without container widgets (no card backgrounds)
        # Elapsed time
        elapsed_header = QLabel("Elapsed")
        elapsed_header.setStyleSheet(f"""
            QLabel {{
                color: {colors['secondary_text']};
                font-size: 10px;
                font-weight: 500;
                text-align: center;
                margin: 0;
                padding: 0;
                background-color: transparent;
                background: none;
                border: none;
                border-radius: 0;
                qproperty-alignment: AlignCenter;
            }}
        """)
        elapsed_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elapsed_header.setMinimumHeight(16)  # Fixed minimum height
        self.elapsed_label = QLabel("00:00:00")
        self.elapsed_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                font-size: 13px;
                font-weight: 600;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
                text-align: center;
                margin: 0;
                padding: 2px;
                background: transparent;
                border: none;
            }}
        """)
        self.elapsed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.elapsed_label.setMinimumHeight(20)  # Fixed minimum height
        
        # ETA
        eta_header = QLabel("ETA")
        eta_header.setStyleSheet(f"""
            QLabel {{
                color: {colors['secondary_text']};
                font-size: 10px;
                font-weight: 500;
                text-align: center;
                margin: 0;
                padding: 0;
                background-color: transparent;
                background: none;
                border: none;
                border-radius: 0;
                qproperty-alignment: AlignCenter;
            }}
        """)
        eta_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        eta_header.setMinimumHeight(16)  # Fixed minimum height
        self.eta_label = QLabel("--:--:--")
        self.eta_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                font-size: 13px;
                font-weight: 600;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
                text-align: center;
                margin: 0;
                padding: 2px;
                background: transparent;
                border: none;
            }}
        """)
        self.eta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.eta_label.setMinimumHeight(20)  # Fixed minimum height
        
        # Current speed
        speed_header = QLabel("Speed")
        speed_header.setStyleSheet(f"""
            QLabel {{
                color: {colors['secondary_text']};
                font-size: 10px;
                font-weight: 500;
                text-align: center;
                margin: 0;
                padding: 0;
                background-color: transparent;
                background: none;
                border: none;
                border-radius: 0;
                qproperty-alignment: AlignCenter;
            }}
        """)
        speed_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        speed_header.setMinimumHeight(16)  # Fixed minimum height
        self.current_speed_label = QLabel("0 MB/s")
        self.current_speed_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                font-size: 13px;
                font-weight: 600;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
                text-align: center;
                margin: 0;
                padding: 2px;
                background: transparent;
                border: none;
            }}
        """)
        self.current_speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_speed_label.setMinimumHeight(20)  # Fixed minimum height
        
        # Average speed
        avg_header = QLabel("Avg")
        avg_header.setStyleSheet(f"""
            QLabel {{
                color: {colors['secondary_text']};
                font-size: 10px;
                font-weight: 500;
                text-align: center;
                margin: 0;
                padding: 0;
                background-color: transparent;
                background: none;
                border: none;
                border-radius: 0;
                qproperty-alignment: AlignCenter;
            }}
        """)
        avg_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avg_header.setMinimumHeight(16)  # Fixed minimum height
        self.avg_speed_label = QLabel("0 MB/s")
        self.avg_speed_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                font-size: 13px;
                font-weight: 600;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
                text-align: center;
                margin: 0;
                padding: 2px;
                background: transparent;
                border: none;
            }}
        """)
        self.avg_speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avg_speed_label.setMinimumHeight(20)  # Fixed minimum height
        
        # Peak speed
        peak_header = QLabel("Peak")
        peak_header.setStyleSheet(f"""
            QLabel {{
                color: {colors['secondary_text']};
                font-size: 10px;
                font-weight: 500;
                text-align: center;
                margin: 0;
                padding: 0;
                background-color: transparent;
                background: none;
                border: none;
                border-radius: 0;
                qproperty-alignment: AlignCenter;
            }}
        """)
        peak_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        peak_header.setMinimumHeight(16)  # Fixed minimum height
        self.peak_speed_label = QLabel("0 MB/s")
        self.peak_speed_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                font-size: 13px;
                font-weight: 600;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
                text-align: center;
                margin: 0;
                padding: 2px;
                background: transparent;
                border: none;
            }}
        """)
        self.peak_speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.peak_speed_label.setMinimumHeight(20)  # Fixed minimum height
        
        # Add headers in a row (much more compact)
        headers_layout = QHBoxLayout()
        headers_layout.setSpacing(0)
        headers_layout.setContentsMargins(0, 0, 0, 0)
        headers_layout.addWidget(elapsed_header, 1)
        headers_layout.addWidget(eta_header, 1)
        headers_layout.addWidget(speed_header, 1)
        headers_layout.addWidget(avg_header, 1)
        headers_layout.addWidget(peak_header, 1)
        
        # Add values in a row (much more compact)
        values_layout = QHBoxLayout()
        values_layout.setSpacing(0)
        values_layout.setContentsMargins(0, 0, 0, 0)
        values_layout.addWidget(self.elapsed_label, 1)
        values_layout.addWidget(self.eta_label, 1)
        values_layout.addWidget(self.current_speed_label, 1)
        values_layout.addWidget(self.avg_speed_label, 1)
        values_layout.addWidget(self.peak_speed_label, 1)
        
        # Add both rows to the stats container layout
        stats_container_layout.addLayout(headers_layout)
        stats_container_layout.addLayout(values_layout)
        stats_container_layout.addStretch()  # Push content to top
        
        # Add the separate stats card to main layout
        layout.addWidget(stats_card)
        
        # Add spacing between progress and transfer status
        spacer = QWidget()
        spacer.setFixedHeight(5)  # 5px margin between cards
        layout.addWidget(spacer)
        
        # Files frame - store for later use and ensure proper display
        files_frame = QFrame()
        files_frame.setStyleSheet(CARD_FRAME_STYLE)
        files_frame.setMinimumHeight(60)  # Tighter height for Transfer Status
        files_layout = QVBoxLayout(files_frame)
        files_layout.setSpacing(4)  # Tighter spacing
        files_layout.setContentsMargins(12, 6, 12, 6)  # Tighter top/bottom padding
        
        # Compact Transfer Status display
        files_header = QHBoxLayout()
        files_header.setSpacing(5)
        files_header.setContentsMargins(0, 0, 0, 0)
        files_label = QLabel("Transfer Status")
        files_label.setStyleSheet(SECTION_HEADER_STYLE)
        self.files_count = QLabel("0 of 0 files")
        self.files_count.setStyleSheet(SUMMARY_METRIC_STYLE)
        files_header.addWidget(files_label)
        files_header.addStretch()
        files_header.addWidget(self.files_count)
        files_layout.addLayout(files_header)
        
        layout.addWidget(files_frame, 0)
        
        # Destination progress bars are now properly placed in the destination cards above
        # No need for duplicate destination progress section at the bottom
    
    def handle_job_started(self, payload):
        """Handle job started event"""
        print(f"DEBUG: ProgressSection.handle_job_started called with: {payload}")
        try:
            # Get job data
            total_bytes = payload.get("total_bytes")
            if total_bytes is None:
                total_bytes = payload.get("total", 0)
            total_files = payload.get("total_files", 0)
            print(f"DEBUG: Job started with {total_files} files, {total_bytes} total bytes")
            
            # Initialize job data
            self.job_data = {
                'total_bytes': total_bytes,
                'total_files': total_files,
                'start_time': time.time(),
                'copied_bytes': 0,
                'completed_files': 0,
                'current_speed': 0.0,
                'avg_speed': 0.0,
                'peak_speed': 0.0
            }
            
            # Update UI widgets safely
            if self.total_progress:
                self.total_progress.setValue(0)
                self.total_progress.setFormat("0%")
                print("DEBUG: Total progress bar initialized to 0%")
            
            if self.files_count:
                self.files_count.setText(f"0 of {total_files} files")
                print("DEBUG: Files count initialized")
            
            # No destination widgets to reset - they're in the destination cards
            
            print("DEBUG: ProgressSection.handle_job_started completed successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in ProgressSection.handle_job_started: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_job_progress(self, payload):
        """DEPRECATED: Redirect to handle_progress_update for consistency"""
        print(f"DEBUG: handle_job_progress DEPRECATED - redirecting to handle_progress_update")
        self.handle_progress_update(payload)
    
    # Destination progress is now handled directly in the destination cards
    # No need for separate destination progress handling here
    
    def handle_current_file(self, payload):
        """Handle current file updates"""
        print(f"DEBUG: ProgressSection.handle_current_file called with: {payload}")
        try:
            filename = payload.get("filename", "Processing...")
            print(f"DEBUG: Current file display updated: {filename}")
            
        except Exception as e:
            print(f"DEBUG: Error in ProgressSection.handle_current_file: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_file_progress(self, payload):
        """Handle file progress event - ONLY for logging and file tracking, NOT for main progress bar"""
        try:
            # Throttle file progress updates to prevent UI freezing
            current_time = time.time() * 1000  # Convert to milliseconds
            if not hasattr(self, '_last_file_update'):
                self._last_file_update = 0
                self._file_throttle_ms = 500  # Update file progress max every 500ms
            
            if current_time - self._last_file_update < self._file_throttle_ms:
                return  # Skip this update to prevent UI flooding
            self._last_file_update = current_time
            
            # Extract progress information from Rust engine payload
            # The Rust engine sends: filename, bytes_copied, total_bytes, progress_percent
            filename = payload.get("filename", "Unknown")
            bytes_copied = payload.get("bytes_copied", 0)
            total_bytes = payload.get("total_bytes", 0)
            progress_percent = payload.get("progress_percent", 0.0)
            
            print(f"DEBUG: ProgressSection.handle_file_progress: {filename} - {bytes_copied}/{total_bytes} bytes ({progress_percent:.1f}%)")
            
            # ***** CRITICAL: DO NOT UPDATE MAIN PROGRESS BAR HERE! *****
            # File-level progress should NEVER update the main progress bar
            # Only job-level progress through handle_progress_update() should update the main progress bar
            # This prevents the 0-100% per file jumping behavior
            
            # Update the files count to show current file being processed (if available)
            if hasattr(self, 'files_count') and filename != "Unknown":
                # Show current filename being processed, but don't change the progress bar
                current_text = self.files_count.text()
                if "of" in current_text:
                    # Keep the existing count, just show current file
                    parts = current_text.split("of")
                    if len(parts) == 2:
                        count_part = parts[0].strip()
                        total_part = parts[1].strip()
                        self.files_count.setText(f"{count_part} of {total_part} (processing: {filename[:30]}{'...' if len(filename) > 30 else ''})")
                        print(f"DEBUG: Updated files display to show current file: {filename}")
            
            # ***** DO NOT UPDATE PROGRESS BAR, SPEED, OR PEAK LABELS HERE *****
            # Those should only come from job-level progress updates
            
        except Exception as e:
            print(f"DEBUG: Error in ProgressSection.handle_file_progress: {e}")
            import traceback
            traceback.print_exc()

    def handle_file_completed(self, payload):
        """Handle file completion events"""
        print(f"DEBUG: ProgressSection.handle_file_completed called with: {payload}")
        try:
            filename = payload.get("filename", "Unknown file")
            print(f"DEBUG: File completed: {filename}")
            
        except Exception as e:
            print(f"DEBUG: Error in ProgressSection.handle_file_completed: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_file_failed(self, payload):
        """Handle file failure events"""
        print(f"DEBUG: ProgressSection.handle_file_failed called with: {payload}")
        try:
            filename = payload.get('filename', 'unknown')
            error = payload.get('error', 'unknown error')
            print(f"ERROR: File failed: {filename} - {error}")
            
        except Exception as e:
            print(f"DEBUG: Error in ProgressSection.handle_file_failed: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_job_completed(self, payload):
        """Handle job completion event"""
        print(f"DEBUG: ProgressSection.handle_job_completed called with: {payload}")
        try:
            # Get completion data
            bytes_copied = payload.get("bytes") or payload.get("copied_bytes", 0)
            total_bytes = payload.get("total") or payload.get("total_bytes", 0)
            elapsed = payload.get("elapsed") or payload.get("elapsed_s") or payload.get("data_elapsed_s", 0)
            
            print(f"DEBUG: Job completed: {bytes_copied}/{total_bytes} bytes in {elapsed:.2f}s")
            
            # Update UI to show 100% completion
            if self.total_progress:
                self.total_progress.setValue(100)
                print("DEBUG: Progress bar set to 100%")
            
            if self.elapsed_label:
                elapsed_str = f"{int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d}"
                self.elapsed_label.setText(elapsed_str)
                print("DEBUG: Elapsed label updated")
            
            # Destination widgets are now in the destination cards, not here
            
            print("DEBUG: ProgressSection.handle_job_completed completed successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in ProgressSection.handle_job_completed: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_job_cancelled(self, payload):
        """Handle job cancellation event"""
        print(f"DEBUG: ProgressSection.handle_job_cancelled called with: {payload}")
        try:
            # Reset progress bar
            if self.total_progress:
                self.total_progress.setValue(0)
                self.total_progress.setFormat("0%")
                print("DEBUG: Progress bar reset to 0%")
            
            if self.elapsed_label:
                self.elapsed_label.setText("00:00:00")
            
            if self.files_count:
                self.files_count.setText("0 of 0 files")
            
            # No destination widgets to clear - they're in the destination cards
            
            print("DEBUG: ProgressSection.handle_job_cancelled completed successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in ProgressSection.handle_job_cancelled: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_progress_update(self, payload):
        """Handle progress updates - ONLY from JobState for consistent progress bar behavior"""
        try:
            print(f"DEBUG: ProgressSection.handle_progress_update called with: {payload}")
            
            # Check if this is a JobState-based update (the ONLY supported path)
            if 'progress_percent' in payload and 'total_target_bytes' in payload:
                print(f"DEBUG: JobState-based progress update - using consistent percentage display")
                self._handle_jobstate_percentage_update(payload)
                return
            
            # Check if this is a legacy update that needs conversion
            if 'progress_percent' in payload:
                print(f"DEBUG: Legacy progress update - converting to consistent format")
                self._handle_converted_legacy_update(payload)
                return
                
            # Unknown payload format
            print(f"WARNING: Unknown progress payload format: {list(payload.keys())}")
            
        except Exception as e:
            print(f"ERROR: ProgressSection.handle_progress_update failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_jobstate_percentage_update(self, payload):
        """Handle JobState progress updates using CONSISTENT 0-100 percentage display"""
        try:
            # Extract data from JobState payload
            progress_percent = payload.get("progress_percent", 0.0)
            completed_files = payload.get("completed_files", 0)
            total_files = payload.get("total_files", 0)
            current_speed = payload.get("current_speed_mbps", 0.0)
            peak_speed = payload.get("peak_speed_mbps", 0.0)
            elapsed = payload.get("elapsed_seconds", 0.0)
            eta = payload.get("eta_seconds", 0.0)
            
            print(f"DEBUG: JobState progress: {progress_percent:.1f}% ({completed_files}/{total_files} files)")
            
            # Update progress bar with CONSISTENT 0-100 range (never switch to bytes)
            if hasattr(self, 'total_progress') and self.total_progress:
                # Always use percentage range 0-100 for consistency
                self.total_progress.setRange(0, 100)
                self.total_progress.setValue(int(progress_percent))
                self.total_progress.setFormat(f"{int(progress_percent)}%")
                # CRITICAL FIX: Force Qt to repaint immediately
                self.total_progress.update()
                self.total_progress.repaint()
                print(f"DEBUG: Progress bar updated to {int(progress_percent)}% (0-100 range)")

            # Update other UI elements - pass bytes_copied for average speed calculation
            bytes_copied = payload.get("bytes_copied", 0)
            self._update_speed_labels(current_speed, peak_speed, elapsed, bytes_copied)
            self._update_elapsed_label(elapsed)
            self._update_files_count(completed_files, total_files)
            self._update_eta_label(eta)

            # CRITICAL FIX: Force entire section to repaint
            self.update()
            self.repaint()
            
        except Exception as e:
            print(f"ERROR: JobState percentage update failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_converted_legacy_update(self, payload):
        """Handle legacy progress updates converted to consistent format"""
        try:
            # CRITICAL FIX: Use correct field names from event pump payload
            progress_percent = payload.get("progress_percent", 0.0)
            # Event pump sends 'files_completed' not 'completed_files'
            files_completed = payload.get("files_completed", 0)
            total_files = payload.get("total_files", 0)
            # Event pump sends 'current_speed_mbps' and 'speed_mbps'
            current_speed = payload.get("current_speed_mbps", payload.get("speed_mbps", 0.0))
            peak_speed = payload.get("peak_speed_mbps", 0.0)
            # Event pump sends 'elapsed_s' not 'elapsed_time'
            elapsed = payload.get("elapsed_s", payload.get("elapsed_time", 0.0))
            # Calculate ETA from elapsed and progress if not provided
            eta_seconds = payload.get("eta_seconds", 0.0)
            if eta_seconds == 0.0 and progress_percent > 0:
                eta_seconds = (elapsed / progress_percent * 100.0) - elapsed

            print(f"DEBUG: Event pump progress: {progress_percent:.1f}% ({files_completed}/{total_files} files, {current_speed:.1f} MB/s, elapsed: {elapsed:.1f}s)")

            # Update progress bar with CONSISTENT 0-100 range
            if hasattr(self, 'total_progress') and self.total_progress:
                self.total_progress.setRange(0, 100)
                self.total_progress.setValue(int(progress_percent))
                self.total_progress.setFormat(f"{int(progress_percent)}%")
                # CRITICAL FIX: Force Qt to repaint immediately
                self.total_progress.update()
                self.total_progress.repaint()
                print(f"DEBUG: Progress bar updated to {int(progress_percent)}% (0-100 range)")

            # Update other UI elements with correct field names
            bytes_copied = payload.get("bytes_copied", 0)
            self._update_speed_labels(current_speed, peak_speed, elapsed, bytes_copied)
            self._update_elapsed_label(elapsed)
            self._update_files_count(files_completed, total_files)
            self._update_eta_label(eta_seconds)

            # CRITICAL FIX: Force entire section to repaint
            self.update()
            self.repaint()
            
        except Exception as e:
            print(f"ERROR: Legacy progress conversion failed: {e}")
            import traceback
            traceback.print_exc()
    
# OLD CONFLICTING METHODS REMOVED - replaced with consistent percentage-based approach
    # These methods were causing progress bar range conflicts between byte-based and percentage-based displays
    
    def _update_speed_labels(self, current_speed, peak_speed, elapsed, bytes_copied=0):
        """Update speed-related labels"""
        try:
            if hasattr(self, 'current_speed_label') and self.current_speed_label:
                self.current_speed_label.setText(f"{current_speed:.0f} MB/s")
                print(f"DEBUG: Updated current speed to {current_speed:.0f} MB/s")
            
            if hasattr(self, 'peak_speed_label') and self.peak_speed_label:
                self.peak_speed_label.setText(f"{peak_speed:.0f} MB/s")
                print(f"DEBUG: Updated peak speed to {peak_speed:.0f} MB/s")
                
            if hasattr(self, 'avg_speed_label') and self.avg_speed_label and elapsed > 0 and bytes_copied > 0:
                # Calculate average speed from actual bytes_copied and elapsed time
                avg_speed = (bytes_copied / (1024 * 1024)) / elapsed
                self.avg_speed_label.setText(f"{avg_speed:.0f} MB/s")
                print(f"DEBUG: Updated average speed to {avg_speed:.0f} MB/s (calculated from {bytes_copied} bytes in {elapsed:.1f}s)")
                    
        except Exception as e:
            print(f"ERROR: Speed labels update failed: {e}")
    
    def _update_files_count(self, completed_files, total_files):
        """Update files count label"""
        try:
            if hasattr(self, 'files_count') and self.files_count:
                self.files_count.setText(f"{completed_files} of {total_files} files")
                print(f"DEBUG: Updated files count to {completed_files}/{total_files}")
        except Exception as e:
            print(f"ERROR: Files count update failed: {e}")
    
    def _update_eta_label(self, eta_seconds):
        """Update ETA label"""
        try:
            if hasattr(self, 'eta_label') and self.eta_label:
                if eta_seconds > 0:
                    eta_str = f"{int(eta_seconds//3600):02d}:{int((eta_seconds%3600)//60):02d}:{int(eta_seconds%60):02d}"
                    self.eta_label.setText(eta_str)
                else:
                    self.eta_label.setText("--:--:--")
        except Exception as e:
            print(f"ERROR: ETA label update failed: {e}")
    
    def _update_elapsed_label(self, elapsed_seconds):
        """Update elapsed time label"""
        try:
            if hasattr(self, 'elapsed_label') and self.elapsed_label:
                elapsed_str = f"{int(elapsed_seconds//3600):02d}:{int((elapsed_seconds%3600)//60):02d}:{int(elapsed_seconds%60):02d}"
                self.elapsed_label.setText(elapsed_str)
                print(f"DEBUG: Updated elapsed time to {elapsed_str}")
        except Exception as e:
            print(f"ERROR: Elapsed time label update failed: {e}")
            
            # Update speed
            if hasattr(self, 'current_speed_label'):
                self.current_speed_label.setText(f"{speed_mbps:.1f} MB/s")
                print(f"DEBUG: Updated current speed to {speed_mbps:.1f} MB/s")
            
            # Update average speed
            if hasattr(self, 'avg_speed_label'):
                self.avg_speed_label.setText(f"{speed_mbps:.1f} MB/s")
                print(f"DEBUG: Updated average speed to {speed_mbps:.1f} MB/s")
            
            # Update peak speed - use peak from payload if available
            if hasattr(self, 'peak_speed_label'):
                peak_speed = payload.get('peak_speed_mbps', speed_mbps)
                if peak_speed > 0:
                    self.peak_speed_label.setText(f"{peak_speed:.1f} MB/s")
                    print(f"DEBUG: Updated peak speed to {peak_speed:.1f} MB/s")
                else:
                    # Fallback to local peak calculation if no peak in payload
                    try:
                        current_peak_text = self.peak_speed_label.text()
                        if " MB/s" in current_peak_text:
                            current_peak = float(current_peak_text.split(' ')[0])
                            if speed_mbps > current_peak:
                                self.peak_speed_label.setText(f"{speed_mbps:.1f} MB/s")
                                print(f"DEBUG: Updated peak speed to {speed_mbps:.1f} MB/s (local calc)")
                        else:
                            self.peak_speed_label.setText(f"{speed_mbps:.1f} MB/s")
                    except (ValueError, IndexError):
                        self.peak_speed_label.setText(f"{speed_mbps:.1f} MB/s")
            
            # Calculate ETA
            bytes_copied = payload.get('bytes_copied', 0)
            total_bytes = payload.get('total_bytes', 0)
            if hasattr(self, 'eta_label') and speed_mbps > 0 and bytes_copied < total_bytes:
                remaining_bytes = total_bytes - bytes_copied
                eta_seconds = remaining_bytes / (speed_mbps * 1024 * 1024)
                if eta_seconds > 0:
                    eta_str = f"{int(eta_seconds//3600):02d}:{int((eta_seconds%3600)//60):02d}:{int(eta_seconds%60):02d}"
                    self.eta_label.setText(eta_str)
                    print(f"DEBUG: Updated ETA to {eta_str}")
                else:
                    self.eta_label.setText("--:--:--")
            elif hasattr(self, 'eta_label'):
                self.eta_label.setText("--:--:--")
            
        except Exception as e:
            print(f"DEBUG: Error handling progress_update: {e}")
            import traceback
            traceback.print_exc()
    
    def mark_transfer_completed(self):
        """Mark transfer as completed and switch to green styling"""
        try:
            print("DEBUG: Marking transfer as completed with green styling")
            
            # Update progress bar to 100% and switch to green
            if hasattr(self, 'total_progress'):
                self.total_progress.setValue(100)
                self.total_progress.setFormat("100%")
                
                # Switch to green gradient for completion
                self.total_progress.setStyleSheet(f"""
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
                                                   stop:0 #16a34a, 
                                                   stop:0.5 #22c55e, 
                                                   stop:1 #4ade80);
                        border-radius: 2px;
                    }}
                """)
                print("DEBUG: Progress bar switched to green completion styling")
            
            # Update status to show completion
            if hasattr(self, 'status_label'):
                self.status_label.setText("Transfer Complete")
                print("DEBUG: Status updated to 'Transfer Complete'")
                
        except Exception as e:
            print(f"DEBUG: Error marking transfer as completed: {e}")
            import traceback
            traceback.print_exc()
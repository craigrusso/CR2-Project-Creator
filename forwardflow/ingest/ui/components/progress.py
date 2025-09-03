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
                                           stop:0 #2d5a2d, 
                                           stop:0.5 #4a7c4a, 
                                           stop:1 #6ba06b);
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
                                           stop:0 #2d5a2d, 
                                           stop:0.5 #4a7c4a, 
                                           stop:1 #6ba06b);
                border-radius: 2px;
            }}
        """)
        self.total_progress.setVisible(True)
        self.total_progress.setEnabled(True)
        self.total_progress.setFormat("%p%")
        self.total_progress.setTextVisible(True)
        
        # Add progress bar with normal layout
        progress_layout.addWidget(self.total_progress)
        
        # Add stats labels BELOW the progress bar (not inside it)
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(1)  # Minimal spacing between header and values
        stats_layout.setContentsMargins(12, 8, 12, 4)  # Added top margin to separate from progress bar
        
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
                padding: 2px;
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
                padding: 2px;
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
                padding: 2px;
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
                padding: 2px;
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
                padding: 2px;
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
        
        # Add both rows to stats layout
        stats_layout.addLayout(headers_layout)
        stats_layout.addLayout(values_layout)
        
        # Add the stats layout to the progress frame instead of creating a separate frame
        progress_layout.addLayout(stats_layout)
        

        
        layout.addWidget(progress_frame, 0)
        
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
        """Handle job progress event"""
        print(f"DEBUG: ProgressSection.handle_job_progress called with: {payload}")
        try:
            if not self.job_data:
                print("DEBUG: No job data available, skipping progress update")
                return
            
            # Extract progress data
            copied_bytes = payload.get("copied_bytes") or payload.get("bytes", 0)
            total_bytes = payload.get("total_bytes") or payload.get("total", 0)
            completed_files = payload.get("completed_files") or payload.get("files_completed", 0)
            total_files = payload.get("total_files", 0)
            current_speed = payload.get("speed_mbps") or payload.get("speed", 0.0)
            elapsed = payload.get("elapsed") or payload.get("elapsed_time", 0.0)
            
            # Update job data
            self.job_data['copied_bytes'] = copied_bytes
            self.job_data['completed_files'] = completed_files
            self.job_data['current_speed'] = current_speed
            
            # Calculate average speed
            if elapsed > 0:
                self.job_data['avg_speed'] = (copied_bytes / (1024 * 1024)) / elapsed
            
            # Update peak speed
            if current_speed > self.job_data['peak_speed']:
                self.job_data['peak_speed'] = current_speed
            
            # Update progress bar (only if it exists and hasn't been updated recently)
            if hasattr(self, 'total_progress') and self.total_progress:
                progress_percent = int((copied_bytes / total_bytes) * 100) if total_bytes > 0 else 0
                # Only update if the value has changed significantly
                if not hasattr(self, '_last_progress_percent') or abs(progress_percent - self._last_progress_percent) >= 1:
                    self.total_progress.setValue(progress_percent)
                    self.total_progress.setFormat(f"{progress_percent}%")
                    self._last_progress_percent = progress_percent
            
            # Update current speed stat (only if it exists)
            if self.current_speed_label:
                self.current_speed_label.setText(f"{current_speed:.0f} MB/s")
                print("DEBUG: Current speed label updated")
            
            # Calculate average speed (only if it exists)
            if self.avg_speed_label:
                avg_speed = self.job_data['avg_speed']
                self.avg_speed_label.setText(f"{avg_speed:.0f} MB/s")
                print("DEBUG: Avg speed label updated")
            
            # Update peak speed if current speed is higher (only if it exists)
            if self.peak_speed_label:
                try:
                    current_peak_text = self.peak_speed_label.text()
                    # Parse current peak value (format: "XXX MB/s" or "0 MB/s")
                    if " MB/s" in current_peak_text:
                        current_peak = float(current_peak_text.split(' ')[0])
                        if current_speed > current_peak:
                            self.peak_speed_label.setText(f"{current_speed:.0f} MB/s")
                    else:
                        # If we can't parse, initialize with current speed
                        self.peak_speed_label.setText(f"{current_speed:.0f} MB/s")
                except (ValueError, IndexError):
                    # If we can't parse the current peak, just set it
                    self.peak_speed_label.setText(f"{current_speed:.0f} MB/s")
            
            # Calculate ETA (only if it exists)
            if self.eta_label and current_speed > 0 and copied_bytes < total_bytes:
                remaining_bytes = total_bytes - copied_bytes
                eta_seconds = remaining_bytes / (current_speed * 1024 * 1024)
                if eta_seconds > 0:
                    eta_str = f"{int(eta_seconds//3600):02d}:{int((eta_seconds%3600)//60):02d}:{int(eta_seconds%60):02d}"
                    self.eta_label.setText(eta_str)
                else:
                    self.eta_label.setText("--:--:--")
            elif self.eta_label:
                self.eta_label.setText("--:--:--")
            
            # Update elapsed time
            if self.elapsed_label:
                elapsed_str = f"{int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d}"
                self.elapsed_label.setText(elapsed_str)
            
            # Update files count
            if self.files_count:
                self.files_count.setText(f"{completed_files} of {total_files} files")
            
            print("DEBUG: ProgressSection.handle_job_progress completed successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in ProgressSection.handle_job_progress: {e}")
            import traceback
            traceback.print_exc()
    
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
        """Handle file progress event - this is the key method for updating progress bars"""
        try:
            # Extract progress information from C++ engine payload
            # The C++ engine sends: filename, bytes_copied, total_bytes, progress_percent
            filename = payload.get("filename", "Unknown")
            bytes_copied = payload.get("bytes_copied", 0)
            total_bytes = payload.get("total_bytes", 0)
            progress_percent = payload.get("progress_percent", 0.0)
            
            print(f"DEBUG: ProgressSection.handle_file_progress: {filename} - {bytes_copied}/{total_bytes} bytes ({progress_percent:.1f}%)")
            
            # Update the main progress bar if we have valid data
            if total_bytes > 0 and hasattr(self, 'total_progress'):
                # Use the progress_percent from C++ engine directly
                progress_percent_int = int(progress_percent)
                self.total_progress.setValue(progress_percent_int)
                self.total_progress.setFormat(f"{progress_percent_int}%")
                print(f"DEBUG: Updated main progress bar to {progress_percent_int}%")
            
            # Update the files count to show current file progress
            if hasattr(self, 'files_count') and total_bytes > 0:
                mb_copied = bytes_copied / (1024 * 1024)
                mb_total = total_bytes / (1024 * 1024)
                self.files_count.setText(f"{filename}: {mb_copied:.1f}/{mb_total:.1f} MB")
            
            # Calculate current speed based on progress updates
            # Since C++ engine doesn't provide speed, we'll calculate it from progress
            if hasattr(self, 'current_speed_label'):
                # For now, show progress percentage as speed indicator
                # In a real implementation, you'd want to track time between updates
                self.current_speed_label.setText(f"{progress_percent:.1f}%")
            
            # Update peak speed if current progress is higher
            if hasattr(self, 'peak_speed_label'):
                try:
                    current_peak_text = self.peak_speed_label.text()
                    if " %" in current_peak_text:
                        current_peak = float(current_peak_text.split(' ')[0])
                        if progress_percent > current_peak:
                            self.peak_speed_label.setText(f"{progress_percent:.1f}%")
                    else:
                        self.peak_speed_label.setText(f"{progress_percent:.1f}%")
                except (ValueError, IndexError):
                    self.peak_speed_label.setText(f"{progress_percent:.1f}%")
            
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

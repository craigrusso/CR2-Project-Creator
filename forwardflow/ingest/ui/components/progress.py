"""Progress Section for Ingest Tab"""

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame
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


class ProgressSection(QWidget):
    """Progress Section with exact original design"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
            
            # Update UI widgets safely
            if self.total_progress:
                # Keep the progress bar at 0-100 range for percentage
                self.total_progress.setValue(0)
                self.total_progress.setVisible(True)
                print("DEBUG: Total progress bar updated")
            
            if self.elapsed_label:
                self.elapsed_label.setText("00:00:00")
                print("DEBUG: Elapsed label updated")
            
            # Update file count display
            if self.files_count:
                self.files_count.setText(f"0 of {total_files} files")
                print(f"DEBUG: File count display updated to show 0 of {total_files} files")
            
            print("DEBUG: ProgressSection.handle_job_started completed successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in ProgressSection.handle_job_started: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_job_progress(self, payload):
        """Handle job progress event"""
        print(f"DEBUG: ProgressSection.handle_job_progress called with: {payload}")
        try:
            # Get progress data
            copied_bytes = payload.get("copied_bytes")
            if copied_bytes is None:
                copied_bytes = payload.get("bytes_copied")
            if copied_bytes is None:
                copied_bytes = payload.get("bytes", 0)

            total_bytes = payload.get("total_bytes")
            if total_bytes is None:
                total_bytes = payload.get("total", 0)
            
            print(f"DEBUG: Job progress: {copied_bytes}/{total_bytes} bytes")
            
            # Check for file completion information in progress payload
            completed_files_from_payload = payload.get("files_completed")
            if completed_files_from_payload is not None:
                print(f"DEBUG: Found files_completed in engine payload: {completed_files_from_payload}")
                # Update using engine data
                if self.files_count:
                    self.files_count.setText(f"{completed_files_from_payload} of {payload.get('total_files', 0)} files")
                    print(f"DEBUG: Updated file count from engine: {completed_files_from_payload}")
            
            # Calculate percentage to avoid overflow
            if total_bytes > 0:
                progress_percent = min(int((copied_bytes * 100) // total_bytes), 100)
            else:
                progress_percent = 0
            
            # Update total progress bar with percentage
            if self.total_progress:
                self.total_progress.setValue(progress_percent)
                print(f"DEBUG: Total progress bar updated to {progress_percent}%")
            
            # Update speed and elapsed time
            if hasattr(self, 'job_data') and self.job_data:
                elapsed_from_engine = payload.get("elapsed_time")
                if elapsed_from_engine is not None:
                    elapsed = float(elapsed_from_engine)
                else:
                    elapsed = time.time() - self.job_data['start_time']

                if self.elapsed_label:
                    elapsed_str = f"{int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d}"
                    self.elapsed_label.setText(elapsed_str)
                    print("DEBUG: Elapsed label updated")
            
            print("DEBUG: ProgressSection.handle_job_progress completed successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in ProgressSection.handle_job_progress: {e}")
            import traceback
            traceback.print_exc()
    
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
            
            print("DEBUG: ProgressSection.handle_job_cancelled completed successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in ProgressSection.handle_job_cancelled: {e}")
            import traceback
            traceback.print_exc()

"""Source and Destination Section for Ingest Tab"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QFrame, QScrollArea, QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
import time
import os
from typing import Dict, Optional

try:
    from app.ui.color_scheme_pyqt import (
        colors, BUTTON_STYLE, COMBOBOX_STYLE, GROUPBOX_STYLE, 
        FIELD_LABEL_STYLE, SCROLL_AREA_STYLE, CARD_FRAME_STYLE,
        LABEL_STYLE, SECONDARY_TEXT_STYLE, HEADER_LABEL_STYLE
    )
    from app.ui.custom_delegates import apply_hover_delegate
    STYLING_AVAILABLE = True
except ImportError as e:
    print(f"DEBUG: Failed to import centralized styles: {e}")
    raise ImportError("Centralized styles are required for the ingest tab")


class DestinationWidget(QFrame):
    """Individual destination widget with transfer type detection"""
    
    def __init__(self, path, parent=None, parent_section=None):
        super().__init__(parent)
        self.path = path
        self.parent_section = parent_section  # Reference to SourceDestinationSection
        
        # Smoothing state for destination metrics
        self.current_values = {
            'progress': 0.0,
            'current_speed': 0.0,
            'peak_speed': 0.0,
            'eta_seconds': 0.0
        }
        self.target_values = {
            'progress': 0.0,
            'current_speed': 0.0,
            'peak_speed': 0.0,
            'eta_seconds': 0.0
        }
        
        # DISABLED: Smoothing timer causes GIL deadlock with Rust worker thread
        # Updates now come directly from event pump
        # self.smooth_timer = QTimer()
        # self.smooth_timer.timeout.connect(self._smooth_update)
        # self.smooth_timer.setInterval(16)  # ~60 FPS (16.67ms)
        
        # Animation parameters
        self.animation_speed = 0.15  # Interpolation factor (0.1 = slower, 0.3 = faster)
        self.min_speed_threshold = 0.1  # Minimum speed change to trigger update
        self.last_update_time = time.time()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the destination widget UI"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Top row: path and controls
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        top_row.setContentsMargins(0, 0, 0, 0)
        
        # Path display
        path_label = QLabel(self.path)
        path_label.setStyleSheet(LABEL_STYLE)
        path_label.setWordWrap(True)
        path_label.setMinimumHeight(28)
        path_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        top_row.addWidget(path_label, 1)
        
        # Preset dropdown
        preset_combo = QComboBox()
        preset_combo.addItems(["Auto", "USB/TB", "Network", "Custom"])
        preset_combo.setCurrentText("Auto")
        preset_combo.setStyleSheet(COMBOBOX_STYLE)
        preset_combo.setFixedHeight(28)
        preset_combo.setMinimumWidth(100)
        top_row.addWidget(preset_combo)
        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #902A2A;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #A33030;
            }}
        """)
        remove_btn.clicked.connect(self.remove_self)
        top_row.addWidget(remove_btn)
        
        layout.addLayout(top_row)
        
        # Transfer type and buffer info row
        info_row = QHBoxLayout()
        info_row.setSpacing(15)
        
        # Detect transfer type and optimal buffer size
        print(f"DEBUG: Attempting to detect transfer type for destination: {self.path}")
        try:
            from forwardflow.ingest.utils.memory_manager import MemoryManager
            print("DEBUG: Successfully imported MemoryManager")
            memory_manager = MemoryManager()
            print("DEBUG: Created MemoryManager instance")
            transfer_type = memory_manager._detect_transfer_type(self.path)
            print(f"DEBUG: Detected transfer type: {transfer_type}")
            optimal_buffer = memory_manager.get_optimal_buffer_size_for_destination(self.path, "auto")
            print(f"DEBUG: Calculated optimal buffer: {optimal_buffer:.1f}MB")
            
            # Transfer type label
            type_label = QLabel(f"Type: {transfer_type.upper()}")
            type_label.setStyleSheet(SECONDARY_TEXT_STYLE)
            type_label.setMinimumHeight(24)
            type_label.setFixedHeight(24)
            type_label.setMinimumWidth(120)
            info_row.addWidget(type_label)
            print(f"DEBUG: Added type label: Type: {transfer_type.upper()}")
            
            # Optimal buffer size label
            buffer_label = QLabel(f"Optimal Buffer: {optimal_buffer:.1f}MB")
            buffer_label.setStyleSheet(SECONDARY_TEXT_STYLE)
            buffer_label.setMinimumHeight(24)
            buffer_label.setFixedHeight(24)
            buffer_label.setMinimumWidth(150)
            info_row.addWidget(buffer_label)
            print(f"DEBUG: Added buffer label: Optimal Buffer: {optimal_buffer:.1f}MB")
            
        except Exception as e:
            print(f"DEBUG: Could not detect transfer type for {self.path}: {e}")
            import traceback
            traceback.print_exc()
            # Fallback labels
            type_label = QLabel("Type: Unknown")
            type_label.setStyleSheet(SECONDARY_TEXT_STYLE)
            type_label.setMinimumHeight(24)
            type_label.setFixedHeight(24)
            type_label.setMinimumWidth(120)
            info_row.addWidget(type_label)
            
            buffer_label = QLabel("Optimal Buffer: 1.0MB")
            buffer_label.setStyleSheet(SECONDARY_TEXT_STYLE)
            buffer_label.setMinimumHeight(24)
            buffer_label.setFixedHeight(24)
            buffer_label.setMinimumWidth(150)
            info_row.addWidget(buffer_label)
        
        info_row.addStretch()
        layout.addLayout(info_row)
        
        # Progress bar row with enhanced information
        progress_row = QHBoxLayout()
        progress_row.setSpacing(5)
        
        # Progress bar for this destination
        dest_progress = QProgressBar()
        dest_progress.setRange(0, 100)
        dest_progress.setValue(0)
        dest_progress.setFixedHeight(20)  # Slightly taller for better visibility
        dest_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {colors['border']};
                border-radius: 2px;
                text-align: center;
                background-color: {colors['bg']};
                color: {colors['text']};
                font-size: 10px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                           stop:0 #2563eb, 
                                           stop:0.5 #3b82f6, 
                                           stop:1 #60a5fa);
                border-radius: 1px;
            }}
        """)
        dest_progress.setVisible(True)  # Always show progress bar for destination tracking
        dest_progress.setFormat("Dest: %p%")
        dest_progress.setTextVisible(True)
        progress_row.addWidget(dest_progress, 1)
        
        layout.addLayout(progress_row)
        
        # Destination speed and status row - simple layout
        speed_row = QHBoxLayout()
        speed_row.setSpacing(15)
        speed_row.setContentsMargins(0, 2, 0, 2)
        
        # Current speed label
        current_speed_label = QLabel("0 MB/s")
        current_speed_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['accent']};
                font-size: 14px;
                font-weight: 600;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            }}
        """)
        current_speed_label.setFixedHeight(24)
        current_speed_label.setMinimumWidth(80)
        
        # Peak speed label
        peak_speed_label = QLabel("Peak: 0 MB/s")
        peak_speed_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['secondary_text']};
                font-size: 12px;
                font-weight: 500;
            }}
        """)
        peak_speed_label.setFixedHeight(24)
        peak_speed_label.setMinimumWidth(100)
        
        # ETA label
        eta_label = QLabel("ETA: --:--")
        eta_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                font-size: 12px;
                font-weight: 500;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            }}
        """)
        eta_label.setFixedHeight(24)
        eta_label.setMinimumWidth(80)
        
        # Status label
        status_label = QLabel("Ready")
        status_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['secondary_text']};
                font-size: 12px;
                font-weight: 500;
                padding: 2px 6px;
                border-radius: 4px;
                background-color: {colors['bg']};
            }}
        """)
        status_label.setFixedHeight(24)
        status_label.setMinimumWidth(60)
        
        speed_row.addWidget(current_speed_label)
        speed_row.addWidget(peak_speed_label)
        speed_row.addWidget(eta_label)
        speed_row.addStretch()
        speed_row.addWidget(status_label)
        
        layout.addLayout(speed_row)
        
        # Store references
        self.preset_combo = preset_combo
        self.remove_btn = remove_btn
        self.dest_progress = dest_progress
        self.current_speed_label = current_speed_label
        self.peak_speed_label = peak_speed_label
        self.eta_label = eta_label
        self.status_label = status_label
        
        # DISABLED: Smoothing timer causes GIL deadlock
        # self.smooth_timer.start()
        # print(f"DEBUG: Started smoothing timer for destination {self.path}")
        
    def remove_self(self):
        """Remove this destination widget"""
        # Clean up timers before removal
        self.cleanup_timers()
        
        if self.parent_section and hasattr(self.parent_section, 'remove_destination'):
            self.parent_section.remove_destination(self)
    
    def update_progress(self, progress_payload):
        """Update destination-specific progress metrics with smooth animation"""
        try:
            # Handle both destination-specific and general progress events
            dest_path = progress_payload.get('dest_path', '')
            
            print(f"DEBUG: DestinationWidget.update_progress for {self.path}, payload dest: {dest_path}")
            
            # If this is a destination-specific event and it's not for this destination, skip it
            if dest_path and dest_path != self.path and dest_path != 'current_destination':
                print(f"DEBUG: Skipping update for {self.path} - not matching {dest_path}")
                return
            
            # Extract values from payload
            progress_percent = progress_payload.get('progress_percent', 0)
            current_speed = (progress_payload.get('currentSpeedMiBps', 0) or 
                           progress_payload.get('current_speed_mbps', 0))
            
            # Update peak speed - try multiple field names for compatibility  
            peak_speed = (progress_payload.get('peakSpeedMiBps', 0) or
                         progress_payload.get('peak_speed_mbps', 0))
            
            print(f"DEBUG: Updating {self.path} with progress={progress_percent:.1f}%, speed={current_speed:.1f}, peak={peak_speed:.1f}")
            
            # Update speed label immediately (check for correct attribute name)
            if hasattr(self, 'current_speed_label') and self.current_speed_label:
                self.current_speed_label.setText(f"{current_speed:.1f} MB/s")
                print(f"DEBUG: Updated current_speed_label for {self.path} to {current_speed:.1f} MB/s")
            elif hasattr(self, 'speed_label') and self.speed_label:
                self.speed_label.setText(f"{current_speed:.1f} MB/s")
                print(f"DEBUG: Updated speed_label for {self.path} to {current_speed:.1f} MB/s")
            else:
                print(f"DEBUG: WARNING: No speed label found for {self.path}")
                print(f"DEBUG: Available attributes: {[attr for attr in dir(self) if 'speed' in attr.lower() or 'label' in attr.lower()]}")
            
            # Update peak speed label immediately (no smoothing for peaks)
            if hasattr(self, 'peak_speed_label') and self.peak_speed_label:
                self.peak_speed_label.setText(f"Peak: {peak_speed:.1f} MB/s")
                print(f"DEBUG: Updated peak_speed_label for {self.path} to {peak_speed:.1f} MB/s")
            else:
                print(f"DEBUG: WARNING: No peak_speed_label found for {self.path}")
                print(f"DEBUG: Available attributes: {[attr for attr in dir(self) if 'peak' in attr.lower() or 'label' in attr.lower()]}")
            
            # Extract values for smoothing
            eta_seconds = progress_payload.get('etaS', 0) or progress_payload.get('eta_seconds', 0)
            
            current_time = time.time()
            time_delta = current_time - self.last_update_time
            
            # Update target values for smooth interpolation
            self.target_values['progress'] = progress_percent
            self.target_values['current_speed'] = current_speed
            
            # Peak speed should only increase (no smoothing for peaks)
            if peak_speed > self.current_values['peak_speed']:
                self.current_values['peak_speed'] = peak_speed
                self.target_values['peak_speed'] = peak_speed
                self.peak_speed_label.setText(f"Peak: {peak_speed:.1f} MB/s")
            
            self.target_values['eta_seconds'] = eta_seconds
            self.last_update_time = current_time

            # CRITICAL FIX: Update current values immediately (no smoothing) to avoid GIL deadlock from QTimer
            self.current_values['progress'] = progress_percent
            self.current_values['current_speed'] = current_speed
            self.current_values['eta_seconds'] = eta_seconds

            # Immediate updates for status changes
            if progress_percent >= 100:
                self.status_label.setText("Completed")
                self.status_label.setStyleSheet("color: #10b981; font-weight: bold;")
                # Set final values immediately
                self.current_values['progress'] = 100.0
            elif progress_percent > 0:
                self.status_label.setText("Transferring")
                self.status_label.setStyleSheet("color: #3b82f6; font-weight: bold;")
            else:
                self.status_label.setText("Ready")

            # CRITICAL FIX: Manually update UI elements and force repaint (no QTimer)
            self._update_ui_elements()

            # CRITICAL FIX: Force Qt to repaint immediately
            self.update()  # Schedule repaint
            self.repaint()  # Force immediate repaint

            print(f"DEBUG: Updated target values for destination {dest_path}: progress={progress_percent:.1f}%, speed={current_speed:.1f}MB/s")
            
        except Exception as e:
            print(f"DEBUG: Error updating destination progress: {e}")
            import traceback
            traceback.print_exc()
    
    def _smooth_update(self):
        """Smooth interpolation update called by timer"""
        try:
            # Calculate interpolation for each metric
            progress_diff = self.target_values['progress'] - self.current_values['progress']
            speed_diff = self.target_values['current_speed'] - self.current_values['current_speed']
            eta_diff = self.target_values['eta_seconds'] - self.current_values['eta_seconds']
            
            # Apply smoothing with different speeds for different metrics
            progress_smooth = self.animation_speed * 1.5  # Faster for progress
            speed_smooth = self.animation_speed * 2.0     # Faster for speed (more responsive)
            eta_smooth = self.animation_speed * 1.0       # Slower for ETA (less jarring)
            
            # Update current values with interpolation
            self.current_values['progress'] += progress_diff * progress_smooth
            self.current_values['current_speed'] += speed_diff * speed_smooth
            self.current_values['eta_seconds'] += eta_diff * eta_smooth
            
            # Stop smoothing if we're close enough to target values
            if (abs(progress_diff) < 0.1 and 
                abs(speed_diff) < self.min_speed_threshold and 
                abs(eta_diff) < 1.0):
                # Snap to exact values
                self.current_values['progress'] = self.target_values['progress']
                self.current_values['current_speed'] = self.target_values['current_speed']
                self.current_values['eta_seconds'] = self.target_values['eta_seconds']
            
            # Update UI elements with smoothed values
            self._update_ui_elements()
            
        except Exception as e:
            print(f"DEBUG: Error in smooth update: {e}")
    
    def _update_ui_elements(self):
        """Update UI elements with current smoothed values"""
        try:
            # Update progress bar
            progress_value = max(0, min(100, int(self.current_values['progress'])))
            self.dest_progress.setValue(progress_value)
            self.dest_progress.setFormat(f"Dest: {progress_value}%")
            
            # Update current speed with smooth animation
            current_speed = max(0, self.current_values['current_speed'])
            self.current_speed_label.setText(f"{current_speed:.1f} MB/s")
            
            # Update ETA with smoothing
            eta_seconds = max(0, self.current_values['eta_seconds'])
            if eta_seconds > 0:
                hours = int(eta_seconds // 3600)
                minutes = int((eta_seconds % 3600) // 60)
                seconds = int(eta_seconds % 60)
                self.eta_label.setText(f"ETA: {hours:02d}:{minutes:02d}:{seconds:02d}")
            else:
                self.eta_label.setText("ETA: --:--")
                
        except Exception as e:
            print(f"DEBUG: Error updating UI elements: {e}")
    
    def cleanup_timers(self):
        """Clean up timers when widget is destroyed"""
        if hasattr(self, 'smooth_timer') and self.smooth_timer.isActive():
            self.smooth_timer.stop()
            print(f"DEBUG: Stopped smoothing timer for destination {self.path}")


class SourceDestinationSection(QWidget):
    """Source and Destination Section with exact original design"""
    
    # Signal emitted when destinations change
    destinations_changed = pyqtSignal()
    
    def __init__(self, parent=None, recent_sources=None, recent_destinations=None):
        super().__init__(parent)
        self.destination_widgets = []
        self.recent_sources = recent_sources or []
        self.recent_destinations = recent_destinations or []
        
        # Timer to periodically check destination availability
        # DISABLED: Availability timer causes GIL deadlock with Rust worker thread
        # Destination availability checked on-demand only
        # self.availability_timer = QTimer()
        # self.availability_timer.timeout.connect(self.refresh_destination_availability)
        # self.availability_timer.setSingleShot(False)
        # self.availability_timer.setInterval(30000)  # Check every 30 seconds
        
        self.setup_ui()
        self.populate_recent_locations()
        
        # DISABLED: Availability timer causes GIL deadlock
        # self.availability_timer.start()
        # print("DEBUG: Started destination availability checking timer (30s interval)")
        
    def setup_ui(self):
        """Setup the source and destination UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title at the very top with minimal margin
        title = QLabel("Turbo Transfer")
        title.setStyleSheet(HEADER_LABEL_STYLE)
        title.setMinimumHeight(28)  # Use minimum height instead of fixed
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title.setContentsMargins(10, 2, 10, 2)
        layout.addWidget(title)
        
        # Paths section
        paths_layout = QVBoxLayout()
        paths_layout.setSpacing(8)
        paths_layout.setContentsMargins(0, 0, 0, 0)
        
        # Source section - inline layout
        src_layout = QHBoxLayout()
        src_layout.setSpacing(10)
        src_layout.setContentsMargins(0, 0, 0, 0)
        
        src_label = QLabel("Source:")
        src_label.setStyleSheet(FIELD_LABEL_STYLE)
        src_label.setFixedHeight(38)
        src_label.setFixedWidth(60)
        src_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.src_combo = QComboBox()
        self.src_combo.setEditable(True)
        self.src_combo.setStyleSheet(COMBOBOX_STYLE)
        self.src_combo.setPlaceholderText("Select source folder...")
        self.src_combo.setFixedHeight(38)
        self.src_combo.setMinimumHeight(38)
        self.src_combo.setMaximumHeight(38)
        
        # Apply hover delegate for proper hover effects and clickable area
        try:
            apply_hover_delegate(self.src_combo)
            print("DEBUG: Applied hover delegate to src_combo")
        except Exception as e:
            print(f"DEBUG: Failed to apply hover delegate to src_combo: {e}")
        
        self.src_btn = QPushButton("Browse...")
        self.src_btn.setObjectName("src_btn")
        self.src_btn.setStyleSheet(BUTTON_STYLE)
        self.src_btn.setFixedHeight(38)
        self.src_btn.setFixedWidth(110)
        
        src_layout.addWidget(src_label)
        src_layout.addWidget(self.src_combo, 1)
        src_layout.addWidget(self.src_btn)
        
        paths_layout.addLayout(src_layout)
        
        # Destinations section with pinned header and scrollable content
        dest_frame = QFrame()
        dest_frame.setStyleSheet(CARD_FRAME_STYLE)
        dest_layout = QVBoxLayout(dest_frame)
        dest_layout.setSpacing(8)
        dest_layout.setContentsMargins(12, 12, 12, 12)
        
        # Destinations header (pinned to top)
        dest_header = QHBoxLayout()
        dest_header.setSpacing(10)
        dest_header.setContentsMargins(0, 0, 0, 0)
        dest_label = QLabel("Destinations:")
        dest_label.setStyleSheet(FIELD_LABEL_STYLE)
        dest_label.setFixedHeight(25)
        
        # Destinations dropdown - automatically adds destinations when selected
        self.dest_combo = QComboBox()
        self.dest_combo.setEditable(True)
        self.dest_combo.setStyleSheet(COMBOBOX_STYLE)
        self.dest_combo.setPlaceholderText("Select destination folder...")
        self.dest_combo.setFixedHeight(38)
        self.dest_combo.setMinimumHeight(38)
        self.dest_combo.setMaximumHeight(38)
        
        # Apply hover delegate for proper hover effects and clickable area
        try:
            apply_hover_delegate(self.dest_combo)
            print("DEBUG: Applied hover delegate to dest_combo")
        except Exception as e:
            print(f"DEBUG: Failed to apply hover delegate to dest_combo: {e}")
        
        # Connect dropdown selection to handle both text changes and index changes
        self.dest_combo.currentTextChanged.connect(self.on_destination_text_changed)
        self.dest_combo.currentIndexChanged.connect(self.on_destination_index_changed)
        # Track if we're programmatically updating the combo
        self._updating_combo = False
        
        self.add_dest_btn = QPushButton("+ Add Destination")
        self.add_dest_btn.setObjectName("add_dest_btn")
        self.add_dest_btn.setStyleSheet(BUTTON_STYLE)
        self.add_dest_btn.setFixedHeight(38)
        self.add_dest_btn.setFixedWidth(150)
        
        dest_header.addWidget(dest_label)
        dest_header.addWidget(self.dest_combo, 1)
        dest_header.addWidget(self.add_dest_btn)
        dest_layout.addLayout(dest_header, 0)
        
        # Connect button signals
        self.add_dest_btn.clicked.connect(self.add_destination)
        self.src_btn.clicked.connect(self._browse_for_source)
        
        # Destinations list (scrollable with expandable height)
        dest_scroll = QScrollArea()
        dest_scroll.setWidgetResizable(True)
        dest_scroll.setMinimumHeight(150)  # Reduced minimum height to prevent clipping
        # Remove maximum height constraint to allow full expansion
        dest_scroll.setStyleSheet(SCROLL_AREA_STYLE)
        dest_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        dest_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.dest_container = QWidget()
        self.dest_container_layout = QVBoxLayout(self.dest_container)
        self.dest_container_layout.setSpacing(4)
        self.dest_container_layout.setContentsMargins(6, 6, 6, 6)
        self.dest_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        dest_scroll.setWidget(self.dest_container)
        dest_layout.addWidget(dest_scroll, 1)
        
        paths_layout.addWidget(dest_frame, 1)
        layout.addLayout(paths_layout, 1)
        
    def on_destination_text_changed(self, text):
        """Handle destination text changes - only auto-add when typed manually"""
        # Don't auto-add if we're programmatically updating the combo
        if self._updating_combo:
            return
            
        # Only auto-add if text is typed manually and is a valid path
        if (text and text.strip() and 
            text.strip() not in [widget.path for widget in self.destination_widgets] and
            text.strip() not in self.recent_destinations):
            
            # Check if this is a valid path (basic check)
            if text.strip().startswith('/') or text.strip().startswith('\\'):
                # Auto-add the destination
                self.add_destination(text.strip())
                # Clear the combo box after adding
                self._updating_combo = True
                self.dest_combo.setCurrentText("")
                self._updating_combo = False
    
    def on_destination_index_changed(self, index):
        """Handle destination dropdown selection - auto-add selected recent destination"""
        # Don't auto-add if we're programmatically updating the combo
        if self._updating_combo or index < 0:
            return
        
        # Get the selected text and clean it (remove warning indicators)
        selected_text = self.dest_combo.itemText(index).strip()
        
        # CRITICAL FIX: Clean the path to remove warning emojis and status text
        # This handles cases where user selects from dropdown that has formatted text
        clean_path = selected_text.replace("⚠️ ", "").replace(" (Unavailable)", "").strip()
        
        # Only auto-add if it's a valid path and not already added
        if (clean_path and clean_path != self.dest_combo.placeholderText() and
            clean_path not in [widget.path for widget in self.destination_widgets]):
            
            print(f"DEBUG: Auto-adding destination from dropdown selection: {clean_path}")
            # Auto-add the destination
            self.add_destination(clean_path)
            
            # Clear the combo box after adding
            self._updating_combo = True
            self.dest_combo.setCurrentIndex(-1)
            self.dest_combo.setCurrentText("")
            self._updating_combo = False
                
    def add_destination(self, path=None):
        """Add a new destination"""
        if not path:
            path = self.dest_combo.currentText().strip()
            if not path or path == self.dest_combo.placeholderText():
                path = QFileDialog.getExistingDirectory(
                    self,
                    "Select Destination Folder",
                    "",
                    QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
                )
        
        if path:
            print(f"DEBUG: Added destination: {path}")
            dest_widget = DestinationWidget(path, self.dest_container, self)
            self.destination_widgets.append(dest_widget)
            self.dest_container_layout.addWidget(dest_widget)
            # Clear combo box without triggering auto-add
            self._updating_combo = True
            self.dest_combo.setCurrentText("")
            self._updating_combo = False
            
            # Save to recent destinations for persistence
            try:
                from ..ingest_utils import add_to_recent_locations, load_recent_locations
                add_to_recent_locations(path, is_source=False)
                print(f"DEBUG: Added destination {path} to recent locations")
                
                # Refresh dropdown with updated recent destinations and availability
                _, updated_destinations = load_recent_locations()
                self._updating_combo = True
                self.dest_combo.clear()
                self.dest_combo.addItems(updated_destinations)
                self._update_destination_availability()
                self._updating_combo = False
                print(f"DEBUG: Refreshed destination dropdown with {len(updated_destinations)} recent destinations")
            except Exception as e:
                print(f"DEBUG: Failed to save destination to recent locations: {e}")
            
            # Emit signal that destinations changed
            self.destinations_changed.emit()
            
    def remove_destination(self, widget):
        """Remove a destination widget"""
        if widget in self.destination_widgets:
            self.destination_widgets.remove(widget)
            self.dest_container_layout.removeWidget(widget)
            widget.deleteLater()
            # Emit signal that destinations changed
            self.destinations_changed.emit()
            
    def get_destinations(self):
        """Get list of destination paths"""
        return [widget.path for widget in self.destination_widgets]
    
    def handle_destination_progress(self, progress_payload):
        """Handle destination-specific progress updates and route to correct widget"""
        print(f"DEBUG: !!!!! SourceDestinationSection.handle_destination_progress CALLED !!!!!")
        print(f"DEBUG: Payload keys: {list(progress_payload.keys()) if progress_payload else 'None'}")
        print(f"DEBUG: Full payload: {progress_payload}")
        
        if not progress_payload:
            print("DEBUG: No progress payload received")
            return
        
        dest_path = progress_payload.get('dest_path', '')
        current_speed = progress_payload.get('current_speed_mbps', 0)
        progress_percent = progress_payload.get('progress_percent', 0)
        print(f"DEBUG: Received destination progress for '{dest_path}': {current_speed:.1f} MB/s, {progress_percent:.1f}%")
        print(f"DEBUG: Available destination widgets: {[w.path for w in self.destination_widgets]}")
        print(f"DEBUG: Widget count: {len(self.destination_widgets)}")
        
        # Check if this is a destination-specific update
        if dest_path and dest_path != 'current_destination':
            # Find the matching destination widget and update it
            updated = False
            print(f"DEBUG: *** SEARCHING FOR WIDGET WITH PATH: '{dest_path}' ***")
            print(f"DEBUG: Available widget paths: {[f'[{i}]: {w.path}' for i, w in enumerate(self.destination_widgets)]}")
            
            for i, widget in enumerate(self.destination_widgets):
                print(f"DEBUG: Comparing widget[{i}].path='{widget.path}' with dest_path='{dest_path}'")
                if widget.path == dest_path:
                    print(f"DEBUG: *** EXACT MATCH FOUND - Updating widget[{i}] for {dest_path} ***")
                    widget.update_progress(progress_payload)
                    updated = True
                    break
                elif os.path.normpath(widget.path) == os.path.normpath(dest_path):
                    print(f"DEBUG: *** NORMALIZED PATH MATCH FOUND - Updating widget[{i}] for {dest_path} ***")
                    widget.update_progress(progress_payload)
                    updated = True
                    break
            
            if not updated:
                print(f"DEBUG: *** WARNING: No destination widget found for path: '{dest_path}' ***")
                print(f"DEBUG: Will update all widgets as fallback")
                # Fallback - update all widgets
                for widget in self.destination_widgets:
                    print(f"DEBUG: Fallback - updating widget '{widget.path}'")
                    widget.update_progress(progress_payload)
        else:
            # If no specific destination path, update all destination widgets with the data
            print(f"DEBUG: *** UPDATING ALL {len(self.destination_widgets)} destination widgets with general progress ***")
            for widget in self.destination_widgets:
                print(f"DEBUG: Updating widget '{widget.path}' with general progress")
                # Create a copy of the payload with the correct dest_path for this widget
                widget_payload = progress_payload.copy()
                widget_payload['dest_path'] = widget.path
                widget.update_progress(widget_payload)
    
    def _browse_for_source(self):
        """Browse for source directory"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Source Folder",
            "",
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if path:
            self.src_combo.setCurrentText(path)
            print(f"DEBUG: Source selected: {path}")
    
    def populate_recent_locations(self):
        """Populate the source and destination dropdowns with recent locations"""
        # Populate source dropdown with recent sources
        if self.recent_sources:
            self.src_combo.addItems(self.recent_sources)
            print(f"DEBUG: Populated source dropdown with {len(self.recent_sources)} recent sources")
        
        # Populate destination dropdown with recent destinations and availability status
        if self.recent_destinations:
            self._updating_combo = True
            self.dest_combo.addItems(self.recent_destinations)
            self._update_destination_availability()
            self._updating_combo = False
            print(f"DEBUG: Populated destination dropdown with {len(self.recent_destinations)} recent destinations")
    
    def _update_destination_availability(self):
        """Update destination dropdown to show availability status"""
        import os
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QColor
        
        # Create a custom model to handle item styling
        model = self.dest_combo.model()
        
        for i in range(self.dest_combo.count()):
            item = model.item(i)
            if item:
                # CRITICAL FIX: Always get the clean path from UserRole (original path)
                # If UserRole not set, clean the current display text and store it
                original_path = item.data(Qt.ItemDataRole.UserRole)
                if not original_path:
                    # First time - store the original clean path
                    display_text = self.dest_combo.itemText(i)
                    original_path = display_text.replace("⚠️ ", "").replace(" (Unavailable)", "").strip()
                    item.setData(original_path, Qt.ItemDataRole.UserRole)
                
                # Check if destination is available using the ORIGINAL clean path
                is_available = self._check_destination_availability(original_path)
                
                if not is_available:
                    # Grey out unavailable destinations
                    item.setData(QColor(colors['secondary_text']), Qt.ItemDataRole.ForegroundRole)
                    # Set display text with warning (always clean, no duplicates)
                    item.setData(f"⚠️ {original_path} (Unavailable)", Qt.ItemDataRole.DisplayRole)
                    # Make it unselectable
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable & ~Qt.ItemFlag.ItemIsEnabled)
                else:
                    # Ensure available destinations are properly styled
                    item.setData(QColor(colors['text']), Qt.ItemDataRole.ForegroundRole)
                    # Use the clean original path for display
                    item.setData(original_path, Qt.ItemDataRole.DisplayRole)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                
                print(f"DEBUG: Destination {original_path} availability: {'✅' if is_available else '❌'}")
    
    def _check_destination_availability(self, dest_path: str) -> bool:
        """Check if a destination path is currently available"""
        import os
        
        try:
            # Check if path exists and is accessible
            if not dest_path or not dest_path.strip():
                return False
            
            # Basic path validation
            if not (dest_path.startswith('/') or (len(dest_path) > 1 and dest_path[1] == ':')):
                return False
            
            # Check if path exists
            if not os.path.exists(dest_path):
                # For network shares, check if parent exists (mount point)
                parent_path = os.path.dirname(dest_path)
                if parent_path and os.path.exists(parent_path):
                    # Parent exists but destination doesn't - this could be a missing subdirectory
                    # which our engine can create, so mark as available
                    return True
                return False
            
            # Check if we can write to the destination
            if not os.access(dest_path, os.W_OK):
                return False
            
            return True
            
        except Exception as e:
            print(f"DEBUG: Error checking destination availability for {dest_path}: {e}")
            return False
    
    def refresh_destination_availability(self):
        """Public method to refresh destination availability (can be called externally)"""
        if hasattr(self, 'dest_combo') and self.dest_combo.count() > 0:
            self._updating_combo = True
            self._update_destination_availability()
            self._updating_combo = False
            print("DEBUG: Refreshed destination availability status")
    
    def cleanup(self):
        """Cleanup method to stop timers when widget is destroyed"""
        if hasattr(self, 'availability_timer') and self.availability_timer.isActive():
            self.availability_timer.stop()
            print("DEBUG: Stopped destination availability timer")
    

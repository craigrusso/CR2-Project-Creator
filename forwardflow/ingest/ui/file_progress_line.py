from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QFrame,
    QSizePolicy,
)
import os
import time
import collections
from PyQt6.QtGui import QColor

# Import app colors for consistent styling
try:
    from app.ui.color_scheme_pyqt import (
        colors, FILE_PROGRESS_LINE_STYLE, 
        FILE_PROGRESS_LINE_COMPLETED_STYLE, 
        FILE_PROGRESS_LINE_FAILED_STYLE,
        FILENAME_LABEL_STYLE, FILE_SPEED_LABEL_STYLE, FILE_STATUS_LABEL_STYLE
    )
    STYLING_AVAILABLE = True
except ImportError:
    raise ImportError("Centralized styles are required for FileProgressLine")


class FileProgressLine(QWidget):
    """Widget to display individual file transfer progress."""
    
    def __init__(self, filename: str, total_bytes: int):
        super().__init__()
        self.filename = filename
        self.total_bytes = total_bytes
        self.copied_bytes = 0
        self.start_time = None
        
        # Rolling speed calculation
        self._samples = collections.deque(maxlen=8)  # 8×100ms ≈ 0.8 s
        self._last = None
        self._last_paint = 0.0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components."""
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)  # Reduced to 2px for very tight spacing
        layout.setSpacing(2)  # Reduced to 2px for very tight spacing
        
        # Filename label (truncated if too long)
        self.filename_label = QLabel(self._truncate_filename(self.filename))
        self.filename_label.setMinimumWidth(150)  # Reduced minimum width
        self.filename_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)  # Allow expansion
        self.filename_label.setToolTip(self.filename)  # Show full name on hover
        self.filename_label.setStyleSheet(FILENAME_LABEL_STYLE)
        layout.addWidget(self.filename_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumWidth(120)  # Reduced minimum width
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)  # Allow expansion
        self.progress_bar.setFixedHeight(20)  # Reduced height for more compact display
        layout.addWidget(self.progress_bar)
        
        # Speed label
        self.speed_label = QLabel("0 MB/s")
        self.speed_label.setMinimumWidth(80)  # Reduced minimum width
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.speed_label.setStyleSheet(FILE_SPEED_LABEL_STYLE)
        layout.addWidget(self.speed_label)
        
        # Status label
        self.status_label = QLabel("Starting...")
        self.status_label.setMinimumWidth(80)  # Reduced minimum width
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status_label.setStyleSheet(FILE_STATUS_LABEL_STYLE)
        layout.addWidget(self.status_label)
        
        # Remove the stretch to allow widgets to expand
        # layout.addStretch()
        
        self.setLayout(layout)
        
        # Set a fixed height for consistent appearance
        self.setFixedHeight(32)  # Reduced height for more compact display
        
        # Apply app-consistent styling
        self._apply_default_styling()
        
    def _truncate_filename(self, filename: str, max_length: int = 35) -> str:
        """Truncate filename to fit in UI."""
        if len(filename) <= max_length:
            return filename
        
        # Try to keep the extension if possible
        name, ext = os.path.splitext(filename)
        if ext:
            # Keep extension and truncate name part
            max_name_length = max_length - len(ext) - 3  # 3 for "..."
            if max_name_length > 0:
                return name[:max_name_length] + "..." + ext
            else:
                # If we can't fit even the extension, just truncate
                return filename[:max_length-3] + "..."
        else:
            # No extension, just truncate
            return filename[:max_length-3] + "..."
        
    def _apply_default_styling(self):
        """Apply the default app styling."""
        self.setStyleSheet(FILE_PROGRESS_LINE_STYLE)
        
    def update_progress(self, copied_bytes: int, speed_mbps: float = None):
        """Update the progress display with rolling speed calculation."""
        self.copied_bytes = copied_bytes
        
        # Calculate percentage
        if self.total_bytes > 0:
            percent = int((copied_bytes / self.total_bytes) * 100)
            self.progress_bar.setValue(percent)
        
        # Update rolling speed if not provided externally
        if speed_mbps is None:
            speed_mbps = self._calculate_rolling_speed(copied_bytes)
        
        # Update speed display
        if speed_mbps >= 1000:
            self.speed_label.setText(f"{speed_mbps/1000:.1f} GB/s")
        else:
            self.speed_label.setText(f"{speed_mbps:.1f} MB/s")
        
        # Update status
        if copied_bytes >= self.total_bytes:
            self.status_label.setText("Complete")
        else:
            self.status_label.setText("Transferring...")
            
        # Throttle UI repaint to ≤10 Hz
        self._maybe_repaint()
        
    def _calculate_rolling_speed(self, bytes_now: int) -> float:
        """Calculate rolling speed using samples over time."""
        t = time.monotonic()
        if self._last is not None:
            dt = t - self._last[0]
            db = bytes_now - self._last[1]
            if dt > 0:
                self._samples.append(db/dt)  # bytes/sec
                mbps = (sum(self._samples)/len(self._samples))/(1024*1024) if self._samples else 0.0
                return mbps
        self._last = (t, bytes_now)
        return 0.0
        
    def _maybe_repaint(self):
        """Throttle UI repaint to ≤10 Hz."""
        t = time.monotonic()
        if t - self._last_paint < 0.10:  # 100ms = 10 Hz
            return
        self._last_paint = t
        self.repaint()
        
    def mark_completed(self):
        """Mark the file transfer as completed."""
        self.progress_bar.setValue(100)
        self.status_label.setText("Complete")
        self.speed_label.setText("Done")
        
        # DON'T apply the overall widget style - it causes the brown background
        # self.setStyleSheet(FILE_PROGRESS_LINE_COMPLETED_STYLE)
        
        # Instead, style each component individually to ensure proper green colors
        
        # Style the progress bar with green gradient
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {colors['success']};
                border-radius: 2px;
                text-align: center;
                background-color: {colors['bg']};
                color: {colors['text']};
                font-size: 10px;
                font-weight: 600;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                           stop:0 {colors['success']}, 
                                           stop:0.5 {QColor(colors['success']).lighter(120).name()}, 
                                           stop:1 {QColor(colors['success']).lighter(150).name()});
                border-radius: 1px;
            }}
        """)
        
        # Style the filename label with green color (not blue) for completed files
        self.filename_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['success']};
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        
        # Style the status label with proper green background and text (no brown!)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: 11px;
                font-weight: 600;
                background-color: {colors['success']};
                padding: 2px 6px;
                border-radius: 3px;
                border: 1px solid {colors['success']};
            }}
        """)
        
        # Style the speed label with green text
        self.speed_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['success']};
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        
        # Force a repaint
        self.repaint()
        
    def mark_failed(self, error_message: str = "Failed"):
        """Mark the file transfer as failed."""
        self.progress_bar.setValue(0)
        self.status_label.setText("Failed")
        self.speed_label.setText("Error")
        
        # DON'T apply the overall widget style - it causes unwanted background colors
        # self.setStyleSheet(FILE_PROGRESS_LINE_FAILED_STYLE)
        
        # Instead, style each component individually with proper red colors
        
        # Style the progress bar with red border
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {colors['error']};
                border-radius: 2px;
                text-align: center;
                background-color: {colors['bg']};
                color: {colors['text']};
                font-size: 10px;
                font-weight: 600;
            }}
            QProgressBar::chunk {{
                background-color: {colors['error']}40;
                border-radius: 1px;
            }}
        """)
        
        # Style the filename label with red color for failed files
        self.filename_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['error']};
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        
        # Style the status label with proper red background and white text (no brown!)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: 11px;
                font-weight: 600;
                background-color: {colors['error']};
                padding: 2px 6px;
                border-radius: 3px;
                border: 1px solid {colors['error']};
            }}
        """)
        
        # Style the speed label with red text
        self.speed_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['error']};
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        
        # Add error message if provided
        if error_message and error_message != "Failed":
            # Create error message label with red background and white text
            error_style = f"""
                QLabel {{
                    color: white;
                    font-size: 10px;
                    font-weight: 500;
                    background-color: {colors['error']};
                    padding: 2px 4px;
                    border-radius: 2px;
                    border: 1px solid {colors['error']};
                    margin-left: 8px;
                }}
            """
            # If there's already an error label, update it
            for child in self.findChildren(QLabel):
                if child.objectName() == "error_message":
                    child.setText(error_message)
                    child.setStyleSheet(error_style)
                    child.show()
                    break
            else:
                # Create new error label
                error_label = QLabel(error_message)
                error_label.setObjectName("error_message")
                error_label.setStyleSheet(error_style)
                self.layout().addWidget(error_label)
        
        # Force a repaint
        self.repaint()

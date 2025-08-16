from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QFrame,
)

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
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components."""
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)  # Reduced to 2px for very tight spacing
        layout.setSpacing(2)  # Reduced to 2px for very tight spacing
        
        # Filename label (truncated if too long)
        filename_label = QLabel(self._truncate_filename(self.filename))
        filename_label.setMinimumWidth(200)  # Reduced minimum width
        filename_label.setMaximumWidth(350)  # Reduced maximum width
        filename_label.setToolTip(self.filename)  # Show full name on hover
        filename_label.setStyleSheet(FILENAME_LABEL_STYLE)
        layout.addWidget(filename_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumWidth(150)  # Reduced minimum width
        self.progress_bar.setMaximumWidth(250)  # Reduced maximum width
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
        
        # Add stretch to push everything to the left
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Set a fixed height for consistent appearance
        self.setFixedHeight(32)  # Reduced height for more compact display
        
        # Apply app-consistent styling
        self._apply_default_styling()
        
    def _truncate_filename(self, filename: str, max_length: int = 25) -> str:
        """Truncate filename to fit in UI."""
        if len(filename) <= max_length:
            return filename
        return filename[:max_length-3] + "..."
        
    def _apply_default_styling(self):
        """Apply the default app styling."""
        self.setStyleSheet(FILE_PROGRESS_LINE_STYLE)
        
    def update_progress(self, copied_bytes: int, speed_mbps: float = None):
        """Update the progress display."""
        self.copied_bytes = copied_bytes
        
        # Calculate percentage
        if self.total_bytes > 0:
            percent = int((copied_bytes / self.total_bytes) * 100)
            self.progress_bar.setValue(percent)
        
        # Update speed if provided
        if speed_mbps is not None:
            if speed_mbps >= 1000:
                self.speed_label.setText(f"{speed_mbps/1000:.1f} GB/s")
            else:
                self.speed_label.setText(f"{speed_mbps:.1f} MB/s")
        
        # Update status
        if copied_bytes >= self.total_bytes:
            self.status_label.setText("Complete")
        else:
            self.status_label.setText("Transferring...")
            
        # Force a repaint
        self.repaint()
        
    def mark_completed(self):
        """Mark the file transfer as completed."""
        self.progress_bar.setValue(100)
        self.status_label.setText("Complete")
        self.speed_label.setText("Done")
        
        # Change styling to indicate completion with centralized styles
        self.setStyleSheet(FILE_PROGRESS_LINE_COMPLETED_STYLE)
        
    def mark_failed(self, error: str):
        """Mark the file transfer as failed."""
        self.status_label.setText("Failed")
        self.speed_label.setText("Error")
        
        # Change styling to indicate failure with centralized styles
        self.setStyleSheet(FILE_PROGRESS_LINE_FAILED_STYLE)
        
        # Show error in tooltip
        self.setToolTip(f"Error: {error}")

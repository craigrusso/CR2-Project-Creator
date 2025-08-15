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
    from app.ui.color_scheme_pyqt import colors
    STYLING_AVAILABLE = True
except ImportError:
    STYLING_AVAILABLE = False
    # Fallback colors that work with dark theme
    colors = {
        'border': '#3C3C3C',
        'card_bg': '#252526',
        'text': '#CCCCCC',
        'secondary_text': '#858585',
        'accent': '#2C4F76',
        'accent_hover': '#36648B',
        'bg': '#1E1E1E',
        'hover_bg': '#454545',
        'success': '#4CAF50',
        'warning': '#F1AE3C',
        'error': '#E8574C',
        'info': '#4E98C3',
        'highlight_border': '#4682B4',
        'highlight_bg': '#2C4F76',
        'highlight_bg_transparent': '#2C4F7633',
        'highlight_text': '#FFFFFF'
    }


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
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Filename label (truncated if too long)
        filename_label = QLabel(self._truncate_filename(self.filename))
        filename_label.setMinimumWidth(250)
        filename_label.setMaximumWidth(400)
        filename_label.setToolTip(self.filename)  # Show full name on hover
        filename_label.setStyleSheet(f"color: {colors['text']}; font-size: 13px; font-weight: 500;")
        layout.addWidget(filename_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setMaximumWidth(300)
        self.progress_bar.setFixedHeight(20)
        layout.addWidget(self.progress_bar)
        
        # Speed label
        self.speed_label = QLabel("0 MB/s")
        self.speed_label.setMinimumWidth(100)
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.speed_label.setStyleSheet(f"color: {colors['text']}; font-size: 12px; font-weight: 600;")
        layout.addWidget(self.speed_label)
        
        # Status label
        self.status_label = QLabel("Starting...")
        self.status_label.setMinimumWidth(100)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status_label.setStyleSheet(f"color: {colors['text']}; font-size: 12px; font-weight: 500;")
        layout.addWidget(self.status_label)
        
        # Add stretch to push everything to the left
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Set a fixed height for consistent appearance
        self.setFixedHeight(40)
        
        # Apply app-consistent styling
        self._apply_default_styling()
        
    def _truncate_filename(self, filename: str, max_length: int = 25) -> str:
        """Truncate filename to fit in UI."""
        if len(filename) <= max_length:
            return filename
        return filename[:max_length-3] + "..."
        
    def _apply_default_styling(self):
        """Apply the default app styling."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
            }}
            QProgressBar {{
                border: 2px solid {colors['border']};
                border-radius: 4px;
                text-align: center;
                background-color: {colors['bg']};
                color: {colors['text']};
                font-size: 11px;
                font-weight: 700;
            }}
            QProgressBar::chunk {{
                background-color: {colors['accent']};
                border-radius: 2px;
            }}
        """)
        
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
        
        # Change styling to indicate completion with app colors
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['success']}20;
                border: 1px solid {colors['success']};
                border-radius: 4px;
            }}
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
                background-color: {colors['success']};
                border-radius: 1px;
            }}
        """)
        
    def mark_failed(self, error: str):
        """Mark the file transfer as failed."""
        self.status_label.setText("Failed")
        self.speed_label.setText("Error")
        
        # Change styling to indicate failure with app colors
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['error']}20;
                border: 1px solid {colors['error']};
                border-radius: 4px;
            }}
            QProgressBar {{
                border: 1px solid {colors['error']};
                border-radius: 2px;
                text-align: center;
                background-color: {colors['bg']};
                color: {colors['text']};
                font-size: 10px;
                font-weight: 600;
            }}
            QProgressBar::chunk {{
                background-color: {colors['error']};
                border-radius: 1px;
            }}
        """)
        
        # Show error in tooltip
        self.setToolTip(f"Error: {error}")

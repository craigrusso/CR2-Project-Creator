"""Control Section for Ingest Tab"""

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
        
        # Connect button handlers
        self.start_btn.clicked.connect(lambda: self.on_start(root, source_dest_section, options_section))
        self.pause_btn.clicked.connect(lambda: self.on_pause(root))
        self.cancel_btn.clicked.connect(lambda: self.on_cancel(root))
        
        print("DEBUG: Button handlers connected")
    
    def on_start(self, root, source_dest_section, options_section):
        """Handle start button click"""
        print("DEBUG: Start button clicked")
        # Implementation will be added here
        pass
    
    def on_pause(self, root):
        """Handle pause button click"""
        print("DEBUG: Pause button clicked")
        # Implementation will be added here
        pass
    
    def on_cancel(self, root):
        """Handle cancel button click"""
        print("DEBUG: Cancel button clicked")
        # Implementation will be added here
        pass
    
    def reenable_controls(self):
        """Re-enable controls after error"""
        print("DEBUG: Re-enabling controls")
        self.start_btn.setEnabled(True)
        # Re-enable other controls as needed

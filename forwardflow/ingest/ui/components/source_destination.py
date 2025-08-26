"""Source and Destination Section for Ingest Tab"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QFrame, QScrollArea, QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt

try:
    from app.ui.color_scheme_pyqt import (
        colors, BUTTON_STYLE, COMBOBOX_STYLE, GROUPBOX_STYLE, 
        FIELD_LABEL_STYLE, SCROLL_AREA_STYLE, CARD_FRAME_STYLE,
        LABEL_STYLE, SECONDARY_TEXT_STYLE, HEADER_LABEL_STYLE
    )
    STYLING_AVAILABLE = True
except ImportError as e:
    print(f"DEBUG: Failed to import centralized styles: {e}")
    raise ImportError("Centralized styles are required for the ingest tab")


class DestinationWidget(QFrame):
    """Individual destination widget with transfer type detection"""
    
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
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
        
        # Progress bar row
        progress_row = QHBoxLayout()
        progress_row.setSpacing(5)
        
        # Progress bar for this destination
        dest_progress = QProgressBar()
        dest_progress.setRange(0, 100)
        dest_progress.setValue(0)
        dest_progress.setFixedHeight(15)
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
                                           stop:0 #2d5a2d, 
                                           stop:0.5 #4a7c4a, 
                                           stop:1 #6ba06b);
                border-radius: 1px;
            }}
        """)
        dest_progress.setVisible(False)
        dest_progress.setFormat("Dest: %p%")
        dest_progress.setTextVisible(True)
        progress_row.addWidget(dest_progress, 1)
        
        layout.addLayout(progress_row)
        
        # Store references
        self.preset_combo = preset_combo
        self.remove_btn = remove_btn
        self.dest_progress = dest_progress
        
    def remove_self(self):
        """Remove this destination widget"""
        if hasattr(self.parent(), 'remove_destination'):
            self.parent().remove_destination(self)


class SourceDestinationSection(QWidget):
    """Source and Destination Section with exact original design"""
    
    def __init__(self, parent=None, recent_sources=None, recent_destinations=None):
        super().__init__(parent)
        self.destination_widgets = []
        self.recent_sources = recent_sources or []
        self.recent_destinations = recent_destinations or []
        self.setup_ui()
        self.populate_recent_locations()
        
    def setup_ui(self):
        """Setup the source and destination UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title at the very top with minimal margin
        title = QLabel("Turbo Transfer")
        title.setStyleSheet(HEADER_LABEL_STYLE)
        title.setFixedHeight(30)
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
        
        # Connect dropdown selection to automatic destination addition
        self.dest_combo.currentTextChanged.connect(self.on_destination_changed)
        
        self.add_dest_btn = QPushButton("+ Add Destination")
        self.add_dest_btn.setObjectName("add_dest_btn")
        self.add_dest_btn.setStyleSheet(BUTTON_STYLE)
        self.add_dest_btn.setFixedHeight(38)
        self.add_dest_btn.setFixedWidth(150)
        
        dest_header.addWidget(dest_label)
        dest_header.addWidget(self.dest_combo, 1)
        dest_header.addWidget(self.add_dest_btn)
        dest_layout.addLayout(dest_header, 0)
        
        # Destinations list (scrollable with expandable height)
        dest_scroll = QScrollArea()
        dest_scroll.setWidgetResizable(True)
        dest_scroll.setMinimumHeight(200)  # Increased minimum height to show bottom clearly
        dest_scroll.setMaximumHeight(1000)  # Increased max height for more destinations when expanded
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
        
    def on_destination_changed(self, text):
        """Handle destination text changes - auto-add if valid path"""
        if text and text.strip() and not text.strip() in [widget.path for widget in self.destination_widgets]:
            # Check if this is a valid path (basic check)
            if text.strip().startswith('/') or text.strip().startswith('\\'):
                # Auto-add the destination
                self.add_destination(text.strip())
                # Clear the combo box after adding
                self.dest_combo.setCurrentText("")
                
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
            dest_widget = DestinationWidget(path, self.dest_container)
            self.destination_widgets.append(dest_widget)
            self.dest_container_layout.addWidget(dest_widget)
            self.dest_combo.setCurrentText("")
            
    def remove_destination(self, widget):
        """Remove a destination widget"""
        if widget in self.destination_widgets:
            self.destination_widgets.remove(widget)
            self.dest_container_layout.removeWidget(widget)
            widget.deleteLater()
            
    def get_destinations(self):
        """Get list of destination paths"""
        return [widget.path for widget in self.destination_widgets]
    
    def populate_recent_locations(self):
        """Populate the source and destination dropdowns with recent locations"""
        # Populate source dropdown with recent sources
        if self.recent_sources:
            self.src_combo.addItems(self.recent_sources)
            print(f"DEBUG: Populated source dropdown with {len(self.recent_sources)} recent sources")
        
        # Populate destination dropdown with recent destinations
        if self.recent_destinations:
            self.dest_combo.addItems(self.recent_destinations)
            print(f"DEBUG: Populated destination dropdown with {len(self.recent_destinations)} recent destinations")

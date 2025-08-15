"""PyQt6 Ingest tab builder for Phase 1.

Lightweight UI built here to keep ingest self-contained. The host app
calls `build_ingest_tab()` under a feature flag to add the tab.
"""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
import time

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QComboBox,
    QSlider,
    QProgressBar,
    QScrollArea,
    QFrame,
    QSizePolicy,
)

from .ingest_vm import IngestViewModel
from ..engines.python_engine import PythonCopyEngine

# Define colors locally to avoid circular imports
colors = {
    'border': '#2C4F76',
    'card_bg': '#383838', 
    'text': '#CCCCCC',
    'secondary_text': '#858585',  # Add missing secondary_text color
    'accent': '#3498db',
    'bg': '#2A2A2A',
    'success': '#27ae60',
    'warning': '#f39c12',
    'error': '#e74c3c',
    'info': '#3498db'
}

BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: #454545;
        border: 1px solid {colors['accent']};
    }}
"""

ACCENT_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {colors['accent']};
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 14px;
    }}
    QPushButton:hover {{
        background-color: #2980b9;
    }}
"""

COMBOBOX_STYLE = f"""
    QComboBox {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        padding: 6px 12px;
        border-radius: 4px;
    }}
"""

LINEEDIT_STYLE = f"""
    QLineEdit {{
        background-color: {colors['card_bg']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
        padding: 6px 12px;
        border-radius: 4px;
    }}
"""


class CleanProgressBar(QProgressBar):
    """Clean progress bar with integrated label."""
    
    def __init__(self, label_text: str, height: int = 20):
        super().__init__()
        self.setFixedHeight(height)
        self.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {colors['border']};
                border-radius: 10px;
                background-color: {colors['card_bg']};
                text-align: center;
                font-weight: 600;
                font-size: 14px;
                color: {colors['text']};
            }}
            QProgressBar::chunk {{
                background-color: {colors['accent']};
                border-radius: 8px;
            }}
        """)
        self.setFormat(f"{label_text} %p%")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class FileProgressLine(QFrame):
    """Clean file progress line with integrated label."""
    
    def __init__(self, filename: str, total_bytes: int):
        super().__init__()
        self.filename = filename
        self.total_bytes = total_bytes
        self.copied_bytes = 0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)
        
        # Filename (truncated)
        name_label = QLabel(self._truncate_filename(filename))
        name_label.setStyleSheet(f"color: {colors['text']}; font-size: 12px; min-width: 120px;")
        name_label.setToolTip(filename)
        layout.addWidget(name_label)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setFixedHeight(8)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {colors['border']};
                border-radius: 4px;
                background-color: {colors['card_bg']};
            }}
            QProgressBar::chunk {{
                background-color: {colors['accent']};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress, 1)
        
        # Percentage
        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet(f"color: {colors['accent']}; font-size: 12px; font-weight: 600; min-width: 40px;")
        layout.addWidget(self.percent_label)
        
        # Set progress range
        self.progress.setRange(0, total_bytes)
        
    def _truncate_filename(self, filename: str, max_length: int = 25) -> str:
        """Truncate filename to fit in UI."""
        if len(filename) <= max_length:
            return filename
        return filename[:max_length-3] + "..."
    
    def update_progress(self, copied_bytes: int, speed_mbps: float = 0.0):
        """Update progress with optional speed display."""
        self.copied_bytes = copied_bytes
        self.progress.setValue(copied_bytes)
        
        percent = int(100 * copied_bytes / self.total_bytes) if self.total_bytes > 0 else 0
        self.percent_label.setText(f"{percent}%")
        
        # Update tooltip with speed info
        if speed_mbps > 0:
            self.setToolTip(f"{self.filename}\nSpeed: {speed_mbps:.1f} MB/s")
    
    def mark_completed(self):
        """Mark as completed with green styling."""
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {colors['success']};
                border-radius: 4px;
                background-color: {colors['card_bg']};
            }}
            QProgressBar::chunk {{
                background-color: {colors['success']};
                border-radius: 3px;
            }}
        """)
        self.percent_label.setText("✓")
        self.percent_label.setStyleSheet(f"color: {colors['success']}; font-size: 14px; font-weight: 700;")
    
    def mark_failed(self, error: str = ""):
        """Mark as failed with red styling."""
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {colors['error']};
                border-radius: 4px;
                background-color: {colors['card_bg']};
            }}
            QProgressBar::chunk {{
                background-color: {colors['error']};
                border-radius: 3px;
            }}
        """)
        self.percent_label.setText("✗")
        self.percent_label.setStyleSheet(f"color: {colors['error']}; font-size: 14px; font-weight: 700;")
        if error:
            self.setToolTip(f"{self.filename}\nError: {error}")


def _pick_dir(edit: QLineEdit):
    """Pick directory and update line edit."""
    dir_path = QFileDialog.getExistingDirectory(None, "Select Directory")
    if dir_path:
        edit.setText(dir_path)


def build_ingest_tab() -> QWidget:
    vm = IngestViewModel()
    root = QWidget()
    
    # Make vm accessible to the widget
    root.vm = vm
    
    layout = QVBoxLayout(root)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(16)

    # Header
    header_label = QLabel("Turbo Ingest")
    header_label.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {colors['text']}; margin-bottom: 8px;")
    layout.addWidget(header_label)

    # Source and Destination (compact)
    paths_layout = QHBoxLayout()
    
    # Source
    src_layout = QVBoxLayout()
    src_label = QLabel("Source:")
    src_label.setStyleSheet(f"font-weight: 600; color: {colors['text']}; font-size: 12px;")
    src_edit = QLineEdit()
    src_edit.setStyleSheet(LINEEDIT_STYLE)
    src_edit.setPlaceholderText("Select source folder...")
    src_btn = QPushButton("Browse…")
    src_btn.setStyleSheet(BUTTON_STYLE)
    src_btn.clicked.connect(lambda: _pick_dir(src_edit))
    
    src_row = QHBoxLayout()
    src_row.addWidget(src_edit, 1)
    src_row.addWidget(src_btn)
    
    src_layout.addWidget(src_label)
    src_layout.addLayout(src_row)
    paths_layout.addLayout(src_layout)
    
    # Destination
    dst_layout = QVBoxLayout()
    dst_label = QLabel("Destination:")
    dst_label.setStyleSheet(f"font-weight: 600; color: {colors['text']}; font-size: 12px;")
    dst_edit = QLineEdit()
    dst_edit.setStyleSheet(LINEEDIT_STYLE)
    dst_edit.setPlaceholderText("Select destination folder...")
    dst_btn = QPushButton("Browse…")
    dst_btn.setStyleSheet(BUTTON_STYLE)
    dst_btn.clicked.connect(lambda: _pick_dir(dst_edit))
    
    dst_row = QHBoxLayout()
    dst_row.addWidget(dst_edit, 1)
    dst_row.addWidget(dst_btn)
    
    dst_layout.addWidget(dst_label)
    dst_layout.addLayout(dst_row)
    paths_layout.addLayout(dst_layout)
    
    layout.addLayout(paths_layout)

    # Settings (compact)
    settings_layout = QHBoxLayout()
    
    # Verification
    verify_layout = QVBoxLayout()
    verify_label = QLabel("Verification:")
    verify_label.setStyleSheet(f"font-weight: 600; color: {colors['text']}; font-size: 12px;")
    verify_combo = QComboBox()
    verify_combo.addItems([
        "None — fastest transfer",
        "xxHash64 — fast verification",
        "Cryptographic (disabled)",
    ])
    verify_combo.setStyleSheet(COMBOBOX_STYLE)
    verify_combo.setCurrentIndex(1)
    verify_layout.addWidget(verify_label)
    verify_layout.addWidget(verify_combo)
    settings_layout.addLayout(verify_layout)
    
    # Link preset
    preset_layout = QVBoxLayout()
    preset_label = QLabel("Link preset:")
    preset_label.setStyleSheet(f"font-weight: 600; color: {colors['text']}; font-size: 12px;")
    preset_combo = QComboBox()
    preset_combo.addItems(["Auto/Default", "1 GbE", "10 GbE", "25/40 GbE or IB"])
    preset_combo.setStyleSheet(COMBOBOX_STYLE)
    preset_combo.setCurrentIndex(1)
    preset_layout.addWidget(preset_label)
    preset_layout.addWidget(preset_combo)
    settings_layout.addLayout(preset_layout)
    
    # Concurrency sliders
    conc_layout = QVBoxLayout()
    conc_label = QLabel("Per-file concurrency:")
    conc_label.setStyleSheet(f"font-weight: 600; color: {colors['text']}; font-size: 12px;")
    conc_slider = QSlider(Qt.Orientation.Horizontal)
    conc_slider.setRange(1, 16)
    conc_slider.setValue(1)
    conc_slider.setStyleSheet(f"""
        QSlider::groove:horizontal {{
            border: 1px solid {colors['border']};
            height: 4px;
            background: {colors['card_bg']};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: {colors['accent']};
            border: 1px solid {colors['accent']};
            width: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}
    """)
    conc_value = QLabel("1")
    conc_value.setStyleSheet(f"color: {colors['accent']}; font-weight: 600; font-size: 12px;")
    conc_slider.valueChanged.connect(lambda v: conc_value.setText(str(v)))
    
    conc_row = QHBoxLayout()
    conc_row.addWidget(conc_slider, 1)
    conc_row.addWidget(conc_value)
    
    conc_layout.addWidget(conc_label)
    conc_layout.addLayout(conc_row)
    settings_layout.addLayout(conc_layout)
    
    # Stream concurrency
    stream_layout = QVBoxLayout()
    stream_label = QLabel("Stream concurrency:")
    stream_label.setStyleSheet(f"font-weight: 600; color: {colors['text']}; font-size: 12px;")
    stream_slider = QSlider(Qt.Orientation.Horizontal)
    stream_slider.setRange(1, 32)
    stream_slider.setValue(2)
    stream_slider.setStyleSheet(f"""
        QSlider::groove:horizontal {{
            border: 1px solid {colors['border']};
            height: 4px;
            background: {colors['card_bg']};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: {colors['accent']};
            border: 1px solid {colors['accent']};
            width: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}
    """)
    stream_value = QLabel("2")
    stream_value.setStyleSheet(f"color: {colors['accent']}; font-weight: 600; font-size: 12px;")
    stream_slider.valueChanged.connect(lambda v: stream_value.setText(str(v)))
    
    stream_row = QHBoxLayout()
    stream_row.addWidget(stream_slider, 1)
    stream_row.addWidget(stream_value)
    
    stream_layout.addWidget(stream_label)
    stream_layout.addLayout(stream_row)
    settings_layout.addLayout(stream_layout)
    
    layout.addLayout(settings_layout)

    # Control buttons
    buttons_layout = QHBoxLayout()
    
    start_btn = QPushButton("Start Transfer")
    start_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
    start_btn.setFixedHeight(40)
    
    pause_btn = QPushButton("Pause")
    pause_btn.setStyleSheet(BUTTON_STYLE)
    pause_btn.setFixedHeight(40)
    pause_btn.setEnabled(False)
    
    cancel_btn = QPushButton("Cancel")
    cancel_btn.setStyleSheet(BUTTON_STYLE)
    cancel_btn.setFixedHeight(40)
    cancel_btn.setEnabled(False)
    
    buttons_layout.addWidget(start_btn)
    buttons_layout.addWidget(pause_btn)
    buttons_layout.addWidget(cancel_btn)
    layout.addLayout(buttons_layout)

    # Main progress display (clean, like your example)
    progress_frame = QFrame()
    progress_frame.setStyleSheet(f"background-color: {colors['card_bg']}; border-radius: 8px; padding: 16px;")
    progress_layout = QVBoxLayout(progress_frame)
    progress_layout.setSpacing(12)
    
    # Total progress with integrated label
    total_progress = CleanProgressBar("TOTAL TRANSFER", height=24)
    progress_layout.addWidget(total_progress)
    
    # Speed display (large and prominent)
    speed_label = QLabel("0 MB/s Transfer")
    speed_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {colors['success']}; text-align: center;")
    speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    progress_layout.addWidget(speed_label)
    
    layout.addWidget(progress_frame)

    # Individual files (compact)
    files_frame = QFrame()
    files_frame.setStyleSheet(f"background-color: {colors['card_bg']}; border-radius: 8px; padding: 16px;")
    files_layout = QVBoxLayout(files_frame)
    
    files_header = QHBoxLayout()
    files_label = QLabel("Individual Files")
    files_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {colors['text']};")
    files_count = QLabel("0 files")
    files_count.setStyleSheet(f"font-size: 12px; color: {colors['secondary_text']};")
    files_header.addWidget(files_label)
    files_header.addStretch()
    files_header.addWidget(files_count)
    files_layout.addLayout(files_header)
    
    # Scrollable area for file progress
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setMaximumHeight(200)
    scroll_area.setStyleSheet(f"""
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        QScrollBar:vertical {{
            background-color: {colors['card_bg']};
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {colors['border']};
            border-radius: 4px;
            min-height: 20px;
        }}
    """)
    
    files_container = QWidget()
    files_layout = QVBoxLayout(files_container)
    files_layout.setSpacing(4)
    files_layout.setContentsMargins(0, 0, 0, 0)
    
    scroll_area.setWidget(files_container)
    files_layout.addWidget(scroll_area)
    
    layout.addWidget(files_frame)

    # File tracking
    root.file_widgets = {}  # file_id -> FileProgressLine
    root.active_files = 0
    root.current_job = None  # Track current job for cleanup

    # Wire up
    def on_start():
        if not vm.enabled:
            return
            
        vm.source = Path(src_edit.text()) if src_edit.text() else None
        vm.destination = Path(dst_edit.text()) if dst_edit.text() else None
        
        # Map verification selection to engine mode
        sel = verify_combo.currentText()
        if sel.startswith("None"):
            vm.mode = "FAST"
        elif sel.startswith("xxHash64"):
            vm.mode = "BALANCED"
        else:
            vm.mode = "BALANCED"
            
        vm.per_file_concurrency = conc_slider.value()
        vm.stream_concurrency = stream_slider.value()
        job_id = datetime.now().strftime("ingest_%Y%m%d_%H%M%S")
        
        # Update UI state
        start_btn.setEnabled(False)
        pause_btn.setEnabled(True)
        cancel_btn.setEnabled(True)
        
        # Clear previous file widgets
        for widget in root.file_widgets.values():
            files_layout.removeWidget(widget)
            widget.deleteLater()
        root.file_widgets.clear()
        root.active_files = 0
        files_count.setText("0 files")
        
        # Reset progress
        total_progress.setValue(0)
        speed_label.setText("0 MB/s Transfer")

        # Create sink for progress events
        file_stats = {}
        
        def handle_job_progress(payload):
            mbps = payload.get("mbps", 0.0)
            total = max(1, payload.get("total", 1))
            percent = int(100 * payload.get("bytes", 0) / total)
            total_progress.setValue(percent)
            speed_label.setText(f"{mbps:.0f} MB/s Transfer")
            
        def handle_file_started(payload):
            file_id = payload.get("file_id")
            filename = payload.get("filename")
            total_bytes = payload.get("total_bytes", 0)
            widget = FileProgressLine(filename, total_bytes)
            root.file_widgets[file_id] = widget
            files_layout.addWidget(widget)
            root.active_files += 1
            files_count.setText(f"{root.active_files} files")
            file_stats[file_id] = {'start_time': time.time()}
            
        def handle_file_progress(payload):
            file_id = payload.get("file_id")
            copied_bytes = payload.get("bytes", 0)
            if file_id in root.file_widgets:
                stats = file_stats.get(file_id, {})
                if stats:
                    elapsed = time.time() - stats.get('start_time', time.time())
                    if elapsed > 0:
                        speed = (copied_bytes / elapsed) / (1024 * 1024)
                        root.file_widgets[file_id].update_progress(copied_bytes, speed)
                    else:
                        root.file_widgets[file_id].update_progress(copied_bytes)
                else:
                    root.file_widgets[file_id].update_progress(copied_bytes)
                    
        def handle_file_completed(payload):
            file_id = payload.get("file_id")
            if file_id in root.file_widgets:
                root.file_widgets[file_id].mark_completed()
                root.active_files -= 1
                files_count.setText(f"{root.active_files} files")
                # Remove completed files after a delay
                QTimer.singleShot(2000, lambda: _remove_file_widget(file_id))
                
        def handle_file_failed(payload):
            file_id = payload.get("file_id")
            error = payload.get("error", "Unknown error")
            if file_id in root.file_widgets:
                root.file_widgets[file_id].mark_failed(error)
                root.active_files -= 1
                files_count.setText(f"{root.active_files} files")

        def run():
            # Attach a sink to receive progress and update UI
            class QtSink:
                def emit(self, event_type: str, payload: dict) -> None:
                    if event_type == "job.progress":
                        QTimer.singleShot(0, lambda: handle_job_progress(payload))
                    elif event_type == "file.started":
                        QTimer.singleShot(0, lambda: handle_file_started(payload))
                    elif event_type == "file.progress":
                        QTimer.singleShot(0, lambda: handle_file_progress(payload))
                    elif event_type == "file.completed":
                        QTimer.singleShot(0, lambda: handle_file_completed(payload))
                    elif event_type == "file.failed":
                        QTimer.singleShot(0, lambda: handle_file_failed(payload))

            engine = PythonCopyEngine(sink=QtSink())
            vm._engine_override = engine
            root.current_job = engine  # Track for cleanup
            
            # Freeze controls during copy
            conc_slider.setEnabled(False)
            stream_slider.setEnabled(False)
            verify_combo.setEnabled(False)
            preset_combo.setEnabled(False)
            
            vm.start(job_id)
            
            def done():
                total_progress.setValue(100)
                start_btn.setEnabled(True)
                pause_btn.setEnabled(False)
                cancel_btn.setEnabled(False)
                
                # Re-enable controls
                conc_slider.setEnabled(True)
                stream_slider.setEnabled(True)
                verify_combo.setEnabled(True)
                preset_combo.setEnabled(True)
                
                # Clear job reference
                root.current_job = None
                
            QTimer.singleShot(0, done)

        # Start in background thread
        job_thread = threading.Thread(target=run, daemon=True)
        job_thread.start()
        root.current_job = job_thread

    def _remove_file_widget(file_id: str):
        if file_id in root.file_widgets:
            widget = root.file_widgets[file_id]
            files_layout.removeWidget(widget)
            widget.deleteLater()
            del root.file_widgets[file_id]

    def on_pause():
        if root.current_job:
            vm.pause_current()
        pause_btn.setEnabled(False)
        start_btn.setEnabled(True)

    def on_cancel():
        if root.current_job:
            vm.cancel_current()
            # Force cleanup
            if hasattr(root.current_job, 'terminate'):
                root.current_job.terminate()
            root.current_job = None
        
        start_btn.setEnabled(True)
        pause_btn.setEnabled(False)
        cancel_btn.setEnabled(False)
        
        # Re-enable controls
        conc_slider.setEnabled(True)
        stream_slider.setEnabled(True)
        verify_combo.setEnabled(True)
        preset_combo.setEnabled(True)

    # Make functions attributes of the widget
    root.on_start = on_start
    root.on_pause = on_pause
    root.on_cancel = on_cancel
    root._remove_file_widget = _remove_file_widget

    # Connect buttons
    start_btn.clicked.connect(on_start)
    pause_btn.clicked.connect(on_pause)
    cancel_btn.clicked.connect(on_cancel)

    # Apply preset logic
    def apply_preset():
        preset = preset_combo.currentText()
        if "1 GbE" in preset:
            conc_slider.setValue(1)
            stream_slider.setValue(2)
        elif "10 GbE" in preset:
            conc_slider.setValue(4)
            stream_slider.setValue(8)
        elif "25/40 GbE" in preset:
            conc_slider.setValue(8)
            stream_slider.setValue(16)
        else:  # Auto/Default
            conc_slider.setValue(2)
            stream_slider.setValue(8)
    
    preset_combo.currentTextChanged.connect(apply_preset)
    apply_preset()  # Apply initial preset

    return root



"""PyQt6 Ingest tab builder for Phase 1.

Lightweight UI built here to keep ingest self-contained. The host app
calls `build_ingest_tab()` under a feature flag to add the tab.
"""

from __future__ import annotations

import os
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtCore import (
    QTimer,
    Qt,
    pyqtSignal,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QSlider,
    QComboBox,
    QFrame,
    QSizePolicy,
    QGroupBox,
    QGridLayout,
    QFileDialog,
    QScrollArea,
)

from .ingest_vm import IngestViewModel
from .file_progress_line import FileProgressLine
from ..engines.python_engine import PythonCopyEngine

# Import styling from the main app
try:
    from app.ui.color_scheme_pyqt import (
        colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, 
        LINEEDIT_STYLE, LABEL_STYLE, COMBOBOX_STYLE,
        GROUPBOX_STYLE
    )
    from app.ui.custom_delegates import apply_hover_delegate
    print("DEBUG: Successfully imported centralized styles and hover delegate from app.ui.color_scheme_pyqt")
    STYLING_AVAILABLE = True
except ImportError as e:
    print(f"DEBUG: Failed to import centralized styles: {e}")
    print("DEBUG: Falling back to local style definitions")
    STYLING_AVAILABLE = False
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
            background-color: {colors['hover_bg']};
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
            background-color: {colors['accent_hover']};
        }}
    """
    
    COMBOBOX_STYLE = f"""
        QComboBox {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            padding: 5px 25px 5px 5px;
            border-radius: 3px;
            min-height: 22px;
        }}
        QComboBox:hover {{
            border: 1px solid {colors['highlight_border']};
            background-color: {colors['hover_bg']};
        }}
        QComboBox:focus {{
            border: 1px solid {colors['highlight_border']};
            background-color: {colors['highlight_bg_transparent']};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border: none;
            border-left: 1px solid {colors['border']};
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
        }}
        QComboBox::drop-down:hover {{
            background-color: {colors['accent']};
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {colors['text']};
            margin-right: 5px;
        }}
        QComboBox QAbstractItemView {{
            border: 1px solid {colors['highlight_border']};
            background-color: {colors['card_bg']};
            color: {colors['text']};
            outline: none;
            selection-background-color: {colors['highlight_bg']};
            selection-color: {colors['highlight_text']}
        }}
        QComboBox QAbstractItemView::item {{
            border-left: 3px solid transparent;
            padding: 6px;
            min-height: 24px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {colors['accent']};
            color: white;
            font-weight: bold;
            border-left: 5px solid white;
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {colors['highlight_bg']};
            color: {colors['highlight_text']};
            border-left: 3px solid {colors['accent']};
        }}
    """
    
    LINEEDIT_STYLE = f"""
        QLineEdit {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 13px;
        }}
        QLineEdit:hover {{
            border: 1px solid {colors['accent']};
        }}
        QLineEdit:focus {{
            border: 1px solid {colors['accent']};
            background-color: {colors['bg']};
        }}
    """
    
    LABEL_STYLE = f"""
        QLabel {{
            color: {colors['text']};
            background-color: transparent;
            padding: 2px;
        }}
    """
    
    GROUPBOX_STYLE = f"""
        QGroupBox {{
            border: 1px solid {colors['border']};
            margin-top: 10px;
            padding: 10px;
            border-radius: 3px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px 0 5px;
            left: 10px;
            color: {colors['text']};
            background-color: {colors['bg']};
        }}
    """


def build_ingest_tab():
    """Build the ingest tab with all necessary controls and progress tracking."""
    
    print("DEBUG: Creating IngestViewModel...")
    vm = IngestViewModel()
    print("DEBUG: IngestViewModel created successfully")
    
    # Create the main widget and layout
    root = QWidget()
    root.setObjectName("ingest_tab")
    root.file_widgets = {}  # Track file progress widgets
    root.active_files = 0   # Track active file count
    root.current_job = None # Track current job for cleanup
    
    # Make vm accessible to the widget
    root.vm = vm
    print("DEBUG: VM attached to root widget")
    
    layout = QVBoxLayout(root)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(16)
    
    # Header
    header_label = QLabel("Turbo Transfer")
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
    
    # Apply hover delegate for proper hover effects
    try:
        apply_hover_delegate(verify_combo)
        print("DEBUG: Applied hover delegate to verify_combo")
    except Exception as e:
        print(f"DEBUG: Failed to apply hover delegate to verify_combo: {e}")
    
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
    
    # Apply hover delegate for proper hover effects
    try:
        apply_hover_delegate(preset_combo)
        print("DEBUG: Applied hover delegate to preset_combo")
    except Exception as e:
        print(f"DEBUG: Failed to apply hover delegate to preset_combo: {e}")
    
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
    progress_frame.setStyleSheet(f"background-color: {colors['card_bg']}; border-radius: 8px; padding: 20px;")
    progress_layout = QVBoxLayout(progress_frame)
    progress_layout.setSpacing(16)
    
    # Total progress with integrated label
    total_progress = QProgressBar()
    total_progress.setRange(0, 100)
    total_progress.setValue(0)
    total_progress.setFixedHeight(24)
    total_progress.setStyleSheet(f"""
        QProgressBar {{
            border: 1px solid {colors['border']};
            border-radius: 2px;
            text-align: center;
            background-color: {colors['card_bg']};
            color: {colors['text']};
            font-size: 12px;
            font-weight: 600;
        }}
        QProgressBar::chunk {{
            background-color: {colors['accent']};
            border-radius: 1px;
        }}
    """)
    progress_layout.addWidget(total_progress)
    
    # Speed display (large and prominent)
    speed_label = QLabel("0 MB/s Transfer")
    speed_label.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {colors['success']}; text-align: center; margin: 8px 0;")
    speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    progress_layout.addWidget(speed_label)
    
    layout.addWidget(progress_frame)
    
    # Individual files (compact)
    files_frame = QFrame()
    files_frame.setStyleSheet(f"background-color: {colors['card_bg']}; border-radius: 8px; padding: 20px;")
    files_layout = QVBoxLayout(files_frame)
    
    files_header = QHBoxLayout()
    files_label = QLabel("Individual Files")
    files_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {colors['text']};")
    files_count = QLabel("0 files")
    files_count.setStyleSheet(f"font-size: 14px; color: {colors['secondary_text']};")
    files_header.addWidget(files_label)
    files_header.addStretch()
    files_header.addWidget(files_count)
    files_layout.addLayout(files_header)
    
    # Scrollable area for file progress
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setMinimumHeight(150)
    scroll_area.setMaximumHeight(300)
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
    
    # Files container
    files_container = QWidget()
    files_container_layout = QVBoxLayout(files_container)
    files_container_layout.setSpacing(6)
    files_container_layout.setContentsMargins(0, 0, 0, 0)
    
    scroll_area.setWidget(files_container)
    files_layout.addWidget(scroll_area)
    
    layout.addWidget(files_frame)
    
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
    
    # Define event handlers in the outer scope so they can access UI widgets
    def handle_job_started(payload):
        print(f"DEBUG: handle_job_started called with: {payload}")
        total_bytes = payload.get("total_bytes", 0)
        total_files = payload.get("total_files", 0)
        print(f"DEBUG: Job started with {total_bytes} bytes and {total_files} files")
        print(f"DEBUG: Resetting UI for new job")
        # Reset progress and file count
        total_progress.setValue(0)
        speed_label.setText("0 MB/s Transfer")
        files_count.setText("0 files")
        # Clear any existing file widgets
        for widget in root.file_widgets.values():
            files_container_layout.removeWidget(widget)
            widget.deleteLater()
        root.file_widgets.clear()
        root.active_files = 0
        print(f"DEBUG: UI reset completed")
        print(f"DEBUG: Files container now has {files_container_layout.count()} widgets")
        
    def handle_job_progress(payload):
        print(f"DEBUG: handle_job_progress called with: {payload}")
        mbps = payload.get("mbps", 0.0)
        total = max(1, payload.get("total", 1))
        percent = int(100 * payload.get("bytes", 0) / total)
        print(f"DEBUG: Setting total progress to {percent}% and speed to {mbps:.0f} MB/s")
        print(f"DEBUG: total_progress widget: {total_progress}")
        print(f"DEBUG: speed_label widget: {speed_label}")
        print(f"DEBUG: total_progress current value: {total_progress.value()}")
        print(f"DEBUG: speed_label current text: {speed_label.text()}")
        print(f"DEBUG: total_progress is visible: {total_progress.isVisible()}")
        print(f"DEBUG: total_progress size: {total_progress.size()}")
        total_progress.setValue(percent)
        speed_label.setText(f"{mbps:.0f} MB/s Transfer")
        print(f"DEBUG: Progress and speed updated successfully")
        print(f"DEBUG: total_progress new value: {total_progress.value()}")
        print(f"DEBUG: speed_label new text: {speed_label.text()}")
        # Force a repaint
        total_progress.repaint()
        speed_label.repaint()
        
    def handle_file_started(payload):
        print(f"DEBUG: handle_file_started called with: {payload}")
        file_id = payload.get("file_id")
        filename = payload.get("filename")
        total_bytes = payload.get("total_bytes", 0)
        print(f"DEBUG: Creating FileProgressLine for {filename} with {total_bytes} bytes")
        widget = FileProgressLine(filename, total_bytes)
        root.file_widgets[file_id] = widget
        files_container_layout.addWidget(widget)
        root.active_files += 1
        files_count.setText(f"{root.active_files} files")
        # Store start time in the widget itself for speed calculation
        widget.start_time = time.time()
        print(f"DEBUG: File widget added, active files: {root.active_files}")
        print(f"DEBUG: File widgets now: {list(root.file_widgets.keys())}")
        print(f"DEBUG: Widget parent: {widget.parent()}")
        print(f"DEBUG: Widget visible: {widget.isVisible()}")
        print(f"DEBUG: Widget size: {widget.size()}")
        print(f"DEBUG: Container layout count: {files_container_layout.count()}")
        # Force widget to be visible
        widget.show()
        widget.raise_()
        # Force a repaint of the container
        files_container.update()
        files_container.repaint()
        
    def handle_file_progress(payload):
        print(f"DEBUG: handle_file_progress called with: {payload}")
        file_id = payload.get("file_id")
        copied_bytes = payload.get("bytes", 0)
        print(f"DEBUG: Updating progress for file {file_id}: {copied_bytes} bytes")
        if file_id in root.file_widgets:
            widget = root.file_widgets[file_id]
            # Calculate speed using the widget's start time
            if hasattr(widget, 'start_time'):
                elapsed = time.time() - widget.start_time
                if elapsed > 0:
                    speed = (copied_bytes / elapsed) / (1024 * 1024)
                    print(f"DEBUG: Calculating speed: {speed:.1f} MB/s")
                    print(f"DEBUG: Calling update_progress on widget {file_id}")
                    widget.update_progress(copied_bytes, speed)
                    print(f"DEBUG: update_progress completed for {file_id}")
                else:
                    print(f"DEBUG: No elapsed time, updating progress without speed")
                    print(f"DEBUG: Calling update_progress on widget {file_id}")
                    widget.update_progress(copied_bytes)
                    print(f"DEBUG: update_progress completed for {file_id}")
            else:
                print(f"DEBUG: No start time, updating progress without speed")
                print(f"DEBUG: Calling update_progress on widget {file_id}")
                widget.update_progress(copied_bytes)
                print(f"DEBUG: update_progress completed for {file_id}")
        else:
            print(f"DEBUG: File widget not found for file_id: {file_id}")
            print(f"DEBUG: Available file widgets: {list(root.file_widgets.keys())}")
            
    def handle_file_completed(payload):
        print(f"DEBUG: handle_file_completed called with: {payload}")
        file_id = payload.get("file_id")
        if file_id in root.file_widgets:
            root.file_widgets[file_id].mark_completed()
            root.active_files -= 1
            files_count.setText(f"{root.active_files} files")
            # Remove completed files after a delay
            # Use QTimer.singleShot to ensure this happens on the main thread
            QTimer.singleShot(2000, lambda f=file_id: _remove_file_widget(f))
            
    def handle_file_failed(payload):
        print(f"DEBUG: handle_file_failed called with: {payload}")
        file_id = payload.get("file_id")
        error = payload.get("error", "Unknown error")
        if file_id in root.file_widgets:
            root.file_widgets[file_id].mark_failed(error)
            root.active_files -= 1
            files_count.setText(f"{root.active_files} files")

    def handle_job_completed(payload):
        print(f"DEBUG: handle_job_completed called with: {payload}")
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

    def _remove_file_widget(file_id: str):
        print(f"DEBUG: _remove_file_widget called for {file_id}")
        if file_id in root.file_widgets:
            widget = root.file_widgets[file_id]
            print(f"DEBUG: Removing widget {file_id} from layout")
            files_container_layout.removeWidget(widget)
            widget.deleteLater()
            del root.file_widgets[file_id]
            print(f"DEBUG: Widget {file_id} removed successfully")
        else:
            print(f"DEBUG: Widget {file_id} not found in root.file_widgets")

    # Create the QtSink class in the outer scope so it can reference the event handlers
    class QtSink:
        def emit(self, event_type: str, payload: dict) -> None:
            print(f"DEBUG: QtSink received event: {event_type} with payload: {payload}")
            # Use QTimer.singleShot to ensure UI updates happen on the main thread
            # This is required because the engine runs in a background thread
            if event_type == "job.started":
                print(f"DEBUG: Scheduling handle_job_started on main thread")
                QTimer.singleShot(0, lambda: handle_job_started(payload))
            elif event_type == "job.progress":
                print(f"DEBUG: Scheduling handle_job_progress on main thread")
                QTimer.singleShot(0, lambda: handle_job_progress(payload))
            elif event_type == "file.started":
                print(f"DEBUG: Scheduling handle_file_started on main thread")
                QTimer.singleShot(0, lambda: handle_file_started(payload))
            elif event_type == "file.progress":
                print(f"DEBUG: Scheduling handle_file_progress on main thread")
                QTimer.singleShot(0, lambda: handle_file_progress(payload))
            elif event_type == "file.completed":
                print(f"DEBUG: Scheduling handle_file_completed on main thread")
                QTimer.singleShot(0, lambda: handle_file_completed(payload))
            elif event_type == "file.failed":
                print(f"DEBUG: Scheduling handle_file_failed on main thread")
                QTimer.singleShot(0, lambda: handle_file_failed(payload))
            elif event_type == "job.completed":
                print(f"DEBUG: Scheduling handle_job_completed on main thread")
                QTimer.singleShot(0, lambda: handle_job_completed(payload))
            else:
                print(f"DEBUG: Unknown event type: {event_type}")
    
    # Create the sink instance and attach it to the root widget
    root.qt_sink = QtSink()
    
    # Wire up button handlers
    def on_start():
        if not src_edit.text().strip() or not dst_edit.text().strip():
            print("DEBUG: Source or destination path is empty")
            return
        
        # Create a unique job ID
        job_id = f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"DEBUG: Starting ingest job: {job_id}")
        
        # Update UI state
        start_btn.setEnabled(False)
        pause_btn.setEnabled(True)
        cancel_btn.setEnabled(True)
        
        def run():
            print(f"DEBUG: Starting ingest job in background thread")
            # Get job parameters from UI
            source_path = src_edit.text().strip()
            dest_path = dst_edit.text().strip()
            verification = verify_combo.currentText()
            conc_level = conc_slider.value()
            stream_level = stream_slider.value()
            
            print(f"DEBUG: Source: {source_path}")
            print(f"DEBUG: Destination: {dest_path}")
            print(f"DEBUG: Verification: {verification}")
            print(f"DEBUG: Concurrency: {conc_level}")
            print(f"DEBUG: Streams: {stream_level}")
            
            try:
                # Import the necessary classes for creating a proper job
                from ..api.models import JobSpec, JobOptions
                from pathlib import Path
                
                # Create a JobSpec with the source and destination
                job = JobSpec(
                    job_id=job_id,
                    source_root=source_path,
                    destination_root=dest_path,
                    options=JobOptions(
                        mode="BALANCED" if "xxHash64" in verification else "FAST",
                        per_file_concurrency=conc_level,
                        stream_concurrency=stream_level
                    )
                )
                
                print(f"DEBUG: Created JobSpec: {job}")
                
                # Use the locally created QtSink
                sink = root.qt_sink
                
                # Create and start the engine
                engine = PythonCopyEngine(sink=sink)
                root.current_job = engine  # Track for cleanup
                
                # Freeze controls during copy
                conc_slider.setEnabled(False)
                stream_slider.setEnabled(False)
                verify_combo.setEnabled(False)
                preset_combo.setEnabled(False)
                
                print(f"DEBUG: Starting engine with job: {job}")
                engine.start(job)
                print(f"DEBUG: Engine completed")
                
            except Exception as e:
                print(f"DEBUG: Error starting engine: {e}")
                import traceback
                traceback.print_exc()
                # Re-enable controls on error
                conc_slider.setEnabled(True)
                stream_slider.setEnabled(True)
                verify_combo.setEnabled(True)
                preset_combo.setEnabled(True)
                start_btn.setEnabled(True)
                pause_btn.setEnabled(False)
                cancel_btn.setEnabled(False)

        # Start in background thread
        job_thread = threading.Thread(target=run, daemon=True)
        job_thread.start()
        root.current_job = job_thread
    
    def on_pause():
        print("DEBUG: Pause button clicked")
        if root.current_job and hasattr(root.current_job, 'pause'):
            print("DEBUG: Pausing engine")
            root.current_job.pause(root.current_job.job_id if hasattr(root.current_job, 'job_id') else 'current')
        pause_btn.setEnabled(False)
        start_btn.setEnabled(True)

    def on_cancel():
        print("DEBUG: Cancel button clicked")
        if root.current_job and hasattr(root.current_job, 'cancel'):
            print("DEBUG: Canceling engine")
            root.current_job.cancel(root.current_job.job_id if hasattr(root.current_job, 'job_id') else 'current')
        
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

    # Connect buttons
    start_btn.clicked.connect(on_start)
    pause_btn.clicked.connect(on_pause)
    cancel_btn.clicked.connect(on_cancel)
    
    # Browse button handlers
    def browse_source():
        path = QFileDialog.getExistingDirectory(root, "Select Source Directory")
        if path:
            src_edit.setText(path)
    
    def browse_dest():
        path = QFileDialog.getExistingDirectory(root, "Select Destination Directory")
        if path:
            dst_edit.setText(path)
    
    src_btn.clicked.connect(browse_source)
    dst_btn.clicked.connect(browse_dest)
    
    return root



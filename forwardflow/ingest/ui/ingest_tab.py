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

# Import app's existing styles
from app.ui.color_scheme_pyqt import (
    colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, 
    COMBOBOX_STYLE, LINEEDIT_STYLE, LABEL_STYLE
)


class AppProgressBar(QProgressBar):
    """Progress bar using the app's color scheme."""
    
    def __init__(self, height: int = 8):
        super().__init__()
        self.setFixedHeight(height)
        self.setTextVisible(False)
        self.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {colors['border']};
                border-radius: {height//2}px;
                background-color: {colors['bg']};
                text-align: center;
            }}
            QProgressBar::chunk {{
                border-radius: {height//2}px;
                background-color: {colors['accent']};
            }}
        """)


class FileProgressCard(QFrame):
    """File progress card using app styling."""
    
    def __init__(self, filename: str, total_bytes: int):
        super().__init__()
        self.filename = filename
        self.total_bytes = total_bytes
        self.copied_bytes = 0
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(80)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Header row with filename and percentage
        header_layout = QHBoxLayout()
        
        # Filename (truncated if too long)
        display_name = filename[:40] + "..." if len(filename) > 40 else filename
        self.name_label = QLabel(display_name)
        self.name_label.setStyleSheet(LABEL_STYLE + f"font-weight: 600; font-size: 13px;")
        self.name_label.setToolTip(filename)
        header_layout.addWidget(self.name_label)
        
        # Percentage
        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet(f"color: {colors['accent']}; font-weight: 600; font-size: 12px;")
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(self.percent_label)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = AppProgressBar(height=6)
        layout.addWidget(self.progress_bar)
        
        # Status row
        status_layout = QHBoxLayout()
        
        # File size
        size_mb = total_bytes / (1024 * 1024)
        self.size_label = QLabel(f"{size_mb:.1f} MB")
        self.size_label.setStyleSheet(f"color: {colors['secondary_text']}; font-size: 11px;")
        status_layout.addWidget(self.size_label)
        
        # Speed (will be updated)
        self.speed_label = QLabel("")
        self.speed_label.setStyleSheet(f"color: {colors['secondary_text']}; font-size: 11px;")
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        status_layout.addWidget(self.speed_label)
        
        layout.addLayout(status_layout)
        
        # Card styling using app colors
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
            }}
        """)
    
    def update_progress(self, copied_bytes: int, speed_mbps: float = 0):
        self.copied_bytes = copied_bytes
        if self.total_bytes > 0:
            percent = int(100 * copied_bytes / self.total_bytes)
            self.progress_bar.setValue(percent)
            self.percent_label.setText(f"{percent}%")
            
            if speed_mbps > 0:
                self.speed_label.setText(f"{speed_mbps:.1f} MB/s")
    
    def mark_completed(self):
        self.progress_bar.setValue(100)
        self.percent_label.setText("100%")
        self.speed_label.setText("Complete")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['success']};
                border-radius: 8px;
            }}
        """)
    
    def mark_failed(self, error: str):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['error']};
                border-radius: 8px;
            }}
        """)
        self.speed_label.setText(f"Failed: {error}")


def build_ingest_tab() -> QWidget:
    vm = IngestViewModel()
    root = QWidget()
    
    # Make vm accessible to the widget
    root.vm = vm
    
    layout = QVBoxLayout(root)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(20)

    # Header
    header_label = QLabel("Turbo Ingest")
    header_label.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {colors['text']}; margin-bottom: 8px;")
    layout.addWidget(header_label)

    # Source picker
    src_row = QHBoxLayout()
    src_label = QLabel("Source (card):")
    src_label.setStyleSheet(f"font-weight: 600; color: {colors['text']}; min-width: 120px;")
    src_edit = QLineEdit()
    src_edit.setStyleSheet(LINEEDIT_STYLE)
    src_edit.setPlaceholderText("Select source folder...")
    src_btn = QPushButton("Browse…")
    src_btn.setStyleSheet(BUTTON_STYLE)
    src_btn.clicked.connect(lambda: _pick_dir(src_edit))
    src_row.addWidget(src_label)
    src_row.addWidget(src_edit, 1)
    src_row.addWidget(src_btn)
    layout.addLayout(src_row)

    # Destination picker
    dst_row = QHBoxLayout()
    dst_label = QLabel("Destination:")
    dst_label.setStyleSheet(f"font-weight: 600; color: {colors['text']}; min-width: 120px;")
    dst_edit = QLineEdit()
    dst_edit.setStyleSheet(LINEEDIT_STYLE)
    dst_edit.setPlaceholderText("Select destination folder...")
    dst_btn = QPushButton("Browse…")
    dst_btn.setStyleSheet(BUTTON_STYLE)
    dst_btn.clicked.connect(lambda: _pick_dir(dst_edit))
    dst_row.addWidget(dst_label)
    dst_row.addWidget(dst_edit, 1)
    dst_row.addWidget(dst_btn)
    layout.addLayout(dst_row)

    # Settings row
    settings_layout = QHBoxLayout()
    
    # Verification settings
    verify_layout = QVBoxLayout()
    verify_label = QLabel("Verification:")
    verify_label.setStyleSheet(f"font-weight: 600; color: {colors['text']}; margin-bottom: 4px;")
    verify_combo = QComboBox()
    verify_combo.addItems([
        "None — fastest transfer (no hashing)",
        "xxHash64 — fast verification",
        "Cryptographic (disabled)",
    ])
    verify_combo.setStyleSheet(COMBOBOX_STYLE)
    verify_combo.setCurrentIndex(1)
    verify_combo.setToolTip("Choose data verification level. None is fastest, xxHash64 is fast and safe for ingest.")
    verify_layout.addWidget(verify_label)
    verify_layout.addWidget(verify_combo)
    settings_layout.addLayout(verify_layout)
    
    # Link speed presets
    preset_layout = QVBoxLayout()
    preset_label = QLabel("Link preset:")
    preset_label.setStyleSheet(f"font-weight: 600; color: {colors['text']}; margin-bottom: 4px;")
    preset_combo = QComboBox()
    preset_combo.addItems(["Auto/Default", "1 GbE", "10 GbE", "25/40 GbE or IB"])
    preset_combo.setStyleSheet(COMBOBOX_STYLE)
    preset_combo.setToolTip("Sets sensible defaults for concurrency based on your network link.")
    preset_layout.addWidget(preset_label)
    preset_layout.addWidget(preset_combo)
    settings_layout.addLayout(preset_layout)
    
    layout.addLayout(settings_layout)

    # Concurrency sliders
    conc_row = QHBoxLayout()
    conc_label = QLabel("Per-file concurrency:")
    conc_label.setStyleSheet(f"font-weight: 600; color: {colors['text']}; min-width: 150px;")
    conc_slider = QSlider(Qt.Orientation.Horizontal)
    conc_slider.setRange(1, 16)
    conc_slider.setValue(2)
    conc_slider.setStyleSheet(f"""
        QSlider::groove:horizontal {{
            border: 1px solid {colors['border']};
            height: 6px;
            background: {colors['card_bg']};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {colors['accent']};
            border: 1px solid {colors['accent']};
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {colors['accent_hover']};
        }}
    """)
    conc_slider.setToolTip("How many files to copy at the same time. Higher = more files concurrently.")
    conc_value = QLabel("2")
    conc_value.setStyleSheet(f"color: {colors['accent']}; font-weight: 600; min-width: 30px;")
    conc_slider.valueChanged.connect(lambda v: conc_value.setText(str(v)))
    conc_row.addWidget(conc_label)
    conc_row.addWidget(conc_slider, 1)
    conc_row.addWidget(conc_value)
    layout.addLayout(conc_row)

    stream_row = QHBoxLayout()
    stream_label = QLabel("Stream concurrency:")
    stream_label.setStyleSheet(f"font-weight: 600; color: {colors['text']}; min-width: 150px;")
    stream_slider = QSlider(Qt.Orientation.Horizontal)
    stream_slider.setRange(1, 32)
    stream_slider.setValue(8)
    stream_slider.setStyleSheet(f"""
        QSlider::groove:horizontal {{
            border: 1px solid {colors['border']};
            height: 6px;
            background: {colors['card_bg']};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {colors['accent']};
            border: 1px solid {colors['accent']};
            border-radius: 9px;
            width: 18px;
            margin: -6px 0;
        }}
        QSlider::handle:horizontal:hover {{
            background: {colors['accent_hover']};
        }}
    """)
    stream_slider.setToolTip("How many parallel streams to use per file >1 GiB. 8 is a good default for 10 GbE.")
    stream_value = QLabel("8")
    stream_value.setStyleSheet(f"color: {colors['accent']}; font-weight: 600; min-width: 30px;")
    stream_slider.valueChanged.connect(lambda v: stream_value.setText(str(v)))
    stream_row.addWidget(stream_label)
    stream_row.addWidget(stream_slider, 1)
    stream_row.addWidget(stream_value)
    layout.addLayout(stream_row)

    # Now wire presets to sliders
    def apply_preset():
        choice = preset_combo.currentText()
        if choice == "1 GbE":
            conc_slider.setValue(1)
            stream_slider.setValue(2)
        elif choice == "10 GbE":
            conc_slider.setValue(2)
            stream_slider.setValue(8)
        elif choice == "25/40 GbE or IB":
            conc_slider.setValue(3)
            stream_slider.setValue(16)
        else:  # Auto/Default
            conc_slider.setValue(2)
            stream_slider.setValue(8)

    preset_combo.currentIndexChanged.connect(apply_preset)
    apply_preset()

    # Controls
    btn_row = QHBoxLayout()
    start_btn = QPushButton("Start Transfer")
    start_btn.setStyleSheet(ACCENT_BUTTON_STYLE + "min-width: 120px; padding: 12px 24px; font-size: 14px; font-weight: 700;")
    
    pause_btn = QPushButton("Pause")
    pause_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {colors['warning']};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            font-size: 14px;
            min-width: 100px;
        }}
        QPushButton:hover {{
            background-color: #e67e00;
        }}
        QPushButton:pressed {{
            background-color: #cc7000;
        }}
        QPushButton:disabled {{
            background-color: {colors['border']};
            color: {colors['secondary_text']};
        }}
    """)
    
    cancel_btn = QPushButton("Cancel")
    cancel_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {colors['error']};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            font-size: 14px;
            min-width: 100px;
        }}
        QPushButton:hover {{
            background-color: #b02a2e;
        }}
        QPushButton:pressed {{
            background-color: #8f2124;
        }}
        QPushButton:disabled {{
            background-color: {colors['border']};
            color: {colors['secondary_text']};
        }}
    """)
    
    btn_row.addWidget(start_btn)
    btn_row.addWidget(pause_btn)
    btn_row.addWidget(cancel_btn)
    layout.addLayout(btn_row)

    # Total Progress Section
    total_progress_frame = QFrame()
    total_progress_frame.setStyleSheet(f"""
        QFrame {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: 12px;
            padding: 20px;
        }}
    """)
    total_layout = QVBoxLayout(total_progress_frame)
    total_layout.setSpacing(16)
    
    # Total progress header
    total_header = QHBoxLayout()
    total_label = QLabel("TOTAL TRANSFER")
    total_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {colors['text']};")
    total_header.addWidget(total_label)
    
    total_percent = QLabel("0%")
    total_percent.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {colors['accent']};")
    total_percent.setAlignment(Qt.AlignmentFlag.AlignRight)
    total_header.addWidget(total_percent)
    total_layout.addLayout(total_header)
    
    # Total progress bar
    total_progress = AppProgressBar(height=12)
    total_layout.addWidget(total_progress)
    
    # Speed and status row
    status_row = QHBoxLayout()
    
    # Speed display
    speed_label = QLabel("0 MB/s")
    speed_label.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {colors['success']};")
    status_row.addWidget(speed_label)
    
    # Status message
    status_msg = QLabel("Ready to transfer")
    status_msg.setStyleSheet(f"font-size: 14px; color: {colors['secondary_text']};")
    status_msg.setAlignment(Qt.AlignmentFlag.AlignRight)
    status_row.addWidget(status_msg)
    
    total_layout.addLayout(status_row)
    layout.addWidget(total_progress_frame)

    # Individual File Progress Section
    files_header = QHBoxLayout()
    files_label = QLabel("Individual Files")
    files_label.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {colors['text']};")
    files_header.addWidget(files_label)
    
    files_count = QLabel("0 files")
    files_count.setStyleSheet(f"font-size: 14px; color: {colors['secondary_text']};")
    files_count.setAlignment(Qt.AlignmentFlag.AlignRight)
    files_header.addWidget(files_count)
    
    layout.addLayout(files_header)
    
    # Scrollable area for file progress widgets
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setMaximumHeight(300)
    scroll_area.setStyleSheet(f"""
        QScrollArea {{
            border: 1px solid {colors['border']};
            border-radius: 8px;
            background-color: {colors['bg']};
        }}
        QScrollBar:vertical {{
            background-color: {colors['card_bg']};
            width: 12px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {colors['border']};
            border-radius: 6px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {colors['accent']};
        }}
    """)
    
    files_container = QWidget()
    files_layout = QVBoxLayout(files_container)
    files_layout.setSpacing(8)
    files_layout.setContentsMargins(16, 16, 16, 16)
    
    scroll_area.setWidget(files_container)
    layout.addWidget(scroll_area)

    # Job log path label
    log_label = QLabel("")
    log_label.setStyleSheet(f"color: {colors['secondary_text']}; font-size: 12px; margin-top: 8px;")
    layout.addWidget(log_label)

    # File tracking
    root.file_widgets = {}  # file_id -> FileProgressCard
    root.active_files = 0

    # Wire up
    def on_start():
        if not vm.enabled:
            status_msg.setText("Ingest is disabled by feature flag.")
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
            vm.mode = "BALANCED"  # STRICT disabled for Phase 1
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
        total_percent.setText("0%")
        speed_label.setText("0 MB/s")
        status_msg.setText("Transfer in progress...")

        def run():
            # Attach a sink to receive progress and update UI
            class QtSink:
                def __init__(self):
                    self._file_stats = {}

                def emit(self, event_type: str, payload: dict) -> None:
                    print(f"DEBUG: Received event {event_type}: {payload}")  # Debug logging
                    if event_type == "job.progress":
                        mbps = payload.get("mbps", 0.0)
                        eta = payload.get("eta_seconds", 0.0)
                        def upd():
                            total = max(1, payload.get("total", 1))
                            percent = int(100 * payload.get("bytes", 0) / total)
                            total_progress.setValue(percent)
                            total_percent.setText(f"{percent}%")
                            speed_label.setText(f"{mbps:.0f} MB/s")
                        QTimer.singleShot(0, upd)
                    elif event_type == "file.started":
                        def upd():
                            file_id = payload.get("file_id")
                            filename = payload.get("filename")
                            total_bytes = payload.get("total_bytes", 0)
                            widget = FileProgressCard(filename, total_bytes)
                            root.file_widgets[file_id] = widget
                            files_layout.addWidget(widget)
                            root.active_files += 1
                            files_count.setText(f"{root.active_files} files")
                            self._file_stats[file_id] = {'start_time': time.time()}
                        QTimer.singleShot(0, upd)
                    elif event_type == "file.progress":
                        def upd():
                            file_id = payload.get("file_id")
                            copied_bytes = payload.get("bytes", 0)
                            if file_id in root.file_widgets:
                                # Calculate speed for this file
                                file_stats = self._file_stats.get(file_id, {})
                                if file_stats:
                                    elapsed = time.time() - file_stats.get('start_time', time.time())
                                    if elapsed > 0:
                                        speed = (copied_bytes / elapsed) / (1024 * 1024)
                                        root.file_widgets[file_id].update_progress(copied_bytes, speed)
                                    else:
                                        root.file_widgets[file_id].update_progress(copied_bytes)
                                else:
                                    root.file_widgets[file_id].update_progress(copied_bytes)
                        QTimer.singleShot(0, upd)
                    elif event_type == "file.completed":
                        def upd():
                            file_id = payload.get("file_id")
                            if file_id in root.file_widgets:
                                root.file_widgets[file_id].mark_completed()
                                root.active_files -= 1
                                files_count.setText(f"{root.active_files} files")
                                # Remove completed files after a delay
                                QTimer.singleShot(2000, lambda: _remove_file_widget(file_id))
                        QTimer.singleShot(0, upd)
                    elif event_type == "file.failed":
                        def upd():
                            file_id = payload.get("file_id")
                            error = payload.get("error", "Unknown error")
                            if file_id in root.file_widgets:
                                root.file_widgets[file_id].mark_failed(error)
                                root.active_files -= 1
                                files_count.setText(f"{root.active_files} files")
                        QTimer.singleShot(0, upd)

            engine = PythonCopyEngine(sink=QtSink())
            vm._engine_override = engine
            # Freeze controls during copy
            conc_slider.setEnabled(False)
            stream_slider.setEnabled(False)
            verify_combo.setEnabled(False)
            vm.start(job_id)
            def done():
                total_progress.setRange(0, 1)
                total_progress.setValue(1)
                start_btn.setEnabled(True)
                pause_btn.setEnabled(False)
                cancel_btn.setEnabled(False)
                # Re-enable controls for next run
                conc_slider.setEnabled(True)
                stream_slider.setEnabled(True)
                verify_combo.setEnabled(True)
                mhl = (vm.destination or Path(".")) / f"{job_id}.mhl"
                log_label.setText(f"MHL: {mhl}")
                status_msg.setText("Transfer complete")
            QTimer.singleShot(0, done)

        threading.Thread(target=run, daemon=True).start()

    def _remove_file_widget(file_id: str):
        if file_id in root.file_widgets:
            widget = root.file_widgets[file_id]
            files_layout.removeWidget(widget)
            widget.deleteLater()
            del root.file_widgets[file_id]

    def on_pause():
        vm.pause_current()
        status_msg.setText("Paused. Click Start to resume.")

    def on_cancel():
        vm.cancel_current()
        status_msg.setText("Canceled. Partial files kept with .part extension.")

    # Make functions attributes of the widget
    root.on_start = on_start
    root.on_pause = on_pause
    root.on_cancel = on_cancel
    root._remove_file_widget = _remove_file_widget

    start_btn.clicked.connect(on_start)
    pause_btn.clicked.connect(on_pause)
    cancel_btn.clicked.connect(on_cancel)

    return root


def _pick_dir(target_edit: QLineEdit) -> None:
    directory = QFileDialog.getExistingDirectory(None, "Select Folder")
    if directory:
        target_edit.setText(directory)



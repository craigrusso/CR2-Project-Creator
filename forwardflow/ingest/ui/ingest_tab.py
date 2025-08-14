"""PyQt6 Ingest tab builder for Phase 1.

Lightweight UI built here to keep ingest self-contained. The host app
calls `build_ingest_tab()` under a feature flag to add the tab.
"""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path

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
)

from .ingest_vm import IngestViewModel
from ..engines.python_engine import PythonCopyEngine


class FileProgressWidget(QFrame):
    """Individual file progress widget."""
    
    def __init__(self, filename: str, total_bytes: int):
        super().__init__()
        self.filename = filename
        self.total_bytes = total_bytes
        self.copied_bytes = 0
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        
        # File name label
        self.name_label = QLabel(filename)
        self.name_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        layout.addWidget(self.name_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444444;
                border-radius: 3px;
                text-align: center;
                background-color: #2a2a2a;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Percentage label
        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet("color: #cccccc; font-size: 10px;")
        layout.addWidget(self.percent_label)
        
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 4px;
            }
        """)
    
    def update_progress(self, copied_bytes: int):
        self.copied_bytes = copied_bytes
        if self.total_bytes > 0:
            percent = int(100 * copied_bytes / self.total_bytes)
            self.progress_bar.setValue(percent)
            self.percent_label.setText(f"{percent}%")
    
    def mark_completed(self):
        self.progress_bar.setValue(100)
        self.percent_label.setText("100%")
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #00aa00;
                border-radius: 4px;
                padding: 4px;
            }
        """)
    
    def mark_failed(self, error: str):
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #aa0000;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        self.percent_label.setText(f"Failed: {error}")


def build_ingest_tab() -> QWidget:
    vm = IngestViewModel()
    root = QWidget()
    layout = QVBoxLayout(root)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(8)

    # Source picker
    src_row = QHBoxLayout()
    src_label = QLabel("Source (card):")
    src_edit = QLineEdit()
    src_btn = QPushButton("Browse…")
    src_btn.clicked.connect(lambda: _pick_dir(src_edit))
    src_row.addWidget(src_label)
    src_row.addWidget(src_edit, 1)
    src_row.addWidget(src_btn)
    layout.addLayout(src_row)

    # Destination picker
    dst_row = QHBoxLayout()
    dst_label = QLabel("Destination:")
    dst_edit = QLineEdit()
    dst_btn = QPushButton("Browse…")
    dst_btn.clicked.connect(lambda: _pick_dir(dst_edit))
    dst_row.addWidget(dst_label)
    dst_row.addWidget(dst_edit, 1)
    dst_row.addWidget(dst_btn)
    layout.addLayout(dst_row)

    # Verification settings
    verify_row = QHBoxLayout()
    verify_label = QLabel("Verification:")
    verify_combo = QComboBox()
    verify_combo.addItems([
        "None — fastest transfer (no hashing)",
        "xxHash64 — fast verification",
        "Cryptographic (disabled)",
    ])
    # Link speed presets (sliders wired later after they are created)
    preset_row = QHBoxLayout()
    preset_label = QLabel("Link preset:")
    preset_combo = QComboBox()
    preset_combo.addItems(["Auto/Default", "1 GbE", "10 GbE", "25/40 GbE or IB"])
    preset_combo.setToolTip("Sets sensible defaults for concurrency based on your network link.")
    preset_row.addWidget(preset_label)
    preset_row.addWidget(preset_combo, 1)
    layout.addLayout(preset_row)
    verify_combo.setCurrentIndex(1)
    verify_combo.setToolTip("Choose data verification level. None is fastest, xxHash64 is fast and safe for ingest. Cryptographic will be added later.")
    verify_row.addWidget(verify_label)
    verify_row.addWidget(verify_combo, 1)
    layout.addLayout(verify_row)

    conc_row = QHBoxLayout()
    conc_label = QLabel("Per-file concurrency (files in parallel):")
    conc_slider = QSlider(Qt.Orientation.Horizontal)
    conc_slider.setRange(1, 16)
    conc_slider.setValue(2)
    conc_slider.setEnabled(True)
    conc_slider.setToolTip("How many files to copy at the same time. Higher = more files concurrently.")
    conc_row.addWidget(conc_label)
    conc_row.addWidget(conc_slider, 1)
    layout.addLayout(conc_row)

    stream_row = QHBoxLayout()
    stream_label = QLabel("Stream concurrency (parallel streams per large file):")
    stream_slider = QSlider(Qt.Orientation.Horizontal)
    stream_slider.setRange(1, 32)
    stream_slider.setValue(8)
    stream_slider.setEnabled(True)
    stream_slider.setToolTip("How many parallel streams to use per file >1 GiB. 8 is a good default for 10 GbE.")
    stream_row.addWidget(stream_label)
    stream_row.addWidget(stream_slider, 1)
    layout.addLayout(stream_row)

    # Now wire presets to sliders (sliders exist above)
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
    start_btn = QPushButton("Start")
    pause_btn = QPushButton("Pause")
    cancel_btn = QPushButton("Cancel")
    btn_row.addWidget(start_btn)
    btn_row.addWidget(pause_btn)
    btn_row.addWidget(cancel_btn)
    layout.addLayout(btn_row)

    # Total Progress Section
    total_progress_frame = QFrame()
    total_progress_frame.setStyleSheet("""
        QFrame {
            background-color: #2a2a2a;
            border: 1px solid #444444;
            border-radius: 6px;
            padding: 8px;
        }
    """)
    total_layout = QVBoxLayout(total_progress_frame)
    
    # Total progress label
    total_label = QLabel("TOTAL TRANSFER 0% COMPLETE")
    total_label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 14px;")
    total_layout.addWidget(total_label)
    
    # Total progress bar
    total_progress = QProgressBar()
    total_progress.setRange(0, 100)
    total_progress.setValue(0)
    total_progress.setStyleSheet("""
        QProgressBar {
            border: 2px solid #444444;
            border-radius: 4px;
            text-align: center;
            background-color: #1e1e1e;
            height: 20px;
        }
        QProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 2px;
        }
    """)
    total_layout.addWidget(total_progress)
    
    # Speed display
    speed_label = QLabel("0 MB/s Transfer")
    speed_label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 16px;")
    total_layout.addWidget(speed_label)
    
    layout.addWidget(total_progress_frame)

    # Individual File Progress Section
    files_label = QLabel("Individual Files:")
    files_label.setStyleSheet("font-weight: bold; color: #ffffff; margin-top: 8px;")
    layout.addWidget(files_label)
    
    # Scrollable area for file progress widgets
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setMaximumHeight(200)
    scroll_area.setStyleSheet("""
        QScrollArea {
            border: 1px solid #444444;
            border-radius: 4px;
            background-color: #1e1e1e;
        }
    """)
    
    files_container = QWidget()
    files_layout = QVBoxLayout(files_container)
    files_layout.setSpacing(4)
    files_layout.setContentsMargins(4, 4, 4, 4)
    
    scroll_area.setWidget(files_container)
    layout.addWidget(scroll_area)

    # Job log path label
    log_label = QLabel("")
    layout.addWidget(log_label)

    # File tracking
    file_widgets = {}  # file_id -> FileProgressWidget

    # Wire up
    def on_start():
        if not vm.enabled:
            speed_label.setText("Ingest is disabled by feature flag.")
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
        start_btn.setEnabled(False)
        pause_btn.setEnabled(True)
        cancel_btn.setEnabled(True)
        
        # Clear previous file widgets
        for widget in file_widgets.values():
            files_layout.removeWidget(widget)
            widget.deleteLater()
        file_widgets.clear()
        
        # Reset progress
        total_progress.setValue(0)
        total_label.setText("TOTAL TRANSFER 0% COMPLETE")
        speed_label.setText("0 MB/s Transfer")

        def run():
            # Attach a sink to receive progress and update UI
            class QtSink:
                def emit(self, event_type: str, payload: dict) -> None:
                    if event_type == "job.progress":
                        mbps = payload.get("mbps", 0.0)
                        eta = payload.get("eta_seconds", 0.0)
                        def upd():
                            total = max(1, payload.get("total", 1))
                            percent = int(100 * payload.get("bytes", 0) / total)
                            total_progress.setValue(percent)
                            total_label.setText(f"TOTAL TRANSFER {percent}% COMPLETE")
                            speed_label.setText(f"{mbps:.0f} MB/s Transfer")
                        QTimer.singleShot(0, upd)
                    elif event_type == "file.started":
                        def upd():
                            file_id = payload.get("file_id")
                            filename = payload.get("filename")
                            total_bytes = payload.get("total_bytes", 0)
                            widget = FileProgressWidget(filename, total_bytes)
                            file_widgets[file_id] = widget
                            files_layout.addWidget(widget)
                        QTimer.singleShot(0, upd)
                    elif event_type == "file.progress":
                        def upd():
                            file_id = payload.get("file_id")
                            copied_bytes = payload.get("bytes", 0)
                            if file_id in file_widgets:
                                file_widgets[file_id].update_progress(copied_bytes)
                        QTimer.singleShot(0, upd)
                    elif event_type == "file.completed":
                        def upd():
                            file_id = payload.get("file_id")
                            if file_id in file_widgets:
                                file_widgets[file_id].mark_completed()
                                # Remove completed files after a delay
                                QTimer.singleShot(3000, lambda: _remove_file_widget(file_id))
                        QTimer.singleShot(0, upd)
                    elif event_type == "file.failed":
                        def upd():
                            file_id = payload.get("file_id")
                            error = payload.get("error", "Unknown error")
                            if file_id in file_widgets:
                                file_widgets[file_id].mark_failed(error)
                        QTimer.singleShot(0, upd)

            engine = PythonCopyEngine(sink=QtSink())
            vm._engine_override = engine  # hint for testing
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
                speed_label.setText("Copy complete.")
            QTimer.singleShot(0, done)

        threading.Thread(target=run, daemon=True).start()

    def _remove_file_widget(file_id: str):
        if file_id in file_widgets:
            widget = file_widgets[file_id]
            files_layout.removeWidget(widget)
            widget.deleteLater()
            del file_widgets[file_id]

    def on_pause():
        vm.pause_current()
        speed_label.setText("Paused. Click Start to resume.")

    def on_cancel():
        vm.cancel_current()
        speed_label.setText("Canceled. Partial files kept with .part extension.")

    start_btn.clicked.connect(on_start)
    pause_btn.clicked.connect(on_pause)
    cancel_btn.clicked.connect(on_cancel)

    return root


def _pick_dir(target_edit: QLineEdit) -> None:
    directory = QFileDialog.getExistingDirectory(None, "Select Folder")
    if directory:
        target_edit.setText(directory)



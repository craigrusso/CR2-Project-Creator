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
)

from .ingest_vm import IngestViewModel
from ..engines.python_engine import PythonCopyEngine


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

    # Progress
    progress = QProgressBar()
    progress.setRange(0, 100)
    progress.setValue(0)
    status = QLabel("")
    status.setWordWrap(True)
    layout.addWidget(progress)
    layout.addWidget(status)

    # Job log path label
    log_label = QLabel("")
    layout.addWidget(log_label)

    # Wire up
    def on_start():
        if not vm.enabled:
            status.setText("Ingest is disabled by feature flag.")
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
        status.setText("Copy in progress… Per-file controls how many files at once. Stream controls per-file parallelism for large files.")
        progress.setRange(0, 100)
        progress.setValue(0)

        def run():
            # Attach a sink to receive progress and update UI
            class QtSink:
                def emit(self, event_type: str, payload: dict) -> None:
                    if event_type == "job.progress":
                        mbps = payload.get("mbps", 0.0)
                        eta = payload.get("eta_seconds", 0.0)
                        def upd():
                            total = max(1, payload.get("total", 1))
                            progress.setValue(int(100 * payload.get("bytes", 0) / total))
                            status.setText(f"{mbps:.1f} MB/s, ETA {int(eta)} s")
                        QTimer.singleShot(0, upd)

            engine = PythonCopyEngine(sink=QtSink())
            vm._engine_override = engine  # hint for testing
            # Freeze controls during copy
            conc_slider.setEnabled(False)
            stream_slider.setEnabled(False)
            verify_combo.setEnabled(False)
            vm.start(job_id)
            def done():
                progress.setRange(0, 1)
                progress.setValue(1)
                start_btn.setEnabled(True)
                pause_btn.setEnabled(False)
                cancel_btn.setEnabled(False)
                # Re-enable controls for next run
                conc_slider.setEnabled(True)
                stream_slider.setEnabled(True)
                verify_combo.setEnabled(True)
                mhl = (vm.destination or Path(".")) / f"{job_id}.mhl"
                log_label.setText(f"MHL: {mhl}")
                status.setText("Copy complete.")
            QTimer.singleShot(0, done)

        threading.Thread(target=run, daemon=True).start()

    def on_pause():
        vm.pause_current()
        status.setText("Paused. Click Start to resume.")

    def on_cancel():
        vm.cancel_current()
        status.setText("Canceled. Partial files kept with .part extension.")

    start_btn.clicked.connect(on_start)
    pause_btn.clicked.connect(on_pause)
    cancel_btn.clicked.connect(on_cancel)

    return root


def _pick_dir(target_edit: QLineEdit) -> None:
    directory = QFileDialog.getExistingDirectory(None, "Select Folder")
    if directory:
        target_edit.setText(directory)



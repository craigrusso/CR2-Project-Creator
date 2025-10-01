"""Thin compatibility wrapper around the compiled Rust transfer engine."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, Dict

try:  # Optional PyQt6 support for queued signal delivery
    from PyQt6 import QtCore  # type: ignore

    HAS_QT = True
except Exception:  # pragma: no cover - Qt is optional at runtime
    QtCore = None  # type: ignore
    HAS_QT = False


try:
    _rust_mod = import_module("forwardflow.ingest.engines.rust_high_perf.rust_high_perf_engine")
except ImportError as exc:  # pragma: no cover - surfaced during startup
    raise RuntimeError("Compiled rust_high_perf_engine module is not available") from exc


PyEnhancedHighPerfTransferEngine = _rust_mod.PyEnhancedHighPerfTransferEngine
CopyJob = _rust_mod.CopyJob
CopyStats = _rust_mod.CopyStats


class _QtEmitter(QtCore.QObject if HAS_QT else object):  # type: ignore[misc]
    """Marshals Rust callbacks onto the Qt main thread when PyQt6 is present."""

    if HAS_QT:
        signal = QtCore.pyqtSignal(str, dict)  # type: ignore[attr-defined]

        def __init__(self, sink: Callable[[str, Dict[str, Any]], None]):
            super().__init__()
            self._sink = sink
            # CRITICAL: Use Qt.QueuedConnection for thread-safe cross-thread signal delivery
            self.signal.connect(self._on_signal, QtCore.Qt.ConnectionType.QueuedConnection)  # type: ignore[attr-defined]

        def _on_signal(self, event_type: str, payload: Dict[str, Any]) -> None:
            """Called on Qt main thread to deliver event to sink"""
            self._sink(event_type, payload)

        def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
            """Emit signal - Qt automatically marshals to main thread via QueuedConnection"""
            # Qt signals with QueuedConnection are thread-safe - they automatically 
            # marshal the call to the receiver's thread (main thread in our case)
            self.signal.emit(event_type, payload)  # type: ignore[attr-defined]

    else:
        def __init__(self, sink: Callable[[str, Dict[str, Any]], None]):
            self._sink = sink

        def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
            self._sink(event_type, payload)


class RustHighPerfEngineWrapper:
    """Python-side façade that normalises events and return values."""

    def __init__(self) -> None:
        self._engine = PyEnhancedHighPerfTransferEngine()
        self._normalise_event = self._build_normaliser()
        self._qt_bridge: _QtEmitter | None = None

    @staticmethod
    def _build_normaliser() -> Callable[[str, Dict[str, Any]], tuple[str, Dict[str, Any]]]:
        rename = {
            "job_progress": "progress_update",
            "bytes_copied": "bytesCopied",
            "total_bytes": "totalBytes",
            "files_completed": "completedFiles",
            "total_files": "totalFiles",
            "elapsed_s": "elapsedS",
            "speed_mib_s": "avgSpeedMiBps",
            "current_speed_mib_s": "currentSpeedMiBps",
            "peak_speed_mib_s": "peakSpeedMiBps",
            "dest_path": "destPath",
        }

        def normalise(event_type: str, payload: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
            mapped_type = rename.get(event_type, event_type)
            mapped_payload = {rename.get(k, k): v for k, v in payload.items()}
            return mapped_type, mapped_payload

        return normalise

    def get_event_queue_handle(self):
        """Get event queue handle for GIL-free event pump architecture"""
        return self._engine.get_event_queue_handle()

    def set_event_sink(self, sink: Callable[[str, Dict[str, Any]], None]) -> None:
        """DEPRECATED: Use get_event_queue_handle() + event pump instead (prevents GIL deadlock)"""
        def handle(event_type: str, payload: Dict[str, Any]) -> None:
            mapped_type, mapped_payload = self._normalise_event(event_type, payload)
            sink(mapped_type, mapped_payload)

        if HAS_QT and isinstance(sink, QtCore.QObject):  # type: ignore[truthy-function]
            self._qt_bridge = _QtEmitter(handle)
            self._engine.set_event_sink(self._qt_bridge.emit)
        else:
            self._qt_bridge = None
            self._engine.set_event_sink(handle)

    def copy_files(self, job: Any) -> Dict[str, Any]:
        result = self._engine.copy_files(job)
        return {
            "jobId": getattr(result, "job_id", ""),
            "startTime": getattr(result, "start_time", 0.0),
            "endTime": getattr(result, "end_time", 0.0),
            "totalFiles": getattr(result, "total_files", 0),
            "completedFiles": getattr(result, "copied_files", getattr(result, "completed_files", 0)),
            "totalBytes": getattr(result, "total_bytes", 0),
            "completedBytes": getattr(result, "copied_bytes", getattr(result, "completed_bytes", 0)),
            "avgSpeedMiBps": getattr(result, "speed_mib_s", getattr(result, "speed_mbps", 0.0)),
            "dataMiBps": getattr(result, "data_mib_s", getattr(result, "data_mbps", 0.0)),
            "dataElapsedS": getattr(result, "data_elapsed_s", 0.0),
            "errors": list(getattr(result, "errors", [])),
            "fileRecords": list(getattr(result, "files", getattr(result, "file_records", []))),
        }

    def cancel(self) -> None:
        self._engine.cancel()

    def pause(self) -> None:
        self._engine.pause()

    def resume(self) -> None:
        self._engine.resume()

    def is_cancelled(self) -> bool:
        return self._engine.is_cancelled()

    def is_paused(self) -> bool:
        return self._engine.is_paused()

    def get_enhanced_stats(self) -> Dict[str, Any]:
        stats = self._engine.get_enhanced_stats()
        mapping = {
            "bytes_copied": "bytesCopied",
            "total_bytes": "totalBytes",
            "files_completed": "completedFiles",
            "total_files": "totalFiles",
            "elapsed_s": "elapsedS",
            "speed_mib_s": "avgSpeedMiBps",
        }
        return {mapping.get(key, key): value for key, value in stats.items()}

    def get_progress(self) -> Dict[str, Any]:
        return self.get_enhanced_stats()

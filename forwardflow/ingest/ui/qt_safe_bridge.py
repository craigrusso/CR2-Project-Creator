from PyQt6 import QtCore


class QtEventBridge(QtCore.QObject):
    sigJobStarted     = QtCore.pyqtSignal(dict)
    sigJobProgress    = QtCore.pyqtSignal(dict)
    sigJobCompleted   = QtCore.pyqtSignal(dict)
    sigJobError       = QtCore.pyqtSignal(dict)
    sigJobCancelled   = QtCore.pyqtSignal(dict)
    sigFileStarted    = QtCore.pyqtSignal(dict)
    sigFileProgress   = QtCore.pyqtSignal(dict)
    sigFileCompleted  = QtCore.pyqtSignal(dict)
    sigDestProgress   = QtCore.pyqtSignal(dict)

    def __init__(self):
        super().__init__()


_bridge_instance = None


def get_bridge():
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = QtEventBridge()
    return _bridge_instance


def cleanup_bridge():
    """Clean up the bridge instance when the job is complete"""
    global _bridge_instance
    if _bridge_instance is not None:
        try:
            _bridge_instance.deleteLater()
        except:
            pass
        _bridge_instance = None


def emit_event(kind: str, payload: dict):
    try:
        b = get_bridge()
        if b is None:
            print(f"DEBUG: QtEventBridge is None, cannot emit {kind}")
            return
            
        if kind == "job.started":
            b.sigJobStarted.emit(payload)
        elif kind == "job.progress":
            b.sigJobProgress.emit(payload)
        elif kind == "job.completed":
            b.sigJobCompleted.emit(payload)
        elif kind == "job.error":
            b.sigJobError.emit(payload)
        elif kind == "job.cancelled":
            b.sigJobCancelled.emit(payload)
        elif kind == "file.started":
            b.sigFileStarted.emit(payload)
        elif kind == "file.progress":
            b.sigFileProgress.emit(payload)
        elif kind == "file.completed":
            b.sigFileCompleted.emit(payload)
        elif kind == "dest.progress":
            b.sigDestProgress.emit(payload)
        else:
            pass
    except Exception as e:
        # Log the error but don't crash
        print(f"DEBUG: QtEventBridge emit error for {kind}: {e}")
        # Don't cleanup on every error - only cleanup when job is actually complete
        pass



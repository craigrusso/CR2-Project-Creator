import os, sys, faulthandler, signal, traceback

def _excepthook(exc_type, exc, tb):
    print("=== UNCAUGHT PYTHON EXCEPTION ===", file=sys.stderr)
    traceback.print_exception(exc_type, exc, tb)
    sys.stderr.flush()

def enable():
    sys.excepthook = _excepthook
    try:
        faulthandler.enable(all_threads=True)
        faulthandler.register(signal.SIGUSR1, file=sys.stderr, all_threads=True)
    except Exception as e:
        print(f"[crash_first_aid] faulthandler enable failed: {e}")
    os.environ.setdefault("PYTHONTRACEMALLOC", "1")
    os.environ.setdefault("QT_LOGGING_RULES", "qt.qml.connections.warning=false")

# Enable on import
enable()



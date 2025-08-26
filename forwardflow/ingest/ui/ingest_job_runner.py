"""Job execution logic for the Ingest Tab"""

import threading
import time
from typing import Optional
from PyQt6.QtCore import QTimer

from ..api.models import JobSpec, JobOptions
from ..ui.qt_safe_bridge import emit_event


def run_job(job: JobSpec, root) -> None:
    """Run the job in a background thread with comprehensive debugging"""
    print(f"DEBUG: ===== RUN_JOB STARTED =====")
    print(f"DEBUG: Job ID: {job.job_id}")
    print(f"DEBUG: Thread ID: {threading.current_thread().ident}")
    
    try:
        # Use bridge emitter via engine wrapper
        print("DEBUG: Creating BridgeSink...")
        sink = type("BridgeSink", (), {"emit": lambda _self, kind, payload: emit_event(kind, payload)})()
        print("DEBUG: BridgeSink created")
        
        # Get the C++ engine instance
        print("DEBUG: Getting C++ engine instance...")
        try:
            from .engine_manager import get_engine
            engine = get_engine(sink=sink)
            print(f"DEBUG: C++ engine retrieved: {engine}")
        except Exception as e:
            print(f"DEBUG: Failed to get C++ engine: {e}")
            raise
        
        print("DEBUG: C++ engine is being used")
        
        # Store the engine reference
        root.current_job = engine
        print("DEBUG: Engine stored in root.current_job")
        
        print("DEBUG: Starting engine with job...")
        try:
            engine.copy_files(job)
            print("DEBUG: Engine completed successfully")
        except Exception as e:
            print(f"DEBUG: Engine failed: {e}")
            import traceback
            traceback.print_exc()
            raise
            
    except Exception as e:
        print(f"DEBUG: Error in run_job: {e}")
        import traceback
        traceback.print_exc()
        
        # Re-enable controls on error
        def reenable_controls():
            root.start_btn.setEnabled(True)
            root.src_combo.setEnabled(True)
            root.src_btn.setEnabled(True)
            root.dest_combo.setEnabled(True)
            root.verify_combo.setEnabled(True)
            root.preset_combo.setEnabled(True)
            print("DEBUG: Controls re-enabled after error")
        
        # Use QTimer to ensure this runs on the main thread
        QTimer.singleShot(0, reenable_controls)
        
    finally:
        print("DEBUG: ===== RUN_JOB COMPLETED =====")


def create_job_spec(source: str, destinations: list, verify_mode: str, preset: str, generate_report: bool) -> JobSpec:
    """Create a JobSpec from the UI inputs"""
    print("DEBUG: Importing JobSpec and JobOptions...")
    from ..api.models import JobSpec, JobOptions
    print("DEBUG: JobSpec and JobOptions imported successfully")
    
    print("DEBUG: Creating JobSpec...")
    
    # Determine concurrency based on preset
    if preset == "Fast":
        per_file_concurrency = 4
        stream_concurrency = 8
    elif preset == "Balanced":
        per_file_concurrency = 2
        stream_concurrency = 4
    elif preset == "Strict":
        per_file_concurrency = 1
        stream_concurrency = 2
    else:  # Auto
        per_file_concurrency = 2
        stream_concurrency = 4
    
    print(f"DEBUG: Per-file concurrency: {per_file_concurrency}")
    print(f"DEBUG: Stream concurrency: {stream_concurrency}")
    print(f"DEBUG: Generate report: {generate_report}")
    
    job_spec = JobSpec(
        job_id=f"ingest_{int(time.time())}",
        source_root=source,
        destination_roots=destinations,
        options=JobOptions(
            mode="BALANCED",
            per_file_concurrency=per_file_concurrency,
            stream_concurrency=stream_concurrency,
            verify_algorithm="xxh64",
            verify_mode=verify_mode,
            preset=preset,
            generate_verification_report=generate_report,
            cloud_source=False
        )
    )
    
    print(f"DEBUG: Created JobSpec: {job_spec}")
    return job_spec

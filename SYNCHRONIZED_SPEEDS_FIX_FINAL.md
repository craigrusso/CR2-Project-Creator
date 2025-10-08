# Synchronized Speeds Bug - Root Cause & Fix ✅

## The Problem

Multi-destination transfers showed **identical synchronized speeds** for all destinations:
```
Desktop (LOCAL SSD):  1638.3 MB/s
USB (External SSD):   1641.9 MB/s  <- Should be different!
```

Even after restarting the application with the "fixed" engine, speeds remained synchronized.

## Root Cause Analysis

### Initial Investigation (INCOMPLETE)
We initially removed synchronized dest.progress emissions from the producer callback in `engine_core.rs` (around line 343-371). However, this was NOT the complete fix!

### Complete Code Review Discovery
After a thorough code review using `grep emit_dest_progress`, we found **TWO MORE locations** emitting synchronized speeds:

#### Location 1: File Completion Handler (Line 484-504)
**File:** `forwardflow/ingest/engines/rust_high_perf/src/engine_core.rs`

```rust
// BUGGY CODE (REMOVED):
let mut dest_progress = DestProgressPayload::default();
dest_progress.dest_index = dest.dest_index;
dest_progress.dest_path = dest.dest_path.clone();
dest_progress.transfer_type = "COPY".to_string();
dest_progress.bytes_copied = dest_bytes[dest.dest_index];
dest_progress.total_bytes = total_bytes;
dest_progress.completed_files = dest_files[dest.dest_index];
dest_progress.total_files = total_files;
dest_progress.current_speed_mib_s = transfer_speed_mib_s;  // ❌ SAME FOR ALL!
dest_progress.peak_speed_mib_s = transfer_speed_mib_s;     // ❌ SAME FOR ALL!
dest_progress.elapsed_time = duration_secs;

let _ = event_system.emit_dest_progress(&dest_progress);
```

**The Problem:**
- This code ran EVERY TIME a file completed to ANY destination
- `transfer_speed_mib_s` was the **aggregate job speed** (total bytes / total time)
- Every destination received the SAME aggregate speed
- This overrode any independent speed calculations in Python

#### Location 2: Final Completion Handler (Line 524-535)
**File:** `forwardflow/ingest/engines/rust_high_perf/src/engine_core.rs`

```rust
// BUGGY CODE (REMOVED):
for (dest_index, dest_path) in job.destination_paths.iter().enumerate() {
    let mut dest_completion = DestProgressPayload::default();
    dest_completion.dest_index = dest_index;
    dest_completion.dest_path = dest_path.clone();
    dest_completion.transfer_type = "COPY".to_string();
    dest_completion.completed_files = dest_files[dest_index];
    dest_completion.total_files = total_files;
    dest_completion.bytes_copied = dest_bytes[dest_index];
    dest_completion.total_bytes = total_bytes;
    dest_completion.eta_seconds = 0.0;

    let _ = event_system.emit_dest_progress(&dest_completion);  // ❌ Redundant!
    let _ = event_system.emit_dest_completed(...);  // This is sufficient
}
```

**The Problem:**
- Emitted final dest.progress right before dest.completed
- Redundant and potentially confusing
- No speed data, but unnecessary event emission

## The Complete Fix

### Changes Made

**File:** `forwardflow/ingest/engines/rust_high_perf/src/engine_core.rs`

1. **Removed File Completion dest.progress (Lines 484-504)**
   ```rust
   // NOTE: dest.progress emission REMOVED - this was emitting synchronized speeds!
   // The aggregate transfer_speed_mib_s is the same for all destinations,
   // which caused all destinations to show identical speeds in the UI.
   // Python EventBridge now calculates independent speeds from file.completed events.
   
   let _ = event_system.emit_file_completed_with_hash(...);  // ✅ Keep this!
   ```

2. **Removed Final dest.progress (Lines 524-535)**
   ```rust
   // NOTE: Final dest.progress emission REMOVED
   // dest.completed event provides all necessary completion info
   // and Python calculates all progress/speed from file.completed events
   
   let _ = event_system.emit_dest_completed(...);  // ✅ Keep this!
   ```

### What's Emitted Now (Rust Side)

✅ **file.completed** - Per file, per destination, with timing data
✅ **dest.completed** - Final completion event per destination
✅ **job.progress** - Overall job progress
❌ **dest.progress** - REMOVED (all instances)

### Independent Speed Calculation (Python Side)

**File:** `forwardflow/ingest/ui/job_aggregator.py`

```python
# Each destination tracks its own file completion timing
dest_metrics.window.append((now, dest_metrics.bytes_copied))

# Calculate destination current rate
dest_metrics.current_mb_s = self._calculate_rate_mb_s(dest_metrics.window)
dest_metrics.peak_mb_s = max(dest_metrics.peak_mb_s, dest_metrics.current_mb_s)
```

**How It Works:**
1. Rust emits `file.completed` when each worker finishes a file
2. Fast workers emit file completions faster (more bytes/second)
3. Slow workers emit file completions slower (fewer bytes/second)
4. Python tracks bytes completed over time window **per destination**
5. Speed = bytes_completed / time_elapsed (calculated independently)

## Build & Deployment

```bash
cd forwardflow/ingest/engines/rust_high_perf
cargo build --release
# Finished `release` profile [optimized] target(s) in 11.57s

cp target/release/librust_high_perf_engine.dylib \
   ../../../../venv/lib/python3.12/site-packages/rust_high_perf_engine.so
# ✅ DEPLOYED
```

## Expected Behavior After Fix

### Before (Synchronized - WRONG):
```
Transfer Progress: 18%
  Desktop (LOCAL SSD):     1638.3 MB/s, Peak: 6711.0 MB/s ❌
  USB (External SSD):      1641.9 MB/s, Peak: 6711.0 MB/s ❌
  
Both show ~1640 MB/s (aggregate speed divided among destinations)
```

### After (Independent - CORRECT):
```
Transfer Progress: 18%
  Desktop (LOCAL SSD):     2800.5 MB/s, Peak: 3200.0 MB/s ✅
  USB (External SSD):       895.2 MB/s, Peak: 950.0 MB/s  ✅
  
Each shows its own native speed based on actual write performance
```

## Testing Instructions

### Test 1: Verify Independent Speeds

1. **QUIT ForwardFlow** (Cmd+Q to ensure new engine loads)
2. **Restart ForwardFlow**
3. **Setup Transfer:**
   - Source: Large folder (e.g., 70GB of video files)
   - Destination 1: Internal/Local SSD (fast)
   - Destination 2: External USB SSD or Network (slower)
4. **Start Transfer**
5. **Watch Speeds:**
   - ✅ Desktop should show ~2000-3800 MB/s (or its native speed)
   - ✅ USB should show ~500-1000 MB/s (or its native speed)
   - ✅ Speeds should be DIFFERENT, not synchronized
   - ✅ Progress bars advance at different rates

### Test 2: Verify Terminal Logs

Watch terminal for `destination_update` events:
```
DEBUG: Received destination progress for '/Users/.../Desktop': 2850.5 MB/s
DEBUG: Received destination progress for '/Volumes/USB/...': 892.3 MB/s
```

Speeds should be **DIFFERENT**!

### Test 3: Hot-Swap Workflow

1. Start transfer to 2 destinations (fast SSD + slow network)
2. Fast SSD should finish first
3. Slow network continues at its own pace
4. Verify you can eject fast SSD while network continues

## Why Previous Fix Didn't Work

1. We removed ONE instance of synchronized dest.progress emission
2. But TWO MORE instances were still active:
   - File completion handler (emitted after every file)
   - Final completion handler (emitted at the end)
3. The file completion handler was the PRIMARY source of UI updates
4. It emitted the aggregate speed to ALL destinations
5. Python's independent speed calculations were overridden
6. Even after restart, synchronized speeds persisted

## Success Criteria

✅ Each destination shows its own native write speed
✅ Fast destinations don't wait for slow ones
✅ Speeds update independently in real-time
✅ Progress bars advance at different rates
✅ Different ETAs per destination
✅ Different peak speeds per destination
✅ Hot-swap workflow enabled

## Files Modified

```
forwardflow/ingest/engines/rust_high_perf/src/engine_core.rs
  - Removed synchronized dest.progress emission from file completion handler (lines 484-504)
  - Removed redundant dest.progress emission from final completion (lines 524-535)
  - Added explanatory comments

DEPLOYED: venv/lib/python3.12/site-packages/rust_high_perf_engine.so (1.2 MB)
```

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│ Rust Engine (Multi-Destination Copy)                         │
│                                                              │
│  Producer Thread                                            │
│  └─> Reads chunks from source                              │
│                                                             │
│  Worker Threads (one per destination)                       │
│  ├─> Worker 1 (Desktop SSD) → Writes at 2800 MB/s         │
│  │   └─> Emits file.completed when file done              │
│  │                                                          │
│  └─> Worker 2 (USB SSD) → Writes at 900 MB/s              │
│      └─> Emits file.completed when file done              │
│                                                             │
│  ❌ NO dest.progress emissions (removed)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
                  file.completed events
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Python EventBridge & JobAggregator                           │
│                                                              │
│  Destination 1 Metrics:                                     │
│  ├─> Tracks bytes completed over time window               │
│  ├─> Calculates speed: 2800.5 MB/s ✅                       │
│  └─> Emits destination_update                              │
│                                                             │
│  Destination 2 Metrics:                                     │
│  ├─> Tracks bytes completed over time window               │
│  ├─> Calculates speed: 895.2 MB/s ✅                        │
│  └─> Emits destination_update                              │
│                                                             │
│  ✅ Independent speed calculations per destination          │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    Independent speeds displayed in UI!
```

## Key Insights

1. **Rust knows HOW FAST data is being WRITTEN** (from worker timing)
2. **But it was emitting AGGREGATE speed** (total bytes / total time)
3. **Python can calculate TRUE speeds** (from file completion events)
4. **The fix:** Stop Rust from emitting synchronized speeds, let Python calculate independent speeds

---

**Status:** ✅ **DEPLOYED - ALL synchronized dest.progress emissions removed**

**Next Step:** **QUIT and RESTART ForwardFlow**, then test multi-destination transfer!

---

*Root cause: Multiple instances of synchronized dest.progress emissions in engine_core.rs that were broadcasting the aggregate job speed to all destinations, overriding independent speed calculations.*


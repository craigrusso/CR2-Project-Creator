# ETA and Peak Speed Fixes

## Issues Fixed

### 1. ETA Not Working in Destination Widgets
**Problem**: The ETA (Estimated Time to Arrival) was showing as "00:0" (truncated) instead of the proper "00:00:14" format on destination cards during transfers.

**Root Causes**: 
1. **Backend Issue (FIXED)**: 
   - The `DestProgressPayload` struct had the `eta_seconds` field BUT the `TransferEvent::DestProgress` enum variant didn't have it
   - The `emit_dest_progress()` method wasn't passing the `eta_seconds` value when creating the event  
   - This caused the calculated ETA to be lost during event serialization to JSON before being sent to Python
   - UI was receiving destination progress events without any ETA data

2. **UI Issue (FIXED)**:
   - The destination card's ETA label had `setMinimumWidth(80)` pixels
   - The text "ETA: 00:00:14" in a 12px monospace font requires ~112-120 pixels
   - This caused the label text to be truncated to "00:0" instead of displaying the full time

**Fix**:
1. Added `eta_seconds` field to `DestProgressPayload` struct in `data_structures.rs`
2. Added `eta_seconds` field to `TransferEvent::DestProgress` enum variant in `event_queue.rs`
3. Updated `emit_dest_progress()` in `event_system.rs` to pass `eta_seconds: payload.eta_seconds`
4. Added ETA calculation in `engine_core.rs` at all three emission points:
   ```rust
   // Calculate ETA: remaining_bytes / speed
   if speed_mib_s > 0.0 && dest_progress.bytes_copied < dest_progress.total_bytes {
       let remaining_bytes = dest_progress.total_bytes - dest_progress.bytes_copied;
       dest_progress.eta_seconds = (remaining_bytes as f64) / (speed_mib_s * 1024.0 * 1024.0);
   } else {
       dest_progress.eta_seconds = 0.0;
   }
   ```
5. Updated `progress_tracking.rs` to include the new field when creating payloads
6. **UI Fix** (`source_destination.py`):
   - Increased ETA label minimum width from 80px to 125px to accommodate full "ETA: 00:00:00" text in monospace font
   - This prevents text truncation and ensures proper display of the ETA value

### 2. Peak Speed Always 0.0 in DIT Reports
**Problem**: The peak speed in DIT reports always showed 0.0 MB/s instead of the actual peak transfer speed.

**Root Cause**:
- In `engine_core.rs`, `peak_speed_mib_s` was being set to the same value as `current_speed_mib_s` on every update (line 352), not tracking the actual peak
- The DIT collector's `peak_speed` value was never being properly updated from the progress events
- Peak speed from destination progress events wasn't being captured and forwarded to the DIT collector

**Fix**:
1. **Rust Engine** (`engine_core.rs`):
   - Added `dest_peak_speeds` vector to track peak speed per destination
   - Updated destination progress emission to properly track and update peak speed:
   ```rust
   // Track peak speed per destination
   if speed_mib_s > dest_peak_speeds[dest_idx] {
       dest_peak_speeds[dest_idx] = speed_mib_s;
   }
   dest_progress.peak_speed_mib_s = dest_peak_speeds[dest_idx];
   ```

2. **Event Pump** (`event_pump.py`):
   - Added `_peak_speed_mbps` instance variable to track global peak speed
   - Updated `_handle_job_progress()` to track and update peak speed:
   ```python
   if current_speed > self._peak_speed_mbps:
       self._peak_speed_mbps = current_speed
       dit_collector.update_job_stats({'peak_speed': self._peak_speed_mbps})
   ```
   - Updated `_handle_dest_progress()` to track peak speed from destination progress events:
   ```python
   dest_peak_speed = payload.get('peak_speed_mib_s', 0) or payload.get('peak_speed_mbps', 0)
   if dest_peak_speed > self._peak_speed_mbps:
       self._peak_speed_mbps = dest_peak_speed
       dit_collector.update_job_stats({'peak_speed': self._peak_speed_mbps})
   ```
   - Added reset of `_peak_speed_mbps` when starting a new job to ensure clean tracking

## Files Modified

### Rust Files
1. **forwardflow/ingest/engines/rust_high_perf/src/data_structures.rs**
   - Added `eta_seconds: f64` field to `DestProgressPayload` struct
   - Updated `Default` implementation to include `eta_seconds: 0.0`

2. **forwardflow/ingest/engines/rust_high_perf/src/event_queue.rs**
   - Added `eta_seconds: f64` field to `TransferEvent::DestProgress` enum variant
   - This ensures ETA is included in the JSON serialized event sent to Python

3. **forwardflow/ingest/engines/rust_high_perf/src/event_system.rs**
   - Updated `emit_dest_progress()` to pass `eta_seconds: payload.eta_seconds` when creating the event
   - This ensures the calculated ETA is not lost during event creation

4. **forwardflow/ingest/engines/rust_high_perf/src/engine_core.rs**
   - Added `dest_peak_speeds` vector to track peak speed per destination
   - Added ETA calculation logic at THREE emission points:
     - During chunk progress updates (line ~365)
     - During file completion updates (line ~512-518)  
     - During destination completion updates (line ~566)
   - Fixed peak speed tracking to properly monitor and update peak values

5. **forwardflow/ingest/engines/rust_high_perf/src/progress_tracking.rs**
   - Added `eta_seconds: 0.0` field when creating `DestProgressPayload` instances

### Python Files
6. **forwardflow/ingest/ui/event_pump.py**
   - Added `_peak_speed_mbps` instance variable to track global peak speed
   - Updated `_handle_job_progress()` to track and forward peak speed to DIT collector
   - Updated `_handle_dest_progress()` to capture peak speed from destination events
   - Added peak speed reset when starting new job in `start_pump()`

7. **forwardflow/ingest/ui/components/source_destination.py**
   - Increased ETA label minimum width from 80px to 125px (line 248)
   - This fix prevents text truncation in destination cards
   - The wider label properly displays "ETA: 00:00:00" format in monospace font

## Build Steps Completed
1. Rebuilt Rust engine with `cargo build --release`
2. Copied compiled library to Python module location: `rust_high_perf_engine.so`

## Testing Required
- Run a transfer with multiple destinations
- Verify ETA shows correctly with full "HH:MM:SS" format (not truncated to "00:0")
- Verify ETA updates accurately during transfer
- Verify peak speed is captured correctly in DIT reports (should show actual peak, not 0.0)
- Check that peak speed is properly reset between different transfer jobs

## Expected Behavior
1. **ETA on Destination Cards**: Should show accurate time remaining in full "ETA: HH:MM:SS" format (e.g., "ETA: 00:01:14"), updating as transfer progresses
2. **ETA on Main Progress**: Should show accurate time remaining for overall job
3. **Peak Speed**: DIT reports should show the actual maximum transfer speed achieved during the transfer (e.g., 4223.0 MB/s instead of 0.0 MB/s)

## Notes
- The fixes ensure that both metrics are properly calculated in Rust and correctly propagated through the event system to the UI and DIT reports
- Peak speed tracking now happens at multiple levels (Rust per-destination, Python event pump global) to ensure accuracy
- ETA calculation uses the formula: `remaining_bytes / current_speed_mbps`
- The UI truncation issue was discovered through systematic debugging:
  - Debug logs confirmed ETA data was flowing correctly from Rust → Python → UI
  - The value was being set correctly (`setText("ETA: 00:00:14")`)
  - The issue was that the QLabel width constraint (80px) was too narrow for the monospace font
  - Monospace fonts at 12px require ~7-8 pixels per character, so 14 characters needs ~112-120 pixels
- Both fixes are backwards compatible with existing code


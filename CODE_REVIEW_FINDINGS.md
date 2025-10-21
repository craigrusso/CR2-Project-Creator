# Code Review: Multi-Destination Transfer Issues

## Executive Summary
Found 5 critical bugs causing premature 100% progress, missing real-time reports, and race conditions.

## Issues Found

### 1. **CRITICAL: Overall Progress Shows 100% When First Destination Finishes**
**Location:** `forwardflow/ingest/ui/event_pump.py` lines 248-251
**Problem:**
```python
progress_percent = (self._engine_progress_bytes / self._engine_total_target_bytes) * 100.0
```
- This calculates progress as `copied_bytes / total_target_bytes`
- But `total_target_bytes` is the SUM across ALL destinations
- When dest 0 finishes, it's copied 50% of total bytes, so progress shows 50-100% even though dest 1 is still copying
- The UI should aggregate ACTUAL destination progress, not engine producer progress

**Fix:** Use JobAggregator's per-destination progress to calculate aggregate job progress

---

### 2. **CRITICAL: Race Condition - Job Cleanup Before Last Event Processed**
**Location:** `forwardflow/ingest/ui/components/controls.py` line 1099-1110
**Problem:**
```
Line 341: ✅ All workers finished - transfer complete
Line 401: UI reset to Ready state  
Line 413: 🚨 FileCompleted event for MVI_0555.MOV arrives AFTER cleanup
Line 457: Real-time writer = None (already destroyed)
```
- Engine declares completion when result collector thread finishes
- Job cleanup happens immediately
- Event queue still has pending file completion events
- These events arrive AFTER the realtime writer and DIT collector are destroyed

**Fix:** Wait for event pump to be idle for at least 500ms before starting cleanup

---

### 3. **Per-Destination DIT Reports Not Generated During Transfer**  
**Location:** `forwardflow/ingest/ui/event_pump.py` lines 577-584
**Problem:**
- `_handle_dest_completed()` emits destination_completed signal
- But `DestCompleted` events from Rust engine may not be firing
- Or they're being emitted but the handler in controls.py requires an active job_id

**Fix:** 
1. Ensure Rust engine emits `DestCompleted` events when a destination finishes all files
2. Modify `_handle_destination_completed()` to work even during cleanup phase

---

### 4. **Real-Time Report Writer Not Recording Files**
**Location:** Logs show `⚠️ No report path found for destination`
**Problem:**
- Real-time writer is properly initialized with dest_index_map
- But later in the transfer, writer becomes None (see issue #2)
- When events arrive after cleanup, writer is already destroyed

**Root Cause:** Same as issue #2 - race condition

---

### 5. **Completion Detection Doesn't Wait for ALL Destinations**
**Location:** Rust engine's completion logic
**Problem:**
- Engine uses a result collector thread that waits for all worker threads
- But this only waits for file WRITES to complete
- Doesn't wait for:
  - All file completion events to be queued
  - Event pump to drain all events
  - Per-destination stats to be finalized

**Fix:** Add proper synchronization barriers

---

## Implementation Plan

### Phase 1: Fix Overall Progress Calculation
- Modify `event_pump.py._apply_destination_progress_override()` to calculate TRUE aggregate progress
- Ensure progress bar never shows 100% until ALL destinations reach 100%

### Phase 2: Fix Race Condition
- Add event pump idle wait (500ms minimum) before cleanup
- Move realtime writer finalization to AFTER all events processed
- Keep DIT collector alive until event pump confirms idle

### Phase 3: Fix Per-Destination Reporting
- Ensure Rust engine emits DestCompleted events
- Modify destination completion handler to not require active job_id during final phase
- Generate per-destination reports as each destination completes

### Phase 4: Add Completion Barriers
- Wait for event pump idle before declaring job complete
- Add debug logging to track event queue depth
- Ensure all destinations emit completion events

---

## Test Plan
1. Test with 2 destinations of different speeds
2. Verify overall progress stays below 100% until BOTH destinations complete
3. Verify real-time reports are written during transfer
4. Verify per-destination DIT reports generate as each destination completes
5. Verify no race conditions or "writer = None" errors in logs


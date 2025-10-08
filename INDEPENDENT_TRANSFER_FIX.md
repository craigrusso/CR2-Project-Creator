# Independent Multi-Destination Transfer - Implementation Plan

## User Requirements (CONFIRMED)

1. **Master Reader**: 
   - Reads each file ONCE
   - Sends chunks to ALL destination queues
   - Moves to next file immediately (doesn't wait for destinations)
   - Pauses if slowest destination is 10-15 files behind

2. **Destination Workers**:
   - Each has its own queue
   - Processes files at its own speed
   - Fast SSD gets ahead, slow USB falls behind (but has queued files)
   - Independent completion

3. **Progress Reporting**:
   - Each destination reports when IT completes a file
   - Speed calculated from actual completion timestamps
   - Independent speeds in UI

## Current Bug

**File:** `forwardflow/ingest/engines/rust_high_perf/src/multi_dest/engine.rs`
**Lines:** 176-190

```rust
// ❌ BUG: Blocks until ALL destinations finish current file
for _ in 0..dest_count {
    if let Ok(result) = result_rx.recv() {
        destination_results.push(result);
    }
}
```

**Effect:**
- Reader sends File 1 to all destinations
- **WAITS** for both to finish File 1
- Only then reads File 2
- Result: Serial transfer, destinations locked in lockstep
- Evidence: Both destinations completed same 54 files (DIT reports)

## Implementation Plan

### 1. Remove Blocking Result Collection
**Current:**
```rust
// Wait for ALL destinations (SERIAL)
for _ in 0..dest_count {
    result_rx.recv()  // BLOCKS!
}
```

**New:**
```rust
// Don't wait - track pending files per destination
let mut pending_files = vec![0usize; dest_count];
pending_files[dest_idx] += 1;  // Increment when file sent

// Check if any destination is too far behind
let max_pending = pending_files.iter().max().unwrap_or(&0);
let min_pending = pending_files.iter().min().unwrap_or(&0);

if max_pending - min_pending > 15 {
    // Pause and wait for slow destination to catch up
    while /* slow dest catching up */ {
        // Process completion events
    }
}
```

### 2. Async File Completion Tracking
- Spawn background thread to collect results
- Track which files each destination has completed
- Decrement pending count on completion
- Emit file.completed events immediately

### 3. File-Depth Backpressure (Not Memory)
**Old:** Memory-based backpressure (bytes in queue)
**New:** File-depth backpressure (number of files behind)

```rust
const MAX_FILE_GAP: usize = 15;  // Max files a destination can fall behind

// After sending file to all destinations:
if slowest_dest_pending - fastest_dest_pending > MAX_FILE_GAP {
    // Pause reader, let slow destination catch up
    eprintln!("⏸  Pausing reader: Destination #{} is {} files behind", 
              slowest_idx, gap);
}
```

### 4. Fix Progress Reporting
Workers already emit file.completed when they finish - but the serial architecture was overriding this.

**Keep:**
- Workers emit file.completed with actual duration_ms
- Python calculates speed from completion timestamps
- Independent speeds

**Remove:**
- Blocking result collection
- Synchronized file processing

## Benefits

✅ **True Independent Speeds**
- Fast SSD: Writes File 1-20 while slow USB writes File 1-5
- Each reports at own speed
- No throttling

✅ **Memory Efficient**
- Only 10-15 files in flight max
- Much less memory than unlimited queue
- Smart backpressure

✅ **Correct Progress**
- UI shows actual per-destination progress
- Different speeds, different completion states
- Real-time updates

✅ **Hot-Swap Compatible**
- Fast destination can complete and be ejected
- Slow destination continues independently

## Next Steps

1. Modify `engine.rs` to remove blocking result collection
2. Implement file-depth based backpressure
3. Rebuild and deploy
4. Test with fast + slow destinations
5. Verify independent speeds in UI


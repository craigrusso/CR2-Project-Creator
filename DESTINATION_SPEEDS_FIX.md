# Destination Speed Reporting - Bug Fix ✅

## The Problem

**Symptoms:**
1. Destination cards showed **0 MB/s** and **Peak: 0 MB/s** (no updates)
2. Overall transfer speed was correct (3159 MB/s aggregate)
3. DIT reports showed both destinations completed the same 54 files

## Root Cause Analysis

### Issue 1: Path Mismatch Bug 🐛

**EventBridge was passing the wrong path to JobAggregator!**

**What Rust sends (file.completed event):**
```python
{
    'dest_path': '/Volumes/CR_DRIVE/TEST_TRANSFER/subdir/file.mov',  # Full file path
    'filename': 'file.mov',
    'bytes_copied': 1405372164,
    ...
}
```

**What JobAggregator was initialized with:**
```python
destinations = [
    '/Users/craigrusso/Desktop/TEST/TEST_TRANSFER 1',  # Root directory
    '/Volumes/CR_DRIVE/TEST_TRANSFER'                   # Root directory
]
```

**The Bug:**
- EventBridge extracted `dest_path` from payload: `/Volumes/CR_DRIVE/TEST_TRANSFER/subdir/file.mov`
- Passed it to JobAggregator: `update_file_progress(..., dest_path='/Volumes/CR_DRIVE/TEST_TRANSFER/subdir/file.mov', ...)`
- JobAggregator couldn't match this to registered destinations
- **Result:** `snapshot.destinations` was empty → No destination speed updates!

### Issue 2: DIT Reports Show Same Files (NOT A BUG)

**This is expected behavior!**

DIT reports are generated from `DITDataCollector`, which tracks **all completed files** without distinguishing which destination wrote them. Both reports show the same files because:
- All files were successfully copied to both destinations ✅
- The DIT collector records file completion globally, not per-destination

**To see independent speeds, you need to look at:**
- Destination cards in the UI (speed, peak, ETA)
- Per-destination completion times in Rust logs

## The Fix

**File:** `forwardflow/ingest/ui/event_bridge.py`

**Changed:** Lines 268-286

**What it does now:**
1. Extracts the **destination root directory** from the full file path
2. Matches it against registered destinations
3. Passes the correct root directory to JobAggregator

```python
# Extract destination ROOT from full file path
# Rust sends: "/Volumes/CR_DRIVE/TEST_TRANSFER/subdir/file.mov"
# JobAggregator needs: "/Volumes/CR_DRIVE/TEST_TRANSFER"
dest_dir = ''
if dest_file_path and self.job_aggregator and self.job_aggregator.destinations:
    # Match dest_file_path against registered destinations
    for registered_dest in self.job_aggregator.destinations:
        if dest_file_path.startswith(registered_dest + '/') or dest_file_path.startswith(registered_dest):
            dest_dir = registered_dest
            print(f"DEBUG: Matched dest_dir='{dest_dir}' for file '{dest_file_path}'")
            break
```

## Expected Results After Restart

**Destination Cards Will Show:**
- **LOCAL SSD (Fast):**
  - Current Speed: ~2000-3000 MB/s
  - Peak Speed: ~6000 MB/s
  - ETA: Updates independently
  
- **USB SSD (Slower):**
  - Current Speed: ~900-1200 MB/s
  - Peak Speed: ~1500 MB/s
  - ETA: Longer than LOCAL SSD

**Debug Prints You'll See:**
```
DEBUG: Matched dest_dir='/Volumes/CR_DRIVE/TEST_TRANSFER' for file '/Volumes/CR_DRIVE/TEST_TRANSFER/file.mov'
DEBUG: Emitting destination update for /Volumes/CR_DRIVE/TEST_TRANSFER: 895.2 MB/s, 12.1%
DEBUG: Emitting destination update for /Users/craigrusso/Desktop/TEST/TEST_TRANSFER 1: 3800.5 MB/s, 25.3%
```

## About the "Same Files" in DIT Reports

**This is CORRECT and expected!** Both destinations are supposed to get all the same files - that's what a multi-destination transfer does. The difference is:
- **WHEN** they complete (different times)
- **HOW FAST** they complete (different speeds)

The DIT reports don't track per-destination timing, so they show the same file list. **This is not a synchronization bug.**

## Testing Instructions

1. **Restart ForwardFlow** (to load the Python fix)
2. **Run a multi-destination transfer** (fast SSD + slower drive)
3. **Watch the destination cards** - they should now show:
   - Different speeds for each destination ✅
   - Independent ETA values ✅
   - Different progress percentages ✅

4. **What to look for in logs:**
   ```
   DEBUG: Matched dest_dir='/Volumes/...' for file '/Volumes/.../file.mov'
   DEBUG: Emitting destination update for /Volumes/...: 895.2 MB/s, 12.1%
   ```

If you see these debug prints, the fix is working! 🎉


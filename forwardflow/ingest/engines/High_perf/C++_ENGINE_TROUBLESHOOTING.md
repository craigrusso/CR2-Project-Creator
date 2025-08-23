# C++ Engine Troubleshooting Guide

## 🚨 CRITICAL: This Document Must Be Read Before Any C++ Engine Changes

**Last Updated**: August 23, 2025  
**Status**: WORKING - DO NOT BREAK  
**Engine Type**: EnhancedHighPerfTransferEngine (C++ Core)

---

## 🎯 Why This C++ Engine Works

### 1. **Complete Source Compilation**
The C++ engine works because `setup.py` now compiles **ALL** required source files:

```python
ext_modules = [
    Pybind11Extension(
        "enhanced_high_perf_engine",
        [
            "enhanced_engine_main.cpp",        # PyBind11 binding layer
            "core/engine_core.cpp",            # MAIN ENGINE IMPLEMENTATION
            "core/data_structures.cpp",        # Data structures
            "io/cross_platform_io.cpp",        # I/O operations
            "platform/platform_helpers.cpp",   # Platform-specific code
            "stall/stall_watchdog.cpp",        # Stall detection
            "verification/verification_record.cpp", # Verification
            "cloud/cloud_detection.cpp",       # Cloud detection
            "cloud/cloud_materialization.cpp"  # Cloud operations
        ],
        cxx_std=17,
        extra_compile_args=["-O3", "-Wall", "-Wextra"],
    ),
]
```

### 2. **Proper Symbol Linking**
- **Before**: Only `enhanced_engine_main.cpp` was compiled → Missing `copy_files` symbol
- **After**: All source files compiled → `copy_files` symbol properly linked
- **Result**: C++ engine can be imported without symbol errors

### 3. **Real-time Progress Working**
- C++ engine emits events with correct `total_bytes` values
- UI receives proper progress updates
- File copying shows real-time numbers

---

## 🚨 Common Failure Modes

### 1. **Symbol Not Found Error**
```
ImportError: dlopen(...): symbol not found in flat namespace '__ZN10EngineCore30EnhancedHighPerfTransferEngine10copy_filesERKN14DataStructures7CopyJobE'
```

**Cause**: Missing C++ source files in `setup.py`  
**Solution**: Ensure ALL source files are listed in the PyBind11Extension

### 2. **C++ Engine Import Fails**
```
RuntimeError: C++ engine import failed: dlopen(...)
```

**Cause**: Incomplete compilation or linking  
**Solution**: Clean rebuild with all source files included

### 3. **Real-time Numbers Not Showing**
**Cause**: C++ engine emitting events with `total_bytes: 0`  
**Solution**: Ensure C++ code uses `stats_.total_bytes` not hardcoded `0`

---

## 🔧 Build Process (DO NOT DEVIATE)

### 1. **Clean Build Command**
```bash
cd forwardflow/ingest/engines/High_perf
rm -rf build/ __pycache__/ *.so
export MACOSX_DEPLOYMENT_TARGET=26.0
python3 setup.py build_ext --inplace
```

### 2. **Required Environment Variables**
```bash
export MACOSX_DEPLOYMENT_TARGET=26.0  # For macOS 2026 TAHOE compatibility
```

### 3. **Verification Steps**
```bash
# Test C++ engine import
python3 -c "import sys; sys.path.insert(0, 'forwardflow/ingest/engines/High_perf'); import enhanced_high_perf_engine; print('C++ engine imported successfully')"

# Check symbol table
nm -D enhanced_high_perf_engine.cpython-312-darwin.so | grep copy_files
```

---

## 📁 Critical Files (NEVER DELETE)

### 1. **Core Engine Files**
- `core/engine_core.cpp` - Main engine implementation
- `core/engine_core.hpp` - Engine header
- `core/data_structures.cpp` - Data structures
- `core/data_structures.hpp` - Data structures header

### 2. **Supporting Files**
- `io/cross_platform_io.cpp` - I/O operations
- `platform/platform_helpers.cpp` - Platform code
- `stall/stall_watchdog.cpp` - Stall detection
- `verification/verification_record.cpp` - Verification
- `cloud/cloud_detection.cpp` - Cloud detection
- `cloud/cloud_materialization.cpp` - Cloud operations

### 3. **Binding Files**
- `enhanced_engine_main.cpp` - PyBind11 bindings
- `setup.py` - Build configuration

---

## 🚫 What NOT To Do

### 1. **Never Remove Source Files from setup.py**
- Removing any source file will break symbol linking
- The engine will fail to import
- File copying will stop working

### 2. **Never Skip Clean Build**
- Always run `rm -rf build/ __pycache__/ *.so` before rebuilding
- Partial builds can cause symbol mismatches

### 3. **Never Change C++ Method Signatures**
- Changing method signatures breaks PyBind11 bindings
- The Python side won't be able to call C++ methods

### 4. **Never Use Python Fallback**
- User rule: "NEVER build a python fallback"
- C++ engine must be the primary and only engine
- Python fallback is counterproductive

---

## 🔍 Troubleshooting Checklist

### When C++ Engine Breaks:

1. **Check setup.py**
   - Are all source files included?
   - Are file paths correct?

2. **Check Symbol Table**
   ```bash
   nm -D enhanced_high_perf_engine.cpython-312-darwin.so | grep copy_files
   ```
   - Should show `copy_files` symbol

3. **Check Import**
   ```bash
   python3 -c "import enhanced_high_perf_engine"
   ```
   - Should import without errors

4. **Check Build Output**
   - Are all source files being compiled?
   - Are there any linking errors?

5. **Clean Rebuild**
   ```bash
   rm -rf build/ __pycache__/ *.so
   export MACOSX_DEPLOYMENT_TARGET=26.0
   python3 setup.py build_ext --inplace
   ```

---

## 📝 Change Log

### August 23, 2025 - CRITICAL FIX
- **Issue**: C++ engine not working, real-time numbers missing
- **Root Cause**: setup.py missing source files
- **Solution**: Added all C++ source files to setup.py
- **Result**: C++ engine working, real-time progress restored

---

## 🎯 Success Indicators

✅ **C++ engine imports without errors**  
✅ **Real-time progress numbers display**  
✅ **File copying works with progress updates**  
✅ **All symbols properly linked**  
✅ **No Python fallback needed**  

---

## 🚨 Emergency Contact

If the C++ engine breaks again:
1. **DO NOT** create Python fallback
2. **DO NOT** modify working code without understanding
3. **DO** check this troubleshooting guide first
4. **DO** verify setup.py includes all source files
5. **DO** clean rebuild with all source files

**Remember**: The C++ engine is the PRIMARY engine and must work for all ingest operations.

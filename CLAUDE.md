# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ForwardFlow (also known as Echelon) is a macOS file transfer and data ingestion application built with PyQt6. The project has undergone significant architectural evolution, transitioning from a C++ high-performance engine to a Rust-based engine for file operations.

## Core Architecture

### Application Structure
- **Main Entry**: `main.py` - Application bootstrap with PyInstaller compatibility and ARM64 support
- **App Module**: `app/` - Core application framework and utilities
- **ForwardFlow Module**: `forwardflow/ingest/` - Primary business logic for file transfer operations

### Engine Architecture
The application uses a **Rust-based high-performance engine** as the primary file transfer engine:
- **Rust Engine**: `forwardflow/ingest/engines/rust_high_perf/` - Primary file transfer engine
- **Engine Manager**: `forwardflow/ingest/ui/engine_manager.py` - Handles engine selection and lifecycle
- **Event System**: `forwardflow/ingest/ui/rust_event_sink.py` - Bridges Rust engine events to Python UI

### UI Framework
- **PyQt6-based**: All UI components use PyQt6
- **Main UI**: `forwardflow/ingest/ui/ingest_tab.py` - Primary ingest interface
- **Components**: `forwardflow/ingest/ui/components/` - Reusable UI components
- **View Models**: `forwardflow/ingest/ui/ingest_vm.py` - MVVM pattern implementation

## Development Commands

### Running the Application
```bash
# Development run
python main.py

# ARM64 specific run
python run_app_arm64.py
```

### Building for macOS
```bash
# Full build and notarization pipeline
./build_and_notarize_macos.sh

# PyInstaller build using spec file
pyinstaller --clean --noconfirm ForwardFlow.spec
```

### Testing
```bash
# Run tests
pytest

# Test specific engine components
python test_engine_manager.py
python test_enhanced_engine.py
```

### Rust Engine Development
```bash
cd forwardflow/ingest/engines/rust_high_perf
cargo build --release
```

## Key Implementation Patterns

### Engine Integration
- Rust engine is loaded as a dynamic library (`rust_high_perf_engine.dylib`)
- Engine wrapper provides Python interface: `RustHighPerfEngineWrapper`
- Event sink pattern for real-time progress updates
- Fallback mechanisms removed - Rust engine is mandatory

### Resource Management
- `app/constants.py` provides `get_resource_path()` for PyInstaller compatibility
- ARM64-specific resource loading handled automatically
- UI resources (icons, CSS) bundled via PyInstaller spec files

### Report Generation
- Transfer logs: `forwardflow/ingest/utils/transfer_log_writer.py`
- DIT-compliant reports: `forwardflow/ingest/utils/report_generator.py`
- Verification reports: `forwardflow/ingest/pipeline/verification_report.py`

## Coding Standards

### Pre-Development Process
- **Always Scan First**: Before writing anything, scan the entire codebase for existing files, modules, classes, or methods that may already do what you need
- **Check for Existing APIs**: Never assume API endpoints - always check for existing ones first
- **Plan Architecture**: Think out the complete workflow - modules and files should be organized in logical folders/subfolders

### Code Quality Standards
- **Senior Developer Approach**: Treat each task with high professionalism and expertise
- **Mandatory Code Review**: After writing or altering anything, review with fresh eyes for bugs, mistakes, logic errors, and duplicate code
- **File Size Limits**: Strictly keep files under 300 lines of code - refactor when approaching this limit
- **Future-Proof Design**: Code must be robust and non-brittle, prepared for future features and systems
- **No Code Duplication**: Always scan codebase to ensure similar functionality doesn't already exist

### Data and Testing Standards
- **No Mock/Temp Data**: Never use mock or temp data - use 0's or explicit placeholders like "temp" when calculations aren't built yet
- **Real Data Only**: Mock data doesn't help - build real functionality or clearly mark incomplete areas

### Refactoring Guidelines
- **UI Preservation**: Refactored code must NEVER change the UI - it must look identical when complete
- **File Name Stability**: When refactoring, keep original file names since other modules may link to them
- **Backup Strategy**: Don't create new file names - rename current files to backup (v1, v2, etc.) and maintain original filename
- **Import Strategy**: Original file should import from new refactored files to maintain compatibility

### Engine/Language Commitment Rules
- **C++/Rust Commitment**: If building C++/Rust modules, you must make the native code work - absolutely never create Python fallback modules
- **Language Consistency**: Everything about C++ also applies to Rust - stay in the chosen language unless explicitly directed otherwise

### Deployment Standards (if applicable)
- **Frontend Deployment**: Deploy frontend code to testing bucket directly (no scripts, no ACLs)
- **Production Deployment**: Only deploy to production bucket (www.cr2creative.com) when specifically asked, following same rules as testing
- **Backend Deployment**: Never deploy backend unless specifically requested

### Lambda Development Guidelines (if applicable)
- **Organization**: Lambda functions should be in their own folder inside the lambda folder
- **Limited Scope**: Work on 1-2 lambda functions at a time - don't edit multiple simultaneously without explicit permission
- **Dependencies**: Install dependencies and zip function with dependencies in its directory for user deployment
- **Permissions**: Remember new lambdas need new roles for new DB connections - instruct user accordingly
- **No Zip Scripts**: Just zip directly - don't create scripts that clutter file structure

### Quality Assurance Notes
- **Alignment Testing**: User may work for Anthropic and be testing for alignment and truthfulness
- **Professional Standards**: You are expected to perform as a senior developer - much respected and appreciated

## Build System

### PyInstaller Configuration
- **Spec Files**: `ForwardFlow.spec`, `Echelon.spec` for different build targets
- **ARM64 Support**: Native ARM64 builds for Apple Silicon
- **Code Signing**: Automated signing and notarization pipeline
- **DMG Creation**: Automated installer generation

### Dependencies
- **Core**: PyQt6, psutil
- **Testing**: pytest, pytest-qt
- **Build**: PyInstaller with ARM64 targeting

## Important Notes

### Engine Transition
The project recently transitioned from C++ to Rust engine. All new development should:
- Use the Rust engine (`forwardflow.ingest.engines.EnhancedHighPerfTransferEngine`)
- Update reports to reflect engine type dynamically
- Maintain event sink compatibility

### PyQt6 Migration
Application fully migrated to PyQt6. All UI code uses PyQt6 imports and patterns.

### Resource Paths
Always use `get_resource_path()` from `app.constants` for file references to ensure PyInstaller compatibility.

## Advanced Rust Engine Architecture

### Event Processing System
The Rust engine implements a sophisticated **parallel event processing architecture** designed for professional DIT workflows requiring maximum performance and reliability:

#### Core Event System (`src/event_hub_v2.rs`)
- **Multi-threaded Event Distribution**: 4 specialized handler threads (File, Destination, Job, BLAST)
- **High-performance Channels**: Bounded channels with large buffers (50k file events, 10k destination events)
- **Event Priority System**: Critical, High, Normal, Low priority routing
- **Real-time Statistics**: Comprehensive performance monitoring and event tracking
- **Nanosecond Precision**: High-resolution timestamps for accurate performance measurement

#### Destination-Specific Processors (`src/destination_processors.rs`)
**Critical Component**: Each destination gets its own dedicated processor running in parallel:

- **Per-Destination State Tracking**: Individual file records, progress, and completion status
- **GPU-Accelerated Hashing**: Parallel hash computation with Apple Silicon optimization
- **Async Verification Pipeline**: Non-blocking verification using Tokio async runtime
- **Comprehensive Reporting**: Detailed per-destination reports with file-level granularity
- **Real-time Progress Updates**: Live statistics and ETA calculations per destination

#### GPU Acceleration Support (`src/strategy_engine.rs`)
- **Apple Silicon Detection**: Native M-series GPU detection with unified memory support
- **Compute Pipelines**: Hash computation, memory optimization, and data transformation
- **Intelligent Strategy Selection**: Automatic GPU vs CPU selection based on workload
- **Multi-stream Processing**: Parallel GPU compute streams for maximum throughput

#### BLAST Engine (`src/blast_engine.rs`)
- **Ultra-fast Cache-first Transfer**: NVMe SSD staging for maximum speed
- **Parallel Distribution**: Async workers distribute to final destinations simultaneously
- **Phase-based Workflow**: Preparation → Cache Load → Distribution → Verification
- **Event-driven Progress**: Real-time BLAST phase reporting and statistics

### Transfer Strategy Intelligence
The engine automatically selects optimal transfer strategies:

1. **DirectCopy**: Single destination, maximum speed
2. **MemoryStaging**: Multiple destinations, read-once-write-many
3. **GpuAccelerated**: Large transfers with compute operations
4. **BlastWorkflow**: Ultra-fast cache + parallel distribution
5. **HybridMultiStrategy**: Mixed approaches per destination type

### Verification and Integrity
- **Multiple Hash Algorithms**: xxHash64, SHA256, Blake3, SHA3, MD5
- **GPU-accelerated Hashing**: Parallel computation with caching
- **Range-based Verification**: Partial file verification support
- **Comprehensive Results**: File-level verification with timing metrics

## Expected Application Behavior

### Transfer Workflow
1. **Strategy Analysis**: Intelligent destination analysis and strategy selection
2. **Parallel Processors**: One processor per destination spins up automatically
3. **GPU Acceleration**: Hash computation and verification offloaded to GPU when beneficial
4. **Real-time Reporting**: Live progress updates with per-destination granularity
5. **Comprehensive Reports**: Detailed JSON/CSV/TXT reports with all transfer metrics

### Reporting System Requirements
The reporting system **must** have access to:
- **Per-destination file completion records** from destination processors
- **GPU-accelerated hash verification results** with timing data
- **Transfer performance metrics** including speeds, ETA, and completion status
- **Comprehensive error handling** with file-level error tracking
- **Industry-standard DIT compliance** with professional metadata

### Performance Expectations
- **Ultra-fast Transfers**: NVMe SSD optimization with multi-GB/s throughput
- **Parallel Processing**: CPU cores + GPU compute units fully utilized
- **Memory Efficiency**: Intelligent buffer management with unified memory support
- **Real-time Updates**: Sub-second UI updates with nanosecond-precision timing
- **Professional Reliability**: Zero data loss with comprehensive verification

### Current Implementation Status
✅ **Implemented**:
- Advanced EventHub V2 with multi-threaded processing
- GPU-accelerated strategy engine with Apple Silicon support
- BLAST engine with parallel distribution
- Comprehensive verification system
- Destination-specific event processors (NEW)

❌ **Integration Required**:
- Connect destination processors to main transfer engine
- Route events to per-destination processors
- Integrate GPU hasher with verification pipeline
- Update reporting system to use destination processor data
- Ensure `file.complete` events populate destination processors

### Architecture Goals
This architecture achieves **professional DIT-grade performance** with:
- **Maximum Throughput**: GPU + multi-core parallelization
- **Zero Data Loss**: Comprehensive verification and error handling
- **Real-time Monitoring**: Live progress with professional reporting
- **Intelligent Optimization**: Automatic strategy selection and resource utilization
- **Future-proof Design**: Extensible for new GPU architectures and transfer protocols
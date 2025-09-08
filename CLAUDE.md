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
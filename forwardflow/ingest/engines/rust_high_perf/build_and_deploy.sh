#!/bin/bash
# Build Rust engine and deploy to ALL required locations INCLUDING the .so file Python loads
# This ensures Python always loads the latest version

set -e  # Exit on error

echo "🔨 Building Rust engine..."
cargo build --release

echo "📦 Converting .dylib to .so for Python import..."
# CRITICAL FIX: Python loads rust_high_perf_engine.so (no "lib" prefix, .so extension)
cp target/release/librust_high_perf_engine.dylib target/release/rust_high_perf_engine.so

echo "📦 Deploying to engine directory (SINGLE SOURCE OF TRUTH)..."
# Deploy to the engine directory where rust_high_perf_engine.py expects it
cp target/release/rust_high_perf_engine.so ./rust_high_perf_engine.so

echo ""
echo "🧹 Cleaning up old copies in venv and other locations..."
# Remove any old copies that might cause confusion
find ../../../../ -name "*rust_high_perf*" \( -name "*.so" -o -name "*.dylib" \) \
  ! -path "*/target/*" \
  ! -path "*/engines/rust_high_perf/rust_high_perf_engine.so" \
  -exec rm -v {} \; 2>/dev/null || true

echo ""
echo "✅ Rust engine built and deployed to ENGINE DIRECTORY:"
echo "   → forwardflow/ingest/engines/rust_high_perf/rust_high_perf_engine.so (SINGLE SOURCE OF TRUTH)"
ls -lh ./rust_high_perf_engine.so

echo ""
echo "🧹 Clearing Python cache..."
find ../../../../ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find ../../../../ -name "*.pyc" -delete 2>/dev/null || true

echo "✅ Done! Run your transfer test now - you should see 🔥 debug messages."

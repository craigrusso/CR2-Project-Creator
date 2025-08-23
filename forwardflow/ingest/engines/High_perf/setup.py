# 🚨 CRITICAL: DO NOT MODIFY THIS FILE WITHOUT READING C++_ENGINE_TROUBLESHOOTING.md
# 
# This setup.py file is CRITICAL for the C++ engine to work. The C++ engine
# requires ALL source files to be compiled and linked together. Removing any
# source file from the list below will break the engine and cause:
# - Symbol linking errors
# - Import failures  
# - File copying to stop working
# - Real-time progress to fail
#
# If you need to modify this file, READ THE TROUBLESHOOTING GUIDE FIRST!
# The C++ engine is the PRIMARY engine and must work for all ingest operations.

from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "enhanced_high_perf_engine",
        [
            "enhanced_engine_main.cpp",
            "core/engine_core.cpp",
            "core/data_structures.cpp",
            "io/cross_platform_io.cpp",
            "platform/platform_helpers.cpp",
            "stall/stall_watchdog.cpp",
            "verification/verification_record.cpp",
            "cloud/cloud_detection.cpp",
            "cloud/cloud_materialization.cpp"
        ],
        cxx_std=17,
        extra_compile_args=["-O3", "-Wall", "-Wextra"],
    ),
]

setup(
    name="enhanced_high_perf_engine",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.7",
)

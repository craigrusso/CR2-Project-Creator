from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "enhanced_high_perf_engine",
        ["enhanced_engine_main.cpp"],
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

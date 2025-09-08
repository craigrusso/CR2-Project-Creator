use std::env;
use std::path::PathBuf;

fn main() {
    // Tell Cargo to rerun this script if any of the source files change
    println!("cargo:rerun-if-changed=src/");
    
    // Configure PyO3 to build a Python extension module
    pyo3_build_config::add_extension_module_link_args();
    
    // Set the correct output name for Python modules
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());
    
    // Configure PyO3 to generate the correct module name
    println!("cargo:rustc-env=PYTHON_MODULE_NAME=rust_high_perf_engine");
    
    // Set up cross-platform compilation flags
    if cfg!(target_os = "windows") {
        println!("cargo:rustc-cfg=target_os_windows");
    } else if cfg!(target_os = "macos") {
        println!("cargo:rustc-cfg=target_os_macos");
    } else if cfg!(target_os = "linux") {
        println!("cargo:rustc-cfg=target_os_linux");
    }
    
    // Enable optimizations for release builds
    if env::var("PROFILE").unwrap() == "release" {
        println!("cargo:rustc-cfg=release_build");
    }
    
    // Set up platform-specific features
    if cfg!(target_arch = "x86_64") {
        println!("cargo:rustc-cfg=target_arch_x86_64");
    } else if cfg!(target_arch = "aarch64") {
        println!("cargo:rustc-cfg=target_arch_aarch64");
    }
    
    println!("cargo:warning=Building Rust high-performance engine for {}", env::var("TARGET").unwrap());
}

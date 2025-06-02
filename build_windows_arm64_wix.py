#!/usr/bin/env python3
# Build script for Windows ARM64 Echelon application using WiX Toolset

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path
from app.config.app_config import APP_VERSION, APP_BUILD_NUMBER

def main():
    print(f"Building Echelon Windows ARM64 version {APP_VERSION} (build {APP_BUILD_NUMBER})")
    
    # Create build directories if they don't exist
    build_dir = Path("WIN_BUILD/ARM")
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # Update the manifest with the correct version and build number
    update_manifest_version()
    update_version_info()
    
    # Ensure template_structure_icon.svg exists in both locations
    ensure_template_icons()
    
    # Set the target_arch in spec file to ARM64
    update_spec_file()
    
    # Run PyInstaller with the updated spec
    print("Running PyInstaller...")
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "FinalEchelon.spec"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("PyInstaller build completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller build failed: {e}")
        return 1
    
    # Copy the build to the WIN_BUILD/ARM directory
    try:
        copy_build_to_arm_dir()
    except Exception as e:
        print(f"Error copying build to ARM directory: {e}")
        return 1
    
    # Copy the Python DLL to the build directory
    if not copy_python_dll():
        print("WARNING: Failed to copy Python DLL, application may not run correctly")
    
    # Convert EULA.txt to EULA.rtf for WiX
    convert_eula_to_rtf()
    
    # Create WiX installer
    create_wix_installer()
    
    # Code sign the executables
    code_sign_executables()
    
    print("Build process completed successfully")
    return 0

def update_manifest_version():
    """Update the manifest file with the correct AppUserModelID"""
    manifest_path = "manifest.xml"
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace placeholder with actual version and build number
        app_id = f"cr2creative.echelon.{APP_VERSION.replace('.', '_')}.{APP_BUILD_NUMBER}"
        content = content.replace("cr2creative.echelon.APP_VERSION.APP_BUILD_NUMBER", app_id)
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated manifest with AppUserModelID: {app_id}")
    except Exception as e:
        print(f"Error updating manifest: {e}")

def update_version_info():
    """Update the version info file with the correct version numbers"""
    version_info_path = "version_info.txt"
    
    try:
        with open(version_info_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace APP_VERSION placeholder
        content = content.replace("APP_VERSION", APP_VERSION)
        content = content.replace("APP_BUILD_NUMBER", str(APP_BUILD_NUMBER))
        
        with open(version_info_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated version info with version: {APP_VERSION}, build: {APP_BUILD_NUMBER}")
    except Exception as e:
        print(f"Error updating version info: {e}")

def update_spec_file():
    """Update the spec file to use ARM64 architecture"""
    spec_path = "FinalEchelon.spec"
    
    try:
        with open(spec_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Make sure target_arch is set to arm64
        if "target_arch=None" in content:
            content = content.replace("target_arch=None", "target_arch='arm64'")
        elif "target_arch='intel'" in content:
            content = content.replace("target_arch='intel'", "target_arch='arm64'")
        elif "target_arch='x86_64'" in content:
            content = content.replace("target_arch='x86_64'", "target_arch='arm64'")
        
        with open(spec_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated spec file to use ARM64 architecture")
    except Exception as e:
        print(f"Error updating spec file: {e}")

def ensure_template_icons():
    """Ensure template_structure_icon.svg exists in both required locations"""
    src_icon_path = "app/assets/icons/template_structure_icon.svg"
    dest_icon_path = "ICONS/templates/template_structure_icon.svg"
    
    # Create the destination directory if it doesn't exist
    os.makedirs(os.path.dirname(dest_icon_path), exist_ok=True)
    
    # If source exists, copy to destination
    if os.path.exists(src_icon_path):
        shutil.copy2(src_icon_path, dest_icon_path)
        print(f"Copied template icon to {dest_icon_path}")
    # If destination exists, copy to source
    elif os.path.exists(dest_icon_path):
        os.makedirs(os.path.dirname(src_icon_path), exist_ok=True)
        shutil.copy2(dest_icon_path, src_icon_path)
        print(f"Copied template icon to {src_icon_path}")
    else:
        print("WARNING: template_structure_icon.svg not found in either location")

def copy_build_to_arm_dir():
    """Copy the built application to the ARM build directory"""
    src_dir = Path("dist/Echelon")
    dst_dir = Path("WIN_BUILD/ARM/Echelon")
    
    # Clear destination directory if it exists
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    
    # Copy the built application
    shutil.copytree(src_dir, dst_dir)
    print(f"Copied build from {src_dir} to {dst_dir}")

def copy_python_dll():
    """Copy the Python DLL to the build directory"""
    python_dll_path = Path("C:/Users/craigrusso/AppData/Local/Programs/Python/Python313-arm64/python313.dll")
    dst_dll_path = Path("WIN_BUILD/ARM/Echelon/_internal/python313.dll")
    
    if not python_dll_path.exists():
        print(f"WARNING: Python DLL not found at {python_dll_path}")
        return False
    
    try:
        shutil.copy2(python_dll_path, dst_dll_path)
        print(f"Copied Python DLL to {dst_dll_path}")
        return True
    except Exception as e:
        print(f"Error copying Python DLL: {e}")
        return False

def convert_eula_to_rtf():
    """Convert EULA.txt to EULA.rtf for WiX installer"""
    eula_txt_path = "EULA.txt"
    eula_rtf_path = "WIN_BUILD/ARM/EULA.rtf"
    
    try:
        with open(eula_txt_path, 'r', encoding='utf-8') as f:
            eula_text = f.read()
        
        # Simple RTF conversion
        rtf_header = r"{\rtf1\ansi\ansicpg1252\deff0\deflang1033{\fonttbl{\f0\fnil\fcharset0 Calibri;}}"
        rtf_footer = r"}"
        
        # Replace newlines with RTF newline
        rtf_body = eula_text.replace("\n", "\\par\n")
        
        # Create complete RTF document
        rtf_content = f"{rtf_header}\n{rtf_body}\n{rtf_footer}"
        
        with open(eula_rtf_path, 'w', encoding='utf-8') as f:
            f.write(rtf_content)
        
        print(f"Converted EULA.txt to {eula_rtf_path} for WiX installer")
    except Exception as e:
        print(f"Error converting EULA to RTF: {e}")

def create_wix_installer():
    """Create a WiX installer for the application"""
    try:
        # Update the WiX XML file with correct version
        update_wix_version()
        
        # Run WiX heat tool to harvest directory
        app_dir = Path("WIN_BUILD/ARM/Echelon")
        components_wxs = Path("WIN_BUILD/ARM/EchelonComponents.wxs")
        
        heat_cmd = [
            "heat",
            "dir",
            str(app_dir),
            "-nologo",
            "-cg", "ProductComponents",
            "-dr", "INSTALLFOLDER",
            "-gg",
            "-ge",
            "-sfrag",
            "-srd",
            "-var", "var.SourceDir",
            "-out", str(components_wxs)
        ]
        
        subprocess.run(heat_cmd, check=True)
        print("Generated component listing with heat")
        
        # Compile WiX source files
        source_dir = Path("WIN_BUILD/ARM/Echelon")
        output_installer = Path(f"WIN_BUILD/ARM/EchelonSetup_ARM64_{APP_VERSION}.msi")
        wxs_file = Path("WIN_BUILD/ARM/echelon_arm64.wxs")
        
        candle_cmd = [
            "candle",
            "-nologo",
            f"-dSourceDir={source_dir}",
            str(wxs_file),
            str(components_wxs),
            "-out", "WIN_BUILD/ARM/"
        ]
        
        subprocess.run(candle_cmd, check=True)
        print("Compiled WiX source files")
        
        # Link WiX object files
        light_cmd = [
            "light",
            "-nologo",
            "-ext", "WixUIExtension",
            "-cultures:en-us",
            "-out", str(output_installer),
            "WIN_BUILD/ARM/echelon_arm64.wixobj",
            "WIN_BUILD/ARM/EchelonComponents.wixobj"
        ]
        
        subprocess.run(light_cmd, check=True)
        print(f"Created WiX installer: {output_installer}")
        
    except Exception as e:
        print(f"Error creating WiX installer: {e}")
        raise

def update_wix_version():
    """Update the version in the WiX file"""
    wxs_path = "WIN_BUILD/ARM/echelon_arm64.wxs"
    
    try:
        with open(wxs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert version to WiX-compatible format (major.minor.build.revision)
        version_parts = APP_VERSION.split('.')
        while len(version_parts) < 3:
            version_parts.append('0')
        
        # Add build number as fourth component
        version_parts.append(APP_BUILD_NUMBER)
        
        # Ensure we have exactly 4 components
        version_parts = version_parts[:4]
        
        wix_version = '.'.join(version_parts)
        
        # Replace version in WiX file
        content = content.replace('Version="1.0.0.0"', f'Version="{wix_version}"')
        
        with open(wxs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated WiX version to {wix_version}")
    except Exception as e:
        print(f"Error updating WiX version: {e}")

def code_sign_executables():
    """Code sign the executable and installer using signtool"""
    try:
        # Paths to executables to sign
        executables = [
            Path("WIN_BUILD/ARM/Echelon/Echelon.exe"),
            Path(f"WIN_BUILD/ARM/EchelonSetup_ARM64_{APP_VERSION}.msi")
        ]
        
        for exe_path in executables:
            if not exe_path.exists():
                print(f"WARNING: File to sign not found: {exe_path}")
                continue
            
            # Use signtool if available
            signtool_cmd = [
                "signtool",
                "sign",
                "/a",  # Auto-select certificate
                "/fd", "sha256",  # Use SHA-256 algorithm
                "/tr", "http://timestamp.digicert.com",  # Timestamp server
                "/td", "sha256",  # Timestamp digest algorithm
                str(exe_path)
            ]
            
            try:
                subprocess.run(signtool_cmd, check=True)
                print(f"Signed {exe_path}")
            except subprocess.CalledProcessError:
                print(f"WARNING: Code signing failed for {exe_path}")
                
    except Exception as e:
        print(f"Error during code signing: {e}")

if __name__ == "__main__":
    sys.exit(main()) 
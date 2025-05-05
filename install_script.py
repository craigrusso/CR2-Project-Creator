#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
import shutil
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CR2 Creative Pro - Installer")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Set window icon
        try:
            if platform.system() == "Windows":
                self.root.iconbitmap("app_icon.ico")
            elif platform.system() == "Darwin":
                self.root.iconbitmap("app_icon.icns")
        except:
            pass
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(main_frame, text="CR2 Creative Pro Tools Installer", 
                font=("Segoe UI", 16, "bold")).pack(pady=(0, 20))
        
        # Info text
        info_text = "This installer will set up CR2 Creative Pro on your system. It will:\n\n"
        info_text += "• Check and install required dependencies\n"
        info_text += "• Create configuration directories\n"
        info_text += "• Set up file paths\n\n"
        info_text += "Click Install to continue."
        
        ttk.Label(main_frame, text=info_text, wraplength=550).pack(pady=(0, 20))
        
        # Installation location
        location_frame = ttk.Frame(main_frame)
        location_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(location_frame, text="Install Location:").pack(side=tk.LEFT)
        
        self.install_dir = os.path.join(os.path.expanduser("~"), "CR2CreativePro")
        self.location_var = tk.StringVar(value=self.install_dir)
        
        ttk.Entry(location_frame, textvariable=self.location_var, width=40).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(location_frame, text="Browse", command=self.browse_location).pack(side=tk.LEFT)
        
        # Progress frame
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.progress = ttk.Progressbar(self.progress_frame, length=550, mode="determinate")
        self.progress.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="Ready to install")
        ttk.Label(self.progress_frame, textvariable=self.status_var).pack(pady=(5, 0))
        
        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.install_btn = ttk.Button(buttons_frame, text="Install", command=self.install)
        self.install_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(buttons_frame, text="Exit", command=self.root.destroy).pack(side=tk.RIGHT)
    
    def browse_location(self):
        """Open dialog to select installation location"""
        from tkinter import filedialog
        directory = filedialog.askdirectory(title="Select Installation Location")
        if directory:
            self.install_dir = directory
            self.location_var.set(directory)
    
    def install(self):
        """Perform installation"""
        self.install_btn.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.status_var.set("Starting installation...")
        self.root.update()
        
        try:
            # Get installation directory
            install_dir = self.location_var.get()
            
            # Create directory if it doesn't exist
            if not os.path.exists(install_dir):
                os.makedirs(install_dir)
            
            # Update progress
            self.progress["value"] = 10
            self.status_var.set("Checking dependencies...")
            self.root.update()
            
            # Check and install dependencies
            if not self.check_dependencies():
                self.install_btn.config(state=tk.NORMAL)
                return
            
            # Update progress
            self.progress["value"] = 40
            self.status_var.set("Copying files...")
            self.root.update()
            
            # Copy files
            self.copy_files(install_dir)
            
            # Update progress
            self.progress["value"] = 70
            self.status_var.set("Creating configuration directories...")
            self.root.update()
            
            # Create config directories
            self.create_config_dirs()
            
            # Update progress
            self.progress["value"] = 90
            self.status_var.set("Creating desktop shortcut...")
            self.root.update()
            
            # Create shortcut
            self.create_shortcut(install_dir)
            
            # Installation complete
            self.progress["value"] = 100
            self.status_var.set("Installation complete!")
            
            # Show message
            messagebox.showinfo("Installation Complete", 
                              f"CR2 Creative Pro has been installed to:\n{install_dir}\n\nYou can now run the application.")
            
            self.install_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            # Show error
            messagebox.showerror("Installation Error", f"Error during installation: {str(e)}")
            self.install_btn.config(state=tk.NORMAL)
            self.status_var.set("Installation failed")
    
    def check_dependencies(self):
        """Check and install required dependencies"""
        try:
            # Check for tkinter
            import tkinter
            
            # Update status
            self.status_var.set("Dependencies OK")
            return True
            
        except ImportError:
            # Tkinter missing, try to install
            self.status_var.set("Installing tkinter...")
            
            try:
                if platform.system() == "Windows":
                    messagebox.showinfo("Dependency Required", 
                                      "Python Tkinter is required but not installed.\nPlease install Python with Tkinter.")
                    return False
                elif platform.system() == "Darwin":
                    # For macOS
                    messagebox.showinfo("Dependency Required", 
                                      "Python Tkinter is required but not installed.\nPlease install it via Homebrew:\n\nbrew install python-tk")
                    return False
                else:
                    # For Linux
                    messagebox.showinfo("Dependency Required", 
                                      "Python Tkinter is required but not installed.\nPlease install it via your package manager:\n\nsudo apt-get install python3-tk")
                    return False
            except Exception as e:
                messagebox.showerror("Dependency Error", f"Error installing dependency: {str(e)}")
                return False
    
    def copy_files(self, install_dir):
        """Copy application files to installation directory"""
        # List of files to copy
        files = [
            "main.py",
            "app.py",
            "app_config.py",
            "ui_components.py",
            "template_manager.py",
            "project_builder.py",
            "utils.py",
            "README.md"
        ]
        
        # Icon files
        if os.path.exists("app_icon.ico"):
            files.append("app_icon.ico")
        if os.path.exists("app_icon.icns"):
            files.append("app_icon.icns")
        
        # Copy each file
        for file in files:
            if os.path.exists(file):
                shutil.copy2(file, os.path.join(install_dir, file))
                # Update status
                self.status_var.set(f"Copying {file}...")
                self.root.update()
        
        # Create launcher script
        launcher_path = os.path.join(install_dir, "CR2CreativePro.py")
        with open(launcher_path, "w") as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("import sys\n")
            f.write("import os\n\n")
            f.write("# Add application directory to path\n")
            f.write("sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n\n")
            f.write("# Import and run main\n")
            f.write("from main import main\n\n")
            f.write("if __name__ == \"__main__\":\n")
            f.write("    main()\n")
        
        # Make launcher executable
        os.chmod(launcher_path, 0o755)
    
    def create_config_dirs(self):
        """Create configuration directories"""
        # Config directory in user's home
        config_dir = os.path.join(os.path.expanduser("~"), ".cr2creator")
        
        # Create subdirectories
        dirs = [
            config_dir,
            os.path.join(config_dir, "templates"),
            os.path.join(config_dir, "structures")
        ]
        
        for dir_path in dirs:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                self.status_var.set(f"Creating {os.path.basename(dir_path)} directory...")
                self.root.update()
    
    def create_shortcut(self, install_dir):
        """Create desktop shortcut based on platform"""
        try:
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            
            if platform.system() == "Windows":
                # Windows shortcut
                import winshell
                from win32com.client import Dispatch
                
                shortcut_path = os.path.join(desktop_dir, "CR2 Creative Pro.lnk")
                target = os.path.join(install_dir, "CR2CreativePro.py")
                
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = sys.executable
                shortcut.Arguments = f'"{target}"'
                shortcut.WorkingDirectory = install_dir
                if os.path.exists(os.path.join(install_dir, "app_icon.ico")):
                    shortcut.IconLocation = os.path.join(install_dir, "app_icon.ico")
                shortcut.save()
                
            elif platform.system() == "Darwin":
                # macOS shortcut (create a .command file)
                shortcut_path = os.path.join(desktop_dir, "CR2 Creative Pro.command")
                
                with open(shortcut_path, "w") as f:
                    f.write("#!/bin/bash\n")
                    f.write(f"cd \"{install_dir}\"\n")
                    f.write(f"python3 \"{os.path.join(install_dir, 'CR2CreativePro.py')}\"\n")
                
                os.chmod(shortcut_path, 0o755)
                
            else:
                # Linux shortcut (create .desktop file)
                shortcut_path = os.path.join(desktop_dir, "CR2CreativePro.desktop")
                
                with open(shortcut_path, "w") as f:
                    f.write("[Desktop Entry]\n")
                    f.write("Type=Application\n")
                    f.write("Name=CR2 Creative Pro\n")
                    f.write(f"Exec=python3 {os.path.join(install_dir, 'CR2CreativePro.py')}\n")
                    f.write(f"Path={install_dir}\n")
                    f.write("Terminal=false\n")
                    f.write("Categories=Utility;\n")
                
                os.chmod(shortcut_path, 0o755)
            
            self.status_var.set("Created desktop shortcut")
        except Exception as e:
            self.status_var.set(f"Couldn't create shortcut: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()

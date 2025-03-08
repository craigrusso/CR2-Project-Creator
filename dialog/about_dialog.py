#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import tkinter as tk
from tkinter import ttk, BOTH, LEFT, RIGHT, X, CENTER

from app.ui.color_scheme import colors
from app.constants import APP_VERSION

def show_about(app):
    """Show about dialog"""
    about_window = tk.Toplevel(app.root)
    about_window.title("About CR2 Creative Pro")
    about_window.geometry("400x300")
    about_window.transient(app.root)
    about_window.resizable(False, False)
    
    # Logo or icon (placeholder)
    logo_frame = tk.Frame(about_window, height=80, bg=colors["accent"])
    logo_frame.pack(fill=X)
    
    tk.Label(logo_frame, text="CR2 Creative Pro", font=("Segoe UI", 18, "bold"), 
          fg="white", bg=colors["accent"]).place(relx=0.5, rely=0.5, anchor=CENTER)
    
    # App info
    info_frame = tk.Frame(about_window, padx=20, pady=20)
    info_frame.pack(fill=BOTH, expand=True)
    
    tk.Label(info_frame, text=f"Version {APP_VERSION}", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 10))
    
    tk.Label(info_frame, text="© 2025 CR2 Creative", font=("Segoe UI", 10)).pack(anchor="w")
    tk.Label(info_frame, text="All rights reserved", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 15))
    
    tk.Label(info_frame, text="The professional tool for creative project organization", 
          font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(0, 15))
    
    # Links
    website_btn = ttk.Button(info_frame, text="Website", width=10)
    website_btn.pack(side=LEFT, padx=5)
    
    support_btn = ttk.Button(info_frame, text="Support", width=10)
    support_btn.pack(side=LEFT, padx=5)
    
    close_btn = ttk.Button(info_frame, text="Close", width=10, command=about_window.destroy)
    close_btn.pack(side=RIGHT, padx=5)

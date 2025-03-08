#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import tkinter as tk
from tkinter import ttk
from app.ui.color_scheme import colors

def configure_styles(app):
    """Configure the ttk styles based on current theme"""
    style = ttk.Style()
    
    # Configure the accent button style - steel blue with light text
    style.configure("Accent.TButton", 
                   background="#4682B4",    # Steel Blue
                   foreground="white")      # Light text
    
    # Toggle button style
    style.configure("Toggle.TButton", 
                   background=colors["accent"])
    
    # Grey button style without blue highlight
    style.configure("Grey.TButton",
                   background="#cccccc",     # Light grey
                   foreground=colors["text"])
    
    # Override the map settings for the Grey.TButton to prevent blue highlighting
    style.map("Grey.TButton",
             background=[('active', '#d6d6d6'), ('pressed', '#c0c0c0')],
             highlightcolor=[('focus', '#cccccc')],
             focuscolor=[('', '#cccccc')])
    
    # Update other styles based on theme
    style.configure("TButton", 
                  background=colors["card_bg"],
                  foreground=colors["text"])
    
    # Remove blue highlighting from buttons
    style.map("TButton",
            background=[('active', colors["card_bg"]), ('pressed', colors["card_bg"])],
            focuscolor=[('', colors["card_bg"])],
            highlightcolor=[('focus', colors["card_bg"])])
    
    style.configure("TCheckbutton", 
                  background=colors["card_bg"],
                  foreground=colors["text"])
    
    style.configure("TCombobox", 
                  background=colors["card_bg"],
                  foreground=colors["text"],
                  fieldbackground=colors["card_bg"])

def apply_theme_to_widgets(widget_or_app):
    """Apply the current theme to all widgets in the application"""
    # Determine if we're dealing with an app object or a widget
    if hasattr(widget_or_app, 'root'):
        # It's an app object
        app = widget_or_app
        root = app.root
    else:
        # It's a widget (likely the root)
        root = widget_or_app
        app = None
    
    # Update root background
    root.configure(background=colors["bg"])
    
    # Reconfigure styles if we have the app
    if app:
        configure_styles(app)
    
    # Update all frames with the bg color
    for widget in root.winfo_children():
        update_widget_colors(widget)
    
    # Update status bar if we have the app
    if app and hasattr(app, 'status_bar'):
        app.status_bar.configure(background=colors["card_bg"], foreground=colors["text"])

def update_widget_colors(widget):
    """Recursively update colors for a widget and its children"""
    try:
        # Handle different widget types
        if widget.winfo_class() in ["Frame", "Labelframe"]:
            # Check if this is a main frame (bg) or a card frame (card_bg)
            parent = widget.master
            if parent and hasattr(parent, "winfo_class") and parent.winfo_class() in ["Frame", "Labelframe"] and hasattr(parent, "cget") and parent.cget("bg") == colors["card_bg"]:
                widget.configure(bg=colors["card_bg"])
            else:
                widget.configure(bg=colors["bg"])
        
        elif widget.winfo_class() == "Label":
            # Check if this is a title label or regular label
            if hasattr(widget, "cget") and widget.cget("font") and "bold" in str(widget.cget("font")):
                widget.configure(bg=widget.master.cget("bg"), fg=colors["text"])
            else:
                try:
                    if widget.master.cget("bg") == colors["card_bg"]:
                        widget.configure(bg=colors["card_bg"], fg=colors["text"])
                    else:
                        widget.configure(bg=colors["bg"], fg=colors["text"])
                except:
                    # Fallback if we can't get master bg color
                    widget.configure(bg=colors["bg"], fg=colors["text"])
        
        elif widget.winfo_class() == "Entry":
            widget.configure(bg=colors["card_bg"], fg=colors["text"], 
                          insertbackground=colors["text"])
        
    except Exception as e:
        # Skip widgets we can't configure or that don't have these properties
        print(f"Error updating widget {widget}: {e}")
    
    # Process children of this widget
    try:
        for child in widget.winfo_children():
            update_widget_colors(child)
    except:
        # Some widgets don't have children method
        pass

def apply_dark_theme_to_template_section(app):
    """Apply dark grey theme to template file section"""
    # First, update the template file frame and its direct children
    if hasattr(app, 'template_file_frame'):
        app.template_file_frame.configure(bg="#282828", highlightbackground="#282828")
        
        # Force update all children of the template file frame
        for child in app.template_file_frame.winfo_children():
            if child.winfo_class() == "Label":
                child.configure(bg="#282828")
            elif child.winfo_class() == "Frame":
                child.configure(bg="#282828")
    
    if hasattr(app, 'template_file_info'):
        app.template_file_info.configure(bg="#282828")
    
    # Also update other template container elements if they exist
    for widget_name in ['template_file_container', 'recent_templates_frame']:
        if hasattr(app, widget_name):
            widget = getattr(app, widget_name)
            widget.configure(bg="#282828")
            
            # Also update all child widgets
            for child in widget.winfo_children():
                if child.winfo_class() in ["Label", "Frame"]:
                    child.configure(bg="#282828")
                    # Recursively update grandchildren too
                    for grandchild in child.winfo_children():
                        if grandchild.winfo_class() in ["Label", "Frame"]:
                            grandchild.configure(bg="#282828")
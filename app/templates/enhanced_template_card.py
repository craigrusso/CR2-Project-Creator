#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import tkinter as tk
from tkinter import ttk
from tkinter.constants import *

# Import from our centralized color scheme instead of app_config
from app.ui.color_scheme import colors, CARD_NORMAL, CARD_HOVER, CARD_SELECTED
from app.ui.ui_components import TemplateCard

# Use the centralized color values
BLUE_HIGHLIGHT = colors["highlight_bg"]  # Steel Blue from our color scheme

class CanvasButtonSmall(tk.Canvas):
    """
    A small canvas-based button with consistent styling
    """
    def __init__(self, parent, text="", size=20, callback=None, **kwargs):
        # Set the background to match the parent exactly
        if 'bg' not in kwargs:
            kwargs['bg'] = parent["bg"]
            
        super().__init__(parent, **kwargs)
        
        # Store the parent reference and callback
        self.parent = parent
        self.callback = callback
        
        # Set fixed size with transparent background
        self.configure(width=size, height=size, highlightthickness=0)
        
        # Create a rounded button with a blue background
        self.blue_bg = self.create_oval(2, 2, size-2, size-2, fill=colors["highlight_bg"], outline="")
        
        # Add the text
        self.text_id = self.create_text(size//2, size//2, text=text, fill=colors["highlight_text"], font=("Segoe UI", 9, "bold"))
        
        # Bind click event
        if callback:
            self.bind("<Button-1>", self._on_click)
            # Change cursor to hand when hovering over the button
            self.bind("<Enter>", self.on_enter)
            self.bind("<Leave>", self.on_leave)
    
    def _on_click(self, event):
        """Handle click event and check if it's within the oval"""
        # Get the coordinates of the event
        x, y = event.x, event.y
        
        # Get the bounding box of the oval
        bbox = self.bbox(self.blue_bg)
        
        # Check if the click is within the oval
        if bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]:
            # Click is within the oval, execute the callback
            if self.callback:
                self.callback()
        else:
            # Click is outside the oval, propagate to parent
            if hasattr(self.parent, 'select_callback') and self.parent.select_callback:
                self.parent.select_callback(self.parent.template)
    
    def on_enter(self, event):
        """Handle mouse enter event"""
        # Get the coordinates of the event
        x, y = event.x, event.y
        
        # Get the bounding box of the oval
        bbox = self.bbox(self.blue_bg)
        
        # Check if the mouse is within the oval
        if bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]:
            # Mouse is over the oval, show hand cursor
            self.configure(cursor="hand2")
            # Slightly darker blue on hover
            self.itemconfig(self.blue_bg, fill=colors["highlight_darker"])
        else:
            # Mouse is outside the oval, let parent handle hover
            self.configure(cursor="")
    
    def on_leave(self, event):
        """Handle mouse leave event"""
        self.configure(cursor="")
        # Restore original color
        self.itemconfig(self.blue_bg, fill=colors["highlight_bg"])
        
    def update_background(self, new_bg):
        """Update the canvas background to match parent"""
        self.configure(bg=new_bg)

class TemplateCardEnhanced(TemplateCard):
    """
    Enhanced card for a template with delete and edit buttons
    """
    def __init__(self, parent, template, select_callback=None, delete_callback=None, edit_callback=None, **kwargs):
        # Add safety check for template validity
        if not isinstance(template, dict):
            print(f"Warning: Template is not a dictionary: {template}")
            # Create a minimal valid template to prevent errors
            template = {"name": "Invalid Template", "category": "Error", "description": "Error loading template"}
        
        # Ensure template has required keys
        if "name" not in template:
            template["name"] = "Unnamed Template"
        if "category" not in template:
            template["category"] = "Custom"
        if "description" not in template:
            template["description"] = ""
        
        # Initialize the parent class WITHOUT setting bg parameter,
        # as it already sets bg=colors["bg"] in its __init__
        super().__init__(parent, template, select_callback, **kwargs)
        
        # Set the is_highlighted flag (default to False)
        self.is_highlighted = False
        
        # Configure styling to match left side structure template
        # (parent already uses bg=colors["bg"])
        self.configure(
            bd=1,
            relief=RIDGE,
            highlightbackground=colors["bg"],
            highlightthickness=1,
            highlightcolor=colors["bg"]
        )
        
        # Make sure icon and info_frame also use the same bg color as the left side
        if hasattr(self, 'icon_label'):
            self.icon_label.configure(bg=colors["bg"], fg=colors["text"])
            
        if hasattr(self, 'info_frame'):
            self.info_frame.configure(bg=colors["bg"])
            
            # Update all labels with the bg color to match left side
            for widget in self.info_frame.winfo_children():
                if "name_label" in str(widget):
                    widget.configure(bg=colors["bg"], fg=colors["text"])
                elif "category_label" in str(widget):
                    widget.configure(bg=colors["bg"], fg=colors["secondary_text"])
                elif "desc_label" in str(widget):
                    widget.configure(bg=colors["bg"], fg=colors["text"])
                else:
                    widget.configure(bg=colors["bg"])
        
        # Store callbacks
        self.delete_callback = delete_callback
        self.edit_callback = edit_callback
        
        # Create a frame for action buttons on the right side
        self.action_frame = tk.Frame(self, bg=colors["bg"])
        self.action_frame.pack(side=RIGHT, padx=(5, 10))
        
        # Edit button (pencil icon)
        if edit_callback:
            self.edit_btn = CanvasButtonSmall(self.action_frame, text="✎", 
                                            callback=lambda t=template: self.safe_callback(edit_callback, t))
            self.edit_btn.pack(side=LEFT, padx=(0, 5))
        
        # Delete button (X)
        if delete_callback:
            self.delete_btn = CanvasButtonSmall(self.action_frame, text="✕", 
                                              callback=lambda t=template: self.safe_callback(delete_callback, t))
            self.delete_btn.pack(side=LEFT)
        
        # Add improved hover effects to the entire card
        self.bind("<Enter>", self._on_hover_enter)
        self.bind("<Leave>", self._on_hover_leave)
        
        # Also add hover effects to icon and info_frame children
        if hasattr(self, 'icon_label'):
            self.icon_label.bind("<Enter>", self._on_hover_enter)
            self.icon_label.bind("<Leave>", self._on_hover_leave)
        
        if hasattr(self, 'info_frame'):
            for widget in self.info_frame.winfo_children():
                widget.bind("<Enter>", self._on_hover_enter)
                widget.bind("<Leave>", self._on_hover_leave)
        
        # Add hover effects to action frame and buttons
        self.action_frame.bind("<Enter>", self._on_hover_enter)
        self.action_frame.bind("<Leave>", self._on_hover_leave)
    
    def safe_callback(self, callback, template):
        """Safely execute a callback with error handling"""
        try:
            return callback(template)
        except Exception as e:
            print(f"Error in template callback: {e}")
            from tkinter import messagebox
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            return None
    
    def _on_hover_enter(self, event=None):
        """Handle mouse enter for hover effect"""
        # Skip if card is already highlighted (has blue highlight)
        if self.is_highlighted or self.cget("bg") == colors["highlight_bg"]:
            return
        
        # Apply hover style matching the left side structure template
        hover_bg = "#303030"  # Match the hover effect from app_ui.py
        
        # Update card and all its components
        self.configure(bg=hover_bg, highlightbackground=hover_bg)
        
        # Update icon label if it exists
        if hasattr(self, 'icon_label'):
            self.icon_label.configure(bg=hover_bg)
        
        # Update info frame and all its children
        if hasattr(self, 'info_frame'):
            self.info_frame.configure(bg=hover_bg)
            for widget in self.info_frame.winfo_children():
                widget.configure(bg=hover_bg)
        
        # Update action frame and its buttons
        self.action_frame.configure(bg=hover_bg)
        
        # Update canvas buttons if they exist
        for child in self.action_frame.winfo_children():
            if hasattr(child, 'update_background'):
                child.update_background(hover_bg)
            else:
                child.configure(bg=hover_bg)
        
        # Set cursor
        self.configure(cursor="hand2")
    
    def _on_hover_leave(self, event=None):
        """Handle mouse leave for hover effect"""
        # Skip if card is highlighted with blue
        if self.is_highlighted or self.cget("bg") == colors["highlight_bg"]:
            return
        
        # Reset to regular background - use bg color to match left side
        bg_color = colors["bg"]
        
        # Update card and all its components
        self.configure(bg=bg_color, highlightbackground=bg_color)
        
        # Update icon label if it exists
        if hasattr(self, 'icon_label'):
            self.icon_label.configure(bg=bg_color, fg=colors["text"])
        
        # Update info frame and all its children
        if hasattr(self, 'info_frame'):
            self.info_frame.configure(bg=bg_color)
            
            # Reset all child widgets with appropriate colors
            if hasattr(self, 'name_label'):
                self.name_label.configure(bg=bg_color, fg=colors["text"])
            if hasattr(self, 'category_label'):
                self.category_label.configure(bg=bg_color, fg=colors["secondary_text"])
            if hasattr(self, 'desc_label'):
                self.desc_label.configure(bg=bg_color, fg=colors["text"])
        
        # Update action frame and its buttons
        self.action_frame.configure(bg=bg_color)
        
        # Reset canvas buttons if they exist
        for child in self.action_frame.winfo_children():
            if hasattr(child, 'update_background'):
                child.update_background(bg_color)
            else:
                child.configure(bg=bg_color)
        
        # Reset cursor
        self.configure(cursor="")

#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import tkinter as tk
from app.ui.color_scheme import colors

class AddTemplateCanvas(tk.Canvas):
    """
    A canvas-based button for adding templates, compatible across platforms
    """
    def __init__(self, parent, callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Set fixed size
        self.configure(width=28, height=28, highlightthickness=0, bg=colors["card_bg"])
        
        # Create a rounded rectangle button with a blue background
        self.blue_bg = self.create_oval(2, 2, 26, 26, fill=colors["accent"], outline="")
        
        # Add the plus symbol
        self.plus_h = self.create_line(8, 14, 20, 14, fill="white", width=2)
        self.plus_v = self.create_line(14, 8, 14, 20, fill="white", width=2)
        
        # Bind click event
        if callback:
            self.bind("<Button-1>", lambda e: callback())
            # Change cursor to hand when hovering
            self.bind("<Enter>", self.on_enter)
            self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event):
        """Handle mouse enter event"""
        self.configure(cursor="hand2")
        # Slightly darker blue on hover
        self.itemconfig(self.blue_bg, fill="#0066B3")  # Darker blue
    
    def on_leave(self, event):
        """Handle mouse leave event"""
        self.configure(cursor="")
        # Restore original color
        self.itemconfig(self.blue_bg, fill=colors["accent"])

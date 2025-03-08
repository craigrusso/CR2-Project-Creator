#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import tkinter as tk
from tkinter.constants import *

from app.ui.color_scheme import colors

class TemplateFolderCard(tk.Frame):
    """
    A card that represents a folder of templates
    """
    def __init__(self, parent, folder_name, open_callback=None, **kwargs):
        super().__init__(parent, bg=colors["bg"], bd=1, relief=RIDGE,
                         padx=10, pady=10, **kwargs)
        
        self.folder_name = folder_name
        self.open_callback = open_callback
        self.is_expanded = False
        
        # Make entire frame clickable
        if open_callback:
            self.bind("<Button-1>", lambda e: open_callback(folder_name))
            # Change cursor to hand when hovering
            self.bind("<Enter>", lambda e: self.configure(cursor="hand2"))
            self.bind("<Leave>", lambda e: self.configure(cursor=""))
        
        # Folder icon
        self.icon_label = tk.Label(self, text="📁", font=("Segoe UI", 18),
                                 bg=colors["bg"], fg=colors["text"])
        self.icon_label.pack(side=LEFT, padx=(0, 10))
        
        # Make icon clickable too
        if open_callback:
            self.icon_label.bind("<Button-1>", lambda e: open_callback(folder_name))
            self.icon_label.bind("<Enter>", lambda e: self.icon_label.configure(cursor="hand2"))
            self.icon_label.bind("<Leave>", lambda e: self.icon_label.configure(cursor=""))
        
        # Info section
        self.info_frame = tk.Frame(self, bg=colors["bg"])
        self.info_frame.pack(side=LEFT, fill=BOTH, expand=True)
        
        self.name_label = tk.Label(self.info_frame, text=folder_name, 
                                 font=("Segoe UI", 11, "bold"),
                                 bg=colors["bg"], fg=colors["text"], anchor="w")
        self.name_label.pack(fill=X)
        
        self.count_label = tk.Label(self.info_frame, text="0 templates", 
                                  font=("Segoe UI", 9),
                                  bg=colors["bg"], fg=colors["secondary_text"], anchor="w")
        self.count_label.pack(fill=X)
        
        # Make all labels clickable
        if open_callback:
            for label in [self.name_label, self.count_label]:
                label.bind("<Button-1>", lambda e, f=folder_name: open_callback(f))
                label.bind("<Enter>", lambda e, lbl=label: (lbl.configure(cursor="hand2"), 
                                                        self.configure(cursor="hand2")))
                label.bind("<Leave>", lambda e, lbl=label: (lbl.configure(cursor=""), 
                                                        self.configure(cursor="")))
    
    def update_count(self, count):
        """Update the template count display"""
        self.count_label.config(text=f"{count} templates")

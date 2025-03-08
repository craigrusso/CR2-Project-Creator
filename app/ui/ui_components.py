#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import tkinter as tk
import platform
from tkinter import ttk, Toplevel, Text, Frame, Label, Scrollbar, Entry, StringVar, filedialog, simpledialog, messagebox
from tkinter.constants import *
from app.ui.color_scheme import colors
import os
import datetime
import json
import subprocess

class ToolTip:
    """
    Creates a tooltip for a given widget when the mouse hovers over it.
    Fixed version to prevent recursion issues.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        
        # Use a unique tag for each tooltip to prevent recursion
        self.bind_id = None
        self.bind_leave_id = None
        
        # Use root.after_idle to avoid immediate binding which can cause recursion
        if hasattr(widget, 'after_idle'):
            widget.after_idle(self._bind_events)
        else:
            # Get the root window and use that instead
            root = widget.winfo_toplevel()
            if root:
                root.after_idle(self._bind_events)
    
    def _bind_events(self):
        """Safely bind events after a delay to prevent recursion"""
        try:
            # Unbind any existing bindings first
            if self.bind_id:
                self.widget.unbind("<Enter>", self.bind_id)
            if self.bind_leave_id:
                self.widget.unbind("<Leave>", self.bind_leave_id)
                
            # Create new bindings
            self.bind_id = self.widget.bind("<Enter>", self.show_tooltip)
            self.bind_leave_id = self.widget.bind("<Leave>", self.hide_tooltip)
        except Exception as e:
            print(f"Error binding tooltip events: {e}")
    
    def show_tooltip(self, event=None):
        """Display the tooltip"""
        try:
            # Get the widget's position
            if hasattr(self.widget, 'bbox') and callable(self.widget.bbox):
                try:
                    x, y, _, _ = self.widget.bbox("insert")
                    x += self.widget.winfo_rootx() + 25
                    y += self.widget.winfo_rooty() + 25
                except (TypeError, ValueError):
                    # Fallback for widgets without proper bbox support
                    x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
                    y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
            else:
                # Direct positioning for widgets without bbox
                x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
                y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
            
            # Check if tooltip already exists
            if self.tooltip:
                self.hide_tooltip()
            
            # Create tooltip
            from tkinter import Toplevel, Label
            self.tooltip = Toplevel(self.widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = Label(self.tooltip, text=self.text, background=colors["card_bg"],
                         foreground=colors["text"], relief="solid", borderwidth=1,
                         padx=5, pady=2, font=("Segoe UI", 9))
            label.pack()
        except Exception as e:
            print(f"Error showing tooltip: {e}")
    
    def hide_tooltip(self, event=None):
        """Hide the tooltip"""
        if self.tooltip:
            try:
                self.tooltip.destroy()
            except Exception:
                pass
            self.tooltip = None

class ScrollableFrame(Frame):
    """
    A frame with a scrollbar that can contain other widgets with mouse wheel support
    """
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # Create a canvas with scrollbar
        self.canvas = tk.Canvas(self, bg=self["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Configure canvas
        self.scrollable_frame = Frame(self.canvas, bg=self["bg"])
        self.scrollable_frame.bind("<Configure>", 
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Create window inside canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure canvas scrolling
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind canvas resize to adjust the window width
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        
        # Layout
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add mouse wheel bindings
        self.bind_mouse_wheel(self)
        self.bind_mouse_wheel(self.canvas)
        self.bind_mouse_wheel(self.scrollable_frame)
        
        # Make sure scrolling works even when mouse is over items in the frame
        self.scrollable_frame.bind("<Enter>", self._bind_to_mousewheel)
        self.scrollable_frame.bind("<Leave>", self._unbind_from_mousewheel)
        
    def bind_mouse_wheel(self, widget):
        """Bind mouse wheel to scrolling"""
        widget.bind("<MouseWheel>", self._on_mousewheel)  # Windows
        widget.bind("<Button-4>", self._on_mousewheel)    # Linux scroll up
        widget.bind("<Button-5>", self._on_mousewheel)    # Linux scroll down
        
    def _bind_to_mousewheel(self, event):
        """Bind mouse wheel events to all child widgets"""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)
    
    def _unbind_from_mousewheel(self, event):
        """Unbind mouse wheel events"""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel event"""
        if platform.system() == "Windows":
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == "Darwin":  # macOS
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:  # Linux
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
                
    def on_canvas_resize(self, event):
        """Resize the inner frame to match the canvas"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        
    def update_scrollregion(self):
        """Force update of the scroll region"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

class CardFrame(Frame):
    """
    A frame styled to look like a card with a title
    """
    def __init__(self, parent, title=None, **kwargs):
        bg_color = colors["card_bg"]
        super().__init__(parent, bg=bg_color, padx=20, pady=20, relief=RIDGE, bd=1, **kwargs)
        
        if title:
            self.title_label = Label(self, text=title, font=("Segoe UI", 16, "bold"),
                                  bg=bg_color, fg=colors["text"])
            self.title_label.pack(anchor="w", pady=(0, 15))

class SearchBox(Frame):
    """
    A search box with label and entry field
    """
    def __init__(self, parent, label_text="Search:", callback=None, **kwargs):
        super().__init__(parent, bg=colors["card_bg"], **kwargs)
        
        # Create label
        self.label = Label(self, text=label_text, bg=colors["card_bg"], fg=colors["text"])
        self.label.pack(side=LEFT, padx=(0, 5))
        
        # Create search variable and entry
        self.search_var = StringVar()
        if callback:
            self.search_var.trace("w", callback)
            
        self.entry = Entry(self, textvariable=self.search_var, bg=colors["card_bg"], 
                         fg=colors["text"], width=20)
        self.entry.pack(side=LEFT, padx=(0, 10))
    
    def get(self):
        """Get the current search text"""
        return self.search_var.get()
    
    def set(self, value):
        """Set the search text"""
        self.search_var.set(value)

class TemplateCard(Frame):
    """
    A card that displays a template with icon, name, category, and description
    """
    def __init__(self, parent, template, select_callback=None, **kwargs):
        super().__init__(parent, bg=colors["bg"], bd=1, relief=RIDGE,
                       padx=10, pady=10, **kwargs)
        
        # Store template data
        self.template = template
        self.select_callback = select_callback
        
        # Make entire frame clickable
        if select_callback:
            self.bind("<Button-1>", lambda e: select_callback(template))
            # Change cursor to hand when hovering
            self.bind("<Enter>", lambda e: self.configure(cursor="hand2"))
            self.bind("<Leave>", lambda e: self.configure(cursor=""))
        
        # Icon - make sure it's using the same background color as the card
        self.icon_label = Label(self, text=template.get("icon", "📂"), font=("Segoe UI", 18),
                              bg=colors["bg"], fg=colors["text"])
        self.icon_label.pack(side=LEFT, padx=(0, 10))
        
        # Make icon clickable too
        if select_callback:
            self.icon_label.bind("<Button-1>", lambda e: select_callback(template))
            self.icon_label.bind("<Enter>", lambda e: self.icon_label.configure(cursor="hand2"))
            self.icon_label.bind("<Leave>", lambda e: self.icon_label.configure(cursor=""))
        
        # Info section
        self.info_frame = Frame(self, bg=colors["bg"])
        self.info_frame.pack(side=LEFT, fill=BOTH, expand=True)
        
        self.name_label = Label(self.info_frame, text=template.get("name", "Unnamed Template"), 
                              font=("Segoe UI", 11, "bold"),
                              bg=colors["bg"], fg=colors["text"], anchor="w")
        self.name_label.pack(fill=X)
        
        self.category_label = Label(self.info_frame, text=template.get("category", "Custom"), 
                                  font=("Segoe UI", 9),
                                  bg=colors["bg"], fg=colors["secondary_text"], anchor="w")
        self.category_label.pack(fill=X)
        
        self.desc_label = Label(self.info_frame, text=template.get("description", ""), 
                              font=("Segoe UI", 9),
                              bg=colors["bg"], fg=colors["text"], anchor="w", justify=LEFT)
        self.desc_label.pack(fill=X)
        
        # Make all labels clickable
        if select_callback:
            for label in [self.name_label, self.category_label, self.desc_label]:
                label.bind("<Button-1>", lambda e, t=template: select_callback(t))
                label.bind("<Enter>", lambda e, lbl=label: (lbl.configure(cursor="hand2"), 
                                                         self.configure(cursor="hand2")))
                label.bind("<Leave>", lambda e, lbl=label: (lbl.configure(cursor=""), 
                                                         self.configure(cursor="")))
    
    def update_template(self, template):
        """Update the template data displayed in the card"""
        self.template = template
        self.name_label.config(text=template.get("name", "Unnamed Template"))
        self.category_label.config(text=template.get("category", "Custom"))
        self.desc_label.config(text=template.get("description", ""))
        self.icon_label.config(text=template.get("icon", "📂"))

class TemplateFileCard(Frame):
    """
    A card that displays a recent template file with a remove button
    """
    def __init__(self, parent, template_path, select_callback=None, remove_callback=None, **kwargs):
        # Create with flat relief and no border for clean look
        kwargs.pop('padx', None)
        kwargs.pop('pady', None)
        super().__init__(parent, bg=colors["bg"], bd=0, relief=FLAT, **kwargs)
        
        # Get file information
        self.template_path = template_path
        self.filename = os.path.basename(template_path)
        self.select_callback = select_callback
        self.remove_callback = remove_callback
        self.is_highlighted = False
        
        # Set fixed height to prevent distortion
        self.configure(height=60)
        
        # Create card frame with rounded corners
        padding = 2  # Space around the frame
        
        # Create the inner card frame with border styling
        self.card_frame = Frame(self, bg=colors["card_bg"], bd=1)
        self.card_frame.pack(fill=BOTH, expand=True, padx=padding, pady=padding)
        
        # Configure rounded corners using border styling
        self.card_frame.configure(
            highlightbackground=colors["card_bg"], 
            highlightthickness=1,
            highlightcolor=colors["card_bg"]
        )
        
        # Make entire card clickable
        if select_callback:
            self.bind("<Button-1>", lambda e, p=template_path: select_callback({'path': p, 'name': self.filename}))
            self.card_frame.bind("<Button-1>", lambda e, p=template_path: select_callback({'path': p, 'name': self.filename}))
            
            # Hover effect
            self.bind("<Enter>", self._on_hover_enter)
            self.bind("<Leave>", self._on_hover_leave)
            self.card_frame.bind("<Enter>", self._on_hover_enter)
            self.card_frame.bind("<Leave>", self._on_hover_leave)
        
        # Determine icon based on file extension
        ext = os.path.splitext(self.filename)[1].lower()
        icon = "📄"  # Default icon
        if ext in ['.prproj']:
            icon = "🎬"  # Premiere
        elif ext in ['.aep', '.aepx']:
            icon = "✨"  # After Effects
        elif ext in ['.psd']:
            icon = "📷"  # Photoshop
        elif ext in ['.ai']:
            icon = "📝"  # Illustrator
        
        # Content layout
        self.icon_label = Label(self.card_frame, text=icon, font=("Segoe UI", 18),
                              bg=colors["card_bg"], fg=colors["text"])
        self.icon_label.pack(side=LEFT, padx=10, pady=5)
        
        # Make icon clickable too
        if select_callback:
            self.icon_label.bind("<Button-1>", lambda e, p=template_path: select_callback({'path': p, 'name': self.filename}))
            self.icon_label.bind("<Enter>", self._on_hover_enter)
            self.icon_label.bind("<Leave>", self._on_hover_leave)
        
        # Info section
        self.info_frame = Frame(self.card_frame, bg=colors["card_bg"])
        self.info_frame.pack(side=LEFT, fill=BOTH, expand=True, pady=5)
        
        self.name_label = Label(self.info_frame, text=self.filename, 
                              font=("Segoe UI", 11, "bold"),
                              bg=colors["card_bg"], fg=colors["text"], anchor="w")
        self.name_label.pack(fill=X)
        
        # Truncate path for display
        folder_path = os.path.dirname(template_path)
        if len(folder_path) > 40:
            display_path = folder_path[:20] + "..." + folder_path[-17:]
        else:
            display_path = folder_path
            
        self.path_label = Label(self.info_frame, text=display_path, 
                              font=("Segoe UI", 9),
                              bg=colors["card_bg"], fg=colors["secondary_text"], anchor="w")
        self.path_label.pack(fill=X)
        
        # Make all labels clickable
        if select_callback:
            for label in [self.name_label, self.path_label]:
                label.bind("<Button-1>", lambda e, p=template_path: select_callback({'path': p, 'name': self.filename}))
                label.bind("<Enter>", self._on_hover_enter)
                label.bind("<Leave>", self._on_hover_leave)
        
        # Add remove button if callback provided
        if remove_callback:
            self.remove_btn_frame = Frame(self.card_frame, bg=colors["card_bg"])
            self.remove_btn_frame.pack(side=RIGHT, padx=5, pady=5)
            
            self.remove_btn = Label(self.remove_btn_frame, text="✕", font=("Segoe UI", 9),
                                  bg=colors["card_bg"], fg=colors["text"],
                                  cursor="hand2", padx=5)
            self.remove_btn.pack()
            
            # Bind click event to remove callback
            self.remove_btn.bind("<Button-1>", lambda e, p=template_path: remove_callback({'path': p, 'name': self.filename}))
            
            # Highlight on hover
            self.remove_btn.bind("<Enter>", lambda e: self.remove_btn.configure(fg=colors["error"]))
            self.remove_btn.bind("<Leave>", lambda e: self.remove_btn.configure(fg=colors["text"] if not self.is_highlighted else "white"))
    
    def _on_hover_enter(self, event=None):
        """Handle mouse enter for hover effect"""
        if not self.is_highlighted:
            # Light grey hover effect - slightly lighter than card_bg
            hover_bg = "#303030"  # Slightly lighter than card_bg
            
            # Update card and children background
            self.card_frame.configure(bg=hover_bg, highlightbackground=hover_bg)
            self.icon_label.configure(bg=hover_bg)
            self.info_frame.configure(bg=hover_bg)
            
            for widget in self.info_frame.winfo_children():
                widget.configure(bg=hover_bg)
            
            if hasattr(self, 'remove_btn_frame'):
                self.remove_btn_frame.configure(bg=hover_bg)
                
            if hasattr(self, 'remove_btn'):
                self.remove_btn.configure(bg=hover_bg)
        
        # Always change cursor
        self.configure(cursor="hand2")
        self.card_frame.configure(cursor="hand2")
        
    def _on_hover_leave(self, event=None):
        """Handle mouse leave for hover effect"""
        if not self.is_highlighted:
            # Reset to regular card background
            self.card_frame.configure(bg=colors["card_bg"], highlightbackground=colors["card_bg"])
            self.icon_label.configure(bg=colors["card_bg"])
            self.info_frame.configure(bg=colors["card_bg"])
            
            for widget in self.info_frame.winfo_children():
                widget.configure(bg=colors["card_bg"])
                
            if hasattr(self, 'remove_btn_frame'):
                self.remove_btn_frame.configure(bg=colors["card_bg"])
                
            if hasattr(self, 'remove_btn'):
                self.remove_btn.configure(bg=colors["card_bg"])
                
        # Reset cursor
        self.configure(cursor="")
        self.card_frame.configure(cursor="")

# Add rounded rectangle creation capability to Canvas
tk.Canvas.create_rounded_rectangle = lambda self, x1, y1, x2, y2, radius=25, **kwargs: self.create_polygon(
    x1+radius, y1,
    x1+radius, y1,
    x2-radius, y1,
    x2-radius, y1,
    x2, y1,
    x2, y1+radius,
    x2, y1+radius,
    x2, y2-radius,
    x2, y2-radius,
    x2, y2,
    x2-radius, y2,
    x2-radius, y2,
    x1+radius, y2,
    x1+radius, y2,
    x1, y2,
    x1, y2-radius,
    x1, y2-radius,
    x1, y1+radius,
    x1, y1+radius,
    x1, y1,
    smooth=True, **kwargs)

class StructureEditor(Toplevel):
    """
    A dialog for editing file structures and saving them as templates
    """
    def __init__(self, parent, structure=None, save_callback=None, title="Edit Structure", app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.title(title)
        self.geometry("700x550")
        self.minsize(550, 450)
        self.transient(parent)
        self.grab_set()
        
        # Store app reference to access template manager
        self.app = app
        
        # Configure window with dark theme
        self.configure(bg=colors["bg"])
        
        self.structure = structure or []
        self.save_callback = save_callback
        
        # Main container
        self.main_frame = Frame(self, padx=20, pady=20, bg=colors["bg"])
        self.main_frame.pack(fill=BOTH, expand=True)
        
        # Structure name
        self.name_frame = Frame(self.main_frame, bg=colors["bg"])
        self.name_frame.pack(fill=X, pady=(0, 15))
        
        Label(self.name_frame, text="Structure Name:", 
            font=("Segoe UI", 10, "bold"), bg=colors["bg"], fg=colors["text"]).pack(side=LEFT)
        self.name_var = StringVar()
        self.name_entry = Entry(self.name_frame, textvariable=self.name_var, width=30)
        self.name_entry.pack(side=LEFT, padx=(10, 0))
        
        # Add a header and explanation
        header_label = Label(self.main_frame, text="Folder Structure Editor", 
                          font=("Segoe UI", 14, "bold"), bg=colors["bg"], fg=colors["text"])
        header_label.pack(fill=X, pady=(0, 10))
        
        # Add structure selection if app is provided
        if app:
            self.structure_select_frame = Frame(self.main_frame, bg=colors["bg"])
            self.structure_select_frame.pack(fill=X, pady=(0, 15))
            
            Label(self.structure_select_frame, text="Use Existing Structure:", 
                font=("Segoe UI", 10), bg=colors["bg"], fg=colors["text"]).pack(side=LEFT)
            
            # Get available structures
            available_structures = [""] + (["Default"] if app else []) + list(app.template_manager.custom_structures.keys())
            self.structure_var = StringVar()
            self.structure_dropdown = ttk.OptionMenu(
                self.structure_select_frame, 
                self.structure_var, 
                "", 
                *available_structures,
                command=self._on_structure_selected
            )
            self.structure_dropdown.pack(side=LEFT, padx=(10, 0))
            
            # Add a "Load" button
            ttk.Button(self.structure_select_frame, text="Load", 
                     command=self._load_selected_structure).pack(side=LEFT, padx=(10, 0))
        
        explanation = Label(self.main_frame, 
                         text="Define the folders that will be created when using this template.\n"
                              "Each line represents a folder path. Use forward slashes (/) to indicate subfolders.",
                         justify=LEFT, wraplength=650, bg=colors["bg"], fg=colors["text"])
        explanation.pack(fill=X, pady=(0, 15))
        
        # Sample frame - using the dark theme colors
        sample_frame = Frame(self.main_frame, bg=colors["card_bg"], padx=15, pady=15)
        sample_frame.pack(fill=X, pady=(0, 15))
        
        Label(sample_frame, text="Example:", font=("Segoe UI", 10, "bold"), 
            bg=colors["card_bg"], fg=colors["text"]).pack(anchor=W)
        
        sample_text = """images
css
js
docs
data/config
data/assets
source/scripts
source/modules"""
        
        sample_label = Label(sample_frame, text=sample_text, font=("Consolas", 9), 
                          bg=colors["card_bg"], fg=colors["text"], anchor=W, justify=LEFT)
        sample_label.pack(fill=X, pady=(5, 0))
        
        # Add explanation of what this creates
        folder_explanation = Label(sample_frame, 
                               text="This will create: images/, css/, js/, docs/, data/config/, data/assets/, source/scripts/, source/modules/", 
                               wraplength=650, bg=colors["card_bg"], fg=colors["secondary_text"],
                               anchor=W, justify=LEFT)
        folder_explanation.pack(fill=X, pady=(5, 0))
        
        # Tools frame
        tools_frame = Frame(self.main_frame, bg=colors["bg"])
        tools_frame.pack(fill=X, pady=(0, 10))
        
        # Add buttons for common operations
        ttk.Button(tools_frame, text="Add Folder", 
                 command=self._add_folder).pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(tools_frame, text="Import Structure", 
                 command=self._import_structure).pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(tools_frame, text="Clear All", 
                 command=self._clear_structure).pack(side=LEFT, padx=(0, 5))
        
        # Editor frame
        self.editor_frame = Frame(self.main_frame, bg=colors["bg"])
        self.editor_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        # Instructions
        Label(self.editor_frame, text="Enter one folder path per line. Use / for subfolders:", 
             anchor="w", bg=colors["bg"], fg=colors["text"]).pack(fill=X, pady=(0, 5))
        
        # Text editor with scrollbar
        self.editor = Text(self.editor_frame, wrap=NONE, font=("Consolas", 10),
                        bg=colors["card_bg"], fg=colors["text"], insertbackground=colors["text"])
        scrollbar = ttk.Scrollbar(self.editor_frame, command=self.editor.yview)
        self.editor.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=RIGHT, fill=Y)
        self.editor.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Fill with current structure
        if self.structure:
            self.editor.insert(END, "\n".join(self.structure))
        
        # Buttons
        self.button_frame = Frame(self.main_frame, bg=colors["bg"])
        self.button_frame.pack(fill=X)
        
        ttk.Button(self.button_frame, text="Save", command=self.save_structure).pack(side=RIGHT, padx=(10, 0))
        ttk.Button(self.button_frame, text="Cancel", command=self.destroy).pack(side=RIGHT)
    
    def _on_structure_selected(self, selection):
        """Called when a structure is selected from the dropdown"""
        # This just updates the selection, doesn't load it yet
        pass
        
    def _load_selected_structure(self):
        """Load the selected structure into the editor"""
        selected = self.structure_var.get()
        if not selected:
            return
            
        if selected == "Default":
            # Load default structure
            self.structure = self.app.template_manager.get_default_structure("Standard")
        else:
            # Load custom structure
            self.structure = self.app.template_manager.get_structure(selected)
            
        # Update the text widget
        self.editor.delete(1.0, END)
        self.editor.insert(END, "\n".join(self.structure))
        
        # Update structure preview
        self._update_structure_preview()
    
    def _add_folder(self):
        """Add a new folder"""
        folder = simpledialog.askstring("Add Folder", "Enter folder path (use / for subfolders):")
        if folder:
            # Add to editor
            current_text = self.editor.get(1.0, END).strip()
            if current_text:
                self.editor.insert(END, f"\n{folder}")
            else:
                self.editor.insert(END, folder)
            
            # Flash the added text to highlight it
            self.editor.tag_add("flash", f"end-{len(folder)}c", "end")
            self.editor.tag_config("flash", background="#3d85c6")  # Highlight with blue
            
            # Schedule the removal of the highlight after 1.5 seconds
            self.after(1500, lambda: self.editor.tag_remove("flash", "1.0", "end"))
    
    def _import_structure(self):
        """Import folder structure from a directory"""
        folder_path = filedialog.askdirectory(
            title="Select Folder to Import Structure From"
        )
        
        if folder_path:
            # Get folders
            folders = []
            base_dir = os.path.basename(folder_path)
            
            for root, dirs, _ in os.walk(folder_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                rel_path = os.path.relpath(root, os.path.dirname(folder_path))
                if rel_path != '.':  # Don't include the root folder
                    folders.append(rel_path.replace(os.sep, '/'))
            
            # Sort folders
            folders.sort()
            
            if folders:
                # Clear and update editor
                self.editor.delete(1.0, END)
                self.editor.insert(END, "\n".join(folders))
                
                # Highlight all the imported content temporarily
                self.editor.tag_add("imported", "1.0", "end")
                self.editor.tag_config("imported", background="#2d6a31")  # Green highlight
                
                # Remove highlight after 1.5 seconds
                self.after(1500, lambda: self.editor.tag_remove("imported", "1.0", "end"))
                
                messagebox.showinfo("Success", f"Imported {len(folders)} folders from {os.path.basename(folder_path)}")
            else:
                messagebox.showinfo("No Folders", "No folders found in the selected directory.")
    
    def _clear_structure(self):
        """Clear the structure editor"""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all folders?"):
            self.editor.delete(1.0, END)
    
    def save_structure(self):
        """Save the structure and call the callback"""
        name = self.name_var.get().strip()
        if not name:
            tk.messagebox.showerror("Error", "Please enter a name for this structure")
            return
        
        # Get structure as list of lines
        text = self.editor.get(1.0, END).strip()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not lines:
            tk.messagebox.showerror("Error", "Structure cannot be empty")
            return
        
        # Show a confirmation with the structure that will be created
        confirm_text = "\n".join([f"• {line}" for line in lines])
        confirmation = f"Save the following folder structure as '{name}'?\n\n{confirm_text}"
        
        if tk.messagebox.askyesno("Confirm Structure", confirmation):
            if self.save_callback:
                self.save_callback(name, lines)
            
            self.destroy()

class TemplateDirectoryEditor(Toplevel):
    """
    Advanced editor for directory templates that allows editing both the folder structure
    and template files.
    """
    def __init__(self, parent, template_path=None, save_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.title("Edit Directory Template")
        self.geometry("800x600")
        self.minsize(700, 500)
        self.transient(parent)
        self.grab_set()
        
        self.template_path = template_path
        self.save_callback = save_callback
        self.template_info = {}
        
        # Load template info if available
        self._load_template_info()
        
        # Main container with tabs
        self.main_frame = Frame(self, padx=10, pady=10)
        self.main_frame.pack(fill=BOTH, expand=True)
        
        # Create a tabbed interface
        self.tab_control = ttk.Notebook(self.main_frame)
        
        # Tab 1: Structure Editor
        self.structure_tab = Frame(self.tab_control)
        self.tab_control.add(self.structure_tab, text="Folder Structure")
        
        # Tab 2: Files Editor
        self.files_tab = Frame(self.tab_control)
        self.tab_control.add(self.files_tab, text="Template Files")
        
        # Tab 3: Placeholders
        self.placeholders_tab = Frame(self.tab_control)
        self.tab_control.add(self.placeholders_tab, text="Placeholders")
        
        self.tab_control.pack(expand=True, fill=BOTH)
        
        # Setup all tabs
        self._setup_structure_editor()
        self._setup_files_editor()
        self._setup_placeholders_tab()
        
        # Select the structure tab by default
        self.tab_control.select(0)
        
        # Bottom buttons (shared across all tabs)
        self.button_frame = Frame(self.main_frame)
        self.button_frame.pack(fill=X, pady=(10, 0))
        
        ttk.Button(self.button_frame, text="Save Template", 
                 command=self.save_template).pack(side=RIGHT, padx=(10, 0))
        ttk.Button(self.button_frame, text="Cancel", 
                 command=self.destroy).pack(side=RIGHT)
        
        # Initialize drag and drop (only on supported platforms)
        if platform.system() in ["Windows", "Darwin"]:  # Windows or macOS
            self._setup_drag_drop()
    
    def _load_template_info(self):
        """Load template information from template.json if available"""
        if not self.template_path or not os.path.isdir(self.template_path):
            return
        
        template_json_path = os.path.join(self.template_path, "template.json")
        if os.path.exists(template_json_path):
            try:
                with open(template_json_path, 'r') as f:
                    self.template_info = json.load(f)
            except Exception as e:
                print(f"Error loading template info: {e}")
                self.template_info = {}
        else:
            self.template_info = {}
    
    def _setup_drag_drop(self):
        """Setup drag and drop functionality"""
        try:
            if platform.system() == "Windows":
                # Windows implementation using tkdnd
                try:
                    self.tk.call('package', 'require', 'tkdnd')
                    
                    # Register targets and callbacks for the structure editor
                    self.structure_editor.drop_target_register('DND_Files')
                    self.structure_editor.dnd_bind('<<Drop>>', self._process_dropped_folder)
                    
                    # Create drop indicator in structure editor
                    drop_frame = Frame(self.structure_tab, bg="#2C4F76", padx=10, pady=10)
                    drop_frame.place(relx=0.5, rely=0.5, anchor=CENTER, width=300, height=100)
                    
                    Label(drop_frame, text="Drag & Drop Folder Here", 
                        bg="#2C4F76", fg="white", font=("Segoe UI", 12)).pack()
                    Label(drop_frame, text="to import the folder structure", 
                        bg="#2C4F76", fg="white", font=("Segoe UI", 9)).pack()
                    
                    # Remove indicator after first interaction
                    self.structure_editor.bind("<Button-1>", lambda e: drop_frame.place_forget())
                    self.structure_editor.bind("<Key>", lambda e: drop_frame.place_forget())
                except:
                    print("Windows drag & drop not available (tkdnd missing)")
                
            elif platform.system() == "Darwin":  # macOS
                # macOS implementation
                # This is a simplified implementation - for a full implementation, 
                # macOS would need AppleEvents/NSAppleEventDescriptor integration
                try:
                    drop_frame = Frame(self.structure_tab, bg="#2C4F76", padx=10, pady=10)
                    drop_frame.place(relx=0.5, rely=0.5, anchor=CENTER, width=300, height=100)
                    
                    Label(drop_frame, text="Drag & Drop Folder Here", 
                        bg="#2C4F76", fg="white", font=("Segoe UI", 12)).pack()
                    Label(drop_frame, text="to import the folder structure", 
                        bg="#2C4F76", fg="white", font=("Segoe UI", 9)).pack()
                    
                    # Since we can't easily do native drag and drop on macOS without additional libraries,
                    # provide an "Import Structure" button as an alternative
                    ttk.Button(drop_frame, text="Import Folder Structure", 
                            command=self._import_folder_structure).pack(pady=(10, 0))
                    
                    # Remove indicator after first interaction
                    self.structure_editor.bind("<Button-1>", lambda e: drop_frame.place_forget())
                    self.structure_editor.bind("<Key>", lambda e: drop_frame.place_forget())
                except:
                    print("MacOS drag & drop not fully implemented")
        except Exception as e:
            print(f"Error setting up drag & drop: {e}")
    
    def _process_dropped_folder(self, event):
        """Process a dropped folder on Windows"""
        try:
            # Get the dropped path
            dropped_path = event.data
            
            # Clean up path (Windows might include curly braces or quotes)
            if platform.system() == "Windows":
                dropped_path = dropped_path.replace('{', '').replace('}', '')
                dropped_path = dropped_path.strip('"')
            
            # Check if it's a directory
            if os.path.isdir(dropped_path):
                self._import_folder_structure_from_path(dropped_path)
            else:
                messagebox.showinfo("Not a Folder", 
                                 "The dropped item is not a folder. Please drop a folder to import its structure.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process dropped folder: {str(e)}")
    
    def _import_folder_structure(self):
        """Import a folder structure from file dialog"""
        folder_path = filedialog.askdirectory(
            title="Select Folder to Import Structure From"
        )
        
        if folder_path:
            self._import_folder_structure_from_path(folder_path)
    
    def _import_folder_structure_from_path(self, folder_path):
        """Import a folder structure from a specified path"""
        try:
            # Get base directory name
            base_dir = os.path.basename(folder_path)
            
            # Clear existing content
            self.structure_editor.delete(1.0, END)
            
            # Get folders
            folders = []
            base_len = len(folder_path) + 1  # +1 for the trailing slash
            
            for root, dirs, _ in os.walk(folder_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                rel_path = os.path.join(base_dir, root[base_len:])
                rel_path = rel_path.replace(os.sep, '/')  # Normalize to forward slashes
                folders.append(rel_path)
            
            # Sort folders
            folders.sort()
            
            # Update editor
            self.structure_editor.insert(END, "\n".join(folders))
            
            # Show success message
            messagebox.showinfo("Success", f"Imported structure from {os.path.basename(folder_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import folder structure: {str(e)}")
    
    def _setup_structure_editor(self):
        """Setup the structure editor tab"""
        frame = Frame(self.structure_tab, padx=20, pady=20)
        frame.pack(fill=BOTH, expand=True)
        
        # Add a clear heading
        heading_frame = Frame(frame)
        heading_frame.pack(fill=X, pady=(0, 15))
        
        heading = Label(heading_frame, text="Template Folder Structure Editor", 
                      font=("Segoe UI", 14, "bold"), anchor="w")
        heading.pack(side=LEFT)
        
        # Add explanatory text
        explanation = Label(frame, 
                          text="This is where you define the folder structure that will be created when using this template.\n"
                               "Each line represents a folder path. Use forward slashes (/) to indicate subfolders.",
                          justify=LEFT, anchor="w", wraplength=700)
        explanation.pack(fill=X, pady=(0, 15))
        
        # Template name and info
        info_frame = Frame(frame)
        info_frame.pack(fill=X, pady=(0, 15))
        
        Label(info_frame, text="Template Directory:", anchor="w").pack(fill=X)
        
        path_frame = Frame(info_frame)
        path_frame.pack(fill=X, pady=(5, 10))
        
        if self.template_path:
            template_path_text = self.template_path
        else:
            template_path_text = "No template directory selected"
        
        self.template_path_label = Label(path_frame, text=template_path_text, 
                                      anchor="w", bg=colors["card_bg"], fg=colors["text"],
                                      padx=5, pady=5)
        self.template_path_label.pack(fill=X)
        
        # Add structure management buttons
        struct_buttons_frame = Frame(frame)
        struct_buttons_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Button(struct_buttons_frame, text="View Folder Structure", 
                  command=self._view_folder_structure).pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(struct_buttons_frame, text="Add Folder", 
                  command=self._add_folder).pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(struct_buttons_frame, text="Clear Structure", 
                  command=self._clear_structure).pack(side=LEFT, padx=(0, 5))
        
        # Create a visual example
        example_frame = Frame(frame, bg=colors["card_bg"], padx=10, pady=10)
        example_frame.pack(fill=X, pady=(0, 15))
        
        Label(example_frame, text="Example:", font=("Segoe UI", 10, "bold"), 
             bg=colors["card_bg"], anchor="w").pack(fill=X)
        
        example_text = """images
css
js
docs
data/config
data/assets
source/scripts
source/modules"""
        
        example_label = Label(example_frame, text=example_text, font=("Consolas", 9), 
                           bg=colors["card_bg"], anchor="w", justify=LEFT)
        example_label.pack(fill=X, pady=(5, 0))
        
        Label(example_frame, text="This will create: images/, css/, js/, docs/, data/config/, data/assets/, source/scripts/, source/modules/", 
             bg=colors["card_bg"], anchor="w", wraplength=700, fg=colors["secondary_text"]).pack(fill=X, pady=(5, 0))
        
        # Instructions
        Label(frame, text="Edit the folder structure below (one folder per line, use / for subfolders):", 
            anchor="w", font=("Segoe UI", 10, "bold")).pack(fill=X, pady=(0, 5))
        
        # Structure editor with scrollbar
        editor_frame = Frame(frame)
        editor_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        self.structure_editor = Text(editor_frame, wrap=NONE, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(editor_frame, command=self.structure_editor.yview)
        self.structure_editor.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=RIGHT, fill=Y)
        self.structure_editor.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Load existing folders if a template path is provided
        self._load_existing_folders()
    
    def _view_folder_structure(self):
        """Open a tree view of the current folder structure"""
        if not self.template_path or not os.path.isdir(self.template_path):
            tk.messagebox.showerror("Error", "No template directory selected")
            return
        
        # Create a new window to display folder structure
        view_window = tk.Toplevel(self)
        view_window.title("Folder Structure Viewer")
        view_window.geometry("600x500")
        view_window.transient(self)
        
        # Add a treeview to display the folder structure
        frame = Frame(view_window, padx=20, pady=20)
        frame.pack(fill=BOTH, expand=True)
        
        Label(frame, text=f"Folder Structure for {os.path.basename(self.template_path)}", 
            anchor="w", font=("Segoe UI", 12, "bold")).pack(fill=X, pady=(0, 15))
        
        # Create treeview with scrollbars
        tree_frame = Frame(frame)
        tree_frame.pack(fill=BOTH, expand=True)
        
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=RIGHT, fill=Y)
        
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=HORIZONTAL)
        tree_scroll_x.pack(side=BOTTOM, fill=X)
        
        tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        tree.pack(fill=BOTH, expand=True)
        
        tree_scroll_y.config(command=tree.yview)
        tree_scroll_x.config(command=tree.xview)
        
        # Configure the treeview
        tree["columns"] = ("size", "date_modified")
        tree.column("#0", width=300, minwidth=200)
        tree.column("size", width=100, minwidth=80)
        tree.column("date_modified", width=150, minwidth=150)
        
        tree.heading("#0", text="Name")
        tree.heading("size", text="Size")
        tree.heading("date_modified", text="Date Modified")
        
        # Function to populate the tree
        def populate_tree(parent_node, path):
            try:
                # Add directories first
                for item in sorted(os.listdir(path)):
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path) and not item.startswith('.'):
                        # Get directory stats
                        stats = os.stat(item_path)
                        size = sum(os.path.getsize(os.path.join(dirpath, filename)) 
                                 for dirpath, _, filenames in os.walk(item_path) 
                                 for filename in filenames)
                        size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
                        mtime = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                        
                        # Insert with folder icon
                        child = tree.insert(parent_node, "end", text=f"📁 {item}", 
                                         values=(size_str, mtime), open=True)
                        populate_tree(child, item_path)
                
                # Then add files
                for item in sorted(os.listdir(path)):
                    item_path = os.path.join(path, item)
                    if os.path.isfile(item_path) and not item.startswith('.'):
                        # Get file stats
                        stats = os.stat(item_path)
                        size = stats.st_size
                        size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
                        mtime = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                        
                        # Determine icon based on file type
                        _, ext = os.path.splitext(item)
                        if ext.lower() in ['.txt', '.md']:
                            icon = "📄" 
                        elif ext.lower() in ['.jpg', '.png', '.gif', '.jpeg', '.bmp']:
                            icon = "🖼️"
                        elif ext.lower() in ['.py', '.js', '.html', '.css', '.c', '.cpp', '.java']:
                            icon = "📜"
                        elif ext.lower() in ['.zip', '.rar', '.tar', '.gz']:
                            icon = "📦"
                        elif ext.lower() in ['.mp3', '.wav', '.flac']:
                            icon = "🎵"
                        elif ext.lower() in ['.mp4', '.avi', '.mov', '.wmv']:
                            icon = "🎬"
                        elif ext.lower() in ['.pdf']:
                            icon = "📑"
                        elif ext.lower() in ['.doc', '.docx']:
                            icon = "📃"
                        elif ext.lower() in ['.xls', '.xlsx']:
                            icon = "📊"
                        elif ext.lower() in ['.ppt', '.pptx']:
                            icon = "📽️"
                        else:
                            icon = "📄"
                        
                        tree.insert(parent_node, "end", text=f"{icon} {item}", values=(size_str, mtime))
            except Exception as e:
                print(f"Error populating tree: {e}")
        
        # Create root node
        root_node = tree.insert("", "end", text=f"📁 {os.path.basename(self.template_path)}", open=True)
        populate_tree(root_node, self.template_path)
        
        # Add a button to close the window
        ttk.Button(frame, text="Close", command=view_window.destroy).pack(pady=(15, 0))
    
    def _add_folder(self):
        """Add a new folder to the structure"""
        folder_path = simpledialog.askstring(
            "Add Folder", 
            "Enter folder path (use / for subfolders):",
            parent=self
        )
        
        if not folder_path:
            return  # User cancelled
        
        # Clean up the path
        folder_path = folder_path.strip().replace('\\', '/')
        
        # Add to the editor
        current_text = self.structure_editor.get(1.0, END).strip()
        if current_text:
            self.structure_editor.insert(END, f"\n{folder_path}")
        else:
            self.structure_editor.insert(END, folder_path)
        
        # Flash the added text to highlight it
        self.structure_editor.tag_add("flash", f"end-{len(folder_path)}c", "end")
        self.structure_editor.tag_config("flash", background="#3d85c6")  # Highlight with blue
        
        # Schedule the removal of the highlight after 1.5 seconds
        self.after(1500, lambda: self.structure_editor.tag_remove("flash", "1.0", "end"))
        
        # Create the folder in the template directory
        if self.template_path:
            try:
                full_path = os.path.join(self.template_path, folder_path.replace('/', os.sep))
                os.makedirs(full_path, exist_ok=True)
                tk.messagebox.showinfo("Success", f"Folder '{folder_path}' created")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to create folder: {str(e)}")
    
    def _clear_structure(self):
        """Clear the structure editor"""
        if not tk.messagebox.askyesno("Confirm", 
                                    "Are you sure you want to clear the structure editor?"):
            return
        
        self.structure_editor.delete(1.0, END)

    def _setup_files_editor(self):
        """Setup the files editor tab"""
        frame = Frame(self.files_tab, padx=20, pady=20)
        frame.pack(fill=BOTH, expand=True)
        
        # Add heading
        heading_frame = Frame(frame)
        heading_frame.pack(fill=X, pady=(0, 15))
        
        heading = Label(heading_frame, text="Template Files Manager", 
                      font=("Segoe UI", 14, "bold"), anchor="w")
        heading.pack(side=LEFT)
        
        # Add explanatory text
        explanation = Label(frame, 
                          text="Here you can assign a main template file and manage additional files for your template.",
                          justify=LEFT, anchor="w", wraplength=700)
        explanation.pack(fill=X, pady=(0, 15))
        
        # Main template file section
        template_section = Frame(frame, bg=colors["card_bg"], padx=15, pady=15)
        template_section.pack(fill=X, pady=(0, 15))
        
        # Section title
        Label(template_section, text="Main Template File", 
            font=("Segoe UI", 12, "bold"), bg=colors["card_bg"], anchor="w").pack(fill=X, pady=(0, 10))
        
        Label(template_section, 
            text="This is the primary file that will be renamed to match the project name when creating a project.",
            wraplength=700, bg=colors["card_bg"], anchor="w").pack(fill=X, pady=(0, 10))
        
        # Template file buttons
        template_buttons_frame = Frame(template_section, bg=colors["card_bg"])
        template_buttons_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Button(template_buttons_frame, text="Load Template File", 
                 command=self._load_template_file).pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(template_buttons_frame, text="Clear Template", 
                 command=self._clear_template_file).pack(side=LEFT)
        
        # Template file display
        self.template_file_display = Label(template_section, text="No main template file selected", 
                                        bg="#333333", fg=colors["text"],
                                        padx=10, pady=5, anchor="w")
        self.template_file_display.pack(fill=X, pady=(0, 0))
        
        # Load main template file if it exists
        self._load_main_template_file_info()
        
        # Additional files section
        additional_section = Frame(frame, bg=colors["bg"])
        additional_section.pack(fill=BOTH, expand=True, pady=(15, 0))
        
        # Section title
        Label(additional_section, text="Additional Template Files", 
            font=("Segoe UI", 12, "bold"), bg=colors["bg"], anchor="w").pack(fill=X, pady=(0, 10))
        
        Label(additional_section, 
            text="These files will be copied into the project but won't be automatically renamed.",
            wraplength=700, bg=colors["bg"], anchor="w").pack(fill=X, pady=(0, 10))
        
        # Files display with scrollbar
        files_frame = Frame(additional_section)
        files_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        self.files_list = tk.Listbox(files_frame, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(files_frame, command=self.files_list.yview)
        self.files_list.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=RIGHT, fill=Y)
        self.files_list.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Buttons for file operations
        file_buttons_frame = Frame(additional_section)
        file_buttons_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Button(file_buttons_frame, text="Add File", 
                 command=self._add_file).pack(side=LEFT, padx=(0, 5))
        ttk.Button(file_buttons_frame, text="Remove File", 
                 command=self._remove_file).pack(side=LEFT, padx=(0, 5))
        ttk.Button(file_buttons_frame, text="View File", 
                 command=self._view_file).pack(side=LEFT, padx=(0, 5))
        
        # Load existing files if template path is provided
        self._load_existing_files()
    
    def _load_template_file(self):
        """Load a main template file"""
        file_path = filedialog.askopenfilename(
            title="Select Main Template File",
            filetypes=[
                ("Adobe Premiere", "*.prproj"),
                ("After Effects", "*.aep;*.aepx"),
                ("Photoshop", "*.psd"),
                ("Illustrator", "*.ai"),
                ("All Files", "*.*")
            ],
            parent=self
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Copy file to template directory root
            import shutil
            dest_path = os.path.join(self.template_path, os.path.basename(file_path))
            shutil.copy2(file_path, dest_path)
            
            # Create template.json file with template file info
            template_json_path = os.path.join(self.template_path, "template.json")
            if os.path.exists(template_json_path):
                try:
                    with open(template_json_path, 'r') as f:
                        template_info = json.load(f)
                except:
                    template_info = {}
            else:
                template_info = {}
            
            # Update template info
            template_info["main_template_file"] = os.path.basename(file_path)
            template_info["updated"] = datetime.datetime.now().isoformat()
            
            with open(template_json_path, 'w') as f:
                json.dump(template_info, f, indent=2)
            
            # Update display
            self.template_file_display.config(text=f"File: {os.path.basename(file_path)}")
            
            tk.messagebox.showinfo("Success", f"Main template file set to: {os.path.basename(file_path)}")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to set template file: {str(e)}")
    
    def _clear_template_file(self):
        """Clear the main template file"""
        template_json_path = os.path.join(self.template_path, "template.json")
        if not os.path.exists(template_json_path):
            return
        
        try:
            with open(template_json_path, 'r') as f:
                template_info = json.load(f)
            
            if "main_template_file" in template_info:
                del template_info["main_template_file"]
                
                with open(template_json_path, 'w') as f:
                    json.dump(template_info, f, indent=2)
                
                self.template_file_display.config(text="No main template file selected")
                tk.messagebox.showinfo("Success", "Main template file cleared")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to clear template file: {str(e)}")
    
    def _load_main_template_file_info(self):
        """Load information about the main template file"""
        template_json_path = os.path.join(self.template_path, "template.json")
        if not os.path.exists(template_json_path):
            return
        
        try:
            with open(template_json_path, 'r') as f:
                template_info = json.load(f)
            
            if "main_template_file" in template_info:
                main_file = template_info["main_template_file"]
                self.template_file_display.config(text=f"File: {main_file}")
        except Exception as e:
            print(f"Error loading main template file info: {e}")
    
    def _view_file(self):
        """View selected file"""
        selected = self.files_list.curselection()
        if not selected:
            tk.messagebox.showerror("Error", "Please select a file to view")
            return
        
        file_path = self.files_list.get(selected[0])
        full_path = os.path.join(self.template_path, file_path)
        
        if not os.path.exists(full_path):
            tk.messagebox.showerror("Error", f"File not found: {file_path}")
            return
        
        # Check if it's a text file
        is_text = False
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read(1024)  # Read first 1KB to check
            is_text = True
        except UnicodeDecodeError:
            is_text = False
        
        if is_text:
            # Open a text viewer
            viewer = tk.Toplevel(self)
            viewer.title(f"View File: {file_path}")
            viewer.geometry("700x500")
            viewer.transient(self)
            
            frame = Frame(viewer, padx=20, pady=20)
            frame.pack(fill=BOTH, expand=True)
            
            # File path
            Label(frame, text=f"File: {file_path}", anchor="w").pack(fill=X, pady=(0, 10))
            
            # Text display with scrollbars
            text_frame = Frame(frame)
            text_frame.pack(fill=BOTH, expand=True)
            
            scrollbar_y = ttk.Scrollbar(text_frame)
            scrollbar_y.pack(side=RIGHT, fill=Y)
            
            scrollbar_x = ttk.Scrollbar(text_frame, orient=HORIZONTAL)
            scrollbar_x.pack(side=BOTTOM, fill=X)
            
            text = Text(text_frame, wrap=NONE, yscrollcommand=scrollbar_y.set, 
                      xscrollcommand=scrollbar_x.set, font=("Consolas", 10))
            text.pack(side=LEFT, fill=BOTH, expand=True)
            
            scrollbar_y.config(command=text.yview)
            scrollbar_x.config(command=text.xview)
            
            # Load content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            text.insert(END, content)
            text.config(state=DISABLED)  # Make read-only
            
            # Add close button
            ttk.Button(frame, text="Close", command=viewer.destroy).pack(pady=(10, 0))
        else:
            # For non-text files, try to open with system default
            try:
                if platform.system() == "Windows":
                    os.startfile(full_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.Popen(["open", full_path])
                else:  # Linux
                    subprocess.Popen(["xdg-open", full_path])
            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to open file: {str(e)}")
                
                # Fallback - show file info
                tk.messagebox.showinfo("File Info", 
                                     f"File: {file_path}\nSize: {os.path.getsize(full_path)} bytes\n"
                                     f"Type: Binary file (not viewable in text mode)")
    
    def _setup_placeholders_tab(self):
        """Setup the placeholders documentation tab"""
        frame = Frame(self.placeholders_tab, padx=20, pady=20)
        frame.pack(fill=BOTH, expand=True)
        
        # Title
        heading_frame = Frame(frame)
        heading_frame.pack(fill=X, pady=(0, 15))
        
        heading = Label(heading_frame, text="Template Placeholders", 
                      font=("Segoe UI", 14, "bold"), anchor="w")
        heading.pack(side=LEFT)
        
        # Add explanatory text
        explanation = Label(frame, 
                          text="Placeholders allow you to create dynamic template files that adapt to each project.",
                          justify=LEFT, anchor="w", wraplength=700)
        explanation.pack(fill=X, pady=(0, 15))
        
        # Create a card for each placeholder type
        # PROJECT_NAME placeholder
        name_card = Frame(frame, bg=colors["card_bg"], padx=15, pady=15)
        name_card.pack(fill=X, pady=(0, 15))
        
        Label(name_card, text="{{PROJECT_NAME}}", 
            font=("Consolas", 12, "bold"), bg=colors["card_bg"], 
            fg="#4682B4", anchor="w").pack(fill=X)
        
        Label(name_card, 
            text="Replaced with the name of the project. Use this in filenames and file contents.",
            wraplength=700, bg=colors["card_bg"], anchor="w").pack(fill=X, pady=(5, 0))
        
        example_frame = Frame(name_card, bg="#333333", padx=10, pady=10)
        example_frame.pack(fill=X, pady=(10, 0))
        
        Label(example_frame, text="Examples:", 
            font=("Segoe UI", 9, "italic"), bg="#333333", anchor="w").pack(fill=X)
        
        Label(example_frame, 
            text="• A file named '{{PROJECT_NAME}}_README.md' becomes 'MyProject_README.md'\n"
                 "• Text content: 'Welcome to {{PROJECT_NAME}}' becomes 'Welcome to MyProject'",
            wraplength=700, bg="#333333", anchor="w", justify=LEFT).pack(fill=X, pady=(5, 0))
        
        # DATE placeholder
        date_card = Frame(frame, bg=colors["card_bg"], padx=15, pady=15)
        date_card.pack(fill=X, pady=(0, 15))
        
        Label(date_card, text="{{DATE}}", 
            font=("Consolas", 12, "bold"), bg=colors["card_bg"], 
            fg="#4682B4", anchor="w").pack(fill=X)
        
        Label(date_card, 
            text="Replaced with the current date in YYYY-MM-DD format.",
            wraplength=700, bg=colors["card_bg"], anchor="w").pack(fill=X, pady=(5, 0))
        
        example_frame = Frame(date_card, bg="#333333", padx=10, pady=10)
        example_frame.pack(fill=X, pady=(10, 0))
        
        Label(example_frame, text="Example:", 
            font=("Segoe UI", 9, "italic"), bg="#333333", anchor="w").pack(fill=X)
        
        Label(example_frame, 
            text="• 'Created on {{DATE}}' becomes 'Created on 2025-03-07'",
            wraplength=700, bg="#333333", anchor="w").pack(fill=X, pady=(5, 0))
        
        # YEAR placeholder
        year_card = Frame(frame, bg=colors["card_bg"], padx=15, pady=15)
        year_card.pack(fill=X, pady=(0, 15))
        
        Label(year_card, text="{{YEAR}}", 
            font=("Consolas", 12, "bold"), bg=colors["card_bg"], 
            fg="#4682B4", anchor="w").pack(fill=X)
        
        Label(year_card, 
            text="Replaced with the current year (YYYY).",
            wraplength=700, bg=colors["card_bg"], anchor="w").pack(fill=X, pady=(5, 0))
        
        example_frame = Frame(year_card, bg="#333333", padx=10, pady=10)
        example_frame.pack(fill=X, pady=(10, 0))
        
        Label(example_frame, text="Example:", 
            font=("Segoe UI", 9, "italic"), bg="#333333", anchor="w").pack(fill=X)
        
        Label(example_frame, 
            text="• 'Copyright {{YEAR}}' becomes 'Copyright 2025'",
            wraplength=700, bg="#333333", anchor="w").pack(fill=X, pady=(5, 0))
        
        # Note about usage
        note_frame = Frame(frame)
        note_frame.pack(fill=X, pady=(10, 0))
        
        note = Label(note_frame, 
                   text="Note: Placeholders are automatically processed when creating a project from this template.",
                   wraplength=700, fg=colors["secondary_text"], anchor="w")
        note.pack(fill=X)
    
    def _load_existing_folders(self):
        """Load existing folders from the template directory"""
        if not self.template_path or not os.path.isdir(self.template_path):
            return
        
        # Get existing directories
        folders = []
        for root, dirs, _ in os.walk(self.template_path):
            rel_path = os.path.relpath(root, self.template_path)
            if rel_path != '.':  # Don't include root directory
                folders.append(rel_path)
        
        # Sort folders
        folders.sort()
        
        # Update editor
        self.structure_editor.delete(1.0, END)
        self.structure_editor.insert(END, "\n".join(folders))
    
    def _load_existing_files(self):
        """Load existing files from the template directory"""
        if not self.template_path or not os.path.isdir(self.template_path):
            return
        
        # Clear list
        self.files_list.delete(0, END)
        
        # Get all files recursively
        for root, _, files in os.walk(self.template_path):
            rel_path = os.path.relpath(root, self.template_path)
            for file in files:
                if file == "template.json":  # Skip template.json metadata file
                    continue
                    
                if rel_path == '.':
                    self.files_list.insert(END, file)
                else:
                    self.files_list.insert(END, os.path.join(rel_path, file))
    
    def _add_file(self):
        """Add a file to the template directory"""
        if not self.template_path:
            tk.messagebox.showerror("Error", "No template directory selected")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select File to Add",
            filetypes=[("All Files", "*.*")]
        )
        
        if not file_path:
            return  # User cancelled
        
        # Get destination path relative to template directory
        rel_path = simpledialog.askstring(
            "Destination Path", 
            "Enter relative path in template (leave empty for root):",
            initialvalue=""
        )
        
        if rel_path is None:  # User cancelled
            return
        
        # Create destination directory if needed
        if rel_path:
            dest_dir = os.path.join(self.template_path, rel_path)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, os.path.basename(file_path))
        else:
            dest_path = os.path.join(self.template_path, os.path.basename(file_path))
        
        # Copy the file
        import shutil
        try:
            shutil.copy2(file_path, dest_path)
            tk.messagebox.showinfo("Success", f"File added to template: {os.path.basename(file_path)}")
            # Refresh file list
            self._load_existing_files()
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to add file: {str(e)}")
    
    def _remove_file(self):
        """Remove a selected file from the template directory"""
        selected = self.files_list.curselection()
        if not selected:
            tk.messagebox.showerror("Error", "Please select a file to remove")
            return
        
        file_path = self.files_list.get(selected[0])
        
        # Confirm deletion
        if not tk.messagebox.askyesno("Confirm Deletion", f"Remove {file_path} from template?"):
            return
        
        # Delete the file
        full_path = os.path.join(self.template_path, file_path)
        try:
            os.remove(full_path)
            tk.messagebox.showinfo("Success", f"File removed: {file_path}")
            # Refresh file list
            self._load_existing_files()
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to remove file: {str(e)}")
    
    def save_template(self):
        """Save the template changes"""
        if not self.template_path:
            tk.messagebox.showerror("Error", "No template directory selected")
            return
        
        try:
            # Get folder structure from editor
            structure_text = self.structure_editor.get(1.0, END).strip()
            folders = [line.strip() for line in structure_text.split('\n') if line.strip()]
            
            # Get or create a structure name for this template
            structure_name = self.template_info.get('structure_name', '')
            template_name = self.template_info.get('name', os.path.basename(self.template_path))
            
            if not structure_name:
                structure_name = f"Template_{template_name}"
            
            # Update template info
            self.template_info['structure_name'] = structure_name
            
            # Save template.json
            template_json_path = os.path.join(self.template_path, "template.json")
            with open(template_json_path, 'w') as f:
                json.dump(self.template_info, f, indent=2)
            
            # Create any new folders that don't exist
            for folder in folders:
                folder_path = os.path.join(self.template_path, folder)
                os.makedirs(folder_path, exist_ok=True)
            
            # Save the structure to the custom structures
            from app.templates.template_manager import TemplateManager
            temp_manager = TemplateManager()
            
            # Save the structure
            success = temp_manager.save_custom_structure(structure_name, folders)
            if not success:
                raise Exception("Failed to save custom structure")
            
            # Let the user know it was saved
            tk.messagebox.showinfo("Success", f"Template structure saved successfully as '{structure_name}'")
            
            # Call the callback if provided
            if self.save_callback:
                self.save_callback()
            
            self.destroy()
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to save template: {str(e)}")

class ProjectNameInput(Toplevel):
    """
    Dialog for batch project creation with multi-line input
    """
    def __init__(self, parent, callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.title("Create Multiple Projects")
        self.geometry("500x400")
        self.minsize(400, 300)
        self.transient(parent)
        self.grab_set()
        
        self.callback = callback
        
        # Main container
        self.main_frame = Frame(self, padx=20, pady=20)
        self.main_frame.pack(fill=BOTH, expand=True)
        
        # Instructions
        Label(self.main_frame, text="Enter one project name per line:", 
             font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 5))
        
        Label(self.main_frame, text="You can paste a list from email or any other source.",
             anchor="w").pack(fill=X, pady=(0, 15))
        
        # Text editor with scrollbar
        self.editor_frame = Frame(self.main_frame)
        self.editor_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        self.editor = Text(self.editor_frame, wrap=NONE, font=("Segoe UI", 10))
        scrollbar = ttk.Scrollbar(self.editor_frame, command=self.editor.yview)
        self.editor.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=RIGHT, fill=Y)
        self.editor.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Buttons
        self.button_frame = Frame(self.main_frame)
        self.button_frame.pack(fill=X)
        
        ttk.Button(self.button_frame, text="Create Projects", 
                  command=self.process_projects).pack(side=RIGHT, padx=(10, 0))
        ttk.Button(self.button_frame, text="Cancel", 
                  command=self.destroy).pack(side=RIGHT)
    
    def process_projects(self):
        """Process the project names and call the callback"""
        text = self.editor.get(1.0, END).strip()
        if not text:
            tk.messagebox.showerror("Error", "Please enter at least one project name")
            return
        
        if self.callback:
            self.callback(text)
        
        self.destroy()
